"""Shadow-only canonical snapshot assembly and in-memory storage.

Stage 1 contains no mechanical formulas and has no production consumers.
SnapshotBuilder assembles validated patches for four initial sections, while
SnapshotStore publishes complete immutable revisions using copy-on-write.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from threading import RLock
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from core.mechanical_refresh_coordinator import RefreshPlan


SNAPSHOT_VERSION = "RDM_V2_CANONICAL_SHADOW_V1"
SNAPSHOT_SECTIONS = (
    "metadata",
    "geometry",
    "current_row_mechanics",
    "open_visit",
)
_PROTECTED_METADATA_FIELDS = frozenset(
    {
        "zone_id",
        "revision",
        "snapshot_version",
        "last_refresh_plan_id",
        "last_event_id",
    }
)


@dataclass(frozen=True)
class CanonicalZoneSnapshot:
    zone_id: str
    revision: int
    snapshot_version: str
    metadata: Mapping[str, Any]
    geometry: Mapping[str, Any]
    current_row_mechanics: Mapping[str, Any]
    open_visit: Mapping[str, Any]
    source_plan_id: str
    source_event_ids: tuple[str, ...]
    shadow_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "revision": self.revision,
            "snapshot_version": self.snapshot_version,
            "metadata": _thaw(self.metadata),
            "geometry": _thaw(self.geometry),
            "current_row_mechanics": _thaw(
                self.current_row_mechanics
            ),
            "open_visit": _thaw(self.open_visit),
            "source_plan_id": self.source_plan_id,
            "source_event_ids": list(self.source_event_ids),
            "shadow_only": self.shadow_only,
        }


class SnapshotBuilder:
    """Assemble immutable snapshots from a plan and supplied result patches."""

    def build(
        self,
        plan: RefreshPlan,
        refresh_result_patches: Iterable[Mapping[str, Any]],
        *,
        previous: CanonicalZoneSnapshot | None = None,
    ) -> CanonicalZoneSnapshot:
        self._validate_plan(plan, previous)

        sections = {
            section: (
                _thaw(getattr(previous, section))
                if previous is not None
                else {}
            )
            for section in SNAPSHOT_SECTIONS
        }

        for patch_index, patch in enumerate(refresh_result_patches):
            normalized = self._validate_patch(patch, patch_index)
            for section, section_patch in normalized.items():
                sections[section] = _merge_mapping(
                    sections[section],
                    section_patch,
                )

        revision = 1 if previous is None else previous.revision + 1
        last_event_id = plan.event_ids[-1] if plan.event_ids else ""
        metadata = sections["metadata"]
        protected_values = {
            "zone_id": plan.zone_id,
            "revision": revision,
            "snapshot_version": SNAPSHOT_VERSION,
            "last_refresh_plan_id": plan.plan_id,
            "last_event_id": last_event_id,
        }
        metadata.update(protected_values)

        return CanonicalZoneSnapshot(
            zone_id=plan.zone_id,
            revision=revision,
            snapshot_version=SNAPSHOT_VERSION,
            metadata=_freeze(metadata),
            geometry=_freeze(sections["geometry"]),
            current_row_mechanics=_freeze(
                sections["current_row_mechanics"]
            ),
            open_visit=_freeze(sections["open_visit"]),
            source_plan_id=plan.plan_id,
            source_event_ids=tuple(plan.event_ids),
        )

    @staticmethod
    def _validate_plan(
        plan: RefreshPlan,
        previous: CanonicalZoneSnapshot | None,
    ) -> None:
        if not isinstance(plan, RefreshPlan):
            raise TypeError("plan must be a RefreshPlan")
        if not plan.zone_id:
            raise ValueError("RefreshPlan zone_id must not be empty")
        if not plan.shadow_only:
            raise ValueError("Stage 1 accepts shadow RefreshPlan only")
        if previous is not None and previous.zone_id != plan.zone_id:
            raise ValueError(
                "RefreshPlan zone does not match previous snapshot"
            )

    @staticmethod
    def _validate_patch(
        patch: Mapping[str, Any],
        patch_index: int,
    ) -> dict[str, Mapping[str, Any]]:
        if not isinstance(patch, Mapping):
            raise TypeError(
                f"refresh result patch {patch_index} must be a mapping"
            )

        unknown = set(patch) - set(SNAPSHOT_SECTIONS)
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise ValueError(f"Unsupported snapshot sections: {names}")

        normalized: dict[str, Mapping[str, Any]] = {}
        for section, section_patch in patch.items():
            if not isinstance(section_patch, Mapping):
                raise TypeError(
                    f"snapshot section {section} must be a mapping"
                )
            if section == "metadata":
                protected = (
                    set(section_patch) & _PROTECTED_METADATA_FIELDS
                )
                if protected:
                    names = ", ".join(sorted(protected))
                    raise ValueError(
                        f"Protected metadata fields cannot be patched: {names}"
                    )
            normalized[section] = deepcopy(dict(section_patch))
        return normalized


class SnapshotStore:
    """Thread-safe in-memory store for current immutable zone snapshots."""

    def __init__(self, builder: SnapshotBuilder | None = None) -> None:
        self._builder = builder or SnapshotBuilder()
        self._current: dict[str, CanonicalZoneSnapshot] = {}
        self._lock = RLock()

    def create(
        self,
        plan: RefreshPlan,
        refresh_result_patches: Iterable[Mapping[str, Any]],
    ) -> CanonicalZoneSnapshot:
        with self._lock:
            if plan.zone_id in self._current:
                raise ValueError(
                    f"Snapshot already exists for zone {plan.zone_id}"
                )
            candidate = self._builder.build(
                plan,
                refresh_result_patches,
            )
            self._current[plan.zone_id] = candidate
            return candidate

    def get_current(
        self,
        zone_id: str,
    ) -> CanonicalZoneSnapshot | None:
        with self._lock:
            return self._current.get(zone_id)

    def update(
        self,
        zone_id: str,
        plan: RefreshPlan,
        refresh_result_patches: Iterable[Mapping[str, Any]],
    ) -> CanonicalZoneSnapshot:
        with self._lock:
            current = self._current.get(zone_id)
            if current is None:
                raise KeyError(f"No snapshot exists for zone {zone_id}")
            if plan.zone_id != zone_id:
                raise ValueError(
                    "RefreshPlan zone does not match requested zone"
                )

            # Build completely before publishing. Any exception leaves the
            # current immutable revision untouched.
            candidate = self._builder.build(
                plan,
                refresh_result_patches,
                previous=current,
            )
            self._current[zone_id] = candidate
            return candidate


def _merge_mapping(
    base: Mapping[str, Any],
    patch: Mapping[str, Any],
) -> dict[str, Any]:
    result = deepcopy(dict(base))
    for key, value in patch.items():
        if (
            isinstance(value, Mapping)
            and isinstance(result.get(key), Mapping)
        ):
            result[key] = _merge_mapping(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                key: _freeze(item)
                for key, item in deepcopy(dict(value)).items()
            }
        )
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return deepcopy(value)


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, frozenset):
        return {_thaw(item) for item in value}
    return deepcopy(value)


__all__ = [
    "CanonicalZoneSnapshot",
    "SNAPSHOT_SECTIONS",
    "SNAPSHOT_VERSION",
    "SnapshotBuilder",
    "SnapshotStore",
]

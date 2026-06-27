"""Shadow-only mechanical refresh planning.

Stage 1 maps normalized interaction events to dirty flags and a symbolic
execution order. It does not import or call RDM components, calculate
mechanics, persist snapshots, or write files.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Iterable

from core.interaction_interpreter import (
    InteractionState,
    MechanicalEvent,
    SUPPORTED_EVENT_TYPES,
)


@dataclass(frozen=True)
class RefreshDirtyFlags:
    geometry_dirty: bool = False
    interaction_dirty: bool = False
    stress_dirty: bool = False
    exposure_dirty: bool = False
    fatigue_recovery_dirty: bool = False
    damage_dirty: bool = False
    health_dirty: bool = False
    visit_dirty: bool = False
    response_dirty: bool = False
    state_dirty: bool = False
    transition_dirty: bool = False
    trajectory_dirty: bool = False
    prediction_dirty: bool = False
    snapshot_dirty: bool = False
    closure_dirty: bool = False

    def active_names(self) -> tuple[str, ...]:
        return tuple(
            field.name
            for field in fields(self)
            if bool(getattr(self, field.name))
        )

    def merged(self, other: "RefreshDirtyFlags") -> "RefreshDirtyFlags":
        return RefreshDirtyFlags(
            **{
                field.name: (
                    bool(getattr(self, field.name))
                    or bool(getattr(other, field.name))
                )
                for field in fields(self)
            }
        )


@dataclass(frozen=True)
class RefreshPlan:
    plan_id: str
    zone_id: str
    event_ids: tuple[str, ...]
    event_types: tuple[str, ...]
    dirty_flags: RefreshDirtyFlags
    execution_order: tuple[str, ...]
    audit_trace: tuple[str, ...]
    shadow_only: bool = True

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["dirty_flags"] = asdict(self.dirty_flags)
        return payload


@dataclass(frozen=True)
class RefreshResult:
    plan: RefreshPlan
    status: str
    executed_stages: tuple[str, ...]
    skipped_stages: tuple[str, ...]
    audit_trace: tuple[str, ...]
    production_effects: bool = False

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["plan"] = self.plan.to_dict()
        return payload


class MechanicalRefreshCoordinator:
    """Create shadow refresh plans from Stage 1 interaction events."""

    _EVENT_FLAGS = {
        "TOUCH": RefreshDirtyFlags(
            interaction_dirty=True,
            stress_dirty=True,
            snapshot_dirty=True,
        ),
        "ZONE_ENTER": RefreshDirtyFlags(
            interaction_dirty=True,
            stress_dirty=True,
            snapshot_dirty=True,
        ),
        "ZONE_EXIT": RefreshDirtyFlags(
            interaction_dirty=True,
            snapshot_dirty=True,
        ),
        "RETURN": RefreshDirtyFlags(
            interaction_dirty=True,
            stress_dirty=True,
            snapshot_dirty=True,
        ),
        "PENETRATION_UPDATED": RefreshDirtyFlags(
            interaction_dirty=True,
            stress_dirty=True,
            exposure_dirty=True,
            fatigue_recovery_dirty=True,
            health_dirty=True,
            snapshot_dirty=True,
        ),
        "VISIT_STARTED": RefreshDirtyFlags(
            interaction_dirty=True,
            visit_dirty=True,
            snapshot_dirty=True,
        ),
        "VISIT_COMPLETED": RefreshDirtyFlags(
            visit_dirty=True,
            response_dirty=True,
            state_dirty=True,
            transition_dirty=True,
            trajectory_dirty=True,
            prediction_dirty=True,
            snapshot_dirty=True,
        ),
    }

    _EXECUTION_ORDER = (
        ("geometry_dirty", "geometry_refresh"),
        ("interaction_dirty", "interaction_refresh"),
        ("stress_dirty", "stress_refresh"),
        ("exposure_dirty", "exposure_refresh"),
        ("fatigue_recovery_dirty", "fatigue_recovery_refresh"),
        ("damage_dirty", "damage_refresh"),
        ("health_dirty", "health_refresh"),
        ("visit_dirty", "visit_refresh"),
        ("response_dirty", "response_refresh"),
        ("state_dirty", "state_refresh"),
        ("transition_dirty", "transition_refresh"),
        ("trajectory_dirty", "trajectory_refresh"),
        ("prediction_dirty", "prediction_refresh"),
        ("snapshot_dirty", "snapshot_refresh"),
        ("closure_dirty", "closure_refresh"),
    )

    def create_plan(
        self,
        state: InteractionState,
        events: Iterable[MechanicalEvent],
    ) -> RefreshPlan:
        normalized_events, duplicate_count = self._normalize_events(
            state,
            events,
        )
        dirty_flags = RefreshDirtyFlags()
        audit: list[str] = [
            f"zone={state.zone_id}",
            f"events_received={len(normalized_events) + duplicate_count}",
            f"duplicate_events_skipped={duplicate_count}",
        ]

        for event in normalized_events:
            event_flags = self._EVENT_FLAGS[event.event_type]
            dirty_flags = dirty_flags.merged(event_flags)
            names = ",".join(event_flags.active_names()) or "none"
            audit.append(
                f"event={event.event_id}:{event.event_type}"
                f" -> dirty={names}"
            )

        execution_order = tuple(
            stage
            for flag_name, stage in self._EXECUTION_ORDER
            if bool(getattr(dirty_flags, flag_name))
        )
        active_flags = ",".join(dirty_flags.active_names()) or "none"
        audit.append(f"combined_dirty={active_flags}")
        audit.append(
            "execution_plan="
            + (",".join(execution_order) if execution_order else "none")
        )
        audit.append("mode=SHADOW_PLAN_ONLY; no components executed")

        event_ids = tuple(event.event_id for event in normalized_events)
        event_types = tuple(event.event_type for event in normalized_events)
        first_event = event_ids[0] if event_ids else "NO_EVENT"
        last_event = event_ids[-1] if event_ids else "NO_EVENT"

        return RefreshPlan(
            plan_id=f"SHADOW:{state.zone_id}:{first_event}:{last_event}",
            zone_id=state.zone_id,
            event_ids=event_ids,
            event_types=event_types,
            dirty_flags=dirty_flags,
            execution_order=execution_order,
            audit_trace=tuple(audit),
        )

    def coordinate(
        self,
        state: InteractionState,
        events: Iterable[MechanicalEvent],
    ) -> RefreshResult:
        plan = self.create_plan(state, events)
        audit = (
            *plan.audit_trace,
            "result=PLANNED_NOT_EXECUTED",
        )
        return RefreshResult(
            plan=plan,
            status="PLANNED_NOT_EXECUTED",
            executed_stages=(),
            skipped_stages=plan.execution_order,
            audit_trace=audit,
        )

    def _normalize_events(
        self,
        state: InteractionState,
        events: Iterable[MechanicalEvent],
    ) -> tuple[tuple[MechanicalEvent, ...], int]:
        normalized: list[MechanicalEvent] = []
        seen_event_ids: set[str] = set()
        duplicate_count = 0

        for event in events:
            if event.event_type not in SUPPORTED_EVENT_TYPES:
                raise ValueError(
                    f"Unsupported mechanical event: {event.event_type}"
                )
            if event.event_type not in self._EVENT_FLAGS:
                raise ValueError(
                    f"No dirty-flag mapping for event: {event.event_type}"
                )
            if event.zone_id != state.zone_id:
                raise ValueError(
                    "MechanicalEvent and InteractionState zone mismatch"
                )
            if event.event_id in seen_event_ids:
                duplicate_count += 1
                continue
            seen_event_ids.add(event.event_id)
            normalized.append(event)

        return tuple(normalized), duplicate_count


__all__ = [
    "MechanicalRefreshCoordinator",
    "RefreshDirtyFlags",
    "RefreshPlan",
    "RefreshResult",
]

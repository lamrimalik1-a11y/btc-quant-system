"""Shadow-only runtime emitter (Phase 0C).

Standalone entry point that will LATER receive the finalized per-case record
from compute_live_rdm_for_case and hand a deep-copied, immutable shadow payload
to the Phase 0A bounded queue. It is NOT yet wired into the LIVE pipeline.

Contract:
  - read the Phase 0A feature flags / kill switch; no-op when disabled or killed
  - build an immutable, deep-copied payload from a finalized record
  - derive global_zone_key = session_id::zone_id
  - synthesize geometry_version from the pinned geometry edges
  - offer the payload to a bounded queue, non-blocking
  - NEVER raise to the caller

No production module is imported here, and nothing in production imports this.
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Optional

from core.shadow_safety.bounded_queue import BoundedDropQueue
from core.shadow_safety.feature_flag import FeatureFlags
from core.shadow_safety.kill_switch import KillSwitch


# Candidate source keys. Exact production naming is confirmed at wiring time
# (Phase 0D); the emitter searches the record and its result_row in order.
_SESSION_KEYS = ("session_id", "session", "session_date", "market_date")
_ZONE_KEYS = ("zone_id", "case_id")
_GEOMETRY_EDGE_KEYS = (
    "formation_lower_edge",
    "formation_upper_edge",
    "interaction_core_lower_edge",
    "interaction_core_upper_edge",
    "interaction_density_lower_band",
    "interaction_density_upper_band",
)

EMIT_DISABLED = "DISABLED"
EMIT_KILLED = "KILLED"
EMIT_ENQUEUED = "ENQUEUED"
EMIT_DROPPED = "DROPPED"
EMIT_ERROR = "ERROR"

_DEFAULT_QUEUE_MAXSIZE = 1024


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze(item) for key, item in dict(value).items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, frozenset):
        return {_thaw(item) for item in value}
    return value


def _first(sources: Iterable[Any], keys: tuple[str, ...]) -> Any:
    for src in sources:
        if not isinstance(src, Mapping):
            continue
        for key in keys:
            if key in src and src[key] not in (None, ""):
                return src[key]
    return None


def _rows_to_list(rows: Any) -> list[dict]:
    """Normalize a DataFrame-like or list-of-mappings into deep-copied dicts."""
    if rows is None:
        return []
    if hasattr(rows, "to_dict"):  # DataFrame-like, without importing pandas
        try:
            records = rows.to_dict("records")
        except Exception:
            try:
                records = rows.to_dict(orient="records")
            except Exception:
                return []
        return [
            copy.deepcopy(dict(r)) for r in records if isinstance(r, Mapping)
        ]
    if isinstance(rows, (list, tuple)):
        return [copy.deepcopy(dict(r)) for r in rows if isinstance(r, Mapping)]
    return []


def _geometry_version(geometry: Mapping[str, Any]) -> str:
    """Deterministic version id synthesized from the pinned geometry edges."""
    try:
        items = tuple(
            sorted((str(key), repr(geometry[key])) for key in geometry)
        )
        if not items:
            return "GEOMv1:NA"
        digest = hashlib.sha1(repr(items).encode("utf-8")).hexdigest()[:12]
        return f"GEOMv1:{digest}"
    except Exception:
        return "GEOMv1:NA"


@dataclass(frozen=True)
class ShadowPayload:
    """Immutable, deep-copied projection of a finalized LIVE record."""

    global_zone_key: str
    session_id: str
    zone_id: str
    episode_id: Any
    emit_status: str
    geometry_version: str
    geometry: Mapping[str, Any]
    rows: tuple
    result_row: Mapping[str, Any]
    trajectory: tuple
    prediction: tuple
    visit_timeline: tuple
    analysis_run_utc: Any = None
    resolved_at_timestamp_utc: Any = None

    def to_dict(self) -> dict:
        return {
            "global_zone_key": self.global_zone_key,
            "session_id": self.session_id,
            "zone_id": self.zone_id,
            "episode_id": self.episode_id,
            "emit_status": self.emit_status,
            "geometry_version": self.geometry_version,
            "geometry": _thaw(self.geometry),
            "rows": _thaw(self.rows),
            "result_row": _thaw(self.result_row),
            "trajectory": _thaw(self.trajectory),
            "prediction": _thaw(self.prediction),
            "visit_timeline": _thaw(self.visit_timeline),
            "analysis_run_utc": self.analysis_run_utc,
            "resolved_at_timestamp_utc": self.resolved_at_timestamp_utc,
        }


@dataclass(frozen=True)
class EmitResult:
    status: str
    payload: Optional[ShadowPayload] = None
    reason: str = ""


class ShadowRuntimeEmitter:
    """Build and enqueue shadow payloads. Never raises to the caller."""

    def __init__(
        self,
        *,
        queue: BoundedDropQueue,
        flags: FeatureFlags | None = None,
        kill_switch: KillSwitch | None = None,
    ) -> None:
        self._queue = queue
        self._flags = flags if flags is not None else FeatureFlags.from_env()
        self._kill = kill_switch if kill_switch is not None else KillSwitch()
        self._enqueued = 0
        self._dropped = 0
        self._errors = 0
        self._skipped = 0

    @property
    def queue(self) -> BoundedDropQueue:
        return self._queue

    def emit(self, record: Any) -> EmitResult:
        """Build + enqueue a payload. Returns a status; never raises."""
        try:
            if not self._flags.should_run():
                self._skipped += 1
                return EmitResult(EMIT_DISABLED)
            if not self._kill.allows():
                self._skipped += 1
                return EmitResult(EMIT_KILLED)

            payload = self._build_payload(record)
            if payload is None:
                self._errors += 1
                return EmitResult(EMIT_ERROR, reason="payload_build_failed")

            if self._queue.offer(payload):
                self._enqueued += 1
                self._kill.record_success()
                return EmitResult(EMIT_ENQUEUED, payload=payload)
            self._dropped += 1
            return EmitResult(EMIT_DROPPED, payload=payload)
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException as exc:  # intentional isolation boundary
            self._errors += 1
            try:
                self._kill.record_failure(type(exc).__name__)
            except Exception:
                pass
            return EmitResult(EMIT_ERROR, reason=type(exc).__name__)

    def _build_payload(self, record: Any) -> Optional[ShadowPayload]:
        if not isinstance(record, Mapping):
            return None
        result_row = record.get("result_row")
        result_row = result_row if isinstance(result_row, Mapping) else {}

        zone_id = _first((record, result_row), _ZONE_KEYS)
        if zone_id in (None, ""):
            return None  # cannot key a snapshot without a zone identity

        session_value = _first((record, result_row), _SESSION_KEYS)
        session_id = (
            str(session_value)
            if session_value not in (None, "")
            else "UNKNOWN_SESSION"
        )
        zone_id = str(zone_id)
        global_zone_key = f"{session_id}::{zone_id}"

        geometry: dict[str, Any] = {}
        rec_geometry = record.get("geometry")
        for source in (result_row, rec_geometry):
            if isinstance(source, Mapping):
                for key in _GEOMETRY_EDGE_KEYS:
                    if key in source and key not in geometry:
                        geometry[key] = source[key]
        geometry_version = _geometry_version(geometry)

        rows = tuple(
            _freeze(row)
            for row in _rows_to_list(
                record.get("live_evolution")
                if record.get("live_evolution") is not None
                else record.get("rows")
            )
        )

        return ShadowPayload(
            global_zone_key=global_zone_key,
            session_id=session_id,
            zone_id=zone_id,
            episode_id=copy.deepcopy(record.get("episode_id")),
            emit_status=str(record.get("emit_status", "")),
            geometry_version=geometry_version,
            geometry=_freeze(copy.deepcopy(geometry)),
            rows=rows,
            result_row=_freeze(copy.deepcopy(dict(result_row))),
            trajectory=tuple(
                _freeze(r) for r in _rows_to_list(record.get("trajectory"))
            ),
            prediction=tuple(
                _freeze(r) for r in _rows_to_list(record.get("prediction"))
            ),
            visit_timeline=tuple(
                _freeze(r) for r in _rows_to_list(record.get("visit_timeline"))
            ),
            analysis_run_utc=copy.deepcopy(record.get("analysis_run_utc")),
            resolved_at_timestamp_utc=copy.deepcopy(
                record.get("resolved_at_timestamp_utc")
            ),
        )

    def stats(self) -> dict:
        return {
            "enqueued": self._enqueued,
            "dropped": self._dropped,
            "errors": self._errors,
            "skipped": self._skipped,
            "queue": self._queue.stats(),
        }


_default_emitter: Optional[ShadowRuntimeEmitter] = None


def get_default_emitter() -> ShadowRuntimeEmitter:
    """Lazily build the process-wide emitter (flags read from env; default OFF)."""
    global _default_emitter
    if _default_emitter is None:
        _default_emitter = ShadowRuntimeEmitter(
            queue=BoundedDropQueue(_DEFAULT_QUEUE_MAXSIZE)
        )
    return _default_emitter


def emit(record: Any) -> EmitResult:
    """Module-level convenience the LIVE tap will call later (no-op until enabled)."""
    return get_default_emitter().emit(record)


__all__ = [
    "EMIT_DISABLED",
    "EMIT_DROPPED",
    "EMIT_ENQUEUED",
    "EMIT_ERROR",
    "EMIT_KILLED",
    "EmitResult",
    "ShadowPayload",
    "ShadowRuntimeEmitter",
    "emit",
    "get_default_emitter",
]

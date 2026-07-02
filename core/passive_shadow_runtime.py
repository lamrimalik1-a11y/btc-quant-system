"""Shadow-only payload-to-snapshot runtime handler (Phase 0E-2)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from core.canonical_snapshot import SnapshotStore
from core.dynamic_mechanics_adapter import DynamicMechanicsAdapter
from core.event_dispatcher import DispatchBatch, DispatchContext, EventDispatcher
from core.geometry_snapshot_adapter import GeometrySnapshotAdapter
from core.interaction_interpreter import ORDER_ACCEPTED, InteractionInterpreter
from core.last_completed_visit_adapter import LastCompletedVisitAdapter
from core.mechanical_refresh_coordinator import RefreshPlan
from core.open_visit_adapter import OpenVisitAdapter
from core.prediction_adapter import PredictionAdapter
from core.row_mechanics_adapter import RowMechanicsAdapter


ROW_DIRTY = ("stress_dirty", "exposure_dirty", "fatigue_recovery_dirty", "health_dirty")
OPEN_VISIT_DIRTY = ("interaction_dirty",)
COMPLETED_VISIT_DIRTY = ("visit_dirty", "response_dirty")
DYNAMIC_DIRTY = ("response_dirty", "state_dirty")
PREDICTION_DIRTY = ("trajectory_dirty", "prediction_dirty")


class ShadowPayloadRejected(ValueError):
    """Raised when a payload violates the shadow ordering contract."""


@dataclass
class _ZoneRuntime:
    interpreter: InteractionInterpreter
    state: Any


class PassiveShadowRuntimeHandler:
    """Consume immutable shadow payloads into an internal snapshot store."""

    def __init__(
        self,
        *,
        store: SnapshotStore | None = None,
        geometry_adapter: GeometrySnapshotAdapter | None = None,
        row_adapter: RowMechanicsAdapter | None = None,
        open_visit_adapter: OpenVisitAdapter | None = None,
        completed_visit_adapter: LastCompletedVisitAdapter | None = None,
        dynamic_adapter: DynamicMechanicsAdapter | None = None,
        prediction_adapter: PredictionAdapter | None = None,
    ) -> None:
        self.store = store or SnapshotStore()
        self._geometry_adapter = geometry_adapter or GeometrySnapshotAdapter()
        self._row_adapter = row_adapter or RowMechanicsAdapter()
        self._open_adapter = open_visit_adapter or OpenVisitAdapter()
        self._completed_adapter = completed_visit_adapter or LastCompletedVisitAdapter()
        self._dynamic_adapter = dynamic_adapter or DynamicMechanicsAdapter()
        self._prediction_adapter = prediction_adapter or PredictionAdapter()
        self._zones: dict[str, _ZoneRuntime] = {}

    def __call__(self, payload: Any) -> None:
        data = _payload_mapping(payload)
        global_key = str(data.get("global_zone_key", "")).strip()
        session_id = str(data.get("session_id", "")).strip()
        zone_id = str(data.get("zone_id", "")).strip()
        if not global_key or not session_id or not zone_id:
            raise ShadowPayloadRejected("payload identity is incomplete")

        geometry = _mapping(data.get("geometry"))
        runtime = self._zones.get(global_key)
        if runtime is None:
            lower, upper = _geometry_edges(geometry)
            interpreter = InteractionInterpreter(zone_id, lower, upper)
            runtime = _ZoneRuntime(interpreter, interpreter.initial_state())

        rows = tuple(data.get("rows") or ())
        if not rows:
            raise ShadowPayloadRejected("payload contains no rows")

        candidate_state = runtime.state
        pending: list[tuple[RefreshPlan, tuple[Mapping[str, Any], ...]]] = []
        for raw_row in rows:
            row = _mapping(raw_row)
            row_index = _first(row, "row_index", "row_id")
            timestamp = _first(row, "timestamp", "market_timestamp")
            price = _first(row, "price", "close")
            interpreted = runtime.interpreter.interpret_in_order(
                candidate_state,
                row_index=row_index,
                timestamp=timestamp,
                price=price,
                return_eligible=bool(row.get("return_eligible", False)),
            )
            if interpreted.status != ORDER_ACCEPTED:
                raise ShadowPayloadRejected(interpreted.status)
            candidate_state = interpreted.state
            if not interpreted.events:
                continue

            context = DispatchContext(
                session_id=session_id,
                zone_id=zone_id,
                row_index=row_index,
                timestamp=timestamp,
                global_zone_key=global_key,
                geometry_version=str(data.get("geometry_version", "")),
            )
            dispatch = EventDispatcher().dispatch(
                DispatchBatch.from_events(context, candidate_state, interpreted.events)
            )
            if dispatch.status != "DISPATCHED_SHADOW":
                raise ShadowPayloadRejected(dispatch.error_code or dispatch.status)
            plan = dispatch.coordinator_result.plan
            patches = self._build_patches(
                plan,
                row,
                candidate_state,
                data,
                interpreted.events,
                include_geometry=(
                    self.store.get_current(global_key) is None and not pending
                ),
            )
            if patches:
                pending.append((plan, patches))

        # Build all patches before publication. Adapter failure publishes nothing.
        for plan, patches in pending:
            if self.store.get_current(global_key) is None:
                self.store.create(plan, patches, global_zone_key=global_key)
            else:
                self.store.update(plan, patches, global_zone_key=global_key)
        self._zones[global_key] = _ZoneRuntime(runtime.interpreter, candidate_state)

    def _build_patches(
        self,
        plan: RefreshPlan,
        row: Mapping[str, Any],
        state: Any,
        payload: Mapping[str, Any],
        events: tuple[Any, ...],
        *,
        include_geometry: bool,
    ) -> tuple[Mapping[str, Any], ...]:
        patches: list[Mapping[str, Any]] = []
        if include_geometry:
            geometry = dict(_mapping(payload.get("geometry")))
            geometry.update(
                {
                    "geometry_version": payload.get("geometry_version"),
                    "zone_id": payload.get("zone_id"),
                    "episode_id": payload.get("episode_id"),
                }
            )
            patches.append(self._geometry_adapter.build_patch(geometry))
            patches.append(
                {"metadata": {"session_id": payload.get("session_id"), "episode_id": payload.get("episode_id")}}
            )
        if _any(plan, ROW_DIRTY):
            patches.append(self._row_adapter.build_patch(row))
        if _any(plan, OPEN_VISIT_DIRTY):
            open_source = asdict(state)
            open_source.update(row)
            patches.append(self._open_adapter.build_patch(open_source))

        completed = _latest(payload.get("visit_timeline"))
        if _all(plan, COMPLETED_VISIT_DIRTY):
            if completed is None:
                completed = dict(events[-1].evidence)
                completed["visit_id"] = events[-1].visit_id
            patches.append(self._completed_adapter.build_patch(completed))
        if _all(plan, DYNAMIC_DIRTY) and completed is not None:
            patches.append(self._dynamic_adapter.build_patch(completed))
        prediction = _latest(payload.get("prediction"))
        if _all(plan, PREDICTION_DIRTY) and prediction is not None:
            patches.append(self._prediction_adapter.build_patch(prediction))

        sections = [next(iter(patch)) for patch in patches]
        if len(sections) != len(set(sections)):
            raise ValueError("conflicting snapshot patch sections")
        return tuple(patches)


def _payload_mapping(payload: Any) -> Mapping[str, Any]:
    if isinstance(payload, Mapping):
        return payload
    to_dict = getattr(payload, "to_dict", None)
    value = to_dict() if callable(to_dict) else None
    if isinstance(value, Mapping):
        return value
    raise ShadowPayloadRejected("payload must be mapping-compatible")


def _mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ShadowPayloadRejected("payload section must be a mapping")
    return value


def _first(source: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in source and source[name] not in (None, ""):
            return source[name]
    raise ShadowPayloadRejected(f"missing required field: {'/'.join(names)}")


def _geometry_edges(geometry: Mapping[str, Any]) -> tuple[Any, Any]:
    lower = _first(geometry, "interaction_core_lower_edge", "active_core_low", "formation_lower_edge", "formation_low")
    upper = _first(geometry, "interaction_core_upper_edge", "active_core_high", "formation_upper_edge", "formation_high")
    return lower, upper


def _latest(value: Any) -> Mapping[str, Any] | None:
    if not isinstance(value, (list, tuple)) or not value:
        return None
    return value[-1] if isinstance(value[-1], Mapping) else None


def _any(plan: RefreshPlan, names: tuple[str, ...]) -> bool:
    return any(bool(getattr(plan.dirty_flags, name)) for name in names)


def _all(plan: RefreshPlan, names: tuple[str, ...]) -> bool:
    return all(bool(getattr(plan.dirty_flags, name)) for name in names)


__all__ = ["PassiveShadowRuntimeHandler", "ShadowPayloadRejected"]

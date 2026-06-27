"""Shadow-only transport for normalized mechanical events.

The dispatcher validates and deduplicates one zone-row event batch, then
passes the accepted events to the shadow MechanicalRefreshCoordinator. It
does not calculate mechanics, persist events, write snapshots, or integrate
with any production path.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from threading import RLock
from typing import Any, Iterable

from core.interaction_interpreter import (
    InteractionState,
    MechanicalEvent,
    SUPPORTED_EVENT_TYPES,
)
from core.mechanical_refresh_coordinator import (
    MechanicalRefreshCoordinator,
    RefreshResult,
)


EVENT_ORDER = (
    "TOUCH",
    "ZONE_ENTER",
    "VISIT_STARTED",
    "RETURN",
    "PENETRATION_UPDATED",
    "ZONE_EXIT",
    "VISIT_COMPLETED",
)
_EVENT_RANK = {event_type: rank for rank, event_type in enumerate(EVENT_ORDER)}


@dataclass(frozen=True)
class DispatchContext:
    session_id: str
    zone_id: str
    row_index: Any
    timestamp: Any
    global_zone_key: str = ""
    geometry_version: str = ""

    def __post_init__(self) -> None:
        if not str(self.session_id).strip():
            raise ValueError("session_id must not be empty")
        if not str(self.zone_id).strip():
            raise ValueError("zone_id must not be empty")
        if self.row_index is None:
            raise ValueError("row_index must not be None")
        if self.timestamp is None:
            raise ValueError("timestamp must not be None")


@dataclass(frozen=True)
class DispatchBatch:
    context: DispatchContext
    interaction_state: InteractionState
    events: tuple[MechanicalEvent, ...]
    batch_id: str = ""

    @classmethod
    def from_events(
        cls,
        context: DispatchContext,
        interaction_state: InteractionState,
        events: Iterable[MechanicalEvent],
        *,
        batch_id: str = "",
    ) -> "DispatchBatch":
        return cls(
            context=context,
            interaction_state=interaction_state,
            events=tuple(events),
            batch_id=batch_id,
        )

    @property
    def resolved_batch_id(self) -> str:
        if self.batch_id:
            return self.batch_id
        return (
            f"SHADOW_DISPATCH:{self.context.session_id}:"
            f"{self.context.zone_id}:{self.context.row_index}"
        )


@dataclass(frozen=True)
class DispatchResult:
    batch_id: str
    status: str
    accepted_event_ids: tuple[str, ...]
    duplicate_event_ids: tuple[str, ...]
    rejected_event_ids: tuple[str, ...]
    coordinator_result: RefreshResult | None
    error_code: str = ""
    error_message: str = ""
    audit_trace: tuple[str, ...] = ()
    shadow_only: bool = True
    production_effects: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["coordinator_result"] = (
            self.coordinator_result.to_dict()
            if self.coordinator_result is not None
            else None
        )
        return payload


class EventDispatcher:
    """Validate and dispatch Stage 1 events to the shadow coordinator."""

    def __init__(
        self,
        coordinator: MechanicalRefreshCoordinator | None = None,
    ) -> None:
        self._coordinator = coordinator or MechanicalRefreshCoordinator()
        self._acknowledged_events: dict[str, tuple[Any, ...]] = {}
        self._lock = RLock()

    def dispatch(self, batch: DispatchBatch) -> DispatchResult:
        with self._lock:
            audit = [
                f"batch={batch.resolved_batch_id}",
                f"zone={batch.context.zone_id}",
                f"row={batch.context.row_index}",
                f"events_received={len(batch.events)}",
            ]

            identity_error = self._validate_identity(batch)
            if identity_error is not None:
                code, message = identity_error
                audit.append(f"rejected={code}:{message}")
                return self._rejected_result(batch, code, message, audit)

            unique_events, duplicate_ids, collision_error = (
                self._deduplicate(batch.events)
            )
            audit.append(f"duplicates_skipped={len(duplicate_ids)}")
            if collision_error is not None:
                code, message, rejected_id = collision_error
                audit.append(f"rejected={code}:{message}")
                return self._rejected_result(
                    batch,
                    code,
                    message,
                    audit,
                    rejected_ids=(rejected_id,),
                    duplicate_ids=duplicate_ids,
                )

            ordering_error = self._validate_order(unique_events)
            if ordering_error is not None:
                code, message = ordering_error
                audit.append(f"rejected={code}:{message}")
                return self._rejected_result(
                    batch,
                    code,
                    message,
                    audit,
                    rejected_ids=tuple(
                        event.event_id for event in unique_events
                    ),
                    duplicate_ids=duplicate_ids,
                )

            if not unique_events:
                audit.append("result=DUPLICATE_ONLY; coordinator_not_called")
                return DispatchResult(
                    batch_id=batch.resolved_batch_id,
                    status="DUPLICATE_ONLY",
                    accepted_event_ids=(),
                    duplicate_event_ids=duplicate_ids,
                    rejected_event_ids=(),
                    coordinator_result=None,
                    audit_trace=tuple(audit),
                )

            try:
                coordinator_result = self._coordinator.coordinate(
                    batch.interaction_state,
                    unique_events,
                )
            except Exception as error:
                message = f"{type(error).__name__}: {error}"
                audit.append(f"coordinator_error={message}")
                return DispatchResult(
                    batch_id=batch.resolved_batch_id,
                    status="COORDINATOR_ERROR",
                    accepted_event_ids=(),
                    duplicate_event_ids=duplicate_ids,
                    rejected_event_ids=tuple(
                        event.event_id for event in unique_events
                    ),
                    coordinator_result=None,
                    error_code="COORDINATOR_ERROR",
                    error_message=message,
                    audit_trace=tuple(audit),
                )

            for event in unique_events:
                self._acknowledged_events[event.event_id] = (
                    self._event_fingerprint(event)
                )

            accepted_ids = tuple(event.event_id for event in unique_events)
            audit.append(f"accepted={len(accepted_ids)}")
            audit.append("coordinator=PLANNED_NOT_EXECUTED")
            audit.append("mode=SHADOW_ONLY; production_effects=false")
            return DispatchResult(
                batch_id=batch.resolved_batch_id,
                status="DISPATCHED_SHADOW",
                accepted_event_ids=accepted_ids,
                duplicate_event_ids=duplicate_ids,
                rejected_event_ids=(),
                coordinator_result=coordinator_result,
                audit_trace=tuple(audit),
            )

    def reset_shadow_acknowledgements(self) -> None:
        """Clear only the dispatcher's in-memory shadow deduplication ledger."""

        with self._lock:
            self._acknowledged_events.clear()

    def _validate_identity(
        self,
        batch: DispatchBatch,
    ) -> tuple[str, str] | None:
        context = batch.context
        state = batch.interaction_state
        if state.zone_id != context.zone_id:
            return (
                "STATE_ZONE_MISMATCH",
                "InteractionState zone does not match DispatchContext",
            )

        for event in batch.events:
            if event.event_type not in SUPPORTED_EVENT_TYPES:
                return (
                    "UNSUPPORTED_EVENT",
                    f"Unsupported event type: {event.event_type}",
                )
            if event.event_type not in _EVENT_RANK:
                return (
                    "UNORDERED_EVENT_TYPE",
                    f"No ordering rank for event type: {event.event_type}",
                )
            if event.zone_id != context.zone_id:
                return (
                    "EVENT_ZONE_MISMATCH",
                    f"Event {event.event_id} belongs to {event.zone_id}",
                )
            if event.row_index != context.row_index:
                return (
                    "EVENT_ROW_MISMATCH",
                    f"Event {event.event_id} row does not match context",
                )
            if event.timestamp != context.timestamp:
                return (
                    "EVENT_TIMESTAMP_MISMATCH",
                    f"Event {event.event_id} timestamp does not match context",
                )
        return None

    def _deduplicate(
        self,
        events: tuple[MechanicalEvent, ...],
    ) -> tuple[
        tuple[MechanicalEvent, ...],
        tuple[str, ...],
        tuple[str, str, str] | None,
    ]:
        unique: list[MechanicalEvent] = []
        duplicate_ids: list[str] = []
        seen: dict[str, tuple[Any, ...]] = {}

        for event in events:
            fingerprint = self._event_fingerprint(event)
            prior = seen.get(event.event_id)
            if prior is None:
                prior = self._acknowledged_events.get(event.event_id)
            if prior is not None:
                if prior != fingerprint:
                    return (
                        tuple(unique),
                        tuple(duplicate_ids),
                        (
                            "EVENT_ID_COLLISION",
                            (
                                f"Event ID {event.event_id} was reused with "
                                "different content"
                            ),
                            event.event_id,
                        ),
                    )
                duplicate_ids.append(event.event_id)
                continue
            seen[event.event_id] = fingerprint
            unique.append(event)

        return tuple(unique), tuple(duplicate_ids), None

    @staticmethod
    def _validate_order(
        events: tuple[MechanicalEvent, ...],
    ) -> tuple[str, str] | None:
        ranks = [_EVENT_RANK[event.event_type] for event in events]
        if ranks != sorted(ranks):
            sequence = " -> ".join(event.event_type for event in events)
            return (
                "INVALID_EVENT_ORDER",
                f"Event sequence is not monotonic: {sequence}",
            )
        return None

    @staticmethod
    def _event_fingerprint(event: MechanicalEvent) -> tuple[Any, ...]:
        return (
            event.event_type,
            event.zone_id,
            event.row_index,
            event.timestamp,
            event.price,
            event.visit_id,
            event.inside_zone,
            event.touching_zone,
            event.distance_to_zone,
            event.penetration_depth,
            event.penetration_ratio,
            event.previous_inside_zone,
            repr(sorted(event.evidence.items())),
        )

    @staticmethod
    def _rejected_result(
        batch: DispatchBatch,
        code: str,
        message: str,
        audit: list[str],
        *,
        rejected_ids: tuple[str, ...] | None = None,
        duplicate_ids: tuple[str, ...] = (),
    ) -> DispatchResult:
        return DispatchResult(
            batch_id=batch.resolved_batch_id,
            status="REJECTED",
            accepted_event_ids=(),
            duplicate_event_ids=duplicate_ids,
            rejected_event_ids=(
                rejected_ids
                if rejected_ids is not None
                else tuple(event.event_id for event in batch.events)
            ),
            coordinator_result=None,
            error_code=code,
            error_message=message,
            audit_trace=tuple(audit),
        )


__all__ = [
    "DispatchBatch",
    "DispatchContext",
    "DispatchResult",
    "EVENT_ORDER",
    "EventDispatcher",
]

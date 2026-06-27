"""Pure geometry-to-interaction event interpreter.

Stage 1 is shadow-only. The module has no file I/O, global state, live-pipeline
imports, or production consumers. Given one immutable prior state and one
market observation, it returns a new state and normalized interaction events.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Mapping


SUPPORTED_EVENT_TYPES = frozenset(
    {
        "TOUCH",
        "ZONE_ENTER",
        "ZONE_EXIT",
        "RETURN",
        "PENETRATION_UPDATED",
        "VISIT_STARTED",
        "VISIT_COMPLETED",
    }
)


@dataclass(frozen=True)
class MechanicalEvent:
    event_id: str
    event_type: str
    zone_id: str
    row_index: Any
    timestamp: Any
    price: float
    visit_id: str
    inside_zone: bool
    touching_zone: bool
    distance_to_zone: float
    penetration_depth: float
    penetration_ratio: float
    previous_inside_zone: bool
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = dict(self.evidence)
        return payload


@dataclass(frozen=True)
class InteractionState:
    zone_id: str
    previous_row_index: Any = None
    previous_timestamp: Any = None
    previous_price: float | None = None
    inside_zone: bool = False
    touching_zone: bool = False
    active_visit_id: str = ""
    active_visit_index: int = 0
    visit_start_row: Any = None
    visit_start_timestamp: Any = None
    visit_start_price: float | None = None
    visit_row_count: int = 0
    inactive_row_count: int = 0
    last_active_row: Any = None
    last_active_timestamp: Any = None
    last_active_price: float | None = None
    visit_max_penetration: float = 0.0
    visit_max_penetration_ratio: float = 0.0
    completed_visit_count: int = 0
    return_count: int = 0
    last_penetration_depth: float = 0.0


class InteractionInterpreter:
    """Interpret spatial changes against one fixed zone geometry."""

    def __init__(
        self,
        zone_id: str,
        lower_edge: float,
        upper_edge: float,
        *,
        touch_tolerance: float | None = None,
        penetration_epsilon: float = 1e-9,
        visit_lull_rows: int = 3,
    ) -> None:
        self.zone_id = str(zone_id).strip()
        self.lower_edge = _finite_float(lower_edge, "lower_edge")
        self.upper_edge = _finite_float(upper_edge, "upper_edge")
        if not self.zone_id:
            raise ValueError("zone_id must not be empty")
        if self.upper_edge <= self.lower_edge:
            raise ValueError("upper_edge must be greater than lower_edge")

        self.width = self.upper_edge - self.lower_edge
        self.midpoint = (self.upper_edge + self.lower_edge) / 2.0
        self.touch_tolerance = (
            _finite_non_negative(touch_tolerance, "touch_tolerance")
            if touch_tolerance is not None
            else None
        )
        self.penetration_epsilon = _finite_non_negative(
            penetration_epsilon,
            "penetration_epsilon",
        )
        if int(visit_lull_rows) < 1:
            raise ValueError("visit_lull_rows must be at least 1")
        self.visit_lull_rows = int(visit_lull_rows)

    def initial_state(self) -> InteractionState:
        return InteractionState(zone_id=self.zone_id)

    def interpret(
        self,
        state: InteractionState,
        *,
        row_index: Any,
        timestamp: Any,
        price: float,
        return_eligible: bool = False,
    ) -> tuple[InteractionState, tuple[MechanicalEvent, ...]]:
        if state.zone_id != self.zone_id:
            raise ValueError("InteractionState belongs to a different zone")

        price_value = _finite_float(price, "price")
        inside = self.lower_edge <= price_value <= self.upper_edge
        distance = (
            0.0
            if inside
            else min(
                abs(price_value - self.lower_edge),
                abs(price_value - self.upper_edge),
            )
        )
        tolerance = (
            self.touch_tolerance
            if self.touch_tolerance is not None
            else max(self.width * 0.05, max(price_value, 1.0) * 0.00005)
        )
        touching = inside or distance <= tolerance
        penetration = (
            max(self.width / 2.0 - abs(price_value - self.midpoint), 0.0)
            if inside
            else 0.0
        )
        penetration_ratio = penetration / self.width

        entering = inside and not state.inside_zone
        exiting = state.inside_zone and not inside
        touch_started = touching and not state.touching_zone
        visit_started = touching and not state.active_visit_id

        events: list[MechanicalEvent] = []
        event_sequence = 0

        active_visit_index = state.active_visit_index
        active_visit_id = state.active_visit_id
        visit_start_row = state.visit_start_row
        visit_start_timestamp = state.visit_start_timestamp
        visit_start_price = state.visit_start_price
        visit_row_count = state.visit_row_count
        inactive_row_count = state.inactive_row_count
        last_active_row = state.last_active_row
        last_active_timestamp = state.last_active_timestamp
        last_active_price = state.last_active_price
        visit_max_penetration = state.visit_max_penetration
        visit_max_penetration_ratio = state.visit_max_penetration_ratio
        completed_visit_count = state.completed_visit_count
        return_count = state.return_count

        def emit(
            event_type: str,
            *,
            visit_id: str = "",
            evidence: Mapping[str, Any] | None = None,
        ) -> None:
            nonlocal event_sequence
            event_sequence += 1
            events.append(
                MechanicalEvent(
                    event_id=(
                        f"{self.zone_id}:{row_index}:{event_type}:"
                        f"{event_sequence:02d}"
                    ),
                    event_type=event_type,
                    zone_id=self.zone_id,
                    row_index=row_index,
                    timestamp=timestamp,
                    price=price_value,
                    visit_id=visit_id,
                    inside_zone=inside,
                    touching_zone=touching,
                    distance_to_zone=distance,
                    penetration_depth=penetration,
                    penetration_ratio=penetration_ratio,
                    previous_inside_zone=state.inside_zone,
                    evidence=dict(evidence or {}),
                )
            )

        if touch_started:
            emit(
                "TOUCH",
                visit_id=active_visit_id,
                evidence={"touch_tolerance": tolerance},
            )

        if visit_started:
            active_visit_index = (
                max(state.active_visit_index, state.completed_visit_count) + 1
            )
            active_visit_id = f"{self.zone_id}:V{active_visit_index:06d}"
            visit_start_row = row_index
            visit_start_timestamp = timestamp
            visit_start_price = price_value
            visit_row_count = 0
            inactive_row_count = 0
            visit_max_penetration = 0.0
            visit_max_penetration_ratio = 0.0

            if entering:
                emit("ZONE_ENTER", visit_id=active_visit_id)
            emit(
                "VISIT_STARTED",
                visit_id=active_visit_id,
                evidence={"visit_index": active_visit_index},
            )

            is_return = bool(
                return_eligible or state.completed_visit_count > 0
            )
            if is_return:
                return_count += 1
                emit(
                    "RETURN",
                    visit_id=active_visit_id,
                    evidence={"return_count": return_count},
                )

        elif entering:
            emit("ZONE_ENTER", visit_id=active_visit_id)

        if touching:
            visit_row_count += 1
            inactive_row_count = 0
            last_active_row = row_index
            last_active_timestamp = timestamp
            last_active_price = price_value

        if inside:
            visit_max_penetration = max(
                visit_max_penetration,
                penetration,
            )
            visit_max_penetration_ratio = max(
                visit_max_penetration_ratio,
                penetration_ratio,
            )
            if (
                entering
                or abs(penetration - state.last_penetration_depth)
                > self.penetration_epsilon
            ):
                emit(
                    "PENETRATION_UPDATED",
                    visit_id=active_visit_id,
                    evidence={
                        "previous_penetration_depth": (
                            state.last_penetration_depth
                        ),
                        "visit_max_penetration": visit_max_penetration,
                    },
                )

        if exiting:
            emit("ZONE_EXIT", visit_id=active_visit_id)

        if active_visit_id and not touching:
            inactive_row_count += 1
        visit_completed = bool(
            active_visit_id
            and not touching
            and inactive_row_count >= self.visit_lull_rows
        )
        if visit_completed:
            closing_visit_id = active_visit_id
            emit(
                "VISIT_COMPLETED",
                visit_id=closing_visit_id,
                evidence={
                    "visit_index": active_visit_index,
                    "visit_start_row": visit_start_row,
                    "visit_start_timestamp": visit_start_timestamp,
                    "visit_start_price": visit_start_price,
                    "visit_end_row": last_active_row,
                    "visit_end_timestamp": last_active_timestamp,
                    "visit_end_price": last_active_price,
                    "completion_confirmed_row": row_index,
                    "completion_confirmed_timestamp": timestamp,
                    "visit_row_count": visit_row_count,
                    "visit_max_penetration": visit_max_penetration,
                    "visit_max_penetration_ratio": visit_max_penetration_ratio,
                    "lull_rows": inactive_row_count,
                },
            )
            completed_visit_count += 1
            active_visit_id = ""
            visit_start_row = None
            visit_start_timestamp = None
            visit_start_price = None
            visit_row_count = 0
            inactive_row_count = 0
            last_active_row = None
            last_active_timestamp = None
            last_active_price = None
            visit_max_penetration = 0.0
            visit_max_penetration_ratio = 0.0

        new_state = replace(
            state,
            previous_row_index=row_index,
            previous_timestamp=timestamp,
            previous_price=price_value,
            inside_zone=inside,
            touching_zone=touching,
            active_visit_id=active_visit_id,
            active_visit_index=active_visit_index,
            visit_start_row=visit_start_row,
            visit_start_timestamp=visit_start_timestamp,
            visit_start_price=visit_start_price,
            visit_row_count=visit_row_count,
            inactive_row_count=inactive_row_count,
            last_active_row=last_active_row,
            last_active_timestamp=last_active_timestamp,
            last_active_price=last_active_price,
            visit_max_penetration=visit_max_penetration,
            visit_max_penetration_ratio=visit_max_penetration_ratio,
            completed_visit_count=completed_visit_count,
            return_count=return_count,
            last_penetration_depth=penetration,
        )
        return new_state, tuple(events)


def _finite_float(value: Any, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must be numeric") from error
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _finite_non_negative(value: Any, field_name: str) -> float:
    result = _finite_float(value, field_name)
    if result < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return result


__all__ = [
    "InteractionInterpreter",
    "InteractionState",
    "MechanicalEvent",
    "SUPPORTED_EVENT_TYPES",
]

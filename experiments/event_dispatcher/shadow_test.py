"""Deterministic Stage 1 shadow test for EventDispatcher."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.event_dispatcher import (
    DispatchBatch,
    DispatchContext,
    EventDispatcher,
)
from core.interaction_interpreter import InteractionInterpreter


def build_entry_batch():
    interpreter = InteractionInterpreter(
        zone_id="DISPATCH_ZONE_1",
        lower_edge=100.0,
        upper_edge=110.0,
        touch_tolerance=0.25,
    )
    state, events = interpreter.interpret(
        interpreter.initial_state(),
        row_index=2,
        timestamp="2026-06-28T00:00:01Z",
        price=100.0,
    )
    context = DispatchContext(
        session_id="BTCUSDT_2026-06-28_230000Z",
        zone_id="DISPATCH_ZONE_1",
        row_index=2,
        timestamp="2026-06-28T00:00:01Z",
        global_zone_key=(
            "BTCUSDT_2026-06-28_230000Z:DISPATCH_ZONE_1"
        ),
        geometry_version="SHADOW_V1",
    )
    return DispatchBatch.from_events(context, state, events)


def main() -> None:
    valid_batch = build_entry_batch()

    valid_dispatcher = EventDispatcher()
    valid = valid_dispatcher.dispatch(valid_batch)
    assert valid.status == "DISPATCHED_SHADOW"
    assert valid.coordinator_result is not None
    assert valid.coordinator_result.status == "PLANNED_NOT_EXECUTED"
    assert valid.production_effects is False
    assert tuple(
        event.event_type for event in valid_batch.events
    ) == (
        "TOUCH",
        "ZONE_ENTER",
        "VISIT_STARTED",
        "PENETRATION_UPDATED",
    )

    duplicate_batch = DispatchBatch.from_events(
        valid_batch.context,
        valid_batch.interaction_state,
        (*valid_batch.events, valid_batch.events[-1]),
        batch_id="SHADOW_DUPLICATE_BATCH",
    )
    duplicate_dispatcher = EventDispatcher()
    duplicate = duplicate_dispatcher.dispatch(duplicate_batch)
    assert duplicate.status == "DISPATCHED_SHADOW"
    assert duplicate.duplicate_event_ids == (
        valid_batch.events[-1].event_id,
    )
    assert len(duplicate.accepted_event_ids) == len(valid_batch.events)

    replayed = valid_dispatcher.dispatch(valid_batch)
    assert replayed.status == "DUPLICATE_ONLY"
    assert replayed.coordinator_result is None
    assert set(replayed.duplicate_event_ids) == {
        event.event_id for event in valid_batch.events
    }

    invalid_order_batch = DispatchBatch.from_events(
        valid_batch.context,
        valid_batch.interaction_state,
        (
            valid_batch.events[-1],
            valid_batch.events[0],
            *valid_batch.events[1:-1],
        ),
        batch_id="SHADOW_INVALID_ORDER_BATCH",
    )
    invalid_order = EventDispatcher().dispatch(invalid_order_batch)
    assert invalid_order.status == "REJECTED"
    assert invalid_order.error_code == "INVALID_EVENT_ORDER"
    assert invalid_order.coordinator_result is None

    mismatched_event = replace(
        valid_batch.events[0],
        zone_id="OTHER_ZONE",
    )
    mismatch_batch = DispatchBatch.from_events(
        valid_batch.context,
        valid_batch.interaction_state,
        (mismatched_event,),
        batch_id="SHADOW_ZONE_MISMATCH_BATCH",
    )
    mismatch = EventDispatcher().dispatch(mismatch_batch)
    assert mismatch.status == "REJECTED"
    assert mismatch.error_code == "EVENT_ZONE_MISMATCH"
    assert mismatch.coordinator_result is None

    print("EVENT_DISPATCHER_SHADOW_TEST = PASS")
    print("VALID_DISPATCH_RESULT")
    print(valid.to_dict())
    print("DUPLICATE_EVENT_IDS")
    print(duplicate.duplicate_event_ids)
    print("INVALID_ORDER")
    print(invalid_order.error_code)
    print("ZONE_MISMATCH")
    print(mismatch.error_code)
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

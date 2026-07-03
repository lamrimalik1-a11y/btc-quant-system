"""Offline Psychological Levels to Event Dispatcher validation."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_DIR = Path(__file__).resolve().parent
for path in (REPO_ROOT, EXPERIMENT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.event_dispatcher import (
    DispatchBatch,
    DispatchContext,
    EventDispatcher,
)
from core.interaction_interpreter import (
    AUDIT_ROW_DUPLICATE,
    AUDIT_ROW_OUT_OF_ORDER,
    ORDER_ACCEPTED,
    InteractionInterpreter,
)
from provider import (
    GEOMETRY_SOURCE,
    GEOMETRY_VERSION,
    PsychologicalLevelsProvider,
)


SESSION_ID = "PSY_DISPATCHER_TEST"
PRICE_PATH = (
    (1, Decimal("60350")),
    (2, Decimal("60376")),
    (3, Decimal("60400")),
    (4, Decimal("60430")),
    (5, Decimal("60435")),
    (6, Decimal("60440")),
    (7, Decimal("60445")),
)


def generated_60400_zone():
    zones = PsychologicalLevelsProvider(
        spacing=Decimal("200"),
        zone_half_width=Decimal("25"),
        active_window=3,
    ).generate(
        price=Decimal("60341"),
        symbol="BTCUSDT",
        market_timestamp="2026-07-03T12:00:00Z",
        session_id=SESSION_ID,
    )
    return next(zone for zone in zones if zone.level_center == 60400)


def run_sequence():
    zone = generated_60400_zone()
    interpreter = InteractionInterpreter(
        zone_id=zone.zone_id,
        lower_edge=zone.lower_edge,
        upper_edge=zone.upper_edge,
        touch_tolerance=5,
        visit_lull_rows=3,
    )
    dispatcher = EventDispatcher()
    state = interpreter.initial_state()
    plans = []
    accepted_event_ids = []

    for row_index, price in PRICE_PATH:
        result = interpreter.interpret_in_order(
            state,
            row_index=row_index,
            timestamp=f"T{row_index}",
            price=price,
        )
        assert result.status == ORDER_ACCEPTED
        state = result.state
        if not result.events:
            continue

        context = DispatchContext(
            session_id=zone.session_id,
            zone_id=zone.zone_id,
            row_index=row_index,
            timestamp=f"T{row_index}",
            global_zone_key=zone.global_zone_key,
            geometry_version=zone.geometry_version,
        )
        dispatched = dispatcher.dispatch(
            DispatchBatch.from_events(
                context,
                state,
                result.events,
            )
        )
        assert dispatched.status == "DISPATCHED_SHADOW"
        assert dispatched.rejected_event_ids == ()
        assert dispatched.duplicate_event_ids == ()
        assert dispatched.accepted_event_ids == tuple(
            event.event_id for event in result.events
        )
        accepted_event_ids.extend(dispatched.accepted_event_ids)
        plans.append(dispatched.coordinator_result.plan)

    return zone, interpreter, state, tuple(plans), tuple(accepted_event_ids)


def test_events_drive_dispatcher() -> None:
    zone, _, _, plans, accepted_ids = run_sequence()
    assert zone.geometry_source == GEOMETRY_SOURCE
    assert GEOMETRY_SOURCE == "PSYCHOLOGICAL_LEVELS_TEST"
    assert zone.geometry_version == GEOMETRY_VERSION
    assert len(accepted_ids) == 7
    assert tuple(plan.event_types for plan in plans) == (
        (
            "TOUCH",
            "ZONE_ENTER",
            "VISIT_STARTED",
            "PENETRATION_UPDATED",
        ),
        ("PENETRATION_UPDATED",),
        ("ZONE_EXIT",),
        ("VISIT_COMPLETED",),
    )
    print("ALL_MECHANICAL_EVENTS_ACCEPTED = PASS")


def test_dirty_flags() -> None:
    _, _, _, plans, _ = run_sequence()
    enter, penetration, exit_plan, completed = plans

    assert set(enter.dirty_flags.active_names()) == {
        "interaction_dirty",
        "stress_dirty",
        "exposure_dirty",
        "fatigue_recovery_dirty",
        "health_dirty",
        "visit_dirty",
        "snapshot_dirty",
    }
    assert set(penetration.dirty_flags.active_names()) == {
        "interaction_dirty",
        "stress_dirty",
        "exposure_dirty",
        "fatigue_recovery_dirty",
        "health_dirty",
        "snapshot_dirty",
    }
    assert set(exit_plan.dirty_flags.active_names()) == {
        "interaction_dirty",
        "snapshot_dirty",
    }
    assert set(completed.dirty_flags.active_names()) == {
        "visit_dirty",
        "response_dirty",
        "state_dirty",
        "transition_dirty",
        "trajectory_dirty",
        "prediction_dirty",
        "snapshot_dirty",
    }
    print("DIRTY_FLAG_MAPPING = PASS")


def test_refresh_plan_determinism() -> None:
    first = run_sequence()[3]
    second = run_sequence()[3]
    assert tuple(plan.to_dict() for plan in first) == tuple(
        plan.to_dict() for plan in second
    )
    print("REFRESH_PLAN_DETERMINISM = PASS")


def test_rejected_rows_create_no_plans() -> None:
    _, interpreter, state, plans, _ = run_sequence()
    original_plan_count = len(plans)

    duplicate = interpreter.interpret_in_order(
        state,
        row_index=7,
        timestamp="T7_DUPLICATE",
        price=Decimal("60445"),
    )
    assert duplicate.status == AUDIT_ROW_DUPLICATE
    assert duplicate.events == ()

    older = interpreter.interpret_in_order(
        state,
        row_index=6,
        timestamp="T6_OLDER",
        price=Decimal("60440"),
    )
    assert older.status == AUDIT_ROW_OUT_OF_ORDER
    assert older.events == ()
    assert original_plan_count == 4
    print("REJECTED_ROWS_CREATE_NO_PLANS = PASS")


def test_no_project1_fields_required() -> None:
    zone, _, _, plans, _ = run_sequence()
    assert zone.geometry_source == "PSYCHOLOGICAL_LEVELS_TEST"
    assert all(plan.zone_id == zone.zone_id for plan in plans)
    assert not hasattr(zone, "preparation_low_price")
    assert not hasattr(zone, "interaction_core_lower_edge")
    assert not hasattr(zone, "interaction_density_lower_band")
    print("NO_PROJECT1_FIELDS_REQUIRED = PASS")


def main() -> None:
    test_events_drive_dispatcher()
    test_dirty_flags()
    test_refresh_plan_determinism()
    test_rejected_rows_create_no_plans()
    test_no_project1_fields_required()
    print("PSYCHOLOGICAL_LEVELS_DISPATCHER_INTEGRATION_TEST = PASS")
    print("OFFLINE_ONLY = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

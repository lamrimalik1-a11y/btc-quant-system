"""Deterministic Interaction Interpreter -> Refresh Coordinator shadow chain.

Research-only validation. No production imports consume this script, and it
does not write files or execute mechanical calculations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.interaction_interpreter import InteractionInterpreter
from core.mechanical_refresh_coordinator import MechanicalRefreshCoordinator


OBSERVATIONS = (
    (1, "2026-06-28T00:00:00Z", 99.0, False),
    (2, "2026-06-28T00:00:01Z", 100.0, False),
    (3, "2026-06-28T00:00:02Z", 105.0, False),
    (4, "2026-06-28T00:00:03Z", 111.0, False),
    (5, "2026-06-28T00:00:04Z", 112.0, False),
    (6, "2026-06-28T00:00:05Z", 113.0, False),
    (7, "2026-06-28T00:00:06Z", 109.0, True),
    (8, "2026-06-28T00:00:07Z", 105.0, False),
    (9, "2026-06-28T00:00:08Z", 111.0, False),
    (10, "2026-06-28T00:00:09Z", 112.0, False),
    (11, "2026-06-28T00:00:10Z", 113.0, False),
)

EXPECTED_EVENTS_BY_ROW = {
    1: (),
    2: (
        "TOUCH",
        "ZONE_ENTER",
        "VISIT_STARTED",
        "PENETRATION_UPDATED",
    ),
    3: ("PENETRATION_UPDATED",),
    4: ("ZONE_EXIT",),
    5: (),
    6: ("VISIT_COMPLETED",),
    7: (
        "TOUCH",
        "ZONE_ENTER",
        "VISIT_STARTED",
        "RETURN",
        "PENETRATION_UPDATED",
    ),
    8: ("PENETRATION_UPDATED",),
    9: ("ZONE_EXIT",),
    10: (),
    11: ("VISIT_COMPLETED",),
}

EXPECTED_FLAGS_BY_EVENT = {
    "TOUCH": {
        "interaction_dirty",
        "stress_dirty",
        "snapshot_dirty",
    },
    "ZONE_ENTER": {
        "interaction_dirty",
        "stress_dirty",
        "snapshot_dirty",
    },
    "ZONE_EXIT": {
        "interaction_dirty",
        "snapshot_dirty",
    },
    "RETURN": {
        "interaction_dirty",
        "stress_dirty",
        "snapshot_dirty",
    },
    "PENETRATION_UPDATED": {
        "interaction_dirty",
        "stress_dirty",
        "exposure_dirty",
        "fatigue_recovery_dirty",
        "health_dirty",
        "snapshot_dirty",
    },
    "VISIT_STARTED": {
        "interaction_dirty",
        "visit_dirty",
        "snapshot_dirty",
    },
    "VISIT_COMPLETED": {
        "visit_dirty",
        "response_dirty",
        "state_dirty",
        "transition_dirty",
        "trajectory_dirty",
        "prediction_dirty",
        "snapshot_dirty",
    },
}


def run_chain() -> tuple[list[dict], list[dict], list[str]]:
    interpreter = InteractionInterpreter(
        zone_id="SHADOW_CHAIN_ZONE",
        lower_edge=100.0,
        upper_edge=110.0,
        touch_tolerance=0.25,
        visit_lull_rows=3,
    )
    coordinator = MechanicalRefreshCoordinator()
    state = interpreter.initial_state()
    event_records: list[dict] = []
    plan_records: list[dict] = []
    mismatches: list[str] = []

    for row_index, timestamp, price, return_eligible in OBSERVATIONS:
        state, events = interpreter.interpret(
            state,
            row_index=row_index,
            timestamp=timestamp,
            price=price,
            return_eligible=return_eligible,
        )
        actual_types = tuple(event.event_type for event in events)
        expected_types = EXPECTED_EVENTS_BY_ROW[row_index]
        if actual_types != expected_types:
            mismatches.append(
                f"row={row_index} events={actual_types} expected={expected_types}"
            )

        result = coordinator.coordinate(state, events)
        plan = result.plan
        expected_flags = set()
        for event_type in actual_types:
            expected_flags.update(EXPECTED_FLAGS_BY_EVENT[event_type])
        actual_flags = set(plan.dirty_flags.active_names())
        if actual_flags != expected_flags:
            mismatches.append(
                f"row={row_index} flags={sorted(actual_flags)} "
                f"expected={sorted(expected_flags)}"
            )
        if result.executed_stages:
            mismatches.append(
                f"row={row_index} unexpectedly executed stages"
            )
        if result.production_effects:
            mismatches.append(
                f"row={row_index} unexpectedly reported production effects"
            )

        event_records.extend(event.to_dict() for event in events)
        plan_record = plan.to_dict()
        plan_record["row_index"] = row_index
        plan_record["status"] = result.status
        plan_records.append(plan_record)

    if state.completed_visit_count != 2:
        mismatches.append(
            "completed_visit_count="
            f"{state.completed_visit_count} expected=2"
        )
    if state.return_count != 1:
        mismatches.append(
            f"return_count={state.return_count} expected=1"
        )

    return event_records, plan_records, mismatches


def main() -> None:
    events_first, plans_first, mismatches_first = run_chain()
    events_second, plans_second, mismatches_second = run_chain()

    mismatches = [*mismatches_first, *mismatches_second]
    if events_first != events_second:
        mismatches.append("event sequence is not deterministic")
    if plans_first != plans_second:
        mismatches.append("refresh plan sequence is not deterministic")

    print("EVENT SEQUENCE")
    for event in events_first:
        print(
            f"row={event['row_index']} "
            f"event={event['event_type']} "
            f"visit={event['visit_id'] or '-'}"
        )

    print("\nREFRESH PLAN SEQUENCE")
    for plan in plans_first:
        flags = [
            name
            for name, enabled in plan["dirty_flags"].items()
            if enabled
        ]
        print(
            f"row={plan['row_index']} "
            f"events={list(plan['event_types'])} "
            f"dirty={flags} "
            f"plan={list(plan['execution_order'])}"
        )

    print("\nMISMATCHES")
    if mismatches:
        for mismatch in mismatches:
            print(mismatch)
    else:
        print("NONE")

    assert not mismatches, json.dumps(mismatches, indent=2)
    print("\nSHADOW_CHAIN_TEST = PASS")
    print("DETERMINISTIC_REPLAY = PASS")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

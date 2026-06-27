"""Synthetic Stage 1 test for refresh planning and audit traces."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.interaction_interpreter import InteractionInterpreter
from core.mechanical_refresh_coordinator import MechanicalRefreshCoordinator


def collect_events(interpreter, state, observations):
    events = []
    for row_index, timestamp, price, return_eligible in observations:
        state, emitted = interpreter.interpret(
            state,
            row_index=row_index,
            timestamp=timestamp,
            price=price,
            return_eligible=return_eligible,
        )
        events.extend(emitted)
    return state, tuple(events)


def main() -> None:
    interpreter = InteractionInterpreter(
        zone_id="SHADOW_ZONE_1",
        lower_edge=100.0,
        upper_edge=110.0,
        touch_tolerance=0.25,
    )
    state, events = collect_events(
        interpreter,
        interpreter.initial_state(),
        [
            (1, "2026-06-28T00:00:00Z", 99.0, False),
            (2, "2026-06-28T00:00:01Z", 100.0, False),
            (3, "2026-06-28T00:00:02Z", 105.0, False),
            (4, "2026-06-28T00:00:03Z", 111.0, False),
            (5, "2026-06-28T00:00:04Z", 112.0, False),
            (6, "2026-06-28T00:00:05Z", 113.0, False),
        ],
    )

    coordinator = MechanicalRefreshCoordinator()
    result = coordinator.coordinate(state, events)
    flags = result.plan.dirty_flags

    assert flags.interaction_dirty
    assert flags.stress_dirty
    assert flags.exposure_dirty
    assert flags.fatigue_recovery_dirty
    assert flags.health_dirty
    assert flags.visit_dirty
    assert flags.response_dirty
    assert flags.state_dirty
    assert flags.transition_dirty
    assert flags.trajectory_dirty
    assert flags.prediction_dirty
    assert flags.snapshot_dirty
    assert not flags.geometry_dirty
    assert not flags.damage_dirty
    assert not flags.closure_dirty

    assert result.status == "PLANNED_NOT_EXECUTED"
    assert result.executed_stages == ()
    assert result.skipped_stages == result.plan.execution_order
    assert "snapshot_refresh" == result.plan.execution_order[-1]
    assert any(
        entry.startswith("event=")
        for entry in result.audit_trace
    )
    assert result.production_effects is False

    penetration_event = next(
        event
        for event in events
        if event.event_type == "PENETRATION_UPDATED"
    )
    duplicate_plan = coordinator.create_plan(
        state,
        [penetration_event, penetration_event],
    )
    assert "duplicate_events_skipped=1" in duplicate_plan.audit_trace

    print("SHADOW_REFRESH_TEST = PASS")
    print(result.plan.to_dict())
    print("AUDIT_TRACE")
    for entry in result.audit_trace:
        print(entry)


if __name__ == "__main__":
    main()

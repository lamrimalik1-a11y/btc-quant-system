"""Synthetic shadow test for the Stage 1 Interaction Interpreter."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.interaction_interpreter import InteractionInterpreter


def main() -> None:
    interpreter = InteractionInterpreter(
        zone_id="SHADOW_ZONE_1",
        lower_edge=100.0,
        upper_edge=110.0,
        touch_tolerance=0.25,
    )
    state = interpreter.initial_state()

    observations = [
        (1, "2026-06-28T00:00:00Z", 99.0, False),
        (2, "2026-06-28T00:00:01Z", 100.0, False),
        (3, "2026-06-28T00:00:02Z", 105.0, False),
        (4, "2026-06-28T00:00:03Z", 111.0, False),
        (5, "2026-06-28T00:00:04Z", 112.0, False),
        (6, "2026-06-28T00:00:05Z", 113.0, False),
        (7, "2026-06-28T00:00:06Z", 109.0, True),
    ]

    emitted = []
    for row_index, timestamp, price, return_eligible in observations:
        state, events = interpreter.interpret(
            state,
            row_index=row_index,
            timestamp=timestamp,
            price=price,
            return_eligible=return_eligible,
        )
        emitted.extend(events)

    event_types = [event.event_type for event in emitted]
    expected = [
        "TOUCH",
        "ZONE_ENTER",
        "VISIT_STARTED",
        "PENETRATION_UPDATED",
        "PENETRATION_UPDATED",
        "ZONE_EXIT",
        "VISIT_COMPLETED",
        "TOUCH",
        "ZONE_ENTER",
        "VISIT_STARTED",
        "RETURN",
        "PENETRATION_UPDATED",
    ]
    assert event_types == expected, (event_types, expected)
    assert state.active_visit_index == 2
    assert state.completed_visit_count == 1
    assert state.return_count == 1

    print("SHADOW_TEST = PASS")
    for event in emitted:
        print(event.to_dict())


if __name__ == "__main__":
    main()

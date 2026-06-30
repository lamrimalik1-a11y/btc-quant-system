"""Shadow test for the Interaction Interpreter Row Ordering Contract.

Validates interpret_in_order():
  1. Normal increasing rows           -> ACCEPTED.
  2. Duplicate row (==)               -> ROW_DUPLICATE, no transition.
  3. Older row (<)                    -> ROW_OUT_OF_ORDER, no transition.
  4. Equal timestamps, increasing row -> ACCEPTED (ordering uses row_index only).
  5. State unchanged after rejected rows (identity-preserved).
  6. No events generated after rejection.
Ordering uses row_index ONLY; timestamp is informational. Shadow-only.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.interaction_interpreter import (
    AUDIT_ROW_DUPLICATE,
    AUDIT_ROW_OUT_OF_ORDER,
    ORDER_ACCEPTED,
    InteractionInterpreter,
)


def main() -> None:
    interp = InteractionInterpreter(
        zone_id="ORDER_ZONE_1",
        lower_edge=100.0,
        upper_edge=110.0,
        touch_tolerance=0.25,
    )
    state = interp.initial_state()

    # 1. Normal increasing rows -> ACCEPTED.
    r1 = interp.interpret_in_order(state, row_index=1, timestamp="t1", price=105.0)
    assert r1.status == ORDER_ACCEPTED, r1.status
    assert r1.audit == ()
    state = r1.state
    assert state.previous_row_index == 1

    r2 = interp.interpret_in_order(state, row_index=2, timestamp="t2", price=106.0)
    assert r2.status == ORDER_ACCEPTED, r2.status
    state = r2.state
    assert state.previous_row_index == 2
    state_after_2 = state  # snapshot for identity checks

    # 2. Duplicate row (row_index == previous) -> ROW_DUPLICATE, no transition.
    dup = interp.interpret_in_order(state, row_index=2, timestamp="t2b", price=120.0)
    assert dup.status == AUDIT_ROW_DUPLICATE, dup.status
    assert dup.audit == (AUDIT_ROW_DUPLICATE,)
    assert dup.events == ()                      # (6) no events after rejection
    assert dup.state is state_after_2            # (5) state identity preserved
    assert dup.state.previous_row_index == 2

    # 3. Older row (row_index < previous) -> ROW_OUT_OF_ORDER, no transition.
    old = interp.interpret_in_order(state, row_index=1, timestamp="t0", price=130.0)
    assert old.status == AUDIT_ROW_OUT_OF_ORDER, old.status
    assert old.audit == (AUDIT_ROW_OUT_OF_ORDER,)
    assert old.events == ()                      # (6) no events after rejection
    assert old.state is state_after_2            # (5) state identity preserved
    assert old.state.previous_row_index == 2

    # State must be usable, unchanged, for the next VALID row after rejections.
    assert state is state_after_2

    # 4. Equal timestamps but increasing row_index -> ACCEPTED for both.
    r3 = interp.interpret_in_order(state, row_index=3, timestamp="SAME_TS", price=107.0)
    assert r3.status == ORDER_ACCEPTED, r3.status
    state = r3.state
    r4 = interp.interpret_in_order(state, row_index=4, timestamp="SAME_TS", price=108.0)
    assert r4.status == ORDER_ACCEPTED, r4.status   # same timestamp, higher row -> valid
    state = r4.state
    assert state.previous_row_index == 4

    # The pure interpret() transition is unchanged and still callable directly.
    raw_state, raw_events = interp.interpret(
        state, row_index=5, timestamp="t5", price=109.0
    )
    assert raw_state.previous_row_index == 5
    _ = raw_events

    print("INTERPRETER_ROW_ORDERING_SHADOW_TEST = PASS")
    print("CASE_1_NORMAL_INCREASING", r1.status, r2.status)
    print("CASE_2_DUPLICATE", dup.status, dup.audit)
    print("CASE_3_OUT_OF_ORDER", old.status, old.audit)
    print("CASE_4_EQUAL_TS_INCREASING_ROW", r3.status, r4.status)
    print("CASE_5_STATE_UNCHANGED_AFTER_REJECT", dup.state is state_after_2 and old.state is state_after_2)
    print("CASE_6_NO_EVENTS_AFTER_REJECT", dup.events == () and old.events == ())
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

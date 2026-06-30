"""Shadow test for copy-on-write canonical snapshot revisions."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.canonical_snapshot import SnapshotStore
from core.interaction_interpreter import InteractionInterpreter
from core.mechanical_refresh_coordinator import MechanicalRefreshCoordinator


# Session-scoped canonical identity (same contract as the Event Dispatcher).
GLOBAL_KEY = "BTCUSDT_2026-06-28_230000Z::SNAPSHOT_ZONE_1"


def make_plan(row_index: int, timestamp: str, price: float):
    interpreter = InteractionInterpreter(
        zone_id="SNAPSHOT_ZONE_1",
        lower_edge=100.0,
        upper_edge=110.0,
        touch_tolerance=0.25,
    )
    state, events = interpreter.interpret(
        interpreter.initial_state(),
        row_index=row_index,
        timestamp=timestamp,
        price=price,
    )
    return MechanicalRefreshCoordinator().create_plan(state, events)


def main() -> None:
    store = SnapshotStore()
    create_plan = make_plan(
        1,
        "2026-06-28T00:00:00Z",
        100.0,
    )
    first = store.create(
        create_plan,
        (
            {
                "metadata": {
                    "session_id": "BTCUSDT_2026-06-28_230000Z",
                    "market_date": "2026-06-29",
                },
                "geometry": {
                    "lower_edge": 100.0,
                    "upper_edge": 110.0,
                    "width": 10.0,
                },
            },
            {
                "current_row_mechanics": {
                    "row_index": 1,
                    "price": 100.0,
                    "penetration_depth": 0.0,
                },
                "open_visit": {
                    "visit_id": "SNAPSHOT_ZONE_1:V000001",
                    "status": "OPEN",
                    "row_count": 1,
                },
            },
        ),
        global_zone_key=GLOBAL_KEY,
    )

    assert first.revision == 1
    assert first.metadata["zone_id"] == "SNAPSHOT_ZONE_1"
    assert first.geometry["width"] == 10.0
    assert first.open_visit["status"] == "OPEN"
    assert store.get_current(GLOBAL_KEY) is first

    update_plan = make_plan(
        2,
        "2026-06-28T00:00:01Z",
        105.0,
    )
    second = store.update(
        update_plan,
        (
            {
                "current_row_mechanics": {
                    "row_index": 2,
                    "price": 105.0,
                    "penetration_depth": 5.0,
                },
                "open_visit": {
                    "row_count": 2,
                    "max_penetration": 5.0,
                },
            },
        ),
        global_zone_key=GLOBAL_KEY,
    )

    assert second.revision == 2
    assert second.current_row_mechanics["price"] == 105.0
    assert second.open_visit["row_count"] == 2
    assert second.open_visit["status"] == "OPEN"
    assert first.revision == 1
    assert first.current_row_mechanics["price"] == 100.0
    assert store.get_current(GLOBAL_KEY) is second

    try:
        store.update(
            update_plan,
            ({"future_prediction": {"prediction": "NOT_IMPLEMENTED"}},),
            global_zone_key=GLOBAL_KEY,
        )
    except ValueError as error:
        assert "Unsupported snapshot sections" in str(error)
    else:
        raise AssertionError("Invalid update unexpectedly succeeded")

    after_failure = store.get_current(GLOBAL_KEY)
    assert after_failure is second
    assert after_failure.revision == 2
    assert after_failure.current_row_mechanics["price"] == 105.0
    # Identity is the session-scoped global_zone_key; zone_id is metadata only.
    assert after_failure.global_zone_key == GLOBAL_KEY
    assert after_failure.metadata["global_zone_key"] == GLOBAL_KEY

    print("CANONICAL_SNAPSHOT_SHADOW_TEST = PASS")
    print("CREATED_REVISION", first.revision)
    print("UPDATED_REVISION", second.revision)
    print("FAILED_UPDATE_PRESERVED_REVISION", after_failure.revision)
    print("CURRENT_SNAPSHOT")
    print(second.to_dict())
    print("PRODUCTION_EFFECTS = FALSE")


def identity_collision() -> None:
    """Two daily sessions reusing the SAME zone_id must NOT collide.

    Before the identity fix the store keyed by bare zone_id, so Session B's
    create() would raise "Snapshot already exists for zone ZONE_17" (or, with
    update, silently overwrite Session A). With the global_zone_key identity,
    each session owns an independent snapshot under the same zone_id.
    """
    # make_plan() builds a plan whose zone_id is "SNAPSHOT_ZONE_1"; both
    # sessions therefore carry the SAME zone_id (the reuse scenario, mirroring
    # the ZONE_17 example) but DIFFERENT session-scoped global identities.
    store = SnapshotStore()
    session_a = "BTCUSDT_2026-06-28_230000Z"
    session_b = "BTCUSDT_2026-06-29_230000Z"
    reused_zone_id = "SNAPSHOT_ZONE_1"
    key_a = f"{session_a}::{reused_zone_id}"
    key_b = f"{session_b}::{reused_zone_id}"

    plan_a = make_plan(1, "2026-06-28T00:00:00Z", 100.0)
    plan_b = make_plan(1, "2026-06-29T00:00:00Z", 100.0)
    patch_a = ({"metadata": {"session_id": session_a}, "geometry": {"width": 10.0}},)
    patch_b = ({"metadata": {"session_id": session_b}, "geometry": {"width": 20.0}},)

    snap_a = store.create(plan_a, patch_a, global_zone_key=key_a)
    # Same zone_id, different session -> must succeed, no collision/overwrite.
    snap_b = store.create(plan_b, patch_b, global_zone_key=key_b)

    assert snap_a is not snap_b
    assert store.get_current(key_a) is snap_a
    assert store.get_current(key_b) is snap_b
    # Both carry the SAME descriptive zone_id...
    assert snap_a.zone_id == snap_b.zone_id == reused_zone_id
    # ...but DIFFERENT canonical identities, and independent state.
    assert snap_a.global_zone_key == key_a
    assert snap_b.global_zone_key == key_b
    assert snap_a.geometry["width"] == 10.0
    assert snap_b.geometry["width"] == 20.0
    assert snap_a.metadata["session_id"] == session_a
    assert snap_b.metadata["session_id"] == session_b

    print("CANONICAL_SNAPSHOT_IDENTITY_COLLISION_TEST = PASS")
    print("SESSION_A_KEY", snap_a.global_zone_key)
    print("SESSION_B_KEY", snap_b.global_zone_key)
    print("SHARED_ZONE_ID", snap_a.zone_id)
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()
    identity_collision()

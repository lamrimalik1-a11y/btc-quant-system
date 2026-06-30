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
    )

    assert first.revision == 1
    assert first.metadata["zone_id"] == "SNAPSHOT_ZONE_1"
    assert first.geometry["width"] == 10.0
    assert first.open_visit["status"] == "OPEN"
    assert store.get_current("SNAPSHOT_ZONE_1") is first

    update_plan = make_plan(
        2,
        "2026-06-28T00:00:01Z",
        105.0,
    )
    second = store.update(
        "SNAPSHOT_ZONE_1",
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
    )

    assert second.revision == 2
    assert second.current_row_mechanics["price"] == 105.0
    assert second.open_visit["row_count"] == 2
    assert second.open_visit["status"] == "OPEN"
    assert first.revision == 1
    assert first.current_row_mechanics["price"] == 100.0
    assert store.get_current("SNAPSHOT_ZONE_1") is second

    try:
        store.update(
            "SNAPSHOT_ZONE_1",
            update_plan,
            ({"future_prediction": {"prediction": "NOT_IMPLEMENTED"}},),
        )
    except ValueError as error:
        assert "Unsupported snapshot sections" in str(error)
    else:
        raise AssertionError("Invalid update unexpectedly succeeded")

    after_failure = store.get_current("SNAPSHOT_ZONE_1")
    assert after_failure is second
    assert after_failure.revision == 2
    assert after_failure.current_row_mechanics["price"] == 105.0

    print("CANONICAL_SNAPSHOT_SHADOW_TEST = PASS")
    print("CREATED_REVISION", first.revision)
    print("UPDATED_REVISION", second.revision)
    print("FAILED_UPDATE_PRESERVED_REVISION", after_failure.revision)
    print("CURRENT_SNAPSHOT")
    print(second.to_dict())
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

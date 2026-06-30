"""Shadow validation for mapping-only Open Visit adaptation."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.canonical_snapshot import SnapshotStore
from core.interaction_interpreter import InteractionInterpreter
from core.mechanical_refresh_coordinator import MechanicalRefreshCoordinator
from core.open_visit_adapter import OpenVisitAdapter
from core.row_mechanics_adapter import NOT_AVAILABLE


def build_active_state():
    interpreter = InteractionInterpreter(
        zone_id="OPEN_VISIT_ZONE_1",
        lower_edge=100.0,
        upper_edge=110.0,
        touch_tolerance=0.25,
    )
    state, events = interpreter.interpret(
        interpreter.initial_state(),
        row_index=4,
        timestamp="2026-06-28T00:00:03Z",
        price=104.0,
    )
    plan = MechanicalRefreshCoordinator().create_plan(state, events)
    return interpreter, state, plan


def main() -> None:
    adapter = OpenVisitAdapter()
    interpreter, active_state, plan = build_active_state()

    active_patch = adapter.build_patch(active_state)
    active = active_patch["open_visit"]
    assert active["active_visit_flag"] is True
    assert active["visit_id"] == "OPEN_VISIT_ZONE_1:V000001"
    assert active["visit_start_row"] == 4
    assert active["visit_start_timestamp"] == "2026-06-28T00:00:03Z"
    assert active["visit_start_price"] == 104.0
    assert active["current_row_count"] == 1
    assert active["max_penetration"] == 4.0
    assert active["inside_zone"] is True
    assert active["touch_active"] is True
    assert active["visit_status"] == NOT_AVAILABLE
    assert active["cumulative_omega"] == NOT_AVAILABLE

    inactive_patch = adapter.build_patch(interpreter.initial_state())
    inactive = inactive_patch["open_visit"]
    assert inactive["active_visit_flag"] is False
    assert inactive["visit_id"] == NOT_AVAILABLE
    assert inactive["visit_start_row"] == NOT_AVAILABLE
    assert inactive["current_row_count"] == NOT_AVAILABLE
    assert inactive["max_penetration"] == NOT_AVAILABLE
    assert inactive["inside_zone"] is False
    assert inactive["touch_active"] is False

    visit_values = {
        "visit_id": "EXISTING_VISIT",
        "visit_status": "PRECOMPUTED_STATUS",
        "visit_start_row": 10,
        "visit_start_timestamp": "2026-06-28T00:01:00Z",
        "visit_start_price": 101.5,
        "current_row_count": 6,
        "max_penetration": 3.25,
        "cumulative_omega": "PRECOMPUTED_OMEGA",
        "pressure_accumulation": "PRECOMPUTED_PRESSURE",
        "attacker_force_current": "PRECOMPUTED_FORCE",
        "inside_zone": True,
        "touch_active": True,
        "last_event_id": "EXISTING_EVENT",
        "last_row_id": 15,
    }
    mapped_values = adapter.build_patch(visit_values)["open_visit"]
    assert mapped_values["cumulative_omega"] == "PRECOMPUTED_OMEGA"
    assert (
        mapped_values["pressure_accumulation"]
        == "PRECOMPUTED_PRESSURE"
    )
    assert (
        mapped_values["attacker_force_current"]
        == "PRECOMPUTED_FORCE"
    )

    store = SnapshotStore()
    snapshot = store.create(
        plan,
        (
            {
                "metadata": {
                    "session_id": "BTCUSDT_2026-06-28_230000Z",
                },
                "geometry": {
                    "lower_edge": 100.0,
                    "upper_edge": 110.0,
                },
            },
            active_patch,
        ),
        global_zone_key="BTCUSDT_2026-06-28_230000Z::ADAPTER_SHADOW_ZONE",
    )
    assert snapshot.open_visit["active_visit_flag"] is True
    assert snapshot.open_visit["visit_id"] == (
        "OPEN_VISIT_ZONE_1:V000001"
    )
    assert snapshot.open_visit["max_penetration"] == 4.0

    print("OPEN_VISIT_ADAPTER_SHADOW_TEST = PASS")
    print("ACTIVE_VISIT_ID", active["visit_id"])
    print("NO_ACTIVE_VISIT", inactive["active_visit_flag"])
    print("MISSING_FIELD_VALUE", active["cumulative_omega"])
    print("SNAPSHOT_REVISION", snapshot.revision)
    print("NO_CALCULATIONS = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

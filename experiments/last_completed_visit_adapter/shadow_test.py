"""Shadow validation for Last Completed Visit mapping."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.canonical_snapshot import SnapshotStore
from core.interaction_interpreter import InteractionInterpreter
from core.last_completed_visit_adapter import LastCompletedVisitAdapter
from core.mechanical_refresh_coordinator import MechanicalRefreshCoordinator
from core.row_mechanics_adapter import NOT_AVAILABLE


def make_plan():
    interpreter = InteractionInterpreter(
        zone_id="COMPLETED_VISIT_ZONE_1",
        lower_edge=100.0,
        upper_edge=110.0,
        touch_tolerance=0.25,
    )
    state, events = interpreter.interpret(
        interpreter.initial_state(),
        row_index=9,
        timestamp="2026-06-28T00:00:08Z",
        price=104.0,
    )
    return MechanicalRefreshCoordinator().create_plan(state, events)


def main() -> None:
    adapter = LastCompletedVisitAdapter()
    source_visit = {
        "visit_id": "COMPLETED_VISIT_ZONE_1:V000003",
        "visit_start_row": 100,
        "visit_end_row": 107,
        "visit_start_time": "2026-06-28T00:01:00Z",
        "visit_end_time": "2026-06-28T00:01:07Z",
        "visit_duration_rows": 8,
        "max_penetration_at_visit": 4.25,
        "omega_at_visit": 72.5,
        "attacker_force_at_visit": 31.0,
        "health_at_visit": 78.0,
        "rigidity_at_visit": 69.0,
        "capacity_at_visit": 64.0,
        "fatigue_at_visit": 21.0,
        "recovery_at_visit": 0.35,
        "visit_result": "REFLECTION",
        "visit_classification": "PRECOMPUTED_CLASSIFICATION",
        "absorption_flag": False,
        "reflection_flag": True,
        "reclaim_flag": False,
        "damage_flag": False,
        "growth_flag": True,
    }
    patch = adapter.build_patch(source_visit)
    completed = patch["last_completed_visit"]

    assert completed["visit_id"] == source_visit["visit_id"]
    assert completed["visit_start_timestamp"] == (
        source_visit["visit_start_time"]
    )
    assert completed["visit_end_timestamp"] == (
        source_visit["visit_end_time"]
    )
    assert completed["visit_duration"] == 8
    assert completed["visit_row_count"] == 8
    assert completed["max_penetration"] == 4.25
    assert completed["omega_at_visit"] == 72.5
    assert completed["reflection_flag"] is True
    assert completed["absorption_flag"] is False
    assert completed["source_fields"]["visit_duration"] == (
        "visit_duration_rows"
    )

    missing_patch = adapter.build_patch(
        {
            "visit_id": "PARTIAL_VISIT",
            "visit_result": "",
            "fatigue_at_visit": float("nan"),
            "damage_flag": False,
        }
    )
    missing = missing_patch["last_completed_visit"]
    assert missing["visit_id"] == "PARTIAL_VISIT"
    assert missing["visit_start_row"] == NOT_AVAILABLE
    assert missing["visit_result"] == NOT_AVAILABLE
    assert missing["fatigue_at_visit"] == NOT_AVAILABLE
    assert missing["damage_flag"] is False

    opaque_patch = adapter.build_patch(
        {
            "visit_id": "OPAQUE_VISIT",
            "omega_at_visit": "PRECOMPUTED_OMEGA",
            "attacker_force_at_visit": "PRECOMPUTED_FORCE",
            "health_at_visit": "PRECOMPUTED_HEALTH",
        }
    )
    opaque = opaque_patch["last_completed_visit"]
    assert opaque["omega_at_visit"] == "PRECOMPUTED_OMEGA"
    assert (
        opaque["attacker_force_at_visit"]
        == "PRECOMPUTED_FORCE"
    )
    assert opaque["health_at_visit"] == "PRECOMPUTED_HEALTH"

    store = SnapshotStore()
    snapshot = store.create(
        make_plan(),
        (
            {
                "metadata": {
                    "session_id": "BTCUSDT_2026-06-28_230000Z",
                },
                "geometry": {
                    "formation_low": 95.0,
                    "formation_high": 115.0,
                },
            },
            patch,
        ),
        global_zone_key="BTCUSDT_2026-06-28_230000Z::ADAPTER_SHADOW_ZONE",
    )
    assert snapshot.last_completed_visit["visit_id"] == (
        "COMPLETED_VISIT_ZONE_1:V000003"
    )
    assert snapshot.last_completed_visit["omega_at_visit"] == 72.5
    assert snapshot.to_dict()["last_completed_visit"][
        "visit_result"
    ] == "REFLECTION"

    print("LAST_COMPLETED_VISIT_ADAPTER_SHADOW_TEST = PASS")
    print("MAPPED_VISIT_ID", completed["visit_id"])
    print("MISSING_FIELD_VALUE", missing["visit_start_row"])
    print("SNAPSHOT_REVISION", snapshot.revision)
    print("NO_CALCULATIONS = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

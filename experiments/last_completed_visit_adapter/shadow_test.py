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
    # Stage-1 additive fields are also NOT_AVAILABLE when absent (no inference).
    assert missing["visit_start_price"] == NOT_AVAILABLE
    assert missing["visit_end_price"] == NOT_AVAILABLE
    assert missing["max_penetration_ratio"] == NOT_AVAILABLE
    assert missing["defender_state"] == NOT_AVAILABLE

    # Stage-1 additive fields map when present under their canonical names.
    new_fields = adapter.build_patch(
        {
            "visit_id": "NEW_FIELDS_VISIT",
            "visit_start_price": 101.5,
            "visit_end_price": 108.25,
            "max_penetration_ratio": 0.42,
            "defender_state": "PRECOMPUTED_DEFENDER_STATE",
        }
    )["last_completed_visit"]
    assert new_fields["visit_start_price"] == 101.5
    assert new_fields["visit_end_price"] == 108.25
    assert new_fields["max_penetration_ratio"] == 0.42
    assert new_fields["defender_state"] == "PRECOMPUTED_DEFENDER_STATE"

    # Extended alias support: alternate source names project onto the canonical
    # snapshot fields, with source_fields recording the alias actually used.
    aliased = adapter.build_patch(
        {
            "completed_visit_id": "ALIASED_VISIT",
            "visit_max_penetration": 6.5,
            "visit_max_penetration_ratio": 0.65,
            "visit_final_omega": 88.0,
            "visit_attacker_force": 40.0,
            "visit_health": 70.0,
            "visit_rigidity": 66.0,
            "visit_capacity": 60.0,
            "visit_fatigue": 25.0,
            "visit_recovery": 0.28,
            "visit_defender_state": "ALIASED_DEFENDER",
        }
    )["last_completed_visit"]
    assert aliased["visit_id"] == "ALIASED_VISIT"
    assert aliased["source_fields"]["visit_id"] == "completed_visit_id"
    assert aliased["max_penetration"] == 6.5
    assert aliased["source_fields"]["max_penetration"] == "visit_max_penetration"
    assert aliased["max_penetration_ratio"] == 0.65
    assert aliased["omega_at_visit"] == 88.0
    assert aliased["source_fields"]["omega_at_visit"] == "visit_final_omega"
    assert aliased["attacker_force_at_visit"] == 40.0
    assert aliased["health_at_visit"] == 70.0
    assert aliased["rigidity_at_visit"] == 66.0
    assert aliased["capacity_at_visit"] == 60.0
    assert aliased["fatigue_at_visit"] == 25.0
    assert aliased["recovery_at_visit"] == 0.28
    assert aliased["defender_state"] == "ALIASED_DEFENDER"
    assert aliased["source_fields"]["defender_state"] == "visit_defender_state"

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
    print("NEW_FIELDS_MAPPED", new_fields["visit_start_price"], new_fields["defender_state"])
    print("ALIAS_VISIT_ID_SOURCE", aliased["source_fields"]["visit_id"])
    print("SNAPSHOT_REVISION", snapshot.revision)
    print("NEW_FIELDS_AND_ALIASES = VALIDATED")
    print("NO_CALCULATIONS = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

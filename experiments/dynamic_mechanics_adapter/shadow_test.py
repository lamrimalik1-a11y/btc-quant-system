"""Shadow validation for Dynamic Mechanics mapping."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.canonical_snapshot import SnapshotStore
from core.dynamic_mechanics_adapter import DynamicMechanicsAdapter
from core.interaction_interpreter import InteractionInterpreter
from core.mechanical_refresh_coordinator import MechanicalRefreshCoordinator
from core.row_mechanics_adapter import NOT_AVAILABLE


def make_plan():
    interpreter = InteractionInterpreter(
        zone_id="DYNAMIC_ZONE_1",
        lower_edge=100.0,
        upper_edge=110.0,
        touch_tolerance=0.25,
    )
    state, events = interpreter.interpret(
        interpreter.initial_state(),
        row_index=12,
        timestamp="2026-06-28T00:00:11Z",
        price=106.0,
    )
    return MechanicalRefreshCoordinator().create_plan(state, events)


def main() -> None:
    adapter = DynamicMechanicsAdapter()
    source_row = {
        "visit_id": "DYNAMIC_ZONE_1:V000004",
        "dynamic_state": "ATTACKER_DOMINANT",
        "previous_dynamic_state": "DEGRADING",
        "first_derivative": -4.5,
        "second_derivative": -1.25,
        "zone_integral": 318.0,
        "attacker_integral": 355.0,
        "SDR": 1.116,
        "health_slope": -2.2,
        "health_total_change": -11.0,
        "omega_total": 144.0,
        "omega_mean": 36.0,
        "dynamic_state_reason": "PRECOMPUTED_REASON",
        "dynamic_state_confidence": 0.82,
        "visit_index": 4,
        "analysis_run_utc": "2026-06-28T00:02:00Z",
    }
    patch = adapter.build_patch(source_row)
    dynamic = patch["dynamic_mechanics"]

    assert dynamic["visit_id"] == source_row["visit_id"]
    assert dynamic["dynamic_state"] == "ATTACKER_DOMINANT"
    assert dynamic["previous_dynamic_state"] == "DEGRADING"
    assert dynamic["first_derivative"] == -4.5
    assert dynamic["second_derivative"] == -1.25
    assert dynamic["zone_integral"] == 318.0
    assert dynamic["attacker_integral"] == 355.0
    assert dynamic["SDR"] == 1.116
    assert dynamic["health_slope"] == -2.2
    assert dynamic["omega_total"] == 144.0
    assert dynamic["dynamic_state_as_of_visit"] == 4
    assert dynamic["dynamic_updated_at"] == (
        "2026-06-28T00:02:00Z"
    )
    assert dynamic["source_fields"]["SDR"] == "SDR"
    assert dynamic["source_fields"]["dynamic_updated_at"] == (
        "analysis_run_utc"
    )

    alias_patch = adapter.build_patch(
        {
            "visit_id": "ALIAS_VISIT",
            "sdr": 0.75,
            "visit_index": 2,
            "analysis_run_utc": "2026-06-28T00:03:00Z",
        }
    )
    alias = alias_patch["dynamic_mechanics"]
    assert alias["SDR"] == 0.75
    assert alias["dynamic_state_as_of_visit"] == 2
    assert alias["dynamic_updated_at"] == "2026-06-28T00:03:00Z"
    assert alias["dynamic_state"] == NOT_AVAILABLE
    assert alias["dynamic_state_reason"] == NOT_AVAILABLE

    missing_patch = adapter.build_patch(
        {
            "dynamic_state": "",
            "first_derivative": float("nan"),
            "second_derivative": 0.0,
        }
    )
    missing = missing_patch["dynamic_mechanics"]
    assert missing["dynamic_state"] == NOT_AVAILABLE
    assert missing["first_derivative"] == NOT_AVAILABLE
    assert missing["second_derivative"] == 0.0
    assert missing["zone_integral"] == NOT_AVAILABLE

    opaque_patch = adapter.build_patch(
        {
            "first_derivative": "PRECOMPUTED_D1",
            "second_derivative": "PRECOMPUTED_D2",
            "zone_integral": "PRECOMPUTED_ZONE_INTEGRAL",
            "attacker_integral": "PRECOMPUTED_ATTACKER_INTEGRAL",
            "SDR": "PRECOMPUTED_SDR",
        }
    )
    opaque = opaque_patch["dynamic_mechanics"]
    assert opaque["first_derivative"] == "PRECOMPUTED_D1"
    assert opaque["second_derivative"] == "PRECOMPUTED_D2"
    assert opaque["zone_integral"] == "PRECOMPUTED_ZONE_INTEGRAL"
    assert (
        opaque["attacker_integral"]
        == "PRECOMPUTED_ATTACKER_INTEGRAL"
    )
    assert opaque["SDR"] == "PRECOMPUTED_SDR"

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
    )
    assert snapshot.dynamic_mechanics["dynamic_state"] == (
        "ATTACKER_DOMINANT"
    )
    assert snapshot.dynamic_mechanics["SDR"] == 1.116
    assert snapshot.to_dict()["dynamic_mechanics"][
        "first_derivative"
    ] == -4.5

    print("DYNAMIC_MECHANICS_ADAPTER_SHADOW_TEST = PASS")
    print("MAPPED_DYNAMIC_STATE", dynamic["dynamic_state"])
    print("SDR_ALIAS", alias["source_fields"]["SDR"])
    print("MISSING_FIELD_VALUE", missing["zone_integral"])
    print("SNAPSHOT_REVISION", snapshot.revision)
    print("NO_DYNAMIC_CALCULATIONS = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

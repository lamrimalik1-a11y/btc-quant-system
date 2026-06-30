"""Shadow validation for mapping-only row mechanics adaptation."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.canonical_snapshot import SnapshotStore
from core.interaction_interpreter import InteractionInterpreter
from core.mechanical_refresh_coordinator import MechanicalRefreshCoordinator
from core.row_mechanics_adapter import NOT_AVAILABLE, RowMechanicsAdapter


def make_plan():
    interpreter = InteractionInterpreter(
        zone_id="ROW_ADAPTER_ZONE_1",
        lower_edge=100.0,
        upper_edge=110.0,
        touch_tolerance=0.25,
    )
    state, events = interpreter.interpret(
        interpreter.initial_state(),
        row_index=7,
        timestamp="2026-06-28T00:00:06Z",
        price=103.0,
    )
    return MechanicalRefreshCoordinator().create_plan(state, events)


def main() -> None:
    adapter = RowMechanicsAdapter()
    source_row = {
        "price": 103.25,
        "timestamp": "2026-06-28T00:00:06Z",
        "row_index": 7,
        "inside_zone_flag": True,
        "zone_touch_flag": True,
        "distance_to_zone": 0.0,
        "zone_penetration_depth": 2.75,
        "fleche_live": 0.275,
        "sigma_live": 14.5,
        "sigma_barre_zone": 18.0,
        "load_live": 31.0,
        "omega_stress_area": 22.75,
        "fatigue_live": 12.0,
        "recovery_live": 0.2,
        "rigidity_live": 71.0,
        "capacity_live": 66.0,
        "health_live": 84.0,
    }
    patch = adapter.build_patch(source_row)
    mechanics = patch["current_row_mechanics"]

    assert mechanics["price"] == source_row["price"]
    assert mechanics["row_id"] == source_row["row_index"]
    assert mechanics["penetration_depth"] == (
        source_row["zone_penetration_depth"]
    )
    assert mechanics["sigma_market_live"] == source_row["sigma_live"]
    assert mechanics["sigma_barre_zone_live"] == (
        source_row["sigma_barre_zone"]
    )
    assert mechanics["omega_stress_area"] == (
        source_row["omega_stress_area"]
    )
    assert mechanics["source_fields"]["sigma_market_live"] == "sigma_live"
    assert mechanics["adapter_mode"] == "SHADOW_MAPPING_ONLY"

    missing_patch = adapter.build_patch(
        {
            "price": 0.0,
            "inside_zone_flag": False,
            "fatigue_live": float("nan"),
            "recovery_live": "",
        }
    )
    missing = missing_patch["current_row_mechanics"]
    assert missing["price"] == 0.0
    assert missing["inside_zone_flag"] is False
    assert missing["timestamp"] == NOT_AVAILABLE
    assert missing["fatigue_live"] == NOT_AVAILABLE
    assert missing["recovery_live"] == NOT_AVAILABLE
    assert missing["source_fields"]["timestamp"] == NOT_AVAILABLE

    store = SnapshotStore()
    snapshot = store.create(
        make_plan(),
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
            patch,
        ),
        global_zone_key="BTCUSDT_2026-06-28_230000Z::ADAPTER_SHADOW_ZONE",
    )
    assert snapshot.current_row_mechanics["price"] == 103.25
    assert snapshot.current_row_mechanics["health_live"] == 84.0
    assert snapshot.current_row_mechanics["adapter_mode"] == (
        "SHADOW_MAPPING_ONLY"
    )

    # Values remain byte-for-byte semantic copies; the adapter performs no
    # arithmetic or numeric coercion.
    opaque_patch = adapter.build_patch(
        {
            "load_live": "PRECOMPUTED_LOAD",
            "health_live": "PRECOMPUTED_HEALTH",
        }
    )
    opaque = opaque_patch["current_row_mechanics"]
    assert opaque["load_live"] == "PRECOMPUTED_LOAD"
    assert opaque["health_live"] == "PRECOMPUTED_HEALTH"

    print("ROW_MECHANICS_ADAPTER_SHADOW_TEST = PASS")
    print("MAPPED_FIELDS", tuple(ROW for ROW in mechanics if ROW not in {
        "source_fields",
        "adapter_mode",
    }))
    print("MISSING_FIELD_VALUE", missing["timestamp"])
    print("SNAPSHOT_REVISION", snapshot.revision)
    print("NO_CALCULATIONS = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

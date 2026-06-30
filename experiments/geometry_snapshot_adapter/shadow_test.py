"""Shadow validation for mapping-only geometry snapshot adaptation."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.canonical_snapshot import SnapshotStore
from core.geometry_snapshot_adapter import GeometrySnapshotAdapter
from core.interaction_interpreter import InteractionInterpreter
from core.mechanical_refresh_coordinator import MechanicalRefreshCoordinator
from core.row_mechanics_adapter import NOT_AVAILABLE


def make_plan():
    interpreter = InteractionInterpreter(
        zone_id="GEOMETRY_ZONE_1",
        lower_edge=100.0,
        upper_edge=110.0,
        touch_tolerance=0.25,
    )
    state, events = interpreter.interpret(
        interpreter.initial_state(),
        row_index=3,
        timestamp="2026-06-28T00:00:02Z",
        price=103.0,
    )
    return MechanicalRefreshCoordinator().create_plan(state, events)


def main() -> None:
    adapter = GeometrySnapshotAdapter()
    full_source = {
        "formation_lower_edge": 95.0,
        "formation_upper_edge": 115.0,
        "formation_mid_price": 105.0,
        "formation_width": 20.0,
        "interaction_core_lower_edge": 100.0,
        "interaction_core_upper_edge": 110.0,
        "interaction_core_mid_price": 105.0,
        "interaction_core_width": 10.0,
        "interaction_density_lower_band": 103.0,
        "interaction_density_upper_band": 107.0,
        "density_band_mid": 105.0,
        "interaction_density_width": 4.0,
        "interaction_density_weighted_center": 105.4,
        "geometry_source": "PRECOMPUTED_GEOMETRY",
        "geometry_version": "GEOMETRY_V1",
        "geometry_valid": True,
        "zone_id": "GEOMETRY_ZONE_1",
        "case_id": "CASE_GEOMETRY_1",
        "episode_id": 17,
    }
    full_patch = adapter.build_patch(full_source)
    geometry = full_patch["geometry"]

    assert geometry["formation_low"] == 95.0
    assert geometry["formation_high"] == 115.0
    assert geometry["formation_mid"] == 105.0
    assert geometry["formation_width"] == 20.0
    assert geometry["active_core_low"] == 100.0
    assert geometry["active_core_high"] == 110.0
    assert geometry["active_core_mid"] == 105.0
    assert geometry["active_core_width"] == 10.0
    assert geometry["density_band_low"] == 103.0
    assert geometry["density_band_high"] == 107.0
    assert geometry["density_band_mid"] == 105.0
    assert geometry["density_band_width"] == 4.0
    assert geometry["density_weighted_center"] == 105.4
    assert geometry["geometry_valid"] is True
    assert geometry["source_fields"]["formation_low"] == (
        "formation_lower_edge"
    )

    partial_patch = adapter.build_patch(
        {
            "real_zone_lower_edge": 90.0,
            "real_zone_upper_edge": 120.0,
            "interaction_core_lower_edge": 100.0,
            "interaction_core_upper_edge": 110.0,
            "interaction_density_weighted_center": 105.25,
            "geometry_valid": False,
        }
    )
    partial = partial_patch["geometry"]
    assert partial["formation_low"] == 90.0
    assert partial["formation_high"] == 120.0
    assert partial["formation_mid"] == NOT_AVAILABLE
    assert partial["formation_width"] == NOT_AVAILABLE
    assert partial["active_core_width"] == NOT_AVAILABLE
    assert partial["density_band_mid"] == NOT_AVAILABLE
    assert partial["density_weighted_center"] == 105.25
    assert partial["geometry_valid"] is False

    opaque_patch = adapter.build_patch(
        {
            "formation_width": "PRECOMPUTED_FORMATION_WIDTH",
            "interaction_core_width": "PRECOMPUTED_CORE_WIDTH",
            "interaction_density_width": "PRECOMPUTED_DENSITY_WIDTH",
        }
    )
    opaque = opaque_patch["geometry"]
    assert (
        opaque["formation_width"]
        == "PRECOMPUTED_FORMATION_WIDTH"
    )
    assert opaque["active_core_width"] == "PRECOMPUTED_CORE_WIDTH"
    assert (
        opaque["density_band_width"]
        == "PRECOMPUTED_DENSITY_WIDTH"
    )

    store = SnapshotStore()
    snapshot = store.create(
        make_plan(),
        (
            {
                "metadata": {
                    "session_id": "BTCUSDT_2026-06-28_230000Z",
                }
            },
            full_patch,
        ),
    )
    assert snapshot.geometry["formation_width"] == 20.0
    assert snapshot.geometry["active_core_width"] == 10.0
    assert snapshot.geometry["density_band_width"] == 4.0

    print("GEOMETRY_SNAPSHOT_ADAPTER_SHADOW_TEST = PASS")
    print("FORMATION_ALIAS", geometry["source_fields"]["formation_low"])
    print("ACTIVE_CORE_ALIAS", geometry["source_fields"]["active_core_low"])
    print("DENSITY_ALIAS", geometry["source_fields"]["density_band_low"])
    print("PARTIAL_MISSING_WIDTH", partial["formation_width"])
    print("SNAPSHOT_REVISION", snapshot.revision)
    print("NO_GEOMETRY_CONSTRUCTION = TRUE")
    print("NO_CALCULATIONS = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

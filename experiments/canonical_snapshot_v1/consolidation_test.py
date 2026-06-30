"""Canonical Snapshot V1 end-to-end shadow consolidation test.

All six mapping adapters feed one in-memory SnapshotStore. The test performs
no mechanical, Dynamic State, B10, or B11 calculations and writes no files.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.canonical_snapshot import SNAPSHOT_SECTIONS, SnapshotStore
from core.dynamic_mechanics_adapter import DynamicMechanicsAdapter
from core.geometry_snapshot_adapter import GeometrySnapshotAdapter
from core.interaction_interpreter import InteractionInterpreter
from core.last_completed_visit_adapter import LastCompletedVisitAdapter
from core.mechanical_refresh_coordinator import MechanicalRefreshCoordinator
from core.open_visit_adapter import OpenVisitAdapter
from core.prediction_adapter import PredictionAdapter
from core.row_mechanics_adapter import NOT_AVAILABLE, RowMechanicsAdapter


ZONE_ID = "CANONICAL_V1_ZONE_1"
SESSION_ID = "BTCUSDT_2026-06-28_230000Z"


def make_plan(row_index: int, timestamp: str, price: float):
    interpreter = InteractionInterpreter(
        zone_id=ZONE_ID,
        lower_edge=70100.0,
        upper_edge=70300.0,
        touch_tolerance=5.0,
    )
    state, events = interpreter.interpret(
        interpreter.initial_state(),
        row_index=row_index,
        timestamp=timestamp,
        price=price,
    )
    return MechanicalRefreshCoordinator().create_plan(state, events)


def initial_patches():
    geometry = GeometrySnapshotAdapter().build_patch(
        {
            "formation_lower_edge": 70000.0,
            "formation_upper_edge": 70500.0,
            "formation_mid_price": 70250.0,
            # Deliberately precomputed and not equal to upper - lower.
            "formation_width": 499.25,
            "interaction_core_lower_edge": 70100.0,
            "interaction_core_upper_edge": 70300.0,
            "interaction_core_mid_price": 70200.0,
            "interaction_core_width": 199.5,
            "interaction_density_lower_band": 70170.0,
            "interaction_density_upper_band": 70230.0,
            "density_band_mid": 70200.0,
            "interaction_density_width": 59.75,
            "interaction_density_weighted_center": 70204.5,
            "geometry_source": "PROJECT_1_PRECOMPUTED",
            "geometry_version": "PROJECT_1_V1",
            "geometry_valid": True,
            "zone_id": ZONE_ID,
            "case_id": "CASE_CANONICAL_V1",
            "episode_id": 901,
        }
    )
    row = RowMechanicsAdapter().build_patch(
        {
            "price": 70180.0,
            "timestamp": "2026-06-28T00:10:00Z",
            "row_index": 1000,
            "inside_zone_flag": True,
            "zone_touch_flag": True,
            "distance_to_zone": 0.0,
            "zone_penetration_depth": 80.0,
            "fleche_live": 0.4,
            "sigma_live": 18.5,
            "sigma_barre_zone": 24.0,
            "load_live": 38.0,
            "omega_stress_area": 91.0,
            "fatigue_live": 27.0,
            "recovery_live": 0.22,
            "rigidity_live": 73.0,
            "capacity_live": 68.0,
            "health_live": 81.0,
        }
    )
    open_visit = OpenVisitAdapter().build_patch(
        {
            "visit_id": f"{ZONE_ID}:V000004",
            "visit_status": "OPEN",
            "visit_start_row": 998,
            "visit_start_timestamp": "2026-06-28T00:09:58Z",
            "visit_start_price": 70305.0,
            "current_row_count": 3,
            "max_penetration": 80.0,
            "cumulative_omega": 144.0,
            "pressure_accumulation": 76.0,
            "attacker_force_current": 38.0,
            "inside_zone": True,
            "touch_active": True,
            "last_event_id": f"{ZONE_ID}:1000:PENETRATION_UPDATED:01",
            "last_row_id": 1000,
        }
    )
    completed_visit = LastCompletedVisitAdapter().build_patch(
        {
            "visit_id": f"{ZONE_ID}:V000003",
            "visit_start_row": 970,
            "visit_end_row": 980,
            "visit_start_time": "2026-06-28T00:09:30Z",
            "visit_end_time": "2026-06-28T00:09:40Z",
            "visit_duration_rows": 11,
            "max_penetration_at_visit": 62.0,
            "omega_at_visit": 118.0,
            "attacker_force_at_visit": 34.0,
            "health_at_visit": 84.0,
            "rigidity_at_visit": 76.0,
            "capacity_at_visit": 71.0,
            "fatigue_at_visit": 23.0,
            "recovery_at_visit": 0.3,
            "visit_result": "REFLECTION",
            "visit_classification": "PRECOMPUTED_REFLECTION",
            "reflection_flag": True,
            "reclaim_flag": False,
            "damage_flag": False,
            "growth_flag": True,
        }
    )
    dynamic = DynamicMechanicsAdapter().build_patch(
        {
            "visit_id": f"{ZONE_ID}:V000003",
            "dynamic_state": "STABLE",
            "first_derivative": 2.0,
            "second_derivative": 0.5,
            "zone_integral": 330.0,
            "attacker_integral": 280.0,
            "SDR": 0.8485,
            "health_slope": 1.25,
            "health_total_change": 7.0,
            "omega_total": 306.0,
            "omega_mean": 102.0,
            "visit_index": 3,
            "analysis_run_utc": "2026-06-28T00:09:45Z",
        }
    )
    prediction = PredictionAdapter().build_patch(
        {
            "structural_trajectory": "STABLE",
            "trajectory_direction": "HOLD",
            "trajectory_reason": "PRECOMPUTED_B10_REASON",
            "trajectory_confidence": "HIGH",
            "structural_prediction": "LIKELY_HOLD",
            "prediction_reason": "PRECOMPUTED_B11_REASON",
            "prediction_confidence": "HIGH",
            "prediction_version": "B11_V1",
            "emit_status": "PENDING_FINALIZATION",
            "dynamic_state": "STABLE",
            "visit_id": f"{ZONE_ID}:V000003",
            "visit_index": 3,
            "analysis_run_utc": "2026-06-28T00:09:46Z",
        }
    )
    metadata = {
        "metadata": {
            "session_id": SESSION_ID,
            "market_date": "2026-06-29",
            "case_id": "CASE_CANONICAL_V1",
            "episode_id": 901,
        }
    }
    return (
        metadata,
        geometry,
        row,
        open_visit,
        completed_visit,
        dynamic,
        prediction,
    )


def main() -> None:
    store = SnapshotStore()
    first = store.create(
        make_plan(1000, "2026-06-28T00:10:00Z", 70180.0),
        initial_patches(),
    )

    expected_sections = {
        "metadata",
        "geometry",
        "current_row_mechanics",
        "open_visit",
        "last_completed_visit",
        "dynamic_mechanics",
        "prediction",
    }
    assert expected_sections.issubset(first.to_dict())
    assert expected_sections == set(SNAPSHOT_SECTIONS)
    assert first.revision == 1

    # Proves mapping-only behavior: no adapter corrected the deliberately
    # inconsistent precomputed widths.
    assert first.geometry["formation_width"] == 499.25
    assert first.geometry["active_core_width"] == 199.5
    assert first.geometry["density_band_width"] == 59.75
    assert first.dynamic_mechanics["SDR"] == 0.8485
    assert first.prediction["b11_prediction"] == "LIKELY_HOLD"

    # Explicit missing values remain visible rather than being inferred.
    assert first.last_completed_visit["absorption_flag"] == NOT_AVAILABLE
    assert first.dynamic_mechanics["previous_dynamic_state"] == NOT_AVAILABLE
    assert first.dynamic_mechanics["dynamic_state_reason"] == NOT_AVAILABLE
    assert first.prediction["b11_state"] == NOT_AVAILABLE

    second = store.update(
        ZONE_ID,
        make_plan(1001, "2026-06-28T00:10:01Z", 70210.0),
        (
            RowMechanicsAdapter().build_patch(
                {
                    "price": 70210.0,
                    "timestamp": "2026-06-28T00:10:01Z",
                    "row_index": 1001,
                    "inside_zone_flag": True,
                    "zone_touch_flag": True,
                    "distance_to_zone": 0.0,
                    "zone_penetration_depth": 110.0,
                    "fleche_live": 0.55,
                    "sigma_live": 20.0,
                    "sigma_barre_zone": 24.0,
                    "load_live": 41.0,
                    "omega_stress_area": 105.0,
                    "fatigue_live": 29.0,
                    "recovery_live": 0.24,
                    "rigidity_live": 72.0,
                    "capacity_live": 67.0,
                    "health_live": 80.0,
                }
            ),
            OpenVisitAdapter().build_patch(
                {
                    "visit_id": f"{ZONE_ID}:V000004",
                    "visit_status": "OPEN",
                    "current_row_count": 4,
                    "max_penetration": 110.0,
                    "cumulative_omega": 166.0,
                    "pressure_accumulation": 83.0,
                    "attacker_force_current": 41.0,
                    "inside_zone": True,
                    "touch_active": True,
                    "last_event_id": (
                        f"{ZONE_ID}:1001:PENETRATION_UPDATED:01"
                    ),
                    "last_row_id": 1001,
                }
            ),
        ),
    )
    assert second.revision == 2
    assert second.current_row_mechanics["price"] == 70210.0
    assert second.open_visit["current_row_count"] == 4
    assert first.revision == 1
    assert first.current_row_mechanics["price"] == 70180.0

    # Deep immutability: both top-level section and nested provenance map.
    try:
        second.geometry["formation_width"] = 500.0
    except TypeError:
        pass
    else:
        raise AssertionError("Snapshot geometry is mutable")

    try:
        second.geometry["source_fields"]["formation_width"] = "changed"
    except TypeError:
        pass
    else:
        raise AssertionError("Nested snapshot provenance is mutable")

    try:
        store.update(
            ZONE_ID,
            make_plan(1002, "2026-06-28T00:10:02Z", 70220.0),
            ({"unsupported_future_section": {"value": 1}},),
        )
    except ValueError as error:
        assert "Unsupported snapshot sections" in str(error)
    else:
        raise AssertionError("Invalid update unexpectedly succeeded")

    after_failure = store.get_current(ZONE_ID)
    assert after_failure is second
    assert after_failure.revision == 2
    assert after_failure.current_row_mechanics["price"] == 70210.0

    print("CANONICAL_SNAPSHOT_V1_CONSOLIDATION_TEST = PASS")
    print("ADAPTER_COUNT", 6)
    print("SNAPSHOT_SECTIONS", SNAPSHOT_SECTIONS)
    print("FINAL_REVISION", after_failure.revision)
    print("NOT_AVAILABLE_VALIDATED = TRUE")
    print("IMMUTABILITY_VALIDATED = TRUE")
    print("FAILED_UPDATE_PRESERVED_REVISION = TRUE")
    print("NO_CALCULATIONS = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

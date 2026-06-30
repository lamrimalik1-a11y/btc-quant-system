"""Shadow validation for mapping-only B10/B11 prediction adaptation."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.canonical_snapshot import SnapshotStore
from core.interaction_interpreter import InteractionInterpreter
from core.mechanical_refresh_coordinator import MechanicalRefreshCoordinator
from core.prediction_adapter import PredictionAdapter
from core.row_mechanics_adapter import NOT_AVAILABLE


def make_plan():
    interpreter = InteractionInterpreter(
        zone_id="PREDICTION_ZONE_1",
        lower_edge=100.0,
        upper_edge=110.0,
        touch_tolerance=0.25,
    )
    state, events = interpreter.interpret(
        interpreter.initial_state(),
        row_index=15,
        timestamp="2026-06-28T00:00:14Z",
        price=107.0,
    )
    return MechanicalRefreshCoordinator().create_plan(state, events)


def main() -> None:
    adapter = PredictionAdapter()
    source_row = {
        "structural_trajectory": "DEGRADING",
        "trajectory_direction": "FAIL",
        "trajectory_reason": "PRECOMPUTED_B10_REASON",
        "trajectory_confidence": "HIGH",
        "structural_prediction": "LIKELY_FAILURE",
        "b11_state": "PRECOMPUTED_B11_STATE",
        "prediction_reason": "PRECOMPUTED_B11_REASON",
        "prediction_confidence": "MEDIUM",
        "prediction_uncertainty": "PRECOMPUTED_B11_UNCERTAINTY",
        "prediction_version": "B11_V1",
        "emit_status": "PENDING_FINALIZATION",
        "dynamic_state": "ATTACKER_DOMINANT",
        "visit_id": "PREDICTION_ZONE_1:V000005",
        "visit_index": 5,
        "analysis_run_utc": "2026-06-28T00:04:00Z",
    }
    patch = adapter.build_patch(source_row)
    prediction = patch["prediction"]

    assert prediction["b10_trajectory"] == "DEGRADING"
    assert prediction["b10_state"] == "FAIL"
    assert prediction["b10_reason"] == "PRECOMPUTED_B10_REASON"
    assert prediction["b10_confidence"] == "HIGH"
    assert prediction["b11_prediction"] == "LIKELY_FAILURE"
    assert prediction["b11_state"] == "PRECOMPUTED_B11_STATE"
    assert prediction["b11_reason"] == "PRECOMPUTED_B11_REASON"
    assert prediction["b11_confidence"] == "MEDIUM"
    assert prediction["prediction_uncertainty"] == (
        "PRECOMPUTED_B11_UNCERTAINTY"
    )
    assert prediction["prediction_status"] == "PENDING_FINALIZATION"
    assert prediction["input_dynamic_state"] == "ATTACKER_DOMINANT"
    assert prediction["input_visit_id"] == (
        "PREDICTION_ZONE_1:V000005"
    )
    assert prediction["prediction_as_of_visit"] == 5
    assert prediction["prediction_updated_at"] == (
        "2026-06-28T00:04:00Z"
    )
    assert prediction["source_fields"]["b10_trajectory"] == (
        "structural_trajectory"
    )
    assert prediction["source_fields"]["b11_prediction"] == (
        "structural_prediction"
    )

    alias_patch = adapter.build_patch(
        {
            "b10_trajectory": "STABLE",
            "b10_state": "HOLD",
            "b11_prediction": "LIKELY_HOLD",
            "prediction_status": "PRECOMPUTED_STATUS",
            "prediction_updated_at": "PRECOMPUTED_TIME",
            "uncertainty": 0.18,
        }
    )
    alias = alias_patch["prediction"]
    assert alias["b10_trajectory"] == "STABLE"
    assert alias["b10_state"] == "HOLD"
    assert alias["b11_prediction"] == "LIKELY_HOLD"
    assert alias["prediction_status"] == "PRECOMPUTED_STATUS"
    assert alias["prediction_updated_at"] == "PRECOMPUTED_TIME"
    assert alias["prediction_uncertainty"] == 0.18
    assert alias["source_fields"]["prediction_uncertainty"] == "uncertainty"

    missing_patch = adapter.build_patch(
        {
            "structural_prediction": "",
            "prediction_confidence": float("nan"),
            "visit_index": 0,
        }
    )
    missing = missing_patch["prediction"]
    assert missing["b11_prediction"] == NOT_AVAILABLE
    assert missing["b11_confidence"] == NOT_AVAILABLE
    assert missing["b10_trajectory"] == NOT_AVAILABLE
    assert missing["prediction_as_of_visit"] == 0
    assert missing["prediction_uncertainty"] == NOT_AVAILABLE

    opaque_patch = adapter.build_patch(
        {
            "structural_trajectory": "PRECOMPUTED_TRAJECTORY",
            "structural_prediction": "PRECOMPUTED_PREDICTION",
            "trajectory_confidence": "PRECOMPUTED_B10_CONFIDENCE",
            "prediction_confidence": "PRECOMPUTED_B11_CONFIDENCE",
        }
    )
    opaque = opaque_patch["prediction"]
    assert opaque["b10_trajectory"] == "PRECOMPUTED_TRAJECTORY"
    assert opaque["b11_prediction"] == "PRECOMPUTED_PREDICTION"
    assert (
        opaque["b10_confidence"]
        == "PRECOMPUTED_B10_CONFIDENCE"
    )
    assert (
        opaque["b11_confidence"]
        == "PRECOMPUTED_B11_CONFIDENCE"
    )

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
    assert snapshot.prediction["b10_trajectory"] == "DEGRADING"
    assert snapshot.prediction["b11_prediction"] == "LIKELY_FAILURE"
    assert snapshot.to_dict()["prediction"]["prediction_version"] == (
        "B11_V1"
    )

    print("PREDICTION_ADAPTER_SHADOW_TEST = PASS")
    print("B10_ALIAS", prediction["source_fields"]["b10_trajectory"])
    print("B11_ALIAS", prediction["source_fields"]["b11_prediction"])
    print("MAPPED_UNCERTAINTY", prediction["prediction_uncertainty"])
    print("UNCERTAINTY_ALIAS_SOURCE", alias["source_fields"]["prediction_uncertainty"])
    print("MISSING_FIELD_VALUE", missing["b11_prediction"])
    print("SNAPSHOT_REVISION", snapshot.revision)
    print("NO_PREDICTION_CALCULATIONS = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

"""Shadow-only mapping from stored B10/B11 outputs to snapshot patches.

The adapter copies existing trajectory and prediction values through explicit
semantic aliases. It does not execute B10, B11, scoring, confidence, or state
logic.
"""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Mapping

from core.row_mechanics_adapter import NOT_AVAILABLE


PREDICTION_FIELD_MAP: dict[str, tuple[str, ...]] = {
    "b10_trajectory": (
        "b10_trajectory",
        "structural_trajectory",
    ),
    "b10_state": (
        "b10_state",
        "trajectory_direction",
    ),
    "b10_reason": (
        "b10_reason",
        "trajectory_reason",
    ),
    "b10_confidence": (
        "b10_confidence",
        "trajectory_confidence",
    ),
    "b11_prediction": (
        "b11_prediction",
        "structural_prediction",
    ),
    "b11_state": ("b11_state",),
    "b11_reason": (
        "b11_reason",
        "prediction_reason",
    ),
    "b11_confidence": (
        "b11_confidence",
        "prediction_confidence",
    ),
    "prediction_uncertainty": (
        "prediction_uncertainty",
        "uncertainty",
    ),
    "prediction_version": ("prediction_version",),
    "prediction_status": (
        "prediction_status",
        "emit_status",
    ),
    "input_dynamic_state": (
        "input_dynamic_state",
        "dynamic_state",
    ),
    "input_visit_id": (
        "input_visit_id",
        "visit_id",
    ),
    "prediction_as_of_visit": (
        "prediction_as_of_visit",
        "visit_index",
    ),
    "prediction_updated_at": (
        "prediction_updated_at",
        "analysis_run_utc",
    ),
}


class PredictionAdapter:
    """Build a Prediction patch from already-computed B10/B11 values."""

    def build_patch(
        self,
        prediction_row: Mapping[str, Any],
    ) -> dict[str, dict[str, Any]]:
        if not isinstance(prediction_row, Mapping):
            raise TypeError("prediction_row must be a mapping")

        prediction: dict[str, Any] = {}
        source_fields: dict[str, str] = {}

        for target_field, aliases in PREDICTION_FIELD_MAP.items():
            source_field, value = _first_available(
                prediction_row,
                aliases,
            )
            if source_field is None:
                prediction[target_field] = NOT_AVAILABLE
                source_fields[target_field] = NOT_AVAILABLE
            else:
                prediction[target_field] = deepcopy(value)
                source_fields[target_field] = source_field

        prediction["source_fields"] = source_fields
        prediction["adapter_mode"] = "SHADOW_MAPPING_ONLY"
        return {"prediction": prediction}


def _first_available(
    prediction_row: Mapping[str, Any],
    aliases: tuple[str, ...],
) -> tuple[str | None, Any]:
    for source_field in aliases:
        if source_field not in prediction_row:
            continue
        value = prediction_row[source_field]
        if _is_available(value):
            return source_field, value
    return None, NOT_AVAILABLE


def _is_available(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    return True


__all__ = [
    "PREDICTION_FIELD_MAP",
    "PredictionAdapter",
]

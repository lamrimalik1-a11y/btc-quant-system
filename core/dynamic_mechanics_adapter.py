"""Shadow-only mapping from dynamic timeline rows to snapshot patches.

The adapter copies existing derivative, integral, SDR, state, and summary
values through explicit aliases. It performs no dynamic calculations or
classification.
"""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Mapping

from core.row_mechanics_adapter import NOT_AVAILABLE


DYNAMIC_MECHANICS_FIELD_MAP: dict[str, tuple[str, ...]] = {
    "visit_id": ("visit_id",),
    "dynamic_state": ("dynamic_state",),
    "previous_dynamic_state": ("previous_dynamic_state",),
    "transition_name": ("transition_name",),
    "first_derivative": ("first_derivative",),
    "second_derivative": ("second_derivative",),
    "zone_integral": ("zone_integral",),
    "attacker_integral": ("attacker_integral",),
    "SDR": ("SDR", "sdr"),
    "health_slope": ("health_slope",),
    "health_total_change": ("health_total_change",),
    "omega_total": ("omega_total",),
    "omega_mean": ("omega_mean",),
    "dynamic_state_reason": ("dynamic_state_reason",),
    "dynamic_state_confidence": ("dynamic_state_confidence",),
    "dynamic_state_as_of_visit": (
        "dynamic_state_as_of_visit",
        "visit_index",
    ),
    "dynamic_updated_at": (
        "dynamic_updated_at",
        "analysis_run_utc",
    ),
}


class DynamicMechanicsAdapter:
    """Build a Dynamic Mechanics patch from existing timeline values."""

    def build_patch(
        self,
        timeline_row: Mapping[str, Any],
    ) -> dict[str, dict[str, Any]]:
        if not isinstance(timeline_row, Mapping):
            raise TypeError("timeline_row must be a mapping")

        mechanics: dict[str, Any] = {}
        source_fields: dict[str, str] = {}

        for target_field, aliases in DYNAMIC_MECHANICS_FIELD_MAP.items():
            source_field, value = _first_available(timeline_row, aliases)
            if source_field is None:
                mechanics[target_field] = NOT_AVAILABLE
                source_fields[target_field] = NOT_AVAILABLE
            else:
                mechanics[target_field] = deepcopy(value)
                source_fields[target_field] = source_field

        mechanics["source_fields"] = source_fields
        mechanics["adapter_mode"] = "SHADOW_MAPPING_ONLY"
        return {"dynamic_mechanics": mechanics}


def _first_available(
    timeline_row: Mapping[str, Any],
    aliases: tuple[str, ...],
) -> tuple[str | None, Any]:
    for source_field in aliases:
        if source_field not in timeline_row:
            continue
        value = timeline_row[source_field]
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
    "DYNAMIC_MECHANICS_FIELD_MAP",
    "DynamicMechanicsAdapter",
]

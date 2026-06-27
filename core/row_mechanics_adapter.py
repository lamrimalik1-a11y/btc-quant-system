"""Shadow-only mapping from existing row fields to snapshot patches.

This adapter performs no mechanical calculations, coercion, normalization,
or fallback derivation. It copies the first available value from an explicit
source alias list and marks unavailable values with NOT_AVAILABLE.
"""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Mapping


NOT_AVAILABLE = "NOT_AVAILABLE"

# Canonical field -> existing source field aliases, in precedence order.
# Aliases only bridge established row/evolution naming differences.
ROW_MECHANICS_FIELD_MAP: dict[str, tuple[str, ...]] = {
    "price": ("price", "close"),
    "timestamp": ("timestamp", "market_timestamp"),
    "row_id": ("row_id", "row_index"),
    "inside_zone_flag": ("inside_zone_flag",),
    "zone_touch_flag": ("zone_touch_flag",),
    "distance_to_zone": ("distance_to_zone",),
    "penetration_depth": (
        "penetration_depth",
        "zone_penetration_depth",
    ),
    "fleche_live": ("fleche_live",),
    "sigma_market_live": (
        "sigma_market_live",
        "sigma_live",
        "sigma_market",
    ),
    "sigma_barre_zone_live": (
        "sigma_barre_zone_live",
        "sigma_barre_zone",
        "adaptive_sigma_barre_v2",
    ),
    "load_live": ("load_live",),
    "omega_stress_area": ("omega_stress_area",),
    "fatigue_live": ("fatigue_live",),
    "recovery_live": ("recovery_live",),
    "rigidity_live": ("rigidity_live",),
    "capacity_live": ("capacity_live",),
    "health_live": ("health_live",),
}


class RowMechanicsAdapter:
    """Build a Current Row Mechanics patch from already-computed values."""

    def build_patch(
        self,
        row: Mapping[str, Any],
    ) -> dict[str, dict[str, Any]]:
        if not isinstance(row, Mapping):
            raise TypeError("row must be a mapping")

        mechanics: dict[str, Any] = {}
        source_fields: dict[str, str] = {}

        for target_field, source_aliases in ROW_MECHANICS_FIELD_MAP.items():
            source_field, value = _first_available(row, source_aliases)
            if source_field is None:
                mechanics[target_field] = NOT_AVAILABLE
                source_fields[target_field] = NOT_AVAILABLE
            else:
                mechanics[target_field] = deepcopy(value)
                source_fields[target_field] = source_field

        mechanics["source_fields"] = source_fields
        mechanics["adapter_mode"] = "SHADOW_MAPPING_ONLY"
        return {"current_row_mechanics": mechanics}


def _first_available(
    row: Mapping[str, Any],
    aliases: tuple[str, ...],
) -> tuple[str | None, Any]:
    for source_field in aliases:
        if source_field not in row:
            continue
        value = row[source_field]
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
    "NOT_AVAILABLE",
    "ROW_MECHANICS_FIELD_MAP",
    "RowMechanicsAdapter",
]

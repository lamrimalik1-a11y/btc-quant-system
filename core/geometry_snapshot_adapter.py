"""Shadow-only mapping from existing zone geometry to snapshot patches.

The adapter copies stored Formation, Active Core, and Density Band values
through explicit semantic aliases. It does not construct bounds, widths,
midpoints, validity, or any other geometry.
"""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Mapping

from core.row_mechanics_adapter import NOT_AVAILABLE


GEOMETRY_FIELD_MAP: dict[str, tuple[str, ...]] = {
    "formation_low": (
        "formation_low",
        "formation_lower_edge",
        "real_zone_lower_edge",
    ),
    "formation_high": (
        "formation_high",
        "formation_upper_edge",
        "real_zone_upper_edge",
    ),
    "formation_mid": (
        "formation_mid",
        "formation_mid_price",
        "real_zone_mid_price",
    ),
    "formation_width": (
        "formation_width",
        "real_zone_width",
    ),
    "active_core_low": (
        "active_core_low",
        "interaction_core_lower_edge",
    ),
    "active_core_high": (
        "active_core_high",
        "interaction_core_upper_edge",
    ),
    "active_core_mid": (
        "active_core_mid",
        "interaction_core_mid_price",
    ),
    "active_core_width": (
        "active_core_width",
        "interaction_core_width",
    ),
    "density_band_low": (
        "density_band_low",
        "interaction_density_lower_band",
    ),
    "density_band_high": (
        "density_band_high",
        "interaction_density_upper_band",
    ),
    "density_band_mid": (
        "density_band_mid",
        "interaction_density_mid_price",
    ),
    "density_band_width": (
        "density_band_width",
        "interaction_density_width",
    ),
    "density_weighted_center": (
        "density_weighted_center",
        "interaction_density_weighted_center",
    ),
    "geometry_source": ("geometry_source",),
    "geometry_version": ("geometry_version",),
    "geometry_valid": ("geometry_valid",),
    "zone_id": ("zone_id",),
    "case_id": ("case_id",),
    "episode_id": ("episode_id",),
}


class GeometrySnapshotAdapter:
    """Build a Geometry patch from already-existing geometry values."""

    def build_patch(
        self,
        zone: Mapping[str, Any],
    ) -> dict[str, dict[str, Any]]:
        if not isinstance(zone, Mapping):
            raise TypeError("zone must be a mapping")

        geometry: dict[str, Any] = {}
        source_fields: dict[str, str] = {}

        for target_field, aliases in GEOMETRY_FIELD_MAP.items():
            source_field, value = _first_available(zone, aliases)
            if source_field is None:
                geometry[target_field] = NOT_AVAILABLE
                source_fields[target_field] = NOT_AVAILABLE
            else:
                geometry[target_field] = deepcopy(value)
                source_fields[target_field] = source_field

        geometry["source_fields"] = source_fields
        geometry["adapter_mode"] = "SHADOW_MAPPING_ONLY"
        return {"geometry": geometry}


def _first_available(
    zone: Mapping[str, Any],
    aliases: tuple[str, ...],
) -> tuple[str | None, Any]:
    for source_field in aliases:
        if source_field not in zone:
            continue
        value = zone[source_field]
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
    "GEOMETRY_FIELD_MAP",
    "GeometrySnapshotAdapter",
]

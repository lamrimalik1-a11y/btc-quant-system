"""Shadow-only mapping from completed visit rows to snapshot patches.

The adapter copies existing visit-level values through explicit aliases. It
does not calculate duration, classify outcomes, or derive mechanical flags.
"""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Mapping

from core.row_mechanics_adapter import NOT_AVAILABLE


LAST_COMPLETED_VISIT_FIELD_MAP: dict[str, tuple[str, ...]] = {
    "visit_id": ("visit_id",),
    "visit_start_row": ("visit_start_row",),
    "visit_end_row": ("visit_end_row",),
    "visit_start_timestamp": (
        "visit_start_timestamp",
        "visit_start_time",
    ),
    "visit_end_timestamp": (
        "visit_end_timestamp",
        "visit_end_time",
    ),
    "visit_duration": (
        "visit_duration",
        "visit_duration_rows",
    ),
    "visit_row_count": (
        "visit_row_count",
        "visit_duration_rows",
    ),
    "max_penetration": (
        "max_penetration",
        "max_penetration_at_visit",
    ),
    "omega_at_visit": ("omega_at_visit",),
    "attacker_force_at_visit": ("attacker_force_at_visit",),
    "health_at_visit": ("health_at_visit",),
    "rigidity_at_visit": ("rigidity_at_visit",),
    "capacity_at_visit": ("capacity_at_visit",),
    "fatigue_at_visit": ("fatigue_at_visit",),
    "recovery_at_visit": ("recovery_at_visit",),
    "visit_result": ("visit_result",),
    "visit_classification": ("visit_classification",),
    "absorption_flag": ("absorption_flag",),
    "reflection_flag": ("reflection_flag",),
    "reclaim_flag": ("reclaim_flag",),
    "damage_flag": ("damage_flag",),
    "growth_flag": ("growth_flag",),
}


class LastCompletedVisitAdapter:
    """Build a Last Completed Visit patch from stored visit values."""

    def build_patch(
        self,
        visit: Mapping[str, Any],
    ) -> dict[str, dict[str, Any]]:
        if not isinstance(visit, Mapping):
            raise TypeError("visit must be a mapping")

        completed_visit: dict[str, Any] = {}
        source_fields: dict[str, str] = {}

        for target_field, aliases in (
            LAST_COMPLETED_VISIT_FIELD_MAP.items()
        ):
            source_field, value = _first_available(visit, aliases)
            if source_field is None:
                completed_visit[target_field] = NOT_AVAILABLE
                source_fields[target_field] = NOT_AVAILABLE
            else:
                completed_visit[target_field] = deepcopy(value)
                source_fields[target_field] = source_field

        completed_visit["source_fields"] = source_fields
        completed_visit["adapter_mode"] = "SHADOW_MAPPING_ONLY"
        return {"last_completed_visit": completed_visit}


def _first_available(
    visit: Mapping[str, Any],
    aliases: tuple[str, ...],
) -> tuple[str | None, Any]:
    for source_field in aliases:
        if source_field not in visit:
            continue
        value = visit[source_field]
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
    "LAST_COMPLETED_VISIT_FIELD_MAP",
    "LastCompletedVisitAdapter",
]

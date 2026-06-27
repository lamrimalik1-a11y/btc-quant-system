"""Shadow-only mapping from interaction state to Open Visit patches.

The adapter copies existing values through explicit aliases. It does not
accumulate visits, calculate mechanics, infer visit outcomes, or persist data.
"""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Mapping

from core.interaction_interpreter import InteractionState
from core.row_mechanics_adapter import NOT_AVAILABLE


OPEN_VISIT_FIELD_MAP: dict[str, tuple[str, ...]] = {
    "visit_id": ("visit_id", "active_visit_id"),
    "visit_status": ("visit_status",),
    "visit_start_row": ("visit_start_row",),
    "visit_start_timestamp": ("visit_start_timestamp",),
    "visit_start_price": ("visit_start_price",),
    "current_row_count": ("current_row_count", "visit_row_count"),
    "max_penetration": (
        "max_penetration",
        "visit_max_penetration",
    ),
    "cumulative_omega": ("cumulative_omega",),
    "pressure_accumulation": ("pressure_accumulation",),
    "attacker_force_current": ("attacker_force_current",),
    "inside_zone": ("inside_zone", "inside_zone_flag"),
    "touch_active": ("touch_active", "touching_zone", "zone_touch_flag"),
    "last_event_id": ("last_event_id",),
    "last_row_id": (
        "last_row_id",
        "previous_row_index",
        "last_active_row",
    ),
}

_VISIT_SPECIFIC_FIELDS = frozenset(
    {
        "visit_id",
        "visit_status",
        "visit_start_row",
        "visit_start_timestamp",
        "visit_start_price",
        "current_row_count",
        "max_penetration",
        "cumulative_omega",
        "pressure_accumulation",
        "attacker_force_current",
        "last_event_id",
    }
)


class OpenVisitAdapter:
    """Build an Open Visit patch from existing state or visit values."""

    def build_patch(
        self,
        source: InteractionState | Mapping[str, Any],
    ) -> dict[str, dict[str, Any]]:
        if not isinstance(source, (InteractionState, Mapping)):
            raise TypeError(
                "source must be InteractionState or a mapping"
            )

        open_visit: dict[str, Any] = {}
        source_fields: dict[str, str] = {}

        for target_field, aliases in OPEN_VISIT_FIELD_MAP.items():
            source_field, value = _first_available(source, aliases)
            if source_field is None:
                open_visit[target_field] = NOT_AVAILABLE
                source_fields[target_field] = NOT_AVAILABLE
            else:
                open_visit[target_field] = deepcopy(value)
                source_fields[target_field] = source_field

        active_visit = open_visit["visit_id"] != NOT_AVAILABLE
        if not active_visit:
            for field_name in _VISIT_SPECIFIC_FIELDS:
                open_visit[field_name] = NOT_AVAILABLE
                source_fields[field_name] = NOT_AVAILABLE

        open_visit["active_visit_flag"] = active_visit
        open_visit["source_fields"] = source_fields
        open_visit["adapter_mode"] = "SHADOW_MAPPING_ONLY"
        return {"open_visit": open_visit}


def _first_available(
    source: InteractionState | Mapping[str, Any],
    aliases: tuple[str, ...],
) -> tuple[str | None, Any]:
    for source_field in aliases:
        found, value = _read_source(source, source_field)
        if found and _is_available(value):
            return source_field, value
    return None, NOT_AVAILABLE


def _read_source(
    source: InteractionState | Mapping[str, Any],
    field_name: str,
) -> tuple[bool, Any]:
    if isinstance(source, Mapping):
        if field_name not in source:
            return False, None
        return True, source[field_name]
    if not hasattr(source, field_name):
        return False, None
    return True, getattr(source, field_name)


def _is_available(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    return True


__all__ = [
    "OPEN_VISIT_FIELD_MAP",
    "OpenVisitAdapter",
]

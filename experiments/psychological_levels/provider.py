"""Offline Psychological Levels test geometry provider.

Experimental only. This module has no RDM, snapshot, worker, live, dashboard,
or Project 1 integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from typing import Any


GEOMETRY_SOURCE = "PSYCHOLOGICAL_LEVELS_TEST"
GEOMETRY_TYPE = "FIXED_PSYCHOLOGICAL_LEVEL"
GEOMETRY_VERSION = "PSY_LEVEL_GEOMETRY_V1"
PROVIDER_VERSION = "PSY_LEVEL_PROVIDER_V1"


@dataclass(frozen=True)
class PsychologicalLevelGeometry:
    geometry_source: str
    geometry_type: str
    geometry_version: str
    symbol: str
    level_center: Decimal
    lower_edge: Decimal
    upper_edge: Decimal
    zone_width: Decimal
    zone_half_width: Decimal
    spacing: Decimal
    level_index: int
    market_timestamp: Any
    session_id: str
    zone_id: str
    case_id: str
    global_zone_key: str
    reference_price: Decimal
    anchor_level: Decimal
    levels_above: int
    levels_below: int
    provider_version: str
    shadow_only: bool = True


class PsychologicalLevelsProvider:
    """Generate deterministic fixed-width geometry around a reference price."""

    def __init__(
        self,
        *,
        spacing: Any = Decimal("200"),
        zone_half_width: Any = Decimal("25"),
        active_window: int = 3,
        provider_version: str = PROVIDER_VERSION,
    ) -> None:
        self.spacing = _decimal(spacing, "spacing")
        self.zone_half_width = _decimal(
            zone_half_width,
            "zone_half_width",
        )
        if self.spacing <= 0:
            raise ValueError("spacing must be greater than zero")
        if self.zone_half_width <= 0:
            raise ValueError("zone_half_width must be greater than zero")
        if self.zone_half_width * 2 >= self.spacing:
            raise ValueError(
                "2 * zone_half_width must be less than spacing"
            )
        if isinstance(active_window, bool) or not isinstance(
            active_window,
            int,
        ):
            raise TypeError("active_window must be an integer")
        if active_window < 0:
            raise ValueError("active_window must be non-negative")
        if not str(provider_version).strip():
            raise ValueError("provider_version must not be empty")
        self.active_window = active_window
        self.provider_version = str(provider_version).strip()

    def generate(
        self,
        *,
        price: Any,
        symbol: str,
        market_timestamp: Any,
        session_id: str,
    ) -> tuple[PsychologicalLevelGeometry, ...]:
        reference_price = _decimal(price, "price")
        normalized_symbol = str(symbol).strip().upper()
        normalized_session = str(session_id).strip()
        if not normalized_symbol:
            raise ValueError("symbol must not be empty")
        if not normalized_session:
            raise ValueError("session_id must not be empty")

        anchor = (
            (
                (reference_price + self.spacing / 2)
                / self.spacing
            ).to_integral_value(rounding=ROUND_FLOOR)
            * self.spacing
        )
        zone_width = self.zone_half_width * 2
        geometries: list[PsychologicalLevelGeometry] = []

        for level_index in range(
            -self.active_window,
            self.active_window + 1,
        ):
            center = anchor + self.spacing * level_index
            level_identity = canonical_decimal(center)
            zone_id = f"PSY_{normalized_symbol}_{level_identity}"
            case_id = (
                f"PSY_CASE_{normalized_symbol}_{level_identity}"
            )
            geometries.append(
                PsychologicalLevelGeometry(
                    geometry_source=GEOMETRY_SOURCE,
                    geometry_type=GEOMETRY_TYPE,
                    geometry_version=GEOMETRY_VERSION,
                    symbol=normalized_symbol,
                    level_center=center,
                    lower_edge=center - self.zone_half_width,
                    upper_edge=center + self.zone_half_width,
                    zone_width=zone_width,
                    zone_half_width=self.zone_half_width,
                    spacing=self.spacing,
                    level_index=level_index,
                    market_timestamp=market_timestamp,
                    session_id=normalized_session,
                    zone_id=zone_id,
                    case_id=case_id,
                    global_zone_key=(
                        f"{normalized_session}::{zone_id}"
                    ),
                    reference_price=reference_price,
                    anchor_level=anchor,
                    levels_above=self.active_window,
                    levels_below=self.active_window,
                    provider_version=self.provider_version,
                )
            )

        return tuple(geometries)


def canonical_decimal(value: Decimal) -> str:
    """Return a non-exponent, identity-stable Decimal representation."""
    if not isinstance(value, Decimal):
        value = _decimal(value, "value")
    if value == 0:
        return "0"
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _decimal(value: Any, field_name: str) -> Decimal:
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must be decimal-compatible") from error
    if not result.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return result


__all__ = [
    "GEOMETRY_SOURCE",
    "GEOMETRY_TYPE",
    "GEOMETRY_VERSION",
    "PROVIDER_VERSION",
    "PsychologicalLevelGeometry",
    "PsychologicalLevelsProvider",
    "canonical_decimal",
]

"""Immutable external geometry contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal


def _text(value: Decimal) -> str:
    normalized = value.normalize()
    return "0" if normalized == 0 else format(normalized, "f")


@dataclass(frozen=True)
class GeometryReference:
    zone_id: str
    center_price: Decimal
    lower_price: Decimal
    upper_price: Decimal
    half_width: Decimal

    def __post_init__(self) -> None:
        if not self.zone_id.strip():
            raise ValueError("zone_id must not be empty")
        if not all(
            isinstance(value, Decimal)
            for value in (
                self.center_price,
                self.lower_price,
                self.upper_price,
                self.half_width,
            )
        ):
            raise TypeError("prices must be Decimal")
        if self.half_width <= 0 or self.lower_price >= self.upper_price:
            raise ValueError("invalid geometry")
        if (
            self.center_price != (self.lower_price + self.upper_price) / Decimal(2)
            or self.half_width != self.center_price - self.lower_price
        ):
            raise ValueError("inconsistent geometry")

    def canonical_value(self) -> dict[str, str]:
        return {
            "zone_id": self.zone_id,
            "center_price": _text(self.center_price),
            "lower_price": _text(self.lower_price),
            "upper_price": _text(self.upper_price),
            "half_width": _text(self.half_width),
        }


@dataclass(frozen=True)
class GeometryContext:
    symbol: str
    geometry_version: str
    references: tuple[GeometryReference, ...]
    geometry_fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.symbol.strip() or not self.geometry_version.strip():
            raise ValueError("identity must not be empty")
        if (
            not isinstance(self.references, tuple)
            or not self.references
            or not all(
                isinstance(value, GeometryReference) for value in self.references
            )
        ):
            raise TypeError("references must be an immutable GeometryReference tuple")

        ordered = tuple(sorted(self.references, key=lambda value: value.zone_id))
        if len({value.zone_id for value in ordered}) != len(ordered):
            raise ValueError("zone IDs must be unique")

        raw = json.dumps(
            {
                "symbol": self.symbol,
                "geometry_version": self.geometry_version,
                "references": [value.canonical_value() for value in ordered],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        object.__setattr__(self, "references", ordered)
        object.__setattr__(
            self,
            "geometry_fingerprint",
            "sha256:" + hashlib.sha256(raw.encode()).hexdigest(),
        )

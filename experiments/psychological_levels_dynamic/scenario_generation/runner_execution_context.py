"""Immutable context required by future scenario runner execution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from experiments.psychological_levels_dynamic.scenario_catalog.compiler.geometry import (
    GeometryContext,
)


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        normalized = value.normalize()
        return "0" if normalized == 0 else format(normalized, "f")
    if isinstance(value, tuple):
        return tuple(_canonical_value(item) for item in value)
    if isinstance(value, list):
        return tuple(_canonical_value(item) for item in value)
    if isinstance(value, dict):
        return tuple(
            (str(key), _canonical_value(item))
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        )
    return value


def _fingerprint_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        _canonical_value(payload),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RunnerExecutionContext:
    symbol: str
    geometry_context: GeometryContext
    active_window: int
    spacing: Decimal
    zone_half_width: Decimal
    market_timestamp: int
    session_id: str
    runner_version: str
    execution_context_fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        if not isinstance(self.geometry_context, GeometryContext):
            raise TypeError("geometry_context must be GeometryContext")
        if not isinstance(self.active_window, int) or self.active_window < 0:
            raise ValueError("active_window must be non-negative int")
        if not isinstance(self.spacing, Decimal) or self.spacing <= 0:
            raise ValueError("spacing must be positive Decimal")
        if not isinstance(self.zone_half_width, Decimal) or self.zone_half_width <= 0:
            raise ValueError("zone_half_width must be positive Decimal")
        if self.zone_half_width * Decimal(2) >= self.spacing:
            raise ValueError("zone width must be less than spacing")
        if not isinstance(self.market_timestamp, int) or self.market_timestamp < 0:
            raise ValueError("market_timestamp must be non-negative int")
        if not self.session_id.strip():
            raise ValueError("session_id must not be empty")
        if not self.runner_version.strip():
            raise ValueError("runner_version must not be empty")
        if self.symbol != self.geometry_context.symbol:
            raise ValueError("symbol must match geometry_context.symbol")

        object.__setattr__(
            self,
            "execution_context_fingerprint",
            _fingerprint_payload(
                {
                    "symbol": self.symbol,
                    "geometry_fingerprint": self.geometry_context.geometry_fingerprint,
                    "active_window": self.active_window,
                    "spacing": self.spacing,
                    "zone_half_width": self.zone_half_width,
                    "market_timestamp": self.market_timestamp,
                    "session_id": self.session_id,
                    "runner_version": self.runner_version,
                }
            ),
        )
"""Shadow-only feature flag reader (Phase 0A safety scaffolding).

Fail-closed: every flag defaults OFF. Reading flags has no side effects and
never raises -- any parse/lookup error resolves to the safe default. No
production module imports this.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any, Mapping


_TRUTHY = frozenset({"1", "true", "yes", "on", "enabled"})

ENV_ENABLED = "SHADOW_RUNTIME_ENABLED"
ENV_DRY_RUN = "SHADOW_DRY_RUN"
ENV_SAMPLE_RATE = "SHADOW_SAMPLE_RATE"


def _truthy(value: Any) -> bool:
    if value is None:
        return False
    try:
        return str(value).strip().lower() in _TRUTHY
    except Exception:
        return False


def _clamp_rate(value: Any) -> float:
    try:
        rate = float(value)
    except (TypeError, ValueError):
        return 1.0
    if rate != rate:  # NaN
        return 1.0
    return min(max(rate, 0.0), 1.0)


def _bucket(key: Any) -> float:
    digest = hashlib.md5(repr(key).encode("utf-8")).hexdigest()
    return (int(digest[:8], 16) % 1000) / 1000.0


@dataclass(frozen=True)
class FeatureFlags:
    """Immutable snapshot of the shadow runtime flags. Defaults are all OFF."""

    enabled: bool = False
    dry_run: bool = False
    sample_rate: float = 1.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "FeatureFlags":
        source = os.environ if env is None else env
        try:
            enabled = _truthy(source.get(ENV_ENABLED))
            dry_run = _truthy(source.get(ENV_DRY_RUN))
            raw_rate = source.get(ENV_SAMPLE_RATE)
            sample_rate = (
                _clamp_rate(raw_rate) if raw_rate is not None else 1.0
            )
        except Exception:
            return cls()  # fail-closed: everything OFF / default
        return cls(enabled=enabled, dry_run=dry_run, sample_rate=sample_rate)

    def should_run(self) -> bool:
        """Master gate: only True when explicitly enabled."""
        return bool(self.enabled)

    def should_sample(self, key: Any) -> bool:
        """Deterministic per-key sampling within sample_rate (default: all)."""
        if not self.enabled:
            return False
        if self.sample_rate >= 1.0:
            return True
        if self.sample_rate <= 0.0:
            return False
        return _bucket(("shadow_sample", key)) < self.sample_rate


__all__ = [
    "ENV_DRY_RUN",
    "ENV_ENABLED",
    "ENV_SAMPLE_RATE",
    "FeatureFlags",
]

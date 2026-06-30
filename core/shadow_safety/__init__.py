"""Shadow-only safety scaffolding (Phase 0A).

Standalone, fail-closed building blocks for the (not-yet-wired) Passive Shadow
Runtime: feature flags, kill switch / circuit breaker, bounded drop-on-full
queue, isolated worker wrapper, and a parity log writer. No production module
imports this package; nothing here touches the LIVE pipeline.
"""

from __future__ import annotations

from core.shadow_safety.bounded_queue import BoundedDropQueue
from core.shadow_safety.feature_flag import FeatureFlags
from core.shadow_safety.isolated_worker import IsolatedWorker
from core.shadow_safety.kill_switch import (
    CircuitBreaker,
    KillSwitch,
    manual_kill_active,
)
from core.shadow_safety.parity_log import PARITY_DIR, ParityLogWriter

__all__ = [
    "BoundedDropQueue",
    "CircuitBreaker",
    "FeatureFlags",
    "IsolatedWorker",
    "KillSwitch",
    "PARITY_DIR",
    "ParityLogWriter",
    "manual_kill_active",
]

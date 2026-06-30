"""Shadow-only kill switch and latching circuit breaker (Phase 0A).

ALLOW by default; latches into a KILLED state that blocks all further shadow
work until an explicit reset(). Fail-closed: an unreadable manual kill source
resolves to KILLED. No production module imports this.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping


_TRUTHY = frozenset({"1", "true", "yes", "on"})
ENV_KILL = "SHADOW_KILL"


def _truthy(value: Any) -> bool:
    if value is None:
        return False
    try:
        return str(value).strip().lower() in _TRUTHY
    except Exception:
        return True  # fail-closed


def manual_kill_active(
    *,
    env: Mapping[str, str] | None = None,
    kill_file: str | Path | None = None,
) -> bool:
    """True when a manual kill is requested via env var or on-disk flag file.

    Fail-closed: if the kill state cannot be read, the shadow is treated as
    KILLED.
    """
    source = os.environ if env is None else env
    try:
        if _truthy(source.get(ENV_KILL)):
            return True
        if kill_file is not None and Path(kill_file).exists():
            return True
        return False
    except Exception:
        return True


class CircuitBreaker:
    """Latching breaker: once KILLED it stays KILLED until reset()."""

    def __init__(self, *, max_consecutive_failures: int = 5) -> None:
        if int(max_consecutive_failures) < 1:
            raise ValueError("max_consecutive_failures must be >= 1")
        self._max = int(max_consecutive_failures)
        self._killed = False
        self._reason = ""
        self._consecutive = 0
        self._failures = 0
        self._successes = 0

    @property
    def killed(self) -> bool:
        return self._killed

    @property
    def reason(self) -> str:
        return self._reason

    def allows(self) -> bool:
        return not self._killed

    def trip(self, reason: str) -> None:
        if not self._killed:
            self._killed = True
            self._reason = str(reason) or "tripped"

    def record_success(self) -> None:
        self._successes += 1
        self._consecutive = 0  # never un-latches an existing kill

    def record_failure(self, reason: str = "") -> None:
        self._failures += 1
        self._consecutive += 1
        if self._consecutive >= self._max:
            self.trip(reason or f"consecutive_failures>={self._max}")

    def reset(self) -> None:
        self._killed = False
        self._reason = ""
        self._consecutive = 0

    def stats(self) -> dict:
        return {
            "killed": self._killed,
            "reason": self._reason,
            "consecutive_failures": self._consecutive,
            "total_failures": self._failures,
            "total_successes": self._successes,
            "max_consecutive_failures": self._max,
        }


class KillSwitch:
    """Combine the latching breaker with manual (env / file) kill sources."""

    def __init__(
        self,
        *,
        breaker: CircuitBreaker | None = None,
        env: Mapping[str, str] | None = None,
        kill_file: str | Path | None = None,
    ) -> None:
        self._breaker = breaker or CircuitBreaker()
        self._env = env
        self._kill_file = kill_file

    @property
    def breaker(self) -> CircuitBreaker:
        return self._breaker

    def allows(self) -> bool:
        if manual_kill_active(env=self._env, kill_file=self._kill_file):
            return False
        return self._breaker.allows()

    def record_success(self) -> None:
        self._breaker.record_success()

    def record_failure(self, reason: str = "") -> None:
        self._breaker.record_failure(reason)

    def trip(self, reason: str) -> None:
        self._breaker.trip(reason)

    def stats(self) -> dict:
        return {
            "manual_kill": manual_kill_active(
                env=self._env, kill_file=self._kill_file
            ),
            "breaker": self._breaker.stats(),
        }


__all__ = [
    "CircuitBreaker",
    "ENV_KILL",
    "KillSwitch",
    "manual_kill_active",
]

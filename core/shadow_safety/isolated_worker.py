"""Shadow-only isolated worker wrapper (Phase 0A).

process() runs a handler in isolation: exceptions are swallowed and counted (and
fed to a CircuitBreaker), never propagated -- except KeyboardInterrupt and
SystemExit, which are re-raised so the host process can still be stopped. No
production module imports this.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from core.shadow_safety.kill_switch import CircuitBreaker


class IsolatedWorker:
    """Run a handler per item behind an isolation + circuit-breaker boundary."""

    def __init__(
        self,
        handler: Callable[[Any], None],
        *,
        breaker: Optional[CircuitBreaker] = None,
        on_error: Optional[Callable[[BaseException, Any], None]] = None,
    ) -> None:
        if not callable(handler):
            raise TypeError("handler must be callable")
        self._handler = handler
        self._breaker = breaker or CircuitBreaker()
        self._on_error = on_error
        self._processed = 0
        self._failures = 0
        self._skipped = 0

    @property
    def breaker(self) -> CircuitBreaker:
        return self._breaker

    @property
    def processed(self) -> int:
        return self._processed

    @property
    def failures(self) -> int:
        return self._failures

    @property
    def skipped(self) -> int:
        return self._skipped

    def process(self, item: Any) -> bool:
        """Run handler(item) in isolation.

        Returns True on success, False on a swallowed error or when the breaker
        has latched KILLED. Never raises except KeyboardInterrupt / SystemExit.
        """
        if not self._breaker.allows():
            self._skipped += 1
            return False
        try:
            self._handler(item)
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException as exc:  # intentional isolation boundary
            self._failures += 1
            self._breaker.record_failure(type(exc).__name__)
            if self._on_error is not None:
                try:
                    self._on_error(exc, item)
                except Exception:
                    pass
            return False
        self._processed += 1
        self._breaker.record_success()
        return True

    def drain(self, source: Any, *, max_items: Optional[int] = None) -> dict:
        """Poll items from a BoundedDropQueue-like source and process each."""
        count = 0
        while max_items is None or count < max_items:
            item = source.poll()
            if item is None:
                break
            self.process(item)
            count += 1
        return {
            "drained": count,
            "processed": self._processed,
            "failures": self._failures,
            "skipped": self._skipped,
        }

    def stats(self) -> dict:
        return {
            "processed": self._processed,
            "failures": self._failures,
            "skipped": self._skipped,
            "breaker": self._breaker.stats(),
        }


__all__ = ["IsolatedWorker"]

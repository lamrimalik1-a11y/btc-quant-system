"""Fail-safe lifecycle bootstrap for the passive shadow runtime (Phase 0F)."""

from __future__ import annotations

from typing import Any, Optional

from core.passive_shadow_worker import PassiveShadowWorker
from core.shadow_parity_runtime import ParityLoggingShadowHandler
from core.shadow_runtime_emitter import get_default_emitter
from core.shadow_safety.bounded_queue import BoundedDropQueue
from core.shadow_safety.feature_flag import FeatureFlags
from core.shadow_safety.kill_switch import KillSwitch


BOOTSTRAP_DISABLED = "DISABLED"
BOOTSTRAP_KILLED = "KILLED"
BOOTSTRAP_STARTED = "STARTED"
BOOTSTRAP_ALREADY_RUNNING = "ALREADY_RUNNING"
BOOTSTRAP_STOPPED = "STOPPED"
BOOTSTRAP_ERROR = "ERROR"


class PassiveShadowBootstrap:
    """Own the optional worker lifecycle without affecting its caller."""

    def __init__(
        self,
        *,
        flags: FeatureFlags | None = None,
        kill_switch: KillSwitch | None = None,
        queue: BoundedDropQueue | None = None,
        handler: Any = None,
    ) -> None:
        self._flags = flags if flags is not None else FeatureFlags.from_env()
        self._kill = kill_switch if kill_switch is not None else KillSwitch()
        self._queue = queue
        self._handler = handler
        self._worker: Optional[PassiveShadowWorker] = None
        self._last_status = BOOTSTRAP_DISABLED
        self._errors = 0

    @property
    def worker(self) -> Optional[PassiveShadowWorker]:
        return self._worker

    @property
    def running(self) -> bool:
        return bool(self._worker is not None and self._worker.running)

    def start(self) -> str:
        """Start only when explicitly enabled. Never raise to production."""
        try:
            if not self._flags.should_run():
                self._last_status = BOOTSTRAP_DISABLED
                return self._last_status
            if not self._kill.allows():
                self._last_status = BOOTSTRAP_KILLED
                return self._last_status
            if self.running:
                self._last_status = BOOTSTRAP_ALREADY_RUNNING
                return self._last_status

            queue = self._queue
            if queue is None:
                queue = get_default_emitter().queue
                self._queue = queue
            handler = self._handler
            if handler is None:
                handler = ParityLoggingShadowHandler()
                self._handler = handler

            worker = PassiveShadowWorker(
                queue=queue,
                handler=handler,
                flags=self._flags,
                kill_switch=self._kill,
            )
            if hasattr(handler, "set_counters_provider"):
                handler.set_counters_provider(worker.stats)
            if not worker.start():
                self._last_status = (
                    BOOTSTRAP_KILLED
                    if not self._kill.allows()
                    else BOOTSTRAP_DISABLED
                )
                return self._last_status
            self._worker = worker
            self._last_status = BOOTSTRAP_STARTED
            return self._last_status
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:
            self._errors += 1
            self._last_status = BOOTSTRAP_ERROR
            return self._last_status

    def stop(self, *, drain_timeout_seconds: float = 2.0) -> str:
        """Stop with a bounded drain. Never raise to production."""
        try:
            worker = self._worker
            if worker is not None:
                worker.stop(drain_timeout_seconds=drain_timeout_seconds)
            self._last_status = BOOTSTRAP_STOPPED
            return self._last_status
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:
            self._errors += 1
            self._last_status = BOOTSTRAP_ERROR
            return self._last_status

    def stats(self) -> dict[str, Any]:
        try:
            worker_stats = self._worker.stats() if self._worker else {}
        except Exception:
            worker_stats = {}
        return {
            "status": self._last_status,
            "enabled": self._flags.should_run(),
            "running": self.running,
            "errors": self._errors,
            "worker": worker_stats,
        }


_default_bootstrap: Optional[PassiveShadowBootstrap] = None


def get_default_bootstrap() -> PassiveShadowBootstrap:
    global _default_bootstrap
    if _default_bootstrap is None:
        _default_bootstrap = PassiveShadowBootstrap()
    return _default_bootstrap


def start_passive_shadow() -> str:
    """Fail-safe process lifecycle entry point."""
    try:
        return get_default_bootstrap().start()
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:
        return BOOTSTRAP_ERROR


def stop_passive_shadow(*, drain_timeout_seconds: float = 2.0) -> str:
    """Fail-safe process lifecycle exit point."""
    try:
        return get_default_bootstrap().stop(
            drain_timeout_seconds=drain_timeout_seconds
        )
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:
        return BOOTSTRAP_ERROR


__all__ = [
    "BOOTSTRAP_ALREADY_RUNNING",
    "BOOTSTRAP_DISABLED",
    "BOOTSTRAP_ERROR",
    "BOOTSTRAP_KILLED",
    "BOOTSTRAP_STARTED",
    "BOOTSTRAP_STOPPED",
    "PassiveShadowBootstrap",
    "get_default_bootstrap",
    "start_passive_shadow",
    "stop_passive_shadow",
]

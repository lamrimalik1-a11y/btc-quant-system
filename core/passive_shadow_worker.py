"""Passive shadow payload worker skeleton (Phase 0E-1).

This module only drains a BoundedDropQueue through an isolated no-op-style
handler. It does not invoke the shadow runtime, adapters, snapshots, or writers.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Optional

from core.shadow_safety.bounded_queue import BoundedDropQueue
from core.shadow_safety.feature_flag import FeatureFlags
from core.shadow_safety.kill_switch import KillSwitch


class PassiveShadowWorker:
    """Background, drop-safe consumer for shadow payloads."""

    def __init__(
        self,
        *,
        queue: BoundedDropQueue,
        handler: Optional[Callable[[Any], None]] = None,
        flags: FeatureFlags | None = None,
        kill_switch: KillSwitch | None = None,
        poll_interval_seconds: float = 0.01,
    ) -> None:
        if not isinstance(queue, BoundedDropQueue):
            raise TypeError("queue must be a BoundedDropQueue")
        if handler is not None and not callable(handler):
            raise TypeError("handler must be callable")
        if float(poll_interval_seconds) <= 0:
            raise ValueError("poll_interval_seconds must be > 0")

        self._queue = queue
        self._handler = handler if handler is not None else self._noop_handler
        self._flags = flags if flags is not None else FeatureFlags.from_env()
        self._kill = kill_switch if kill_switch is not None else KillSwitch()
        self._poll_interval = float(poll_interval_seconds)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._received = 0
        self._processed = 0
        self._failed = 0
        self._killed = 0
        self._desynchronized = 0
        self._observed_queue_drops = queue.dropped

    @staticmethod
    def _noop_handler(payload: Any) -> None:
        del payload

    @property
    def running(self) -> bool:
        thread = self._thread
        return bool(thread is not None and thread.is_alive())

    def start(self) -> bool:
        """Start the daemon worker when enabled and not killed."""
        with self._lock:
            if self.running:
                return True
            if not self._flags.should_run() or not self._kill.allows():
                return False
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="passive-shadow-worker",
                daemon=True,
            )
            self._thread.start()
            return True

    def stop(self, *, drain_timeout_seconds: float = 0.0) -> bool:
        """Request stop, optionally allowing a bounded queue drain first."""
        timeout = max(float(drain_timeout_seconds), 0.0)
        deadline = time.monotonic() + timeout
        while (
            timeout > 0
            and self.running
            and self._queue.qsize() > 0
            and self._flags.should_run()
            and self._kill.allows()
            and time.monotonic() < deadline
        ):
            time.sleep(min(self._poll_interval, max(deadline - time.monotonic(), 0)))

        self._stop_event.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=max(timeout, self._poll_interval * 2))
        return not self.running

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._observe_drops()
            if not self._flags.should_run():
                self._stop_event.wait(self._poll_interval)
                continue
            if not self._kill.allows():
                with self._lock:
                    self._killed += 1
                self._stop_event.set()
                break

            payload = self._queue.poll()
            if payload is None:
                self._stop_event.wait(self._poll_interval)
                continue

            with self._lock:
                self._received += 1
            try:
                self._handler(payload)
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException as exc:
                with self._lock:
                    self._failed += 1
                try:
                    self._kill.record_failure(type(exc).__name__)
                except Exception:
                    pass
                continue

            with self._lock:
                self._processed += 1
            try:
                self._kill.record_success()
            except Exception:
                pass

        self._observe_drops()

    def _observe_drops(self) -> None:
        current = self._queue.dropped
        with self._lock:
            delta = max(current - self._observed_queue_drops, 0)
            if delta:
                self._desynchronized += delta
                self._observed_queue_drops = current

    def stats(self) -> dict:
        self._observe_drops()
        with self._lock:
            return {
                "received": self._received,
                "processed": self._processed,
                "dropped": self._queue.dropped,
                "failed": self._failed,
                "killed": self._killed,
                "desynchronized": self._desynchronized,
                "running": self.running,
                "queue_size": self._queue.qsize(),
            }


__all__ = ["PassiveShadowWorker"]

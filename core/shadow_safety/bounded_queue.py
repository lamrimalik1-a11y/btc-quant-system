"""Shadow-only bounded, non-blocking queue with drop-on-full (Phase 0A).

offer() never blocks and never raises; when the queue is full the item is
dropped and counted, so the producer (the LIVE loop) is never throttled by
shadow throughput. No production module imports this.
"""

from __future__ import annotations

import queue
import threading
from typing import Any


class BoundedDropQueue:
    """Fixed-size FIFO. Non-blocking offer/poll; full -> drop and count."""

    def __init__(self, maxsize: int) -> None:
        if int(maxsize) < 1:
            raise ValueError("maxsize must be >= 1")
        self._q: "queue.Queue[Any]" = queue.Queue(maxsize=int(maxsize))
        self._lock = threading.Lock()
        self._enqueued = 0
        self._dropped = 0

    def offer(self, item: Any) -> bool:
        """Non-blocking enqueue. True if stored, False if dropped. Never raises."""
        try:
            self._q.put_nowait(item)
        except queue.Full:
            with self._lock:
                self._dropped += 1
            return False
        except Exception:
            with self._lock:
                self._dropped += 1
            return False
        with self._lock:
            self._enqueued += 1
        return True

    def poll(self) -> Any:
        """Non-blocking dequeue. Returns the item or None if empty. Never raises."""
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return None
        except Exception:
            return None

    def qsize(self) -> int:
        return self._q.qsize()

    @property
    def maxsize(self) -> int:
        return self._q.maxsize

    @property
    def enqueued(self) -> int:
        with self._lock:
            return self._enqueued

    @property
    def dropped(self) -> int:
        with self._lock:
            return self._dropped

    def stats(self) -> dict:
        with self._lock:
            return {
                "enqueued": self._enqueued,
                "dropped": self._dropped,
                "qsize": self._q.qsize(),
                "maxsize": self._q.maxsize,
            }


__all__ = ["BoundedDropQueue"]

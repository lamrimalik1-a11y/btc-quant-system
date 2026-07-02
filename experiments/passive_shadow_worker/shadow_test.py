"""Shadow validation for the Phase 0E-1 passive worker skeleton."""

from __future__ import annotations

import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.passive_shadow_worker import PassiveShadowWorker
from core.shadow_safety.bounded_queue import BoundedDropQueue
from core.shadow_safety.feature_flag import FeatureFlags
from core.shadow_safety.kill_switch import CircuitBreaker, KillSwitch


def wait_until(predicate, timeout: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return bool(predicate())


def test_disabled_worker_does_nothing() -> None:
    queue = BoundedDropQueue(maxsize=4)
    queue.offer({"payload": 1})
    worker = PassiveShadowWorker(
        queue=queue,
        flags=FeatureFlags(enabled=False),
    )
    assert worker.start() is False
    time.sleep(0.02)
    assert queue.qsize() == 1
    assert worker.stats()["received"] == 0
    print("DISABLED_WORKER_DOES_NOTHING = PASS")


def test_kill_switch_stops_processing() -> None:
    queue = BoundedDropQueue(maxsize=4)
    breaker = CircuitBreaker()
    worker = PassiveShadowWorker(
        queue=queue,
        flags=FeatureFlags(enabled=True),
        kill_switch=KillSwitch(breaker=breaker, env={}),
    )
    assert worker.start()
    breaker.trip("shadow_test")
    queue.offer({"payload": 1})
    assert wait_until(lambda: not worker.running)
    stats = worker.stats()
    assert stats["killed"] == 1
    assert stats["processed"] == 0
    assert queue.qsize() == 1
    print("KILL_SWITCH_STOPS_PROCESSING = PASS")


def test_queue_saturation_drops_without_blocking() -> None:
    queue = BoundedDropQueue(maxsize=1)
    worker = PassiveShadowWorker(
        queue=queue,
        flags=FeatureFlags(enabled=False),
    )
    assert queue.offer({"payload": 0})
    start = time.monotonic()
    accepted = [queue.offer({"payload": i}) for i in range(2000)]
    elapsed = time.monotonic() - start
    stats = worker.stats()
    assert not any(accepted)
    assert stats["dropped"] == 2000
    assert stats["desynchronized"] == 2000
    assert elapsed < 5.0
    print("QUEUE_SATURATION_NON_BLOCKING = PASS", round(elapsed, 4))


def test_handler_exception_is_isolated() -> None:
    queue = BoundedDropQueue(maxsize=4)

    def failing_handler(payload):
        del payload
        raise ValueError("expected")

    worker = PassiveShadowWorker(
        queue=queue,
        handler=failing_handler,
        flags=FeatureFlags(enabled=True),
        kill_switch=KillSwitch(
            breaker=CircuitBreaker(max_consecutive_failures=5),
            env={},
        ),
    )
    queue.offer({"payload": 1})
    assert worker.start()
    assert wait_until(lambda: worker.stats()["failed"] == 1)
    assert worker.stop(drain_timeout_seconds=0.1)
    stats = worker.stats()
    assert stats["received"] == 1
    assert stats["processed"] == 0
    assert stats["failed"] == 1
    print("HANDLER_EXCEPTION_ISOLATED = PASS")


def test_start_stop_and_drain() -> None:
    queue = BoundedDropQueue(maxsize=8)
    handled = []
    worker = PassiveShadowWorker(
        queue=queue,
        handler=handled.append,
        flags=FeatureFlags(enabled=True),
        kill_switch=KillSwitch(env={}),
    )
    for value in range(4):
        assert queue.offer(value)
    assert worker.start()
    assert worker.stop(drain_timeout_seconds=1.0)
    assert handled == [0, 1, 2, 3]
    stats = worker.stats()
    assert stats["received"] == 4
    assert stats["processed"] == 4
    assert stats["failed"] == 0
    assert stats["running"] is False
    print("START_STOP_DRAIN = PASS")


def main() -> None:
    test_disabled_worker_does_nothing()
    test_kill_switch_stops_processing()
    test_queue_saturation_drops_without_blocking()
    test_handler_exception_is_isolated()
    test_start_stop_and_drain()
    print("PASSIVE_SHADOW_WORKER_TEST = PASS")
    print("NO_FULL_RUNTIME = TRUE")
    print("NO_SNAPSHOT_UPDATE = TRUE")
    print("NO_PRODUCTION_INTEGRATION = TRUE")


if __name__ == "__main__":
    main()


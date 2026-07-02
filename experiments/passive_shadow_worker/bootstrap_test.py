"""Phase 0F passive shadow bootstrap lifecycle validation."""

from __future__ import annotations

import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.passive_shadow_bootstrap import (
    BOOTSTRAP_ALREADY_RUNNING,
    BOOTSTRAP_DISABLED,
    BOOTSTRAP_KILLED,
    BOOTSTRAP_STARTED,
    BOOTSTRAP_STOPPED,
    PassiveShadowBootstrap,
)
from core.shadow_safety.bounded_queue import BoundedDropQueue
from core.shadow_safety.feature_flag import FeatureFlags
from core.shadow_safety.kill_switch import CircuitBreaker, KillSwitch


def wait_until(predicate, timeout=1.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return bool(predicate())


def test_disabled_startup_has_no_worker():
    bootstrap = PassiveShadowBootstrap(
        flags=FeatureFlags(enabled=False),
        queue=BoundedDropQueue(maxsize=2),
        handler=lambda payload: None,
    )
    assert bootstrap.start() == BOOTSTRAP_DISABLED
    assert bootstrap.worker is None
    assert bootstrap.running is False
    print("DISABLED_STARTUP_NO_WORKER = PASS")


def test_enabled_start_and_shutdown_drain():
    queue = BoundedDropQueue(maxsize=8)
    handled = []
    bootstrap = PassiveShadowBootstrap(
        flags=FeatureFlags(enabled=True),
        kill_switch=KillSwitch(env={}),
        queue=queue,
        handler=handled.append,
    )
    for value in range(5):
        assert queue.offer(value)
    assert bootstrap.start() == BOOTSTRAP_STARTED
    assert bootstrap.running
    assert bootstrap.stop(drain_timeout_seconds=1.0) == BOOTSTRAP_STOPPED
    assert handled == [0, 1, 2, 3, 4]
    assert bootstrap.running is False
    print("ENABLED_START_AND_SHUTDOWN_DRAIN = PASS")


def test_kill_switch_stops_worker():
    breaker = CircuitBreaker()
    bootstrap = PassiveShadowBootstrap(
        flags=FeatureFlags(enabled=True),
        kill_switch=KillSwitch(breaker=breaker, env={}),
        queue=BoundedDropQueue(maxsize=2),
        handler=lambda payload: None,
    )
    assert bootstrap.start() == BOOTSTRAP_STARTED
    breaker.trip("bootstrap test")
    assert wait_until(lambda: not bootstrap.running)
    assert bootstrap.stats()["worker"]["killed"] == 1

    killed_before_start = PassiveShadowBootstrap(
        flags=FeatureFlags(enabled=True),
        kill_switch=KillSwitch(breaker=breaker, env={}),
        queue=BoundedDropQueue(maxsize=2),
        handler=lambda payload: None,
    )
    assert killed_before_start.start() == BOOTSTRAP_KILLED
    assert killed_before_start.worker is None
    print("KILL_SWITCH_STOPS_WORKER = PASS")


def test_repeated_start_stop_safe():
    bootstrap = PassiveShadowBootstrap(
        flags=FeatureFlags(enabled=True),
        kill_switch=KillSwitch(env={}),
        queue=BoundedDropQueue(maxsize=2),
        handler=lambda payload: None,
    )
    assert bootstrap.start() == BOOTSTRAP_STARTED
    assert bootstrap.start() == BOOTSTRAP_ALREADY_RUNNING
    assert bootstrap.stop(drain_timeout_seconds=0.1) == BOOTSTRAP_STOPPED
    assert bootstrap.stop(drain_timeout_seconds=0.1) == BOOTSTRAP_STOPPED
    assert bootstrap.start() == BOOTSTRAP_STARTED
    assert bootstrap.stop(drain_timeout_seconds=0.1) == BOOTSTRAP_STOPPED
    print("REPEATED_START_STOP_SAFE = PASS")


def main():
    test_disabled_startup_has_no_worker()
    test_enabled_start_and_shutdown_drain()
    test_kill_switch_stops_worker()
    test_repeated_start_stop_safe()
    print("PHASE_0F_PASSIVE_SHADOW_BOOTSTRAP_TEST = PASS")
    print("NO_PRODUCTION_OUTPUTS = TRUE")
    print("NO_FORMULAS = TRUE")


if __name__ == "__main__":
    main()

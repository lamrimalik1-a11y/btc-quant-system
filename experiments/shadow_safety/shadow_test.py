"""Shadow validation for the Phase 0A safety scaffolding modules.

Validates:
  - feature flags default OFF (fail-closed)
  - kill switch latches closed (and auto-trips on consecutive failures)
  - bounded queue drops on full and never blocks
  - isolated worker swallows + counts exceptions (never propagates)
  - parity logger writes only inside research/shadow_parity/
Shadow only: no production import, no live pipeline, no production outputs.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.shadow_safety import (
    BoundedDropQueue,
    CircuitBreaker,
    FeatureFlags,
    IsolatedWorker,
    KillSwitch,
    PARITY_DIR,
    ParityLogWriter,
    manual_kill_active,
)


def test_feature_flags_default_off() -> None:
    # No env -> everything OFF.
    default = FeatureFlags()
    assert default.enabled is False
    assert default.dry_run is False
    assert default.should_run() is False
    assert default.should_sample("zone") is False

    from_empty = FeatureFlags.from_env(env={})
    assert from_empty.enabled is False
    assert from_empty.should_run() is False

    # Garbage values stay OFF (fail-closed).
    assert FeatureFlags.from_env(env={"SHADOW_RUNTIME_ENABLED": "maybe"}).enabled is False

    # Explicit opt-in only.
    enabled = FeatureFlags.from_env(
        env={
            "SHADOW_RUNTIME_ENABLED": "1",
            "SHADOW_DRY_RUN": "true",
            "SHADOW_SAMPLE_RATE": "0.5",
        }
    )
    assert enabled.enabled is True
    assert enabled.dry_run is True
    assert enabled.sample_rate == 0.5
    assert enabled.should_run() is True
    # sample_rate 1.0 (default when enabled) processes all.
    assert FeatureFlags(enabled=True).should_sample("zone") is True
    print("FEATURE_FLAGS_DEFAULT_OFF = PASS")


def test_kill_switch_latches() -> None:
    breaker = CircuitBreaker(max_consecutive_failures=3)
    assert breaker.allows() is True

    # Manual trip latches: subsequent successes must NOT revive it.
    breaker.trip("manual")
    assert breaker.killed is True and breaker.allows() is False
    for _ in range(10):
        breaker.record_success()
    assert breaker.killed is True and breaker.allows() is False
    assert breaker.reason == "manual"
    # Only an explicit reset un-latches.
    breaker.reset()
    assert breaker.allows() is True

    # Auto-trip on consecutive failures.
    auto = CircuitBreaker(max_consecutive_failures=3)
    auto.record_failure("e1")
    auto.record_failure("e2")
    assert auto.allows() is True
    auto.record_failure("e3")
    assert auto.killed is True and auto.allows() is False

    # Manual kill via env / file resolves through KillSwitch and is fail-closed.
    assert manual_kill_active(env={"SHADOW_KILL": "1"}) is True
    assert manual_kill_active(env={}) is False
    ks = KillSwitch(env={"SHADOW_KILL": "1"})
    assert ks.allows() is False
    ks_ok = KillSwitch(env={})
    assert ks_ok.allows() is True
    print("KILL_SWITCH_LATCHES_CLOSED = PASS")


def test_bounded_queue_drop_on_full() -> None:
    q = BoundedDropQueue(maxsize=3)
    assert q.offer("a") and q.offer("b") and q.offer("c")
    assert q.qsize() == 3

    # Full -> drop, never block, never raise.
    start = time.monotonic()
    drops = sum(0 if q.offer(i) else 1 for i in range(10_000))
    elapsed = time.monotonic() - start
    assert drops == 10_000
    assert q.dropped == 10_000
    assert q.enqueued == 3
    assert elapsed < 5.0  # 10k full-offers complete near-instantly (non-blocking)

    # Poll drains FIFO; empty poll returns None (never raises).
    assert q.poll() == "a"
    assert q.poll() == "b"
    assert q.poll() == "c"
    assert q.poll() is None
    print("BOUNDED_QUEUE_DROP_ON_FULL = PASS", "elapsed_s", round(elapsed, 4))


def test_isolated_worker_swallows_and_counts() -> None:
    calls = {"n": 0}

    def boom(_item):
        calls["n"] += 1
        raise RuntimeError("synthetic handler failure")

    breaker = CircuitBreaker(max_consecutive_failures=3)
    worker = IsolatedWorker(boom, breaker=breaker)

    # Each failing call is swallowed (returns False) and counted.
    for _ in range(3):
        assert worker.process(object()) is False
    assert worker.failures == 3
    assert calls["n"] == 3
    # After 3 consecutive failures the breaker latched: handler not called again.
    assert breaker.killed is True
    assert worker.process(object()) is False
    assert worker.skipped == 1
    assert calls["n"] == 3  # handler was NOT invoked while killed

    # A healthy worker records success and never raises.
    seen = []
    ok = IsolatedWorker(lambda item: seen.append(item))
    assert ok.process("x") is True
    assert ok.processed == 1 and ok.failures == 0
    assert seen == ["x"]

    # drain() over a queue, with a mid-stream failure, stays isolated.
    q = BoundedDropQueue(maxsize=8)
    for v in (1, 2, "bad", 4):
        q.offer(v)

    def maybe_fail(item):
        if item == "bad":
            raise ValueError("bad item")

    drainer = IsolatedWorker(maybe_fail)
    result = drainer.drain(q)
    assert result["drained"] == 4
    assert drainer.processed == 3 and drainer.failures == 1
    print("ISOLATED_WORKER_SWALLOWS_AND_COUNTS = PASS")


def test_parity_logger_confined() -> None:
    # Default writer targets research/shadow_parity/ ONLY.
    default = ParityLogWriter()
    assert default.base_dir == PARITY_DIR.resolve()
    assert PARITY_DIR.parts[-2:] == ("research", "shadow_parity")

    # Path traversal outside the parity dir is rejected at construction.
    for escape in ("../escape.jsonl", "../../etc/passwd", "a/../../escape.jsonl"):
        try:
            ParityLogWriter(escape)
        except ValueError:
            pass
        else:
            raise AssertionError(f"escape path not rejected: {escape}")

    # A real append into the default parity dir, then cleaned up.
    probe = ParityLogWriter("shadow_safety_probe.jsonl")
    assert probe.path.parent == PARITY_DIR.resolve()
    try:
        probe.write({"event": "probe", "row_index": 1})
        probe.write({"event": "probe", "row_index": 2})
        assert probe.path.exists()
        lines = probe.path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        assert '"row_index": 2' in lines[1]
    finally:
        if probe.path.exists():
            probe.path.unlink()

    print("PARITY_LOGGER_CONFINED = PASS", "base", str(PARITY_DIR.parts[-2:]))


def main() -> None:
    test_feature_flags_default_off()
    test_kill_switch_latches()
    test_bounded_queue_drop_on_full()
    test_isolated_worker_swallows_and_counts()
    test_parity_logger_confined()
    print("SHADOW_SAFETY_SCAFFOLDING_TEST = PASS")
    print("NO_LIVE_TAP = TRUE")
    print("NO_PRODUCTION_INTEGRATION = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

"""Shadow validation for the Phase 0C shadow runtime emitter.

Validates:
  - disabled flag = no-op (nothing enqueued)
  - enabled flag enqueues payload
  - kill switch blocks emit
  - queue full drops without blocking
  - a bad record never raises
  - payload is deep-copied (isolated from source mutation)
  - global_zone_key generated (session_id::zone_id)
  - geometry_version generated (deterministic, from pinned edges)
Shadow only: no production import, no live tap, no production outputs.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.shadow_runtime_emitter import (
    EMIT_DISABLED,
    EMIT_DROPPED,
    EMIT_ENQUEUED,
    EMIT_ERROR,
    EMIT_KILLED,
    ShadowRuntimeEmitter,
)
from core.shadow_safety.bounded_queue import BoundedDropQueue
from core.shadow_safety.feature_flag import FeatureFlags
from core.shadow_safety.kill_switch import CircuitBreaker, KillSwitch


def make_record():
    return {
        "session_id": "BTCUSDT_2026-06-28_230000Z",
        "zone_id": "ZONE_7",
        "case_id": "CASE_7",
        "episode_id": 101,
        "emit_status": "PENDING_FINALIZATION",
        "analysis_run_utc": "2026-06-28T00:00:00Z",
        "resolved_at_timestamp_utc": "2026-06-28T01:00:00Z",
        "result_row": {
            "formation_lower_edge": 100.0,
            "formation_upper_edge": 110.0,
            "interaction_core_lower_edge": 102.0,
            "interaction_core_upper_edge": 108.0,
            "interaction_density_lower_band": 104.0,
            "interaction_density_upper_band": 106.0,
            "sigma_live": 18.5,
            "health_live": 81.0,
        },
        "live_evolution": [
            {"row_index": 1, "price": 105.0, "zone_penetration_depth": 5.0},
            {"row_index": 2, "price": 106.0, "zone_penetration_depth": 4.0},
        ],
        "trajectory": [{"structural_trajectory": "STABLE"}],
        "prediction": [{"structural_prediction": "LIKELY_HOLD"}],
        "visit_timeline": [{"visit_id": "ZONE_7:V000001"}],
    }


def _enabled_emitter(maxsize=64):
    return ShadowRuntimeEmitter(
        queue=BoundedDropQueue(maxsize=maxsize),
        flags=FeatureFlags(enabled=True),
        kill_switch=KillSwitch(env={}),
    )


def test_disabled_is_noop() -> None:
    emitter = ShadowRuntimeEmitter(
        queue=BoundedDropQueue(maxsize=8),
        flags=FeatureFlags(enabled=False),  # default OFF
    )
    result = emitter.emit(make_record())
    assert result.status == EMIT_DISABLED
    assert emitter.queue.enqueued == 0
    assert emitter.queue.qsize() == 0
    print("DISABLED_FLAG_NO_OP = PASS")


def test_enabled_enqueues() -> None:
    emitter = _enabled_emitter()
    result = emitter.emit(make_record())
    assert result.status == EMIT_ENQUEUED
    assert result.payload is not None
    assert emitter.queue.enqueued == 1
    assert emitter.queue.qsize() == 1
    queued = emitter.queue.poll()
    assert queued is result.payload
    print("ENABLED_FLAG_ENQUEUES = PASS")


def test_kill_switch_blocks() -> None:
    breaker = CircuitBreaker()
    breaker.trip("manual")
    emitter = ShadowRuntimeEmitter(
        queue=BoundedDropQueue(maxsize=8),
        flags=FeatureFlags(enabled=True),
        kill_switch=KillSwitch(breaker=breaker, env={}),
    )
    result = emitter.emit(make_record())
    assert result.status == EMIT_KILLED
    assert emitter.queue.enqueued == 0
    # Manual env kill also blocks.
    env_emitter = ShadowRuntimeEmitter(
        queue=BoundedDropQueue(maxsize=8),
        flags=FeatureFlags(enabled=True),
        kill_switch=KillSwitch(env={"SHADOW_KILL": "1"}),
    )
    assert env_emitter.emit(make_record()).status == EMIT_KILLED
    print("KILL_SWITCH_BLOCKS = PASS")


def test_queue_full_drops_without_blocking() -> None:
    emitter = _enabled_emitter(maxsize=1)
    assert emitter.emit(make_record()).status == EMIT_ENQUEUED  # fills the queue

    start = time.monotonic()
    statuses = [emitter.emit(make_record()).status for _ in range(2000)]
    elapsed = time.monotonic() - start
    assert all(s == EMIT_DROPPED for s in statuses)
    assert emitter.queue.dropped == 2000
    assert emitter.queue.enqueued == 1
    assert elapsed < 5.0  # non-blocking
    print("QUEUE_FULL_DROPS_WITHOUT_BLOCKING = PASS", "elapsed_s", round(elapsed, 4))


def test_bad_record_never_raises() -> None:
    emitter = _enabled_emitter()
    for bad in (None, 123, "not-a-record", {}, {"result_row": 5}, {"foo": "bar"}):
        result = emitter.emit(bad)  # must not raise
        assert result.status == EMIT_ERROR, (bad, result.status)
    assert emitter.queue.enqueued == 0
    print("BAD_RECORD_NEVER_RAISES = PASS")


def test_payload_is_deep_copied() -> None:
    emitter = _enabled_emitter()
    record = make_record()
    result = emitter.emit(record)
    assert result.status == EMIT_ENQUEUED
    payload = result.payload

    # Mutate the source AFTER emit; the payload must be unaffected.
    record["result_row"]["sigma_live"] = 999.0
    record["live_evolution"][0]["row_index"] = 999
    record["live_evolution"].append({"row_index": 3})
    record["prediction"][0]["structural_prediction"] = "MUTATED"

    assert payload.result_row["sigma_live"] == 18.5
    assert payload.rows[0]["row_index"] == 1
    assert len(payload.rows) == 2
    assert payload.prediction[0]["structural_prediction"] == "LIKELY_HOLD"
    print("PAYLOAD_IS_DEEP_COPIED = PASS")


def test_identity_and_geometry_version() -> None:
    emitter = _enabled_emitter()
    payload = emitter.emit(make_record()).payload

    # global_zone_key = session_id::zone_id
    assert payload.global_zone_key == "BTCUSDT_2026-06-28_230000Z::ZONE_7"
    assert payload.session_id == "BTCUSDT_2026-06-28_230000Z"
    assert payload.zone_id == "ZONE_7"

    # geometry_version generated, deterministic, edge-derived.
    assert payload.geometry_version.startswith("GEOMv1:")
    assert payload.geometry_version != "GEOMv1:NA"
    again = emitter.emit(make_record()).payload
    assert again.geometry_version == payload.geometry_version  # deterministic

    # Different edges -> different version.
    moved = make_record()
    moved["result_row"]["formation_lower_edge"] = 200.0
    moved_version = emitter.emit(moved).payload.geometry_version
    assert moved_version != payload.geometry_version

    # Missing session falls back, zone_id still keys the snapshot.
    no_session = make_record()
    no_session.pop("session_id")
    no_session["result_row"].pop("session_id", None)
    key = emitter.emit(no_session).payload.global_zone_key
    assert key == "UNKNOWN_SESSION::ZONE_7"
    print("GLOBAL_ZONE_KEY_AND_GEOMETRY_VERSION = PASS", payload.geometry_version)


def main() -> None:
    test_disabled_is_noop()
    test_enabled_enqueues()
    test_kill_switch_blocks()
    test_queue_full_drops_without_blocking()
    test_bad_record_never_raises()
    test_payload_is_deep_copied()
    test_identity_and_geometry_version()
    print("SHADOW_RUNTIME_EMITTER_TEST = PASS")
    print("NO_LIVE_TAP = TRUE")
    print("NO_PRODUCTION_INTEGRATION = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

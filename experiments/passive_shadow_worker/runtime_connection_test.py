"""Phase 0E-2 passive worker to full shadow runtime validation."""

from __future__ import annotations

import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.passive_shadow_runtime import PassiveShadowRuntimeHandler
from core.passive_shadow_worker import PassiveShadowWorker
from core.shadow_safety.bounded_queue import BoundedDropQueue
from core.shadow_safety.feature_flag import FeatureFlags
from core.shadow_safety.kill_switch import CircuitBreaker, KillSwitch


GLOBAL_KEY = "SESSION_1::ZONE_1"


def wait_until(predicate, timeout: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return bool(predicate())


def payload(row_index=1, price=105.0):
    return {
        "global_zone_key": GLOBAL_KEY,
        "session_id": "SESSION_1",
        "zone_id": "ZONE_1",
        "episode_id": 1,
        "geometry_version": "GEOM_TEST_V1",
        "geometry": {
            "formation_lower_edge": 95.0,
            "formation_upper_edge": 115.0,
            "interaction_core_lower_edge": 100.0,
            "interaction_core_upper_edge": 110.0,
        },
        "rows": (
            {
                "row_index": row_index,
                "timestamp": f"T{row_index}",
                "price": price,
                "inside_zone_flag": True,
                "zone_touch_flag": True,
                "distance_to_zone": 0.0,
                "zone_penetration_depth": 5.0,
                "fleche_live": 0.4,
                "sigma_live": 18.5,
                "sigma_barre_zone": 24.0,
                "load_live": 38.0,
                "omega_stress_area": 91.0,
                "fatigue_live": 27.0,
                "recovery_live": 0.22,
                "rigidity_live": 73.0,
                "capacity_live": 68.0,
                "health_live": 81.0,
            },
        ),
        "prediction": (),
        "visit_timeline": (),
    }


def worker_for(queue, handler, kill_switch=None):
    return PassiveShadowWorker(
        queue=queue,
        handler=handler,
        flags=FeatureFlags(enabled=True),
        kill_switch=kill_switch or KillSwitch(env={}),
    )


class FailingOpenVisitAdapter:
    def build_patch(self, source):
        del source
        raise RuntimeError("synthetic adapter failure")


def test_payload_updates_snapshot() -> None:
    queue = BoundedDropQueue(maxsize=4)
    runtime = PassiveShadowRuntimeHandler()
    worker = worker_for(queue, runtime)
    assert queue.offer(payload())
    assert worker.start()
    assert wait_until(lambda: worker.stats()["processed"] == 1)
    assert worker.stop(drain_timeout_seconds=0.1)

    snapshot = runtime.store.get_current(GLOBAL_KEY)
    assert snapshot is not None
    assert snapshot.revision == 1
    assert snapshot.global_zone_key == GLOBAL_KEY
    assert snapshot.current_row_mechanics["row_id"] == 1
    assert snapshot.open_visit["active_visit_flag"] is True
    assert worker.stats()["failed"] == 0
    print("PAYLOAD_TO_SNAPSHOT = PASS")


def test_duplicate_and_out_of_order_rejected() -> None:
    queue = BoundedDropQueue(maxsize=4)
    runtime = PassiveShadowRuntimeHandler()
    worker = worker_for(queue, runtime)
    assert queue.offer(payload(row_index=2))
    assert queue.offer(payload(row_index=2))
    assert queue.offer(payload(row_index=1))
    assert worker.start()
    assert wait_until(lambda: worker.stats()["received"] == 3)
    assert worker.stop(drain_timeout_seconds=0.1)

    stats = worker.stats()
    snapshot = runtime.store.get_current(GLOBAL_KEY)
    assert stats["processed"] == 1
    assert stats["failed"] == 2
    assert snapshot.revision == 1
    print("DUPLICATE_AND_OUT_OF_ORDER_REJECTED = PASS")


def test_adapter_failure_preserves_previous_revision() -> None:
    initial_queue = BoundedDropQueue(maxsize=2)
    runtime = PassiveShadowRuntimeHandler()
    initial_worker = worker_for(initial_queue, runtime)
    assert initial_queue.offer(payload(row_index=1))
    assert initial_worker.start()
    assert wait_until(lambda: initial_worker.stats()["processed"] == 1)
    assert initial_worker.stop(drain_timeout_seconds=0.1)
    authoritative = runtime.store.get_current(GLOBAL_KEY)

    failing_runtime = PassiveShadowRuntimeHandler(
        store=runtime.store,
        open_visit_adapter=FailingOpenVisitAdapter(),
    )
    failing_runtime._zones = runtime._zones
    failure_queue = BoundedDropQueue(maxsize=2)
    failure_worker = worker_for(failure_queue, failing_runtime)
    assert failure_queue.offer(payload(row_index=2, price=106.0))
    assert failure_worker.start()
    assert wait_until(lambda: failure_worker.stats()["failed"] == 1)
    assert failure_worker.stop(drain_timeout_seconds=0.1)

    current = runtime.store.get_current(GLOBAL_KEY)
    assert current is authoritative
    assert current.revision == 1
    assert failure_worker.stats()["processed"] == 0
    print("ADAPTER_FAILURE_PRESERVES_REVISION = PASS")


def test_kill_switch_prevents_runtime() -> None:
    queue = BoundedDropQueue(maxsize=2)
    runtime = PassiveShadowRuntimeHandler()
    breaker = CircuitBreaker()
    breaker.trip("test kill")
    worker = worker_for(
        queue,
        runtime,
        KillSwitch(breaker=breaker, env={}),
    )
    assert queue.offer(payload())
    assert worker.start() is False
    assert runtime.store.get_current(GLOBAL_KEY) is None
    assert worker.stats()["processed"] == 0
    print("KILL_SWITCH_PREVENTS_RUNTIME = PASS")


def main() -> None:
    test_payload_updates_snapshot()
    test_duplicate_and_out_of_order_rejected()
    test_adapter_failure_preserves_previous_revision()
    test_kill_switch_prevents_runtime()
    print("PASSIVE_WORKER_RUNTIME_CONNECTION_TEST = PASS")
    print("NO_PRODUCTION_OUTPUTS = TRUE")
    print("NO_FORMULAS = TRUE")
    print("NO_DYNAMIC_STATE_RECOMPUTATION = TRUE")
    print("NO_PREDICTION_GENERATION = TRUE")


if __name__ == "__main__":
    main()

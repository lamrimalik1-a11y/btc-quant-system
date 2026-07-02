"""Phase 0E-3 shadow-only parity JSONL validation."""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.passive_shadow_runtime import PassiveShadowRuntimeHandler
from core.passive_shadow_worker import PassiveShadowWorker
from core.shadow_parity_logger import ShadowParityLogger
from core.shadow_parity_runtime import ParityLoggingShadowHandler
from core.shadow_safety.bounded_queue import BoundedDropQueue
from core.shadow_safety.feature_flag import FeatureFlags
from core.shadow_safety.kill_switch import KillSwitch


GLOBAL_KEY = "SESSION_PARITY::ZONE_1"


def wait_until(predicate, timeout=1.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return bool(predicate())


def make_row(index, price):
    return {
        "row_index": index,
        "timestamp": f"T{index}",
        "price": price,
        "inside_zone_flag": 100.0 <= price <= 110.0,
        "zone_touch_flag": 100.0 <= price <= 110.0,
        "distance_to_zone": 0.0 if price <= 110.0 else price - 110.0,
        "zone_penetration_depth": 5.0 if price == 105.0 else 0.0,
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
    }


def make_payload(rows, *, prediction=(), timeline=()):
    return {
        "payload_id": f"PAYLOAD_{rows[-1]['row_index']}",
        "global_zone_key": GLOBAL_KEY,
        "session_id": "SESSION_PARITY",
        "zone_id": "ZONE_1",
        "episode_id": 1,
        "geometry_version": "GEOM_PARITY_V1",
        "geometry": {
            "formation_lower_edge": 95.0,
            "formation_upper_edge": 115.0,
            "interaction_core_lower_edge": 100.0,
            "interaction_core_upper_edge": 110.0,
        },
        "rows": tuple(rows),
        "prediction": tuple(prediction),
        "visit_timeline": tuple(timeline),
        "production_reference_values": {
            "health_live": rows[-1]["health_live"],
            "capacity_live": rows[-1]["capacity_live"],
        },
    }


def make_worker(queue, handler):
    worker = PassiveShadowWorker(
        queue=queue,
        handler=handler,
        flags=FeatureFlags(enabled=True),
        kill_switch=KillSwitch(env={}),
    )
    handler.set_counters_provider(worker.stats)
    return worker


def records(logger):
    return [
        json.loads(line)
        for line in logger.path.read_text(encoding="utf-8").splitlines()
    ]


class FailingOpenVisitAdapter:
    def build_patch(self, source):
        del source
        raise RuntimeError("synthetic parity adapter failure")


class FailingLogger:
    def __init__(self):
        self.calls = 0

    def write(self, record):
        del record
        self.calls += 1
        return False


def test_success_and_pending_prediction(root):
    logger = ShadowParityLogger(root=root)
    handler = ParityLoggingShadowHandler(logger=logger)
    queue = BoundedDropQueue(maxsize=4)
    worker = make_worker(queue, handler)
    timeline = {
        "visit_id": "ZONE_1:V000001",
        "dynamic_state": "STABLE",
        "SDR": 0.8,
    }
    prediction = {
        "emit_status": "PENDING",
        "visit_id": "ZONE_1:V000001",
    }
    payload = make_payload(
        [
            make_row(1, 105.0),
            make_row(2, 111.0),
            make_row(3, 112.0),
            make_row(4, 113.0),
        ],
        prediction=(prediction,),
        timeline=(timeline,),
    )
    assert queue.offer(payload)
    assert worker.start()
    assert wait_until(lambda: worker.stats()["processed"] == 1)
    assert worker.stop(drain_timeout_seconds=0.1)

    record = records(logger)[-1]
    snapshot = handler.store.get_current(GLOBAL_KEY)
    assert record["event_status"] == "PROCESSED"
    assert record["payload_id"] == "PAYLOAD_4"
    assert record["snapshot_revision"] == snapshot.revision
    assert record["refresh_plan_id"] == snapshot.source_plan_id
    assert record["shadow_snapshot_values"]["prediction"]["prediction_status"] == "PENDING"
    assert record["mismatch_flags"]["health_live"] is False
    assert record["queue_worker_counters"]["received"] == 1
    assert record["error_status"] == "OK"
    print("SUCCESS_AND_PENDING_PREDICTION_LOGGED = PASS")


def test_failure_logged_without_snapshot_corruption(root):
    logger = ShadowParityLogger(root=root, filename="failure.jsonl")
    runtime = PassiveShadowRuntimeHandler()
    handler = ParityLoggingShadowHandler(runtime=runtime, logger=logger)
    queue = BoundedDropQueue(maxsize=2)
    worker = make_worker(queue, handler)
    assert queue.offer(make_payload([make_row(10, 105.0)]))
    assert worker.start()
    assert wait_until(lambda: worker.stats()["processed"] == 1)
    assert worker.stop(drain_timeout_seconds=0.1)
    authoritative = handler.store.get_current(GLOBAL_KEY)

    runtime._open_adapter = FailingOpenVisitAdapter()
    failure_queue = BoundedDropQueue(maxsize=2)
    failure_worker = make_worker(failure_queue, handler)
    assert failure_queue.offer(make_payload([make_row(11, 106.0)]))
    assert failure_worker.start()
    assert wait_until(lambda: failure_worker.stats()["failed"] == 1)
    assert failure_worker.stop(drain_timeout_seconds=0.1)

    current = handler.store.get_current(GLOBAL_KEY)
    failure_record = records(logger)[-1]
    assert current is authoritative
    assert current.revision == authoritative.revision
    assert failure_record["event_status"] == "FAILED"
    assert failure_record["error_status"] == "RuntimeError"
    assert failure_record["snapshot_revision"] == authoritative.revision
    print("FAILURE_LOGGED_WITHOUT_SNAPSHOT_CORRUPTION = PASS")


def test_logger_failure_is_non_fatal():
    logger = FailingLogger()
    handler = ParityLoggingShadowHandler(logger=logger)
    queue = BoundedDropQueue(maxsize=2)
    worker = make_worker(queue, handler)
    assert queue.offer(make_payload([make_row(20, 105.0)]))
    assert worker.start()
    assert wait_until(lambda: worker.stats()["processed"] == 1)
    assert worker.stop(drain_timeout_seconds=0.1)
    assert handler.store.get_current(GLOBAL_KEY).revision == 1
    assert worker.stats()["failed"] == 0
    assert logger.calls == 1
    print("LOGGER_FAILURE_NON_FATAL = PASS")


def test_path_confinement(temp_root):
    try:
        ShadowParityLogger(root=temp_root / "outside")
    except ValueError:
        pass
    else:
        raise AssertionError("outside parity root was accepted")
    try:
        ShadowParityLogger(root=temp_root / "research" / "shadow_parity", filename="../escape.jsonl")
    except ValueError:
        pass
    else:
        raise AssertionError("escaping filename was accepted")
    print("LOGGER_PATH_CONFINEMENT = PASS")


def main():
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        root = base / "research" / "shadow_parity"
        test_success_and_pending_prediction(root)
        test_failure_logged_without_snapshot_corruption(root)
        test_path_confinement(base)
    test_logger_failure_is_non_fatal()
    print("PHASE_0E3_PARITY_LOGGING_TEST = PASS")
    print("NO_PRODUCTION_OUTPUTS = TRUE")
    print("NO_FORMULAS = TRUE")


if __name__ == "__main__":
    main()

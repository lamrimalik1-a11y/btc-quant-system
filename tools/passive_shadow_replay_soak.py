"""Replay-driven passive shadow soak using existing local research outputs."""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ["SHADOW_RUNTIME_ENABLED"] = "1"
os.environ["SHADOW_DRY_RUN"] = "1"
os.environ["SHADOW_SAMPLE_RATE"] = "0.05"
os.environ.pop("SHADOW_KILL", None)

from core.passive_shadow_bootstrap import get_default_bootstrap
from core.shadow_runtime_emitter import get_default_emitter


RESULTS_PATH = REPO_ROOT / "research" / "zone_mechanics_cycle3_results.csv"
EVOLUTION_PATH = REPO_ROOT / "research" / "zone_live_rdm_evolution.csv"
PARITY_PATH = REPO_ROOT / "research" / "shadow_parity" / "parity.jsonl"
TARGET_PARITY_RECORDS = 5
MAX_ENQUEUED_PAYLOADS = 10
WAIT_TIMEOUT_SECONDS = 120.0


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def row_ordinal(row: dict[str, str]) -> int:
    value = row.get("row_index") or row.get("row_id") or 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def read_new_parity_records(baseline: int) -> list[dict]:
    if not PARITY_PATH.exists():
        return []
    records: list[dict] = []
    with PARITY_PATH.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if index < baseline:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def main() -> int:
    missing = [
        str(path)
        for path in (RESULTS_PATH, EVOLUTION_PATH)
        if not path.exists()
    ]
    if missing:
        print(
            json.dumps(
                {
                    "result": "FAIL",
                    "error": "required local replay/RDM files are missing",
                    "missing_files": missing,
                },
                indent=2,
            )
        )
        return 1

    baseline = count_lines(PARITY_PATH)
    results = read_csv(RESULTS_PATH)
    rows_by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(EVOLUTION_PATH):
        case_id = row.get("case_id")
        if case_id:
            rows_by_case[case_id].append(row)

    bootstrap = get_default_bootstrap()
    emitter = get_default_emitter()
    started = time.monotonic()
    bootstrap_status = bootstrap.start()
    emit_statuses: list[str] = []

    try:
        for result in results:
            case_id = result.get("case_id")
            rows = rows_by_case.get(case_id or "", [])
            if not case_id or not rows:
                continue
            rows.sort(key=row_ordinal)
            record = {
                "session_id": "REPLAY_SHADOW_SOAK",
                "zone_id": result.get("zone_id") or case_id,
                "case_id": case_id,
                "episode_id": result.get("episode_id"),
                "emit_status": "REPLAY_FINALIZED",
                "result_row": result,
                "live_evolution": rows,
                "trajectory": [],
                "prediction": [],
                "visit_timeline": [],
            }
            emit_statuses.append(emitter.emit(record).status)
            if emit_statuses.count("ENQUEUED") >= MAX_ENQUEUED_PAYLOADS:
                break

        deadline = time.monotonic() + WAIT_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if count_lines(PARITY_PATH) - baseline >= TARGET_PARITY_RECORDS:
                break
            time.sleep(0.25)
    finally:
        bootstrap.stop(drain_timeout_seconds=10.0)

    duration = time.monotonic() - started
    worker = bootstrap.stats().get("worker", {})
    records = read_new_parity_records(baseline)
    summary = {
        "bootstrap": bootstrap_status,
        "duration_seconds": round(duration, 3),
        "payloads_attempted": len(emit_statuses),
        "payloads_enqueued": emit_statuses.count("ENQUEUED"),
        "payloads_dropped": emit_statuses.count("DROPPED"),
        "payloads_processed": worker.get("processed", 0),
        "worker_failed": worker.get("failed", 0),
        "worker_desynchronized": worker.get("desynchronized", 0),
        "queue_depth": worker.get("queue_size", 0),
        "parity_records": len(records),
        "parity_success": sum(
            record.get("event_status") == "PROCESSED" for record in records
        ),
        "parity_failed": sum(
            record.get("event_status") == "FAILED" for record in records
        ),
    }
    summary["result"] = (
        "PASS"
        if summary["parity_records"] >= TARGET_PARITY_RECORDS
        and summary["worker_failed"] == 0
        and summary["payloads_dropped"] == 0
        and summary["worker_desynchronized"] == 0
        else "FAIL"
    )
    print(json.dumps(summary, indent=2))
    return 0 if summary["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

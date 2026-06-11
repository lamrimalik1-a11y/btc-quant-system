"""
Dry-run validation harness for B12 (Live Validation Instrumentation --
core.live_b12_validation / core.live_rdm.append_live_b12_validation_for_case).

Goal: replay real market data through the live stack (V2 -> Preparation ->
Return Detection -> RDM -> B12) for the 14 already-finalized 2026-06-10/11
live cases, so the NEW post_return_feature_window_rows buffer
(core/live_return_detection.py) is populated and B12 produces real
CONFIRMED / REFUTED / NOT_TESTED verdicts instead of NO_POST_RETURN_DATA.

DATA SOURCE (Amendment 2): outputs/observation_rows.csv contains FOUR
concatenated live-process segments (row_id resets to 1 at each process
restart). The 14 finalized cases (start_row_id 345..2053, return_row up to
2054) all belong to the LAST segment, which spans row_id 1..2153 and covers
2026-06-10 09:47:32 UTC -> 2026-06-11 04:18:14 UTC -- containing every
FEATURE_WINDOW_FIELDS column needed to rebuild post_return_feature_window_rows
for 13/14 cases in full (4h) and the 14th (LIVE_PREP_ZONE_105, return
2026-06-11 00:22:16) to ~3h56m (dataset ends 04:18:14, ~4 min short of the
4h bound). historical_observation_rows.csv (used by validate_live_rdm.py) was
checked and only covers 2026-02-26..2026-02-28 -- NOT usable for this period.

This harness writes nothing to any tracked output file: B12 records are
captured via a monkeypatched core.live_rdm._append_b12_validation_csv, and
all of observation_logger / live_lifecycle / live_return_detection / live_rdm
writers are monkeypatched out exactly as in tools/validate_live_rdm.py's
run_live_capture.

AMENDMENT 1 (decay-saturation bias check): for every case, the FIRST
post-return evolution row's rigidity_live/capacity_live (computed by
core.live_b12_validation.build_post_return_evolution, captured via a thin
monkeypatch wrapper) is compared to 0.5 * rigidity_birth / 0.5 * capacity_birth
BEFORE any segment/engagement filtering. This is a measurement only -- no
code-side compensation is applied anywhere.

Usage: python -m tools.validate_live_b12
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

import core.live_b12_validation as lb12
import core.live_lifecycle as ll
import core.live_rdm as lr
import core.live_return_detection as lrd
import core.observation_logger as ol
from tools.validate_live_preparation import _event_timestamp

ROOT = Path(__file__).resolve().parents[1]
OBSERVATION_ROWS_FILE = ROOT / "outputs" / "observation_rows.csv"


def load_last_segment():
    """
    outputs/observation_rows.csv concatenates multiple live-process segments,
    each with its own row_id sequence starting at 1. Returns the LAST segment
    (the one containing the 14 finalized 2026-06-10/11 cases), reindexed with
    its original row_id values intact.
    """
    df = pd.read_csv(OBSERVATION_ROWS_FILE, low_memory=False)
    reset_positions = df.index[(df["row_id"] == 1)].tolist()
    last_reset = reset_positions[-1]
    segment = df.iloc[last_reset:].reset_index(drop=True)
    return segment


def run_b12_replay(market_rows):
    """
    Drives the live stack row by row (V2 -> Preparation -> Return Detection
    -> RDM -> B12), capturing every B12 record core.live_rdm would have
    written to outputs/live_b12_validation.csv, plus the Amendment 1
    first-post-return-row rigidity_live/capacity_live for every case B12
    actually computed (i.e. every case that reached
    build_post_return_evolution with a non-empty result).

    Mirrors tools/validate_live_rdm.py's run_live_capture monkeypatch/reset
    pattern. Writes nothing to any tracked output file.
    """
    captured_b12_records = []
    captured_first_postreturn = {}

    original_append_rows = ol._append_rows
    original_append_result_row = lrd._append_result_row
    original_append_jsonl = ll._append_jsonl
    original_write_state_snapshot = ll._write_lifecycle_state_snapshot
    original_persist_record = lr._persist_record
    original_append_b12_csv = lr._append_b12_validation_csv
    original_build_post_return_evolution = lb12.build_post_return_evolution

    def capture_append_rows(path, fieldnames, rows):
        if path in (ol.LIVE_PREPARATION_FILE, ol.DASHBOARD_V2_EPISODES_FILE):
            return
        original_append_rows(path, fieldnames, rows)

    def capture_persist_record(record):
        pass

    def capture_b12_csv(record):
        captured_b12_records.append(dict(record))

    def capture_build_post_return_evolution(post_return_window, case_record, run_utc):
        evolution = original_build_post_return_evolution(post_return_window, case_record, run_utc)
        if not evolution.empty:
            first_row = evolution.iloc[0]
            captured_first_postreturn[case_record.get("case_id")] = {
                "rigidity_first_postreturn": first_row.get("rigidity_live"),
                "capacity_first_postreturn": first_row.get("capacity_live"),
                "rigidity_birth": case_record.get("rigidity_birth"),
                "capacity_birth": case_record.get("capacity_birth"),
            }
        return evolution

    lrd.reset_live_return_detection()
    ll.reset_live_lifecycle_memory()
    lr.reset_live_rdm_state()
    ol._active_v2_episode = None
    ol._v2_episode_counter = 0
    ol._previous_dashboard_v2_state = None
    ol._live_preparation_row_buffer.clear()
    ol._append_rows = capture_append_rows
    lrd._append_result_row = lambda result_row: None
    ll._append_jsonl = lambda path, payload: None
    ll._write_lifecycle_state_snapshot = lambda: None
    lr._persist_record = capture_persist_record
    lr._append_b12_validation_csv = capture_b12_csv
    lb12.build_post_return_evolution = capture_build_post_return_evolution

    try:
        previous_state = ol.NO_CONFLUENCE_STATE

        for row_index, row in market_rows.iterrows():
            row_data = row.to_dict()
            row_id = int(row_data.get("row_id", row_index + 1))
            event_timestamp = _event_timestamp(row_data)

            ol._capture_preparation_row(row_data, row_id)
            lrd.process_live_return_detection_row(row_data, row_id, event_timestamp)

            snapshot = ol._get_dashboard_v2_snapshot(row_data)
            new_state = snapshot["state"]

            ol._update_dashboard_v2_episode(
                row=row_data,
                row_id=row_id,
                event_timestamp=event_timestamp,
                previous_state=previous_state,
                new_state=new_state,
                snapshot=snapshot,
            )

            previous_state = new_state
    finally:
        ol._append_rows = original_append_rows
        lrd._append_result_row = original_append_result_row
        ll._append_jsonl = original_append_jsonl
        ll._write_lifecycle_state_snapshot = original_write_state_snapshot
        lr._persist_record = original_persist_record
        lr._append_b12_validation_csv = original_append_b12_csv
        lb12.build_post_return_evolution = original_build_post_return_evolution
        ol._active_v2_episode = None
        ol._v2_episode_counter = 0
        ol._previous_dashboard_v2_state = None
        ol._live_preparation_row_buffer.clear()
        lrd.reset_live_return_detection()
        ll.reset_live_lifecycle_memory()
        lr.reset_live_rdm_state()

    return captured_b12_records, captured_first_postreturn


def main():
    market_rows = load_last_segment()
    print(f"Replaying {len(market_rows)} rows from outputs/observation_rows.csv "
          f"(last segment, row_id {market_rows['row_id'].min()}..{market_rows['row_id'].max()})")

    b12_records, first_postreturn = run_b12_replay(market_rows)

    print(f"\nB12 records captured: {len(b12_records)}")
    print("=" * 100)

    verdict_counts = {}
    bias_flagged_cases = []

    for record in b12_records:
        case_id = record.get("case_id")
        verdict = record.get("b12_verdict")
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1

        bias = first_postreturn.get(case_id)
        rigidity_first = capacity_first = prebias_flag = ""
        if bias is not None:
            rig_birth = bias.get("rigidity_birth") or 0.0
            cap_birth = bias.get("capacity_birth") or 0.0
            rigidity_first = bias.get("rigidity_first_postreturn")
            capacity_first = bias.get("capacity_first_postreturn")
            rig_flag = (rigidity_first is not None) and (float(rigidity_first) < 0.5 * float(rig_birth))
            cap_flag = (capacity_first is not None) and (float(capacity_first) < 0.5 * float(cap_birth))
            prebias_flag = bool(rig_flag or cap_flag)
            if prebias_flag:
                bias_flagged_cases.append(case_id)

        print(f"case_id={case_id}  episode_id={record.get('episode_id')}")
        print(f"  b11_prediction_label   = {record.get('b11_prediction_label')}")
        print(f"  interaction_core_valid = {record.get('interaction_core_valid_flag')}")
        print(f"  post_return_rows       = {record.get('post_return_rows_captured')}")
        print(f"  segment_found          = {record.get('segment_found')}  source={record.get('segment_source')}")
        print(f"  segment_start/end_row  = {record.get('segment_start_row')} / {record.get('segment_end_row')}")
        print(f"  visit_classification   = {record.get('visit_classification')}")
        print(f"  b12_verdict            = {verdict}   not_tested_reason={record.get('not_tested_reason')}")
        print(f"  rigidity_birth         = {record.get('rigidity_birth')}   "
              f"rigidity_first_postreturn = {rigidity_first}")
        print(f"  capacity_birth         = {record.get('capacity_birth')}   "
              f"capacity_first_postreturn = {capacity_first}")
        print(f"  prebias_breakdown_flag = {prebias_flag}")
        print("-" * 100)

    print("\nVerdict distribution:")
    for verdict, count in sorted(verdict_counts.items()):
        print(f"  {verdict}: {count}")

    print("\n" + "=" * 100)
    if bias_flagged_cases:
        print("*** AMENDMENT 1 WARNING: prebias_breakdown_flag=True for the following cases ***")
        print("*** rigidity_live or capacity_live at the FIRST post-return row was already   ***")
        print("*** below 0.5 * birth, BEFORE any Active Core engagement was observed.        ***")
        for case_id in bias_flagged_cases:
            print(f"  - {case_id}")
    else:
        print("Amendment 1 bias check: no case had prebias_breakdown_flag=True.")
    print("=" * 100)


if __name__ == "__main__":
    main()

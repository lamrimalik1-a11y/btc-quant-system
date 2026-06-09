"""
Validation harness for LIVE Preparation snapshot freezing
(core.observation_logger._capture_preparation_row /
_freeze_live_preparation_snapshot).

Goal: prove that Preparation zones frozen at LIVE V2 episode close — computed
from a bounded rolling row buffer via the directly-imported, validated
find_preparation_zone / ResearchRowIndex / prepare_rows functions from
tools.analyze_phase1b_episode_research — are FIELD-IDENTICAL to the same
functions run against the full historical dataset (the offline reference),
for every episode whose live buffer was "warm" (i.e., contained the full
history window the offline computation would have consulted).

This does not download data, does not call the replay generator, does not
modify any formula/threshold/B12v2/RDM/Synthesis/Preparation logic, and does
not write to any tracked output file — it reads a sample prefix of the
existing outputs/historical_observation_rows.csv (already-generated,
validated replay output) and drives the live state machine over that slice
in memory, capturing both V2 episodes and live preparation snapshots via
monkeypatched _append_rows.

Usage: python -m tools.validate_live_preparation
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import core.observation_logger as ol
from tools.analyze_phase1b_episode_research import (
    ResearchRowIndex,
    find_preparation_zone,
    prepare_rows,
    public_preparation_fields,
)

ROOT = Path(__file__).resolve().parents[1]
OBSERVATION_ROWS_FILE = ROOT / "outputs" / "historical_observation_rows.csv"

# Kept within the live buffer's maxlen so the buffer never evicts a row —
# this guarantees the live buffer is an exact prefix of the full dataset
# (same rows, same order, same positions), which in turn guarantees
# add_preparation_baselines' rolling computations are bit-identical between
# the live (buffer-derived) and offline (full-dataset-derived) DataFrames.
SAMPLE_ROWS = 700

NUMERIC_TOLERANCE = 1e-9

# Preparation fields we expect to be present and comparable. Mirrors
# core.observation_logger.LIVE_PREPARATION_FIELDNAMES minus the episode
# linkage/bookkeeping columns (those are V2-episode fields, not Preparation
# zone fields, and are already covered by validate_live_v2_episode_closure).
PREPARATION_COMPARISON_FIELDS = [
    field
    for field in ol.LIVE_PREPARATION_FIELDNAMES
    if field
    not in {
        "episode_id",
        "episode_start_timestamp_utc",
        "episode_end_timestamp_utc",
        "start_row_id",
        "end_row_id",
        "frozen_at_row_id",
        "frozen_at_timestamp_utc",
    }
]

# A live snapshot is only directly comparable to the offline (full-history)
# reference once the live buffer has accumulated enough history for
# find_preparation_zone to consult the SAME rows offline would: up to
# BACKWARD_WINDOW=100 backward rows plus up to 300 reference rows, all drawn
# from rows strictly before start_row_id. Cold-start episodes — where the
# live process simply has not observed that much history yet — are a
# structural, expected difference (the live process cannot see rows before
# it started), not a state-machine defect, and are reported separately.
MINIMUM_WARM_HISTORY_ROWS = 400


def load_sample_rows():
    return pd.read_csv(OBSERVATION_ROWS_FILE, nrows=SAMPLE_ROWS, low_memory=False)


def load_full_rows():
    return pd.read_csv(OBSERVATION_ROWS_FILE, low_memory=False)


def build_offline_row_index(full_rows):
    prepared = prepare_rows(full_rows)
    return ResearchRowIndex(prepared)


def run_live_capture(market_rows):
    """
    Drives the live V2 state machine row by row exactly as
    core.observation_logger._log_observation_events does (including feeding
    each row through _capture_preparation_row first), capturing every
    frozen live preparation snapshot in memory instead of writing to
    outputs/live_preparation_zones.csv. Mirrors the harness pattern in
    tools/validate_live_v2_episode_closure.py.
    """
    captured_snapshots = []

    original_append_rows = ol._append_rows

    def capture_append_rows(path, fieldnames, rows):
        if path == ol.LIVE_PREPARATION_FILE:
            captured_snapshots.extend(rows)
            return
        if path == ol.DASHBOARD_V2_EPISODES_FILE:
            return
        original_append_rows(path, fieldnames, rows)

    ol._active_v2_episode = None
    ol._v2_episode_counter = 0
    ol._previous_dashboard_v2_state = None
    ol._live_preparation_row_buffer.clear()
    ol._append_rows = capture_append_rows

    try:
        previous_state = ol.NO_CONFLUENCE_STATE

        for row_index, row in market_rows.iterrows():
            row_data = row.to_dict()
            row_id = int(row_data.get("row_id", row_index + 1))
            event_timestamp = _event_timestamp(row_data)

            ol._capture_preparation_row(row_data, row_id)

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

        history_before_start = {
            snapshot["start_row_id"]: _count_rows_before(market_rows, snapshot["start_row_id"])
            for snapshot in captured_snapshots
        }
    finally:
        ol._append_rows = original_append_rows
        ol._active_v2_episode = None
        ol._v2_episode_counter = 0
        ol._previous_dashboard_v2_state = None
        ol._live_preparation_row_buffer.clear()

    return captured_snapshots, history_before_start


def _count_rows_before(market_rows, start_row_id):
    row_ids = pd.to_numeric(market_rows["row_id"], errors="coerce")
    return int((row_ids < float(start_row_id)).sum())


def _event_timestamp(row_data):
    """Same deterministic timestamp derivation as validate_live_v2_episode_closure."""
    timestamp = (
        row_data.get("market_timestamp")
        or row_data.get("end_ts")
        or row_data.get("timestamp")
        or row_data.get("start_ts")
    )

    if timestamp is None or (isinstance(timestamp, float) and pd.isna(timestamp)):
        return datetime.now(timezone.utc).isoformat()

    numeric_timestamp = float(timestamp)
    if numeric_timestamp > 10_000_000_000:
        numeric_timestamp = numeric_timestamp / 1000

    return datetime.fromtimestamp(numeric_timestamp, tz=timezone.utc).isoformat()


def run_offline_reference(offline_row_index, start_row_id):
    preparation_zone = find_preparation_zone(offline_row_index, start_row_id=start_row_id)
    return public_preparation_fields(preparation_zone)


def compare_snapshot(reference_fields, live_snapshot):
    mismatches = []

    for field in PREPARATION_COMPARISON_FIELDS:
        reference_value = reference_fields.get(field)
        live_value = live_snapshot.get(field)

        if _values_equal(reference_value, live_value):
            continue

        mismatches.append(
            f"{field}: reference={reference_value!r} live={live_value!r}"
        )

    return mismatches


def _values_equal(reference_value, live_value):
    if reference_value == live_value:
        return True

    reference_number = _maybe_number(reference_value)
    live_number = _maybe_number(live_value)

    if reference_number is not None and live_number is not None:
        return abs(reference_number - live_number) <= NUMERIC_TOLERANCE

    if _is_blank(reference_value) and _is_blank(live_value):
        return True

    return False


def _is_blank(value):
    return value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == ""


def _maybe_number(value):
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def main():
    if not OBSERVATION_ROWS_FILE.exists():
        raise SystemExit(f"Required input not found: {OBSERVATION_ROWS_FILE}")

    market_rows = load_sample_rows()
    full_rows = load_full_rows()
    offline_row_index = build_offline_row_index(full_rows)

    live_snapshots, history_before_start = run_live_capture(market_rows)

    print(f"Sample rows (live, prefix-fed): {len(market_rows)}")
    print(f"Full historical rows (offline reference): {len(full_rows)}")
    print(f"Live preparation snapshots captured: {len(live_snapshots)}")

    warm_results = []
    cold_results = []

    for snapshot in live_snapshots:
        start_row_id = snapshot["start_row_id"]
        history_rows = history_before_start.get(start_row_id, 0)

        reference_fields = run_offline_reference(offline_row_index, start_row_id)
        mismatches = compare_snapshot(reference_fields, snapshot)

        record = {
            "episode_id": snapshot.get("episode_id"),
            "start_row_id": start_row_id,
            "history_rows_in_live_buffer": history_rows,
            "mismatches": mismatches,
        }

        if history_rows >= MINIMUM_WARM_HISTORY_ROWS:
            warm_results.append(record)
        else:
            cold_results.append(record)

    print(f"\nWarm episodes (>= {MINIMUM_WARM_HISTORY_ROWS} live history rows before start_row_id): {len(warm_results)}")
    print(f"Cold-start episodes (< {MINIMUM_WARM_HISTORY_ROWS} live history rows — expected, structural, not comparable): {len(cold_results)}")

    warm_failures = [r for r in warm_results if r["mismatches"]]

    print("\n--- WARM EPISODES (must be field-identical to offline reference) ---")
    for record in warm_results:
        status = "FAIL" if record["mismatches"] else "PASS"
        print(
            f"  [{status}] episode_id={record['episode_id']} start_row_id={record['start_row_id']:.0f} "
            f"history_rows={record['history_rows_in_live_buffer']}"
        )
        for mismatch in record["mismatches"]:
            print(f"      - {mismatch}")

    print("\n--- COLD-START EPISODES (informational only — live had less history than offline) ---")
    for record in cold_results:
        print(
            f"  [COLD] episode_id={record['episode_id']} start_row_id={record['start_row_id']:.0f} "
            f"history_rows={record['history_rows_in_live_buffer']} "
            f"(differs from offline by design — live process had not observed that much history)"
        )

    if warm_failures:
        print(f"\nFAIL — {len(warm_failures)} warm episode(s) mismatched the offline reference.")
        raise SystemExit(1)

    if not warm_results:
        print(
            "\nNo warm episodes found in this sample — increase SAMPLE_ROWS "
            "(while staying <= the live buffer maxlen) to capture comparable episodes."
        )
        raise SystemExit(1)

    print(
        "\nPASS — every warm live preparation snapshot is field-identical to the "
        "validated offline find_preparation_zone reference."
    )


if __name__ == "__main__":
    main()

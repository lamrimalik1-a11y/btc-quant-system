"""
Validation harness for the LIVE V2 episode open/close state machine
(core.observation_logger._update_dashboard_v2_episode and friends).

Goal: prove the new live state machine produces episodes that are
IDENTICAL to the already-validated offline V2 replay logic
(tools.generate_replay_observation.build_replay_observation_v2) when
fed the exact same row sequence in the exact same order.

This does not download data, does not call the replay generator, does
not modify any formula/threshold/B12v2/RDM/Synthesis logic, and does
not write to any tracked output file — it reads a sample slice of the
existing outputs/historical_observation_rows.csv (already-generated,
validated replay output containing live-computed dashboard_v2_* fields)
and drives both implementations over that slice in memory.

Usage: python -m tools.validate_live_v2_episode_closure
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import core.observation_logger as ol
from tools.generate_replay_observation import build_replay_observation_v2

ROOT = Path(__file__).resolve().parents[1]
OBSERVATION_ROWS_FILE = ROOT / "outputs" / "historical_observation_rows.csv"

SAMPLE_ROWS = 4000

NUMERIC_TOLERANCE = 1e-9


def load_sample_rows():
    market_rows = pd.read_csv(OBSERVATION_ROWS_FILE, nrows=SAMPLE_ROWS, low_memory=False)
    return market_rows


def run_reference_v2(market_rows):
    """The validated offline V2 replay builder — untouched, used as ground truth."""
    _, episodes = build_replay_observation_v2(market_rows)
    return episodes


def run_live_v2(market_rows):
    """
    Drives the new live V2 state machine (core.observation_logger) row by
    row, exactly mirroring how _log_observation_events invokes it per
    incoming live row — including stamping each row with an ISO-8601
    UTC event_timestamp the same way _log_observation_events does
    (`datetime.now(timezone.utc).isoformat()`), here derived
    deterministically from each row's market_timestamp so the run is
    reproducible. _append_rows is monkeypatched so nothing is written to
    outputs/dashboard_v2_episodes.csv during validation — episodes are
    captured in memory instead.
    """
    captured_episodes = []

    original_append_rows = ol._append_rows

    def capture_append_rows(path, fieldnames, rows):
        if path == ol.DASHBOARD_V2_EPISODES_FILE:
            captured_episodes.extend(rows)
            return
        original_append_rows(path, fieldnames, rows)

    # Reset module-level state so this run starts cold, matching a fresh
    # live process, and isolate it from any other state in the module.
    ol._active_v2_episode = None
    ol._v2_episode_counter = 0
    ol._previous_dashboard_v2_state = None
    ol._append_rows = capture_append_rows

    try:
        previous_state = ol.NO_CONFLUENCE_STATE

        for row_index, row in market_rows.iterrows():
            row_data = row.to_dict()
            row_id = int(row_data.get("row_id", row_index + 1))
            event_timestamp = _event_timestamp(row_data, row_index)

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
        ol._active_v2_episode = None
        ol._v2_episode_counter = 0
        ol._previous_dashboard_v2_state = None

    return captured_episodes


def _event_timestamp(row_data, row_index):
    """
    Live code always stamps events with
    `datetime.now(timezone.utc).isoformat()` (an ISO-8601 string) — never
    the row's market_timestamp. To keep this validation deterministic and
    reproducible while exercising the exact code path live uses
    (_duration_seconds via datetime.fromisoformat), this derives an
    ISO-8601 UTC string from each row's market_timestamp (epoch ms).
    """
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


# Timestamp *string* fields differ in representation by design: the
# offline replay stamps episodes with the historical row's raw
# market_timestamp (epoch ms, as a string), while live always stamps
# with datetime.now(timezone.utc).isoformat() (an ISO-8601 string).
# This is the same intentional difference that exists between V1 live
# and V1 replay episodes — not a state-machine discrepancy. These two
# fields are therefore validated for "non-empty and parseable" rather
# than string equality. Every other field — including duration_seconds,
# which is independently recomputed from each implementation's own
# timestamp representation — must match exactly.
TIMESTAMP_STRING_FIELDS = {
    "episode_start_timestamp_utc",
    "episode_end_timestamp_utc",
}


def compare_episodes(reference_episodes, live_episodes):
    mismatches = []

    if len(reference_episodes) != len(live_episodes):
        mismatches.append(
            f"episode count mismatch: reference={len(reference_episodes)} live={len(live_episodes)}"
        )

    for index, (reference, live) in enumerate(zip(reference_episodes, live_episodes)):
        for field in ol.V2_EPISODE_FIELDNAMES:
            reference_value = reference.get(field)
            live_value = live.get(field)

            if field in TIMESTAMP_STRING_FIELDS:
                if _is_non_empty(reference_value) and _is_non_empty(live_value):
                    continue
                mismatches.append(
                    f"episode[{index}].{field}: reference={reference_value!r} live={live_value!r} (expected both non-empty)"
                )
                continue

            if _values_equal(reference_value, live_value):
                continue

            mismatches.append(
                f"episode[{index}].{field}: reference={reference_value!r} live={live_value!r}"
            )

    return mismatches


def _is_non_empty(value):
    return value is not None and str(value).strip() != ""


def _values_equal(reference_value, live_value):
    if reference_value == live_value:
        return True

    reference_number = _maybe_number(reference_value)
    live_number = _maybe_number(live_value)

    if reference_number is not None and live_number is not None:
        return abs(reference_number - live_number) <= NUMERIC_TOLERANCE

    return False


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

    reference_episodes = run_reference_v2(market_rows)
    live_episodes = run_live_v2(market_rows)

    mismatches = compare_episodes(reference_episodes, live_episodes)

    print(f"Sample rows: {len(market_rows)}")
    print(f"Reference (validated offline V2 replay) episodes: {len(reference_episodes)}")
    print(f"Live V2 state machine episodes: {len(live_episodes)}")

    if mismatches:
        print(f"\nFAIL — {len(mismatches)} mismatch(es):")
        for mismatch in mismatches[:50]:
            print(f"  - {mismatch}")
        raise SystemExit(1)

    print("\nPASS — live V2 episode state machine output is field-identical to the validated offline V2 replay logic.")

    if live_episodes:
        print("\nFirst generated live V2 episode:")
        for field in ol.V2_EPISODE_FIELDNAMES:
            print(f"  {field}: {live_episodes[0].get(field)!r}")


if __name__ == "__main__":
    main()

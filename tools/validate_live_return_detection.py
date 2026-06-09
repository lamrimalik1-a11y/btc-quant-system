"""
Validation harness for LIVE Return Detection / Reversal Context
(core.live_return_detection — PHASE 3B of the LIVE integration roadmap).

Goal: prove that the streaming, event-driven return-detection engine —
which tracks each live Preparation zone as "pending" until its
return_to_preparation genuinely resolves (per the explicit "accept unbounded
logical tracking" decision: no timeouts/expiry/max-age/live-only filters),
then computes return_context / reversal_context / expansion_split from small
bounded buffers via VERBATIM-imported validated functions — produces output
that is FIELD-IDENTICAL to running those same validated functions
(detect_preparation_return / analyze_reversal_context /
analyze_expansion_reversal_split, all imported directly from
tools.analyze_phase1b_episode_research, zero drift) against the FULL
historical dataset for the exact same zone.

Method: drive the live V2 + live Preparation + live Return Detection state
machine row-by-row over the full outputs/historical_observation_rows.csv
(the same validated replay output validate_live_preparation /
validate_live_lifecycle already use), capturing every finalized live
return-detection result via a monkeypatched _append_result_row (nothing is
written to tracked output files). For each finalized zone, independently
recompute the OFFLINE reference by calling the unmodified offline functions
against a ResearchRowIndex over the FULL dataset — same zone (re-derived via
find_preparation_zone for the same start_row_id, exactly as
validate_live_preparation already proved is warm/field-identical), same
end_dt/end_price/episode_direction, same call shape analyze_episode uses —
just with full-dataset (unbounded) row access instead of the live engine's
small accumulated buffers.

Comparing the two proves the STREAMING engine reproduces the UNBOUNDED
offline computation field-for-field for the 9 required live fields:
return_to_preparation, return_price, return_timestamp, return_row,
failed_after_return, expansion_type, expansion_strength, reversal_type,
reversal_strength.

zone_revisit_count is intentionally not compared — see
core/live_return_detection.py's module docstring (documented, analogous to
the zone_expired/zone_broken precedent: requires an unbounded full-future
scan that is not in the required-field list and not consumed by any required
formula; reproducing it would require a brand-new unbounded-retention
mechanism the Phase 3B decision explicitly rules out).

This does not download data, does not call the replay generator, does not
modify any formula/threshold/B12v2/RDM/Synthesis/Preparation/Lifecycle/
Return-Detection logic, and does not write to any tracked output file.

Usage: python -m tools.validate_live_return_detection
"""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pandas as pd

import core.live_lifecycle as ll
import core.live_return_detection as lrd
import core.observation_logger as ol
from tools.analyze_phase1b_episode_research import (
    HORIZONS,
    ResearchRowIndex,
    analyze_expansion_reversal_split,
    analyze_reversal_context,
    calculate_window_extremes,
    detect_preparation_return,
    episode_direction_proxy,
    find_preparation_zone,
    nearest_close_at_or_after,
    parse_datetime_value,
    prepare_rows,
    subtract,
    to_float,
)
from tools.validate_live_preparation import (
    MINIMUM_WARM_HISTORY_ROWS,
    _count_rows_before,
    _event_timestamp,
)

ROOT = Path(__file__).resolve().parents[1]
OBSERVATION_ROWS_FILE = ROOT / "outputs" / "historical_observation_rows.csv"

NUMERIC_TOLERANCE = 1e-9

FOUR_HOURS = timedelta(hours=4)
_REVERSAL_HORIZON_LABELS = ["1m", "5m", "15m", "30m", "1h"]

# The 9 fields the user's PHASE 3B directive explicitly requires live to
# produce, fed into the validated Phase 3A lifecycle wiring. These are the
# ONLY fields compared for field-identity.
REQUIRED_LIVE_FIELDS = [
    "return_to_preparation",
    "return_price",
    "return_timestamp",
    "return_row",
    "failed_after_return",
    "expansion_type",
    "expansion_strength",
    "reversal_type",
    "reversal_strength",
]

# Documented, not compared — see core/live_return_detection.py docstring
# ("WHAT IS DELIBERATELY NOT REPRODUCED") for the full reasoning: requires an
# unbounded full-future scan, not in the required-field list, not consumed by
# any required formula. Reported separately, analogous to the
# zone_expired/zone_broken precedent.
DOCUMENTED_NOT_COMPARED_FIELDS = ["zone_revisit_count"]


def load_full_rows():
    return pd.read_csv(OBSERVATION_ROWS_FILE, low_memory=False)


def build_full_row_index(full_rows):
    prepared = prepare_rows(full_rows)
    return ResearchRowIndex(prepared)


def run_live_capture(market_rows):
    """
    Drives the live V2 + live Preparation + live Return Detection state
    machine row by row exactly as core.observation_logger._log_observation_
    events does, capturing every finalized live return-detection result row
    and every V2 episode in memory. Nothing is written to tracked output
    files (both _append_rows / _append_result_row and core.live_lifecycle's
    JSONL/CSV writers are monkeypatched out for the duration of this run).
    """
    captured_results = []
    captured_episode_by_id = {}

    original_append_rows = ol._append_rows
    original_append_result_row = lrd._append_result_row
    original_append_jsonl = ll._append_jsonl
    original_write_state_snapshot = ll._write_lifecycle_state_snapshot

    def capture_append_rows(path, fieldnames, rows):
        if path == ol.LIVE_PREPARATION_FILE:
            return
        if path == ol.DASHBOARD_V2_EPISODES_FILE:
            for captured_row in rows:
                captured_episode_by_id[captured_row.get("episode_id")] = captured_row
            return
        original_append_rows(path, fieldnames, rows)

    def capture_append_result_row(result_row):
        captured_results.append(dict(result_row))

    lrd.reset_live_return_detection()
    ll.reset_live_lifecycle_memory()
    ol._active_v2_episode = None
    ol._v2_episode_counter = 0
    ol._previous_dashboard_v2_state = None
    ol._live_preparation_row_buffer.clear()
    ol._append_rows = capture_append_rows
    lrd._append_result_row = capture_append_result_row
    ll._append_jsonl = lambda path, payload: None
    ll._write_lifecycle_state_snapshot = lambda: None

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

        history_before_start = {
            result["start_row_id"]: _count_rows_before(market_rows, result["start_row_id"])
            for result in captured_results
        }
        pending_count = len(lrd._pending_zones)
    finally:
        ol._append_rows = original_append_rows
        lrd._append_result_row = original_append_result_row
        ll._append_jsonl = original_append_jsonl
        ll._write_lifecycle_state_snapshot = original_write_state_snapshot
        ol._active_v2_episode = None
        ol._v2_episode_counter = 0
        ol._previous_dashboard_v2_state = None
        ol._live_preparation_row_buffer.clear()
        lrd.reset_live_return_detection()
        ll.reset_live_lifecycle_memory()

    return captured_results, captured_episode_by_id, history_before_start, pending_count


def build_offline_reference(episode_row, full_row_index):
    """
    Recomputes return_context / reversal_context / expansion_split for the
    SAME zone (re-derived via find_preparation_zone for the same
    start_row_id — already proven warm/field-identical to live by
    validate_live_preparation) using the unmodified, validated offline
    functions — imported directly, zero drift — against a ResearchRowIndex
    over the FULL historical dataset (unbounded access), mirroring
    analyze_episode's exact call shape and input construction.
    """
    start_row_id = to_float(episode_row.get("start_row_id"))
    preparation_zone = find_preparation_zone(full_row_index, start_row_id=start_row_id)

    end_dt = parse_datetime_value(episode_row.get("episode_end_timestamp_utc"))
    end_price = to_float(episode_row.get("end_price"))
    episode_direction = episode_direction_proxy(episode_row)

    return_context = detect_preparation_return(
        rows=full_row_index,
        episode=episode_row,
        preparation_zone=preparation_zone,
    )

    future_moves = {}
    for label in _REVERSAL_HORIZON_LABELS:
        future_price = nearest_close_at_or_after(full_row_index, end_dt + HORIZONS[label])
        future_moves[f"move_{label}"] = subtract(future_price, end_price)

    extremes_4h = calculate_window_extremes(
        rows=full_row_index,
        start_dt=end_dt,
        end_dt=end_dt + FOUR_HOURS,
        base_price=end_price,
        suffix="4h",
    )

    reversal_context = analyze_reversal_context(
        rows=full_row_index,
        end_dt=end_dt,
        end_price=end_price,
        episode_direction=episode_direction,
        future_moves=future_moves,
        extremes_4h=extremes_4h,
        return_context=return_context,
    )
    expansion_split = analyze_expansion_reversal_split(
        rows=full_row_index,
        end_dt=end_dt,
        end_price=end_price,
        episode_direction=episode_direction,
        reversal_context=reversal_context,
        extremes_4h=extremes_4h,
    )

    return {
        "return_to_preparation": return_context.get("return_to_preparation"),
        "return_price": return_context.get("return_price"),
        "return_timestamp": return_context.get("return_timestamp"),
        "return_row": return_context.get("return_row"),
        "failed_after_return": reversal_context.get("failed_after_return"),
        "expansion_type": expansion_split.get("expansion_type"),
        "expansion_strength": expansion_split.get("expansion_strength"),
        "reversal_type": reversal_context.get("reversal_type"),
        "reversal_strength": reversal_context.get("reversal_strength"),
        "zone_revisit_count": return_context.get("zone_revisit_count"),
    }


def compare_records(reference, live):
    mismatches = []
    for field in REQUIRED_LIVE_FIELDS:
        reference_value = reference.get(field)
        live_value = live.get(field)
        if not _values_equal(reference_value, live_value):
            mismatches.append(f"{field}: offline={reference_value!r} live={live_value!r}")
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

    full_rows = load_full_rows()
    full_row_index = build_full_row_index(full_rows)

    print(f"Full historical rows (live driven over the complete dataset): {len(full_rows)}")

    live_results, episode_by_id, history_before_start, pending_count = run_live_capture(full_rows)

    warm_results = [
        result for result in live_results
        if history_before_start.get(result["start_row_id"], 0) >= MINIMUM_WARM_HISTORY_ROWS
    ]

    print(f"Live zones that finalized (return resolved + both 4h windows complete): {len(live_results)}")
    print(f"  ...of which 'warm' (>= {MINIMUM_WARM_HISTORY_ROWS} history rows before start_row_id — comparable to a field-identical Preparation zone, per validate_live_preparation): {len(warm_results)}")
    print(f"Zones still pending at end of dataset (return not yet found, or 4h windows incomplete — expected, NOT a defect; see core/live_return_detection.py docstring on unbounded logical tracking): {pending_count}")

    if not warm_results:
        print(
            "\nNo warm finalized zones found in this run — the streaming engine "
            "needs more forward data than the historical dataset provides to "
            "resolve at least one warm zone's return + both 4h windows. This "
            "would indicate the dataset is too short for end-to-end PHASE 3B "
            "validation, not an engine defect."
        )
        raise SystemExit(1)

    results = []
    for live_result in warm_results:
        episode_id = live_result.get("episode_id")
        episode_row = episode_by_id.get(episode_id)

        if episode_row is None:
            results.append({
                "episode_id": episode_id,
                "mismatches": ["missing captured episode_row for offline reference construction"],
                "zone_revisit_count": (None, live_result.get("zone_revisit_count")),
            })
            continue

        reference = build_offline_reference(episode_row, full_row_index)
        results.append({
            "episode_id": episode_id,
            "mismatches": compare_records(reference, live_result),
            "zone_revisit_count": (reference.get("zone_revisit_count"), live_result.get("zone_revisit_count")),
        })

    failures = [r for r in results if r["mismatches"]]

    print("\n--- FIELD-IDENTICAL VALIDATION — required PHASE 3B live fields vs. offline (full-dataset) reference ---")
    for record in results:
        status = "FAIL" if record["mismatches"] else "PASS"
        print(f"  [{status}] episode_id={record['episode_id']}")
        for mismatch in record["mismatches"]:
            print(f"      - {mismatch}")

    print("\n--- DOCUMENTED, NOT COMPARED (by design — see core/live_return_detection.py docstring) ---")
    for record in results:
        offline_value, live_value = record["zone_revisit_count"]
        print(
            f"  episode_id={record['episode_id']}: zone_revisit_count "
            f"offline(full-future-scan)={offline_value!r} live(never computed)={live_value!r} "
            f"-- expected divergence, documented analogously to zone_expired/zone_broken"
        )

    print("\n--- MISMATCH SUMMARY ---")
    if failures:
        print(f"  {len(failures)} of {len(results)} warm finalized zone(s) MISMATCHED on at least one required field:")
        for record in failures:
            print(f"    episode_id={record['episode_id']}: {len(record['mismatches'])} mismatching field(s)")
    else:
        print(f"  0 mismatches across {len(results)} warm finalized zone(s) and {len(REQUIRED_LIVE_FIELDS)} required fields each.")

    if failures:
        print(
            f"\nFAIL — {len(failures)} warm finalized zone(s) diverged from the "
            "offline (full-dataset) reference on at least one required field."
        )
        raise SystemExit(1)

    print(
        "\nPASS — every required PHASE 3B live field "
        f"({', '.join(REQUIRED_LIVE_FIELDS)}) is field-identical to the "
        "validated offline forward-analysis chain (detect_preparation_return / "
        "analyze_reversal_context / analyze_expansion_reversal_split) run "
        "against the full historical dataset, for every warm finalized zone."
    )


if __name__ == "__main__":
    main()

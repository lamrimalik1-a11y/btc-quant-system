"""
Validation harness for LIVE Lifecycle wiring (core.live_lifecycle).

Goal: prove that the live-computable-now lifecycle subset — zone_created,
delta_zscore field events, and preparation_candidate field events, fed into
ZoneLifecycleMemory / FieldLifecycleMemory the instant a live V2 episode
closes — is FORMULA-IDENTICAL to what the validated offline wiring
(tools.analyze_phase1b_episode_research.add_zone_lifecycle_events /
add_delta_field_events / add_preparation_field_events) would produce from
the exact same frozen-snapshot data.

Method: drive the live V2 + live Preparation state machine over a sample
prefix of outputs/historical_observation_rows.csv exactly as
validate_live_preparation.py does (capturing snapshots via a monkeypatched
_append_rows so nothing is written to tracked output files), which in turn
feeds core.live_lifecycle through the wiring added in
core.observation_logger._freeze_live_preparation_snapshot. In parallel, for
each captured (snapshot, episode) pair, build a minimal synthetic
research-log-style row carrying ONLY the fields the live snapshot/episode
actually has available (no return_to_preparation / failed_after_return /
expansion_type / reversal_type — those require the unbounded forward
look-ahead chain live does not implement, see core/live_lifecycle.py's
docstring), and feed it through the OFFLINE wiring functions — imported
directly, zero drift — into a separate, isolated reference memory pair.

Comparing the two proves the FORMULA outputs (lifecycle_state
classification, thresholds, zone_price/zone_strength/field_value/
field_strength) are identical. The IDENTITY fields (zone_id / field_id /
zone_source / research_notes / event_timestamp source) are EXPECTED,
DOCUMENTED, structural differences — live has no case_id (an RDM-only
concept) and stamps its own live clock — and are reported separately, not
as defects.

This does not download data, does not call the replay generator, does not
modify any formula/threshold/B12v2/RDM/Synthesis/Preparation/Lifecycle
logic, and does not write to any tracked output file.

Usage: python -m tools.validate_live_lifecycle
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

import core.live_lifecycle as ll
import core.observation_logger as ol
from context_memory import FieldLifecycleMemory, ZoneLifecycleMemory
from tools.analyze_phase1b_episode_research import (
    add_delta_field_events,
    add_preparation_field_events,
    add_zone_lifecycle_events,
)
from tools.validate_live_preparation import (
    MINIMUM_WARM_HISTORY_ROWS,
    SAMPLE_ROWS,
    _count_rows_before,
    _event_timestamp,
    load_sample_rows,
)

ROOT = Path(__file__).resolve().parents[1]
OBSERVATION_ROWS_FILE = ROOT / "outputs" / "historical_observation_rows.csv"

NUMERIC_TOLERANCE = 1e-9

# Fields whose VALUES must be formula-identical between live and the offline
# wiring run on the same frozen-snapshot data — these are the thresholded /
# classified outputs the wiring computes, not identity bookkeeping.
ZONE_FORMULA_FIELDS = [
    "lifecycle_state",
    "zone_type",
    "zone_price",
    "zone_strength",
    "reaction_quality",
    "lifecycle_age",
    "test_count",
    "rejection_count",
    "break_count",
    "reclaim_count",
]

FIELD_FORMULA_FIELDS = [
    "lifecycle_state",
    "field_type",
    "field_value",
    "field_strength",
]

# IDENTITY fields that intentionally differ — live has no case_id (RDM-only
# concept; see core/live_lifecycle.py docstring) and uses a "live_*"
# zone_source / "LIVE_" id marker for traceability/non-collision. These are
# reported as expected structural differences, never compared for equality.
EXPECTED_IDENTITY_DIFFERENCES = [
    "zone_id / field_id naming: live uses LIVE_PREP_ZONE_{episode_id} / "
    "{field_type}_LIVE_{episode_id} (no case_id available live — case_id is "
    "an RDM-only concept); offline uses PREP_ZONE_{case_id}_{episode_id} / "
    "{field_type}_{case_id}_{episode_id}.",
    "zone_source: live tags 'live_preparation_detector' vs offline "
    "'phase1b_research_preparation_detector' — traceability marker only.",
    "event_timestamp_utc source: live derives from the live V2 episode's own "
    "episode_start_timestamp_utc (live clock); offline uses the research "
    "log's episode_start_time_utc (historical replay clock).",
    "research_notes: live vs offline wording differs (both describe the same "
    "event; text is presentational, not a formula output).",
]

# Lifecycle states / field types the offline wiring CAN emit but that the
# live wiring intentionally does not (yet) emit, because they depend on the
# unbounded forward look-ahead chain (detect_preparation_return /
# analyze_reversal_context) — see core/live_lifecycle.py's module docstring
# for the full architectural finding. These are the central, expected
# "mismatches": absence by design, not a defect to fix in this phase.
DEFERRED_ZONE_STATES = ["zone_tested", "zone_rejected", "zone_reclaimed"]
DEFERRED_FIELD_TYPES = ["expansion_state", "reversal_state", "hypothesis02_state"]


def load_full_rows():
    return pd.read_csv(OBSERVATION_ROWS_FILE, low_memory=False)


def run_live_capture(market_rows):
    """
    Drives the live V2 + live Preparation state machine row by row exactly
    as validate_live_preparation.run_live_capture does — including feeding
    _capture_preparation_row and _freeze_live_preparation_snapshot, which
    (per the wiring added in this phase) also feeds core.live_lifecycle.
    Captures snapshots/episodes in memory; nothing is written to tracked
    output files (both _append_rows and core.live_lifecycle's JSONL/CSV
    writers are monkeypatched out for the duration of this run).
    """
    captured_snapshots = []
    captured_episode_by_id = {}

    original_append_rows = ol._append_rows
    original_append_jsonl = ll._append_jsonl
    original_write_state_snapshot = ll._write_lifecycle_state_snapshot

    def capture_append_rows(path, fieldnames, rows):
        if path == ol.LIVE_PREPARATION_FILE:
            captured_snapshots.extend(rows)
            return
        if path == ol.DASHBOARD_V2_EPISODES_FILE:
            for captured_row in rows:
                captured_episode_by_id[captured_row.get("episode_id")] = captured_row
            return
        original_append_rows(path, fieldnames, rows)

    ll.reset_live_lifecycle_memory()
    ol._active_v2_episode = None
    ol._v2_episode_counter = 0
    ol._previous_dashboard_v2_state = None
    ol._live_preparation_row_buffer.clear()
    ol._append_rows = capture_append_rows
    ll._append_jsonl = lambda path, payload: None
    ll._write_lifecycle_state_snapshot = lambda: None

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
        ll._append_jsonl = original_append_jsonl
        ll._write_lifecycle_state_snapshot = original_write_state_snapshot
        ol._active_v2_episode = None
        ol._v2_episode_counter = 0
        ol._previous_dashboard_v2_state = None
        ol._live_preparation_row_buffer.clear()

    return captured_snapshots, captured_episode_by_id, history_before_start


def build_synthetic_offline_row(snapshot, episode):
    """
    Minimal research-log-style row carrying ONLY the fields available to the
    live process at V2 episode close / Preparation freeze — deliberately
    omitting return_to_preparation / failed_after_return / expansion_type /
    reversal_type / direct_reversal_flag / expansion_after_return (the
    forward-look-ahead-derived fields live cannot compute). Feeding this into
    the unmodified offline wiring functions therefore exercises exactly the
    same "computable now" code paths live does — the correct apples-to-apples
    comparison for this phase's scope.
    """
    return {
        "case_id": None,
        "episode_id": snapshot.get("episode_id"),
        "start_row_id": snapshot.get("start_row_id"),
        "episode_start_time_utc": episode.get("episode_start_timestamp_utc"),
        "preparation_candidate": snapshot.get("preparation_candidate"),
        "preparation_mid_price": snapshot.get("preparation_mid_price"),
        "preparation_strength": snapshot.get("preparation_strength"),
        "preparation_duration_rows": snapshot.get("preparation_duration_rows"),
        "peak_delta_zscore": episode.get("peak_delta_zscore"),
    }


def run_offline_reference_wiring(snapshots, episode_by_id):
    """
    Feeds each synthetic row through the unmodified, validated offline
    wiring functions (imported directly — zero drift) into a fresh, isolated
    reference memory pair, mirroring exactly what
    tools.analyze_phase1b_episode_research.build_lifecycle_memories does for
    each research-log row (minus the forward-derived fields, by design).
    """
    zone_memory = ZoneLifecycleMemory()
    field_memory = FieldLifecycleMemory()

    for snapshot in snapshots:
        episode = episode_by_id.get(snapshot.get("episode_id"), {})
        synthetic_row = build_synthetic_offline_row(snapshot, episode)

        add_zone_lifecycle_events(zone_memory, synthetic_row)
        add_delta_field_events(
            field_memory,
            synthetic_row,
            case_id=synthetic_row["case_id"],
            episode_id=synthetic_row["episode_id"],
            row_index=synthetic_row["start_row_id"],
            event_timestamp=synthetic_row["episode_start_time_utc"],
        )
        add_preparation_field_events(
            field_memory,
            synthetic_row,
            case_id=synthetic_row["case_id"],
            episode_id=synthetic_row["episode_id"],
            row_index=synthetic_row["start_row_id"],
            event_timestamp=synthetic_row["episode_start_time_utc"],
        )

    return zone_memory, field_memory


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


def compare_zone_records(reference_zone, live_zone):
    mismatches = []
    for field in ZONE_FORMULA_FIELDS:
        reference_value = reference_zone.get(field)
        live_value = live_zone.get(field)
        if not _values_equal(reference_value, live_value):
            mismatches.append(f"{field}: offline={reference_value!r} live={live_value!r}")
    return mismatches


def compare_field_records(reference_field, live_field):
    mismatches = []
    for field in FIELD_FORMULA_FIELDS:
        reference_value = reference_field.get(field)
        live_value = live_field.get(field)
        if not _values_equal(reference_value, live_value):
            mismatches.append(f"{field}: offline={reference_value!r} live={live_value!r}")
    return mismatches


def main():
    if not OBSERVATION_ROWS_FILE.exists():
        raise SystemExit(f"Required input not found: {OBSERVATION_ROWS_FILE}")

    market_rows = load_sample_rows()
    full_rows = load_full_rows()

    live_snapshots, live_episode_by_id, history_before_start = run_live_capture(market_rows)

    candidate_snapshots = [s for s in live_snapshots if str(s.get("preparation_candidate")).strip().lower() in {"true", "1", "yes"}]
    warm_count = sum(
        1 for s in candidate_snapshots
        if history_before_start.get(s["start_row_id"], 0) >= MINIMUM_WARM_HISTORY_ROWS
    )

    print(f"Sample rows (live, prefix-fed): {len(market_rows)}")
    print(f"Full historical rows (offline reference dataset present): {len(full_rows)}")
    print(f"Live preparation snapshots captured: {len(live_snapshots)}")
    print(f"  ...of which preparation_candidate=True: {len(candidate_snapshots)}")
    print(f"  ...of which 'warm' (>= {MINIMUM_WARM_HISTORY_ROWS} live history rows, informational only — see note below): {warm_count}")
    print(
        "  NOTE: 'warm vs cold' governs whether a live-computed PREPARATION "
        "ZONE matches the offline find_preparation_zone reference (already "
        "validated PASS in validate_live_preparation). It is irrelevant here: "
        "this harness feeds the SAME live-computed snapshot values into BOTH "
        "the live wiring and the offline wiring functions, so it tests "
        "whether the LIFECYCLE FORMULA — not the underlying zone computation "
        "— is identical. All preparation_candidate=True snapshots are used."
    )

    # Feed ALL captured snapshots through the offline wiring — not just the
    # candidates — because add_delta_field_events (unlike add_zone_lifecycle_
    # events / add_preparation_field_events) is NOT gated on
    # preparation_candidate; it fires for every episode with a valid
    # peak_delta_zscore, exactly mirroring what record_live_field_lifecycle_
    # events does live. The offline functions already gate zone_created /
    # preparation_candidate internally, so this remains a true apples-to-
    # apples replica of the live call sequence.
    reference_zone_memory, reference_field_memory = run_offline_reference_wiring(
        live_snapshots, live_episode_by_id
    )

    live_zone_memory = ll.get_zone_memory()
    live_field_memory = ll.get_field_memory()

    print(f"\nReference (offline-wiring-on-live-snapshot-data) zones created: {len(reference_zone_memory._zones)}")
    print(f"Live zones created: {len(live_zone_memory._zones)}")
    print(f"Reference field records created: {len(reference_field_memory._fields)}")
    print(f"Live field records created: {len(live_field_memory._fields)}")

    zone_results = []
    for snapshot in candidate_snapshots:
        episode_id = snapshot.get("episode_id")
        reference_zone_id = f"PREP_ZONE_None_{episode_id}"
        live_zone_id = ll.live_zone_id(episode_id)

        reference_zone = reference_zone_memory.get_zone(reference_zone_id)
        live_zone = live_zone_memory.get_zone(live_zone_id)

        if reference_zone is None or live_zone is None:
            zone_results.append({
                "episode_id": episode_id,
                "mismatches": [f"missing record: offline_present={reference_zone is not None} live_present={live_zone is not None}"],
            })
            continue

        zone_results.append({
            "episode_id": episode_id,
            "mismatches": compare_zone_records(reference_zone, live_zone),
        })

    field_results = []
    candidate_episode_ids = {s.get("episode_id") for s in candidate_snapshots}
    for snapshot in live_snapshots:
        episode_id = snapshot.get("episode_id")
        applicable_field_types = ["delta_zscore"]
        if episode_id in candidate_episode_ids:
            applicable_field_types.append("preparation_candidate")

        for field_type in applicable_field_types:
            reference_field_id = f"{field_type}_None_{episode_id}"
            live_field_id = ll.live_field_id(field_type, episode_id)

            reference_field = reference_field_memory.get_field(reference_field_id)
            live_field = live_field_memory.get_field(live_field_id)

            if reference_field is None and live_field is None:
                continue

            if reference_field is None or live_field is None:
                field_results.append({
                    "episode_id": episode_id,
                    "field_type": field_type,
                    "mismatches": [f"missing record: offline_present={reference_field is not None} live_present={live_field is not None}"],
                })
                continue

            field_results.append({
                "episode_id": episode_id,
                "field_type": field_type,
                "mismatches": compare_field_records(reference_field, live_field),
            })

    zone_failures = [r for r in zone_results if r["mismatches"]]
    field_failures = [r for r in field_results if r["mismatches"]]

    print("\n--- ZONE LIFECYCLE (zone_created) — formula fields must be identical ---")
    for record in zone_results:
        status = "FAIL" if record["mismatches"] else "PASS"
        print(f"  [{status}] episode_id={record['episode_id']}")
        for mismatch in record["mismatches"]:
            print(f"      - {mismatch}")

    print("\n--- FIELD LIFECYCLE (delta_zscore / preparation_candidate) — formula fields must be identical ---")
    for record in field_results:
        status = "FAIL" if record["mismatches"] else "PASS"
        print(f"  [{status}] episode_id={record['episode_id']} field_type={record['field_type']}")
        for mismatch in record["mismatches"]:
            print(f"      - {mismatch}")

    print("\n--- EXPECTED IDENTITY DIFFERENCES (documented, not defects) ---")
    for note in EXPECTED_IDENTITY_DIFFERENCES:
        print(f"  - {note}")

    print("\n--- DEFERRED LIFECYCLE SUBSYSTEM (documented scope limitation, not a defect) ---")
    print(
        "  The following offline-emittable lifecycle states / field types are NOT "
        "produced by live lifecycle in this phase, because they depend on the "
        "unbounded forward look-ahead chain (detect_preparation_return -> "
        "analyze_reversal_context -> ~15 functions) — see core/live_lifecycle.py "
        "module docstring for the full architectural finding:"
    )
    print(f"    zone states:  {', '.join(DEFERRED_ZONE_STATES)}")
    print(f"    field types:  {', '.join(DEFERRED_FIELD_TYPES)}")
    print(
        "  zone_expired / zone_broken / field_expired are emitted by NEITHER "
        "offline nor live (confirmed: offline wiring never triggers them — "
        "no ground-truth formula exists to mirror)."
    )

    if not candidate_snapshots:
        print(
            "\nNo warm preparation_candidate snapshots found in this sample — "
            "increase SAMPLE_ROWS in tools.validate_live_preparation (while "
            "staying <= the live buffer maxlen) to capture comparable episodes."
        )
        raise SystemExit(1)

    if zone_failures or field_failures:
        print(
            f"\nFAIL — {len(zone_failures)} zone record(s) and {len(field_failures)} "
            f"field record(s) mismatched the offline-wiring-on-live-snapshot-data reference."
        )
        raise SystemExit(1)

    print(
        "\nPASS — every live-computable-now lifecycle event "
        "(zone_created, delta_zscore, preparation_candidate) is formula-identical "
        "to the validated offline wiring run on the same frozen snapshot data."
    )


if __name__ == "__main__":
    main()

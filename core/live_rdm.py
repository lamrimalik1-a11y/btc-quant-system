"""
LIVE RDM (PHASE 4 of the LIVE integration roadmap).

Per the explicit governing directive: "LIVE RDM must behave exactly like
REPLAY RDM. The same mechanics. The same formulas. The same calculations.
The same classifications. The same outputs. The same architecture." This
module does NOT redesign, simplify, or lighten RDM. It wraps and reuses the
already-validated functions in research.zone_mechanics_calculator (the
verbatim replay RDM engine), feeding them a single completed live case
instead of the full offline population.

────────────────────────────────────────────────────────────────────────────
WHAT "completed live case" MEANS HERE
────────────────────────────────────────────────────────────────────────────
A live Preparation zone whose return-to-preparation has resolved — exactly
the point core.live_return_detection._finalize_pending_zone already reaches
(merged_row = snapshot_row + return_context + reversal_context +
expansion_split, the same shape offline's analyze_episode produces for one
zone, per build_dataset's merge of research_log + episodes + case_labels).
This module is invoked from that exact hook, once, per finalized zone — never
on pending/open zones, never with look-ahead beyond the completed case's own
resolved window.

────────────────────────────────────────────────────────────────────────────
DESIGN — "thin adapter, not reimplementation"
────────────────────────────────────────────────────────────────────────────
1. Case-row assembly (build_completed_live_case_row): merges the live
   merged_row with the small set of offline dataset/research-log columns it
   does not yet carry under the SAME names — peak_* fields from episode_row
   (V2_EPISODE_FIELDNAMES already has them), name aliases
   (episode_start_time_utc / episode_end_time_utc), pre_range /
   pre_volatility_proxy / pre_direction / pre_compression_flag (recomputed
   VERBATIM via calculate_pre_episode_state against the same buffered
   pre-episode rows find_preparation_zone already consumed — strictly
   pre-episode, zero leakage), score_bucket (recomputed VERBATIM via
   score_bucket(peak_layer_count) — a pure function of an already-available
   field) — and documents the two genuinely unsupported fields (case_label,
   price_at_*/score-bucket's sibling pre-episode pass-throughs) as "" exactly
   the way value(row, column, default="") already treats missing/NaN data
   offline. See UNSUPPORTED FIELDS in the PHASE 4 report for the full list
   and the reason each one cannot be reproduced live.

2. Event re-keying (_rekey_events_to_case): live lifecycle events carry
   related_episode_id, not related_case_id. The adapter filters
   get_recent_zone_events()/get_recent_field_events() by
   related_episode_id == episode_id, stamps a synthetic
   related_case_id = live_zone_id(episode_id) — the SAME identifier this
   module assigns to the assembled case row's case_id — and hands the result
   to events_for_case/event_states/count_state UNMODIFIED. Only the join
   key's source changes; the verbatim event-filtering call chain runs as-is.

3. Pipeline (compute_live_rdm_for_case): runs the EXACT sequence of Group A
   / Group B builder + merge functions main() runs, verbatim-imported from
   research.zone_mechanics_calculator, against a single-row results_df for
   this one completed case (each of those functions iterates results.iterrows()
   independently — confirmed by direct inspection — so single-row input
   produces field-identical per-row output with zero population dependency).
   The per-zone "historical_rows" companion build_live_rdm_evolution /
   attach_historical_delta_to_live_rows need is supplied by
   core.live_return_detection.build_zone_feature_window(pending) — the
   per-zone row-feature buffer captured across [preparation_start_row,
   return_row], the exact span live_row_window resolves offline.

   Group C (build_zone_strength_profile / build_zone_vs_attacker_profile /
   build_zone_anomaly_profile / build_zone_reinforcement_profile /
   build_attacker_conversion_profile / build_zone_structural_trajectory /
   build_zone_structural_prediction / build_zone_synthesis) is SKIPPED —
   these compute population-relative baselines (percentile ranks, population
   maxima/means across all cases) that are structurally undefined for a
   single completed case observed in isolation. Documented as an
   architectural limitation, not approximated.

No formula, threshold, or classification is redefined anywhere in this
module. Every numeric/classification field is produced by calling the
validated offline function directly. Research only — no execution, no
trading, no signals.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from research.zone_mechanics_calculator import (
    RdmCaseCache,
    add_dynamic_layers_to_timeline_live,
    add_rdm_result_summaries,
    add_rdm_v16_numeric_foundation,
    build_attacker_evolution,
    build_force_allocation_profile,
    build_interaction_core_geometry,
    build_interaction_density_map,
    build_live_rdm_evolution,
    build_mechanics_capacity,
    build_mechanics_lifecycle,
    build_mechanics_sigma,
    build_mechanics_timeline,
    build_real_geometry_tracking,
    build_sigma_evolution,
    build_true_lifecycle_tracking,
    build_verestchaguine_fleche,
    build_zone_birth_registry,
    build_zone_death_registry,
    build_zone_evolution_chart,
    build_zone_evolution_history,
    build_zone_health_evolution,
    build_zone_mechanical_memory,
    build_zone_structural_prediction,
    build_zone_structural_trajectory,
    build_zone_visit_timeline,
    calculate_zone_mechanics_row,
    merge_capacity_into_results,
    merge_interaction_core_into_results,
    merge_interaction_density_into_results,
    merge_live_rdm_evolution_into_results,
    merge_real_geometry_tracking_into_results,
    merge_sigma_evolution_into_results,
    merge_sigma_into_results,
    merge_true_lifecycle_into_results,
    merge_verestchaguine_into_results,
    round_float,
    run_zone_visit_timeline_dynamic_live,
    to_float,
    utc_now,
    value,
)
from research.synthesis_engine import build_zone_synthesis
from tools.analyze_phase1b_episode_research import (
    ResearchRowIndex,
    calculate_pre_episode_state,
    parse_datetime_value,
    prepare_rows,
    score_bucket,
)
from core.live_lifecycle import get_field_memory, get_zone_memory, live_zone_id
from context_memory import MARKET_CONTEXT_MEMORY_SIZE

OUTPUT_DIR = Path("outputs")
LIVE_RDM_RESULTS_FILE = OUTPUT_DIR / "live_rdm_results.csv"
LIVE_RDM_EVOLUTION_FILE = OUTPUT_DIR / "live_rdm_evolution.csv"
LIVE_RDM_STATE_FILE = OUTPUT_DIR / "live_rdm_state.csv"

# B12 (Live Validation Instrumentation) -- ADDITIVE, research-only. Own file;
# does not alter any existing output file's columns or rows.
LIVE_B12_VALIDATION_FILE = OUTPUT_DIR / "live_b12_validation.csv"
LIVE_B10_TRAJECTORY_FILE = OUTPUT_DIR / "live_b10_trajectory.csv"
LIVE_B11_PREDICTION_FILE = OUTPUT_DIR / "live_b11_prediction.csv"
LIVE_SYNTHESIS_FILE = OUTPUT_DIR / "live_synthesis.csv"

# Fields the live dataset row carries directly under the SAME name offline's
# dataset (research_log + episodes peak_* merge) uses — pure pass-through,
# zero transformation. See V2_EPISODE_FIELDNAMES in core.observation_logger.
_PEAK_FIELDS_FROM_EPISODE_ROW = (
    "peak_state",
    "peak_layer_count",
    "peak_max_severity",
    "peak_primary_context",
    "peak_conditions",
    "peak_active_layers",
    "peak_observation_confidence",
    "peak_rvi",
    "peak_velocity",
    "duration_seconds",
    "start_price",
    "end_price",
)

# Genuinely unreproducible live — require an unbounded forward/future-row scan
# beyond the completed case's own resolved window (look-ahead is forbidden).
# Offline's value(row, column, default="") already treats missing/NaN the
# same way ("" is the documented missing-value representation, not an
# approximation of a real value).
_FUTURE_LOOKAHEAD_PASSTHROUGH_FIELDS = (
    "price_at_1m",
    "price_at_5m",
    "price_at_15m",
    "price_at_30m",
    "price_at_1h",
    "price_at_2h",
    "price_at_4h",
    "price_at_day_end",
)

# case_label comes from zone_mechanics_case_labels.csv -- a hand-curated,
# population-scoped reference file keyed by case_id values that only exist in
# the offline replay run. A live case_id is a synthetic identifier
# (live_zone_id) that cannot appear in that file; there is no live equivalent
# of "manually label this completed case" at finalization time.
_EXTERNAL_LABEL_PASSTHROUGH_FIELDS = ("case_label",)

_live_rdm_state = {}


def reset_live_rdm_state():
    """Used only by validation harnesses to start a clean, isolated run."""
    _live_rdm_state.clear()


def _live_case_identifier(episode_id):
    return live_zone_id(episode_id)


def _events_dataframe(raw_events):
    if not raw_events:
        return pd.DataFrame()
    return pd.DataFrame(raw_events)


def _rekey_events_to_case(events, episode_id):
    """
    Live lifecycle events carry related_episode_id (see
    core.live_lifecycle.LIVE_*_LIFECYCLE_STATE_FIELDNAMES /
    record_live_return_lifecycle_events). events_for_case (the verbatim,
    unmodified offline filter) keys on related_case_id. This adapter performs
    ONLY the join-key substitution: filter by related_episode_id, then stamp
    the SAME synthetic identifier this module uses for the case row's
    case_id — so events_for_case / event_states / count_state run100%
    verbatim against correctly-shaped input.
    """
    if events.empty or "related_episode_id" not in events.columns:
        return events.head(0).copy()

    matched = events[events["related_episode_id"].astype(str) == str(episode_id)].copy()
    matched["related_case_id"] = _live_case_identifier(episode_id)
    return matched


def collect_live_case_events(episode_id):
    """
    Fetches the full bounded zone/field lifecycle event history
    (MARKET_CONTEXT_MEMORY_SIZE-bounded — large relative to one zone's
    ~5-8-event lifecycle, the same retention-bound pattern
    _live_preparation_row_buffer already relies on) and re-keys it to this
    case. Returns (zone_events, field_events) DataFrames shaped exactly as
    events_for_case expects.
    """
    zone_events = _events_dataframe(get_zone_memory().get_recent_zone_events(limit=MARKET_CONTEXT_MEMORY_SIZE))
    field_events = _events_dataframe(get_field_memory().get_recent_field_events(limit=MARKET_CONTEXT_MEMORY_SIZE))
    return (
        _rekey_events_to_case(zone_events, episode_id),
        _rekey_events_to_case(field_events, episode_id),
    )


def _pre_episode_row_index(feature_window, start_row_id):
    """
    Builds a ResearchRowIndex over strictly-pre-episode rows from the
    captured per-zone feature window (which already spans
    [preparation_start_row, return_row] -- backfilled from the SAME
    _live_preparation_row_buffer find_preparation_zone consumes). Used only
    to recompute pre_range / pre_volatility_proxy / pre_direction /
    pre_compression_flag VERBATIM via calculate_pre_episode_state -- strictly
    pre-episode data, zero leakage, zero new retention mechanism.
    """
    if feature_window.empty or start_row_id is None:
        return None

    start_row = to_float(start_row_id)
    if start_row is None:
        return None

    frame = feature_window.copy()
    frame["row_id_numeric"] = pd.to_numeric(frame["row_id"], errors="coerce")
    pre_rows = frame[frame["row_id_numeric"] < start_row].drop(columns=["row_id_numeric"])
    if pre_rows.empty:
        return None

    prepared = prepare_rows(pre_rows)
    if prepared.empty:
        return None

    return ResearchRowIndex(prepared)


def _pre_episode_context(case_row, feature_window):
    """
    Recomputes pre_range / pre_volatility_proxy / pre_direction /
    pre_compression_flag via the VERBATIM offline function
    calculate_pre_episode_state, fed a ResearchRowIndex over the buffered
    pre-episode rows -- the live mirror of analyze_episode's own call shape
    (rows.before_time / rows.before_row_id over data strictly before
    start_dt / start_row_id). Returns {} (leaving the case row's existing
    "" defaults in place) if the buffered window cannot support it.
    """
    start_row_id = case_row.get("start_row_id")
    row_index = _pre_episode_row_index(feature_window, start_row_id)
    if row_index is None:
        return {}

    start_dt = parse_datetime_value(case_row.get("episode_start_time_utc"))
    if start_dt is None:
        return {}

    base_price = to_float(case_row.get("start_price"))
    return calculate_pre_episode_state(
        rows=row_index,
        start_dt=start_dt,
        start_row_id=to_float(start_row_id),
        base_price=base_price,
    )


def build_completed_live_case_row(pending, merged_row, feature_window):
    """
    Assembles the single completed live case row in the exact shape
    build_dataset's merged research_log+episodes+case_labels rows take —
    the row calculate_zone_mechanics_row (and every downstream RDM stage)
    consumes. Field provenance:

      - merged_row (snapshot_row + return_context + reversal_context +
        expansion_split): direct, field-identical to offline's
        analyze_episode output for this zone (validated PHASE 3A/3B).
      - case_id: synthetic live_zone_id(episode_id) -- offline has no live
        equivalent; used consistently here AND for event re-keying so
        events_for_case resolves correctly.
      - episode_start_time_utc / episode_end_time_utc: name-aliased from
        live's episode_start_timestamp_utc / episode_end_timestamp_utc
        (key-mapping only -- zero value transformation).
      - peak_* / duration_seconds / start_price / end_price: copied from
        episode_row (V2_EPISODE_FIELDNAMES already carries them).
      - pre_range / pre_volatility_proxy / pre_direction /
        pre_compression_flag: recomputed verbatim, see _pre_episode_context.
      - score_bucket: recomputed verbatim via score_bucket(peak_layer_count)
        -- a pure function of an already-available field, zero drift.
      - price_at_* / price_at_day_end: "" -- requires future-row look-ahead
        beyond the completed case's resolved window (forbidden).
      - case_label: "" -- requires the offline-only, hand-curated
        zone_mechanics_case_labels.csv keyed by offline case_id values.
    """
    episode_id = pending.episode_id
    case_id = _live_case_identifier(episode_id)
    episode_row = pending.episode_row or {}

    case_row = dict(merged_row)
    case_row["case_id"] = case_id
    case_row["episode_id"] = episode_id
    case_row["episode_start_time_utc"] = merged_row.get("episode_start_timestamp_utc")
    case_row["episode_end_time_utc"] = merged_row.get("episode_end_timestamp_utc")
    case_row["source_status"] = "FOUND"

    for field in _PEAK_FIELDS_FROM_EPISODE_ROW:
        if field not in case_row or case_row.get(field) in (None, ""):
            case_row[field] = episode_row.get(field, "")

    for field in _FUTURE_LOOKAHEAD_PASSTHROUGH_FIELDS:
        case_row.setdefault(field, "")

    for field in _EXTERNAL_LABEL_PASSTHROUGH_FIELDS:
        case_row.setdefault(field, "")
    case_row.setdefault("reference_example_flag", False)

    case_row["score_bucket"] = score_bucket(case_row.get("peak_layer_count"))

    pre_episode_context = _pre_episode_context(case_row, feature_window)
    for field in ("pre_range", "pre_volatility_proxy", "pre_direction", "pre_compression_flag"):
        if field in pre_episode_context:
            case_row[field] = pre_episode_context[field]
        else:
            case_row.setdefault(field, "")

    return case_row


def _single_row_frame(case_row):
    return pd.DataFrame([case_row])


def _run_group_a(results_df, zone_events, field_events, run_utc):
    """
    Group A -- base mechanics through real-geometry tracking, in the exact
    sequential order main() runs them. Every stage operates row-by-row on
    `results` independently (confirmed by direct inspection of each
    build_mechanics_* / build_verestchaguine_fleche / build_real_geometry_
    tracking body); single-row input yields field-identical per-row output.
    """
    base_row = calculate_zone_mechanics_row(
        row=results_df.iloc[0],
        zone_events=zone_events,
        field_events=field_events,
        run_utc=run_utc,
    )
    results_df = pd.DataFrame([base_row])

    capacity_df = build_mechanics_capacity(results_df, run_utc)
    results_df = merge_capacity_into_results(results_df, capacity_df)

    sigma_df = build_mechanics_sigma(results_df, run_utc)
    results_df = merge_sigma_into_results(results_df, sigma_df)

    sigma_evolution_df = build_sigma_evolution(results_df, run_utc)
    results_df = merge_sigma_evolution_into_results(results_df, sigma_evolution_df)

    verestchaguine_df = build_verestchaguine_fleche(results_df, run_utc)
    results_df = merge_verestchaguine_into_results(results_df, verestchaguine_df)

    results_df = add_rdm_result_summaries(results_df)

    geometry_tracking_df = build_real_geometry_tracking(results_df, run_utc)
    results_df = merge_real_geometry_tracking_into_results(results_df, geometry_tracking_df)

    return results_df


def _run_group_b(results_df, feature_window, run_utc):
    """
    Group B -- live RDM evolution through true-lifecycle tracking, in the
    exact sequential order main() runs them. feature_window stands in for
    offline's full historical_observation_rows.csv: build_live_rdm_evolution
    internally derives the same [start_row, end_row] window via
    live_row_window(zone, rows_source) from the case row's own
    preparation_start_row / start_row_id / return_row / end_row_id /
    preparation_end_row fields and slices rows_source by row_id range --
    feature_window already IS that exact per-zone slice (captured across
    [preparation_start_row, return_row], verified zero-gap/zero-duplicate),
    so the slice the verbatim function resolves is field-identical to what
    it would resolve from the full dataset for this same zone.
    """
    live_evolution_df = build_live_rdm_evolution(results_df, feature_window, run_utc)
    results_df = merge_live_rdm_evolution_into_results(results_df, live_evolution_df)

    attacker_df = build_attacker_evolution(results_df, live_evolution_df, feature_window, run_utc)

    case_cache = RdmCaseCache(live_evolution_df)
    case_cache.precompute_interaction_masks()

    interaction_core_df = build_interaction_core_geometry(
        results_df, live_evolution_df, run_utc, case_cache=case_cache
    )
    results_df = merge_interaction_core_into_results(results_df, interaction_core_df)

    density_df = build_interaction_density_map(
        results_df, live_evolution_df, run_utc, case_cache=case_cache
    )
    results_df = merge_interaction_density_into_results(results_df, density_df)

    true_lifecycle_df = build_true_lifecycle_tracking(
        results_df, interaction_core_df, live_evolution_df, run_utc, case_cache=case_cache
    )
    results_df = merge_true_lifecycle_into_results(results_df, true_lifecycle_df)

    results_df = add_rdm_v16_numeric_foundation(results_df)

    return results_df, live_evolution_df, attacker_df, case_cache


def _make_episodes_df(results_df):
    """
    Build a minimal episodes DataFrame for Synthesis from the single live case
    row. Synthesis.assemble_bundles accesses Bundle A fields (peak_state,
    peak_layer_count, peak_max_severity, peak_primary_context) from episodes_df
    keyed by episode_id. These fields are already in results_df (they were
    copied from pending.episode_row during build_completed_live_case_row), so
    projecting them into episodes_df shape costs nothing and avoids an
    external lookup.
    """
    if results_df.empty:
        return pd.DataFrame()
    row = results_df.iloc[0]
    return pd.DataFrame([{
        "episode_id": row.get("episode_id"),
        "peak_state": row.get("peak_state", ""),
        "peak_layer_count": row.get("peak_layer_count", ""),
        "peak_max_severity": row.get("peak_max_severity", ""),
        "peak_primary_context": row.get("peak_primary_context", ""),
    }])


def _run_memory_and_timeline_stages(results_df, live_evolution_df, attacker_df, run_utc):
    """
    Birth/death/memory/timeline/evolution/visit-timeline/health-evolution/
    B10 structural-trajectory/B11 structural-prediction/Synthesis --
    every stage iterates results (and small per-case companion frames) row-
    by-row with no cross-case aggregation.

    B8 (build_zone_visit_timeline): per-case — uses only live_evolution_df
    and attacker_df rows for this case's own zone_id/case_id.
    B9 (build_zone_health_evolution): per-case — aggregates this zone's own
    B8 visit rows.
    B10 (build_zone_structural_trajectory): per-case — classifies B9 summary.
    B11 (build_zone_structural_prediction): per-case in its core label and
    confidence logic; vs_attacker_df is passed empty because B3/B4
    (population-normalized strength/attacker profiles) are structurally
    undefined for a single isolated case (same limitation as Group C in
    Phase 4). force_ratio, zone_strength_score, attacker_force_score are NA
    in live output; structural_prediction label and prediction_confidence
    achieve full Replay parity. prediction_score may differ from the replay
    batch value by +/-7 to +/-12 pts on [-100,+100] when the replay's
    force_ratio would have triggered a threshold adjustment -- documented
    as UNSUPPORTED, not approximated.
    Synthesis (build_zone_synthesis): per-case -- combines B10 trajectory,
    B11 prediction, and episode-level peak context fields. engagement column
    uses force_balance(_force_balance) which receives None force_ratio in
    live, producing "unknown balance" vs replay's actual classification --
    documented as UNSUPPORTED.
    """
    timeline_df = build_mechanics_timeline(results_df, run_utc)
    lifecycle_df = build_mechanics_lifecycle(timeline_df, run_utc)

    birth_df = build_zone_birth_registry(results_df, run_utc)
    death_df = build_zone_death_registry(results_df, run_utc)
    memory = build_zone_mechanical_memory(results_df, birth_df, death_df, timeline_df, run_utc)

    evolution_chart_df = build_zone_evolution_chart(results_df, birth_df, death_df, run_utc)
    evolution_history_df = build_zone_evolution_history(evolution_chart_df, run_utc)

    force_allocation_df = build_force_allocation_profile(results_df, attacker_df, run_utc)
    visit_timeline_df = build_zone_visit_timeline(results_df, live_evolution_df, attacker_df, run_utc)
    health_evolution_df = build_zone_health_evolution(results_df, visit_timeline_df, run_utc)

    trajectory_df = build_zone_structural_trajectory(results_df, health_evolution_df, run_utc)
    prediction_df = build_zone_structural_prediction(
        results_df, trajectory_df, pd.DataFrame(), run_utc
    )
    episodes_df = _make_episodes_df(results_df)
    synthesis_df = build_zone_synthesis(
        results_df, trajectory_df, prediction_df, episodes_df, run_utc
    )

    return {
        "timeline": timeline_df,
        "lifecycle": lifecycle_df,
        "birth": birth_df,
        "death": death_df,
        "memory": memory,
        "evolution_chart": evolution_chart_df,
        "evolution_history": evolution_history_df,
        "force_allocation": force_allocation_df,
        "visit_timeline": visit_timeline_df,
        "health_evolution": health_evolution_df,
        "trajectory": trajectory_df,
        "prediction": prediction_df,
        "synthesis": synthesis_df,
    }


def compute_live_rdm_for_case(
    pending, merged_row, feature_window, event_timestamp,
    emit_status="PENDING_FINALIZATION",
):
    """
    Runs Group A + Group B + B8-B11 + Synthesis for one completed live case
    and persists results. Called immediately at return_found=True (early emit,
    emit_status=PENDING_FINALIZATION) with a partial merged_row whose
    future-dependent fields are empty strings — Group A/B/B8-B11/Synthesis
    consume only feature_window + snapshot_row fields, so output is correct
    and complete at that point. NOT re-called at 4h finalization; use
    append_live_outcome_for_case for the deferred outcome write instead.
    """
    run_utc = utc_now()
    feature_window = feature_window if feature_window is not None else pd.DataFrame()

    case_row = build_completed_live_case_row(pending, merged_row, feature_window)
    case_id = case_row["case_id"]
    episode_id = case_row["episode_id"]

    zone_events, field_events = collect_live_case_events(episode_id)

    results_df = _run_group_a(_single_row_frame(case_row), zone_events, field_events, run_utc)
    results_df, live_evolution_df, attacker_df, case_cache = _run_group_b(
        results_df, feature_window, run_utc
    )
    extra = _run_memory_and_timeline_stages(results_df, live_evolution_df, attacker_df, run_utc)

    final_row = results_df.iloc[0].to_dict()

    record = {
        "case_id": case_id,
        "episode_id": episode_id,
        "analysis_run_utc": run_utc,
        "resolved_at_timestamp_utc": event_timestamp,
        "emit_status": emit_status,
        "result_row": final_row,
        "live_evolution": live_evolution_df,
        "attacker_evolution": attacker_df,
        "interaction_core_valid_count": int(case_cache.case_count),
        **extra,
    }

    _live_rdm_state[case_id] = record
    _persist_record(record)

    # B12.5 auto-trigger — rebuild live dynamic visit timeline immediately
    # after the new zone is persisted. Runtime confirmed <2s (50 zones).
    # Failure must never block the main live pipeline.
    try:
        run_zone_visit_timeline_dynamic_live()
        add_dynamic_layers_to_timeline_live()
    except Exception:
        pass

    return record


def append_live_outcome_for_case(pending, merged_row, event_timestamp):
    """
    Appends a FINALIZED_OUTCOME row to live_rdm_state.csv carrying the
    4h-window-dependent outcome fields (reversal_type, failed_after_return,
    expansion_type, max_move_after_return, etc.) that were empty strings in
    the earlier PENDING_FINALIZATION record. Does NOT re-run Group A/B or
    B8-B11 — the structural prediction from PENDING_FINALIZATION is already
    the correct, complete record for those fields. Append-only; the
    PENDING_FINALIZATION record is never modified.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    case_id = _live_case_identifier(pending.episode_id)
    run_utc = utc_now()

    state_row = {field: "" for field in _STATE_FIELDNAMES}
    state_row["case_id"] = case_id
    state_row["episode_id"] = pending.episode_id
    state_row["analysis_run_utc"] = run_utc
    state_row["resolved_at_timestamp_utc"] = event_timestamp
    state_row["emit_status"] = "FINALIZED_OUTCOME"

    for field in _FINALIZED_OUTCOME_FIELDS:
        state_row[field] = merged_row.get(field, "")

    _ensure_csv(LIVE_RDM_STATE_FILE, _STATE_FIELDNAMES)
    with LIVE_RDM_STATE_FILE.open(mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=_STATE_FIELDNAMES, extrasaction="ignore")
        writer.writerow(state_row)


def _append_b12_validation_csv(record):
    """
    B12 (Live Validation Instrumentation) -- ADDITIVE, research-only.
    Appends one record to its own new file (LIVE_B12_VALIDATION_FILE).
    Does not read or write LIVE_RDM_STATE_FILE / LIVE_RDM_RESULTS_FILE /
    LIVE_RDM_EVOLUTION_FILE or any other existing tracked output.
    """
    fieldnames = list(record.keys())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _ensure_csv(LIVE_B12_VALIDATION_FILE, fieldnames)
    with LIVE_B12_VALIDATION_FILE.open(mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writerow(record)


def append_live_b12_validation_for_case(pending, event_timestamp):
    """
    B12 (Live Validation Instrumentation) -- ADDITIVE, research-only.

    Mechanical ground-truth observer for B11. Called once a zone's two 4h
    windows are complete (the same point append_live_outcome_for_case is
    called from), reusing the PENDING_FINALIZATION record already computed
    and persisted by compute_live_rdm_for_case (Group A/B/B8-B11/Synthesis
    are NOT re-run here -- this function only reads that record plus the new
    post_return_feature_window_rows buffer).

    If no PENDING_FINALIZATION record exists for this case (e.g.
    interaction_core_valid_flag never computed), or anything else prevents
    computation, writes a NOT_TESTED record rather than raising -- B12 must
    never affect existing finalization (lifecycle events, FINALIZED_OUTCOME
    state row) regardless of its own outcome.
    """
    from core.live_b12_validation import compute_b12_validation_for_case

    case_id = _live_case_identifier(pending.episode_id)
    cached = _live_rdm_state.get(case_id)

    if cached is None:
        record = {
            "analysis_run_utc": utc_now(),
            "research_only": True,
            "case_id": case_id,
            "episode_id": pending.episode_id,
            "zone_id": "",
            "b11_prediction_label": "",
            "interaction_core_lower_edge": "",
            "interaction_core_upper_edge": "",
            "interaction_core_valid_flag": "",
            "rigidity_birth": "",
            "capacity_birth": "",
            "fatigue_birth": "",
            "rigidity_at_return": "",
            "capacity_at_return": "",
            "fatigue_at_return": "",
            "observation_window_hours": 4.0,
            "post_return_rows_captured": 0,
            "segment_found": False,
            "segment_source": "",
            "segment_start_row": "",
            "segment_end_row": "",
            "visit_classification": "",
            "rigidity_v_n1": "",
            "capacity_v_n1": "",
            "fatigue_v_n1": "",
            "inside_count_n1": 0,
            "max_pen_n1": "",
            "b12_verdict": "NOT_TESTED",
            "not_tested_reason": "NO_PENDING_FINALIZATION_RECORD",
        }
        _append_b12_validation_csv(record)
        return record

    case_record = cached.get("result_row", {})
    prediction_df = cached.get("prediction")
    prediction_label = None
    if prediction_df is not None and not prediction_df.empty:
        prediction_label = prediction_df.iloc[0].get("structural_prediction")

    record = compute_b12_validation_for_case(pending, case_record, prediction_label)
    _append_b12_validation_csv(record)
    return record


def _append_b10_trajectory_csv(trajectory_df, emit_status="PENDING_FINALIZATION"):
    if trajectory_df is None or trajectory_df.empty:
        return
    rows = trajectory_df.to_dict("records")
    for row in rows:
        row["emit_status"] = emit_status
    fieldnames = list(rows[0].keys())
    _ensure_csv(LIVE_B10_TRAJECTORY_FILE, fieldnames)
    with LIVE_B10_TRAJECTORY_FILE.open(mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        for row in rows:
            writer.writerow(row)


def _append_b11_prediction_csv(prediction_df, emit_status="PENDING_FINALIZATION"):
    if prediction_df is None or prediction_df.empty:
        return
    rows = prediction_df.to_dict("records")
    for row in rows:
        row["emit_status"] = emit_status
    fieldnames = list(rows[0].keys())
    _ensure_csv(LIVE_B11_PREDICTION_FILE, fieldnames)
    with LIVE_B11_PREDICTION_FILE.open(mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        for row in rows:
            writer.writerow(row)


def _append_synthesis_csv(synthesis_df, emit_status="PENDING_FINALIZATION"):
    if synthesis_df is None or synthesis_df.empty:
        return
    rows = synthesis_df.to_dict("records")
    for row in rows:
        row["emit_status"] = emit_status
    fieldnames = list(rows[0].keys())
    _ensure_csv(LIVE_SYNTHESIS_FILE, fieldnames)
    with LIVE_SYNTHESIS_FILE.open(mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        for row in rows:
            writer.writerow(row)


def _persist_record(record):
    emit_status = record.get("emit_status", "PENDING_FINALIZATION")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _append_results_csv(record["result_row"])
    _append_evolution_csv(record["case_id"], record["episode_id"], record["live_evolution"])
    _append_state_csv(record)
    _append_b10_trajectory_csv(record.get("trajectory", pd.DataFrame()), emit_status)
    _append_b11_prediction_csv(record.get("prediction", pd.DataFrame()), emit_status)
    _append_synthesis_csv(record.get("synthesis", pd.DataFrame()), emit_status)


def _ensure_csv(path, fieldnames):
    if not path.exists():
        with path.open(mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()


def _append_results_csv(result_row):
    fieldnames = list(result_row.keys())
    _ensure_csv(LIVE_RDM_RESULTS_FILE, fieldnames)
    with LIVE_RDM_RESULTS_FILE.open(mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writerow(result_row)


def _append_evolution_csv(case_id, episode_id, live_evolution_df):
    if live_evolution_df is None or live_evolution_df.empty:
        return

    rows = live_evolution_df.to_dict("records")
    fieldnames = list(rows[0].keys())
    _ensure_csv(LIVE_RDM_EVOLUTION_FILE, fieldnames)
    with LIVE_RDM_EVOLUTION_FILE.open(mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        for row in rows:
            writer.writerow(row)


_STATE_FIELDNAMES = [
    "case_id",
    "episode_id",
    "analysis_run_utc",
    "resolved_at_timestamp_utc",
    "emit_status",
    "mechanical_family",
    "mechanical_subtype",
    "rdm_zone_status",
    "rdm_health_score",
    "rdm_risk_level",
    "rdm_watch_action",
    "rdm_short_reason",
    "rigidity_birth",
    "rigidity_live",
    "sigma_barre_zone",
    "sigma_state",
    "capacity_birth",
    "capacity_live",
    "fatigue_index",
    "recovery_ratio",
    "health_score",
    # Geometry fields — Active Core and Density Band computed at return_found=True
    # by build_interaction_core_geometry / build_interaction_density_map inside
    # _run_group_b. Empty for zones that have not yet returned.
    "interaction_core_upper_edge",
    "interaction_core_lower_edge",
    "interaction_core_mid_price",
    "interaction_core_width",
    "interaction_core_source",
    "interaction_core_valid_flag",
    "interaction_density_upper_band",
    "interaction_density_lower_band",
    "interaction_density_weighted_center",
    "interaction_density_width",
    "interaction_density_score",
    # Outcome fields — empty in PENDING_FINALIZATION, populated in FINALIZED_OUTCOME
    "failed_after_return",
    "reversal_type",
    "reversal_strength",
    "expansion_type",
    "expansion_strength",
    "max_move_after_return",
    "direction_after_return",
    "expansion_after_return",
]

# Fields from the 4h-window analysis that are absent in PENDING_FINALIZATION
# and populated in FINALIZED_OUTCOME by append_live_outcome_for_case.
_FINALIZED_OUTCOME_FIELDS = (
    "failed_after_return",
    "reversal_type",
    "reversal_strength",
    "expansion_type",
    "expansion_strength",
    "max_move_after_return",
    "direction_after_return",
    "expansion_after_return",
    "revisit_expansion_delay_minutes",
)


def _append_state_csv(record):
    final_row = record["result_row"]
    state_row = {
        "case_id": record["case_id"],
        "episode_id": record["episode_id"],
        "analysis_run_utc": record["analysis_run_utc"],
        "resolved_at_timestamp_utc": record["resolved_at_timestamp_utc"],
        "emit_status": record.get("emit_status", "PENDING_FINALIZATION"),
    }
    for field in _STATE_FIELDNAMES:
        if field not in state_row:
            state_row[field] = final_row.get(field, "")

    _ensure_csv(LIVE_RDM_STATE_FILE, _STATE_FIELDNAMES)
    with LIVE_RDM_STATE_FILE.open(mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=_STATE_FIELDNAMES, extrasaction="ignore")
        writer.writerow(state_row)

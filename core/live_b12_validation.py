"""
B12 -- LIVE VALIDATION INSTRUMENTATION (research/observation only).

Mechanical ground-truth observer for B11 (build_zone_structural_prediction)
predictions. Determines whether the FIRST post-return engagement segment
("visit N+1") -- detected and classified using the SAME B8 mechanisms
(segment_force_lull_attempts / _compute_touch_spans / _classify_visit, same
constants and thresholds) -- agrees with B11's HOLD/FAIL prediction for that
zone.

ADDITIVE ONLY. Every formula/threshold/classification call below is a
verbatim call into research.zone_mechanics_calculator -- nothing is
reimplemented or modified. No existing field, formula, lifecycle, replay,
or FINALIZED_OUTCOME logic is touched. Output is written to its own new file
(outputs/live_b12_validation.csv) and every record carries
research_only=True.

Design decisions implemented here (recorded, not re-derived):
  D1  : visit N+1 segmentation = segment_force_lull_attempts (primary,
        ATTACKER_LULL_THRESHOLD_RATIO=0.50, ATTACKER_FORCE_WINDOW=5,
        ATTACKER_LULL_DURATION=3) with _compute_touch_spans (lull_gap=3)
        fallback -- identical algorithm/parameters to B8.
  D1a : the inside_zone_flag / zone_touch_flag fed to that segmentation are
        recomputed (in build_post_return_evolution, below) against the
        Active Core geometry (interaction_core_lower_edge /
        interaction_core_upper_edge), NOT Formation bounds. This is NEW
        computation; the existing Formation-keyed flags in live_evolution_df
        are produced by a separate call (live_evolution_record against
        real_zone_upper_edge/real_zone_lower_edge) and are not touched.
  D2  : observation window = 4 hours after the return row (same FOUR_HOURS
        bound already used for return_window_rows / FINALIZED_OUTCOME).
        PROVISIONAL -- not empirically derived; revisit after extended data
        collection (per directive).
  D3  : verdict taxonomy = CONFIRMED / REFUTED / NOT_TESTED (see
        compute_b12_verdict). NOT_TESTED is never a success.
  D4  : each zone is judged independently against its own Active Core
        geometry and its own post-return buffer -- no cross-zone state.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import pandas as pd

from research.zone_mechanics_calculator import (
    _classify_visit,
    _compute_touch_spans,
    apply_live_rdm_guard,
    filter_attacker_interaction_rows,
    live_evolution_record,
    round_float,
    segment_force_lull_attempts,
    to_float,
    truthy,
    utc_now,
)

# Observation window for the B12 judge -- identical bound to
# return_window_rows / post_return_feature_window_rows (FOUR_HOURS).
# PROVISIONAL choice (D2): not empirically derived from time_to_return_minutes
# or visit_duration_rows distributions; documented for future revisit.
OBSERVATION_WINDOW_HOURS = 4.0


def _zone_series_with_active_core_geometry(case_record: Dict[str, Any]) -> pd.Series:
    """
    Builds the `zone` Series passed to live_evolution_record() for the
    POST-RETURN (visit N+1 judge) stream.

    Starts from a copy of the case's persisted result row (case_record),
    so all *_birth fields (rigidity_birth, capacity_birth, fatigue_birth,
    sigma_birth, health_birth, recovery_birth) -- the values _classify_visit
    compares "visit N+1" against -- are passed through UNCHANGED, exactly as
    B8 uses them for visits 1..N.

    Overrides ONLY real_zone_upper_edge / real_zone_lower_edge /
    real_zone_width with interaction_core_upper_edge /
    interaction_core_lower_edge / their difference (D1a) -- these are the
    only fields live_evolution_record reads to compute inside_zone_flag /
    zone_touch_flag / distance_to_zone / fleche_live / penetration. This is
    a NEW Series built for this call only; the original case_record /
    Formation-keyed live_evolution_df are not mutated.

    NOTE on zone_strength_decay / "failed_after_return": case_record is the
    PENDING_FINALIZATION snapshot (the same one cached in _live_rdm_state),
    in which "failed_after_return" -- one of the two-phase outcome fields
    only populated later in FINALIZED_OUTCOME -- is always empty/falsy. The
    "+12" term in calculate_zone_strength_decay that depends on
    failed_after_return can therefore NEVER fire for any B12 case, by
    construction. This is an architectural neutrality property of the judge,
    not a per-case observation: any nonzero zone_strength_decay seen here
    must come from zone_rejected/field_exhausted/field_weakening events that
    occurred before the return, never from the failed_after_return term.
    """
    zone = pd.Series(dict(case_record))

    core_upper = to_float(case_record.get("interaction_core_upper_edge"))
    core_lower = to_float(case_record.get("interaction_core_lower_edge"))

    zone["real_zone_upper_edge"] = core_upper
    zone["real_zone_lower_edge"] = core_lower
    zone["real_zone_width"] = (
        abs(core_upper - core_lower) if core_upper is not None and core_lower is not None else None
    )

    return zone


def build_post_return_evolution(
    post_return_window: pd.DataFrame,
    case_record: Dict[str, Any],
    run_utc: str,
) -> pd.DataFrame:
    """
    B12 / D1a -- Active-Core-keyed live evolution stream for the post-return
    observation window.

    For every row in post_return_window (FEATURE_WINDOW_FIELDS, from
    build_zone_post_return_feature_window), calls live_evolution_record()
    UNCHANGED -- the same function build_live_rdm_evolution's
    live_evolution_rows_for_zone uses for visits 1..N -- but with `zone`
    geometry overridden to the Active Core bounds (see
    _zone_series_with_active_core_geometry). breach_memory / guard_state are
    fresh, local, per-call dicts: no state is shared with the Formation-keyed
    live_evolution_df or across zones (D4).

    KNOWN, DOCUMENTED, UNCHANGED PROPERTIES of reusing live_evolution_record
    as-is for post-return rows (no compensation applied -- per directive,
    these are measurement properties, not bugs to fix):

    - live_row_progress(zone, row_number) clamps to 1.0 once
      row_number > end_row_id, which is true for every post-return row.
      The temporal decay term in rigidity_live/capacity_live therefore
      saturates at row_progress=1.0 immediately for the whole post-return
      window. tools/validate_live_b12.py measures the resulting
      rigidity_live/capacity_live at the FIRST post-return row against
      0.5 * birth (Amendment 1 bias-check) -- this module does not adjust
      for it.
    - return_to_zone_flag = touch AND row_number >= return_row. Since
      row_number >= return_row holds for every post-return row,
      return_to_zone_flag reduces to `touch` here. In _classify_visit this
      means `reclaim` will be True whenever any touch occurred in the visit
      N+1 span, which can label a non-BREAKDOWN visit RECLAIM rather than
      REFLECTION/ABSORPTION/UNKNOWN. This does not affect the B12 verdict
      (D3 depends only on BREAKDOWN vs. not-BREAKDOWN, and BREAKDOWN is
      _classify_visit's priority-1 check) -- documented, not patched.
    """
    if post_return_window is None or post_return_window.empty:
        return pd.DataFrame()

    zone = _zone_series_with_active_core_geometry(case_record)
    if zone.get("real_zone_upper_edge") is None or zone.get("real_zone_lower_edge") is None:
        return pd.DataFrame()

    breach_memory: Dict[str, bool] = {}
    guard_state: Dict[str, int] = {}

    rows = []
    for _, source_row in post_return_window.sort_values("row_id").iterrows():
        record = live_evolution_record(
            zone=zone,
            row_index=source_row.get("row_id"),
            timestamp=source_row.get("market_timestamp"),
            price=to_float(source_row.get("close")),
            source_row=source_row,
            run_utc=run_utc,
            breach_memory=breach_memory,
        )
        rows.append(apply_live_rdm_guard(record, guard_state))

    return pd.DataFrame(rows)


def find_visit_n_plus_1_segment(
    post_return_evolution: pd.DataFrame,
) -> Tuple[Optional[Tuple[int, int]], str]:
    """
    B12 / D1 -- locate the FIRST post-return engagement segment ("visit N+1")
    using B8's segmentation, called as-is.

    Primary: segment_force_lull_attempts(filter_attacker_interaction_rows(df))
    -- same ATTACKER_LULL_THRESHOLD_RATIO/ATTACKER_FORCE_WINDOW/
    ATTACKER_LULL_DURATION constants as B8 (V1.6-B3.5-B), applied to rows
    where the Active-Core-keyed zone_touch_flag/inside_zone_flag (D1a) is
    True.

    Fallback: _compute_touch_spans(post_return_evolution, lull_gap=3) -- same
    function/threshold B8 falls back to, applied directly to the
    Active-Core-keyed evolution frame (it already reads zone_touch_flag /
    inside_zone_flag / evolution_state / row_index).

    Returns ((start_row, end_row), span_source) for the first segment, or
    (None, "") if neither path finds a qualifying segment (-> NOT_TESTED /
    NO_QUALIFYING_SEGMENT).
    """
    if post_return_evolution is None or post_return_evolution.empty:
        return None, ""

    interaction_rows = filter_attacker_interaction_rows(post_return_evolution)
    if not interaction_rows.empty and "delta" in interaction_rows.columns:
        attempts = segment_force_lull_attempts(interaction_rows)
        if attempts:
            first = attempts[0]
            start_ridx = first.get("start_ridx")
            end_ridx = first.get("end_ridx")
            if start_ridx is not None and end_ridx is not None and not (
                isinstance(start_ridx, float) and pd.isna(start_ridx)
            ):
                return (int(start_ridx), int(end_ridx)), "force_lull_segments"

    touch_spans = _compute_touch_spans(post_return_evolution, lull_gap=3)
    if touch_spans:
        span_start, span_end = touch_spans[0]
        return (int(span_start), int(span_end)), "touch_flag_derived"

    return None, ""


def classify_visit_n_plus_1(
    post_return_evolution: pd.DataFrame,
    segment: Tuple[int, int],
    case_record: Dict[str, Any],
) -> Dict[str, Any]:
    """
    B12 / D3 -- classify the visit N+1 segment using B8's _classify_visit,
    called as-is with the same priority order/thresholds
    (BREAKDOWN > GROWTH > DAMAGE > RECLAIM > REFLECTION > ABSORPTION >
    UNKNOWN; BREAKDOWN iff rigidity_v < 0.5*rigidity_birth OR
    capacity_v < 0.5*capacity_birth).

    Structural metrics at visit (rig_v/cap_v/fat_v) = last row of the
    segment, mirroring B8's "structural metrics taken from the last
    live-evolution row within each span".

    "Previous visit" state (prev_rig/prev_cap/prev_fat) = visit N's END
    state, i.e. the *_at_return fields already persisted on case_record
    (rigidity_at_return / capacity_at_return / fatigue_at_return) --
    read-only, not recomputed.

    Birth state (rig_birth/cap_birth/fat_birth) = case_record's *_birth
    fields, read-only, unchanged from B8's own birth values.
    """
    span_start, span_end = segment
    span_rows = post_return_evolution[
        (pd.to_numeric(post_return_evolution["row_index"], errors="coerce") >= span_start)
        & (pd.to_numeric(post_return_evolution["row_index"], errors="coerce") <= span_end)
    ]

    if span_rows.empty:
        return {
            "visit_classification": "",
            "rigidity_v_n1": pd.NA,
            "capacity_v_n1": pd.NA,
            "fatigue_v_n1": pd.NA,
            "inside_count_n1": 0,
            "max_pen_n1": pd.NA,
        }

    last_row = span_rows.iloc[-1]

    rig_v = to_float(last_row.get("rigidity_live")) or 0.0
    cap_v = to_float(last_row.get("capacity_live")) or 0.0
    fat_v = to_float(last_row.get("fatigue_live")) or 0.0

    rig_birth = to_float(case_record.get("rigidity_birth")) or 0.0
    cap_birth = to_float(case_record.get("capacity_birth")) or 0.0
    fat_birth = to_float(case_record.get("fatigue_birth")) or 0.0

    prev_rig = to_float(case_record.get("rigidity_at_return")) or 0.0
    prev_cap = to_float(case_record.get("capacity_at_return")) or 0.0
    prev_fat = to_float(case_record.get("fatigue_at_return")) or 0.0

    inside_series = span_rows["inside_zone_flag"].apply(truthy)
    inside_count = int(inside_series.sum())

    width = to_float(last_row.get("real_zone_width")) or 0.0
    fleche_series = pd.to_numeric(span_rows.get("fleche_live"), errors="coerce").fillna(0.0)
    max_pen = float((fleche_series * width).max()) if not fleche_series.empty else 0.0

    reclaim = bool(span_rows["return_to_zone_flag"].apply(truthy).any())

    label = _classify_visit(
        rig_v, cap_v, fat_v,
        rig_birth, cap_birth, fat_birth,
        prev_rig, prev_cap, prev_fat,
        inside_count, max_pen, reclaim,
    )

    return {
        "visit_classification": label,
        "rigidity_v_n1": round_float(rig_v),
        "capacity_v_n1": round_float(cap_v),
        "fatigue_v_n1": round_float(fat_v),
        "inside_count_n1": inside_count,
        "max_pen_n1": round_float(max_pen),
    }


def compute_b12_verdict(
    b11_label: Optional[str],
    segment: Optional[Tuple[int, int]],
    visit_classification: Optional[str],
) -> Tuple[str, str]:
    """
    B12 / D3 -- CONFIRMED / REFUTED / NOT_TESTED. NOT_TESTED is never counted
    as success (enforced by callers/offline aggregation, not here).
    """
    if b11_label not in ("HOLD", "FAIL"):
        return "NOT_TESTED", "B11_UNCERTAIN_OR_NO_PREDICTION"

    if segment is None:
        return "NOT_TESTED", "NO_QUALIFYING_SEGMENT"

    is_breakdown = visit_classification == "BREAKDOWN"

    if (b11_label == "HOLD" and not is_breakdown) or (b11_label == "FAIL" and is_breakdown):
        return "CONFIRMED", ""

    return "REFUTED", ""


def compute_b12_validation_for_case(pending, case_record: Dict[str, Any], prediction_label: Optional[str]) -> Dict[str, Any]:
    """
    B12 top-level orchestrator (D1-D4). Returns one research_only=True record
    for outputs/live_b12_validation.csv. Does not mutate pending, case_record,
    or any existing live_rdm state.
    """
    from core.live_return_detection import build_zone_post_return_feature_window

    run_utc = utc_now()

    record: Dict[str, Any] = {
        "analysis_run_utc": run_utc,
        "research_only": True,
        "case_id": case_record.get("case_id"),
        "episode_id": case_record.get("episode_id"),
        "zone_id": case_record.get("zone_id"),
        "b11_prediction_label": prediction_label or "",
        "interaction_core_lower_edge": case_record.get("interaction_core_lower_edge"),
        "interaction_core_upper_edge": case_record.get("interaction_core_upper_edge"),
        "interaction_core_valid_flag": case_record.get("interaction_core_valid_flag"),
        "rigidity_birth": case_record.get("rigidity_birth"),
        "capacity_birth": case_record.get("capacity_birth"),
        "fatigue_birth": case_record.get("fatigue_birth"),
        "rigidity_at_return": case_record.get("rigidity_at_return"),
        "capacity_at_return": case_record.get("capacity_at_return"),
        "fatigue_at_return": case_record.get("fatigue_at_return"),
        "observation_window_hours": OBSERVATION_WINDOW_HOURS,
        "post_return_rows_captured": 0,
        "segment_found": False,
        "segment_source": "",
        "segment_start_row": pd.NA,
        "segment_end_row": pd.NA,
        "visit_classification": "",
        "rigidity_v_n1": pd.NA,
        "capacity_v_n1": pd.NA,
        "fatigue_v_n1": pd.NA,
        "inside_count_n1": 0,
        "max_pen_n1": pd.NA,
        "b12_verdict": "NOT_TESTED",
        "not_tested_reason": "",
    }

    if prediction_label not in ("HOLD", "FAIL"):
        record["b12_verdict"] = "NOT_TESTED"
        record["not_tested_reason"] = "B11_UNCERTAIN_OR_NO_PREDICTION"
        return record

    if not truthy(case_record.get("interaction_core_valid_flag")):
        record["b12_verdict"] = "NOT_TESTED"
        record["not_tested_reason"] = "INTERACTION_CORE_INVALID"
        return record

    post_return_window = build_zone_post_return_feature_window(pending)
    record["post_return_rows_captured"] = int(len(post_return_window))

    if post_return_window.empty:
        record["b12_verdict"] = "NOT_TESTED"
        record["not_tested_reason"] = "NO_POST_RETURN_DATA"
        return record

    evolution = build_post_return_evolution(post_return_window, case_record, run_utc)
    if evolution.empty:
        record["b12_verdict"] = "NOT_TESTED"
        record["not_tested_reason"] = "NO_POST_RETURN_DATA"
        return record

    segment, segment_source = find_visit_n_plus_1_segment(evolution)
    record["segment_found"] = segment is not None
    record["segment_source"] = segment_source

    visit_classification = None
    if segment is not None:
        record["segment_start_row"], record["segment_end_row"] = segment
        visit = classify_visit_n_plus_1(evolution, segment, case_record)
        record.update(visit)
        visit_classification = visit["visit_classification"]

    verdict, reason = compute_b12_verdict(prediction_label, segment, visit_classification)
    record["b12_verdict"] = verdict
    record["not_tested_reason"] = reason

    return record

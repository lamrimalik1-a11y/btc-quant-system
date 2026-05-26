"""Research-only RDM market mechanics calculator.

This script reads existing replay/research outputs and produces zone mechanics
research files. It does not modify live logic, Dashboard V2 scoring, execution,
or any engine state.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "outputs"
RESEARCH_DIR = ROOT_DIR / "research"

EPISODES_FILE = OUTPUT_DIR / "historical_replay_dashboard_v2_episodes.csv"
RESEARCH_LOG_FILE = RESEARCH_DIR / "phase1b_episode_research_log.csv"
ZONE_LIFECYCLE_FILE = RESEARCH_DIR / "zone_lifecycle_events.jsonl"
FIELD_LIFECYCLE_FILE = RESEARCH_DIR / "field_lifecycle_events.jsonl"
CASE_LABELS_FILE = RESEARCH_DIR / "zone_mechanics_case_labels.csv"

RESULTS_FILE = RESEARCH_DIR / "zone_mechanics_cycle3_results.csv"
SUMMARY_FILE = RESEARCH_DIR / "zone_mechanics_cycle3_summary.csv"
NOTES_FILE = RESEARCH_DIR / "zone_mechanics_cycle3_notes.md"
TIMELINE_FILE = RESEARCH_DIR / "zone_mechanics_timeline.csv"
LIFECYCLE_FILE = RESEARCH_DIR / "zone_mechanics_lifecycle.csv"
TIMELINE_NOTES_FILE = RESEARCH_DIR / "zone_mechanics_timeline_notes.md"
CAPACITY_FILE = RESEARCH_DIR / "zone_mechanics_capacity.csv"
CAPACITY_NOTES_FILE = RESEARCH_DIR / "zone_mechanics_capacity_notes.md"
SIGMA_FILE = RESEARCH_DIR / "zone_mechanics_sigma.csv"
SIGMA_NOTES_FILE = RESEARCH_DIR / "zone_mechanics_sigma_notes.md"
SIGMA_EVOLUTION_FILE = RESEARCH_DIR / "zone_mechanics_sigma_evolution.csv"
SIGMA_EVOLUTION_NOTES_FILE = RESEARCH_DIR / "zone_mechanics_sigma_evolution_notes.md"

NOTABLE_CASES = [
    "CASE_00021",
    "CASE_00035",
    "CASE_00041",
    "CASE_00036",
    "CASE_00044",
]


def main() -> None:
    run_utc = utc_now()

    episodes = read_csv(EPISODES_FILE)
    research_log = read_csv(RESEARCH_LOG_FILE)
    case_labels = read_optional_csv(CASE_LABELS_FILE)
    zone_events = read_jsonl(ZONE_LIFECYCLE_FILE)
    field_events = read_jsonl(FIELD_LIFECYCLE_FILE)

    dataset = build_dataset(episodes, research_log, case_labels)
    results = []

    for _, row in dataset.iterrows():
        results.append(
            calculate_zone_mechanics_row(
                row=row,
                zone_events=zone_events,
                field_events=field_events,
                run_utc=run_utc,
            )
        )

    results_df = pd.DataFrame(results)
    capacity_df = build_mechanics_capacity(results_df, run_utc)
    results_df = merge_capacity_into_results(results_df, capacity_df)
    sigma_df = build_mechanics_sigma(results_df, run_utc)
    results_df = merge_sigma_into_results(results_df, sigma_df)
    sigma_evolution_df = build_sigma_evolution(results_df, run_utc)
    results_df = merge_sigma_evolution_into_results(results_df, sigma_evolution_df)
    timeline_df = build_mechanics_timeline(results_df, run_utc)
    lifecycle_df = build_mechanics_lifecycle(timeline_df, run_utc)
    summary_df = build_summary(results_df, run_utc)
    notes_text = build_notes(results_df, summary_df, run_utc)
    timeline_notes_text = build_timeline_notes(timeline_df, lifecycle_df, run_utc)
    capacity_notes_text = build_capacity_notes(capacity_df, run_utc)
    sigma_notes_text = build_sigma_notes(sigma_df, run_utc)
    sigma_evolution_notes_text = build_sigma_evolution_notes(sigma_evolution_df, run_utc)

    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(RESULTS_FILE, index=False)
    capacity_df.to_csv(CAPACITY_FILE, index=False)
    sigma_df.to_csv(SIGMA_FILE, index=False)
    sigma_evolution_df.to_csv(SIGMA_EVOLUTION_FILE, index=False)
    timeline_df.to_csv(TIMELINE_FILE, index=False)
    lifecycle_df.to_csv(LIFECYCLE_FILE, index=False)
    summary_df.to_csv(SUMMARY_FILE, index=False)
    NOTES_FILE.write_text(notes_text, encoding="utf-8")
    TIMELINE_NOTES_FILE.write_text(timeline_notes_text, encoding="utf-8")
    CAPACITY_NOTES_FILE.write_text(capacity_notes_text, encoding="utf-8")
    SIGMA_NOTES_FILE.write_text(sigma_notes_text, encoding="utf-8")
    SIGMA_EVOLUTION_NOTES_FILE.write_text(sigma_evolution_notes_text, encoding="utf-8")

    print("Zone mechanics calculator complete.")
    print(f"Results: {relative_path(RESULTS_FILE)}")
    print(f"Summary: {relative_path(SUMMARY_FILE)}")
    print(f"Notes: {relative_path(NOTES_FILE)}")
    print(f"Timeline: {relative_path(TIMELINE_FILE)}")
    print(f"Lifecycle: {relative_path(LIFECYCLE_FILE)}")
    print(f"Timeline notes: {relative_path(TIMELINE_NOTES_FILE)}")
    print(f"Capacity: {relative_path(CAPACITY_FILE)}")
    print(f"Capacity notes: {relative_path(CAPACITY_NOTES_FILE)}")
    print(f"Sigma: {relative_path(SIGMA_FILE)}")
    print(f"Sigma notes: {relative_path(SIGMA_NOTES_FILE)}")
    print(f"Sigma evolution: {relative_path(SIGMA_EVOLUTION_FILE)}")
    print(f"Sigma evolution notes: {relative_path(SIGMA_EVOLUTION_NOTES_FILE)}")
    print(f"Rows generated: {len(results_df)}")
    print(f"Timeline rows generated: {len(timeline_df)}")
    print("Mechanical state counts:")
    for state, count in results_df["zone_mechanical_state"].value_counts().items():
        print(f"- {state}: {count}")
    print("Notable cases:")
    for case_id in NOTABLE_CASES:
        matched = results_df[results_df["case_id"] == case_id]
        if matched.empty:
            print(f"- {case_id}: NOT_FOUND")
        else:
            state = matched.iloc[0]["zone_mechanical_state"]
            label = matched.iloc[0]["case_label"]
            print(f"- {case_id}: {state} / {label}")


def build_dataset(episodes: pd.DataFrame, research_log: pd.DataFrame, case_labels: pd.DataFrame) -> pd.DataFrame:
    base = research_log.copy()

    if base.empty:
        return base

    base["episode_id"] = base["episode_id"].astype(str)

    episode_columns = [
        "episode_id",
        "peak_state",
        "peak_layer_count",
        "peak_max_severity",
        "peak_primary_context",
        "peak_conditions",
        "peak_active_layers",
        "peak_observation_confidence",
    ]
    available_episode_columns = [
        column for column in episode_columns if column in episodes.columns
    ]

    if available_episode_columns:
        episode_context = episodes[available_episode_columns].copy()
        episode_context["episode_id"] = episode_context["episode_id"].astype(str)
        base = base.merge(
            episode_context,
            on="episode_id",
            how="left",
            suffixes=("", "_episode"),
        )

    if not case_labels.empty and "case_id" in case_labels.columns:
        labels = case_labels.copy()
        base = base.merge(
            labels,
            on="case_id",
            how="left",
            suffixes=("", "_label"),
        )

    return base


def calculate_zone_mechanics_row(
    row: pd.Series,
    zone_events: pd.DataFrame,
    field_events: pd.DataFrame,
    run_utc: str,
) -> Dict[str, Any]:
    case_id = value(row, "case_id")
    episode_id = value(row, "episode_id")
    zone_case_events = events_for_case(zone_events, case_id)
    field_case_events = events_for_case(field_events, case_id)

    penetration_depth = zone_penetration_depth(row)
    zone_height = zone_range_height(row)
    fleche_ratio = safe_divide(penetration_depth, zone_height)
    fleche_state = classify_fleche_state(fleche_ratio)

    penetration_direction = direction_from_signed(
        subtract_number(row.get("return_price"), row.get("preparation_mid_price"))
    )
    delta_direction = direction_from_signed(row.get("peak_delta_zscore"))
    moment_stress_type = classify_moment_stress(delta_direction, penetration_direction)
    signed_moment_proxy = signed_moment(row, penetration_depth, delta_direction)
    moment_absorption_flag = moment_stress_type == "ABSORPTION"

    mechanical_load_score = calculate_mechanical_load_score(
        fleche_ratio=fleche_ratio,
        delta_zscore=row.get("peak_delta_zscore"),
        layer_count=row.get("peak_layer_count"),
        zone_revisit_count=row.get("zone_revisit_count"),
        failed_after_return=row.get("failed_after_return"),
        confidence_collapse=is_confidence_collapse(row),
    )
    fatigue_index = calculate_fatigue_index(row, zone_case_events, field_case_events)
    fatigue_state = classify_fatigue_state(fatigue_index)

    zone_rigidity = calculate_zone_rigidity(row, zone_case_events)
    zone_strength_decay = calculate_zone_strength_decay(row, zone_case_events, field_case_events)
    recovery_ratio = calculate_recovery_ratio(row, zone_case_events, field_case_events)
    zone_recovery_state = classify_recovery_state(recovery_ratio, zone_case_events, field_case_events)

    moment_utilization_ratio = safe_divide(mechanical_load_score, max(zone_rigidity, 1))
    els_elu_state = classify_els_elu_state(moment_utilization_ratio, fleche_state)
    mechanics = classify_zone_mechanics(
        row=row,
        fleche_state=fleche_state,
        fatigue_state=fatigue_state,
        zone_case_events=zone_case_events,
        field_case_events=field_case_events,
        recovery_ratio=recovery_ratio,
        zone_strength_decay=zone_strength_decay,
    )
    mechanical_state = mechanics["zone_mechanical_state"]

    return {
        "analysis_run_utc": run_utc,
        "case_id": case_id,
        "episode_id": episode_id,
        "source_status": value(row, "source_status", "FOUND"),
        "case_label": value(row, "case_label", ""),
        "reference_example_flag": bool(value(row, "case_label", "")),
        "episode_start_time_utc": value(row, "episode_start_time_utc"),
        "duration_seconds": value(row, "duration_seconds"),
        "score_bucket": value(row, "score_bucket"),
        "peak_layer_count": value(row, "peak_layer_count"),
        "peak_max_severity": value(row, "peak_max_severity"),
        "peak_primary_context": value(row, "peak_primary_context"),
        "return_to_preparation": value(row, "return_to_preparation"),
        "failed_after_return": value(row, "failed_after_return"),
        "pre_velocity_abs_mean": value(row, "pre_velocity_abs_mean"),
        "pre_delta_abs_mean": value(row, "pre_delta_abs_mean"),
        "pre_quiet_score": value(row, "pre_quiet_score"),
        "pre_range_ratio": value(row, "pre_range_ratio"),
        "preparation_strength": value(row, "preparation_strength"),
        "zone_revisit_count": value(row, "zone_revisit_count"),
        "expansion_type": value(row, "expansion_type"),
        "expansion_strength": value(row, "expansion_strength"),
        "reversal_type": value(row, "reversal_type"),
        "reversal_strength": value(row, "reversal_strength"),
        "zone_penetration_depth": round_float(penetration_depth),
        "zone_fleche_ratio": round_float(fleche_ratio),
        "zone_fleche_state": fleche_state,
        "signed_moment_proxy": round_float(signed_moment_proxy),
        "moment_stress_type": moment_stress_type,
        "moment_absorption_flag": moment_absorption_flag,
        "mechanical_load_score": round_float(mechanical_load_score),
        "fatigue_index": round_float(fatigue_index),
        "fatigue_state": fatigue_state,
        "zone_rigidity": round_float(zone_rigidity),
        "zone_strength_decay": round_float(zone_strength_decay),
        "recovery_ratio": round_float(recovery_ratio),
        "zone_recovery_state": zone_recovery_state,
        "moment_utilization_ratio": round_float(moment_utilization_ratio),
        "els_elu_state": els_elu_state,
        "mechanical_family": mechanics["mechanical_family"],
        "mechanical_subtype": mechanics["mechanical_subtype"],
        "zone_mechanical_state": mechanical_state,
        "zone_lifecycle_states": "|".join(event_states(zone_case_events)),
        "field_lifecycle_states": "|".join(event_states(field_case_events)),
        "zone_event_count": len(zone_case_events),
        "field_event_count": len(field_case_events),
        "research_only": True,
    }


def zone_penetration_depth(row: pd.Series) -> float:
    low = to_float(row.get("preparation_low_price"))
    high = to_float(row.get("preparation_high_price"))
    mid = to_float(row.get("preparation_mid_price"))
    return_price = to_float(row.get("return_price"))
    max_move_after_return = abs_number(row.get("max_move_after_return"))

    if return_price is not None and low is not None and high is not None:
        if low <= return_price <= high:
            return min(abs(return_price - low), abs(high - return_price))
        if return_price < low:
            return low - return_price
        return return_price - high

    if return_price is not None and mid is not None:
        return abs(return_price - mid)

    return max_move_after_return or 0.0


def zone_range_height(row: pd.Series) -> float:
    low = to_float(row.get("preparation_low_price"))
    high = to_float(row.get("preparation_high_price"))
    if low is not None and high is not None and high != low:
        return abs(high - low)

    pre_range = abs_number(row.get("pre_range"))
    if pre_range:
        return pre_range

    return 1.0


def classify_fleche_state(fleche_ratio: float) -> str:
    if fleche_ratio <= 0.25:
        return "LOW"
    if fleche_ratio <= 0.60:
        return "MEDIUM"
    if fleche_ratio <= 1.00:
        return "HIGH"
    return "RUPTURE"


def classify_moment_stress(delta_direction: str, penetration_direction: str) -> str:
    if delta_direction == "UNKNOWN" or penetration_direction == "UNKNOWN":
        return "UNKNOWN"
    if delta_direction == penetration_direction:
        return "STRESS"
    return "ABSORPTION"


def signed_moment(row: pd.Series, penetration_depth: float, delta_direction: str) -> float:
    delta = to_float(row.get("peak_delta_zscore")) or 0.0
    load = abs(delta) * max(penetration_depth, 0.0)
    if delta_direction == "DOWN":
        return -load
    return load


def calculate_mechanical_load_score(
    fleche_ratio: float,
    delta_zscore: Any,
    layer_count: Any,
    zone_revisit_count: Any,
    failed_after_return: Any,
    confidence_collapse: bool,
) -> float:
    score = 0.0
    score += min(max(fleche_ratio, 0.0), 2.0) * 25
    score += min(abs_number(delta_zscore) or 0.0, 5.0) * 10
    score += min(to_float(layer_count) or 0.0, 8.0) * 4
    score += min(to_float(zone_revisit_count) or 0.0, 10.0) * 3
    if truthy(failed_after_return):
        score += 20
    if confidence_collapse:
        score += 10
    return min(score, 100.0)


def calculate_fatigue_index(row: pd.Series, zone_events: pd.DataFrame, field_events: pd.DataFrame) -> float:
    revisit_count = to_float(row.get("zone_revisit_count")) or 0.0
    zone_rejections = count_state(zone_events, "zone_rejected")
    field_exhaustions = count_state(field_events, "field_exhausted")
    field_weakening = count_state(field_events, "field_weakening")
    reaction_delay = to_float(row.get("revisit_expansion_delay_minutes")) or 0.0
    fatigue = revisit_count * 8 + zone_rejections * 25 + field_exhaustions * 20 + field_weakening * 15
    fatigue += min(reaction_delay, 60) * 0.5
    return min(fatigue, 100.0)


def classify_fatigue_state(fatigue_index: float) -> str:
    if fatigue_index < 25:
        return "LOW_FATIGUE"
    if fatigue_index < 50:
        return "MEDIUM_FATIGUE"
    if fatigue_index < 75:
        return "HIGH_FATIGUE"
    return "CRITICAL_FATIGUE"


def calculate_zone_rigidity(row: pd.Series, zone_events: pd.DataFrame) -> float:
    strength = str(row.get("preparation_strength") or "").upper()
    base = {
        "LOW": 35,
        "MEDIUM": 50,
        "HIGH": 70,
        "EXTREME": 85,
    }.get(strength, 40)
    if count_state(zone_events, "zone_reclaimed"):
        base += 10
    if count_state(zone_events, "zone_rejected"):
        base -= 20
    return max(min(base, 100), 1)


def calculate_zone_strength_decay(row: pd.Series, zone_events: pd.DataFrame, field_events: pd.DataFrame) -> float:
    decay = 0.0
    decay += count_state(zone_events, "zone_rejected") * 35
    decay += count_state(field_events, "field_exhausted") * 20
    decay += count_state(field_events, "field_weakening") * 15
    if truthy(row.get("failed_after_return")):
        decay += 20
    if count_state(zone_events, "zone_reclaimed"):
        decay -= 25
    if count_state(field_events, "field_recovered"):
        decay -= 25
    return max(min(decay, 100), 0)


def calculate_recovery_ratio(row: pd.Series, zone_events: pd.DataFrame, field_events: pd.DataFrame) -> float:
    recovery = 0.0
    stress = 1.0
    recovery += count_state(zone_events, "zone_reclaimed") * 40
    recovery += count_state(field_events, "field_recovered") * 40
    if str(row.get("expansion_type") or "") == "PURE_EXPANSION":
        recovery += 20
    stress += count_state(zone_events, "zone_rejected") * 30
    stress += count_state(field_events, "field_exhausted") * 20
    if truthy(row.get("failed_after_return")):
        stress += 25
    return max(min(recovery / stress, 2.0), 0.0)


def classify_recovery_state(recovery_ratio: float, zone_events: pd.DataFrame, field_events: pd.DataFrame) -> str:
    if count_state(zone_events, "zone_reclaimed") and count_state(field_events, "field_recovered"):
        return "RECOVERED"
    if recovery_ratio >= 1.0:
        return "STRONG_RECOVERY"
    if recovery_ratio >= 0.5:
        return "PARTIAL_RECOVERY"
    return "NO_RECOVERY"


def classify_els_elu_state(moment_utilization_ratio: float, fleche_state: str) -> str:
    if fleche_state == "RUPTURE" or moment_utilization_ratio > 1.0:
        return "ELU_RUPTURE_RESEARCH_ZONE"
    if moment_utilization_ratio > 0.75:
        return "HIGH_UTILIZATION_RESEARCH_ZONE"
    if moment_utilization_ratio > 0.5:
        return "ELS_DEFORMATION_RESEARCH_ZONE"
    return "ELS_ACCEPTABLE_RESEARCH_ZONE"


def classify_zone_mechanics(
    row: pd.Series,
    fleche_state: str,
    fatigue_state: str,
    zone_case_events: pd.DataFrame,
    field_case_events: pd.DataFrame,
    recovery_ratio: float,
    zone_strength_decay: float,
) -> Dict[str, str]:
    if str(row.get("source_status") or "") == "NOT_FOUND":
        return mechanics_result(
            "PENDING_REVIEW",
            "PENDING_REVIEW",
            "PENDING_REVIEW",
        )

    if count_state(zone_case_events, "zone_reclaimed") and count_state(field_case_events, "field_recovered"):
        return mechanics_result(
            "RECOVERY_FAMILY",
            "RECLAIM_RECOVERY",
            "RECOVERED_ZONE",
        )

    if count_state(zone_case_events, "zone_rejected") and count_state(field_case_events, "field_exhausted"):
        if has_expansion_before_failure(row):
            return mechanics_result(
                "EXHAUSTION_FAMILY",
                "EXPANSION_EXHAUSTION",
                "EXHAUSTED_ZONE",
            )
        if zone_strength_decay >= 70:
            return mechanics_result(
                "RUPTURE_FAMILY",
                "FAILED_RETURN_RUPTURE",
                "RUPTURE_ZONE",
            )
        return mechanics_result(
            "EXHAUSTION_FAMILY",
            "LATE_FAILURE",
            "EXHAUSTED_ZONE",
        )

    if fleche_state == "RUPTURE":
        return mechanics_result(
            "RUPTURE_FAMILY",
            "DIRECT_RUPTURE",
            "RUPTURE_ZONE",
        )

    if is_fatigue_family_candidate(
        row=row,
        fatigue_state=fatigue_state,
        zone_case_events=zone_case_events,
        field_case_events=field_case_events,
        zone_strength_decay=zone_strength_decay,
    ):
        return mechanics_result(
            "FATIGUE_FAMILY",
            fatigue_subtype(
                row=row,
                zone_case_events=zone_case_events,
                field_case_events=field_case_events,
                zone_strength_decay=zone_strength_decay,
            ),
            "FATIGUE_ZONE",
        )

    if is_plastic_family_candidate(
        row=row,
        fleche_state=fleche_state,
        recovery_ratio=recovery_ratio,
        mechanical_load_score=calculate_mechanical_load_score(
            fleche_ratio=safe_divide(zone_penetration_depth(row), zone_range_height(row)),
            delta_zscore=row.get("peak_delta_zscore"),
            layer_count=row.get("peak_layer_count"),
            zone_revisit_count=row.get("zone_revisit_count"),
            failed_after_return=row.get("failed_after_return"),
            confidence_collapse=is_confidence_collapse(row),
        ),
    ):
        return mechanics_result(
            "PLASTIC_FAMILY",
            plastic_subtype(fleche_state, recovery_ratio),
            "PLASTIC_ZONE",
        )

    if recovery_ratio > 0.5:
        return mechanics_result(
            "ELASTIC_FAMILY",
            "STRONG_REACTION",
            "ELASTIC_ZONE",
        )

    return mechanics_result(
        "ELASTIC_FAMILY",
        "RIGID_SUPPORT",
        "RIGID_ZONE",
    )


def mechanics_result(family: str, subtype: str, state: str) -> Dict[str, str]:
    return {
        "mechanical_family": family,
        "mechanical_subtype": subtype,
        "zone_mechanical_state": state,
    }


def is_fatigue_family_candidate(
    row: pd.Series,
    fatigue_state: str,
    zone_case_events: pd.DataFrame,
    field_case_events: pd.DataFrame,
    zone_strength_decay: float,
) -> bool:
    test_count = count_state(zone_case_events, "zone_tested")
    repeated_events = len(zone_case_events) >= 3
    field_weakening = count_state(field_case_events, "field_weakening") > 0
    field_exhausted = count_state(field_case_events, "field_exhausted") > 0
    progressive_weakening = field_weakening or field_exhausted
    high_fatigue = fatigue_state in {"HIGH_FATIGUE", "CRITICAL_FATIGUE"}
    high_decay = zone_strength_decay >= 50

    if truthy(row.get("failed_after_return")) and not progressive_weakening:
        return False

    return (
        test_count >= 2
        or repeated_events
        or high_decay
        or high_fatigue
    ) and progressive_weakening


def fatigue_subtype(
    row: pd.Series,
    zone_case_events: pd.DataFrame,
    field_case_events: pd.DataFrame,
    zone_strength_decay: float,
) -> str:
    if count_state(field_case_events, "field_weakening"):
        return "PROGRESSIVE_WEAKENING"
    if zone_strength_decay >= 70:
        return "RIGIDITY_DECAY"
    if count_state(field_case_events, "field_exhausted"):
        return "RECOVERY_LOSS"
    if count_state(zone_case_events, "zone_tested") >= 2:
        return "REPEATED_TEST_FATIGUE"
    return "PROGRESSIVE_WEAKENING"


def is_plastic_family_candidate(
    row: pd.Series,
    fleche_state: str,
    recovery_ratio: float,
    mechanical_load_score: float,
) -> bool:
    fleche_ratio = safe_divide(zone_penetration_depth(row), zone_range_height(row))
    deep_penetration = fleche_state == "HIGH" or 0.60 <= fleche_ratio <= 1.00
    partial_recovery = 0 < recovery_ratio < 1
    medium_high_load = mechanical_load_score >= 50

    if truthy(row.get("failed_after_return")):
        return False

    return deep_penetration and partial_recovery and medium_high_load


def plastic_subtype(fleche_state: str, recovery_ratio: float) -> str:
    if fleche_state == "HIGH":
        return "DEEP_PENETRATION_PARTIAL_RECOVERY"
    if recovery_ratio > 0:
        return "PLASTIC_REACTION"
    return "TEMPORARY_DEFORMATION"


def has_expansion_before_failure(row: pd.Series) -> bool:
    expansion_type = str(row.get("expansion_type") or "")
    expansion_strength = str(row.get("expansion_strength") or "")
    max_move_after_return = abs_number(row.get("max_move_after_return"))

    if expansion_type in {"EXPANSION_THEN_REVERSAL", "PURE_EXPANSION"}:
        return True
    if truthy(row.get("expansion_survived")):
        return True
    if expansion_strength in {"HIGH", "EXTREME"} and max_move_after_return >= 500:
        return True
    return max_move_after_return >= 550


def build_summary(results: pd.DataFrame, run_utc: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = [
        {"analysis_run_utc": run_utc, "metric": "rows_generated", "value": len(results), "notes": ""},
    ]

    for state, count in results["zone_mechanical_state"].value_counts().items():
        rows.append(
            {
                "analysis_run_utc": run_utc,
                "metric": f"state_count_{state}",
                "value": int(count),
                "notes": "Mechanical state count",
            }
        )

    for family, count in results["mechanical_family"].value_counts().items():
        rows.append(
            {
                "analysis_run_utc": run_utc,
                "metric": f"family_count_{family}",
                "value": int(count),
                "notes": "Mechanical family count",
            }
        )

    for subtype, count in results["mechanical_subtype"].value_counts().items():
        rows.append(
            {
                "analysis_run_utc": run_utc,
                "metric": f"subtype_count_{subtype}",
                "value": int(count),
                "notes": "Mechanical subtype count",
            }
        )

    for case_id in NOTABLE_CASES:
        matched = results[results["case_id"] == case_id]
        rows.append(
            {
                "analysis_run_utc": run_utc,
                "metric": f"notable_{case_id}",
                "value": matched.iloc[0]["zone_mechanical_state"] if not matched.empty else "NOT_FOUND",
                "notes": matched.iloc[0]["case_label"] if not matched.empty else "Case not present in current research log",
            }
        )

    return pd.DataFrame(rows)


def build_mechanics_timeline(results: pd.DataFrame, run_utc: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for _, row in results.iterrows():
        path = lifecycle_path_for_row(row)
        current_step = current_timeline_step(row)
        previous_state, next_state = neighboring_states(path, current_step)
        rows.append(
            {
                "analysis_run_utc": run_utc,
                "case_id": row.get("case_id"),
                "episode_id": row.get("episode_id"),
                "mechanical_family": row.get("mechanical_family"),
                "mechanical_subtype": row.get("mechanical_subtype"),
                "zone_mechanical_state": row.get("zone_mechanical_state"),
                "timeline_step": current_step,
                "timeline_order": timeline_order(path, current_step),
                "previous_state": previous_state,
                "next_state": next_state,
                "state_duration": row.get("duration_seconds", ""),
                "transition_reason": transition_reason_for_row(row),
                "lifecycle_path": " -> ".join(path),
                "timeline_position": f"{timeline_order(path, current_step)}/{len(path)}",
                "recovery_ratio": row.get("recovery_ratio"),
                "fatigue_index": row.get("fatigue_index"),
                "zone_strength_decay": row.get("zone_strength_decay"),
                "moment_utilization_ratio": row.get("moment_utilization_ratio"),
                "els_elu_state": row.get("els_elu_state"),
                "research_only": True,
            }
        )

    return pd.DataFrame(rows)


def build_mechanics_capacity(results: pd.DataFrame, run_utc: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for _, row in results.iterrows():
        m_applied = abs_number(row.get("mechanical_load_score"))
        m_capacity = zone_moment_capacity(row)
        capacity_ratio = safe_divide(m_applied, m_capacity)
        regime_context = mechanical_regime_context(row)
        regime_multiplier = volatility_capacity_multiplier(row, regime_context)
        adjusted_capacity = m_capacity * regime_multiplier
        adaptive_threshold = 1.50 * regime_multiplier
        repair_strength = zone_repair_strength(row)
        material_recovery = zone_material_recovery(row, repair_strength)
        residual_strength = zone_residual_strength(row, material_recovery)
        calibration_state = capacity_calibration_state(row, regime_context, residual_strength)
        capacity_state = classify_adaptive_capacity_state(
            capacity_ratio=capacity_ratio,
            regime_multiplier=regime_multiplier,
            calibration_state=calibration_state,
        )
        dynamic_elu = classify_dynamic_elu_state(
            capacity_ratio=capacity_ratio,
            adaptive_threshold=adaptive_threshold,
            fatigue_index=to_float(row.get("fatigue_index")) or 0.0,
            residual_strength=residual_strength,
            capacity_state=capacity_state,
            zone_strength_decay=to_float(row.get("zone_strength_decay")) or 0.0,
            calibration_state=calibration_state,
        )

        rows.append(
            {
                "analysis_run_utc": run_utc,
                "case_id": row.get("case_id"),
                "episode_id": row.get("episode_id"),
                "mechanical_family": row.get("mechanical_family"),
                "mechanical_subtype": row.get("mechanical_subtype"),
                "zone_mechanical_state": row.get("zone_mechanical_state"),
                "zone_moment_capacity": round_float(m_capacity),
                "zone_capacity_ratio": round_float(capacity_ratio),
                "zone_capacity_state": capacity_state,
                "zone_repair_strength": round_float(repair_strength),
                "zone_material_recovery": round_float(material_recovery),
                "zone_residual_strength": round_float(residual_strength),
                "regime_adjusted_capacity": round_float(adjusted_capacity),
                "adaptive_capacity_threshold": round_float(adaptive_threshold),
                "volatility_capacity_multiplier": round_float(regime_multiplier),
                "mechanical_regime_context": regime_context,
                "capacity_calibration_state": calibration_state,
                "dynamic_elu_state": dynamic_elu,
                "mechanical_load_score": row.get("mechanical_load_score"),
                "fatigue_index": row.get("fatigue_index"),
                "zone_strength_decay": row.get("zone_strength_decay"),
                "recovery_ratio": row.get("recovery_ratio"),
                "research_only": True,
            }
        )

    return pd.DataFrame(rows)


def merge_capacity_into_results(results: pd.DataFrame, capacity: pd.DataFrame) -> pd.DataFrame:
    if results.empty or capacity.empty:
        return results

    capacity_columns = [
        "case_id",
        "zone_moment_capacity",
        "zone_capacity_ratio",
        "zone_capacity_state",
        "zone_repair_strength",
        "zone_material_recovery",
        "zone_residual_strength",
        "regime_adjusted_capacity",
        "adaptive_capacity_threshold",
        "volatility_capacity_multiplier",
        "mechanical_regime_context",
        "capacity_calibration_state",
        "dynamic_elu_state",
    ]
    available_columns = [column for column in capacity_columns if column in capacity.columns]
    return results.merge(capacity[available_columns], on="case_id", how="left")


def build_mechanics_sigma(results: pd.DataFrame, run_utc: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for _, row in results.iterrows():
        v_formation = formation_velocity(row)
        delta_formation = formation_delta(row)
        t_formation = formation_quality(row)
        base_resistance = base_zone_resistance(
            v_formation=v_formation,
            delta_formation=delta_formation,
            t_formation=t_formation,
        )
        volatility_modifier = sigma_volatility_modifier(row)
        fatigue_factor = sigma_fatigue_factor(row)
        sigma_barre = safe_divide(base_resistance * volatility_modifier, fatigue_factor)
        sigma_market = calculate_sigma_market(row)
        utilization = safe_divide(sigma_market, sigma_barre)
        sigma_state = calibrate_sigma_state(row, classify_sigma_state(utilization))
        failure_risk = classify_sigma_failure_risk(
            utilization=utilization,
            sigma_state=sigma_state,
            fatigue_factor=fatigue_factor,
            mechanical_state=str(row.get("zone_mechanical_state") or ""),
        )

        rows.append(
            {
                "analysis_run_utc": run_utc,
                "case_id": row.get("case_id"),
                "episode_id": row.get("episode_id"),
                "mechanical_family": row.get("mechanical_family"),
                "mechanical_subtype": row.get("mechanical_subtype"),
                "zone_mechanical_state": row.get("zone_mechanical_state"),
                "v_formation": round_float(v_formation),
                "delta_formation": round_float(delta_formation),
                "t_formation": round_float(t_formation),
                "base_zone_resistance": round_float(base_resistance),
                "volatility_modifier": round_float(volatility_modifier),
                "fatigue_factor": round_float(fatigue_factor),
                "sigma_barre_zone": round_float(sigma_barre),
                "sigma_market": round_float(sigma_market),
                "stress_utilization": round_float(utilization),
                "sigma_state": sigma_state,
                "sigma_failure_risk": failure_risk,
                "sigma_model_version": "SIGMA_BARRE_ZONE_V1",
                "research_only": True,
            }
        )

    return pd.DataFrame(rows)


def merge_sigma_into_results(results: pd.DataFrame, sigma: pd.DataFrame) -> pd.DataFrame:
    if results.empty or sigma.empty:
        return results

    sigma_columns = [
        "case_id",
        "v_formation",
        "delta_formation",
        "t_formation",
        "base_zone_resistance",
        "volatility_modifier",
        "fatigue_factor",
        "sigma_barre_zone",
        "sigma_market",
        "stress_utilization",
        "sigma_state",
        "sigma_failure_risk",
        "sigma_model_version",
    ]
    available_columns = [column for column in sigma_columns if column in sigma.columns]
    return results.merge(sigma[available_columns], on="case_id", how="left")


def build_sigma_evolution(results: pd.DataFrame, run_utc: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for _, row in results.iterrows():
        zone_age = calculate_zone_age(row)
        zone_test_count = calculate_zone_test_count(row)
        repair_cycles = calculate_repair_cycles(row)
        reclaim_history = calculate_reclaim_history(row)
        institutional_reinforcement = calculate_institutional_reinforcement(row)
        mechanical_memory_score = calculate_mechanical_memory_score(
            row=row,
            zone_age=zone_age,
            zone_test_count=zone_test_count,
            repair_cycles=repair_cycles,
            reclaim_history=reclaim_history,
            institutional_reinforcement=institutional_reinforcement,
        )
        sigma_age_factor = calculate_sigma_age_factor(row, zone_age, zone_test_count)
        sigma_repair_bonus = calculate_sigma_repair_bonus(
            repair_cycles=repair_cycles,
            reclaim_history=reclaim_history,
            institutional_reinforcement=institutional_reinforcement,
        )
        memory_multiplier = 1.0 + min(mechanical_memory_score, 100.0) / 200.0
        repair_multiplier = 1.0 + min(sigma_repair_bonus, 100.0) / 100.0
        aging_penalty = max(sigma_age_factor, 0.50)
        adaptive_sigma_barre_v2 = safe_divide(
            (to_float(row.get("sigma_barre_zone")) or 0.0) * memory_multiplier * repair_multiplier,
            aging_penalty,
        )
        sigma_memory_state = classify_sigma_memory_state(
            row=row,
            zone_age=zone_age,
            zone_test_count=zone_test_count,
            repair_cycles=repair_cycles,
            institutional_reinforcement=institutional_reinforcement,
            sigma_age_factor=sigma_age_factor,
            adaptive_sigma_barre_v2=adaptive_sigma_barre_v2,
        )

        rows.append(
            {
                "analysis_run_utc": run_utc,
                "case_id": row.get("case_id"),
                "episode_id": row.get("episode_id"),
                "mechanical_family": row.get("mechanical_family"),
                "mechanical_subtype": row.get("mechanical_subtype"),
                "zone_mechanical_state": row.get("zone_mechanical_state"),
                "zone_age": round_float(zone_age),
                "zone_test_count": round_float(zone_test_count),
                "repair_cycles": round_float(repair_cycles),
                "reclaim_history": round_float(reclaim_history),
                "institutional_reinforcement": round_float(institutional_reinforcement),
                "mechanical_memory_score": round_float(mechanical_memory_score),
                "sigma_age_factor": round_float(sigma_age_factor),
                "sigma_repair_bonus": round_float(sigma_repair_bonus),
                "adaptive_sigma_barre_v2": round_float(adaptive_sigma_barre_v2),
                "sigma_memory_state": sigma_memory_state,
                "sigma_model_version": "SIGMA_EVOLUTION_V1",
                "research_only": True,
            }
        )

    return pd.DataFrame(rows)


def merge_sigma_evolution_into_results(results: pd.DataFrame, evolution: pd.DataFrame) -> pd.DataFrame:
    if results.empty or evolution.empty:
        return results

    evolution_columns = [
        "case_id",
        "zone_age",
        "zone_test_count",
        "repair_cycles",
        "reclaim_history",
        "institutional_reinforcement",
        "mechanical_memory_score",
        "sigma_age_factor",
        "sigma_repair_bonus",
        "adaptive_sigma_barre_v2",
        "sigma_memory_state",
    ]
    available_columns = [column for column in evolution_columns if column in evolution.columns]
    return results.merge(evolution[available_columns], on="case_id", how="left")


def calculate_zone_age(row: pd.Series) -> float:
    duration = to_float(row.get("duration_seconds")) or 0.0
    revisit_count = to_float(row.get("zone_revisit_count")) or 0.0
    event_count = to_float(row.get("zone_event_count")) or 0.0
    return max(duration / 60.0, 0.0) + revisit_count * 5.0 + event_count * 2.0


def calculate_zone_test_count(row: pd.Series) -> float:
    revisit_count = to_float(row.get("zone_revisit_count")) or 0.0
    zone_states = str(row.get("zone_lifecycle_states") or "")
    tested_count = zone_states.split("|").count("zone_tested")
    return max(revisit_count, tested_count)


def calculate_repair_cycles(row: pd.Series) -> float:
    zone_states = str(row.get("zone_lifecycle_states") or "")
    field_states = str(row.get("field_lifecycle_states") or "")
    return (
        zone_states.split("|").count("zone_reclaimed")
        + field_states.split("|").count("field_recovered")
        + (1 if str(row.get("zone_recovery_state") or "") in {"RECOVERED", "STRONG_RECOVERY"} else 0)
    )


def calculate_reclaim_history(row: pd.Series) -> float:
    zone_states = str(row.get("zone_lifecycle_states") or "")
    field_states = str(row.get("field_lifecycle_states") or "")
    history = zone_states.split("|").count("zone_reclaimed") * 1.0
    history += field_states.split("|").count("field_recovered") * 0.75
    if str(row.get("zone_mechanical_state") or "") == "RECOVERED_ZONE":
        history += 1.0
    return history


def calculate_institutional_reinforcement(row: pd.Series) -> float:
    formation_score = 0.0
    formation_score += min(abs_number(row.get("v_formation")) / 2.0, 25.0)
    formation_score += min(abs_number(row.get("delta_formation")) * 3.0, 25.0)
    formation_score += min((to_float(row.get("t_formation")) or 0.0) * 30.0, 30.0)
    formation_score += calculate_reclaim_history(row) * 10.0
    return min(formation_score, 100.0)


def calculate_mechanical_memory_score(
    row: pd.Series,
    zone_age: float,
    zone_test_count: float,
    repair_cycles: float,
    reclaim_history: float,
    institutional_reinforcement: float,
) -> float:
    score = institutional_reinforcement
    score += repair_cycles * 15.0
    score += reclaim_history * 10.0
    score += min(zone_age, 120.0) * 0.10
    score -= zone_test_count * 5.0
    score -= min(to_float(row.get("zone_strength_decay")) or 0.0, 100.0) * 0.35
    return max(min(score, 100.0), 0.0)


def calculate_sigma_age_factor(row: pd.Series, zone_age: float, zone_test_count: float) -> float:
    fatigue_index = to_float(row.get("fatigue_index")) or 0.0
    strength_decay = to_float(row.get("zone_strength_decay")) or 0.0
    factor = 1.0
    factor += min(zone_age, 240.0) / 240.0
    factor += min(zone_test_count, 10.0) * 0.08
    factor += min(fatigue_index, 100.0) / 150.0
    factor += min(strength_decay, 100.0) / 150.0
    return max(min(factor, 3.0), 0.75)


def calculate_sigma_repair_bonus(
    repair_cycles: float,
    reclaim_history: float,
    institutional_reinforcement: float,
) -> float:
    bonus = repair_cycles * 15.0
    bonus += reclaim_history * 10.0
    bonus += institutional_reinforcement * 0.35
    return max(min(bonus, 100.0), 0.0)


def classify_sigma_memory_state(
    row: pd.Series,
    zone_age: float,
    zone_test_count: float,
    repair_cycles: float,
    institutional_reinforcement: float,
    sigma_age_factor: float,
    adaptive_sigma_barre_v2: float,
) -> str:
    mechanical_state = str(row.get("zone_mechanical_state") or "")
    fatigue_index = to_float(row.get("fatigue_index")) or 0.0

    if mechanical_state == "RUPTURE_ZONE" or adaptive_sigma_barre_v2 <= 1.0:
        return "CRITICAL_SIGMA"
    if repair_cycles > 0 and mechanical_state == "RECOVERED_ZONE":
        return "REPAIRED_SIGMA"
    if institutional_reinforcement >= 55 and repair_cycles > 0:
        return "INSTITUTIONAL_SIGMA"
    if fatigue_index >= 70 or zone_test_count >= 3:
        return "FATIGUED_SIGMA"
    if zone_age >= 60 or sigma_age_factor >= 1.75:
        return "AGED_SIGMA"
    return "FRESH_SIGMA"


def formation_velocity(row: pd.Series) -> float:
    value = abs_number(row.get("pre_velocity_abs_mean"))
    if value:
        return min(value, 100.0)
    return min(abs_number(row.get("peak_velocity")) or 1.0, 100.0)


def formation_delta(row: pd.Series) -> float:
    value = abs_number(row.get("pre_delta_abs_mean"))
    if value:
        return min(value, 100.0)
    return min(abs_number(row.get("peak_delta_zscore")) * 10.0, 100.0)


def formation_quality(row: pd.Series) -> float:
    quiet_score = to_float(row.get("pre_quiet_score"))
    range_ratio = to_float(row.get("pre_range_ratio"))
    strength = str(row.get("preparation_strength") or "").upper()
    strength_bonus = {
        "LOW": 0.25,
        "MEDIUM": 0.50,
        "HIGH": 0.75,
        "EXTREME": 1.00,
    }.get(strength, 0.35)

    if quiet_score is None:
        quiet_component = strength_bonus
    else:
        quiet_component = max(min(quiet_score, 1.0), 0.0)

    if range_ratio is None:
        compression_component = strength_bonus
    else:
        compression_component = max(min(1.0 - range_ratio, 1.0), 0.0)

    return max((quiet_component + compression_component + strength_bonus) / 3.0, 0.10)


def base_zone_resistance(v_formation: float, delta_formation: float, t_formation: float) -> float:
    alpha = 0.25
    beta = 0.35
    gamma = 40.0
    return max(alpha * v_formation + beta * abs(delta_formation) + gamma * t_formation, 1.0)


def sigma_volatility_modifier(row: pd.Series) -> float:
    context = str(row.get("mechanical_regime_context") or "")
    severity = str(row.get("peak_max_severity") or "")
    layer_count = to_float(row.get("peak_layer_count")) or 0.0
    range_ratio = to_float(row.get("pre_range_ratio"))

    if context == "RECOVERY_CONTEXT":
        return 2.00
    if context == "EXPANSION_EXHAUSTION_CONTEXT":
        return 1.75
    if context == "RUPTURE_CONTEXT":
        return 0.85
    if context == "LOW_VOLATILITY_COMPRESSION_CONTEXT" or (range_ratio is not None and range_ratio <= 0.45):
        return 0.85
    if context == "HIGH_VOLATILITY_CONTEXT":
        return 1.35 if severity != "EXTREME" else 1.50
    if severity == "EXTREME" or layer_count >= 6:
        return 1.25
    return 1.0


def sigma_fatigue_factor(row: pd.Series) -> float:
    fatigue_index = to_float(row.get("fatigue_index")) or 0.0
    revisit_count = to_float(row.get("zone_revisit_count")) or 0.0
    strength_decay = to_float(row.get("zone_strength_decay")) or 0.0
    zone_event_count = to_float(row.get("zone_event_count")) or 0.0
    field_states = str(row.get("field_lifecycle_states") or "")

    factor = 1.0
    factor += min(fatigue_index, 100.0) / 100.0
    factor += min(revisit_count, 10.0) * 0.05
    factor += min(strength_decay, 100.0) / 200.0
    factor += min(zone_event_count, 10.0) * 0.03
    if "field_exhausted" in field_states:
        factor += 0.35
    return max(min(factor, 3.0), 0.75)


def calculate_sigma_market(row: pd.Series) -> float:
    penetration = abs_number(row.get("zone_penetration_depth"))
    volume_proxy = 1.0 + min(abs_number(row.get("peak_layer_count")) / 6.0, 1.5)
    velocity_proxy = 1.0 + min(abs_number(row.get("mechanical_load_score")) / 100.0, 1.0)
    delta_alignment = 1.15 if str(row.get("moment_stress_type") or "") == "STRESS" else 0.90
    context = str(row.get("mechanical_regime_context") or "")
    context_adjustment = 1.0
    if context == "RECOVERY_CONTEXT":
        context_adjustment = 0.20
    elif context == "EXPANSION_EXHAUSTION_CONTEXT":
        context_adjustment = 0.45
    return penetration * volume_proxy * velocity_proxy * delta_alignment * context_adjustment


def classify_sigma_state(stress_utilization: float) -> str:
    if stress_utilization < 0.75:
        return "SAFE_STRESS"
    if stress_utilization < 1.00:
        return "ELS_STRESS_WARNING"
    if stress_utilization < 1.30:
        return "ELU_STRESS_CRITICAL"
    return "SIGMA_RUPTURE_RISK"


def calibrate_sigma_state(row: pd.Series, sigma_state: str) -> str:
    if sigma_state != "SIGMA_RUPTURE_RISK":
        return sigma_state

    mechanical_state = str(row.get("zone_mechanical_state") or "")
    regime_context = str(row.get("mechanical_regime_context") or "")
    if mechanical_state == "RUPTURE_ZONE" or regime_context == "RUPTURE_CONTEXT":
        return sigma_state
    if regime_context in {"EXPANSION_EXHAUSTION_CONTEXT", "RECOVERY_CONTEXT"}:
        return "ELU_STRESS_CRITICAL"
    return sigma_state


def classify_sigma_failure_risk(
    utilization: float,
    sigma_state: str,
    fatigue_factor: float,
    mechanical_state: str,
) -> str:
    if sigma_state == "SIGMA_RUPTURE_RISK" and fatigue_factor >= 2.0:
        return "HIGH"
    if sigma_state == "SIGMA_RUPTURE_RISK":
        return "MEDIUM"
    if sigma_state == "ELU_STRESS_CRITICAL" or mechanical_state == "RUPTURE_ZONE":
        return "MEDIUM"
    if utilization >= 0.75:
        return "LOW"
    return "NONE"


def zone_moment_capacity(row: pd.Series) -> float:
    rigidity = to_float(row.get("zone_rigidity")) or 1.0
    decay = to_float(row.get("zone_strength_decay")) or 0.0
    recovery = to_float(row.get("recovery_ratio")) or 0.0
    fatigue = to_float(row.get("fatigue_index")) or 0.0

    capacity = rigidity * (1 - min(decay, 100.0) / 100.0)
    capacity += min(recovery, 2.0) * 20.0
    capacity -= min(fatigue, 100.0) * 0.15
    return max(capacity, 1.0)


def zone_repair_strength(row: pd.Series) -> float:
    recovery_ratio = to_float(row.get("recovery_ratio")) or 0.0
    if str(row.get("zone_recovery_state") or "") == "RECOVERED":
        recovery_ratio += 0.5
    if str(row.get("zone_mechanical_state") or "") == "RECOVERED_ZONE":
        recovery_ratio += 0.5
    return min(recovery_ratio, 2.0)


def zone_material_recovery(row: pd.Series, repair_strength: float) -> float:
    recovery_ratio = to_float(row.get("recovery_ratio")) or 0.0
    reclaim_strength = 1.0 if str(row.get("zone_recovery_state") or "") == "RECOVERED" else 0.5
    defensive_absorption = 1.0 if str(row.get("moment_stress_type") or "") == "ABSORPTION" else 0.75
    return min(recovery_ratio * reclaim_strength * defensive_absorption * max(repair_strength, 0.5), 2.0)


def zone_residual_strength(row: pd.Series, material_recovery: float) -> float:
    strength_decay = (to_float(row.get("zone_strength_decay")) or 0.0) / 100.0
    recovery_bonus = min(material_recovery, 1.0) * 0.5
    residual = 1.0 - strength_decay + recovery_bonus
    return max(min(residual, 1.5), 0.0)


def classify_capacity_state(capacity_ratio: float) -> str:
    if capacity_ratio <= 0.50:
        return "SAFE"
    if capacity_ratio <= 0.75:
        return "WARNING"
    if capacity_ratio <= 1.00:
        return "HIGH_LOAD"
    if capacity_ratio <= 1.25:
        return "ELS_LIMIT"
    if capacity_ratio <= 1.50:
        return "ELU_LIMIT"
    return "CAPACITY_FAILURE"


def classify_adaptive_capacity_state(
    capacity_ratio: float,
    regime_multiplier: float,
    calibration_state: str,
) -> str:
    multiplier = max(regime_multiplier, 0.50)
    if capacity_ratio <= 0.50 * multiplier:
        return "SAFE"
    if capacity_ratio <= 0.75 * multiplier:
        return "WARNING"
    if capacity_ratio <= 1.00 * multiplier:
        return "HIGH_LOAD"
    if capacity_ratio <= 1.25 * multiplier:
        return "ELS_LIMIT"
    if capacity_ratio <= 1.50 * multiplier:
        return "ELU_LIMIT"

    if calibration_state in {"RECOVERY_PROTECTED", "EXPANSION_PROTECTED"}:
        return "ELU_LIMIT"
    return "CAPACITY_FAILURE"


def mechanical_regime_context(row: pd.Series) -> str:
    mechanical_family = str(row.get("mechanical_family") or "")
    mechanical_subtype = str(row.get("mechanical_subtype") or "")
    mechanical_state = str(row.get("zone_mechanical_state") or "")
    expansion_type = str(row.get("expansion_type") or "")
    volatility_regime = str(row.get("volatility_regime") or "")
    velocity_state = str(row.get("velocity_state") or "")
    volume_state = str(row.get("volume_state") or "")

    if mechanical_state == "RECOVERED_ZONE" or "RECOVERY" in mechanical_family:
        return "RECOVERY_CONTEXT"
    if "EXHAUSTION" in mechanical_family or "EXHAUSTION" in mechanical_subtype:
        return "EXPANSION_EXHAUSTION_CONTEXT"
    if "EXPANSION" in expansion_type and "REVERSAL" in expansion_type:
        return "EXPANSION_EXHAUSTION_CONTEXT"
    if "RUPTURE" in mechanical_family or "RUPTURE" in mechanical_subtype:
        return "RUPTURE_CONTEXT"

    high_context = any(
        token in f"{volatility_regime} {velocity_state} {volume_state}".upper()
        for token in ["HIGH", "EXTREME", "EXPANSION", "SHOCK"]
    )
    low_context = any(
        token in f"{volatility_regime} {velocity_state} {volume_state}".upper()
        for token in ["LOW", "QUIET", "COMPRESSION"]
    )

    if high_context:
        return "HIGH_VOLATILITY_CONTEXT"
    if low_context:
        return "LOW_VOLATILITY_COMPRESSION_CONTEXT"
    return "NORMAL_CONTEXT"


def volatility_capacity_multiplier(row: pd.Series, regime_context: str) -> float:
    multiplier = 1.0
    layer_count = to_float(row.get("dashboard_v2_layer_count")) or to_float(row.get("peak_layer_count")) or 0.0
    moment_utilization = to_float(row.get("moment_utilization_ratio")) or 0.0

    if regime_context == "HIGH_VOLATILITY_CONTEXT":
        multiplier += 0.35
    elif regime_context == "EXPANSION_EXHAUSTION_CONTEXT":
        multiplier += 0.70
    elif regime_context == "RECOVERY_CONTEXT":
        multiplier += 0.50
    elif regime_context == "LOW_VOLATILITY_COMPRESSION_CONTEXT":
        multiplier -= 0.15
    elif regime_context == "RUPTURE_CONTEXT":
        multiplier -= 0.20

    if layer_count >= 6:
        multiplier += 0.25
    elif layer_count >= 5:
        multiplier += 0.15

    if moment_utilization >= 2.0 and regime_context != "RUPTURE_CONTEXT":
        multiplier += 0.10

    return max(min(multiplier, 2.0), 0.65)


def capacity_calibration_state(row: pd.Series, regime_context: str, residual_strength: float) -> str:
    failed_after_return = truthy(row.get("failed_after_return"))
    return_to_preparation = truthy(row.get("return_to_preparation"))
    expansion_type = str(row.get("expansion_type") or "")
    zone_state = str(row.get("zone_mechanical_state") or "")
    field_states = str(row.get("field_lifecycle_states") or "")
    zone_states = str(row.get("zone_lifecycle_states") or "")
    fatigue_index = to_float(row.get("fatigue_index")) or 0.0

    rupture_confirmed = (
        failed_after_return
        and "RUPTURE" in str(row.get("mechanical_family") or "")
        and fatigue_index >= 70
        and residual_strength <= 0.30
    )
    if rupture_confirmed:
        return "RUPTURE_CONFIRMED"
    if zone_state == "RECOVERED_ZONE" or "zone_reclaimed" in zone_states or "field_recovered" in field_states:
        return "RECOVERY_PROTECTED"
    if "EXPANSION" in expansion_type or regime_context == "EXPANSION_EXHAUSTION_CONTEXT":
        return "EXPANSION_PROTECTED"
    if return_to_preparation and residual_strength >= 0.75:
        return "REGIME_PROTECTED"
    return "ADAPTIVE_NORMAL"


def classify_dynamic_elu_state(
    capacity_ratio: float,
    adaptive_threshold: float,
    fatigue_index: float,
    residual_strength: float,
    capacity_state: str,
    zone_strength_decay: float,
    calibration_state: str,
) -> str:
    if calibration_state == "RECOVERY_PROTECTED" and residual_strength >= 0.75:
        return "WARNING" if capacity_state == "CAPACITY_FAILURE" else capacity_state
    if calibration_state == "EXPANSION_PROTECTED":
        return "ELU_LIMIT"
    if capacity_ratio > adaptive_threshold and fatigue_index >= 75 and residual_strength <= 0.25:
        return "CAPACITY_FAILURE"
    if capacity_ratio > 1.00 and fatigue_index >= 60 and residual_strength <= 0.50:
        return "ELU_LIMIT"
    if capacity_state in {"ELS_LIMIT", "ELU_LIMIT", "CAPACITY_FAILURE"}:
        return capacity_state
    if zone_strength_decay >= 70 and fatigue_index >= 60:
        return "ELS_LIMIT"
    return capacity_state


def build_mechanics_lifecycle(timeline: pd.DataFrame, run_utc: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for _, row in timeline.iterrows():
        path = str(row.get("lifecycle_path") or "").split(" -> ")
        for index, step in enumerate(path, start=1):
            rows.append(
                {
                    "analysis_run_utc": run_utc,
                    "case_id": row.get("case_id"),
                    "episode_id": row.get("episode_id"),
                    "mechanical_family": row.get("mechanical_family"),
                    "mechanical_subtype": row.get("mechanical_subtype"),
                    "zone_mechanical_state": row.get("zone_mechanical_state"),
                    "lifecycle_step": step,
                    "lifecycle_order": index,
                    "is_current_step": step == row.get("timeline_step"),
                    "transition_reason": row.get("transition_reason"),
                    "research_only": True,
                }
            )

    return pd.DataFrame(rows)


def lifecycle_path_for_row(row: pd.Series) -> List[str]:
    family = str(row.get("mechanical_family") or "")
    subtype = str(row.get("mechanical_subtype") or "")
    state = str(row.get("zone_mechanical_state") or "")

    if family == "RECOVERY_FAMILY":
        return ["ZONE_BIRTH", "ELASTIC", "PLASTIC", "FATIGUE", "RECOVERY"]
    if family == "EXHAUSTION_FAMILY":
        if subtype == "EXPANSION_EXHAUSTION":
            return ["ZONE_BIRTH", "ELASTIC", "EXPANSION", "EXHAUSTION"]
        return ["ZONE_BIRTH", "ELASTIC", "FATIGUE", "EXHAUSTION"]
    if family == "RUPTURE_FAMILY":
        return ["ZONE_BIRTH", "ELASTIC", "PLASTIC", "FATIGUE", "RUPTURE"]
    if family == "FATIGUE_FAMILY":
        return ["ZONE_BIRTH", "ELASTIC", "PLASTIC", "FATIGUE"]
    if family == "PLASTIC_FAMILY":
        return ["ZONE_BIRTH", "ELASTIC", "PLASTIC"]
    if family == "ELASTIC_FAMILY" and state == "ELASTIC_ZONE":
        return ["ZONE_BIRTH", "ELASTIC"]
    if family == "ELASTIC_FAMILY":
        return ["ZONE_BIRTH", "ELASTIC"]
    return ["ZONE_BIRTH", "PENDING_REVIEW"]


def current_timeline_step(row: pd.Series) -> str:
    family = str(row.get("mechanical_family") or "")
    state = str(row.get("zone_mechanical_state") or "")

    if family == "RECOVERY_FAMILY":
        return "RECOVERY"
    if family == "EXHAUSTION_FAMILY":
        return "EXHAUSTION"
    if family == "RUPTURE_FAMILY":
        return "RUPTURE"
    if family == "FATIGUE_FAMILY":
        return "FATIGUE"
    if family == "PLASTIC_FAMILY":
        return "PLASTIC"
    if state in {"RIGID_ZONE", "ELASTIC_ZONE"}:
        return "ELASTIC"
    return "PENDING_REVIEW"


def neighboring_states(path: List[str], current_step: str) -> tuple[str, str]:
    if current_step not in path:
        return "", ""

    index = path.index(current_step)
    previous_state = path[index - 1] if index > 0 else ""
    next_state = path[index + 1] if index + 1 < len(path) else ""
    return previous_state, next_state


def timeline_order(path: List[str], current_step: str) -> int:
    if current_step not in path:
        return 0
    return path.index(current_step) + 1


def transition_reason_for_row(row: pd.Series) -> str:
    family = str(row.get("mechanical_family") or "")
    subtype = str(row.get("mechanical_subtype") or "")
    fleche_state = str(row.get("zone_fleche_state") or "")
    fatigue_state = str(row.get("fatigue_state") or "")

    if family == "RECOVERY_FAMILY":
        return "zone reclaimed and field recovered"
    if subtype == "EXPANSION_EXHAUSTION":
        return "strong expansion followed by exhaustion"
    if family == "RUPTURE_FAMILY":
        return "recovery failure with zone rejection and field exhaustion"
    if family == "FATIGUE_FAMILY":
        return "repeated tests, strength decay, or field weakening"
    if family == "PLASTIC_FAMILY":
        return "deep penetration with partial recovery"
    if fleche_state in {"HIGH", "RUPTURE"}:
        return "deep penetration"
    if fatigue_state in {"HIGH_FATIGUE", "CRITICAL_FATIGUE"}:
        return "fatigue pressure"
    if family == "ELASTIC_FAMILY":
        return "low penetration or rigid reaction"
    return "pending review"


def build_notes(results: pd.DataFrame, summary: pd.DataFrame, run_utc: str) -> str:
    state_counts = Counter(results["zone_mechanical_state"])
    family_counts = Counter(results["mechanical_family"])
    subtype_counts = Counter(results["mechanical_subtype"])
    lines = [
        "# Zone Mechanics Cycle 3 Notes",
        "",
        f"- Run UTC: {run_utc}",
        "- Mode: Research only",
        "- No live signals",
        "- No execution",
        "- No Dashboard V2 scoring changes",
        "- No Phase 2",
        "",
        "## Mechanical State Counts",
    ]

    for state, count in state_counts.items():
        lines.append(f"- {state}: {count}")

    lines.extend(["", "## Mechanical Family Counts"])
    for family, count in family_counts.items():
        lines.append(f"- {family}: {count}")

    lines.extend(["", "## Mechanical Subtype Counts"])
    for subtype, count in subtype_counts.items():
        lines.append(f"- {subtype}: {count}")

    lines.extend(["", "## Reference Examples"])
    for case_id in NOTABLE_CASES:
        matched = results[results["case_id"] == case_id]
        if matched.empty:
            lines.append(f"- {case_id}: NOT_FOUND")
        else:
            row = matched.iloc[0]
            lines.append(
                f"- {case_id}: {row['mechanical_family']} / "
                f"{row['mechanical_subtype']} / "
                f"{row['zone_mechanical_state']} / "
                f"{row['case_label']} / fatigue={row['fatigue_state']} / "
                f"ELS-ELU={row['els_elu_state']}"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "- Mechanics are classified first by family/subtype/state.",
            "- Case IDs are retained only as reference examples, not as classification anchors.",
            "- RUPTURE_ZONE means research-observed zone rejection plus field exhaustion or rupture-level deformation.",
            "- RECOVERED_ZONE means research-observed zone reclaim plus field recovery.",
            "- EXHAUSTED_ZONE means the zone shows failure/exhaustion characteristics but does not yet meet the rupture threshold.",
            "",
            "Research-only note: these classifications are not signals and do not affect scoring.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_timeline_notes(timeline: pd.DataFrame, lifecycle: pd.DataFrame, run_utc: str) -> str:
    step_counts = Counter(timeline["timeline_step"]) if not timeline.empty else Counter()
    path_counts = Counter(timeline["lifecycle_path"]) if not timeline.empty else Counter()
    lines = [
        "# Zone Mechanics Timeline Notes",
        "",
        f"- Run UTC: {run_utc}",
        "- Mode: Research only",
        "- No live signals",
        "- No execution",
        "- No Dashboard V2 scoring changes",
        "- No Phase 2",
        "",
        "## Timeline Step Counts",
    ]

    for step, count in step_counts.items():
        lines.append(f"- {step}: {count}")

    lines.extend(["", "## Lifecycle Paths"])
    for path, count in path_counts.items():
        lines.append(f"- {path}: {count}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "- Timeline describes mechanical evolution, not a trade signal.",
            "- Lifecycle rows expand each episode path for research review.",
            "- Branches can end in RECOVERY, EXHAUSTION, or RUPTURE.",
        ]
    )

    return "\n".join(lines) + "\n"


def build_capacity_notes(capacity: pd.DataFrame, run_utc: str) -> str:
    state_counts = Counter(capacity["zone_capacity_state"]) if not capacity.empty else Counter()
    dynamic_counts = Counter(capacity["dynamic_elu_state"]) if not capacity.empty else Counter()
    regime_counts = Counter(capacity["mechanical_regime_context"]) if "mechanical_regime_context" in capacity else Counter()
    calibration_counts = (
        Counter(capacity["capacity_calibration_state"]) if "capacity_calibration_state" in capacity else Counter()
    )
    lines = [
        "# Zone Mechanics Capacity Notes",
        "",
        f"- Run UTC: {run_utc}",
        "- Mode: Research only",
        "- No live signals",
        "- No execution",
        "- No Dashboard V2 scoring changes",
        "- No Phase 2",
        "",
        "## Capacity State Counts",
    ]

    for state, count in state_counts.items():
        lines.append(f"- {state}: {count}")

    lines.extend(["", "## Dynamic ELU State Counts"])
    for state, count in dynamic_counts.items():
        lines.append(f"- {state}: {count}")

    lines.extend(["", "## Mechanical Regime Context Counts"])
    for state, count in regime_counts.items():
        lines.append(f"- {state}: {count}")

    lines.extend(["", "## Capacity Calibration State Counts"])
    for state, count in calibration_counts.items():
        lines.append(f"- {state}: {count}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "- M_applied is represented by mechanical_load_score.",
            "- M_capacity is represented by remaining zone moment capacity.",
            "- Capacity ratio = M_applied / M_capacity.",
            "- Regime-adjusted capacity applies context-only volatility and recovery multipliers.",
            "- Adaptive capacity threshold is the failure threshold after regime calibration.",
            "- Dynamic ELU combines capacity ratio, fatigue, residual strength, and strength decay.",
            "",
            "Research-only note: capacity states are not live signals and do not affect scoring.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_sigma_notes(sigma: pd.DataFrame, run_utc: str) -> str:
    state_counts = Counter(sigma["sigma_state"]) if not sigma.empty else Counter()
    risk_counts = Counter(sigma["sigma_failure_risk"]) if "sigma_failure_risk" in sigma else Counter()
    lines = [
        "# Zone Mechanics Sigma Barre Notes",
        "",
        f"- Run UTC: {run_utc}",
        "- Mode: Research only",
        "- No live signals",
        "- No execution",
        "- No Dashboard V2 scoring changes",
        "- No Phase 2",
        "",
        "## Sigma State Counts",
    ]

    for state, count in state_counts.items():
        lines.append(f"- {state}: {count}")

    lines.extend(["", "## Sigma Failure Risk Counts"])
    for state, count in risk_counts.items():
        lines.append(f"- {state}: {count}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "- sigma_barre_zone is the per-zone allowable stress proxy.",
            "- sigma_market is the observed research stress proxy.",
            "- stress_utilization = sigma_market / sigma_barre_zone.",
            "- Volatility modifier raises allowable stress during high-volatility context.",
            "- Fatigue factor lowers allowable stress as lifecycle decay accumulates.",
            "",
            "Research-only note: sigma states are not live signals and do not affect scoring.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_sigma_evolution_notes(evolution: pd.DataFrame, run_utc: str) -> str:
    memory_counts = (
        Counter(evolution["sigma_memory_state"]) if not evolution.empty else Counter()
    )
    lines = [
        "# Zone Mechanics Sigma Evolution Notes",
        "",
        f"- Run UTC: {run_utc}",
        "- Mode: Research only",
        "- No live signals",
        "- No execution",
        "- No entries",
        "- No Dashboard V2 scoring changes",
        "- No Phase 2",
        "",
        "## Sigma Memory State Counts",
    ]

    for state, count in memory_counts.items():
        lines.append(f"- {state}: {count}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "- Sigma evolution extends sigma_barre_zone with age, tests, repair cycles, and memory.",
            "- adaptive_sigma_barre_v2 = sigma_barre_zone * memory_multiplier * repair_multiplier / aging_penalty.",
            "- Recovered and reclaimed zones can gain repair bonus.",
            "- Old, repeatedly tested, or fatigued zones lose allowable stress through sigma_age_factor.",
            "",
            "Research-only note: sigma memory states are not live signals and do not affect scoring.",
        ]
    )
    return "\n".join(lines) + "\n"


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"Required input file not found: {relative_path(path)}")
    return pd.read_csv(path)


def read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def read_jsonl(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return pd.DataFrame(rows)


def events_for_case(events: pd.DataFrame, case_id: Any) -> pd.DataFrame:
    if events.empty or "related_case_id" not in events.columns:
        return events.head(0).copy()
    return events[events["related_case_id"].astype(str) == str(case_id)].copy()


def event_states(events: pd.DataFrame) -> List[str]:
    if events.empty:
        return []
    state_column = "event_state" if "event_state" in events.columns else "lifecycle_state"
    if state_column not in events.columns:
        return []
    return events[state_column].dropna().astype(str).tolist()


def count_state(events: pd.DataFrame, state: str) -> int:
    return event_states(events).count(state)


def truthy(value: Any) -> bool:
    return str(value).upper() in {"TRUE", "1", "YES"}


def is_confidence_collapse(row: pd.Series) -> bool:
    confidence = str(row.get("peak_observation_confidence") or "")
    state = str(row.get("peak_state") or "")
    return confidence in {"LOW_CONFIDENCE", "UNSTABLE_STATISTICAL_CONTEXT"} or "UNSTABLE" in state


def direction_from_signed(value: Any) -> str:
    number = to_float(value)
    if number is None or number == 0:
        return "UNKNOWN"
    return "UP" if number > 0 else "DOWN"


def safe_divide(numerator: Any, denominator: Any) -> float:
    numerator_value = to_float(numerator) or 0.0
    denominator_value = to_float(denominator)
    if denominator_value is None or denominator_value == 0:
        return 0.0
    return numerator_value / denominator_value


def subtract_number(left: Any, right: Any) -> float:
    left_value = to_float(left)
    right_value = to_float(right)
    if left_value is None or right_value is None:
        return 0.0
    return left_value - right_value


def abs_number(value: Any) -> float:
    number = to_float(value)
    return abs(number) if number is not None else 0.0


def to_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def round_float(value: Any, digits: int = 6) -> Any:
    number = to_float(value)
    if number is None:
        return ""
    return round(number, digits)


def value(row: pd.Series, column: str, default: Any = "") -> Any:
    if column not in row:
        return default
    selected = row.get(column)
    if pd.isna(selected):
        return default
    return selected


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()

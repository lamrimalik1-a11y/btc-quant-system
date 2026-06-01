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
import sys
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.performance_profile import PerfProfiler

OUTPUT_DIR = ROOT_DIR / "outputs"
RESEARCH_DIR = ROOT_DIR / "research"

EPISODES_FILE = OUTPUT_DIR / "historical_replay_dashboard_v2_episodes.csv"
HISTORICAL_ROWS_FILE = OUTPUT_DIR / "historical_observation_rows.csv"
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
VERESTCHAGUINE_FILE = RESEARCH_DIR / "zone_mechanics_verestchaguine.csv"
VERESTCHAGUINE_NOTES_FILE = RESEARCH_DIR / "zone_mechanics_verestchaguine_notes.md"
ZONE_BIRTH_REGISTRY_FILE = RESEARCH_DIR / "zone_birth_registry.csv"
ZONE_DEATH_REGISTRY_FILE = RESEARCH_DIR / "zone_death_registry.csv"
ZONE_MECHANICAL_MEMORY_FILE = RESEARCH_DIR / "zone_mechanical_memory.json"
ZONE_BIRTH_CONCEPT_FILE = ROOT_DIR / "docs" / "zone_mechanics_birth_concept.md"
ZONE_EVOLUTION_CHART_FILE = RESEARCH_DIR / "zone_evolution_chart.csv"
ZONE_EVOLUTION_HISTORY_FILE = RESEARCH_DIR / "zone_evolution_history.csv"
ZONE_EVOLUTION_NOTES_FILE = RESEARCH_DIR / "zone_evolution_notes.md"
ZONE_REAL_GEOMETRY_TRACKING_FILE = RESEARCH_DIR / "zone_real_geometry_tracking.csv"
ZONE_LIVE_RDM_EVOLUTION_FILE = RESEARCH_DIR / "zone_live_rdm_evolution.csv"
ZONE_LIVE_RDM_EVOLUTION_NOTES_FILE = RESEARCH_DIR / "zone_live_rdm_evolution_notes.md"
ZONE_INTERACTION_CORE_GEOMETRY_FILE = RESEARCH_DIR / "zone_interaction_core_geometry.csv"
ZONE_TRUE_LIFECYCLE_TRACKING_FILE = RESEARCH_DIR / "zone_true_lifecycle_tracking.csv"
ZONE_INTERACTION_CORE_NOTES_FILE = RESEARCH_DIR / "zone_interaction_core_notes.md"
ZONE_INTERACTION_DENSITY_MAP_FILE = RESEARCH_DIR / "zone_interaction_density_map.csv"
ZONE_INTERACTION_DENSITY_NOTES_FILE = RESEARCH_DIR / "zone_interaction_density_notes.md"

NOTABLE_CASES = [
    "CASE_00021",
    "CASE_00035",
    "CASE_00041",
    "CASE_00036",
    "CASE_00044",
]


def main() -> None:
    profiler = PerfProfiler("rdm_zone_mechanics_calculator")
    run_utc = utc_now()

    try:
        with profiler.step("csv_read_rdm_inputs"):
            episodes = read_csv(EPISODES_FILE)
            historical_rows = read_optional_csv(HISTORICAL_ROWS_FILE)
            research_log = read_csv(RESEARCH_LOG_FILE)
            case_labels = read_optional_csv(CASE_LABELS_FILE)
        with profiler.step("jsonl_read_lifecycle_events"):
            zone_events = read_jsonl(ZONE_LIFECYCLE_FILE)
            field_events = read_jsonl(FIELD_LIFECYCLE_FILE)

        with profiler.step("pandas_dataset_build"):
            dataset = build_dataset(episodes, research_log, case_labels)
        results = []

        with profiler.step("rdm_base_mechanics"):
            for _, row in dataset.iterrows():
                results.append(
                    calculate_zone_mechanics_row(
                        row=row,
                        zone_events=zone_events,
                        field_events=field_events,
                        run_utc=run_utc,
                    )
                )

        with profiler.step("pandas_dataframe_build"):
            results_df = pd.DataFrame(results)
        with profiler.step("rdm_capacity"):
            capacity_df = build_mechanics_capacity(results_df, run_utc)
            results_df = merge_capacity_into_results(results_df, capacity_df)
        with profiler.step("rdm_sigma"):
            sigma_df = build_mechanics_sigma(results_df, run_utc)
            results_df = merge_sigma_into_results(results_df, sigma_df)
        with profiler.step("rdm_sigma_evolution"):
            sigma_evolution_df = build_sigma_evolution(results_df, run_utc)
            results_df = merge_sigma_evolution_into_results(results_df, sigma_evolution_df)
        with profiler.step("rdm_verestchaguine"):
            verestchaguine_df = build_verestchaguine_fleche(results_df, run_utc)
            results_df = merge_verestchaguine_into_results(results_df, verestchaguine_df)
        with profiler.step("rdm_result_summaries"):
            results_df = add_rdm_result_summaries(results_df)
        with profiler.step("rdm_real_geometry_tracking"):
            geometry_tracking_df = build_real_geometry_tracking(results_df, run_utc)
            results_df = merge_real_geometry_tracking_into_results(results_df, geometry_tracking_df)
        with profiler.step("rdm_live_evolution_after_cache"):
            live_evolution_df = build_live_rdm_evolution(results_df, historical_rows, run_utc)
            results_df = merge_live_rdm_evolution_into_results(results_df, live_evolution_df)
        with profiler.step("rdm_case_cache_build_time"):
            rdm_case_cache = RdmCaseCache(live_evolution_df)
        with profiler.step("interaction_mask_build_time"):
            rdm_case_cache.precompute_interaction_masks()
        profiler.add_metric("rdm_case_cache_count", rdm_case_cache.case_count)
        with profiler.step("rdm_interaction_core_after_cache"):
            interaction_core_df = build_interaction_core_geometry(
                results_df,
                live_evolution_df,
                run_utc,
                case_cache=rdm_case_cache,
            )
            results_df = merge_interaction_core_into_results(results_df, interaction_core_df)
        with profiler.step("rdm_density_after_cache"):
            density_df = build_interaction_density_map(
                results_df,
                live_evolution_df,
                run_utc,
                case_cache=rdm_case_cache,
            )
            results_df = merge_interaction_density_into_results(results_df, density_df)
        with profiler.step("rdm_true_lifecycle"):
            true_lifecycle_df = build_true_lifecycle_tracking(
                results_df,
                interaction_core_df,
                live_evolution_df,
                run_utc,
                case_cache=rdm_case_cache,
            )
            results_df = merge_true_lifecycle_into_results(results_df, true_lifecycle_df)
        with profiler.step("rdm_v16_numeric_foundation"):
            results_df = add_rdm_v16_numeric_foundation(results_df)
        profiler.add_metric("interaction_mask_reuse_count", rdm_case_cache.mask_reuse_count)
        with profiler.step("rdm_timeline_lifecycle"):
            timeline_df = build_mechanics_timeline(results_df, run_utc)
            lifecycle_df = build_mechanics_lifecycle(timeline_df, run_utc)
        with profiler.step("rdm_birth_death_memory"):
            birth_df = build_zone_birth_registry(results_df, run_utc)
            death_df = build_zone_death_registry(results_df, run_utc)
            memory = build_zone_mechanical_memory(results_df, birth_df, death_df, timeline_df, run_utc)
        with profiler.step("rdm_evolution_chart"):
            evolution_chart_df = build_zone_evolution_chart(results_df, birth_df, death_df, run_utc)
            evolution_history_df = build_zone_evolution_history(evolution_chart_df, run_utc)
        with profiler.step("rdm_summary_notes_build"):
            summary_df = build_summary(results_df, run_utc)
            notes_text = build_notes(results_df, summary_df, run_utc)
            timeline_notes_text = build_timeline_notes(timeline_df, lifecycle_df, run_utc)
            capacity_notes_text = build_capacity_notes(capacity_df, run_utc)
            sigma_notes_text = build_sigma_notes(sigma_df, run_utc)
            sigma_evolution_notes_text = build_sigma_evolution_notes(sigma_evolution_df, run_utc)
            verestchaguine_notes_text = build_verestchaguine_notes(verestchaguine_df, run_utc)
            birth_concept_text = build_zone_birth_concept()
            evolution_notes_text = build_zone_evolution_notes(
                evolution_chart_df,
                evolution_history_df,
                run_utc=run_utc,
            )
            live_evolution_notes_text = build_live_rdm_evolution_notes(live_evolution_df, run_utc)
            interaction_core_notes_text = build_interaction_core_notes(
                interaction_core_df,
                true_lifecycle_df,
                run_utc,
            )
            density_notes_text = build_interaction_density_notes(density_df, run_utc)

        RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
        ZONE_BIRTH_CONCEPT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with profiler.step("csv_write_rdm_outputs"):
            results_df.to_csv(RESULTS_FILE, index=False)
            capacity_df.to_csv(CAPACITY_FILE, index=False)
            sigma_df.to_csv(SIGMA_FILE, index=False)
            sigma_evolution_df.to_csv(SIGMA_EVOLUTION_FILE, index=False)
            verestchaguine_df.to_csv(VERESTCHAGUINE_FILE, index=False)
            geometry_tracking_df.to_csv(ZONE_REAL_GEOMETRY_TRACKING_FILE, index=False)
            live_evolution_df.to_csv(ZONE_LIVE_RDM_EVOLUTION_FILE, index=False)
            interaction_core_df.to_csv(ZONE_INTERACTION_CORE_GEOMETRY_FILE, index=False)
            density_df.to_csv(ZONE_INTERACTION_DENSITY_MAP_FILE, index=False)
            true_lifecycle_df.to_csv(ZONE_TRUE_LIFECYCLE_TRACKING_FILE, index=False)
            birth_df.to_csv(ZONE_BIRTH_REGISTRY_FILE, index=False)
            death_df.to_csv(ZONE_DEATH_REGISTRY_FILE, index=False)
            evolution_chart_df.to_csv(ZONE_EVOLUTION_CHART_FILE, index=False)
            evolution_history_df.to_csv(ZONE_EVOLUTION_HISTORY_FILE, index=False)
            timeline_df.to_csv(TIMELINE_FILE, index=False)
            lifecycle_df.to_csv(LIFECYCLE_FILE, index=False)
            summary_df.to_csv(SUMMARY_FILE, index=False)
        with profiler.step("text_json_write_rdm_outputs"):
            NOTES_FILE.write_text(notes_text, encoding="utf-8")
            TIMELINE_NOTES_FILE.write_text(timeline_notes_text, encoding="utf-8")
            CAPACITY_NOTES_FILE.write_text(capacity_notes_text, encoding="utf-8")
            SIGMA_NOTES_FILE.write_text(sigma_notes_text, encoding="utf-8")
            SIGMA_EVOLUTION_NOTES_FILE.write_text(sigma_evolution_notes_text, encoding="utf-8")
            VERESTCHAGUINE_NOTES_FILE.write_text(verestchaguine_notes_text, encoding="utf-8")
            ZONE_LIVE_RDM_EVOLUTION_NOTES_FILE.write_text(live_evolution_notes_text, encoding="utf-8")
            ZONE_INTERACTION_CORE_NOTES_FILE.write_text(interaction_core_notes_text, encoding="utf-8")
            ZONE_INTERACTION_DENSITY_NOTES_FILE.write_text(density_notes_text, encoding="utf-8")
            ZONE_MECHANICAL_MEMORY_FILE.write_text(
                json.dumps(memory, indent=2, ensure_ascii=True),
                encoding="utf-8",
            )
            ZONE_BIRTH_CONCEPT_FILE.write_text(birth_concept_text, encoding="utf-8")
            ZONE_EVOLUTION_NOTES_FILE.write_text(evolution_notes_text, encoding="utf-8")

        profiler.add_metric("rows_processed", len(results_df))
        profiler.add_metric("historical_rows_loaded", len(historical_rows))
        profiler.add_metric("live_evolution_rows", len(live_evolution_df))
        profiler.add_metric("interaction_core_rows", len(interaction_core_df))
        profiler.add_metric("interaction_density_rows", len(density_df))
        profiler.add_metric("timeline_rows", len(timeline_df))
        profiler.add_metric("lifecycle_rows", len(lifecycle_df))

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
        print(f"Verestchaguine: {relative_path(VERESTCHAGUINE_FILE)}")
        print(f"Verestchaguine notes: {relative_path(VERESTCHAGUINE_NOTES_FILE)}")
        print(f"Real geometry tracking: {relative_path(ZONE_REAL_GEOMETRY_TRACKING_FILE)}")
        print(f"Live RDM evolution: {relative_path(ZONE_LIVE_RDM_EVOLUTION_FILE)}")
        print(f"Live RDM evolution notes: {relative_path(ZONE_LIVE_RDM_EVOLUTION_NOTES_FILE)}")
        print(f"Interaction core geometry: {relative_path(ZONE_INTERACTION_CORE_GEOMETRY_FILE)}")
        print(f"Interaction density map: {relative_path(ZONE_INTERACTION_DENSITY_MAP_FILE)}")
        print(f"True lifecycle tracking: {relative_path(ZONE_TRUE_LIFECYCLE_TRACKING_FILE)}")
        print(f"Interaction core notes: {relative_path(ZONE_INTERACTION_CORE_NOTES_FILE)}")
        print(f"Interaction density notes: {relative_path(ZONE_INTERACTION_DENSITY_NOTES_FILE)}")
        print(f"Zone birth registry: {relative_path(ZONE_BIRTH_REGISTRY_FILE)}")
        print(f"Zone death registry: {relative_path(ZONE_DEATH_REGISTRY_FILE)}")
        print(f"Zone mechanical memory: {relative_path(ZONE_MECHANICAL_MEMORY_FILE)}")
        print(f"Zone birth concept: {relative_path(ZONE_BIRTH_CONCEPT_FILE)}")
        print(f"Zone evolution chart: {relative_path(ZONE_EVOLUTION_CHART_FILE)}")
        print(f"Zone evolution history: {relative_path(ZONE_EVOLUTION_HISTORY_FILE)}")
        print(f"Zone evolution notes: {relative_path(ZONE_EVOLUTION_NOTES_FILE)}")
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
    finally:
        profiler.finish(
            csv_files=[
                RESULTS_FILE,
                SUMMARY_FILE,
                TIMELINE_FILE,
                LIFECYCLE_FILE,
                CAPACITY_FILE,
                SIGMA_FILE,
                SIGMA_EVOLUTION_FILE,
                VERESTCHAGUINE_FILE,
                ZONE_REAL_GEOMETRY_TRACKING_FILE,
                ZONE_LIVE_RDM_EVOLUTION_FILE,
                ZONE_INTERACTION_CORE_GEOMETRY_FILE,
                ZONE_INTERACTION_DENSITY_MAP_FILE,
                ZONE_TRUE_LIFECYCLE_TRACKING_FILE,
                ZONE_BIRTH_REGISTRY_FILE,
                ZONE_DEATH_REGISTRY_FILE,
                ZONE_EVOLUTION_CHART_FILE,
                ZONE_EVOLUTION_HISTORY_FILE,
            ]
        )


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
        "episode_end_time_utc": value(row, "episode_end_time_utc"),
        "start_row_id": value(row, "start_row_id"),
        "end_row_id": value(row, "end_row_id"),
        "duration_seconds": value(row, "duration_seconds"),
        "start_price": value(row, "start_price"),
        "end_price": value(row, "end_price"),
        "price_at_1m": value(row, "price_at_1m"),
        "price_at_5m": value(row, "price_at_5m"),
        "price_at_15m": value(row, "price_at_15m"),
        "price_at_30m": value(row, "price_at_30m"),
        "price_at_1h": value(row, "price_at_1h"),
        "price_at_2h": value(row, "price_at_2h"),
        "price_at_4h": value(row, "price_at_4h"),
        "price_at_day_end": value(row, "price_at_day_end"),
        "score_bucket": value(row, "score_bucket"),
        "peak_layer_count": value(row, "peak_layer_count"),
        "peak_max_severity": value(row, "peak_max_severity"),
        "peak_primary_context": value(row, "peak_primary_context"),
        "return_to_preparation": value(row, "return_to_preparation"),
        "failed_after_return": value(row, "failed_after_return"),
        "pre_velocity_abs_mean": value(row, "pre_velocity_abs_mean"),
        "pre_delta_abs_mean": value(row, "pre_delta_abs_mean"),
        "pre_quiet_score": value(row, "pre_quiet_score"),
        "pre_range": value(row, "pre_range"),
        "pre_range_value": value(row, "pre_range_value"),
        "pre_range_ratio": value(row, "pre_range_ratio"),
        "preparation_low_price": value(row, "preparation_low_price"),
        "preparation_high_price": value(row, "preparation_high_price"),
        "preparation_mid_price": value(row, "preparation_mid_price"),
        "preparation_start_row": value(row, "preparation_start_row"),
        "preparation_end_row": value(row, "preparation_end_row"),
        "preparation_strength": value(row, "preparation_strength"),
        "zone_revisit_count": value(row, "zone_revisit_count"),
        "return_price": value(row, "return_price"),
        "return_row": value(row, "return_row"),
        "return_timestamp": value(row, "return_timestamp"),
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
    zone_reclaims = count_state(zone_events, "zone_reclaimed")
    field_recoveries = count_state(field_events, "field_recovered")
    reaction_delay = to_float(row.get("revisit_expansion_delay_minutes")) or 0.0
    fatigue = revisit_count * 4 + zone_rejections * 18 + field_exhaustions * 14 + field_weakening * 9
    fatigue += min(reaction_delay, 60) * 0.25
    fatigue -= zone_reclaims * 14 + field_recoveries * 16
    if str(row.get("expansion_type") or "") == "PURE_EXPANSION":
        fatigue -= 8
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
    decay += count_state(zone_events, "zone_rejected") * 22
    decay += count_state(field_events, "field_exhausted") * 14
    decay += count_state(field_events, "field_weakening") * 9
    if truthy(row.get("failed_after_return")):
        decay += 12
    if count_state(zone_events, "zone_reclaimed"):
        decay -= 30
    if count_state(field_events, "field_recovered"):
        decay -= 32
    return max(min(decay, 100), 0)


def calculate_recovery_ratio(row: pd.Series, zone_events: pd.DataFrame, field_events: pd.DataFrame) -> float:
    recovery = 0.0
    stress = 1.0
    recovery += count_state(zone_events, "zone_reclaimed") * 55
    recovery += count_state(field_events, "field_recovered") * 55
    if str(row.get("expansion_type") or "") == "PURE_EXPANSION":
        recovery += 25
    stress += count_state(zone_events, "zone_rejected") * 24
    stress += count_state(field_events, "field_exhausted") * 16
    if truthy(row.get("failed_after_return")):
        stress += 18
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
        if zone_strength_decay >= 85 and truthy(row.get("failed_after_return")):
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

    if fleche_state == "RUPTURE" and zone_strength_decay >= 80 and fatigue_state == "CRITICAL_FATIGUE":
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
        guard = no_active_load_guard(row)
        if guard["zero_stress_flag"]:
            calibration_state = "NO_ACTIVE_LOAD_PROTECTED"
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
        if guard["zero_stress_flag"]:
            capacity_state = "SAFE"
            dynamic_elu = "ELS_SAFE"

        preparation_activation_state = classify_preparation_activation_state(row, guard["active_load_flag"])

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
                "active_load_flag": guard["active_load_flag"],
                "zero_stress_flag": guard["zero_stress_flag"],
                "no_active_load_reason": guard["no_active_load_reason"],
                "market_silence_flag": guard["market_silence_flag"],
                "dormant_preparation_flag": preparation_activation_state == "DORMANT_PREPARATION",
                "preparation_activation_state": preparation_activation_state,
                "capacity_guard_applied": guard["zero_stress_flag"],
                "research_reaction_candidate": (
                    "DORMANT_OR_UNTESTED_ZONE"
                    if guard["zero_stress_flag"]
                    else "ACTIVE_REACTION_REVIEW"
                ),
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
        "active_load_flag",
        "zero_stress_flag",
        "no_active_load_reason",
        "market_silence_flag",
        "dormant_preparation_flag",
        "preparation_activation_state",
        "capacity_guard_applied",
        "research_reaction_candidate",
    ]
    available_columns = [column for column in capacity_columns if column in capacity.columns]
    return results.merge(capacity[available_columns], on="case_id", how="left")


def no_active_load_guard(row: pd.Series) -> Dict[str, Any]:
    fleche_ratio = to_float(row.get("zone_fleche_ratio")) or 0.0
    penetration = abs_number(row.get("zone_penetration_depth"))
    signed_moment_value = abs_number(row.get("signed_moment_proxy"))
    sigma_market_value = abs_number(row.get("sigma_market"))
    if sigma_market_value == 0:
        sigma_market_value = abs_number(calculate_sigma_market(row))
    mechanical_load = abs_number(row.get("mechanical_load_score"))

    no_penetration = is_near_zero(fleche_ratio) or is_near_zero(penetration)
    no_moment = is_near_zero(signed_moment_value)
    no_sigma = is_near_zero(sigma_market_value)
    no_load = is_near_zero(mechanical_load)
    zero_stress = no_penetration and no_moment and no_sigma

    reasons: List[str] = []
    if no_penetration:
        reasons.append("NO_PENETRATION")
    if no_moment:
        reasons.append("NO_SIGNED_MOMENT")
    if no_sigma:
        reasons.append("NO_SIGMA_MARKET")
    if no_load:
        reasons.append("NO_MECHANICAL_LOAD")
    elif zero_stress:
        reasons.append("MECHANICAL_LOAD_SCORE_IGNORED_NO_STRESS")

    return {
        "active_load_flag": not zero_stress,
        "zero_stress_flag": zero_stress,
        "market_silence_flag": no_moment and no_sigma and no_load,
        "no_active_load_reason": "|".join(reasons) if zero_stress else "",
    }


def classify_preparation_activation_state(row: pd.Series, active_load_flag: bool) -> str:
    preparation_candidate = truthy(row.get("preparation_candidate"))
    if not preparation_candidate and not active_load_flag:
        return "UNTESTED_ZONE"
    if preparation_candidate and not active_load_flag:
        return "DORMANT_PREPARATION"
    if truthy(row.get("failed_after_return")):
        return "FAILED_PREPARATION"
    if str(row.get("expansion_strength") or "") in {"HIGH", "EXTREME"} and active_load_flag:
        return "EXPLOSIVE_PREPARATION"
    if preparation_candidate and active_load_flag:
        return "ACTIVE_PREPARATION"
    return "UNTESTED_ZONE"


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


def build_verestchaguine_fleche(results: pd.DataFrame, run_utc: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for _, row in results.iterrows():
        stress_history = build_zone_stress_history(row)
        ei_adaptive = verestchaguine_ei_adaptive(row)
        fleche = calculate_verestchaguine_fleche(stress_history, ei_adaptive)
        normalized_fleche = min(fleche["fleche_verestchaguine"], 2.0)
        static_fleche = to_float(row.get("zone_fleche_ratio")) or 0.0
        combined_score = 0.5 * static_fleche + 0.5 * normalized_fleche
        dynamic_state = classify_dynamic_fleche_state(combined_score)

        rows.append(
            {
                "analysis_run_utc": run_utc,
                "case_id": row.get("case_id"),
                "episode_id": row.get("episode_id"),
                "mechanical_family": row.get("mechanical_family"),
                "mechanical_subtype": row.get("mechanical_subtype"),
                "zone_mechanical_state": row.get("zone_mechanical_state"),
                "omega_stress_area": round_float(fleche["omega_stress_area"]),
                "stress_center_of_gravity": round_float(fleche["stress_center_of_gravity"]),
                "virtual_moment_at_g": round_float(fleche["virtual_moment_at_g"]),
                "ei_adaptive": round_float(ei_adaptive),
                "fleche_verestchaguine": round_float(fleche["fleche_verestchaguine"]),
                "fleche_dynamic_state": dynamic_state,
                "fleche_combined_score": round_float(combined_score),
                "fleche_model_version": "VERESTCHAGUINE_FLECHE_V1",
                "research_only": True,
            }
        )

    return pd.DataFrame(rows)


def merge_verestchaguine_into_results(results: pd.DataFrame, verestchaguine: pd.DataFrame) -> pd.DataFrame:
    if results.empty or verestchaguine.empty:
        return results

    verestchaguine_columns = [
        "case_id",
        "omega_stress_area",
        "stress_center_of_gravity",
        "virtual_moment_at_g",
        "ei_adaptive",
        "fleche_verestchaguine",
        "fleche_dynamic_state",
        "fleche_combined_score",
        "fleche_model_version",
    ]
    available_columns = [column for column in verestchaguine_columns if column in verestchaguine.columns]
    return results.merge(verestchaguine[available_columns], on="case_id", how="left")


def add_rdm_result_summaries(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return results

    rows = []
    for _, row in results.iterrows():
        summary = rdm_result_summary(row)
        enriched = row.to_dict()
        enriched.update(summary)
        rows.append(enriched)

    return pd.DataFrame(rows)


def rdm_result_summary(row: pd.Series) -> Dict[str, Any]:
    status = rdm_zone_status(row)
    risk = rdm_risk_level(row, status)
    health = rdm_health_score(row, status, risk)
    confidence = rdm_confidence(row, status)
    reason = rdm_short_reason(row, status, risk)
    watch_action = rdm_watch_action(status, risk)
    return {
        "rdm_zone_status": status,
        "rdm_health_score": round_float(health),
        "rdm_risk_level": risk,
        "rdm_confidence": confidence,
        "rdm_short_reason": reason,
        "rdm_watch_action": watch_action,
    }


def rdm_zone_status(row: pd.Series) -> str:
    state = str(row.get("zone_mechanical_state") or "")
    capacity = str(row.get("zone_capacity_state") or "")
    sigma = str(row.get("sigma_state") or "")
    memory = str(row.get("sigma_memory_state") or "")

    if truthy(row.get("zero_stress_flag")):
        return "DORMANT"
    if state == "RUPTURE_ZONE":
        return "RUPTURED"
    if capacity == "CAPACITY_FAILURE" and sigma == "SIGMA_RUPTURE_RISK":
        return "CRITICAL"
    if state == "EXHAUSTED_ZONE":
        return "EXHAUSTED"
    if state == "FATIGUE_ZONE" or memory == "FATIGUED_SIGMA":
        return "FATIGUED"
    if state == "RECOVERED_ZONE" or memory == "REPAIRED_SIGMA":
        return "RECOVERING"
    if str(row.get("current_state") or "") == "ZONE_DEATH":
        return "DEAD"
    return "ALIVE"


def rdm_risk_level(row: pd.Series, status: str) -> str:
    if status in {"RUPTURED", "DEAD", "CRITICAL"}:
        return "CRITICAL"
    if status in {"EXHAUSTED", "FATIGUED"}:
        return "HIGH"
    if str(row.get("sigma_state") or "") == "ELU_STRESS_CRITICAL":
        return "HIGH"
    if str(row.get("zone_capacity_state") or "") in {"ELU_LIMIT", "ELS_LIMIT", "HIGH_LOAD"}:
        return "MEDIUM"
    if status == "DORMANT":
        return "LOW"
    return "LOW"


def rdm_health_score(row: pd.Series, status: str, risk: str) -> float:
    base = {
        "ALIVE": 82.0,
        "RECOVERING": 76.0,
        "DORMANT": 68.0,
        "FATIGUED": 46.0,
        "EXHAUSTED": 34.0,
        "CRITICAL": 22.0,
        "RUPTURED": 12.0,
        "DEAD": 8.0,
    }.get(status, 50.0)
    fatigue_penalty = min(to_float(row.get("fatigue_index")) or 0.0, 100.0) * 0.12
    decay_penalty = min(to_float(row.get("zone_strength_decay")) or 0.0, 100.0) * 0.10
    recovery_bonus = min(to_float(row.get("recovery_ratio")) or 0.0, 2.0) * 8.0
    risk_penalty = {
        "CRITICAL": 12.0,
        "HIGH": 7.0,
        "MEDIUM": 3.0,
        "LOW": 0.0,
    }.get(risk, 0.0)
    return max(min(base - fatigue_penalty - decay_penalty - risk_penalty + recovery_bonus, 100.0), 0.0)


def rdm_confidence(row: pd.Series, status: str) -> str:
    if str(row.get("mechanical_birth_state") or "") == "UNKNOWN_BIRTH":
        return "MEDIUM"
    if status == "DORMANT":
        return "MEDIUM"
    if str(row.get("source_status") or "") == "NOT_FOUND":
        return "LOW"
    return "HIGH"


def rdm_short_reason(row: pd.Series, status: str, risk: str) -> str:
    if status == "DORMANT":
        return "No active load; zero stress guard protected the zone."
    if status == "RUPTURED":
        return "Mechanical state reached rupture context."
    if status == "CRITICAL":
        return "Capacity and sigma both show critical stress context."
    if status == "EXHAUSTED":
        return "Expansion/exhaustion branch dominates the zone outcome."
    if status == "FATIGUED":
        return "Fatigue lifecycle and memory dominate current state."
    if status == "RECOVERING":
        return "Recovery/reclaim memory is active."
    return f"Zone remains observable with {risk.lower()} research risk."


def rdm_watch_action(status: str, risk: str) -> str:
    if status in {"RUPTURED", "CRITICAL"}:
        return "REVIEW_RUPTURE_CONTEXT"
    if status == "EXHAUSTED":
        return "WATCH_EXHAUSTION_BRANCH"
    if status == "FATIGUED":
        return "WATCH_FATIGUE_DECAY"
    if status == "RECOVERING":
        return "REVIEW_RECOVERY_BEHAVIOR"
    if status == "DORMANT":
        return "WAIT_FOR_ACTIVE_LOAD"
    if risk == "MEDIUM":
        return "MONITOR_MECHANICAL_CONTEXT"
    return "OBSERVE_ONLY"


def build_real_geometry_tracking(results: pd.DataFrame, run_utc: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for _, row in results.iterrows():
        geometry = real_zone_geometry(row)
        tracking = mechanical_tracking_values(row, geometry)
        breaches = mechanical_breach_flags(tracking)
        rows.append(
            {
                "analysis_run_utc": run_utc,
                "case_id": row.get("case_id"),
                "episode_id": row.get("episode_id"),
                "zone_id": zone_identifier(row),
                **geometry,
                **tracking,
                **breaches,
                "research_only": True,
            }
        )

    return pd.DataFrame(rows)


def merge_real_geometry_tracking_into_results(results: pd.DataFrame, tracking: pd.DataFrame) -> pd.DataFrame:
    if results.empty or tracking.empty or "case_id" not in tracking.columns:
        return results

    tracking_columns = [column for column in tracking.columns if column not in {"analysis_run_utc", "research_only"}]
    return results.merge(tracking[tracking_columns], on=["case_id", "episode_id"], how="left")


def real_zone_geometry(row: pd.Series) -> Dict[str, Any]:
    low = to_float(row.get("preparation_low_price"))
    high = to_float(row.get("preparation_high_price"))
    fallback_used = False
    source = "PREPARATION_ZONE"

    if low is not None and high is not None and high != low:
        lower_edge, upper_edge = min(low, high), max(low, high)
    else:
        prices = available_real_prices(row)
        if len(prices) >= 2 and max(prices) != min(prices):
            lower_edge, upper_edge = min(prices), max(prices)
            source = "EPISODE_PRICE_RANGE"
        elif prices:
            center = prices[0]
            width = fallback_price_width(row, center)
            lower_edge, upper_edge = center - width / 2.0, center + width / 2.0
            source = "SINGLE_PRICE_WIDTH_ESTIMATE"
        else:
            lower_edge, upper_edge = 0.0, 1.0
            fallback_used = True
            source = "PLACEHOLDER_FALLBACK"

    zone_width = abs(upper_edge - lower_edge)
    mid_price = (upper_edge + lower_edge) / 2.0
    birth_price = first_price(row, ["start_price", "preparation_mid_price", "return_price", "end_price"])
    end_time = row.get("episode_end_time_utc")
    return {
        "real_zone_upper_edge": round_float(upper_edge),
        "real_zone_lower_edge": round_float(lower_edge),
        "real_zone_mid_price": round_float(mid_price),
        "real_zone_width": round_float(zone_width),
        "real_birth_price": round_float(birth_price if birth_price is not None else mid_price),
        "real_birth_time": row.get("episode_start_time_utc"),
        "real_zone_left_time": row.get("episode_start_time_utc"),
        "real_zone_right_time": row.get("return_timestamp") or end_time,
        "real_zone_end_time": end_time,
        "real_zone_lifetime": round_float(row.get("zone_age") or row.get("duration_seconds")),
        "real_zone_active_duration": round_float(row.get("duration_seconds")),
        "geometry_fallback_used": fallback_used,
        "geometry_source": source,
    }


def available_real_prices(row: pd.Series) -> List[float]:
    fields = [
        "start_price",
        "end_price",
        "return_price",
        "price_at_1m",
        "price_at_5m",
        "price_at_15m",
        "price_at_30m",
        "price_at_1h",
        "price_at_2h",
        "price_at_4h",
        "price_at_day_end",
    ]
    prices: List[float] = []
    for field in fields:
        price = to_float(row.get(field))
        if price is not None and price > 0:
            prices.append(price)
    return prices


def fallback_price_width(row: pd.Series, center: float) -> float:
    range_value = abs_number(row.get("pre_range_value")) or abs_number(row.get("pre_range"))
    if range_value:
        return max(range_value, center * 0.0001)
    return max(center * 0.001, 1.0)


def first_price(row: pd.Series, fields: List[str]) -> float | None:
    for field in fields:
        price = to_float(row.get(field))
        if price is not None and price > 0:
            return price
    return None


def mechanical_tracking_values(row: pd.Series, geometry: Dict[str, Any]) -> Dict[str, Any]:
    sigma_birth = to_float(row.get("sigma_barre_zone"))
    sigma_current = to_float(row.get("adaptive_sigma_barre_v2")) or sigma_birth
    sigma_return = to_float(row.get("sigma_market")) if truthy(row.get("return_to_preparation")) else None
    sigma_final = sigma_current

    capacity_birth = to_float(row.get("zone_moment_capacity"))
    capacity_current = to_float(row.get("regime_adjusted_capacity")) or capacity_birth
    capacity_return = capacity_current
    capacity_final = capacity_current

    rigidity_birth = to_float(row.get("initial_rigidity")) or to_float(row.get("zone_rigidity"))
    rigidity_current = to_float(row.get("zone_rigidity"))
    rigidity_return = rigidity_current
    rigidity_final = max((rigidity_current or 0.0) - (to_float(row.get("zone_strength_decay")) or 0.0) * 0.25, 0.0)

    resistance_birth = to_float(row.get("base_zone_resistance"))
    resistance_current = to_float(row.get("adaptive_sigma_barre_v2")) or resistance_birth
    resistance_return = resistance_current
    resistance_final = resistance_current

    fleche_birth = 0.0
    fleche_current = to_float(row.get("zone_fleche_ratio"))
    fleche_return = fleche_current if truthy(row.get("return_to_preparation")) else None
    fleche_final = fleche_current

    dynamic_fleche_birth = 0.0
    dynamic_fleche_current = to_float(row.get("fleche_verestchaguine"))
    dynamic_fleche_return = dynamic_fleche_current if truthy(row.get("return_to_preparation")) else None
    dynamic_fleche_final = dynamic_fleche_current

    moment_birth = 0.0
    moment_current = to_float(row.get("signed_moment_proxy"))
    moment_return = moment_current if truthy(row.get("return_to_preparation")) else None
    moment_final = moment_current

    load_birth = 0.0
    load_current = to_float(row.get("mechanical_load_score"))
    load_return = load_current if truthy(row.get("return_to_preparation")) else None
    load_final = load_current

    fatigue_birth = 0.0
    fatigue_current = to_float(row.get("fatigue_index"))
    fatigue_return = fatigue_current if truthy(row.get("return_to_preparation")) else None
    fatigue_final = fatigue_current

    recovery_birth = 0.0
    recovery_current = to_float(row.get("recovery_ratio"))
    recovery_return = recovery_current if truthy(row.get("return_to_preparation")) else None
    recovery_final = recovery_current

    health_current = to_float(row.get("rdm_health_score"))
    health_birth = min((health_current or 70.0) + 12.0, 100.0)
    health_return = health_current if truthy(row.get("return_to_preparation")) else None
    health_final = health_current

    return {
        "sigma_birth": round_float(sigma_birth),
        "capacity_birth": round_float(capacity_birth),
        "rigidity_birth": round_float(rigidity_birth),
        "resistance_birth": round_float(resistance_birth),
        "fleche_birth": round_float(fleche_birth),
        "dynamic_fleche_birth": round_float(dynamic_fleche_birth),
        "moment_birth": round_float(moment_birth),
        "load_birth": round_float(load_birth),
        "fatigue_birth": round_float(fatigue_birth),
        "recovery_birth": round_float(recovery_birth),
        "health_birth": round_float(health_birth),
        "sigma_current": round_float(sigma_current),
        "capacity_current": round_float(capacity_current),
        "rigidity_current": round_float(rigidity_current),
        "resistance_current": round_float(resistance_current),
        "fleche_current": round_float(fleche_current),
        "dynamic_fleche_current": round_float(dynamic_fleche_current),
        "moment_current": round_float(moment_current),
        "load_current": round_float(load_current),
        "fatigue_current": round_float(fatigue_current),
        "recovery_current": round_float(recovery_current),
        "health_current": round_float(health_current),
        "return_time": row.get("return_timestamp"),
        "return_price": round_float(row.get("return_price")),
        "sigma_at_return": round_float(sigma_return),
        "capacity_at_return": round_float(capacity_return),
        "rigidity_at_return": round_float(rigidity_return),
        "resistance_at_return": round_float(resistance_return),
        "fleche_at_return": round_float(fleche_return),
        "dynamic_fleche_at_return": round_float(dynamic_fleche_return),
        "moment_at_return": round_float(moment_return),
        "load_at_return": round_float(load_return),
        "fatigue_at_return": round_float(fatigue_return),
        "recovery_at_return": round_float(recovery_return),
        "health_at_return": round_float(health_return),
        "final_time": row.get("episode_end_time_utc"),
        "final_price": round_float(first_price(row, ["price_at_day_end", "end_price", "return_price"])),
        "sigma_final": round_float(sigma_final),
        "capacity_final": round_float(capacity_final),
        "rigidity_final": round_float(rigidity_final),
        "resistance_final": round_float(resistance_final),
        "fleche_final": round_float(fleche_final),
        "dynamic_fleche_final": round_float(dynamic_fleche_final),
        "moment_final": round_float(moment_final),
        "load_final": round_float(load_final),
        "fatigue_final": round_float(fatigue_final),
        "recovery_final": round_float(recovery_final),
        "health_final": round_float(health_final),
        "sigma_change_from_birth": round_float(change_from_birth(sigma_birth, sigma_current)),
        "capacity_change_from_birth": round_float(change_from_birth(capacity_birth, capacity_current)),
        "rigidity_change_from_birth": round_float(change_from_birth(rigidity_birth, rigidity_current)),
        "resistance_change_from_birth": round_float(change_from_birth(resistance_birth, resistance_current)),
        "fleche_change_from_birth": round_float(change_from_birth(fleche_birth, fleche_current)),
        "dynamic_fleche_change_from_birth": round_float(change_from_birth(dynamic_fleche_birth, dynamic_fleche_current)),
        "moment_change_from_birth": round_float(change_from_birth(moment_birth, moment_current)),
        "load_change_from_birth": round_float(change_from_birth(load_birth, load_current)),
        "fatigue_change_from_birth": round_float(change_from_birth(fatigue_birth, fatigue_current)),
        "recovery_change_from_birth": round_float(change_from_birth(recovery_birth, recovery_current)),
        "health_change_from_birth": round_float(change_from_birth(health_birth, health_current)),
    }


def mechanical_breach_flags(values: Dict[str, Any]) -> Dict[str, Any]:
    sigma_breach = compare_greater(values.get("sigma_at_return") or values.get("sigma_current"), values.get("sigma_birth"))
    capacity_breach = compare_greater(values.get("load_current"), values.get("capacity_birth"))
    rigidity_decay = compare_less(values.get("rigidity_current"), (to_float(values.get("rigidity_birth")) or 0.0) * 0.70)
    fatigue_breach = compare_greater(values.get("fatigue_current"), (to_float(values.get("fatigue_birth")) or 0.0) + 50.0)
    health_collapse = compare_less(values.get("health_current"), (to_float(values.get("health_birth")) or 0.0) - 30.0)
    flags = {
        "sigma_breach_flag": sigma_breach,
        "capacity_breach_flag": capacity_breach,
        "rigidity_decay_flag": rigidity_decay,
        "fatigue_breach_flag": fatigue_breach,
        "health_collapse_flag": health_collapse,
    }
    active = [name.replace("_flag", "").upper() for name, enabled in flags.items() if enabled]
    return {
        **flags,
        "mechanical_breach_count": len(active),
        "mechanical_breach_summary": "|".join(active),
    }


def change_from_birth(birth: Any, current: Any) -> float | None:
    birth_value = to_float(birth)
    current_value = to_float(current)
    if birth_value is None or current_value is None:
        return None
    return current_value - birth_value


def compare_greater(left: Any, right: Any) -> bool:
    left_value = to_float(left)
    right_value = to_float(right)
    if left_value is None or right_value is None:
        return False
    return left_value > right_value


def compare_less(left: Any, right: Any) -> bool:
    left_value = to_float(left)
    right_value = to_float(right)
    if left_value is None or right_value is None:
        return False
    return left_value < right_value


def build_live_rdm_evolution(results: pd.DataFrame, historical_rows: pd.DataFrame, run_utc: str) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame()
    if historical_rows.empty or "row_id" not in historical_rows.columns or "close" not in historical_rows.columns:
        return build_static_live_rdm_evolution(results, run_utc)

    rows_source = historical_rows.copy()
    rows_source["row_id_numeric"] = pd.to_numeric(rows_source["row_id"], errors="coerce")
    rows_source = rows_source.dropna(subset=["row_id_numeric"]).copy()
    rows_source = rows_source.sort_values("row_id_numeric").reset_index(drop=True)
    if rows_source.empty:
        return build_static_live_rdm_evolution(results, run_utc)

    row_ids = rows_source["row_id_numeric"].reset_index(drop=True)
    output_rows: List[Dict[str, Any]] = []
    for _, zone in results.iterrows():
        start_row, end_row = live_row_window(zone, rows_source)
        start_position = row_ids.searchsorted(start_row, side="left")
        end_position = row_ids.searchsorted(end_row, side="right")
        zone_rows = rows_source.iloc[int(start_position):int(end_position)].copy()
        if zone_rows.empty:
            output_rows.extend(build_static_live_rdm_evolution(pd.DataFrame([zone]), run_utc).to_dict("records"))
            continue
        output_rows.extend(live_evolution_rows_for_zone(zone, zone_rows, run_utc))

    return pd.DataFrame(output_rows)


def build_static_live_rdm_evolution(results: pd.DataFrame, run_utc: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for _, zone in results.iterrows():
        price = first_price(zone, ["final_price", "return_price", "real_birth_price"])
        record = live_evolution_record(
                zone=zone,
                row_index=zone.get("end_row_id") or zone.get("episode_id"),
                timestamp=zone.get("final_time") or zone.get("episode_end_time_utc"),
                price=price,
                source_row=pd.Series(dtype=object),
                run_utc=run_utc,
                breach_memory={},
        )
        rows.append(apply_live_rdm_guard(record, {}))
    return pd.DataFrame(rows)


def live_row_window(zone: pd.Series, rows_source: pd.DataFrame) -> tuple[float, float]:
    candidates_start = [
        to_float(zone.get("preparation_start_row")),
        to_float(zone.get("start_row_id")),
        to_float(zone.get("return_row")),
    ]
    candidates_end = [
        to_float(zone.get("end_row_id")),
        to_float(zone.get("return_row")),
        to_float(zone.get("preparation_end_row")),
    ]
    valid_start = [item for item in candidates_start if item is not None and item > 0]
    valid_end = [item for item in candidates_end if item is not None and item > 0]
    start = min(valid_start) if valid_start else float(rows_source["row_id_numeric"].min())
    end = max(valid_end) if valid_end else start + 120.0
    if end <= start:
        end = start + 120.0
    return start, end


def live_evolution_rows_for_zone(zone: pd.Series, zone_rows: pd.DataFrame, run_utc: str) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    breach_memory: Dict[str, bool] = {}
    guard_state: Dict[str, int] = {}
    for _, source_row in zone_rows.sort_values("row_id_numeric").iterrows():
        record = live_evolution_record(
            zone=zone,
            row_index=source_row.get("row_id"),
            timestamp=source_row.get("market_timestamp"),
            price=to_float(source_row.get("close")),
            source_row=source_row,
            run_utc=run_utc,
            breach_memory=breach_memory,
        )
        output.append(apply_live_rdm_guard(record, guard_state))
    return output


def live_evolution_record(
    zone: pd.Series,
    row_index: Any,
    timestamp: Any,
    price: Any,
    source_row: pd.Series,
    run_utc: str,
    breach_memory: Dict[str, bool],
) -> Dict[str, Any]:
    price_value = to_float(price) or to_float(zone.get("real_birth_price")) or 0.0
    upper = to_float(zone.get("real_zone_upper_edge")) or 0.0
    lower = to_float(zone.get("real_zone_lower_edge")) or 0.0
    width = max(to_float(zone.get("real_zone_width")) or abs(upper - lower), 1e-9)
    mid = (upper + lower) / 2.0
    inside = lower <= price_value <= upper if upper >= lower else False
    distance = 0.0 if inside else min(abs(price_value - lower), abs(price_value - upper))
    touch = inside or distance <= max(width * 0.05, max(price_value, 1.0) * 0.00005)
    return_row = to_float(zone.get("return_row"))
    row_number = to_float(row_index)
    return_to_zone = bool(touch and return_row is not None and row_number is not None and row_number >= return_row)

    sigma_birth = to_float(zone.get("sigma_birth")) or to_float(zone.get("sigma_barre_zone")) or 0.0
    capacity_birth = to_float(zone.get("capacity_birth")) or to_float(zone.get("zone_moment_capacity")) or 0.0
    rigidity_birth = to_float(zone.get("rigidity_birth")) or to_float(zone.get("zone_rigidity")) or 0.0
    health_birth = to_float(zone.get("health_birth")) or min((to_float(zone.get("rdm_health_score")) or 70.0) + 12.0, 100.0)

    active_load = inside or touch
    delta_zscore = abs_number(source_row.get("delta_zscore"))
    velocity_zscore = abs_number(source_row.get("velocity_zscore"))
    volume_zscore = abs_number(source_row.get("volume_zscore"))
    penetration = max(width / 2.0 - abs(price_value - mid), 0.0) if inside else 0.0
    fleche_live = safe_divide(penetration, width) if active_load else 0.0
    row_progress = live_row_progress(zone, row_number)
    regime_normalizer = live_regime_stress_normalizer(source_row, zone)
    stress_factor = min(((delta_zscore + velocity_zscore + volume_zscore) / 9.0) / regime_normalizer, 1.2) if active_load else 0.0
    sigma_live = sigma_birth * (1.0 + stress_factor * fleche_live) if active_load else sigma_birth
    recovery_base = to_float(zone.get("recovery_current")) or 0.0
    repair_effect = min(recovery_base, 2.0)
    capacity_live = max(capacity_birth - row_progress * (to_float(zone.get("zone_strength_decay")) or 0.0) * 0.08 + repair_effect * 10.0, 0.0)
    rigidity_live = max(rigidity_birth - row_progress * (to_float(zone.get("zone_strength_decay")) or 0.0) * 0.55 + repair_effect * 8.0, 0.0)
    dynamic_fleche_live = fleche_live * (1.0 + row_progress * 0.25)
    moment_live = (delta_zscore if direction_from_signed(source_row.get("delta_zscore")) != "DOWN" else -delta_zscore) * penetration if active_load else 0.0
    load_live = min(fleche_live * 35.0 + stress_factor * 25.0, 100.0) if active_load else 0.0
    stress_activity = min(stress_factor + fleche_live, 1.0) if active_load else 0.0
    recovery_live = recovery_base * row_progress if active_load else 0.0
    fatigue_live = min(
        max(
            (to_float(zone.get("fatigue_birth")) or 0.0)
            + row_progress * (to_float(zone.get("fatigue_current")) or 0.0) * stress_activity
            - recovery_live * 22.0,
            0.0,
        ),
        100.0,
    )
    health_live = max(health_birth - fatigue_live * 0.18 - max(load_live - 50.0, 0.0) * 0.12 + recovery_live * 12.0, 0.0)

    sigma_status = live_sigma_status(sigma_live, sigma_birth, breach_memory)
    capacity_status = live_capacity_status(capacity_live, capacity_birth, load_live, breach_memory)
    rigidity_status = live_rigidity_status(rigidity_live, rigidity_birth, breach_memory)
    fleche_status = live_fleche_status(fleche_live)
    health_status = live_health_status(health_live, health_birth, breach_memory)
    breach_items = [
        item
        for item, status in {
            "SIGMA": sigma_status,
            "CAPACITY": capacity_status,
            "RIGIDITY": rigidity_status,
            "HEALTH": health_status,
        }.items()
        if status in {"BREACHED", "DECAYED", "COLLAPSED"}
    ]
    stored_breach_items = sorted(key.upper() for key, enabled in breach_memory.items() if enabled)
    live_status, live_risk, live_reason, watch_action = live_rdm_summary(
        active_load=active_load,
        breach_count=len(breach_items),
        fatigue_live=fatigue_live,
        recovery_live=recovery_live,
        health_live=health_live,
    )
    evolution_step, transition, state = live_evolution_state(
        inside=inside,
        touch=touch,
        breach_count=len(breach_items),
        recovery_live=recovery_live,
        fatigue_live=fatigue_live,
    )

    return {
        "analysis_run_utc": run_utc,
        "zone_id": zone_identifier(zone),
        "case_id": zone.get("case_id"),
        "episode_id": zone.get("episode_id"),
        "row_index": row_index,
        "timestamp": timestamp,
        "price": round_float(price_value),
        "real_zone_upper_edge": round_float(upper),
        "real_zone_lower_edge": round_float(lower),
        "real_zone_width": round_float(width),
        "inside_zone_flag": inside,
        "distance_to_zone": round_float(distance),
        "zone_touch_flag": touch,
        "return_to_zone_flag": return_to_zone,
        "sigma_birth": round_float(sigma_birth),
        "sigma_live": round_float(sigma_live),
        "sigma_change_from_birth": round_float(change_from_birth(sigma_birth, sigma_live)),
        "sigma_live_status": sigma_status,
        "capacity_birth": round_float(capacity_birth),
        "capacity_live": round_float(capacity_live),
        "capacity_change_from_birth": round_float(change_from_birth(capacity_birth, capacity_live)),
        "capacity_live_status": capacity_status,
        "rigidity_birth": round_float(rigidity_birth),
        "rigidity_live": round_float(rigidity_live),
        "rigidity_change_from_birth": round_float(change_from_birth(rigidity_birth, rigidity_live)),
        "rigidity_live_status": rigidity_status,
        "fleche_birth": round_float(zone.get("fleche_birth")),
        "fleche_live": round_float(fleche_live),
        "dynamic_fleche_live": round_float(dynamic_fleche_live),
        "fleche_live_status": fleche_status,
        "moment_live": round_float(moment_live),
        "load_live": round_float(load_live),
        "fatigue_live": round_float(fatigue_live),
        "recovery_live": round_float(recovery_live),
        "health_live": round_float(health_live),
        "health_live_status": health_status,
        "mechanical_breach_count_live": len(stored_breach_items),
        "mechanical_breach_summary_live": "|".join(stored_breach_items),
        "raw_live_status": live_status,
        "guarded_live_status": live_status,
        "rdm_live_status": live_status,
        "rdm_live_risk": live_risk,
        "rdm_live_reason": live_reason,
        "rdm_live_watch_action": watch_action,
        "evolution_step": evolution_step,
        "evolution_transition": transition,
        "evolution_state": state,
        "research_only": True,
    }


def merge_live_rdm_evolution_into_results(results: pd.DataFrame, live: pd.DataFrame) -> pd.DataFrame:
    if results.empty or live.empty or "case_id" not in live.columns:
        return results
    latest = live.sort_values(["case_id", "row_index"]).groupby("case_id", as_index=False).tail(1)
    live_columns = [
        column
        for column in latest.columns
        if column not in {"analysis_run_utc", "research_only", "zone_id", "episode_id", "case_id"}
    ]
    return results.merge(latest[["case_id", *live_columns]], on="case_id", how="left", suffixes=("", "_live"))


def live_regime_stress_normalizer(source_row: pd.Series, zone: pd.Series) -> float:
    regime_text = " ".join(
        str(value or "")
        for value in [
            source_row.get("volatility_regime"),
            source_row.get("velocity_state"),
            source_row.get("volume_state"),
            zone.get("mechanical_regime_context"),
        ]
    ).upper()
    if "RECOVERY" in regime_text:
        return 1.45
    if "EXTREME" in regime_text:
        return 1.80
    if "HIGH" in regime_text or "EXPANSION" in regime_text or "SHOCK" in regime_text:
        return 1.55
    if "LOW" in regime_text or "COMPRESSION" in regime_text or "QUIET" in regime_text:
        return 0.95
    return 1.25


def apply_live_rdm_guard(record: Dict[str, Any], state: Dict[str, int]) -> Dict[str, Any]:
    inside = truthy(record.get("inside_zone_flag"))
    raw_status = str(record.get("raw_live_status") or record.get("rdm_live_status") or "LIVE_SAFE")
    sigma_confirmed = str(record.get("sigma_live_status") or "") == "BREACHED"
    capacity_confirmed = str(record.get("capacity_live_status") or "") == "BREACHED"
    health_confirmed = str(record.get("health_live_status") or "") == "COLLAPSED"
    fatigue_confirmed = (to_float(record.get("fatigue_live")) or 0.0) >= 85.0
    current_factor_count = sum(
        [sigma_confirmed, capacity_confirmed, health_confirmed, fatigue_confirmed]
    )
    current_breach = current_factor_count > 0
    current_rupture = current_factor_count >= 2
    current_recovery = raw_status == "LIVE_RECOVERY"
    current_stress = inside and (
        current_breach
        or (to_float(record.get("load_live")) or 0.0) > 0.0
        or (to_float(record.get("fatigue_live")) or 0.0) > 0.0
    )

    state["inside"] = state.get("inside", 0) + 1 if inside else 0
    state["breach"] = state.get("breach", 0) + 1 if inside and current_breach else 0
    state["rupture"] = state.get("rupture", 0) + 1 if inside and current_rupture else 0
    state["recovery"] = state.get("recovery", 0) + 1 if inside and current_recovery else 0
    state["stress"] = state.get("stress", 0) + 1 if current_stress else 0

    breach_streak = state["breach"]
    rupture_streak = state["rupture"]
    confirmation_score = current_factor_count
    multi_factor = confirmation_score >= 2
    guarded_status = raw_status
    guard_applied = False
    guard_reason = "NO_GUARD_NEEDED"

    if not inside:
        guarded_status = live_outside_zone_status(record)
        guard_applied = raw_status in {"LIVE_BREACH", "LIVE_RUPTURE"}
        guard_reason = "OUTSIDE_ZONE_NO_RUPTURE"
    elif rupture_streak >= 5 and breach_streak >= 5 and multi_factor and (health_confirmed or fatigue_confirmed):
        guarded_status = "LIVE_RUPTURE"
        guard_reason = "PERSISTENT_STRUCTURAL_FAILURE_CONFIRMED"
    elif breach_streak >= 3 and confirmation_score >= 1:
        guarded_status = "LIVE_BREACH"
        if raw_status == "LIVE_RUPTURE":
            guard_applied = True
            guard_reason = "RUPTURE_REQUIRES_THREE_ROW_MULTI_FACTOR_CONFIRMATION"
        else:
            guard_reason = "PERSISTENT_CONFIRMED_BREACH"
    elif current_breach:
        guarded_status = "LIVE_WARNING"
        guard_applied = raw_status in {"LIVE_BREACH", "LIVE_RUPTURE"}
        guard_reason = "SINGLE_ROW_BREACH_DOWNGRADED_TO_WARNING"
    elif fatigue_confirmed and state["stress"] >= 3:
        guarded_status = "LIVE_FATIGUE"
        guard_reason = "FATIGUE_WITHOUT_CONFIRMED_BREACH"
    elif current_recovery or state.get("recovery", 0) >= 2:
        guarded_status = "LIVE_RECOVERY"
        guard_reason = "RECOVERY_AFTER_STRESS"
    elif inside:
        guarded_status = "LIVE_SAFE"
        guard_reason = "INSIDE_ZONE_WITHOUT_CONFIRMED_BREACH"

    risk, reason, action = guarded_live_outcome(
        guarded_status=guarded_status,
        guard_reason=guard_reason,
        confirmation_score=confirmation_score,
    )
    record.update(
        {
            "live_breach_streak": breach_streak,
            "live_rupture_streak": rupture_streak,
            "live_inside_zone_streak": state["inside"],
            "live_recovery_streak": state["recovery"],
            "live_stress_persistence": state["stress"],
            "sigma_confirmed_breach": sigma_confirmed and breach_streak >= 2,
            "capacity_confirmed_breach": capacity_confirmed and breach_streak >= 2,
            "health_confirmed_collapse": health_confirmed and breach_streak >= 2,
            "fatigue_confirmed_high": fatigue_confirmed and state["stress"] >= 3,
            "multi_factor_breach_confirmed": multi_factor and breach_streak >= 3,
            "live_guard_applied": guard_applied,
            "live_guard_reason": guard_reason,
            "raw_live_status": raw_status,
            "guarded_live_status": guarded_status,
            "live_confirmation_score": confirmation_score,
            "rdm_live_status": guarded_status,
            "rdm_live_risk": risk,
            "rdm_live_reason": reason,
            "rdm_live_watch_action": action,
        }
    )
    return record


def live_outside_zone_status(record: Dict[str, Any]) -> str:
    distance = to_float(record.get("distance_to_zone")) or 0.0
    width = to_float(record.get("real_zone_width")) or 1.0
    if distance > width:
        return "LIVE_AGING"
    if distance > 0:
        return "LIVE_DORMANT"
    return "LIVE_SAFE"


def guarded_live_outcome(guarded_status: str, guard_reason: str, confirmation_score: int) -> tuple[str, str, str]:
    if guarded_status == "LIVE_RUPTURE":
        return "CRITICAL", "Guard confirmed persistent multi-factor live rupture context.", "REVIEW_LIVE_BREACH_CONTEXT"
    if guarded_status == "LIVE_BREACH":
        return "HIGH", "Guard confirmed persistent live breach context.", "WATCH_LIVE_BREACH"
    if guarded_status == "LIVE_WARNING":
        return "MEDIUM", "Single-row breach was downgraded to warning by persistence guard.", "MONITOR_MECHANICAL_CONTEXT"
    if guarded_status == "LIVE_FATIGUE":
        return "HIGH", "Live fatigue is persistent without rupture confirmation.", "WATCH_FATIGUE_DECAY"
    if guarded_status == "LIVE_RECOVERY":
        return "MEDIUM", "Live recovery is present after stress context.", "REVIEW_RECOVERY_BEHAVIOR"
    if guarded_status == "LIVE_AGING":
        return "LOW", "Price is outside zone; only aging context is tracked.", "WAIT_FOR_ACTIVE_LOAD"
    if guarded_status == "LIVE_DORMANT":
        return "LOW", "Price is near/outside the zone; active load is not confirmed.", "WAIT_FOR_ACTIVE_LOAD"
    return "LOW", f"Live guard state is stable ({guard_reason}, confirmations={confirmation_score}).", "OBSERVE_ONLY"


def live_row_progress(zone: pd.Series, row_number: float | None) -> float:
    start = to_float(zone.get("preparation_start_row")) or to_float(zone.get("start_row_id")) or row_number or 0.0
    end = to_float(zone.get("end_row_id")) or to_float(zone.get("return_row")) or start + 1.0
    if row_number is None or end <= start:
        return 1.0
    return max(min((row_number - start) / (end - start), 1.0), 0.0)


def live_sigma_status(value: float, birth: float, memory: Dict[str, bool]) -> str:
    breached = birth > 0 and value > birth * 1.15
    if breached:
        memory["sigma"] = True
    return "BREACHED" if breached else "LIVE_SAFE"


def live_capacity_status(capacity_live: float, capacity_birth: float, load_live: float, memory: Dict[str, bool]) -> str:
    breached = capacity_birth > 0 and (capacity_live < capacity_birth * 0.55 or load_live > capacity_birth * 1.35)
    if breached:
        memory["capacity"] = True
    if breached:
        return "BREACHED"
    if capacity_birth > 0 and capacity_live < capacity_birth * 0.75:
        return "DECAYED"
    return "LIVE_SAFE"


def live_rigidity_status(rigidity_live: float, rigidity_birth: float, memory: Dict[str, bool]) -> str:
    decayed = rigidity_birth > 0 and rigidity_live < rigidity_birth * 0.55
    if decayed:
        memory["rigidity"] = True
    return "DECAYED" if decayed else "LIVE_SAFE"


def live_fleche_status(fleche_live: float) -> str:
    if fleche_live >= 1.0:
        return "BREACHED"
    if fleche_live >= 0.60:
        return "LIVE_WARNING"
    return "LIVE_SAFE"


def live_health_status(health_live: float, health_birth: float, memory: Dict[str, bool]) -> str:
    collapsed = health_birth > 0 and health_live < health_birth - 45.0
    if collapsed:
        memory["health"] = True
    return "COLLAPSED" if collapsed else "LIVE_SAFE"


def live_rdm_summary(active_load: bool, breach_count: int, fatigue_live: float, recovery_live: float, health_live: float) -> tuple[str, str, str, str]:
    if not active_load:
        return "LIVE_DORMANT", "LOW", "Price is outside the zone; no active mechanical load.", "WAIT_FOR_ACTIVE_LOAD"
    if breach_count >= 3 and fatigue_live >= 85 and health_live < 35:
        return "LIVE_RUPTURE", "CRITICAL", "Multiple live mechanical breach conditions are active.", "REVIEW_LIVE_BREACH_CONTEXT"
    if breach_count == 1:
        return "LIVE_BREACH", "HIGH", "One live mechanical baseline is breached.", "WATCH_LIVE_BREACH"
    if fatigue_live >= 85:
        return "LIVE_FATIGUE", "HIGH", "Live fatigue is elevated while the zone is active.", "WATCH_FATIGUE_DECAY"
    if recovery_live > 0 and health_live >= 55:
        return "LIVE_RECOVERY", "MEDIUM", "Live recovery is improving the zone context.", "REVIEW_RECOVERY_BEHAVIOR"
    return "LIVE_SAFE", "LOW", "Live mechanics remain inside research-safe context.", "OBSERVE_ONLY"


def live_evolution_state(inside: bool, touch: bool, breach_count: int, recovery_live: float, fatigue_live: float) -> tuple[str, str, str]:
    if breach_count >= 2:
        return "BREACH", "STRESS_TO_BREACH", "LIVE_RUPTURE"
    if recovery_live > 0:
        return "RECOVERY", "STRESS_TO_RECOVERY", "LIVE_RECOVERY"
    if fatigue_live >= 70:
        return "STRESS", "TO_FATIGUE", "LIVE_FATIGUE"
    if inside:
        return "CURRENT", "TO_ACTIVE_LOAD", "LIVE_ACTIVE"
    if touch:
        return "RETURN", "TO_ZONE_TOUCH", "LIVE_TOUCH"
    return "CURRENT", "AGING_OUTSIDE_ZONE", "LIVE_DORMANT"


def build_live_rdm_evolution_notes(live: pd.DataFrame, run_utc: str) -> str:
    status_counts = Counter(live["rdm_live_status"].dropna().astype(str)) if not live.empty and "rdm_live_status" in live.columns else Counter()
    raw_status_counts = Counter(live["raw_live_status"].dropna().astype(str)) if not live.empty and "raw_live_status" in live.columns else Counter()
    breach_counts = Counter(live["mechanical_breach_count_live"].dropna().astype(str)) if not live.empty and "mechanical_breach_count_live" in live.columns else Counter()
    guard_count = int(live["live_guard_applied"].astype(str).str.upper().isin(["TRUE", "1"]).sum()) if not live.empty and "live_guard_applied" in live.columns else 0
    lines = [
        "# Zone Live RDM Evolution",
        "",
        f"Run UTC: {run_utc}",
        "",
        "Research-only live-style replay timeline. No live execution, no scoring changes, and no signals.",
        "",
        f"Rows: {len(live)}",
        f"Guard applied rows: {guard_count}",
        "",
        "## Raw Live Status Counts",
        "",
    ]
    lines.extend(f"- {status}: {count}" for status, count in raw_status_counts.items())
    lines.extend([
        "",
        "## Guarded Live Status Counts",
        "",
    ])
    lines.extend(f"- {status}: {count}" for status, count in status_counts.items())
    lines.extend(["", "## Live Breach Counts", ""])
    lines.extend(f"- {count_value}: {count}" for count_value, count in breach_counts.items())
    return "\n".join(lines) + "\n"


class RdmCaseCache:
    def __init__(self, live: pd.DataFrame) -> None:
        self.live = live
        self.live_by_case = {
            str(case_id): group.copy()
            for case_id, group in live.groupby("case_id")
        } if not live.empty and "case_id" in live.columns else {}
        self.base_masks: Dict[str, pd.Series] = {}
        self.temporal_windows: Dict[str, pd.DataFrame] = {}
        self.lifecycle_rows: Dict[str, pd.DataFrame] = {}
        self.mask_reuse_count = 0

    @property
    def case_count(self) -> int:
        return len(self.live_by_case)

    def precompute_interaction_masks(self) -> None:
        for case_id in self.live_by_case:
            self.base_interaction_mask(case_id)

    def case_live(self, case_id: Any) -> pd.DataFrame:
        return self.live_by_case.get(str(case_id or ""), pd.DataFrame())

    def base_interaction_mask(self, case_id: Any) -> pd.Series:
        key = str(case_id or "")
        if key in self.base_masks:
            self.mask_reuse_count += 1
            return self.base_masks[key]
        live = self.case_live(key)
        if live.empty:
            mask = pd.Series(False, index=live.index)
        else:
            mask = base_interaction_mask(live)
        self.base_masks[key] = mask
        return mask

    def temporal_interaction_window(self, case_id: Any, max_rows: int = 30) -> pd.DataFrame:
        key = str(case_id or "")
        if key in self.temporal_windows:
            return self.temporal_windows[key]
        live = self.case_live(key)
        window = temporal_interaction_window(
            live,
            max_rows=max_rows,
            interaction_mask=self.base_interaction_mask(key),
        )
        self.temporal_windows[key] = window
        return window

    def lifecycle_interaction_rows(self, case_id: Any) -> pd.DataFrame:
        key = str(case_id or "")
        if key in self.lifecycle_rows:
            return self.lifecycle_rows[key]
        case_live = self.case_live(key)
        if case_live.empty:
            rows = pd.DataFrame()
        else:
            rows = case_live[
                case_live.get("inside_zone_flag", pd.Series(False, index=case_live.index)).astype(str).str.upper().isin(["TRUE", "1"])
                | case_live.get("zone_touch_flag", pd.Series(False, index=case_live.index)).astype(str).str.upper().isin(["TRUE", "1"])
                | case_live.get("mechanical_breach_summary_live", pd.Series("", index=case_live.index)).fillna("").astype(str).str.strip().ne("")
            ]
        self.lifecycle_rows[key] = rows
        return rows


def build_interaction_core_geometry(
    results: pd.DataFrame,
    live: pd.DataFrame,
    run_utc: str,
    case_cache: RdmCaseCache | None = None,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    cache = case_cache or RdmCaseCache(live)

    for _, row in results.iterrows():
        case_id = str(row.get("case_id") or "")
        formation_lower = to_float(row.get("real_zone_lower_edge")) or 0.0
        formation_upper = to_float(row.get("real_zone_upper_edge")) or 0.0
        formation_width = max(to_float(row.get("real_zone_width")) or abs(formation_upper - formation_lower), 1e-9)
        formation_mid = (formation_upper + formation_lower) / 2.0
        temporal_live = cache.temporal_interaction_window(case_id)
        interaction_points = interaction_core_points(
            temporal_live,
            formation_lower=formation_lower,
            formation_upper=formation_upper,
            formation_width=formation_width,
        )
        temporal_rows = len(temporal_live)

        if len(interaction_points) >= 3:
            point_lower = min(interaction_points)
            point_upper = max(interaction_points)
            point_width = max(point_upper - point_lower, 0.0)
            margin = max(point_width * 0.10, 5.0)
            raw_lower = point_lower - margin
            raw_upper = point_upper + margin
            source = "LIVE_INTERACTION_POINTS"
            valid = True
        else:
            fallback_width = min(formation_width * 0.25, max(50.0, formation_width * 0.10))
            center = to_float(row.get("real_birth_price")) or formation_mid
            raw_lower = center - fallback_width / 2.0
            raw_upper = center + fallback_width / 2.0
            margin = fallback_width / 2.0
            source = "FALLBACK_ADAPTIVE_CORE"
            valid = False

        raw_width = max(raw_upper - raw_lower, 0.0)
        clamped_lower = max(raw_lower, formation_lower)
        clamped_upper = min(raw_upper, formation_upper)
        if clamped_upper < clamped_lower:
            clamped_lower, clamped_upper = adaptive_core_bounds(row, formation_lower, formation_upper, formation_width, formation_mid)
        clamped_width = max(clamped_upper - clamped_lower, 0.0)
        clamp_applied = clamped_lower != raw_lower or clamped_upper != raw_upper
        clamp_reason = "CLAMPED_TO_FORMATION_RANGE" if clamp_applied else "NO_CLAMP_NEEDED"

        weighted_center = interaction_weighted_center(interaction_points, row, formation_mid)
        compression_applied = False
        compression_reason = "NO_COMPRESSION_NEEDED"
        compressed_width = clamped_width
        core_lower, core_upper = clamped_lower, clamped_upper
        if safe_divide(clamped_width, formation_width) > 0.50:
            compression_applied = True
            compression_reason = "CORE_WIDTH_ABOVE_HALF_FORMATION"
            compressed_width = min(clamped_width, formation_width * 0.25)
            core_lower = weighted_center - compressed_width / 2.0
            core_upper = weighted_center + compressed_width / 2.0
            core_lower = max(core_lower, formation_lower)
            core_upper = min(core_upper, formation_upper)
            compressed_width = max(core_upper - core_lower, 0.0)

        core_width = max(core_upper - core_lower, 0.0)
        efficiency = safe_divide(core_width, formation_width)
        if efficiency > 1.0:
            core_lower, core_upper = adaptive_core_bounds(row, formation_lower, formation_upper, formation_width, formation_mid)
            core_width = max(core_upper - core_lower, 0.0)
            efficiency = safe_divide(core_width, formation_width)
            source = "FALLBACK_ADAPTIVE_CORE"
            valid = False
            compression_applied = True
            compression_reason = "INVALID_TOO_WIDE_FALLBACK"

        rows.append(
            {
                "analysis_run_utc": run_utc,
                "case_id": row.get("case_id"),
                "episode_id": row.get("episode_id"),
                "zone_id": zone_identifier(row),
                "formation_upper_edge": round_float(formation_upper),
                "formation_lower_edge": round_float(formation_lower),
                "formation_mid_price": round_float(formation_mid),
                "formation_width": round_float(formation_width),
                "raw_interaction_core_upper_edge": round_float(raw_upper),
                "raw_interaction_core_lower_edge": round_float(raw_lower),
                "raw_interaction_core_width": round_float(raw_width),
                "clamped_interaction_core_upper_edge": round_float(clamped_upper),
                "clamped_interaction_core_lower_edge": round_float(clamped_lower),
                "clamped_interaction_core_width": round_float(clamped_width),
                "core_spatial_clamp_applied": clamp_applied,
                "core_spatial_clamp_reason": clamp_reason,
                "core_temporal_window_start": row.get("real_birth_time") or row.get("episode_start_time_utc"),
                "core_temporal_window_end": temporal_window_end(temporal_live),
                "core_temporal_window_seconds": round_float(temporal_window_seconds(temporal_live)),
                "core_temporal_window_rows": temporal_rows,
                "core_temporal_filter_applied": True,
                "interaction_core_weighted_center": round_float(weighted_center),
                "interaction_core_compression_applied": compression_applied,
                "interaction_core_compression_reason": compression_reason,
                "interaction_core_compressed_width": round_float(compressed_width),
                "interaction_core_upper_edge": round_float(core_upper),
                "interaction_core_lower_edge": round_float(core_lower),
                "interaction_core_mid_price": round_float((core_upper + core_lower) / 2.0),
                "interaction_core_width": round_float(core_width),
                "interaction_core_efficiency_ratio": round_float(efficiency),
                "interaction_core_source": source,
                "interaction_core_points_count": len(interaction_points),
                "interaction_core_valid_flag": valid,
                "interaction_core_margin": round_float(margin),
                "interaction_core_width_state": interaction_core_width_state(efficiency, source),
                "research_only": True,
            }
        )

    return pd.DataFrame(rows)


def temporal_interaction_window(
    live: pd.DataFrame,
    max_rows: int = 30,
    interaction_mask: pd.Series | None = None,
) -> pd.DataFrame:
    if live.empty:
        return live
    rows = live.copy()
    if "row_index" in rows.columns:
        rows = rows.sort_values("row_index")
    if interaction_mask is None:
        interaction_mask = base_interaction_mask(rows)
    else:
        interaction_mask = interaction_mask.reindex(rows.index, fill_value=False)
    interaction_rows = rows[interaction_mask].copy()
    if interaction_rows.empty:
        return rows.head(max_rows).copy()
    first_position = rows.index.get_loc(interaction_rows.index[0])
    return rows.iloc[first_position : first_position + max_rows].copy()


def base_interaction_mask(rows: pd.DataFrame) -> pd.Series:
    text_status = (
        rows.get("guarded_live_status", pd.Series("", index=rows.index)).astype(str)
        + "|"
        + rows.get("rdm_live_status", pd.Series("", index=rows.index)).astype(str)
    )
    breach_text = rows.get("mechanical_breach_summary_live", pd.Series("", index=rows.index)).fillna("").astype(str)
    return (
        rows.get("inside_zone_flag", pd.Series(False, index=rows.index)).astype(str).str.upper().isin(["TRUE", "1"])
        | rows.get("zone_touch_flag", pd.Series(False, index=rows.index)).astype(str).str.upper().isin(["TRUE", "1"])
        | rows.get("return_to_zone_flag", pd.Series(False, index=rows.index)).astype(str).str.upper().isin(["TRUE", "1"])
        | text_status.str.contains("LIVE_BREACH|LIVE_WARNING|LIVE_RECOVERY|LIVE_FATIGUE", regex=True)
        | (breach_text.str.strip().ne("") & breach_text.str.upper().ne("NONE"))
        | (pd.to_numeric(rows.get("recovery_live", 0), errors="coerce").fillna(0) > 0)
        | (pd.to_numeric(rows.get("fatigue_live", 0), errors="coerce").fillna(0).diff().abs().fillna(0) > 10)
        | (pd.to_numeric(rows.get("load_live", 0), errors="coerce").fillna(0) > 0)
    )


def interaction_core_points(
    live: pd.DataFrame,
    formation_lower: float,
    formation_upper: float,
    formation_width: float,
) -> List[float]:
    if live.empty or "price" not in live.columns:
        return []
    rows = live.copy()
    near_lower = formation_lower - formation_width * 0.10
    near_upper = formation_upper + formation_width * 0.10
    prices = pd.to_numeric(rows["price"], errors="coerce")
    near_formation = prices.between(near_lower, near_upper)
    stress_inside = (pd.to_numeric(rows.get("load_live", 0), errors="coerce").fillna(0) > 0) & prices.between(formation_lower, formation_upper)
    mask = (base_interaction_mask(rows) | stress_inside) & near_formation
    return pd.to_numeric(rows.loc[mask, "price"], errors="coerce").dropna().astype(float).tolist()


def interaction_weighted_center(points: List[float], row: pd.Series, formation_mid: float) -> float:
    if points:
        series = pd.Series(points)
        return float(series.median())
    return to_float(row.get("real_birth_price")) or formation_mid


def adaptive_core_bounds(row: pd.Series, formation_lower: float, formation_upper: float, formation_width: float, formation_mid: float) -> tuple[float, float]:
    fallback_width = min(formation_width * 0.25, max(50.0, formation_width * 0.10))
    center = to_float(row.get("real_birth_price")) or formation_mid
    lower = max(center - fallback_width / 2.0, formation_lower)
    upper = min(center + fallback_width / 2.0, formation_upper)
    return lower, upper


def temporal_window_end(rows: pd.DataFrame) -> Any:
    if rows.empty or "timestamp" not in rows.columns:
        return ""
    return rows.tail(1).iloc[0].get("timestamp")


def temporal_window_seconds(rows: pd.DataFrame) -> float | None:
    if rows.empty or "timestamp" not in rows.columns:
        return None
    start = to_float(rows.head(1).iloc[0].get("timestamp"))
    end = to_float(rows.tail(1).iloc[0].get("timestamp"))
    if start is None or end is None:
        return None
    return max((end - start) / 1000.0, 0.0)


def interaction_core_width_state(ratio: float, source: str) -> str:
    if ratio > 1.0:
        return "CORE_INVALID_TOO_WIDE"
    if source == "FALLBACK_ADAPTIVE_CORE":
        return "CORE_FALLBACK"
    if ratio <= 0.25:
        return "CORE_TIGHT"
    if ratio <= 0.50:
        return "CORE_NORMAL"
    if ratio <= 0.80:
        return "CORE_WIDE"
    return "CORE_TOO_WIDE"


def merge_interaction_core_into_results(results: pd.DataFrame, core: pd.DataFrame) -> pd.DataFrame:
    if results.empty or core.empty:
        return results
    columns = [column for column in core.columns if column not in {"analysis_run_utc", "research_only", "zone_id"}]
    return results.merge(core[columns], on=["case_id", "episode_id"], how="left")


def build_interaction_density_map(
    results: pd.DataFrame,
    live: pd.DataFrame,
    run_utc: str,
    case_cache: RdmCaseCache | None = None,
) -> pd.DataFrame:
    cache = case_cache or RdmCaseCache(live)
    rows: List[Dict[str, Any]] = []

    for _, row in results.iterrows():
        case_id = str(row.get("case_id") or "")
        case_live = cache.case_live(case_id)
        density = interaction_density_for_row(row, case_live)
        rows.append(
            {
                "analysis_run_utc": run_utc,
                "case_id": row.get("case_id"),
                "episode_id": row.get("episode_id"),
                "zone_id": zone_identifier(row),
                **density,
                "research_only": True,
            }
        )

    return pd.DataFrame(rows)


def interaction_density_for_row(row: pd.Series, live: pd.DataFrame, bucket_count: int = 7) -> Dict[str, Any]:
    lower = to_float(row.get("interaction_core_lower_edge"))
    upper = to_float(row.get("interaction_core_upper_edge"))
    if lower is None or upper is None or upper <= lower or live.empty:
        return empty_density_result(row)

    zone_rows = live.copy()
    zone_rows["price_numeric"] = pd.to_numeric(zone_rows.get("price"), errors="coerce")
    zone_rows = zone_rows[
        (zone_rows["price_numeric"] >= lower)
        & (zone_rows["price_numeric"] <= upper)
    ].copy()
    if zone_rows.empty:
        return empty_density_result(row)

    zone_rows["density_weight"] = zone_rows.apply(interaction_density_weight, axis=1)
    zone_rows = zone_rows[zone_rows["density_weight"] > 0].copy()
    if zone_rows.empty:
        return empty_density_result(row)

    weighted_center = safe_divide(
        (zone_rows["price_numeric"] * zone_rows["density_weight"]).sum(),
        zone_rows["density_weight"].sum(),
    )
    peak_row = zone_rows.sort_values("density_weight", ascending=False).iloc[0]
    peak_price = to_float(peak_row.get("price_numeric")) or weighted_center
    bucket_edges = density_bucket_edges(lower, upper, bucket_count)
    bucket_scores = density_bucket_scores(zone_rows, bucket_edges)
    dominant_indexes = dominant_density_indexes(bucket_scores)
    band_lower = bucket_edges[min(dominant_indexes)]
    band_upper = bucket_edges[max(dominant_indexes) + 1]
    density_width = max(band_upper - band_lower, 0.0)
    efficiency = safe_divide(density_width, upper - lower)
    upper_score, middle_score, lower_score = density_band_scores(bucket_scores)
    dominant_location = dominant_density_location(bucket_scores)
    density_score = float(sum(bucket_scores))

    return {
        "interaction_density_score": round_float(density_score),
        "interaction_density_state": interaction_density_state(density_score, len(zone_rows)),
        "interaction_density_peak_price": round_float(peak_price),
        "interaction_density_weighted_center": round_float(weighted_center),
        "interaction_density_upper_band": round_float(band_upper),
        "interaction_density_lower_band": round_float(band_lower),
        "interaction_density_width": round_float(density_width),
        "interaction_density_efficiency_ratio": round_float(efficiency),
        "interaction_density_points_count": len(zone_rows),
        "core_upper_density_score": round_float(upper_score),
        "core_middle_density_score": round_float(middle_score),
        "core_lower_density_score": round_float(lower_score),
        "dominant_interaction_band": dominant_location,
        "dominant_interaction_location": dominant_location,
    }


def empty_density_result(row: pd.Series) -> Dict[str, Any]:
    lower = to_float(row.get("interaction_core_lower_edge")) or 0.0
    upper = to_float(row.get("interaction_core_upper_edge")) or lower
    mid = (upper + lower) / 2.0
    return {
        "interaction_density_score": 0.0,
        "interaction_density_state": "LOW_DENSITY",
        "interaction_density_peak_price": round_float(mid),
        "interaction_density_weighted_center": round_float(mid),
        "interaction_density_upper_band": round_float(upper),
        "interaction_density_lower_band": round_float(lower),
        "interaction_density_width": round_float(max(upper - lower, 0.0)),
        "interaction_density_efficiency_ratio": 1.0 if upper > lower else 0.0,
        "interaction_density_points_count": 0,
        "core_upper_density_score": 0.0,
        "core_middle_density_score": 0.0,
        "core_lower_density_score": 0.0,
        "dominant_interaction_band": "NO_CLEAR_DENSITY",
        "dominant_interaction_location": "NO_CLEAR_DENSITY",
    }


def interaction_density_weight(row: pd.Series) -> float:
    weight = 1.0
    if truthy(row.get("zone_touch_flag")):
        weight += 1.0
    if truthy(row.get("return_to_zone_flag")):
        weight += 1.25
    if str(row.get("guarded_live_status") or "") in {"LIVE_WARNING", "LIVE_BREACH", "LIVE_RECOVERY", "LIVE_FATIGUE"}:
        weight += 1.5
    if (to_float(row.get("recovery_live")) or 0.0) > 0:
        weight += 0.75
    if (to_float(row.get("fatigue_live")) or 0.0) > 0:
        weight += min((to_float(row.get("fatigue_live")) or 0.0) / 60.0, 1.5)
    weight += min(abs_number(row.get("sigma_live")) / 100.0, 1.0)
    weight += min(abs_number(row.get("load_live")) / 35.0, 1.5)
    weight += min(abs_number(row.get("moment_live")) / 100.0, 1.0)
    if str(row.get("mechanical_breach_summary_live") or "").strip():
        weight += 1.0
    return weight


def density_bucket_edges(lower: float, upper: float, bucket_count: int) -> List[float]:
    width = (upper - lower) / bucket_count
    return [lower + width * index for index in range(bucket_count + 1)]


def density_bucket_scores(rows: pd.DataFrame, edges: List[float]) -> List[float]:
    scores = [0.0 for _ in range(len(edges) - 1)]
    for _, row in rows.iterrows():
        price = to_float(row.get("price_numeric"))
        if price is None:
            continue
        for index in range(len(edges) - 1):
            is_last = index == len(edges) - 2
            if edges[index] <= price < edges[index + 1] or (is_last and price <= edges[index + 1]):
                scores[index] += to_float(row.get("density_weight")) or 0.0
                break
    return scores


def dominant_density_indexes(scores: List[float]) -> List[int]:
    if not scores or max(scores) <= 0:
        return [0]
    peak = max(scores)
    return [index for index, score in enumerate(scores) if score >= peak * 0.85]


def density_band_scores(scores: List[float]) -> tuple[float, float, float]:
    if not scores:
        return 0.0, 0.0, 0.0
    third = max(len(scores) // 3, 1)
    lower_score = sum(scores[:third])
    middle_score = sum(scores[third : len(scores) - third])
    upper_score = sum(scores[len(scores) - third :])
    return upper_score, middle_score, lower_score


def dominant_density_location(scores: List[float]) -> str:
    if not scores or max(scores) <= 0:
        return "NO_CLEAR_DENSITY"
    peak = max(scores)
    close = [index for index, score in enumerate(scores) if score >= peak * 0.85]
    if len(close) > 1:
        return "MULTI_NODE"
    index = close[0]
    ratio = (index + 0.5) / len(scores)
    if ratio >= 0.66:
        return "UPPER_CORE"
    if ratio <= 0.34:
        return "LOWER_CORE"
    return "MIDDLE_CORE"


def interaction_density_state(score: float, points: int) -> str:
    if points < 3 or score < 8:
        return "LOW_DENSITY"
    if score < 20:
        return "NORMAL_DENSITY"
    if score < 40:
        return "HIGH_DENSITY"
    return "EXTREME_DENSITY"


def merge_interaction_density_into_results(results: pd.DataFrame, density: pd.DataFrame) -> pd.DataFrame:
    if results.empty or density.empty:
        return results
    columns = [column for column in density.columns if column not in {"analysis_run_utc", "research_only", "zone_id"}]
    return results.merge(density[columns], on=["case_id", "episode_id"], how="left")


def build_interaction_density_notes(density: pd.DataFrame, run_utc: str) -> str:
    state_counts = Counter(density["interaction_density_state"].dropna().astype(str)) if not density.empty else Counter()
    location_counts = Counter(density["dominant_interaction_location"].dropna().astype(str)) if not density.empty else Counter()
    return "\n".join(
        [
            "# Interaction Density Map",
            "",
            f"Run UTC: {run_utc}",
            "",
            "Research-only map of weighted interaction density inside Active RDM Zone.",
            "",
            f"Rows: {len(density)}",
            "",
            "## Density States",
            "",
            *[f"- {state}: {count}" for state, count in state_counts.items()],
            "",
            "## Dominant Locations",
            "",
            *[f"- {location}: {count}" for location, count in location_counts.items()],
        ]
    ) + "\n"


def build_true_lifecycle_tracking(
    results: pd.DataFrame,
    core: pd.DataFrame,
    live: pd.DataFrame,
    run_utc: str,
    case_cache: RdmCaseCache | None = None,
) -> pd.DataFrame:
    core_by_case = {str(row["case_id"]): row for _, row in core.iterrows()} if not core.empty else {}
    cache = case_cache or RdmCaseCache(live)
    rows: List[Dict[str, Any]] = []

    for _, row in results.iterrows():
        case_id = str(row.get("case_id") or "")
        case_live = cache.case_live(case_id)
        interaction_rows = cache.lifecycle_interaction_rows(case_id)
        last_interaction = interaction_rows.tail(1).iloc[0] if not interaction_rows.empty else None
        latest = case_live.tail(1).iloc[0] if not case_live.empty else None
        death = mechanical_death_review(row, core_by_case.get(case_id), latest)
        state = true_lifecycle_state(row, latest, last_interaction, death)
        degradation = birth_live_degradation(row, latest)

        rows.append(
            {
                "analysis_run_utc": run_utc,
                "case_id": row.get("case_id"),
                "episode_id": row.get("episode_id"),
                "zone_id": zone_identifier(row),
                "formation_start_time": row.get("real_birth_time") or row.get("episode_start_time_utc"),
                "formation_end_time": row.get("episode_end_time_utc"),
                "active_life_start_time": row.get("real_birth_time") or row.get("episode_start_time_utc"),
                "last_mechanical_interaction_time": last_interaction.get("timestamp") if last_interaction is not None else "",
                "last_mechanical_interaction_price": round_float(last_interaction.get("price")) if last_interaction is not None else "",
                "time_since_last_interaction": round_float(time_since_last_interaction(case_live, last_interaction)),
                "dormant_state_flag": state == "DORMANT",
                "true_mechanical_death_flag": death["true_mechanical_death_flag"],
                "mechanical_death_score": death["mechanical_death_score"],
                "mechanical_death_reason": death["mechanical_death_reason"],
                "true_lifecycle_state": state,
                **degradation,
                "rdm_final_status": final_status_from_lifecycle(state, death, latest),
                "rdm_final_reason": final_reason_from_lifecycle(state, death),
                "research_only": True,
            }
        )

    return pd.DataFrame(rows)


def mechanical_death_review(row: pd.Series, core_row: Any, latest: Any) -> Dict[str, Any]:
    score = 0
    reasons: List[str] = []
    guarded = str(latest.get("guarded_live_status") if latest is not None else row.get("guarded_live_status") or "")
    rupture_streak = to_float(latest.get("live_rupture_streak") if latest is not None else row.get("live_rupture_streak")) or 0.0
    if guarded == "LIVE_RUPTURE" and rupture_streak >= 5:
        score += 2
        reasons.append("CONFIRMED_LIVE_RUPTURE")
    if truthy(row.get("failed_after_return")):
        score += 1
        reasons.append("FAILED_RETURN")
    if not truthy(row.get("return_to_preparation")) and str(row.get("guarded_live_status") or "") == "LIVE_BREACH":
        score += 1
        reasons.append("NO_RECOVERY_AFTER_BREACH")
    if (to_float(row.get("fatigue_current")) or to_float(row.get("fatigue_live")) or 0.0) >= 85:
        score += 1
        reasons.append("SEVERE_FATIGUE")
    if truthy(row.get("health_collapse_flag")) or str(latest.get("health_live_status") if latest is not None else "") == "COLLAPSED":
        score += 1
        reasons.append("HEALTH_COLLAPSE")
    if truthy(row.get("capacity_breach_flag")) or str(latest.get("capacity_live_status") if latest is not None else "") == "BREACHED":
        score += 1
        reasons.append("CAPACITY_BREACH")
    if str(row.get("sigma_state") or "") == "SIGMA_RUPTURE_RISK":
        score += 1
        reasons.append("SIGMA_RUPTURE_RISK")
    if core_row is not None and (to_float(core_row.get("interaction_core_efficiency_ratio")) or 0.0) > 0.80:
        score += 1
        reasons.append("CORE_DEEP_BREACH")
    recovery_active = (
        str(latest.get("guarded_live_status") if latest is not None else "") == "LIVE_RECOVERY"
        or (to_float(row.get("recovery_live")) or 0.0) > 0.25
        or str(row.get("zone_recovery_state") or "") in {"RECOVERED", "STRONG_RECOVERY", "PARTIAL_RECOVERY"}
    )
    return {
        "mechanical_death_score": score,
        "true_mechanical_death_flag": score >= 4 and not recovery_active,
        "mechanical_death_reason": "|".join(reasons),
    }


def true_lifecycle_state(row: pd.Series, latest: Any, last_interaction: Any, death: Dict[str, Any]) -> str:
    if death["true_mechanical_death_flag"]:
        return "MECHANICALLY_DEAD"
    guarded = str(latest.get("guarded_live_status") if latest is not None else row.get("guarded_live_status") or "")
    if guarded == "LIVE_RUPTURE":
        return "RUPTURE"
    if guarded == "LIVE_RECOVERY":
        return "RECOVERY"
    if guarded == "LIVE_FATIGUE":
        return "FATIGUE"
    if guarded in {"LIVE_BREACH", "LIVE_WARNING"}:
        return "ACTIVE_INTERACTION"
    if latest is not None and truthy(latest.get("return_to_zone_flag")):
        return "RETEST"
    if latest is not None and not truthy(latest.get("inside_zone_flag")):
        return "DORMANT"
    if last_interaction is not None:
        return "ACTIVE_INTERACTION"
    return "FORMATION"


def time_since_last_interaction(case_live: pd.DataFrame, last_interaction: Any) -> float | None:
    if case_live.empty or last_interaction is None:
        return None
    latest_row = to_float(case_live.tail(1).iloc[0].get("row_index"))
    last_row = to_float(last_interaction.get("row_index"))
    if latest_row is None or last_row is None:
        return None
    return latest_row - last_row


def birth_live_degradation(row: pd.Series, latest: Any) -> Dict[str, Any]:
    sigma_birth = to_float(row.get("sigma_birth")) or 0.0
    sigma_live = to_float(latest.get("sigma_live") if latest is not None else row.get("sigma_live")) or 0.0
    rigidity_birth = to_float(row.get("rigidity_birth")) or 0.0
    rigidity_live = to_float(latest.get("rigidity_live") if latest is not None else row.get("rigidity_live")) or 0.0
    fatigue_birth = to_float(row.get("fatigue_birth")) or 0.0
    fatigue_live = to_float(latest.get("fatigue_live") if latest is not None else row.get("fatigue_live")) or 0.0
    health_birth = to_float(row.get("health_birth")) or 0.0
    health_live = to_float(latest.get("health_live") if latest is not None else row.get("health_live")) or 0.0
    sigma_degradation = max(sigma_birth - sigma_live, 0.0)
    rigidity_degradation = max(rigidity_birth - rigidity_live, 0.0)
    fatigue_increase = max(fatigue_live - fatigue_birth, 0.0)
    health_degradation = max(health_birth - health_live, 0.0)
    state = degradation_state(rigidity_degradation, fatigue_increase, health_degradation)
    return {
        "sigma_degradation_from_birth": round_float(sigma_degradation),
        "rigidity_degradation_from_birth": round_float(rigidity_degradation),
        "fatigue_increase_from_birth": round_float(fatigue_increase),
        "health_degradation_from_birth": round_float(health_degradation),
        "birth_vs_live_degradation_state": state,
    }


def degradation_state(rigidity_degradation: float, fatigue_increase: float, health_degradation: float) -> str:
    if health_degradation >= 60 or fatigue_increase >= 95:
        return "COLLAPSED"
    if health_degradation >= 42 or rigidity_degradation >= 45 or fatigue_increase >= 80:
        return "SEVERE_DEGRADATION"
    if health_degradation >= 22 or rigidity_degradation >= 25 or fatigue_increase >= 45:
        return "MODERATE_DEGRADATION"
    return "STABLE"


def final_status_from_lifecycle(state: str, death: Dict[str, Any], latest: Any) -> str:
    if death["true_mechanical_death_flag"] or state == "MECHANICALLY_DEAD":
        return "MECHANICALLY_DEAD"
    guarded = str(latest.get("guarded_live_status") if latest is not None else "")
    if guarded == "LIVE_RUPTURE" or state == "RUPTURE":
        return "RUPTURED"
    if guarded == "LIVE_FATIGUE" or state == "FATIGUE":
        return "FATIGUED"
    if guarded == "LIVE_RECOVERY" or state == "RECOVERY":
        return "RECOVERING"
    if state == "DORMANT":
        return "DORMANT"
    if state in {"ACTIVE_INTERACTION", "RETEST"}:
        return "ACTIVE_INTERACTION"
    return "ALIVE"


def final_reason_from_lifecycle(state: str, death: Dict[str, Any]) -> str:
    if death["true_mechanical_death_flag"]:
        return f"True mechanical death confirmed: {death['mechanical_death_reason']}"
    return f"True lifecycle state is {state}; formation end is not used as death proof."


def merge_true_lifecycle_into_results(results: pd.DataFrame, lifecycle: pd.DataFrame) -> pd.DataFrame:
    if results.empty or lifecycle.empty:
        return results
    columns = [column for column in lifecycle.columns if column not in {"analysis_run_utc", "research_only", "zone_id"}]
    return results.merge(lifecycle[columns], on=["case_id", "episode_id"], how="left")


def add_rdm_v16_numeric_foundation(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return results

    enriched = results.copy()
    metric_sources = {
        "rigidity": {
            "birth": "rigidity_birth",
            "current": "rigidity_current",
            "live": "rigidity_live",
            "final": "rigidity_final",
        },
        "sigma": {
            "birth": "sigma_birth",
            "current": "sigma_current",
            "live": "sigma_live",
            "final": "sigma_final",
        },
        "fleche": {
            "birth": "fleche_birth",
            "current": "fleche_current",
            "live": "fleche_live",
            "final": "fleche_final",
        },
        "capacity": {
            "birth": "capacity_birth",
            "current": "capacity_current",
            "live": "capacity_live",
            "final": "capacity_final",
        },
        "fatigue": {
            "birth": "fatigue_birth",
            "current": "fatigue_current",
            "live": "fatigue_live",
            "final": "fatigue_final",
        },
        "recovery": {
            "birth": "recovery_birth",
            "current": "recovery_current",
            "live": "recovery_live",
            "final": "recovery_final",
        },
    }

    for metric_name, source_fields in metric_sources.items():
        birth_column = source_fields["birth"]
        current_column = source_fields["current"]
        add_v16_value_column(enriched, metric_name, "birth", birth_column)
        add_v16_value_column(enriched, metric_name, "current", current_column)
        add_v16_value_column(enriched, metric_name, "live", source_fields["live"])
        add_v16_value_column(enriched, metric_name, "final", source_fields["final"])
        add_v16_delta_columns(
            enriched,
            metric_name,
            birth_column=birth_column,
            current_column=current_column,
        )

    current_only_sources = {
        "stress_utilization": "stress_utilization",
        "moment_utilization": "moment_utilization_ratio",
        "interaction_density_score": "interaction_density_score",
        "interaction_density_width": "interaction_density_width",
        "interaction_density_efficiency_ratio": "interaction_density_efficiency_ratio",
        "interaction_density_points": "interaction_density_points_count",
    }

    for metric_name, source_column in current_only_sources.items():
        add_v16_value_column(enriched, metric_name, "current", source_column)

    return enriched


def add_v16_value_column(
    dataframe: pd.DataFrame,
    metric_name: str,
    value_name: str,
    source_column: str,
) -> None:
    output_column = f"rdm_v16_{metric_name}_{value_name}"
    if source_column in dataframe.columns:
        dataframe[output_column] = dataframe[source_column].map(round_float)
    else:
        dataframe[output_column] = ""


def add_v16_delta_columns(
    dataframe: pd.DataFrame,
    metric_name: str,
    birth_column: str,
    current_column: str,
) -> None:
    delta_column = f"rdm_v16_{metric_name}_delta"
    pct_column = f"rdm_v16_{metric_name}_change_pct"

    if birth_column not in dataframe.columns or current_column not in dataframe.columns:
        dataframe[delta_column] = ""
        dataframe[pct_column] = ""
        return

    dataframe[delta_column] = dataframe.apply(
        lambda row: round_float(
            change_from_birth(row.get(birth_column), row.get(current_column))
        ),
        axis=1,
    )
    dataframe[pct_column] = dataframe.apply(
        lambda row: round_float(
            percent_change_from_birth(row.get(birth_column), row.get(current_column))
        ),
        axis=1,
    )


def percent_change_from_birth(birth: Any, current: Any) -> float | None:
    birth_value = to_float(birth)
    current_value = to_float(current)
    if birth_value is None or current_value is None or birth_value == 0:
        return None
    return ((current_value - birth_value) / abs(birth_value)) * 100.0


def build_interaction_core_notes(core: pd.DataFrame, lifecycle: pd.DataFrame, run_utc: str) -> str:
    state_counts = Counter(core["interaction_core_width_state"].dropna().astype(str)) if not core.empty else Counter()
    lifecycle_counts = Counter(lifecycle["true_lifecycle_state"].dropna().astype(str)) if not lifecycle.empty else Counter()
    return "\n".join(
        [
            "# Interaction Core Geometry",
            "",
            f"Run UTC: {run_utc}",
            "",
            "Research-only split between formation range and interaction core.",
            "",
            f"Rows: {len(core)}",
            "",
            "## Core Width States",
            "",
            *[f"- {state}: {count}" for state, count in state_counts.items()],
            "",
            "## True Lifecycle States",
            "",
            *[f"- {state}: {count}" for state, count in lifecycle_counts.items()],
            "",
            "Formation end is not treated as mechanical death.",
        ]
    ) + "\n"


def build_zone_stress_history(row: pd.Series) -> List[Dict[str, float]]:
    penetration = abs_number(row.get("zone_penetration_depth"))
    sigma_market = abs_number(row.get("sigma_market"))
    if sigma_market == 0:
        sigma_market = abs_number(row.get("mechanical_load_score"))

    duration_minutes = max((to_float(row.get("duration_seconds")) or 0.0) / 60.0, 1.0)
    tests = max(int(to_float(row.get("zone_test_count")) or 0), 1)
    samples = max(min(tests + int(duration_minutes // 15) + 2, 12), 3)
    stress_bias = 1.0 + min(to_float(row.get("fatigue_index")) or 0.0, 100.0) / 250.0

    history: List[Dict[str, float]] = []
    for index in range(samples):
        progress = index / max(samples - 1, 1)
        penetration_value = penetration * progress
        hold_factor = 0.65 + 0.35 * progress
        if str(row.get("zone_mechanical_state") or "") == "RECOVERED_ZONE":
            hold_factor *= 0.65
        elif str(row.get("zone_mechanical_state") or "") == "RUPTURE_ZONE":
            hold_factor *= 1.25
        history.append(
            {
                "row_index": float(index),
                "penetration": penetration_value,
                "sigma_market": sigma_market * hold_factor * stress_bias,
            }
        )
    return history


def calculate_verestchaguine_fleche(
    zone_stress_history: List[Dict[str, float]],
    base_zone_resistance: float,
) -> Dict[str, float]:
    if not zone_stress_history:
        return {
            "omega_stress_area": 0.0,
            "stress_center_of_gravity": 0.0,
            "virtual_moment_at_g": 0.0,
            "fleche_verestchaguine": 0.0,
        }

    omega = 0.0
    weighted_penetration = 0.0
    stress_weight = 0.0
    max_penetration = max(point["penetration"] for point in zone_stress_history) or 1.0

    for previous, current in zip(zone_stress_history, zone_stress_history[1:]):
        delta_penetration = abs(current["penetration"] - previous["penetration"])
        average_sigma = (previous["sigma_market"] + current["sigma_market"]) / 2.0
        area = average_sigma * delta_penetration
        midpoint_penetration = (previous["penetration"] + current["penetration"]) / 2.0
        omega += area
        weighted_penetration += midpoint_penetration * area
        stress_weight += area

    x_g = safe_divide(weighted_penetration, stress_weight)
    y_g = safe_divide(x_g, max_penetration)
    ei_adaptive = max(base_zone_resistance, 1.0)
    fleche_verestchaguine = safe_divide(omega * y_g, ei_adaptive)

    return {
        "omega_stress_area": omega,
        "stress_center_of_gravity": x_g,
        "virtual_moment_at_g": y_g,
        "fleche_verestchaguine": fleche_verestchaguine,
    }


def verestchaguine_ei_adaptive(row: pd.Series) -> float:
    base_resistance = to_float(row.get("base_zone_resistance"))
    sigma_barre = to_float(row.get("adaptive_sigma_barre_v2")) or to_float(row.get("sigma_barre_zone"))
    return max(base_resistance or sigma_barre or 1.0, 1.0)


def classify_dynamic_fleche_state(fleche_combined_score: float) -> str:
    if fleche_combined_score < 0.35:
        return "DYNAMIC_LOW"
    if fleche_combined_score < 0.75:
        return "DYNAMIC_MEDIUM"
    if fleche_combined_score < 1.25:
        return "DYNAMIC_HIGH"
    return "DYNAMIC_CRITICAL"


def build_zone_birth_registry(results: pd.DataFrame, run_utc: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for _, row in results.iterrows():
        lower_edge = to_float(row.get("real_zone_lower_edge"))
        upper_edge = to_float(row.get("real_zone_upper_edge"))
        if lower_edge is None or upper_edge is None:
            lower_edge, upper_edge = zone_edges(row)
        zone_width = to_float(row.get("real_zone_width"))
        if zone_width is None:
            zone_width = abs(upper_edge - lower_edge) if upper_edge != lower_edge else zone_range_height(row)
        zone_id = zone_identifier(row)
        birth = classify_mechanical_birth(row)

        rows.append(
            {
                "analysis_run_utc": run_utc,
                "zone_id": zone_id,
                "case_id": row.get("case_id"),
                "episode_id": row.get("episode_id"),
                "zone_type": zone_type_for_row(row),
                "birth_time": row.get("real_birth_time") or row.get("episode_start_time_utc"),
                "birth_price_range": f"{round_float(lower_edge)}-{round_float(upper_edge)}",
                "upper_edge": round_float(upper_edge),
                "lower_edge": round_float(lower_edge),
                "zone_width": round_float(zone_width),
                "formation_volume": round_float(abs_number(row.get("v_formation"))),
                "formation_delta": round_float(row.get("delta_formation")),
                "formation_velocity": round_float(row.get("v_formation")),
                "formation_duration": row.get("duration_seconds"),
                "formation_quality": round_float(row.get("t_formation")),
                "base_resistance": row.get("base_zone_resistance"),
                "initial_sigma_barre": row.get("sigma_barre_zone"),
                "initial_rigidity": row.get("zone_rigidity"),
                "initial_capacity": row.get("zone_moment_capacity"),
                "institutional_reinforcement": row.get("institutional_reinforcement"),
                "mechanical_birth_state": birth["mechanical_birth_state"],
                "birth_confidence_score": round_float(birth["birth_confidence_score"]),
                "birth_candidate_count": birth["birth_candidate_count"],
                "birth_reason": birth["birth_reason"],
                "birth_classification_source": birth["birth_classification_source"],
                "birth_regime": row.get("mechanical_regime_context"),
                "birth_family_candidate": row.get("mechanical_family"),
                "zone_birth_time": row.get("real_birth_time") or row.get("episode_start_time_utc"),
                "zone_last_test_time": row.get("real_zone_right_time") or row.get("episode_end_time_utc"),
                "zone_age": row.get("zone_age"),
                "zone_test_count": row.get("zone_test_count"),
                "zone_active_duration": row.get("real_zone_active_duration") or row.get("duration_seconds"),
                "zone_lifetime": row.get("real_zone_lifetime") or row.get("zone_age"),
                "zone_decay_rate": zone_decay_rate(row),
                "zone_survival_ratio": zone_survival_ratio(row),
                "research_only": True,
            }
        )

    return pd.DataFrame(rows)


def build_zone_death_registry(results: pd.DataFrame, run_utc: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for _, row in results.iterrows():
        rows.append(
            {
                "analysis_run_utc": run_utc,
                "zone_id": zone_identifier(row),
                "case_id": row.get("case_id"),
                "episode_id": row.get("episode_id"),
                "death_time": row.get("episode_end_time_utc"),
                "death_cause": classify_zone_death_cause(row),
                "final_state": row.get("zone_mechanical_state"),
                "mechanical_family": row.get("mechanical_family"),
                "mechanical_subtype": row.get("mechanical_subtype"),
                "total_tests": row.get("zone_test_count"),
                "zone_age_at_death": row.get("zone_age"),
                "max_stress_utilization": row.get("stress_utilization"),
                "final_fleche": row.get("zone_fleche_ratio"),
                "final_dynamic_fleche": row.get("fleche_verestchaguine"),
                "final_sigma_state": row.get("sigma_state"),
                "final_capacity_state": row.get("zone_capacity_state"),
                "final_timeline_path": " -> ".join(lifecycle_path_for_row(row)),
                "final_repair_count": row.get("repair_cycles"),
                "final_fatigue_cycles": fatigue_cycles(row),
                "research_only": True,
            }
        )

    return pd.DataFrame(rows)


def build_zone_mechanical_memory(
    results: pd.DataFrame,
    birth: pd.DataFrame,
    death: pd.DataFrame,
    timeline: pd.DataFrame,
    run_utc: str,
) -> Dict[str, Any]:
    memory: Dict[str, Any] = {
        "analysis_run_utc": run_utc,
        "mode": "research_only",
        "zones": {},
    }

    birth_by_zone = {str(row["zone_id"]): row for _, row in birth.iterrows()} if not birth.empty else {}
    death_by_zone = {str(row["zone_id"]): row for _, row in death.iterrows()} if not death.empty else {}
    timeline_by_zone: Dict[str, List[str]] = {}
    if not timeline.empty:
        for _, row in timeline.iterrows():
            zone_id = zone_identifier(row)
            timeline_by_zone.setdefault(zone_id, []).append(str(row.get("timeline_step") or ""))

    for _, row in results.iterrows():
        zone_id = zone_identifier(row)
        birth_row = birth_by_zone.get(zone_id)
        death_row = death_by_zone.get(zone_id)
        memory["zones"][zone_id] = {
            "zone_id": zone_id,
            "case_id": json_scalar(row.get("case_id")),
            "episode_id": json_scalar(row.get("episode_id")),
            "previous_stress_states": compact_history(
                row.get("sigma_state"),
                row.get("sigma_memory_state"),
                row.get("zone_capacity_state"),
            ),
            "cumulative_fleche": json_number(row.get("zone_fleche_ratio")),
            "cumulative_dynamic_fleche": json_number(row.get("fleche_verestchaguine")),
            "last_recovery_time": json_scalar(row.get("episode_end_time_utc"))
            if str(row.get("zone_recovery_state") or "") in {"RECOVERED", "STRONG_RECOVERY"}
            else "",
            "permanent_deformation": json_number(row.get("zone_strength_decay")),
            "max_stress_utilization": json_number(row.get("stress_utilization")),
            "max_sigma_market": json_number(row.get("sigma_market")),
            "max_fatigue_index": json_number(row.get("fatigue_index")),
            "repair_count": json_number(row.get("repair_cycles")),
            "rupture_count": 1 if str(row.get("zone_mechanical_state") or "") == "RUPTURE_ZONE" else 0,
            "exhaustion_count": 1 if str(row.get("zone_mechanical_state") or "") == "EXHAUSTED_ZONE" else 0,
            "recovery_count": 1 if str(row.get("zone_mechanical_state") or "") == "RECOVERED_ZONE" else 0,
            "elastic_cycles": 1 if str(row.get("mechanical_family") or "") == "ELASTIC_FAMILY" else 0,
            "plastic_cycles": 1 if str(row.get("mechanical_family") or "") == "PLASTIC_FAMILY" else 0,
            "fatigue_cycles": json_number(fatigue_cycles(row)),
            "sigma_memory_state_history": compact_history(row.get("sigma_memory_state")),
            "capacity_history": compact_history(row.get("zone_capacity_state"), row.get("dynamic_elu_state")),
            "timeline_history": timeline_by_zone.get(zone_id, compact_history(row.get("zone_mechanical_state"))),
            "birth": row_to_memory_dict(birth_row) if birth_row is not None else {},
            "death": row_to_memory_dict(death_row) if death_row is not None else {},
        }

    return memory


def build_zone_evolution_chart(
    results: pd.DataFrame,
    birth: pd.DataFrame,
    death: pd.DataFrame,
    run_utc: str,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    birth_by_case = {str(row["case_id"]): row for _, row in birth.iterrows()} if not birth.empty else {}
    death_by_case = {str(row["case_id"]): row for _, row in death.iterrows()} if not death.empty else {}

    for _, row in results.iterrows():
        case_id = str(row.get("case_id") or "")
        birth_row = birth_by_case.get(case_id)
        death_row = death_by_case.get(case_id)
        path = evolution_path_for_row(row, birth_row, death_row)
        current_state = current_evolution_state(row, death_row)
        previous_state, next_state = neighboring_states(path, current_state)
        transition_reason = evolution_transition_reason(row, current_state)
        source, target = transition_pair(previous_state, current_state)

        rows.append(
            {
                "analysis_run_utc": run_utc,
                "zone_id": zone_identifier(row),
                "case_id": row.get("case_id"),
                "episode_id": row.get("episode_id"),
                "birth_state": birth_row.get("mechanical_birth_state") if birth_row is not None else "",
                "current_state": current_state,
                "previous_state": previous_state,
                "next_candidate_state": next_state,
                "state_transition_reason": transition_reason,
                "transition_count": max(len(path) - 1, 0),
                "life_stage_index": timeline_order(path, current_state),
                "mechanical_age": row.get("zone_age"),
                "survival_ratio": row.get("zone_survival_ratio"),
                "fatigue_progress": round_float(progress_fatigue(row)),
                "recovery_progress": round_float(progress_recovery(row)),
                "rupture_progress": round_float(progress_rupture(row)),
                "plastic_progress": round_float(progress_plastic(row)),
                "elastic_progress": round_float(progress_elastic(row)),
                "sigma_progress": round_float(progress_sigma(row)),
                "capacity_progress": round_float(progress_capacity(row)),
                "transition_source": source,
                "transition_target": target,
                "transition_reason": transition_reason,
                "transition_strength": round_float(transition_strength(row)),
                "evolution_timeline": " -> ".join(path),
                "research_only": True,
            }
        )

    return pd.DataFrame(rows)


def build_zone_evolution_history(chart: pd.DataFrame, run_utc: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    if chart.empty:
        return pd.DataFrame(rows)

    for _, row in chart.iterrows():
        path = str(row.get("evolution_timeline") or "").split(" -> ")
        for index, state in enumerate([step for step in path if step], start=1):
            previous_state = path[index - 2] if index > 1 else ""
            next_state = path[index] if index < len(path) else ""
            rows.append(
                {
                    "analysis_run_utc": run_utc,
                    "zone_id": row.get("zone_id"),
                    "case_id": row.get("case_id"),
                    "episode_id": row.get("episode_id"),
                    "life_stage_index": index,
                    "evolution_state": state,
                    "previous_state": previous_state,
                    "next_state": next_state,
                    "transition_reason": row.get("transition_reason"),
                    "transition_strength": row.get("transition_strength"),
                    "research_only": True,
                }
            )

    return pd.DataFrame(rows)


def evolution_path_for_row(row: pd.Series, birth_row: Any, death_row: Any) -> List[str]:
    path = ["ZONE_BIRTH", "ELASTIC_STAGE"]
    state = str(row.get("zone_mechanical_state") or "")
    family = str(row.get("mechanical_family") or "")
    death_cause = str(death_row.get("death_cause") if death_row is not None else "")

    if progress_plastic(row) >= 0.35 or family == "PLASTIC_FAMILY":
        path.append("PLASTIC_STAGE")
    if progress_fatigue(row) >= 0.35 or family == "FATIGUE_FAMILY":
        path.append("FATIGUE_STAGE")
    if state == "RECOVERED_ZONE" or death_cause == "RECOVERY_COMPLETE":
        path.append("RECOVERY_STAGE")
        path.append("ELASTIC_STAGE")
    if state == "EXHAUSTED_ZONE" or death_cause == "EXHAUSTION":
        if "FATIGUE_STAGE" not in path:
            path.append("FATIGUE_STAGE")
        path.append("EXHAUSTION_STAGE")
    if state == "RUPTURE_ZONE" or death_cause == "RUPTURE":
        if "FATIGUE_STAGE" not in path:
            path.append("FATIGUE_STAGE")
        path.append("RUPTURE_STAGE")
    if truthy(row.get("zero_stress_flag")) or death_cause == "DORMANT_EXPIRED":
        path.append("DORMANT_STAGE")

    path.append("ZONE_DEATH")
    return collapse_repeated(path)


def current_evolution_state(row: pd.Series, death_row: Any) -> str:
    death_cause = str(death_row.get("death_cause") if death_row is not None else "")
    state = str(row.get("zone_mechanical_state") or "")
    if truthy(row.get("zero_stress_flag")) or death_cause == "DORMANT_EXPIRED":
        return "DORMANT_STAGE"
    if state == "RUPTURE_ZONE":
        return "RUPTURE_STAGE"
    if state == "EXHAUSTED_ZONE":
        return "EXHAUSTION_STAGE"
    if state == "RECOVERED_ZONE":
        return "RECOVERY_STAGE"
    if state == "FATIGUE_ZONE":
        return "FATIGUE_STAGE"
    if state == "PLASTIC_ZONE":
        return "PLASTIC_STAGE"
    return "ELASTIC_STAGE"


def evolution_transition_reason(row: pd.Series, current_state: str) -> str:
    if current_state == "DORMANT_STAGE":
        return "No active load or zero stress guard"
    if current_state == "RUPTURE_STAGE":
        return "Rupture or sigma/capacity failure context"
    if current_state == "EXHAUSTION_STAGE":
        return "Expansion exhausted or late failure context"
    if current_state == "RECOVERY_STAGE":
        return "Zone reclaimed or field recovered"
    if current_state == "FATIGUE_STAGE":
        return "Fatigue, repeated tests, or lifecycle weakening"
    if current_state == "PLASTIC_STAGE":
        return "Deep deformation or partial recovery"
    return "Elastic or rigid observation context"


def transition_pair(previous_state: str, current_state: str) -> tuple[str, str]:
    return previous_state or "ZONE_BIRTH", current_state or "ZONE_DEATH"


def transition_strength(row: pd.Series) -> float:
    return max(
        progress_fatigue(row),
        progress_recovery(row),
        progress_rupture(row),
        progress_plastic(row),
        progress_sigma(row),
        progress_capacity(row),
    )


def progress_fatigue(row: pd.Series) -> float:
    return max(min((to_float(row.get("fatigue_index")) or 0.0) / 100.0, 1.0), 0.0)


def progress_recovery(row: pd.Series) -> float:
    return max(min((to_float(row.get("recovery_ratio")) or 0.0) / 2.0, 1.0), 0.0)


def progress_rupture(row: pd.Series) -> float:
    stress = to_float(row.get("stress_utilization")) or 0.0
    capacity_ratio = to_float(row.get("zone_capacity_ratio")) or 0.0
    return max(min(max(stress / 1.30, capacity_ratio / 1.50), 1.0), 0.0)


def progress_plastic(row: pd.Series) -> float:
    fleche = to_float(row.get("zone_fleche_ratio")) or 0.0
    combined = to_float(row.get("fleche_combined_score")) or 0.0
    return max(min(max(fleche, combined) / 1.0, 1.0), 0.0)


def progress_elastic(row: pd.Series) -> float:
    return max(1.0 - max(progress_plastic(row), progress_fatigue(row)), 0.0)


def progress_sigma(row: pd.Series) -> float:
    stress = to_float(row.get("stress_utilization")) or 0.0
    return max(min(stress / 1.30, 1.0), 0.0)


def progress_capacity(row: pd.Series) -> float:
    ratio = to_float(row.get("zone_capacity_ratio")) or 0.0
    return max(min(ratio / 1.50, 1.0), 0.0)


def collapse_repeated(path: List[str]) -> List[str]:
    collapsed: List[str] = []
    for state in path:
        if not collapsed or collapsed[-1] != state:
            collapsed.append(state)
    return collapsed


def zone_identifier(row: pd.Series) -> str:
    case_id = str(row.get("case_id") or "UNKNOWN_CASE")
    episode_id = str(row.get("episode_id") or "UNKNOWN_EPISODE")
    return f"ZONE_{case_id}_EP_{episode_id}"


def zone_edges(row: pd.Series) -> tuple[float, float]:
    low = to_float(row.get("preparation_low_price"))
    high = to_float(row.get("preparation_high_price"))
    mid = to_float(row.get("preparation_mid_price"))
    close_price = to_float(row.get("start_price")) or to_float(row.get("return_price"))

    if low is not None and high is not None and high != low:
        return min(low, high), max(low, high)
    if mid is not None:
        width = max(zone_range_height(row), 1.0)
        return mid - width / 2.0, mid + width / 2.0
    if close_price is not None:
        width = max(zone_range_height(row), 1.0)
        return close_price - width / 2.0, close_price + width / 2.0
    return 0.0, max(zone_range_height(row), 1.0)


def zone_type_for_row(row: pd.Series) -> str:
    if truthy(row.get("preparation_candidate")):
        return "PREPARATION_ZONE"
    if str(row.get("mechanical_family") or "") == "RECOVERY_FAMILY":
        return "RECOVERY_ZONE"
    if str(row.get("mechanical_family") or "") == "RUPTURE_FAMILY":
        return "RUPTURE_RESEARCH_ZONE"
    return "RDM_RESEARCH_ZONE"


def classify_mechanical_birth_state(row: pd.Series) -> str:
    return classify_mechanical_birth(row)["mechanical_birth_state"]


def classify_mechanical_birth(row: pd.Series) -> Dict[str, Any]:
    candidates = birth_candidates(row)
    if not candidates:
        return {
            "mechanical_birth_state": "UNKNOWN_BIRTH",
            "birth_confidence_score": 0.0,
            "birth_candidate_count": 0,
            "birth_reason": "No birth candidate rules matched",
            "birth_classification_source": "FALLBACK",
        }

    ranked = sorted(candidates, key=lambda item: item["score"], reverse=True)
    winner = ranked[0]
    return {
        "mechanical_birth_state": winner["state"],
        "birth_confidence_score": min(winner["score"], 100.0),
        "birth_candidate_count": len(candidates),
        "birth_reason": winner["reason"],
        "birth_classification_source": winner["source"],
    }


def birth_candidates(row: pd.Series) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    reinforcement = to_float(row.get("institutional_reinforcement")) or 0.0
    formation_quality_value = to_float(row.get("t_formation")) or 0.0
    formation_volume = abs_number(row.get("v_formation"))
    formation_delta = abs_number(row.get("delta_formation"))
    base_resistance = to_float(row.get("base_zone_resistance")) or 0.0
    initial_sigma = to_float(row.get("sigma_barre_zone")) or 0.0
    initial_rigidity = to_float(row.get("zone_rigidity")) or 0.0
    penetration = abs_number(row.get("zone_penetration_depth"))
    fleche_ratio = to_float(row.get("zone_fleche_ratio")) or 0.0
    load_score = to_float(row.get("mechanical_load_score")) or 0.0
    fatigue_index = to_float(row.get("fatigue_index")) or 0.0
    activation_state = str(row.get("preparation_activation_state") or "")
    family = str(row.get("mechanical_family") or "")
    capacity_state = str(row.get("zone_capacity_state") or "")
    sigma_state = str(row.get("sigma_state") or "")
    expansion_strength = str(row.get("expansion_strength") or "")
    velocity_proxy = formation_volume

    rupture_context = (
        family == "RUPTURE_FAMILY"
        or capacity_state == "CAPACITY_FAILURE"
        or sigma_state == "SIGMA_RUPTURE_RISK"
    )

    if (
        truthy(row.get("preparation_candidate"))
        and not truthy(row.get("active_load_flag"))
        and not rupture_context
        and activation_state != "EXPLOSIVE_PREPARATION"
    ):
        candidates.append(
            birth_candidate(
                "PREPARATION_BIRTH",
                55 + formation_quality_value * 25,
                "Preparation candidate exists without active load, rupture, or expansion",
                "PREPARATION_RULE",
            )
        )

    if (
        reinforcement >= 55
        or (
            formation_volume >= 0.75
            and formation_delta >= 3.0
            and base_resistance >= 35
            and initial_sigma >= 10
        )
    ):
        candidates.append(
            birth_candidate(
                "INSTITUTIONAL_BIRTH",
                60 + min(reinforcement, 100.0) * 0.35,
                "Strong formation volume/delta/resistance/sigma or reinforcement",
                "INSTITUTIONAL_RULE",
            )
        )

    if initial_rigidity >= 65 and fleche_ratio <= 0.25 and base_resistance >= 30:
        candidates.append(
            birth_candidate(
                "RIGID_BIRTH",
                58 + min(initial_rigidity, 100.0) * 0.25,
                "High initial rigidity with low penetration and high resistance",
                "RIGIDITY_RULE",
            )
        )

    if (
        activation_state == "EXPLOSIVE_PREPARATION"
        or expansion_strength in {"HIGH", "EXTREME"}
        or (load_score >= 55 and velocity_proxy >= 0.75)
    ):
        candidates.append(
            birth_candidate(
                "EXPANSION_BIRTH",
                52 + min(load_score, 100.0) * 0.30,
                "Strong move, velocity, or load activation after birth",
                "EXPANSION_RULE",
            )
        )

    stable_context = (
        fatigue_index < 35
        and fleche_ratio <= 0.60
        and penetration <= max(zone_range_height(row), 1.0)
        and not rupture_context
    )
    if stable_context:
        candidates.append(
            birth_candidate(
                "ELASTIC_BIRTH",
                50 + (1.0 - min(fleche_ratio, 1.0)) * 25,
                "Stable low-fatigue and low-deformation formation",
                "ELASTIC_RULE",
            )
        )

    return candidates


def birth_candidate(state: str, score: float, reason: str, source: str) -> Dict[str, Any]:
    return {
        "state": state,
        "score": max(min(score, 100.0), 0.0),
        "reason": reason,
        "source": source,
    }


def zone_decay_rate(row: pd.Series) -> float:
    age = to_float(row.get("zone_age")) or 0.0
    decay = to_float(row.get("zone_strength_decay")) or 0.0
    return safe_divide(decay, max(age, 1.0))


def zone_survival_ratio(row: pd.Series) -> float:
    memory_score = to_float(row.get("mechanical_memory_score")) or 0.0
    decay = to_float(row.get("zone_strength_decay")) or 0.0
    return max(min((memory_score + 100.0 - decay) / 200.0, 1.0), 0.0)


def classify_zone_death_cause(row: pd.Series) -> str:
    state = str(row.get("zone_mechanical_state") or "")
    sigma_state = str(row.get("sigma_state") or "")
    capacity_state = str(row.get("zone_capacity_state") or "")
    memory_state = str(row.get("sigma_memory_state") or "")

    if truthy(row.get("zero_stress_flag")):
        return "DORMANT_EXPIRED"
    if state == "RECOVERED_ZONE":
        return "RECOVERY_COMPLETE"
    if state == "RUPTURE_ZONE" or sigma_state == "SIGMA_RUPTURE_RISK" or capacity_state == "CAPACITY_FAILURE":
        return "RUPTURE"
    if state == "EXHAUSTED_ZONE":
        return "EXHAUSTION"
    if "FATIGUE" in state or memory_state == "FATIGUED_SIGMA":
        return "FATIGUE"
    if (to_float(row.get("zone_age")) or 0.0) >= 120:
        return "TIME_DECAY"
    return "UNKNOWN_DEATH"


def fatigue_cycles(row: pd.Series) -> float:
    fatigue_state = str(row.get("fatigue_state") or "")
    fatigue_index = to_float(row.get("fatigue_index")) or 0.0
    if fatigue_state == "CRITICAL_FATIGUE":
        return 2.0
    if fatigue_state == "HIGH_FATIGUE" or fatigue_index >= 50:
        return 1.0
    return 0.0


def compact_history(*values: Any) -> List[str]:
    return [str(value) for value in values if str(value or "") not in {"", "nan", "None"}]


def row_to_memory_dict(row: pd.Series) -> Dict[str, Any]:
    return {key: json_scalar(value) for key, value in row.to_dict().items()}


def json_scalar(value: Any) -> Any:
    if pd.isna(value):
        return ""
    if hasattr(value, "item"):
        return value.item()
    return value


def json_number(value: Any) -> float:
    return to_float(value) or 0.0


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
        context_adjustment = 0.18
    elif context == "EXPANSION_EXHAUSTION_CONTEXT":
        context_adjustment = 0.38
    elif context == "HIGH_VOLATILITY_CONTEXT":
        context_adjustment = 0.65
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

    capacity = rigidity * (1 - min(decay, 100.0) / 140.0)
    capacity += min(recovery, 2.0) * 28.0
    capacity -= min(fatigue, 100.0) * 0.08
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


def build_verestchaguine_notes(verestchaguine: pd.DataFrame, run_utc: str) -> str:
    state_counts = (
        Counter(verestchaguine["fleche_dynamic_state"]) if not verestchaguine.empty else Counter()
    )
    lines = [
        "# Zone Mechanics Verestchaguine Dynamic Fleche Notes",
        "",
        f"- Run UTC: {run_utc}",
        "- Mode: Research only",
        "- No live signals",
        "- No execution",
        "- No entries",
        "- No Dashboard V2 scoring changes",
        "- No Phase 2",
        "",
        "## Dynamic Fleche State Counts",
    ]

    for state, count in state_counts.items():
        lines.append(f"- {state}: {count}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "- Static fleche remains zone_fleche_ratio and is not replaced.",
            "- Verestchaguine fleche estimates accumulated deformation from stress-area proxies.",
            "- omega_stress_area is a discrete trapezoidal stress integral inside the zone.",
            "- stress_center_of_gravity and virtual_moment_at_g describe where stress concentrates.",
            "- fleche_combined_score blends static penetration and dynamic accumulated deformation.",
            "",
            "Research-only note: dynamic fleche states are not live signals and do not affect scoring.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_zone_evolution_notes(
    chart: pd.DataFrame,
    history: pd.DataFrame,
    run_utc: str,
) -> str:
    stage_counts = Counter(chart["current_state"]) if not chart.empty else Counter()
    transition_counts = (
        Counter(chart["transition_target"]) if "transition_target" in chart else Counter()
    )
    lines = [
        "# Zone Evolution Notes",
        "",
        f"- Run UTC: {run_utc}",
        "- Mode: Research only",
        "- No live signals",
        "- No execution",
        "- No entries",
        "- No Dashboard V2 scoring changes",
        "- No Phase 2",
        "",
        f"- Evolution rows: {len(chart)}",
        f"- Evolution history rows: {len(history)}",
        "",
        "## Stage Counts",
    ]

    for state, count in stage_counts.items():
        lines.append(f"- {state}: {count}")

    lines.extend(["", "## Transition Target Counts"])
    for state, count in transition_counts.items():
        lines.append(f"- {state}: {count}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "- Evolution chart summarizes the mechanical life path of each zone.",
            "- History expands each path into stage rows.",
            "- Progress fields are normalized research indicators, not signals.",
            "",
            "Research-only note: evolution states do not affect scoring or execution.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_zone_birth_concept() -> str:
    return "\n".join(
        [
            "# Zone Mechanics Birth Concept",
            "",
            "Mode: Research only",
            "",
            "This document defines the Phase 1B+ RDM Market Mechanics zone lifecycle model.",
            "It does not introduce execution, entries, live signals, Phase 2 logic, or Dashboard V2 scoring changes.",
            "",
            "## Lifecycle",
            "",
            "Birth -> Life -> Memory -> Interaction -> Outcome -> Death",
            "",
            "## Birth",
            "",
            "Zone birth captures formation volume, delta, velocity, duration, quality, base resistance,",
            "initial sigma barre, initial rigidity, initial capacity, and institutional reinforcement.",
            "",
            "Birth states:",
            "",
            "- ELASTIC_BIRTH",
            "- RIGID_BIRTH",
            "- INSTITUTIONAL_BIRTH",
            "- PREPARATION_BIRTH",
            "- EXPANSION_BIRTH",
            "- UNKNOWN_BIRTH",
            "",
            "## Life Tracking",
            "",
            "Life tracking records age, tests, active duration, decay rate, and survival ratio.",
            "",
            "## Mechanical Memory",
            "",
            "Mechanical memory stores per-zone stress, fleche, fatigue, repair, capacity, sigma, and timeline history.",
            "",
            "## Death",
            "",
            "Death labels:",
            "",
            "- RUPTURE",
            "- FATIGUE",
            "- EXHAUSTION",
            "- RECOVERY_COMPLETE",
            "- TIME_DECAY",
            "- DORMANT_EXPIRED",
            "- UNKNOWN_DEATH",
            "",
            "## Safety Rule",
            "",
            "Cases may be shown as reference examples, but classification remains mechanics-first:",
            "",
            "Variables -> Family -> Subtype -> State",
            "",
        ]
    )


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


def is_near_zero(value: Any, threshold: float = 1e-9) -> bool:
    number = to_float(value)
    if number is None:
        return True
    return abs(number) <= threshold


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

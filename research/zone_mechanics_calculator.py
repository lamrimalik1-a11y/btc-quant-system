"""Research-only RDM market mechanics calculator.

This script reads existing replay/research outputs and produces zone mechanics
research files. It does not modify live logic, Dashboard V2 scoring, execution,
or any engine state.
"""

from __future__ import annotations

import csv
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
from research.synthesis_engine import build_zone_synthesis

OUTPUT_DIR = ROOT_DIR / "outputs"
RESEARCH_DIR = ROOT_DIR / "research"

EPISODES_FILE = OUTPUT_DIR / "historical_replay_dashboard_v2_episodes.csv"
HISTORICAL_ROWS_FILE = OUTPUT_DIR / "historical_observation_rows.csv"
RESEARCH_LOG_FILE = RESEARCH_DIR / "phase1b_episode_research_log.csv"

# Memory optimization: build_live_rdm_evolution / attach_historical_delta_to_live_rows
# only ever read this subset of historical_observation_rows.csv columns. Restricting
# the load to these columns + downcasting dtypes cuts resident memory for this frame
# by ~45x (476 MB -> ~10 MB on the April-scale file) with no change to values read.
HISTORICAL_ROWS_USECOLS = [
    "row_id",
    "close",
    "market_timestamp",
    "delta",
    "delta_zscore",
    "velocity_zscore",
    "volume_zscore",
    "volatility_regime",
    "velocity_state",
    "volume_state",
]
HISTORICAL_ROWS_DTYPES = {
    "row_id": "int32",
    "market_timestamp": "int64",
    "close": "float32",
    "delta": "float32",
    "delta_zscore": "float32",
    "velocity_zscore": "float32",
    "volume_zscore": "float32",
    "volatility_regime": "category",
    "velocity_state": "category",
    "volume_state": "category",
}
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
ZONE_ATTACKER_EVOLUTION_FILE = RESEARCH_DIR / "zone_attacker_evolution.csv"
ZONE_STRENGTH_PROFILE_FILE = RESEARCH_DIR / "zone_strength_profile.csv"
ZONE_VS_ATTACKER_FILE      = RESEARCH_DIR / "zone_vs_attacker_profile.csv"
ZONE_ANOMALY_FILE          = RESEARCH_DIR / "zone_anomaly_profile.csv"
ZONE_REINFORCEMENT_FILE    = RESEARCH_DIR / "zone_reinforcement_profile.csv"
ATTACKER_CONVERSION_FILE   = RESEARCH_DIR / "attacker_conversion_profile.csv"
FORCE_ALLOCATION_FILE      = RESEARCH_DIR / "force_allocation_profile.csv"
ZONE_VISIT_TIMELINE_FILE      = RESEARCH_DIR / "zone_visit_timeline.csv"
ZONE_VISIT_TIMELINE_DYNAMIC_FILE = RESEARCH_DIR / "zone_visit_timeline_dynamic.csv"
ZONE_HEALTH_EVOLUTION_FILE       = RESEARCH_DIR / "zone_health_evolution.csv"
ZONE_STRUCTURAL_TRAJECTORY_FILE   = RESEARCH_DIR / "zone_structural_trajectory.csv"
ZONE_STRUCTURAL_PREDICTION_FILE   = RESEARCH_DIR / "zone_structural_prediction.csv"
ZONE_SYNTHESIS_FILE               = RESEARCH_DIR / "zone_synthesis.csv"

# ==================================================
# RDM V1.6-B3.5-B — FORCE LULL SEGMENTATION CONSTANTS
# Research only.  Do not use in scoring, lifecycle, or replay.
# ==================================================
ATTACKER_LULL_THRESHOLD_RATIO: float = 0.50   # lull if rolling_force < 50% of session mean
ATTACKER_FORCE_WINDOW: int = 5                 # trailing rolling mean window (rows)
ATTACKER_LULL_DURATION: int = 3               # min lull rows to separate attempts; shorter lulls are bridged

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
            historical_rows = read_optional_csv(
                HISTORICAL_ROWS_FILE,
                usecols=HISTORICAL_ROWS_USECOLS,
                dtype=HISTORICAL_ROWS_DTYPES,
            )
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
        with profiler.step("rdm_v16b_attacker_basics"):
            attacker_df = build_attacker_evolution(
                results_df,
                live_evolution_df,
                historical_rows,
                run_utc,
            )
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
        with profiler.step("rdm_v16b4_zone_strength_foundation"):
            strength_df = build_zone_strength_profile(results_df, run_utc)
        with profiler.step("rdm_v16b4_zone_vs_attacker"):
            vs_attacker_df = build_zone_vs_attacker_profile(
                strength_df, attacker_df, results_df, run_utc
            )
        with profiler.step("rdm_v16b5_anomaly_physics"):
            anomaly_df = build_zone_anomaly_profile(
                vs_attacker_df, results_df, run_utc
            )
        with profiler.step("rdm_v16b6_reinforcement_physics"):
            reinforcement_df = build_zone_reinforcement_profile(
                results_df, run_utc
            )
        with profiler.step("rdm_v16b7_attacker_conversion_physics"):
            conversion_df = build_attacker_conversion_profile(
                results_df, attacker_df, run_utc
            )
        with profiler.step("rdm_v16b75b_force_allocation_physics"):
            force_alloc_df = build_force_allocation_profile(
                results_df, attacker_df, run_utc
            )
        with profiler.step("rdm_v16b8_zone_visit_timeline"):
            visit_timeline_df = build_zone_visit_timeline(
                results_df, live_evolution_df, attacker_df, run_utc
            )
        with profiler.step("rdm_v16b9_zone_health_evolution"):
            health_evolution_df = build_zone_health_evolution(
                results_df, visit_timeline_df, run_utc
            )
        with profiler.step("rdm_v16b10_zone_structural_trajectory"):
            trajectory_df = build_zone_structural_trajectory(
                results_df, health_evolution_df, run_utc
            )
        with profiler.step("rdm_v16b11_zone_structural_prediction"):
            prediction_df = build_zone_structural_prediction(
                results_df, trajectory_df, vs_attacker_df, run_utc
            )
        with profiler.step("rdm_synthesis_engine"):
            synthesis_df = build_zone_synthesis(
                results_df, trajectory_df, prediction_df, episodes, run_utc
            )
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
            attacker_df.to_csv(ZONE_ATTACKER_EVOLUTION_FILE, index=False)
            strength_df.to_csv(ZONE_STRENGTH_PROFILE_FILE, index=False)
            vs_attacker_df.to_csv(ZONE_VS_ATTACKER_FILE, index=False)
            anomaly_df.to_csv(ZONE_ANOMALY_FILE, index=False)
            reinforcement_df.to_csv(ZONE_REINFORCEMENT_FILE, index=False)
            conversion_df.to_csv(ATTACKER_CONVERSION_FILE, index=False)
            force_alloc_df.to_csv(FORCE_ALLOCATION_FILE, index=False)
            visit_timeline_df.to_csv(ZONE_VISIT_TIMELINE_FILE, index=False)
            health_evolution_df.to_csv(ZONE_HEALTH_EVOLUTION_FILE, index=False)
            trajectory_df.to_csv(ZONE_STRUCTURAL_TRAJECTORY_FILE, index=False)
            prediction_df.to_csv(ZONE_STRUCTURAL_PREDICTION_FILE, index=False)
            synthesis_df.to_csv(ZONE_SYNTHESIS_FILE, index=False)
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
        profiler.add_metric("attacker_evolution_rows", len(attacker_df))
        profiler.add_metric("zone_strength_profile_rows", len(strength_df))
        profiler.add_metric("zone_vs_attacker_rows", len(vs_attacker_df))
        profiler.add_metric("zone_anomaly_rows", len(anomaly_df))
        profiler.add_metric("zone_reinforcement_rows", len(reinforcement_df))
        profiler.add_metric("attacker_conversion_rows", len(conversion_df))
        profiler.add_metric("force_allocation_rows", len(force_alloc_df))
        profiler.add_metric("zone_visit_timeline_rows", len(visit_timeline_df))
        profiler.add_metric("zone_health_evolution_rows", len(health_evolution_df))
        profiler.add_metric("zone_structural_trajectory_rows", len(trajectory_df))
        profiler.add_metric("zone_structural_prediction_rows", len(prediction_df))
        profiler.add_metric("zone_synthesis_rows", len(synthesis_df))
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
        print(f"Attacker evolution: {relative_path(ZONE_ATTACKER_EVOLUTION_FILE)}")
        print(f"Zone strength profile: {relative_path(ZONE_STRENGTH_PROFILE_FILE)}")
        print(f"Zone vs attacker profile: {relative_path(ZONE_VS_ATTACKER_FILE)}")
        print(f"Zone anomaly profile: {relative_path(ZONE_ANOMALY_FILE)}")
        print(f"Zone reinforcement profile: {relative_path(ZONE_REINFORCEMENT_FILE)}")
        print(f"Attacker conversion profile: {relative_path(ATTACKER_CONVERSION_FILE)}")
        print(f"Force allocation profile: {relative_path(FORCE_ALLOCATION_FILE)}")
        print(f"Zone visit timeline: {relative_path(ZONE_VISIT_TIMELINE_FILE)}")
        print(f"Zone health evolution: {relative_path(ZONE_HEALTH_EVOLUTION_FILE)}")
        print(f"Zone structural trajectory: {relative_path(ZONE_STRUCTURAL_TRAJECTORY_FILE)}")
        print(f"Zone structural prediction: {relative_path(ZONE_STRUCTURAL_PREDICTION_FILE)}")
        print(f"Zone synthesis: {relative_path(ZONE_SYNTHESIS_FILE)}")
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

    # Memory optimization: stream each zone's evolution rows to a temp CSV
    # as they are produced, instead of accumulating all rows in a Python
    # list (output_rows) before building the DataFrame. This avoids ever
    # holding both the full row-dict list AND its DataFrame copy in memory
    # at once. Write-to-temp-then-rename guards against a partial file if
    # interrupted mid-write.
    tmp_path = ZONE_LIVE_RDM_EVOLUTION_FILE.with_suffix(".incremental.tmp.csv")
    final_path = ZONE_LIVE_RDM_EVOLUTION_FILE.with_suffix(".incremental.csv")
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    rows_written = 0
    writer: csv.DictWriter | None = None
    with open(tmp_path, "w", newline="", encoding="utf-8") as handle:
        for _, zone in results.iterrows():
            start_row, end_row = live_row_window(zone, rows_source)
            start_position = row_ids.searchsorted(start_row, side="left")
            end_position = row_ids.searchsorted(end_row, side="right")
            zone_rows = rows_source.iloc[int(start_position):int(end_position)].copy()
            if zone_rows.empty:
                zone_output = build_static_live_rdm_evolution(pd.DataFrame([zone]), run_utc).to_dict("records")
            else:
                zone_output = live_evolution_rows_for_zone(zone, zone_rows, run_utc)
            for record in zone_output:
                if writer is None:
                    writer = csv.DictWriter(handle, fieldnames=list(record.keys()))
                    writer.writeheader()
                writer.writerow(record)
                rows_written += 1

    if rows_written == 0:
        tmp_path.unlink(missing_ok=True)
        return pd.DataFrame()

    tmp_path.replace(final_path)
    return pd.read_csv(final_path)


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


def live_row_window(
    zone: pd.Series,
    rows_source: pd.DataFrame,
    post_return_rows: int = 500,
) -> tuple[float, float]:
    return_row = to_float(zone.get("return_row"))
    candidates_start = [
        to_float(zone.get("preparation_start_row")),
        to_float(zone.get("start_row_id")),
        to_float(zone.get("return_row")),
    ]
    # End candidates EXCLUDING return_row; the bounded return horizon is
    # added below so the window can extend past the return event.
    candidates_end = [
        to_float(zone.get("end_row_id")),
        to_float(zone.get("preparation_end_row")),
    ]
    valid_start = [item for item in candidates_start if item is not None and item > 0]
    valid_end = [item for item in candidates_end if item is not None and item > 0]
    start = min(valid_start) if valid_start else float(rows_source["row_id_numeric"].min())

    # Stage 1 (B12.5): extend the live window by a STRICTLY BOUNDED horizon
    # past the return event so post-return visits can be scanned. The +N
    # horizon is mandatory-capped at max_observed_row_id below to prevent the
    # unbounded return_row window blow-up that previously filled the disk.
    if return_row is not None and return_row > 0:
        post_return_end = return_row + float(post_return_rows)
        end = max(valid_end + [post_return_end])
    else:
        end = max(valid_end) if valid_end else start + 120.0

    if end <= start:
        end = start + 120.0

    # HARD CAP (mandatory): never scan past the last observed row.
    max_observed_row_id = float(rows_source["row_id_numeric"].max())
    end = min(end, max_observed_row_id)
    assert end <= max_observed_row_id, (
        f"Window end {end} exceeds max row {max_observed_row_id}"
    )

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


def build_attacker_evolution(
    results: pd.DataFrame,
    live: pd.DataFrame,
    historical_rows: pd.DataFrame,
    run_utc: str,
) -> pd.DataFrame:
    rows = []
    if results.empty:
        return pd.DataFrame(rows)

    live_with_delta = attach_historical_delta_to_live_rows(live, historical_rows)
    grouped_live = (
        {
            str(case_id): group.copy()
            for case_id, group in live_with_delta.groupby("case_id")
        }
        if not live_with_delta.empty and "case_id" in live_with_delta.columns
        else {}
    )

    # V1.6-B2: build capacity_birth lookup for zone-relative normalization.
    # capacity_birth is already present in results from V1.5 / V1.6-A.
    # Only positive, finite values are stored; zero or missing → NaN output.
    capacity_lookup: dict = {}
    if "case_id" in results.columns and "capacity_birth" in results.columns:
        for _, _r in results.iterrows():
            _cid = str(_r.get("case_id") or "")
            try:
                _cb = float(_r.get("capacity_birth"))
                if _cb > 0:
                    capacity_lookup[_cid] = _cb
            except (TypeError, ValueError):
                pass

    for _, result_row in results.iterrows():
        case_id = str(result_row.get("case_id") or "")
        case_live = grouped_live.get(case_id, pd.DataFrame())
        interaction_rows = filter_attacker_interaction_rows(case_live)
        force_values = pd.Series(dtype="float64")

        if not interaction_rows.empty and "delta" in interaction_rows.columns:
            force_values = pd.to_numeric(
                interaction_rows["delta"],
                errors="coerce",
            ).abs().dropna()

        # B1 core values (computed once, reused for both B1 and B2 fields)
        force_mean = (
            round_float(force_values.mean()) if not force_values.empty else pd.NA
        )
        force_peak = (
            round_float(force_values.max()) if not force_values.empty else pd.NA
        )

        # V1.6-B2: zone-relative normalization (per-case denominator)
        capacity_birth_val = capacity_lookup.get(case_id)
        if isinstance(force_mean, float) and capacity_birth_val is not None:
            force_zone_norm = round_float(force_mean / capacity_birth_val)
        else:
            force_zone_norm = pd.NA

        if isinstance(force_peak, float) and capacity_birth_val is not None:
            force_peak_zone_norm = round_float(force_peak / capacity_birth_val)
        else:
            force_peak_zone_norm = pd.NA

        # V1.6-B3: attacker evolution across sequential interaction events.
        # Each contiguous run of interaction rows = one event.
        event_forces = compute_event_forces(interaction_rows)
        n_events = len(event_forces)
        attack_attempts = segment_attacker_attempts(interaction_rows)
        attempt_diagnostics = attacker_attempt_diagnostics(attack_attempts)

        # V1.6-B3.5-B: FORCE_LULL_ATTEMPT_SEGMENTATION_V1 (parallel model)
        force_lull_attempts = segment_force_lull_attempts(interaction_rows)
        force_lull_metrics = force_lull_attempt_metrics(force_lull_attempts)

        force_birth = event_forces[0] if n_events >= 1 else pd.NA
        force_final = event_forces[-1] if n_events >= 1 else pd.NA

        if isinstance(force_birth, float) and isinstance(force_final, float):
            force_delta = round_float(force_final - force_birth)
            force_pct_change = (
                round_float((force_final - force_birth) / force_birth * 100)
                if force_birth != 0
                else pd.NA
            )
        else:
            force_delta = pd.NA
            force_pct_change = pd.NA

        force_trend_slope = linear_slope_from_values(event_forces)
        force_trend_count = n_events if n_events > 0 else pd.NA

        if n_events >= 1:
            valid_events = [
                (i, v) for i, v in enumerate(event_forces)
                if isinstance(v, float) and pd.notna(v)
            ]
            force_peak_event_index = (
                max(valid_events, key=lambda t: t[1])[0] + 1  # 1-indexed
                if valid_events
                else pd.NA
            )
        else:
            force_peak_event_index = pd.NA

        rows.append(
            {
                "analysis_run_utc": run_utc,
                "case_id": result_row.get("case_id"),
                "episode_id": result_row.get("episode_id"),
                "zone_id": result_row.get("zone_id"),
                # B1 fields (unchanged)
                "rdm_v16b_attacker_interaction_count": (
                    len(interaction_rows) if not interaction_rows.empty else pd.NA
                ),
                "rdm_v16b_attacker_force_mean_at_touch": force_mean,
                "rdm_v16b_attacker_force_peak": force_peak,
                "rdm_v16b_attacker_force_std": (
                    round_float(force_values.std()) if len(force_values) > 1 else pd.NA
                ),
                "rdm_v16b_attacker_persistence_max": (
                    max_consecutive_truthy(case_live.get("inside_zone_flag"))
                    if not case_live.empty and "inside_zone_flag" in case_live.columns
                    else pd.NA
                ),
                # B2 fields — zone-relative normalization
                "rdm_v16b_attacker_force_zone_normalized": force_zone_norm,
                "rdm_v16b_attacker_force_peak_zone_normalized": force_peak_zone_norm,
                # B3 fields — attacker evolution through lifecycle events
                "rdm_v16b_attacker_force_birth": force_birth,
                "rdm_v16b_attacker_force_final": force_final,
                "rdm_v16b_attacker_force_delta": force_delta,
                "rdm_v16b_attacker_force_pct_change": force_pct_change,
                "rdm_v16b_attacker_force_trend_slope": force_trend_slope,
                "rdm_v16b_attacker_force_trend_count": force_trend_count,
                "rdm_v16b_attacker_force_peak_event_index": force_peak_event_index,
                # B3.5-A fields — CONTIGUOUS_INTERACTION_ROWS_V1 (preserved, diagnostic)
                "rdm_v16b_attacker_attempt_count": attempt_diagnostics["count"],
                "rdm_v16b_attacker_attempt_rows_total": attempt_diagnostics["rows_total"],
                "rdm_v16b_attacker_attempt_rows_mean": attempt_diagnostics["rows_mean"],
                "rdm_v16b_attacker_attempt_rows_max": attempt_diagnostics["rows_max"],
                "rdm_v16b_attacker_attempt_first_row": attempt_diagnostics["first_row"],
                "rdm_v16b_attacker_attempt_last_row": attempt_diagnostics["last_row"],
                "rdm_v16b_attacker_attempt_row_spans": attempt_diagnostics["row_spans"],
                "rdm_v16b_attacker_attempt_segmentation_model": (
                    "CONTIGUOUS_INTERACTION_ROWS_V1"
                ),
                # B3.5-B fields — FORCE_LULL_ATTEMPT_SEGMENTATION_V1 (parallel model)
                **force_lull_metrics,
                "research_only": True,
            }
        )

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # V1.6-B2: cycle-relative normalization (cross-case denominator).
    # Denominator = mean of each metric across all cases that have valid data.
    # Cases with NaN numerator produce NaN output. Guard against zero denominator.
    _mean_series = pd.to_numeric(
        df["rdm_v16b_attacker_force_mean_at_touch"], errors="coerce"
    )
    _peak_series = pd.to_numeric(
        df["rdm_v16b_attacker_force_peak"], errors="coerce"
    )

    _cycle_mean_denom = (
        float(_mean_series.dropna().mean())
        if not _mean_series.dropna().empty
        else None
    )
    _cycle_peak_denom = (
        float(_peak_series.dropna().mean())
        if not _peak_series.dropna().empty
        else None
    )

    if _cycle_mean_denom is not None and _cycle_mean_denom > 0:
        df["rdm_v16b_attacker_force_cycle_normalized"] = (
            (_mean_series / _cycle_mean_denom)
            .apply(lambda v: round_float(v) if pd.notna(v) else pd.NA)
        )
    else:
        df["rdm_v16b_attacker_force_cycle_normalized"] = pd.NA

    if _cycle_peak_denom is not None and _cycle_peak_denom > 0:
        df["rdm_v16b_attacker_force_peak_cycle_normalized"] = (
            (_peak_series / _cycle_peak_denom)
            .apply(lambda v: round_float(v) if pd.notna(v) else pd.NA)
        )
    else:
        df["rdm_v16b_attacker_force_peak_cycle_normalized"] = pd.NA

    return df


def attach_historical_delta_to_live_rows(
    live: pd.DataFrame,
    historical_rows: pd.DataFrame,
) -> pd.DataFrame:
    if live.empty:
        return live.copy()

    enriched = live.copy()
    if "delta" in enriched.columns:
        return enriched

    if (
        historical_rows.empty
        or "row_id" not in historical_rows.columns
        or "delta" not in historical_rows.columns
        or "row_index" not in enriched.columns
    ):
        enriched["delta"] = pd.NA
        return enriched

    delta_lookup = historical_rows[["row_id", "delta"]].copy()
    delta_lookup["row_index_numeric"] = pd.to_numeric(
        delta_lookup["row_id"],
        errors="coerce",
    )
    delta_lookup = delta_lookup.dropna(
        subset=["row_index_numeric"]
    ).drop_duplicates("row_index_numeric", keep="last")
    enriched["row_index_numeric"] = pd.to_numeric(
        enriched["row_index"],
        errors="coerce",
    )
    enriched = enriched.merge(
        delta_lookup[["row_index_numeric", "delta"]],
        on="row_index_numeric",
        how="left",
    )
    return enriched.drop(columns=["row_index_numeric"])


def filter_attacker_interaction_rows(live: pd.DataFrame) -> pd.DataFrame:
    if live.empty:
        return live

    mask = pd.Series(False, index=live.index)
    if "zone_touch_flag" in live.columns:
        mask = mask | live["zone_touch_flag"].apply(truthy)
    if "inside_zone_flag" in live.columns:
        mask = mask | live["inside_zone_flag"].apply(truthy)
    return live[mask].copy()


def max_consecutive_truthy(values: Any) -> Any:
    if values is None:
        return pd.NA

    max_count = 0
    current_count = 0
    for value in values:
        if truthy(value):
            current_count += 1
            max_count = max(max_count, current_count)
        else:
            current_count = 0

    return max_count if max_count > 0 else pd.NA


def build_zone_strength_profile(results: pd.DataFrame, run_utc: str) -> pd.DataFrame:
    """
    RDM V1.6-B4-A — Zone Strength Foundation.

    Computes a Zone Strength Score (ZSS) for each case using five orthogonal
    mechanical components from existing RDM V1.5 / V1.6-A metrics.

    Normalization strategy
    ---------------------
    capacity / rigidity  : per-case ratio against birth value (birth is non-zero).
    fatigue inverse      : population-normalized (fatigue_birth = 0 always;
                           normalize live value against max observed in this run).
    recovery ratio       : population-normalized (recovery_birth = 0 always;
                           normalize live value against max observed in this run).
    stress availability  : rdm_v16_stress_utilization_current is 0-100 percent;
                           divide by 100 to convert to [0,1] fraction.

    Missing denominators  → NaN.  No fallback values.
    All components clamped to [0, 1] before formula application.
    ZSS is always in [0, 100].

    Research only.  Does not affect scoring, lifecycle, replay, or dashboard.
    """
    if results.empty:
        return pd.DataFrame()

    # Population-level denominators for metrics where birth value = 0.
    # Computed once so each per-case ratio is consistent across the dataset.
    fat_series = pd.to_numeric(results["fatigue_live"], errors="coerce")
    rec_series = pd.to_numeric(results["recovery_live"], errors="coerce")
    fatigue_pop_max = float(fat_series.dropna().max()) if not fat_series.dropna().empty else None
    recovery_pop_max = float(rec_series.dropna().max()) if not rec_series.dropna().empty else None

    rows = []

    for _, row in results.iterrows():

        # ── Component 1: Capacity Ratio ──────────────────────────────────────
        # capacity_live tracks the evolving mechanical capacity; birth is the
        # original structural reserve.  Ratio > 1 (recovery beyond birth) is
        # clamped to 1.
        cap_live  = to_float(row.get("capacity_live"))
        cap_birth = to_float(row.get("capacity_birth"))
        if cap_live is not None and cap_birth is not None and cap_birth > 0:
            capacity_ratio = round_float(min(max(cap_live / cap_birth, 0.0), 1.0))
        else:
            capacity_ratio = pd.NA

        # ── Component 2: Rigidity Ratio ──────────────────────────────────────
        rig_live  = to_float(row.get("rigidity_live"))
        rig_birth = to_float(row.get("rigidity_birth"))
        if rig_live is not None and rig_birth is not None and rig_birth > 0:
            rigidity_ratio = round_float(min(max(rig_live / rig_birth, 0.0), 1.0))
        else:
            rigidity_ratio = pd.NA

        # ── Component 3: Fatigue Inverse (population-normalized) ─────────────
        # fatigue_birth = 0 for every zone; normalize fatigue_live against the
        # maximum observed fatigue across all cases in this run.
        fat_live = to_float(row.get("fatigue_live"))
        if fat_live is not None and fatigue_pop_max is not None and fatigue_pop_max > 0:
            fatigue_inverse = round_float(min(max(1.0 - fat_live / fatigue_pop_max, 0.0), 1.0))
        else:
            fatigue_inverse = pd.NA

        # ── Component 4: Recovery Ratio (population-normalized) ──────────────
        # recovery_birth = 0 for every zone; normalize recovery_live against the
        # maximum observed recovery across all cases in this run.
        rec_live = to_float(row.get("recovery_live"))
        if rec_live is not None and recovery_pop_max is not None and recovery_pop_max > 0:
            recovery_ratio = round_float(min(max(rec_live / recovery_pop_max, 0.0), 1.0))
        else:
            recovery_ratio = pd.NA

        # ── Component 5: Stress Availability ─────────────────────────────────
        # rdm_v16_stress_utilization_current is stored as a 0-100 percentage.
        # Divide by 100 to convert to a [0, 1] fraction, then invert.
        stress_pct = to_float(row.get("rdm_v16_stress_utilization_current"))
        if stress_pct is not None:
            stress_availability = round_float(min(max(1.0 - stress_pct / 100.0, 0.0), 1.0))
        else:
            stress_availability = pd.NA

        # ── ZSS Formula ───────────────────────────────────────────────────────
        components = [
            to_float(capacity_ratio),
            to_float(rigidity_ratio),
            to_float(fatigue_inverse),
            to_float(recovery_ratio),
            to_float(stress_availability),
        ]
        if any(v is None for v in components):
            zone_strength_score = pd.NA
        else:
            cap, rig, fat, rec, stress = components
            zss_base = (
                0.30 * cap
                + 0.25 * rig
                + 0.20 * fat
                + 0.15 * rec
                + 0.10 * (cap * rec)
            )
            zone_strength_score = round_float(min(max(zss_base * stress, 0.0), 1.0) * 100.0)

        rows.append(
            {
                "analysis_run_utc": run_utc,
                "case_id": row.get("case_id"),
                "episode_id": row.get("episode_id"),
                "zone_id": row.get("zone_id"),
                "zone_mechanical_state": row.get("zone_mechanical_state"),
                "rdm_v16b4_zss_capacity_ratio": capacity_ratio,
                "rdm_v16b4_zss_rigidity_ratio": rigidity_ratio,
                "rdm_v16b4_zss_fatigue_inverse": fatigue_inverse,
                "rdm_v16b4_zss_recovery_ratio": recovery_ratio,
                "rdm_v16b4_zss_stress_availability": stress_availability,
                "rdm_v16b4_zone_strength_score": zone_strength_score,
                "research_only": True,
            }
        )

    return pd.DataFrame(rows)


# Legacy helpers kept for any external callers; not used by the corrected
# build_zone_strength_profile above.

def ratio_or_na(numerator: Any, denominator: Any) -> Any:
    numerator_value = to_float(numerator)
    denominator_value = to_float(denominator)
    if numerator_value is None or denominator_value is None or denominator_value == 0:
        return pd.NA
    return round_float(numerator_value / denominator_value)


def fatigue_inverse_or_na(fatigue_current: Any) -> Any:
    fatigue_value = to_float(fatigue_current)
    if fatigue_value is None:
        return pd.NA
    return round_float(1.0 - (fatigue_value / 100.0))


def stress_availability_or_na(stress_utilization: Any) -> Any:
    stress_value = to_float(stress_utilization)
    if stress_value is None:
        return pd.NA
    bounded_stress = min(max(stress_value, 0.0), 1.0)
    return round_float(1.0 - bounded_stress)


def zone_strength_score_or_na(
    capacity_ratio: Any,
    rigidity_ratio: Any,
    fatigue_inverse: Any,
    recovery_ratio: Any,
    stress_availability: Any,
) -> Any:
    values = [
        to_float(capacity_ratio),
        to_float(rigidity_ratio),
        to_float(fatigue_inverse),
        to_float(recovery_ratio),
        to_float(stress_availability),
    ]
    if any(value is None for value in values):
        return pd.NA
    cap, rig, fat, rec, stress = values
    zss_base = (
        0.30 * cap
        + 0.25 * rig
        + 0.20 * fat
        + 0.15 * rec
        + 0.10 * (cap * rec)
    )
    return round_float(zss_base * stress * 100.0)


def build_zone_vs_attacker_profile(
    strength_df: pd.DataFrame,
    attacker_df: pd.DataFrame,
    results_df: pd.DataFrame,
    run_utc: str,
) -> pd.DataFrame:
    """
    RDM V1.6-B4-B — Zone Strength vs Attacker Force.

    Merges zone_strength_profile and zone_attacker_evolution on case_id.
    Computes:
      attacker_force_score  — composite 0-100 score from five attacker metrics
      force_ratio           — attacker_force_score / zone_strength_score

    Attacker Force Score formula (all inputs normalized to [0,1] then weighted):

      AFS_base =
          0.40 * force_mean_zone_normalized_norm    (primary sustained force)
        + 0.25 * force_peak_zone_normalized_norm    (peak attack capacity)
        + 0.20 * persistence_max_norm               (sustained pressure duration)
        + 0.10 * attempt_count_norm                 (engagement frequency)
        + 0.05 * trend_slope_norm                   (trajectory; NaN -> 0)

      attacker_force_score = AFS_base * 100  (range [0, 100])

    Normalization: population max for each metric (computed within this run).
    Trend slope uses min-max normalization over the valid (non-NaN) population.
    NaN input for any component -> that component contributes 0.

    force_ratio = attacker_force_score / zone_strength_score.
    If zone_strength_score <= 0 or NaN: force_ratio = NaN.

    Research only.  Does not affect scoring, lifecycle, replay, or dashboard.
    """
    if strength_df.empty or attacker_df.empty:
        return pd.DataFrame()

    # ── Prepare lookup dicts keyed by case_id ────────────────────────────────
    str_idx = strength_df.set_index("case_id").to_dict("index")
    att_idx = attacker_df.set_index("case_id").to_dict("index")
    res_idx = results_df.set_index("case_id").to_dict("index") if (
        not results_df.empty and "case_id" in results_df.columns
    ) else {}

    # ── Population normalization denominators ─────────────────────────────────
    def _pop_max(df: pd.DataFrame, col: str) -> float:
        s = pd.to_numeric(df[col], errors="coerce")
        v = float(s.dropna().max()) if not s.dropna().empty else None
        return v if v is not None and v > 0 else None

    def _pop_minmax(df: pd.DataFrame, col: str):
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if s.empty:
            return None, None
        return float(s.min()), float(s.max())

    denom_force_mean  = _pop_max(attacker_df, "rdm_v16b_attacker_force_zone_normalized")
    denom_force_peak  = _pop_max(attacker_df, "rdm_v16b_attacker_force_peak_zone_normalized")
    denom_persistence = _pop_max(attacker_df, "rdm_v16b_attacker_persistence_max")
    denom_attempts    = _pop_max(attacker_df, "rdm_v16b_force_lull_attempt_count")
    slope_min, slope_max = _pop_minmax(
        attacker_df, "rdm_v16b_force_lull_attempt_force_trend_slope"
    )
    slope_range = (slope_max - slope_min) if (
        slope_min is not None and slope_max is not None
        and slope_max > slope_min
    ) else None

    # ── Build output rows ─────────────────────────────────────────────────────
    rows = []
    all_case_ids = sorted(set(list(str_idx.keys()) + list(att_idx.keys())))

    for case_id in all_case_ids:
        s_row  = str_idx.get(case_id, {})
        a_row  = att_idx.get(case_id, {})
        r_row  = res_idx.get(case_id, {})

        zss = to_float(s_row.get("rdm_v16b4_zone_strength_score"))

        # ── Normalize each attacker component to [0, 1] ──────────────────────
        def _norm(raw_val: Any, denom: float) -> float:
            v = to_float(raw_val)
            if v is None or denom is None:
                return 0.0
            return min(max(v / denom, 0.0), 1.0)

        def _norm_minmax(raw_val: Any) -> float:
            v = to_float(raw_val)
            if v is None or slope_range is None:
                return 0.0          # NaN or no range -> no trend contribution
            return min(max((v - slope_min) / slope_range, 0.0), 1.0)

        c_force_mean  = _norm(a_row.get("rdm_v16b_attacker_force_zone_normalized"), denom_force_mean)
        c_force_peak  = _norm(a_row.get("rdm_v16b_attacker_force_peak_zone_normalized"), denom_force_peak)
        c_persistence = _norm(a_row.get("rdm_v16b_attacker_persistence_max"), denom_persistence)
        c_attempts    = _norm(a_row.get("rdm_v16b_force_lull_attempt_count"), denom_attempts)
        c_trend_slope = _norm_minmax(a_row.get("rdm_v16b_force_lull_attempt_force_trend_slope"))

        afs_base = (
            0.40 * c_force_mean
            + 0.25 * c_force_peak
            + 0.20 * c_persistence
            + 0.10 * c_attempts
            + 0.05 * c_trend_slope
        )
        attacker_force_score = round_float(min(max(afs_base, 0.0), 1.0) * 100.0)

        # ── Force ratio ───────────────────────────────────────────────────────
        if zss is not None and zss > 0 and attacker_force_score is not None:
            force_ratio = round_float(attacker_force_score / zss)
        else:
            force_ratio = pd.NA

        rows.append({
            "analysis_run_utc": run_utc,
            "case_id": case_id,
            "episode_id": s_row.get("episode_id") or a_row.get("episode_id"),
            "zone_id": s_row.get("zone_id") or a_row.get("zone_id"),
            "zone_mechanical_state": (
                s_row.get("zone_mechanical_state")
                or r_row.get("zone_mechanical_state")
            ),
            # Zone strength (from B4-A)
            "rdm_v16b4_zone_strength_score": zss,
            # Attacker force components (normalized, for transparency)
            "rdm_v16b4_afs_force_mean_norm":  round_float(c_force_mean),
            "rdm_v16b4_afs_force_peak_norm":  round_float(c_force_peak),
            "rdm_v16b4_afs_persistence_norm": round_float(c_persistence),
            "rdm_v16b4_afs_attempts_norm":    round_float(c_attempts),
            "rdm_v16b4_afs_trend_slope_norm": round_float(c_trend_slope),
            # Composite score and ratio
            "rdm_v16b4_attacker_force_score": attacker_force_score,
            "rdm_v16b4_force_ratio":          force_ratio,
            "research_only": True,
        })

    return pd.DataFrame(rows)


def build_zone_reinforcement_profile(
    results_df: pd.DataFrame,
    run_utc: str,
) -> pd.DataFrame:
    """
    RDM V1.6-B6 — Elastic Reinforcement Physics.

    Measures structural reinforcement: the phenomenon where a zone's
    mechanical properties (capacity, rigidity) exceed their birth-state
    baseline under sustained attacker pressure.

    This captures the ELASTIC ZONE superpower missed by ZSS: when a zone
    runs at maximum recovery with zero fatigue accumulation, it actively
    grows its structural reserve beyond its original birth state.

    Fields
    ------
    rdm_v16b6_capacity_growth_factor
        capacity_live / capacity_birth.  > 1 = grew beyond birth.

    rdm_v16b6_capacity_growth_pct
        (capacity_live - capacity_birth) / capacity_birth * 100.
        Negative = degraded.  Positive = reinforced.

    rdm_v16b6_rigidity_growth_factor
        rigidity_live / rigidity_birth.  > 1 = grew beyond birth.

    rdm_v16b6_rigidity_growth_pct
        (rigidity_live - rigidity_birth) / rigidity_birth * 100.

    rdm_v16b6_reinforcement_score  [0 – 100]
        Composite score from four components:
          0.40 * capacity_excess_normalized
          0.40 * rigidity_excess_normalized
          0.15 * recovery_live / recovery_pop_max
          0.05 * (1 - fatigue_live / fatigue_pop_max)
        Where *_excess = max(factor - 1, 0), normalized against pop max.

    rdm_v16b6_reinforcement_mode
        STRONG_REINFORCEMENT  : cap_factor > 1.10 AND rig_factor > 1.10
        MODERATE_REINFORCEMENT: cap_factor > 1.0  OR  rig_factor > 1.0
        NO_REINFORCEMENT      : neither exceeds birth baseline

    Research only.  Does not affect scoring, lifecycle, replay, or dashboard.
    """
    # Reinforcement mode thresholds
    _STRONG_THRESHOLD   = 1.10
    _MODERATE_THRESHOLD = 1.00

    if results_df.empty:
        return pd.DataFrame()

    # ── Population denominators for normalization ─────────────────────────────
    def _pop_max(col: str) -> float:
        s = pd.to_numeric(results_df[col], errors="coerce").dropna()
        v = float(s.max()) if not s.empty else None
        return v if v is not None and v > 0 else None

    def _pop_excess_max(live_col: str, birth_col: str) -> float:
        liv = pd.to_numeric(results_df[live_col], errors="coerce")
        bir = pd.to_numeric(results_df[birth_col], errors="coerce")
        excess = ((liv / bir) - 1.0).clip(lower=0.0).dropna()
        v = float(excess.max()) if not excess.empty else None
        return v if v is not None and v > 0 else None

    cap_excess_max  = _pop_excess_max("capacity_live", "capacity_birth")
    rig_excess_max  = _pop_excess_max("rigidity_live",  "rigidity_birth")
    recovery_max    = _pop_max("recovery_live")
    fatigue_max     = _pop_max("fatigue_live")

    res_idx = results_df.set_index("case_id").to_dict("index") if (
        "case_id" in results_df.columns
    ) else {}

    rows = []

    for case_id, r_row in res_idx.items():

        cap_live  = to_float(r_row.get("capacity_live"))
        cap_birth = to_float(r_row.get("capacity_birth"))
        rig_live  = to_float(r_row.get("rigidity_live"))
        rig_birth = to_float(r_row.get("rigidity_birth"))
        rec_live  = to_float(r_row.get("recovery_live"))
        fat_live  = to_float(r_row.get("fatigue_live"))

        # ── Growth factors (raw, uncapped) ────────────────────────────────────
        if cap_live is not None and cap_birth is not None and cap_birth > 0:
            cap_factor  = cap_live / cap_birth
            cap_pct     = round_float((cap_live - cap_birth) / cap_birth * 100.0)
        else:
            cap_factor = pd.NA
            cap_pct    = pd.NA

        if rig_live is not None and rig_birth is not None and rig_birth > 0:
            rig_factor = rig_live / rig_birth
            rig_pct    = round_float((rig_live - rig_birth) / rig_birth * 100.0)
        else:
            rig_factor = pd.NA
            rig_pct    = pd.NA

        # ── Reinforcement score ───────────────────────────────────────────────
        cap_excess = max(float(cap_factor) - 1.0, 0.0) if isinstance(cap_factor, float) else 0.0
        rig_excess = max(float(rig_factor) - 1.0, 0.0) if isinstance(rig_factor, float) else 0.0

        cap_excess_norm = min(cap_excess / cap_excess_max, 1.0) if cap_excess_max else 0.0
        rig_excess_norm = min(rig_excess / rig_excess_max, 1.0) if rig_excess_max else 0.0

        rec_norm = min(float(rec_live) / recovery_max, 1.0) if (
            rec_live is not None and recovery_max
        ) else 0.0

        fat_inv = min(max(1.0 - float(fat_live) / fatigue_max, 0.0), 1.0) if (
            fat_live is not None and fatigue_max
        ) else 1.0  # no fatigue data → full contribution

        rein_raw = (
            0.40 * cap_excess_norm
            + 0.40 * rig_excess_norm
            + 0.15 * rec_norm
            + 0.05 * fat_inv
        )
        reinforcement_score = round_float(min(max(rein_raw, 0.0), 1.0) * 100.0)

        # ── Reinforcement mode ────────────────────────────────────────────────
        cf = float(cap_factor) if isinstance(cap_factor, float) else 0.0
        rf = float(rig_factor) if isinstance(rig_factor, float) else 0.0

        if cf > _STRONG_THRESHOLD and rf > _STRONG_THRESHOLD:
            reinforcement_mode = "STRONG_REINFORCEMENT"
        elif cf > _MODERATE_THRESHOLD or rf > _MODERATE_THRESHOLD:
            reinforcement_mode = "MODERATE_REINFORCEMENT"
        else:
            reinforcement_mode = "NO_REINFORCEMENT"

        rows.append({
            "analysis_run_utc": run_utc,
            "case_id": case_id,
            "episode_id": r_row.get("episode_id"),
            "zone_id": r_row.get("zone_id"),
            "zone_mechanical_state": r_row.get("zone_mechanical_state"),
            "rdm_v16b6_capacity_growth_factor":   round_float(cap_factor) if isinstance(cap_factor, float) else pd.NA,
            "rdm_v16b6_capacity_growth_pct":      cap_pct,
            "rdm_v16b6_rigidity_growth_factor":   round_float(rig_factor) if isinstance(rig_factor, float) else pd.NA,
            "rdm_v16b6_rigidity_growth_pct":      rig_pct,
            "rdm_v16b6_reinforcement_score":      reinforcement_score,
            "rdm_v16b6_reinforcement_mode":       reinforcement_mode,
            "research_only": True,
        })

    return pd.DataFrame(rows)


def build_attacker_conversion_profile(
    results_df: pd.DataFrame,
    attacker_df: pd.DataFrame,
    run_utc: str,
) -> pd.DataFrame:
    """
    RDM V1.6-B7 — Attacker Conversion Physics.

    Measures how efficiently attacker force is converted into actual zone
    structural damage.  High conversion = attacker force successfully
    degraded the zone.  Low conversion = large force delivered, little or
    no structural damage produced (zone absorbed or reflected the force).

    This is the process-level metric that complements B6 (state-level
    reinforcement).  Where B6 asks "did the zone grow?", B7 asks "how
    much damage did the attacker actually produce per unit of force?".

    attacker_force_input
        Total cumulative force delivered:
        rdm_v16b_attacker_force_mean_at_touch * rdm_v16b_attacker_interaction_count.
        Represents the total mechanical energy applied to the zone.

    rdm_v16b7_fatigue_generated
        fatigue_live − fatigue_birth.  Always >= 0 (fatigue_birth == 0 for
        all observed zones).  Measures accumulated internal stress damage.

    rdm_v16b7_rigidity_damage
        rigidity_birth − rigidity_live.  Positive = zone lost structural
        rigidity.  Negative = zone grew rigidity beyond birth (reinforcement).

    rdm_v16b7_capacity_damage
        capacity_birth − capacity_live.  Positive = capacity consumed.
        Negative = capacity grew beyond birth (reinforcement).

    rdm_v16b7_conversion_efficiency_fatigue / _rigidity / _capacity
        Raw signed ratio: damage / attacker_force_input.
        Negative values indicate structural reinforcement (anti-damage).
        Preserved unsigned for directional research use.

    rdm_v16b7_attacker_conversion_score  [0 – 100]
        Composite conversion score.  Weights:
          0.40 * fatigue_efficiency_normalized
          0.35 * rigidity_efficiency_normalized   (clamped >= 0)
          0.25 * capacity_efficiency_normalized   (clamped >= 0)
        Normalized against population max of each positive-clamped component.
        High score: attacker force successfully converts to structural damage.
        Low score: large force produces little or no zone damage.

    rdm_v16b7_conversion_mode
        HIGH_CONVERSION    : score >= 50
        NORMAL_CONVERSION  : 15 <= score < 50
        INEFFICIENT_ATTACKER: score < 15

    Research only.  No scoring, lifecycle, replay, or dashboard impact.
    """
    _HIGH_THRESHOLD    = 50.0
    _NORMAL_THRESHOLD  = 15.0

    if results_df.empty or attacker_df.empty:
        return pd.DataFrame()

    # ── Merge zone structural data with attacker force data ───────────────────
    res_idx = results_df.set_index("case_id").to_dict("index") if (
        "case_id" in results_df.columns
    ) else {}
    att_idx = attacker_df.set_index("case_id").to_dict("index") if (
        "case_id" in attacker_df.columns
    ) else {}

    if not res_idx or not att_idx:
        return pd.DataFrame()

    # ── Compute raw efficiencies for population normalisation ─────────────────
    raw_fat_effs: list[float] = []
    raw_rig_effs: list[float] = []
    raw_cap_effs: list[float] = []

    for case_id, r_row in res_idx.items():
        a_row = att_idx.get(case_id, {})

        force_mean  = to_float(a_row.get("rdm_v16b_attacker_force_mean_at_touch")) or 0.0
        force_count = to_float(a_row.get("rdm_v16b_attacker_interaction_count")) or 0.0
        force_input = force_mean * force_count
        if force_input <= 0:
            continue

        fat_live  = to_float(r_row.get("fatigue_live"))  or 0.0
        fat_birth = to_float(r_row.get("fatigue_birth")) or 0.0
        rig_live  = to_float(r_row.get("rigidity_live"))
        rig_birth = to_float(r_row.get("rigidity_birth"))
        cap_live  = to_float(r_row.get("capacity_live"))
        cap_birth = to_float(r_row.get("capacity_birth"))

        fat_gen = fat_live - fat_birth
        rig_dam = (rig_birth - rig_live) if (rig_live is not None and rig_birth is not None) else 0.0
        cap_dam = (cap_birth - cap_live) if (cap_live is not None and cap_birth is not None) else 0.0

        raw_fat_effs.append(max(fat_gen / force_input, 0.0))
        raw_rig_effs.append(max(rig_dam / force_input, 0.0))
        raw_cap_effs.append(max(cap_dam / force_input, 0.0))

    def _safe_max(vals: list[float]) -> float | None:
        positives = [v for v in vals if v > 0]
        if not positives:
            return None
        m = max(positives)
        return m if m > 0 else None

    pop_max_fat_eff = _safe_max(raw_fat_effs)
    pop_max_rig_eff = _safe_max(raw_rig_effs)
    pop_max_cap_eff = _safe_max(raw_cap_effs)

    # ── Per-case rows ─────────────────────────────────────────────────────────
    rows = []

    for case_id, r_row in res_idx.items():
        a_row = att_idx.get(case_id, {})

        force_mean  = to_float(a_row.get("rdm_v16b_attacker_force_mean_at_touch")) or 0.0
        force_count = to_float(a_row.get("rdm_v16b_attacker_interaction_count")) or 0.0
        force_input = force_mean * force_count

        fat_live  = to_float(r_row.get("fatigue_live"))  or 0.0
        fat_birth = to_float(r_row.get("fatigue_birth")) or 0.0
        rig_live  = to_float(r_row.get("rigidity_live"))
        rig_birth = to_float(r_row.get("rigidity_birth"))
        cap_live  = to_float(r_row.get("capacity_live"))
        cap_birth = to_float(r_row.get("capacity_birth"))

        fat_gen = fat_live - fat_birth
        rig_dam = (rig_birth - rig_live) if (rig_live is not None and rig_birth is not None) else 0.0
        cap_dam = (cap_birth - cap_live) if (cap_live is not None and cap_birth is not None) else 0.0

        # ── Raw signed efficiency ratios ──────────────────────────────────────
        if force_input > 0:
            eff_fat_raw = fat_gen / force_input
            eff_rig_raw = rig_dam / force_input
            eff_cap_raw = cap_dam / force_input
        else:
            eff_fat_raw = 0.0
            eff_rig_raw = 0.0
            eff_cap_raw = 0.0

        # ── Normalized components for composite score (clamp negatives to 0) ─
        pos_fat = max(eff_fat_raw, 0.0)
        pos_rig = max(eff_rig_raw, 0.0)
        pos_cap = max(eff_cap_raw, 0.0)

        fat_norm = min(pos_fat / pop_max_fat_eff, 1.0) if pop_max_fat_eff else 0.0
        rig_norm = min(pos_rig / pop_max_rig_eff, 1.0) if pop_max_rig_eff else 0.0
        cap_norm = min(pos_cap / pop_max_cap_eff, 1.0) if pop_max_cap_eff else 0.0

        # ── Composite conversion score ────────────────────────────────────────
        score_raw = (
            0.40 * fat_norm
            + 0.35 * rig_norm
            + 0.25 * cap_norm
        )
        conversion_score = round_float(min(max(score_raw, 0.0), 1.0) * 100.0)

        # ── Conversion mode ───────────────────────────────────────────────────
        s = float(conversion_score) if isinstance(conversion_score, float) else 0.0
        if s >= _HIGH_THRESHOLD:
            conversion_mode = "HIGH_CONVERSION"
        elif s >= _NORMAL_THRESHOLD:
            conversion_mode = "NORMAL_CONVERSION"
        else:
            conversion_mode = "INEFFICIENT_ATTACKER"

        rows.append({
            "analysis_run_utc":                       run_utc,
            "case_id":                                case_id,
            "episode_id":                             r_row.get("episode_id"),
            "zone_id":                                r_row.get("zone_id"),
            "zone_mechanical_state":                  r_row.get("zone_mechanical_state"),
            "rdm_v16b7_attacker_force_input":         round_float(force_input),
            "rdm_v16b7_fatigue_generated":            round_float(fat_gen),
            "rdm_v16b7_rigidity_damage":              round_float(rig_dam),
            "rdm_v16b7_capacity_damage":              round_float(cap_dam),
            "rdm_v16b7_conversion_efficiency_fatigue":  round_float(eff_fat_raw),
            "rdm_v16b7_conversion_efficiency_rigidity": round_float(eff_rig_raw),
            "rdm_v16b7_conversion_efficiency_capacity": round_float(eff_cap_raw),
            "rdm_v16b7_attacker_conversion_score":    conversion_score,
            "rdm_v16b7_conversion_mode":              conversion_mode,
            "research_only":                          True,
        })

    return pd.DataFrame(rows)


def build_force_allocation_profile(
    results_df: pd.DataFrame,
    attacker_df: pd.DataFrame,
    run_utc: str,
) -> pd.DataFrame:
    """
    RDM V1.6-B7.5-B — Force Allocation Physics.

    Measures how attacker force is split between two structural channels:

    DAMAGE CHANNEL  — force that converts into structural degradation:
      fatigue accumulation, rigidity loss, capacity loss.

    GROWTH CHANNEL  — force that converts into structural reinforcement:
      rigidity gain, capacity gain beyond birth baseline.

    B7 established: force ≠ damage (conversion can be zero).
    B7.5-A established: growth rate is a symptom, not the mechanism.
    B7.5-B establishes: the force split between channels is the bridge variable.

    Fields
    ------
    rdm_v16b75b_fatigue_generated
        fatigue_live - fatigue_birth.  Always >= 0.

    rdm_v16b75b_rigidity_damage / rdm_v16b75b_capacity_damage
        Signed raw: rigidity_birth - rigidity_live, capacity_birth - capacity_live.
        Positive = zone lost structure.  Negative = zone gained structure.

    rdm_v16b75b_rigidity_growth / rdm_v16b75b_capacity_growth
        Signed raw: rigidity_live - rigidity_birth, capacity_live - capacity_birth.
        Mirror of the damage fields; positive = growth.

    rdm_v16b75b_total_damage
        Positive-clamped sum: max(rigidity_damage, 0) + max(capacity_damage, 0)
        + fatigue_generated.  Represents total structural loss volume.

    rdm_v16b75b_total_growth
        Positive-clamped sum: max(rigidity_growth, 0) + max(capacity_growth, 0).
        Represents total structural gain volume.

    rdm_v16b75b_attacker_force_input
        force_mean_at_touch * interaction_count.  Total cumulative force delivered.

    rdm_v16b75b_damage_allocation_ratio
        total_damage / attacker_force_input.  How much structural loss per unit force.

    rdm_v16b75b_growth_allocation_ratio
        total_growth / attacker_force_input.  How much structural gain per unit force.

    rdm_v16b75b_force_allocation_balance
        growth_allocation_ratio - damage_allocation_ratio.
        Positive = growth dominates.  Negative = damage dominates.
        Near zero = force produced neither meaningful growth nor damage.

    rdm_v16b75b_force_allocation_mode
        GROWTH_DOMINANT  : balance >  0.010
        BALANCED         : balance >= -0.010 and <= 0.010
        DAMAGE_DOMINANT  : balance < -0.010

    Research only.  No scoring, lifecycle, replay, or dashboard impact.
    """
    _DOMINANT_THRESHOLD = 0.010

    if results_df.empty or attacker_df.empty:
        return pd.DataFrame()

    res_idx = results_df.set_index("case_id").to_dict("index") if (
        "case_id" in results_df.columns
    ) else {}
    att_idx = attacker_df.set_index("case_id").to_dict("index") if (
        "case_id" in attacker_df.columns
    ) else {}

    if not res_idx or not att_idx:
        return pd.DataFrame()

    rows = []

    for case_id, r in res_idx.items():
        a = att_idx.get(case_id, {})

        fat_live  = to_float(r.get("fatigue_live"))  or 0.0
        fat_birth = to_float(r.get("fatigue_birth")) or 0.0
        rig_live  = to_float(r.get("rigidity_live"))
        rig_birth = to_float(r.get("rigidity_birth"))
        cap_live  = to_float(r.get("capacity_live"))
        cap_birth = to_float(r.get("capacity_birth"))

        force_mean  = to_float(a.get("rdm_v16b_attacker_force_mean_at_touch")) or 0.0
        force_count = to_float(a.get("rdm_v16b_attacker_interaction_count")) or 0.0
        force_input = force_mean * force_count

        # ── Raw signed damage/growth fields ───────────────────────────────────
        fat_gen  = fat_live - fat_birth
        rig_raw  = (rig_birth - rig_live) if (rig_live is not None and rig_birth is not None) else 0.0
        cap_raw  = (cap_birth - cap_live) if (cap_live is not None and cap_birth is not None) else 0.0

        # ── Positive-clamped totals (damage vs growth) ────────────────────────
        rig_damage_pos = max(rig_raw, 0.0)
        cap_damage_pos = max(cap_raw, 0.0)
        rig_growth_pos = max(-rig_raw, 0.0)
        cap_growth_pos = max(-cap_raw, 0.0)

        total_damage = fat_gen + rig_damage_pos + cap_damage_pos
        total_growth = rig_growth_pos + cap_growth_pos

        # ── Allocation ratios ─────────────────────────────────────────────────
        if force_input > 0:
            damage_alloc = total_damage / force_input
            growth_alloc = total_growth / force_input
        else:
            damage_alloc = 0.0
            growth_alloc = 0.0

        balance = growth_alloc - damage_alloc

        # ── Mode classification ───────────────────────────────────────────────
        if balance > _DOMINANT_THRESHOLD:
            mode = "GROWTH_DOMINANT"
        elif balance < -_DOMINANT_THRESHOLD:
            mode = "DAMAGE_DOMINANT"
        else:
            mode = "BALANCED"

        rows.append({
            "analysis_run_utc":                        run_utc,
            "case_id":                                 case_id,
            "episode_id":                              r.get("episode_id"),
            "zone_id":                                 r.get("zone_id"),
            "zone_mechanical_state":                   r.get("zone_mechanical_state"),
            "rdm_v16b75b_fatigue_generated":           round_float(fat_gen),
            "rdm_v16b75b_rigidity_damage":             round_float(rig_raw),
            "rdm_v16b75b_capacity_damage":             round_float(cap_raw),
            "rdm_v16b75b_rigidity_growth":             round_float(-rig_raw),
            "rdm_v16b75b_capacity_growth":             round_float(-cap_raw),
            "rdm_v16b75b_total_damage":                round_float(total_damage),
            "rdm_v16b75b_total_growth":                round_float(total_growth),
            "rdm_v16b75b_attacker_force_input":        round_float(force_input),
            "rdm_v16b75b_damage_allocation_ratio":     round_float(damage_alloc),
            "rdm_v16b75b_growth_allocation_ratio":     round_float(growth_alloc),
            "rdm_v16b75b_force_allocation_balance":    round_float(balance),
            "rdm_v16b75b_force_allocation_mode":       mode,
            "research_only":                           True,
        })

    return pd.DataFrame(rows)


# ==================================================
# RDM V1.6-B8 — Zone Visit Timeline helpers
# ==================================================

def _parse_visit_spans(atk_row: dict) -> list:
    """Parse force-lull or attacker attempt row spans into (start, end) tuples.

    Uses rdm_v16b_force_lull_attempt_row_spans (finest segmentation) as primary.
    Falls back to rdm_v16b_attacker_attempt_row_spans when lull data is absent.
    Span format stored as string: "start-end|start-end|..."
    Returns empty list when both fields are NaN or absent.
    """
    for key in ("rdm_v16b_force_lull_attempt_row_spans",
                "rdm_v16b_attacker_attempt_row_spans"):
        raw = str(atk_row.get(key) or "").strip()
        if raw and raw.lower() not in ("", "nan", "none"):
            spans = []
            for part in raw.split("|"):
                part = part.strip()
                if "-" in part:
                    try:
                        lo, hi = part.split("-", 1)
                        spans.append((int(lo), int(hi)))
                    except ValueError:
                        continue
            if spans:
                return spans
    return []


def _compute_touch_spans(evo_case: pd.DataFrame, lull_gap: int = 3) -> list:
    """Derive visit spans from live evolution activity signals.

    Priority 1: rows where zone_touch_flag OR inside_zone_flag is True
    Priority 2: rows where evolution_state is not LIVE_DORMANT
    (covers cases where zones are active / ruptured but touch flags are not set)

    Groups consecutive active rows into visit windows.  A visit boundary is
    declared when there is a gap of at least lull_gap rows with no activity,
    matching the B3.5-B lull threshold.

    This is the fallback when pre-computed span strings are NaN.
    Returns list of (start_row, end_row) tuples.
    """
    # Build activity mask: touch/inside flags first, then evolution state
    touch_series   = pd.to_numeric(evo_case["zone_touch_flag"],  errors="coerce").fillna(0).astype(bool)
    inside_series  = pd.to_numeric(evo_case["inside_zone_flag"], errors="coerce").fillna(0).astype(bool)
    dormant_states = {"LIVE_DORMANT", ""}
    active_series  = ~evo_case["evolution_state"].astype(str).isin(dormant_states)

    activity_mask = touch_series | inside_series | active_series

    active_rows = (
        evo_case.loc[activity_mask, "row_index"]
        .dropna()
        .astype(int)
        .sort_values()
        .tolist()
    )
    if not active_rows:
        return []

    spans: list = []
    span_start = active_rows[0]
    span_end   = active_rows[0]

    for i in range(1, len(active_rows)):
        gap = active_rows[i] - active_rows[i - 1]
        if gap > lull_gap:
            spans.append((span_start, span_end))
            span_start = active_rows[i]
        span_end = active_rows[i]

    spans.append((span_start, span_end))
    return spans


def _classify_visit(
    rig_v: float,
    cap_v: float,
    fat_v: float,
    rig_birth: float,
    cap_birth: float,
    fat_birth: float,
    prev_rig: float,
    prev_cap: float,
    prev_fat: float,
    inside_count: int,
    max_pen: float,
    reclaim: bool,
) -> str:
    """Classify a single zone visit for research purposes.

    Priority order: BREAKDOWN > GROWTH > DAMAGE > RECLAIM > REFLECTION > ABSORPTION > UNKNOWN

    Classification is research-only — no signal, entry, or execution logic.
    """
    # BREAKDOWN: severe structural loss (rigidity or capacity < 50% of birth)
    if (rig_birth > 0 and rig_v < rig_birth * 0.50) or \
       (cap_birth > 0 and cap_v < cap_birth * 0.50):
        return "BREAKDOWN"

    # GROWTH: zone structurally grew beyond birth baseline (ELASTIC reinforcement)
    if rig_v > rig_birth and cap_v > cap_birth:
        return "GROWTH"

    # DAMAGE: meaningful new fatigue accumulated during this visit
    if fat_v > prev_fat + 0.5:
        return "DAMAGE"

    # RECLAIM: price returned to zone from outside (return_to_zone_flag seen)
    if reclaim:
        return "RECLAIM"

    # REFLECTION: zone touched/approached but not meaningfully entered
    if inside_count == 0 or max_pen < 0.05:
        return "REFLECTION"

    # ABSORPTION: entered zone with measurable penetration, structural state held
    if max_pen >= 0.05:
        return "ABSORPTION"

    return "UNKNOWN"


def build_zone_visit_timeline(
    results_df: pd.DataFrame,
    evolution_df: pd.DataFrame,
    attacker_df: pd.DataFrame,
    run_utc: str,
) -> pd.DataFrame:
    """
    RDM V1.6-B8 — Zone Visit Timeline.

    Creates a per-visit structural record for every zone interaction episode.
    Each row corresponds to one distinct attacker attempt (force-lull segmented),
    exposing structural state at the end of each visit and delta comparisons
    against birth state and the previous visit.

    Visit segmentation
    ------------------
    Primary:  rdm_v16b_force_lull_attempt_row_spans  (B3.5-B finest segmentation)
    Fallback: rdm_v16b_attacker_attempt_row_spans    (B3.5-A coarser segmentation)

    Structural metrics at visit
    ---------------------------
    Taken from the last live-evolution row within each span.
    Penetration is reconstructed as fleche_live * real_zone_width.
    omega_at_visit is approximated as sigma_at_visit * penetration_at_visit
    (validated in B7.6-D: r = 0.9935 with true omega).
    attacker_force_at_visit is the peak load_live observed in the span.

    Visit result classification (research-only, no signals)
    -------------------------------------------------------
    BREAKDOWN    rigidity or capacity < 50% of birth
    GROWTH       rigidity and capacity both exceed birth (ELASTIC reinforcement)
    DAMAGE       fatigue > previous visit + 0.5 (new structural fatigue)
    RECLAIM      return_to_zone_flag seen — price returned from outside zone
    REFLECTION   inside_count == 0 or max penetration < 0.05 units
    ABSORPTION   penetration >= 0.05 with no meaningful damage
    UNKNOWN      insufficient data for classification

    Research only. No scores, signals, entries, exits, or lifecycle changes.
    """
    if results_df.empty or evolution_df.empty or attacker_df.empty:
        return pd.DataFrame()

    # ── Index data for O(1) lookup ────────────────────────────────────────────
    evo_by_case: dict = {}
    for case_id, grp in evolution_df.groupby("case_id"):
        evo_by_case[case_id] = grp.sort_values("row_index").reset_index(drop=True)

    res_idx = results_df.set_index("case_id").to_dict("index") if (
        "case_id" in results_df.columns
    ) else {}

    atk_idx = attacker_df.set_index("case_id").to_dict("index") if (
        "case_id" in attacker_df.columns
    ) else {}

    rows: list = []

    for case_id, r in res_idx.items():
        evo_case = evo_by_case.get(case_id)
        if evo_case is None or evo_case.empty:
            continue

        a = atk_idx.get(case_id, {})
        spans = _parse_visit_spans(a)
        span_source = "force_lull_segments"
        if not spans:
            # Pre-computed spans are absent (NaN) — derive from live evolution
            # touch/inside flags using the B3.5-B lull gap threshold.
            spans = _compute_touch_spans(evo_case)
            span_source = "touch_flag_derived"
        if not spans:
            continue

        # Birth state
        rig_birth = to_float(r.get("rigidity_birth"))  or 35.0
        cap_birth = to_float(r.get("capacity_birth"))  or 30.0
        fat_birth = to_float(r.get("fatigue_birth"))   or 0.0
        rec_birth = to_float(r.get("recovery_birth"))  or 0.0
        hlt_birth = to_float(r.get("health_birth"))    or 70.0
        sig_birth = to_float(r.get("sigma_birth"))     or 0.0

        # Previous-visit state (starts at birth)
        prev_rig = rig_birth
        prev_cap = cap_birth
        prev_fat = fat_birth
        prev_hlt = hlt_birth

        for visit_idx, (span_start, span_end) in enumerate(spans, start=1):
            visit_rows = evo_case[
                (evo_case["row_index"] >= span_start) &
                (evo_case["row_index"] <= span_end)
            ]

            if visit_rows.empty:
                # No evolution data for this span — emit a minimal record
                rows.append({
                    "analysis_run_utc":          run_utc,
                    "case_id":                   case_id,
                    "episode_id":                r.get("episode_id"),
                    "zone_id":                   r.get("zone_id"),
                    "zone_mechanical_state":     r.get("zone_mechanical_state"),
                    "visit_index":               visit_idx,
                    "visit_start_row":           span_start,
                    "visit_end_row":             span_end,
                    "visit_start_time":          pd.NA,
                    "visit_end_time":            pd.NA,
                    "visit_duration_rows":       span_end - span_start + 1,
                    "rigidity_at_visit":         pd.NA,
                    "capacity_at_visit":         pd.NA,
                    "fatigue_at_visit":          pd.NA,
                    "recovery_at_visit":         pd.NA,
                    "sigma_at_visit":            pd.NA,
                    "health_at_visit":           pd.NA,
                    "penetration_at_visit":      pd.NA,
                    "max_penetration_at_visit":  pd.NA,
                    "omega_at_visit":            pd.NA,
                    "attacker_force_at_visit":   pd.NA,
                    "rigidity_change_from_birth":   pd.NA,
                    "capacity_change_from_birth":   pd.NA,
                    "fatigue_change_from_birth":    pd.NA,
                    "recovery_change_from_birth":   pd.NA,
                    "rigidity_change_from_previous":  pd.NA,
                    "capacity_change_from_previous":  pd.NA,
                    "fatigue_change_from_previous":   pd.NA,
                    "health_change_from_previous":    pd.NA,
                    "inside_zone_rows":          0,
                    "evolution_state_at_visit":  "NO_DATA",
                    "span_source":               span_source,
                    "visit_result":              "UNKNOWN",
                    "research_only":             True,
                })
                continue

            last_row  = visit_rows.iloc[-1]
            first_row = visit_rows.iloc[0]

            # Structural state at end of visit (last row in span)
            # Explicit None-check: preserves 0.0 (fully decayed) vs None (missing data).
            # The previous `or rig_birth` treated 0.0 as falsy, silently resetting
            # fully-decayed rigidity to birth value before the BREAKDOWN classifier saw it.
            _rig_raw = to_float(last_row.get("rigidity_live"))
            rig_v    = rig_birth if _rig_raw is None else _rig_raw
            cap_v = to_float(last_row.get("capacity_live"))  or cap_birth
            fat_v = to_float(last_row.get("fatigue_live"))   or 0.0
            rec_v = to_float(last_row.get("recovery_live"))  or 0.0
            hlt_v = to_float(last_row.get("health_live"))    or hlt_birth
            sig_v = to_float(last_row.get("sigma_live"))     or sig_birth
            fle_v = to_float(last_row.get("fleche_live"))    or 0.0
            zone_w = to_float(last_row.get("real_zone_width")) or 1.0

            penetration_v = fle_v * zone_w

            # Peak values during the visit
            fle_max  = pd.to_numeric(visit_rows["fleche_live"], errors="coerce").max()
            max_pen  = (float(fle_max) if pd.notna(fle_max) else 0.0) * zone_w
            sig_max  = pd.to_numeric(visit_rows["sigma_live"], errors="coerce").max()
            load_max = pd.to_numeric(visit_rows["load_live"], errors="coerce").max()
            load_max = float(load_max) if pd.notna(load_max) else 0.0

            # omega approximation: sigma_peak * max_penetration (from B7.6-D, r=0.9935)
            sig_max_f = float(sig_max) if pd.notna(sig_max) else sig_v
            omega_approx = sig_max_f * max_pen

            inside_count = int(
                pd.to_numeric(visit_rows["inside_zone_flag"], errors="coerce")
                .fillna(0).astype(bool).sum()
            )
            reclaim_flag = bool(
                pd.to_numeric(visit_rows["return_to_zone_flag"], errors="coerce")
                .fillna(0).astype(bool).any()
            )
            evo_state_v = str(last_row.get("evolution_state") or "")

            visit_result = _classify_visit(
                rig_v=rig_v, cap_v=cap_v, fat_v=fat_v,
                rig_birth=rig_birth, cap_birth=cap_birth, fat_birth=fat_birth,
                prev_rig=prev_rig, prev_cap=prev_cap, prev_fat=prev_fat,
                inside_count=inside_count,
                max_pen=max_pen,
                reclaim=reclaim_flag,
            )

            rows.append({
                "analysis_run_utc":          run_utc,
                "case_id":                   case_id,
                "episode_id":                r.get("episode_id"),
                "zone_id":                   r.get("zone_id"),
                "zone_mechanical_state":     r.get("zone_mechanical_state"),
                "visit_index":               visit_idx,
                "visit_start_row":           span_start,
                "visit_end_row":             span_end,
                "visit_start_time":          str(first_row.get("timestamp", "")),
                "visit_end_time":            str(last_row.get("timestamp", "")),
                "visit_duration_rows":       span_end - span_start + 1,
                "rigidity_at_visit":         round_float(rig_v),
                "capacity_at_visit":         round_float(cap_v),
                "fatigue_at_visit":          round_float(fat_v),
                "recovery_at_visit":         round_float(rec_v),
                "sigma_at_visit":            round_float(sig_v),
                "health_at_visit":           round_float(hlt_v),
                "penetration_at_visit":      round_float(penetration_v),
                "max_penetration_at_visit":  round_float(max_pen),
                "omega_at_visit":            round_float(omega_approx),
                "attacker_force_at_visit":   round_float(load_max),
                "rigidity_change_from_birth":   round_float(rig_v - rig_birth),
                "capacity_change_from_birth":   round_float(cap_v - cap_birth),
                "fatigue_change_from_birth":    round_float(fat_v - fat_birth),
                "recovery_change_from_birth":   round_float(rec_v - rec_birth),
                "rigidity_change_from_previous":  round_float(rig_v - prev_rig),
                "capacity_change_from_previous":  round_float(cap_v - prev_cap),
                "fatigue_change_from_previous":   round_float(fat_v - prev_fat),
                "health_change_from_previous":    round_float(hlt_v - prev_hlt),
                "inside_zone_rows":          inside_count,
                "evolution_state_at_visit":  evo_state_v,
                "span_source":               span_source,
                "visit_result":              visit_result,
                "research_only":             True,
            })

            prev_rig = rig_v
            prev_cap = cap_v
            prev_fat = fat_v
            prev_hlt = hlt_v

    return pd.DataFrame(rows)


# ==================================================
# RDM V1.6-B12.5 (Stage 2) — Post-Return Zone Visit Timeline (DYNAMIC)
# ADDITIVE companion to build_zone_visit_timeline. Writes a NEW file
# (zone_visit_timeline_dynamic.csv). Does NOT modify build_zone_visit_timeline
# or zone_visit_timeline.csv. Research only — no scores, signals, lifecycle.
# ==================================================

def build_zone_visit_timeline_dynamic(
    results_df: pd.DataFrame,
    evolution_df: pd.DataFrame,
    pre_return_timeline_df: pd.DataFrame,
    run_utc: str,
) -> pd.DataFrame:
    """
    RDM V1.6-B12.5 — Post-return zone visit timeline.

    Segments ONLY the post-return window — rows AFTER the return_to_zone_flag
    event, made available by the Stage-1 bounded window extension
    (return_row + 500, hard-capped) — into per-visit structural records.

    Reuses the EXACT pre-return aggregation/classification logic:
      - _compute_touch_spans  for visit segmentation (touch/inside/non-dormant
        activity with the B3.5-B 3-row lull gap)
      - last-row structural metrics + span peaks (penetration = fleche_live *
        real_zone_width, omega = sigma_peak * max_penetration, attacker_force =
        peak load_live)
      - _classify_visit        for BREAKDOWN/GROWTH/DAMAGE/RECLAIM/REFLECTION/
        ABSORPTION

    Differences vs build_zone_visit_timeline (all additive, no formula change):
      - Operates on the post-return slice only (row_index > return event row).
      - visit_index continues monotonically from the last pre-return visit_index
        for the case (N+1, N+2, ...), read from pre_return_timeline_df.
      - *_change_from_previous for the FIRST post-return visit is seeded from
        the last pre-return visit state (continuity across the return boundary);
        falls back to birth state when no pre-return visit exists.
      - post_return_flag is always True.
      - Returning zones whose attacker never re-engages (no post-return span)
        get ONE row with post_return_visit_count=0 and null metrics, so the
        zone is present in the file, not absent.

    Only returning zones (those with a return_to_zone_flag=True row in the
    evolution data) appear in this file; non-returning zones have no
    post-return window and are intentionally excluded.

    Research only. No scores, signals, entries, exits, or lifecycle changes.
    """
    if results_df.empty or evolution_df.empty:
        return pd.DataFrame()
    if "case_id" not in evolution_df.columns or "row_index" not in evolution_df.columns:
        return pd.DataFrame()

    # ── Index evolution rows per case ─────────────────────────────────────────
    evo_by_case: dict = {}
    for case_id, grp in evolution_df.groupby("case_id"):
        evo_by_case[case_id] = grp.sort_values("row_index").reset_index(drop=True)

    res_idx = results_df.set_index("case_id").to_dict("index") if (
        "case_id" in results_df.columns
    ) else {}

    # ── Last pre-return visit per case (visit_index continuity + derivative seed)
    last_visit_state: dict = {}
    if (
        pre_return_timeline_df is not None
        and not pre_return_timeline_df.empty
        and "case_id" in pre_return_timeline_df.columns
        and "visit_index" in pre_return_timeline_df.columns
    ):
        pre = pre_return_timeline_df.copy()
        pre["visit_index"] = pd.to_numeric(pre["visit_index"], errors="coerce")
        pre = pre.dropna(subset=["visit_index"])
        if not pre.empty:
            idx_max = pre.groupby("case_id")["visit_index"].idxmax()
            for cid, ix in idx_max.items():
                prow = pre.loc[ix]
                last_visit_state[cid] = {
                    "visit_index": int(prow.get("visit_index") or 0),
                    "rigidity":    to_float(prow.get("rigidity_at_visit")),
                    "capacity":    to_float(prow.get("capacity_at_visit")),
                    "fatigue":     to_float(prow.get("fatigue_at_visit")),
                    "health":      to_float(prow.get("health_at_visit")),
                }

    rows: list = []

    for case_id, r in res_idx.items():
        evo_case = evo_by_case.get(case_id)
        if evo_case is None or evo_case.empty:
            continue
        if "return_to_zone_flag" not in evo_case.columns:
            continue

        # Locate the return event row; only returning zones have a post-return
        # window. Use the earliest flagged row as the return boundary.
        return_mask = (
            pd.to_numeric(evo_case["return_to_zone_flag"], errors="coerce")
            .fillna(0).astype(bool)
        )
        if not bool(return_mask.any()):
            continue
        return_row_index = int(
            evo_case.loc[return_mask, "row_index"].astype(float).min()
        )

        post_rows = evo_case[
            pd.to_numeric(evo_case["row_index"], errors="coerce") > return_row_index
        ]

        # Birth state (same source/order as build_zone_visit_timeline)
        rig_birth = to_float(r.get("rigidity_birth")) or 35.0
        cap_birth = to_float(r.get("capacity_birth")) or 30.0
        fat_birth = to_float(r.get("fatigue_birth"))  or 0.0
        rec_birth = to_float(r.get("recovery_birth")) or 0.0
        hlt_birth = to_float(r.get("health_birth"))   or 70.0
        sig_birth = to_float(r.get("sigma_birth"))    or 0.0

        # visit_index continuation + previous-visit seed (continuity across return)
        seed = last_visit_state.get(case_id, {})
        base_visit_index = int(seed.get("visit_index") or 0)
        prev_rig = seed.get("rigidity") if seed.get("rigidity") is not None else rig_birth
        prev_cap = seed.get("capacity") if seed.get("capacity") is not None else cap_birth
        prev_fat = seed.get("fatigue")  if seed.get("fatigue")  is not None else fat_birth
        prev_hlt = seed.get("health")   if seed.get("health")   is not None else hlt_birth

        spans = _compute_touch_spans(post_rows) if not post_rows.empty else []

        identity = {
            "analysis_run_utc":      run_utc,
            "case_id":               case_id,
            "episode_id":            r.get("episode_id"),
            "zone_id":               r.get("zone_id"),
            "zone_mechanical_state": r.get("zone_mechanical_state"),
        }

        # Returning zone with no post-return activity: emit ONE null row so the
        # zone is present (attacker ran out of force / never re-engaged).
        if not spans:
            rows.append({
                **identity,
                "visit_index":               base_visit_index + 1,
                "post_return_flag":          True,
                "post_return_visit_count":   0,
                "visit_start_row":           pd.NA,
                "visit_end_row":             pd.NA,
                "visit_duration_rows":       pd.NA,
                "timestamp_start":           pd.NA,
                "timestamp_end":             pd.NA,
                "visit_result":              "NO_POST_RETURN_ACTIVITY",
                "rigidity_at_visit":         pd.NA,
                "fatigue_at_visit":          pd.NA,
                "recovery_at_visit":         pd.NA,
                "capacity_at_visit":         pd.NA,
                "attacker_force_at_visit":   pd.NA,
                "omega_at_visit":            pd.NA,
                "penetration_at_visit":      pd.NA,
                "max_penetration_at_visit":  pd.NA,
                "health_at_visit":           pd.NA,
                "sigma_at_visit":            pd.NA,
                "health_change_from_previous":    pd.NA,
                "rigidity_change_from_previous":  pd.NA,
                "capacity_change_from_previous":  pd.NA,
                "fatigue_change_from_previous":   pd.NA,
                "evolution_state_at_visit":  "NO_DATA",
                "span_source":               "post_return_touch_derived",
                "research_only":             True,
            })
            continue

        post_return_visit_count = len(spans)

        for k, (span_start, span_end) in enumerate(spans, start=1):
            visit_rows = post_rows[
                (pd.to_numeric(post_rows["row_index"], errors="coerce") >= span_start) &
                (pd.to_numeric(post_rows["row_index"], errors="coerce") <= span_end)
            ]
            if visit_rows.empty:
                continue

            last_row  = visit_rows.iloc[-1]
            first_row = visit_rows.iloc[0]

            # Structural state at end of visit (last row) — identical None-handling
            _rig_raw = to_float(last_row.get("rigidity_live"))
            rig_v    = rig_birth if _rig_raw is None else _rig_raw
            cap_v = to_float(last_row.get("capacity_live"))    or cap_birth
            fat_v = to_float(last_row.get("fatigue_live"))     or 0.0
            rec_v = to_float(last_row.get("recovery_live"))    or 0.0
            hlt_v = to_float(last_row.get("health_live"))      or hlt_birth
            sig_v = to_float(last_row.get("sigma_live"))       or sig_birth
            fle_v = to_float(last_row.get("fleche_live"))      or 0.0
            zone_w = to_float(last_row.get("real_zone_width")) or 1.0

            penetration_v = fle_v * zone_w

            # Peaks during the visit
            fle_max  = pd.to_numeric(visit_rows["fleche_live"], errors="coerce").max()
            max_pen  = (float(fle_max) if pd.notna(fle_max) else 0.0) * zone_w
            sig_max  = pd.to_numeric(visit_rows["sigma_live"], errors="coerce").max()
            load_max = pd.to_numeric(visit_rows["load_live"], errors="coerce").max()
            load_max = float(load_max) if pd.notna(load_max) else 0.0

            sig_max_f = float(sig_max) if pd.notna(sig_max) else sig_v
            omega_approx = sig_max_f * max_pen

            inside_count = int(
                pd.to_numeric(visit_rows["inside_zone_flag"], errors="coerce")
                .fillna(0).astype(bool).sum()
            )
            reclaim_flag = bool(
                pd.to_numeric(visit_rows["return_to_zone_flag"], errors="coerce")
                .fillna(0).astype(bool).any()
            )
            evo_state_v = str(last_row.get("evolution_state") or "")

            visit_result = _classify_visit(
                rig_v=rig_v, cap_v=cap_v, fat_v=fat_v,
                rig_birth=rig_birth, cap_birth=cap_birth, fat_birth=fat_birth,
                prev_rig=prev_rig, prev_cap=prev_cap, prev_fat=prev_fat,
                inside_count=inside_count,
                max_pen=max_pen,
                reclaim=reclaim_flag,
            )

            rows.append({
                **identity,
                "visit_index":               base_visit_index + k,
                "post_return_flag":          True,
                "post_return_visit_count":   post_return_visit_count,
                "visit_start_row":           span_start,
                "visit_end_row":             span_end,
                "visit_duration_rows":       span_end - span_start + 1,
                "timestamp_start":           str(first_row.get("timestamp", "")),
                "timestamp_end":             str(last_row.get("timestamp", "")),
                "visit_result":              visit_result,
                "rigidity_at_visit":         round_float(rig_v),
                "fatigue_at_visit":          round_float(fat_v),
                "recovery_at_visit":         round_float(rec_v),
                "capacity_at_visit":         round_float(cap_v),
                "attacker_force_at_visit":   round_float(load_max),
                "omega_at_visit":            round_float(omega_approx),
                "penetration_at_visit":      round_float(penetration_v),
                "max_penetration_at_visit":  round_float(max_pen),
                "health_at_visit":           round_float(hlt_v),
                "sigma_at_visit":            round_float(sig_v),
                "health_change_from_previous":    round_float(hlt_v - prev_hlt),
                "rigidity_change_from_previous":  round_float(rig_v - prev_rig),
                "capacity_change_from_previous":  round_float(cap_v - prev_cap),
                "fatigue_change_from_previous":   round_float(fat_v - prev_fat),
                "evolution_state_at_visit":  evo_state_v,
                "span_source":               "post_return_touch_derived",
                "research_only":             True,
            })

            prev_rig = rig_v
            prev_cap = cap_v
            prev_fat = fat_v
            prev_hlt = hlt_v

    return pd.DataFrame(rows)


def run_zone_visit_timeline_dynamic() -> None:
    """Standalone builder for zone_visit_timeline_dynamic.csv.

    Reads the already-written outputs (the Stage-1-extended
    zone_live_rdm_evolution.csv, the per-case results, and the pre-return
    visit timeline) and writes the NEW dynamic file. Avoids re-running the
    full RDM pipeline. ADDITIVE: never touches zone_visit_timeline.csv.

    Run with:
        python -c "from research.zone_mechanics_calculator import run_zone_visit_timeline_dynamic as r; r()"
    """
    run_utc = utc_now()
    evolution_df = read_csv(ZONE_LIVE_RDM_EVOLUTION_FILE)
    results_df = read_csv(RESULTS_FILE)
    pre_return_timeline_df = read_csv(ZONE_VISIT_TIMELINE_FILE)

    dynamic_df = build_zone_visit_timeline_dynamic(
        results_df, evolution_df, pre_return_timeline_df, run_utc
    )

    tmp_path = ZONE_VISIT_TIMELINE_DYNAMIC_FILE.with_suffix(".tmp.csv")
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    dynamic_df.to_csv(tmp_path, index=False)
    tmp_path.replace(ZONE_VISIT_TIMELINE_DYNAMIC_FILE)

    print(f"Dynamic post-return visit timeline: {relative_path(ZONE_VISIT_TIMELINE_DYNAMIC_FILE)}")
    print(f"Rows: {len(dynamic_df)}")
    if not dynamic_df.empty:
        print(f"Unique returning zones: {dynamic_df['case_id'].nunique()}")
        zero_rows = int((dynamic_df['post_return_visit_count'] == 0).sum())
        print(f"Zones with zero post-return visits (null rows): {zero_rows}")
        active = dynamic_df[dynamic_df['post_return_visit_count'] > 0]
        if not active.empty:
            print(f"Post-return visit rows: {len(active)}")
            print(f"visit_result distribution:\n{active['visit_result'].value_counts()}")


# ==================================================
# RDM V1.6-B9 — Zone Health Evolution
# ==================================================

def _health_state(
    slope: float,
    total_change: float,
    damage_count: int,
    growth_count: int,
    breakdown_count: int,
    visit_count: int,
) -> str:
    """Classify zone health trajectory from structural variables only.

    Uses conservative thresholds that do not reference price outcomes.
    Priority order: COLLAPSING > DEGRADING_FAST > WEAKENING >
                    RECOVERING > STRENGTHENING > STABLE > UNKNOWN
    """
    if visit_count == 0:
        return "UNKNOWN"

    if breakdown_count > 0 and damage_count >= growth_count:
        return "HEALTH_COLLAPSING"

    slope_known = slope is not None and not (slope != slope)  # NaN-safe check

    if slope_known and slope < -3.0:
        return "HEALTH_DEGRADING_FAST"

    if (slope_known and slope < -0.5) or total_change < -10.0:
        return "HEALTH_WEAKENING"

    if damage_count > 0 and growth_count > damage_count and (
        not slope_known or slope > 0.0
    ):
        return "HEALTH_RECOVERING"

    if (slope_known and slope > 0.5) and growth_count >= damage_count:
        return "HEALTH_STRENGTHENING"

    if slope_known and abs(slope) <= 0.5 and abs(total_change) < 5.0:
        return "HEALTH_STABLE"

    return "UNKNOWN"


def build_zone_health_evolution(
    results_df: pd.DataFrame,
    visit_timeline_df: pd.DataFrame,
    run_utc: str,
) -> pd.DataFrame:
    """
    RDM V1.6-B9 — Zone Health Evolution.

    One row per zone case.  Aggregates the B8 zone_visit_timeline into a
    zone-level health trajectory summary.

    health_slope
        Linear regression slope of health_at_visit over visit_index.
        Positive = health improving visit-over-visit.
        Negative = health declining.
        NaN for single-visit zones (slope undefined with one point).

    health_state
        HEALTH_STRENGTHENING   slope > 0.5  AND  growth >= damage visits
        HEALTH_STABLE          |slope| <= 0.5  AND  |total_change| < 5
        HEALTH_RECOVERING      prior damage  AND  currently positive trend
        HEALTH_WEAKENING       slope < -0.5  OR  total_change < -10
        HEALTH_DEGRADING_FAST  slope < -3.0
        HEALTH_COLLAPSING      breakdown occurred  AND  damage >= growth
        UNKNOWN                insufficient data

    Classification uses only structural variables already computed by the
    B8 visit timeline.  No price outcome, no forecast, no signal.

    Research only.  No scoring, lifecycle, replay, or dashboard changes.
    """
    if results_df.empty or visit_timeline_df.empty:
        return pd.DataFrame()

    res_idx = results_df.set_index("case_id").to_dict("index") if (
        "case_id" in results_df.columns
    ) else {}

    rows: list = []

    for case_id, r in res_idx.items():
        visits = visit_timeline_df[
            visit_timeline_df["case_id"] == case_id
        ].sort_values("visit_index").copy()

        visit_count = len(visits)

        # ── Birth state from results ──────────────────────────────────────────
        health_birth  = to_float(r.get("health_birth"))  or 0.0
        rig_birth     = to_float(r.get("rigidity_birth")) or 0.0
        cap_birth     = to_float(r.get("capacity_birth")) or 0.0
        fat_birth     = to_float(r.get("fatigue_birth"))  or 0.0
        rec_birth     = to_float(r.get("recovery_birth")) or 0.0

        if visit_count == 0:
            # Zone has no visit data — emit minimal row
            rows.append({
                "analysis_run_utc":         run_utc,
                "case_id":                  case_id,
                "episode_id":               r.get("episode_id"),
                "zone_id":                  r.get("zone_id"),
                "zone_mechanical_state":    r.get("zone_mechanical_state"),
                "visit_count":              0,
                "health_birth":             round_float(health_birth),
                "health_first_visit":       pd.NA,
                "health_last_visit":        pd.NA,
                "health_min":               pd.NA,
                "health_max":               pd.NA,
                "health_mean":              pd.NA,
                "health_std":               pd.NA,
                "health_slope":             pd.NA,
                "health_total_change":      pd.NA,
                "health_change_pct_from_birth": pd.NA,
                "rigidity_total_change":    pd.NA,
                "capacity_total_change":    pd.NA,
                "fatigue_total_change":     pd.NA,
                "recovery_total_change":    pd.NA,
                "omega_total":              pd.NA,
                "omega_max":                pd.NA,
                "omega_mean":               pd.NA,
                "attacker_force_total":     pd.NA,
                "attacker_force_max":       pd.NA,
                "damage_visit_count":       0,
                "growth_visit_count":       0,
                "breakdown_visit_count":    0,
                "absorption_visit_count":   0,
                "dominant_visit_result":    "UNKNOWN",
                "final_visit_result":       "UNKNOWN",
                "health_state":             "UNKNOWN",
                "research_only":            True,
            })
            continue

        # ── Health series ─────────────────────────────────────────────────────
        health_series = pd.to_numeric(visits["health_at_visit"], errors="coerce")
        idx_series    = visits["visit_index"].astype(float)

        h_first = float(health_series.iloc[0])  if health_series.notna().any() else health_birth
        h_last  = float(health_series.iloc[-1]) if health_series.notna().any() else health_birth
        h_min   = float(health_series.min())
        h_max   = float(health_series.max())
        h_mean  = float(health_series.mean())
        h_std   = float(health_series.std()) if visit_count > 1 else 0.0

        h_total_change = h_last - health_birth
        h_change_pct   = (h_total_change / health_birth * 100.0) if health_birth != 0 else 0.0

        # Linear slope — requires at least 2 valid pairs
        valid_mask = health_series.notna() & idx_series.notna()
        if valid_mask.sum() >= 2:
            try:
                import numpy as _np
                slope_val = float(_np.polyfit(
                    idx_series[valid_mask].values,
                    health_series[valid_mask].values,
                    deg=1
                )[0])
            except Exception:
                slope_val = None
        else:
            slope_val = None

        # ── Structural change accumulators ────────────────────────────────────
        def _col_sum(col: str) -> float:
            s = pd.to_numeric(visits[col], errors="coerce").fillna(0.0)
            return float(s.sum())

        def _col_max(col: str) -> float:
            s = pd.to_numeric(visits[col], errors="coerce").dropna()
            return float(s.max()) if not s.empty else 0.0

        def _col_mean(col: str) -> float:
            s = pd.to_numeric(visits[col], errors="coerce").dropna()
            return float(s.mean()) if not s.empty else 0.0

        rig_total = _col_sum("rigidity_change_from_previous")
        cap_total = _col_sum("capacity_change_from_previous")
        fat_total = _col_sum("fatigue_change_from_previous")
        rec_total = float(
            pd.to_numeric(visits["recovery_change_from_birth"], errors="coerce").iloc[-1]
        ) if "recovery_change_from_birth" in visits.columns else 0.0

        omega_total  = _col_sum("omega_at_visit")
        omega_max    = _col_max("omega_at_visit")
        omega_mean   = _col_mean("omega_at_visit")
        force_total  = _col_sum("attacker_force_at_visit")
        force_max    = _col_max("attacker_force_at_visit")

        # ── Visit result counts ───────────────────────────────────────────────
        vr = visits["visit_result"].astype(str)
        damage_count    = int((vr == "DAMAGE").sum())
        growth_count    = int((vr == "GROWTH").sum())
        breakdown_count = int((vr == "BREAKDOWN").sum())
        absorption_count= int((vr == "ABSORPTION").sum())

        dominant = vr.value_counts().idxmax() if not vr.empty else "UNKNOWN"
        final    = str(vr.iloc[-1]) if not vr.empty else "UNKNOWN"

        # ── Health state classification ───────────────────────────────────────
        state = _health_state(
            slope=slope_val,
            total_change=h_total_change,
            damage_count=damage_count,
            growth_count=growth_count,
            breakdown_count=breakdown_count,
            visit_count=visit_count,
        )

        rows.append({
            "analysis_run_utc":             run_utc,
            "case_id":                      case_id,
            "episode_id":                   r.get("episode_id"),
            "zone_id":                      r.get("zone_id"),
            "zone_mechanical_state":        r.get("zone_mechanical_state"),
            "visit_count":                  visit_count,
            "health_birth":                 round_float(health_birth),
            "health_first_visit":           round_float(h_first),
            "health_last_visit":            round_float(h_last),
            "health_min":                   round_float(h_min),
            "health_max":                   round_float(h_max),
            "health_mean":                  round_float(h_mean),
            "health_std":                   round_float(h_std),
            "health_slope":                 round_float(slope_val) if slope_val is not None else pd.NA,
            "health_total_change":          round_float(h_total_change),
            "health_change_pct_from_birth": round_float(h_change_pct),
            "rigidity_total_change":        round_float(rig_total),
            "capacity_total_change":        round_float(cap_total),
            "fatigue_total_change":         round_float(fat_total),
            "recovery_total_change":        round_float(rec_total),
            "omega_total":                  round_float(omega_total),
            "omega_max":                    round_float(omega_max),
            "omega_mean":                   round_float(omega_mean),
            "attacker_force_total":         round_float(force_total),
            "attacker_force_max":           round_float(force_max),
            "damage_visit_count":           damage_count,
            "growth_visit_count":           growth_count,
            "breakdown_visit_count":        breakdown_count,
            "absorption_visit_count":       absorption_count,
            "dominant_visit_result":        dominant,
            "final_visit_result":           final,
            "health_state":                 state,
            "research_only":                True,
        })

    return pd.DataFrame(rows)


# ==================================================
# RDM V1.6-B10 — Structural Trajectory Classification
# ==================================================

def _structural_trajectory_label(
    health_state: str,
    health_slope,
    final_visit_result: str,
    dominant_visit_result: str,
    growth_count: int,
    damage_count: int,
    breakdown_count: int,
    absorption_count: int,
    visit_count: int,
) -> str:
    """Classify zone structural trajectory using only structural variables.

    Priority order (highest to lowest):
      TERMINAL > ACCELERATING_FAILURE > DEGRADING >
      RECOVERY > STRENGTHENING > STABLE > TRANSITIONAL > UNKNOWN

    No price outcome, no True/Fake Breakout, no Range labels.
    """
    if visit_count == 0:
        return "UNKNOWN"

    slope_ok   = health_slope is not None and health_slope == health_slope  # NaN-safe
    slope_neg  = slope_ok and health_slope < 0
    slope_pos  = slope_ok and health_slope > 0

    # TERMINAL: structural end state reached
    if final_visit_result == "BREAKDOWN" or breakdown_count >= 2:
        return "TERMINAL"

    # ACCELERATING_FAILURE: collapsing with confirmed negative slope + multiple damage
    if (
        health_state == "HEALTH_COLLAPSING"
        and damage_count >= 2
        and slope_neg
    ):
        return "ACCELERATING_FAILURE"

    # STABLE (early check): B9 explicitly declared this zone structurally stable.
    # Must fire BEFORE the damage_count > growth_count gate so that zones whose
    # health barely moved despite damage visits are not misclassified as DEGRADING.
    if health_state == "HEALTH_STABLE":
        return "STABLE"

    # DEGRADING: weakening health or more damage than growth
    if health_state in ("HEALTH_WEAKENING", "HEALTH_COLLAPSING") or (
        damage_count > growth_count
    ):
        return "DEGRADING"

    # RECOVERY: improving after prior damage
    if final_visit_result == "GROWTH" and damage_count > 0 and slope_pos:
        return "RECOVERY"

    # STRENGTHENING: consistent growth with no breakdown
    if (
        health_state == "HEALTH_STRENGTHENING"
        and growth_count >= damage_count
        and breakdown_count == 0
    ):
        return "STRENGTHENING"

    # STABLE (second check): absorption-dominant with no damage or breakdown
    if absorption_count > 0 and damage_count == 0 and breakdown_count == 0:
        return "STABLE"

    # TRANSITIONAL: mixed growth and damage without a terminal signal
    if growth_count > 0 and damage_count > 0:
        return "TRANSITIONAL"

    # UNKNOWN: not enough information to classify
    return "UNKNOWN"


def _trajectory_score(
    label: str,
    health_slope,
    health_total_change: float,
    growth_count: int,
    damage_count: int,
    breakdown_count: int,
) -> float:
    """Return a continuous trajectory score [-100, +100].

    Higher = structurally stronger / more likely to sustain.
    Lower  = structurally weaker  / more likely to fail.
    Does not represent price direction.
    """
    base = {
        "STRENGTHENING":       65.0,
        "RECOVERY":            35.0,
        "STABLE":              15.0,
        "TRANSITIONAL":         0.0,
        "UNKNOWN":              0.0,
        "DEGRADING":          -40.0,
        "ACCELERATING_FAILURE":-70.0,
        "TERMINAL":           -90.0,
    }.get(label, 0.0)

    slope_ok = health_slope is not None and health_slope == health_slope
    if slope_ok:
        if label in ("STRENGTHENING", "RECOVERY"):
            base += min(float(health_slope) * 3.0,  25.0)
        elif label in ("DEGRADING", "ACCELERATING_FAILURE", "TERMINAL"):
            base += max(float(health_slope) * 3.0, -25.0)

    # Small adjustment for growth/damage ratio
    total = growth_count + damage_count
    if total > 0:
        ratio = (growth_count - damage_count) / total
        base += ratio * 5.0

    return float(max(-100.0, min(100.0, base)))


def _trajectory_confidence(
    health_state: str,
    health_slope,
    visit_count: int,
) -> str:
    """HIGH / MEDIUM / LOW based on data sufficiency."""
    slope_ok = health_slope is not None and health_slope == health_slope
    if visit_count >= 3 and slope_ok and health_state != "UNKNOWN":
        return "HIGH"
    if visit_count >= 2 or (visit_count >= 3 and not slope_ok):
        return "MEDIUM"
    return "LOW"


def _trajectory_reason(
    label: str,
    health_state: str,
    visit_count: int,
    health_slope,
    damage_count: int,
    growth_count: int,
    breakdown_count: int,
    final_visit_result: str,
) -> str:
    """Short human-readable reason for the trajectory label."""
    slope_str = (
        f"slope={float(health_slope):.2f}" if (
            health_slope is not None and health_slope == health_slope
        ) else "slope=N/A"
    )
    if label == "TERMINAL":
        if final_visit_result == "BREAKDOWN":
            return f"breakdown reached on final visit; {breakdown_count} breakdown visit(s)"
        return f"{breakdown_count} breakdown visit(s) observed"
    if label == "ACCELERATING_FAILURE":
        return f"health_state=COLLAPSING, {damage_count} damage visits, {slope_str}"
    if label == "DEGRADING":
        return f"{damage_count} damage > {growth_count} growth; health_state={health_state}"
    if label == "RECOVERY":
        return f"final=GROWTH after {damage_count} damage visit(s); {slope_str}"
    if label == "STRENGTHENING":
        return f"{growth_count} growth visits, 0 breakdown, health_state={health_state}"
    if label == "STABLE":
        return f"health_state={health_state}; no damage or breakdown"
    if label == "TRANSITIONAL":
        return f"mixed: {growth_count} growth, {damage_count} damage — no terminal state"
    return f"visit_count={visit_count}; health_state={health_state}"


def build_zone_structural_trajectory(
    results_df: pd.DataFrame,
    health_evolution_df: pd.DataFrame,
    run_utc: str,
) -> pd.DataFrame:
    """
    RDM V1.6-B10 — Structural Trajectory Classification.

    One row per zone case.  Synthesises the B9 health evolution summary into
    a single structural trajectory label that describes what the zone is
    becoming structurally over the observed visit sequence.

    Trajectory labels (research-only — not trading signals):
      STRENGTHENING       zone consistently gaining structural strength
      STABLE              zone holding with minimal change
      RECOVERY            zone improving after prior damage
      TRANSITIONAL        mixed signals — no clear direction yet
      DEGRADING           zone losing structural integrity progressively
      ACCELERATING_FAILURE confirmed collapse trajectory with negative slope
      TERMINAL            structural end-state: breakdown reached
      UNKNOWN             insufficient visit data for classification

    trajectory_score  [-100, +100]
      Continuous measure: higher = structurally stronger.
      Derived from label, health slope, and growth/damage ratio.

    trajectory_direction
      POSITIVE / NEUTRAL / NEGATIVE — directional grouping.

    trajectory_confidence
      HIGH   : 3+ visits with slope computed and non-UNKNOWN health_state
      MEDIUM : 2 visits, or 3+ visits with missing slope
      LOW    : 1 visit or UNKNOWN health_state

    trajectory_reason
      Short explanation of why the label was assigned.

    Classification uses only structural variables (B8 / B9 outputs).
    No price outcome, no True/Fake Breakout, no Range labels.

    Research only.  No scoring, lifecycle, replay, or dashboard changes.
    """
    if results_df.empty or health_evolution_df.empty:
        return pd.DataFrame()

    res_idx = results_df.set_index("case_id").to_dict("index") if (
        "case_id" in results_df.columns
    ) else {}
    he_idx  = health_evolution_df.set_index("case_id").to_dict("index") if (
        "case_id" in health_evolution_df.columns
    ) else {}

    _direction_map = {
        "STRENGTHENING":       "POSITIVE",
        "RECOVERY":            "POSITIVE",
        "STABLE":              "NEUTRAL",
        "TRANSITIONAL":        "NEUTRAL",
        "UNKNOWN":             "NEUTRAL",
        "DEGRADING":           "NEGATIVE",
        "ACCELERATING_FAILURE":"NEGATIVE",
        "TERMINAL":            "NEGATIVE",
    }

    rows: list = []

    for case_id, r in res_idx.items():
        he = he_idx.get(case_id, {})

        # Pull all required fields from health_evolution
        visit_count      = int(to_float(he.get("visit_count")) or 0)
        health_state     = str(he.get("health_state") or "UNKNOWN")
        health_slope_raw = to_float(he.get("health_slope"))
        health_slope     = health_slope_raw  # may be None / NaN

        h_total_change   = to_float(he.get("health_total_change")) or 0.0
        h_last           = to_float(he.get("health_last_visit"))    or 0.0
        h_birth          = to_float(he.get("health_birth"))         or 0.0

        dominant_vr      = str(he.get("dominant_visit_result") or "UNKNOWN")
        final_vr         = str(he.get("final_visit_result")    or "UNKNOWN")
        growth_count     = int(to_float(he.get("growth_visit_count"))    or 0)
        damage_count     = int(to_float(he.get("damage_visit_count"))    or 0)
        breakdown_count  = int(to_float(he.get("breakdown_visit_count")) or 0)
        absorption_count = int(to_float(he.get("absorption_visit_count"))or 0)
        omega_total      = to_float(he.get("omega_total"))   or 0.0
        omega_max        = to_float(he.get("omega_max"))     or 0.0
        omega_mean       = to_float(he.get("omega_mean"))    or 0.0
        force_total      = to_float(he.get("attacker_force_total")) or 0.0
        force_max        = to_float(he.get("attacker_force_max"))   or 0.0

        # ── Classify ──────────────────────────────────────────────────────────
        label = _structural_trajectory_label(
            health_state=health_state,
            health_slope=health_slope,
            final_visit_result=final_vr,
            dominant_visit_result=dominant_vr,
            growth_count=growth_count,
            damage_count=damage_count,
            breakdown_count=breakdown_count,
            absorption_count=absorption_count,
            visit_count=visit_count,
        )

        score      = _trajectory_score(
            label, health_slope, h_total_change,
            growth_count, damage_count, breakdown_count,
        )
        direction  = _direction_map.get(label, "NEUTRAL")
        confidence = _trajectory_confidence(health_state, health_slope, visit_count)
        reason     = _trajectory_reason(
            label, health_state, visit_count, health_slope,
            damage_count, growth_count, breakdown_count, final_vr,
        )

        rows.append({
            "analysis_run_utc":       run_utc,
            "case_id":                case_id,
            "episode_id":             r.get("episode_id"),
            "zone_id":                r.get("zone_id"),
            "zone_mechanical_state":  r.get("zone_mechanical_state"),
            "visit_count":            visit_count,
            "health_state":           health_state,
            "health_slope":           round_float(health_slope) if health_slope is not None else pd.NA,
            "health_total_change":    round_float(h_total_change),
            "health_last_visit":      round_float(h_last),
            "dominant_visit_result":  dominant_vr,
            "final_visit_result":     final_vr,
            "growth_visit_count":     growth_count,
            "damage_visit_count":     damage_count,
            "breakdown_visit_count":  breakdown_count,
            "absorption_visit_count": absorption_count,
            "omega_total":            round_float(omega_total),
            "omega_max":              round_float(omega_max),
            "omega_mean":             round_float(omega_mean),
            "attacker_force_total":   round_float(force_total),
            "attacker_force_max":     round_float(force_max),
            "trajectory_score":       round_float(score),
            "trajectory_direction":   direction,
            "structural_trajectory":  label,
            "trajectory_confidence":  confidence,
            "trajectory_reason":      reason,
            "research_only":          True,
        })

    return pd.DataFrame(rows)


# ==================================================
# RDM V1.6-B11 — Structural Engagement Prediction
# ==================================================

_HOLD_TRAJECTORIES  = {"STRENGTHENING", "STABLE", "RECOVERY"}
_FAIL_TRAJECTORIES  = {"TERMINAL", "ACCELERATING_FAILURE", "DEGRADING"}
_UNCERT_TRAJECTORIES = {"TRANSITIONAL"}
_HEALTH_CRITICAL_LOW = 20.0   # health below this is structurally compromised


def _structural_prediction_label(
    structural_trajectory: str,
    trajectory_confidence: str,
    health_state: str,
    health_last_visit: float,
    breakdown_count: int,
    damage_count: int,
) -> str:
    """Classify the structural expectation for the NEXT zone interaction.

    Research-only: HOLD / FAIL / UNCERTAIN / NO_PREDICTION.

    Priority: NO_PREDICTION (data gate) → FAIL → HOLD → UNCERTAIN → NO_PREDICTION

    This is a structural expectation, not a price prediction.  No BUY/SELL,
    no entry/exit, no range or breakout classification.
    """
    # NO_PREDICTION: data quality gate
    if (structural_trajectory == "UNKNOWN"
            or trajectory_confidence == "LOW"):
        return "NO_PREDICTION"

    # FAIL: structural failure signals present
    if (structural_trajectory in _FAIL_TRAJECTORIES
            or breakdown_count >= 1
            or (health_state == "HEALTH_COLLAPSING" and damage_count >= 2)):
        return "FAIL"

    # HOLD: structural strength confirmed
    if (structural_trajectory in _HOLD_TRAJECTORIES
            and breakdown_count == 0
            and (health_last_visit is None or health_last_visit >= _HEALTH_CRITICAL_LOW)):
        return "HOLD"

    # UNCERTAIN: trajectory is intermediate or mixed
    if structural_trajectory in _UNCERT_TRAJECTORIES:
        return "UNCERTAIN"

    # Default fallback
    return "UNCERTAIN"


def _prediction_score(
    structural_prediction: str,
    trajectory_score: float,
    breakdown_count: int,
    health_last_visit: float,
    force_ratio: float,
    sigma_barre: float,
    damage_count: int,
    growth_count: int,
) -> float:
    """Continuous prediction score [-100, +100].

    Positive → structural HOLD expectation.
    Negative → structural FAIL expectation.
    Near zero → UNCERTAIN.

    Derived from trajectory_score with adjustments for zone defense capacity
    and attacker force characteristics.  No price outcome used.
    """
    if structural_prediction == "NO_PREDICTION":
        return 0.0

    base = float(trajectory_score)

    # Breakdown penalises strongly regardless of trajectory
    base -= breakdown_count * 20.0

    # Very low health signals structural compromise
    if health_last_visit is not None and health_last_visit < _HEALTH_CRITICAL_LOW:
        base -= 15.0

    # High sigma_barre = harder for attacker to engage = HOLD-friendly
    if sigma_barre is not None and sigma_barre > 0:
        if sigma_barre > 40.0:    # RECOVERED-class high memory barre
            base += 8.0
        elif sigma_barre < 15.0:  # easy to engage
            base -= 5.0

    # Force ratio: low = attacker weak = more likely HOLD
    if force_ratio is not None:
        if force_ratio < 0.30:
            base += 7.0
        elif force_ratio > 1.00:
            base -= 12.0

    return float(max(-100.0, min(100.0, base)))


def _prediction_confidence(
    structural_prediction: str,
    trajectory_confidence: str,
    visit_count: int,
) -> str:
    """HIGH / MEDIUM / LOW confidence for the structural prediction."""
    if structural_prediction == "NO_PREDICTION":
        return "LOW"
    if (trajectory_confidence == "HIGH"
            and visit_count >= 3
            and structural_prediction in ("HOLD", "FAIL")):
        return "HIGH"
    if (trajectory_confidence in ("HIGH", "MEDIUM")
            and structural_prediction in ("HOLD", "FAIL", "UNCERTAIN")):
        return "MEDIUM"
    return "LOW"


def _prediction_reason(
    structural_prediction: str,
    structural_trajectory: str,
    trajectory_confidence: str,
    health_state: str,
    breakdown_count: int,
    damage_count: int,
    growth_count: int,
    visit_count: int,
) -> str:
    """Short explanation for the structural prediction label."""
    if structural_prediction == "NO_PREDICTION":
        if trajectory_confidence == "LOW":
            return f"confidence=LOW; visit_count={visit_count} — insufficient structural evidence"
        return f"trajectory=UNKNOWN; no structural classification available"

    if structural_prediction == "FAIL":
        if structural_trajectory in _FAIL_TRAJECTORIES:
            return f"trajectory={structural_trajectory}; breakdown_count={breakdown_count}"
        if breakdown_count >= 1:
            return f"{breakdown_count} breakdown visit(s); health_state={health_state}"
        return f"health_state=COLLAPSING; damage_count={damage_count} >= 2"

    if structural_prediction == "HOLD":
        return (f"trajectory={structural_trajectory}; "
                f"growth={growth_count}, damage={damage_count}, breakdown=0; "
                f"health_state={health_state}")

    # UNCERTAIN
    return f"trajectory={structural_trajectory}; mixed structural signals"


def build_zone_structural_prediction(
    results_df: pd.DataFrame,
    trajectory_df: pd.DataFrame,
    vs_attacker_df: pd.DataFrame,
    run_utc: str,
) -> pd.DataFrame:
    """
    RDM V1.6-B11 — Structural Engagement Prediction.

    One row per zone case.  Produces a structural expectation (HOLD / FAIL /
    UNCERTAIN / NO_PREDICTION) for the next zone interaction, derived from the
    B9–B10 health and trajectory layers together with zone defense capacity
    variables from the B4 series.

    This is NOT a price prediction.  It is NOT a trading signal.
    It is the model's current structural expectation given all available
    mechanical evidence.  B12 will later validate whether the expectation
    matched the observed market outcome.

    Prediction labels (research-only):
      HOLD           zone expected to hold if tested again
      FAIL           zone expected to fail if tested again
      UNCERTAIN      mixed or insufficient structural signals
      NO_PREDICTION  data quality insufficient for a reliable prediction
                     (trajectory=UNKNOWN or confidence=LOW)

    prediction_score  [-100, +100]
      Positive → HOLD expectation.  Negative → FAIL expectation.
      Derived from trajectory_score with adjustments for sigma_barre_zone
      (defense capacity) and force_ratio (attacker strength).

    prediction_confidence
      HIGH   : trajectory HIGH confidence, 3+ visits, clear HOLD or FAIL
      MEDIUM : moderate evidence
      LOW    : single visit, UNKNOWN trajectory, or NO_PREDICTION

    prediction_reason
      Brief explanation of the primary classification driver.

    Research only.  No scoring, lifecycle, replay, or dashboard changes.
    """
    if results_df.empty or trajectory_df.empty:
        return pd.DataFrame()

    # ── Index all inputs ──────────────────────────────────────────────────────
    tr_idx  = trajectory_df.set_index("case_id").to_dict("index") if (
        "case_id" in trajectory_df.columns
    ) else {}
    res_idx = results_df.set_index("case_id").to_dict("index") if (
        "case_id" in results_df.columns
    ) else {}
    va_idx: dict = {}
    if vs_attacker_df is not None and not vs_attacker_df.empty and "case_id" in vs_attacker_df.columns:
        va_idx = vs_attacker_df.set_index("case_id").to_dict("index")

    rows: list = []

    for case_id, r in res_idx.items():
        tr = tr_idx.get(case_id, {})
        va = va_idx.get(case_id, {})

        # ── Pull B10 / B9 fields from trajectory row ─────────────────────────
        structural_trajectory   = str(tr.get("structural_trajectory")  or "UNKNOWN")
        trajectory_score_raw    = to_float(tr.get("trajectory_score")) or 0.0
        trajectory_confidence   = str(tr.get("trajectory_confidence")  or "LOW")
        trajectory_direction    = str(tr.get("trajectory_direction")   or "NEUTRAL")
        health_state            = str(tr.get("health_state")           or "UNKNOWN")
        health_slope            = to_float(tr.get("health_slope"))
        health_total_change     = to_float(tr.get("health_total_change")) or 0.0
        health_last_visit       = to_float(tr.get("health_last_visit")) or 0.0
        omega_total             = to_float(tr.get("omega_total"))     or 0.0
        omega_max               = to_float(tr.get("omega_max"))       or 0.0
        omega_mean              = to_float(tr.get("omega_mean"))      or 0.0
        force_total             = to_float(tr.get("attacker_force_total")) or 0.0
        force_max               = to_float(tr.get("attacker_force_max"))   or 0.0
        damage_count            = int(to_float(tr.get("damage_visit_count"))    or 0)
        growth_count            = int(to_float(tr.get("growth_visit_count"))    or 0)
        breakdown_count         = int(to_float(tr.get("breakdown_visit_count")) or 0)
        absorption_count        = int(to_float(tr.get("absorption_visit_count"))or 0)
        visit_count             = int(to_float(tr.get("visit_count"))           or 0)
        dominant_vr             = str(tr.get("dominant_visit_result") or "UNKNOWN")
        final_vr                = str(tr.get("final_visit_result")    or "UNKNOWN")

        # ── Pull structural defense metrics ───────────────────────────────────
        sigma_barre    = to_float(r.get("sigma_barre_zone"))
        sigma_at_ret   = to_float(r.get("sigma_at_return"))
        omega_area     = to_float(r.get("omega_stress_area")) or 0.0
        pen_depth      = to_float(r.get("zone_penetration_depth")) or 0.0

        # ── Pull B4 metrics from zone vs attacker profile ─────────────────────
        zss        = to_float(va.get("rdm_v16b4_zone_strength_score"))
        afs        = to_float(va.get("rdm_v16b4_attacker_force_score"))
        force_ratio = to_float(va.get("rdm_v16b4_force_ratio"))

        # ── Predict ───────────────────────────────────────────────────────────
        prediction = _structural_prediction_label(
            structural_trajectory=structural_trajectory,
            trajectory_confidence=trajectory_confidence,
            health_state=health_state,
            health_last_visit=health_last_visit,
            breakdown_count=breakdown_count,
            damage_count=damage_count,
        )

        score = _prediction_score(
            structural_prediction=prediction,
            trajectory_score=trajectory_score_raw,
            breakdown_count=breakdown_count,
            health_last_visit=health_last_visit,
            force_ratio=force_ratio,
            sigma_barre=sigma_barre,
            damage_count=damage_count,
            growth_count=growth_count,
        )

        confidence = _prediction_confidence(
            structural_prediction=prediction,
            trajectory_confidence=trajectory_confidence,
            visit_count=visit_count,
        )

        reason = _prediction_reason(
            structural_prediction=prediction,
            structural_trajectory=structural_trajectory,
            trajectory_confidence=trajectory_confidence,
            health_state=health_state,
            breakdown_count=breakdown_count,
            damage_count=damage_count,
            growth_count=growth_count,
            visit_count=visit_count,
        )

        rows.append({
            "analysis_run_utc":       run_utc,
            "case_id":                case_id,
            "episode_id":             r.get("episode_id"),
            "zone_id":                r.get("zone_id"),
            "zone_mechanical_state":  r.get("zone_mechanical_state"),
            "visit_count":            visit_count,
            "health_state":           health_state,
            "structural_trajectory":  structural_trajectory,
            "trajectory_score":       round_float(trajectory_score_raw),
            "trajectory_confidence":  trajectory_confidence,
            "trajectory_direction":   trajectory_direction,
            "health_slope":           round_float(health_slope) if health_slope is not None else pd.NA,
            "health_total_change":    round_float(health_total_change),
            "health_last_visit":      round_float(health_last_visit),
            "omega_total":            round_float(omega_total),
            "omega_max":              round_float(omega_max),
            "omega_mean":             round_float(omega_mean),
            "attacker_force_total":   round_float(force_total),
            "attacker_force_max":     round_float(force_max),
            "damage_visit_count":     damage_count,
            "growth_visit_count":     growth_count,
            "breakdown_visit_count":  breakdown_count,
            "absorption_visit_count": absorption_count,
            "sigma_barre_zone":       round_float(sigma_barre) if sigma_barre is not None else pd.NA,
            "sigma_at_return":        round_float(sigma_at_ret) if sigma_at_ret is not None else pd.NA,
            "omega_stress_area":      round_float(omega_area),
            "zone_penetration_depth": round_float(pen_depth),
            "zone_strength_score":    round_float(zss) if zss is not None else pd.NA,
            "attacker_force_score":   round_float(afs) if afs is not None else pd.NA,
            "force_ratio":            round_float(force_ratio) if force_ratio is not None else pd.NA,
            "prediction_score":       round_float(score),
            "structural_prediction":  prediction,
            "prediction_confidence":  confidence,
            "prediction_reason":      reason,
            "research_only":          True,
        })

    return pd.DataFrame(rows)


def build_zone_anomaly_profile(
    vs_df: pd.DataFrame,
    results_df: pd.DataFrame,
    run_utc: str,
) -> pd.DataFrame:
    """
    RDM V1.6-B5 + B5.5 — Anomaly Physics with Trajectory Context.

    Detects structural anomalies: cases where the observed zone outcome
    does not match the mechanical expectation set by ZSS vs AFS.

    ZSS, AFS, Expected Balance, Observed Balance, Balance Gap, and the
    original anomaly_score / anomaly_direction are unchanged from B5.

    B5.5 adds:
      trajectory_context  — classifies each case's lifecycle trajectory.
      anomaly_direction_gated — anomaly direction filtered by trajectory.
      anomaly_score_gated     — anomaly score filtered by trajectory.

    ── Trajectory Context (B5.5) ────────────────────────────────────────────

    Uses three signals from existing lifecycle fields:
      birth_vs_live_degradation_state  (categorical degradation trajectory)
      zone_recovery_state              (recovery outcome)
      fatigue_increase_from_birth      (cumulative fatigue accumulation)

    Classification priority (first match wins):

    RECOVERING_ZONE
      zone_recovery_state = RECOVERED or STRONG_RECOVERY
      Active recovery dominates regardless of degradation state.

    ACTIVE_DEGRADATION
      (birth_vs_live_degradation_state in MODERATE/SEVERE AND zone_recovery_state = NO_RECOVERY)
      OR
      (fatigue_increase_normalized > 0.5 AND zone_recovery_state = NO_RECOVERY)
      Zone is on a known degradation trajectory with no recovery.

    STABLE_ZONE
      Everything else.

    ── Trajectory-Gated Anomaly (B5.5) ─────────────────────────────────────

    ACTIVE_DEGRADATION + gap < 0 → EXPECTED_DEGRADATION
      The outcome is mechanically predictable from the trajectory.
      Not a genuine anomaly.  anomaly_score_gated = 0.

    All other combinations → same as original anomaly_direction.

    Original B5 fields are preserved unchanged.

    Research only.  No scoring, lifecycle, replay, or dashboard impact.
    """
    _ANOMALY_THRESHOLD      = 20.0
    _HEALTH_MAX             = 100.0
    _FATIGUE_HIGH_THRESHOLD = 0.5    # normalized: above 50% of pop max = high fatigue

    if vs_df.empty:
        return pd.DataFrame()

    vs_idx  = vs_df.set_index("case_id").to_dict("index")
    res_idx = results_df.set_index("case_id").to_dict("index") if (
        not results_df.empty and "case_id" in results_df.columns
    ) else {}

    # Population max for fatigue normalization (used in trajectory classification)
    fat_series = pd.to_numeric(
        results_df["fatigue_increase_from_birth"], errors="coerce"
    ) if (not results_df.empty and "fatigue_increase_from_birth" in results_df.columns) else pd.Series(dtype=float)
    fatigue_pop_max = float(fat_series.dropna().max()) if not fat_series.dropna().empty else None

    rows = []

    for case_id, v_row in vs_idx.items():
        r_row = res_idx.get(case_id, {})

        zss = to_float(v_row.get("rdm_v16b4_zone_strength_score"))
        afs = to_float(v_row.get("rdm_v16b4_attacker_force_score"))

        # ── Expected balance (B5 — UNCHANGED) ────────────────────────────────
        if zss is not None and afs is not None:
            expected_balance = round_float(zss - afs)
        else:
            expected_balance = pd.NA

        # ── Observed balance (B5 — UNCHANGED) ────────────────────────────────
        health_val = to_float(r_row.get("rdm_health_score"))
        if health_val is not None:
            health_norm = min(max(health_val / _HEALTH_MAX, 0.0), 1.0)
            health_contribution = (health_norm * 2.0 - 1.0) * 50.0
        else:
            health_contribution = 0.0

        deg_state = str(r_row.get("birth_vs_live_degradation_state") or "").upper()
        if "STABLE" in deg_state:
            deg_contribution = 25.0
        elif "SEVERE" in deg_state:
            deg_contribution = -35.0
        elif "MODERATE" in deg_state:
            deg_contribution = -15.0
        else:
            deg_contribution = 0.0

        rec_state = str(r_row.get("zone_recovery_state") or "").upper()
        if "RECOVERED" in rec_state and "STRONG" not in rec_state:
            rec_contribution = 20.0
        elif "STRONG_RECOVERY" in rec_state:
            rec_contribution = 10.0
        elif "NO_RECOVERY" in rec_state:
            rec_contribution = -5.0
        else:
            rec_contribution = 0.0

        obs_raw = health_contribution + deg_contribution + rec_contribution
        observed_balance = round_float(min(max(obs_raw, -100.0), 100.0))

        # ── Balance gap and original anomaly fields (B5 — UNCHANGED) ─────────
        if expected_balance is not pd.NA and expected_balance is not None:
            gap_raw = (observed_balance or 0.0) - float(expected_balance)
            balance_gap   = round_float(gap_raw)
            anomaly_score = round_float(min(abs(gap_raw), 100.0))

            if gap_raw < -_ANOMALY_THRESHOLD:
                anomaly_direction = "ZONE_STRONGER_THAN_RESULT"
            elif gap_raw > _ANOMALY_THRESHOLD:
                anomaly_direction = "ATTACKER_STRONGER_THAN_RESULT"
            else:
                anomaly_direction = "BALANCED"
        else:
            gap_raw           = None
            balance_gap       = pd.NA
            anomaly_score     = pd.NA
            anomaly_direction = "UNKNOWN"

        # ── B5.5: Trajectory Context ──────────────────────────────────────────
        # Fatigue accumulation normalized against population max
        fat_val = to_float(r_row.get("fatigue_increase_from_birth"))
        if fat_val is not None and fatigue_pop_max is not None and fatigue_pop_max > 0:
            fat_norm = fat_val / fatigue_pop_max
        else:
            fat_norm = 0.0

        no_recovery = "NO_RECOVERY" in rec_state

        if "RECOVERED" in rec_state:
            # Active recovery overrides degradation signal
            trajectory_context = "RECOVERING_ZONE"
        elif (
            ("MODERATE" in deg_state or "SEVERE" in deg_state)
            and no_recovery
        ) or (
            fat_norm > _FATIGUE_HIGH_THRESHOLD
            and no_recovery
        ):
            trajectory_context = "ACTIVE_DEGRADATION"
        else:
            trajectory_context = "STABLE_ZONE"

        # ── B5.5: Trajectory-Gated Anomaly ───────────────────────────────────
        # ACTIVE_DEGRADATION with negative gap = trajectory explains the outcome.
        if gap_raw is not None:
            if trajectory_context == "ACTIVE_DEGRADATION" and gap_raw < 0:
                anomaly_direction_gated = "EXPECTED_DEGRADATION"
                anomaly_score_gated     = round_float(0.0)
            else:
                anomaly_direction_gated = anomaly_direction
                anomaly_score_gated     = anomaly_score
        else:
            anomaly_direction_gated = "UNKNOWN"
            anomaly_score_gated     = pd.NA

        rows.append({
            "analysis_run_utc": run_utc,
            "case_id": case_id,
            "episode_id": v_row.get("episode_id"),
            "zone_id": v_row.get("zone_id"),
            "zone_mechanical_state": v_row.get("zone_mechanical_state"),
            "rdm_v16b4_zone_strength_score": zss,
            "rdm_v16b4_attacker_force_score": afs,
            # B5 fields — unchanged
            "rdm_v16b5_expected_balance":   expected_balance,
            "rdm_v16b5_observed_balance":   observed_balance,
            "rdm_v16b5_balance_gap":        balance_gap,
            "rdm_v16b5_anomaly_score":      anomaly_score,
            "rdm_v16b5_anomaly_direction":  anomaly_direction,
            # B5.5 fields — trajectory context and gated anomaly
            "rdm_v16b5_trajectory_context":      trajectory_context,
            "rdm_v16b5_anomaly_direction_gated": anomaly_direction_gated,
            "rdm_v16b5_anomaly_score_gated":     anomaly_score_gated,
            "research_only": True,
        })

    return pd.DataFrame(rows)


def compute_event_forces(interaction_rows: pd.DataFrame) -> list:
    """
    Split interaction rows into contiguous events by row_index.

    Each contiguous run of rows (no gap in row_index > 1) is one interaction
    event.  Returns a list of mean |delta| per event in chronological order.
    Returns an empty list when no valid data is present.

    V1.6-B3 helper.  Does not change any existing calculation.
    """
    if interaction_rows.empty or "delta" not in interaction_rows.columns:
        return []

    rows = interaction_rows.copy()
    has_row_index = "row_index" in rows.columns

    if has_row_index:
        rows["_ridx"] = pd.to_numeric(rows["row_index"], errors="coerce")
        rows = (
            rows.dropna(subset=["_ridx"])
            .sort_values("_ridx")
            .reset_index(drop=True)
        )

    if rows.empty:
        return []

    rows["_dabs"] = pd.to_numeric(rows["delta"], errors="coerce").abs()

    if not has_row_index:
        # No row_index column: treat all rows as a single event.
        mean_val = rows["_dabs"].dropna().mean()
        return [round_float(mean_val)] if pd.notna(mean_val) else []

    event_forces: list = []
    current_group: list = []
    prev_ridx: float = float("nan")

    for _, row in rows.iterrows():
        ridx = row["_ridx"]
        dval = row["_dabs"]

        if pd.isna(prev_ridx) or (ridx - prev_ridx) <= 1:
            current_group.append(dval)
        else:
            # Gap detected — close current event and start a new one.
            group_vals = pd.Series(current_group, dtype="float64").dropna()
            if not group_vals.empty:
                event_forces.append(round_float(group_vals.mean()))
            current_group = [dval]

        prev_ridx = ridx

    # Close the final event.
    if current_group:
        group_vals = pd.Series(current_group, dtype="float64").dropna()
        if not group_vals.empty:
            event_forces.append(round_float(group_vals.mean()))

    return event_forces


def segment_attacker_attempts(interaction_rows: pd.DataFrame) -> list[Dict[str, Any]]:
    """
    Segment attack attempts in parallel with the existing B3 session model.

    B3.5-A defines an attempt as a contiguous run of interaction rows.  The
    segmentation is diagnostic-only and does not feed force trend, anomaly,
    lifecycle, scoring, or dashboard behavior.
    """
    if interaction_rows.empty:
        return []

    rows = interaction_rows.copy()
    if "row_index" not in rows.columns:
        return [
            {
                "start_row": pd.NA,
                "end_row": pd.NA,
                "row_count": len(rows),
            }
        ]

    rows["_ridx"] = pd.to_numeric(rows["row_index"], errors="coerce")
    rows = rows.dropna(subset=["_ridx"]).sort_values("_ridx").reset_index(drop=True)
    if rows.empty:
        return []

    attempts: list[Dict[str, Any]] = []
    start_row = rows.iloc[0]["_ridx"]
    previous_row = start_row
    row_count = 0

    for _, row in rows.iterrows():
        current_row = row["_ridx"]
        if current_row - previous_row > 1 and row_count > 0:
            attempts.append(
                {
                    "start_row": int(start_row),
                    "end_row": int(previous_row),
                    "row_count": row_count,
                }
            )
            start_row = current_row
            row_count = 0

        row_count += 1
        previous_row = current_row

    if row_count > 0:
        attempts.append(
            {
                "start_row": int(start_row),
                "end_row": int(previous_row),
                "row_count": row_count,
            }
        )

    return attempts


def attacker_attempt_diagnostics(attempts: list[Dict[str, Any]]) -> Dict[str, Any]:
    if not attempts:
        return {
            "count": pd.NA,
            "rows_total": pd.NA,
            "rows_mean": pd.NA,
            "rows_max": pd.NA,
            "first_row": pd.NA,
            "last_row": pd.NA,
            "row_spans": "",
        }

    row_counts = [attempt["row_count"] for attempt in attempts]
    return {
        "count": len(attempts),
        "rows_total": sum(row_counts),
        "rows_mean": round_float(sum(row_counts) / len(row_counts)),
        "rows_max": max(row_counts),
        "first_row": attempts[0]["start_row"],
        "last_row": attempts[-1]["end_row"],
        "row_spans": "|".join(
            f"{attempt['start_row']}-{attempt['end_row']}"
            for attempt in attempts
        ),
    }


def segment_force_lull_attempts(
    interaction_rows: pd.DataFrame,
) -> list:
    """
    FORCE_LULL_ATTEMPT_SEGMENTATION_V1

    Splits a continuous interaction session into discrete attack attempts by
    detecting force lull periods *within* the session.

    Algorithm
    ---------
    1. Compute impulse = |delta| for every interaction row.
    2. session_mean_force = mean(impulse) across the session.
    3. lull_threshold = session_mean_force * ATTACKER_LULL_THRESHOLD_RATIO.
    4. rolling_force = trailing rolling mean of impulse, window = ATTACKER_FORCE_WINDOW.
    5. active_flag = (rolling_force >= lull_threshold) per row.
    6. Bridge short lulls: consecutive False runs shorter than ATTACKER_LULL_DURATION
       rows are set to True (the attacker paused briefly, not ended).
    7. Each contiguous run of True (after bridging) = one attempt.

    Returns a list of attempt dicts, each containing:
      start_ridx, end_ridx, row_count, mean_force, peak_force.

    V1.6-B3.5-B helper.  Research only.  Does not change scoring, lifecycle,
    or replay.
    """
    if interaction_rows.empty or "delta" not in interaction_rows.columns:
        return []

    rows = interaction_rows.copy()

    has_ridx = "row_index" in rows.columns
    if has_ridx:
        rows["_ridx"] = pd.to_numeric(rows["row_index"], errors="coerce")
        rows = (
            rows.dropna(subset=["_ridx"])
            .sort_values("_ridx")
            .reset_index(drop=True)
        )
    else:
        rows = rows.reset_index(drop=True)

    if rows.empty:
        return []

    rows["_impulse"] = pd.to_numeric(rows["delta"], errors="coerce").abs()

    session_mean = rows["_impulse"].dropna().mean()
    if pd.isna(session_mean) or session_mean <= 0:
        # Degenerate session (all-zero or missing delta): one attempt.
        return [
            {
                "start_ridx": int(rows.iloc[0]["_ridx"]) if has_ridx else pd.NA,
                "end_ridx": int(rows.iloc[-1]["_ridx"]) if has_ridx else pd.NA,
                "row_count": len(rows),
                "mean_force": round_float(rows["_impulse"].dropna().mean()),
                "peak_force": round_float(rows["_impulse"].dropna().max()),
            }
        ]

    lull_threshold = session_mean * ATTACKER_LULL_THRESHOLD_RATIO

    # Trailing rolling mean; min_periods=1 so the first rows are not NaN.
    rows["_rolling"] = (
        rows["_impulse"].rolling(window=ATTACKER_FORCE_WINDOW, min_periods=1).mean()
    )
    rows["_active"] = rows["_rolling"] >= lull_threshold

    # --- Bridge short lulls (False runs < ATTACKER_LULL_DURATION) ----------
    active_list = rows["_active"].tolist()
    n = len(active_list)
    bridged = list(active_list)

    i = 0
    while i < n:
        if not bridged[i]:
            j = i
            while j < n and not bridged[j]:
                j += 1
            if (j - i) < ATTACKER_LULL_DURATION:
                for k in range(i, j):
                    bridged[k] = True
            i = j
        else:
            i += 1

    rows["_bridged"] = bridged

    # --- Segment into attempts -------------------------------------------
    attempts: list = []
    current: list = []

    for _, row in rows.iterrows():
        if row["_bridged"]:
            current.append(row)
        else:
            if current:
                attempts.append(current)
                current = []

    if current:
        attempts.append(current)

    # --- Build summary dicts for each attempt ----------------------------
    result: list = []
    for attempt_rows_list in attempts:
        adf = pd.DataFrame(attempt_rows_list)
        impulses = adf["_impulse"].dropna()
        result.append(
            {
                "start_ridx": int(adf["_ridx"].iloc[0]) if has_ridx else pd.NA,
                "end_ridx": int(adf["_ridx"].iloc[-1]) if has_ridx else pd.NA,
                "row_count": len(adf),
                "mean_force": round_float(impulses.mean()) if not impulses.empty else pd.NA,
                "peak_force": round_float(impulses.max()) if not impulses.empty else pd.NA,
            }
        )

    return result


def force_lull_attempt_metrics(attempts: list) -> dict:
    """
    Derive all rdm_v16b_force_lull_* column values from the output of
    segment_force_lull_attempts().

    V1.6-B3.5-B.  Research only.  Additive — does not modify any existing
    field.
    """
    _na_defaults: dict = {
        "rdm_v16b_force_lull_attempt_count": pd.NA,
        "rdm_v16b_force_lull_attempt_rows_total": pd.NA,
        "rdm_v16b_force_lull_attempt_rows_mean": pd.NA,
        "rdm_v16b_force_lull_attempt_rows_max": pd.NA,
        "rdm_v16b_force_lull_attempt_first_row": pd.NA,
        "rdm_v16b_force_lull_attempt_last_row": pd.NA,
        "rdm_v16b_force_lull_attempt_row_spans": "",
        "rdm_v16b_force_lull_attempt_force_mean": pd.NA,
        "rdm_v16b_force_lull_attempt_force_peak": pd.NA,
        "rdm_v16b_force_lull_attempt_force_birth": pd.NA,
        "rdm_v16b_force_lull_attempt_force_final": pd.NA,
        "rdm_v16b_force_lull_attempt_force_delta": pd.NA,
        "rdm_v16b_force_lull_attempt_force_pct_change": pd.NA,
        "rdm_v16b_force_lull_attempt_force_trend_slope": pd.NA,
        "rdm_v16b_force_lull_attempt_force_trend_count": pd.NA,
        "rdm_v16b_force_lull_attempt_peak_event_index": pd.NA,
        "rdm_v16b_force_lull_segmentation_model": (
            "FORCE_LULL_ATTEMPT_SEGMENTATION_V1"
        ),
    }

    if not attempts:
        return _na_defaults

    out = dict(_na_defaults)
    n = len(attempts)
    row_counts = [a["row_count"] for a in attempts]

    # Counts and row geometry
    out["rdm_v16b_force_lull_attempt_count"] = n
    out["rdm_v16b_force_lull_attempt_rows_total"] = sum(row_counts)
    out["rdm_v16b_force_lull_attempt_rows_mean"] = round_float(sum(row_counts) / n)
    out["rdm_v16b_force_lull_attempt_rows_max"] = max(row_counts)

    first_start = attempts[0].get("start_ridx")
    last_end = attempts[-1].get("end_ridx")
    if first_start is not None and not (isinstance(first_start, float) and pd.isna(first_start)):
        out["rdm_v16b_force_lull_attempt_first_row"] = first_start
    if last_end is not None and not (isinstance(last_end, float) and pd.isna(last_end)):
        out["rdm_v16b_force_lull_attempt_last_row"] = last_end

    out["rdm_v16b_force_lull_attempt_row_spans"] = "|".join(
        f"{a.get('start_ridx', '?')}-{a.get('end_ridx', '?')}" for a in attempts
    )

    # Per-attempt mean forces (the evolution signal)
    attempt_means = [
        a["mean_force"] for a in attempts
        if isinstance(a.get("mean_force"), float) and pd.notna(a["mean_force"])
    ]
    attempt_peaks = [
        a["peak_force"] for a in attempts
        if isinstance(a.get("peak_force"), float) and pd.notna(a["peak_force"])
    ]

    if attempt_means:
        out["rdm_v16b_force_lull_attempt_force_mean"] = round_float(
            sum(attempt_means) / len(attempt_means)
        )
    if attempt_peaks:
        out["rdm_v16b_force_lull_attempt_force_peak"] = round_float(max(attempt_peaks))

    # Evolution: birth → final
    force_birth = attempt_means[0] if attempt_means else pd.NA
    force_final = attempt_means[-1] if attempt_means else pd.NA
    out["rdm_v16b_force_lull_attempt_force_birth"] = force_birth
    out["rdm_v16b_force_lull_attempt_force_final"] = force_final

    if isinstance(force_birth, float) and isinstance(force_final, float):
        out["rdm_v16b_force_lull_attempt_force_delta"] = round_float(
            force_final - force_birth
        )
        if force_birth != 0:
            out["rdm_v16b_force_lull_attempt_force_pct_change"] = round_float(
                (force_final - force_birth) / force_birth * 100
            )

    # Trend slope across attempt-level mean forces
    out["rdm_v16b_force_lull_attempt_force_trend_slope"] = (
        linear_slope_from_values(attempt_means)
    )
    out["rdm_v16b_force_lull_attempt_force_trend_count"] = (
        len(attempt_means) if attempt_means else pd.NA
    )

    # Peak event index (1-indexed attempt with highest mean force)
    if attempt_means:
        peak_idx = max(range(len(attempt_means)), key=lambda i: attempt_means[i])
        out["rdm_v16b_force_lull_attempt_peak_event_index"] = peak_idx + 1

    return out


def linear_slope_from_values(values: list) -> Any:
    """
    Compute the least-squares regression slope across a sequence of floats.

    Returns pd.NA when fewer than 3 valid values are present (insufficient
    data for a meaningful trend).  x-coordinates are zero-indexed integers.

    V1.6-B3 helper.  Does not change any existing calculation.
    """
    valid = [float(v) for v in values if v is not None and pd.notna(v)]
    if len(valid) < 3:
        return pd.NA

    n = len(valid)
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(valid) / n

    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(xs, valid))
    denominator = sum((xi - x_mean) ** 2 for xi in xs)

    if denominator == 0:
        return pd.NA

    return round_float(numerator / denominator)


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


def read_optional_csv(path: Path, usecols: list | None = None, dtype: dict | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, usecols=usecols, dtype=dtype)


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

import json
from pathlib import Path

import pandas as pd


RESEARCH_FIELDS = [
    "preparation_candidate",
    "preparation_strength",
    "return_to_preparation",
    "expansion_type",
    "expansion_strength",
    "reversal_type",
    "reversal_strength",
    "comparison_group",
    "preparation_result",
    "hypothesis02_state",
]

RESEARCH_CASE_FIELDS = [
    "case_id",
    "episode_id",
    "episode_start_time_utc",
    "episode_end_time_utc",
    "peak_layer_count",
    "peak_max_severity",
    "peak_primary_context",
    "preparation_candidate",
    "preparation_strength",
    "return_to_preparation",
    "pre_quiet_score",
    "pre_range_ratio",
    "preparation_result",
    "expansion_type",
    "expansion_strength",
    "time_to_expansion_minutes",
    "expansion_survived",
    "expansion_failed",
    "reversal_type",
    "reversal_strength",
    "time_to_reversal_minutes",
    "direct_reversal_flag",
    "late_reversal_flag",
    "reversal_after_return",
    "comparison_group",
    "hypothesis02_state",
    "classification",
    "classification_reason",
]

RDM_MECHANICS_FIELDS = [
    "mechanical_family",
    "mechanical_subtype",
    "zone_mechanical_state",
    "zone_fleche_state",
    "zone_fleche_ratio",
    "signed_moment_proxy",
    "moment_stress_type",
    "moment_absorption_flag",
    "mechanical_load_score",
    "fatigue_index",
    "fatigue_state",
    "zone_rigidity",
    "zone_strength_decay",
    "recovery_ratio",
    "zone_recovery_state",
    "moment_utilization_ratio",
    "els_elu_state",
    "reference_example_flag",
    "rdm_zone_status",
    "rdm_health_score",
    "rdm_risk_level",
    "rdm_confidence",
    "rdm_short_reason",
    "rdm_watch_action",
]

RDM_TIMELINE_FIELDS = [
    "timeline_step",
    "timeline_order",
    "previous_state",
    "next_state",
    "state_duration",
    "transition_reason",
    "lifecycle_path",
    "timeline_position",
]

RDM_CAPACITY_FIELDS = [
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

RDM_SIGMA_FIELDS = [
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

RDM_SIGMA_EVOLUTION_FIELDS = [
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

RDM_VERESTCHAGUINE_FIELDS = [
    "omega_stress_area",
    "stress_center_of_gravity",
    "virtual_moment_at_g",
    "ei_adaptive",
    "fleche_verestchaguine",
    "fleche_dynamic_state",
    "fleche_combined_score",
    "fleche_model_version",
]

RDM_BIRTH_FIELDS = [
    "zone_id",
    "zone_type",
    "birth_time",
    "birth_price_range",
    "upper_edge",
    "lower_edge",
    "zone_width",
    "formation_volume",
    "formation_delta",
    "formation_velocity",
    "formation_duration",
    "formation_quality",
    "base_resistance",
    "initial_sigma_barre",
    "initial_rigidity",
    "initial_capacity",
    "institutional_reinforcement",
    "mechanical_birth_state",
    "birth_confidence_score",
    "birth_candidate_count",
    "birth_reason",
    "birth_classification_source",
    "birth_regime",
    "birth_family_candidate",
    "zone_birth_time",
    "zone_last_test_time",
    "zone_active_duration",
    "zone_lifetime",
    "zone_decay_rate",
    "zone_survival_ratio",
]

RDM_DEATH_FIELDS = [
    "death_time",
    "death_cause",
    "final_state",
    "total_tests",
    "zone_age_at_death",
    "max_stress_utilization",
    "final_fleche",
    "final_dynamic_fleche",
    "final_sigma_state",
    "final_capacity_state",
    "final_timeline_path",
    "final_repair_count",
    "final_fatigue_cycles",
]

RDM_MEMORY_FIELDS = [
    "memory_previous_stress_states",
    "memory_cumulative_fleche",
    "memory_cumulative_dynamic_fleche",
    "memory_permanent_deformation",
    "memory_max_stress_utilization",
    "memory_max_sigma_market",
    "memory_max_fatigue_index",
    "memory_repair_count",
    "memory_rupture_count",
    "memory_exhaustion_count",
    "memory_recovery_count",
    "memory_elastic_cycles",
    "memory_plastic_cycles",
    "memory_fatigue_cycles",
    "memory_sigma_memory_state_history",
    "memory_capacity_history",
    "memory_timeline_history",
]

RDM_EVOLUTION_FIELDS = [
    "birth_state",
    "current_state",
    "previous_state_evolution",
    "next_candidate_state",
    "state_transition_reason",
    "transition_count",
    "life_stage_index_evolution",
    "mechanical_age",
    "survival_ratio",
    "fatigue_progress",
    "recovery_progress",
    "rupture_progress",
    "plastic_progress",
    "elastic_progress",
    "sigma_progress",
    "capacity_progress",
    "transition_source",
    "transition_target",
    "transition_reason_evolution",
    "transition_strength",
    "evolution_timeline",
]


def load_dashboard_research_mapping(base_dir):
    research_dir = Path(base_dir) / "research"
    episode_log = read_csv(research_dir / "phase1b_episode_research_log.csv")
    comparison_log = read_csv(research_dir / "phase1b_comparison_log.csv")
    preparation_quality = read_csv(
        research_dir / "phase1b_preparation_quality.csv"
    )
    rdm_mechanics = read_csv(
        research_dir / "zone_mechanics_cycle3_results.csv"
    )
    rdm_timeline = read_csv(
        research_dir / "zone_mechanics_timeline.csv"
    )
    rdm_capacity = read_csv(
        research_dir / "zone_mechanics_capacity.csv"
    )
    rdm_sigma = read_csv(
        research_dir / "zone_mechanics_sigma.csv"
    )
    rdm_sigma_evolution = read_csv(
        research_dir / "zone_mechanics_sigma_evolution.csv"
    )
    rdm_verestchaguine = read_csv(
        research_dir / "zone_mechanics_verestchaguine.csv"
    )
    rdm_birth = read_csv(
        research_dir / "zone_birth_registry.csv"
    )
    rdm_death = read_csv(
        research_dir / "zone_death_registry.csv"
    )
    rdm_memory = read_zone_memory(
        research_dir / "zone_mechanical_memory.json"
    )
    rdm_evolution = read_csv(
        research_dir / "zone_evolution_chart.csv"
    )

    return build_research_mapping(
        episode_log=episode_log,
        comparison_log=comparison_log,
        preparation_quality=preparation_quality,
        rdm_mechanics=rdm_mechanics,
        rdm_timeline=rdm_timeline,
        rdm_capacity=rdm_capacity,
        rdm_sigma=rdm_sigma,
        rdm_sigma_evolution=rdm_sigma_evolution,
        rdm_verestchaguine=rdm_verestchaguine,
        rdm_birth=rdm_birth,
        rdm_death=rdm_death,
        rdm_memory=rdm_memory,
        rdm_evolution=rdm_evolution,
    )


def build_research_mapping(
    episode_log,
    comparison_log,
    preparation_quality,
    rdm_mechanics=None,
    rdm_timeline=None,
    rdm_capacity=None,
    rdm_sigma=None,
    rdm_sigma_evolution=None,
    rdm_verestchaguine=None,
    rdm_birth=None,
    rdm_death=None,
    rdm_memory=None,
    rdm_evolution=None,
):
    if episode_log.empty:
        return empty_mapping()

    mapping = episode_log.copy()
    ensure_columns(
        mapping,
        [
            "case_id",
            "episode_id",
            "preparation_candidate",
            "preparation_strength",
            "return_to_preparation",
            "expansion_type",
            "expansion_strength",
            "reversal_type",
            "reversal_strength",
            "expansion_after_return",
            "failed_after_return",
            "episode_start_time_utc",
            "episode_end_time_utc",
            "peak_layer_count",
            "peak_max_severity",
            "peak_primary_context",
            "pre_quiet_score",
            "pre_range_ratio",
            "time_to_expansion_minutes",
            "expansion_survived",
            "expansion_failed",
            "time_to_reversal_minutes",
            "direct_reversal_flag",
            "late_reversal_flag",
            "reversal_after_return",
            "classification",
            "classification_reason",
        ],
    )

    base_case_fields = [
        field
        for field in RESEARCH_CASE_FIELDS
        if field not in {
            "comparison_group",
            "preparation_result",
            "hypothesis02_state",
        }
    ]
    keep_episode_fields = list(
        dict.fromkeys(
            [
                *base_case_fields,
                "expansion_after_return",
                "failed_after_return",
            ]
        )
    )
    mapping = mapping[keep_episode_fields].copy()

    comparison_fields = comparison_case_fields(comparison_log)
    if not comparison_fields.empty:
        mapping = mapping.merge(
            comparison_fields,
            on="case_id",
            how="left",
        )
    else:
        mapping["comparison_group"] = ""

    quality_fields = preparation_quality_case_fields(preparation_quality)
    if not quality_fields.empty:
        mapping = mapping.merge(
            quality_fields,
            on="case_id",
            how="left",
        )
    else:
        mapping["preparation_result"] = ""

    mapping["hypothesis02_state"] = mapping.apply(
        derive_hypothesis02_state,
        axis=1,
    )

    mechanics_fields = rdm_mechanics_case_fields(
        rdm_mechanics if rdm_mechanics is not None else pd.DataFrame()
    )
    if not mechanics_fields.empty:
        mapping = mapping.merge(
            mechanics_fields,
            on="case_id",
            how="left",
        )
    else:
        ensure_columns(mapping, RDM_MECHANICS_FIELDS)

    timeline_fields = rdm_timeline_case_fields(
        rdm_timeline if rdm_timeline is not None else pd.DataFrame()
    )
    if not timeline_fields.empty:
        mapping = mapping.merge(
            timeline_fields,
            on="case_id",
            how="left",
        )
    else:
        ensure_columns(mapping, RDM_TIMELINE_FIELDS)

    capacity_fields = rdm_capacity_case_fields(
        rdm_capacity if rdm_capacity is not None else pd.DataFrame()
    )
    if not capacity_fields.empty:
        mapping = mapping.merge(
            capacity_fields,
            on="case_id",
            how="left",
        )
    else:
        ensure_columns(mapping, RDM_CAPACITY_FIELDS)

    sigma_fields = rdm_sigma_case_fields(
        rdm_sigma if rdm_sigma is not None else pd.DataFrame()
    )
    if not sigma_fields.empty:
        mapping = mapping.merge(
            sigma_fields,
            on="case_id",
            how="left",
        )
    else:
        ensure_columns(mapping, RDM_SIGMA_FIELDS)

    sigma_evolution_fields = rdm_sigma_evolution_case_fields(
        rdm_sigma_evolution if rdm_sigma_evolution is not None else pd.DataFrame()
    )
    if not sigma_evolution_fields.empty:
        mapping = mapping.merge(
            sigma_evolution_fields,
            on="case_id",
            how="left",
        )
    else:
        ensure_columns(mapping, RDM_SIGMA_EVOLUTION_FIELDS)

    verestchaguine_fields = rdm_verestchaguine_case_fields(
        rdm_verestchaguine if rdm_verestchaguine is not None else pd.DataFrame()
    )
    if not verestchaguine_fields.empty:
        mapping = mapping.merge(
            verestchaguine_fields,
            on="case_id",
            how="left",
        )
    else:
        ensure_columns(mapping, RDM_VERESTCHAGUINE_FIELDS)

    birth_fields = rdm_birth_case_fields(
        rdm_birth if rdm_birth is not None else pd.DataFrame()
    )
    if not birth_fields.empty:
        mapping = mapping.merge(
            birth_fields,
            on="case_id",
            how="left",
        )
    else:
        ensure_columns(mapping, RDM_BIRTH_FIELDS)

    death_fields = rdm_death_case_fields(
        rdm_death if rdm_death is not None else pd.DataFrame()
    )
    if not death_fields.empty:
        mapping = mapping.merge(
            death_fields,
            on="case_id",
            how="left",
        )
    else:
        ensure_columns(mapping, RDM_DEATH_FIELDS)

    memory_fields = rdm_memory_case_fields(
        rdm_memory if rdm_memory is not None else pd.DataFrame()
    )
    if not memory_fields.empty:
        mapping = mapping.merge(
            memory_fields,
            on="case_id",
            how="left",
        )
    else:
        ensure_columns(mapping, RDM_MEMORY_FIELDS)

    evolution_fields = rdm_evolution_case_fields(
        rdm_evolution if rdm_evolution is not None else pd.DataFrame()
    )
    if not evolution_fields.empty:
        mapping = mapping.merge(
            evolution_fields,
            on="case_id",
            how="left",
        )
    else:
        ensure_columns(mapping, RDM_EVOLUTION_FIELDS)

    keep_fields = list(
        dict.fromkeys(
            [
                *RESEARCH_CASE_FIELDS,
                *RESEARCH_FIELDS,
                *RDM_MECHANICS_FIELDS,
                *RDM_TIMELINE_FIELDS,
                *RDM_CAPACITY_FIELDS,
                *RDM_SIGMA_FIELDS,
                *RDM_SIGMA_EVOLUTION_FIELDS,
                *RDM_VERESTCHAGUINE_FIELDS,
                *RDM_BIRTH_FIELDS,
                *RDM_DEATH_FIELDS,
                *RDM_MEMORY_FIELDS,
                *RDM_EVOLUTION_FIELDS,
            ]
        )
    )
    ensure_columns(mapping, keep_fields)
    return mapping[keep_fields].copy()


def map_research_to_dashboard_episodes(episodes, research_mapping):
    if episodes.empty or research_mapping.empty:
        return episodes.copy()

    mapped = episodes.copy()

    if "episode_id" not in mapped.columns:
        return mapped

    mapped["episode_id"] = mapped["episode_id"].astype(str)
    mapping = research_mapping.copy()
    mapping["episode_id"] = mapping["episode_id"].astype(str)

    return mapped.merge(
        mapping,
        on="episode_id",
        how="left",
        suffixes=("", "_research"),
    )


def comparison_case_fields(comparison_log):
    if comparison_log.empty:
        return pd.DataFrame(columns=["case_id", "comparison_group"])

    if "comparison_group" not in comparison_log.columns:
        return pd.DataFrame(columns=["case_id", "comparison_group"])

    rows = comparison_log[
        comparison_log["comparison_group"].astype(str).isin(
            ["PURE_EXPANSION", "DIRECT_REVERSAL"]
        )
    ].copy()

    if rows.empty:
        return pd.DataFrame(columns=["case_id", "comparison_group"])

    ensure_columns(rows, ["case_id", "comparison_group"])
    return rows[["case_id", "comparison_group"]].copy()


def preparation_quality_case_fields(preparation_quality):
    if preparation_quality.empty:
        return pd.DataFrame(columns=["case_id", "preparation_result"])

    rows = preparation_quality.copy()

    if "row_type" in rows.columns:
        rows = rows[rows["row_type"].astype(str) == "CASE"].copy()

    ensure_columns(rows, ["case_id", "preparation_result"])
    return rows[["case_id", "preparation_result"]].copy()


def rdm_mechanics_case_fields(rdm_mechanics):
    if rdm_mechanics.empty:
        return pd.DataFrame(columns=["case_id", *RDM_MECHANICS_FIELDS])

    rows = rdm_mechanics.copy()
    ensure_columns(rows, ["case_id", *RDM_MECHANICS_FIELDS])
    return rows[["case_id", *RDM_MECHANICS_FIELDS]].copy()


def rdm_timeline_case_fields(rdm_timeline):
    if rdm_timeline.empty:
        return pd.DataFrame(columns=["case_id", *RDM_TIMELINE_FIELDS])

    rows = rdm_timeline.copy()
    ensure_columns(rows, ["case_id", *RDM_TIMELINE_FIELDS])
    return rows[["case_id", *RDM_TIMELINE_FIELDS]].copy()


def rdm_capacity_case_fields(rdm_capacity):
    if rdm_capacity.empty:
        return pd.DataFrame(columns=["case_id", *RDM_CAPACITY_FIELDS])

    rows = rdm_capacity.copy()
    ensure_columns(rows, ["case_id", *RDM_CAPACITY_FIELDS])
    return rows[["case_id", *RDM_CAPACITY_FIELDS]].copy()


def rdm_sigma_case_fields(rdm_sigma):
    if rdm_sigma.empty:
        return pd.DataFrame(columns=["case_id", *RDM_SIGMA_FIELDS])

    rows = rdm_sigma.copy()
    ensure_columns(rows, ["case_id", *RDM_SIGMA_FIELDS])
    return rows[["case_id", *RDM_SIGMA_FIELDS]].copy()


def rdm_sigma_evolution_case_fields(rdm_sigma_evolution):
    if rdm_sigma_evolution.empty:
        return pd.DataFrame(columns=["case_id", *RDM_SIGMA_EVOLUTION_FIELDS])

    rows = rdm_sigma_evolution.copy()
    ensure_columns(rows, ["case_id", *RDM_SIGMA_EVOLUTION_FIELDS])
    return rows[["case_id", *RDM_SIGMA_EVOLUTION_FIELDS]].copy()


def rdm_verestchaguine_case_fields(rdm_verestchaguine):
    if rdm_verestchaguine.empty:
        return pd.DataFrame(columns=["case_id", *RDM_VERESTCHAGUINE_FIELDS])

    rows = rdm_verestchaguine.copy()
    ensure_columns(rows, ["case_id", *RDM_VERESTCHAGUINE_FIELDS])
    return rows[["case_id", *RDM_VERESTCHAGUINE_FIELDS]].copy()


def rdm_birth_case_fields(rdm_birth):
    if rdm_birth.empty:
        return pd.DataFrame(columns=["case_id", *RDM_BIRTH_FIELDS])

    rows = rdm_birth.copy()
    ensure_columns(rows, ["case_id", *RDM_BIRTH_FIELDS])
    return rows[["case_id", *RDM_BIRTH_FIELDS]].copy()


def rdm_death_case_fields(rdm_death):
    if rdm_death.empty:
        return pd.DataFrame(columns=["case_id", *RDM_DEATH_FIELDS])

    rows = rdm_death.copy()
    ensure_columns(rows, ["case_id", *RDM_DEATH_FIELDS])
    return rows[["case_id", *RDM_DEATH_FIELDS]].copy()


def rdm_memory_case_fields(rdm_memory):
    if rdm_memory.empty:
        return pd.DataFrame(columns=["case_id", *RDM_MEMORY_FIELDS])

    rows = rdm_memory.copy()
    ensure_columns(rows, ["case_id", *RDM_MEMORY_FIELDS])
    return rows[["case_id", *RDM_MEMORY_FIELDS]].copy()


def rdm_evolution_case_fields(rdm_evolution):
    if rdm_evolution.empty:
        return pd.DataFrame(columns=["case_id", *RDM_EVOLUTION_FIELDS])

    rows = rdm_evolution.copy()
    rename_map = {
        "previous_state": "previous_state_evolution",
        "life_stage_index": "life_stage_index_evolution",
        "transition_reason": "transition_reason_evolution",
    }
    rows = rows.rename(columns=rename_map)
    ensure_columns(rows, ["case_id", *RDM_EVOLUTION_FIELDS])
    return rows[["case_id", *RDM_EVOLUTION_FIELDS]].copy()


def derive_hypothesis02_state(row):
    if truthy_value(row.get("failed_after_return")):
        return "RETURN_FAILURE"

    if (
        truthy_value(row.get("return_to_preparation"))
        and truthy_value(row.get("expansion_after_return"))
    ):
        return "RETURN_EXPANSION_OBSERVED"

    if truthy_value(row.get("return_to_preparation")):
        return "RETURN_OBSERVED"

    if truthy_value(row.get("preparation_candidate")):
        return "PREPARATION_NO_RETURN"

    return "NO_RESEARCH_CONTEXT"


def ensure_columns(dataframe, columns):
    for column in columns:
        if column not in dataframe.columns:
            dataframe[column] = ""


def empty_mapping():
    return pd.DataFrame(
        columns=[
            "case_id",
            "episode_id",
            *RESEARCH_FIELDS,
            *RDM_MECHANICS_FIELDS,
            *RDM_TIMELINE_FIELDS,
            *RDM_CAPACITY_FIELDS,
            *RDM_SIGMA_FIELDS,
            *RDM_SIGMA_EVOLUTION_FIELDS,
            *RDM_VERESTCHAGUINE_FIELDS,
            *RDM_BIRTH_FIELDS,
            *RDM_DEATH_FIELDS,
            *RDM_MEMORY_FIELDS,
            *RDM_EVOLUTION_FIELDS,
        ]
    )


def read_csv(path):
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def read_zone_memory(path):
    if not path.exists():
        return pd.DataFrame()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return pd.DataFrame()

    rows = []
    for zone in payload.get("zones", {}).values():
        rows.append(
            {
                "case_id": zone.get("case_id", ""),
                "memory_previous_stress_states": format_memory_list(
                    zone.get("previous_stress_states")
                ),
                "memory_cumulative_fleche": zone.get("cumulative_fleche", ""),
                "memory_cumulative_dynamic_fleche": zone.get("cumulative_dynamic_fleche", ""),
                "memory_permanent_deformation": zone.get("permanent_deformation", ""),
                "memory_max_stress_utilization": zone.get("max_stress_utilization", ""),
                "memory_max_sigma_market": zone.get("max_sigma_market", ""),
                "memory_max_fatigue_index": zone.get("max_fatigue_index", ""),
                "memory_repair_count": zone.get("repair_count", ""),
                "memory_rupture_count": zone.get("rupture_count", ""),
                "memory_exhaustion_count": zone.get("exhaustion_count", ""),
                "memory_recovery_count": zone.get("recovery_count", ""),
                "memory_elastic_cycles": zone.get("elastic_cycles", ""),
                "memory_plastic_cycles": zone.get("plastic_cycles", ""),
                "memory_fatigue_cycles": zone.get("fatigue_cycles", ""),
                "memory_sigma_memory_state_history": format_memory_list(
                    zone.get("sigma_memory_state_history")
                ),
                "memory_capacity_history": format_memory_list(
                    zone.get("capacity_history")
                ),
                "memory_timeline_history": format_memory_list(
                    zone.get("timeline_history")
                ),
            }
        )

    return pd.DataFrame(rows)


def format_memory_list(value):
    if isinstance(value, list):
        return "|".join(str(item) for item in value if str(item))
    return str(value or "")


def truthy_value(value):
    if value is None:
        return False

    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value != 0

    return str(value).strip().lower() in {"true", "1", "yes", "y"}

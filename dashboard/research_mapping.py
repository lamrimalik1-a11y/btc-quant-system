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

    return build_research_mapping(
        episode_log=episode_log,
        comparison_log=comparison_log,
        preparation_quality=preparation_quality,
        rdm_mechanics=rdm_mechanics,
        rdm_timeline=rdm_timeline,
        rdm_capacity=rdm_capacity,
        rdm_sigma=rdm_sigma,
    )


def build_research_mapping(
    episode_log,
    comparison_log,
    preparation_quality,
    rdm_mechanics=None,
    rdm_timeline=None,
    rdm_capacity=None,
    rdm_sigma=None,
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

    keep_fields = list(
        dict.fromkeys(
            [
                *RESEARCH_CASE_FIELDS,
                *RESEARCH_FIELDS,
                *RDM_MECHANICS_FIELDS,
                *RDM_TIMELINE_FIELDS,
                *RDM_CAPACITY_FIELDS,
                *RDM_SIGMA_FIELDS,
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
        ]
    )


def read_csv(path):
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


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

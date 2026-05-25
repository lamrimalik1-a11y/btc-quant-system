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


def load_dashboard_research_mapping(base_dir):
    research_dir = Path(base_dir) / "research"
    episode_log = read_csv(research_dir / "phase1b_episode_research_log.csv")
    comparison_log = read_csv(research_dir / "phase1b_comparison_log.csv")
    preparation_quality = read_csv(
        research_dir / "phase1b_preparation_quality.csv"
    )

    return build_research_mapping(
        episode_log=episode_log,
        comparison_log=comparison_log,
        preparation_quality=preparation_quality,
    )


def build_research_mapping(episode_log, comparison_log, preparation_quality):
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

    keep_fields = list(dict.fromkeys([*RESEARCH_CASE_FIELDS, *RESEARCH_FIELDS]))
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
    return pd.DataFrame(columns=["case_id", "episode_id", *RESEARCH_FIELDS])


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

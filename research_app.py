from pathlib import Path

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent
RESEARCH_DIR = ROOT_DIR / "research"

RESEARCH_LOG_FILE = RESEARCH_DIR / "phase1b_episode_research_log.csv"
PREPARATION_ZONES_FILE = RESEARCH_DIR / "phase1b_preparation_zones.csv"
RESEARCH_SUMMARY_FILE = RESEARCH_DIR / "phase1b_research_summary.csv"
RESEARCH_JOURNAL_FILE = RESEARCH_DIR / "RESEARCH_JOURNAL.md"
COMPARISON_LOG_FILE = RESEARCH_DIR / "phase1b_comparison_log.csv"
PREPARATION_QUALITY_FILE = RESEARCH_DIR / "phase1b_preparation_quality.csv"

CLASSIFICATION_COLUMNS = [
    "classification",
    "case_id",
]

COMPACT_EPISODE_COLUMNS = [
    "case_id",
    "episode_id",
    "episode_start_time_utc",
    "score_bucket",
    "peak_layer_count",
    "peak_max_severity",
    "peak_primary_context",
    "classification",
    "preparation_candidate",
    "preparation_strength",
    "expansion_type",
    "reversal_type",
    "max_abs_move_4h",
    "manual_review_required",
]

CASE_BASIC_COLUMNS = [
    "case_id",
    "episode_id",
    "episode_start_time_utc",
    "episode_end_time_utc",
    "score_bucket",
    "peak_layer_count",
    "peak_max_severity",
    "peak_primary_context",
]

CASE_CONTEXT_COLUMNS = [
    "peak_state",
    "peak_conditions",
    "peak_active_layers",
    "peak_observation_confidence",
]

CASE_FUTURE_COLUMNS = [
    "move_1m",
    "move_5m",
    "move_15m",
    "move_30m",
    "move_1h",
    "move_2h",
    "move_4h",
    "move_day_end",
]

CASE_MAX_COLUMNS = [
    "max_up_move_1h",
    "max_down_move_1h",
    "max_abs_move_1h",
    "max_up_move_4h",
    "max_down_move_4h",
    "max_abs_move_4h",
]

CASE_PREPARATION_COLUMNS = [
    "preparation_zone_found",
    "preparation_candidate",
    "preparation_strength",
    "pre_quiet_score",
    "pre_compression_ratio",
    "pre_range_value",
    "pre_range_ratio",
    "pre_delta_mean",
    "pre_delta_abs_mean",
    "pre_velocity_mean",
    "pre_velocity_abs_mean",
    "pre_zscore_abs_mean",
    "pre_market_bias",
    "pre_setup_quality",
    "pre_setup_reason",
    "preparation_start_row",
    "preparation_end_row",
    "preparation_duration_rows",
    "preparation_low_price",
    "preparation_high_price",
    "preparation_mid_price",
    "pre_entropy",
    "pre_price_zscore_mean",
    "pre_range_mean",
    "pre_volume_mean",
    "pre_market_state",
]

CASE_RESEARCH_COLUMNS = [
    "classification",
    "classification_reason",
    "manual_review_required",
    "manual_notes",
]

CASE_HYPOTHESIS_02_COLUMNS = [
    "episode_direction_proxy",
    "future_direction",
    "agreement_flag",
    "expansion_strength",
    "return_to_preparation",
    "time_to_return_minutes",
    "expansion_after_return",
    "zone_revisit_count",
    "max_move_after_return",
    "direction_after_return",
    "return_price",
    "return_row",
    "return_timestamp",
    "revisit_duration_rows",
    "revisit_expansion_delay_minutes",
]

CASE_REVERSAL_COLUMNS = [
    "reversal_distance_1m",
    "reversal_distance_5m",
    "reversal_distance_15m",
    "reversal_distance_30m",
    "reversal_distance_1h",
    "reversal_distance_4h",
    "reversal_strength",
    "time_to_reversal_minutes",
    "peak_before_reversal",
    "reversal_ratio",
    "reversal_after_return",
    "failed_after_return",
    "direct_reversal_flag",
    "late_reversal_flag",
    "reversal_type",
]

CASE_EXPANSION_COLUMNS = [
    "expansion_before_reversal",
    "time_to_expansion_minutes",
    "expansion_strength",
    "expansion_to_reversal_ratio",
    "expansion_survived",
    "expansion_failed",
    "expansion_type",
]

EXPANSION_LAB_COLUMNS = [
    "case_id",
    "episode_id",
    "episode_start_time_utc",
    "score_bucket",
    "peak_layer_count",
    "peak_max_severity",
    "peak_primary_context",
    "episode_direction_proxy",
    "future_direction",
    "agreement_flag",
    "expansion_type",
    "expansion_strength",
    "time_to_expansion_minutes",
    "expansion_to_reversal_ratio",
    "expansion_survived",
    "expansion_failed",
    "reversal_type",
    "reversal_strength",
    "time_to_reversal_minutes",
    "reversal_distance_4h",
    "max_up_move_4h",
    "max_down_move_4h",
    "classification",
    "classification_reason",
]

REVERSAL_LAB_COLUMNS = [
    "case_id",
    "episode_id",
    "episode_start_time_utc",
    "score_bucket",
    "peak_layer_count",
    "peak_max_severity",
    "peak_primary_context",
    "episode_direction_proxy",
    "future_direction",
    "agreement_flag",
    "return_to_preparation",
    "reversal_type",
    "reversal_strength",
    "time_to_reversal_minutes",
    "reversal_distance_15m",
    "reversal_distance_1h",
    "reversal_distance_4h",
    "max_up_move_4h",
    "max_down_move_4h",
    "classification",
    "classification_reason",
]

PREPARATION_COLUMNS = [
    "case_id",
    "episode_id",
    "preparation_start_row",
    "preparation_end_row",
    "preparation_low_price",
    "preparation_high_price",
    "preparation_mid_price",
    "preparation_strength",
    "pre_quiet_score",
    "pre_range_ratio",
    "pre_market_bias",
    "pre_setup_quality",
    "pre_setup_reason",
    "return_to_preparation",
    "max_move_after_return",
    "preparation_duration_rows",
    "pre_market_state",
    "pre_range_mean",
    "pre_volume_mean",
    "pre_price_zscore_mean",
    "pre_entropy",
]

FULL_PREPARE_ANALYSIS_COLUMNS = [
    "case_id",
    "episode_id",
    "episode_start_time_utc",
    "preparation_candidate",
    "preparation_zone_found",
    "preparation_strength",
    "zone_type",
    "zone_health_grade",
    "manipulation_risk_score",
    "zone_type_confidence",
    "attacker_persistence_max",
    "penetration_depth_decay",
    "volume_decay_on_attempts",
    "recovery_speed_mean_rows",
    "delta_trap_count",
    "classification",
    "classification_reason",
    "pre_setup_reason",
    "manual_notes",
]

ZONE_CLASSIFICATION_COLUMNS = [
    "case_id",
    "episode_id",
    "episode_start_time_utc",
    "preparation_candidate",
    "preparation_strength",
    "zone_type",
    "zone_health_grade",
    "manipulation_risk_score",
    "zone_type_confidence",
    "attacker_persistence_max",
    "penetration_depth_decay",
    "volume_decay_on_attempts",
    "recovery_speed_mean_rows",
    "delta_trap_count",
    "classification",
    "classification_reason",
]

MOVE_COLUMNS = [
    "move_5m",
    "move_15m",
    "move_30m",
    "move_1h",
    "move_4h",
]


st.set_page_config(
    page_title="BTC Quant Phase 1B Research Dashboard",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_csv(path_string):
    path = Path(path_string)

    if not path.exists():
        return pd.DataFrame(), f"Missing file: {relative_path(path)}"

    try:
        return pd.read_csv(path), None
    except pd.errors.EmptyDataError:
        return pd.DataFrame(), f"Empty file: {relative_path(path)}"
    except Exception as error:  # pragma: no cover - Streamlit display safety.
        return pd.DataFrame(), f"Could not read {relative_path(path)}: {error}"


@st.cache_data(show_spinner=False)
def load_text(path_string):
    path = Path(path_string)

    if not path.exists():
        return "", f"Missing file: {relative_path(path)}"

    try:
        return path.read_text(encoding="utf-8"), None
    except Exception as error:  # pragma: no cover - Streamlit display safety.
        return "", f"Could not read {relative_path(path)}: {error}"


def main():
    st.title("BTC Quant Phase 1B Research Dashboard")
    st.caption("Observation research interface — read-only")

    research_log, log_warning = load_csv(str(RESEARCH_LOG_FILE))
    preparation_zones, preparation_warning = load_csv(str(PREPARATION_ZONES_FILE))
    research_summary, summary_warning = load_csv(str(RESEARCH_SUMMARY_FILE))
    comparison_log, comparison_warning = load_csv(str(COMPARISON_LOG_FILE))
    preparation_quality, preparation_quality_warning = load_csv(
        str(PREPARATION_QUALITY_FILE)
    )
    journal_text, journal_warning = load_text(str(RESEARCH_JOURNAL_FILE))

    show_file_warnings(
        [
            log_warning,
            preparation_warning,
            summary_warning,
            comparison_warning,
            preparation_quality_warning,
            journal_warning,
        ]
    )

    if research_log.empty:
        st.info("Waiting for Phase 1B research data...")
        return

    normalized_log = normalize_dataframe(research_log)
    filtered_log = apply_sidebar_filters(normalized_log)

    tabs = st.tabs(
        [
            "Overview",
            "Episodes",
            "Case Review",
            "Movement Analysis",
            "Reversal Lab",
            "Expansion Lab",
            "Comparison Lab",
            "Preparation Zones",
            "Preparation Quality",
            "Hypothesis 02",
            "Journal",
        ]
    )

    with tabs[0]:
        render_overview(filtered_log, research_summary)
        render_classification_breakdown(filtered_log)

    with tabs[1]:
        render_episode_explorer(filtered_log)

    with tabs[2]:
        render_case_review(filtered_log)

    with tabs[3]:
        render_movement_analysis(filtered_log)

    with tabs[4]:
        render_reversal_lab(filtered_log)

    with tabs[5]:
        render_expansion_lab(filtered_log)

    with tabs[6]:
        render_comparison_lab(comparison_log)

    with tabs[7]:
        render_preparation_zones(filtered_log, preparation_zones)

    with tabs[8]:
        render_preparation_quality(preparation_quality)

    with tabs[9]:
        render_hypothesis_02(filtered_log)

    with tabs[10]:
        render_journal(journal_text, journal_warning)


def apply_sidebar_filters(dataframe):
    st.sidebar.header("Research Filters")

    filtered = dataframe.copy()

    date_options = options_from_column(filtered, "date_bucket")
    selected_date = st.sidebar.selectbox(
        "Date",
        ["ALL", *date_options],
        key="research_date_filter",
    )

    score_options = [
        value
        for value in ["SCORE_4", "SCORE_5", "SCORE_6"]
        if column_contains(filtered, "score_bucket", value)
    ]
    selected_score = st.sidebar.selectbox(
        "Layer Count Proxy",
        ["ALL", *score_options],
        key="research_score_filter",
    )
    st.sidebar.caption(
        "V2 has no direct score field. Score bucket currently maps from "
        "peak_layer_count."
    )

    classification_options = options_from_column(filtered, "classification")
    selected_classification = st.sidebar.selectbox(
        "Classification",
        ["ALL", *classification_options],
        key="research_classification_filter",
    )

    severity_options = options_from_column(filtered, "severity_bucket")
    selected_severity = st.sidebar.selectbox(
        "Severity",
        ["ALL", *severity_options],
        key="research_severity_filter",
    )

    context_options = options_from_column(filtered, "primary_context_bucket")
    selected_context = st.sidebar.selectbox(
        "Primary Context",
        ["ALL", *context_options],
        key="research_context_filter",
    )

    selected_preparation = st.sidebar.selectbox(
        "Preparation Zone",
        ["ALL", "FOUND", "NOT_FOUND"],
        key="research_preparation_filter",
    )

    selected_min_layer_count = st.sidebar.slider(
        "Minimum Layer Count",
        min_value=1,
        max_value=10,
        value=1,
        step=1,
        key="research_layer_count_filter",
    )

    selected_manual_review = st.sidebar.selectbox(
        "Manual Review Required",
        ["ALL", "YES", "NO"],
        key="research_manual_review_filter",
    )

    filtered = filter_equals(filtered, "date_bucket", selected_date)
    filtered = filter_equals(filtered, "score_bucket", selected_score)
    filtered = filter_equals(filtered, "classification", selected_classification)
    filtered = filter_equals(filtered, "severity_bucket", selected_severity)
    filtered = filter_equals(filtered, "primary_context_bucket", selected_context)

    if selected_preparation != "ALL":
        expected = selected_preparation == "FOUND"
        if "preparation_zone_found" in filtered.columns:
            filtered = filtered[
                filtered["preparation_zone_found"].apply(bool_value) == expected
            ]
        else:
            missing_column_warning("preparation_zone_found")
            filtered = filtered.head(0)

    if "peak_layer_count" in filtered.columns:
        layer_counts = pd.to_numeric(
            filtered["peak_layer_count"],
            errors="coerce",
        ).fillna(0)
        filtered = filtered[layer_counts >= selected_min_layer_count]
    else:
        missing_column_warning("peak_layer_count")

    if selected_manual_review != "ALL":
        expected = selected_manual_review == "YES"
        if "manual_review_required" in filtered.columns:
            filtered = filtered[
                filtered["manual_review_required"].apply(bool_value) == expected
            ]
        else:
            missing_column_warning("manual_review_required")
            filtered = filtered.head(0)

    st.sidebar.metric("Displayed Cases", len(filtered))
    st.sidebar.metric("Total Loaded Cases", len(dataframe))
    st.sidebar.caption("Research only. No trading signals. No execution.")

    return filtered


def render_overview(dataframe, summary):
    st.subheader("Overview")
    st.caption("Global research summary.")

    summary_row = summary.iloc[0].to_dict() if not summary.empty else {}

    metrics = [
        ("Total analyzed cases", len(dataframe)),
        ("Research candidates", count_true(dataframe, "is_research_candidate")),
        (
            "Layer proxy 4 count",
            count_value(dataframe, "score_bucket", "SCORE_4"),
        ),
        (
            "Layer proxy 5 count",
            count_value(dataframe, "score_bucket", "SCORE_5"),
        ),
        (
            "Layer proxy 6 count",
            count_value(dataframe, "score_bucket", "SCORE_6"),
        ),
        (
            "Preparation zones found",
            count_true(dataframe, "preparation_zone_found"),
        ),
        (
            "Preparation candidates",
            count_true(dataframe, "preparation_candidate"),
        ),
        (
            "High preparation count",
            count_value(dataframe, "preparation_strength", "HIGH"),
        ),
        (
            "Return to preparation",
            count_true(dataframe, "return_to_preparation"),
        ),
        (
            "Momentum precursor count",
            count_value(dataframe, "classification", "MOMENTUM_PRECURSOR"),
        ),
        (
            "Pre-expansion count",
            count_value(dataframe, "classification", "PRE_EXPANSION"),
        ),
        (
            "Acceleration zone count",
            count_value(dataframe, "classification", "ACCELERATION_ZONE"),
        ),
        (
            "Reversal warning count",
            count_value(dataframe, "classification", "REVERSAL_WARNING"),
        ),
        (
            "Failed context count",
            count_value(dataframe, "classification", "FAILED_CONTEXT"),
        ),
        (
            "Context only count",
            count_value(dataframe, "classification", "CONTEXT_ONLY"),
        ),
    ]

    columns = st.columns(4)
    for index, (label, value) in enumerate(metrics):
        columns[index % 4].metric(label, safe_metric_value(value))

    if summary_row:
        with st.expander("Latest summary file", expanded=False):
            st.dataframe(
                sanitize_dataframe_for_display(summary),
                use_container_width=True,
                hide_index=True,
            )


def render_classification_breakdown(dataframe):
    st.subheader("Classification Breakdown")

    if dataframe.empty:
        st.info("No cases match the current filters.")
        return

    if not has_columns(dataframe, CLASSIFICATION_COLUMNS):
        return

    classification_counts = (
        dataframe["classification"]
        .value_counts(dropna=False)
        .rename_axis("classification")
        .reset_index(name="count")
    )
    st.dataframe(
        sanitize_dataframe_for_display(classification_counts),
        use_container_width=True,
        hide_index=True,
    )

    if has_columns(dataframe, ["score_bucket", "classification"]):
        pivot = pd.pivot_table(
            dataframe,
            index="score_bucket",
            columns="classification",
            values="case_id",
            aggfunc="count",
            fill_value=0,
        ).reset_index()
        pivot = pivot.rename(columns={"score_bucket": "layer_count_proxy"})
        st.dataframe(
            sanitize_dataframe_for_display(pivot),
            use_container_width=True,
            hide_index=True,
        )


def render_episode_explorer(dataframe):
    st.subheader("Episode Explorer")
    st.caption("Filtered cases.")

    if dataframe.empty:
        st.info("No cases match the current filters.")
        return

    st.dataframe(
        sanitize_dataframe_for_display(
            select_existing_columns(dataframe, COMPACT_EPISODE_COLUMNS)
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_case_review(dataframe):
    st.subheader("Case Review")
    st.caption("Detailed review for one selected case.")

    if dataframe.empty:
        st.info("No cases match the current filters.")
        return

    if "case_id" not in dataframe.columns:
        missing_column_warning("case_id")
        return

    case_ids = [str(value) for value in dataframe["case_id"].dropna().unique()]

    if not case_ids:
        st.info("No case IDs available.")
        return

    selected_case_id = st.selectbox(
        "Select case_id",
        case_ids,
        key="research_case_selector",
    )
    selected = dataframe[dataframe["case_id"].astype(str) == selected_case_id]

    if selected.empty:
        st.info("Selected case is not available after filters.")
        return

    row = selected.iloc[0]

    left, right = st.columns(2)
    with left:
        render_key_value_block("Basic Info", row, CASE_BASIC_COLUMNS)
        render_key_value_block("Future Movement", row, CASE_FUTURE_COLUMNS)
        render_key_value_block("Preparation", row, CASE_PREPARATION_COLUMNS)

    with right:
        render_key_value_block("Episode Context", row, CASE_CONTEXT_COLUMNS)
        render_key_value_block("Max Movement", row, CASE_MAX_COLUMNS)
        render_key_value_block("Research Classification", row, CASE_RESEARCH_COLUMNS)
        render_key_value_block("Hypothesis 02", row, CASE_HYPOTHESIS_02_COLUMNS)
        render_key_value_block("Reversal Lab", row, CASE_REVERSAL_COLUMNS)
        render_key_value_block("Expansion Lab", row, CASE_EXPANSION_COLUMNS)


def render_preparation_zones(research_log, preparation_zones):
    st.subheader("Preparation Zones")
    st.caption("Preparation review split into full True/False analysis and detected geometry.")

    st.markdown("### Full Prepare Zone Analysis = True and False")
    st.caption(
        "All analyzed episodes from phase1b_episode_research_log.csv, including "
        "cases where preparation was not detected."
    )

    if research_log.empty:
        st.info("No analyzed research cases match the current filters.")
    else:
        full_analysis = select_existing_columns(
            research_log,
            FULL_PREPARE_ANALYSIS_COLUMNS,
        )
        st.dataframe(
            sanitize_dataframe_for_display(full_analysis),
            use_container_width=True,
            hide_index=True,
        )

        render_preparation_zone_classification(research_log)

    st.markdown("### Preparation Zone Geometry = True cases only")
    st.caption(
        "Detected preparation-zone geometry from phase1b_preparation_zones.csv. "
        "This file intentionally contains True cases only."
    )

    if preparation_zones.empty:
        st.info(
            "Preparation zones may be unavailable if required historical fields are missing."
        )
        return

    st.dataframe(
        sanitize_dataframe_for_display(
            select_existing_columns(preparation_zones, PREPARATION_COLUMNS)
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_preparation_zone_classification(dataframe):
    st.markdown("### Preparation Zone Classification V1")
    st.caption(
        "Classification fields already generated in phase1b_episode_research_log.csv. "
        "Displayed for observation only."
    )

    if "zone_type" not in dataframe.columns:
        missing_column_warning("zone_type")
        return

    render_zone_type_distribution(dataframe)
    render_top_zone_classification_tables(dataframe)


def render_zone_type_distribution(dataframe):
    st.markdown("Zone Type Distribution")

    zone_types = [
        "BATTLE",
        "EXHAUSTION",
        "MANIPULATED",
        "MIXED",
        "CLEAN",
    ]
    rows = [
        {
            "zone_type": zone_type,
            "count": count_value(dataframe, "zone_type", zone_type),
        }
        for zone_type in zone_types
    ]

    distribution = pd.DataFrame(rows)
    st.dataframe(
        sanitize_dataframe_for_display(distribution),
        use_container_width=True,
        hide_index=True,
    )


def render_top_zone_classification_tables(dataframe):
    st.markdown("Top Manipulation Risk Cases")
    manipulation_cases = sort_dataframe(
        dataframe,
        "manipulation_risk_score",
        False,
    )
    render_zone_classification_table(manipulation_cases.head(10))

    st.markdown("Top Battle Zones")
    battle_zones = dataframe[
        dataframe["zone_type"].astype(str) == "BATTLE"
    ].copy()
    battle_zones = sort_by_preparation_strength_and_confidence(battle_zones)
    render_zone_classification_table(battle_zones.head(10))

    st.markdown("Top Exhaustion Zones")
    exhaustion_zones = dataframe[
        dataframe["zone_type"].astype(str) == "EXHAUSTION"
    ].copy()
    exhaustion_zones = sort_by_preparation_strength(exhaustion_zones)
    render_zone_classification_table(exhaustion_zones.head(10))


def render_zone_classification_table(dataframe):
    if dataframe.empty:
        st.info("No cases available for this table.")
        return

    st.dataframe(
        sanitize_dataframe_for_display(
            round_numeric_dataframe(
                select_existing_columns(dataframe, ZONE_CLASSIFICATION_COLUMNS)
            )
        ),
        use_container_width=True,
        hide_index=True,
    )


def sort_by_preparation_strength_and_confidence(dataframe):
    sorted_dataframe = add_preparation_strength_rank(dataframe)
    if "zone_type_confidence" in sorted_dataframe.columns:
        sorted_dataframe["_zone_type_confidence_sort"] = pd.to_numeric(
            sorted_dataframe["zone_type_confidence"],
            errors="coerce",
        )
    else:
        sorted_dataframe["_zone_type_confidence_sort"] = 0

    sorted_dataframe = sorted_dataframe.sort_values(
        ["_preparation_strength_rank", "_zone_type_confidence_sort"],
        ascending=[False, False],
        na_position="last",
    )

    return sorted_dataframe.drop(
        columns=[
            "_preparation_strength_rank",
            "_zone_type_confidence_sort",
        ],
        errors="ignore",
    )


def sort_by_preparation_strength(dataframe):
    sorted_dataframe = add_preparation_strength_rank(dataframe)
    sorted_dataframe = sorted_dataframe.sort_values(
        "_preparation_strength_rank",
        ascending=False,
        na_position="last",
    )

    return sorted_dataframe.drop(
        columns=["_preparation_strength_rank"],
        errors="ignore",
    )


def add_preparation_strength_rank(dataframe):
    sorted_dataframe = dataframe.copy()
    rank = {
        "NONE": 0,
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "EXTREME": 4,
    }
    sorted_dataframe["_preparation_strength_rank"] = (
        sorted_dataframe.get("preparation_strength", "NONE")
        .fillna("NONE")
        .astype(str)
        .str.upper()
        .map(rank)
        .fillna(0)
    )

    return sorted_dataframe


def render_movement_analysis(dataframe):
    st.subheader("Movement Analysis")
    st.caption("Future move behavior.")

    if dataframe.empty:
        st.info("No cases match the current filters.")
        return

    available_move_columns = [column for column in MOVE_COLUMNS if column in dataframe.columns]

    if "classification" in dataframe.columns and available_move_columns:
        movement = dataframe.copy()
        for column in available_move_columns:
            movement[column] = pd.to_numeric(movement[column], errors="coerce")

        average_moves = (
            movement.groupby("classification")[available_move_columns]
            .mean(numeric_only=True)
            .reset_index()
        )
        st.markdown("Average move by classification")
        st.dataframe(
            sanitize_dataframe_for_display(round_numeric_dataframe(average_moves)),
            use_container_width=True,
            hide_index=True,
        )
    else:
        missing_column_warning("classification / movement columns")

    if has_columns(dataframe, ["classification", "max_abs_move_4h"]):
        max_abs = dataframe.copy()
        max_abs["max_abs_move_4h"] = pd.to_numeric(
            max_abs["max_abs_move_4h"],
            errors="coerce",
        )
        average_abs = (
            max_abs.groupby("classification")["max_abs_move_4h"]
            .mean()
            .reset_index(name="average_max_abs_move_4h")
        )
        st.markdown("Average max_abs_move_4h by classification")
        st.dataframe(
            sanitize_dataframe_for_display(round_numeric_dataframe(average_abs)),
            use_container_width=True,
            hide_index=True,
        )

        strongest = max_abs.sort_values("max_abs_move_4h", ascending=False).head(10)
        st.markdown("Top 10 strongest max_abs_move_4h cases")
        st.dataframe(
            sanitize_dataframe_for_display(
                select_existing_columns(strongest, COMPACT_EPISODE_COLUMNS)
            ),
            use_container_width=True,
            hide_index=True,
        )

    reversal_failed = dataframe[
        dataframe.get("classification", pd.Series(dtype=str)).isin(
            ["REVERSAL_WARNING", "FAILED_CONTEXT"]
        )
    ].copy()

    if not reversal_failed.empty and "max_abs_move_4h" in reversal_failed.columns:
        reversal_failed["max_abs_move_4h"] = pd.to_numeric(
            reversal_failed["max_abs_move_4h"],
            errors="coerce",
        )
        reversal_failed = reversal_failed.sort_values(
            "max_abs_move_4h",
            ascending=False,
        ).head(10)
        st.markdown("Top 10 strongest reversal / failed context cases")
        st.dataframe(
            sanitize_dataframe_for_display(
                select_existing_columns(reversal_failed, COMPACT_EPISODE_COLUMNS)
            ),
            use_container_width=True,
            hide_index=True,
        )

    render_hypothesis_02_movement_tables(dataframe)


def render_hypothesis_02(dataframe):
    st.subheader("Hypothesis 02")
    st.caption(
        "Backward zone -> revisit -> expansion."
    )

    if dataframe.empty:
        st.info("No cases match the current filters.")
        return

    required = [
        "return_to_preparation",
        "expansion_after_return",
        "agreement_flag",
        "expansion_strength",
    ]

    missing = [column for column in required if column not in dataframe.columns]
    if missing:
        st.warning(f"Missing Hypothesis 02 column(s): {', '.join(missing)}")
        return

    return_count = count_true(dataframe, "return_to_preparation")
    preparation_candidate_count = count_true(dataframe, "preparation_candidate")
    success_count = count_true(dataframe, "expansion_after_return")
    failure_count = count_return_failures(dataframe)
    agreement_true = count_value(dataframe, "agreement_flag", "True")
    agreement_false = count_value(dataframe, "agreement_flag", "False")
    agreement_unknown = count_value(dataframe, "agreement_flag", "UNKNOWN")
    avg_return_delay = average_numeric(dataframe, "time_to_return_minutes")
    avg_expansion_after_return = average_numeric(dataframe, "max_move_after_return")
    avg_revisit_duration = average_numeric(dataframe, "revisit_duration_rows")
    avg_quiet_score = average_numeric(dataframe, "pre_quiet_score")
    avg_range_ratio = average_numeric(dataframe, "pre_range_ratio")

    return_ratio = ratio(success_count, return_count)
    agreement_ratio = ratio(agreement_true, agreement_true + agreement_false)

    metrics = [
        ("Preparation candidates", preparation_candidate_count),
        ("Preparation returns", return_count),
        ("Return success ratio", return_ratio),
        ("Agreement ratio", agreement_ratio),
        ("Return failures", failure_count),
        ("Agreement TRUE", agreement_true),
        ("Agreement FALSE", agreement_false),
        ("Agreement UNKNOWN", agreement_unknown),
        ("Avg return delay", avg_return_delay),
        ("Avg revisit duration", avg_revisit_duration),
        ("Avg expansion after return", avg_expansion_after_return),
        ("Avg quiet score", avg_quiet_score),
        ("Avg range ratio", avg_range_ratio),
    ]

    columns = st.columns(5)
    for index, (label, value) in enumerate(metrics):
        columns[index % 5].metric(label, value)

    st.markdown("Expansion strength breakdown")
    strength_counts = (
        dataframe["expansion_strength"]
        .fillna("UNKNOWN")
        .astype(str)
        .value_counts()
        .rename_axis("expansion_strength")
        .reset_index(name="count")
    )
    st.dataframe(
        sanitize_dataframe_for_display(strength_counts),
        use_container_width=True,
        hide_index=True,
    )

    if "preparation_strength" in dataframe.columns:
        st.markdown("Preparation strength breakdown")
        preparation_strength = (
            dataframe["preparation_strength"]
            .fillna("UNKNOWN")
            .astype(str)
            .value_counts()
            .rename_axis("preparation_strength")
            .reset_index(name="count")
        )
        st.dataframe(
            sanitize_dataframe_for_display(preparation_strength),
            use_container_width=True,
            hide_index=True,
        )

    if "zone_revisit_count" in dataframe.columns:
        revisit_stats = pd.DataFrame(
            [
                {
                    "metric": "total_revisits",
                    "value": pd.to_numeric(
                        dataframe["zone_revisit_count"],
                        errors="coerce",
                    ).fillna(0).sum(),
                },
                {
                    "metric": "max_revisits",
                    "value": pd.to_numeric(
                        dataframe["zone_revisit_count"],
                        errors="coerce",
                    ).fillna(0).max(),
                },
                {
                    "metric": "average_revisits",
                    "value": pd.to_numeric(
                        dataframe["zone_revisit_count"],
                        errors="coerce",
                    ).fillna(0).mean(),
                },
            ]
        )
        st.markdown("Zone revisit stats")
        st.dataframe(
            sanitize_dataframe_for_display(round_numeric_dataframe(revisit_stats)),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("Top return cases")
    returned = dataframe[dataframe["return_to_preparation"].apply(bool_value)].copy()
    st.dataframe(
        sanitize_dataframe_for_display(
            select_existing_columns(
                returned.head(10),
                [
                    "case_id",
                    "episode_id",
                    "return_timestamp",
                    "return_row",
                    "return_price",
                    "time_to_return_minutes",
                    "zone_revisit_count",
                    "expansion_after_return",
                    "max_move_after_return",
                    "direction_after_return",
                    "classification",
                ],
            )
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("Top failed return cases")
    failed_returns = returned[
        ~returned["expansion_after_return"].apply(bool_value)
    ].copy()
    st.dataframe(
        sanitize_dataframe_for_display(
            select_existing_columns(
                failed_returns.head(10),
                [
                    "case_id",
                    "episode_id",
                    "return_timestamp",
                    "time_to_return_minutes",
                    "max_move_after_return",
                    "direction_after_return",
                    "classification",
                    "classification_reason",
                ],
            )
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_hypothesis_02_movement_tables(dataframe):
    st.markdown("Hypothesis 02 Movement Tables")

    if dataframe.empty:
        st.info("No Hypothesis 02 movement cases match the current filters.")
        return

    table_specs = [
        (
            "Top return_to_preparation TRUE",
            dataframe[dataframe.get("return_to_preparation", pd.Series(dtype=bool)).apply(bool_value)]
            if "return_to_preparation" in dataframe.columns
            else dataframe.head(0),
            "time_to_return_minutes",
            True,
        ),
        (
            "Top expansion_after_return",
            dataframe.copy(),
            "max_move_after_return",
            False,
        ),
        (
            "Top agreement TRUE",
            dataframe[dataframe.get("agreement_flag", pd.Series(dtype=str)).astype(str) == "True"]
            if "agreement_flag" in dataframe.columns
            else dataframe.head(0),
            "max_abs_move_4h",
            False,
        ),
        (
            "Top disagreement cases",
            dataframe[dataframe.get("agreement_flag", pd.Series(dtype=str)).astype(str) == "False"]
            if "agreement_flag" in dataframe.columns
            else dataframe.head(0),
            "max_abs_move_4h",
            False,
        ),
        (
            "Top revisit count",
            dataframe.copy(),
            "zone_revisit_count",
            False,
        ),
    ]

    columns = [
        "case_id",
        "episode_id",
        "score_bucket",
        "classification",
        "episode_direction_proxy",
        "future_direction",
        "agreement_flag",
        "return_to_preparation",
        "time_to_return_minutes",
        "expansion_after_return",
        "zone_revisit_count",
        "max_move_after_return",
        "direction_after_return",
        "max_abs_move_4h",
    ]

    for title, table, sort_column, ascending in table_specs:
        st.markdown(title)
        if table.empty:
            st.info("No rows available.")
            continue

        sorted_table = sort_dataframe(table, sort_column, ascending)
        st.dataframe(
            sanitize_dataframe_for_display(
                select_existing_columns(sorted_table.head(10), columns)
            ),
            use_container_width=True,
            hide_index=True,
        )


def render_reversal_lab(dataframe):
    st.subheader("Reversal Lab")
    st.caption("Direct/late reversals.")

    if dataframe.empty:
        st.info("No cases match the current filters.")
        return

    required = [
        "reversal_type",
        "reversal_strength",
        "time_to_reversal_minutes",
        "direct_reversal_flag",
        "late_reversal_flag",
        "reversal_after_return",
        "failed_after_return",
    ]
    missing = [column for column in required if column not in dataframe.columns]
    if missing:
        st.warning(f"Missing reversal column(s): {', '.join(missing)}")
        return

    total_reversals = int((dataframe["reversal_type"].astype(str) != "NO_REVERSAL").sum())
    direct_count = count_true(dataframe, "direct_reversal_flag")
    late_count = count_true(dataframe, "late_reversal_flag")
    after_return_count = count_true(dataframe, "reversal_after_return")
    failed_after_return_count = count_true(dataframe, "failed_after_return")
    high_count = count_value(dataframe, "reversal_strength", "HIGH")
    extreme_count = count_value(dataframe, "reversal_strength", "EXTREME")
    avg_time = average_numeric(dataframe, "time_to_reversal_minutes")

    metrics = [
        ("Total reversals", total_reversals),
        ("Direct reversals", direct_count),
        ("Late reversals", late_count),
        ("Reversal after preparation return", after_return_count),
        ("Failed after return", failed_after_return_count),
        ("High reversal count", high_count),
        ("Extreme reversal count", extreme_count),
        ("Average time to reversal", avg_time),
    ]

    columns = st.columns(4)
    for index, (label, value) in enumerate(metrics):
        columns[index % 4].metric(label, value)

    st.markdown("Reversal type breakdown")
    type_counts = (
        dataframe["reversal_type"]
        .fillna("UNKNOWN")
        .astype(str)
        .value_counts()
        .rename_axis("reversal_type")
        .reset_index(name="count")
    )
    st.dataframe(
        sanitize_dataframe_for_display(type_counts),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("Reversal strength breakdown")
    strength_counts = (
        dataframe["reversal_strength"]
        .fillna("UNKNOWN")
        .astype(str)
        .value_counts()
        .rename_axis("reversal_strength")
        .reset_index(name="count")
    )
    st.dataframe(
        sanitize_dataframe_for_display(strength_counts),
        use_container_width=True,
        hide_index=True,
    )

    table_specs = [
        (
            "Top reversal cases",
            dataframe[dataframe["reversal_type"].astype(str) != "NO_REVERSAL"].copy(),
            "reversal_distance_4h",
            False,
        ),
        (
            "Direct reversal cases",
            dataframe[dataframe["direct_reversal_flag"].apply(bool_value)].copy(),
            "reversal_distance_15m",
            False,
        ),
        (
            "Late reversal cases",
            dataframe[dataframe["late_reversal_flag"].apply(bool_value)].copy(),
            "time_to_reversal_minutes",
            True,
        ),
        (
            "Reversal after preparation cases",
            dataframe[dataframe["reversal_after_return"].apply(bool_value)].copy(),
            "time_to_reversal_minutes",
            True,
        ),
        (
            "Failed return reversal cases",
            dataframe[dataframe["failed_after_return"].apply(bool_value)].copy(),
            "reversal_distance_4h",
            False,
        ),
    ]

    for title, table, sort_column, ascending in table_specs:
        st.markdown(title)
        if table.empty:
            st.info("No rows available.")
            continue

        sorted_table = sort_dataframe(table, sort_column, ascending)
        st.dataframe(
            sanitize_dataframe_for_display(
                select_existing_columns(sorted_table.head(10), REVERSAL_LAB_COLUMNS)
            ),
            use_container_width=True,
            hide_index=True,
        )


def render_expansion_lab(dataframe):
    st.subheader("Expansion Lab")
    st.caption("Expansion vs reversal split.")

    if dataframe.empty:
        st.info("No cases match the current filters.")
        return

    required = [
        "expansion_type",
        "expansion_strength",
        "expansion_to_reversal_ratio",
        "expansion_survived",
        "expansion_failed",
    ]
    missing = [column for column in required if column not in dataframe.columns]
    if missing:
        st.warning(f"Missing expansion split column(s): {', '.join(missing)}")
        return

    pure_count = count_value(dataframe, "expansion_type", "PURE_EXPANSION")
    then_reversal_count = count_value(
        dataframe,
        "expansion_type",
        "EXPANSION_THEN_REVERSAL",
    )
    failed_count = count_value(dataframe, "expansion_type", "FAILED_EXPANSION")
    direct_reversal_count = count_value(dataframe, "expansion_type", "DIRECT_REVERSAL")
    avg_strength = average_strength_score(dataframe, "expansion_strength")
    avg_ratio = average_numeric(dataframe, "expansion_to_reversal_ratio")

    metrics = [
        ("Pure expansions", pure_count),
        ("Expansion then reversal", then_reversal_count),
        ("Failed expansions", failed_count),
        ("Direct reversals", direct_reversal_count),
        ("Average expansion strength", avg_strength),
        ("Average expansion/reversal ratio", avg_ratio),
    ]

    columns = st.columns(3)
    for index, (label, value) in enumerate(metrics):
        columns[index % 3].metric(label, value)

    st.markdown("Expansion strength distribution")
    strength_counts = (
        dataframe["expansion_strength"]
        .fillna("UNKNOWN")
        .astype(str)
        .value_counts()
        .rename_axis("expansion_strength")
        .reset_index(name="count")
    )
    st.dataframe(
        sanitize_dataframe_for_display(strength_counts),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("Expansion type distribution")
    type_counts = (
        dataframe["expansion_type"]
        .fillna("UNKNOWN")
        .astype(str)
        .value_counts()
        .rename_axis("expansion_type")
        .reset_index(name="count")
    )
    st.dataframe(
        sanitize_dataframe_for_display(type_counts),
        use_container_width=True,
        hide_index=True,
    )

    table_specs = [
        (
            "Top expansion cases",
            dataframe[
                dataframe["expansion_type"].astype(str).isin(
                    ["PURE_EXPANSION", "EXPANSION_THEN_REVERSAL"]
                )
            ].copy(),
            "time_to_expansion_minutes",
            True,
        ),
        (
            "Top failed cases",
            dataframe[
                dataframe["expansion_type"].astype(str).isin(
                    ["FAILED_EXPANSION", "DIRECT_REVERSAL"]
                )
            ].copy(),
            "reversal_distance_4h",
            False,
        ),
        (
            "Pure expansion cases",
            dataframe[
                dataframe["expansion_type"].astype(str) == "PURE_EXPANSION"
            ].copy(),
            "max_abs_move_4h",
            False,
        ),
        (
            "Expansion then reversal cases",
            dataframe[
                dataframe["expansion_type"].astype(str)
                == "EXPANSION_THEN_REVERSAL"
            ].copy(),
            "expansion_to_reversal_ratio",
            False,
        ),
    ]

    for title, table, sort_column, ascending in table_specs:
        st.markdown(title)
        if table.empty:
            st.info("No rows available.")
            continue

        sorted_table = sort_dataframe(table, sort_column, ascending)
        st.dataframe(
            sanitize_dataframe_for_display(
                select_existing_columns(sorted_table.head(10), EXPANSION_LAB_COLUMNS)
            ),
            use_container_width=True,
            hide_index=True,
        )


def render_comparison_lab(dataframe):
    st.subheader("Comparison Lab")
    st.caption("PURE_EXPANSION vs DIRECT_REVERSAL.")

    if dataframe.empty:
        st.info("No comparison lab data found. Run tools/analyze_phase1b_comparison_lab.py first.")
        return

    normalized = normalize_comparison_dataframe(dataframe)
    pure_cases = normalized[
        normalized.get("comparison_group", pd.Series(dtype=str)).astype(str)
        == "PURE_EXPANSION"
    ].copy()
    direct_cases = normalized[
        normalized.get("comparison_group", pd.Series(dtype=str)).astype(str)
        == "DIRECT_REVERSAL"
    ].copy()
    summary_rows = normalized[
        normalized.get("comparison_group", pd.Series(dtype=str)).astype(str)
        == "SUMMARY"
    ].copy()

    metrics = [
        ("PURE_EXPANSION cases", len(pure_cases)),
        ("DIRECT_REVERSAL cases", len(direct_cases)),
        (
            "Avg expansion advantage",
            average_numeric(normalized, "expansion_advantage_score"),
        ),
        (
            "Avg reversal advantage",
            average_numeric(normalized, "reversal_advantage_score"),
        ),
    ]

    columns = st.columns(4)
    for index, (label, value) in enumerate(metrics):
        columns[index].metric(label, value)

    st.markdown("PURE_EXPANSION cases")
    st.dataframe(
        sanitize_dataframe_for_display(
            select_existing_columns(pure_cases, comparison_case_columns())
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("DIRECT_REVERSAL cases")
    st.dataframe(
        sanitize_dataframe_for_display(
            select_existing_columns(direct_cases, comparison_case_columns())
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("Comparison summary")
    st.dataframe(
        sanitize_dataframe_for_display(summary_rows),
        use_container_width=True,
        hide_index=True,
    )

    render_comparison_summary_section(
        title="Expansion advantage score",
        dataframe=sort_dataframe(normalized, "expansion_advantage_score", False),
        columns=comparison_score_columns(),
    )
    render_comparison_summary_section(
        title="Reversal advantage score",
        dataframe=sort_dataframe(normalized, "reversal_advantage_score", False),
        columns=comparison_score_columns(),
    )
    render_summary_type_section(
        "Top shared contexts",
        summary_rows,
        "TOP_SHARED_CONTEXT",
    )
    render_summary_type_section(
        "Contexts that mostly expand",
        summary_rows,
        "CONTEXT_MOSTLY_EXPANDS",
    )
    render_summary_type_section(
        "Contexts that mostly reverse",
        summary_rows,
        "CONTEXT_MOSTLY_REVERSES",
    )
    render_summary_type_section(
        "Strong preparation vs failed preparation",
        summary_rows,
        "PREPARATION_STRENGTH_COMPARISON",
    )


def render_comparison_summary_section(title, dataframe, columns):
    st.markdown(title)
    if dataframe.empty:
        st.info("No rows available.")
        return

    st.dataframe(
        sanitize_dataframe_for_display(select_existing_columns(dataframe.head(10), columns)),
        use_container_width=True,
        hide_index=True,
    )


def render_summary_type_section(title, dataframe, summary_type):
    st.markdown(title)
    if dataframe.empty or "summary_type" not in dataframe.columns:
        st.info("No summary rows available.")
        return

    rows = dataframe[dataframe["summary_type"].astype(str) == summary_type].copy()
    if rows.empty:
        st.info("No rows available.")
        return

    st.dataframe(
        sanitize_dataframe_for_display(rows),
        use_container_width=True,
        hide_index=True,
    )


def normalize_comparison_dataframe(dataframe):
    normalized = dataframe.copy()

    for column in [
        "peak_layer_count",
        "pre_quiet_score",
        "pre_range_ratio",
        "pre_delta_abs_mean",
        "pre_velocity_abs_mean",
        "max_abs_move_1h",
        "max_abs_move_4h",
        "expansion_advantage_score",
        "reversal_advantage_score",
        "difference_score",
        "pure_expansion_count",
        "direct_reversal_count",
        "context_total",
    ]:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    return normalized


def comparison_case_columns():
    return [
        "case_id",
        "expansion_type",
        "peak_layer_count",
        "peak_max_severity",
        "peak_primary_context",
        "episode_direction_proxy",
        "future_direction",
        "agreement_flag",
        "preparation_candidate",
        "preparation_strength",
        "return_to_preparation",
        "pre_quiet_score",
        "pre_range_ratio",
        "pre_delta_abs_mean",
        "pre_velocity_abs_mean",
        "expansion_strength",
        "reversal_strength",
        "max_abs_move_1h",
        "max_abs_move_4h",
        "expansion_advantage_score",
        "reversal_advantage_score",
        "difference_score",
    ]


def comparison_score_columns():
    return [
        "case_id",
        "comparison_group",
        "expansion_type",
        "peak_primary_context",
        "preparation_strength",
        "expansion_strength",
        "reversal_strength",
        "max_abs_move_4h",
        "expansion_advantage_score",
        "reversal_advantage_score",
        "difference_score",
    ]


def render_preparation_quality(dataframe):
    st.subheader("Preparation Quality")
    st.caption("Quality of backward preparation zones.")

    if dataframe.empty:
        st.info(
            "No preparation quality data found. Run "
            "tools/analyze_phase1b_preparation_quality.py first."
        )
        return

    normalized = normalize_preparation_quality_dataframe(dataframe)
    case_rows = normalized[
        normalized.get("row_type", pd.Series(dtype=str)).astype(str) == "CASE"
    ].copy()
    summary_rows = normalized[
        normalized.get("row_type", pd.Series(dtype=str)).astype(str) == "SUMMARY"
    ].copy()

    average_score = summary_value(summary_rows, "average_preparation_score")
    low_failure_rate = summary_value(summary_rows, "low_preparation_failure_rate")
    extreme_success_rate = summary_value(
        summary_rows,
        "extreme_preparation_success_rate",
    )

    metrics = [
        ("Average preparation score", average_score),
        ("Strong success cases", count_value(case_rows, "preparation_result", "STRONG_SUCCESS")),
        ("False preparation cases", count_value(case_rows, "preparation_result", "FALSE_PREPARATION")),
        ("Return failure cases", count_value(case_rows, "preparation_result", "RETURN_FAILURE")),
        ("Low preparation failure rate", low_failure_rate),
        ("Extreme preparation success rate", extreme_success_rate),
    ]

    columns = st.columns(3)
    for index, (label, value) in enumerate(metrics):
        columns[index % 3].metric(label, value)

    st.markdown("Preparation result counts")
    if "preparation_result" in case_rows.columns:
        result_counts = (
            case_rows["preparation_result"]
            .fillna("UNKNOWN")
            .astype(str)
            .value_counts()
            .rename_axis("preparation_result")
            .reset_index(name="count")
        )
        st.dataframe(
            sanitize_dataframe_for_display(result_counts),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("Missing column: preparation_result")

    st.markdown("Success by preparation strength")
    success_rows = summary_rows[
        summary_rows.get("summary_metric", pd.Series(dtype=str))
        .astype(str)
        .str.startswith("success_by_preparation_strength_")
    ].copy()
    st.dataframe(
        sanitize_dataframe_for_display(success_rows),
        use_container_width=True,
        hide_index=True,
    )

    render_preparation_quality_table(
        "Strong success cases",
        case_rows,
        "preparation_result",
        "STRONG_SUCCESS",
    )
    render_preparation_quality_table(
        "False preparation cases",
        case_rows,
        "preparation_result",
        "FALSE_PREPARATION",
    )
    render_preparation_quality_table(
        "Return failure cases",
        case_rows,
        "preparation_result",
        "RETURN_FAILURE",
    )


def render_preparation_quality_table(title, dataframe, column, value):
    st.markdown(title)

    if dataframe.empty or column not in dataframe.columns:
        st.info("No rows available.")
        return

    rows = dataframe[dataframe[column].astype(str) == value].copy()

    if rows.empty:
        st.info("No rows available.")
        return

    rows = sort_dataframe(rows, "preparation_quality_score", False)
    st.dataframe(
        sanitize_dataframe_for_display(
            select_existing_columns(rows, preparation_quality_columns())
        ),
        use_container_width=True,
        hide_index=True,
    )


def normalize_preparation_quality_dataframe(dataframe):
    normalized = dataframe.copy()

    for column in [
        "pre_quiet_score",
        "pre_range_ratio",
        "pre_delta_abs_mean",
        "pre_velocity_abs_mean",
        "revisit_duration_rows",
        "preparation_quality_score",
        "summary_value",
    ]:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    return normalized


def preparation_quality_columns():
    return [
        "case_id",
        "preparation_candidate",
        "preparation_strength",
        "pre_quiet_score",
        "pre_range_ratio",
        "pre_delta_abs_mean",
        "pre_velocity_abs_mean",
        "return_to_preparation",
        "revisit_duration_rows",
        "expansion_type",
        "expansion_strength",
        "reversal_strength",
        "expansion_survived",
        "expansion_failed",
        "preparation_quality_score",
        "preparation_result",
    ]


def summary_value(summary_rows, metric):
    if (
        summary_rows.empty
        or "summary_metric" not in summary_rows.columns
        or "summary_value" not in summary_rows.columns
    ):
        return "N/A"

    row = summary_rows[summary_rows["summary_metric"].astype(str) == metric]

    if row.empty:
        return "N/A"

    value = row.iloc[0].get("summary_value")

    if pd.isna(value):
        return "N/A"

    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return value


def render_journal(journal_text, journal_warning):
    st.subheader("Journal")
    st.caption("Human/research notes.")

    if journal_warning:
        st.warning(journal_warning)
        return

    if not journal_text.strip():
        st.info("Research journal is empty.")
        return

    st.markdown(journal_text)


def render_key_value_block(title, row, columns):
    st.markdown(f"**{title}**")
    values = []

    for column in columns:
        if column not in row.index:
            continue

        values.append(
            {
                "field": column,
                "value": safe_display_value(row.get(column)),
            }
        )

    if not values:
        st.info(f"No {title.lower()} fields available.")
        return

    st.dataframe(
        sanitize_dataframe_for_display(pd.DataFrame(values)),
        use_container_width=True,
        hide_index=True,
    )


def normalize_dataframe(dataframe):
    normalized = dataframe.copy()

    for column in [
        "peak_layer_count",
        "move_1m",
        "move_5m",
        "move_15m",
        "move_30m",
        "move_1h",
        "move_2h",
        "move_4h",
        "move_day_end",
        "max_up_move_4h",
        "max_down_move_4h",
        "max_abs_move_4h",
        "time_to_return_minutes",
        "zone_revisit_count",
        "max_move_after_return",
        "return_price",
        "return_row",
        "revisit_duration_rows",
        "revisit_expansion_delay_minutes",
        "pre_quiet_score",
        "pre_compression_ratio",
        "pre_range_value",
        "pre_range_ratio",
        "pre_delta_mean",
        "pre_delta_abs_mean",
        "pre_velocity_mean",
        "pre_velocity_abs_mean",
        "pre_volume_mean",
        "pre_zscore_abs_mean",
        "preparation_low_price",
        "preparation_high_price",
        "preparation_mid_price",
        "reversal_distance_1m",
        "reversal_distance_5m",
        "reversal_distance_15m",
        "reversal_distance_30m",
        "reversal_distance_1h",
        "reversal_distance_4h",
        "time_to_reversal_minutes",
        "peak_before_reversal",
        "reversal_ratio",
        "time_to_expansion_minutes",
        "expansion_to_reversal_ratio",
    ]:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    return normalized


def sanitize_dataframe_for_display(dataframe):
    sanitized = dataframe.copy()

    for column in sanitized.columns:
        if sanitized[column].dtype == "object":
            sanitized[column] = sanitized[column].apply(safe_display_value)

    return sanitized.fillna("")


def round_numeric_dataframe(dataframe):
    rounded = dataframe.copy()

    for column in rounded.columns:
        if pd.api.types.is_numeric_dtype(rounded[column]):
            rounded[column] = rounded[column].round(4)

    return rounded


def select_existing_columns(dataframe, columns):
    existing_columns = [column for column in columns if column in dataframe.columns]
    missing_columns = [column for column in columns if column not in dataframe.columns]

    if missing_columns:
        st.caption(f"Missing columns skipped: {', '.join(missing_columns)}")

    return dataframe[existing_columns].copy() if existing_columns else pd.DataFrame()


def options_from_column(dataframe, column):
    if column not in dataframe.columns:
        missing_column_warning(column)
        return []

    return sorted(
        [
            str(value)
            for value in dataframe[column].dropna().unique()
            if str(value).strip()
        ]
    )


def column_contains(dataframe, column, value):
    return column in dataframe.columns and value in set(dataframe[column].dropna())


def filter_equals(dataframe, column, selected_value):
    if selected_value == "ALL":
        return dataframe

    if column not in dataframe.columns:
        missing_column_warning(column)
        return dataframe.head(0)

    return dataframe[dataframe[column].astype(str) == str(selected_value)]


def has_columns(dataframe, columns):
    missing = [column for column in columns if column not in dataframe.columns]

    if missing:
        st.warning(f"Missing column(s): {', '.join(missing)}")
        return False

    return True


def show_file_warnings(warnings):
    for warning in [item for item in warnings if item]:
        st.warning(warning)


def missing_column_warning(column):
    st.sidebar.caption(f"Missing column: {column}")


def count_value(dataframe, column, value):
    if column not in dataframe.columns:
        return 0

    return int((dataframe[column].astype(str) == value).sum())


def count_true(dataframe, column):
    if column not in dataframe.columns:
        return 0

    return int(dataframe[column].apply(bool_value).sum())


def count_return_failures(dataframe):
    if (
        dataframe.empty
        or "return_to_preparation" not in dataframe.columns
        or "expansion_after_return" not in dataframe.columns
    ):
        return 0

    returned = dataframe[dataframe["return_to_preparation"].apply(bool_value)]

    if returned.empty:
        return 0

    return int((~returned["expansion_after_return"].apply(bool_value)).sum())


def average_numeric(dataframe, column):
    if dataframe.empty or column not in dataframe.columns:
        return "N/A"

    values = pd.to_numeric(dataframe[column], errors="coerce").dropna()

    if values.empty:
        return "N/A"

    return round(float(values.mean()), 4)


def average_strength_score(dataframe, column):
    if dataframe.empty or column not in dataframe.columns:
        return "N/A"

    rank = {
        "NONE": 0,
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "EXTREME": 4,
    }
    values = [rank.get(str(value), 0) for value in dataframe[column].fillna("NONE")]

    if not values:
        return "N/A"

    return round(sum(values) / len(values), 4)


def ratio(numerator, denominator):
    if denominator <= 0:
        return "N/A"

    return f"{round((numerator / denominator) * 100, 2)}%"


def sort_dataframe(dataframe, column, ascending):
    if dataframe.empty or column not in dataframe.columns:
        return dataframe

    sorted_dataframe = dataframe.copy()
    sorted_dataframe[column] = pd.to_numeric(
        sorted_dataframe[column],
        errors="coerce",
    )

    return sorted_dataframe.sort_values(
        column,
        ascending=ascending,
        na_position="last",
    )


def bool_value(value):
    if pd.isna(value):
        return False

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value != 0

    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def safe_metric_value(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def safe_display_value(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    if isinstance(value, (list, dict, set, tuple)):
        return " | ".join(str(item) for item in value)

    return value


def relative_path(path):
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()

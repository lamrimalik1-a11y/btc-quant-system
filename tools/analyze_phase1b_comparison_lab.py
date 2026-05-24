from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT_DIR / "research"

RESEARCH_LOG_FILE = RESEARCH_DIR / "phase1b_episode_research_log.csv"
COMPARISON_LOG_FILE = RESEARCH_DIR / "phase1b_comparison_log.csv"

COMPARISON_FIELDS = [
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
]

NUMERIC_FIELDS = [
    "peak_layer_count",
    "pre_quiet_score",
    "pre_range_ratio",
    "pre_delta_abs_mean",
    "pre_velocity_abs_mean",
    "max_abs_move_1h",
    "max_abs_move_4h",
]

GROUPS = ["PURE_EXPANSION", "DIRECT_REVERSAL"]


def main():
    research_log = load_research_log()
    comparison_rows = build_comparison_rows(research_log)
    summary_rows = build_summary_rows(comparison_rows)
    output = pd.concat([comparison_rows, summary_rows], ignore_index=True)

    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    output.to_csv(COMPARISON_LOG_FILE, index=False)

    print("Phase 1B comparison lab complete.")
    print(f"Source: {relative_path(RESEARCH_LOG_FILE)}")
    print(f"Output: {relative_path(COMPARISON_LOG_FILE)}")
    print(f"PURE_EXPANSION cases: {count_type(comparison_rows, 'PURE_EXPANSION')}")
    print(f"DIRECT_REVERSAL cases: {count_type(comparison_rows, 'DIRECT_REVERSAL')}")
    print("Research only. No live system changes.")


def load_research_log():
    if not RESEARCH_LOG_FILE.exists():
        raise SystemExit(f"Missing research log: {relative_path(RESEARCH_LOG_FILE)}")

    try:
        return pd.read_csv(RESEARCH_LOG_FILE)
    except pd.errors.EmptyDataError as error:
        raise SystemExit(f"Empty research log: {relative_path(RESEARCH_LOG_FILE)}") from error


def build_comparison_rows(research_log):
    if research_log.empty:
        return empty_comparison_frame()

    rows = research_log[
        research_log.get("expansion_type", pd.Series(dtype=str)).astype(str).isin(GROUPS)
    ].copy()

    if rows.empty:
        return empty_comparison_frame()

    for field in COMPARISON_FIELDS:
        if field not in rows.columns:
            rows[field] = ""

    output = rows[COMPARISON_FIELDS].copy()

    for field in NUMERIC_FIELDS:
        output[field] = pd.to_numeric(output[field], errors="coerce")

    add_difference_scores(output)
    return output


def add_difference_scores(output):
    group_means = output.groupby("expansion_type")[NUMERIC_FIELDS].mean(numeric_only=True)
    pure_means = group_means.loc["PURE_EXPANSION"] if "PURE_EXPANSION" in group_means.index else pd.Series(dtype=float)
    reversal_means = group_means.loc["DIRECT_REVERSAL"] if "DIRECT_REVERSAL" in group_means.index else pd.Series(dtype=float)

    output["comparison_group"] = output["expansion_type"]
    output["expansion_advantage_score"] = output.apply(
        lambda row: expansion_advantage_score(row, pure_means, reversal_means),
        axis=1,
    )
    output["reversal_advantage_score"] = output.apply(
        lambda row: reversal_advantage_score(row, pure_means, reversal_means),
        axis=1,
    )
    output["difference_score"] = (
        output["expansion_advantage_score"] - output["reversal_advantage_score"]
    ).round(8)


def expansion_advantage_score(row, pure_means, reversal_means):
    score = 0

    score += compare_to_group_gap(
        row.get("max_abs_move_4h"),
        pure_means.get("max_abs_move_4h"),
        reversal_means.get("max_abs_move_4h"),
    )
    score += compare_to_group_gap(
        row.get("pre_quiet_score"),
        pure_means.get("pre_quiet_score"),
        reversal_means.get("pre_quiet_score"),
    )
    score += inverse_compare_to_group_gap(
        row.get("pre_range_ratio"),
        pure_means.get("pre_range_ratio"),
        reversal_means.get("pre_range_ratio"),
    )
    score += strength_rank(row.get("expansion_strength"))
    score -= strength_rank(row.get("reversal_strength")) * 0.5

    return round_float(score)


def reversal_advantage_score(row, pure_means, reversal_means):
    score = 0

    score += strength_rank(row.get("reversal_strength"))
    score -= strength_rank(row.get("expansion_strength")) * 0.5
    score += compare_to_group_gap(
        row.get("pre_velocity_abs_mean"),
        reversal_means.get("pre_velocity_abs_mean"),
        pure_means.get("pre_velocity_abs_mean"),
    )
    score += compare_to_group_gap(
        row.get("pre_delta_abs_mean"),
        reversal_means.get("pre_delta_abs_mean"),
        pure_means.get("pre_delta_abs_mean"),
    )
    score += inverse_compare_to_group_gap(
        row.get("pre_quiet_score"),
        reversal_means.get("pre_quiet_score"),
        pure_means.get("pre_quiet_score"),
    )

    return round_float(score)


def compare_to_group_gap(value, favorable_mean, opposite_mean):
    value = to_float(value)
    favorable_mean = to_float(favorable_mean)
    opposite_mean = to_float(opposite_mean)

    if value is None or favorable_mean is None or opposite_mean is None:
        return 0

    gap = abs(favorable_mean - opposite_mean)
    if gap == 0:
        return 0

    return (value - opposite_mean) / gap


def inverse_compare_to_group_gap(value, favorable_mean, opposite_mean):
    score = compare_to_group_gap(value, favorable_mean, opposite_mean)
    return -score


def build_summary_rows(comparison_rows):
    summary = []
    summary.extend(group_average_rows(comparison_rows))
    summary.extend(metric_difference_rows(comparison_rows))
    summary.extend(context_summary_rows(comparison_rows))
    summary.extend(preparation_summary_rows(comparison_rows))
    return pd.DataFrame(summary)


def group_average_rows(comparison_rows):
    rows = []

    for group in GROUPS:
        group_rows = comparison_rows[
            comparison_rows.get("expansion_type", pd.Series(dtype=str)).astype(str) == group
        ]
        row = base_summary_row(f"{group}_AVERAGE_VALUES")
        row["expansion_type"] = group
        row["case_id"] = f"SUMMARY_{group}_AVERAGES"
        row["comparison_group"] = "SUMMARY"

        for field in NUMERIC_FIELDS:
            row[field] = round_float(pd.to_numeric(group_rows.get(field), errors="coerce").mean())

        row["expansion_advantage_score"] = round_float(
            pd.to_numeric(
                group_rows.get("expansion_advantage_score"),
                errors="coerce",
            ).mean()
        )
        row["reversal_advantage_score"] = round_float(
            pd.to_numeric(
                group_rows.get("reversal_advantage_score"),
                errors="coerce",
            ).mean()
        )
        row["difference_score"] = round_float(
            pd.to_numeric(group_rows.get("difference_score"), errors="coerce").mean()
        )
        rows.append(row)

    return rows


def metric_difference_rows(comparison_rows):
    pure = comparison_rows[comparison_rows["expansion_type"] == "PURE_EXPANSION"]
    reversal = comparison_rows[comparison_rows["expansion_type"] == "DIRECT_REVERSAL"]
    row = base_summary_row("DIFFERENCE_SCORES")
    row["case_id"] = "SUMMARY_DIFFERENCE_SCORES"
    row["comparison_group"] = "SUMMARY"

    for field in NUMERIC_FIELDS:
        pure_mean = pd.to_numeric(pure.get(field), errors="coerce").mean()
        reversal_mean = pd.to_numeric(reversal.get(field), errors="coerce").mean()
        row[field] = round_float(pure_mean - reversal_mean)

    row["expansion_advantage_score"] = round_float(
        pd.to_numeric(pure.get("expansion_advantage_score"), errors="coerce").mean()
    )
    row["reversal_advantage_score"] = round_float(
        pd.to_numeric(reversal.get("reversal_advantage_score"), errors="coerce").mean()
    )
    row["difference_score"] = round_float(
        (row["expansion_advantage_score"] or 0)
        - (row["reversal_advantage_score"] or 0)
    )
    return [row]


def context_summary_rows(comparison_rows):
    rows = []

    if comparison_rows.empty or "peak_primary_context" not in comparison_rows.columns:
        return rows

    context_counts = (
        comparison_rows.groupby(["peak_primary_context", "expansion_type"])
        .size()
        .reset_index(name="count")
    )
    pivot = context_counts.pivot_table(
        index="peak_primary_context",
        columns="expansion_type",
        values="count",
        fill_value=0,
        aggfunc="sum",
    ).reset_index()

    for _, context_row in pivot.iterrows():
        pure_count = int(context_row.get("PURE_EXPANSION", 0))
        reversal_count = int(context_row.get("DIRECT_REVERSAL", 0))
        total = pure_count + reversal_count
        summary_type = "TOP_SHARED_CONTEXT"

        if pure_count > reversal_count:
            summary_type = "CONTEXT_MOSTLY_EXPANDS"
        elif reversal_count > pure_count:
            summary_type = "CONTEXT_MOSTLY_REVERSES"

        row = base_summary_row(summary_type)
        row["case_id"] = f"SUMMARY_CONTEXT_{context_row.get('peak_primary_context')}"
        row["peak_primary_context"] = context_row.get("peak_primary_context")
        row["comparison_group"] = "SUMMARY"
        row["pure_expansion_count"] = pure_count
        row["direct_reversal_count"] = reversal_count
        row["context_total"] = total
        rows.append(row)

    return rows


def preparation_summary_rows(comparison_rows):
    rows = []

    if comparison_rows.empty or "preparation_strength" not in comparison_rows.columns:
        return rows

    for strength, group in comparison_rows.groupby("preparation_strength"):
        row = base_summary_row("PREPARATION_STRENGTH_COMPARISON")
        row["case_id"] = f"SUMMARY_PREPARATION_{strength}"
        row["preparation_strength"] = strength
        row["comparison_group"] = "SUMMARY"
        row["pure_expansion_count"] = count_type(group, "PURE_EXPANSION")
        row["direct_reversal_count"] = count_type(group, "DIRECT_REVERSAL")
        row["context_total"] = len(group)
        rows.append(row)

    return rows


def base_summary_row(summary_type):
    row = {field: "" for field in COMPARISON_FIELDS}
    row.update(
        {
            "comparison_group": "SUMMARY",
            "summary_type": summary_type,
            "expansion_advantage_score": "",
            "reversal_advantage_score": "",
            "difference_score": "",
            "pure_expansion_count": "",
            "direct_reversal_count": "",
            "context_total": "",
        }
    )
    return row


def empty_comparison_frame():
    columns = [
        *COMPARISON_FIELDS,
        "comparison_group",
        "summary_type",
        "expansion_advantage_score",
        "reversal_advantage_score",
        "difference_score",
        "pure_expansion_count",
        "direct_reversal_count",
        "context_total",
    ]
    return pd.DataFrame(columns=columns)


def count_type(dataframe, expansion_type):
    if dataframe.empty or "expansion_type" not in dataframe.columns:
        return 0

    return int((dataframe["expansion_type"].astype(str) == expansion_type).sum())


def strength_rank(value):
    return {
        "NONE": 0,
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "EXTREME": 4,
    }.get(str(value), 0)


def to_float(value):
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_float(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    try:
        return round(float(value), 8)
    except (TypeError, ValueError):
        return ""


def relative_path(path):
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()

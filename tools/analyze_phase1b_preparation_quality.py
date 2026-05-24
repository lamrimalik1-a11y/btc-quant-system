from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT_DIR / "research"

RESEARCH_LOG_FILE = RESEARCH_DIR / "phase1b_episode_research_log.csv"
PREPARATION_QUALITY_FILE = RESEARCH_DIR / "phase1b_preparation_quality.csv"

OUTPUT_FIELDS = [
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


def main():
    research_log = load_research_log()
    quality_rows = build_quality_rows(research_log)
    summary_rows = build_summary_rows(quality_rows)
    output = pd.concat([quality_rows, summary_rows], ignore_index=True)

    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    output.to_csv(PREPARATION_QUALITY_FILE, index=False)

    print("Phase 1B preparation quality analysis complete.")
    print(f"Source: {relative_path(RESEARCH_LOG_FILE)}")
    print(f"Output: {relative_path(PREPARATION_QUALITY_FILE)}")
    print(f"Preparation cases: {len(quality_rows)}")
    print(f"Average preparation score: {average_numeric(quality_rows, 'preparation_quality_score')}")
    print("Research only. No live system changes.")


def load_research_log():
    if not RESEARCH_LOG_FILE.exists():
        raise SystemExit(f"Missing research log: {relative_path(RESEARCH_LOG_FILE)}")

    try:
        return pd.read_csv(RESEARCH_LOG_FILE)
    except pd.errors.EmptyDataError as error:
        raise SystemExit(f"Empty research log: {relative_path(RESEARCH_LOG_FILE)}") from error


def build_quality_rows(research_log):
    if research_log.empty:
        return pd.DataFrame(columns=[*OUTPUT_FIELDS, "row_type", "summary_metric", "summary_value"])

    rows = research_log.copy()

    for field in OUTPUT_FIELDS:
        if field not in rows.columns:
            rows[field] = ""

    for field in [
        "pre_quiet_score",
        "pre_range_ratio",
        "pre_delta_abs_mean",
        "pre_velocity_abs_mean",
        "revisit_duration_rows",
    ]:
        rows[field] = pd.to_numeric(rows[field], errors="coerce")

    output_rows = []
    for _, row in rows.iterrows():
        quality_score = preparation_quality_score(row)
        result = preparation_result(row, quality_score)
        output = {field: row.get(field, "") for field in OUTPUT_FIELDS}
        output["preparation_quality_score"] = quality_score
        output["preparation_result"] = result
        output["row_type"] = "CASE"
        output["summary_metric"] = ""
        output["summary_value"] = ""
        output_rows.append(output)

    return pd.DataFrame(output_rows)


def preparation_quality_score(row):
    quiet_score = to_float(row.get("pre_quiet_score")) or 0
    range_ratio = to_float(row.get("pre_range_ratio"))
    delta_abs = to_float(row.get("pre_delta_abs_mean")) or 0
    velocity_abs = to_float(row.get("pre_velocity_abs_mean")) or 0
    strength_bonus = {
        "EXTREME": 15,
        "HIGH": 10,
        "MEDIUM": 6,
        "LOW": 2,
        "NONE": 0,
    }.get(str(row.get("preparation_strength")), 0)

    score = quiet_score + strength_bonus

    if range_ratio is not None:
        if range_ratio <= 0.35:
            score += 15
        elif range_ratio <= 0.50:
            score += 10
        elif range_ratio <= 0.65:
            score += 5
        elif range_ratio > 1:
            score -= 10

    if delta_abs > 5:
        score -= 8

    if velocity_abs > 1:
        score -= 8

    if truthy_value(row.get("expansion_survived")):
        score += 10

    if truthy_value(row.get("expansion_failed")):
        score -= 15

    return round(max(min(score, 100), 0), 8)


def preparation_result(row, quality_score):
    candidate = truthy_value(row.get("preparation_candidate"))
    returned = truthy_value(row.get("return_to_preparation"))
    survived = truthy_value(row.get("expansion_survived"))
    failed = truthy_value(row.get("expansion_failed"))
    strength = str(row.get("preparation_strength") or "")
    expansion_type = str(row.get("expansion_type") or "")
    reversal_strength = str(row.get("reversal_strength") or "")

    if not candidate:
        return "FALSE_PREPARATION"

    if not returned:
        return "NO_RETURN"

    if failed or expansion_type in {"FAILED_EXPANSION", "DIRECT_REVERSAL"}:
        return "RETURN_FAILURE"

    if reversal_strength in {"HIGH", "EXTREME"} and not survived:
        return "UNSTABLE_PREPARATION"

    if survived and strength in {"HIGH", "EXTREME"} and quality_score >= 70:
        return "STRONG_SUCCESS"

    if survived:
        return "WEAK_SUCCESS"

    return "UNSTABLE_PREPARATION"


def build_summary_rows(quality_rows):
    if quality_rows.empty:
        return pd.DataFrame(columns=quality_rows.columns)

    summaries = [
        summary_row(
            "average_preparation_score",
            average_numeric(quality_rows, "preparation_quality_score"),
        ),
        summary_row(
            "success_after_return",
            success_rate(
                quality_rows[quality_rows["return_to_preparation"].apply(truthy_value)]
            ),
        ),
        summary_row(
            "failure_after_return",
            failure_rate(
                quality_rows[quality_rows["return_to_preparation"].apply(truthy_value)]
            ),
        ),
        summary_row(
            "extreme_preparation_success_rate",
            success_rate(
                quality_rows[
                    quality_rows["preparation_strength"].astype(str) == "EXTREME"
                ]
            ),
        ),
        summary_row(
            "low_preparation_failure_rate",
            failure_rate(
                quality_rows[
                    quality_rows["preparation_strength"].astype(str) == "LOW"
                ]
            ),
        ),
    ]

    for strength, group in quality_rows.groupby("preparation_strength"):
        summaries.append(
            summary_row(
                f"success_by_preparation_strength_{strength}",
                success_rate(group),
            )
        )

    return pd.DataFrame(summaries)


def summary_row(metric, value):
    row = {field: "" for field in OUTPUT_FIELDS}
    row["row_type"] = "SUMMARY"
    row["summary_metric"] = metric
    row["summary_value"] = value
    return row


def success_rate(dataframe):
    if dataframe.empty:
        return ""

    success_count = int(
        dataframe["preparation_result"].astype(str).isin(
            ["STRONG_SUCCESS", "WEAK_SUCCESS"]
        ).sum()
    )
    return round(success_count / len(dataframe), 8)


def failure_rate(dataframe):
    if dataframe.empty:
        return ""

    failure_count = int(
        dataframe["preparation_result"].astype(str).isin(
            ["RETURN_FAILURE", "FALSE_PREPARATION", "UNSTABLE_PREPARATION"]
        ).sum()
    )
    return round(failure_count / len(dataframe), 8)


def average_numeric(dataframe, column):
    if dataframe.empty or column not in dataframe.columns:
        return ""

    values = pd.to_numeric(dataframe[column], errors="coerce").dropna()

    if values.empty:
        return ""

    return round(float(values.mean()), 8)


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


def relative_path(path):
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()

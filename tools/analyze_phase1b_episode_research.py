import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from context_memory import FieldLifecycleMemory, ZoneLifecycleMemory
from tools.performance_profile import PerfProfiler

OUTPUT_DIR = ROOT_DIR / "outputs"
RESEARCH_DIR = ROOT_DIR / "research"

EPISODE_FILE = OUTPUT_DIR / "historical_replay_dashboard_v2_episodes.csv"
ROWS_FILE = OUTPUT_DIR / "historical_observation_rows.csv"

RESEARCH_LOG_FILE = RESEARCH_DIR / "phase1b_episode_research_log.csv"
RESEARCH_SUMMARY_FILE = RESEARCH_DIR / "phase1b_research_summary.csv"
RESEARCH_JOURNAL_FILE = RESEARCH_DIR / "RESEARCH_JOURNAL.md"
PREPARATION_ZONES_FILE = RESEARCH_DIR / "phase1b_preparation_zones.csv"
ZONE_LIFECYCLE_EVENTS_FILE = RESEARCH_DIR / "zone_lifecycle_events.jsonl"
FIELD_LIFECYCLE_EVENTS_FILE = RESEARCH_DIR / "field_lifecycle_events.jsonl"

BACKWARD_WINDOW = 100
OPTIONAL_TEST_WINDOW = 200
RANGE_LOOKBACK = 20
ROLLING_BASELINE_LOOKBACK = 50
EXPANSION_MEDIUM_THRESHOLD = 100
EXPANSION_HIGH_THRESHOLD = 250
EXPANSION_EXTREME_THRESHOLD = 500
RETURN_EXPANSION_SUCCESS_THRESHOLD = EXPANSION_MEDIUM_THRESHOLD
REVERSAL_MEDIUM_THRESHOLD = 100
REVERSAL_HIGH_THRESHOLD = 250
REVERSAL_EXTREME_THRESHOLD = 500

HORIZONS = {
    "1m": timedelta(minutes=1),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "2h": timedelta(hours=2),
    "4h": timedelta(hours=4),
}

CLASSIFICATIONS = [
    "MOMENTUM_PRECURSOR",
    "ACCELERATION_ZONE",
    "PRE_EXPANSION",
    "CONTEXT_ONLY",
    "REVERSAL_WARNING",
    "ACCUMULATION",
    "ABSORPTION",
    "FAILED_CONTEXT",
    "RANGE_NOISE",
    "UNKNOWN",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Analyze Phase 1B Dashboard V2 episodes from existing CSV files. "
            "Research only. No downloads, no replay generation, no trading."
        )
    )
    parser.add_argument(
        "--mode",
        choices=["score4plus", "all"],
        default="score4plus",
        help="Analyze score >= 4 episodes by default, or all episodes.",
    )
    return parser.parse_args()


def main():
    profiler = PerfProfiler("phase1b_episode_research")
    args = parse_args()
    analysis_run_utc = utc_now_text()

    try:
        with profiler.step("csv_read_episodes"):
            episodes = load_csv(EPISODE_FILE)
        with profiler.step("csv_read_observation_rows"):
            rows = load_csv(ROWS_FILE)

        score4plus_episodes = filter_score4plus_episodes(episodes)
        selected_episodes = (
            episodes.copy() if args.mode == "all" else score4plus_episodes.copy()
        )

        with profiler.step("research_prepare_rows"):
            prepared_rows = prepare_rows(rows)
        with profiler.step("index_build_time"):
            row_index = ResearchRowIndex(prepared_rows)
        profiler.add_metric("indexed_episode_count", len(selected_episodes))
        profiler.add_metric(
            "indexed_case_count",
            int(selected_episodes["episode_id"].nunique())
            if "episode_id" in selected_episodes.columns
            else len(selected_episodes),
        )
        analyzed_rows = []

        with profiler.step("research_analysis_time_after_cache"):
            for _, episode in selected_episodes.iterrows():
                analyzed_rows.append(
                    analyze_episode(
                        episode=episode,
                        rows=prepared_rows,
                        row_index=row_index,
                        analysis_run_utc=analysis_run_utc,
                    )
                )

        with profiler.step("pandas_dataframe_build"):
            research_log = pd.DataFrame(analyzed_rows)
        with profiler.step("research_preparation_zones"):
            preparation_zones = build_preparation_zones_log(research_log)
        with profiler.step("research_lifecycle_memory"):
            zone_lifecycle_memory, field_lifecycle_memory = build_lifecycle_memories(
                research_log
            )
        output_log = research_log.copy()
        output_preparation_zones = preparation_zones.copy()

        RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
        with profiler.step("csv_write_research_log"):
            output_log.to_csv(RESEARCH_LOG_FILE, index=False)
        with profiler.step("csv_write_preparation_zones"):
            output_preparation_zones.to_csv(PREPARATION_ZONES_FILE, index=False)
        with profiler.step("jsonl_write_lifecycle_events"):
            write_lifecycle_events_jsonl(
                zone_lifecycle_memory.get_recent_zone_events(
                    limit=zone_lifecycle_memory.get_zone_stats().total_events
                ),
                ZONE_LIFECYCLE_EVENTS_FILE,
            )
            write_lifecycle_events_jsonl(
                field_lifecycle_memory.get_recent_field_events(
                    limit=field_lifecycle_memory.get_field_stats().total_events
                ),
                FIELD_LIFECYCLE_EVENTS_FILE,
            )

        with profiler.step("research_summary_build"):
            summary = build_summary(
                research_log=research_log,
                output_log=output_log,
                preparation_zones=output_preparation_zones,
                episodes_total_loaded=len(episodes),
                episodes_score4plus_count=len(score4plus_episodes),
                mode=args.mode,
                analysis_run_utc=analysis_run_utc,
            )
        with profiler.step("csv_write_research_summary"):
            pd.DataFrame([summary]).to_csv(RESEARCH_SUMMARY_FILE, index=False)

        with profiler.step("research_journal_append"):
            append_research_journal(
                summary=summary,
                research_log=output_log,
                mode=args.mode,
            )

        profiler.add_metric("episodes_loaded", len(episodes))
        profiler.add_metric("rows_loaded", len(rows))
        profiler.add_metric("episodes_analyzed", len(output_log))
        profiler.add_metric("score4plus_episodes", len(score4plus_episodes))
        profiler.add_metric("research_candidates", int(output_log["is_research_candidate"].sum()))

        print("Phase 1B episode research complete.")
        print("Files created:")
        print(f"- {relative_path(RESEARCH_LOG_FILE)}")
        print(f"- {relative_path(PREPARATION_ZONES_FILE)}")
        print(f"- {relative_path(RESEARCH_SUMMARY_FILE)}")
        print(f"- {relative_path(RESEARCH_JOURNAL_FILE)}")
        print(f"- {relative_path(ZONE_LIFECYCLE_EVENTS_FILE)}")
        print(f"- {relative_path(FIELD_LIFECYCLE_EVENTS_FILE)}")
        print(f"Episodes analyzed: {len(output_log)}")
        print(f"Score >= 4 episodes: {len(score4plus_episodes)}")
        print(f"Research candidates: {int(output_log['is_research_candidate'].sum())}")
        print("Classification counts:")
        for label, count in classification_counts(output_log).items():
            print(f"- {label}: {count}")
        print(f"Open results in: {relative_path(RESEARCH_DIR)}")
    finally:
        profiler.finish(
            csv_files=[
                EPISODE_FILE,
                ROWS_FILE,
                RESEARCH_LOG_FILE,
                PREPARATION_ZONES_FILE,
                RESEARCH_SUMMARY_FILE,
            ]
        )


def load_csv(path):
    if not path.exists():
        raise SystemExit(f"Required input file not found: {relative_path(path)}")

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError as error:
        raise SystemExit(f"Required input file is empty: {relative_path(path)}") from error


def prepare_rows(rows):
    prepared = rows.copy()
    prepared["market_datetime"] = prepared["market_timestamp"].apply(
        parse_datetime_value
    )
    prepared["close"] = pd.to_numeric(prepared["close"], errors="coerce")
    prepared["row_id"] = pd.to_numeric(prepared["row_id"], errors="coerce")
    for column in [
        "volume",
        "price_zscore",
        "entropy",
        "delta_zscore",
        "velocity",
        "rvi",
    ]:
        if column in prepared.columns:
            prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    prepared = prepared.dropna(subset=["market_datetime", "close"])
    prepared = prepared.sort_values("market_datetime").reset_index(drop=True)
    prepared = add_preparation_baselines(prepared)
    return prepared


class ResearchRowIndex:
    def __init__(self, rows):
        self.rows = rows
        self.columns = rows.columns
        self.datetimes = rows["market_datetime"].reset_index(drop=True)
        self.row_ids = (
            pd.to_numeric(rows["row_id"], errors="coerce").reset_index(drop=True)
            if "row_id" in rows.columns
            else pd.Series(dtype="float64")
        )
        self.day_positions = {}
        if not rows.empty:
            for day, positions in rows.groupby(rows["market_datetime"].dt.date).groups.items():
                self.day_positions[day] = list(positions)

    def at_or_after(self, target_dt):
        if target_dt is None or self.rows.empty:
            return None
        position = self.datetimes.searchsorted(target_dt, side="left")
        if position >= len(self.rows):
            return None
        return self.rows.iloc[int(position)]

    def same_day(self, day):
        positions = self.day_positions.get(day, [])
        if not positions:
            return self.rows.head(0).copy()
        return self.rows.iloc[positions].copy()

    def between(self, start_dt, end_dt, include_end=True):
        if start_dt is None or end_dt is None or self.rows.empty:
            return self.rows.head(0).copy()
        start_position = self.datetimes.searchsorted(start_dt, side="left")
        end_side = "right" if include_end else "left"
        end_position = self.datetimes.searchsorted(end_dt, side=end_side)
        return self.rows.iloc[int(start_position):int(end_position)].copy()

    def before_time(self, target_dt, start_dt=None):
        if target_dt is None or self.rows.empty:
            return self.rows.head(0).copy()
        if start_dt is None:
            start_position = 0
        else:
            start_position = self.datetimes.searchsorted(start_dt, side="left")
        end_position = self.datetimes.searchsorted(target_dt, side="left")
        return self.rows.iloc[int(start_position):int(end_position)].copy()

    def after_time(self, target_dt):
        if target_dt is None or self.rows.empty:
            return self.rows.head(0).copy()
        position = self.datetimes.searchsorted(target_dt, side="right")
        return self.rows.iloc[int(position):].copy()

    def before_row_id(self, row_id, tail=None):
        if row_id is None or self.rows.empty or self.row_ids.empty:
            return self.rows.head(0).copy()
        position = self.row_ids.searchsorted(float(row_id), side="left")
        frame = self.rows.iloc[:int(position)].copy()
        return frame.tail(tail).copy() if tail is not None else frame


def analyze_episode(episode, rows, analysis_run_utc, row_index=None):
    indexed_rows = row_index or rows
    start_dt = parse_datetime_value(episode.get("episode_start_timestamp_utc"))
    end_dt = parse_datetime_value(episode.get("episode_end_timestamp_utc"))
    end_price = to_float(episode.get("end_price"))

    if end_dt is None:
        end_dt = start_dt

    if end_price is None and end_dt is not None:
        end_price = nearest_close_at_or_after(indexed_rows, end_dt)

    future_prices = {}
    future_moves = {}

    for label, delta in HORIZONS.items():
        future_price = nearest_close_at_or_after(indexed_rows, end_dt + delta)
        future_prices[f"price_at_{label}"] = future_price
        future_moves[f"move_{label}"] = subtract(future_price, end_price)

    day_end_price = close_at_day_end(indexed_rows, end_dt)
    future_prices["price_at_day_end"] = day_end_price
    future_moves["move_day_end"] = subtract(day_end_price, end_price)

    extremes_1h = calculate_window_extremes(
        rows=indexed_rows,
        start_dt=end_dt,
        end_dt=end_dt + timedelta(hours=1),
        base_price=end_price,
        suffix="1h",
    )
    extremes_4h = calculate_window_extremes(
        rows=indexed_rows,
        start_dt=end_dt,
        end_dt=end_dt + timedelta(hours=4),
        base_price=end_price,
        suffix="4h",
    )
    pre_state = calculate_pre_episode_state(
        rows=indexed_rows,
        start_dt=start_dt,
        start_row_id=to_float(episode.get("start_row_id")),
        base_price=end_price,
    )
    preparation_zone = find_preparation_zone(
        rows=indexed_rows,
        start_row_id=to_float(episode.get("start_row_id")),
    )
    episode_direction = episode_direction_proxy(episode)
    future_direction = classify_future_direction(
        future_moves=future_moves,
        extremes_4h=extremes_4h,
    )
    return_context = detect_preparation_return(
        rows=indexed_rows,
        episode=episode,
        preparation_zone=preparation_zone,
    )
    reversal_context = analyze_reversal_context(
        rows=indexed_rows,
        end_dt=end_dt,
        end_price=end_price,
        episode_direction=episode_direction,
        future_moves=future_moves,
        extremes_4h=extremes_4h,
        return_context=return_context,
    )
    expansion_split = analyze_expansion_reversal_split(
        rows=indexed_rows,
        end_dt=end_dt,
        end_price=end_price,
        episode_direction=episode_direction,
        reversal_context=reversal_context,
        extremes_4h=extremes_4h,
    )

    candidate = is_research_candidate(episode)
    classification, reason = classify_episode(
        episode=episode,
        candidate=candidate,
        future_moves=future_moves,
        extremes_1h=extremes_1h,
        extremes_4h=extremes_4h,
        pre_state=pre_state,
        base_price=end_price,
    )

    episode_date = format_date(end_dt or start_dt)
    peak_layer_count = to_int(episode.get("peak_layer_count"), 0)

    row = {
        "case_id": f"CASE_{to_int(episode.get('episode_id'), 0):05d}",
        "analysis_run_utc": analysis_run_utc,
        "source_episode_file": relative_path(EPISODE_FILE),
        "source_rows_file": relative_path(ROWS_FILE),
        "episode_id": episode.get("episode_id"),
        "episode_start_time_utc": format_datetime(start_dt),
        "episode_end_time_utc": format_datetime(end_dt),
        "start_row_id": episode.get("start_row_id"),
        "end_row_id": episode.get("end_row_id"),
        "duration_seconds": episode.get("duration_seconds"),
        "episode_date": episode_date,
        "peak_state": episode.get("peak_state"),
        "peak_layer_count": peak_layer_count,
        "peak_max_severity": episode.get("peak_max_severity"),
        "peak_primary_context": episode.get("peak_primary_context"),
        "peak_conditions": episode.get("peak_conditions"),
        "peak_active_layers": episode.get("peak_active_layers"),
        "peak_observation_confidence": episode.get("peak_observation_confidence"),
        "start_price": episode.get("start_price"),
        "end_price": end_price,
        "peak_rvi": episode.get("peak_rvi"),
        "peak_velocity": episode.get("peak_velocity"),
        "peak_delta_zscore": episode.get("peak_delta_zscore"),
        **future_prices,
        **future_moves,
        **extremes_1h,
        **extremes_4h,
        **pre_state,
        **public_preparation_fields(preparation_zone),
        "episode_direction_proxy": episode_direction,
        "future_direction": future_direction,
        "agreement_flag": agreement_flag(episode_direction, future_direction),
        "expansion_strength": expansion_strength(
            extremes_4h.get("max_abs_move_4h")
        ),
        **return_context,
        **reversal_context,
        **expansion_split,
        "classification": classification,
        "classification_reason": reason,
        "manual_review_required": True,
        "manual_notes": "",
        "score_bucket": score_bucket(peak_layer_count),
        "layer_count_bucket": layer_count_bucket(peak_layer_count),
        "severity_bucket": value_or_unknown(episode.get("peak_max_severity")),
        "primary_context_bucket": value_or_unknown(
            episode.get("peak_primary_context")
        ),
        "date_bucket": episode_date,
        "is_research_candidate": candidate,
    }

    return normalize_output_row(row)


def add_preparation_baselines(rows):
    prepared = rows.copy()
    rolling_close = prepared["close"].rolling(
        RANGE_LOOKBACK,
        min_periods=5,
    )
    prepared["research_range_value"] = (
        rolling_close.max() - rolling_close.min()
    )
    prepared["research_rolling_range_mean"] = prepared[
        "research_range_value"
    ].rolling(
        ROLLING_BASELINE_LOOKBACK,
        min_periods=5,
    ).mean()

    if "volume" in prepared.columns:
        prepared["research_volume_mean"] = prepared["volume"].rolling(
            ROLLING_BASELINE_LOOKBACK,
            min_periods=5,
        ).mean()
    else:
        prepared["research_volume_mean"] = None

    return prepared


def find_preparation_zone(rows, start_row_id):
    defaults = {
        "preparation_zone_found": False,
        "preparation_candidate": False,
        "preparation_strength": "NONE",
        "pre_quiet_score": "",
        "pre_compression_ratio": "",
        "pre_range_value": "",
        "pre_range_ratio": "",
        "pre_delta_mean": "",
        "pre_delta_abs_mean": "",
        "pre_velocity_mean": "",
        "pre_velocity_abs_mean": "",
        "pre_zscore_abs_mean": "",
        "pre_market_bias": "UNKNOWN",
        "pre_setup_quality": "UNKNOWN",
        "pre_setup_reason": "Insufficient backward rows.",
        "preparation_start_row": "",
        "preparation_end_row": "",
        "preparation_duration_rows": 0,
        "pre_entropy": "",
        "pre_price_zscore_mean": "",
        "pre_range_mean": "",
        "pre_volume_mean": "",
        "pre_market_state": "UNKNOWN",
        "preparation_low_price": "",
        "preparation_high_price": "",
        "preparation_mid_price": "",
        "_preparation_zone_low": "",
        "_preparation_zone_high": "",
    }

    if start_row_id is None or "row_id" not in rows.columns:
        return defaults

    if hasattr(rows, "before_row_id"):
        historical_rows = rows.before_row_id(start_row_id)
    else:
        historical_rows = rows[rows["row_id"] < start_row_id].copy()
    previous_rows = historical_rows.tail(BACKWARD_WINDOW).copy()

    if previous_rows.empty:
        return defaults

    reference_rows = historical_rows.tail(300).copy()
    metrics = calculate_preparation_metrics(previous_rows, reference_rows)
    candidate = is_preparation_candidate_metrics(metrics)
    strength = preparation_strength_from_metrics(metrics)
    quality = preparation_setup_quality(candidate, strength, metrics)
    reason = preparation_setup_reason(candidate, strength, quality, metrics)
    close_low = closes_min(previous_rows)
    close_high = closes_max(previous_rows)
    close_mid = (
        (close_low + close_high) / 2
        if close_low is not None and close_high is not None
        else None
    )
    entropy_values = numeric_series(previous_rows, "entropy")
    price_zscore_values = numeric_series(previous_rows, "price_zscore")

    return {
        "preparation_zone_found": candidate,
        "preparation_candidate": candidate,
        "preparation_strength": strength,
        "pre_quiet_score": metrics.get("pre_quiet_score"),
        "pre_compression_ratio": metrics.get("pre_compression_ratio"),
        "pre_range_value": metrics.get("pre_range_value"),
        "pre_range_ratio": metrics.get("pre_range_ratio"),
        "pre_delta_mean": metrics.get("pre_delta_mean"),
        "pre_delta_abs_mean": metrics.get("pre_delta_abs_mean"),
        "pre_velocity_mean": metrics.get("pre_velocity_mean"),
        "pre_velocity_abs_mean": metrics.get("pre_velocity_abs_mean"),
        "pre_zscore_abs_mean": metrics.get("pre_zscore_abs_mean"),
        "pre_market_bias": metrics.get("pre_market_bias"),
        "pre_setup_quality": quality,
        "pre_setup_reason": reason,
        "preparation_start_row": to_int(previous_rows["row_id"].iloc[0])
        if candidate
        else "",
        "preparation_end_row": to_int(previous_rows["row_id"].iloc[-1])
        if candidate
        else "",
        "preparation_duration_rows": len(previous_rows) if candidate else 0,
        "pre_entropy": round_float(entropy_values.mean())
        if not entropy_values.empty
        else "",
        "pre_price_zscore_mean": round_float(price_zscore_values.mean())
        if not price_zscore_values.empty
        else "",
        "pre_range_mean": metrics.get("pre_range_value"),
        "pre_volume_mean": metrics.get("pre_volume_mean"),
        "pre_market_state": classify_preparation_market_state(previous_rows)
        if candidate
        else "UNKNOWN",
        "preparation_low_price": round_float(close_low) if candidate else "",
        "preparation_high_price": round_float(close_high) if candidate else "",
        "preparation_mid_price": round_float(close_mid) if candidate else "",
        "_preparation_zone_low": round_float(close_low) if candidate else "",
        "_preparation_zone_high": round_float(close_high) if candidate else "",
    }


def public_preparation_fields(preparation_zone):
    return {
        key: value
        for key, value in preparation_zone.items()
        if not str(key).startswith("_")
    }


def calculate_preparation_metrics(window_rows, reference_rows):
    closes = numeric_series(window_rows, "close")
    reference_closes = numeric_series(reference_rows, "close")
    volume_values = numeric_series(window_rows, "volume")
    reference_volume_values = numeric_series(reference_rows, "volume")
    delta_values = numeric_series(window_rows, "delta")
    velocity_values = numeric_series(window_rows, "velocity")
    reference_velocity_values = numeric_series(reference_rows, "velocity").abs()
    zscore_abs_mean = calculate_zscore_abs_mean(window_rows)

    pre_range_value = float(closes.max() - closes.min()) if not closes.empty else None
    reference_range = (
        float(reference_closes.max() - reference_closes.min())
        if not reference_closes.empty
        else None
    )

    if not reference_range or reference_range <= 0:
        reference_range = pre_range_value

    pre_range_ratio = (
        pre_range_value / reference_range
        if pre_range_value is not None and reference_range and reference_range > 0
        else None
    )
    pre_compression_ratio = pre_range_ratio
    pre_volume_mean = volume_values.mean() if not volume_values.empty else None
    reference_volume_mean = (
        reference_volume_values.mean() if not reference_volume_values.empty else None
    )
    pre_velocity_abs_mean = (
        velocity_values.abs().mean() if not velocity_values.empty else None
    )
    reference_velocity_abs_mean = (
        reference_velocity_values.mean()
        if not reference_velocity_values.empty
        else None
    )
    reference_velocity_abs_std = (
        reference_velocity_values.std() if len(reference_velocity_values) > 1 else 0
    )

    return {
        "pre_range_value": round_float(pre_range_value),
        "pre_range_ratio": round_float(pre_range_ratio),
        "pre_compression_ratio": round_float(pre_compression_ratio),
        "pre_delta_mean": round_float(delta_values.mean())
        if not delta_values.empty
        else "",
        "pre_delta_abs_mean": round_float(delta_values.abs().mean())
        if not delta_values.empty
        else "",
        "pre_velocity_mean": round_float(velocity_values.mean())
        if not velocity_values.empty
        else "",
        "pre_velocity_abs_mean": round_float(pre_velocity_abs_mean),
        "pre_volume_mean": round_float(pre_volume_mean),
        "pre_zscore_abs_mean": round_float(zscore_abs_mean),
        "pre_market_bias": classify_pre_market_bias(closes),
        "pre_quiet_score": round_float(
            calculate_pre_quiet_score(
                range_ratio=pre_range_ratio,
                zscore_abs_mean=zscore_abs_mean,
                velocity_abs_mean=pre_velocity_abs_mean,
                reference_velocity_abs_mean=reference_velocity_abs_mean,
                reference_velocity_abs_std=reference_velocity_abs_std,
                volume_mean=pre_volume_mean,
                reference_volume_mean=reference_volume_mean,
            )
        ),
        "_reference_velocity_abs_mean": round_float(reference_velocity_abs_mean),
        "_reference_velocity_abs_std": round_float(reference_velocity_abs_std),
        "_reference_volume_mean": round_float(reference_volume_mean),
    }


def calculate_zscore_abs_mean(rows):
    values = []

    for column in [
        "price_zscore",
        "volume_zscore",
        "delta_zscore",
        "velocity_zscore",
    ]:
        series = numeric_series(rows, column)
        if not series.empty:
            values.append(series.abs().mean())

    if not values:
        return None

    return float(pd.Series(values).mean())


def calculate_pre_quiet_score(
    range_ratio,
    zscore_abs_mean,
    velocity_abs_mean,
    reference_velocity_abs_mean,
    reference_velocity_abs_std,
    volume_mean,
    reference_volume_mean,
):
    score = 0
    checks = 0

    if range_ratio is not None:
        checks += 1
        if range_ratio <= 0.45:
            score += 35
        elif range_ratio <= 0.65:
            score += 28
        elif range_ratio <= 0.85:
            score += 15

    if zscore_abs_mean is not None:
        checks += 1
        if zscore_abs_mean <= 0.90:
            score += 25
        elif zscore_abs_mean <= 1.50:
            score += 18
        elif zscore_abs_mean <= 2.00:
            score += 8

    if (
        velocity_abs_mean is not None
        and reference_velocity_abs_mean is not None
        and reference_velocity_abs_mean > 0
    ):
        checks += 1
        velocity_limit = reference_velocity_abs_mean + 2 * (
            reference_velocity_abs_std or 0
        )
        if velocity_abs_mean <= reference_velocity_abs_mean:
            score += 20
        elif velocity_abs_mean <= velocity_limit:
            score += 12

    if (
        volume_mean is not None
        and reference_volume_mean is not None
        and reference_volume_mean > 0
    ):
        checks += 1
        volume_ratio = volume_mean / reference_volume_mean
        if 0.70 <= volume_ratio <= 1.30:
            score += 20
        elif 0.50 <= volume_ratio <= 1.50:
            score += 12

    if checks == 0:
        return None

    return min(score, 100)


def is_preparation_candidate_metrics(metrics):
    range_ratio = to_float(metrics.get("pre_range_ratio"))
    zscore_abs_mean = to_float(metrics.get("pre_zscore_abs_mean"))
    velocity_abs_mean = to_float(metrics.get("pre_velocity_abs_mean"))
    reference_velocity_abs_mean = to_float(metrics.get("_reference_velocity_abs_mean"))
    reference_velocity_abs_std = to_float(metrics.get("_reference_velocity_abs_std")) or 0
    volume_mean = to_float(metrics.get("pre_volume_mean"))
    reference_volume_mean = to_float(metrics.get("_reference_volume_mean"))

    if range_ratio is None or range_ratio > 0.65:
        return False

    if zscore_abs_mean is not None and zscore_abs_mean > 1.50:
        return False

    if (
        velocity_abs_mean is not None
        and reference_velocity_abs_mean is not None
        and reference_velocity_abs_mean > 0
    ):
        velocity_limit = reference_velocity_abs_mean + 2 * reference_velocity_abs_std
        if velocity_abs_mean > max(velocity_limit, reference_velocity_abs_mean * 1.75):
            return False

    if (
        volume_mean is not None
        and reference_volume_mean is not None
        and reference_volume_mean > 0
    ):
        volume_ratio = volume_mean / reference_volume_mean
        if volume_ratio < 0.50 or volume_ratio > 1.50:
            return False

    return True


def preparation_strength_from_metrics(metrics):
    quiet_score = to_float(metrics.get("pre_quiet_score"))
    range_ratio = to_float(metrics.get("pre_range_ratio"))

    if quiet_score is None or range_ratio is None:
        return "NONE"

    if quiet_score >= 85 and range_ratio <= 0.35:
        return "EXTREME"

    if quiet_score >= 70 and range_ratio <= 0.50:
        return "HIGH"

    if quiet_score >= 55 and range_ratio <= 0.65:
        return "MEDIUM"

    if quiet_score >= 35:
        return "LOW"

    return "NONE"


def preparation_setup_quality(candidate, strength, metrics):
    if not candidate:
        return "WEAK"

    if strength in {"HIGH", "EXTREME"}:
        return "GOOD"

    if strength == "MEDIUM":
        return "MIXED"

    if strength == "LOW":
        return "WEAK"

    if metrics.get("pre_quiet_score") == "":
        return "UNKNOWN"

    return "WEAK"


def preparation_setup_reason(candidate, strength, quality, metrics):
    range_ratio = metrics.get("pre_range_ratio")
    quiet_score = metrics.get("pre_quiet_score")
    zscore_abs = metrics.get("pre_zscore_abs_mean")
    velocity_abs = metrics.get("pre_velocity_abs_mean")

    if not candidate:
        return (
            "No preparation candidate: compression, zscore, velocity, or volume "
            "conditions were not aligned."
        )

    return (
        f"{quality} {strength} preparation: "
        f"range_ratio={range_ratio}, quiet_score={quiet_score}, "
        f"zscore_abs_mean={zscore_abs}, velocity_abs_mean={velocity_abs}."
    )


def classify_pre_market_bias(closes):
    if closes.empty:
        return "UNKNOWN"

    start = float(closes.iloc[0])
    end = float(closes.iloc[-1])
    close_range = float(closes.max() - closes.min())
    threshold = max(close_range * 0.25, end * 0.0002, 10)
    move = end - start

    if move > threshold:
        return "UP"

    if move < -threshold:
        return "DOWN"

    return "RANGE"


def episode_direction_proxy(episode):
    text = " ".join(
        [
            str(episode.get("peak_primary_context") or ""),
            str(episode.get("peak_conditions") or ""),
            str(episode.get("peak_active_layers") or ""),
            str(episode.get("peak_state") or ""),
        ]
    ).upper()

    if any(
        marker in text
        for marker in [
            "BUY_ACCELERATION",
            "BUY_PRESSURE",
            "AGGRESSIVE_BUYERS",
        ]
    ):
        return "UP"

    if any(
        marker in text
        for marker in [
            "SELL_PRESSURE",
            "SELL_ACCELERATION",
            "AGGRESSIVE_SELLERS",
            "EXHAUSTION",
            "REVERSAL",
        ]
    ):
        return "DOWN"

    if "DELTA_ZSCORE_EXTREME" in text:
        delta_zscore = to_float(episode.get("peak_delta_zscore"))
        if delta_zscore is not None:
            if delta_zscore > 0:
                return "UP"
            if delta_zscore < 0:
                return "DOWN"

    return "UNKNOWN"


def classify_future_direction(future_moves, extremes_4h):
    move_1h = to_float(future_moves.get("move_1h"))
    move_2h = to_float(future_moves.get("move_2h"))
    move_4h = to_float(future_moves.get("move_4h"))
    max_up = to_float(extremes_4h.get("max_up_move_4h")) or 0
    max_down = to_float(extremes_4h.get("max_down_move_4h")) or 0
    max_abs = to_float(extremes_4h.get("max_abs_move_4h")) or 0

    available_moves = [
        value for value in [move_1h, move_2h, move_4h] if value is not None
    ]

    if not available_moves and max_abs == 0:
        return "UNKNOWN"

    strongest_directional_move = max(
        [max_up, abs(max_down), *[abs(value) for value in available_moves]],
        default=0,
    )

    if strongest_directional_move < EXPANSION_MEDIUM_THRESHOLD:
        return "RANGE"

    if abs(max_up) > abs(max_down):
        return "UP"

    if abs(max_down) > abs(max_up):
        return "DOWN"

    strongest_late_move = available_moves[-1] if available_moves else 0
    if strongest_late_move > 0:
        return "UP"
    if strongest_late_move < 0:
        return "DOWN"

    return "RANGE"


def agreement_flag(episode_direction, future_direction):
    if episode_direction == "UNKNOWN" or future_direction in {"UNKNOWN", "RANGE"}:
        return "UNKNOWN"

    return episode_direction == future_direction


def expansion_strength(max_abs_move_4h):
    value = to_float(max_abs_move_4h)

    if value is None:
        return "UNKNOWN"

    if value >= EXPANSION_EXTREME_THRESHOLD:
        return "EXTREME"

    if value >= EXPANSION_HIGH_THRESHOLD:
        return "HIGH"

    if value >= EXPANSION_MEDIUM_THRESHOLD:
        return "MEDIUM"

    return "LOW"


def detect_preparation_return(rows, episode, preparation_zone):
    defaults = {
        "return_to_preparation": False,
        "time_to_return_minutes": "",
        "expansion_after_return": False,
        "zone_revisit_count": 0,
        "max_move_after_return": "",
        "direction_after_return": "UNKNOWN",
        "return_price": "",
        "return_row": "",
        "return_timestamp": "",
        "revisit_duration_rows": 0,
        "revisit_expansion_delay_minutes": "",
    }

    if not truthy_value(preparation_zone.get("preparation_zone_found")):
        return defaults

    zone_low = to_float(preparation_zone.get("_preparation_zone_low"))
    zone_high = to_float(preparation_zone.get("_preparation_zone_high"))
    episode_end_dt = parse_datetime_value(episode.get("episode_end_timestamp_utc"))

    if zone_low is None or zone_high is None or episode_end_dt is None:
        return defaults

    if zone_low > zone_high:
        zone_low, zone_high = zone_high, zone_low

    if hasattr(rows, "after_time"):
        future_rows = rows.after_time(episode_end_dt)
    else:
        future_rows = rows[rows["market_datetime"] > episode_end_dt].copy()

    if future_rows.empty:
        return defaults

    in_zone = future_rows[
        (future_rows["close"] >= zone_low) & (future_rows["close"] <= zone_high)
    ].copy()

    if in_zone.empty:
        return defaults

    revisit_groups = contiguous_row_groups(in_zone)
    first_revisit = revisit_groups[0]
    return_row = first_revisit.iloc[0]
    return_dt = return_row.get("market_datetime")
    return_price = to_float(return_row.get("close"))

    if return_dt is None or return_price is None:
        return defaults

    expansion = calculate_after_return_expansion(
        rows=rows,
        return_dt=return_dt,
        return_price=return_price,
    )

    return {
        "return_to_preparation": True,
        "time_to_return_minutes": round_float(
            (return_dt - episode_end_dt).total_seconds() / 60
        ),
        "expansion_after_return": (
            (to_float(expansion.get("max_move_after_return")) or 0)
            >= RETURN_EXPANSION_SUCCESS_THRESHOLD
        ),
        "zone_revisit_count": len(revisit_groups),
        "max_move_after_return": expansion.get("max_move_after_return"),
        "direction_after_return": expansion.get("direction_after_return"),
        "return_price": round_float(return_price),
        "return_row": to_int(return_row.get("row_id")),
        "return_timestamp": format_datetime(return_dt),
        "revisit_duration_rows": len(first_revisit),
        "revisit_expansion_delay_minutes": expansion.get(
            "revisit_expansion_delay_minutes"
        ),
    }


def calculate_after_return_expansion(rows, return_dt, return_price):
    window_end = return_dt + timedelta(hours=4)
    if hasattr(rows, "between"):
        window = rows.between(return_dt, window_end)
    else:
        window = rows[
            (rows["market_datetime"] >= return_dt)
            & (rows["market_datetime"] <= window_end)
        ].copy()

    if window.empty or return_price is None:
        return {
            "max_move_after_return": "",
            "direction_after_return": "UNKNOWN",
            "revisit_expansion_delay_minutes": "",
        }

    moves = window["close"] - return_price
    abs_index = moves.abs().idxmax()
    strongest_move = float(moves.loc[abs_index])
    strongest_abs = abs(strongest_move)
    strongest_dt = window.loc[abs_index, "market_datetime"]

    if strongest_abs < EXPANSION_MEDIUM_THRESHOLD:
        direction = "RANGE"
    elif strongest_move > 0:
        direction = "UP"
    elif strongest_move < 0:
        direction = "DOWN"
    else:
        direction = "RANGE"

    return {
        "max_move_after_return": round_float(strongest_abs),
        "direction_after_return": direction,
        "revisit_expansion_delay_minutes": round_float(
            (strongest_dt - return_dt).total_seconds() / 60
        ),
    }


def analyze_reversal_context(
    rows,
    end_dt,
    end_price,
    episode_direction,
    future_moves,
    extremes_4h,
    return_context,
):
    defaults = {
        "reversal_distance_1m": "",
        "reversal_distance_5m": "",
        "reversal_distance_15m": "",
        "reversal_distance_30m": "",
        "reversal_distance_1h": "",
        "reversal_distance_4h": "",
        "reversal_strength": "NONE",
        "time_to_reversal_minutes": "",
        "peak_before_reversal": "",
        "reversal_ratio": "",
        "reversal_after_return": False,
        "failed_after_return": False,
        "direct_reversal_flag": False,
        "late_reversal_flag": False,
        "reversal_type": "NO_REVERSAL",
    }

    if end_dt is None or end_price is None:
        return defaults

    distances = reversal_distances_by_horizon(
        episode_direction=episode_direction,
        future_moves=future_moves,
        extremes_4h=extremes_4h,
    )
    reversal_strength_value = reversal_strength(distances["reversal_distance_4h"])
    reversal_event = find_reversal_event(
        rows=rows,
        end_dt=end_dt,
        end_price=end_price,
        episode_direction=episode_direction,
    )
    reversal_after_return = is_reversal_after_return(
        reversal_dt=reversal_event.get("reversal_dt"),
        return_context=return_context,
    )
    failed_after_return = is_failed_after_return(
        episode_direction=episode_direction,
        return_context=return_context,
    )
    direct_reversal = (
        reversal_event.get("time_to_reversal_minutes") is not None
        and reversal_event["time_to_reversal_minutes"] <= 15
    )
    late_reversal = (
        reversal_event.get("time_to_reversal_minutes") is not None
        and reversal_event["time_to_reversal_minutes"] > 15
    )

    return {
        **distances,
        "reversal_strength": reversal_strength_value,
        "time_to_reversal_minutes": round_float(
            reversal_event.get("time_to_reversal_minutes")
        ),
        "peak_before_reversal": reversal_event.get("peak_before_reversal"),
        "reversal_ratio": reversal_event.get("reversal_ratio"),
        "reversal_after_return": reversal_after_return,
        "failed_after_return": failed_after_return,
        "direct_reversal_flag": direct_reversal,
        "late_reversal_flag": late_reversal,
        "reversal_type": classify_reversal_type(
            episode_direction=episode_direction,
            reversal_strength_value=reversal_strength_value,
            direct_reversal=direct_reversal,
            late_reversal=late_reversal,
            reversal_after_return=reversal_after_return,
            failed_after_return=failed_after_return,
        ),
    }


def reversal_distances_by_horizon(episode_direction, future_moves, extremes_4h):
    distances = {}

    for label in ["1m", "5m", "15m", "30m", "1h"]:
        move = to_float(future_moves.get(f"move_{label}"))
        distances[f"reversal_distance_{label}"] = round_float(
            adverse_distance(episode_direction, move)
        )

    if episode_direction == "UP":
        distance_4h = abs(min(to_float(extremes_4h.get("max_down_move_4h")) or 0, 0))
    elif episode_direction == "DOWN":
        distance_4h = max(to_float(extremes_4h.get("max_up_move_4h")) or 0, 0)
    else:
        distance_4h = to_float(extremes_4h.get("max_abs_move_4h")) or 0

    distances["reversal_distance_4h"] = round_float(distance_4h)
    return distances


def adverse_distance(episode_direction, move):
    if move is None:
        return None

    if episode_direction == "UP":
        return abs(move) if move < 0 else 0

    if episode_direction == "DOWN":
        return move if move > 0 else 0

    return abs(move)


def reversal_strength(distance):
    value = to_float(distance)

    if value is None or value <= 0:
        return "NONE"

    if value >= REVERSAL_EXTREME_THRESHOLD:
        return "EXTREME"

    if value >= REVERSAL_HIGH_THRESHOLD:
        return "HIGH"

    if value >= REVERSAL_MEDIUM_THRESHOLD:
        return "MEDIUM"

    return "LOW"


def find_reversal_event(rows, end_dt, end_price, episode_direction):
    defaults = {
        "time_to_reversal_minutes": None,
        "peak_before_reversal": "",
        "reversal_ratio": "",
        "reversal_dt": None,
    }

    if end_dt is None or end_price is None:
        return defaults

    if hasattr(rows, "between"):
        window = rows.between(end_dt, end_dt + timedelta(hours=4))
    else:
        window = rows[
            (rows["market_datetime"] >= end_dt)
            & (rows["market_datetime"] <= end_dt + timedelta(hours=4))
        ].copy()

    if window.empty:
        return defaults

    moves = window["close"] - end_price
    adverse = moves.apply(lambda move: adverse_distance(episode_direction, move))
    favorable = moves.apply(lambda move: favorable_distance(episode_direction, move))
    threshold = max(end_price * 0.0005, 25)
    reversal_rows = window[adverse >= threshold]

    if reversal_rows.empty:
        return defaults

    reversal_index = reversal_rows.index[0]
    reversal_dt = window.loc[reversal_index, "market_datetime"]
    before_reversal = favorable.loc[favorable.index <= reversal_index]
    peak_before = float(before_reversal.max()) if not before_reversal.empty else 0
    reversal_distance = float(adverse.loc[reversal_index])
    ratio_base = peak_before if peak_before > 0 else 1

    return {
        "time_to_reversal_minutes": (
            reversal_dt - end_dt
        ).total_seconds()
        / 60,
        "peak_before_reversal": round_float(peak_before),
        "reversal_ratio": round_float(reversal_distance / ratio_base),
        "reversal_dt": reversal_dt,
    }


def favorable_distance(episode_direction, move):
    if move is None:
        return 0

    if episode_direction == "UP":
        return move if move > 0 else 0

    if episode_direction == "DOWN":
        return abs(move) if move < 0 else 0

    return 0


def is_reversal_after_return(reversal_dt, return_context):
    if reversal_dt is None or not truthy_value(return_context.get("return_to_preparation")):
        return False

    return_dt = parse_datetime_value(return_context.get("return_timestamp"))

    if return_dt is None:
        return False

    return reversal_dt >= return_dt


def is_failed_after_return(episode_direction, return_context):
    if not truthy_value(return_context.get("return_to_preparation")):
        return False

    if not truthy_value(return_context.get("expansion_after_return")):
        return True

    direction_after_return = str(return_context.get("direction_after_return") or "")

    if episode_direction in {"UP", "DOWN"} and direction_after_return in {"UP", "DOWN"}:
        return direction_after_return != episode_direction

    return False


def classify_reversal_type(
    episode_direction,
    reversal_strength_value,
    direct_reversal,
    late_reversal,
    reversal_after_return,
    failed_after_return,
):
    if reversal_strength_value == "NONE":
        return "NO_REVERSAL"

    if episode_direction == "UNKNOWN":
        return "UNKNOWN_DIRECTION_REVERSAL"

    if failed_after_return:
        return "FAILED_RETURN_REVERSAL"

    if reversal_after_return:
        return "REVERSAL_AFTER_PREPARATION_RETURN"

    if direct_reversal:
        return "DIRECT_REVERSAL"

    if late_reversal:
        return "LATE_REVERSAL"

    return "NO_REVERSAL"


def analyze_expansion_reversal_split(
    rows,
    end_dt,
    end_price,
    episode_direction,
    reversal_context,
    extremes_4h,
):
    defaults = {
        "expansion_before_reversal": False,
        "time_to_expansion_minutes": "",
        "expansion_strength": "NONE",
        "expansion_to_reversal_ratio": "",
        "expansion_survived": False,
        "expansion_failed": False,
        "expansion_type": "NO_EXPANSION",
    }

    if end_dt is None or end_price is None:
        return defaults

    expansion_event = find_expansion_event(
        rows=rows,
        end_dt=end_dt,
        end_price=end_price,
        episode_direction=episode_direction,
    )
    expansion_distance = expansion_event.get("expansion_distance") or 0
    expansion_strength_value = expansion_strength(expansion_distance)
    reversal_distance = to_float(reversal_context.get("reversal_distance_4h")) or 0
    reversal_time = to_float(reversal_context.get("time_to_reversal_minutes"))
    expansion_time = expansion_event.get("time_to_expansion_minutes")
    expansion_before_reversal = (
        expansion_time is not None
        and reversal_time is not None
        and expansion_time < reversal_time
    )

    if reversal_distance > 0:
        ratio = round_float(expansion_distance / reversal_distance)
    elif expansion_distance > 0:
        ratio = ""
    else:
        ratio = ""

    expansion_survived = (
        expansion_distance >= EXPANSION_MEDIUM_THRESHOLD
        and (
            reversal_distance < REVERSAL_MEDIUM_THRESHOLD
            or expansion_distance >= reversal_distance * 1.25
        )
    )
    expansion_failed = (
        reversal_distance >= REVERSAL_MEDIUM_THRESHOLD
        and (
            expansion_distance < EXPANSION_MEDIUM_THRESHOLD
            or reversal_distance > expansion_distance
        )
    )

    return {
        "expansion_before_reversal": expansion_before_reversal,
        "time_to_expansion_minutes": round_float(expansion_time),
        "expansion_strength": expansion_strength_value,
        "expansion_to_reversal_ratio": ratio,
        "expansion_survived": expansion_survived,
        "expansion_failed": expansion_failed,
        "expansion_type": classify_expansion_type(
            expansion_distance=expansion_distance,
            reversal_distance=reversal_distance,
            expansion_time=expansion_time,
            reversal_time=reversal_time,
            expansion_before_reversal=expansion_before_reversal,
            expansion_survived=expansion_survived,
            expansion_failed=expansion_failed,
        ),
    }


def find_expansion_event(rows, end_dt, end_price, episode_direction):
    defaults = {
        "time_to_expansion_minutes": None,
        "expansion_distance": 0,
    }

    if hasattr(rows, "between"):
        window = rows.between(end_dt, end_dt + timedelta(hours=4))
    else:
        window = rows[
            (rows["market_datetime"] >= end_dt)
            & (rows["market_datetime"] <= end_dt + timedelta(hours=4))
        ].copy()

    if window.empty:
        return defaults

    moves = window["close"] - end_price
    favorable = moves.apply(lambda move: favorable_distance(episode_direction, move))
    threshold = max(end_price * 0.0005, 25)
    expansion_rows = window[favorable >= threshold]

    if expansion_rows.empty:
        strongest = float(favorable.max()) if not favorable.empty else 0
        return {
            "time_to_expansion_minutes": None,
            "expansion_distance": round_float(strongest),
        }

    expansion_index = expansion_rows.index[0]
    expansion_dt = window.loc[expansion_index, "market_datetime"]
    strongest = float(favorable.max()) if not favorable.empty else 0

    return {
        "time_to_expansion_minutes": (
            expansion_dt - end_dt
        ).total_seconds()
        / 60,
        "expansion_distance": round_float(strongest),
    }


def expansion_strength(distance):
    value = to_float(distance)

    if value is None or value <= 0:
        return "NONE"

    if value >= EXPANSION_EXTREME_THRESHOLD:
        return "EXTREME"

    if value >= EXPANSION_HIGH_THRESHOLD:
        return "HIGH"

    if value >= EXPANSION_MEDIUM_THRESHOLD:
        return "MEDIUM"

    return "LOW"


def classify_expansion_type(
    expansion_distance,
    reversal_distance,
    expansion_time,
    reversal_time,
    expansion_before_reversal,
    expansion_survived,
    expansion_failed,
):
    has_expansion = expansion_distance >= EXPANSION_MEDIUM_THRESHOLD
    has_reversal = reversal_distance >= REVERSAL_MEDIUM_THRESHOLD

    if has_reversal and (reversal_time is not None and reversal_time <= 15):
        return "DIRECT_REVERSAL"

    if has_expansion and not has_reversal:
        return "PURE_EXPANSION"

    if has_expansion and has_reversal and expansion_before_reversal:
        return "EXPANSION_THEN_REVERSAL"

    if expansion_failed:
        return "FAILED_EXPANSION"

    if not has_expansion and not has_reversal:
        return "NO_EXPANSION"

    if expansion_survived:
        return "PURE_EXPANSION"

    return "FAILED_EXPANSION"


def contiguous_row_groups(rows):
    groups = []
    current_rows = []
    previous_row_id = None

    for _, row in rows.iterrows():
        row_id = to_int(row.get("row_id"), None)

        if (
            previous_row_id is not None
            and row_id is not None
            and row_id != previous_row_id + 1
            and current_rows
        ):
            groups.append(pd.DataFrame(current_rows))
            current_rows = []

        current_rows.append(row)
        previous_row_id = row_id

    if current_rows:
        groups.append(pd.DataFrame(current_rows))

    return groups


def classify_preparation_market_state(rows):
    closes = numeric_series(rows, "close")
    range_values = numeric_series(rows, "research_range_value")
    range_baseline = numeric_series(rows, "research_rolling_range_mean")
    volatility_values = numeric_series(rows, "volatility_acceleration")

    if closes.empty:
        return "UNKNOWN"

    close_range = float(closes.max() - closes.min())
    close_start = float(closes.iloc[0])
    close_end = float(closes.iloc[-1])
    move = close_end - close_start
    move_threshold = max(close_range * 0.35, close_end * 0.0003, 10)
    average_range = range_values.mean() if not range_values.empty else None
    average_baseline = range_baseline.mean() if not range_baseline.empty else None
    average_volatility = (
        volatility_values.mean() if not volatility_values.empty else None
    )

    if average_baseline and average_range is not None:
        if average_range <= 0.65 * average_baseline:
            return "COMPRESSION"
        if average_range >= 1.5 * average_baseline:
            return "EXPANSION"

    if average_volatility is not None and average_volatility >= 1.5:
        return "VOLATILE"

    if move > move_threshold:
        return "TREND_UP"

    if move < -move_threshold:
        return "TREND_DOWN"

    return "RANGE"


def build_preparation_zones_log(research_log):
    zone_columns = [
        "case_id",
        "episode_id",
        "episode_start_time_utc",
        "classification",
        "preparation_start_row",
        "preparation_end_row",
        "preparation_duration_rows",
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
        "pre_entropy",
        "pre_price_zscore_mean",
        "pre_range_mean",
        "pre_volume_mean",
        "pre_market_state",
    ]

    if research_log.empty:
        return pd.DataFrame(columns=zone_columns)

    zones = research_log[research_log["preparation_zone_found"] == True].copy()

    if zones.empty:
        return pd.DataFrame(columns=zone_columns)

    existing_columns = [column for column in zone_columns if column in zones.columns]
    return zones[existing_columns].copy()


def build_lifecycle_memories(research_log):
    zone_memory = ZoneLifecycleMemory()
    field_memory = FieldLifecycleMemory()

    if research_log.empty:
        return zone_memory, field_memory

    for _, row in research_log.iterrows():
        add_zone_lifecycle_events(zone_memory, row)
        add_field_lifecycle_events(field_memory, row)

    return zone_memory, field_memory


def add_zone_lifecycle_events(zone_memory, row):
    if not truthy_value(row.get("preparation_candidate")):
        return

    case_id = row.get("case_id")
    episode_id = row.get("episode_id")
    row_index = row.get("start_row_id")
    event_timestamp = row.get("episode_start_time_utc")
    zone_id = research_zone_id(row)

    zone_memory.add_zone_event(
        zone_id=zone_id,
        lifecycle_state="zone_created",
        zone_type="preparation",
        zone_price=row.get("preparation_mid_price"),
        zone_strength=row.get("preparation_strength"),
        zone_source="phase1b_research_preparation_detector",
        reaction_quality="PENDING_RETURN_REACTION",
        research_notes="Preparation zone detected by research-only detector.",
        event_timestamp=event_timestamp,
        lifecycle_age=row.get("preparation_duration_rows"),
        related_case_id=case_id,
        related_episode_id=episode_id,
        row_index=row_index,
    )

    if truthy_value(row.get("return_to_preparation")):
        zone_memory.add_zone_event(
            zone_id=zone_id,
            lifecycle_state="zone_tested",
            zone_type="preparation",
            zone_price=row.get("return_price") or row.get("preparation_mid_price"),
            zone_strength=row.get("preparation_strength"),
            zone_source="phase1b_research_return_detection",
            reaction_quality=zone_reaction_quality(row),
            research_notes="Preparation zone revisited after Dashboard V2 episode.",
            event_timestamp=row.get("return_timestamp") or event_timestamp,
            lifecycle_age=row.get("preparation_duration_rows"),
            related_case_id=case_id,
            related_episode_id=episode_id,
            row_index=row.get("return_row") or row_index,
        )

    if truthy_value(row.get("failed_after_return")):
        zone_memory.add_zone_event(
            zone_id=zone_id,
            lifecycle_state="zone_rejected",
            zone_type="preparation",
            zone_price=row.get("return_price") or row.get("preparation_mid_price"),
            zone_strength=row.get("preparation_strength"),
            zone_source="phase1b_research_failed_return",
            reaction_quality="FAILED_RETURN_REVERSAL",
            research_notes="Return to preparation failed and reversal context appeared.",
            event_timestamp=row.get("return_timestamp") or event_timestamp,
            lifecycle_age=row.get("preparation_duration_rows"),
            related_case_id=case_id,
            related_episode_id=episode_id,
            row_index=row.get("return_row") or row_index,
        )
    elif truthy_value(row.get("return_to_preparation")) and not is_direct_reversal(row):
        zone_memory.add_zone_event(
            zone_id=zone_id,
            lifecycle_state="zone_reclaimed",
            zone_type="preparation",
            zone_price=row.get("return_price") or row.get("preparation_mid_price"),
            zone_strength=row.get("preparation_strength"),
            zone_source="phase1b_research_successful_return",
            reaction_quality="RETURN_EXPANSION_OBSERVED",
            research_notes="Return to preparation produced non-failed reaction.",
            event_timestamp=row.get("return_timestamp") or event_timestamp,
            lifecycle_age=row.get("preparation_duration_rows"),
            related_case_id=case_id,
            related_episode_id=episode_id,
            row_index=row.get("return_row") or row_index,
        )


def add_field_lifecycle_events(field_memory, row):
    case_id = row.get("case_id")
    episode_id = row.get("episode_id")
    row_index = row.get("start_row_id")
    event_timestamp = row.get("episode_start_time_utc")

    add_delta_field_events(field_memory, row, case_id, episode_id, row_index, event_timestamp)
    add_preparation_field_events(field_memory, row, case_id, episode_id, row_index, event_timestamp)
    add_expansion_field_events(field_memory, row, case_id, episode_id, row_index, event_timestamp)
    add_reversal_field_events(field_memory, row, case_id, episode_id, row_index, event_timestamp)
    add_hypothesis02_field_events(field_memory, row, case_id, episode_id, row_index, event_timestamp)


def add_delta_field_events(field_memory, row, case_id, episode_id, row_index, event_timestamp):
    delta_value = to_float(row.get("peak_delta_zscore"))
    if delta_value is None:
        return

    state = "field_active"
    strength = "LOW"
    if abs(delta_value) >= 3:
        state = "field_strengthening"
        strength = "EXTREME"
    elif abs(delta_value) >= 2.75:
        state = "field_strengthening"
        strength = "HIGH"
    elif abs(delta_value) >= 2:
        strength = "MEDIUM"

    field_memory.add_field_event(
        field_id=research_field_id(row, "delta_zscore"),
        field_type="delta_zscore",
        lifecycle_state=state,
        field_value=delta_value,
        field_strength=strength,
        related_episode_id=episode_id,
        related_case_id=case_id,
        row_index=row_index,
        event_timestamp=event_timestamp,
        research_notes="Peak delta zscore captured for research lifecycle context.",
    )


def add_preparation_field_events(field_memory, row, case_id, episode_id, row_index, event_timestamp):
    if not truthy_value(row.get("preparation_candidate")):
        return

    strength = value_or_unknown(row.get("preparation_strength"))
    state = "field_strengthening" if strength in {"HIGH", "EXTREME"} else "field_active"
    field_memory.add_field_event(
        field_id=research_field_id(row, "preparation_candidate"),
        field_type="preparation_candidate",
        lifecycle_state=state,
        field_value=True,
        field_strength=strength,
        related_episode_id=episode_id,
        related_case_id=case_id,
        row_index=row_index,
        event_timestamp=event_timestamp,
        research_notes="Preparation candidate captured by research detector.",
    )


def add_expansion_field_events(field_memory, row, case_id, episode_id, row_index, event_timestamp):
    expansion_type = str(row.get("expansion_type") or "")
    if not expansion_type:
        return

    if expansion_type == "PURE_EXPANSION":
        state = "field_strengthening"
    elif expansion_type == "EXPANSION_THEN_REVERSAL":
        state = "field_weakening"
    elif expansion_type in {"FAILED_EXPANSION", "DIRECT_REVERSAL", "NO_EXPANSION"}:
        state = "field_exhausted"
    else:
        state = "field_active"

    field_memory.add_field_event(
        field_id=research_field_id(row, "expansion_state"),
        field_type="expansion_state",
        lifecycle_state=state,
        field_value=expansion_type,
        field_strength=row.get("expansion_strength"),
        related_episode_id=episode_id,
        related_case_id=case_id,
        row_index=row_index,
        event_timestamp=event_timestamp,
        research_notes="Expansion state captured for research lifecycle context.",
    )


def add_reversal_field_events(field_memory, row, case_id, episode_id, row_index, event_timestamp):
    reversal_type = str(row.get("reversal_type") or "")
    if not reversal_type:
        return

    if reversal_type in {"DIRECT_REVERSAL", "FAILED_RETURN_REVERSAL"}:
        state = "field_strengthening"
    elif reversal_type == "NO_REVERSAL":
        state = "field_inactive"
    else:
        state = "field_active"

    field_memory.add_field_event(
        field_id=research_field_id(row, "reversal_state"),
        field_type="reversal_state",
        lifecycle_state=state,
        field_value=reversal_type,
        field_strength=row.get("reversal_strength"),
        related_episode_id=episode_id,
        related_case_id=case_id,
        row_index=row_index,
        event_timestamp=event_timestamp,
        research_notes="Reversal state captured for research lifecycle context.",
    )


def add_hypothesis02_field_events(field_memory, row, case_id, episode_id, row_index, event_timestamp):
    state_value = hypothesis02_state(row)
    if state_value == "NO_RESEARCH_CONTEXT":
        lifecycle_state = "field_inactive"
    elif state_value == "RETURN_EXPANSION_OBSERVED":
        lifecycle_state = "field_recovered"
    elif state_value == "RETURN_FAILURE":
        lifecycle_state = "field_exhausted"
    else:
        lifecycle_state = "field_active"

    field_memory.add_field_event(
        field_id=research_field_id(row, "hypothesis02_state"),
        field_type="hypothesis02_state",
        lifecycle_state=lifecycle_state,
        field_value=state_value,
        field_strength=row.get("expansion_strength") or row.get("reversal_strength"),
        related_episode_id=episode_id,
        related_case_id=case_id,
        row_index=row.get("return_row") or row_index,
        event_timestamp=row.get("return_timestamp") or event_timestamp,
        research_notes="HYPOTHESIS_02 return/revisit state captured for research lifecycle context.",
    )


def write_lifecycle_events_jsonl(events, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for event in events:
            file.write(json.dumps(event, ensure_ascii=True, sort_keys=True))
            file.write("\n")


def research_zone_id(row):
    return f"PREP_ZONE_{row.get('case_id')}_{row.get('episode_id')}"


def research_field_id(row, field_type):
    return f"{field_type}_{row.get('case_id')}_{row.get('episode_id')}"


def zone_reaction_quality(row):
    if truthy_value(row.get("failed_after_return")):
        return "FAILED_RETURN_REVERSAL"
    if str(row.get("expansion_type") or "") == "PURE_EXPANSION":
        return "SUCCESSFUL_RETURN_EXPANSION"
    if str(row.get("expansion_type") or "") == "EXPANSION_THEN_REVERSAL":
        return "MIXED_RETURN_REACTION"
    return "RETURN_REACTION_UNCLEAR"


def is_direct_reversal(row):
    return truthy_value(row.get("direct_reversal_flag")) or str(
        row.get("reversal_type") or ""
    ) in {"DIRECT_REVERSAL", "FAILED_RETURN_REVERSAL"}


def hypothesis02_state(row):
    if truthy_value(row.get("failed_after_return")):
        return "RETURN_FAILURE"
    if truthy_value(row.get("return_to_preparation")) and truthy_value(
        row.get("expansion_after_return")
    ):
        return "RETURN_EXPANSION_OBSERVED"
    if truthy_value(row.get("return_to_preparation")):
        return "RETURN_OBSERVED"
    if truthy_value(row.get("preparation_candidate")):
        return "PREPARATION_NO_RETURN"
    return "NO_RESEARCH_CONTEXT"


def is_research_candidate(episode):
    layer_count = to_int(episode.get("peak_layer_count"), 0)
    severity = str(episode.get("peak_max_severity") or "")
    primary_context = str(episode.get("peak_primary_context") or "")

    return (
        layer_count >= 4
        or severity in {"HIGH", "EXTREME"}
        or primary_context == "DELTA_ZSCORE_EXTREME"
    )


def filter_score4plus_episodes(episodes):
    if episodes.empty or "peak_layer_count" not in episodes.columns:
        return episodes.head(0).copy()

    filtered = episodes.copy()
    filtered["research_score_proxy"] = pd.to_numeric(
        filtered["peak_layer_count"],
        errors="coerce",
    ).fillna(0)

    return filtered[filtered["research_score_proxy"] >= 4].drop(
        columns=["research_score_proxy"],
    )


def calculate_pre_episode_state(rows, start_dt, start_row_id, base_price):
    if start_dt is None:
        return {
            "pre_range": None,
            "pre_volatility_proxy": None,
            "pre_direction": "UNKNOWN",
            "pre_compression_flag": False,
        }

    window_start = start_dt - timedelta(minutes=30)
    if hasattr(rows, "before_time"):
        pre_rows = rows.before_time(start_dt, start_dt=window_start)
    else:
        pre_rows = rows[
            (rows["market_datetime"] >= window_start)
            & (rows["market_datetime"] < start_dt)
        ].copy()

    if pre_rows.empty and start_row_id is not None and "row_id" in rows.columns:
        if hasattr(rows, "before_row_id"):
            pre_rows = rows.before_row_id(start_row_id, tail=50)
        else:
            pre_rows = rows[rows["row_id"] < start_row_id].tail(50).copy()

    if pre_rows.empty:
        return {
            "pre_range": None,
            "pre_volatility_proxy": None,
            "pre_direction": "UNKNOWN",
            "pre_compression_flag": False,
        }

    closes = pd.to_numeric(pre_rows["close"], errors="coerce").dropna()

    if closes.empty:
        return {
            "pre_range": None,
            "pre_volatility_proxy": None,
            "pre_direction": "UNKNOWN",
            "pre_compression_flag": False,
        }

    pre_range = float(closes.max() - closes.min())
    pre_volatility_proxy = float(closes.diff().dropna().std() or 0)
    direction_move = float(closes.iloc[-1] - closes.iloc[0])
    direction_threshold = max(pre_range * 0.2, (base_price or closes.iloc[-1]) * 0.0002)

    if direction_move > direction_threshold:
        pre_direction = "UP"
    elif direction_move < -direction_threshold:
        pre_direction = "DOWN"
    else:
        pre_direction = "FLAT"

    compression_base = base_price or closes.iloc[-1]
    pre_compression_flag = (
        compression_base > 0
        and (pre_range / compression_base) <= 0.001
    )

    return {
        "pre_range": round_float(pre_range),
        "pre_volatility_proxy": round_float(pre_volatility_proxy),
        "pre_direction": pre_direction,
        "pre_compression_flag": pre_compression_flag,
    }


def calculate_window_extremes(rows, start_dt, end_dt, base_price, suffix):
    keys = {
        "max_up": f"max_up_move_{suffix}",
        "max_down": f"max_down_move_{suffix}",
        "max_abs": f"max_abs_move_{suffix}",
        "time_abs": f"time_to_max_abs_move_{suffix}",
    }

    if start_dt is None or end_dt is None or base_price is None:
        return {
            keys["max_up"]: None,
            keys["max_down"]: None,
            keys["max_abs"]: None,
            keys["time_abs"]: None,
        }

    if hasattr(rows, "between"):
        window = rows.between(start_dt, end_dt)
    else:
        window = rows[
            (rows["market_datetime"] >= start_dt)
            & (rows["market_datetime"] <= end_dt)
        ].copy()

    if window.empty:
        return {
            keys["max_up"]: None,
            keys["max_down"]: None,
            keys["max_abs"]: None,
            keys["time_abs"]: None,
        }

    moves = window["close"] - base_price
    max_up = float(moves.max())
    max_down = float(moves.min())
    abs_index = moves.abs().idxmax()
    max_abs = float(abs(moves.loc[abs_index]))
    time_to_abs = (
        window.loc[abs_index, "market_datetime"] - start_dt
    ).total_seconds()

    return {
        keys["max_up"]: round_float(max_up),
        keys["max_down"]: round_float(max_down),
        keys["max_abs"]: round_float(max_abs),
        keys["time_abs"]: round_float(time_to_abs),
    }


def classify_episode(
    episode,
    candidate,
    future_moves,
    extremes_1h,
    extremes_4h,
    pre_state,
    base_price,
):
    if base_price is None or base_price <= 0:
        return "UNKNOWN", "Missing base price or insufficient price data."

    pre_range = to_float(pre_state.get("pre_range")) or 0
    base_threshold = max(base_price * 0.001, pre_range * 0.75, 25)
    strong_threshold = max(base_price * 0.002, pre_range * 1.25, 50)
    range_threshold = max(base_price * 0.0005, pre_range * 0.35, 15)

    move_1m = abs_value(future_moves.get("move_1m"))
    move_5m = abs_value(future_moves.get("move_5m"))
    move_15m = abs_value(future_moves.get("move_15m"))
    move_30m = abs_value(future_moves.get("move_30m"))
    move_1h = abs_value(future_moves.get("move_1h"))
    move_2h = abs_value(future_moves.get("move_2h"))
    move_4h = abs_value(future_moves.get("move_4h"))

    early_abs = max(move_1m, move_5m, move_15m)
    mid_abs = max(move_30m, move_1h)
    later_abs = max(move_2h, move_4h)
    max_abs_1h = to_float(extremes_1h.get("max_abs_move_1h")) or 0
    max_abs_4h = to_float(extremes_4h.get("max_abs_move_4h")) or 0

    delta_zscore = abs_value(episode.get("peak_delta_zscore"))
    velocity = abs_value(episode.get("peak_velocity"))
    primary_context = str(episode.get("peak_primary_context") or "")
    active_layers = str(episode.get("peak_active_layers") or "")
    episode_direction = direction_from_episode(episode)

    if max_abs_4h == 0 and later_abs == 0 and mid_abs == 0 and early_abs == 0:
        return "UNKNOWN", "No post-episode price rows available."

    if candidate and max_abs_4h < base_threshold:
        if delta_zscore >= 2 and velocity < 1:
            return (
                "ABSORPTION",
                "High delta context with limited post-episode expansion.",
            )

        return (
            "FAILED_CONTEXT",
            "Research candidate did not produce meaningful expansion.",
        )

    if max_abs_4h < range_threshold:
        return "RANGE_NOISE", "Post-episode movement remained range-bound."

    if is_reversal_warning(episode_direction, future_moves, base_threshold):
        return (
            "REVERSAL_WARNING",
            "Post-episode movement moved against the episode direction proxy.",
        )

    if early_abs >= strong_threshold:
        return (
            "ACCELERATION_ZONE",
            "Large movement appeared within the early 1m-15m window.",
        )

    if (
        delta_zscore >= 2
        and early_abs < base_threshold
        and later_abs >= strong_threshold
    ):
        return (
            "ACCUMULATION",
            "High delta context stayed quiet early and expanded later.",
        )

    if mid_abs >= strong_threshold or later_abs >= strong_threshold:
        return (
            "MOMENTUM_PRECURSOR",
            "Meaningful movement developed after the episode.",
        )

    if (
        "DELTA_ZSCORE_EXTREME" in primary_context
        or "volume" in active_layers
        or "velocity" in active_layers
    ) and max_abs_1h >= base_threshold:
        return (
            "PRE_EXPANSION",
            "Statistical context preceded moderate expansion.",
        )

    return "CONTEXT_ONLY", "Episode remained useful as context only."


def is_reversal_warning(episode_direction, future_moves, threshold):
    if episode_direction == "FLAT":
        return False

    move_30m = to_float(future_moves.get("move_30m"))
    move_1h = to_float(future_moves.get("move_1h"))
    check_moves = [value for value in [move_30m, move_1h] if value is not None]

    if not check_moves:
        return False

    strongest = max(check_moves, key=lambda value: abs(value))

    if abs(strongest) < threshold:
        return False

    return (
        episode_direction == "UP"
        and strongest < 0
    ) or (
        episode_direction == "DOWN"
        and strongest > 0
    )


def direction_from_episode(episode):
    start_price = to_float(episode.get("start_price"))
    end_price = to_float(episode.get("end_price"))

    if start_price is None or end_price is None:
        return "FLAT"

    move = end_price - start_price
    threshold = max(end_price * 0.0002, 10)

    if move > threshold:
        return "UP"

    if move < -threshold:
        return "DOWN"

    return "FLAT"


def nearest_close_at_or_after(rows, target_dt):
    if target_dt is None:
        return None

    if hasattr(rows, "at_or_after"):
        row = rows.at_or_after(target_dt)
        if row is None:
            return None
        return round_float(row.get("close"))

    future_rows = rows[rows["market_datetime"] >= target_dt]

    if future_rows.empty:
        return None

    return round_float(future_rows.iloc[0]["close"])


def close_at_day_end(rows, reference_dt):
    if reference_dt is None:
        return None

    day = reference_dt.date()
    if hasattr(rows, "same_day"):
        same_day = rows.same_day(day)
    else:
        same_day = rows[rows["market_datetime"].dt.date == day]

    if same_day.empty:
        return None

    return round_float(same_day.iloc[-1]["close"])


def build_summary(
    research_log,
    output_log,
    preparation_zones,
    episodes_total_loaded,
    episodes_score4plus_count,
    mode,
    analysis_run_utc,
):
    counts = classification_counts(output_log)
    score_counts = output_log["score_bucket"].value_counts().to_dict()
    preparation_stats = preparation_summary(output_log)
    agreement_counts = value_counts(output_log, "agreement_flag")
    expansion_counts = value_counts(output_log, "expansion_strength")
    reversal_strength_counts = value_counts(output_log, "reversal_strength")
    expansion_type_counts = value_counts(output_log, "expansion_type")

    return {
        "analysis_run_utc": analysis_run_utc,
        "mode": mode,
        "episodes_total": episodes_total_loaded,
        "episodes_analyzed": len(output_log),
        "episodes_loaded": len(research_log),
        "episodes_score4plus": episodes_score4plus_count,
        "research_candidates": int(output_log["is_research_candidate"].sum()),
        "momentum_count": counts.get("MOMENTUM_PRECURSOR", 0),
        "momentum_precursor_count": counts.get("MOMENTUM_PRECURSOR", 0),
        "acceleration_zone_count": counts.get("ACCELERATION_ZONE", 0),
        "pre_expansion_count": counts.get("PRE_EXPANSION", 0),
        "context_only_count": counts.get("CONTEXT_ONLY", 0),
        "reversal_count": counts.get("REVERSAL_WARNING", 0),
        "reversal_warning_count": counts.get("REVERSAL_WARNING", 0),
        "accumulation_count": counts.get("ACCUMULATION", 0),
        "absorption_count": counts.get("ABSORPTION", 0),
        "failed_count": counts.get("FAILED_CONTEXT", 0),
        "failed_context_count": counts.get("FAILED_CONTEXT", 0),
        "range_noise_count": counts.get("RANGE_NOISE", 0),
        "unknown_count": counts.get("UNKNOWN", 0),
        "score_4_count": int(score_counts.get("SCORE_4", 0)),
        "score_5_count": int(score_counts.get("SCORE_5", 0)),
        "score_6_count": int(score_counts.get("SCORE_6", 0)),
        "preparation_zone_count": int(
            output_log["preparation_zone_found"].sum()
        )
        if "preparation_zone_found" in output_log.columns
        else 0,
        "preparation_candidate_count": count_true_column(
            output_log,
            "preparation_candidate",
        ),
        "preparation_high_count": count_value_column(
            output_log,
            "preparation_strength",
            "HIGH",
        ),
        "preparation_extreme_count": count_value_column(
            output_log,
            "preparation_strength",
            "EXTREME",
        ),
        "return_to_preparation_count": count_true_column(
            output_log,
            "return_to_preparation",
        ),
        "return_count": count_true_column(output_log, "return_to_preparation"),
        "return_success_count": count_true_column(
            output_log,
            "expansion_after_return",
        ),
        "return_failure_count": count_return_failures(output_log),
        "agreement_true": int(agreement_counts.get("True", 0)),
        "agreement_false": int(agreement_counts.get("False", 0)),
        "agreement_unknown": int(agreement_counts.get("UNKNOWN", 0)),
        "high_expansion_count": int(expansion_counts.get("HIGH", 0)),
        "extreme_expansion_count": int(expansion_counts.get("EXTREME", 0)),
        "avg_return_delay": average_numeric_column(
            output_log,
            "time_to_return_minutes",
        ),
        "avg_revisit_duration": average_numeric_column(
            output_log,
            "revisit_duration_rows",
        ),
        "avg_quiet_score": average_numeric_column(
            output_log,
            "pre_quiet_score",
        ),
        "avg_range_ratio": average_numeric_column(
            output_log,
            "pre_range_ratio",
        ),
        "best_preparation_cases": format_case_id_list(
            best_preparation_cases(output_log)
        ),
        "failed_preparation_cases": format_case_id_list(
            failed_preparation_cases(output_log)
        ),
        "reversal_after_return_count": count_true_column(
            output_log,
            "reversal_after_return",
        ),
        "direct_reversal_count": count_true_column(
            output_log,
            "direct_reversal_flag",
        ),
        "late_reversal_count": count_true_column(
            output_log,
            "late_reversal_flag",
        ),
        "failed_after_return_count": count_true_column(
            output_log,
            "failed_after_return",
        ),
        "avg_time_to_reversal": average_numeric_column(
            output_log,
            "time_to_reversal_minutes",
        ),
        "avg_reversal_strength_score": average_reversal_strength_score(output_log),
        "extreme_reversal_count": int(reversal_strength_counts.get("EXTREME", 0)),
        "high_reversal_count": int(reversal_strength_counts.get("HIGH", 0)),
        "pure_expansion_count": int(
            expansion_type_counts.get("PURE_EXPANSION", 0)
        ),
        "expansion_then_reversal_count": int(
            expansion_type_counts.get("EXPANSION_THEN_REVERSAL", 0)
        ),
        "failed_expansion_count": int(
            expansion_type_counts.get("FAILED_EXPANSION", 0)
        ),
        "direct_reversal_expansion_split_count": int(
            expansion_type_counts.get("DIRECT_REVERSAL", 0)
        ),
        "avg_expansion_strength": average_expansion_strength_score(output_log),
        "avg_expansion_to_reversal_ratio": average_numeric_column(
            output_log,
            "expansion_to_reversal_ratio",
        ),
        "preparation_zones_found": int(
            output_log["preparation_zone_found"].sum()
        )
        if "preparation_zone_found" in output_log.columns
        else 0,
        "preparation_zones_written": len(preparation_zones),
        "momentum_precursor_with_preparation": preparation_stats.get(
            "MOMENTUM_PRECURSOR",
            0,
        ),
        "reversal_warning_with_preparation": preparation_stats.get(
            "REVERSAL_WARNING",
            0,
        ),
        "failed_context_with_preparation": preparation_stats.get(
            "FAILED_CONTEXT",
            0,
        ),
        "pre_expansion_with_preparation": preparation_stats.get(
            "PRE_EXPANSION",
            0,
        ),
        **preparation_state_rates(output_log),
        "source_episode_file": relative_path(EPISODE_FILE),
        "source_rows_file": relative_path(ROWS_FILE),
    }


def append_research_journal(summary, research_log, mode):
    counts = classification_counts(research_log)
    strongest = strongest_examples(research_log)
    counterexamples = counterexample_rows(research_log)
    replay_window = replay_window_text(research_log)

    lines = [
        "",
        "==================================================",
        "PHASE 1B EPISODE RESEARCH RUN",
        "==================================================",
        "",
        f"Run UTC: {summary['analysis_run_utc']}",
        f"Replay window: {replay_window}",
        f"Mode: {mode}",
        f"Episodes total: {summary['episodes_total']}",
        f"Episodes analyzed: {summary['episodes_analyzed']}",
        f"Score >= 4 episodes: {summary['episodes_score4plus']}",
        f"Research candidates: {summary['research_candidates']}",
        "",
        "Classification counts:",
    ]

    for label in CLASSIFICATIONS:
        lines.append(f"- {label}: {counts.get(label, 0)}")

    lines.extend(["", "Strongest examples:"])
    lines.extend(format_example_lines(strongest))
    lines.extend(["", "Counterexamples:"])
    lines.extend(format_example_lines(counterexamples))
    lines.extend(
        [
            "",
            "Preparation zone summary:",
            f"- Preparation candidates: {summary.get('preparation_candidate_count', 0)}",
            f"- Preparation zones found: {summary.get('preparation_zones_found', 0)}",
            f"- HIGH preparation count: {summary.get('preparation_high_count', 0)}",
            f"- EXTREME preparation count: {summary.get('preparation_extreme_count', 0)}",
            "- MOMENTUM_PRECURSOR with preparation: "
            f"{summary.get('momentum_precursor_with_preparation', 0)}",
            "- REVERSAL_WARNING with preparation: "
            f"{summary.get('reversal_warning_with_preparation', 0)}",
            "- FAILED_CONTEXT with preparation: "
            f"{summary.get('failed_context_with_preparation', 0)}",
            "- PRE_EXPANSION with preparation: "
            f"{summary.get('pre_expansion_with_preparation', 0)}",
            "",
            "HYPOTHESIS_02 revisit summary:",
            f"- Return count: {summary.get('return_to_preparation_count', 0)}",
            f"- Return success count: {summary.get('return_success_count', 0)}",
            f"- Return failure count: {summary.get('return_failure_count', 0)}",
            f"- Agreement true: {summary.get('agreement_true', 0)}",
            f"- Agreement false: {summary.get('agreement_false', 0)}",
            f"- Agreement unknown: {summary.get('agreement_unknown', 0)}",
            f"- High expansion count: {summary.get('high_expansion_count', 0)}",
            f"- Extreme expansion count: {summary.get('extreme_expansion_count', 0)}",
            f"- Average quiet score: {summary.get('avg_quiet_score', '')}",
            f"- Average range ratio: {summary.get('avg_range_ratio', '')}",
            f"- Best preparation cases: {summary.get('best_preparation_cases', '')}",
            f"- Failed preparation cases: {summary.get('failed_preparation_cases', '')}",
            "",
            "REVERSAL ANALYZER V1 summary:",
            f"- Direct reversals: {summary.get('direct_reversal_count', 0)}",
            f"- Late reversals: {summary.get('late_reversal_count', 0)}",
            "- Reversal after preparation return: "
            f"{summary.get('reversal_after_return_count', 0)}",
            f"- Failed after return: {summary.get('failed_after_return_count', 0)}",
            f"- HIGH reversal count: {summary.get('high_reversal_count', 0)}",
            f"- EXTREME reversal count: {summary.get('extreme_reversal_count', 0)}",
            f"- Average time to reversal: {summary.get('avg_time_to_reversal', '')}",
            "",
            "EXPANSION / REVERSAL SPLIT V1 summary:",
            f"- Pure expansions: {summary.get('pure_expansion_count', 0)}",
            "- Expansion then reversal: "
            f"{summary.get('expansion_then_reversal_count', 0)}",
            f"- Failed expansions: {summary.get('failed_expansion_count', 0)}",
            "- Direct reversals: "
            f"{summary.get('direct_reversal_expansion_split_count', 0)}",
            "- Average expansion strength: "
            f"{summary.get('avg_expansion_strength', '')}",
            "- Average expansion to reversal ratio: "
            f"{summary.get('avg_expansion_to_reversal_ratio', '')}",
        ]
    )
    lines.extend(
        [
            "",
            "Note:",
            "HYPOTHESIS_01 remains unproven.",
            "No trading interpretation.",
            "",
        ]
    )

    with RESEARCH_JOURNAL_FILE.open("a", encoding="utf-8") as file:
        file.write("\n".join(lines))


def classification_counts(dataframe):
    counts = dataframe["classification"].value_counts().to_dict()
    return {label: int(counts.get(label, 0)) for label in CLASSIFICATIONS}


def value_counts(dataframe, column):
    if dataframe.empty or column not in dataframe.columns:
        return {}

    return {
        str(key): int(value)
        for key, value in dataframe[column].fillna("UNKNOWN").value_counts().to_dict().items()
    }


def count_true_column(dataframe, column):
    if dataframe.empty or column not in dataframe.columns:
        return 0

    return int(dataframe[column].apply(truthy_value).sum())


def count_value_column(dataframe, column, value):
    if dataframe.empty or column not in dataframe.columns:
        return 0

    return int((dataframe[column].astype(str) == value).sum())


def count_return_failures(dataframe):
    if dataframe.empty:
        return 0

    if "return_to_preparation" not in dataframe.columns:
        return 0

    returned = dataframe[dataframe["return_to_preparation"].apply(truthy_value)]

    if returned.empty or "expansion_after_return" not in returned.columns:
        return 0

    return int((~returned["expansion_after_return"].apply(truthy_value)).sum())


def average_numeric_column(dataframe, column):
    if dataframe.empty or column not in dataframe.columns:
        return ""

    values = pd.to_numeric(dataframe[column], errors="coerce").dropna()

    if values.empty:
        return ""

    return round_float(values.mean())


def average_reversal_strength_score(dataframe):
    if dataframe.empty or "reversal_strength" not in dataframe.columns:
        return ""

    rank = {
        "NONE": 0,
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "EXTREME": 4,
    }
    values = [
        rank.get(str(value), 0)
        for value in dataframe["reversal_strength"].fillna("NONE")
    ]

    if not values:
        return ""

    return round_float(sum(values) / len(values))


def average_expansion_strength_score(dataframe):
    if dataframe.empty or "expansion_strength" not in dataframe.columns:
        return ""

    rank = {
        "NONE": 0,
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "EXTREME": 4,
    }
    values = [
        rank.get(str(value), 0)
        for value in dataframe["expansion_strength"].fillna("NONE")
    ]

    if not values:
        return ""

    return round_float(sum(values) / len(values))


def best_preparation_cases(dataframe):
    if dataframe.empty or "preparation_candidate" not in dataframe.columns:
        return dataframe.head(0)

    prepared = dataframe[dataframe["preparation_candidate"].apply(truthy_value)].copy()

    if prepared.empty:
        return prepared

    if "max_move_after_return" in prepared.columns:
        prepared["max_move_after_return"] = pd.to_numeric(
            prepared["max_move_after_return"],
            errors="coerce",
        ).fillna(0)
        return prepared.sort_values("max_move_after_return", ascending=False).head(5)

    return prepared.head(5)


def failed_preparation_cases(dataframe):
    if dataframe.empty or "preparation_candidate" not in dataframe.columns:
        return dataframe.head(0)

    prepared = dataframe[dataframe["preparation_candidate"].apply(truthy_value)].copy()

    if prepared.empty or "expansion_after_return" not in prepared.columns:
        return prepared.head(0)

    failed = prepared[~prepared["expansion_after_return"].apply(truthy_value)].copy()
    return failed.head(5)


def format_case_id_list(dataframe):
    if dataframe.empty or "case_id" not in dataframe.columns:
        return ""

    return "|".join(str(value) for value in dataframe["case_id"].dropna().head(5))


def preparation_summary(dataframe):
    if dataframe.empty or "preparation_zone_found" not in dataframe.columns:
        return {}

    prepared = dataframe[dataframe["preparation_zone_found"] == True]

    if prepared.empty:
        return {}

    counts = prepared["classification"].value_counts().to_dict()
    return {label: int(counts.get(label, 0)) for label in CLASSIFICATIONS}


def preparation_state_rates(dataframe):
    output = {}

    if dataframe.empty or "pre_market_state" not in dataframe.columns:
        return output

    prepared = dataframe[dataframe["preparation_zone_found"] == True].copy()

    if prepared.empty:
        return output

    favorable_labels = {
        "MOMENTUM_PRECURSOR",
        "ACCELERATION_ZONE",
        "PRE_EXPANSION",
    }

    for state, group in prepared.groupby("pre_market_state"):
        state_name = value_or_unknown(state).lower()
        total = len(group)
        favorable = int(group["classification"].isin(favorable_labels).sum())
        failed = int((group["classification"] == "FAILED_CONTEXT").sum())
        reversal = int((group["classification"] == "REVERSAL_WARNING").sum())
        rate = round_float(favorable / total) if total else 0

        output[f"pre_state_{state_name}_episodes"] = total
        output[f"pre_state_{state_name}_favorable_count"] = favorable
        output[f"pre_state_{state_name}_failed_count"] = failed
        output[f"pre_state_{state_name}_reversal_count"] = reversal
        output[f"pre_state_{state_name}_success_rate"] = rate

    return output


def strongest_examples(dataframe):
    if dataframe.empty or "max_abs_move_4h" not in dataframe.columns:
        return dataframe.head(0)

    ranked = dataframe.copy()
    ranked["max_abs_move_4h"] = pd.to_numeric(
        ranked["max_abs_move_4h"],
        errors="coerce",
    ).fillna(0)
    return ranked.sort_values("max_abs_move_4h", ascending=False).head(5)


def counterexample_rows(dataframe):
    if dataframe.empty:
        return dataframe

    candidates = dataframe[
        dataframe["classification"].isin(["FAILED_CONTEXT", "RANGE_NOISE"])
    ].copy()

    if candidates.empty:
        return candidates

    candidates["peak_layer_count"] = pd.to_numeric(
        candidates["peak_layer_count"],
        errors="coerce",
    ).fillna(0)
    return candidates.sort_values("peak_layer_count", ascending=False).head(5)


def format_example_lines(dataframe):
    if dataframe.empty:
        return ["- None"]

    lines = []
    for _, row in dataframe.iterrows():
        lines.append(
            "- "
            f"{row.get('case_id')} | "
            f"episode_id={row.get('episode_id')} | "
            f"classification={row.get('classification')} | "
            f"layers={row.get('peak_layer_count')} | "
            f"context={row.get('peak_primary_context')} | "
            f"max_abs_4h={row.get('max_abs_move_4h')}"
        )

    return lines


def replay_window_text(dataframe):
    if dataframe.empty:
        return "N/A"

    dates = sorted(
        {
            str(value)
            for value in dataframe["episode_date"].dropna().unique()
            if str(value).strip()
        }
    )

    if not dates:
        return "N/A"

    if len(dates) == 1:
        return dates[0]

    return f"{dates[0]} -> {dates[-1]}"


def parse_datetime_value(value):
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()

        if not text:
            return None

        try:
            timestamp = float(text)
        except ValueError:
            timestamp = None

        if timestamp is not None:
            if timestamp > 10_000_000_000:
                timestamp = timestamp / 1000

            try:
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
            except (OverflowError, OSError, ValueError):
                return None

        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"

        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc)
    else:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


def utc_now_text():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def format_datetime(value):
    if value is None:
        return ""

    return value.strftime("%Y-%m-%d %H:%M:%S")


def format_date(value):
    if value is None:
        return ""

    return value.strftime("%Y-%m-%d")


def score_bucket(score_value):
    score = to_int(score_value, 0)

    if score <= 0:
        return "SCORE_UNKNOWN"

    return f"SCORE_{score}"


def layer_count_bucket(layer_count):
    count = to_int(layer_count, 0)

    if count <= 0:
        return "LAYER_UNKNOWN"

    return f"LAYER_{count}"


def value_or_unknown(value):
    if value is None:
        return "UNKNOWN"

    try:
        if pd.isna(value):
            return "UNKNOWN"
    except (TypeError, ValueError):
        pass

    text = str(value).strip()

    return text if text else "UNKNOWN"


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


def numeric_series(dataframe, column):
    if column not in dataframe.columns:
        return pd.Series(dtype="float64")

    return pd.to_numeric(dataframe[column], errors="coerce").dropna()


def closes_min(dataframe):
    closes = numeric_series(dataframe, "close")
    return closes.min() if not closes.empty else None


def closes_max(dataframe):
    closes = numeric_series(dataframe, "close")
    return closes.max() if not closes.empty else None


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


def to_int(value, default=0):
    number = to_float(value)

    if number is None:
        return default

    return int(number)


def subtract(value, base):
    if value is None or base is None:
        return None

    return round_float(value - base)


def abs_value(value):
    number = to_float(value)

    if number is None:
        return 0

    return abs(number)


def round_float(value):
    if value is None:
        return None

    try:
        return round(float(value), 8)
    except (TypeError, ValueError):
        return None


def normalize_output_row(row):
    normalized = {}

    for key, value in row.items():
        if value is None:
            normalized[key] = ""
            continue

        try:
            if pd.isna(value):
                normalized[key] = ""
                continue
        except (TypeError, ValueError):
            pass

        normalized[key] = value

    return normalized


def relative_path(path):
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()

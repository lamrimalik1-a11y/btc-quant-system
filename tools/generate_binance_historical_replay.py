import argparse
import json
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.adaptive_window import calculate_adaptive_window
from core.observation_archive import (
    DASHBOARD_V2_ARCHIVE_FIELDS,
    FIELDNAMES as OBSERVATION_FIELDNAMES,
)
from core.renko import renko_state
from core.row_builder import build_trade_row
from core.state import (
    delta_history,
    price_history,
    system_state,
    update_history,
    velocity_history,
    volume_history,
)
from engines.renko_engine import RenkoEngine
from engines.statistics_engine import StatisticsEngine
from tools.generate_replay_observation import (
    EPISODE_FIELDNAMES,
    EVENT_FIELDNAMES,
    V2_EPISODE_FIELDNAMES,
    V2_EVENT_FIELDNAMES,
    build_replay_observation,
    build_replay_observation_v2,
    write_dict_rows,
)
from tools.performance_profile import PerfProfiler


BINANCE_AGGTRADES_URL = "https://api.binance.com/api/v3/aggTrades"
OUTPUT_DIR = Path("outputs")

HISTORICAL_MARKET_ROWS_FILE = OUTPUT_DIR / "historical_market_rows.csv"
HISTORICAL_OBSERVATION_ROWS_FILE = OUTPUT_DIR / "historical_observation_rows.csv"
HISTORICAL_REPLAY_EVENTS_FILE = (
    OUTPUT_DIR / "historical_replay_observation_events.csv"
)
HISTORICAL_REPLAY_EPISODES_FILE = (
    OUTPUT_DIR / "historical_replay_dashboard_episodes.csv"
)
HISTORICAL_REPLAY_V2_EVENTS_FILE = (
    OUTPUT_DIR / "historical_replay_observation_v2_events.csv"
)
HISTORICAL_REPLAY_V2_EPISODES_FILE = (
    OUTPUT_DIR / "historical_replay_dashboard_v2_episodes.csv"
)
HISTORICAL_RAW_AGGTRADES_FILE = OUTPUT_DIR / "historical_raw_aggtrades.csv"
HISTORICAL_DOWNLOAD_CHECKPOINT_FILE = (
    OUTPUT_DIR / "historical_download_checkpoint.json"
)
HISTORICAL_DOWNLOAD_PARTIAL_FILE = (
    OUTPUT_DIR / "historical_download_partial_aggtrades.jsonl"
)

REQUEST_LIMIT = 1000
REQUEST_SLEEP_SECONDS = 0.5
REQUEST_TIMEOUT_SECONDS = 120
MAX_RETRIES = 10
RETRY_BACKOFF_SECONDS = [5, 10, 20, 40, 60]
WARMUP_TARGET_ROWS = 500
WARMUP_LOOKBACK_MS = 24 * 60 * 60 * 1000


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Generate Binance historical observation replay files for PHASE 1B. "
            "This is observation replay only, not trading backtesting."
        )
    )
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--row-size", type=int, default=500)
    parser.add_argument("--save-raw", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main():
    profiler = PerfProfiler("historical_replay_generation")
    args = parse_args()

    try:
        if args.row_size <= 0:
            raise SystemExit("--row-size must be greater than 0")

        start_ms = parse_datetime_to_ms(args.start)
        end_ms = parse_datetime_to_ms(args.end)

        if start_ms >= end_ms:
            raise SystemExit("--start must be before --end")

        warmup_start_ms = max(
            0,
            start_ms - WARMUP_LOOKBACK_MS,
        )

        if args.overwrite:
            clear_download_checkpoint()

        resume_checkpoint = load_matching_checkpoint(
            symbol=args.symbol,
            start_date=args.start,
            end_date=args.end,
        )

        ensure_outputs_can_be_written(
            overwrite=args.overwrite,
            save_raw=args.save_raw,
            resume_active=resume_checkpoint is not None,
        )

        print(f"Symbol: {args.symbol}")
        print(f"Start: {args.start}")
        print(f"End: {args.end}")
        print(f"Row size: {args.row_size}")
        if resume_checkpoint:
            print(
                "Resume checkpoint found: "
                f"last timestamp={resume_checkpoint.get('last_success_timestamp')} | "
                f"last aggTrade id={resume_checkpoint.get('last_success_agg_trade_id')} | "
                f"downloaded={resume_checkpoint.get('downloaded_count')}"
            )

        with profiler.step("download_total"):
            agg_trades = download_agg_trades(
                symbol=args.symbol,
                start_ms=warmup_start_ms,
                end_ms=end_ms,
                start_date=args.start,
                end_date=args.end,
                checkpoint=resume_checkpoint,
                profiler=profiler,
            )

        if agg_trades is None:
            profiler.add_metric("download_paused", True)
            return

        warmup_agg_trades, target_agg_trades = split_warmup_and_target_trades(
            agg_trades=agg_trades,
            target_start_ms=start_ms,
            target_end_ms=end_ms,
        )

        with profiler.step("aggregation_replay_row_build"):
            warmup_rows = build_historical_rows(
                agg_trades=warmup_agg_trades,
                row_size=args.row_size,
            )
            warmup_rows = warmup_rows[
                -WARMUP_TARGET_ROWS:
            ]
            historical_rows = build_historical_rows(
                agg_trades=target_agg_trades,
                row_size=args.row_size,
            )

        if len(warmup_rows) < WARMUP_TARGET_ROWS:
            print(
                "WARNING: Fewer than 500 warmup rows available. "
                f"Available warmup rows: {len(warmup_rows)}"
            )

        print(f"WARMUP_ROWS_USED = {len(warmup_rows)}")

        with profiler.step("observation_row_build"):
            historical_observation_rows = build_historical_observation_rows(
                historical_rows=historical_rows,
                warmup_rows=warmup_rows,
            )

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        with profiler.step("csv_write_market_rows"):
            write_dict_rows(
                HISTORICAL_MARKET_ROWS_FILE,
                get_union_fieldnames(historical_rows),
                historical_rows,
            )
        with profiler.step("csv_write_observation_rows"):
            write_dict_rows(
                HISTORICAL_OBSERVATION_ROWS_FILE,
                OBSERVATION_FIELDNAMES,
                historical_observation_rows,
            )

        with profiler.step("pandas_dataframe_build"):
            observation_dataframe = pd.DataFrame(historical_observation_rows)

        with profiler.step("replay_v1_build"):
            replay_events, replay_episodes = build_replay_observation(
                observation_dataframe
            )
        with profiler.step("replay_v2_build"):
            replay_v2_events, replay_v2_episodes = build_replay_observation_v2(
                observation_dataframe
            )

        with profiler.step("csv_write_replay_v1_events"):
            write_dict_rows(
                HISTORICAL_REPLAY_EVENTS_FILE,
                EVENT_FIELDNAMES,
                replay_events,
            )
        with profiler.step("csv_write_replay_v1_episodes"):
            write_dict_rows(
                HISTORICAL_REPLAY_EPISODES_FILE,
                EPISODE_FIELDNAMES,
                replay_episodes,
            )
        with profiler.step("csv_write_replay_v2_events"):
            write_dict_rows(
                HISTORICAL_REPLAY_V2_EVENTS_FILE,
                V2_EVENT_FIELDNAMES,
                replay_v2_events,
            )
        with profiler.step("csv_write_replay_v2_episodes"):
            write_dict_rows(
                HISTORICAL_REPLAY_V2_EPISODES_FILE,
                V2_EPISODE_FIELDNAMES,
                replay_v2_episodes,
            )

        if args.save_raw:
            with profiler.step("csv_write_raw_aggtrades"):
                write_raw_agg_trades(target_agg_trades)

        clear_download_checkpoint()

        profiler.add_metric("trades_processed", len(target_agg_trades))
        profiler.add_metric("warmup_trades_processed", len(warmup_agg_trades))
        profiler.add_metric("warmup_rows_used", len(warmup_rows))
        profiler.add_metric("rows_processed", len(historical_rows))
        profiler.add_metric("observation_rows_processed", len(historical_observation_rows))
        profiler.add_metric("v1_events", len(replay_events))
        profiler.add_metric("v1_episodes", len(replay_episodes))
        profiler.add_metric("v2_events", len(replay_v2_events))
        profiler.add_metric("v2_episodes", len(replay_v2_episodes))

        print(f"Trades downloaded: {len(agg_trades)}")
        print(f"Target trades processed: {len(target_agg_trades)}")
        print(f"Rows built: {len(historical_rows)}")
        print(f"TARGET_ROWS_WRITTEN = {len(historical_observation_rows)}")
        print(
            "Historical observation rows written: "
            f"{len(historical_observation_rows)}"
        )
        print(f"Historical events found: {len(replay_events)}")
        print(f"Historical episodes found: {len(replay_episodes)}")
        print(f"Historical V2 events found: {len(replay_v2_events)}")
        print(f"Historical V2 episodes found: {len(replay_v2_episodes)}")
        print(f"Historical market rows: {HISTORICAL_MARKET_ROWS_FILE}")
        print(f"Historical observation rows: {HISTORICAL_OBSERVATION_ROWS_FILE}")
        print(f"Historical replay events: {HISTORICAL_REPLAY_EVENTS_FILE}")
        print(f"Historical replay episodes: {HISTORICAL_REPLAY_EPISODES_FILE}")
        print(f"Historical replay V2 events: {HISTORICAL_REPLAY_V2_EVENTS_FILE}")
        print(
            "Historical replay V2 episodes: "
            f"{HISTORICAL_REPLAY_V2_EPISODES_FILE}"
        )

        if args.save_raw:
            print(f"Historical raw aggTrades: {HISTORICAL_RAW_AGGTRADES_FILE}")
    finally:
        profiler.finish(
            csv_files=[
                HISTORICAL_MARKET_ROWS_FILE,
                HISTORICAL_OBSERVATION_ROWS_FILE,
                HISTORICAL_REPLAY_EVENTS_FILE,
                HISTORICAL_REPLAY_EPISODES_FILE,
                HISTORICAL_REPLAY_V2_EVENTS_FILE,
                HISTORICAL_REPLAY_V2_EPISODES_FILE,
                HISTORICAL_RAW_AGGTRADES_FILE,
            ]
        )


def download_agg_trades(symbol, start_ms, end_ms, start_date, end_date, checkpoint, profiler=None):
    trades = load_partial_agg_trades() if checkpoint else []
    current_start_ms = start_ms

    if checkpoint:
        last_success_timestamp = checkpoint.get("last_success_timestamp")
        if last_success_timestamp is not None:
            current_start_ms = int(last_success_timestamp) + 1
            print(f"Resuming from timestamp: {current_start_ms}")

    while current_start_ms <= end_ms:
        batch_start = time.perf_counter()
        batch = fetch_agg_trades_batch_with_retries(
            symbol=symbol,
            start_ms=current_start_ms,
            end_ms=end_ms,
            profiler=profiler,
        )
        if profiler:
            profiler.record("download_batch", time.perf_counter() - batch_start)

        if batch is None:
            last_success_timestamp = current_start_ms - 1
            last_success_agg_trade_id = (
                get_agg_trade_id(trades[-1]) if trades else None
            )
            save_download_checkpoint(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                last_success_timestamp=last_success_timestamp,
                last_success_agg_trade_id=last_success_agg_trade_id,
                downloaded_count=len(trades),
            )
            print("Download paused. Re-run the same command to resume.")
            return None

        if not batch:
            break

        trades.extend(batch)
        append_partial_agg_trades(batch)

        last_timestamp = int(batch[-1]["T"])
        last_trade_id = get_agg_trade_id(batch[-1])
        save_download_checkpoint(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            last_success_timestamp=last_timestamp,
            last_success_agg_trade_id=last_trade_id,
            downloaded_count=len(trades),
        )

        if last_timestamp >= end_ms:
            break

        next_start_ms = last_timestamp + 1

        if next_start_ms <= current_start_ms:
            break

        current_start_ms = next_start_ms

        print(
            "Trades downloaded: "
            f"{len(trades)} | current timestamp: {current_start_ms} | "
            f"last aggTrade id: {last_trade_id}"
        )
        time.sleep(REQUEST_SLEEP_SECONDS)

    return trades


def fetch_agg_trades_batch_with_retries(symbol, start_ms, end_ms, profiler=None):
    params = {
        "symbol": symbol.upper(),
        "startTime": int(start_ms),
        "endTime": int(end_ms),
        "limit": REQUEST_LIMIT,
    }
    url = f"{BINANCE_AGGTRADES_URL}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "User-Agent": "btc-quant-observation-replay/1.0",
        },
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            http_start = time.perf_counter()
            with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                payload = response.read()
            if profiler:
                profiler.record("http_wait", time.perf_counter() - http_start)
            parse_start = time.perf_counter()
            decoded = payload.decode("utf-8")
            parsed = json.loads(decoded)
            if profiler:
                profiler.record("parse_batch", time.perf_counter() - parse_start)
            return parsed
        except HTTPError as error:
            if error.code in [429, 500, 502, 503, 504]:
                sleep_before_retry(attempt, error)
                continue
            raise
        except (TimeoutError, socket.timeout, URLError) as error:
            sleep_before_retry(attempt, error)

    return None


def split_warmup_and_target_trades(agg_trades, target_start_ms, target_end_ms):
    warmup_trades = []
    target_trades = []

    for trade in agg_trades:
        trade_timestamp = int(trade["T"])

        if trade_timestamp < target_start_ms:
            warmup_trades.append(trade)
        elif trade_timestamp <= target_end_ms:
            target_trades.append(trade)

    return warmup_trades, target_trades


def build_historical_rows(agg_trades, row_size):
    rows = []

    for row_index, start_index in enumerate(range(0, len(agg_trades), row_size)):
        batch = agg_trades[start_index:start_index + row_size]

        if not batch:
            continue

        tick_buffer = [
            agg_trade_to_tick(trade)
            for trade in batch
        ]

        row = build_trade_row(tick_buffer)
        row["row_id"] = row_index + 1
        row["market_timestamp"] = row.get("end_ts")
        row["duration_seconds"] = row.get("duration_sec")
        rows.append(row)

    return rows


def build_historical_observation_rows(historical_rows, warmup_rows=None):
    reset_observation_state()

    statistics_engine = StatisticsEngine()
    renko_engine = RenkoEngine()
    observation_rows = []

    for row in warmup_rows or []:
        process_historical_row(
            row=row,
            statistics_engine=statistics_engine,
            renko_engine=renko_engine,
        )

    for row in historical_rows:
        row, statistics = process_historical_row(
            row=row,
            statistics_engine=statistics_engine,
            renko_engine=renko_engine,
        )

        observation_rows.append(
            build_observation_row(
                row=row,
                statistics=statistics,
                row_id=row["row_id"],
            )
        )

    return observation_rows


def process_historical_row(row, statistics_engine, renko_engine):
    row = dict(row)
    update_history(row)
    row["adaptive_window"] = calculate_adaptive_window(
        row["velocity"],
        velocity_history,
    )

    context = SimpleNamespace(row=row)
    renko_engine.process(context)
    statistics = statistics_engine.process(context)

    return context.row, statistics


def build_observation_row(row, statistics, row_id):
    observation_row = {
        "row_id": row_id,
        "market_timestamp": get_market_timestamp(row),
        "close": get_value(row, "close"),
        "volume": get_value(row, "volume"),
        "delta": get_value(row, "delta"),
        "velocity": get_value(row, "velocity"),
        "rvi": get_value(row, "rvi"),
        "price_zone": get_value(row, "price_zone"),
        "volume_zone": get_value(row, "volume_zone"),
        "delta_zone": get_value(row, "delta_zone"),
        "velocity_zone": get_value(row, "velocity_zone"),
        "price_zscore": get_value(statistics, "price_zscore"),
        "volume_zscore": get_value(statistics, "volume_zscore"),
        "velocity_zscore": get_value(statistics, "velocity_zscore"),
        "spread_zscore": get_value(statistics, "spread_zscore"),
        "price_percentile_zone": get_value(
            statistics,
            "price_percentile_zone",
        ),
        "distribution_shift_state": get_value(
            statistics,
            "distribution_shift_state",
        ),
        "distribution_shift_strength": get_value(
            statistics,
            "distribution_shift_strength",
        ),
        "price_mean_shift": get_value(statistics, "price_mean_shift"),
        "price_std_shift": get_value(statistics, "price_std_shift"),
        "gaussian_extreme": get_value(statistics, "gaussian_extreme"),
        "gaussian_zone": get_value(statistics, "gaussian_zone"),
        "gaussian_tail": get_value(statistics, "gaussian_tail"),
        "gaussian_confidence": get_value(statistics, "gaussian_confidence"),
        "price_tail_risk": get_value(statistics, "price_tail_risk"),
        "price_tail_persistence": get_value(
            statistics,
            "price_tail_persistence",
        ),
        "price_tail_exhaustion": get_value(
            statistics,
            "price_tail_exhaustion",
        ),
        "price_tail_strength": get_value(statistics, "price_tail_strength"),
        "price_tail_side": get_value(statistics, "price_tail_side"),
        "volatility_regime": get_value(statistics, "volatility_regime"),
        "volatility_transition": get_value(
            statistics,
            "volatility_transition",
        ),
        "volatility_acceleration": get_value(
            statistics,
            "volatility_acceleration",
        ),
        "volume_state": get_value(statistics, "volume_state"),
        "volume_expansion": get_value(statistics, "volume_expansion"),
        "abnormal_volume": get_value(statistics, "abnormal_volume"),
        "velocity_state": get_value(statistics, "velocity_state"),
        "velocity_acceleration_state": get_value(
            statistics,
            "velocity_acceleration_state",
        ),
        "velocity_deceleration": get_value(
            statistics,
            "velocity_deceleration",
        ),
        "velocity_exhaustion_state": get_value(
            statistics,
            "velocity_exhaustion_state",
        ),
        "exhaustion_strength": get_value(statistics, "exhaustion_strength"),
        "delta_pressure_state": get_value(
            statistics,
            "delta_pressure_state",
        ),
        "delta_exhaustion": get_value(statistics, "delta_exhaustion"),
        "imbalance_state": get_value(statistics, "imbalance_state"),
        "aggressive_flow": get_value(statistics, "aggressive_flow"),
        "delta_acceleration_state": get_value(
            statistics,
            "delta_acceleration_state",
        ),
        "spread_state": get_value(statistics, "spread_state"),
        "spread_expansion": get_value(statistics, "spread_expansion"),
        "execution_quality": get_value(statistics, "execution_quality"),
        "distribution_shift": get_value(statistics, "distribution_shift"),
        "climactic_volume": get_value(statistics, "climactic_volume"),
        "velocity_shock": get_value(statistics, "velocity_shock"),
        "velocity_exhaustion": get_value(statistics, "velocity_exhaustion"),
        "abnormal_spread": get_value(statistics, "abnormal_spread"),
        "delta_zscore": get_value(statistics, "delta_zscore"),
        "price_extreme_event": get_value(statistics, "price_extreme_event"),
        "volume_extreme_event": get_value(statistics, "volume_extreme_event"),
        "delta_extreme_event": get_value(statistics, "delta_extreme_event"),
        "velocity_extreme_event": get_value(
            statistics,
            "velocity_extreme_event",
        ),
        "spread_extreme_event": get_value(statistics, "spread_extreme_event"),
        "extreme_event_state": get_value(statistics, "extreme_event_state"),
        "extreme_event_context": get_value(
            statistics,
            "extreme_event_context",
        ),
        "extreme_event_origin": get_value(
            statistics,
            "extreme_event_origin",
        ),
        "statistical_dashboard_state": get_value(
            statistics,
            "statistical_dashboard_state",
        ),
        "statistical_dashboard_score": get_value(
            statistics,
            "statistical_dashboard_score",
        ),
        "statistical_dashboard_conditions": format_conditions(
            get_value(
                statistics,
                "statistical_dashboard_conditions",
                [],
            )
        ),
    }

    for field in DASHBOARD_V2_ARCHIVE_FIELDS:
        value = get_value(row, field)

        if value is None:
            value = get_value(statistics, field, "")

        observation_row[field] = format_conditions(value)

    return observation_row


def reset_observation_state():
    price_history.clear()
    volume_history.clear()
    delta_history.clear()
    velocity_history.clear()
    system_state["row_counter"] = 0

    renko_state["last_brick_close"] = None
    renko_state["direction"] = "NEUTRAL"
    renko_state["brick_count"] = 0

    import core.statistics as statistics_module

    for name in [
        "price_distribution",
        "volume_distribution",
        "delta_distribution",
        "velocity_distribution",
        "spread_distribution",
        "tail_history",
        "volatility_regime_history",
        "volatility_ratio_history",
        "cumulative_delta_history",
        "delta_pressure_history",
        "delta_acceleration_history",
    ]:
        getattr(statistics_module, name).clear()


def agg_trade_to_tick(trade):
    price = float(trade["p"])
    quantity = float(trade["q"])
    timestamp = int(trade["T"])
    buyer_is_maker = bool(trade["m"])

    return {
        "price": price,
        "quantity": quantity,
        "timestamp": timestamp,
        "side": "SELL" if buyer_is_maker else "BUY",
    }


def parse_datetime_to_ms(value):
    text = value.strip()

    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise SystemExit(
            "Datetime must use YYYY-MM-DD HH:MM:SS"
        ) from error

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)

    return int(parsed.timestamp() * 1000)


def load_matching_checkpoint(symbol, start_date, end_date):
    if not HISTORICAL_DOWNLOAD_CHECKPOINT_FILE.exists():
        return None

    try:
        checkpoint = json.loads(
            HISTORICAL_DOWNLOAD_CHECKPOINT_FILE.read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError):
        return None

    if (
        str(checkpoint.get("symbol", "")).upper() == symbol.upper()
        and checkpoint.get("start_date") == start_date
        and checkpoint.get("end_date") == end_date
    ):
        if (
            int(checkpoint.get("downloaded_count") or 0) > 0
            and not HISTORICAL_DOWNLOAD_PARTIAL_FILE.exists()
        ):
            print(
                "Checkpoint found but partial download file is missing. "
                "Starting from the beginning."
            )
            return None
        return checkpoint

    return None


def save_download_checkpoint(
    symbol,
    start_date,
    end_date,
    last_success_timestamp,
    last_success_agg_trade_id,
    downloaded_count,
):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "symbol": symbol.upper(),
        "start_date": start_date,
        "end_date": end_date,
        "last_success_timestamp": last_success_timestamp,
        "last_success_agg_trade_id": last_success_agg_trade_id,
        "downloaded_count": downloaded_count,
    }
    HISTORICAL_DOWNLOAD_CHECKPOINT_FILE.write_text(
        json.dumps(checkpoint, indent=2),
        encoding="utf-8",
    )


def clear_download_checkpoint():
    for path in [
        HISTORICAL_DOWNLOAD_CHECKPOINT_FILE,
        HISTORICAL_DOWNLOAD_PARTIAL_FILE,
    ]:
        if path.exists():
            path.unlink()


def append_partial_agg_trades(batch):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with HISTORICAL_DOWNLOAD_PARTIAL_FILE.open("a", encoding="utf-8") as handle:
        for trade in batch:
            handle.write(json.dumps(trade, separators=(",", ":")) + "\n")


def load_partial_agg_trades():
    if not HISTORICAL_DOWNLOAD_PARTIAL_FILE.exists():
        return []

    trades = []
    with HISTORICAL_DOWNLOAD_PARTIAL_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                trades.append(json.loads(line))
    return trades


def get_agg_trade_id(trade):
    return trade.get("a") or trade.get("aggTradeId") or trade.get("id")


def ensure_outputs_can_be_written(overwrite, save_raw, resume_active=False):
    output_files = [
        HISTORICAL_MARKET_ROWS_FILE,
        HISTORICAL_OBSERVATION_ROWS_FILE,
        HISTORICAL_REPLAY_EVENTS_FILE,
        HISTORICAL_REPLAY_EPISODES_FILE,
        HISTORICAL_REPLAY_V2_EVENTS_FILE,
        HISTORICAL_REPLAY_V2_EPISODES_FILE,
    ]

    if save_raw:
        output_files.append(HISTORICAL_RAW_AGGTRADES_FILE)

    existing_files = [
        path
        for path in output_files
        if path.exists()
    ]

    if existing_files and not overwrite and not resume_active:
        existing = "\n".join(str(path) for path in existing_files)
        raise SystemExit(
            "Historical output files already exist. "
            "Use --overwrite to replace them:\n"
            f"{existing}"
        )


def write_raw_agg_trades(agg_trades):
    fieldnames = get_union_fieldnames(agg_trades)
    write_dict_rows(
        HISTORICAL_RAW_AGGTRADES_FILE,
        fieldnames,
        agg_trades,
    )


def get_union_fieldnames(rows):
    fieldnames = []

    for row in rows:
        for field in row:
            if field not in fieldnames:
                fieldnames.append(field)

    return fieldnames


def sleep_before_retry(attempt, error):
    sleep_seconds = RETRY_BACKOFF_SECONDS[
        min(attempt - 1, len(RETRY_BACKOFF_SECONDS) - 1)
    ]
    print(
        "Download retry: "
        f"attempt {attempt}/{MAX_RETRIES} | "
        f"sleep {sleep_seconds}s | error: {type(error).__name__}: {error}"
    )
    time.sleep(sleep_seconds)


def get_market_timestamp(row):
    return (
        get_value(row, "market_timestamp")
        or get_value(row, "end_ts")
        or get_value(row, "timestamp")
        or get_value(row, "start_ts")
    )


def format_conditions(value):
    if value is None:
        return ""

    if isinstance(value, list):
        return "|".join(str(item) for item in value)

    return str(value)


def get_value(source, key, default=None):
    if source is None:
        return default

    if isinstance(source, dict):
        return source.get(key, default)

    return getattr(source, key, default)


if __name__ == "__main__":
    main()

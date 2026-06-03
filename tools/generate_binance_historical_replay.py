import argparse
import calendar
import json
import random
import socket
import sys
import time
from datetime import date, datetime, timedelta, timezone
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
ARCHIVE_DIR = Path("archives")

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
ARCHIVE_MANIFEST_FILE_NAME = "manifest.json"
ARCHIVE_INDEX_FILE_NAME = "archive_index.json"

REQUEST_LIMIT = 1000
REQUEST_SLEEP_SECONDS = 0.5
REQUEST_TIMEOUT_SECONDS = 150          # raised from 120 — WinError 10060 needs more margin
MAX_RETRIES = 15                       # raised from 10 — extra tolerance for flaky networks
RETRY_BACKOFF_SECONDS = [10, 20, 40, 80, 120, 180, 240, 300]  # longer ramp; capped at 300s
RETRY_JITTER_FACTOR   = 0.30          # add up to ±30% random jitter to each backoff delay
WARMUP_TARGET_ROWS = 500
WARMUP_LOOKBACK_MS = 24 * 60 * 60 * 1000


# ==================================================
# DOWNLOAD DIAGNOSTICS — helpers
# Visibility only.  No logic changes.
# ==================================================

def _fmt_dur(seconds: float) -> str:
    """Format a duration in seconds as HH:MM:SS."""
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def _fmt_ts(ms: int) -> str:
    """Convert a Unix-millisecond timestamp to a compact UTC string."""
    try:
        from datetime import datetime, timezone
        dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return str(ms)


def _fmt_speed(trades: int, elapsed_s: float) -> str:
    """Return a human-readable trades/second string."""
    if elapsed_s <= 0:
        return "—"
    speed = trades / elapsed_s
    if speed >= 1000:
        return f"{speed / 1000:.1f}k t/s"
    return f"{speed:.0f} t/s"


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
    parser.add_argument("--overwrite-archive", action="store_true")
    parser.add_argument(
        "--max-retries",
        type=int,
        default=MAX_RETRIES,
        help=f"Max retry attempts per request batch (default: {MAX_RETRIES})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=REQUEST_TIMEOUT_SECONDS,
        help=f"HTTP timeout in seconds per request (default: {REQUEST_TIMEOUT_SECONDS})",
    )
    return parser.parse_args()


def main():
    profiler = PerfProfiler("historical_replay_generation")
    args = parse_args()

    # Apply CLI overrides to module-level retry/timeout constants so that
    # sleep_before_retry and fetch_agg_trades_batch_with_retries pick them up.
    global MAX_RETRIES, REQUEST_TIMEOUT_SECONDS
    if args.max_retries != MAX_RETRIES:
        print(f"max_retries overridden: {args.max_retries} (default={MAX_RETRIES})")
        MAX_RETRIES = args.max_retries
    if args.timeout != REQUEST_TIMEOUT_SECONDS:
        print(f"timeout overridden: {args.timeout}s (default={REQUEST_TIMEOUT_SECONDS}s)")
        REQUEST_TIMEOUT_SECONDS = args.timeout

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

        verify_downloaded_trades(agg_trades)

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

        with profiler.step("archive_historical_outputs"):
            archive_summary = archive_historical_outputs(
                symbol=args.symbol,
                start_date=args.start,
                end_date=args.end,
                save_raw=args.save_raw,
                overwrite_archive=args.overwrite_archive,
            )

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
        profiler.add_metric("archive_days", archive_summary["archive_days"])
        profiler.add_metric("archive_files_written", archive_summary["files_written"])

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
        print(
            "Archived historical market dates: "
            f"{archive_summary['archive_days']} | "
            f"files written: {archive_summary['files_written']}"
        )
        print(f"Archive index: {archive_summary['archive_index']}")
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

    # ── Session-level diagnostic state ──────────────────────────────────────
    session_start    = time.perf_counter()
    request_num      = 0                 # batch counter (1-indexed in output)
    session_retries  = 0                 # total retry events this session
    total_range_ms   = max(end_ms - start_ms, 1)
    _speed_window: list = []
    _SPEED_WINDOW_SIZE  = 10
    _CHECKPOINT_LOG_INTERVAL = 25        # emit full checkpoint line every N batches
    # ────────────────────────────────────────────────────────────────────────

    if checkpoint:
        last_success_timestamp = checkpoint.get("last_success_timestamp")
        if last_success_timestamp is not None:
            current_start_ms = int(last_success_timestamp) + 1
            # Deduplicate partial trades by aggTrade ID to guard against
            # edge-case double-writes at crash boundaries.
            if trades:
                seen_ids = set()
                deduped  = []
                for t in trades:
                    tid = get_agg_trade_id(t)
                    if tid not in seen_ids:
                        seen_ids.add(tid)
                        deduped.append(t)
                dup_count = len(trades) - len(deduped)
                if dup_count:
                    print(f"RESUME | removed {dup_count} duplicate trade(s) from partial file")
                trades = deduped
            print(
                f"RESUME | from {_fmt_ts(current_start_ms)} | "
                f"already have {len(trades):,} trades | "
                f"checkpoint={HISTORICAL_DOWNLOAD_CHECKPOINT_FILE}"
            )
        else:
            print("RESUME | checkpoint found but no timestamp — starting fresh")
    else:
        print(
            f"DOWNLOAD START | {start_date} -> {end_date} | "
            f"range={_fmt_ts(start_ms)} -> {_fmt_ts(end_ms)} | "
            f"max_retries={MAX_RETRIES} | timeout={REQUEST_TIMEOUT_SECONDS}s"
        )

    while current_start_ms <= end_ms:
        request_num += 1
        batch_wall_start = time.perf_counter()

        batch, retries_used = fetch_agg_trades_batch_with_retries(
            symbol=symbol,
            start_ms=current_start_ms,
            end_ms=end_ms,
            profiler=profiler,
            request_num=request_num,
        )
        session_retries += retries_used

        batch_wall_elapsed = time.perf_counter() - batch_wall_start
        if profiler:
            profiler.record("download_batch", batch_wall_elapsed)

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
            elapsed = time.perf_counter() - session_start
            print(
                f"\nDOWNLOAD PAUSED after REQ {request_num} | "
                f"elapsed={_fmt_dur(elapsed)} | "
                f"trades_so_far={len(trades):,} | "
                f"session_retries={session_retries} | "
                f"checkpoint={HISTORICAL_DOWNLOAD_CHECKPOINT_FILE} | "
                f"Re-run the same command to resume."
            )
            return None

        if not batch:
            break

        # ── Update in-memory and on-disk state ───────────────────────────────
        trades.extend(batch)
        append_partial_agg_trades(batch)

        last_timestamp = int(batch[-1]["T"])
        last_trade_id  = get_agg_trade_id(batch[-1])
        save_download_checkpoint(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            last_success_timestamp=last_timestamp,
            last_success_agg_trade_id=last_trade_id,
            downloaded_count=len(trades),
        )

        # ── Rolling speed calculation ────────────────────────────────────────
        _speed_window.append((len(batch), batch_wall_elapsed))
        if len(_speed_window) > _SPEED_WINDOW_SIZE:
            _speed_window.pop(0)
        window_trades  = sum(t for t, _ in _speed_window)
        window_seconds = sum(s for _, s in _speed_window)
        speed_str      = _fmt_speed(window_trades, window_seconds)

        # ── Progress estimate ────────────────────────────────────────────────
        elapsed_total = time.perf_counter() - session_start
        done_ms       = last_timestamp - start_ms
        pct           = min(done_ms / total_range_ms * 100, 100.0)
        if pct > 0 and elapsed_total > 0:
            remaining_ms  = total_range_ms - done_ms
            ms_per_second = done_ms / elapsed_total
            eta_seconds   = remaining_ms / ms_per_second if ms_per_second > 0 else 0
            eta_str       = _fmt_dur(eta_seconds)
        else:
            eta_str = "calculating..."

        retry_tag = f" | retries={session_retries}" if session_retries else ""
        print(
            f"  BATCH {request_num} | trades={len(trades):,} | "
            f"speed={speed_str} | elapsed={_fmt_dur(elapsed_total)} | "
            f"eta={eta_str} | {pct:.1f}% | "
            f"ts={_fmt_ts(last_timestamp)} | last_id={last_trade_id}"
            f"{retry_tag}"
        )

        # ── Periodic full checkpoint log ──────────────────────────────────────
        if request_num % _CHECKPOINT_LOG_INTERVAL == 0:
            print(
                f"  --- CHECKPOINT LOG ---\n"
                f"    trades_downloaded : {len(trades):,}\n"
                f"    current_timestamp : {_fmt_ts(last_timestamp)}\n"
                f"    last_aggtrade_id  : {last_trade_id}\n"
                f"    session_retries   : {session_retries}\n"
                f"    elapsed           : {_fmt_dur(elapsed_total)}\n"
                f"    eta               : {eta_str}\n"
                f"    checkpoint_file   : {HISTORICAL_DOWNLOAD_CHECKPOINT_FILE}\n"
                f"    partial_file      : {HISTORICAL_DOWNLOAD_PARTIAL_FILE}"
            )
        # ────────────────────────────────────────────────────────────────────

        if last_timestamp >= end_ms:
            break

        next_start_ms = last_timestamp + 1
        if next_start_ms <= current_start_ms:
            break
        current_start_ms = next_start_ms

        time.sleep(REQUEST_SLEEP_SECONDS)

    elapsed_total = time.perf_counter() - session_start
    print(
        f"\nDOWNLOAD COMPLETE | {len(trades):,} trades | "
        f"elapsed={_fmt_dur(elapsed_total)} | "
        f"avg_speed={_fmt_speed(len(trades), elapsed_total)} | "
        f"session_retries={session_retries}"
    )
    return trades


def fetch_agg_trades_batch_with_retries(
    symbol, start_ms, end_ms, profiler=None, request_num=None
):
    """Fetch one batch of aggTrades.

    Returns a tuple (batch_or_none, retries_used):
      batch_or_none  — list of trades on success, None when all retries exhaust
      retries_used   — number of retry attempts made (0 = first-attempt success)
    """
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

    req_tag = f"REQ {request_num}" if request_num is not None else "REQ"
    retries_used = 0

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            http_start = time.perf_counter()
            with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                payload = response.read()
            elapsed = time.perf_counter() - http_start

            if profiler:
                profiler.record("http_wait", elapsed)

            parse_start = time.perf_counter()
            decoded = payload.decode("utf-8")
            parsed  = json.loads(decoded)

            if profiler:
                profiler.record("parse_batch", time.perf_counter() - parse_start)

            trade_count = len(parsed) if isinstance(parsed, list) else 0
            retry_tag   = f" | after {retries_used} retry(ies)" if retries_used else ""
            print(
                f"{req_tag} | HTTP 200 | {elapsed:.3f}s | "
                f"{trade_count} trades | ts={_fmt_ts(start_ms)}"
                f"{retry_tag}"
            )
            return parsed, retries_used

        except HTTPError as error:
            if error.code in [429, 418, 500, 502, 503, 504]:
                retries_used += 1
                sleep_before_retry(attempt, error, request_num=request_num)
                continue
            # Non-retryable HTTP error — surface immediately
            print(
                f"{req_tag} | HTTP {error.code} — {error.reason} | "
                f"ts={_fmt_ts(start_ms)} | NOT retrying (fatal HTTP error)"
            )
            raise
        except (TimeoutError, socket.timeout, URLError) as error:
            retries_used += 1
            sleep_before_retry(attempt, error, request_num=request_num)

    # All retries exhausted
    print(
        f"{req_tag} | ALL {MAX_RETRIES} RETRIES EXHAUSTED | "
        f"ts={_fmt_ts(start_ms)} | download will pause"
    )
    return None, retries_used


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


def archive_historical_outputs(
    symbol,
    start_date,
    end_date,
    save_raw=False,
    overwrite_archive=False,
):
    symbol = symbol.upper()
    archive_root = ARCHIVE_DIR / symbol
    archive_root.mkdir(parents=True, exist_ok=True)

    source_files = get_archive_source_files(save_raw=save_raw)
    archive_targets_by_date = {}
    manifest_data_by_date = {}
    files_written = 0

    for source_file, timestamp_candidates in source_files:
        if not source_file.exists():
            continue

        dataframe = pd.read_csv(source_file)
        if dataframe.empty:
            continue

        timestamp_column = find_existing_column(dataframe, timestamp_candidates)
        if timestamp_column is None:
            print(
                "Archive skipped file without timestamp column: "
                f"{source_file}"
            )
            continue

        dataframe = dataframe.copy()
        dataframe["_archive_market_date"] = convert_to_market_dates(
            dataframe[timestamp_column]
        )
        dataframe = dataframe.dropna(subset=["_archive_market_date"])

        for market_date, daily_dataframe in dataframe.groupby("_archive_market_date"):
            market_date = str(market_date)
            archive_path = archive_targets_by_date.get(market_date)

            if archive_path is None:
                archive_path = resolve_archive_day_path(
                    archive_root=archive_root,
                    market_date=market_date,
                    overwrite_archive=overwrite_archive,
                )
                archive_path.mkdir(parents=True, exist_ok=True)
                archive_targets_by_date[market_date] = archive_path
                manifest_data_by_date[market_date] = create_archive_manifest(
                    symbol=symbol,
                    market_date=market_date,
                    start_date=start_date,
                    end_date=end_date,
                    archive_path=archive_path,
                )

            output_dataframe = daily_dataframe.drop(
                columns=["_archive_market_date"],
                errors="ignore",
            )
            archive_file = archive_path / source_file.name
            output_dataframe.to_csv(archive_file, index=False)
            files_written += 1

            update_archive_manifest_file_stats(
                manifest=manifest_data_by_date[market_date],
                source_file=source_file,
                archive_file=archive_file,
                row_count=len(output_dataframe),
            )

    for market_date, manifest in manifest_data_by_date.items():
        manifest_path = Path(manifest["archive_path"]) / ARCHIVE_MANIFEST_FILE_NAME
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    archive_index_path = rebuild_archive_index(archive_root)

    return {
        "archive_days": len(manifest_data_by_date),
        "files_written": files_written,
        "archive_index": str(archive_index_path),
    }


def get_archive_source_files(save_raw=False):
    source_files = [
        (
            HISTORICAL_MARKET_ROWS_FILE,
            ["market_timestamp", "end_ts", "timestamp", "start_ts"],
        ),
        (
            HISTORICAL_OBSERVATION_ROWS_FILE,
            ["market_timestamp", "end_ts", "timestamp", "start_ts"],
        ),
        (
            HISTORICAL_REPLAY_EVENTS_FILE,
            ["market_timestamp", "event_timestamp_utc", "timestamp"],
        ),
        (
            HISTORICAL_REPLAY_EPISODES_FILE,
            [
                "episode_start_timestamp_utc",
                "episode_start_time_utc",
                "start_timestamp",
                "timestamp",
            ],
        ),
        (
            HISTORICAL_REPLAY_V2_EVENTS_FILE,
            ["market_timestamp", "event_timestamp_utc", "timestamp"],
        ),
        (
            HISTORICAL_REPLAY_V2_EPISODES_FILE,
            [
                "episode_start_timestamp_utc",
                "episode_start_time_utc",
                "start_timestamp",
                "timestamp",
            ],
        ),
    ]

    if save_raw:
        source_files.append(
            (
                HISTORICAL_RAW_AGGTRADES_FILE,
                ["T", "timestamp", "market_timestamp"],
            )
        )

    return source_files


def find_existing_column(dataframe, candidates):
    for candidate in candidates:
        if candidate in dataframe.columns:
            return candidate
    return None


def convert_to_market_dates(series):
    numeric_values = pd.to_numeric(series, errors="coerce")

    if numeric_values.notna().any():
        datetime_values = pd.to_datetime(
            numeric_values,
            unit="ms",
            utc=True,
            errors="coerce",
        )
    else:
        datetime_values = pd.to_datetime(series, utc=True, errors="coerce")

    return datetime_values.dt.strftime("%Y-%m-%d")


def resolve_archive_day_path(archive_root, market_date, overwrite_archive=False):
    market_day = date.fromisoformat(market_date)
    window_start, window_end = ten_day_window_for_date(market_day)
    window_name = f"{window_start.isoformat()}_to_{window_end.isoformat()}"
    day_root = archive_root / window_name / market_date

    if overwrite_archive or not day_root.exists() or is_empty_archive_day(day_root):
        return day_root

    return next_archive_run_path(day_root)


def ten_day_window_for_date(market_day):
    if market_day.day <= 9 and previous_month_has_day_31(market_day):
        if market_day.month == 1:
            return date(market_day.year - 1, 12, 31), date(market_day.year, 1, 9)
        return (
            date(market_day.year, market_day.month - 1, 31),
            date(market_day.year, market_day.month - 1, 31) + timedelta(days=9),
        )

    if previous_month_has_day_31(market_day):
        start_day = ((market_day.day - 10) // 10) * 10 + 10
    else:
        start_day = ((market_day.day - 1) // 10) * 10 + 1

    start_day = max(1, min(start_day, calendar.monthrange(market_day.year, market_day.month)[1]))
    window_start = date(market_day.year, market_day.month, start_day)
    return window_start, window_start + timedelta(days=9)


def previous_month_has_day_31(market_day):
    if market_day.month == 1:
        previous_year = market_day.year - 1
        previous_month = 12
    else:
        previous_year = market_day.year
        previous_month = market_day.month - 1

    return calendar.monthrange(previous_year, previous_month)[1] == 31


def is_empty_archive_day(day_root):
    if not day_root.exists():
        return True

    return not any(day_root.iterdir())


def next_archive_run_path(day_root):
    run_index = 1

    while True:
        run_path = day_root / f"run_{run_index:03d}"

        if not run_path.exists():
            return run_path

        run_index += 1


def create_archive_manifest(symbol, market_date, start_date, end_date, archive_path):
    source_command = " ".join(sys.argv)

    return {
        "symbol": symbol,
        "market_date": market_date,
        "batch_window": {
            "start": start_date,
            "end": end_date,
        },
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "source_command": source_command,
        "row_counts": {},
        "event_counts": {},
        "episode_counts": {},
        "file_sizes": {},
        "archive_path": str(archive_path),
    }


def update_archive_manifest_file_stats(manifest, source_file, archive_file, row_count):
    file_name = source_file.name
    manifest["row_counts"][file_name] = int(row_count)
    manifest["file_sizes"][file_name] = int(archive_file.stat().st_size)

    if "events" in file_name:
        manifest["event_counts"][file_name] = int(row_count)

    if "episodes" in file_name:
        manifest["episode_counts"][file_name] = int(row_count)


def rebuild_archive_index(archive_root):
    archive_root.mkdir(parents=True, exist_ok=True)
    index_path = archive_root / ARCHIVE_INDEX_FILE_NAME
    entries = []

    for manifest_path in archive_root.rglob(ARCHIVE_MANIFEST_FILE_NAME):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        relative_parts = manifest_path.relative_to(archive_root).parts

        entries.append(
            {
                "market_date": manifest.get("market_date"),
                "batch_window": manifest.get("batch_window", {}),
                "archive_path": manifest.get("archive_path"),
                "manifest_path": str(manifest_path),
                "created_at": manifest.get("created_at"),
                "parent_window": relative_parts[0] if relative_parts else "",
            }
        )

    entries = sorted(
        entries,
        key=lambda item: (
            item.get("market_date") or "",
            item.get("archive_path") or "",
        ),
    )
    index = {
        "symbol": archive_root.name,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "available_dates": entries,
    }
    index_path.write_text(
        json.dumps(index, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return index_path


def get_union_fieldnames(rows):
    fieldnames = []

    for row in rows:
        for field in row:
            if field not in fieldnames:
                fieldnames.append(field)

    return fieldnames


def verify_downloaded_trades(trades):
    """Print final verification stats for the downloaded aggTrades list.

    Called once after the download loop completes successfully, before the
    replay pipeline runs.  Does not modify any data.
    """
    print()
    print("=" * 60)
    print("DOWNLOAD VERIFICATION")
    if not trades:
        print("  WARNING: trades list is empty — nothing to verify")
        print("=" * 60)
        return

    trade_ids = [get_agg_trade_id(t) for t in trades]
    valid_ids  = [tid for tid in trade_ids if tid is not None]
    dup_count  = len(valid_ids) - len(set(valid_ids))

    first_ts = int(trades[0]["T"])
    last_ts  = int(trades[-1]["T"])

    print(f"  Total trades      : {len(trades):,}")
    print(f"  First timestamp   : {_fmt_ts(first_ts)}")
    print(f"  Last timestamp    : {_fmt_ts(last_ts)}")
    print(f"  Duplicate trade IDs: {dup_count}")
    if dup_count:
        print(f"  WARNING: {dup_count} duplicate aggTrade IDs found — "
              f"check {HISTORICAL_DOWNLOAD_PARTIAL_FILE}")
    else:
        print("  Duplicate check   : PASSED (0 duplicates)")
    print(f"  Partial file      : {HISTORICAL_DOWNLOAD_PARTIAL_FILE}")
    print(f"  Checkpoint file   : {HISTORICAL_DOWNLOAD_CHECKPOINT_FILE}")
    print("=" * 60)
    print()


def sleep_before_retry(attempt, error, request_num=None):
    base_seconds = RETRY_BACKOFF_SECONDS[
        min(attempt - 1, len(RETRY_BACKOFF_SECONDS) - 1)
    ]

    # Classify error type.  Detect WinError 10060 (WSAETIMEDOUT) explicitly
    # because it appears wrapped inside URLError on Windows and needs a longer
    # backoff than generic network errors.
    is_win_10060 = False
    if isinstance(error, HTTPError):
        http_code   = error.code
        reason      = _http_code_label(http_code)
        error_label = f"HTTP {http_code} — {reason}"
    elif isinstance(error, (TimeoutError, socket.timeout)):
        error_label = f"TIMEOUT (Python {REQUEST_TIMEOUT_SECONDS}s limit)"
    elif isinstance(error, URLError):
        reason_str = str(getattr(error, "reason", error))
        if "10060" in reason_str or "WinError 10060" in reason_str:
            is_win_10060 = True
            error_label  = "WinError 10060 — TCP connection timeout (Windows WSAETIMEDOUT)"
        else:
            error_label = f"NETWORK ERROR — {error.reason}"
    else:
        error_label = f"{type(error).__name__}: {error}"

    # For WinError 10060, multiply base by 1.5 — the OS-level TCP timeout
    # needs more recovery time than application-level rate limits.
    if is_win_10060:
        base_seconds = min(base_seconds * 1.5, 300)

    # Add random jitter to spread concurrent retries and avoid thundering herd.
    jitter         = random.uniform(0.0, base_seconds * RETRY_JITTER_FACTOR)
    sleep_seconds  = round(base_seconds + jitter, 1)

    req_tag = f"REQ {request_num} | " if request_num is not None else ""
    print(
        f"  {req_tag}RETRY {attempt}/{MAX_RETRIES} | "
        f"cause: {error_label} | "
        f"backoff: {sleep_seconds}s (base={int(base_seconds)}s + jitter={jitter:.1f}s)"
    )
    time.sleep(sleep_seconds)


def _http_code_label(code: int) -> str:
    """Return a short human-readable label for common HTTP error codes."""
    return {
        429: "Too Many Requests — rate limit hit",
        418: "IP Banned — Binance auto-ban",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
    }.get(code, f"Server Error")


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

"""
PoC: raw-trade replay parity check for 2026-06-11 00:00:00-00:35:49 UTC.

READ-ONLY w.r.t. outputs/ and research/. Writes only inside
archives/parity_poc/2026-06-11_raw_replay/.

Reuses build_trade_row() (core/row_builder.py) UNMODIFIED, and reuses the
existing historical-replay observation pipeline
(process_historical_row / build_observation_row / reset_observation_state
from tools/generate_binance_historical_replay.py) UNMODIFIED, feeding it
raw-trade-built rows instead of aggTrade-built rows.
"""

import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.row_builder import build_trade_row  # noqa: E402
from tools.generate_binance_historical_replay import (  # noqa: E402
    build_observation_row,
    process_historical_row,
    reset_observation_state,
)
from engines.statistics_engine import StatisticsEngine  # noqa: E402
from engines.renko_engine import RenkoEngine  # noqa: E402

POC_DIR = Path(__file__).resolve().parent
ZIP_PATH = POC_DIR / "raw_trades_cache" / "BTCUSDT-trades-2026-06-11.zip"
CSV_NAME = "BTCUSDT-trades-2026-06-11.csv"

START_US = 1781136000000000  # 2026-06-11 00:00:00.000000 UTC
END_US = 1781138149000000    # 2026-06-11 00:35:49.000000 UTC

ROW_SIZE = 500


def raw_trade_to_tick(parts):
    price = float(parts[1])
    quantity = float(parts[2])
    timestamp_ms = int(parts[4]) // 1000
    is_buyer_maker = parts[5] == "True"
    return {
        "price": price,
        "quantity": quantity,
        "timestamp": timestamp_ms,
        "side": "SELL" if is_buyer_maker else "BUY",
    }


def load_window_ticks():
    zf = zipfile.ZipFile(ZIP_PATH)
    ticks = []
    with zf.open(CSV_NAME) as f:
        for line in f:
            parts = line.decode().strip().split(",")
            t = int(parts[4])
            if t < START_US:
                continue
            if t > END_US:
                break
            ticks.append(raw_trade_to_tick(parts))
    return ticks


def build_raw_replay_rows(ticks, row_size=ROW_SIZE):
    rows = []
    for row_index, start in enumerate(range(0, len(ticks), row_size)):
        batch = ticks[start:start + row_size]
        if len(batch) < row_size:
            continue  # drop trailing partial row, same as full-row units elsewhere
        row = build_trade_row(batch)
        row["row_id"] = row_index + 1
        row["market_timestamp"] = row.get("end_ts")
        row["duration_seconds"] = row.get("duration_sec")
        rows.append(row)
    return rows


def build_observation_rows(raw_rows):
    reset_observation_state()
    statistics_engine = StatisticsEngine()
    renko_engine = RenkoEngine()

    observation_rows = []
    for row in raw_rows:
        row, statistics = process_historical_row(
            row=row,
            statistics_engine=statistics_engine,
            renko_engine=renko_engine,
        )
        observation_rows.append(
            build_observation_row(row=row, statistics=statistics, row_id=row["row_id"])
        )
    return observation_rows


def load_live_window():
    df = pd.read_csv(ROOT_DIR / "outputs" / "observation_rows.csv", low_memory=False)
    mask = (df["market_timestamp"] >= 1781136000000) & (df["market_timestamp"] <= 1781138149527)
    return df[mask].reset_index(drop=True)


def main():
    ticks = load_window_ticks()
    raw_rows = build_raw_replay_rows(ticks)
    poc_obs = pd.DataFrame(build_observation_rows(raw_rows))
    live_obs = load_live_window()

    poc_obs.to_csv(POC_DIR / "raw_replay_observation_rows.csv", index=False)

    report_lines = []
    report_lines.append("# Raw-Trade Replay Parity PoC -- 2026-06-11 00:00:00-00:35:49 UTC\n")
    report_lines.append("## Inputs\n")
    report_lines.append(f"- Raw trades in window: {len(ticks)}")
    report_lines.append(f"- PoC rows built (500 raw trades/row, full rows only): {len(poc_obs)}")
    report_lines.append(f"- LIVE rows in same market_timestamp window (observation_rows.csv): {len(live_obs)}\n")

    n = min(len(poc_obs), len(live_obs))
    report_lines.append(f"## Row-count comparison\n")
    report_lines.append(f"- PoC row count: {len(poc_obs)}")
    report_lines.append(f"- LIVE row count: {len(live_obs)}")
    report_lines.append(f"- Difference: {len(poc_obs) - len(live_obs)} ({(len(poc_obs)/len(live_obs)-1)*100:.2f}% )")
    report_lines.append(f"- Index-aligned rows compared (min): {n}\n")

    # OHLCV/delta/velocity comparison
    numeric_cols = ["close", "volume", "delta", "velocity"]
    report_lines.append("## OHLCV / delta / velocity comparison (tolerance: <1e-6 relative)\n")
    for col in numeric_cols:
        if col not in poc_obs.columns or col not in live_obs.columns:
            report_lines.append(f"- {col}: column missing, skipped")
            continue
        a = poc_obs[col].iloc[:n].astype(float).reset_index(drop=True)
        b = live_obs[col].iloc[:n].astype(float).reset_index(drop=True)
        rel_diff = ((a - b).abs() / b.abs().replace(0, 1e-12))
        within_tol = (rel_diff < 1e-6).sum()
        report_lines.append(
            f"- {col}: {within_tol}/{n} rows within tolerance "
            f"(max rel diff = {rel_diff.max():.6g}, mean rel diff = {rel_diff.mean():.6g})"
        )

    # z-score comparison
    zscore_cols = ["price_zscore", "volume_zscore", "velocity_zscore", "spread_zscore", "delta_zscore"]
    report_lines.append("\n## Z-score comparison (tolerance: <0.01 absolute)\n")
    for col in zscore_cols:
        if col not in poc_obs.columns or col not in live_obs.columns:
            report_lines.append(f"- {col}: column missing, skipped")
            continue
        a = pd.to_numeric(poc_obs[col].iloc[:n], errors="coerce").reset_index(drop=True)
        b = pd.to_numeric(live_obs[col].iloc[:n], errors="coerce").reset_index(drop=True)
        abs_diff = (a - b).abs()
        within_tol = (abs_diff < 0.01).sum()
        valid = abs_diff.notna().sum()
        report_lines.append(
            f"- {col}: {within_tol}/{valid} rows within tolerance "
            f"(max abs diff = {abs_diff.max():.6g}, mean abs diff = {abs_diff.mean():.6g})"
        )

    # categorical / layer comparison
    cat_cols = ["dashboard_v2_state", "dashboard_v2_layer_count", "dashboard_v2_active_layers", "extreme_event_state"]
    report_lines.append("\n## Layer / state comparison (tolerance: exact match)\n")
    for col in cat_cols:
        if col not in poc_obs.columns or col not in live_obs.columns:
            report_lines.append(f"- {col}: column missing, skipped")
            continue
        a = poc_obs[col].iloc[:n].astype(str).reset_index(drop=True)
        b = live_obs[col].iloc[:n].astype(str).reset_index(drop=True)
        match = (a == b).sum()
        report_lines.append(f"- {col}: {match}/{n} exact matches")

    # first divergence point for close price (cheap sanity index)
    a = poc_obs["close"].iloc[:n].astype(float).reset_index(drop=True)
    b = live_obs["close"].iloc[:n].astype(float).reset_index(drop=True)
    diverge_idx = None
    for i in range(n):
        if abs(a[i] - b[i]) / max(abs(b[i]), 1e-12) >= 1e-6:
            diverge_idx = i
            break
    report_lines.append(f"\n## First divergence (close price)\n")
    if diverge_idx is None:
        report_lines.append("- No divergence found within tolerance across all compared rows.")
    else:
        report_lines.append(
            f"- First divergence at index {diverge_idx} (PoC row_id={poc_obs['row_id'].iloc[diverge_idx]}, "
            f"LIVE row_id={live_obs['row_id'].iloc[diverge_idx]}): "
            f"PoC close={a[diverge_idx]} vs LIVE close={b[diverge_idx]}"
        )

    (POC_DIR / "parity_comparison_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    print("\n".join(report_lines))


if __name__ == "__main__":
    main()

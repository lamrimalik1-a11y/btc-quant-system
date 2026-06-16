"""
Merge archived per-day March 2026 BTCUSDT replay outputs into one
chronologically-ordered, globally re-indexed research dataset.

This is a March-period adaptation of merge_feb2026_archive.py, built to
regenerate the canonical checkpoint research dataset (originally produced
from a March 2026 run, then inadvertently overwritten by a February
research run with no backup of the downstream gitignored research/*.csv
files). March's raw replay data is archived as 31 separate single-calendar-
day folders spanning five overlapping ~10-day download windows under
archives/BTCUSDT/. Some episode_id/row_id numbering may reset across these
windows, so this script applies the same offset-based re-indexing used for
February (matching tools/run_backtesting_chunks.py's merge_chunks()
mechanism), and remaps start_row_id/end_row_id consistently with the new
row_id space (required because March's episodes have not yet passed through
episode research, and analyze_phase1b_episode_research.py looks rows up by
row_id).

Reads only from archives/. Writes only to a staging directory
(outputs/mar2026_merge_staging/). Does not download anything, does not call
the replay generator, does not touch raw aggtrades, does not modify any
formula, RDM, B12v2, Synthesis, Formation Model, or lifecycle logic.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = ROOT / "archives" / "BTCUSDT"
STAGING_DIR = ROOT / "outputs" / "mar2026_merge_staging"

MAR_DATES = [f"2026-03-{d:02d}" for d in range(1, 32)]

OBS_FILE = "historical_observation_rows.csv"
EP_FILE = "historical_replay_dashboard_v2_episodes.csv"

MAR_START = pd.Timestamp("2026-03-01 00:00:00", tz="UTC")
MAR_END = pd.Timestamp("2026-03-31 23:59:59.999999999", tz="UTC")


def find_day_archive(market_date: str) -> Path:
    """Locate the single archived day folder whose manifest.json market_date matches."""
    matches = []
    for manifest_path in ARCHIVE_ROOT.rglob("manifest.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if manifest.get("market_date") == market_date and manifest.get("symbol") == "BTCUSDT":
            matches.append(manifest_path.parent)

    if not matches:
        raise SystemExit(f"No archived day folder found for market_date={market_date}")
    if len(matches) > 1:
        raise SystemExit(f"Multiple archived day folders found for market_date={market_date}: {matches}")
    return matches[0]


def parse_market_timestamp(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().any():
        return pd.to_datetime(numeric, unit="ms", utc=True, errors="coerce")
    return pd.to_datetime(series, utc=True, errors="coerce")


def remap_row_id_column(series: pd.Series, mapping: dict[int, int]) -> pd.Series:
    def remap(value):
        if pd.isna(value):
            return value
        return mapping.get(int(value), value)

    return series.map(remap)


def main() -> None:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    day_paths = [(date, find_day_archive(date)) for date in MAR_DATES]

    obs_header: list[str] | None = None
    ep_header: list[str] | None = None
    obs_chunks: list[pd.DataFrame] = []
    ep_chunks: list[pd.DataFrame] = []

    next_row_id = 1
    next_episode_id = 1

    out_of_bounds_total = 0
    per_day_dup_total = 0
    log_lines: list[str] = []

    for date, path in day_paths:
        obs_df = pd.read_csv(path / OBS_FILE, low_memory=False)
        ep_df = pd.read_csv(path / EP_FILE, low_memory=False)

        if obs_header is None:
            obs_header = list(obs_df.columns)
        if ep_header is None:
            ep_header = list(ep_df.columns)

        # Enforce March-only boundary defensively (exclude Feb 28 / Apr 1 spillover).
        ts = parse_market_timestamp(obs_df["market_timestamp"])
        in_bounds = (ts >= MAR_START) & (ts <= MAR_END)
        out_of_bounds_total += int((~in_bounds).sum())
        obs_df = obs_df.loc[in_bounds].copy()

        # Defensive duplicate removal — identity must be the FULL row, not
        # market_timestamp: distinct aggregation rows can legitimately share
        # a millisecond-precision timestamp (different close/volume), and
        # such rows can be directly referenced by start_row_id/end_row_id.
        # A timestamp-only dedupe would both destroy real data and break
        # row_id referential integrity (lesson learned from the Feb merge).
        identity_cols = [c for c in obs_df.columns if c != "row_id"]
        before = len(obs_df)
        obs_df = obs_df.drop_duplicates(subset=identity_cols).copy()
        per_day_dup_total += before - len(obs_df)

        obs_df.sort_values("row_id", inplace=True)

        # ── Re-index row_id (offset-based, preserves existing continuity) ──
        local_min_row_id = int(obs_df["row_id"].min())
        row_offset = next_row_id - local_min_row_id
        old_row_ids = obs_df["row_id"].astype(int)
        new_row_ids = old_row_ids + row_offset
        row_id_map = dict(zip(old_row_ids.tolist(), new_row_ids.tolist()))
        obs_df["row_id"] = new_row_ids
        next_row_id = int(new_row_ids.max()) + 1

        # ── Re-index episode_id (offset-based) and remap start/end row refs ──
        ep_df.sort_values("episode_id", inplace=True)
        for col in ("start_row_id", "end_row_id"):
            if col in ep_df.columns:
                ep_df[col] = remap_row_id_column(ep_df[col], row_id_map)

        local_min_ep_id = int(ep_df["episode_id"].min())
        ep_offset = next_episode_id - local_min_ep_id
        old_ep_ids = ep_df["episode_id"].astype(int)
        new_ep_ids = old_ep_ids + ep_offset
        ep_df["episode_id"] = new_ep_ids
        next_episode_id = int(new_ep_ids.max()) + 1

        obs_chunks.append(obs_df)
        ep_chunks.append(ep_df)

        log_lines.append(
            f"{date}  obs={len(obs_df):>5} row_id[{int(new_row_ids.min()):>6}-{int(new_row_ids.max()):>6}]"
            f"  episodes={len(ep_df):>4} episode_id[{int(new_ep_ids.min()):>5}-{int(new_ep_ids.max()):>5}]"
            f"  (row_offset={row_offset:+d}, ep_offset={ep_offset:+d})"
        )

    assert obs_header is not None and ep_header is not None

    merged_obs = pd.concat(obs_chunks, ignore_index=True)[obs_header]
    merged_ep = pd.concat(ep_chunks, ignore_index=True)[ep_header]

    # Final cross-day duplicate pass — again full-row identity (excluding the
    # freshly-assigned row_id) since archived days are confirmed non-overlapping
    # single calendar days and market_timestamp alone is not a safe identity key.
    final_identity_cols = [c for c in merged_obs.columns if c != "row_id"]
    before_final = len(merged_obs)
    merged_obs = merged_obs.drop_duplicates(subset=final_identity_cols).reset_index(drop=True)
    final_dup_total = before_final - len(merged_obs)

    merged_obs.to_csv(STAGING_DIR / OBS_FILE, index=False)
    merged_ep.to_csv(STAGING_DIR / EP_FILE, index=False)

    # ── Verification ──────────────────────────────────────────────────────
    row_id_unique = bool(merged_obs["row_id"].is_unique)
    row_id_monotonic = bool(merged_obs["row_id"].is_monotonic_increasing)
    ep_id_unique = bool(merged_ep["episode_id"].is_unique)
    ep_id_monotonic = bool(merged_ep["episode_id"].is_monotonic_increasing)

    ts_all = parse_market_timestamp(merged_obs["market_timestamp"])
    ts_min, ts_max = ts_all.min(), ts_all.max()
    all_in_bounds = bool(((ts_all >= MAR_START) & (ts_all <= MAR_END)).all())

    valid_row_ids = set(merged_obs["row_id"].astype(int).tolist())
    bad_refs = 0
    for col in ("start_row_id", "end_row_id"):
        if col in merged_ep.columns:
            vals = pd.to_numeric(merged_ep[col], errors="coerce").dropna().astype(int)
            bad_refs += int((~vals.isin(valid_row_ids)).sum())

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    report = []
    report.append("# March 2026 Archive Merge — Verification Report\n\n")
    report.append(f"Generated: {generated_at}\n\n")
    report.append(f"Source: {len(day_paths)} archived day folders ({MAR_DATES[0]} .. {MAR_DATES[-1]})\n\n")
    report.append(f"Output staging dir: {STAGING_DIR.relative_to(ROOT)}\n\n")
    report.append("## Per-day merge log\n\n")
    report.append("```\n")
    report.extend(line + "\n" for line in log_lines)
    report.append("```\n\n")
    report.append("## Totals\n\n")
    report.append(f"- Observation rows merged: {len(merged_obs):,}\n")
    report.append(f"- Episodes merged: {len(merged_ep):,}\n\n")
    report.append("## Integrity checks\n\n")
    report.append(f"- row_id unique: {row_id_unique}\n")
    report.append(f"- row_id monotonic increasing: {row_id_monotonic}\n")
    report.append(f"- episode_id unique: {ep_id_unique}\n")
    report.append(f"- episode_id monotonic increasing: {ep_id_monotonic}\n")
    report.append(f"- timestamp range: [{ts_min} .. {ts_max}]\n")
    report.append(f"- all timestamps within Mar 1 00:00:00 .. Mar 31 23:59:59 bounds: {all_in_bounds}\n")
    report.append(f"- rows dropped as out-of-March-bounds: {out_of_bounds_total}\n")
    report.append(f"- duplicate rows removed (per-day pass): {per_day_dup_total}\n")
    report.append(f"- duplicate rows removed (cross-day pass): {final_dup_total}\n")
    report.append(f"- start_row_id/end_row_id references not resolving to a merged row_id: {bad_refs}\n")

    report_text = "".join(report)
    (STAGING_DIR / "merge_report.md").write_text(report_text, encoding="utf-8")
    print(report_text)


if __name__ == "__main__":
    main()

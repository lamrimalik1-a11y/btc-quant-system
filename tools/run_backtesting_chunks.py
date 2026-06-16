"""
Chunked backtesting dataset builder.

Processes 2026-04-30 -> 2026-06-03 in 3-day chunks to stay within
the memory envelope (each chunk loads ~3 × 650k = ~2M trades).

After all chunks complete, merges outputs into unified research files
with globally-unique case_ids and episode_ids, then runs the full
RDM pipeline (B1-B11 + Synthesis) once on the merged dataset.

Research only. No formulas, dashboard, RDM, lifecycle, or replay
logic is modified by this script.
"""
from __future__ import annotations

import csv
import gc
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT  = ROOT / "outputs"
RES  = ROOT / "research"
CHUNKS_DIR = ROOT / "outputs" / "backtesting_chunks"

CHUNKS: list[tuple[str, str]] = [
    ("2026-04-30 00:00:00", "2026-05-03 00:00:00"),
    ("2026-05-03 00:00:00", "2026-05-06 00:00:00"),
    ("2026-05-06 00:00:00", "2026-05-09 00:00:00"),
    ("2026-05-09 00:00:00", "2026-05-12 00:00:00"),
    ("2026-05-12 00:00:00", "2026-05-15 00:00:00"),
    ("2026-05-15 00:00:00", "2026-05-18 00:00:00"),
    ("2026-05-18 00:00:00", "2026-05-21 00:00:00"),
    ("2026-05-21 00:00:00", "2026-05-24 00:00:00"),
    ("2026-05-24 00:00:00", "2026-05-27 00:00:00"),
    ("2026-05-27 00:00:00", "2026-05-30 00:00:00"),
    ("2026-05-30 00:00:00", "2026-06-02 00:00:00"),
    ("2026-06-02 00:00:00", "2026-06-03 00:00:00"),
]

PYTHON = sys.executable


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def run(cmd: list[str], label: str) -> int:
    t0 = time.perf_counter()
    print(f"  RUN: {' '.join(cmd[1:])}")
    result = subprocess.run(cmd, capture_output=False, cwd=str(ROOT))
    elapsed = time.perf_counter() - t0
    if result.returncode != 0:
        print(f"  ERROR: {label} exited with code {result.returncode}")
    else:
        print(f"  OK ({elapsed:.0f}s): {label}")
    return result.returncode


def count_csv(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in open(path, encoding="utf-8")) - 1


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_chunk_outputs(chunk_dir: Path) -> None:
    """Save current pipeline outputs to the chunk's saved directory."""
    for fname in [
        "historical_observation_rows.csv",
        "historical_replay_dashboard_v2_episodes.csv",
        "historical_market_rows.csv",
    ]:
        src = OUT / fname
        if src.exists():
            copy_file(src, chunk_dir / fname)

    for fname in [
        "phase1b_episode_research_log.csv",
    ]:
        src = RES / fname
        if src.exists():
            copy_file(src, chunk_dir / fname)

    for fname in [
        "zone_lifecycle_events.jsonl",
        "field_lifecycle_events.jsonl",
    ]:
        src = RES / fname
        if src.exists():
            copy_file(src, chunk_dir / fname)


# ──────────────────────────────────────────────────────────────────────────────
# PHASE 1 — Process each chunk
# ──────────────────────────────────────────────────────────────────────────────

def process_chunks() -> list[Path]:
    chunk_dirs: list[Path] = []

    for i, (start, end) in enumerate(CHUNKS, start=1):
        label = f"Chunk {i:02d}/{len(CHUNKS)}: {start[:10]} -> {end[:10]}"
        chunk_dir = CHUNKS_DIR / f"chunk_{i:02d}"
        chunk_dir.mkdir(parents=True, exist_ok=True)

        # Skip if already completed
        marker = chunk_dir / "DONE"
        if marker.exists():
            print(f"\n[SKIP] {label} — already completed")
            chunk_dirs.append(chunk_dir)
            continue

        print(f"\n{'='*60}")
        print(f"[CHUNK {i:02d}] {label}")
        print(f"{'='*60}")

        # Step A: Historical replay
        rc = run([PYTHON, "tools/generate_binance_historical_replay.py",
                  "--start", start, "--end", end,
                  "--symbol", "BTCUSDT", "--row-size", "500", "--overwrite"],
                 "replay")
        if rc != 0:
            print(f"  FATAL: Replay failed for chunk {i}. Stopping.")
            sys.exit(1)

        obs_rows = count_csv(OUT / "historical_observation_rows.csv")
        eps_rows = count_csv(OUT / "historical_replay_dashboard_v2_episodes.csv")
        print(f"  Replay: {obs_rows:,} obs rows, {eps_rows:,} episodes")

        # Step B: Episode research
        rc = run([PYTHON, "tools/analyze_phase1b_episode_research.py",
                  "--mode", "score4plus"], "episode research")
        if rc != 0:
            print(f"  FATAL: Episode research failed for chunk {i}. Stopping.")
            sys.exit(1)

        log_rows = count_csv(RES / "phase1b_episode_research_log.csv")
        print(f"  Research: {log_rows:,} score4plus cases")

        # Save chunk outputs
        copy_chunk_outputs(chunk_dir)
        marker.write_text(
            json.dumps({"start": start, "end": end, "obs_rows": obs_rows,
                        "episodes": eps_rows, "cases": log_rows}),
            encoding="utf-8"
        )
        chunk_dirs.append(chunk_dir)
        gc.collect()

    return chunk_dirs


# ──────────────────────────────────────────────────────────────────────────────
# PHASE 2 — Merge all chunks
# ──────────────────────────────────────────────────────────────────────────────

def merge_chunks(chunk_dirs: list[Path]) -> dict:
    print(f"\n{'='*60}")
    print("[MERGE] Combining all chunks into unified research dataset")
    print(f"{'='*60}")

    # ── Merge observation rows ──────────────────────────────────────────────
    print("  Merging historical_observation_rows.csv...")
    obs_frames: list[list[str]] = []
    obs_header = None
    row_id_offset = 0

    for cdir in chunk_dirs:
        p = cdir / "historical_observation_rows.csv"
        if not p.exists():
            continue
        with p.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            if obs_header is None:
                obs_header = header
            row_id_col = header.index("row_id") if "row_id" in header else -1
            for row in reader:
                if row_id_col >= 0:
                    try:
                        row[row_id_col] = str(int(row[row_id_col]) + row_id_offset)
                    except ValueError:
                        pass
                obs_frames.append(row)
        if obs_frames and row_id_col >= 0:
            try:
                row_id_offset = int(obs_frames[-1][row_id_col]) + 1
            except (ValueError, IndexError):
                pass

    merged_obs = OUT / "historical_observation_rows.csv"
    with merged_obs.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(obs_header)
        writer.writerows(obs_frames)
    print(f"  -> {len(obs_frames):,} observation rows")

    # ── Merge episodes with re-indexed episode_id ───────────────────────────
    print("  Merging historical_replay_dashboard_v2_episodes.csv...")
    ep_frames: list[list[str]] = []
    ep_header = None
    ep_id_offset = 0

    for cdir in chunk_dirs:
        p = cdir / "historical_replay_dashboard_v2_episodes.csv"
        if not p.exists():
            continue
        with p.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            if ep_header is None:
                ep_header = header
            ep_id_col = header.index("episode_id") if "episode_id" in header else -1
            rows = list(reader)
            for row in rows:
                if ep_id_col >= 0:
                    try:
                        row[ep_id_col] = str(int(row[ep_id_col]) + ep_id_offset)
                    except ValueError:
                        pass
                ep_frames.append(row)
            if rows and ep_id_col >= 0:
                try:
                    ep_id_offset = int(rows[-1][ep_id_col]) + ep_id_offset + 1
                except (ValueError, IndexError):
                    ep_id_offset += len(rows)

    merged_ep = OUT / "historical_replay_dashboard_v2_episodes.csv"
    with merged_ep.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(ep_header)
        writer.writerows(ep_frames)
    print(f"  -> {len(ep_frames):,} episodes")

    # ── Build episode_id remap table for research log re-indexing ────────────
    # We need to know old_episode_id (per chunk) -> new_episode_id (global)
    # This is encoded in the offsets we tracked above, but simpler to rebuild:
    ep_remap: dict[int, dict[int, int]] = {}   # chunk_idx -> {old_ep_id: new_ep_id}
    ep_id_offset_rebuild = 0
    for ci, cdir in enumerate(chunk_dirs):
        p = cdir / "historical_replay_dashboard_v2_episodes.csv"
        if not p.exists():
            ep_remap[ci] = {}
            continue
        mapping: dict[int, int] = {}
        with p.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            ep_id_col = header.index("episode_id") if "episode_id" in header else -1
            for row in reader:
                if ep_id_col >= 0:
                    try:
                        old_id = int(row[ep_id_col])
                        mapping[old_id] = old_id + ep_id_offset_rebuild
                    except ValueError:
                        pass
            if mapping:
                ep_id_offset_rebuild = max(mapping.values()) + 1
        ep_remap[ci] = mapping

    # ── Merge research log with globally-unique case_ids ────────────────────
    print("  Merging phase1b_episode_research_log.csv with re-indexed case_ids...")
    log_frames: list[list[str]] = []
    log_header = None
    case_counter = 1

    for ci, cdir in enumerate(chunk_dirs):
        p = cdir / "phase1b_episode_research_log.csv"
        if not p.exists():
            continue
        with p.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            if log_header is None:
                log_header = header
            case_col = header.index("case_id") if "case_id" in header else -1
            ep_col   = header.index("episode_id") if "episode_id" in header else -1
            for row in reader:
                # Re-assign globally unique case_id
                if case_col >= 0:
                    row[case_col] = f"CASE_{case_counter:05d}"
                # Re-map episode_id to global space
                if ep_col >= 0 and ci in ep_remap:
                    try:
                        old_ep = int(row[ep_col])
                        row[ep_col] = str(ep_remap[ci].get(old_ep, old_ep))
                    except ValueError:
                        pass
                log_frames.append(row)
                case_counter += 1

    merged_log = RES / "phase1b_episode_research_log.csv"
    with merged_log.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(log_header)
        writer.writerows(log_frames)
    total_cases = case_counter - 1
    print(f"  -> {total_cases:,} score4plus cases (CASE_00001 to CASE_{total_cases:05d})")

    # Build case_id remap for lifecycle events (old_case_id per chunk -> new global)
    case_remap: dict[int, dict[str, str]] = {}
    case_counter2 = 1
    for ci, cdir in enumerate(chunk_dirs):
        p = cdir / "phase1b_episode_research_log.csv"
        if not p.exists():
            case_remap[ci] = {}
            continue
        mapping: dict[str, str] = {}
        with p.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            case_col = header.index("case_id") if "case_id" in header else -1
            for row in reader:
                if case_col >= 0:
                    old_cid = row[case_col]
                    new_cid = f"CASE_{case_counter2:05d}"
                    mapping[old_cid] = new_cid
                    case_counter2 += 1
        case_remap[ci] = mapping

    # ── Merge zone lifecycle events ─────────────────────────────────────────
    print("  Merging zone_lifecycle_events.jsonl...")
    zone_events: list[str] = []
    for ci, cdir in enumerate(chunk_dirs):
        p = cdir / "zone_lifecycle_events.jsonl"
        if not p.exists():
            continue
        remap = case_remap.get(ci, {})
        for line in p.read_text(encoding="utf-8").strip().splitlines():
            if not line:
                continue
            try:
                evt = json.loads(line)
                old_cid = evt.get("related_case_id", "")
                if old_cid in remap:
                    evt["related_case_id"] = remap[old_cid]
                zone_events.append(json.dumps(evt, ensure_ascii=True, sort_keys=True))
            except json.JSONDecodeError:
                pass
    (RES / "zone_lifecycle_events.jsonl").write_text(
        "\n".join(zone_events) + ("\n" if zone_events else ""),
        encoding="utf-8"
    )
    print(f"  -> {len(zone_events):,} zone lifecycle events")

    # ── Merge field lifecycle events ────────────────────────────────────────
    print("  Merging field_lifecycle_events.jsonl...")
    field_events: list[str] = []
    for ci, cdir in enumerate(chunk_dirs):
        p = cdir / "field_lifecycle_events.jsonl"
        if not p.exists():
            continue
        remap = case_remap.get(ci, {})
        for line in p.read_text(encoding="utf-8").strip().splitlines():
            if not line:
                continue
            try:
                evt = json.loads(line)
                old_cid = evt.get("related_case_id", "")
                if old_cid in remap:
                    evt["related_case_id"] = remap[old_cid]
                field_events.append(json.dumps(evt, ensure_ascii=True, sort_keys=True))
            except json.JSONDecodeError:
                pass
    (RES / "field_lifecycle_events.jsonl").write_text(
        "\n".join(field_events) + ("\n" if field_events else ""),
        encoding="utf-8"
    )
    print(f"  -> {len(field_events):,} field lifecycle events")

    return {
        "obs_rows": len(obs_frames),
        "episodes": len(ep_frames),
        "cases": total_cases,
        "zone_events": len(zone_events),
        "field_events": len(field_events),
    }


# ──────────────────────────────────────────────────────────────────────────────
# PHASE 3 — Duplicate audit
# ──────────────────────────────────────────────────────────────────────────────

def duplicate_audit(merge_stats: dict) -> None:
    print(f"\n{'='*60}")
    print("[DUPLICATE AUDIT]")
    print(f"{'='*60}")

    # episode_ids in merged episodes file
    ep_ids: list[str] = []
    p = OUT / "historical_replay_dashboard_v2_episodes.csv"
    if p.exists():
        with p.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            h = next(reader)
            col = h.index("episode_id") if "episode_id" in h else -1
            for row in reader:
                if col >= 0: ep_ids.append(row[col])
    dup_ep = len(ep_ids) - len(set(ep_ids))
    print(f"  Duplicate episode_ids: {dup_ep}")

    # case_ids in merged research log
    case_ids: list[str] = []
    p2 = RES / "phase1b_episode_research_log.csv"
    if p2.exists():
        with p2.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            h = next(reader)
            col = h.index("case_id") if "case_id" in h else -1
            for row in reader:
                if col >= 0: case_ids.append(row[col])
    dup_case = len(case_ids) - len(set(case_ids))
    print(f"  Duplicate case_ids:    {dup_case}")

    # related_case_id in lifecycle events
    zone_cids = set()
    p3 = RES / "zone_lifecycle_events.jsonl"
    if p3.exists():
        for line in p3.read_text(encoding="utf-8").strip().splitlines():
            try:
                zone_cids.add(json.loads(line).get("related_case_id", ""))
            except: pass
    print(f"  Zone event case_ids:   {len(zone_cids)} unique")

    if dup_ep > 0 or dup_case > 0:
        print(f"  WARNING: Duplicates detected — inspect before running calculator")
    else:
        print(f"  PASS: No duplicates in episode_id or case_id")


# ──────────────────────────────────────────────────────────────────────────────
# PHASE 4 — RDM Calculator
# ──────────────────────────────────────────────────────────────────────────────

def run_calculator() -> None:
    print(f"\n{'='*60}")
    print("[RDM] Running zone_mechanics_calculator.py on merged dataset")
    print(f"{'='*60}")
    rc = run([PYTHON, "research/zone_mechanics_calculator.py"], "zone_mechanics_calculator")
    if rc != 0:
        print("  FATAL: Calculator failed.")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    t_start = time.perf_counter()
    print("=" * 60)
    print("RDM BACKTESTING DATASET BUILDER")
    print(f"Target: 2026-04-30 -> 2026-06-03 BTCUSDT")
    print(f"Chunks: {len(CHUNKS)} × ~3 days each")
    print("=" * 60)

    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    # Phase 1
    chunk_dirs = process_chunks()

    # Phase 2
    merge_stats = merge_chunks(chunk_dirs)

    # Phase 3
    duplicate_audit(merge_stats)

    # Phase 4
    run_calculator()

    elapsed = time.perf_counter() - t_start
    print(f"\n{'='*60}")
    print(f"COMPLETE — {elapsed/60:.1f} minutes")
    print(f"  Observation rows  : {merge_stats['obs_rows']:,}")
    print(f"  Episodes          : {merge_stats['episodes']:,}")
    print(f"  Score4plus cases  : {merge_stats['cases']:,}")
    print(f"  Zone events       : {merge_stats['zone_events']:,}")
    print(f"  Field events      : {merge_stats['field_events']:,}")
    print("=" * 60)


if __name__ == "__main__":
    main()

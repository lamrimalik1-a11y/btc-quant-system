"""
Run a complete single-day validation cycle:
  1. replay generation
  2. research analysis
  3. stats extraction

Usage: python tools/run_day_validation.py --date 2026-05-28
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, label):
    print(f"\n{'='*60}")
    print(f"STEP: {label}")
    print(f"CMD:  {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=False, text=True)
    if result.returncode != 0:
        print(f"FAILED with exit code {result.returncode}")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="YYYY-MM-DD to replay")
    args = parser.parse_args()
    date = args.date

    start = f"{date} 00:00:00"
    # end = next calendar day
    from datetime import datetime, timedelta
    end_dt = datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)
    end = end_dt.strftime("%Y-%m-%d") + " 00:00:00"

    run(
        [sys.executable, "tools/generate_binance_historical_replay.py",
         "--start", start, "--end", end, "--overwrite"],
        f"Replay generation for {date}",
    )

    run(
        [sys.executable, "tools/analyze_phase1b_episode_research.py", "--mode", "all"],
        f"Research analysis for {date}",
    )

    run(
        [sys.executable, "tools/extract_day_stats.py", "--date", date],
        f"Stats extraction for {date}",
    )

    print(f"\nDay {date} complete.")


if __name__ == "__main__":
    main()

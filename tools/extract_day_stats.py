"""
Extract and save preparation family stats from the current analysis output.
Run after each daily replay+analysis cycle to build the multi-day comparison.
Usage: python tools/extract_day_stats.py --date 2026-05-29
"""
import argparse
import json
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT / "research"
STATS_FILE = RESEARCH_DIR / "prep_family_day_stats.json"


def load_existing():
    if STATS_FILE.exists():
        with open(STATS_FILE) as f:
            return json.load(f)
    return {}


def outcome(row):
    cl = str(row.get("classification", ""))
    move = pd.to_numeric(row.get("max_abs_move_4h"), errors="coerce") or 0
    if cl in ("ACCELERATION_ZONE", "MOMENTUM_PRECURSOR") and move >= 250:
        return "MAJOR_EXPANSION"
    if cl in ("ACCELERATION_ZONE", "PRE_EXPANSION", "MOMENTUM_PRECURSOR", "ACCUMULATION") and move >= 100:
        return "REAL_BREAKOUT"
    if cl == "REVERSAL_WARNING":
        return "FAKE_BREAKOUT"
    if cl == "FAILED_CONTEXT":
        return "ZONE_COLLAPSE"
    return "ZONE_SURVIVAL"


def family_stats(df, family):
    sub = df[df["prep_family"] == family]
    if sub.empty:
        return {"n": 0}

    sub2 = sub.copy()
    sub2["_outcome"] = sub2.apply(outcome, axis=1)

    move = pd.to_numeric(sub2["max_abs_move_4h"], errors="coerce").dropna()
    eq = pd.to_numeric(sub2["pre_equil_rows"], errors="coerce").dropna()
    conf = pd.to_numeric(sub2["prep_family_confidence"], errors="coerce").dropna()

    n = len(sub2)
    n_exp = int(sub2["_outcome"].isin(["MAJOR_EXPANSION", "REAL_BREAKOUT"]).sum())
    n_fake = int((sub2["_outcome"] == "FAKE_BREAKOUT").sum())
    n_surv = int((sub2["_outcome"] == "ZONE_SURVIVAL").sum())

    rules = sub2["prep_family_rule"].value_counts().to_dict() if "prep_family_rule" in sub2.columns else {}
    aligns = sub2["prep_delta_alignment"].value_counts().to_dict() if "prep_delta_alignment" in sub2.columns else {}

    return {
        "n": n,
        "expansion_pct": round(n_exp / n * 100, 1) if n > 0 else 0,
        "fake_pct": round(n_fake / n * 100, 1) if n > 0 else 0,
        "survival_pct": round(n_surv / n * 100, 1) if n > 0 else 0,
        "mean_move_4h": round(float(move.mean()), 1) if not move.empty else None,
        "mean_equil_rows": round(float(eq.mean()), 1) if not eq.empty else None,
        "min_equil_rows": int(eq.min()) if not eq.empty else None,
        "max_equil_rows": int(eq.max()) if not eq.empty else None,
        "mean_confidence": round(float(conf.mean()), 3) if not conf.empty else None,
        "rules": {str(k): int(v) for k, v in rules.items()},
        "delta_alignment": {str(k): int(v) for k, v in aligns.items()},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()

    log_path = RESEARCH_DIR / "phase1b_episode_research_log.csv"
    if not log_path.exists():
        print(f"ERROR: {log_path} not found")
        return

    log = pd.read_csv(log_path)
    print(f"Loaded {len(log)} episodes for {args.date}")

    stats = {
        "date": args.date,
        "total_episodes": len(log),
        "families": {
            "EQUILIBRIUM_COMPRESSION": family_stats(log, "EQUILIBRIUM_COMPRESSION"),
            "EXTREME_COMPRESSION":     family_stats(log, "EXTREME_COMPRESSION"),
            "AMBIGUOUS":               family_stats(log, "AMBIGUOUS"),
            "UNKNOWN":                 family_stats(log, "UNKNOWN"),
        },
        "episode_rules": log["prep_family_rule"].value_counts().to_dict()
            if "prep_family_rule" in log.columns else {},
        "prep_family_dist": log["prep_family"].value_counts().to_dict()
            if "prep_family" in log.columns else {},
        "future_direction": log["future_direction"].value_counts().to_dict()
            if "future_direction" in log.columns else {},
        "pre_equil_all_mean": round(
            float(pd.to_numeric(log["pre_equil_rows"], errors="coerce").dropna().mean()), 1
        ) if "pre_equil_rows" in log.columns else None,
    }

    existing = load_existing()
    existing[args.date] = stats

    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATS_FILE, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"Saved stats for {args.date} to {STATS_FILE}")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()

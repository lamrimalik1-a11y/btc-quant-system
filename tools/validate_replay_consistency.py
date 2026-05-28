"""Replay consistency validator for Dashboard V2 / RDM research rendering.

Diagnostics only. It does not change replay, scoring, dashboard logic, RDM
logic, or live/execution behavior.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
RESEARCH = ROOT / "research"
REPORT_MD = OUTPUTS / "replay_consistency_report.md"
REPORT_JSON = OUTPUTS / "replay_consistency_report.json"

HISTORICAL_SOURCES = {
    "historical_market_rows": OUTPUTS / "historical_market_rows.csv",
    "historical_observation_rows": OUTPUTS / "historical_observation_rows.csv",
    "historical_v2_episodes": OUTPUTS / "historical_replay_dashboard_v2_episodes.csv",
    "historical_v2_events": OUTPUTS / "historical_replay_observation_v2_events.csv",
}

LIVE_SOURCES = {
    "market_rows": OUTPUTS / "market_rows.csv",
    "observation_events": OUTPUTS / "observation_events.csv",
    "dashboard_episodes": OUTPUTS / "dashboard_episodes.csv",
}

RESEARCH_SOURCES = {
    "research_log": RESEARCH / "phase1b_episode_research_log.csv",
    "rdm_results": RESEARCH / "zone_mechanics_cycle3_results.csv",
    "live_evolution": RESEARCH / "zone_live_rdm_evolution.csv",
    "interaction_core": RESEARCH / "zone_interaction_core_geometry.csv",
    "density": RESEARCH / "zone_interaction_density_map.csv",
    "true_lifecycle": RESEARCH / "zone_true_lifecycle_tracking.csv",
}


def main() -> None:
    historical_info = {name: file_info(path) for name, path in HISTORICAL_SOURCES.items()}
    live_info = {name: file_info(path) for name, path in LIVE_SOURCES.items()}
    research_info = {name: file_info(path) for name, path in RESEARCH_SOURCES.items()}

    historical_windows = {
        name: timestamp_window(path)
        for name, path in HISTORICAL_SOURCES.items()
    }
    live_windows = {
        name: timestamp_window(path)
        for name, path in LIVE_SOURCES.items()
    }
    research_windows = {
        name: timestamp_window(path)
        for name, path in RESEARCH_SOURCES.items()
    }

    stale_live = stale_live_files(live_info, historical_info)
    mixed_source_usage = detect_mixed_source_usage()
    timestamp_inconsistencies = detect_timestamp_inconsistencies(
        historical_windows,
        research_windows,
    )
    replay_live_overlap = detect_replay_live_overlap(
        historical_windows,
        live_windows,
    )

    result = {
        "run_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "historical_sources": historical_info,
        "live_sources": live_info,
        "research_sources": research_info,
        "historical_windows": historical_windows,
        "live_windows": live_windows,
        "research_windows": research_windows,
        "mixed_source_usage": mixed_source_usage,
        "stale_live_file_contamination": stale_live,
        "timestamp_inconsistencies": timestamp_inconsistencies,
        "replay_live_overlap": replay_live_overlap,
        "conclusions": {
            "MIXED_SOURCE_USAGE_DETECTED": bool(mixed_source_usage),
            "STALE_LIVE_FILES_FOUND": bool(stale_live),
            "TIMESTAMP_INCONSISTENCIES_FOUND": bool(timestamp_inconsistencies),
            "REPLAY_LIVE_OVERLAP_FOUND": bool(replay_live_overlap),
            "HISTORICAL_REPLAY_SOURCES_PRESENT": all(
                item.get("exists") for item in historical_info.values()
            ),
        },
    }

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    REPORT_MD.write_text(markdown_report(result), encoding="utf-8")

    print(f"Replay consistency report: {relative_path(REPORT_MD)}")
    print(f"Replay consistency JSON: {relative_path(REPORT_JSON)}")
    print(f"Conclusions: {result['conclusions']}")


def detect_mixed_source_usage() -> list[str]:
    issues = []
    dashboard = (ROOT / "dashboard_app.py").read_text(encoding="utf-8")
    if "HISTORICAL REPLAY" in dashboard and "MARKET_ROWS_FILE" in dashboard:
        # This is allowed as long as source isolation guards are present.
        if "assert_source_mode" not in dashboard:
            issues.append("dashboard_app.py references live source constants without source isolation guard.")
    return issues


def stale_live_files(live_info: dict[str, Any], historical_info: dict[str, Any]) -> list[str]:
    historical_times = [
        item.get("modified_epoch")
        for item in historical_info.values()
        if item.get("modified_epoch")
    ]
    if not historical_times:
        return []
    newest_historical = max(historical_times)
    issues = []
    for name, info in live_info.items():
        modified = info.get("modified_epoch")
        if not info.get("exists"):
            continue
        if modified and modified < newest_historical:
            issues.append(
                f"{name} is older than historical replay sources and must not be used in HISTORICAL_REPLAY_MODE."
            )
    return issues


def detect_timestamp_inconsistencies(historical_windows, research_windows) -> list[str]:
    issues = []
    hist = historical_windows.get("historical_observation_rows", {})
    research = research_windows.get("research_log", {})
    if hist.get("start") and research.get("start"):
        if str(hist["start"])[:10] != str(research["start"])[:10]:
            issues.append("Research log date does not match historical observation date.")
    return issues


def detect_replay_live_overlap(historical_windows, live_windows) -> list[str]:
    issues = []
    hist = historical_windows.get("historical_observation_rows", {})
    live = live_windows.get("market_rows", {})
    if not hist.get("start") or not live.get("start"):
        return issues
    if hist.get("start") == live.get("start") and hist.get("end") == live.get("end"):
        issues.append("Live market rows have the same window as historical replay; verify source mode.")
    return issues


def timestamp_window(path: Path) -> dict[str, Any]:
    dataframe = read_csv(path)
    if dataframe.empty:
        return {"path": relative_path(path), "exists": path.exists(), "rows": 0}
    timestamp_column = first_existing_column(
        dataframe,
        [
            "market_timestamp",
            "episode_start_timestamp_utc",
            "event_timestamp_utc",
            "timestamp",
            "end_ts",
        ],
    )
    if not timestamp_column:
        return {"path": relative_path(path), "exists": True, "rows": len(dataframe), "timestamp_column": ""}
    parsed = dataframe[timestamp_column].apply(parse_time).dropna()
    if parsed.empty:
        return {"path": relative_path(path), "exists": True, "rows": len(dataframe), "timestamp_column": timestamp_column}
    return {
        "path": relative_path(path),
        "exists": True,
        "rows": len(dataframe),
        "timestamp_column": timestamp_column,
        "start": parsed.min().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "end": parsed.max().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def file_info(path: Path) -> dict[str, Any]:
    info = {"path": relative_path(path), "exists": path.exists()}
    if not path.exists():
        return info
    stat = path.stat()
    info["size_bytes"] = stat.st_size
    info["modified"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    info["modified_epoch"] = stat.st_mtime
    if path.suffix.lower() == ".csv":
        dataframe = read_csv(path)
        info["rows"] = len(dataframe)
    return info


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def first_existing_column(dataframe: pd.DataFrame, columns: list[str]) -> str:
    for column in columns:
        if column in dataframe.columns:
            return column
    return ""


def parse_time(value: Any):
    if pd.isna(value):
        return None
    try:
        numeric = float(value)
        if abs(numeric) > 1e11:
            return pd.to_datetime(numeric, unit="ms", utc=True).to_pydatetime()
        if abs(numeric) > 1e9:
            return pd.to_datetime(numeric, unit="s", utc=True).to_pydatetime()
    except (TypeError, ValueError):
        pass
    parsed = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime()


def markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# Replay Consistency Report",
        "",
        f"Run UTC: {result['run_utc']}",
        "",
        "## Conclusions",
        "",
    ]
    for key, value in result["conclusions"].items():
        lines.append(f"- {key}: {value}")
    for title, key in [
        ("Historical Sources", "historical_sources"),
        ("Live Sources", "live_sources"),
        ("Research Sources", "research_sources"),
        ("Historical Windows", "historical_windows"),
        ("Live Windows", "live_windows"),
        ("Research Windows", "research_windows"),
    ]:
        lines.extend(["", f"## {title}", ""])
        for name, info in result[key].items():
            lines.append(f"- {name}: {info}")
    for title, key in [
        ("Mixed Source Usage", "mixed_source_usage"),
        ("Stale Live File Contamination", "stale_live_file_contamination"),
        ("Timestamp Inconsistencies", "timestamp_inconsistencies"),
        ("Replay / Live Overlap", "replay_live_overlap"),
    ]:
        lines.extend(["", f"## {title}", ""])
        items = result[key]
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("- None detected.")
    return "\n".join(lines) + "\n"


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()

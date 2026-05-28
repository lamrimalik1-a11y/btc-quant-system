"""Read-only data integrity diagnostic for episode 75 / CASE_00075."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
RESEARCH = ROOT / "research"
REPORT_MD = OUTPUTS / "data_integrity_episode_75_report.md"
REPORT_JSON = OUTPUTS / "data_integrity_episode_75.json"
EPISODE_ID = "75"
CASE_ID = "CASE_00075"
TARGET = datetime(2026, 5, 28, 14, 5, 0, tzinfo=timezone.utc)


FILES = {
    "historical_v2_episodes": OUTPUTS / "historical_replay_dashboard_v2_episodes.csv",
    "historical_v2_events": OUTPUTS / "historical_replay_observation_v2_events.csv",
    "historical_observation_rows": OUTPUTS / "historical_observation_rows.csv",
    "historical_market_rows": OUTPUTS / "historical_market_rows.csv",
    "live_market_rows": OUTPUTS / "market_rows.csv",
    "dashboard_v2_episodes_expected": OUTPUTS / "dashboard_v2_episodes.csv",
    "dashboard_v2_episode_research_expected": OUTPUTS / "dashboard_v2_episode_research.csv",
    "research_log": RESEARCH / "phase1b_episode_research_log.csv",
    "rdm_results": RESEARCH / "zone_mechanics_cycle3_results.csv",
    "real_geometry": RESEARCH / "zone_real_geometry_tracking.csv",
    "live_evolution": RESEARCH / "zone_live_rdm_evolution.csv",
    "interaction_core": RESEARCH / "zone_interaction_core_geometry.csv",
    "density": RESEARCH / "zone_interaction_density_map.csv",
    "true_lifecycle": RESEARCH / "zone_true_lifecycle_tracking.csv",
    "birth": RESEARCH / "zone_birth_registry.csv",
    "death": RESEARCH / "zone_death_registry.csv",
}


def main() -> None:
    v2 = read_csv(FILES["historical_v2_episodes"])
    research = read_csv(FILES["research_log"])
    rdm = read_csv(FILES["rdm_results"])
    geometry = read_csv(FILES["real_geometry"])
    core = read_csv(FILES["interaction_core"])
    density = read_csv(FILES["density"])
    live = read_csv(FILES["live_evolution"])
    hist_obs = read_csv(FILES["historical_observation_rows"])
    hist_market = read_csv(FILES["historical_market_rows"])

    episode = row_dict(find_row(v2, "episode_id", EPISODE_ID))
    research_row = row_dict(find_row(research, "case_id", CASE_ID))
    rdm_row = row_dict(find_row(rdm, "case_id", CASE_ID))
    geometry_row = row_dict(find_row(geometry, "case_id", CASE_ID))
    core_row = row_dict(find_row(core, "case_id", CASE_ID))
    density_row = row_dict(find_row(density, "case_id", CASE_ID))

    start_row_id = episode.get("start_row_id")
    end_row_id = episode.get("end_row_id")
    obs_start = row_dict(find_row(hist_obs, "row_id", start_row_id))
    obs_end = row_dict(find_row(hist_obs, "row_id", end_row_id))
    market_start = row_dict(find_row(hist_market, "row_id", start_row_id))
    market_end = row_dict(find_row(hist_market, "row_id", end_row_id))

    windows = {
        "14:05_UTC": TARGET,
        "14:05_local_Africa_Lagos_as_13:05_UTC": TARGET - timedelta(hours=1),
        "13:05_UTC": datetime(2026, 5, 28, 13, 5, 0, tzinfo=timezone.utc),
        "15:05_UTC": datetime(2026, 5, 28, 15, 5, 0, tzinfo=timezone.utc),
    }
    window_checks = {
        label: {
            "historical_observation_rows": window_rows(FILES["historical_observation_rows"], center),
            "historical_market_rows": window_rows(FILES["historical_market_rows"], center),
            "live_market_rows": window_rows(FILES["live_market_rows"], center),
        }
        for label, center in windows.items()
    }

    live_case = (
        live[live["case_id"].astype(str) == CASE_ID].copy()
        if not live.empty and "case_id" in live.columns
        else pd.DataFrame()
    )
    rdm_compare = {
        "birth_time": geometry_row.get("real_birth_time") or rdm_row.get("real_birth_time"),
        "real_birth_price": geometry_row.get("real_birth_price") or rdm_row.get("real_birth_price"),
        "real_zone_upper_edge": geometry_row.get("real_zone_upper_edge") or rdm_row.get("real_zone_upper_edge"),
        "real_zone_lower_edge": geometry_row.get("real_zone_lower_edge") or rdm_row.get("real_zone_lower_edge"),
        "active_core_upper": core_row.get("interaction_core_upper_edge") or rdm_row.get("interaction_core_upper_edge"),
        "active_core_lower": core_row.get("interaction_core_lower_edge") or rdm_row.get("interaction_core_lower_edge"),
        "density_peak_price": density_row.get("interaction_density_peak_price") or rdm_row.get("interaction_density_peak_price"),
        "final_price": rdm_row.get("final_price"),
        "live_latest_price": "",
        "source_csvs": {
            "rdm_results": "research/zone_mechanics_cycle3_results.csv",
            "real_geometry": "research/zone_real_geometry_tracking.csv",
            "interaction_core": "research/zone_interaction_core_geometry.csv",
            "density": "research/zone_interaction_density_map.csv",
            "live_evolution": "research/zone_live_rdm_evolution.csv",
        },
    }
    if not live_case.empty:
        latest = live_case.tail(1).iloc[0]
        rdm_compare["live_latest_price"] = latest.get("price")
        rdm_compare["live_latest_timestamp"] = latest.get("timestamp")

    align_ok = episode_row_alignment_ok(episode, obs_start, obs_end)
    mapping_ok = dashboard_mapping_ok(episode, rdm_compare)
    source_ok = (
        window_checks["14:05_UTC"]["historical_observation_rows"]["rows"] > 0
        and window_checks["14:05_UTC"]["historical_observation_rows"]["min_price"] is not None
    )
    has_74_window = [
        label
        for label, group in window_checks.items()
        if (group["historical_observation_rows"]["max_price"] or 0) >= 74000
    ]
    timezone_mismatch = bool(has_74_window and "14:05_UTC" not in has_74_window)
    stale_artifacts = stale_artifact_notes()

    conclusions = {
        "SOURCE_DATA_OK" if source_ok else "SOURCE_DATA_WRONG": True,
        "TIMEZONE_MISMATCH" if timezone_mismatch else "TIMEZONE_OK": True,
        "DASHBOARD_MAPPING_OK" if mapping_ok else "DASHBOARD_MAPPING_BUG": True,
        "EPISODE_ROW_ALIGNMENT_OK" if align_ok else "EPISODE_ROW_ALIGNMENT_BUG": True,
        "STALE_ARTIFACTS_FOUND" if stale_artifacts else "NO_STALE_ARTIFACTS": True,
    }

    data = {
        "episode_id": EPISODE_ID,
        "case_id": CASE_ID,
        "target_time": "2026-05-28 14:05:00 UTC",
        "files_inspected": [
            "tools/generate_binance_historical_replay.py",
            "tools/analyze_phase1b_episode_research.py",
            "research/zone_mechanics_calculator.py",
            "dashboard/research_mapping.py",
            "dashboard_app.py",
            "dashboard/overlay_renderer.py",
        ],
        "file_infos": {name: file_info(path) for name, path in FILES.items()},
        "episode_metadata": select_fields(
            episode,
            [
                "episode_id",
                "episode_start_timestamp_utc",
                "episode_end_timestamp_utc",
                "duration_seconds",
                "start_row_id",
                "end_row_id",
                "peak_state",
                "peak_layer_count",
                "peak_max_severity",
                "peak_primary_context",
                "peak_conditions",
                "peak_active_layers",
                "peak_observation_confidence",
                "start_price",
                "end_price",
                "peak_rvi",
                "peak_velocity",
                "peak_delta_zscore",
            ],
        ),
        "episode_times_readable": {
            "start": dt_iso(episode.get("episode_start_timestamp_utc")),
            "end": dt_iso(episode.get("episode_end_timestamp_utc")),
        },
        "row_alignment": {
            "obs_start": select_fields(obs_start, price_columns_from_dict(obs_start)),
            "obs_end": select_fields(obs_end, price_columns_from_dict(obs_end)),
            "market_start": select_fields(market_start, price_columns_from_dict(market_start)),
            "market_end": select_fields(market_end, price_columns_from_dict(market_end)),
            "alignment_ok": align_ok,
        },
        "window_checks": window_checks,
        "research_case": select_fields(
            research_row,
            [
                "case_id",
                "episode_id",
                "episode_start_time_utc",
                "episode_end_time_utc",
                "start_row_id",
                "end_row_id",
                "start_price",
                "end_price",
                "classification",
                "peak_layer_count",
                "peak_primary_context",
                "price_at_1m",
                "price_at_5m",
                "price_at_1h",
                "price_at_4h",
            ],
        ),
        "rdm_compare": rdm_compare,
        "stale_artifacts": stale_artifacts,
        "conclusions": conclusions,
        "notes": [
            "Binance chart external value was not fetched because diagnostics are local/read-only/no network.",
            "Dashboard historical mode loads historical_observation_rows.csv and historical_replay_dashboard_v2_episodes.csv.",
            "Default/live dashboard files such as outputs/market_rows.csv are older than current historical files and can cause visual confusion if mode is mixed.",
        ],
    }

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(data, indent=2, default=json_default), encoding="utf-8")
    REPORT_MD.write_text(markdown_report(data), encoding="utf-8")

    print(f"REPORT_JSON {relative_path(REPORT_JSON)}")
    print(f"REPORT_MD {relative_path(REPORT_MD)}")
    print(f"CONCLUSIONS {conclusions}")
    print(f"EPISODE {data['episode_metadata']}")
    print("WINDOW_14UTC_HIST_OBS", window_checks["14:05_UTC"]["historical_observation_rows"])
    print("WINDOW_13UTC_HIST_OBS", window_checks["13:05_UTC"]["historical_observation_rows"])
    print("WINDOW_15UTC_HIST_OBS", window_checks["15:05_UTC"]["historical_observation_rows"])
    print(f"RDM_COMPARE {rdm_compare}")
    print(f"STALE {stale_artifacts}")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as error:
        return pd.DataFrame({"__read_error__": [str(error)]})


def find_row(dataframe: pd.DataFrame, column: str, value: Any) -> pd.DataFrame:
    if dataframe.empty or column not in dataframe.columns:
        return pd.DataFrame()
    return dataframe[dataframe[column].astype(str) == str(value)].copy()


def row_dict(dataframe: pd.DataFrame) -> dict[str, Any]:
    if dataframe.empty:
        return {}
    row = dataframe.iloc[0]
    return {column: none_if_na(row.get(column)) for column in dataframe.columns}


def parse_dt(value: Any):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return parse_epoch(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        numeric = float(text)
        parsed = parse_epoch(numeric)
        if parsed is not None:
            return parsed
    except ValueError:
        pass
    parsed = pd.to_datetime(text, utc=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime()


def parse_epoch(value: float):
    try:
        if abs(value) > 1e11:
            return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
        if abs(value) > 1e9:
            return datetime.fromtimestamp(value, tz=timezone.utc)
    except Exception:
        return None
    return None


def dt_iso(value: Any) -> str:
    parsed = parse_dt(value)
    return parsed.strftime("%Y-%m-%d %H:%M:%S UTC") if parsed else ""


def add_datetime(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe
    prepared = dataframe.copy()
    for column in [
        "market_timestamp",
        "event_timestamp_utc",
        "episode_start_timestamp_utc",
        "episode_end_timestamp_utc",
        "timestamp",
        "end_ts",
        "start_ts",
    ]:
        if column in prepared.columns:
            parsed = prepared[column].apply(parse_dt)
            if parsed.notna().sum() > 0:
                prepared["__dt"] = parsed
                prepared["__dt_source"] = column
                return prepared
    return prepared


def window_rows(path: Path, center: datetime, minutes: int = 1) -> dict[str, Any]:
    dataframe = read_csv(path)
    if dataframe.empty:
        return empty_window(path, path.exists())
    dataframe = add_datetime(dataframe)
    if "__dt" not in dataframe.columns:
        result = empty_window(path, True)
        result["rows"] = len(dataframe)
        result["dt_source"] = "NO_TIMESTAMP_PARSED"
        return result

    start = center - timedelta(minutes=minutes)
    end = center + timedelta(minutes=minutes)
    mask = dataframe["__dt"].apply(lambda value: value is not None and start <= value <= end)
    window = dataframe[mask].copy()
    columns = price_columns(window)
    records = []
    for _, row in window.head(50).iterrows():
        item = {column: none_if_na(row.get(column)) for column in columns}
        item["parsed_time"] = dt_iso(row.get("__dt"))
        records.append(item)
    prices = []
    for column in ["open", "high", "low", "close", "price", "vwap", "end_price", "start_price"]:
        if column in window.columns:
            prices.extend(pd.to_numeric(window[column], errors="coerce").dropna().tolist())
    return {
        "path": relative_path(path),
        "exists": True,
        "rows": len(window),
        "dt_source": str(dataframe["__dt_source"].iloc[0]),
        "records": records,
        "min_price": min(prices) if prices else None,
        "max_price": max(prices) if prices else None,
    }


def empty_window(path: Path, exists: bool) -> dict[str, Any]:
    return {
        "path": relative_path(path),
        "exists": exists,
        "rows": 0,
        "dt_source": "",
        "records": [],
        "min_price": None,
        "max_price": None,
    }


def price_columns(dataframe: pd.DataFrame) -> list[str]:
    return [
        column
        for column in [
            "row_id",
            "market_timestamp",
            "timestamp",
            "start_ts",
            "end_ts",
            "open",
            "high",
            "low",
            "close",
            "price",
            "vwap",
            "last_price",
            "end_price",
            "start_price",
        ]
        if column in dataframe.columns
    ]


def price_columns_from_dict(row: dict[str, Any]) -> list[str]:
    return [
        column
        for column in [
            "row_id",
            "market_timestamp",
            "timestamp",
            "start_ts",
            "end_ts",
            "open",
            "high",
            "low",
            "close",
            "price",
            "vwap",
            "last_price",
            "end_price",
            "start_price",
        ]
        if column in row
    ]


def select_fields(row: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    return {field: row.get(field) for field in fields if field in row}


def file_info(path: Path) -> dict[str, Any]:
    info = {"path": relative_path(path), "exists": path.exists()}
    if not path.exists():
        return info
    stat = path.stat()
    info["size_bytes"] = stat.st_size
    info["modified"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    if path.suffix.lower() == ".csv":
        try:
            info["rows"] = len(pd.read_csv(path))
        except Exception as error:
            info["rows_error"] = str(error)
    elif path.suffix.lower() == ".jsonl":
        try:
            info["rows"] = sum(1 for _ in path.open("r", encoding="utf-8"))
        except Exception as error:
            info["rows_error"] = str(error)
    return info


def stale_artifact_notes() -> list[str]:
    notes = []
    for name in [
        "live_market_rows",
        "dashboard_v2_episodes_expected",
        "dashboard_v2_episode_research_expected",
    ]:
        path = FILES[name]
        if not path.exists():
            notes.append(f"{name}: missing")
            continue
        modified = datetime.fromtimestamp(path.stat().st_mtime)
        if (datetime.now() - modified).days >= 1:
            notes.append(f"{name}: old modified {modified:%Y-%m-%d %H:%M:%S}")
    return notes


def episode_row_alignment_ok(episode: dict[str, Any], obs_start: dict[str, Any], obs_end: dict[str, Any]) -> bool:
    try:
        episode_start = to_float(episode.get("start_price"))
        episode_end = to_float(episode.get("end_price"))
        obs_start_close = to_float(obs_start.get("close"))
        obs_end_close = to_float(obs_end.get("close"))
        if episode_start is not None and obs_start_close is not None and abs(episode_start - obs_start_close) > 1e-6:
            return False
        if episode_end is not None and obs_end_close is not None and abs(episode_end - obs_end_close) > 1e-6:
            return False
    except Exception:
        return False
    return True


def dashboard_mapping_ok(episode: dict[str, Any], rdm_compare: dict[str, Any]) -> bool:
    try:
        start_price = to_float(episode.get("start_price"))
        end_price = to_float(episode.get("end_price"))
        birth_price = to_float(rdm_compare.get("real_birth_price"))
        if start_price is None or birth_price is None:
            return True
        high = max(start_price, end_price or start_price) + 1000
        low = min(start_price, end_price or start_price) - 1000
        return low <= birth_price <= high
    except Exception:
        return False


def markdown_report(data: dict[str, Any]) -> str:
    lines = [
        "# Data Integrity Diagnostic - Episode 75",
        "",
        f"Episode: {EPISODE_ID}",
        f"Case: {CASE_ID}",
        "Target: 2026-05-28 14:05:00 UTC",
        "",
        "## Conclusions",
        "",
    ]
    lines.extend(f"- {key}" for key in data["conclusions"])
    lines.extend(["", "## Episode Metadata", ""])
    lines.extend(f"- {key}: {value}" for key, value in data["episode_metadata"].items())
    lines.append(f"- readable_start: {data['episode_times_readable']['start']}")
    lines.append(f"- readable_end: {data['episode_times_readable']['end']}")
    lines.extend(["", "## Row Alignment", "", f"- alignment_ok: {data['row_alignment']['alignment_ok']}"])
    lines.extend(["", "### Observation start row", "```json", json.dumps(data["row_alignment"]["obs_start"], indent=2, default=json_default), "```"])
    lines.extend(["", "### Observation end row", "```json", json.dumps(data["row_alignment"]["obs_end"], indent=2, default=json_default), "```"])
    lines.extend(["", "## Raw Market Rows Around Compared Times", ""])
    for label, group in data["window_checks"].items():
        lines.extend([f"### {label}", ""])
        for source, info in group.items():
            lines.append(
                f"- {source}: rows={info['rows']}, min={info['min_price']}, "
                f"max={info['max_price']}, dt_source={info['dt_source']}, file={info['path']}"
            )
            for record in info["records"][:8]:
                lines.append(f"  - {record}")
        lines.append("")
    lines.extend(["## Dashboard / RDM Compare", ""])
    lines.extend(f"- {key}: {value}" for key, value in data["rdm_compare"].items())
    lines.extend(["", "## Stale / Mixed Artifact Check", ""])
    if data["stale_artifacts"]:
        lines.extend(f"- {item}" for item in data["stale_artifacts"])
    else:
        lines.append("- No stale artifacts detected among checked dashboard-facing files.")
    lines.extend(["", "## File Modified Times / Row Counts", ""])
    lines.extend(f"- {key}: {value}" for key, value in data["file_infos"].items())
    lines.extend(["", "## Diagnostic Notes", ""])
    lines.extend(f"- {note}" for note in data["notes"])
    return "\n".join(lines) + "\n"


def to_float(value: Any):
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def none_if_na(value: Any):
    if pd.isna(value):
        return None
    return value


def json_default(value: Any):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (datetime, pd.Timestamp)):
        return str(value)
    return str(value)


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()

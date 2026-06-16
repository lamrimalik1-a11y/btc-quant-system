import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = ROOT_DIR / "archives"
OUTPUT_DIR = ROOT_DIR / "outputs"
BACKUP_ROOT = OUTPUT_DIR / "archive_loader_backups"

FILES_TO_LOAD = [
    "historical_observation_rows.csv",
    "historical_market_rows.csv",
    "historical_replay_dashboard_v2_episodes.csv",
    "historical_replay_observation_v2_events.csv",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Load one archived historical day into outputs/ for dashboard "
            "visualization only. This does not download, replay, or run research."
        )
    )
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--date", required=True, help="Market date: YYYY-MM-DD")
    parser.add_argument(
        "--archive-path",
        help="Explicit archived day/run folder. Defaults to newest manifest for date.",
    )
    parser.add_argument(
        "--restore",
        help="Restore outputs from a backup folder created by this tool.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.restore:
        restore_outputs(Path(args.restore))
        return

    archive_path = (
        Path(args.archive_path)
        if args.archive_path
        else find_latest_archive_path(args.symbol, args.date)
    )
    archive_path = resolve_workspace_path(archive_path)
    validate_archive_path(archive_path)

    backup_path = backup_current_outputs(args.symbol, args.date)
    copy_archive_to_outputs(archive_path)
    verification = verify_loaded_outputs(args.date)

    print("ARCHIVED DAY LOADED FOR DASHBOARD VISUALIZATION")
    print(f"symbol={args.symbol.upper()}")
    print(f"market_date={args.date}")
    print(f"archive_path={archive_path}")
    print(f"backup_path={backup_path}")
    print("")
    print_verification(verification)
    print("")
    print("RESTORE COMMAND:")
    print(f'python tools/load_archived_day_to_outputs.py --restore "{backup_path}"')


def resolve_workspace_path(path):
    if path.is_absolute():
        return path
    return ROOT_DIR / path


def find_latest_archive_path(symbol, market_date):
    symbol_root = ARCHIVE_ROOT / symbol.upper()

    if not symbol_root.exists():
        raise SystemExit(f"Archive symbol folder not found: {symbol_root}")

    manifests = []

    for manifest_path in symbol_root.rglob("manifest.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        if manifest.get("market_date") != market_date:
            continue

        created_at = parse_created_at(manifest.get("created_at"))
        archive_path = manifest.get("archive_path") or str(manifest_path.parent)
        manifests.append((created_at, manifest_path, archive_path))

    if not manifests:
        raise SystemExit(
            f"No archive manifest found for {symbol.upper()} {market_date}"
        )

    manifests.sort(key=lambda item: (item[0], str(item[1])))
    return Path(manifests[-1][2])


def parse_created_at(value):
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)

    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def validate_archive_path(archive_path):
    if not archive_path.exists():
        raise SystemExit(f"Archive path not found: {archive_path}")

    missing = [
        file_name
        for file_name in FILES_TO_LOAD
        if not (archive_path / file_name).exists()
    ]

    if missing:
        raise SystemExit(
            "Archive is missing required dashboard files:\n"
            + "\n".join(missing)
            + f"\narchive_path={archive_path}"
        )


def backup_current_outputs(symbol, market_date):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_ROOT / f"{symbol.upper()}_{market_date}_{timestamp}"
    backup_path.mkdir(parents=True, exist_ok=False)

    manifest = {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "purpose": "Backup before loading archived day into outputs/",
        "files": {},
    }

    for file_name in FILES_TO_LOAD:
        source = OUTPUT_DIR / file_name
        if not source.exists():
            manifest["files"][file_name] = {
                "existed": False,
                "backup_path": None,
            }
            continue

        destination = backup_path / file_name
        shutil.copy2(source, destination)
        manifest["files"][file_name] = {
            "existed": True,
            "backup_path": str(destination),
            "size": destination.stat().st_size,
        }

    (backup_path / "backup_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return backup_path


def copy_archive_to_outputs(archive_path):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for file_name in FILES_TO_LOAD:
        shutil.copy2(archive_path / file_name, OUTPUT_DIR / file_name)


def restore_outputs(backup_path):
    backup_path = resolve_workspace_path(backup_path)

    if not backup_path.exists():
        raise SystemExit(f"Backup folder not found: {backup_path}")

    manifest_path = backup_path / "backup_manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"Backup manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    restored = []

    for file_name, details in manifest.get("files", {}).items():
        destination = OUTPUT_DIR / file_name

        if details.get("existed"):
            source = backup_path / file_name
            if not source.exists():
                raise SystemExit(f"Backup file missing: {source}")
            shutil.copy2(source, destination)
            restored.append(file_name)
        elif destination.exists():
            destination.unlink()
            restored.append(f"{file_name} (removed; did not exist before backup)")

    print("OUTPUTS RESTORED FROM ARCHIVE LOADER BACKUP")
    print(f"backup_path={backup_path}")
    print("restored_files=" + ", ".join(restored))


def verify_loaded_outputs(target_date):
    verification = {}

    for file_name in FILES_TO_LOAD:
        path = OUTPUT_DIR / file_name
        verification[file_name] = summarize_csv(path)

    all_dates = set()
    for item in verification.values():
        all_dates.update(item.get("dates", []))

    verification["loaded_target_day_only"] = all_dates == {target_date}
    verification["all_dates"] = sorted(all_dates)
    return verification


def summarize_csv(path):
    if not path.exists():
        return {"exists": False}

    dataframe = pd.read_csv(path, low_memory=False)
    timestamp_column = first_existing_column(
        dataframe,
        [
            "market_timestamp",
            "episode_start_timestamp_utc",
            "event_timestamp_utc",
            "episode_start_time_utc",
            "timestamp",
        ],
    )
    timestamps = parse_timestamps(dataframe[timestamp_column]) if timestamp_column else None
    dates = []

    if timestamps is not None:
        dates = sorted(timestamps.dropna().dt.strftime("%Y-%m-%d").unique().tolist())

    return {
        "exists": True,
        "rows": int(len(dataframe)),
        "timestamp_column": timestamp_column,
        "first_timestamp_utc": format_timestamp(timestamps.min())
        if timestamps is not None and timestamps.notna().any()
        else None,
        "last_timestamp_utc": format_timestamp(timestamps.max())
        if timestamps is not None and timestamps.notna().any()
        else None,
        "dates": dates,
    }


def first_existing_column(dataframe, candidates):
    for candidate in candidates:
        if candidate in dataframe.columns:
            return candidate
    return None


def parse_timestamps(series):
    numeric = pd.to_numeric(series, errors="coerce")

    if numeric.notna().any():
        return pd.to_datetime(numeric, unit="ms", utc=True, errors="coerce")

    return pd.to_datetime(series, utc=True, errors="coerce")


def format_timestamp(value):
    if pd.isna(value):
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")


def print_verification(verification):
    print("VERIFICATION:")
    for file_name in FILES_TO_LOAD:
        summary = verification.get(file_name, {})
        print(f"- {file_name}")
        print(f"  rows={summary.get('rows')}")
        print(f"  timestamp_column={summary.get('timestamp_column')}")
        print(f"  first_timestamp_utc={summary.get('first_timestamp_utc')}")
        print(f"  last_timestamp_utc={summary.get('last_timestamp_utc')}")
        print(f"  dates={summary.get('dates')}")

    print(
        "MARCH/APRIL/JUNE day only = "
        + ("YES" if verification.get("loaded_target_day_only") else "NO")
    )
    print(f"all_dates={verification.get('all_dates')}")


if __name__ == "__main__":
    main()

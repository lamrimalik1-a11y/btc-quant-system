import csv
from pathlib import Path


OUTPUT_DIR = Path("outputs")
OBSERVATION_ROWS_FILE = OUTPUT_DIR / "observation_rows.csv"

FIELDNAMES = [
    "row_id",
    "market_timestamp",
    "close",
    "volume",
    "delta",
    "velocity",
    "rvi",
    "price_zone",
    "volume_zone",
    "delta_zone",
    "velocity_zone",
    "gaussian_extreme",
    "distribution_shift",
    "climactic_volume",
    "velocity_shock",
    "velocity_exhaustion",
    "abnormal_spread",
    "delta_zscore",
    "statistical_dashboard_state",
    "statistical_dashboard_score",
    "statistical_dashboard_conditions",
]


def archive_observation_row(row, statistics, row_id):
    try:
        _archive_observation_row(row, statistics, row_id)
    except Exception:
        return


def _archive_observation_row(row, statistics, row_id):
    _ensure_csv_file()

    with OBSERVATION_ROWS_FILE.open(mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writerow(
            {
                "row_id": row_id,
                "market_timestamp": _get_market_timestamp(row),
                "close": _get(row, "close"),
                "volume": _get(row, "volume"),
                "delta": _get(row, "delta"),
                "velocity": _get(row, "velocity"),
                "rvi": _get(row, "rvi"),
                "price_zone": _get(row, "price_zone"),
                "volume_zone": _get(row, "volume_zone"),
                "delta_zone": _get(row, "delta_zone"),
                "velocity_zone": _get(row, "velocity_zone"),
                "gaussian_extreme": _get(statistics, "gaussian_extreme"),
                "distribution_shift": _get(statistics, "distribution_shift"),
                "climactic_volume": _get(statistics, "climactic_volume"),
                "velocity_shock": _get(statistics, "velocity_shock"),
                "velocity_exhaustion": _get(statistics, "velocity_exhaustion"),
                "abnormal_spread": _get(statistics, "abnormal_spread"),
                "delta_zscore": _get(statistics, "delta_zscore"),
                "statistical_dashboard_state": _get(
                    statistics,
                    "statistical_dashboard_state",
                ),
                "statistical_dashboard_score": _get(
                    statistics,
                    "statistical_dashboard_score",
                ),
                "statistical_dashboard_conditions": _format_conditions(
                    _get(
                        statistics,
                        "statistical_dashboard_conditions",
                        [],
                    )
                ),
            }
        )


def _ensure_csv_file():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not OBSERVATION_ROWS_FILE.exists():
        _write_header()
        return

    with OBSERVATION_ROWS_FILE.open(mode="r", newline="") as file:
        reader = csv.reader(file)
        current_header = next(reader, [])

    if current_header == FIELDNAMES:
        return

    _migrate_csv_header(current_header)


def _migrate_csv_header(current_header):
    if not current_header:
        _write_header()
        return

    with OBSERVATION_ROWS_FILE.open(mode="r", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    with OBSERVATION_ROWS_FILE.open(mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    field: row.get(field, "")
                    for field in FIELDNAMES
                }
            )


def _write_header():
    with OBSERVATION_ROWS_FILE.open(mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()


def _format_conditions(value):
    if value is None:
        return ""

    if isinstance(value, list):
        return "|".join(str(item) for item in value)

    return str(value)


def _get_market_timestamp(row):
    timestamp = (
        _get(row, "end_ts")
        or _get(row, "timestamp")
        or _get(row, "start_ts")
    )

    if timestamp is None:
        return None

    return timestamp


def _get(source, key, default=None):
    if source is None:
        return default

    if isinstance(source, dict):
        return source.get(key, default)

    return getattr(source, key, default)

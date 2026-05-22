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
    "price_zscore",
    "volume_zscore",
    "velocity_zscore",
    "spread_zscore",
    "price_percentile_zone",
    "distribution_shift_state",
    "distribution_shift_strength",
    "price_mean_shift",
    "price_std_shift",
    "gaussian_extreme",
    "gaussian_zone",
    "gaussian_tail",
    "gaussian_confidence",
    "price_tail_risk",
    "price_tail_persistence",
    "price_tail_exhaustion",
    "price_tail_strength",
    "price_tail_side",
    "volatility_regime",
    "volatility_transition",
    "volatility_acceleration",
    "volume_state",
    "volume_expansion",
    "abnormal_volume",
    "velocity_state",
    "velocity_acceleration_state",
    "velocity_deceleration",
    "velocity_exhaustion_state",
    "exhaustion_strength",
    "delta_pressure_state",
    "delta_exhaustion",
    "imbalance_state",
    "aggressive_flow",
    "delta_acceleration_state",
    "spread_state",
    "spread_expansion",
    "execution_quality",
    "distribution_shift",
    "climactic_volume",
    "velocity_shock",
    "velocity_exhaustion",
    "abnormal_spread",
    "delta_zscore",
    "price_extreme_event",
    "volume_extreme_event",
    "delta_extreme_event",
    "velocity_extreme_event",
    "spread_extreme_event",
    "extreme_event_state",
    "extreme_event_context",
    "extreme_event_origin",
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
                "price_zscore": _get(statistics, "price_zscore"),
                "volume_zscore": _get(statistics, "volume_zscore"),
                "velocity_zscore": _get(statistics, "velocity_zscore"),
                "spread_zscore": _get(statistics, "spread_zscore"),
                "price_percentile_zone": _get(
                    statistics,
                    "price_percentile_zone",
                ),
                "distribution_shift_state": _get(
                    statistics,
                    "distribution_shift_state",
                ),
                "distribution_shift_strength": _get(
                    statistics,
                    "distribution_shift_strength",
                ),
                "price_mean_shift": _get(statistics, "price_mean_shift"),
                "price_std_shift": _get(statistics, "price_std_shift"),
                "gaussian_extreme": _get(statistics, "gaussian_extreme"),
                "gaussian_zone": _get(statistics, "gaussian_zone"),
                "gaussian_tail": _get(statistics, "gaussian_tail"),
                "gaussian_confidence": _get(
                    statistics,
                    "gaussian_confidence",
                ),
                "price_tail_risk": _get(statistics, "price_tail_risk"),
                "price_tail_persistence": _get(
                    statistics,
                    "price_tail_persistence",
                ),
                "price_tail_exhaustion": _get(
                    statistics,
                    "price_tail_exhaustion",
                ),
                "price_tail_strength": _get(
                    statistics,
                    "price_tail_strength",
                ),
                "price_tail_side": _get(statistics, "price_tail_side"),
                "volatility_regime": _get(statistics, "volatility_regime"),
                "volatility_transition": _get(
                    statistics,
                    "volatility_transition",
                ),
                "volatility_acceleration": _get(
                    statistics,
                    "volatility_acceleration",
                ),
                "volume_state": _get(statistics, "volume_state"),
                "volume_expansion": _get(statistics, "volume_expansion"),
                "abnormal_volume": _get(statistics, "abnormal_volume"),
                "velocity_state": _get(statistics, "velocity_state"),
                "velocity_acceleration_state": _get(
                    statistics,
                    "velocity_acceleration_state",
                ),
                "velocity_deceleration": _get(
                    statistics,
                    "velocity_deceleration",
                ),
                "velocity_exhaustion_state": _get(
                    statistics,
                    "velocity_exhaustion_state",
                ),
                "exhaustion_strength": _get(
                    statistics,
                    "exhaustion_strength",
                ),
                "delta_pressure_state": _get(
                    statistics,
                    "delta_pressure_state",
                ),
                "delta_exhaustion": _get(statistics, "delta_exhaustion"),
                "imbalance_state": _get(statistics, "imbalance_state"),
                "aggressive_flow": _get(statistics, "aggressive_flow"),
                "delta_acceleration_state": _get(
                    statistics,
                    "delta_acceleration_state",
                ),
                "spread_state": _get(statistics, "spread_state"),
                "spread_expansion": _get(statistics, "spread_expansion"),
                "execution_quality": _get(statistics, "execution_quality"),
                "distribution_shift": _get(statistics, "distribution_shift"),
                "climactic_volume": _get(statistics, "climactic_volume"),
                "velocity_shock": _get(statistics, "velocity_shock"),
                "velocity_exhaustion": _get(statistics, "velocity_exhaustion"),
                "abnormal_spread": _get(statistics, "abnormal_spread"),
                "delta_zscore": _get(statistics, "delta_zscore"),
                "price_extreme_event": _get(
                    statistics,
                    "price_extreme_event",
                ),
                "volume_extreme_event": _get(
                    statistics,
                    "volume_extreme_event",
                ),
                "delta_extreme_event": _get(
                    statistics,
                    "delta_extreme_event",
                ),
                "velocity_extreme_event": _get(
                    statistics,
                    "velocity_extreme_event",
                ),
                "spread_extreme_event": _get(
                    statistics,
                    "spread_extreme_event",
                ),
                "extreme_event_state": _get(
                    statistics,
                    "extreme_event_state",
                ),
                "extreme_event_context": _get(
                    statistics,
                    "extreme_event_context",
                ),
                "extreme_event_origin": _get(
                    statistics,
                    "extreme_event_origin",
                ),
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

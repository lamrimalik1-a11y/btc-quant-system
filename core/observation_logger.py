import csv
from datetime import datetime, timezone
from pathlib import Path


OUTPUT_DIR = Path("outputs")
OBSERVATION_EVENTS_FILE = OUTPUT_DIR / "observation_events.csv"
DASHBOARD_EPISODES_FILE = OUTPUT_DIR / "dashboard_episodes.csv"
THROTTLE_ROWS = 5

NO_STRONG_STATE = "NO_STRONG_CONFLUENCE"
ACTIVE_STATES = {
    "WEAK_CONFLUENCE",
    "MODERATE_CONFLUENCE",
    "STRONG_CONFLUENCE",
}

EVENT_FIELDNAMES = [
    "event_timestamp_utc",
    "market_timestamp",
    "row_id",
    "event_type",
    "previous_dashboard_state",
    "new_dashboard_state",
    "dashboard_score",
    "dashboard_conditions",
    "price",
    "rvi",
    "velocity",
    "delta_zscore",
    "gaussian_extreme",
    "distribution_shift",
    "climactic_volume",
    "velocity_shock",
    "velocity_exhaustion",
    "abnormal_spread",
    "delta_zscore_extreme",
]

EPISODE_FIELDNAMES = [
    "episode_id",
    "episode_start_timestamp_utc",
    "episode_end_timestamp_utc",
    "duration_seconds",
    "start_row_id",
    "end_row_id",
    "peak_dashboard_score",
    "peak_dashboard_state",
    "peak_conditions",
    "start_price",
    "end_price",
    "peak_rvi",
    "peak_velocity",
    "peak_delta_zscore",
]

_previous_dashboard_state = None
_last_event_row_by_type = {}
_active_episode = None
_episode_counter = 0


def log_observation_events(row, statistics, row_id):
    try:
        _log_observation_events(row, statistics, row_id)
    except Exception:
        return


def _log_observation_events(row, statistics, row_id):
    global _previous_dashboard_state

    _ensure_csv_file(
        OBSERVATION_EVENTS_FILE,
        EVENT_FIELDNAMES
    )
    _ensure_csv_file(
        DASHBOARD_EPISODES_FILE,
        EPISODE_FIELDNAMES
    )

    event_timestamp = datetime.now(timezone.utc).isoformat()
    market_timestamp = _get_market_timestamp(row)

    previous_state = (
        _previous_dashboard_state
        if _previous_dashboard_state is not None
        else NO_STRONG_STATE
    )

    new_state = _get(
        statistics,
        "statistical_dashboard_state",
        NO_STRONG_STATE
    )

    dashboard_score = _to_number(
        _get(
            statistics,
            "statistical_dashboard_score",
            0
        )
    )

    dashboard_conditions = _format_conditions(
        _get(
            statistics,
            "statistical_dashboard_conditions",
            []
        )
    )

    delta_zscore = _to_number(
        _get(
            statistics,
            "delta_zscore"
        )
    )

    delta_zscore_extreme = (
        delta_zscore is not None
        and abs(delta_zscore) >= 2
    )

    _update_dashboard_episode(
        row=row,
        row_id=row_id,
        event_timestamp=event_timestamp,
        previous_state=previous_state,
        new_state=new_state,
        dashboard_score=dashboard_score,
        dashboard_conditions=dashboard_conditions,
        delta_zscore=delta_zscore,
    )

    event_types = []

    if new_state != previous_state:
        event_types.append(
            (
                "DASHBOARD_STATE_CHANGE",
                True
            )
        )

    if (
        new_state in ACTIVE_STATES
        and dashboard_score >= 2
    ):
        event_types.append(
            (
                "DASHBOARD_ACTIVE",
                False
            )
        )

    if _is_true(
        _get(
            statistics,
            "gaussian_extreme"
        )
    ):
        event_types.append(("GAUSSIAN_EXTREME", False))

    if _is_true(
        _get(
            statistics,
            "distribution_shift"
        )
    ):
        event_types.append(("DISTRIBUTION_SHIFT", False))

    if _is_true(
        _get(
            statistics,
            "climactic_volume"
        )
    ):
        event_types.append(("CLIMACTIC_VOLUME", False))

    if _is_true(
        _get(
            statistics,
            "velocity_shock"
        )
    ):
        event_types.append(("VELOCITY_SHOCK", False))

    if _is_true(
        _get(
            statistics,
            "velocity_exhaustion"
        )
    ):
        event_types.append(("VELOCITY_EXHAUSTION", False))

    if _is_true(
        _get(
            statistics,
            "abnormal_spread"
        )
    ):
        event_types.append(("ABNORMAL_SPREAD_EXECUTION_RISK", False))

    if delta_zscore_extreme:
        event_types.append(("DELTA_ZSCORE_EXTREME", False))

    rows = []

    for event_type, force_write in event_types:
        if _should_write_event(
            event_type,
            row_id,
            force_write
        ):
            rows.append(
                _build_event_row(
                    row=row,
                    statistics=statistics,
                    row_id=row_id,
                    event_timestamp=event_timestamp,
                    market_timestamp=market_timestamp,
                    event_type=event_type,
                    previous_state=previous_state,
                    new_state=new_state,
                    dashboard_score=dashboard_score,
                    dashboard_conditions=dashboard_conditions,
                    delta_zscore=delta_zscore,
                    delta_zscore_extreme=delta_zscore_extreme,
                )
            )

    if rows:
        _append_rows(
            OBSERVATION_EVENTS_FILE,
            EVENT_FIELDNAMES,
            rows
        )

    _previous_dashboard_state = new_state


def _update_dashboard_episode(
    row,
    row_id,
    event_timestamp,
    previous_state,
    new_state,
    dashboard_score,
    dashboard_conditions,
    delta_zscore,
):
    global _active_episode
    global _episode_counter

    if (
        previous_state == NO_STRONG_STATE
        and new_state in ACTIVE_STATES
    ):
        _episode_counter += 1
        _active_episode = {
            "episode_id": _episode_counter,
            "episode_start_timestamp_utc": event_timestamp,
            "start_row_id": row_id,
            "peak_dashboard_score": dashboard_score,
            "peak_dashboard_state": new_state,
            "peak_conditions": dashboard_conditions,
            "start_price": _get(row, "close"),
            "peak_rvi": _to_number(_get(row, "rvi")),
            "peak_velocity": _to_number(_get(row, "velocity")),
            "peak_delta_zscore": delta_zscore,
        }
        return

    if _active_episode is None:
        return

    _update_episode_peak(
        row=row,
        new_state=new_state,
        dashboard_score=dashboard_score,
        dashboard_conditions=dashboard_conditions,
        delta_zscore=delta_zscore,
    )

    if (
        previous_state in ACTIVE_STATES
        and new_state == NO_STRONG_STATE
    ):
        episode_row = _build_episode_row(
            row=row,
            row_id=row_id,
            event_timestamp=event_timestamp,
        )
        _append_rows(
            DASHBOARD_EPISODES_FILE,
            EPISODE_FIELDNAMES,
            [episode_row]
        )
        _active_episode = None


def _update_episode_peak(
    row,
    new_state,
    dashboard_score,
    dashboard_conditions,
    delta_zscore,
):
    current_peak_score = _active_episode.get(
        "peak_dashboard_score",
        0
    )

    if dashboard_score >= current_peak_score:
        _active_episode["peak_dashboard_score"] = dashboard_score
        _active_episode["peak_dashboard_state"] = new_state
        _active_episode["peak_conditions"] = dashboard_conditions

    rvi = _to_number(_get(row, "rvi"))
    velocity = _to_number(_get(row, "velocity"))

    if rvi is not None:
        peak_rvi = _active_episode.get("peak_rvi")
        if peak_rvi is None or rvi > peak_rvi:
            _active_episode["peak_rvi"] = rvi

    if velocity is not None:
        peak_velocity = _active_episode.get("peak_velocity")
        if peak_velocity is None or velocity > peak_velocity:
            _active_episode["peak_velocity"] = velocity

    if delta_zscore is not None:
        peak_delta_zscore = _active_episode.get("peak_delta_zscore")
        if (
            peak_delta_zscore is None
            or abs(delta_zscore) > abs(peak_delta_zscore)
        ):
            _active_episode["peak_delta_zscore"] = delta_zscore


def _build_episode_row(row, row_id, event_timestamp):
    start_timestamp = _active_episode["episode_start_timestamp_utc"]

    return {
        "episode_id": _active_episode["episode_id"],
        "episode_start_timestamp_utc": start_timestamp,
        "episode_end_timestamp_utc": event_timestamp,
        "duration_seconds": _duration_seconds(
            start_timestamp,
            event_timestamp
        ),
        "start_row_id": _active_episode["start_row_id"],
        "end_row_id": row_id,
        "peak_dashboard_score": _active_episode["peak_dashboard_score"],
        "peak_dashboard_state": _active_episode["peak_dashboard_state"],
        "peak_conditions": _active_episode["peak_conditions"],
        "start_price": _active_episode["start_price"],
        "end_price": _get(row, "close"),
        "peak_rvi": _active_episode.get("peak_rvi"),
        "peak_velocity": _active_episode.get("peak_velocity"),
        "peak_delta_zscore": _active_episode.get("peak_delta_zscore"),
    }


def _ensure_csv_file(path, fieldnames):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if not path.exists():
        _write_header(
            path,
            fieldnames
        )
        return

    with path.open(
        mode="r",
        newline=""
    ) as file:
        reader = csv.reader(file)
        current_header = next(reader, [])

    if current_header == fieldnames:
        return

    _migrate_csv_header(
        path,
        current_header,
        fieldnames
    )


def _migrate_csv_header(path, current_header, fieldnames):
    if not current_header:
        _write_header(
            path,
            fieldnames
        )
        return

    with path.open(
        mode="r",
        newline=""
    ) as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    with path.open(
        mode="w",
        newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    field: row.get(field, "")
                    for field in fieldnames
                }
            )


def _write_header(path, fieldnames):
    with path.open(
        mode="w",
        newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )
        writer.writeheader()


def _append_rows(path, fieldnames, rows):
    with path.open(
        mode="a",
        newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )
        writer.writerows(rows)


def _build_event_row(
    row,
    statistics,
    row_id,
    event_timestamp,
    market_timestamp,
    event_type,
    previous_state,
    new_state,
    dashboard_score,
    dashboard_conditions,
    delta_zscore,
    delta_zscore_extreme,
):
    return {
        "event_timestamp_utc": event_timestamp,
        "market_timestamp": market_timestamp,
        "row_id": row_id,
        "event_type": event_type,
        "previous_dashboard_state": previous_state,
        "new_dashboard_state": new_state,
        "dashboard_score": dashboard_score,
        "dashboard_conditions": dashboard_conditions,
        "price": _get(row, "close"),
        "rvi": _get(row, "rvi"),
        "velocity": _get(row, "velocity"),
        "delta_zscore": delta_zscore,
        "gaussian_extreme": _get(statistics, "gaussian_extreme"),
        "distribution_shift": _get(statistics, "distribution_shift"),
        "climactic_volume": _get(statistics, "climactic_volume"),
        "velocity_shock": _get(statistics, "velocity_shock"),
        "velocity_exhaustion": _get(statistics, "velocity_exhaustion"),
        "abnormal_spread": _get(statistics, "abnormal_spread"),
        "delta_zscore_extreme": delta_zscore_extreme,
    }


def _should_write_event(event_type, row_id, force_write):
    if force_write:
        _last_event_row_by_type[event_type] = row_id
        return True

    previous_row_id = _last_event_row_by_type.get(event_type)

    if previous_row_id is None:
        _last_event_row_by_type[event_type] = row_id
        return True

    if row_id is None:
        return False

    if row_id - previous_row_id >= THROTTLE_ROWS:
        _last_event_row_by_type[event_type] = row_id
        return True

    return False


def _format_conditions(value):
    if value is None:
        return ""

    if isinstance(value, list):
        return "|".join(str(item) for item in value)

    return str(value)


def _duration_seconds(start_timestamp, end_timestamp):
    try:
        start = datetime.fromisoformat(start_timestamp)
        end = datetime.fromisoformat(end_timestamp)
    except ValueError:
        return None

    return (end - start).total_seconds()


def _get_market_timestamp(row):
    timestamp = (
        _get(row, "end_ts")
        or _get(row, "timestamp")
        or _get(row, "start_ts")
    )

    if timestamp is None:
        return None

    return timestamp


def _to_number(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_true(value):
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    return str(value).strip().lower() in [
        "true",
        "1",
        "yes",
        "y",
    ]


def _get(source, key, default=None):
    if source is None:
        return default

    if isinstance(source, dict):
        return source.get(key, default)

    return getattr(source, key, default)

import argparse
import csv
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("outputs")
DEFAULT_INPUT_FILE = OUTPUT_DIR / "observation_rows.csv"
REPLAY_MARKET_ROWS_FILE = OUTPUT_DIR / "replay_market_rows.csv"
REPLAY_OBSERVATION_EVENTS_FILE = OUTPUT_DIR / "replay_observation_events.csv"
REPLAY_DASHBOARD_EPISODES_FILE = OUTPUT_DIR / "replay_dashboard_episodes.csv"

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

V2_EVENT_FIELDNAMES = [
    "event_timestamp_utc",
    "market_timestamp",
    "row_id",
    "event_type",
    "previous_dashboard_v2_state",
    "new_dashboard_v2_state",
    "dashboard_v2_layer_count",
    "dashboard_v2_max_severity",
    "dashboard_v2_primary_context",
    "dashboard_v2_conditions",
    "dashboard_v2_active_layers",
    "observation_confidence",
    "price",
    "rvi",
    "velocity",
    "delta_zscore",
]

V2_EPISODE_FIELDNAMES = [
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
]

DASHBOARD_CONDITIONS = [
    ("gaussian_extreme", "GAUSSIAN_EXTREME"),
    ("distribution_shift", "DISTRIBUTION_SHIFT"),
    ("climactic_volume", "CLIMACTIC_VOLUME"),
    ("velocity_shock", "VELOCITY_SHOCK"),
    ("velocity_exhaustion", "VELOCITY_EXHAUSTION"),
    ("abnormal_spread", "ABNORMAL_SPREAD_EXECUTION_RISK"),
]


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Generate replay observation CSVs for PHASE 1B observation review. "
            "This is not trading backtesting."
        )
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_FILE),
        help="Historical market rows CSV to replay.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory where replay CSV files will be written.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_file = Path(args.input)
    output_dir = Path(args.output_dir)

    if not input_file.exists():
        raise SystemExit(f"Input file not found: {input_file}")

    market_rows = pd.read_csv(input_file)
    output_dir.mkdir(parents=True, exist_ok=True)

    replay_market_rows_file = output_dir / REPLAY_MARKET_ROWS_FILE.name
    replay_events_file = output_dir / REPLAY_OBSERVATION_EVENTS_FILE.name
    replay_episodes_file = output_dir / REPLAY_DASHBOARD_EPISODES_FILE.name

    market_rows.to_csv(replay_market_rows_file, index=False)

    replay_events, replay_episodes = build_replay_observation(market_rows)

    write_dict_rows(replay_events_file, EVENT_FIELDNAMES, replay_events)
    write_dict_rows(replay_episodes_file, EPISODE_FIELDNAMES, replay_episodes)

    print(f"Input: {input_file}")
    print(f"Replay market rows: {replay_market_rows_file}")
    print(f"Replay observation events: {replay_events_file}")
    print(f"Replay dashboard episodes: {replay_episodes_file}")
    print(f"Rows processed: {len(market_rows)}")
    print(f"Episodes found: {len(replay_episodes)}")
    print(f"Events found: {len(replay_events)}")


def build_replay_observation(market_rows):
    events = []
    episodes = []
    previous_dashboard_state = NO_STRONG_STATE
    last_event_row_by_type = {}
    active_episode = None
    episode_counter = 0

    for row_index, row in market_rows.iterrows():
        row_data = row.to_dict()
        row_id = get_row_id(row_data, row_index)
        event_timestamp = get_event_timestamp(row_data, row_index)
        market_timestamp = get_market_timestamp(row_data)
        dashboard_snapshot = get_dashboard_snapshot(row_data)

        new_dashboard_state = dashboard_snapshot["state"]
        dashboard_score = dashboard_snapshot["score"]
        dashboard_conditions = dashboard_snapshot["conditions"]
        formatted_conditions = format_conditions(dashboard_conditions)
        delta_zscore = to_number(get_value(row_data, "delta_zscore"))
        delta_zscore_extreme = (
            delta_zscore is not None
            and abs(delta_zscore) >= 2
        )

        if (
            previous_dashboard_state == NO_STRONG_STATE
            and new_dashboard_state in ACTIVE_STATES
        ):
            episode_counter += 1
            active_episode = {
                "episode_id": episode_counter,
                "episode_start_timestamp_utc": event_timestamp,
                "start_row_id": row_id,
                "peak_dashboard_score": dashboard_score,
                "peak_dashboard_state": new_dashboard_state,
                "peak_conditions": formatted_conditions,
                "start_price": get_value(row_data, "close"),
                "peak_rvi": to_number(get_value(row_data, "rvi")),
                "peak_velocity": to_number(get_value(row_data, "velocity")),
                "peak_delta_zscore": delta_zscore,
            }

        if active_episode is not None:
            update_episode_peak(
                active_episode,
                row_data,
                new_dashboard_state,
                dashboard_score,
                formatted_conditions,
                delta_zscore,
            )

            if (
                previous_dashboard_state in ACTIVE_STATES
                and new_dashboard_state == NO_STRONG_STATE
            ):
                episodes.append(
                    build_episode_row(
                        active_episode,
                        row_data,
                        row_id,
                        event_timestamp,
                    )
                )
                active_episode = None

        event_types = []

        if new_dashboard_state != previous_dashboard_state:
            event_types.append(("DASHBOARD_STATE_CHANGE", True))

        if (
            new_dashboard_state in ACTIVE_STATES
            and dashboard_score >= 2
        ):
            event_types.append(("DASHBOARD_ACTIVE", False))

        if is_true(get_value(row_data, "gaussian_extreme")):
            event_types.append(("GAUSSIAN_EXTREME", False))

        if is_true(get_value(row_data, "distribution_shift")):
            event_types.append(("DISTRIBUTION_SHIFT", False))

        if is_true(get_value(row_data, "climactic_volume")):
            event_types.append(("CLIMACTIC_VOLUME", False))

        if is_true(get_value(row_data, "velocity_shock")):
            event_types.append(("VELOCITY_SHOCK", False))

        if is_true(get_value(row_data, "velocity_exhaustion")):
            event_types.append(("VELOCITY_EXHAUSTION", False))

        if is_true(get_value(row_data, "abnormal_spread")):
            event_types.append(("ABNORMAL_SPREAD_EXECUTION_RISK", False))

        if delta_zscore_extreme:
            event_types.append(("DELTA_ZSCORE_EXTREME", False))

        for event_type, force_write in event_types:
            if should_write_event(
                last_event_row_by_type,
                event_type,
                row_id,
                force_write,
            ):
                events.append(
                    build_event_row(
                        row_data=row_data,
                        row_id=row_id,
                        event_timestamp=event_timestamp,
                        market_timestamp=market_timestamp,
                        event_type=event_type,
                        previous_state=previous_dashboard_state,
                        new_state=new_dashboard_state,
                        dashboard_score=dashboard_score,
                        dashboard_conditions=formatted_conditions,
                        delta_zscore=delta_zscore,
                        delta_zscore_extreme=delta_zscore_extreme,
                    )
                )

        previous_dashboard_state = new_dashboard_state

    return events, episodes


def build_replay_observation_v2(market_rows):
    events = []
    episodes = []
    previous_state = "NO_CONFLUENCE"
    active_episode = None
    episode_counter = 0

    for row_index, row in market_rows.iterrows():
        row_data = row.to_dict()
        row_id = get_row_id(row_data, row_index)
        event_timestamp = get_v2_event_timestamp(row_data, row_index)
        market_timestamp = get_v2_market_timestamp(row_data)
        snapshot = get_dashboard_v2_snapshot(row_data)
        new_state = snapshot["state"]
        is_active = new_state != "NO_CONFLUENCE"

        if previous_state == "NO_CONFLUENCE" and is_active:
            episode_counter += 1
            active_episode = {
                "episode_id": episode_counter,
                "episode_start_timestamp_utc": event_timestamp,
                "start_row_id": row_id,
                "peak_state": new_state,
                "peak_layer_count": snapshot["layer_count"],
                "peak_max_severity": snapshot["max_severity"],
                "peak_primary_context": snapshot["primary_context"],
                "peak_conditions": snapshot["conditions"],
                "peak_active_layers": snapshot["active_layers"],
                "peak_observation_confidence": snapshot[
                    "observation_confidence"
                ],
                "start_price": get_value(row_data, "close"),
                "peak_rvi": to_number(get_value(row_data, "rvi")),
                "peak_velocity": to_number(get_value(row_data, "velocity")),
                "peak_delta_zscore": to_number(
                    get_value(row_data, "delta_zscore")
                ),
            }

        if active_episode is not None:
            update_v2_episode_peak(
                active_episode,
                row_data,
                snapshot,
            )

            if is_active is False and previous_state != "NO_CONFLUENCE":
                episodes.append(
                    build_v2_episode_row(
                        active_episode,
                        row_data,
                        row_id,
                        event_timestamp,
                    )
                )
                active_episode = None

        if new_state != previous_state:
            events.append(
                build_v2_event_row(
                    row_data=row_data,
                    row_id=row_id,
                    event_timestamp=event_timestamp,
                    market_timestamp=market_timestamp,
                    event_type="DASHBOARD_V2_STATE_CHANGE",
                    previous_state=previous_state,
                    new_state=new_state,
                    snapshot=snapshot,
                )
            )

        if is_active:
            events.append(
                build_v2_event_row(
                    row_data=row_data,
                    row_id=row_id,
                    event_timestamp=event_timestamp,
                    market_timestamp=market_timestamp,
                    event_type="DASHBOARD_V2_ACTIVE",
                    previous_state=previous_state,
                    new_state=new_state,
                    snapshot=snapshot,
                )
            )

        previous_state = new_state

    return events, episodes


def get_dashboard_v2_snapshot(row_data):
    state = get_value(row_data, "dashboard_v2_state", "NO_CONFLUENCE")

    if state is None:
        state = "NO_CONFLUENCE"

    return {
        "state": str(state),
        "layer_count": to_int(
            get_value(row_data, "dashboard_v2_layer_count"),
            0,
        ),
        "max_severity": get_value(row_data, "dashboard_v2_max_severity"),
        "primary_context": get_value(
            row_data,
            "dashboard_v2_primary_context",
        ),
        "conditions": format_conditions(
            get_value(row_data, "dashboard_v2_conditions")
        ),
        "active_layers": format_conditions(
            get_value(row_data, "dashboard_v2_active_layers")
        ),
        "observation_confidence": get_value(
            row_data,
            "observation_confidence",
        ),
    }


def get_v2_market_timestamp(row_data):
    timestamp = (
        get_value(row_data, "market_timestamp")
        or get_value(row_data, "end_ts")
        or get_value(row_data, "timestamp")
        or get_value(row_data, "start_ts")
    )

    if timestamp is None:
        return None

    return timestamp


def get_v2_event_timestamp(row_data, row_index):
    market_timestamp = get_v2_market_timestamp(row_data)

    if market_timestamp is not None:
        return str(market_timestamp)

    return f"REPLAY_ROW_{row_index + 1}"


def build_v2_event_row(
    row_data,
    row_id,
    event_timestamp,
    market_timestamp,
    event_type,
    previous_state,
    new_state,
    snapshot,
):
    return {
        "event_timestamp_utc": event_timestamp,
        "market_timestamp": market_timestamp,
        "row_id": row_id,
        "event_type": event_type,
        "previous_dashboard_v2_state": previous_state,
        "new_dashboard_v2_state": new_state,
        "dashboard_v2_layer_count": snapshot["layer_count"],
        "dashboard_v2_max_severity": snapshot["max_severity"],
        "dashboard_v2_primary_context": snapshot["primary_context"],
        "dashboard_v2_conditions": snapshot["conditions"],
        "dashboard_v2_active_layers": snapshot["active_layers"],
        "observation_confidence": snapshot["observation_confidence"],
        "price": get_value(row_data, "close"),
        "rvi": get_value(row_data, "rvi"),
        "velocity": get_value(row_data, "velocity"),
        "delta_zscore": get_value(row_data, "delta_zscore"),
    }


def update_v2_episode_peak(active_episode, row_data, snapshot):
    if (
        snapshot["layer_count"]
        >= active_episode.get("peak_layer_count", 0)
    ):
        active_episode["peak_state"] = snapshot["state"]
        active_episode["peak_layer_count"] = snapshot["layer_count"]
        active_episode["peak_max_severity"] = snapshot["max_severity"]
        active_episode["peak_primary_context"] = snapshot["primary_context"]
        active_episode["peak_conditions"] = snapshot["conditions"]
        active_episode["peak_active_layers"] = snapshot["active_layers"]
        active_episode["peak_observation_confidence"] = snapshot[
            "observation_confidence"
        ]

    rvi = to_number(get_value(row_data, "rvi"))
    velocity = to_number(get_value(row_data, "velocity"))
    delta_zscore = to_number(get_value(row_data, "delta_zscore"))

    if rvi is not None:
        peak_rvi = active_episode.get("peak_rvi")
        if peak_rvi is None or rvi > peak_rvi:
            active_episode["peak_rvi"] = rvi

    if velocity is not None:
        peak_velocity = active_episode.get("peak_velocity")
        if peak_velocity is None or velocity > peak_velocity:
            active_episode["peak_velocity"] = velocity

    if delta_zscore is not None:
        peak_delta_zscore = active_episode.get("peak_delta_zscore")
        if (
            peak_delta_zscore is None
            or abs(delta_zscore) > abs(peak_delta_zscore)
        ):
            active_episode["peak_delta_zscore"] = delta_zscore


def build_v2_episode_row(
    active_episode,
    row_data,
    row_id,
    event_timestamp,
):
    start_timestamp = active_episode["episode_start_timestamp_utc"]

    return {
        "episode_id": active_episode["episode_id"],
        "episode_start_timestamp_utc": start_timestamp,
        "episode_end_timestamp_utc": event_timestamp,
        "duration_seconds": duration_seconds(start_timestamp, event_timestamp),
        "start_row_id": active_episode["start_row_id"],
        "end_row_id": row_id,
        "peak_state": active_episode["peak_state"],
        "peak_layer_count": active_episode["peak_layer_count"],
        "peak_max_severity": active_episode["peak_max_severity"],
        "peak_primary_context": active_episode["peak_primary_context"],
        "peak_conditions": active_episode["peak_conditions"],
        "peak_active_layers": active_episode["peak_active_layers"],
        "peak_observation_confidence": active_episode[
            "peak_observation_confidence"
        ],
        "start_price": active_episode["start_price"],
        "end_price": get_value(row_data, "close"),
        "peak_rvi": active_episode.get("peak_rvi"),
        "peak_velocity": active_episode.get("peak_velocity"),
        "peak_delta_zscore": active_episode.get("peak_delta_zscore"),
    }


def get_dashboard_snapshot(row_data):
    state = get_value(row_data, "statistical_dashboard_state")
    score = to_number(get_value(row_data, "statistical_dashboard_score"))
    conditions = get_value(row_data, "statistical_dashboard_conditions")

    if state is not None and score is not None:
        return {
            "state": str(state),
            "score": int(score),
            "conditions": parse_conditions(conditions),
        }

    active_conditions = []

    for field, label in DASHBOARD_CONDITIONS:
        if is_true(get_value(row_data, field)):
            active_conditions.append(label)

    delta_zscore = to_number(get_value(row_data, "delta_zscore"))

    if delta_zscore is not None and abs(delta_zscore) >= 2:
        active_conditions.append("DELTA_ZSCORE_EXTREME")

    score = len(active_conditions)

    if score <= 1:
        state = NO_STRONG_STATE
    elif score <= 3:
        state = "WEAK_CONFLUENCE"
    elif score <= 5:
        state = "MODERATE_CONFLUENCE"
    else:
        state = "STRONG_CONFLUENCE"

    return {
        "state": state,
        "score": score,
        "conditions": active_conditions,
    }


def build_event_row(
    row_data,
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
        "price": get_value(row_data, "close"),
        "rvi": get_value(row_data, "rvi"),
        "velocity": get_value(row_data, "velocity"),
        "delta_zscore": delta_zscore,
        "gaussian_extreme": get_value(row_data, "gaussian_extreme"),
        "distribution_shift": get_value(row_data, "distribution_shift"),
        "climactic_volume": get_value(row_data, "climactic_volume"),
        "velocity_shock": get_value(row_data, "velocity_shock"),
        "velocity_exhaustion": get_value(row_data, "velocity_exhaustion"),
        "abnormal_spread": get_value(row_data, "abnormal_spread"),
        "delta_zscore_extreme": delta_zscore_extreme,
    }


def update_episode_peak(
    active_episode,
    row_data,
    new_state,
    dashboard_score,
    dashboard_conditions,
    delta_zscore,
):
    current_peak_score = active_episode.get("peak_dashboard_score", 0)

    if dashboard_score >= current_peak_score:
        active_episode["peak_dashboard_score"] = dashboard_score
        active_episode["peak_dashboard_state"] = new_state
        active_episode["peak_conditions"] = dashboard_conditions

    rvi = to_number(get_value(row_data, "rvi"))
    velocity = to_number(get_value(row_data, "velocity"))

    if rvi is not None:
        peak_rvi = active_episode.get("peak_rvi")
        if peak_rvi is None or rvi > peak_rvi:
            active_episode["peak_rvi"] = rvi

    if velocity is not None:
        peak_velocity = active_episode.get("peak_velocity")
        if peak_velocity is None or velocity > peak_velocity:
            active_episode["peak_velocity"] = velocity

    if delta_zscore is not None:
        peak_delta_zscore = active_episode.get("peak_delta_zscore")
        if (
            peak_delta_zscore is None
            or abs(delta_zscore) > abs(peak_delta_zscore)
        ):
            active_episode["peak_delta_zscore"] = delta_zscore


def build_episode_row(active_episode, row_data, row_id, event_timestamp):
    start_timestamp = active_episode["episode_start_timestamp_utc"]

    return {
        "episode_id": active_episode["episode_id"],
        "episode_start_timestamp_utc": start_timestamp,
        "episode_end_timestamp_utc": event_timestamp,
        "duration_seconds": duration_seconds(start_timestamp, event_timestamp),
        "start_row_id": active_episode["start_row_id"],
        "end_row_id": row_id,
        "peak_dashboard_score": active_episode["peak_dashboard_score"],
        "peak_dashboard_state": active_episode["peak_dashboard_state"],
        "peak_conditions": active_episode["peak_conditions"],
        "start_price": active_episode["start_price"],
        "end_price": get_value(row_data, "close"),
        "peak_rvi": active_episode.get("peak_rvi"),
        "peak_velocity": active_episode.get("peak_velocity"),
        "peak_delta_zscore": active_episode.get("peak_delta_zscore"),
    }


def should_write_event(last_event_row_by_type, event_type, row_id, force_write):
    if force_write:
        last_event_row_by_type[event_type] = row_id
        return True

    previous_row_id = last_event_row_by_type.get(event_type)

    if previous_row_id is None:
        last_event_row_by_type[event_type] = row_id
        return True

    if row_id is None:
        return False

    if row_id - previous_row_id >= THROTTLE_ROWS:
        last_event_row_by_type[event_type] = row_id
        return True

    return False


def write_dict_rows(path, fieldnames, rows):
    with path.open(mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def get_row_id(row_data, row_index):
    for key in ["row_id", "row_counter", "id"]:
        value = to_number(get_value(row_data, key))

        if value is not None:
            return int(value)

    return int(row_index) + 1


def get_market_timestamp(row_data):
    timestamp = (
        get_value(row_data, "end_ts")
        or get_value(row_data, "timestamp")
        or get_value(row_data, "start_ts")
    )

    if timestamp is None:
        return None

    return timestamp


def get_event_timestamp(row_data, row_index):
    market_timestamp = get_market_timestamp(row_data)

    if market_timestamp is not None:
        return str(market_timestamp)

    return f"REPLAY_ROW_{row_index + 1}"


def duration_seconds(start_timestamp, end_timestamp):
    start = parse_datetime(start_timestamp)
    end = parse_datetime(end_timestamp)

    if start is None or end is None:
        return None

    return (end - start).total_seconds()


def parse_datetime(value):
    if value is None:
        return None

    if isinstance(value, (int, float)) and not math.isnan(value):
        timestamp = float(value)

        if timestamp > 10_000_000_000:
            timestamp = timestamp / 1000

        try:
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None

    text = str(value).strip()

    if not text:
        return None

    try:
        numeric_timestamp = float(text)
    except ValueError:
        numeric_timestamp = None

    if numeric_timestamp is not None:
        if numeric_timestamp > 10_000_000_000:
            numeric_timestamp = numeric_timestamp / 1000

        try:
            return datetime.fromtimestamp(numeric_timestamp, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None

    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"

    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def format_conditions(value):
    if value is None:
        return ""

    if isinstance(value, list):
        return "|".join(str(item) for item in value)

    return str(value)


def parse_conditions(value):
    if value is None:
        return []

    if isinstance(value, list):
        return value

    text = str(value).strip()

    if not text:
        return []

    for separator in ["|", ";", ","]:
        if separator in text:
            return [
                item.strip()
                for item in text.split(separator)
                if item.strip()
            ]

    return [text]


def to_number(value):
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if math.isnan(number):
        return None

    return number


def to_int(value, default=None):
    number = to_number(value)

    if number is None:
        return default

    return int(number)


def is_true(value):
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    if isinstance(value, float) and math.isnan(value):
        return False

    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
        "y",
    }


def get_value(row_data, key, default=None):
    value = row_data.get(key, default)

    if value is None:
        return default

    if isinstance(value, float) and math.isnan(value):
        return default

    return value


if __name__ == "__main__":
    main()

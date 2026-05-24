from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
MARKET_ROWS_FILE = OUTPUT_DIR / "market_rows.csv"
OBSERVATION_EVENTS_FILE = OUTPUT_DIR / "observation_events.csv"
DASHBOARD_EPISODES_FILE = OUTPUT_DIR / "dashboard_episodes.csv"
REPLAY_MARKET_ROWS_FILE = OUTPUT_DIR / "replay_market_rows.csv"
REPLAY_OBSERVATION_EVENTS_FILE = OUTPUT_DIR / "replay_observation_events.csv"
REPLAY_DASHBOARD_EPISODES_FILE = OUTPUT_DIR / "replay_dashboard_episodes.csv"
HISTORICAL_OBSERVATION_ROWS_FILE = OUTPUT_DIR / "historical_observation_rows.csv"
HISTORICAL_REPLAY_OBSERVATION_EVENTS_FILE = (
    OUTPUT_DIR / "historical_replay_observation_events.csv"
)
HISTORICAL_REPLAY_DASHBOARD_EPISODES_FILE = (
    OUTPUT_DIR / "historical_replay_dashboard_episodes.csv"
)
HISTORICAL_REPLAY_OBSERVATION_V2_EVENTS_FILE = (
    OUTPUT_DIR / "historical_replay_observation_v2_events.csv"
)
HISTORICAL_REPLAY_DASHBOARD_V2_EPISODES_FILE = (
    OUTPUT_DIR / "historical_replay_dashboard_v2_episodes.csv"
)

OBSERVATION_FILE_SOURCES = {
    "LIVE": {
        "market_rows": MARKET_ROWS_FILE,
        "observation_events": OBSERVATION_EVENTS_FILE,
        "dashboard_episodes": DASHBOARD_EPISODES_FILE,
    },
    "RECORDED REPLAY": {
        "market_rows": REPLAY_MARKET_ROWS_FILE,
        "observation_events": REPLAY_OBSERVATION_EVENTS_FILE,
        "dashboard_episodes": REPLAY_DASHBOARD_EPISODES_FILE,
    },
    "HISTORICAL REPLAY": {
        "market_rows": HISTORICAL_OBSERVATION_ROWS_FILE,
        "observation_events": HISTORICAL_REPLAY_OBSERVATION_EVENTS_FILE,
        "dashboard_episodes": HISTORICAL_REPLAY_DASHBOARD_EPISODES_FILE,
    },
}

NO_STRONG_STATE = "NO_STRONG_CONFLUENCE"
STATE_OPTIONS = [
    "WEAK_CONFLUENCE",
    "MODERATE_CONFLUENCE",
    "STRONG_CONFLUENCE",
]

STATE_RANK = {
    "NO_STRONG_CONFLUENCE": 0,
    "WEAK_CONFLUENCE": 1,
    "MODERATE_CONFLUENCE": 2,
    "STRONG_CONFLUENCE": 3,
}

IMPORTANT_EVENT_COLUMNS = [
    "gaussian_extreme",
    "distribution_shift",
    "climactic_volume",
    "velocity_shock",
    "velocity_exhaustion",
    "abnormal_spread",
    "delta_zscore_extreme",
]

ARCHIVE_V2_FIELDS = [
    "price_zscore",
    "volume_zscore",
    "velocity_zscore",
    "spread_zscore",
    "price_percentile_zone",
    "distribution_shift_state",
    "distribution_shift_strength",
    "gaussian_zone",
    "gaussian_tail",
    "gaussian_confidence",
    "price_tail_risk",
    "price_tail_persistence",
    "price_tail_exhaustion",
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
    "price_extreme_event",
    "volume_extreme_event",
    "delta_extreme_event",
    "velocity_extreme_event",
    "spread_extreme_event",
    "extreme_event_state",
    "extreme_event_context",
    "extreme_event_origin",
]


def read_csv_safely(path):
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    except Exception as error:
        st.warning(f"Could not read {path.name}: {error}")
        return pd.DataFrame()


def ensure_csv_cache_state():
    if "csv_cache" not in st.session_state:
        st.session_state["csv_cache"] = {}


def read_csv_with_mtime_cache(path, force_refresh=False):
    ensure_csv_cache_state()

    cache_key = str(path)
    csv_cache = st.session_state["csv_cache"]
    cached_snapshot = csv_cache.get(
        cache_key,
        {
            "mtime": None,
            "dataframe": pd.DataFrame(),
        },
    )

    if not path.exists():
        csv_cache[cache_key] = {
            "mtime": None,
            "dataframe": cached_snapshot["dataframe"],
        }
        return cached_snapshot["dataframe"]

    try:
        current_mtime = path.stat().st_mtime
    except OSError:
        st.warning("Data file is being updated, using last valid snapshot.")
        return cached_snapshot["dataframe"]

    if (
        not force_refresh
        and cached_snapshot["mtime"] == current_mtime
    ):
        return cached_snapshot["dataframe"]

    try:
        dataframe = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        dataframe = pd.DataFrame()
    except Exception:
        st.warning("Data file is being updated, using last valid snapshot.")
        return cached_snapshot["dataframe"]

    csv_cache[cache_key] = {
        "mtime": current_mtime,
        "dataframe": dataframe,
    }

    return dataframe


def load_dashboard_data(file_sources, force_refresh=False):
    return (
        read_csv_with_mtime_cache(file_sources["market_rows"], force_refresh),
        read_csv_with_mtime_cache(file_sources["observation_events"], force_refresh),
        read_csv_with_mtime_cache(file_sources["dashboard_episodes"], force_refresh),
    )


def load_historical_dashboard_v2_data(force_refresh=False):
    return (
        read_csv_with_mtime_cache(
            HISTORICAL_REPLAY_OBSERVATION_V2_EVENTS_FILE,
            force_refresh,
        ),
        read_csv_with_mtime_cache(
            HISTORICAL_REPLAY_DASHBOARD_V2_EPISODES_FILE,
            force_refresh,
        ),
    )


def get_latest_row(dataframe):
    if dataframe.empty:
        return None

    return dataframe.iloc[-1]


def get_column_value(row, column, default=None):
    if row is None:
        return default

    if column not in row.index:
        return default

    value = row[column]

    if pd.isna(value):
        return default

    return value


def get_state_column(dataframe):
    if "new_dashboard_state" in dataframe.columns:
        return "new_dashboard_state"

    if "dashboard_state" in dataframe.columns:
        return "dashboard_state"

    if "statistical_dashboard_state" in dataframe.columns:
        return "statistical_dashboard_state"

    return None


def get_score_column(dataframe):
    if "dashboard_score" in dataframe.columns:
        return "dashboard_score"

    if "statistical_dashboard_score" in dataframe.columns:
        return "statistical_dashboard_score"

    return None


def get_conditions_column(dataframe):
    if "dashboard_conditions" in dataframe.columns:
        return "dashboard_conditions"

    if "statistical_dashboard_conditions" in dataframe.columns:
        return "statistical_dashboard_conditions"

    return None


def get_timestamp_column(dataframe):
    if "event_timestamp_utc" in dataframe.columns:
        return "event_timestamp_utc"

    if "timestamp" in dataframe.columns:
        return "timestamp"

    return None


def build_row_market_time_map(market_rows):
    if (
        market_rows.empty
        or "row_id" not in market_rows.columns
        or "market_timestamp" not in market_rows.columns
    ):
        return {}

    row_time_map = {}

    for _, row in market_rows.iterrows():
        row_id = normalize_row_id(row.get("row_id"))

        if row_id is None:
            continue

        row_time_map[row_id] = row.get("market_timestamp")

    return row_time_map


def add_market_time_to_events(observation_events, market_rows):
    if observation_events.empty:
        return observation_events

    row_time_map = build_row_market_time_map(market_rows)
    events = observation_events.copy()

    events["market_time"] = events.apply(
        lambda row: format_market_time(
            get_event_market_timestamp(row, row_time_map)
        ),
        axis=1,
    )

    return events


def add_market_time_to_episodes(dashboard_episodes, market_rows):
    if dashboard_episodes.empty:
        return dashboard_episodes

    row_time_map = build_row_market_time_map(market_rows)
    episodes = dashboard_episodes.copy()

    episodes["start_market_time"] = episodes.apply(
        lambda row: format_market_time(
            get_episode_market_timestamp(
                row,
                row_time_map,
                "start_row_id",
                "episode_start_timestamp_utc",
            )
        ),
        axis=1,
    )
    episodes["end_market_time"] = episodes.apply(
        lambda row: format_market_time(
            get_episode_market_timestamp(
                row,
                row_time_map,
                "end_row_id",
                "episode_end_timestamp_utc",
            )
        ),
        axis=1,
    )

    return episodes


def get_episode_date_options(dashboard_episodes, market_rows):
    episodes = add_market_time_to_episodes(
        dashboard_episodes,
        market_rows,
    )

    if episodes.empty or "start_market_time" not in episodes.columns:
        return ["All dates"]

    dates = sorted(
        {
            str(value)[:10]
            for value in episodes["start_market_time"].dropna()
            if str(value).strip()
        }
    )

    return ["All dates"] + dates


def get_episode_id_options(dashboard_episodes):
    if dashboard_episodes.empty or "episode_id" not in dashboard_episodes.columns:
        return ["All episodes"]

    episode_ids = sorted(
        {
            str(value)
            for value in dashboard_episodes["episode_id"].dropna()
            if str(value).strip()
        },
        key=lambda value: int(float(value))
        if value.replace(".", "", 1).isdigit()
        else value,
    )

    return ["All episodes"] + episode_ids


def get_event_market_timestamp(row, row_time_map):
    market_timestamp = row.get("market_timestamp")

    if has_display_value(market_timestamp):
        return market_timestamp

    row_id = normalize_row_id(row.get("row_id"))

    if row_id in row_time_map:
        return row_time_map[row_id]

    return row.get("event_timestamp_utc")


def get_episode_market_timestamp(
    row,
    row_time_map,
    row_id_column,
    fallback_column,
):
    row_id = normalize_row_id(row.get(row_id_column))

    if row_id in row_time_map:
        return row_time_map[row_id]

    return row.get(fallback_column)


def normalize_row_id(value):
    if not has_display_value(value):
        return None

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return str(value)


def has_display_value(value):
    if value is None:
        return False

    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        return True

    text = str(value).strip()

    return text != ""


def format_market_time(value):
    if not has_display_value(value):
        return ""

    parsed_datetime = parse_market_datetime(value)

    if parsed_datetime is None:
        return str(value)

    return parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")


def parse_market_datetime(value):
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()

        try:
            timestamp = float(text)
        except ValueError:
            timestamp = None

        if timestamp is not None:
            if timestamp > 10_000_000_000:
                timestamp = timestamp / 1000

            try:
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
            except (OverflowError, OSError, ValueError):
                return None

        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"

        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc)

    return parsed


def parse_conditions(value):
    if value is None:
        return []

    if isinstance(value, list):
        return value

    value = str(value).strip()

    if not value:
        return []

    for separator in ["|", ";", ","]:
        if separator in value:
            return [
                item.strip()
                for item in value.split(separator)
                if item.strip()
            ]

    return [value]


def sanitize_dataframe_for_display(dataframe):
    display_dataframe = dataframe.copy()

    for column in display_dataframe.columns:
        if display_dataframe[column].dtype == "object":
            display_dataframe[column] = display_dataframe[column].map(
                sanitize_display_value
            )

    return display_dataframe.fillna("")


def sanitize_display_value(value):
    if value is None:
        return ""

    if isinstance(value, float) and pd.isna(value):
        return ""

    if isinstance(value, (list, tuple, set)):
        return "|".join(str(item) for item in value)

    if isinstance(value, dict):
        return "; ".join(
            f"{key}={item}"
            for key, item in value.items()
        )

    return str(value)


def is_truthy(value):
    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return False

    return str(value).strip().lower() in [
        "true",
        "1",
        "yes",
        "y",
    ]


def to_number(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_duration(seconds):
    if seconds is None:
        return "N/A"

    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {remaining_seconds}s"

    if minutes > 0:
        return f"{minutes}m {remaining_seconds}s"

    return f"{remaining_seconds}s"


def get_active_episode(observation_events, latest_market_row):
    if observation_events.empty:
        return None

    state_column = get_state_column(observation_events)
    score_column = get_score_column(observation_events)
    conditions_column = get_conditions_column(observation_events)
    timestamp_column = get_timestamp_column(observation_events)

    if (
        state_column is None
        or score_column is None
        or timestamp_column is None
    ):
        return None

    events = observation_events.copy().reset_index(drop=True)
    latest_event = get_latest_row(events)
    current_state = get_column_value(
        latest_event,
        state_column,
        NO_STRONG_STATE,
    )

    if current_state == NO_STRONG_STATE:
        return None

    previous_state_column = (
        "previous_dashboard_state"
        if "previous_dashboard_state" in events.columns
        else None
    )

    start_index = None

    if previous_state_column is not None:
        start_candidates = events[
            (events[previous_state_column] == NO_STRONG_STATE)
            & (events[state_column].isin(STATE_OPTIONS))
        ]

        if not start_candidates.empty:
            start_index = start_candidates.index[-1]

    if start_index is None:
        active_candidates = events[
            events[state_column].isin(STATE_OPTIONS)
        ]

        if active_candidates.empty:
            return None

        start_index = active_candidates.index[0]

    episode_events = events.loc[start_index:].copy()

    if episode_events.empty:
        return None

    start_event = episode_events.iloc[0]
    start_timestamp = get_column_value(
        start_event,
        timestamp_column,
    )

    start_time = pd.to_datetime(
        start_timestamp,
        utc=True,
        errors="coerce",
    )

    if pd.isna(start_time):
        duration_seconds = None
    else:
        now = pd.Timestamp.utcnow()
        duration_seconds = (now - start_time).total_seconds()

    episode_events[score_column] = pd.to_numeric(
        episode_events[score_column],
        errors="coerce",
    ).fillna(0)

    peak_score = episode_events[score_column].max()
    peak_score_rows = episode_events[
        episode_events[score_column] == peak_score
    ]
    peak_score_row = peak_score_rows.iloc[-1]

    peak_state = max(
        episode_events[state_column],
        key=lambda state: STATE_RANK.get(state, 0),
    )

    peak_conditions = get_column_value(
        peak_score_row,
        conditions_column,
        "",
    )

    current_price = get_column_value(
        latest_market_row,
        "close",
        get_column_value(latest_event, "price"),
    )
    current_rvi = get_column_value(
        latest_market_row,
        "rvi",
        get_column_value(latest_event, "rvi"),
    )
    current_velocity = get_column_value(
        latest_market_row,
        "velocity",
        get_column_value(latest_event, "velocity"),
    )
    current_delta_zscore = get_column_value(
        latest_event,
        "delta_zscore",
    )

    return {
        "episode_start_time": start_timestamp,
        "current_dashboard_state": current_state,
        "duration_so_far": format_duration(duration_seconds),
        "current_dashboard_score": get_column_value(
            latest_event,
            score_column,
            0,
        ),
        "peak_dashboard_score_so_far": peak_score,
        "peak_dashboard_state_so_far": peak_state,
        "peak_conditions_so_far": peak_conditions,
        "current_price": current_price,
        "current_rvi": current_rvi,
        "current_velocity": current_velocity,
        "current_delta_zscore": current_delta_zscore,
    }


def apply_event_filters(
    observation_events,
    minimum_score,
    selected_states,
    latest_only,
):
    if observation_events.empty:
        return observation_events

    filtered = observation_events.copy()
    state_column = get_state_column(filtered)
    score_column = get_score_column(filtered)

    if state_column is not None:
        filtered = filtered[
            filtered[state_column] != NO_STRONG_STATE
        ]

        if selected_states:
            filtered = filtered[
                filtered[state_column].isin(selected_states)
            ]

    if score_column is not None:
        filtered[score_column] = pd.to_numeric(
            filtered[score_column],
            errors="coerce",
        ).fillna(0)
        filtered = filtered[
            filtered[score_column] >= minimum_score
        ]

    if latest_only and not filtered.empty:
        filtered = filtered.tail(1)

    return filtered


def render_metric_cards(market_rows, observation_events, dashboard_episodes):
    latest_market_row = get_latest_row(market_rows)

    filtered_events = observation_events.copy()
    state_column = get_state_column(filtered_events)

    if (
        state_column is not None
        and not filtered_events.empty
    ):
        filtered_events = filtered_events[
            filtered_events[state_column] != NO_STRONG_STATE
        ]

    latest_event = get_latest_row(filtered_events)
    score_column = get_score_column(filtered_events)

    dashboard_state = get_column_value(
        latest_event,
        state_column,
        "Waiting for event",
    )

    dashboard_score = get_column_value(
        latest_event,
        score_column,
        0,
    )

    highest_rvi = (
        market_rows["rvi"].max()
        if "rvi" in market_rows.columns and not market_rows.empty
        else None
    )

    highest_velocity = (
        market_rows["velocity"].max()
        if "velocity" in market_rows.columns and not market_rows.empty
        else None
    )

    highest_dashboard_score = (
        filtered_events[score_column].max()
        if (
            score_column in filtered_events.columns
            and not filtered_events.empty
        )
        else None
    )

    first_row = st.columns(4)
    first_row[0].metric("Latest Event State", dashboard_state)
    first_row[1].metric("Latest Event Score", dashboard_score)
    first_row[2].metric("Highest RVI", highest_rvi if highest_rvi is not None else "N/A")
    first_row[3].metric(
        "Highest Velocity",
        highest_velocity if highest_velocity is not None else "N/A",
    )

    second_row = st.columns(3)
    second_row[0].metric(
        "Highest Dashboard Score",
        highest_dashboard_score if highest_dashboard_score is not None else "N/A",
    )
    second_row[1].metric(
        "Observation Events",
        len(filtered_events),
    )
    second_row[2].metric(
        "Completed Episodes",
        len(dashboard_episodes),
    )

    return latest_market_row, latest_event


def render_latest_row(latest_market_row):
    st.subheader("Latest Row")

    if latest_market_row is None:
        st.info("Waiting for live data...")
        return

    fields = [
        "close",
        "volume",
        "delta",
        "velocity",
        "rvi",
        "adaptive_window",
        "price_zone",
        "volume_zone",
        "delta_zone",
        "velocity_zone",
        "renko_direction",
        "renko_event",
        "renko_bricks",
    ]

    available_fields = [
        field
        for field in fields
        if field in latest_market_row.index
    ]

    if not available_fields:
        st.info("Latest row exists, but expected columns are not available yet.")
        return

    st.dataframe(
        sanitize_dataframe_for_display(
            pd.DataFrame(
                {
                    "field": available_fields,
                    "value": [
                        latest_market_row[field]
                        for field in available_fields
                    ],
                }
            )
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_latest_event(latest_event):
    st.subheader("Latest Dashboard Event")

    if latest_event is None:
        st.info("No meaningful dashboard event yet.")
        return

    display_fields = [
        "market_time",
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
    ]

    available_fields = [
        field
        for field in display_fields
        if field in latest_event.index
    ]

    st.dataframe(
        sanitize_dataframe_for_display(
            pd.DataFrame(
                {
                    "field": available_fields,
                    "value": [
                        latest_event[field]
                        for field in available_fields
                    ],
                }
            )
        ),
        use_container_width=True,
        hide_index=True,
    )

    conditions = parse_conditions(
        get_column_value(
            latest_event,
            "dashboard_conditions",
            "",
        )
    )

    if conditions:
        st.write("Active Conditions:")
        for condition in conditions:
            st.write(f"- {condition}")


def render_active_episode_panel(active_episode):
    st.subheader("Active Dashboard Episode")

    if active_episode is None:
        st.info("No active dashboard episode.")
        return

    metric_row = st.columns(4)
    metric_row[0].metric(
        "Current State",
        active_episode["current_dashboard_state"],
    )
    metric_row[1].metric(
        "Duration So Far",
        active_episode["duration_so_far"],
    )
    metric_row[2].metric(
        "Current Score",
        active_episode["current_dashboard_score"],
    )
    metric_row[3].metric(
        "Peak Score",
        active_episode["peak_dashboard_score_so_far"],
    )

    detail_fields = [
        "episode_start_time",
        "peak_dashboard_state_so_far",
        "peak_conditions_so_far",
        "current_price",
        "current_rvi",
        "current_velocity",
        "current_delta_zscore",
    ]

    st.dataframe(
        sanitize_dataframe_for_display(
            pd.DataFrame(
                {
                    "field": detail_fields,
                    "value": [
                        active_episode[field]
                        for field in detail_fields
                    ],
                }
            )
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_event_history(observation_events):
    st.subheader("Statistical Dashboard Event History")

    if observation_events.empty:
        st.info("No meaningful dashboard events available yet.")
        return

    display_columns = [
        "market_time",
        "row_id",
        "event_type",
        "dashboard_score",
        "dashboard_conditions",
        "price",
        "rvi",
        "velocity",
        "delta_zscore",
    ]

    columns = [
        column
        for column in display_columns
        if column in observation_events.columns
    ]

    st.dataframe(
        sanitize_dataframe_for_display(
            observation_events[columns].tail(100)
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_dashboard_episodes(
    dashboard_episodes,
    episode_date_filter,
    minimum_episode_score,
    episode_score_at_least_4,
    episode_id_filter,
    show_all_episodes,
    episode_sort_order,
):
    st.subheader("Dashboard Episodes")

    if dashboard_episodes.empty:
        st.info("No completed dashboard episodes yet.")
        return

    filtered_episodes = filter_dashboard_episodes(
        dashboard_episodes,
        episode_date_filter,
        minimum_episode_score,
        episode_score_at_least_4,
        episode_id_filter,
        episode_sort_order,
    )

    render_dashboard_episode_summary(
        dashboard_episodes,
        filtered_episodes,
        episode_date_filter,
    )

    display_columns = [
        "episode_id",
        "start_market_time",
        "end_market_time",
        "duration_seconds",
        "peak_dashboard_state",
        "peak_dashboard_score",
        "peak_conditions",
        "start_price",
        "end_price",
        "peak_rvi",
        "peak_velocity",
        "peak_delta_zscore",
    ]

    columns = [
        column
        for column in display_columns
        if column in dashboard_episodes.columns
    ]

    if filtered_episodes.empty:
        st.info("No dashboard episodes match the current filters.")
        return

    display_episodes = (
        filtered_episodes
        if show_all_episodes
        else filtered_episodes.tail(100)
    )

    st.dataframe(
        sanitize_dataframe_for_display(
            display_episodes[columns]
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_historical_dashboard_v2(
    v2_events,
    v2_episodes,
):
    st.subheader("Dashboard V2 Historical Replay")

    metric_columns = st.columns(2)
    metric_columns[0].metric("V2 Events", len(v2_events))
    metric_columns[1].metric("V2 Episodes", len(v2_episodes))

    if not HISTORICAL_REPLAY_OBSERVATION_V2_EVENTS_FILE.exists():
        st.warning(
            "Missing historical_replay_observation_v2_events.csv"
        )

    if not HISTORICAL_REPLAY_DASHBOARD_V2_EPISODES_FILE.exists():
        st.warning(
            "Missing historical_replay_dashboard_v2_episodes.csv"
        )

    render_dashboard_v2_episodes(v2_episodes)
    render_dashboard_v2_events(v2_events)


def render_dashboard_v2_episodes(v2_episodes):
    st.subheader("Dashboard V2 Episodes")
    st.caption(
        "Dashboard V2 episode = period where layer-based statistical "
        "confluence is active."
    )
    st.caption(
        "peak_state = strongest state inside episode | "
        "peak_layer_count = number of active layers at peak | "
        "peak_max_severity = strongest severity inside episode | "
        "peak_primary_context = main context driver | "
        "peak_active_layers = layers involved | "
        "peak_observation_confidence = confidence / caution label"
    )

    if v2_episodes.empty:
        st.info("No Dashboard V2 episodes available yet.")
        return

    display_episodes = v2_episodes.copy()

    if "episode_start_timestamp_utc" in display_episodes.columns:
        display_episodes["episode_start_time_utc"] = (
            display_episodes["episode_start_timestamp_utc"].apply(
                format_market_time
            )
        )

    if "episode_end_timestamp_utc" in display_episodes.columns:
        display_episodes["episode_end_time_utc"] = (
            display_episodes["episode_end_timestamp_utc"].apply(
                format_market_time
            )
        )

    filtered_episodes = filter_dashboard_v2_episodes(display_episodes)

    display_columns = [
        "episode_id",
        "episode_start_time_utc",
        "episode_end_time_utc",
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
    columns = [
        column
        for column in display_columns
        if column in display_episodes.columns
    ]

    if filtered_episodes.empty:
        st.info("No Dashboard V2 episodes match the current filters.")
        return

    st.dataframe(
        sanitize_dataframe_for_display(
            filtered_episodes[columns].tail(100)
        ),
        use_container_width=True,
        hide_index=True,
    )


def filter_dashboard_v2_episodes(display_episodes):
    filter_row_one = st.columns(3)
    filter_row_two = st.columns(3)

    minimum_score = filter_row_one[0].selectbox(
        "Dashboard score >=",
        [2, 3, 4, 5, 6],
        index=0,
        key="dashboard_v2_minimum_score",
    )
    minimum_layer_count = filter_row_one[1].selectbox(
        "peak_layer_count >=",
        list(range(1, 11)),
        index=0,
        key="dashboard_v2_minimum_layer_count",
    )
    severity_filter = filter_row_one[2].selectbox(
        "Severity",
        ["ALL", "LOW", "MEDIUM", "HIGH", "EXTREME"],
        index=0,
        key="dashboard_v2_severity_filter",
    )

    context_filter = filter_row_two[0].selectbox(
        "Context",
        [
            "ALL",
            "DELTA_ZSCORE_EXTREME",
            "GAUSSIAN_EXTREME",
            "DISTRIBUTION_SHIFT",
            "PRICE_ZSCORE",
            "VELOCITY",
            "VOLUME",
            "UNSTABLE_STATISTICAL_CONTEXT",
        ],
        index=0,
        key="dashboard_v2_context_filter",
    )
    date_options = get_dashboard_v2_date_options(display_episodes)
    date_filter = filter_row_two[1].selectbox(
        "Date",
        date_options,
        index=0,
        key="dashboard_v2_date_filter",
    )
    research_candidates_only = filter_row_two[2].checkbox(
        "Show only research candidates",
        value=False,
        key="dashboard_v2_research_candidates_only",
    )

    filtered = display_episodes.copy()
    score_values = get_dashboard_v2_score_values(filtered)
    layer_count_values = pd.to_numeric(
        filtered.get("peak_layer_count", 0),
        errors="coerce",
    ).fillna(0)

    filtered = filtered[score_values >= minimum_score]
    score_values = score_values.loc[filtered.index]
    layer_count_values = layer_count_values.loc[filtered.index]

    filtered = filtered[layer_count_values >= minimum_layer_count]
    score_values = score_values.loc[filtered.index]
    layer_count_values = layer_count_values.loc[filtered.index]

    if severity_filter != "ALL" and "peak_max_severity" in filtered.columns:
        filtered = filtered[
            filtered["peak_max_severity"].astype(str) == severity_filter
        ]
        score_values = score_values.loc[filtered.index]
        layer_count_values = layer_count_values.loc[filtered.index]

    if context_filter != "ALL":
        context_mask = get_dashboard_v2_context_mask(
            filtered,
            context_filter,
        )
        filtered = filtered[context_mask]
        score_values = score_values.loc[filtered.index]
        layer_count_values = layer_count_values.loc[filtered.index]

    if date_filter != "ALL" and "episode_start_time_utc" in filtered.columns:
        filtered = filtered[
            filtered["episode_start_time_utc"].astype(str).str[:10]
            == date_filter
        ]
        score_values = score_values.loc[filtered.index]
        layer_count_values = layer_count_values.loc[filtered.index]

    if research_candidates_only:
        severity_values = (
            filtered["peak_max_severity"].astype(str)
            if "peak_max_severity" in filtered.columns
            else pd.Series("", index=filtered.index)
        )
        candidate_mask = (
            (score_values >= 4)
            | (layer_count_values >= 4)
            | severity_values.isin(["HIGH", "EXTREME"])
        )
        filtered = filtered[candidate_mask]

    st.caption(
        f"Displayed Dashboard V2 episodes: {len(filtered)} / "
        f"{len(display_episodes)}"
    )

    return filtered


def get_dashboard_v2_score_values(display_episodes):
    if "peak_dashboard_score" in display_episodes.columns:
        return pd.to_numeric(
            display_episodes["peak_dashboard_score"],
            errors="coerce",
        ).fillna(0)

    if "dashboard_v2_score" in display_episodes.columns:
        return pd.to_numeric(
            display_episodes["dashboard_v2_score"],
            errors="coerce",
        ).fillna(0)

    if "peak_layer_count" in display_episodes.columns:
        return pd.to_numeric(
            display_episodes["peak_layer_count"],
            errors="coerce",
        ).fillna(0)

    return pd.Series(0, index=display_episodes.index)


def get_dashboard_v2_context_mask(display_episodes, context_filter):
    context_columns = [
        "peak_state",
        "peak_primary_context",
        "peak_conditions",
        "peak_active_layers",
    ]
    available_columns = [
        column
        for column in context_columns
        if column in display_episodes.columns
    ]

    if not available_columns:
        return pd.Series(False, index=display_episodes.index)

    haystack = (
        display_episodes[available_columns]
        .fillna("")
        .astype(str)
        .agg("|".join, axis=1)
        .str.upper()
    )

    return haystack.str.contains(
        context_filter.upper(),
        regex=False,
        na=False,
    )


def get_dashboard_v2_date_options(display_episodes):
    if "episode_start_time_utc" not in display_episodes.columns:
        return ["ALL"]

    dates = sorted(
        {
            str(value)[:10]
            for value in display_episodes["episode_start_time_utc"].dropna()
            if str(value).strip()
        }
    )

    return ["ALL"] + dates


def render_dashboard_v2_events(v2_events):
    st.subheader("Dashboard V2 Events")

    if v2_events.empty:
        st.info("No Dashboard V2 events available yet.")
        return

    display_events = v2_events.copy()

    if "event_timestamp_utc" in display_events.columns:
        display_events["event_time_utc"] = (
            display_events["event_timestamp_utc"].apply(format_market_time)
        )

    if "market_timestamp" in display_events.columns:
        display_events["market_time_utc"] = (
            display_events["market_timestamp"].apply(format_market_time)
        )

    display_columns = [
        "event_time_utc",
        "market_time_utc",
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
    columns = [
        column
        for column in display_columns
        if column in display_events.columns
    ]

    st.dataframe(
        sanitize_dataframe_for_display(
            display_events[columns].tail(100)
        ),
        use_container_width=True,
        hide_index=True,
    )


def filter_dashboard_episodes(
    dashboard_episodes,
    episode_date_filter,
    minimum_episode_score,
    episode_score_at_least_4,
    episode_id_filter,
    episode_sort_order,
):
    filtered = dashboard_episodes.copy()

    effective_minimum_score = (
        max(minimum_episode_score, 4)
        if episode_score_at_least_4
        else minimum_episode_score
    )

    if "peak_dashboard_score" in filtered.columns:
        filtered["peak_dashboard_score"] = pd.to_numeric(
            filtered["peak_dashboard_score"],
            errors="coerce",
        ).fillna(0)
        filtered = filtered[
            filtered["peak_dashboard_score"] >= effective_minimum_score
        ]

    if (
        episode_date_filter != "All dates"
        and "start_market_time" in filtered.columns
    ):
        filtered = filtered[
            filtered["start_market_time"].astype(str).str[:10]
            == episode_date_filter
        ]

    if (
        episode_id_filter != "All episodes"
        and "episode_id" in filtered.columns
    ):
        filtered = filtered[
            filtered["episode_id"].astype(str) == str(episode_id_filter)
        ]

    if episode_sort_order == "Newest first":
        return filtered.sort_values(
            by="start_market_time",
            ascending=False,
            na_position="last",
        )

    if episode_sort_order == "Oldest first":
        return filtered.sort_values(
            by="start_market_time",
            ascending=True,
            na_position="last",
        )

    if episode_sort_order == "Highest score first":
        return filtered.sort_values(
            by=["peak_dashboard_score", "start_market_time"],
            ascending=[False, False],
            na_position="last",
        )

    return filtered


def render_dashboard_episode_summary(
    dashboard_episodes,
    filtered_episodes,
    episode_date_filter,
):
    score_column = (
        pd.to_numeric(
            dashboard_episodes["peak_dashboard_score"],
            errors="coerce",
        )
        if "peak_dashboard_score" in dashboard_episodes.columns
        else pd.Series(dtype="float64")
    )
    valid_scores = score_column.dropna()

    available_dates = []

    if "start_market_time" in dashboard_episodes.columns:
        available_dates = sorted(
            {
                str(value)[:10]
                for value in dashboard_episodes["start_market_time"].dropna()
                if str(value).strip()
            }
        )

    displayed_dates = []

    if "start_market_time" in filtered_episodes.columns:
        displayed_dates = sorted(
            {
                str(value)[:10]
                for value in filtered_episodes["start_market_time"].dropna()
                if str(value).strip()
            }
        )

    date_range_displayed = (
        f"{displayed_dates[0]} to {displayed_dates[-1]}"
        if displayed_dates
        else "N/A"
    )

    summary_columns = st.columns(4)
    summary_columns[0].metric("Total Episodes", len(dashboard_episodes))
    summary_columns[1].metric("Displayed Episodes", len(filtered_episodes))
    summary_columns[2].metric(
        "Max Episode Score",
        int(valid_scores.max()) if not valid_scores.empty else "N/A",
    )
    summary_columns[3].metric("Available Dates", len(available_dates))

    detail_columns = st.columns(2)
    detail_columns[0].metric("Selected Date", episode_date_filter)
    detail_columns[1].metric("Date Range Displayed", date_range_displayed)

    st.write(
        "Available dates: "
        + (
            ", ".join(available_dates)
            if available_dates
            else "N/A"
        )
    )

    if not valid_scores.empty:
        count_by_score = (
            valid_scores
            .value_counts()
            .sort_index()
            .astype(int)
            .to_dict()
        )
        st.write(f"Count by score: {count_by_score}")


def render_archive_v2_field_coverage(market_rows):
    st.subheader("Archive V2 Field Coverage")

    if market_rows.empty:
        st.info("No loaded observation rows available.")
        return

    rows = []

    for field in ARCHIVE_V2_FIELDS:
        exists = field in market_rows.columns
        non_empty_count = 0
        samples = ""

        if exists:
            series = market_rows[field].dropna()
            series = series[
                series.astype(str).str.strip() != ""
            ]
            non_empty_count = len(series)
            samples = " | ".join(
                str(value)
                for value in series.astype(str).drop_duplicates().head(5)
            )

        rows.append(
            {
                "field": field,
                "exists": "yes" if exists else "no",
                "non_empty_count": non_empty_count,
                "sample_values": samples,
            }
        )

    st.dataframe(
        sanitize_dataframe_for_display(pd.DataFrame(rows)),
        use_container_width=True,
        hide_index=True,
    )


def render_recent_events(observation_events):
    st.subheader("Recent Important Events")

    if observation_events.empty:
        st.info("No observation events available yet.")
        return

    available_columns = [
        column
        for column in IMPORTANT_EVENT_COLUMNS
        if column in observation_events.columns
    ]

    if not available_columns:
        st.info("Important event columns are not available yet.")
        return

    event_mask = observation_events[available_columns].apply(
        lambda row: any(is_truthy(value) for value in row),
        axis=1,
    )

    recent_events = observation_events[event_mask].tail(50)

    if recent_events.empty:
        st.info("No important events observed yet.")
        return

    st.dataframe(
        sanitize_dataframe_for_display(recent_events),
        use_container_width=True,
        hide_index=True,
    )


def render_live_observation_panels(
    observation_mode,
    file_sources,
    minimum_score,
    selected_states,
    latest_only,
    show_event_history,
    show_completed_episodes,
    episode_date_filter,
    minimum_episode_score,
    episode_score_at_least_4,
    episode_id_filter,
    show_all_episodes,
    episode_sort_order,
    show_archive_field_coverage,
    force_refresh=False,
):
    market_rows, observation_events, dashboard_episodes = load_dashboard_data(
        file_sources,
        force_refresh=force_refresh,
    )
    v2_events = pd.DataFrame()
    v2_episodes = pd.DataFrame()

    if observation_mode == "HISTORICAL REPLAY":
        v2_events, v2_episodes = load_historical_dashboard_v2_data(
            force_refresh=force_refresh,
        )

    if (
        market_rows.empty
        and observation_events.empty
        and dashboard_episodes.empty
    ):
        if observation_mode == "RECORDED REPLAY":
            st.info("Waiting for recorded replay data...")
        elif observation_mode == "HISTORICAL REPLAY":
            st.info("Historical replay data not generated yet.")
        else:
            st.info("Waiting for live data...")
        return

    if observation_mode == "HISTORICAL REPLAY":
        v2_metric_columns = st.columns(4)
        v2_metric_columns[0].metric("V1 Episodes", len(dashboard_episodes))
        v2_metric_columns[1].metric("V2 Episodes", len(v2_episodes))
        v2_metric_columns[2].metric("V1 Events", len(observation_events))
        v2_metric_columns[3].metric("V2 Events", len(v2_events))

    filtered_events = apply_event_filters(
        observation_events,
        minimum_score,
        selected_states,
        latest_only,
    )
    display_events = add_market_time_to_events(
        filtered_events,
        market_rows,
    )
    display_dashboard_episodes = add_market_time_to_episodes(
        dashboard_episodes,
        market_rows,
    )

    latest_market_row, latest_event = render_metric_cards(
        market_rows,
        display_events,
        display_dashboard_episodes,
    )

    active_episode = get_active_episode(
        observation_events,
        latest_market_row,
    )

    left_column, right_column = st.columns([1, 1])

    with left_column:
        render_latest_row(latest_market_row)
        render_active_episode_panel(active_episode)
        render_latest_event(latest_event)
        render_recent_events(display_events)

    with right_column:
        if show_event_history:
            render_event_history(display_events)

        if show_completed_episodes:
            render_dashboard_episodes(
                display_dashboard_episodes,
                episode_date_filter,
                minimum_episode_score,
                episode_score_at_least_4,
                episode_id_filter,
                show_all_episodes,
                episode_sort_order,
            )

        if show_archive_field_coverage:
            render_archive_v2_field_coverage(market_rows)

        if observation_mode == "HISTORICAL REPLAY":
            render_historical_dashboard_v2(
                v2_events,
                v2_episodes,
            )


def main():
    st.set_page_config(
        page_title="BTC Quant Observation Studio",
        layout="wide",
    )

    if "auto_refresh" not in st.session_state:
        st.session_state["auto_refresh"] = False

    if "refresh_seconds" not in st.session_state:
        st.session_state["refresh_seconds"] = 5
    elif st.session_state["refresh_seconds"] not in [3, 5, 10, 30]:
        st.session_state["refresh_seconds"] = 5

    if "force_csv_refresh" not in st.session_state:
        st.session_state["force_csv_refresh"] = False

    if "observation_mode" not in st.session_state:
        st.session_state["observation_mode"] = "LIVE"
    elif st.session_state["observation_mode"] == "REPLAY":
        st.session_state["observation_mode"] = "RECORDED REPLAY"
    elif st.session_state["observation_mode"] not in OBSERVATION_FILE_SOURCES:
        st.session_state["observation_mode"] = "LIVE"

    st.title("BTC Quant Observation Studio V1.6")
    st.caption("PHASE 1B Observation / Calibration - read-only CSV interface")

    with st.sidebar:
        st.header("Observation Mode")
        observation_mode = st.selectbox(
            "Observation Mode",
            ["LIVE", "RECORDED REPLAY", "HISTORICAL REPLAY"],
            key="observation_mode",
        )
        file_sources = OBSERVATION_FILE_SOURCES[observation_mode]
        sidebar_market_rows, _, sidebar_dashboard_episodes = load_dashboard_data(
            file_sources,
            force_refresh=False,
        )
        episode_date_options = get_episode_date_options(
            sidebar_dashboard_episodes,
            sidebar_market_rows,
        )
        sidebar_display_episodes = add_market_time_to_episodes(
            sidebar_dashboard_episodes,
            sidebar_market_rows,
        )
        episode_id_options = get_episode_id_options(
            sidebar_display_episodes
        )

        if (
            st.session_state.get("episode_date_filter")
            not in episode_date_options
        ):
            st.session_state["episode_date_filter"] = "All dates"

        if (
            st.session_state.get("episode_id_filter")
            not in episode_id_options
        ):
            st.session_state["episode_id_filter"] = "All episodes"

        st.header("Refresh")
        st.checkbox("Auto refresh", key="auto_refresh")
        st.selectbox(
            "Refresh interval seconds",
            [3, 5, 10, 30],
            key="refresh_seconds",
        )

        st.header("Filters")
        minimum_score = st.slider(
            "Minimum dashboard score",
            min_value=0,
            max_value=7,
            value=0,
            key="minimum_dashboard_score",
        )
        selected_states = st.multiselect(
            "State filter",
            STATE_OPTIONS,
            default=STATE_OPTIONS,
            key="selected_dashboard_states",
        )
        latest_only = st.checkbox(
            "Show latest event only",
            value=False,
            key="show_latest_event_only",
        )
        show_event_history = st.checkbox(
            "Show event history",
            value=True,
            key="show_event_history",
        )
        show_completed_episodes = st.checkbox(
            "Show completed episodes",
            value=True,
            key="show_completed_episodes",
        )

        st.header("Episode Filters")
        st.markdown("**Episode Date Filter**")
        episode_date_filter = st.selectbox(
            "Select episode date",
            episode_date_options,
            key="episode_date_filter",
        )
        st.caption(
            "Available dates: "
            + (
                ", ".join(episode_date_options[1:])
                if len(episode_date_options) > 1
                else "N/A"
            )
        )
        minimum_episode_score = st.selectbox(
            "Minimum episode score",
            [2, 3, 4, 5],
            key="minimum_episode_score",
        )
        episode_score_at_least_4 = st.checkbox(
            "Show only score >= 4",
            value=False,
            key="episode_score_at_least_4",
        )
        episode_id_filter = st.selectbox(
            "Jump to episode_id",
            episode_id_options,
            key="episode_id_filter",
        )
        show_all_episodes = st.checkbox(
            "Show all episodes",
            value=False,
            key="show_all_episodes",
        )
        episode_sort_order = st.selectbox(
            "Episode sort order",
            ["Newest first", "Oldest first", "Highest score first"],
            key="episode_sort_order",
        )
        show_archive_field_coverage = st.checkbox(
            "Show Archive V2 Field Coverage",
            value=False,
            key="show_archive_field_coverage",
        )

        if st.button("Refresh now", key="manual_refresh_button"):
            st.session_state["force_csv_refresh"] = True
            st.rerun()

    st.info(f"Current Observation Mode: {observation_mode}")

    force_refresh = bool(st.session_state.get("force_csv_refresh", False))
    st.session_state["force_csv_refresh"] = False

    auto_refresh_enabled = st.session_state.get("auto_refresh") is True
    fragment_runner = getattr(st, "fragment", None)

    if auto_refresh_enabled and callable(fragment_runner):
        refresh_interval = int(st.session_state["refresh_seconds"])

        @fragment_runner(run_every=f"{refresh_interval}s")
        def live_observation_fragment():
            render_live_observation_panels(
                observation_mode,
                file_sources,
                minimum_score,
                selected_states,
                latest_only,
                show_event_history,
                show_completed_episodes,
                episode_date_filter,
                minimum_episode_score,
                episode_score_at_least_4,
                episode_id_filter,
                show_all_episodes,
                episode_sort_order,
                show_archive_field_coverage,
                force_refresh=force_refresh,
            )

        live_observation_fragment()
        return

    if auto_refresh_enabled and not callable(fragment_runner):
        st.info(
            "Smooth Auto Refresh requires Streamlit fragment support. "
            "Use Refresh now to update this Streamlit version."
        )

    render_live_observation_panels(
        observation_mode,
        file_sources,
        minimum_score,
        selected_states,
        latest_only,
        show_event_history,
        show_completed_episodes,
        episode_date_filter,
        minimum_episode_score,
        episode_score_at_least_4,
        episode_id_filter,
        show_all_episodes,
        episode_sort_order,
        show_archive_field_coverage,
        force_refresh=force_refresh,
    )


if __name__ == "__main__":
    main()

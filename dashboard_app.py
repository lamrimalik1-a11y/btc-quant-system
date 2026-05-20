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

OBSERVATION_FILE_SOURCES = {
    "LIVE": {
        "market_rows": MARKET_ROWS_FILE,
        "observation_events": OBSERVATION_EVENTS_FILE,
        "dashboard_episodes": DASHBOARD_EPISODES_FILE,
    },
    "REPLAY": {
        "market_rows": REPLAY_MARKET_ROWS_FILE,
        "observation_events": REPLAY_OBSERVATION_EVENTS_FILE,
        "dashboard_episodes": REPLAY_DASHBOARD_EPISODES_FILE,
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
        pd.DataFrame(
            {
                "field": available_fields,
                "value": [
                    latest_market_row[field]
                    for field in available_fields
                ],
            }
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
    ]

    available_fields = [
        field
        for field in display_fields
        if field in latest_event.index
    ]

    st.dataframe(
        pd.DataFrame(
            {
                "field": available_fields,
                "value": [
                    latest_event[field]
                    for field in available_fields
                ],
            }
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
        pd.DataFrame(
            {
                "field": detail_fields,
                "value": [
                    active_episode[field]
                    for field in detail_fields
                ],
            }
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
        "event_timestamp_utc",
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

    columns = [
        column
        for column in display_columns
        if column in observation_events.columns
    ]

    st.dataframe(
        observation_events[columns].tail(100),
        use_container_width=True,
        hide_index=True,
    )


def render_dashboard_episodes(dashboard_episodes):
    st.subheader("Dashboard Episodes")

    if dashboard_episodes.empty:
        st.info("No completed dashboard episodes yet.")
        return

    display_columns = [
        "episode_id",
        "episode_start_timestamp_utc",
        "episode_end_timestamp_utc",
        "duration_seconds",
        "start_row_id",
        "end_row_id",
        "peak_dashboard_state",
        "peak_dashboard_score",
        "peak_conditions",
        "start_price",
        "end_price",
    ]

    columns = [
        column
        for column in display_columns
        if column in dashboard_episodes.columns
    ]

    st.dataframe(
        dashboard_episodes[columns].tail(100),
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
        recent_events,
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
    force_refresh=False,
):
    market_rows, observation_events, dashboard_episodes = load_dashboard_data(
        file_sources,
        force_refresh=force_refresh,
    )

    if (
        market_rows.empty
        and observation_events.empty
        and dashboard_episodes.empty
    ):
        if observation_mode == "REPLAY":
            st.info("Waiting for replay data...")
        else:
            st.info("Waiting for live data...")
        return

    filtered_events = apply_event_filters(
        observation_events,
        minimum_score,
        selected_states,
        latest_only,
    )

    latest_market_row, latest_event = render_metric_cards(
        market_rows,
        filtered_events,
        dashboard_episodes,
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
        render_recent_events(filtered_events)

    with right_column:
        if show_event_history:
            render_event_history(filtered_events)

        if show_completed_episodes:
            render_dashboard_episodes(dashboard_episodes)


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

    st.title("BTC Quant Observation Studio V1.6")
    st.caption("PHASE 1B Observation / Calibration - read-only CSV interface")

    with st.sidebar:
        st.header("Observation Mode")
        observation_mode = st.selectbox(
            "Observation Mode",
            ["LIVE", "REPLAY"],
            key="observation_mode",
        )

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

        if st.button("Refresh now", key="manual_refresh_button"):
            st.session_state["force_csv_refresh"] = True
            st.rerun()

    file_sources = OBSERVATION_FILE_SOURCES[observation_mode]
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
        force_refresh=force_refresh,
    )


if __name__ == "__main__":
    main()

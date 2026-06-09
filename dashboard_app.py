import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from dashboard.overlay_renderer import (
    load_rdm_overlay_data,
    render_rdm_visual_overlay,
)
from dashboard.research_mapping import (
    PREPARATION_DATASET_MISMATCH,
    check_period_alignment,
    get_research_log_date_range,
    load_dashboard_research_mapping,
    map_research_to_dashboard_episodes,
)


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
LIVE_MODE = "LIVE_MODE"
HISTORICAL_REPLAY_MODE = "HISTORICAL_REPLAY_MODE"
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
LIVE_HEARTBEAT_SECONDS = 5
ALGERIA_TIMEZONE = timezone(timedelta(hours=1))
TIME_DISPLAY_OPTIONS = ["Algeria (UTC+1)", "UTC"]

RESEARCH_DIR = BASE_DIR / "research"
PREPARATION_LOG_FILE = RESEARCH_DIR / "phase1b_episode_research_log.csv"
PREPARATION_ZONES_FILE = RESEARCH_DIR / "phase1b_preparation_zones.csv"
LIVE_PREPARATION_FILE = OUTPUT_DIR / "live_preparation_zones.csv"
LIVE_LIFECYCLE_EVENTS_FILE = OUTPUT_DIR / "live_lifecycle_events.jsonl"
LIVE_FIELD_LIFECYCLE_EVENTS_FILE = OUTPUT_DIR / "live_field_lifecycle_events.jsonl"
LIVE_LIFECYCLE_STATE_FILE = OUTPUT_DIR / "live_lifecycle_state.csv"
LIVE_DASHBOARD_V2_EPISODES_FILE = OUTPUT_DIR / "dashboard_v2_episodes.csv"
LIVE_RETURN_DETECTION_FILE = OUTPUT_DIR / "live_return_detection.csv"
LIVE_RDM_STATE_FILE = OUTPUT_DIR / "live_rdm_state.csv"
LIVE_B10_TRAJECTORY_FILE = OUTPUT_DIR / "live_b10_trajectory.csv"
LIVE_B11_PREDICTION_FILE = OUTPUT_DIR / "live_b11_prediction.csv"
LIVE_SYNTHESIS_FILE = OUTPUT_DIR / "live_synthesis.csv"

OBSERVATION_FILE_SOURCES = {
    "LIVE": {
        "mode": LIVE_MODE,
        "market_rows": MARKET_ROWS_FILE,
        "observation_events": OBSERVATION_EVENTS_FILE,
        "dashboard_episodes": DASHBOARD_EPISODES_FILE,
    },
    "RECORDED REPLAY": {
        "mode": HISTORICAL_REPLAY_MODE,
        "market_rows": REPLAY_MARKET_ROWS_FILE,
        "observation_events": REPLAY_OBSERVATION_EVENTS_FILE,
        "dashboard_episodes": REPLAY_DASHBOARD_EPISODES_FILE,
    },
    "HISTORICAL REPLAY": {
        "mode": HISTORICAL_REPLAY_MODE,
        "market_rows": HISTORICAL_OBSERVATION_ROWS_FILE,
        "historical_market_rows": OUTPUT_DIR / "historical_market_rows.csv",
        "observation_events": HISTORICAL_REPLAY_OBSERVATION_EVENTS_FILE,
        "dashboard_episodes": HISTORICAL_REPLAY_DASHBOARD_EPISODES_FILE,
        "v2_events": HISTORICAL_REPLAY_OBSERVATION_V2_EVENTS_FILE,
        "v2_episodes": HISTORICAL_REPLAY_DASHBOARD_V2_EPISODES_FILE,
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


def source_mode_for_observation_mode(observation_mode):
    if observation_mode == "LIVE":
        return LIVE_MODE
    return HISTORICAL_REPLAY_MODE


def assert_source_mode(file_sources, expected_mode):
    actual_mode = file_sources.get("mode")
    if actual_mode != expected_mode:
        st.error(
            f"Source mode mismatch: expected {expected_mode}, got {actual_mode}."
        )
        return False

    if expected_mode == HISTORICAL_REPLAY_MODE:
        forbidden = {
            MARKET_ROWS_FILE.resolve(),
            OBSERVATION_EVENTS_FILE.resolve(),
            DASHBOARD_EPISODES_FILE.resolve(),
        }
        requested = [
            path.resolve()
            for key, path in file_sources.items()
            if key != "mode" and isinstance(path, Path)
        ]
        contaminated = [path for path in requested if path in forbidden]
        if contaminated:
            st.error(
                "Historical replay mode blocked a live/default source request: "
                + ", ".join(path.name for path in contaminated)
            )
            return False

    return True


def source_label_for_mode(source_mode):
    return (
        "historical replay"
        if source_mode == HISTORICAL_REPLAY_MODE
        else "live"
    )


def load_dashboard_data(file_sources, force_refresh=False):
    source_mode = file_sources.get("mode", LIVE_MODE)
    return (
        read_source_csv(file_sources["market_rows"], source_mode, force_refresh),
        read_source_csv(file_sources["observation_events"], source_mode, force_refresh),
        read_source_csv(file_sources["dashboard_episodes"], source_mode, force_refresh),
    )


def read_source_csv(path, source_mode, force_refresh=False):
    if source_mode == HISTORICAL_REPLAY_MODE and not path.exists():
        st.warning(f"Historical replay source missing: {path.name}")
        return pd.DataFrame()
    return read_csv_with_mtime_cache(path, force_refresh)


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


def render_replay_source_banner(market_rows, v2_episodes, file_sources):
    st.info("REPLAY MODE ACTIVE")
    replay_start, replay_end = dataframe_time_window(market_rows)
    row_start, row_end = dataframe_row_range(market_rows)
    episode_row_start, episode_row_end = episode_row_range(v2_episodes)

    columns = st.columns(4)
    columns[0].metric("Replay Source", "Historical Replay")
    columns[1].metric("Replay Date", replay_start[:10] if replay_start else "N/A")
    columns[2].metric("Row Range", format_range(row_start, row_end))
    columns[3].metric("Episode Row Range", format_range(episode_row_start, episode_row_end))

    st.caption(
        "Replay Display Window: "
        f"{replay_start or 'N/A'} -> {replay_end or 'N/A'} | "
        f"Time Display: {current_time_display_mode()} | "
        f"Source file: {file_sources.get('market_rows')}"
    )


def _file_period_info(path, ts_col, unit="ms"):
    """Return (min_date, max_date, row_count, mtime_str) for a CSV file."""
    if path is None or not Path(path).exists():
        return "N/A", "N/A", 0, "N/A"
    try:
        mtime = datetime.fromtimestamp(Path(path).stat().st_mtime, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"
        )
        df = pd.read_csv(path, usecols=[ts_col])
        if df.empty:
            return "N/A", "N/A", 0, mtime
        if unit == "ms":
            dates = pd.to_datetime(pd.to_numeric(df[ts_col], errors="coerce"), unit="ms", utc=True)
        else:
            dates = pd.to_datetime(df[ts_col], errors="coerce", utc=True)
        dates = dates.dropna()
        if dates.empty:
            return "N/A", "N/A", len(df), mtime
        return (
            dates.min().strftime("%Y-%m-%d"),
            dates.max().strftime("%Y-%m-%d"),
            len(df),
            mtime,
        )
    except Exception:
        return "N/A", "N/A", 0, "N/A"


def render_dataset_consistency_panel(v2_episodes, market_rows):
    """Show a table of all source files with their periods and last-modified times."""
    with st.expander("Dataset Consistency Panel", expanded=True):
        rows_info = []

        obs_min, obs_max, obs_rows, obs_mtime = _file_period_info(
            HISTORICAL_OBSERVATION_ROWS_FILE, "market_timestamp", unit="ms"
        )
        rows_info.append({
            "File": "outputs/historical_observation_rows.csv",
            "Period start": obs_min,
            "Period end": obs_max,
            "Rows": obs_rows,
            "Last modified": obs_mtime,
        })

        v2_min, v2_max, v2_rows, v2_mtime = _file_period_info(
            HISTORICAL_REPLAY_DASHBOARD_V2_EPISODES_FILE,
            "episode_start_timestamp_utc",
            unit="ms",
        )
        rows_info.append({
            "File": "outputs/historical_replay_dashboard_v2_episodes.csv",
            "Period start": v2_min,
            "Period end": v2_max,
            "Rows": v2_rows,
            "Last modified": v2_mtime,
        })

        res_min, res_max, res_rows, res_mtime = _file_period_info(
            PREPARATION_LOG_FILE, "episode_start_time_utc", unit="str"
        )
        rows_info.append({
            "File": "research/phase1b_episode_research_log.csv",
            "Period start": res_min,
            "Period end": res_max,
            "Rows": res_rows,
            "Last modified": res_mtime,
        })

        pz_min, pz_max, pz_rows, pz_mtime = _file_period_info(
            PREPARATION_ZONES_FILE, "episode_start_time_utc", unit="str"
        )
        rows_info.append({
            "File": "research/phase1b_preparation_zones.csv",
            "Period start": pz_min,
            "Period end": pz_max,
            "Rows": pz_rows,
            "Last modified": pz_mtime,
        })

        st.dataframe(pd.DataFrame(rows_info), use_container_width=True, hide_index=True)

        # Period alignment check
        period_aligned = check_period_alignment(v2_episodes, PREPARATION_LOG_FILE)
        if not period_aligned:
            st.error(
                "DATASET MISMATCH: outputs and research files are from different periods. "
                "Research mapping disabled to prevent wrong preparation_candidate values. "
                f"outputs V2 episodes: {v2_min} to {v2_max} | "
                f"research log: {res_min} to {res_max}"
            )
        else:
            st.success(
                f"Dataset periods aligned: outputs {v2_min} to {v2_max} | "
                f"research {res_min} to {res_max}"
            )

        st.caption(
            "preparation_candidate values: "
            "True = preparation detected | "
            "False = analyzed, no preparation detected | "
            "NOT_ANALYZED = same dataset, episode not in research run | "
            "UNKNOWN = research row exists but value missing | "
            "DATASET_MISMATCH = outputs and research are from different periods"
        )

    return period_aligned


def dataframe_time_window(dataframe):
    if dataframe.empty or "market_timestamp" not in dataframe.columns:
        return "", ""
    parsed = dataframe["market_timestamp"].apply(format_market_time)
    parsed = parsed[parsed.astype(str).str.len() > 0]
    if parsed.empty:
        return "", ""
    return str(parsed.iloc[0]), str(parsed.iloc[-1])


def dataframe_row_range(dataframe):
    if dataframe.empty or "row_id" not in dataframe.columns:
        return "", ""
    values = pd.to_numeric(dataframe["row_id"], errors="coerce").dropna()
    if values.empty:
        return "", ""
    return int(values.min()), int(values.max())


def episode_row_range(episodes):
    if episodes.empty:
        return "", ""
    values = []
    for column in ["start_row_id", "end_row_id"]:
        if column in episodes.columns:
            values.extend(pd.to_numeric(episodes[column], errors="coerce").dropna().tolist())
    if not values:
        return "", ""
    return int(min(values)), int(max(values))


def format_range(start, end):
    if start == "" or end == "":
        return "N/A"
    return f"{start} - {end}"


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


def current_time_display_mode():
    return st.session_state.get("time_display_mode", "Algeria (UTC+1)")


def display_timezone_for_mode(display_mode=None):
    mode = display_mode or current_time_display_mode()
    if mode == "UTC":
        return timezone.utc, "UTC"
    return ALGERIA_TIMEZONE, "Algeria"


def format_market_time(value, display_mode=None, include_utc=False):
    if not has_display_value(value):
        return ""

    parsed_datetime = parse_market_datetime(value)

    if parsed_datetime is None:
        return str(value)

    target_timezone, label = display_timezone_for_mode(display_mode)
    display_datetime = parsed_datetime.astimezone(target_timezone)
    display_value = display_datetime.strftime("%Y-%m-%d %H:%M:%S")

    if include_utc and label != "UTC":
        utc_value = parsed_datetime.astimezone(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return f"{label}: {display_value} | UTC: {utc_value}"

    return display_value


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
    else:
        parsed = parsed.replace(tzinfo=timezone.utc)

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
        "market_timestamp",
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
                        (
                            format_market_time(
                                latest_market_row[field],
                                include_utc=True,
                            )
                            if field == "market_timestamp"
                            else latest_market_row[field]
                        )
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
    st.subheader("Dashboard V1 Episodes")

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
    market_rows,
    file_sources,
    show_all_v2_episodes=False,
):
    st.subheader("Dashboard V2 Historical Replay")
    render_replay_source_banner(market_rows, v2_episodes, file_sources)

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

    period_aligned = render_dataset_consistency_panel(v2_episodes, market_rows)

    research_mapping = load_dashboard_research_mapping(BASE_DIR)
    render_dashboard_v2_episodes(
        v2_episodes,
        research_mapping,
        file_sources=file_sources,
        period_aligned=period_aligned,
        show_all_v2_episodes=show_all_v2_episodes,
    )
    render_dashboard_v2_events(v2_events)


def render_dashboard_v2_episodes(
    v2_episodes,
    research_mapping=None,
    file_sources=None,
    period_aligned=True,
    show_all_v2_episodes=False,
):
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
    st.caption(
        "Preparation status: "
        "True = preparation detected | "
        "False = analyzed, no preparation detected | "
        "NOT_ANALYZED = same dataset, episode not in research run | "
        "UNKNOWN = research row exists but value missing | "
        "DATASET_MISMATCH = outputs and research are from different periods"
    )

    if not period_aligned:
        st.warning(
            "Research mapping is DISABLED: outputs and research files are from different "
            "periods. preparation_candidate shows DATASET_MISMATCH to prevent spurious "
            "episode_id collisions across replay runs."
        )

    if v2_episodes.empty:
        st.info("No Dashboard V2 episodes available yet.")
        return

    display_episodes = v2_episodes.copy()

    if research_mapping is not None and not research_mapping.empty:
        display_episodes = map_research_to_dashboard_episodes(
            display_episodes,
            research_mapping,
            period_aligned=period_aligned,
        )

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

    render_dashboard_v2_summary(display_episodes)

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
        "preparation_candidate",
        "preparation_strength",
        "return_to_preparation",
        "expansion_type",
        "expansion_strength",
        "reversal_type",
        "reversal_strength",
        "comparison_group",
        "preparation_result",
        "hypothesis02_state",
    ]
    columns = [
        column
        for column in display_columns
        if column in display_episodes.columns
    ]

    if filtered_episodes.empty:
        st.info("No Dashboard V2 episodes match the current filters.")
        return

    total = len(filtered_episodes)
    if show_all_v2_episodes:
        display_slice = filtered_episodes[columns]
        st.caption(f"Showing all {total} filtered V2 episodes.")
    else:
        display_slice = filtered_episodes[columns].tail(100)
        hidden = max(0, total - 100)
        if hidden:
            st.caption(
                f"Showing latest 100 of {total} filtered V2 episodes "
                f"({hidden} older episodes hidden). Enable 'Show all V2 episodes' in sidebar to see all."
            )
        else:
            st.caption(f"Showing all {total} V2 episodes.")

    st.dataframe(
        sanitize_dataframe_for_display(display_slice),
        use_container_width=True,
        hide_index=True,
    )
    render_dashboard_v2_source_audit(filtered_episodes, file_sources)
    render_dashboard_v2_research_panel(filtered_episodes)
    render_dashboard_v2_research_case_lookup(filtered_episodes)


def render_dashboard_v2_source_audit(filtered_episodes, file_sources=None):
    st.subheader("Replay Source Audit")
    st.caption(
        "Source isolation check for rendered Dashboard V2 episodes. "
        "Historical replay mode must not use live/default CSV files."
    )
    if filtered_episodes.empty:
        st.info("No episodes available for source audit.")
        return

    source_file = (
        file_sources.get("v2_episodes")
        if file_sources and "v2_episodes" in file_sources
        else HISTORICAL_REPLAY_DASHBOARD_V2_EPISODES_FILE
    )
    audit = filtered_episodes.copy().tail(100)
    audit["source_file"] = str(source_file)
    audit["replay_mode"] = HISTORICAL_REPLAY_MODE
    audit["live_mode"] = False
    audit["timestamp_range"] = (
        audit.get("episode_start_time_utc", "").astype(str)
        + " -> "
        + audit.get("episode_end_time_utc", "").astype(str)
    )
    columns = [
        "episode_id",
        "source_file",
        "start_row_id",
        "end_row_id",
        "timestamp_range",
        "replay_mode",
        "live_mode",
    ]
    st.dataframe(
        sanitize_dataframe_for_display(
            audit[[column for column in columns if column in audit.columns]]
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_dashboard_v2_summary(display_episodes):
    layer_count_values = pd.to_numeric(
        display_episodes.get("peak_layer_count", 0),
        errors="coerce",
    ).fillna(0)
    valid_layer_counts = layer_count_values.dropna()

    metric_columns = st.columns(4)
    metric_columns[0].metric("Total V2 Episodes", len(display_episodes))
    metric_columns[1].metric(
        "Max V2 Layer Count",
        int(valid_layer_counts.max()) if not valid_layer_counts.empty else "N/A",
    )
    metric_columns[2].metric(
        "Score 5 Episodes",
        int((layer_count_values == 5).sum()),
    )
    metric_columns[3].metric(
        "Score 6 Episodes",
        int((layer_count_values == 6).sum()),
    )

    if not valid_layer_counts.empty:
        count_by_layer_count = (
            valid_layer_counts
            .value_counts()
            .sort_index()
            .astype(int)
            .to_dict()
        )
        st.write(f"V2 Count by Layer Count: {count_by_layer_count}")


def add_episode_time_columns(dataframe, source_column="episode_start_time_utc"):
    if dataframe.empty or source_column not in dataframe.columns:
        return dataframe

    enriched = dataframe.copy()
    values = enriched[source_column]
    if pd.api.types.is_numeric_dtype(values):
        parsed = pd.to_datetime(values, unit="ms", utc=True, errors="coerce")
    else:
        parsed = pd.to_datetime(values, utc=True, errors="coerce")
    enriched["_episode_start_dt"] = parsed
    enriched["_episode_date"] = parsed.dt.strftime("%Y-%m-%d")
    return enriched


def apply_research_mapping_display_controls(
    dataframe,
    key_prefix,
    default_limit=20,
    show_all_label="Show all research mapping rows",
):
    if dataframe.empty:
        return dataframe, {
            "total_rows": 0,
            "filtered_rows": 0,
            "displayed_rows": 0,
            "date_range": "No rows",
            "first_displayed": "N/A",
            "last_displayed": "N/A",
        }

    working = add_episode_time_columns(dataframe)
    control_columns = st.columns([1, 1, 1, 1])

    available_dates = []
    if "_episode_date" in working.columns:
        available_dates = sorted(
            date for date in working["_episode_date"].dropna().unique()
        )

    with control_columns[0]:
        show_all_rows = st.checkbox(
            show_all_label,
            value=False,
            key=f"{key_prefix}_show_all_rows",
        )

    row_limit_options = ["20", "50", "100", "200", "500", "ALL"]
    default_index = (
        row_limit_options.index(str(default_limit))
        if str(default_limit) in row_limit_options
        else 0
    )
    with control_columns[1]:
        selected_limit = st.selectbox(
            "Row limit",
            row_limit_options,
            index=default_index,
            key=f"{key_prefix}_row_limit",
        )

    with control_columns[2]:
        selected_date = st.selectbox(
            "Date",
            ["ALL DATES"] + available_dates,
            key=f"{key_prefix}_date_filter",
        )

    with control_columns[3]:
        sort_order = st.selectbox(
            "Sort order",
            ["Newest first", "Oldest first"],
            key=f"{key_prefix}_sort_order",
        )

    if selected_date != "ALL DATES" and "_episode_date" in working.columns:
        working = working[working["_episode_date"] == selected_date].copy()

    if "_episode_start_dt" in working.columns:
        working = working.sort_values(
            "_episode_start_dt",
            ascending=(sort_order == "Oldest first"),
            na_position="last",
        )
    elif "episode_id" in working.columns:
        working = working.assign(
            _episode_id_numeric=pd.to_numeric(
                working["episode_id"], errors="coerce"
            ).fillna(0)
        ).sort_values(
            "_episode_id_numeric",
            ascending=(sort_order == "Oldest first"),
        ).drop(columns=["_episode_id_numeric"])

    filtered_rows = len(working)
    if show_all_rows or selected_limit == "ALL":
        displayed = working
    else:
        displayed = working.head(int(selected_limit))

    full_time = working.get("_episode_start_dt")
    display_time = displayed.get("_episode_start_dt")
    date_range = "N/A"
    first_displayed = "N/A"
    last_displayed = "N/A"
    if full_time is not None and full_time.notna().any():
        date_range = (
            f"{full_time.min().strftime('%Y-%m-%d')} to "
            f"{full_time.max().strftime('%Y-%m-%d')}"
        )
    if display_time is not None and display_time.notna().any():
        first_displayed = display_time.min().strftime("%Y-%m-%d %H:%M:%S UTC")
        last_displayed = display_time.max().strftime("%Y-%m-%d %H:%M:%S UTC")

    metadata = {
        "total_rows": len(dataframe),
        "filtered_rows": filtered_rows,
        "displayed_rows": len(displayed),
        "date_range": date_range,
        "first_displayed": first_displayed,
        "last_displayed": last_displayed,
    }
    display_columns = [
        column
        for column in ["_episode_start_dt", "_episode_date"]
        if column in displayed.columns
    ]
    return displayed.drop(columns=display_columns), metadata


def render_research_mapping_metrics(metadata, total_label="Total research mapping rows"):
    metric_columns = st.columns(5)
    metric_columns[0].metric(total_label, metadata["total_rows"])
    metric_columns[1].metric("Displayed rows", metadata["displayed_rows"])
    metric_columns[2].metric("Rows after date filter", metadata["filtered_rows"])
    metric_columns[3].metric("First displayed time", metadata["first_displayed"])
    metric_columns[4].metric("Last displayed time", metadata["last_displayed"])
    st.caption(f"Available date range: {metadata['date_range']}")


def render_dashboard_v2_research_panel(filtered_episodes):
    st.subheader("Dashboard V2 Research Mapping")
    st.caption(
        "Research labels are observation-only context. They do not change "
        "Dashboard V2 scoring, execution, or decision logic."
    )

    if filtered_episodes.empty:
        st.info("No mapped research rows available for the current filters.")
        return

    research_fields = [
        "preparation_candidate",
        "preparation_strength",
        "return_to_preparation",
        "expansion_type",
        "expansion_strength",
        "reversal_type",
        "reversal_strength",
        "comparison_group",
        "preparation_result",
        "hypothesis02_state",
    ]
    available_fields = [
        field for field in research_fields if field in filtered_episodes.columns
    ]

    if not available_fields:
        st.info("No Research Agent V1 fields are mapped for these episodes yet.")
        return

    mapping_rows, mapping_metadata = apply_research_mapping_display_controls(
        filtered_episodes,
        key_prefix="dashboard_v2_research_mapping",
        default_limit=20,
    )
    render_preparation_status_counts(filtered_episodes)
    render_research_mapping_metrics(mapping_metadata)

    panel_columns = st.columns(5)
    panel_columns[0].markdown("**PREPARATION**")
    panel_columns[0].dataframe(
        sanitize_dataframe_for_display(
            mapping_rows[
                [
                    field
                    for field in [
                        "episode_id",
                        "preparation_candidate",
                        "preparation_strength",
                        "return_to_preparation",
                    ]
                    if field in filtered_episodes.columns
                ]
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    panel_columns[1].markdown("**EXPANSION**")
    panel_columns[1].dataframe(
        sanitize_dataframe_for_display(
            mapping_rows[
                [
                    field
                    for field in [
                        "episode_id",
                        "expansion_type",
                        "expansion_strength",
                    ]
                    if field in filtered_episodes.columns
                ]
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    panel_columns[2].markdown("**REVERSAL**")
    panel_columns[2].dataframe(
        sanitize_dataframe_for_display(
            mapping_rows[
                [
                    field
                    for field in [
                        "episode_id",
                        "reversal_type",
                        "reversal_strength",
                    ]
                    if field in filtered_episodes.columns
                ]
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    panel_columns[3].markdown("**COMPARISON**")
    panel_columns[3].dataframe(
        sanitize_dataframe_for_display(
            mapping_rows[
                [
                    field
                    for field in [
                        "episode_id",
                        "comparison_group",
                        "preparation_result",
                    ]
                    if field in filtered_episodes.columns
                ]
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    panel_columns[4].markdown("**HYPOTHESIS**")
    panel_columns[4].dataframe(
        sanitize_dataframe_for_display(
            mapping_rows[
                [
                    field
                    for field in [
                        "episode_id",
                        "hypothesis02_state",
                    ]
                    if field in filtered_episodes.columns
                ]
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_preparation_status_counts(filtered_episodes):
    status_counts = preparation_status_counts(filtered_episodes)
    columns = st.columns(5)
    columns[0].metric("Total V2 Episodes", len(filtered_episodes))
    columns[1].metric("True", status_counts["True"])
    columns[2].metric("False", status_counts["False"])
    columns[3].metric("NOT_ANALYZED", status_counts["NOT_ANALYZED"])
    columns[4].metric("UNKNOWN", status_counts["UNKNOWN"])


def preparation_status_counts(dataframe):
    counts = {
        "True": 0,
        "False": 0,
        "NOT_ANALYZED": 0,
        "UNKNOWN": 0,
    }

    if "preparation_candidate" not in dataframe.columns:
        counts["NOT_ANALYZED"] = len(dataframe)
        return counts

    for value in dataframe["preparation_candidate"]:
        status = normalize_preparation_display_status(value)
        counts[status] = counts.get(status, 0) + 1

    return counts


def normalize_preparation_display_status(value):
    if isinstance(value, bool):
        return "True" if value else "False"

    if pd.isna(value):
        return "UNKNOWN"

    text = str(value).strip()
    lowered = text.lower()

    if text == "NOT_ANALYZED":
        return "NOT_ANALYZED"

    if text == "UNKNOWN" or text == "":
        return "UNKNOWN"

    if lowered == "true":
        return "True"

    if lowered == "false":
        return "False"

    return "UNKNOWN"


def render_dashboard_v2_research_case_lookup(filtered_episodes):
    st.subheader("Dashboard V2 Episode Research Case")
    st.caption(
        "Dashboard Episode -> Research Case -> Preparation -> Expansion -> "
        "Reversal -> Outcome. Observation-only mapping."
    )

    if filtered_episodes.empty or "episode_id" not in filtered_episodes.columns:
        st.info("No Dashboard V2 episode is available for research lookup.")
        return

    episode_options = [
        str(value)
        for value in filtered_episodes["episode_id"].dropna().unique()
        if str(value).strip()
    ]

    if not episode_options:
        st.info("No episode_id values are available for research lookup.")
        return

    selected_episode_id = st.selectbox(
        "Select Dashboard V2 episode_id",
        episode_options,
        key="dashboard_v2_research_case_episode_id",
    )
    open_case = st.button(
        "Open Research Case",
        key="dashboard_v2_open_research_case",
    )

    if open_case:
        st.session_state["dashboard_v2_open_research_episode_id"] = (
            selected_episode_id
        )

    active_episode_id = st.session_state.get(
        "dashboard_v2_open_research_episode_id",
        selected_episode_id,
    )

    if active_episode_id not in episode_options:
        active_episode_id = selected_episode_id
        st.session_state["dashboard_v2_open_research_episode_id"] = (
            active_episode_id
        )

    selected_rows = filtered_episodes[
        filtered_episodes["episode_id"].astype(str) == active_episode_id
    ]

    if selected_rows.empty:
        st.info("Selected episode is no longer available after filters.")
        return

    selected = selected_rows.iloc[0]

    if not has_research_case_data(selected):
        st.info(
            "No Research Agent V1 case is mapped to this Dashboard V2 episode yet."
        )
        return

    st.caption(f"Open Research Case: episode_id={active_episode_id}")
    render_dashboard_v2_selected_research_panel(selected)
    render_dashboard_v2_case_summary(selected)
    render_research_case_section(
        "Dashboard Episode",
        selected,
        [
            "episode_id",
            "episode_start_time_utc",
            "episode_end_time_utc",
            "peak_state",
            "peak_layer_count",
            "peak_max_severity",
            "peak_primary_context",
            "peak_observation_confidence",
        ],
    )
    render_research_case_section(
        "Research Case",
        selected,
        [
            "case_id",
            "classification",
            "classification_reason",
        ],
    )
    render_research_case_section(
        "Preparation",
        selected,
        [
            "preparation_candidate",
            "preparation_strength",
            "return_to_preparation",
            "pre_quiet_score",
            "pre_range_ratio",
            "preparation_result",
        ],
    )
    render_research_case_section(
        "Expansion",
        selected,
        [
            "expansion_type",
            "expansion_strength",
            "time_to_expansion_minutes",
            "expansion_survived",
            "expansion_failed",
        ],
    )
    render_research_case_section(
        "Reversal",
        selected,
        [
            "reversal_type",
            "reversal_strength",
            "time_to_reversal_minutes",
            "direct_reversal_flag",
            "late_reversal_flag",
            "reversal_after_return",
        ],
    )
    render_research_case_section(
        "Outcome",
        selected,
        [
            "comparison_group",
            "hypothesis02_state",
        ],
    )
    render_dashboard_v2_observation_outcome(selected)


def render_dashboard_v2_case_summary(row):
    st.subheader("Case Summary")
    summary_fields = [
        ("Research Case", "case_id"),
        ("Episode", "episode_id"),
        ("Primary Context", "peak_primary_context"),
        ("Layer Count", "peak_layer_count"),
        ("Severity", "peak_max_severity"),
        ("Preparation", "preparation_strength"),
        ("Expansion", "expansion_type"),
        ("Reversal", "reversal_type"),
        ("Outcome", "hypothesis02_state"),
    ]
    summary_columns = st.columns(3)

    for index, (label, field) in enumerate(summary_fields):
        summary_columns[index % 3].metric(
            label,
            safe_research_panel_value(row, field),
        )


def render_dashboard_v2_observation_outcome(row):
    st.subheader("Observation Outcome")
    st.caption(
        "Outcome labels are research observations only. They are not trading "
        "signals or decision instructions."
    )
    outcome_fields = [
        "classification",
        "classification_reason",
        "comparison_group",
        "preparation_result",
        "hypothesis02_state",
        "expansion_type",
        "reversal_type",
        "peak_observation_confidence",
    ]
    render_research_case_section("Observation Outcome Details", row, outcome_fields)


def render_dashboard_v2_selected_research_panel(row):
    st.subheader("Dashboard V2 Research Panel")
    st.caption(
        "Selected episode research context. Observation-only; does not affect "
        "Dashboard V2 scoring or live logic."
    )
    card_columns = st.columns(4)
    render_research_card(
        card_columns[0],
        "Preparation",
        [
            ("Candidate", "preparation_candidate", "status"),
            ("Strength", "preparation_strength", "severity"),
            ("Return", "return_to_preparation", "status"),
        ],
        row,
    )
    render_research_card(
        card_columns[1],
        "Expansion",
        [
            ("Type", "expansion_type", "outcome"),
            ("Strength", "expansion_strength", "severity"),
            ("Survived", "expansion_survived", "status"),
            ("Failed", "expansion_failed", "status"),
        ],
        row,
    )
    render_research_card(
        card_columns[2],
        "Reversal",
        [
            ("Type", "reversal_type", "outcome"),
            ("Strength", "reversal_strength", "severity"),
            ("Direct", "direct_reversal_flag", "status"),
            ("Late", "late_reversal_flag", "status"),
        ],
        row,
    )
    render_research_card(
        card_columns[3],
        "Outcome",
        [
            ("Classification", "classification", "outcome"),
            ("Confidence", "peak_observation_confidence", "confidence"),
            ("Result", "preparation_result", "outcome"),
            ("Hypothesis", "hypothesis02_state", "outcome"),
        ],
        row,
    )
    observation_rows, live_rows = load_rdm_overlay_data(
        BASE_DIR,
        source_mode=HISTORICAL_REPLAY_MODE,
    )
    render_rdm_visual_overlay(row, observation_rows, live_rows)
    render_rdm_market_mechanics_panel(row)
    render_rdm_real_zone_geometry_panel(row)
    render_rdm_interaction_core_panel(row)
    render_zone_birth_panel(row)
    render_rdm_birth_current_tracking_panel(row)
    render_live_rdm_evolution_panel(row)
    render_true_lifecycle_panel(row)
    render_birth_live_degradation_panel(row)
    render_zone_life_tracking_panel(row)
    render_zone_evolution_panel(row)
    render_rdm_verestchaguine_panel(row)
    render_rdm_timeline_panel(row)
    render_rdm_capacity_panel(row)
    render_rdm_sigma_panel(row)
    render_rdm_sigma_evolution_panel(row)
    render_zone_mechanical_memory_panel(row)
    render_zone_death_panel(row)
    render_final_rdm_result(row)


def render_rdm_market_mechanics_panel(row):
    st.subheader("RDM Market Mechanics - Research Only")
    st.caption(
        "Observation panel only. This is not a signal, not execution, and not "
        "Dashboard V2 scoring. It summarizes mechanical context for research review."
    )

    if safe_research_panel_value(row, "zone_mechanical_state") == "N/A":
        st.info("No RDM Mechanics data mapped for this case yet.")
        return

    card_columns = st.columns(3)
    render_research_card(
        card_columns[0],
        "Mechanical Family",
        [
            ("Family", "mechanical_family", "mechanics"),
            ("Subtype", "mechanical_subtype", "mechanics"),
            ("State", "zone_mechanical_state", "mechanics"),
            ("Reference", "reference_example_flag", "status"),
        ],
        row,
    )
    render_research_card(
        card_columns[1],
        "Flèche / Penetration",
        [
            ("Flèche State", "zone_fleche_state", "severity"),
            ("Flèche Ratio", "zone_fleche_ratio", "metric"),
            ("Penetration", "zone_penetration_depth", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[2],
        "Moment / Load",
        [
            ("Moment", "signed_moment_proxy", "metric"),
            ("Stress Type", "moment_stress_type", "mechanics"),
            ("Absorption", "moment_absorption_flag", "status"),
            ("Load Score", "mechanical_load_score", "metric"),
        ],
        row,
    )

    detail_columns = st.columns(3)
    render_research_card(
        detail_columns[0],
        "Fatigue / Rigidity",
        [
            ("Fatigue Index", "fatigue_index", "metric"),
            ("Fatigue State", "fatigue_state", "mechanics"),
            ("Rigidity", "zone_rigidity", "metric"),
            ("Strength Decay", "zone_strength_decay", "metric"),
        ],
        row,
    )
    render_research_card(
        detail_columns[1],
        "Recovery / Rupture",
        [
            ("Recovery Ratio", "recovery_ratio", "metric"),
            ("Recovery State", "zone_recovery_state", "mechanics"),
            ("Mechanical State", "zone_mechanical_state", "mechanics"),
        ],
        row,
    )
    render_research_card(
        detail_columns[2],
        "ELS / ELU",
        [
            ("Utilization", "moment_utilization_ratio", "metric"),
            ("ELS / ELU State", "els_elu_state", "mechanics"),
        ],
        row,
    )
    render_rdm_section_result(row, "RDM Market Mechanics")


def render_rdm_real_zone_geometry_panel(row):
    st.subheader("RDM Real Zone Geometry - Research Only")
    st.caption(
        "Real chart geometry for the research zone. This is observation-only "
        "context and does not affect scoring, signals, or execution."
    )

    if safe_research_panel_value(row, "real_zone_upper_edge") == "N/A":
        st.info("No real zone geometry mapped for this case yet.")
        return

    card_columns = st.columns(3)
    render_research_card(
        card_columns[0],
        "Time Window",
        [
            ("Birth Time", "real_birth_time", "metric"),
            ("Left Time", "real_zone_left_time", "metric"),
            ("Right Time", "real_zone_right_time", "metric"),
            ("End Time", "real_zone_end_time", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[1],
        "Price Geometry",
        [
            ("Upper Edge", "real_zone_upper_edge", "metric"),
            ("Lower Edge", "real_zone_lower_edge", "metric"),
            ("Mid Price", "real_zone_mid_price", "metric"),
            ("Real Width", "real_zone_width", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[2],
        "Geometry Source",
        [
            ("Birth Price", "real_birth_price", "metric"),
            ("Lifetime", "real_zone_lifetime", "metric"),
            ("Active Duration", "real_zone_active_duration", "metric"),
            ("Fallback Used", "geometry_fallback_used", "status"),
            ("Source", "geometry_source", "mechanics"),
        ],
        row,
    )
    render_rdm_section_result(row, "RDM Real Zone Geometry")


def render_rdm_birth_current_tracking_panel(row):
    st.subheader("Birth vs Current Mechanical Tracking - Research Only")
    st.caption(
        "Compares birth, current, return, and final research mechanics. Breach "
        "flags are retained for observation review only."
    )

    if safe_research_panel_value(row, "sigma_birth") == "N/A":
        st.info("No birth/current mechanical tracking mapped for this case yet.")
        return

    table = build_birth_current_tracking_table(row)
    st.dataframe(sanitize_dataframe_for_display(table), use_container_width=True)
    render_research_card(
        st.container(),
        "Mechanical Breach Summary",
        [
            ("Breach Count", "mechanical_breach_count", "metric"),
            ("Breach Summary", "mechanical_breach_summary", "mechanics"),
        ],
        row,
    )
    render_rdm_section_result(row, "Birth vs Current Mechanical Tracking")


def render_rdm_interaction_core_panel(row):
    st.subheader("RDM Interaction Core Geometry - Research Only")
    st.caption(
        "Separates the large formation range from the smaller price area where "
        "touch, return, stress, absorption, or rejection actually occurred. "
        "Formation Range is broad context, not entry zone. Operational decision "
        "zone is Active Core / Density Band."
    )

    if safe_research_panel_value(row, "interaction_core_upper_edge") == "N/A":
        st.info("No interaction core geometry mapped for this case yet.")
        return

    columns = st.columns(3)
    render_research_card(
        columns[0],
        "Formation Range (broad context)",
        [
            ("Formation Range Upper", "formation_upper_edge", "metric"),
            ("Formation Range Lower", "formation_lower_edge", "metric"),
            ("Formation Range Width", "formation_width", "metric"),
        ],
        row,
    )
    render_research_card(
        columns[1],
        "Active RDM Zone / Interaction Core",
        [
            ("Active Core Upper", "interaction_core_upper_edge", "metric"),
            ("Active Core Lower", "interaction_core_lower_edge", "metric"),
            ("Active RDM Zone / Interaction Core Width", "interaction_core_width", "metric"),
            ("Efficiency", "interaction_core_efficiency_ratio", "metric"),
        ],
        row,
    )
    render_research_card(
        columns[2],
        "Core Quality",
        [
            ("Source", "interaction_core_source", "mechanics"),
            ("Points", "interaction_core_points_count", "metric"),
            ("Valid", "interaction_core_valid_flag", "status"),
            ("Width State", "interaction_core_width_state", "capacity"),
        ],
        row,
    )
    density_columns = st.columns(3)
    render_research_card(
        density_columns[0],
        "Interaction Density",
        [
            ("Density State", "interaction_density_state", "capacity"),
            ("Dominant Location", "dominant_interaction_location", "mechanics"),
            ("Peak Price", "interaction_density_peak_price", "metric"),
            ("Weighted Center", "interaction_density_weighted_center", "metric"),
        ],
        row,
    )
    render_research_card(
        density_columns[1],
        "Density Band / Interaction Heart",
        [
            ("Band Upper", "interaction_density_upper_band", "metric"),
            ("Band Lower", "interaction_density_lower_band", "metric"),
            ("Density Band / Interaction Heart Width", "interaction_density_width", "metric"),
            ("Points", "interaction_density_points_count", "metric"),
        ],
        row,
    )
    render_research_card(
        density_columns[2],
        "Core Sub-Zones",
        [
            ("Upper Score", "core_upper_density_score", "metric"),
            ("Middle Score", "core_middle_density_score", "metric"),
            ("Lower Score", "core_lower_density_score", "metric"),
            ("Band", "dominant_interaction_band", "mechanics"),
        ],
        row,
    )
    detail_columns = st.columns(3)
    render_research_card(
        detail_columns[0],
        "Raw Core",
        [
            ("Raw Upper", "raw_interaction_core_upper_edge", "metric"),
            ("Raw Lower", "raw_interaction_core_lower_edge", "metric"),
            ("Raw Width", "raw_interaction_core_width", "metric"),
        ],
        row,
    )
    render_research_card(
        detail_columns[1],
        "Spatial Clamp / Compression",
        [
            ("Clamped Upper", "clamped_interaction_core_upper_edge", "metric"),
            ("Clamped Lower", "clamped_interaction_core_lower_edge", "metric"),
            ("Clamped Width", "clamped_interaction_core_width", "metric"),
            ("Clamp Applied", "core_spatial_clamp_applied", "status"),
            ("Compression Applied", "interaction_core_compression_applied", "status"),
            ("Compression Reason", "interaction_core_compression_reason", "mechanics"),
        ],
        row,
    )
    render_research_card(
        detail_columns[2],
        "Temporal Window",
        [
            ("Window Start", "core_temporal_window_start", "metric"),
            ("Window End", "core_temporal_window_end", "metric"),
            ("Seconds", "core_temporal_window_seconds", "metric"),
            ("Rows", "core_temporal_window_rows", "metric"),
            ("Temporal Filter", "core_temporal_filter_applied", "status"),
        ],
        row,
    )
    render_rdm_section_result(row, "RDM Interaction Core Geometry")


def render_live_rdm_evolution_panel(row):
    st.subheader("Live RDM Evolution - Research Only")
    st.caption(
        "Live-style replay evolution for this zone. It reads historical rows only; "
        "it is not live scanning, not a signal, and not execution."
    )

    if safe_research_panel_value(row, "rdm_live_status") == "N/A":
        st.info("No live RDM evolution data mapped for this case yet.")
        return

    card_columns = st.columns(3)
    render_research_card(
        card_columns[0],
        "Current Live Status",
        [
            ("Raw Status", "raw_live_status", "capacity"),
            ("Guarded Status", "guarded_live_status", "capacity"),
            ("Risk", "rdm_live_risk", "severity"),
            ("Watch", "rdm_live_watch_action", "capacity"),
        ],
        row,
    )
    render_research_card(
        card_columns[1],
        "Zone Contact",
        [
            ("Inside Zone", "inside_zone_flag", "status"),
            ("Touch", "zone_touch_flag", "status"),
            ("Return", "return_to_zone_flag", "status"),
            ("Distance", "distance_to_zone", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[2],
        "Evolution",
        [
            ("Step", "evolution_step", "mechanics"),
            ("Transition", "evolution_transition", "mechanics"),
            ("State", "evolution_state", "mechanics"),
            ("Breach Count", "mechanical_breach_count_live", "metric"),
        ],
        row,
    )
    guard_columns = st.columns(3)
    render_research_card(
        guard_columns[0],
        "Live Guard",
        [
            ("Guard Applied", "live_guard_applied", "status"),
            ("Guard Reason", "live_guard_reason", "mechanics"),
            ("Confirmation Score", "live_confirmation_score", "metric"),
        ],
        row,
    )
    render_research_card(
        guard_columns[1],
        "Persistence",
        [
            ("Breach Streak", "live_breach_streak", "metric"),
            ("Rupture Streak", "live_rupture_streak", "metric"),
            ("Inside Streak", "live_inside_zone_streak", "metric"),
            ("Stress Persistence", "live_stress_persistence", "metric"),
        ],
        row,
    )
    render_research_card(
        guard_columns[2],
        "Confirmations",
        [
            ("Sigma", "sigma_confirmed_breach", "status"),
            ("Capacity", "capacity_confirmed_breach", "status"),
            ("Health", "health_confirmed_collapse", "status"),
            ("Fatigue", "fatigue_confirmed_high", "status"),
            ("Multi Factor", "multi_factor_breach_confirmed", "status"),
        ],
        row,
    )
    st.caption(safe_research_panel_value(row, "rdm_live_reason"))
    table = build_live_rdm_tracking_table(row)
    st.dataframe(sanitize_dataframe_for_display(table), use_container_width=True)
    render_rdm_section_result(row, "Live RDM Evolution")


def render_true_lifecycle_panel(row):
    st.subheader("True Zone Lifecycle - Research Only")
    st.caption(
        "Tracks lifecycle after formation. Formation end is not treated as proof "
        "of zone death."
    )

    if safe_research_panel_value(row, "true_lifecycle_state") == "N/A":
        st.info("No true lifecycle tracking mapped for this case yet.")
        return

    columns = st.columns(3)
    render_research_card(
        columns[0],
        "Formation / Life",
        [
            ("Formation Start", "formation_start_time", "metric"),
            ("Formation End", "formation_end_time", "metric"),
            ("Active Life Start", "active_life_start_time", "metric"),
        ],
        row,
    )
    render_research_card(
        columns[1],
        "Last Interaction",
        [
            ("Last Time", "last_mechanical_interaction_time", "metric"),
            ("Last Price", "last_mechanical_interaction_price", "metric"),
            ("Rows Since", "time_since_last_interaction", "metric"),
        ],
        row,
    )
    render_research_card(
        columns[2],
        "Lifecycle Result",
        [
            ("Dormant", "dormant_state_flag", "status"),
            ("True Death", "true_mechanical_death_flag", "status"),
            ("Death Score", "mechanical_death_score", "metric"),
            ("State", "true_lifecycle_state", "capacity"),
            ("Reason", "mechanical_death_reason", "mechanics"),
        ],
        row,
    )
    render_rdm_section_result(row, "True Zone Lifecycle")


def render_birth_live_degradation_panel(row):
    st.subheader("Birth vs Live Degradation - Research Only")
    st.caption("Observation-only degradation from zone birth baseline to guarded live state.")

    if safe_research_panel_value(row, "birth_vs_live_degradation_state") == "N/A":
        st.info("No birth/live degradation data mapped for this case yet.")
        return

    columns = st.columns(2)
    render_research_card(
        columns[0],
        "Degradation Metrics",
        [
            ("Sigma", "sigma_degradation_from_birth", "metric"),
            ("Rigidity", "rigidity_degradation_from_birth", "metric"),
            ("Fatigue Increase", "fatigue_increase_from_birth", "metric"),
            ("Health", "health_degradation_from_birth", "metric"),
        ],
        row,
    )
    render_research_card(
        columns[1],
        "Degradation State",
        [
            ("State", "birth_vs_live_degradation_state", "capacity"),
            ("Final Status", "rdm_final_status", "capacity"),
            ("Reason", "rdm_final_reason", "mechanics"),
        ],
        row,
    )
    render_rdm_section_result(row, "Birth vs Live Degradation")


def build_live_rdm_tracking_table(row):
    metrics = [
        ("Sigma", "sigma"),
        ("Capacity", "capacity"),
        ("Rigidity", "rigidity"),
        ("Fleche", "fleche"),
        ("Dynamic Fleche", "dynamic_fleche"),
        ("Moment", "moment"),
        ("Load", "load"),
        ("Fatigue", "fatigue"),
        ("Recovery", "recovery"),
        ("Health", "health"),
    ]
    rows = []
    for label, prefix in metrics:
        rows.append(
            {
                "Metric": label,
                "Birth": safe_research_panel_value(row, f"{prefix}_birth"),
                "Live": safe_research_panel_value(row, f"{prefix}_live"),
                "Change": live_change_value(row, prefix),
                "Status": live_metric_status(row, prefix),
            }
        )
    return pd.DataFrame(rows)


def live_change_value(row, prefix):
    if prefix in {"moment", "load", "fatigue", "recovery", "health"}:
        birth = numeric_research_value(row, f"{prefix}_birth")
        live = numeric_research_value(row, f"{prefix}_live")
        if birth is None or live is None:
            return "N/A"
        return round(live - birth, 6)
    return safe_research_panel_value(row, f"{prefix}_change_from_birth")


def live_metric_status(row, prefix):
    direct_field = f"{prefix}_live_status"
    value = safe_research_panel_value(row, direct_field)
    if value != "N/A":
        return value
    if prefix == "health":
        return safe_research_panel_value(row, "health_live_status")
    if safe_research_panel_value(row, f"{prefix}_live") == "N/A":
        return "NO_DATA"
    return "LIVE_SAFE"


def build_birth_current_tracking_table(row):
    metrics = [
        ("Sigma", "sigma"),
        ("Capacity", "capacity"),
        ("Rigidity", "rigidity"),
        ("Resistance", "resistance"),
        ("Fleche", "fleche"),
        ("Dynamic Fleche", "dynamic_fleche"),
        ("Moment", "moment"),
        ("Load", "load"),
        ("Fatigue", "fatigue"),
        ("Recovery", "recovery"),
        ("Health", "health"),
    ]
    rows = []
    for label, prefix in metrics:
        rows.append(
            {
                "Metric": label,
                "Birth": safe_research_panel_value(row, f"{prefix}_birth"),
                "Current": safe_research_panel_value(row, f"{prefix}_current"),
                "Return": safe_research_panel_value(row, f"{prefix}_at_return"),
                "Final": safe_research_panel_value(row, f"{prefix}_final"),
                "Change From Birth": safe_research_panel_value(row, f"{prefix}_change_from_birth"),
                "Status": mechanical_tracking_status(row, prefix),
            }
        )
    return pd.DataFrame(rows)


def mechanical_tracking_status(row, prefix):
    if prefix == "sigma" and safe_research_panel_value(row, "sigma_breach_flag") == "True":
        return "BREACHED"
    if prefix == "capacity" and safe_research_panel_value(row, "capacity_breach_flag") == "True":
        return "BREACHED"
    if prefix == "rigidity" and safe_research_panel_value(row, "rigidity_decay_flag") == "True":
        return "DECAYED"
    if prefix == "fatigue" and safe_research_panel_value(row, "fatigue_breach_flag") == "True":
        return "BREACHED"
    if prefix == "health" and safe_research_panel_value(row, "health_collapse_flag") == "True":
        return "COLLAPSED"
    if prefix == "recovery":
        change = numeric_research_value(row, "recovery_change_from_birth")
        if change is not None and change > 0:
            return "RECOVERED"
    value = safe_research_panel_value(row, f"{prefix}_current")
    if value == "N/A":
        return "NO_DATA"
    return "SAFE"


def numeric_research_value(row, field):
    value = safe_research_panel_value(row, field)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def render_rdm_timeline_panel(row):
    st.subheader("RDM Timeline - Research Only")
    st.caption(
        "Mechanical evolution path for observation research only. It is not a "
        "signal, not execution, and does not affect Dashboard V2 scoring."
    )

    if safe_research_panel_value(row, "timeline_step") == "N/A":
        st.info("No timeline mechanics available yet.")
        return

    card_columns = st.columns(3)
    render_research_card(
        card_columns[0],
        "Current Step",
        [
            ("Step", "timeline_step", "mechanics"),
            ("Position", "timeline_position", "metric"),
            ("Duration", "state_duration", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[1],
        "Transition",
        [
            ("Previous", "previous_state", "mechanics"),
            ("Next", "next_state", "mechanics"),
            ("Reason", "transition_reason", "mechanics"),
        ],
        row,
    )
    render_research_card(
        card_columns[2],
        "Lifecycle Path",
        [
            ("Path", "lifecycle_path", "mechanics"),
            ("Family", "mechanical_family", "mechanics"),
            ("State", "zone_mechanical_state", "mechanics"),
        ],
        row,
    )
    render_rdm_section_result(row, "RDM Timeline")


def render_zone_birth_panel(row):
    st.subheader("Zone Birth Certificate - Research Only")
    st.caption(
        "Research registry for zone identity and formation quality. This is not "
        "a signal, not execution, and not Dashboard V2 scoring."
    )

    if safe_research_panel_value(row, "zone_id") == "N/A":
        st.info("No birth data mapped for this case yet.")
        return

    card_columns = st.columns(3)
    render_research_card(
        card_columns[0],
        "Identity",
        [
            ("Zone ID", "zone_id", "mechanics"),
            ("Zone Type", "zone_type", "mechanics"),
            ("Birth Time", "birth_time", "metric"),
            ("Birth State", "mechanical_birth_state", "capacity"),
        ],
        row,
    )
    render_research_card(
        card_columns[1],
        "Price Range",
        [
            ("Birth Range", "birth_price_range", "metric"),
            ("Upper Edge", "upper_edge", "metric"),
            ("Lower Edge", "lower_edge", "metric"),
            ("Zone Width", "zone_width", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[2],
        "Formation",
        [
            ("Formation Volume", "formation_volume", "metric"),
            ("Formation Delta", "formation_delta", "metric"),
            ("Formation Velocity", "formation_velocity", "metric"),
            ("Formation Quality", "formation_quality", "metric"),
        ],
        row,
    )
    confidence_columns = st.columns(2)
    render_research_card(
        confidence_columns[0],
        "Birth Confidence",
        [
            ("Confidence", "birth_confidence_score", "metric"),
            ("Candidates", "birth_candidate_count", "metric"),
            ("Source", "birth_classification_source", "mechanics"),
        ],
        row,
    )
    render_research_card(
        confidence_columns[1],
        "Birth Reason",
        [
            ("Reason", "birth_reason", "mechanics"),
        ],
        row,
    )
    render_rdm_section_result(row, "Zone Birth Certificate")


def render_zone_life_tracking_panel(row):
    st.subheader("Zone Life Tracking - Research Only")
    st.caption(
        "Observation-only lifecycle tracking for age, tests, decay, and survival."
    )

    if safe_research_panel_value(row, "zone_birth_time") == "N/A":
        st.info("No life tracking data mapped for this case yet.")
        return

    card_columns = st.columns(3)
    render_research_card(
        card_columns[0],
        "Life Window",
        [
            ("Birth Time", "zone_birth_time", "metric"),
            ("Last Test", "zone_last_test_time", "metric"),
            ("Active Duration", "zone_active_duration", "metric"),
            ("Lifetime", "zone_lifetime", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[1],
        "Testing",
        [
            ("Age", "zone_age", "metric"),
            ("Tests", "zone_test_count", "metric"),
            ("Decay Rate", "zone_decay_rate", "metric"),
            ("Survival Ratio", "zone_survival_ratio", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[2],
        "Birth Resistance",
        [
            ("Base Resistance", "base_resistance", "metric"),
            ("Initial Sigma", "initial_sigma_barre", "metric"),
            ("Initial Rigidity", "initial_rigidity", "metric"),
            ("Initial Capacity", "initial_capacity", "metric"),
        ],
        row,
    )
    render_rdm_section_result(row, "Zone Life Tracking")


def render_zone_evolution_panel(row):
    st.subheader("Zone Evolution Chart - Research Only")
    st.caption(
        "Complete mechanical life path for the selected zone. This is observation "
        "research only and does not affect scoring, entries, or execution."
    )

    if safe_research_panel_value(row, "current_state") == "N/A":
        st.info("No evolution data available yet.")
        return

    card_columns = st.columns(3)
    render_research_card(
        card_columns[0],
        "Life Stage",
        [
            ("Birth State", "birth_state", "capacity"),
            ("Current Stage", "current_state", "mechanics"),
            ("Previous Stage", "previous_state_evolution", "mechanics"),
            ("Next Candidate", "next_candidate_state", "mechanics"),
        ],
        row,
    )
    render_research_card(
        card_columns[1],
        "Transition",
        [
            ("Path", "evolution_timeline", "mechanics"),
            ("Transition Reason", "state_transition_reason", "mechanics"),
            ("Transition Count", "transition_count", "metric"),
            ("Transition Strength", "transition_strength", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[2],
        "Progress",
        [
            ("Fatigue Progress", "fatigue_progress", "metric"),
            ("Recovery Progress", "recovery_progress", "metric"),
            ("Sigma Progress", "sigma_progress", "metric"),
            ("Capacity Progress", "capacity_progress", "metric"),
        ],
        row,
    )
    render_rdm_section_result(row, "Zone Evolution Chart")


def render_rdm_verestchaguine_panel(row):
    st.subheader("Verestchaguine Dynamic Fleche - Research Only")
    st.caption(
        "Parallel dynamic fleche model for accumulated deformation. It does not "
        "replace static fleche and does not affect Dashboard V2 scoring."
    )

    if safe_research_panel_value(row, "fleche_dynamic_state") == "N/A":
        st.info("No Verestchaguine dynamic fleche data mapped for this case yet.")
        return

    card_columns = st.columns(3)
    render_research_card(
        card_columns[0],
        "Stress Area",
        [
            ("Omega Stress Area", "omega_stress_area", "metric"),
            ("Stress Center of Gravity", "stress_center_of_gravity", "metric"),
            ("Virtual Moment at G", "virtual_moment_at_g", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[1],
        "Dynamic Fleche",
        [
            ("EI Adaptive", "ei_adaptive", "metric"),
            ("Dynamic Fleche", "fleche_verestchaguine", "metric"),
            ("Dynamic State", "fleche_dynamic_state", "capacity"),
        ],
        row,
    )
    render_research_card(
        card_columns[2],
        "Combined View",
        [
            ("Static Fleche", "zone_fleche_ratio", "metric"),
            ("Combined Fleche Score", "fleche_combined_score", "metric"),
            ("Model", "fleche_model_version", "mechanics"),
        ],
        row,
    )
    render_rdm_section_result(row, "Verestchaguine Dynamic Fleche")


def render_rdm_capacity_panel(row):
    st.subheader("Mechanical Capacity - Research Only")
    st.caption(
        "Capacity context only. Capacity states are not signals, not execution, "
        "and do not change Dashboard V2 scoring."
    )

    if safe_research_panel_value(row, "zone_capacity_state") == "N/A":
        st.info("No mechanical capacity data mapped for this case yet.")
        return

    card_columns = st.columns(4)
    render_research_card(
        card_columns[0],
        "Capacity",
        [
            ("Capacity Ratio", "zone_capacity_ratio", "metric"),
            ("Capacity State", "zone_capacity_state", "capacity"),
            ("Moment Capacity", "zone_moment_capacity", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[1],
        "Residual / Repair",
        [
            ("Residual Strength", "zone_residual_strength", "metric"),
            ("Repair Strength", "zone_repair_strength", "metric"),
            ("Material Recovery", "zone_material_recovery", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[2],
        "Regime Calibration",
        [
            ("Regime Context", "mechanical_regime_context", "capacity"),
            ("Adaptive Threshold", "adaptive_capacity_threshold", "metric"),
            ("Regime Multiplier", "volatility_capacity_multiplier", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[3],
        "Dynamic ELU",
        [
            ("Dynamic ELU", "dynamic_elu_state", "capacity"),
            ("Calibration State", "capacity_calibration_state", "capacity"),
            ("Fatigue", "fatigue_state", "mechanics"),
        ],
        row,
    )
    guard_columns = st.columns(3)
    render_research_card(
        guard_columns[0],
        "Zero Stress Protection",
        [
            ("Active Load", "active_load_flag", "status"),
            ("Zero Stress", "zero_stress_flag", "status"),
            ("Market Silence", "market_silence_flag", "status"),
        ],
        row,
    )
    render_research_card(
        guard_columns[1],
        "Dormant Preparation",
        [
            ("Dormant Preparation", "dormant_preparation_flag", "status"),
            ("Preparation State", "preparation_activation_state", "capacity"),
            ("Capacity Guard", "capacity_guard_applied", "status"),
        ],
        row,
    )
    render_research_card(
        guard_columns[2],
        "Reaction Candidate",
        [
            ("Reaction Candidate", "research_reaction_candidate", "capacity"),
            ("No Active Load Reason", "no_active_load_reason", "mechanics"),
        ],
        row,
    )
    render_rdm_section_result(row, "Mechanical Capacity")


def render_rdm_sigma_panel(row):
    st.subheader("Adaptive Sigma Barre - Research Only")
    st.caption(
        "Per-zone allowable stress model for research review only. Sigma states "
        "are not signals, not entries, and do not change Dashboard V2 scoring."
    )

    if safe_research_panel_value(row, "sigma_state") == "N/A":
        st.info("No adaptive sigma barre data mapped for this case yet.")
        return

    card_columns = st.columns(3)
    render_research_card(
        card_columns[0],
        "Zone Formation",
        [
            ("v Formation", "v_formation", "metric"),
            ("Delta Formation", "delta_formation", "metric"),
            ("t Formation", "t_formation", "metric"),
            ("Base Resistance", "base_zone_resistance", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[1],
        "Sigma Stress",
        [
            ("Sigma Barre Zone", "sigma_barre_zone", "metric"),
            ("Sigma Market", "sigma_market", "metric"),
            ("Stress Utilization", "stress_utilization", "metric"),
            ("Sigma State", "sigma_state", "capacity"),
        ],
        row,
    )
    render_research_card(
        card_columns[2],
        "Adaptive Modifiers",
        [
            ("Volatility Modifier", "volatility_modifier", "metric"),
            ("Fatigue Factor", "fatigue_factor", "metric"),
            ("Failure Risk", "sigma_failure_risk", "severity"),
            ("Model", "sigma_model_version", "mechanics"),
        ],
        row,
    )
    render_rdm_section_result(row, "Adaptive Sigma Barre")


def render_rdm_sigma_evolution_panel(row):
    st.subheader("Sigma Evolution - Research Only")
    st.caption(
        "Mechanical memory view for zone aging, repair, and reinforcement. "
        "This is not a signal, not an entry model, and not Dashboard V2 scoring."
    )

    if safe_research_panel_value(row, "sigma_memory_state") == "N/A":
        st.info("No sigma evolution data mapped for this case yet.")
        return

    card_columns = st.columns(3)
    render_research_card(
        card_columns[0],
        "Zone Memory",
        [
            ("Zone Age", "zone_age", "metric"),
            ("Tests", "zone_test_count", "metric"),
            ("Repair Cycles", "repair_cycles", "metric"),
            ("Reclaim History", "reclaim_history", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[1],
        "Mechanical Memory",
        [
            ("Institutional Reinforcement", "institutional_reinforcement", "metric"),
            ("Mechanical Memory", "mechanical_memory_score", "metric"),
            ("Sigma Aging", "sigma_age_factor", "metric"),
            ("Repair Bonus", "sigma_repair_bonus", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[2],
        "Evolved Sigma",
        [
            ("Adaptive Sigma V2", "adaptive_sigma_barre_v2", "metric"),
            ("Sigma State", "sigma_memory_state", "capacity"),
            ("Base Sigma", "sigma_barre_zone", "metric"),
            ("Stress Utilization", "stress_utilization", "metric"),
        ],
        row,
    )
    render_rdm_section_result(row, "Sigma Evolution")


def render_zone_mechanical_memory_panel(row):
    st.subheader("Zone Mechanical Memory - Research Only")
    st.caption(
        "Per-zone memory object summarized for research. It does not feed live "
        "logic, scoring, entries, or execution."
    )

    if safe_research_panel_value(row, "memory_previous_stress_states") == "N/A":
        st.info("No memory data mapped for this case yet.")
        return

    card_columns = st.columns(3)
    render_research_card(
        card_columns[0],
        "Stress Memory",
        [
            ("Stress States", "memory_previous_stress_states", "mechanics"),
            ("Max Utilization", "memory_max_stress_utilization", "metric"),
            ("Max Sigma Market", "memory_max_sigma_market", "metric"),
            ("Max Fatigue", "memory_max_fatigue_index", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[1],
        "Deformation Memory",
        [
            ("Cumulative Fleche", "memory_cumulative_fleche", "metric"),
            ("Dynamic Fleche", "memory_cumulative_dynamic_fleche", "metric"),
            ("Permanent Deformation", "memory_permanent_deformation", "metric"),
            ("Repair Count", "memory_repair_count", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[2],
        "Cycle Memory",
        [
            ("Rupture Count", "memory_rupture_count", "metric"),
            ("Exhaustion Count", "memory_exhaustion_count", "metric"),
            ("Recovery Count", "memory_recovery_count", "metric"),
            ("Timeline", "memory_timeline_history", "mechanics"),
        ],
        row,
    )
    render_rdm_section_result(row, "Zone Mechanical Memory")


def render_zone_death_panel(row):
    st.subheader("Zone Death Certificate - Research Only")
    st.caption(
        "Final observed outcome registry for research review only. This is not "
        "a signal and does not change Dashboard V2 scoring."
    )

    if safe_research_panel_value(row, "death_cause") == "N/A":
        st.info("No death data mapped for this case yet.")
        return

    card_columns = st.columns(3)
    render_research_card(
        card_columns[0],
        "Outcome",
        [
            ("Death Time", "death_time", "metric"),
            ("Death Cause", "death_cause", "capacity"),
            ("Final State", "final_state", "mechanics"),
            ("Total Tests", "total_tests", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[1],
        "Final Stress",
        [
            ("Age at Death", "zone_age_at_death", "metric"),
            ("Max Utilization", "max_stress_utilization", "metric"),
            ("Final Fleche", "final_fleche", "metric"),
            ("Final Dynamic Fleche", "final_dynamic_fleche", "metric"),
        ],
        row,
    )
    render_research_card(
        card_columns[2],
        "Final Mechanics",
        [
            ("Final Sigma", "final_sigma_state", "capacity"),
            ("Final Capacity", "final_capacity_state", "capacity"),
            ("Repair Count", "final_repair_count", "metric"),
            ("Fatigue Cycles", "final_fatigue_cycles", "metric"),
        ],
        row,
    )
    render_rdm_section_result(row, "Zone Death Certificate")


def render_rdm_section_result(row, section_name):
    st.markdown(f"**{section_name} Result**")
    result_columns = st.columns(4)
    render_research_card(
        result_columns[0],
        "Result",
        [
            ("Zone Status", "rdm_zone_status", "capacity"),
            ("Health Score", "rdm_health_score", "metric"),
        ],
        row,
    )
    render_research_card(
        result_columns[1],
        "Risk",
        [
            ("Risk Level", "rdm_risk_level", "severity"),
            ("Confidence", "rdm_confidence", "confidence"),
        ],
        row,
    )
    render_research_card(
        result_columns[2],
        "Short Explanation",
        [
            ("Reason", "rdm_short_reason", "mechanics"),
        ],
        row,
    )
    render_research_card(
        result_columns[3],
        "Research-only Notice",
        [
            ("Watch Action", "rdm_watch_action", "capacity"),
        ],
        row,
    )
    with result_columns[3]:
        st.caption("Research only. No signal. No execution.")


def render_final_rdm_result(row):
    st.subheader("Final RDM Result - Research Only")
    st.caption(
        "Final mechanical summary for observation research. Active zone references "
        "use Interaction Core Width, while Formation Range remains background context. "
        "Formation Range is broad context, not entry zone. Operational decision "
        "zone is Active Core / Density Band. "
        "This is not a signal, not an entry, not execution, and not Dashboard V2 scoring."
    )

    if safe_research_panel_value(row, "rdm_zone_status") == "N/A":
        st.info("No final RDM result mapped for this case yet.")
        return

    columns = st.columns(3)
    render_research_card(
        columns[0],
        "Zone Result",
        [
            ("ZONE STATUS", "rdm_final_status", "capacity"),
            ("LIVE STATUS", "guarded_live_status", "capacity"),
            ("STATIC STATUS", "rdm_zone_status", "capacity"),
            ("ACTIVE RDM ZONE WIDTH", "interaction_core_width", "metric"),
            ("HEALTH SCORE", "rdm_health_score", "metric"),
        ],
        row,
    )
    render_research_card(
        columns[1],
        "Risk / Confidence",
        [
            ("RISK LEVEL", "rdm_risk_level", "severity"),
            ("CONFIDENCE", "rdm_confidence", "confidence"),
        ],
        row,
    )
    render_research_card(
        columns[2],
        "Reason / Watch",
        [
            ("SHORT REASON", "rdm_short_reason", "mechanics"),
            ("WATCH ACTION", "rdm_watch_action", "capacity"),
            ("FINAL REASON", "rdm_final_reason", "mechanics"),
        ],
        row,
    )


def render_research_card(container, title, fields, row):
    with container:
        st.markdown(f"**{title}**")

        for label, field, badge_type in fields:
            value = safe_research_panel_value(row, field)
            display_value = format_research_label(value)
            badge = research_badge(display_value, badge_type)
            st.markdown(f"{label}: {badge}", unsafe_allow_html=True)


def research_badge(label, badge_type):
    color = research_badge_color(label, badge_type)
    return (
        "<span style='"
        f"background:{color};"
        "color:#111;"
        "padding:0.15rem 0.45rem;"
        "border-radius:0.45rem;"
        "font-size:0.82rem;"
        "font-weight:600;"
        "white-space:nowrap;"
        "'>"
        f"{label}"
        "</span>"
    )


def research_badge_color(label, badge_type):
    normalized = str(label).upper()

    if label == "N/A":
        return "#E5E7EB"

    if badge_type == "confidence":
        if "HIGH" in normalized:
            return "#BBF7D0"
        if "LOW" in normalized or "UNSTABLE" in normalized:
            return "#FECACA"
        return "#BFDBFE"

    if badge_type == "severity":
        if "EXTREME" in normalized:
            return "#FCA5A5"
        if "HIGH" in normalized:
            return "#FDBA74"
        if "MEDIUM" in normalized:
            return "#FDE68A"
        if "LOW" in normalized:
            return "#BFDBFE"
        return "#E5E7EB"

    if badge_type == "status":
        if normalized in {"TRUE", "YES"}:
            return "#BBF7D0"
        if normalized in {"FALSE", "NO"}:
            return "#E5E7EB"
        return "#DBEAFE"

    if badge_type == "mechanics":
        if "RUPTURE" in normalized:
            return "#FCA5A5"
        if "EXHAUST" in normalized or "FATIGUE" in normalized:
            return "#FDBA74"
        if "PLASTIC" in normalized:
            return "#FDE68A"
        if "RECOVER" in normalized:
            return "#BBF7D0"
        if "ELASTIC" in normalized or "RIGID" in normalized:
            return "#BFDBFE"
        if "ABSORPTION" in normalized:
            return "#C4B5FD"
        return "#DBEAFE"

    if badge_type == "metric":
        return "#E0F2FE"

    if badge_type == "capacity":
        if "FAILURE" in normalized or "ELU" in normalized:
            return "#FCA5A5"
        if "RUPTURE" in normalized or "CRITICAL" in normalized or "DEAD" in normalized:
            return "#FCA5A5"
        if "EXHAUST" in normalized or "FATIGUE" in normalized:
            return "#FDBA74"
        if "PROTECTED" in normalized or "RECOVERY" in normalized or "RECOVERING" in normalized:
            return "#BBF7D0"
        if "DORMANT" in normalized:
            return "#E5E7EB"
        if "EXPANSION" in normalized or "HIGH VOLATILITY" in normalized:
            return "#BFDBFE"
        if "ELS" in normalized or "HIGH LOAD" in normalized:
            return "#FDBA74"
        if "WARNING" in normalized:
            return "#FDE68A"
        if "SAFE" in normalized:
            return "#BBF7D0"
        return "#DBEAFE"

    if "FALSE PREPARATION" in normalized or "FAILED" in normalized:
        return "#FECACA"
    if "BREACHED" in normalized or "COLLAPSED" in normalized:
        return "#FCA5A5"
    if "DECAYED" in normalized:
        return "#FDBA74"
    if "RECOVERED" in normalized:
        return "#BBF7D0"
    if "NO DATA" in normalized:
        return "#E5E7EB"
    if "DIRECT REVERSAL" in normalized or "REVERSAL" in normalized:
        return "#FDBA74"
    if "PURE EXPANSION" in normalized or "SUCCESS" in normalized:
        return "#BBF7D0"
    if "CONTEXT ONLY" in normalized:
        return "#E5E7EB"
    return "#DBEAFE"


def safe_research_panel_value(row, field):
    if field not in row.index:
        return "N/A"

    value = row.get(field)

    try:
        if pd.isna(value):
            return "N/A"
    except (TypeError, ValueError):
        pass

    text = str(value).strip()
    if is_time_display_field(field):
        formatted_time = format_market_time(text, include_utc=True)
        if formatted_time:
            return formatted_time

    return text if text else "N/A"


def is_time_display_field(field):
    normalized = str(field).lower()
    return (
        normalized.endswith("_time")
        or normalized.endswith("_timestamp")
        or "_time_" in normalized
        or "timestamp" in normalized
    )


def format_research_label(value):
    replacements = {
        "FALSE_PREPARATION": "False Preparation",
        "NO_RESEARCH_CONTEXT": "Context Only",
        "DIRECT_REVERSAL": "Direct Reversal",
        "HIGH_CONFIDENCE": "High Confidence",
        "DELTA_ZSCORE_EXTREME": "Delta ZScore Extreme",
        "PURE_EXPANSION": "Pure Expansion",
        "EXPANSION_THEN_REVERSAL": "Expansion Then Reversal",
        "FAILED_EXPANSION": "Failed Expansion",
        "RETURN_EXPANSION_OBSERVED": "Return Expansion Observed",
        "RETURN_OBSERVED": "Return Observed",
        "PREPARATION_NO_RETURN": "Preparation No Return",
        "RETURN_FAILURE": "Return Failure",
        "STRONG_SUCCESS": "Strong Success",
        "WEAK_SUCCESS": "Weak Success",
        "UNSTABLE_PREPARATION": "Unstable Preparation",
        "RUPTURE_FAMILY": "Rupture Family",
        "EXHAUSTION_FAMILY": "Exhaustion Family",
        "RECOVERY_FAMILY": "Recovery Family",
        "ELASTIC_FAMILY": "Elastic Family",
        "FATIGUE_FAMILY": "Fatigue Family",
        "PLASTIC_FAMILY": "Plastic Family",
        "FAILED_RETURN_RUPTURE": "Failed Return Rupture",
        "EXPANSION_EXHAUSTION": "Expansion Exhaustion",
        "RECLAIM_RECOVERY": "Reclaim Recovery",
        "RIGID_SUPPORT": "Rigid Support",
        "STRONG_REACTION": "Strong Reaction",
        "RUPTURE_ZONE": "Rupture Zone",
        "EXHAUSTED_ZONE": "Exhausted Zone",
        "RECOVERED_ZONE": "Recovered Zone",
        "ELASTIC_ZONE": "Elastic Zone",
        "RIGID_ZONE": "Rigid Zone",
        "PLASTIC_ZONE": "Plastic Zone",
        "FATIGUE_ZONE": "Fatigue Zone",
        "STRESS": "Stress",
        "ABSORPTION": "Absorption",
        "LOW_FATIGUE": "Low Fatigue",
        "MEDIUM_FATIGUE": "Medium Fatigue",
        "HIGH_FATIGUE": "High Fatigue",
        "CRITICAL_FATIGUE": "Critical Fatigue",
        "NO_RECOVERY": "No Recovery",
        "PARTIAL_RECOVERY": "Partial Recovery",
        "STRONG_RECOVERY": "Strong Recovery",
        "RECOVERED": "Recovered",
        "ELS_ACCEPTABLE_RESEARCH_ZONE": "ELS Acceptable Research Zone",
        "ELS_DEFORMATION_RESEARCH_ZONE": "ELS Deformation Research Zone",
        "HIGH_UTILIZATION_RESEARCH_ZONE": "High Utilization Research Zone",
        "ELU_RUPTURE_RESEARCH_ZONE": "ELU Rupture Research Zone",
        "SAFE": "Safe",
        "WARNING": "Warning",
        "HIGH_LOAD": "High Load",
        "ELS_LIMIT": "ELS Limit",
        "ELU_LIMIT": "ELU Limit",
        "CAPACITY_FAILURE": "Capacity Failure",
        "ELS_SAFE": "ELS Safe",
        "NO_ACTIVE_LOAD_PROTECTED": "No Active Load Protected",
        "DORMANT_OR_UNTESTED_ZONE": "Dormant Or Untested Zone",
        "ACTIVE_REACTION_REVIEW": "Active Reaction Review",
        "ACTIVE_PREPARATION": "Active Preparation",
        "DORMANT_PREPARATION": "Dormant Preparation",
        "FAILED_PREPARATION": "Failed Preparation",
        "EXPLOSIVE_PREPARATION": "Explosive Preparation",
        "UNTESTED_ZONE": "Untested Zone",
        "NO_PENETRATION": "No Penetration",
        "NO_SIGNED_MOMENT": "No Signed Moment",
        "NO_SIGMA_MARKET": "No Sigma Market",
        "NO_MECHANICAL_LOAD": "No Mechanical Load",
        "MECHANICAL_LOAD_SCORE_IGNORED_NO_STRESS": "Mechanical Load Score Ignored No Stress",
        "SAFE_STRESS": "Safe Stress",
        "ELS_STRESS_WARNING": "ELS Stress Warning",
        "ELU_STRESS_CRITICAL": "ELU Stress Critical",
        "SIGMA_RUPTURE_RISK": "Sigma Rupture Risk",
        "SIGMA_BARRE_ZONE_V1": "Sigma Barre Zone V1",
        "FRESH_SIGMA": "Fresh Sigma",
        "AGED_SIGMA": "Aged Sigma",
        "FATIGUED_SIGMA": "Fatigued Sigma",
        "REPAIRED_SIGMA": "Repaired Sigma",
        "INSTITUTIONAL_SIGMA": "Institutional Sigma",
        "CRITICAL_SIGMA": "Critical Sigma",
        "SIGMA_EVOLUTION_V1": "Sigma Evolution V1",
        "DYNAMIC_LOW": "Dynamic Low",
        "DYNAMIC_MEDIUM": "Dynamic Medium",
        "DYNAMIC_HIGH": "Dynamic High",
        "DYNAMIC_CRITICAL": "Dynamic Critical",
        "VERESTCHAGUINE_FLECHE_V1": "Verestchaguine Fleche V1",
        "ELASTIC_BIRTH": "Elastic Birth",
        "RIGID_BIRTH": "Rigid Birth",
        "INSTITUTIONAL_BIRTH": "Institutional Birth",
        "PREPARATION_BIRTH": "Preparation Birth",
        "EXPANSION_BIRTH": "Expansion Birth",
        "UNKNOWN_BIRTH": "Unknown Birth",
        "PREPARATION_RULE": "Preparation Rule",
        "INSTITUTIONAL_RULE": "Institutional Rule",
        "RIGIDITY_RULE": "Rigidity Rule",
        "EXPANSION_RULE": "Expansion Rule",
        "ELASTIC_RULE": "Elastic Rule",
        "FALLBACK": "Fallback",
        "PREPARATION_ZONE": "Formation Range (broad context)",
        "RECOVERY_ZONE": "Recovery Zone",
        "RUPTURE_RESEARCH_ZONE": "Rupture Research Zone",
        "RDM_RESEARCH_ZONE": "RDM Research Zone",
        "RECOVERY_COMPLETE": "Recovery Complete",
        "TIME_DECAY": "Time Decay",
        "DORMANT_EXPIRED": "Dormant Expired",
        "UNKNOWN_DEATH": "Unknown Death",
        "ZONE_BIRTH": "Zone Birth",
        "ELASTIC_STAGE": "Elastic Stage",
        "PLASTIC_STAGE": "Plastic Stage",
        "FATIGUE_STAGE": "Fatigue Stage",
        "RECOVERY_STAGE": "Recovery Stage",
        "EXHAUSTION_STAGE": "Exhaustion Stage",
        "RUPTURE_STAGE": "Rupture Stage",
        "DORMANT_STAGE": "Dormant Stage",
        "ZONE_DEATH": "Zone Death",
        "RECOVERY_CONTEXT": "Recovery Context",
        "EXPANSION_EXHAUSTION_CONTEXT": "Expansion Exhaustion Context",
        "RUPTURE_CONTEXT": "Rupture Context",
        "HIGH_VOLATILITY_CONTEXT": "High Volatility Context",
        "LOW_VOLATILITY_COMPRESSION_CONTEXT": "Low Volatility Compression Context",
        "NORMAL_CONTEXT": "Normal Context",
        "RECOVERY_PROTECTED": "Recovery Protected",
        "EXPANSION_PROTECTED": "Expansion Protected",
        "RUPTURE_CONFIRMED": "Rupture Confirmed",
        "REGIME_PROTECTED": "Regime Protected",
        "ADAPTIVE_NORMAL": "Adaptive Normal",
        "EXTREME": "Extreme",
        "HIGH": "High",
        "MEDIUM": "Medium",
        "LOW": "Low",
        "NONE": "None",
        "TRUE": "True",
        "FALSE": "False",
        "ALIVE": "Alive",
        "RECOVERING": "Recovering",
        "FATIGUED": "Fatigued",
        "CRITICAL": "Critical",
        "EXHAUSTED": "Exhausted",
        "RUPTURED": "Ruptured",
        "DEAD": "Dead",
        "DORMANT": "Dormant",
        "REVIEW_RUPTURE_CONTEXT": "Review Rupture Context",
        "WATCH_EXHAUSTION_BRANCH": "Watch Exhaustion Branch",
        "WATCH_FATIGUE_DECAY": "Watch Fatigue Decay",
        "REVIEW_RECOVERY_BEHAVIOR": "Review Recovery Behavior",
        "WAIT_FOR_ACTIVE_LOAD": "Wait For Active Load",
        "MONITOR_MECHANICAL_CONTEXT": "Monitor Mechanical Context",
        "OBSERVE_ONLY": "Observe Only",
        "LIVE_SAFE": "Live Safe",
        "LIVE_WARNING": "Live Warning",
        "LIVE_FATIGUE": "Live Fatigue",
        "LIVE_BREACH": "Live Breach",
        "LIVE_RECOVERY": "Live Recovery",
        "LIVE_RUPTURE": "Live Rupture",
        "LIVE_DORMANT": "Live Dormant",
        "LIVE_AGING": "Live Aging",
        "OUTSIDE_ZONE_NO_RUPTURE": "Outside Zone No Rupture",
        "PERSISTENT_MULTI_FACTOR_BREACH": "Persistent Multi Factor Breach",
        "RUPTURE_REQUIRES_THREE_ROW_MULTI_FACTOR_CONFIRMATION": "Rupture Requires Three Row Multi Factor Confirmation",
        "PERSISTENT_CONFIRMED_BREACH": "Persistent Confirmed Breach",
        "SINGLE_ROW_BREACH_DOWNGRADED_TO_WARNING": "Single Row Breach Downgraded To Warning",
        "FATIGUE_WITHOUT_CONFIRMED_BREACH": "Fatigue Without Confirmed Breach",
        "RECOVERY_AFTER_STRESS": "Recovery After Stress",
        "INSIDE_ZONE_WITHOUT_CONFIRMED_BREACH": "Inside Zone Without Confirmed Breach",
        "NO_GUARD_NEEDED": "No Guard Needed",
        "REVIEW_LIVE_BREACH_CONTEXT": "Review Live Breach Context",
        "WATCH_LIVE_BREACH": "Watch Live Breach",
        "TO_ACTIVE_LOAD": "To Active Load",
        "TO_ZONE_TOUCH": "To Zone Touch",
        "TO_FATIGUE": "To Fatigue",
        "STRESS_TO_BREACH": "Stress To Breach",
        "STRESS_TO_RECOVERY": "Stress To Recovery",
        "AGING_OUTSIDE_ZONE": "Aging Outside Zone",
        "PREPARATION_ZONE": "Formation Range (broad context)",
        "EPISODE_PRICE_RANGE": "Episode Price Range",
        "SINGLE_PRICE_WIDTH_ESTIMATE": "Single Price Width Estimate",
        "PLACEHOLDER_FALLBACK": "Placeholder Fallback",
        "LIVE_INTERACTION_POINTS": "Live Interaction Points",
        "FALLBACK_ADAPTIVE_CORE": "Fallback Adaptive Core",
        "CORE_TIGHT": "Core Tight",
        "CORE_NORMAL": "Core Normal",
        "CORE_WIDE": "Core Wide",
        "CORE_FALLBACK": "Core Fallback",
        "CORE_TOO_WIDE": "Core Too Wide",
        "CORE_INVALID_TOO_WIDE": "Core Invalid Too Wide",
        "LOW_DENSITY": "Low Density",
        "NORMAL_DENSITY": "Normal Density",
        "HIGH_DENSITY": "High Density",
        "EXTREME_DENSITY": "Extreme Density",
        "UPPER_CORE": "Upper Core",
        "MIDDLE_CORE": "Middle Core",
        "LOWER_CORE": "Lower Core",
        "MULTI_NODE": "Multi Node",
        "NO_CLEAR_DENSITY": "No Clear Density",
        "CLAMPED_TO_FORMATION_RANGE": "Clamped To Formation Range",
        "NO_CLAMP_NEEDED": "No Clamp Needed",
        "CORE_WIDTH_ABOVE_HALF_FORMATION": "Core Width Above Half Formation",
        "INVALID_TOO_WIDE_FALLBACK": "Invalid Too Wide Fallback",
        "BIRTH": "Birth",
        "FORMATION": "Formation",
        "ACTIVE_INTERACTION": "Active Interaction",
        "RETEST": "Retest",
        "MECHANICALLY_DEAD": "Mechanically Dead",
        "MODERATE_DEGRADATION": "Moderate Degradation",
        "SEVERE_DEGRADATION": "Severe Degradation",
        "BREACHED": "Breached",
        "DECAYED": "Decayed",
        "COLLAPSED": "Collapsed",
        "NO_DATA": "No Data",
    }
    text = str(value).strip()

    if text.upper() in replacements:
        return replacements[text.upper()]

    if "_" in text:
        return text.replace("_", " ").title()

    return text


def render_research_case_section(title, row, fields):
    st.markdown(f"**{title}**")
    values = []

    for field in fields:
        if field not in row.index:
            continue

        value = row.get(field)
        if pd.isna(value):
            value = ""

        values.append(
            {
                "field": field,
                "value": value,
            }
        )

    if not values:
        st.info(f"No {title.lower()} fields are available.")
        return

    st.dataframe(
        sanitize_dataframe_for_display(pd.DataFrame(values)),
        use_container_width=True,
        hide_index=True,
    )


def has_research_case_data(row):
    for field in [
        "case_id",
        "preparation_candidate",
        "expansion_type",
        "reversal_type",
        "comparison_group",
        "preparation_result",
        "hypothesis02_state",
    ]:
        if field not in row.index:
            continue

        value = row.get(field)
        if pd.isna(value):
            continue

        text = str(value).strip()

        if text in ["NOT_ANALYZED"]:
            continue

        if text:
            return True

    return False


def filter_dashboard_v2_episodes(display_episodes):
    filter_row_one = st.columns(3)
    filter_row_two = st.columns(3)

    minimum_score = filter_row_one[0].selectbox(
        "V2 Layer Count Proxy >=",
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
        "Max V1 Episode Score",
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
        st.write(f"V1 Count by Score: {count_by_score}")


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


def render_preparation_watch_panel():
    """
    Preparation Watch Panel — research display only.
    Shows episodes where a preparation zone was detected so the researcher
    can cross-reference timestamps with the price chart.
    """
    st.subheader("Preparation Watch")
    st.caption(
        "Episodes where a preparation zone was identified by the research analysis. "
        "Use episode_id or episode_start_time_utc to locate the zone on the price chart. "
        "Research observation only — not a signal."
    )

    if not PREPARATION_LOG_FILE.exists():
        st.info(
            "No preparation zone data found. "
            "Run tools/analyze_phase1b_episode_research.py first."
        )
        return

    try:
        df = pd.read_csv(PREPARATION_LOG_FILE)
    except Exception as err:
        st.warning(f"Could not read preparation log: {err}")
        return

    if df.empty:
        st.info("Research log is empty.")
        return

    # Keep only preparation candidates
    if "preparation_candidate" in df.columns:
        df = df[
            df["preparation_candidate"]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(["true", "1", "yes"])
        ].copy()

    if df.empty:
        st.info("No preparation zone candidates in the current research log.")
        return

    # ── Filters ──────────────────────────────────────────────────────────────
    filter_col, detail_col = st.columns([2, 1])

    family_options = [
        "ALL",
        "EQUILIBRIUM_COMPRESSION",
        "EXTREME_COMPRESSION",
        "AMBIGUOUS",
        "UNKNOWN",
    ]
    with filter_col:
        selected_family = st.selectbox(
            "Prep Family",
            family_options,
            key="prep_watch_family_filter",
        )

    with detail_col:
        show_extra = st.checkbox(
            "Extra columns",
            value=False,
            key="prep_watch_show_extra",
            help="Show pre_equil_rows and prep_family_rule",
        )

    if selected_family != "ALL" and "prep_family" in df.columns:
        df = df[df["prep_family"] == selected_family].copy()

    if df.empty:
        st.info(f"No episodes match prep family: {selected_family}")
        return

    # ── Sort newest first ─────────────────────────────────────────────────────
    # ── Build display columns ─────────────────────────────────────────────────
    core_columns = [
        "episode_id",
        "episode_start_time_utc",
        "preparation_candidate",
        "prep_family",
        "prep_family_confidence",
        "zone_type",
        "manipulation_risk_score",
    ]
    extra_columns = ["pre_equil_rows", "prep_family_rule"]

    display_columns = core_columns + (extra_columns if show_extra else [])
    available = [c for c in display_columns if c in df.columns]

    display_df, display_metadata = apply_research_mapping_display_controls(
        df,
        key_prefix="prep_watch",
        default_limit=200,
        show_all_label="Show all preparation rows",
    )
    display_df = display_df[available]
    render_research_mapping_metrics(
        display_metadata,
        total_label="Total preparation rows",
    )

    st.dataframe(
        sanitize_dataframe_for_display(display_df),
        use_container_width=True,
        hide_index=True,
    )


def _live_csv_panel(file_path, subheader, caption, waiting_msg, cols):
    """Shared loader for all simple live CSV panels."""
    st.subheader(subheader)
    st.caption(caption)
    if not file_path.exists():
        st.info(waiting_msg)
        return None
    try:
        df = pd.read_csv(file_path, low_memory=False)
    except Exception as err:
        st.warning(f"Could not read {file_path.name}: {err}")
        return None
    if df.empty:
        st.info(waiting_msg)
        return None
    return df


def render_live_v2_episodes_panel():
    """LIVE V2 Episodes — closed episodes logged by core.observation_logger. Research only."""
    df = _live_csv_panel(
        LIVE_DASHBOARD_V2_EPISODES_FILE,
        "Live V2 Episodes",
        "Completed V2 observation episodes from core.observation_logger. Research only — not a signal.",
        "No live V2 episodes yet. Waiting for episodes to close...",
        [],
    )
    if df is None:
        return
    cols = [
        "episode_id", "episode_start_timestamp_utc", "episode_end_timestamp_utc",
        "peak_state", "peak_layer_count", "peak_max_severity",
        "peak_primary_context", "peak_observation_confidence",
    ]
    available = [c for c in cols if c in df.columns]
    display_df = (
        df[available].sort_values("episode_id", ascending=False)
        if "episode_id" in available else df[available]
    )
    st.metric("Total V2 episodes", len(df))
    st.dataframe(sanitize_dataframe_for_display(display_df), use_container_width=True, hide_index=True)


def render_live_return_detection_panel():
    """LIVE Return Detection — zones resolved by core.live_return_detection. Research only."""
    df = _live_csv_panel(
        LIVE_RETURN_DETECTION_FILE,
        "Return Detection (LIVE)",
        "Zone return-to-preparation events resolved by core.live_return_detection. Research only.",
        "No return detection records yet. Waiting for zones to resolve...",
        [],
    )
    if df is None:
        return

    has_status = "emit_status" in df.columns
    pending_df = df[df["emit_status"] == "PENDING_FINALIZATION"] if has_status else df
    final_df   = df[df["emit_status"] == "FINALIZED_OUTCOME"]   if has_status else pd.DataFrame()

    unique_zones = df["zone_id"].nunique() if "zone_id" in df.columns else len(df)
    st.metric("Zones with return detected", unique_zones)

    if not pending_df.empty:
        st.markdown("**Prediction available — outcome pending**")
        cols_pending = [
            "episode_id", "zone_id", "emit_status",
            "preparation_low_price", "preparation_high_price",
            "return_to_preparation", "return_price", "return_timestamp",
            "resolved_at_timestamp_utc",
        ]
        avail = [c for c in cols_pending if c in pending_df.columns]
        disp = pending_df[avail].sort_values("episode_id", ascending=False) if "episode_id" in avail else pending_df[avail]
        st.dataframe(sanitize_dataframe_for_display(disp), use_container_width=True, hide_index=True)

    if not final_df.empty:
        st.markdown("**Prediction + observed outcome available**")
        cols_final = [
            "episode_id", "zone_id", "emit_status",
            "return_price", "return_timestamp",
            "failed_after_return", "expansion_type", "expansion_strength",
            "reversal_type", "reversal_strength",
            "resolved_at_timestamp_utc",
        ]
        avail = [c for c in cols_final if c in final_df.columns]
        disp = final_df[avail].sort_values("episode_id", ascending=False) if "episode_id" in avail else final_df[avail]
        st.dataframe(sanitize_dataframe_for_display(disp), use_container_width=True, hide_index=True)


def render_live_rdm_status_panel():
    """LIVE RDM Status — mechanical state summary from core.live_rdm. Research only."""
    df = _live_csv_panel(
        LIVE_RDM_STATE_FILE,
        "RDM Status (LIVE)",
        "Zone mechanical state summary from core.live_rdm (Group A + B). Research only.",
        "No RDM results yet. Waiting for zones to resolve through RDM...",
        [],
    )
    if df is None:
        return

    has_status = "emit_status" in df.columns
    pending_df = df[df["emit_status"] == "PENDING_FINALIZATION"] if has_status else df
    final_df   = df[df["emit_status"] == "FINALIZED_OUTCOME"]   if has_status else pd.DataFrame()

    unique_zones = df["episode_id"].nunique() if "episode_id" in df.columns else len(df)
    st.metric("RDM zones", unique_zones)

    if not pending_df.empty:
        st.markdown("**Structural prediction (PENDING_FINALIZATION)**")
        cols = [
            "episode_id", "case_id", "emit_status",
            "mechanical_family", "mechanical_subtype", "rdm_zone_status",
            "rdm_health_score", "rdm_risk_level", "rdm_watch_action",
            "rdm_short_reason", "resolved_at_timestamp_utc",
        ]
        avail = [c for c in cols if c in pending_df.columns]
        disp = pending_df[avail].sort_values("episode_id", ascending=False) if "episode_id" in avail else pending_df[avail]
        st.dataframe(sanitize_dataframe_for_display(disp), use_container_width=True, hide_index=True)

    if not final_df.empty:
        st.markdown("**Observed outcome (FINALIZED_OUTCOME)**")
        cols = [
            "episode_id", "case_id", "emit_status",
            "failed_after_return", "reversal_type", "reversal_strength",
            "expansion_type", "expansion_strength",
            "max_move_after_return", "direction_after_return",
            "resolved_at_timestamp_utc",
        ]
        avail = [c for c in cols if c in final_df.columns]
        disp = final_df[avail].sort_values("episode_id", ascending=False) if "episode_id" in avail else final_df[avail]
        st.dataframe(sanitize_dataframe_for_display(disp), use_container_width=True, hide_index=True)


def render_live_b10_trajectory_panel():
    """LIVE B10 Structural Trajectory — from core.live_rdm. Research only."""
    df = _live_csv_panel(
        LIVE_B10_TRAJECTORY_FILE,
        "B10 Structural Trajectory (LIVE)",
        "Zone structural trajectory (B8→B9→B10) from core.live_rdm. Research only.",
        "No B10 trajectory data yet. Waiting for zones to resolve through RDM...",
        [],
    )
    if df is None:
        return
    cols = [
        "episode_id", "zone_id", "emit_status", "zone_mechanical_state",
        "visit_count", "health_state", "health_slope",
        "structural_trajectory", "trajectory_score",
        "trajectory_confidence", "trajectory_reason",
    ]
    available = [c for c in cols if c in df.columns]
    display_df = (
        df[available].sort_values("episode_id", ascending=False)
        if "episode_id" in available else df[available]
    )
    st.metric("B10 records", len(df))
    st.dataframe(sanitize_dataframe_for_display(display_df), use_container_width=True, hide_index=True)


def render_live_b11_prediction_panel():
    """LIVE B11 Structural Prediction — from core.live_rdm. Research only."""
    df = _live_csv_panel(
        LIVE_B11_PREDICTION_FILE,
        "B11 Structural Prediction (LIVE)",
        "Zone structural prediction (B11) from core.live_rdm. Research only.",
        "No B11 prediction data yet. Waiting for zones to resolve through RDM...",
        [],
    )
    if df is None:
        return
    cols = [
        "episode_id", "zone_id", "emit_status", "zone_mechanical_state",
        "structural_prediction", "prediction_confidence",
        "prediction_reason", "prediction_score",
    ]
    available = [c for c in cols if c in df.columns]
    display_df = (
        df[available].sort_values("episode_id", ascending=False)
        if "episode_id" in available else df[available]
    )
    st.metric("B11 records", len(df))
    st.dataframe(sanitize_dataframe_for_display(display_df), use_container_width=True, hide_index=True)


def render_live_synthesis_panel():
    """LIVE Synthesis — from core.live_rdm. Research only."""
    df = _live_csv_panel(
        LIVE_SYNTHESIS_FILE,
        "Synthesis (LIVE)",
        "Zone synthesis output from core.live_rdm. Research only.",
        "No synthesis data yet. Waiting for zones to resolve through RDM...",
        [],
    )
    if df is None:
        return
    cols = [
        "episode_id", "zone_id", "emit_status", "zone_mechanical_state",
        "context", "structure", "engagement",
        "flow", "prediction", "coherence", "interpretation",
    ]
    available = [c for c in cols if c in df.columns]
    display_df = (
        df[available].sort_values("episode_id", ascending=False)
        if "episode_id" in available else df[available]
    )
    st.metric("Synthesis records", len(df))
    st.dataframe(sanitize_dataframe_for_display(display_df), use_container_width=True, hide_index=True)


def render_live_preparation_watch_panel():
    """
    LIVE Preparation Watch Panel — research display only.
    Shows Preparation snapshots frozen at LIVE V2 episode close, computed by
    core.observation_logger using the same validated find_preparation_zone /
    ResearchRowIndex / prepare_rows logic as the offline research pipeline
    (imported directly — zero formula drift), applied to a bounded live row
    buffer instead of the full historical dataset.

    Geometry display contract:
    - Formation + Tight Formation: always shown at zone creation.
    - Active Core + Density Band: shown after return_found=True (from
      live_rdm_state.csv PENDING_FINALIZATION record). Zones not yet returned
      show "awaiting return" status.
    - Return Detection uses Formation bounds only (replay parity).
    """
    st.subheader("Preparation Watch (LIVE)")
    st.caption(
        "Preparation zones frozen at LIVE V2 episode close, using the same "
        "validated Preparation logic as offline research. "
        "Use episode_id or episode_start_timestamp_utc to locate the zone "
        "on the live price chart. Research observation only — not a signal."
    )

    if not LIVE_PREPARATION_FILE.exists():
        st.info("No live preparation snapshots yet. Waiting for V2 episodes to close...")
        return

    try:
        prep_df = pd.read_csv(LIVE_PREPARATION_FILE)
    except Exception as err:
        st.warning(f"Could not read live preparation log: {err}")
        return

    if prep_df.empty:
        st.info("No live preparation snapshots yet. Waiting for V2 episodes to close...")
        return

    if "preparation_candidate" in prep_df.columns:
        prep_df = prep_df[
            prep_df["preparation_candidate"]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(["true", "1", "yes"])
        ].copy()

    if prep_df.empty:
        st.info("No live preparation candidates yet.")
        return

    st.caption(
        "Return Detection uses Formation bounds only for replay parity. "
        "Active Core and Density Band are structural context after return. "
        "Return Detection uses CLOSE-only parity with replay — wick touches are not counted."
    )

    # --- Section 1: Formation + Tight Formation (always available) ---
    st.markdown("**Formation Geometry** — frozen at zone creation")
    formation_cols = [
        "episode_id",
        "episode_start_timestamp_utc",
        "frozen_at_row_id",
        "preparation_candidate",
        "preparation_low_price",
        "preparation_high_price",
        "preparation_mid_price",
        "tight_formation_low_price",
        "tight_formation_high_price",
        "tight_formation_mid_price",
        "prep_family",
        "prep_family_confidence",
        "zone_type",
        "manipulation_risk_score",
        "pre_setup_reason",
    ]
    avail_formation = [c for c in formation_cols if c in prep_df.columns]
    formation_display = (
        prep_df[avail_formation].sort_values("episode_id", ascending=False)
        if "episode_id" in avail_formation else prep_df[avail_formation]
    )
    st.dataframe(
        sanitize_dataframe_for_display(formation_display),
        use_container_width=True,
        hide_index=True,
    )

    # --- Section 2: Active Core + Density Band (available after return_found=True) ---
    st.markdown("**Active Core + Density Band** — populated after return_found=True")

    rdm_pending = pd.DataFrame()
    if LIVE_RDM_STATE_FILE.exists():
        try:
            rdm_df = pd.read_csv(LIVE_RDM_STATE_FILE)
            if "emit_status" in rdm_df.columns:
                rdm_pending = rdm_df[
                    rdm_df["emit_status"] == "PENDING_FINALIZATION"
                ].copy()
        except Exception:
            pass

    _GEOMETRY_COLS = [
        "episode_id",
        "interaction_core_upper_edge",
        "interaction_core_lower_edge",
        "interaction_core_mid_price",
        "interaction_core_width",
        "interaction_core_source",
        "interaction_core_valid_flag",
        "interaction_density_upper_band",
        "interaction_density_lower_band",
        "interaction_density_weighted_center",
        "interaction_density_width",
        "interaction_density_score",
    ]

    prep_episode_ids = set(prep_df["episode_id"].astype(str)) if "episode_id" in prep_df.columns else set()

    if not rdm_pending.empty and "episode_id" in rdm_pending.columns:
        geom_avail = [c for c in _GEOMETRY_COLS if c in rdm_pending.columns]
        geom_df = rdm_pending[geom_avail].copy()
        geom_df = geom_df[
            geom_df["episode_id"].astype(str).isin(prep_episode_ids)
        ]
        geom_df = (
            geom_df.sort_values("episode_id", ascending=False)
            if "episode_id" in geom_df.columns else geom_df
        )
        if not geom_df.empty:
            st.dataframe(
                sanitize_dataframe_for_display(geom_df),
                use_container_width=True,
                hide_index=True,
            )
        rdm_episode_ids = set(rdm_pending["episode_id"].astype(str))
        awaiting = sorted(prep_episode_ids - rdm_episode_ids, key=lambda x: int(x) if x.isdigit() else 0, reverse=True)
        if awaiting:
            st.caption(f"Awaiting return (Active Core / Density Band not yet computed): episodes {', '.join(awaiting)}")
    else:
        st.info("Active Core: awaiting return. Density Band: awaiting return.")


def _read_jsonl_tail(path, limit):
    if not path.exists():
        return pd.DataFrame()

    try:
        records = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
    except Exception:
        return pd.DataFrame()

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records[-limit:])


def render_live_lifecycle_panel():
    """
    LIVE Lifecycle Watch Panel — research display only.
    Shows zone/field lifecycle events fed live (at LIVE V2 episode close)
    into the existing, validated context_memory.ZoneLifecycleMemory /
    FieldLifecycleMemory layers via core.live_lifecycle — the same memory
    classes and lifecycle states/thresholds the offline research pipeline
    uses (zero formula drift). Research observation only — not a signal.
    """
    st.subheader("Lifecycle Watch (LIVE)")
    st.caption(
        "Zone and field lifecycle state fed live into ZoneLifecycleMemory / "
        "FieldLifecycleMemory at LIVE V2 episode close — zone_created plus "
        "delta_zscore / preparation_candidate field events (the subset "
        "computable without forward look-ahead). Research observation only."
    )

    if not LIVE_LIFECYCLE_STATE_FILE.exists():
        st.info("No live lifecycle state yet. Waiting for V2 episodes to close...")
        return

    try:
        state_df = pd.read_csv(LIVE_LIFECYCLE_STATE_FILE)
    except Exception as err:
        st.warning(f"Could not read live lifecycle state log: {err}")
        return

    if state_df.empty:
        st.info("No live lifecycle zones yet. Waiting for V2 episodes to close...")
        return

    active_states = {"zone_created", "zone_active", "zone_tested", "zone_reclaimed"}
    active_df = state_df[state_df["lifecycle_state"].isin(active_states)].copy() \
        if "lifecycle_state" in state_df.columns else state_df.copy()

    metric_columns = st.columns(2)
    metric_columns[0].metric("Tracked zones", len(state_df))
    metric_columns[1].metric("Active zones", len(active_df))

    state_columns = [
        "zone_id",
        "zone_type",
        "zone_price",
        "zone_strength",
        "lifecycle_state",
        "lifecycle_path",
        "test_count",
        "rejection_count",
        "reclaim_count",
        "related_episode_id",
        "created_at",
        "last_seen_at",
    ]
    available_state_columns = [c for c in state_columns if c in state_df.columns]

    st.caption("Active zones")
    st.dataframe(
        sanitize_dataframe_for_display(active_df[available_state_columns]),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("All tracked zones (current state)"):
        st.dataframe(
            sanitize_dataframe_for_display(state_df[available_state_columns]),
            use_container_width=True,
            hide_index=True,
        )

    zone_events_df = _read_jsonl_tail(LIVE_LIFECYCLE_EVENTS_FILE, limit=50)
    field_events_df = _read_jsonl_tail(LIVE_FIELD_LIFECYCLE_EVENTS_FILE, limit=50)

    event_columns = [
        "event_timestamp_utc",
        "event_state",
        "zone_id",
        "zone_type",
        "zone_price",
        "related_episode_id",
    ]
    field_event_columns = [
        "event_timestamp_utc",
        "event_state",
        "field_id",
        "field_type",
        "field_value",
        "field_strength",
        "related_episode_id",
    ]

    left_column, right_column = st.columns([1, 1])

    with left_column:
        st.caption("Recent zone lifecycle events")
        if zone_events_df.empty:
            st.info("No zone lifecycle events yet.")
        else:
            available = [c for c in event_columns if c in zone_events_df.columns]
            st.dataframe(
                sanitize_dataframe_for_display(zone_events_df[available].iloc[::-1]),
                use_container_width=True,
                hide_index=True,
            )

    with right_column:
        st.caption("Recent field lifecycle events")
        if field_events_df.empty:
            st.info("No field lifecycle events yet.")
        else:
            available = [c for c in field_event_columns if c in field_events_df.columns]
            st.dataframe(
                sanitize_dataframe_for_display(field_events_df[available].iloc[::-1]),
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
    show_all_v2_episodes=False,
    force_refresh=False,
):
    expected_mode = source_mode_for_observation_mode(observation_mode)
    if not assert_source_mode(file_sources, expected_mode):
        return

    market_rows, observation_events, dashboard_episodes = load_dashboard_data(
        file_sources,
        force_refresh=force_refresh,
    )
    v2_events = pd.DataFrame()
    v2_episodes = pd.DataFrame()

    if observation_mode == "LIVE":
        render_live_last_update_panel(market_rows, file_sources)

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
                market_rows,
                file_sources,
                show_all_v2_episodes=show_all_v2_episodes,
            )

    render_active_source_footer(expected_mode)

    if observation_mode == "HISTORICAL REPLAY":
        st.divider()
        render_preparation_watch_panel()

    if observation_mode == "LIVE":
        st.divider()
        render_live_v2_episodes_panel()
        st.divider()
        render_live_preparation_watch_panel()
        st.divider()
        render_live_lifecycle_panel()
        st.divider()
        render_live_return_detection_panel()
        st.divider()
        render_live_rdm_status_panel()
        st.divider()
        render_live_b10_trajectory_panel()
        st.divider()
        render_live_b11_prediction_panel()
        st.divider()
        render_live_synthesis_panel()


def render_active_source_footer(source_mode):
    st.caption(f"ACTIVE SOURCE: {source_label_for_mode(source_mode)}")


def render_live_last_update_panel(market_rows, file_sources):
    latest_market_time = ""
    latest_row_count = len(market_rows)

    if not market_rows.empty and "market_timestamp" in market_rows.columns:
        latest_market_time = format_market_time(
            market_rows.iloc[-1].get("market_timestamp"),
            include_utc=True,
        )

    market_file = file_sources.get("market_rows")
    file_modified_time = format_file_modified_time(market_file)

    columns = st.columns(4)
    columns[0].metric("LIVE Status", "ALIVE")
    columns[1].metric("Last Market Time", latest_market_time or "N/A")
    columns[2].metric("Market Rows", latest_row_count)
    columns[3].metric("File Updated UTC", file_modified_time or "N/A")

    st.caption(
        "LIVE heartbeat reads market_rows.csv, so the dashboard remains current "
        "even when no statistical event is written."
    )


def format_file_modified_time(path):
    if path is None or not path.exists():
        return ""

    try:
        modified = datetime.fromtimestamp(
            path.stat().st_mtime,
            tz=timezone.utc,
        )
    except OSError:
        return ""

    return modified.strftime("%Y-%m-%d %H:%M:%S")


def render_live_heartbeat(interval_seconds):
    components.html(
        f"""
        <script>
        setTimeout(function() {{
            window.parent.location.reload();
        }}, {int(interval_seconds) * 1000});
        </script>
        """,
        height=0,
    )


def main():
    st.set_page_config(
        page_title="BTC Quant Observation Studio",
        layout="wide",
    )

    if "auto_refresh" not in st.session_state:
        st.session_state["auto_refresh"] = True

    if "refresh_seconds" not in st.session_state:
        st.session_state["refresh_seconds"] = LIVE_HEARTBEAT_SECONDS
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
        st.selectbox(
            "Time Display",
            TIME_DISPLAY_OPTIONS,
            index=0,
            key="time_display_mode",
        )
        st.caption(
            "Stored timestamps remain UTC. This option changes display only."
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
        show_all_v2_episodes = st.checkbox(
            "Show all V2 episodes",
            value=False,
            key="show_all_v2_episodes",
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
    live_heartbeat_enabled = observation_mode == "LIVE"
    fragment_runner = getattr(st, "fragment", None)

    if (
        (auto_refresh_enabled or live_heartbeat_enabled)
        and callable(fragment_runner)
    ):
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
                show_all_v2_episodes=show_all_v2_episodes,
                force_refresh=force_refresh,
            )

        live_observation_fragment()
        return

    if live_heartbeat_enabled and not callable(fragment_runner):
        render_live_heartbeat(
            st.session_state["refresh_seconds"]
        )
    elif auto_refresh_enabled and not callable(fragment_runner):
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
        show_all_v2_episodes=show_all_v2_episodes,
        force_refresh=force_refresh,
    )


if __name__ == "__main__":
    main()

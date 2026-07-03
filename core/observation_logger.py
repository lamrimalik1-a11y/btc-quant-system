import csv
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from tools.analyze_phase1b_episode_research import (
    ResearchRowIndex,
    find_preparation_zone,
    prepare_rows,
    public_preparation_fields,
)
from core.daily_session import (
    SESSION_IDENTITY_FIELDNAMES,
    build_session_identity,
    ensure_identity_csv_schema,
    get_current_session_manifest,
    inherit_session_identity,
)
from core.live_lifecycle import (
    record_live_field_lifecycle_events,
    record_live_preparation_zone_created,
)
from core.live_return_detection import (
    process_live_return_detection_row,
    register_pending_return_zone,
)


OUTPUT_DIR = Path("outputs")
OBSERVATION_EVENTS_FILE = OUTPUT_DIR / "observation_events.csv"
DASHBOARD_EPISODES_FILE = OUTPUT_DIR / "dashboard_episodes.csv"
DASHBOARD_V2_EPISODES_FILE = OUTPUT_DIR / "dashboard_v2_episodes.csv"
LIVE_PREPARATION_FILE = OUTPUT_DIR / "live_preparation_zones.csv"
THROTTLE_ROWS = 5

# Bounded rolling buffer of raw rows used to freeze a Preparation snapshot
# at V2 episode close. find_preparation_zone only ever consults up to 500
# rows strictly before start_row_id (ResearchRowIndex.before_row_id default
# tail), and the rolling baselines (research_range_value/_rolling_range_mean/
# _volume_mean) stabilize within ~70 rows of warmup — so >= ~370 rows of
# history before start_row_id reproduces the offline computation bit-for-bit.
# Observed V2 episode duration in the validated replay is at most 54 rows
# (p99 ~33), so 370 history + 700 buffer leaves ample margin for the rows
# accumulated between episode open and close.
LIVE_PREPARATION_BUFFER_MAXLEN = 700

LIVE_PREPARATION_RAW_FIELDS = [
    "market_timestamp",
    "close",
    "volume",
    "delta",
    "velocity",
    "rvi",
    "price_zscore",
    "volume_zscore",
    "delta_zscore",
    "velocity_zscore",
    "volatility_acceleration",
    "entropy",
    # Added for PHASE 4 (Live RDM): the per-zone row-feature buffer that
    # backfills the preparation-period portion of a zone's row window
    # (core.live_return_detection._seed_feature_window_rows) needs these
    # three regime/state classifications -- already computed onto every
    # live row by core.statistics before it reaches this buffer -- to
    # reproduce live_regime_stress_normalizer / live_evolution_record
    # without drift. Purely additive capture; no formula/threshold changes.
    "volatility_regime",
    "velocity_state",
    "volume_state",
]

LIVE_PREPARATION_FIELDNAMES = [
    "episode_id",
    "episode_start_timestamp_utc",
    "episode_end_timestamp_utc",
    "start_row_id",
    "end_row_id",
    "frozen_at_row_id",
    "frozen_at_timestamp_utc",
    "preparation_zone_found",
    "preparation_candidate",
    "preparation_strength",
    "pre_quiet_score",
    "pre_compression_ratio",
    "pre_range_value",
    "pre_range_ratio",
    "pre_delta_mean",
    "pre_delta_abs_mean",
    "pre_velocity_mean",
    "pre_velocity_abs_mean",
    "pre_zscore_abs_mean",
    "pre_market_bias",
    "pre_setup_quality",
    "pre_setup_reason",
    "preparation_start_row",
    "preparation_end_row",
    "preparation_duration_rows",
    "pre_entropy",
    "pre_price_zscore_mean",
    "pre_range_mean",
    "pre_volume_mean",
    "pre_market_state",
    "preparation_low_price",
    "preparation_high_price",
    "preparation_mid_price",
    "tight_formation_low_price",
    "tight_formation_high_price",
    "zone_return_count",
    "zone_penetration_count",
    "zone_failed_breakout_count",
    "max_penetration_depth_ratio",
    "time_inside_zone_ratio",
    "attacker_persistence_max",
    "penetration_depth_decay",
    "volume_decay_on_attempts",
    "recovery_speed_mean_rows",
    "delta_trap_count",
    "manipulation_risk_score",
    "zone_type",
    "zone_type_confidence",
    "zone_health_grade",
    "pre_equil_rows",
    "pre_delta_sum",
    "prep_family",
    "prep_family_confidence",
    "prep_family_rule",
    "prep_delta_alignment",
    "prep_family_lean",
    *SESSION_IDENTITY_FIELDNAMES,
]

_live_preparation_row_buffer = deque(maxlen=LIVE_PREPARATION_BUFFER_MAXLEN)

NO_STRONG_STATE = "NO_STRONG_CONFLUENCE"
ACTIVE_STATES = {
    "WEAK_CONFLUENCE",
    "MODERATE_CONFLUENCE",
    "STRONG_CONFLUENCE",
}

NO_CONFLUENCE_STATE = "NO_CONFLUENCE"

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

# LIVE-only additive schema. Replay imports V2_EPISODE_FIELDNAMES unchanged.
LIVE_V2_EPISODE_FIELDNAMES = [
    *V2_EPISODE_FIELDNAMES,
    *SESSION_IDENTITY_FIELDNAMES,
]

_previous_dashboard_state = None
_last_event_row_by_type = {}
_active_episode = None
_episode_counter = 0

_previous_dashboard_v2_state = None
_active_v2_episode = None
_v2_episode_counter = 0
_v2_episode_counter_session_id = None



def _initialize_v2_episode_counter(timestamp_utc):
    """Recover the current session counter without changing legacy IDs."""
    global _v2_episode_counter
    global _v2_episode_counter_session_id

    manifest = get_current_session_manifest(timestamp_utc=timestamp_utc)
    if _v2_episode_counter_session_id == manifest.session_id:
        return

    highest_episode_id = 0
    if DASHBOARD_V2_EPISODES_FILE.exists():
        try:
            with DASHBOARD_V2_EPISODES_FILE.open(
                mode="r", newline="", encoding="utf-8"
            ) as file:
                for record in csv.DictReader(file):
                    if record.get("session_id") != manifest.session_id:
                        continue
                    try:
                        episode_id = int(float(record.get("episode_id", 0)))
                    except (TypeError, ValueError):
                        continue
                    highest_episode_id = max(highest_episode_id, episode_id)
        except (OSError, csv.Error):
            highest_episode_id = 0

    _v2_episode_counter = highest_episode_id
    _v2_episode_counter_session_id = manifest.session_id

def log_observation_events(row, statistics, row_id):
    try:
        _log_observation_events(row, statistics, row_id)
    except Exception:
        return


def _log_observation_events(row, statistics, row_id):
    global _previous_dashboard_state
    global _previous_dashboard_v2_state

    _ensure_csv_file(
        OBSERVATION_EVENTS_FILE,
        EVENT_FIELDNAMES
    )
    _ensure_csv_file(
        DASHBOARD_EPISODES_FILE,
        EPISODE_FIELDNAMES
    )
    _ensure_csv_file(
        DASHBOARD_V2_EPISODES_FILE,
        LIVE_V2_EPISODE_FIELDNAMES
    )
    _ensure_csv_file(
        LIVE_PREPARATION_FILE,
        LIVE_PREPARATION_FIELDNAMES
    )

    event_timestamp = datetime.now(timezone.utc).isoformat()
    market_timestamp = _get_market_timestamp(row)
    identity_timestamp = market_timestamp or event_timestamp
    _initialize_v2_episode_counter(identity_timestamp)

    _capture_preparation_row(row, row_id)
    process_live_return_detection_row(row, row_id, event_timestamp)

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

    previous_v2_state = (
        _previous_dashboard_v2_state
        if _previous_dashboard_v2_state is not None
        else NO_CONFLUENCE_STATE
    )

    v2_snapshot = _get_dashboard_v2_snapshot(row)
    new_v2_state = v2_snapshot["state"]

    _update_dashboard_v2_episode(
        row=row,
        row_id=row_id,
        event_timestamp=event_timestamp,
        previous_state=previous_v2_state,
        new_state=new_v2_state,
        snapshot=v2_snapshot,
        identity_timestamp=identity_timestamp,
    )

    _previous_dashboard_v2_state = new_v2_state

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


def _get_dashboard_v2_snapshot(row):
    state = _get(row, "dashboard_v2_state", NO_CONFLUENCE_STATE)

    if state is None:
        state = NO_CONFLUENCE_STATE

    return {
        "state": str(state),
        "layer_count": _to_int(
            _get(row, "dashboard_v2_layer_count"),
            0,
        ),
        "max_severity": _get(row, "dashboard_v2_max_severity"),
        "primary_context": _get(row, "dashboard_v2_primary_context"),
        "conditions": _format_conditions(
            _get(row, "dashboard_v2_conditions")
        ),
        "active_layers": _format_conditions(
            _get(row, "dashboard_v2_active_layers")
        ),
        "observation_confidence": _get(row, "observation_confidence"),
    }


def _capture_preparation_row(row, row_id):
    """
    Append the current row's raw fields to the bounded rolling buffer used
    to freeze a Preparation snapshot at V2 episode close. Mirrors exactly
    the raw column set find_preparation_zone/prepare_rows depend on, read
    via _get so this works whether `row` is a dict or an attribute-bearing
    object (matching the rest of this module's row access pattern).
    """
    captured = {field: _get(row, field) for field in LIVE_PREPARATION_RAW_FIELDS}
    captured["row_id"] = row_id
    _live_preparation_row_buffer.append(captured)


def _freeze_live_preparation_snapshot(episode_row, row_id, event_timestamp):
    """
    At V2 episode close, compute the Preparation zone for this episode using
    the SAME validated logic as offline research (find_preparation_zone /
    ResearchRowIndex / prepare_rows imported directly from
    tools.analyze_phase1b_episode_research — zero formula drift) applied to
    the bounded live row buffer instead of the full historical dataset.

    find_preparation_zone only looks at rows strictly before the episode's
    start_row_id (BACKWARD_WINDOW=100, capped at 500 by
    ResearchRowIndex.before_row_id's default tail), so this is fully
    computable — and frozen here for stability — once the episode has closed.
    """
    try:
        peak_layer_count = int(float(episode_row.get("peak_layer_count") or 0))
        if peak_layer_count < 4:
            return

        start_row_id = episode_row.get("start_row_id")

        if start_row_id is None or not _live_preparation_row_buffer:
            return

        buffered_rows = pd.DataFrame(list(_live_preparation_row_buffer))
        prepared = prepare_rows(buffered_rows)

        if prepared.empty:
            return

        row_index = ResearchRowIndex(prepared)
        preparation_zone = find_preparation_zone(row_index, start_row_id=start_row_id)
        public_fields = public_preparation_fields(preparation_zone)

        snapshot_row = {
            "episode_id": episode_row.get("episode_id"),
            "episode_start_timestamp_utc": episode_row.get("episode_start_timestamp_utc"),
            "episode_end_timestamp_utc": event_timestamp,
            "start_row_id": start_row_id,
            "end_row_id": row_id,
            "frozen_at_row_id": row_id,
            "frozen_at_timestamp_utc": event_timestamp,
            **inherit_session_identity(episode_row),
        }
        for field in LIVE_PREPARATION_FIELDNAMES:
            if field not in snapshot_row:
                snapshot_row[field] = public_fields.get(field, "")

        _append_rows(
            LIVE_PREPARATION_FILE,
            LIVE_PREPARATION_FIELDNAMES,
            [snapshot_row],
        )

        record_live_preparation_zone_created(snapshot_row, episode_row, event_timestamp)
        record_live_field_lifecycle_events(snapshot_row, episode_row, event_timestamp)
        # PHASE 4 (Live RDM): hand the rolling preparation buffer's current
        # snapshot to the return-detection registration so it can backfill
        # the PREPARATION-period portion of its new per-zone row-feature
        # window (rows already scrolled out of any per-row watcher's reach
        # by the time a zone registers) -- the same buffer
        # find_preparation_zone itself just consumed above, reused for a
        # second validated purpose with zero formula drift.
        register_pending_return_zone(
            snapshot_row, episode_row, event_timestamp, list(_live_preparation_row_buffer)
        )
    except Exception:
        return


def _update_dashboard_v2_episode(
    row,
    row_id,
    event_timestamp,
    previous_state,
    new_state,
    snapshot,
    identity_timestamp,
):
    global _active_v2_episode
    global _v2_episode_counter

    is_active = new_state != NO_CONFLUENCE_STATE

    if previous_state == NO_CONFLUENCE_STATE and is_active:
        _v2_episode_counter += 1
        _active_v2_episode = {
            "episode_id": _v2_episode_counter,
            "episode_start_timestamp_utc": event_timestamp,
            "start_row_id": row_id,
            "peak_state": new_state,
            "peak_layer_count": snapshot["layer_count"],
            "peak_max_severity": snapshot["max_severity"],
            "peak_primary_context": snapshot["primary_context"],
            "peak_conditions": snapshot["conditions"],
            "peak_active_layers": snapshot["active_layers"],
            "peak_observation_confidence": snapshot["observation_confidence"],
            "start_price": _get(row, "close"),
            "peak_rvi": _to_number(_get(row, "rvi")),
            "peak_velocity": _to_number(_get(row, "velocity")),
            "peak_delta_zscore": _to_number(_get(row, "delta_zscore")),
            **build_session_identity(
                _v2_episode_counter,
                case_id=f"LIVE_PREP_ZONE_{_v2_episode_counter}",
                timestamp_utc=identity_timestamp,
            ),
        }

    if _active_v2_episode is None:
        return

    _update_v2_episode_peak(
        row=row,
        snapshot=snapshot,
    )

    if is_active is False and previous_state != NO_CONFLUENCE_STATE:
        episode_row = _build_v2_episode_row(
            row=row,
            row_id=row_id,
            event_timestamp=event_timestamp,
        )
        _append_rows(
            DASHBOARD_V2_EPISODES_FILE,
            LIVE_V2_EPISODE_FIELDNAMES,
            [episode_row]
        )
        _freeze_live_preparation_snapshot(
            episode_row=episode_row,
            row_id=row_id,
            event_timestamp=event_timestamp,
        )
        _active_v2_episode = None


def _update_v2_episode_peak(row, snapshot):
    if (
        snapshot["layer_count"]
        >= _active_v2_episode.get("peak_layer_count", 0)
    ):
        _active_v2_episode["peak_state"] = snapshot["state"]
        _active_v2_episode["peak_layer_count"] = snapshot["layer_count"]
        _active_v2_episode["peak_max_severity"] = snapshot["max_severity"]
        _active_v2_episode["peak_primary_context"] = snapshot["primary_context"]
        _active_v2_episode["peak_conditions"] = snapshot["conditions"]
        _active_v2_episode["peak_active_layers"] = snapshot["active_layers"]
        _active_v2_episode["peak_observation_confidence"] = snapshot[
            "observation_confidence"
        ]

    rvi = _to_number(_get(row, "rvi"))
    velocity = _to_number(_get(row, "velocity"))
    delta_zscore = _to_number(_get(row, "delta_zscore"))

    if rvi is not None:
        peak_rvi = _active_v2_episode.get("peak_rvi")
        if peak_rvi is None or rvi > peak_rvi:
            _active_v2_episode["peak_rvi"] = rvi

    if velocity is not None:
        peak_velocity = _active_v2_episode.get("peak_velocity")
        if peak_velocity is None or velocity > peak_velocity:
            _active_v2_episode["peak_velocity"] = velocity

    if delta_zscore is not None:
        peak_delta_zscore = _active_v2_episode.get("peak_delta_zscore")
        if (
            peak_delta_zscore is None
            or abs(delta_zscore) > abs(peak_delta_zscore)
        ):
            _active_v2_episode["peak_delta_zscore"] = delta_zscore


def _build_v2_episode_row(row, row_id, event_timestamp):
    start_timestamp = _active_v2_episode["episode_start_timestamp_utc"]

    return {
        "episode_id": _active_v2_episode["episode_id"],
        "episode_start_timestamp_utc": start_timestamp,
        "episode_end_timestamp_utc": event_timestamp,
        "duration_seconds": _duration_seconds(
            start_timestamp,
            event_timestamp
        ),
        "start_row_id": _active_v2_episode["start_row_id"],
        "end_row_id": row_id,
        "peak_state": _active_v2_episode["peak_state"],
        "peak_layer_count": _active_v2_episode["peak_layer_count"],
        "peak_max_severity": _active_v2_episode["peak_max_severity"],
        "peak_primary_context": _active_v2_episode["peak_primary_context"],
        "peak_conditions": _active_v2_episode["peak_conditions"],
        "peak_active_layers": _active_v2_episode["peak_active_layers"],
        "peak_observation_confidence": _active_v2_episode[
            "peak_observation_confidence"
        ],
        "start_price": _active_v2_episode["start_price"],
        "end_price": _get(row, "close"),
        "peak_rvi": _active_v2_episode.get("peak_rvi"),
        "peak_velocity": _active_v2_episode.get("peak_velocity"),
        "peak_delta_zscore": _active_v2_episode.get("peak_delta_zscore"),
        **{
            field: _active_v2_episode.get(field, "")
            for field in SESSION_IDENTITY_FIELDNAMES
        },
    }


def _ensure_csv_file(path, fieldnames):
    return ensure_identity_csv_schema(path, fieldnames)


def _migrate_csv_header(path, current_header, fieldnames):
    del current_header
    return ensure_identity_csv_schema(path, fieldnames)


def _write_header(path, fieldnames):
    return ensure_identity_csv_schema(path, fieldnames)


def _append_rows(path, fieldnames, rows):
    effective_fieldnames = ensure_identity_csv_schema(path, fieldnames)
    with path.open(
        mode="a", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=effective_fieldnames,
            extrasaction="ignore",
        )
        writer.writerows(
            {
                field: row.get(field, "")
                for field in effective_fieldnames
            }
            for row in rows
        )

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


def _to_int(value, default=None):
    number = _to_number(value)

    if number is None:
        return default

    return int(number)


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

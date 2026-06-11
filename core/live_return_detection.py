"""
LIVE Return Detection / Reversal Context (PHASE 3B of the LIVE integration roadmap).

Builds a streaming, event-driven live equivalent of the offline forward-analysis
chain — detect_preparation_return / calculate_after_return_expansion /
find_reversal_event / analyze_reversal_context / analyze_expansion_reversal_split
(tools.analyze_phase1b_episode_research) — and feeds the resulting fields into
the already-validated Phase 3A lifecycle wiring (core.live_lifecycle) so that
zone_tested / zone_rejected / zone_reclaimed / expansion_state / reversal_state /
hypothesis02_state are emitted automatically, with zero formula/threshold drift.

────────────────────────────────────────────────────────────────────────────
DESIGN — "Accept unbounded logical tracking" (per the explicit Phase 3B decision)
────────────────────────────────────────────────────────────────────────────
Offline, analyze_episode computes return_context FIRST — an unbounded forward
scan (rows.after_time(episode_end_dt)) for the first preparation revisit — and
only THEN computes reversal_context / expansion_split from it, both of which
are bounded to a 4-hour window anchored at episode close (or at the return
point). Mirroring that exact dependency order live means nothing downstream of
return_context is computed or emitted until the return point itself is found.
A zone whose return has not yet occurred simply stays "pending":

    A pending zone remains pending until:
      - return_to_preparation is detected, or
      - process restart, or
      - natural eviction through existing bounded memory mechanisms

No timeout / expiry / max-age / live-only filter is introduced anywhere in this
module. _pending_zones is a plain dict that grows as preparation_candidate
zones are created and shrinks as returns are detected — its bound is simply
how many zones the live process creates, the same kind of "bound" that
ZoneLifecycleMemory itself already relies on (MARKET_CONTEXT_MEMORY_SIZE).

The ONLY genuinely unbounded operation is the per-row return-point watch
(_advance_pending_zone's zone-bounds check — the live mirror of
detect_preparation_return's rows.after_time(episode_end_dt) scan). Everything
else this module computes is bounded to <= 4 hours from a known anchor
(episode_end_dt or return_dt) and is delegated, VERBATIM, to the validated
offline functions (calculate_after_return_expansion / analyze_reversal_context /
analyze_expansion_reversal_split / calculate_window_extremes / etc.), run once
against a small ResearchRowIndex built from the accumulated bounded buffer —
the same "accumulate, then compute with the validated batch function" pattern
core.observation_logger._freeze_live_preparation_snapshot already established
for find_preparation_zone, just run forward instead of backward.

────────────────────────────────────────────────────────────────────────────
WHAT IS DELIBERATELY NOT REPRODUCED (documented, not approximated)
────────────────────────────────────────────────────────────────────────────
- zone_revisit_count: offline counts EVERY contiguous preparation-revisit group
  across the rest of the dataset — itself an unbounded forward scan distinct
  from the bounded one this module performs. It is not in the user's required
  live-field list and no required field's formula consumes it
  (is_failed_after_return / is_reversal_after_return / classify_reversal_type
  only need the FIRST revisit's return point and its bounded 4h after-return
  expansion). Reproducing it live would require retaining an unbounded forward
  buffer per pending zone — a brand new mechanism the Phase 3B decision rules
  out. Left blank here, exactly as zone_expired/zone_broken are intentionally
  never emitted live (see core.live_lifecycle's module docstring).
- hypothesis02_state's PREPARATION_NO_RETURN / NO_RESEARCH_CONTEXT outcomes:
  offline reaches these only once a full-dataset scan concludes a return NEVER
  happens — a conclusion live can never reach for a zone that is still pending
  (it might return tomorrow). Field events for hypothesis02_state are therefore
  only emitted once a pending zone resolves (return_to_preparation becomes
  true), so only RETURN_FAILURE / RETURN_EXPANSION_OBSERVED / RETURN_OBSERVED
  are live-reachable — never a premature "it will never return".
"""
from __future__ import annotations

import csv
from datetime import timedelta
from pathlib import Path

import pandas as pd

from tools.analyze_phase1b_episode_research import (
    HORIZONS,
    RETURN_EXPANSION_SUCCESS_THRESHOLD,
    ResearchRowIndex,
    analyze_expansion_reversal_split,
    analyze_reversal_context,
    calculate_after_return_expansion,
    calculate_window_extremes,
    episode_direction_proxy,
    format_datetime,
    nearest_close_at_or_after,
    parse_datetime_value,
    prepare_rows,
    round_float,
    subtract,
    to_float,
    to_int,
    truthy_value,
)
from core.live_lifecycle import (
    live_zone_id,
    record_live_return_field_lifecycle_events,
    record_live_return_lifecycle_events,
)
from core.live_rdm import (
    append_live_b12_validation_for_case,
    append_live_outcome_for_case,
    compute_live_rdm_for_case,
)

OUTPUT_DIR = Path("outputs")
LIVE_RETURN_DETECTION_FILE = OUTPUT_DIR / "live_return_detection.csv"

LIVE_RETURN_DETECTION_FIELDNAMES = [
    "zone_id",
    "episode_id",
    "emit_status",
    "start_row_id",
    "episode_end_timestamp_utc",
    "episode_direction_proxy",
    "preparation_low_price",
    "preparation_high_price",
    "return_to_preparation",
    "return_price",
    "return_timestamp",
    "return_row",
    "failed_after_return",
    "expansion_type",
    "expansion_strength",
    "reversal_type",
    "reversal_strength",
    "resolved_at_timestamp_utc",
]

FOUR_HOURS = timedelta(hours=4)

# reversal_distances_by_horizon only ever consults these five — classify_future_
# direction's 2h/4h/day_end horizons are not consumed by any required field's
# formula, so they are intentionally not computed (keeps the bounded window
# anchored strictly at end_dt + 4h, never wider).
_REVERSAL_HORIZON_LABELS = ["1m", "5m", "15m", "30m", "1h"]

# PHASE 4 (Live RDM) -- per the user's explicit decision to build a new
# per-zone row-feature buffer rather than document Group B as a limitation.
# This is the exact field set build_live_rdm_evolution / live_evolution_record
# / live_regime_stress_normalizer / attach_historical_delta_to_live_rows read
# from a zone's `historical_rows` (research/zone_mechanics_calculator.py
# lines ~1893-2062, ~2491-2528) -- nothing more, nothing less. row_id/
# market_timestamp/close anchor the window (live_row_window); delta/
# delta_zscore/velocity_zscore/volume_zscore/volatility_regime/velocity_state/
# volume_state are the per-row stress-mechanics inputs those formulas consume
# verbatim. All are already computed onto every live row by core.statistics
# (or, for the preparation-period portion, retained in
# core.observation_logger's rolling _live_preparation_row_buffer once
# LIVE_PREPARATION_RAW_FIELDS captures them -- see that module's PHASE 4 note).
FEATURE_WINDOW_FIELDS = (
    "row_id",
    "market_timestamp",
    "close",
    "delta",
    "delta_zscore",
    "velocity_zscore",
    "volume_zscore",
    "volatility_regime",
    "velocity_state",
    "volume_state",
)

_pending_zones = {}


class _PendingReturnZone:
    """
    State for one Preparation zone awaiting return-to-preparation detection —
    the live mirror of one detect_preparation_return invocation, decomposed
    into incrementally-checkable steps. zone_low/zone_high/episode_direction/
    end_dt/end_price are frozen at registration (identical to what offline
    would read from the same episode/preparation_zone), exactly as
    record_live_preparation_zone_created freezes its zone fields at episode
    close.
    """

    __slots__ = (
        "zone_id",
        "episode_id",
        "episode_row",
        "snapshot_row",
        "episode_direction",
        "end_dt",
        "end_price",
        "zone_low",
        "zone_high",
        "episode_window_rows",
        "episode_window_complete",
        "return_found",
        "return_dt",
        "return_price",
        "return_row_id",
        "revisit_group_active",
        "revisit_group_row_count",
        "revisit_group_last_row_id",
        "return_window_rows",
        "return_window_complete",
        "feature_window_rows",
        "feature_capture_complete",
        "early_emit_done",
        "post_return_feature_window_rows",
        "post_return_capture_complete",
    )

    def __init__(
        self,
        zone_id,
        episode_id,
        episode_row,
        snapshot_row,
        episode_direction,
        end_dt,
        end_price,
        zone_low,
        zone_high,
        seed_row,
        feature_seed_rows=(),
    ):
        self.zone_id = zone_id
        self.episode_id = episode_id
        self.episode_row = episode_row
        self.snapshot_row = snapshot_row
        self.episode_direction = episode_direction
        self.end_dt = end_dt
        self.end_price = end_price
        self.zone_low = zone_low
        self.zone_high = zone_high

        self.episode_window_rows = [seed_row]
        self.episode_window_complete = False

        self.return_found = False
        self.return_dt = None
        self.return_price = None
        self.return_row_id = None
        self.revisit_group_active = False
        self.revisit_group_row_count = 0
        self.revisit_group_last_row_id = None

        self.return_window_rows = []
        self.return_window_complete = False

        # PHASE 4 (Live RDM) -- per-zone row-feature window spanning
        # [preparation_start_row, return_row], the same span
        # live_row_window resolves offline (start = min(preparation_start_row,
        # start_row_id, return_row); end = max(end_row_id, return_row,
        # preparation_end_row), and return_row is always the latter's max
        # since it is by construction found strictly after end_dt). Seeded
        # at registration with the already-elapsed preparation-period prefix
        # (backfilled from the rolling preparation buffer -- see
        # _seed_feature_window_rows) and extended forward, row by row, until
        # the return point itself is captured.
        self.feature_window_rows = list(feature_seed_rows)
        self.feature_capture_complete = False
        self.early_emit_done = False

        # B12 (Live Validation Instrumentation) -- ADDITIVE, research-only.
        # Mirrors feature_window_rows' shape (FEATURE_WINDOW_FIELDS) but spans
        # the POST-return period [return_dt, return_dt + FOUR_HOURS], the same
        # bound already used for return_window_rows. This is the new buffer
        # that makes the rich per-row inputs (delta/zscores/regime/state)
        # available after the return point, where feature_window_rows (capped
        # at feature_capture_complete=True, set the instant return_found flips
        # True) does not reach. Does not alter feature_window_rows or any
        # existing buffer/flag.
        self.post_return_feature_window_rows = []
        self.post_return_capture_complete = False

    def is_ready_to_finalize(self):
        return (
            self.return_found
            and self.episode_window_complete
            and self.return_window_complete
        )


def reset_live_return_detection():
    """Used only by validation harnesses to start a clean, isolated run."""
    _pending_zones.clear()


def get_pending_zone_records():
    """Snapshot of zones still awaiting return detection (diagnostics/dashboard)."""
    return [
        {
            "zone_id": pending.zone_id,
            "episode_id": pending.episode_id,
            "episode_direction_proxy": pending.episode_direction,
            "preparation_low_price": pending.snapshot_row.get("preparation_low_price"),
            "preparation_high_price": pending.snapshot_row.get("preparation_high_price"),
            "episode_end_timestamp_utc": pending.episode_row.get("episode_end_timestamp_utc"),
            "return_found": pending.return_found,
        }
        for pending in _pending_zones.values()
    ]


def _seed_feature_window_rows(preparation_buffer_rows, preparation_start_row):
    """
    Backfills the PREPARATION-period prefix of a new per-zone row-feature
    window -- rows from preparation_start_row through the registering
    episode's close, which by registration time have already scrolled past
    any per-row watcher's reach -- from a snapshot of
    core.observation_logger's rolling _live_preparation_row_buffer (handed
    in by _freeze_live_preparation_snapshot, which already proved this same
    buffer warm/sufficient for find_preparation_zone's identical backward
    span). Reads exactly FEATURE_WINDOW_FIELDS, the field set
    LIVE_PREPARATION_RAW_FIELDS now captures (plus row_id) for precisely
    this purpose -- a pure data-capture extension, zero formula drift.
    Forward rows (registration onward, through the return point) are
    appended live by _advance_pending_zone; together the two halves span
    exactly [preparation_start_row, return_row] -- live_row_window's window.
    """
    if not preparation_buffer_rows:
        return []

    start_row = to_float(preparation_start_row)
    seeded = []
    seen_row_ids = set()
    for buffered_row in preparation_buffer_rows:
        row_id_value = to_float(buffered_row.get("row_id"))
        if row_id_value is None or row_id_value in seen_row_ids:
            continue
        if start_row is not None and row_id_value < start_row:
            continue
        seen_row_ids.add(row_id_value)
        seeded.append({field: buffered_row.get(field) for field in FEATURE_WINDOW_FIELDS})
    return seeded


def register_pending_return_zone(snapshot_row, episode_row, event_timestamp, preparation_buffer_rows=None):
    """
    Begins streaming, event-driven tracking of a freshly-created live
    Preparation zone's eventual return-to-preparation — the live equivalent of
    detect_preparation_return's setup. Gated on preparation_candidate exactly
    like record_live_preparation_zone_created (preparation_candidate and
    preparation_zone_found are the SAME validated value offline — both are
    `candidate` in find_preparation_zone's return dict), so a pending watch
    begins precisely when, and only when, a zone_created lifecycle event is
    also recorded for this zone.
    """
    if not truthy_value(snapshot_row.get("preparation_candidate")):
        return

    episode_id = episode_row.get("episode_id")
    zone_id = live_zone_id(episode_id)

    if zone_id in _pending_zones:
        return

    end_dt = parse_datetime_value(episode_row.get("episode_end_timestamp_utc"))
    end_price = to_float(episode_row.get("end_price"))
    zone_low = to_float(snapshot_row.get("preparation_low_price"))
    zone_high = to_float(snapshot_row.get("preparation_high_price"))

    if end_dt is None or end_price is None or zone_low is None or zone_high is None:
        return

    if zone_low > zone_high:
        zone_low, zone_high = zone_high, zone_low

    episode_direction = episode_direction_proxy(episode_row)

    # The row that closed the episode (market_datetime == end_dt) is the first
    # row of the bounded [end_dt, end_dt + 4h] window offline consults — but by
    # the time this zone is registered, the per-row watcher has already moved
    # past it. Seed it explicitly so the accumulated buffer is a faithful,
    # gap-free prefix of that window (mirrors rows.between(end_dt, ...,
    # include_end=True), which always includes the row at end_dt itself).
    seed_row = {
        "market_timestamp": episode_row.get("episode_end_timestamp_utc") or event_timestamp,
        "close": episode_row.get("end_price"),
        "row_id": episode_row.get("end_row_id"),
    }

    feature_seed_rows = _seed_feature_window_rows(
        preparation_buffer_rows, snapshot_row.get("preparation_start_row")
    )

    _pending_zones[zone_id] = _PendingReturnZone(
        zone_id=zone_id,
        episode_id=episode_id,
        episode_row=dict(episode_row),
        snapshot_row=dict(snapshot_row),
        episode_direction=episode_direction,
        end_dt=end_dt,
        end_price=end_price,
        zone_low=zone_low,
        zone_high=zone_high,
        seed_row=seed_row,
        feature_seed_rows=feature_seed_rows,
    )


def process_live_return_detection_row(row, row_id, event_timestamp):
    """
    Per-row watcher: advances every currently-pending zone with this market
    row, and finalizes (computes + emits) any zone whose unbounded return-point
    search has resolved AND whose two bounded 4h windows have fully
    accumulated. Called once per live market row, mirroring how
    _capture_preparation_row feeds the backward-looking Preparation buffer.
    """
    if not _pending_zones:
        return

    market_timestamp = _field_value(row, "market_timestamp")
    market_dt = parse_datetime_value(market_timestamp)
    close_price = to_float(_field_value(row, "close"))

    if market_dt is None or close_price is None:
        return

    raw_row = {
        "market_timestamp": market_timestamp,
        "close": _field_value(row, "close"),
        "row_id": row_id,
    }

    # PHASE 4 (Live RDM) -- the full per-row feature snapshot forward-captured
    # into each pending zone's feature_window_rows (see FEATURE_WINDOW_FIELDS
    # for why exactly these fields and no others). All are already present on
    # the live market row by the time it reaches this watcher (computed
    # upstream by core.statistics), so this is a direct, verbatim read --
    # zero derivation, zero formula drift.
    feature_row = {
        "row_id": row_id,
        "market_timestamp": market_timestamp,
        "close": _field_value(row, "close"),
        "delta": _field_value(row, "delta"),
        "delta_zscore": _field_value(row, "delta_zscore"),
        "velocity_zscore": _field_value(row, "velocity_zscore"),
        "volume_zscore": _field_value(row, "volume_zscore"),
        "volatility_regime": _field_value(row, "volatility_regime"),
        "velocity_state": _field_value(row, "velocity_state"),
        "volume_state": _field_value(row, "volume_state"),
    }

    ready_zone_ids = []
    for zone_id, pending in _pending_zones.items():
        _advance_pending_zone(pending, market_dt, close_price, row_id, raw_row, feature_row)
        # Two-phase emit: fire Group A/B + B8-B11 + Synthesis immediately when
        # return_found flips True (feature_window is sealed at this point).
        # The 4h finalization later appends only the outcome fields — no recompute.
        if pending.return_found and not pending.early_emit_done:
            _early_emit_pending_zone(pending, event_timestamp)
            pending.early_emit_done = True
        if pending.is_ready_to_finalize():
            ready_zone_ids.append(zone_id)

    for zone_id in ready_zone_ids:
        pending = _pending_zones.pop(zone_id)
        _finalize_pending_zone(pending, event_timestamp)


def _early_emit_pending_zone(pending, event_timestamp):
    """
    Fires at the exact row where return_found flips True. At that moment
    feature_capture_complete is also True (set by _advance_pending_zone on
    the same row), so feature_window spans [preparation_start_row, return_row]
    completely. Group A/B + B8-B11 + Synthesis use only feature_window and
    snapshot_row — neither depends on the 4h-window future fields — so all
    structural prediction fields are correct and final here.

    Appends a PENDING_FINALIZATION record to live_return_detection.csv and
    triggers the full RDM pipeline. The 4h-window outcome fields
    (reversal_type, failed_after_return, max_move_after_return, etc.) are
    left as empty strings. _finalize_pending_zone appends the complementary
    FINALIZED_OUTCOME record once both 4h buffers complete.
    """
    try:
        immediate_return_context = {
            "return_to_preparation": True,
            "time_to_return_minutes": round_float(
                (pending.return_dt - pending.end_dt).total_seconds() / 60
            ),
            "expansion_after_return": "",
            "zone_revisit_count": "",
            "max_move_after_return": "",
            "direction_after_return": "",
            "return_price": round_float(pending.return_price),
            "return_row": to_int(pending.return_row_id),
            "return_timestamp": format_datetime(pending.return_dt),
            "revisit_duration_rows": pending.revisit_group_row_count,
            "revisit_expansion_delay_minutes": "",
        }
        merged_row = {
            **pending.snapshot_row,
            "peak_delta_zscore": pending.episode_row.get("peak_delta_zscore"),
            **immediate_return_context,
            # 4h-window outcome fields — empty, awaiting _finalize_pending_zone
            "failed_after_return": "",
            "expansion_type": "",
            "expansion_strength": "",
            "reversal_type": "",
            "reversal_strength": "",
        }

        result_row = _build_result_row(
            pending,
            immediate_return_context,
            {},
            {},
            event_timestamp,
            emit_status="PENDING_FINALIZATION",
        )
        _append_result_row(result_row)

        compute_live_rdm_for_case(
            pending,
            merged_row,
            build_zone_feature_window(pending),
            event_timestamp,
            emit_status="PENDING_FINALIZATION",
        )
    except Exception:
        return


def _advance_pending_zone(pending, market_dt, close_price, row_id, raw_row, feature_row):
    end_dt = pending.end_dt
    episode_window_end = end_dt + FOUR_HOURS

    # Bounded [end_dt, end_dt + 4h] accumulation — same inclusive bounds as
    # ResearchRowIndex.between(start_dt, end_dt, include_end=True), the window
    # find_reversal_event / find_expansion_event / calculate_window_extremes /
    # reversal_distances_by_horizon are all anchored to.
    if not pending.episode_window_complete:
        if end_dt <= market_dt <= episode_window_end:
            pending.episode_window_rows.append(raw_row)
        if market_dt > episode_window_end:
            pending.episode_window_complete = True

    # Unbounded return-point watch — the live mirror of detect_preparation_
    # return's `in_zone = future_rows[(close >= zone_low) & (close <= zone_high)]`
    # over `future_rows = rows.after_time(episode_end_dt)`. The chronologically
    # first in-zone row IS, by construction, the first row of
    # contiguous_row_groups(in_zone)[0] — so the first in-zone row encountered
    # here is exactly offline's return_row/return_dt/return_price.
    if not pending.return_found:
        if market_dt > end_dt and pending.zone_low <= close_price <= pending.zone_high:
            pending.return_found = True
            pending.return_dt = market_dt
            pending.return_price = close_price
            pending.return_row_id = row_id
            pending.revisit_group_active = True
            pending.revisit_group_row_count = 1
            pending.revisit_group_last_row_id = row_id
    elif pending.revisit_group_active:
        # Faithful streaming re-expression of contiguous_row_groups' grouping
        # rule (a group ends at the first non-contiguous row_id), bounded to
        # just the first group — all revisit_duration_rows ever needs.
        in_zone = pending.zone_low <= close_price <= pending.zone_high
        contiguous = (
            row_id is not None
            and pending.revisit_group_last_row_id is not None
            and row_id == pending.revisit_group_last_row_id + 1
        )
        if in_zone and contiguous:
            pending.revisit_group_row_count += 1
            pending.revisit_group_last_row_id = row_id
        else:
            pending.revisit_group_active = False

    # Bounded [return_dt, return_dt + 4h] accumulation — only begins once the
    # return point is known; identical inclusive bounds to
    # calculate_after_return_expansion's rows.between(return_dt, return_dt + 4h).
    if pending.return_found and not pending.return_window_complete:
        return_window_end = pending.return_dt + FOUR_HOURS
        if pending.return_dt <= market_dt <= return_window_end:
            pending.return_window_rows.append(raw_row)
        if market_dt > return_window_end:
            pending.return_window_complete = True

    # PHASE 4 (Live RDM) -- forward half of the per-zone row-feature window:
    # captures every row from registration through (and including) the return
    # point itself, completing the [preparation_start_row, return_row] span
    # whose preparation-period prefix _seed_feature_window_rows already
    # backfilled. Stops the instant return_found flips true on this very row
    # (the return row IS included -- live_row_window's `end` resolves to
    # return_row, and build_live_rdm_evolution's slice is end-inclusive via
    # searchsorted(..., side="right")), mirroring the same "accumulate the
    # exact bounded/resolved span, then compute" pattern this module already
    # uses for episode_window_rows / return_window_rows -- just anchored to
    # the unbounded return-point watch instead of a fixed 4h horizon, which
    # is the one genuinely unbounded operation this module's docstring already
    # documents and the user's "build new buffer" decision explicitly accepts.
    if not pending.feature_capture_complete:
        pending.feature_window_rows.append(feature_row)
        if pending.return_found:
            pending.feature_capture_complete = True

    # B12 (Live Validation Instrumentation) -- ADDITIVE, research-only.
    # Bounded [return_dt, return_dt + 4h] accumulation of FEATURE_WINDOW_FIELDS
    # rows -- the same inclusive bounds and same FOUR_HOURS anchor as
    # return_window_rows above, just carrying the richer feature_row instead
    # of raw_row. This is new, independent state: it does not read from or
    # write to feature_window_rows / return_window_rows / feature_capture_complete,
    # and does not change when/whether early-emit or finalization fire.
    if pending.return_found and not pending.post_return_capture_complete:
        post_return_window_end = pending.return_dt + FOUR_HOURS
        if pending.return_dt <= market_dt <= post_return_window_end:
            pending.post_return_feature_window_rows.append(feature_row)
        if market_dt > post_return_window_end:
            pending.post_return_capture_complete = True


def _finalize_pending_zone(pending, event_timestamp):
    """
    Fires when both 4h windows complete. Builds the full return/reversal/
    expansion context (all outcome fields now available), appends a
    FINALIZED_OUTCOME record to live_return_detection.csv, fires lifecycle
    events (which need full context), and appends the outcome-only state row
    via append_live_outcome_for_case. Does NOT re-run Group A/B/B8-B11 —
    those fields are already in the PENDING_FINALIZATION record emitted at
    return_found time by _early_emit_pending_zone.
    """
    try:
        return_context = _build_return_context(pending)
        reversal_context, expansion_split = _build_reversal_and_expansion_context(
            pending, return_context
        )

        merged_row = {
            **pending.snapshot_row,
            "peak_delta_zscore": pending.episode_row.get("peak_delta_zscore"),
            **return_context,
            **reversal_context,
            **expansion_split,
        }

        result_row = _build_result_row(
            pending, return_context, reversal_context, expansion_split, event_timestamp,
            emit_status="FINALIZED_OUTCOME",
        )
        _append_result_row(result_row)

        record_live_return_lifecycle_events(merged_row, pending.episode_row, event_timestamp)
        record_live_return_field_lifecycle_events(merged_row, pending.episode_row, event_timestamp)

        # Append FINALIZED_OUTCOME state row with outcome fields only.
        # Group A/B/B8-B11/Synthesis were already run at return_found time.
        append_live_outcome_for_case(pending, merged_row, event_timestamp)

        # B12 (Live Validation Instrumentation) -- ADDITIVE, research-only.
        # Reads the PENDING_FINALIZATION record + new post-return buffer;
        # writes its own file. Isolated try/except so a B12 failure can never
        # prevent the FINALIZED_OUTCOME row / lifecycle events above.
        try:
            append_live_b12_validation_for_case(pending, event_timestamp)
        except Exception:
            pass
    except Exception:
        return


def _build_return_context(pending):
    """
    Live equivalent of detect_preparation_return's return-value assembly: the
    return point itself comes from this module's streaming watch (faithfully
    reproducing offline's "first in-zone row after episode close"); the
    after-return expansion analysis is delegated VERBATIM to
    calculate_after_return_expansion against the accumulated, bounded
    [return_dt, return_dt + 4h] buffer — zero formula drift.
    """
    return_window_index = _build_row_index(pending.return_window_rows)
    expansion = calculate_after_return_expansion(
        rows=return_window_index,
        return_dt=pending.return_dt,
        return_price=pending.return_price,
    )
    max_move_after_return = expansion.get("max_move_after_return")
    expansion_after_return = (
        (to_float(max_move_after_return) or 0) >= RETURN_EXPANSION_SUCCESS_THRESHOLD
    )

    return {
        "return_to_preparation": True,
        "time_to_return_minutes": round_float(
            (pending.return_dt - pending.end_dt).total_seconds() / 60
        ),
        "expansion_after_return": expansion_after_return,
        "zone_revisit_count": "",
        "max_move_after_return": max_move_after_return,
        "direction_after_return": expansion.get("direction_after_return"),
        "return_price": round_float(pending.return_price),
        "return_row": to_int(pending.return_row_id),
        "return_timestamp": format_datetime(pending.return_dt),
        "revisit_duration_rows": pending.revisit_group_row_count,
        "revisit_expansion_delay_minutes": expansion.get("revisit_expansion_delay_minutes"),
    }


def _build_reversal_and_expansion_context(pending, return_context):
    """
    Delegates the entire bounded [end_dt, end_dt + 4h] reversal/expansion
    analysis VERBATIM to analyze_reversal_context / analyze_expansion_reversal_
    split (which themselves call find_reversal_event / find_expansion_event /
    reversal_distances_by_horizon / classify_reversal_type / classify_expansion_
    type / is_failed_after_return / is_reversal_after_return / reversal_strength
    / expansion_strength) — identical call shape to analyze_episode's, just
    fed a ResearchRowIndex over the accumulated live buffer instead of the
    full historical dataset. Zero formula/threshold drift.
    """
    episode_window_index = _build_row_index(pending.episode_window_rows)
    end_dt = pending.end_dt
    end_price = pending.end_price

    future_moves = {}
    for label in _REVERSAL_HORIZON_LABELS:
        future_price = nearest_close_at_or_after(episode_window_index, end_dt + HORIZONS[label])
        future_moves[f"move_{label}"] = subtract(future_price, end_price)

    extremes_4h = calculate_window_extremes(
        rows=episode_window_index,
        start_dt=end_dt,
        end_dt=end_dt + FOUR_HOURS,
        base_price=end_price,
        suffix="4h",
    )

    reversal_context = analyze_reversal_context(
        rows=episode_window_index,
        end_dt=end_dt,
        end_price=end_price,
        episode_direction=pending.episode_direction,
        future_moves=future_moves,
        extremes_4h=extremes_4h,
        return_context=return_context,
    )
    expansion_split = analyze_expansion_reversal_split(
        rows=episode_window_index,
        end_dt=end_dt,
        end_price=end_price,
        episode_direction=pending.episode_direction,
        reversal_context=reversal_context,
        extremes_4h=extremes_4h,
    )
    return reversal_context, expansion_split


def _build_result_row(
    pending, return_context, reversal_context, expansion_split, event_timestamp,
    emit_status="FINALIZED_OUTCOME",
):
    return {
        "zone_id": pending.zone_id,
        "episode_id": pending.episode_id,
        "emit_status": emit_status,
        "start_row_id": pending.episode_row.get("start_row_id"),
        "episode_end_timestamp_utc": pending.episode_row.get("episode_end_timestamp_utc"),
        "episode_direction_proxy": pending.episode_direction,
        "preparation_low_price": pending.snapshot_row.get("preparation_low_price"),
        "preparation_high_price": pending.snapshot_row.get("preparation_high_price"),
        "return_to_preparation": return_context.get("return_to_preparation"),
        "return_price": return_context.get("return_price"),
        "return_timestamp": return_context.get("return_timestamp"),
        "return_row": return_context.get("return_row"),
        "failed_after_return": reversal_context.get("failed_after_return", ""),
        "expansion_type": expansion_split.get("expansion_type", ""),
        "expansion_strength": expansion_split.get("expansion_strength", ""),
        "reversal_type": reversal_context.get("reversal_type", ""),
        "reversal_strength": reversal_context.get("reversal_strength", ""),
        "resolved_at_timestamp_utc": event_timestamp,
    }


def _build_row_index(raw_rows):
    frame = pd.DataFrame(raw_rows, columns=["market_timestamp", "close", "row_id"])
    prepared = prepare_rows(frame)
    return ResearchRowIndex(prepared)


def build_zone_feature_window(pending):
    """
    Assembles a finalized pending zone's captured per-zone row-feature window
    into the exact `historical_rows` shape build_live_rdm_evolution /
    attach_historical_delta_to_live_rows expect (a row_id-sorted, deduplicated
    DataFrame carrying FEATURE_WINDOW_FIELDS) -- the live equivalent of the
    `historical_rows` slice offline's build_live_rdm_evolution receives as the
    full historical_observation_rows.csv. PHASE 4 (Live RDM)'s wrapper module
    is the intended caller, at the same point _finalize_pending_zone already
    builds merged_row -- this is the per-zone "historical_rows" companion to
    that per-zone "completed case row".

    Deduplication is defensive only: registration seeds the buffer through
    (and including) the row at end_row_id, and forward capture begins on the
    NEXT processed row (process_live_return_detection_row runs return-
    detection for a row strictly before that same row's V2-episode-close path
    can register a new zone), so no overlap is expected in practice -- but
    keep_row_id="last" prefers the freshest capture, matching
    attach_historical_delta_to_live_rows' own drop_duplicates(keep="last").
    """
    if not pending.feature_window_rows:
        return pd.DataFrame(columns=FEATURE_WINDOW_FIELDS)

    frame = pd.DataFrame(pending.feature_window_rows, columns=FEATURE_WINDOW_FIELDS)
    frame["row_id_numeric"] = pd.to_numeric(frame["row_id"], errors="coerce")
    frame = frame.dropna(subset=["row_id_numeric"])
    frame = frame.sort_values("row_id_numeric").drop_duplicates("row_id_numeric", keep="last")
    return frame.drop(columns=["row_id_numeric"]).reset_index(drop=True)


def build_zone_post_return_feature_window(pending):
    """
    B12 (Live Validation Instrumentation) -- ADDITIVE, research-only.

    Assembles a finalized pending zone's captured POST-RETURN per-zone
    row-feature window (post_return_feature_window_rows, spanning
    [return_dt, return_dt + FOUR_HOURS]) into the same FEATURE_WINDOW_FIELDS
    shape build_zone_feature_window returns -- the "historical_rows" companion
    for computing an Active-Core-keyed live evolution stream over the
    post-return observation window. Mirrors build_zone_feature_window's
    dedup/sort logic exactly; reads only the new buffer, leaves
    feature_window_rows / build_zone_feature_window untouched.
    """
    if not pending.post_return_feature_window_rows:
        return pd.DataFrame(columns=FEATURE_WINDOW_FIELDS)

    frame = pd.DataFrame(pending.post_return_feature_window_rows, columns=FEATURE_WINDOW_FIELDS)
    frame["row_id_numeric"] = pd.to_numeric(frame["row_id"], errors="coerce")
    frame = frame.dropna(subset=["row_id_numeric"])
    frame = frame.sort_values("row_id_numeric").drop_duplicates("row_id_numeric", keep="last")
    return frame.drop(columns=["row_id_numeric"]).reset_index(drop=True)


def _field_value(source, key, default=None):
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _ensure_output_file():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not LIVE_RETURN_DETECTION_FILE.exists():
        with LIVE_RETURN_DETECTION_FILE.open(mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=LIVE_RETURN_DETECTION_FIELDNAMES)
            writer.writeheader()


def _append_result_row(result_row):
    _ensure_output_file()
    with LIVE_RETURN_DETECTION_FILE.open(mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=LIVE_RETURN_DETECTION_FIELDNAMES)
        writer.writerow(
            {field: result_row.get(field, "") for field in LIVE_RETURN_DETECTION_FIELDNAMES}
        )

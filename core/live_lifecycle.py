"""
LIVE Lifecycle integration (PHASE 3 / PHASE 3B of the LIVE integration roadmap).

Feeds live Preparation snapshots (frozen at V2 episode close — see
core.observation_logger / tools.analyze_phase1b_episode_research), live V2
episode closure events, and — as of PHASE 3B — live return-detection /
reversal-context results (core.live_return_detection) into the existing,
validated lifecycle memory layers (context_memory.ZoneLifecycleMemory /
FieldLifecycleMemory) — reused directly, unmodified, exactly as the offline
research pipeline (tools.analyze_phase1b_episode_research.build_lifecycle_
memories) uses them. No lifecycle formulas, states, identities, or
thresholds are changed here.

────────────────────────────────────────────────────────────────────────────
SCOPE — what is (and is not) live-computable without look-ahead
────────────────────────────────────────────────────────────────────────────
Implemented in PHASE 3, with zero look-ahead (fully computable the moment a
live V2 episode closes):

  - zone_created                 (mirrors add_zone_lifecycle_events's first
                                  event: a Preparation zone is born the
                                  instant the detector confirms it)
  - delta_zscore field event     (mirrors add_delta_field_events — uses
                                  peak_delta_zscore, known at episode close)
  - preparation_candidate field event (mirrors add_preparation_field_events —
                                  uses preparation_candidate/_strength, known
                                  at Preparation snapshot freeze)
  - active zone tracking, lifecycle_state, lifecycle_path (derived from the
    zone's own recorded event history — a presentational view over
    ZoneLifecycleMemory's existing event stream, not a new formula),
    current active zones

Implemented in PHASE 3B, once core.live_return_detection resolves a pending
zone's return_to_preparation (see that module's docstring for the streaming
"accept unbounded logical tracking" design that makes this possible without
look-ahead — a zone simply emits nothing until its return is genuinely
found):

  - zone_tested / zone_rejected / zone_reclaimed transitions (mirrors
    add_zone_lifecycle_events' three return-dependent branches verbatim —
    same trigger conditions, same zone_source/reaction_quality/research_notes
    families, same event_timestamp/row_index sourcing)
  - expansion_state / reversal_state / hypothesis02_state field events
    (mirrors add_expansion_field_events / add_reversal_field_events /
    add_hypothesis02_field_events verbatim — same lifecycle_state mapping
    tables, same field_strength sourcing, same is_direct_reversal /
    hypothesis02_state / zone_reaction_quality helper calls)

Deliberately NOT implemented (documented, not approximated):

  - zone_expired / zone_broken / field_expired: the offline wiring
    (add_zone_lifecycle_events / add_field_lifecycle_events) NEVER emits
    these states either — they exist only in ZoneLifecycleMemory's/
    FieldLifecycleMemory's generic state vocabulary, with no offline trigger
    to mirror. Inventing a live-only expiry rule would be a NEW formula not
    present in the validated pipeline, so none is added here.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from context_memory import FieldLifecycleMemory, ZoneLifecycleMemory
from tools.analyze_phase1b_episode_research import (
    is_direct_reversal,
    hypothesis02_state,
    to_float,
    truthy_value,
    value_or_unknown,
    zone_reaction_quality,
)

OUTPUT_DIR = Path("outputs")
LIVE_LIFECYCLE_EVENTS_FILE = OUTPUT_DIR / "live_lifecycle_events.jsonl"
LIVE_FIELD_LIFECYCLE_EVENTS_FILE = OUTPUT_DIR / "live_field_lifecycle_events.jsonl"
LIVE_LIFECYCLE_STATE_FILE = OUTPUT_DIR / "live_lifecycle_state.csv"

LIVE_LIFECYCLE_STATE_FIELDNAMES = [
    "zone_id",
    "zone_type",
    "zone_price",
    "zone_strength",
    "zone_source",
    "created_at",
    "last_seen_at",
    "test_count",
    "rejection_count",
    "break_count",
    "reclaim_count",
    "lifecycle_state",
    "lifecycle_age",
    "reaction_quality",
    "lifecycle_path",
    "related_episode_id",
    "research_notes",
]

_zone_memory = ZoneLifecycleMemory()
_field_memory = FieldLifecycleMemory()


def get_zone_memory():
    return _zone_memory


def get_field_memory():
    return _field_memory


def reset_live_lifecycle_memory():
    """Used only by validation harnesses to start a clean, isolated run."""
    _zone_memory.clear()
    _field_memory.clear()


def live_zone_id(episode_id):
    return f"LIVE_PREP_ZONE_{episode_id}"


def live_field_id(field_type, episode_id):
    return f"{field_type}_LIVE_{episode_id}"


def record_live_preparation_zone_created(snapshot_row, episode_row, event_timestamp):
    """
    Mirrors tools.analyze_phase1b_episode_research.add_zone_lifecycle_events'
    FIRST event exactly (zone_created — the only transition that requires no
    forward/return-detection data): same lifecycle_state, zone_type,
    zone_source family, reaction_quality starting value, and research_notes
    intent — adapted only in zone_id (live has no case_id; uses the live
    V2 episode_id instead) and zone_source (tagged "live_*" for traceability,
    not a formula change).
    """
    if not truthy_value(snapshot_row.get("preparation_candidate")):
        return None

    episode_id = episode_row.get("episode_id")
    zone_id = live_zone_id(episode_id)
    timestamp = episode_row.get("episode_start_timestamp_utc") or event_timestamp

    _zone_memory.add_zone_event(
        zone_id=zone_id,
        lifecycle_state="zone_created",
        zone_type="preparation",
        zone_price=snapshot_row.get("preparation_mid_price"),
        zone_strength=snapshot_row.get("preparation_strength"),
        zone_source="live_preparation_detector",
        reaction_quality="PENDING_RETURN_REACTION",
        research_notes=(
            "Preparation zone detected live by the validated Preparation "
            "detector at V2 episode close."
        ),
        event_timestamp=timestamp,
        lifecycle_age=snapshot_row.get("preparation_duration_rows"),
        related_episode_id=episode_id,
        row_index=episode_row.get("start_row_id"),
    )

    _append_zone_event()
    _write_lifecycle_state_snapshot()
    return zone_id


def record_live_return_lifecycle_events(merged_row, episode_row, event_timestamp):
    """
    Mirrors add_zone_lifecycle_events' three return-dependent branches
    VERBATIM (zone_tested / zone_rejected / zone_reclaimed) — same trigger
    conditions (return_to_preparation / failed_after_return /
    is_direct_reversal), same zone_source/reaction_quality/research_notes
    families (live_* tags only, not a formula change), same
    event_timestamp/row_index sourcing (return_timestamp/return_row, falling
    back to the zone's creation timestamp/row exactly as offline falls back
    to episode_start_time_utc/start_row_id).

    Called once, exactly when core.live_return_detection finalizes a pending
    zone (return_to_preparation has just resolved True) — merged_row carries
    the zone's frozen Preparation snapshot fields plus the freshly-computed
    return_context / reversal_context / expansion_split fields, the same
    "single merged research row" shape add_zone_lifecycle_events consumes
    offline.
    """
    if not truthy_value(merged_row.get("preparation_candidate")):
        return

    episode_id = episode_row.get("episode_id")
    row_index = episode_row.get("start_row_id")
    creation_timestamp = episode_row.get("episode_start_timestamp_utc") or event_timestamp
    zone_id = live_zone_id(episode_id)

    if not truthy_value(merged_row.get("return_to_preparation")):
        return

    _zone_memory.add_zone_event(
        zone_id=zone_id,
        lifecycle_state="zone_tested",
        zone_type="preparation",
        zone_price=merged_row.get("return_price") or merged_row.get("preparation_mid_price"),
        zone_strength=merged_row.get("preparation_strength"),
        zone_source="live_return_detection",
        reaction_quality=zone_reaction_quality(merged_row),
        research_notes="Preparation zone revisited live after V2 episode close.",
        event_timestamp=merged_row.get("return_timestamp") or creation_timestamp,
        lifecycle_age=merged_row.get("preparation_duration_rows"),
        related_episode_id=episode_id,
        row_index=merged_row.get("return_row") or row_index,
    )
    _append_zone_event()

    if truthy_value(merged_row.get("failed_after_return")):
        _zone_memory.add_zone_event(
            zone_id=zone_id,
            lifecycle_state="zone_rejected",
            zone_type="preparation",
            zone_price=merged_row.get("return_price") or merged_row.get("preparation_mid_price"),
            zone_strength=merged_row.get("preparation_strength"),
            zone_source="live_failed_return",
            reaction_quality="FAILED_RETURN_REVERSAL",
            research_notes="Live return to preparation failed and reversal context appeared.",
            event_timestamp=merged_row.get("return_timestamp") or creation_timestamp,
            lifecycle_age=merged_row.get("preparation_duration_rows"),
            related_episode_id=episode_id,
            row_index=merged_row.get("return_row") or row_index,
        )
        _append_zone_event()
    elif not is_direct_reversal(merged_row):
        _zone_memory.add_zone_event(
            zone_id=zone_id,
            lifecycle_state="zone_reclaimed",
            zone_type="preparation",
            zone_price=merged_row.get("return_price") or merged_row.get("preparation_mid_price"),
            zone_strength=merged_row.get("preparation_strength"),
            zone_source="live_successful_return",
            reaction_quality="RETURN_EXPANSION_OBSERVED",
            research_notes="Live return to preparation produced non-failed reaction.",
            event_timestamp=merged_row.get("return_timestamp") or creation_timestamp,
            lifecycle_age=merged_row.get("preparation_duration_rows"),
            related_episode_id=episode_id,
            row_index=merged_row.get("return_row") or row_index,
        )
        _append_zone_event()

    _write_lifecycle_state_snapshot()


def record_live_field_lifecycle_events(snapshot_row, episode_row, event_timestamp):
    """
    Mirrors the two add_field_lifecycle_events sub-routines that depend ONLY
    on data available at V2 episode close / Preparation freeze
    (add_delta_field_events, add_preparation_field_events) — same
    thresholds, same state/strength mapping, same field_type vocabulary.
    The remaining three (expansion/reversal/hypothesis02) require the same
    forward return-detection chain documented in this module's docstring and
    are intentionally deferred to a future sub-phase.
    """
    episode_id = episode_row.get("episode_id")
    row_index = episode_row.get("start_row_id")
    timestamp = episode_row.get("episode_start_timestamp_utc") or event_timestamp
    related_zone_id = live_zone_id(episode_id)

    _record_delta_field_event(episode_row, episode_id, row_index, timestamp, related_zone_id)
    _record_preparation_field_event(snapshot_row, episode_id, row_index, timestamp, related_zone_id)


def _record_delta_field_event(episode_row, episode_id, row_index, timestamp, related_zone_id):
    delta_value = to_float(episode_row.get("peak_delta_zscore"))
    if delta_value is None:
        return

    state = "field_active"
    strength = "LOW"
    if abs(delta_value) >= 3:
        state = "field_strengthening"
        strength = "EXTREME"
    elif abs(delta_value) >= 2.75:
        state = "field_strengthening"
        strength = "HIGH"
    elif abs(delta_value) >= 2:
        strength = "MEDIUM"

    _field_memory.add_field_event(
        field_id=live_field_id("delta_zscore", episode_id),
        field_type="delta_zscore",
        lifecycle_state=state,
        field_value=delta_value,
        field_strength=strength,
        related_episode_id=episode_id,
        related_zone_id=related_zone_id,
        row_index=row_index,
        event_timestamp=timestamp,
        research_notes="Peak delta zscore captured live for lifecycle context at V2 episode close.",
    )
    _append_field_event()


def _record_preparation_field_event(snapshot_row, episode_id, row_index, timestamp, related_zone_id):
    if not truthy_value(snapshot_row.get("preparation_candidate")):
        return

    strength = value_or_unknown(snapshot_row.get("preparation_strength"))
    state = "field_strengthening" if strength in {"HIGH", "EXTREME"} else "field_active"

    _field_memory.add_field_event(
        field_id=live_field_id("preparation_candidate", episode_id),
        field_type="preparation_candidate",
        lifecycle_state=state,
        field_value=True,
        field_strength=strength,
        related_episode_id=episode_id,
        related_zone_id=related_zone_id,
        row_index=row_index,
        event_timestamp=timestamp,
        research_notes="Preparation candidate captured live by the validated Preparation detector.",
    )
    _append_field_event()


def record_live_return_field_lifecycle_events(merged_row, episode_row, event_timestamp):
    """
    Mirrors add_expansion_field_events / add_reversal_field_events /
    add_hypothesis02_field_events VERBATIM — same lifecycle_state mapping
    tables, same field_value/field_strength sourcing, same field_type
    vocabulary, same is_direct_reversal/hypothesis02_state helper calls.

    Called once, alongside record_live_return_lifecycle_events, exactly when
    core.live_return_detection finalizes a pending zone — merged_row carries
    the same merged Preparation + return/reversal/expansion field shape
    add_field_lifecycle_events consumes offline.
    """
    episode_id = episode_row.get("episode_id")
    related_zone_id = live_zone_id(episode_id)
    creation_timestamp = episode_row.get("episode_start_timestamp_utc") or event_timestamp
    row_index = episode_row.get("start_row_id")

    _record_expansion_field_event(merged_row, episode_id, row_index, creation_timestamp, related_zone_id)
    _record_reversal_field_event(merged_row, episode_id, row_index, creation_timestamp, related_zone_id)
    _record_hypothesis02_field_event(merged_row, episode_id, row_index, creation_timestamp, related_zone_id)


def _record_expansion_field_event(row, episode_id, row_index, event_timestamp, related_zone_id):
    expansion_type = str(row.get("expansion_type") or "")
    if not expansion_type:
        return

    if expansion_type == "PURE_EXPANSION":
        state = "field_strengthening"
    elif expansion_type == "EXPANSION_THEN_REVERSAL":
        state = "field_weakening"
    elif expansion_type in {"FAILED_EXPANSION", "DIRECT_REVERSAL", "NO_EXPANSION"}:
        state = "field_exhausted"
    else:
        state = "field_active"

    _field_memory.add_field_event(
        field_id=live_field_id("expansion_state", episode_id),
        field_type="expansion_state",
        lifecycle_state=state,
        field_value=expansion_type,
        field_strength=row.get("expansion_strength"),
        related_episode_id=episode_id,
        related_zone_id=related_zone_id,
        row_index=row_index,
        event_timestamp=event_timestamp,
        research_notes="Expansion state captured live for lifecycle context after return detection.",
    )
    _append_field_event()


def _record_reversal_field_event(row, episode_id, row_index, event_timestamp, related_zone_id):
    reversal_type = str(row.get("reversal_type") or "")
    if not reversal_type:
        return

    if reversal_type in {"DIRECT_REVERSAL", "FAILED_RETURN_REVERSAL"}:
        state = "field_strengthening"
    elif reversal_type == "NO_REVERSAL":
        state = "field_inactive"
    else:
        state = "field_active"

    _field_memory.add_field_event(
        field_id=live_field_id("reversal_state", episode_id),
        field_type="reversal_state",
        lifecycle_state=state,
        field_value=reversal_type,
        field_strength=row.get("reversal_strength"),
        related_episode_id=episode_id,
        related_zone_id=related_zone_id,
        row_index=row_index,
        event_timestamp=event_timestamp,
        research_notes="Reversal state captured live for lifecycle context after return detection.",
    )
    _append_field_event()


def _record_hypothesis02_field_event(row, episode_id, row_index, event_timestamp, related_zone_id):
    state_value = hypothesis02_state(row)
    if state_value == "NO_RESEARCH_CONTEXT":
        lifecycle_state = "field_inactive"
    elif state_value == "RETURN_EXPANSION_OBSERVED":
        lifecycle_state = "field_recovered"
    elif state_value == "RETURN_FAILURE":
        lifecycle_state = "field_exhausted"
    else:
        lifecycle_state = "field_active"

    _field_memory.add_field_event(
        field_id=live_field_id("hypothesis02_state", episode_id),
        field_type="hypothesis02_state",
        lifecycle_state=lifecycle_state,
        field_value=state_value,
        field_strength=row.get("expansion_strength") or row.get("reversal_strength"),
        related_episode_id=episode_id,
        related_zone_id=related_zone_id,
        row_index=row.get("return_row") or row_index,
        event_timestamp=row.get("return_timestamp") or event_timestamp,
        research_notes="HYPOTHESIS_02 return/revisit state captured live for lifecycle context.",
    )
    _append_field_event()


def _last_zone_event():
    events = _zone_memory.get_recent_zone_events(limit=1)
    return events[-1] if events else None


def _append_zone_event():
    event = _last_zone_event()
    if event is not None:
        _append_jsonl(LIVE_LIFECYCLE_EVENTS_FILE, event)


def _append_field_event():
    events = _field_memory.get_recent_field_events(limit=1)
    if events:
        _append_jsonl(LIVE_FIELD_LIFECYCLE_EVENTS_FILE, events[-1])


def _append_jsonl(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open(mode="a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=True, sort_keys=True))
        file.write("\n")


def _zone_event_history(zone_id):
    normalized_zone_id = str(zone_id)
    return [
        event
        for event in _zone_memory.get_recent_zone_events(limit=_zone_memory.max_events)
        if str(event.get("zone_id")) == normalized_zone_id
    ]


def lifecycle_path_for_zone(zone_id):
    """
    Chronological sequence of lifecycle states a zone has traversed, derived
    purely from ZoneLifecycleMemory's own recorded event history (a
    presentational view over existing data — " -> " join convention already
    used elsewhere in this codebase, e.g. research/zone_mechanics_calculator.py).
    Not a new formula: no thresholds, no classification — just the recorded
    event_state sequence for this zone_id, in order.
    """
    states = [event.get("event_state") for event in _zone_event_history(zone_id) if event.get("event_state")]
    return " -> ".join(states)


def _related_episode_id_for_zone(zone_id):
    """
    ZoneLifecycleMemory.add_zone_event does not carry related_episode_id on
    the zone record itself (only on each event — same behavior offline's
    add_zone_lifecycle_events relies on). Reading it back from the zone's own
    most recent event is a presentational lookup over existing tracked data,
    not a new field/formula.
    """
    history = _zone_event_history(zone_id)
    for event in reversed(history):
        related_episode_id = event.get("related_episode_id")
        if related_episode_id not in (None, ""):
            return related_episode_id
    return ""


def _write_lifecycle_state_snapshot():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for zone_id, zone in sorted(_zone_memory._zones.items()):
        record = dict(zone)
        record["lifecycle_path"] = lifecycle_path_for_zone(zone_id)
        record["related_episode_id"] = _related_episode_id_for_zone(zone_id)
        rows.append({field: record.get(field, "") for field in LIVE_LIFECYCLE_STATE_FIELDNAMES})

    with LIVE_LIFECYCLE_STATE_FILE.open(mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=LIVE_LIFECYCLE_STATE_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def get_active_zone_records():
    """Current active zones, each enriched with its derived lifecycle_path / related_episode_id."""
    active = []
    for zone in _zone_memory.get_active_zones():
        zone_id = zone.get("zone_id")
        record = dict(zone)
        record["lifecycle_path"] = lifecycle_path_for_zone(zone_id)
        record["related_episode_id"] = _related_episode_id_for_zone(zone_id)
        active.append(record)
    return active

"""Phase 1B+ market context memory.

This module is intentionally standalone. The 50k context layer is for
observation, replay context, research, and baseline history only.

Hard rule:
50k memory MUST NOT be used for every live calculation or live signal scan.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional


MARKET_CONTEXT_MEMORY_SIZE = 50_000
LIVE_MEMORY_TARGET_SIZE = 5_000

CONTEXT_FIELDS = [
    "price_context",
    "volume_context",
    "delta_context",
    "velocity_context",
    "distribution_context",
    "zone_context",
    "preparation_context",
    "expansion_context",
    "reversal_context",
    "research_context",
]

ZONE_LIFECYCLE_STATES = [
    "zone_created",
    "zone_active",
    "zone_tested",
    "zone_rejected",
    "zone_broken",
    "zone_reclaimed",
    "zone_expired",
]

ZONE_LIFECYCLE_FIELDS = [
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
    "research_notes",
]

FIELD_LIFECYCLE_STATES = [
    "field_inactive",
    "field_active",
    "field_strengthening",
    "field_weakening",
    "field_exhausted",
    "field_recovered",
    "field_expired",
]

FIELD_LIFECYCLE_TYPES = [
    "price_zscore",
    "volume_zscore",
    "delta_zscore",
    "velocity_zscore",
    "distribution_shift",
    "volatility_regime",
    "tail_event",
    "preparation_candidate",
    "expansion_state",
    "reversal_state",
    "hypothesis02_state",
]

FIELD_LIFECYCLE_FIELDS = [
    "field_id",
    "field_type",
    "field_value",
    "field_strength",
    "lifecycle_state",
    "created_at",
    "last_seen_at",
    "activation_count",
    "strengthening_count",
    "weakening_count",
    "exhaustion_count",
    "recovery_count",
    "expiration_count",
    "related_zone_id",
    "related_episode_id",
    "research_notes",
]

IDENTITY_FIELDS = [
    "timestamp_utc",
    "market_timestamp",
    "row_id",
    "source",
]


@dataclass(frozen=True)
class MemoryStats:
    """Lightweight statistics for the context memory buffer."""

    total_records: int
    max_records: int
    live_memory_target: int
    context_fields: List[str]
    oldest_timestamp_utc: Optional[str]
    latest_timestamp_utc: Optional[str]
    persistence_path: Optional[str]
    context_only: bool = True
    feeds_live_scans: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "total_records": self.total_records,
            "max_records": self.max_records,
            "live_memory_target": self.live_memory_target,
            "context_fields": list(self.context_fields),
            "oldest_timestamp_utc": self.oldest_timestamp_utc,
            "latest_timestamp_utc": self.latest_timestamp_utc,
            "persistence_path": self.persistence_path,
            "context_only": self.context_only,
            "feeds_live_scans": self.feeds_live_scans,
        }


@dataclass(frozen=True)
class ZoneLifecycleRecord:
    """Scalar zone lifecycle record for context-only observation."""

    zone_id: Any
    zone_type: Any = None
    zone_price: Any = None
    zone_strength: Any = None
    zone_source: Any = None
    created_at: Any = None
    last_seen_at: Any = None
    test_count: int = 0
    rejection_count: int = 0
    break_count: int = 0
    reclaim_count: int = 0
    lifecycle_state: str = "zone_created"
    lifecycle_age: Any = None
    reaction_quality: Any = None
    research_notes: Any = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "zone_id": _scalarize(self.zone_id),
            "zone_type": _scalarize(self.zone_type),
            "zone_price": _scalarize(self.zone_price),
            "zone_strength": _scalarize(self.zone_strength),
            "zone_source": _scalarize(self.zone_source),
            "created_at": _scalarize(self.created_at),
            "last_seen_at": _scalarize(self.last_seen_at),
            "test_count": _safe_int(self.test_count),
            "rejection_count": _safe_int(self.rejection_count),
            "break_count": _safe_int(self.break_count),
            "reclaim_count": _safe_int(self.reclaim_count),
            "lifecycle_state": _normalize_zone_state(self.lifecycle_state),
            "lifecycle_age": _scalarize(self.lifecycle_age),
            "reaction_quality": _scalarize(self.reaction_quality),
            "research_notes": _scalarize(self.research_notes),
        }


@dataclass(frozen=True)
class ZoneLifecycleStats:
    """Lightweight stats for zone lifecycle context memory."""

    total_zones: int
    active_zones: int
    total_events: int
    state_counts: Dict[str, int]
    max_events: int
    persistence_path: Optional[str]
    context_only: bool = True
    feeds_live_scans: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "total_zones": self.total_zones,
            "active_zones": self.active_zones,
            "total_events": self.total_events,
            "state_counts": dict(self.state_counts),
            "max_events": self.max_events,
            "persistence_path": self.persistence_path,
            "context_only": self.context_only,
            "feeds_live_scans": self.feeds_live_scans,
        }


@dataclass(frozen=True)
class FieldLifecycleRecord:
    """Scalar field lifecycle record for context-only observation."""

    field_id: Any
    field_type: Any
    field_value: Any = None
    field_strength: Any = None
    lifecycle_state: str = "field_active"
    created_at: Any = None
    last_seen_at: Any = None
    activation_count: int = 0
    strengthening_count: int = 0
    weakening_count: int = 0
    exhaustion_count: int = 0
    recovery_count: int = 0
    expiration_count: int = 0
    related_zone_id: Any = None
    related_episode_id: Any = None
    research_notes: Any = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "field_id": _scalarize(self.field_id),
            "field_type": _normalize_field_type(self.field_type),
            "field_value": _scalarize(self.field_value),
            "field_strength": _scalarize(self.field_strength),
            "lifecycle_state": _normalize_field_state(self.lifecycle_state),
            "created_at": _scalarize(self.created_at),
            "last_seen_at": _scalarize(self.last_seen_at),
            "activation_count": _safe_int(self.activation_count),
            "strengthening_count": _safe_int(self.strengthening_count),
            "weakening_count": _safe_int(self.weakening_count),
            "exhaustion_count": _safe_int(self.exhaustion_count),
            "recovery_count": _safe_int(self.recovery_count),
            "expiration_count": _safe_int(self.expiration_count),
            "related_zone_id": _scalarize(self.related_zone_id),
            "related_episode_id": _scalarize(self.related_episode_id),
            "research_notes": _scalarize(self.research_notes),
        }


@dataclass(frozen=True)
class FieldLifecycleStats:
    """Lightweight stats for field lifecycle context memory."""

    total_fields: int
    active_fields: int
    total_events: int
    state_counts: Dict[str, int]
    type_counts: Dict[str, int]
    max_events: int
    persistence_path: Optional[str]
    context_only: bool = True
    feeds_live_scans: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "total_fields": self.total_fields,
            "active_fields": self.active_fields,
            "total_events": self.total_events,
            "state_counts": dict(self.state_counts),
            "type_counts": dict(self.type_counts),
            "max_events": self.max_events,
            "persistence_path": self.persistence_path,
            "context_only": self.context_only,
            "feeds_live_scans": self.feeds_live_scans,
        }


class MarketContextMemory:
    """50k context memory layer for observation and research.

    The class stores normalized scalar records in a bounded deque. It does not
    perform live calculations, emit signals, or mutate engine rows.
    """

    def __init__(
        self,
        max_records: int = MARKET_CONTEXT_MEMORY_SIZE,
        live_memory_target: int = LIVE_MEMORY_TARGET_SIZE,
        persistence_path: Optional[str] = None,
    ) -> None:
        if max_records <= 0:
            raise ValueError("max_records must be greater than zero")
        if live_memory_target <= 0:
            raise ValueError("live_memory_target must be greater than zero")

        self.max_records = int(max_records)
        self.live_memory_target = int(live_memory_target)
        self.persistence_path = str(persistence_path) if persistence_path else None
        self._buffer: Deque[Dict[str, Any]] = deque(maxlen=self.max_records)

    def add_context(self, row: Dict[str, Any], source: Optional[str] = None) -> Dict[str, Any]:
        """Add one context row and return the normalized stored record."""

        record = self._normalize_record(row, source=source)
        self._buffer.append(record)
        return dict(record)

    def append(self, row: Dict[str, Any], source: Optional[str] = None) -> Dict[str, Any]:
        """Alias for add_context for archive-style callers."""

        return self.add_context(row, source=source)

    def latest(self) -> Optional[Dict[str, Any]]:
        if not self._buffer:
            return None
        return dict(self._buffer[-1])

    def snapshot(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        records = list(self._buffer)
        if limit is not None:
            records = records[-max(int(limit), 0) :]
        return [dict(record) for record in records]

    def get_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.snapshot(limit=limit)

    def get_context(self, field_name: str, limit: Optional[int] = None) -> List[Any]:
        if field_name not in CONTEXT_FIELDS and field_name not in IDENTITY_FIELDS:
            raise KeyError(f"Unknown context field: {field_name}")
        return [record.get(field_name) for record in self.snapshot(limit=limit)]

    def stats(self) -> MemoryStats:
        oldest = self._buffer[0].get("timestamp_utc") if self._buffer else None
        latest = self._buffer[-1].get("timestamp_utc") if self._buffer else None
        return MemoryStats(
            total_records=len(self._buffer),
            max_records=self.max_records,
            live_memory_target=self.live_memory_target,
            context_fields=list(CONTEXT_FIELDS),
            oldest_timestamp_utc=oldest,
            latest_timestamp_utc=latest,
            persistence_path=self.persistence_path,
        )

    def clear(self) -> None:
        self._buffer.clear()

    def save_jsonl(self, path: Optional[str] = None) -> Path:
        target = self._resolve_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            for record in self._buffer:
                handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True))
                handle.write("\n")
        return target

    def load_jsonl(self, path: Optional[str] = None, replace: bool = True) -> int:
        target = self._resolve_path(path)
        if not target.exists():
            return 0

        loaded = 0
        if replace:
            self.clear()

        with target.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                raw_record = json.loads(line)
                self._buffer.append(self._normalize_record(raw_record))
                loaded += 1

        return loaded

    def persist(self, path: Optional[str] = None) -> Path:
        return self.save_jsonl(path=path)

    def restore(self, path: Optional[str] = None, replace: bool = True) -> int:
        return self.load_jsonl(path=path, replace=replace)

    def _resolve_path(self, path: Optional[str]) -> Path:
        selected = path or self.persistence_path
        if not selected:
            raise ValueError("A persistence path is required")
        return Path(selected)

    def _normalize_record(
        self,
        row: Dict[str, Any],
        source: Optional[str] = None,
    ) -> Dict[str, Any]:
        if row is None:
            row = {}

        timestamp_utc = row.get("timestamp_utc") or _utc_now()
        record: Dict[str, Any] = {
            "timestamp_utc": _scalarize(timestamp_utc),
            "market_timestamp": _scalarize(row.get("market_timestamp")),
            "row_id": _scalarize(row.get("row_id")),
            "source": _scalarize(source if source is not None else row.get("source")),
        }

        for field_name in CONTEXT_FIELDS:
            record[field_name] = _scalarize(row.get(field_name))

        return record


class ZoneLifecycleMemory:
    """Context-only zone lifecycle memory.

    This layer tracks research and replay context for zones. It does not scan
    live rows, score trades, or feed execution logic.
    """

    def __init__(
        self,
        max_events: int = MARKET_CONTEXT_MEMORY_SIZE,
        persistence_path: Optional[str] = None,
    ) -> None:
        if max_events <= 0:
            raise ValueError("max_events must be greater than zero")

        self.max_events = int(max_events)
        self.persistence_path = str(persistence_path) if persistence_path else None
        self._events: Deque[Dict[str, Any]] = deque(maxlen=self.max_events)
        self._zones: Dict[str, Dict[str, Any]] = {}

    def add_zone_event(
        self,
        zone_id: Any,
        lifecycle_state: str,
        zone_type: Any = None,
        zone_price: Any = None,
        zone_strength: Any = None,
        zone_source: Any = None,
        reaction_quality: Any = None,
        research_notes: Any = None,
        event_timestamp: Optional[Any] = None,
        lifecycle_age: Any = None,
        related_case_id: Any = None,
        related_episode_id: Any = None,
        row_index: Any = None,
    ) -> Dict[str, Any]:
        """Add a zone lifecycle event and return the current zone record."""

        if zone_id is None:
            raise ValueError("zone_id is required")

        normalized_zone_id = str(_scalarize(zone_id))
        normalized_state = _normalize_zone_state(lifecycle_state)
        now = _scalarize(event_timestamp or _utc_now())
        existing = self._zones.get(normalized_zone_id)

        if existing is None:
            existing = ZoneLifecycleRecord(
                zone_id=normalized_zone_id,
                zone_type=zone_type,
                zone_price=zone_price,
                zone_strength=zone_strength,
                zone_source=zone_source,
                created_at=now,
                last_seen_at=now,
                lifecycle_state=normalized_state,
                lifecycle_age=lifecycle_age,
                reaction_quality=reaction_quality,
                research_notes=research_notes,
            ).as_dict()
        else:
            existing = dict(existing)
            existing["last_seen_at"] = now
            existing["lifecycle_state"] = normalized_state
            existing["lifecycle_age"] = _scalarize(lifecycle_age)

            if zone_type is not None:
                existing["zone_type"] = _scalarize(zone_type)
            if zone_price is not None:
                existing["zone_price"] = _scalarize(zone_price)
            if zone_strength is not None:
                existing["zone_strength"] = _scalarize(zone_strength)
            if zone_source is not None:
                existing["zone_source"] = _scalarize(zone_source)
            if reaction_quality is not None:
                existing["reaction_quality"] = _scalarize(reaction_quality)
            if research_notes is not None:
                existing["research_notes"] = _scalarize(research_notes)

        self._increment_lifecycle_counts(existing, normalized_state)
        self._zones[normalized_zone_id] = existing

        event = dict(existing)
        event["event_timestamp_utc"] = now
        event["event_state"] = normalized_state
        event["related_case_id"] = _scalarize(related_case_id)
        event["related_episode_id"] = _scalarize(related_episode_id)
        event["row_index"] = _scalarize(row_index)
        self._events.append(event)

        return dict(existing)

    def get_zone(self, zone_id: Any) -> Optional[Dict[str, Any]]:
        normalized_zone_id = str(_scalarize(zone_id))
        zone = self._zones.get(normalized_zone_id)
        if zone is None:
            return None
        return dict(zone)

    def get_active_zones(self) -> List[Dict[str, Any]]:
        active_states = {"zone_created", "zone_active", "zone_tested", "zone_reclaimed"}
        return [
            dict(zone)
            for zone in self._zones.values()
            if zone.get("lifecycle_state") in active_states
        ]

    def get_recent_zone_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        events = list(self._events)[-max(int(limit), 0) :]
        return [dict(event) for event in events]

    def get_zone_stats(self) -> ZoneLifecycleStats:
        state_counts = {state: 0 for state in ZONE_LIFECYCLE_STATES}
        for zone in self._zones.values():
            state = zone.get("lifecycle_state")
            if state not in state_counts:
                state_counts[state] = 0
            state_counts[state] += 1

        return ZoneLifecycleStats(
            total_zones=len(self._zones),
            active_zones=len(self.get_active_zones()),
            total_events=len(self._events),
            state_counts=state_counts,
            max_events=self.max_events,
            persistence_path=self.persistence_path,
        )

    def clear(self) -> None:
        self._events.clear()
        self._zones.clear()

    def persist(self, path: Optional[str] = None) -> Path:
        target = self._resolve_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "zone_lifecycle_memory_version": 1,
            "zones": list(self._zones.values()),
            "events": list(self._events),
        }
        with target.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True, sort_keys=True))
            handle.write("\n")
        return target

    def restore(self, path: Optional[str] = None, replace: bool = True) -> int:
        target = self._resolve_path(path)
        if not target.exists():
            return 0

        if replace:
            self.clear()

        restored_events = 0
        with target.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                zones = payload.get("zones", [])
                events = payload.get("events", [])

                for zone in zones:
                    normalized = self._normalize_zone_record(zone)
                    self._zones[str(normalized["zone_id"])] = normalized

                for event in events:
                    self._events.append(self._normalize_zone_event(event))
                    restored_events += 1

        return restored_events

    def _resolve_path(self, path: Optional[str]) -> Path:
        selected = path or self.persistence_path
        if not selected:
            raise ValueError("A persistence path is required")
        return Path(selected)

    def _normalize_zone_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {
            field_name: _scalarize(record.get(field_name))
            for field_name in ZONE_LIFECYCLE_FIELDS
        }
        normalized["zone_id"] = str(normalized.get("zone_id"))
        normalized["lifecycle_state"] = _normalize_zone_state(
            normalized.get("lifecycle_state")
        )
        normalized["test_count"] = _safe_int(normalized.get("test_count"))
        normalized["rejection_count"] = _safe_int(normalized.get("rejection_count"))
        normalized["break_count"] = _safe_int(normalized.get("break_count"))
        normalized["reclaim_count"] = _safe_int(normalized.get("reclaim_count"))
        return normalized

    def _normalize_zone_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_zone_record(event)
        normalized["event_timestamp_utc"] = _scalarize(
            event.get("event_timestamp_utc") or event.get("last_seen_at") or _utc_now()
        )
        normalized["event_state"] = _normalize_zone_state(
            event.get("event_state") or event.get("lifecycle_state")
        )
        normalized["related_case_id"] = _scalarize(event.get("related_case_id"))
        normalized["related_episode_id"] = _scalarize(event.get("related_episode_id"))
        normalized["row_index"] = _scalarize(event.get("row_index"))
        return normalized

    def _increment_lifecycle_counts(
        self,
        zone_record: Dict[str, Any],
        lifecycle_state: str,
    ) -> None:
        if lifecycle_state == "zone_tested":
            zone_record["test_count"] = _safe_int(zone_record.get("test_count")) + 1
        elif lifecycle_state == "zone_rejected":
            zone_record["rejection_count"] = (
                _safe_int(zone_record.get("rejection_count")) + 1
            )
        elif lifecycle_state == "zone_broken":
            zone_record["break_count"] = _safe_int(zone_record.get("break_count")) + 1
        elif lifecycle_state == "zone_reclaimed":
            zone_record["reclaim_count"] = (
                _safe_int(zone_record.get("reclaim_count")) + 1
            )


class FieldLifecycleMemory:
    """Context-only lifecycle memory for statistical and research fields.

    This memory layer is observational. It tracks field context over time but
    never changes Dashboard V2 scoring, live scans, or execution behavior.
    """

    def __init__(
        self,
        max_events: int = MARKET_CONTEXT_MEMORY_SIZE,
        persistence_path: Optional[str] = None,
    ) -> None:
        if max_events <= 0:
            raise ValueError("max_events must be greater than zero")

        self.max_events = int(max_events)
        self.persistence_path = str(persistence_path) if persistence_path else None
        self._events: Deque[Dict[str, Any]] = deque(maxlen=self.max_events)
        self._fields: Dict[str, Dict[str, Any]] = {}

    def add_field_event(
        self,
        field_id: Any,
        field_type: str,
        lifecycle_state: str,
        field_value: Any = None,
        field_strength: Any = None,
        related_zone_id: Any = None,
        related_episode_id: Any = None,
        research_notes: Any = None,
        event_timestamp: Optional[Any] = None,
        related_case_id: Any = None,
        row_index: Any = None,
    ) -> Dict[str, Any]:
        """Add a field lifecycle event and return the current field record."""

        if field_id is None:
            raise ValueError("field_id is required")

        normalized_field_id = str(_scalarize(field_id))
        normalized_type = _normalize_field_type(field_type)
        normalized_state = _normalize_field_state(lifecycle_state)
        now = _scalarize(event_timestamp or _utc_now())
        existing = self._fields.get(normalized_field_id)

        if existing is None:
            existing = FieldLifecycleRecord(
                field_id=normalized_field_id,
                field_type=normalized_type,
                field_value=field_value,
                field_strength=field_strength,
                lifecycle_state=normalized_state,
                created_at=now,
                last_seen_at=now,
                related_zone_id=related_zone_id,
                related_episode_id=related_episode_id,
                research_notes=research_notes,
            ).as_dict()
        else:
            existing = dict(existing)
            existing["field_type"] = normalized_type
            existing["last_seen_at"] = now
            existing["lifecycle_state"] = normalized_state

            if field_value is not None:
                existing["field_value"] = _scalarize(field_value)
            if field_strength is not None:
                existing["field_strength"] = _scalarize(field_strength)
            if related_zone_id is not None:
                existing["related_zone_id"] = _scalarize(related_zone_id)
            if related_episode_id is not None:
                existing["related_episode_id"] = _scalarize(related_episode_id)
            if research_notes is not None:
                existing["research_notes"] = _scalarize(research_notes)

        self._increment_lifecycle_counts(existing, normalized_state)
        self._fields[normalized_field_id] = existing

        event = dict(existing)
        event["event_timestamp_utc"] = now
        event["event_state"] = normalized_state
        event["related_case_id"] = _scalarize(related_case_id)
        event["row_index"] = _scalarize(row_index)
        self._events.append(event)

        return dict(existing)

    def get_field(self, field_id: Any) -> Optional[Dict[str, Any]]:
        normalized_field_id = str(_scalarize(field_id))
        field = self._fields.get(normalized_field_id)
        if field is None:
            return None
        return dict(field)

    def get_active_fields(self) -> List[Dict[str, Any]]:
        active_states = {"field_active", "field_strengthening", "field_weakening", "field_recovered"}
        return [
            dict(field)
            for field in self._fields.values()
            if field.get("lifecycle_state") in active_states
        ]

    def get_recent_field_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        events = list(self._events)[-max(int(limit), 0) :]
        return [dict(event) for event in events]

    def get_field_stats(self) -> FieldLifecycleStats:
        state_counts = {state: 0 for state in FIELD_LIFECYCLE_STATES}
        type_counts = {field_type: 0 for field_type in FIELD_LIFECYCLE_TYPES}

        for field in self._fields.values():
            state = field.get("lifecycle_state")
            field_type = field.get("field_type")

            if state not in state_counts:
                state_counts[state] = 0
            state_counts[state] += 1

            if field_type not in type_counts:
                type_counts[field_type] = 0
            type_counts[field_type] += 1

        return FieldLifecycleStats(
            total_fields=len(self._fields),
            active_fields=len(self.get_active_fields()),
            total_events=len(self._events),
            state_counts=state_counts,
            type_counts=type_counts,
            max_events=self.max_events,
            persistence_path=self.persistence_path,
        )

    def clear(self) -> None:
        self._events.clear()
        self._fields.clear()

    def persist(self, path: Optional[str] = None) -> Path:
        target = self._resolve_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "field_lifecycle_memory_version": 1,
            "fields": list(self._fields.values()),
            "events": list(self._events),
        }
        with target.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True, sort_keys=True))
            handle.write("\n")
        return target

    def restore(self, path: Optional[str] = None, replace: bool = True) -> int:
        target = self._resolve_path(path)
        if not target.exists():
            return 0

        if replace:
            self.clear()

        restored_events = 0
        with target.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                fields = payload.get("fields", [])
                events = payload.get("events", [])

                for field in fields:
                    normalized = self._normalize_field_record(field)
                    self._fields[str(normalized["field_id"])] = normalized

                for event in events:
                    self._events.append(self._normalize_field_event(event))
                    restored_events += 1

        return restored_events

    def _resolve_path(self, path: Optional[str]) -> Path:
        selected = path or self.persistence_path
        if not selected:
            raise ValueError("A persistence path is required")
        return Path(selected)

    def _normalize_field_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {
            field_name: _scalarize(record.get(field_name))
            for field_name in FIELD_LIFECYCLE_FIELDS
        }
        normalized["field_id"] = str(normalized.get("field_id"))
        normalized["field_type"] = _normalize_field_type(normalized.get("field_type"))
        normalized["lifecycle_state"] = _normalize_field_state(
            normalized.get("lifecycle_state")
        )
        normalized["activation_count"] = _safe_int(normalized.get("activation_count"))
        normalized["strengthening_count"] = _safe_int(
            normalized.get("strengthening_count")
        )
        normalized["weakening_count"] = _safe_int(normalized.get("weakening_count"))
        normalized["exhaustion_count"] = _safe_int(normalized.get("exhaustion_count"))
        normalized["recovery_count"] = _safe_int(normalized.get("recovery_count"))
        normalized["expiration_count"] = _safe_int(normalized.get("expiration_count"))
        return normalized

    def _normalize_field_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_field_record(event)
        normalized["event_timestamp_utc"] = _scalarize(
            event.get("event_timestamp_utc") or event.get("last_seen_at") or _utc_now()
        )
        normalized["event_state"] = _normalize_field_state(
            event.get("event_state") or event.get("lifecycle_state")
        )
        normalized["related_case_id"] = _scalarize(event.get("related_case_id"))
        normalized["row_index"] = _scalarize(event.get("row_index"))
        return normalized

    def _increment_lifecycle_counts(
        self,
        field_record: Dict[str, Any],
        lifecycle_state: str,
    ) -> None:
        if lifecycle_state == "field_active":
            field_record["activation_count"] = (
                _safe_int(field_record.get("activation_count")) + 1
            )
        elif lifecycle_state == "field_strengthening":
            field_record["strengthening_count"] = (
                _safe_int(field_record.get("strengthening_count")) + 1
            )
        elif lifecycle_state == "field_weakening":
            field_record["weakening_count"] = (
                _safe_int(field_record.get("weakening_count")) + 1
            )
        elif lifecycle_state == "field_exhausted":
            field_record["exhaustion_count"] = (
                _safe_int(field_record.get("exhaustion_count")) + 1
            )
        elif lifecycle_state == "field_recovered":
            field_record["recovery_count"] = (
                _safe_int(field_record.get("recovery_count")) + 1
            )
        elif lifecycle_state == "field_expired":
            field_record["expiration_count"] = (
                _safe_int(field_record.get("expiration_count")) + 1
            )


def create_context_memory(
    max_records: int = MARKET_CONTEXT_MEMORY_SIZE,
    persistence_path: Optional[str] = None,
) -> MarketContextMemory:
    return MarketContextMemory(max_records=max_records, persistence_path=persistence_path)


def create_zone_lifecycle_memory(
    max_events: int = MARKET_CONTEXT_MEMORY_SIZE,
    persistence_path: Optional[str] = None,
) -> ZoneLifecycleMemory:
    return ZoneLifecycleMemory(max_events=max_events, persistence_path=persistence_path)


def create_field_lifecycle_memory(
    max_events: int = MARKET_CONTEXT_MEMORY_SIZE,
    persistence_path: Optional[str] = None,
) -> FieldLifecycleMemory:
    return FieldLifecycleMemory(max_events=max_events, persistence_path=persistence_path)


def build_context_record(
    *,
    price_context: Any = None,
    volume_context: Any = None,
    delta_context: Any = None,
    velocity_context: Any = None,
    distribution_context: Any = None,
    zone_context: Any = None,
    preparation_context: Any = None,
    expansion_context: Any = None,
    reversal_context: Any = None,
    research_context: Any = None,
    row_id: Any = None,
    market_timestamp: Any = None,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "timestamp_utc": _utc_now(),
        "market_timestamp": market_timestamp,
        "row_id": row_id,
        "source": source,
        "price_context": price_context,
        "volume_context": volume_context,
        "delta_context": delta_context,
        "velocity_context": velocity_context,
        "distribution_context": distribution_context,
        "zone_context": zone_context,
        "preparation_context": preparation_context,
        "expansion_context": expansion_context,
        "reversal_context": reversal_context,
        "research_context": research_context,
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _scalarize(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple, set)):
        return "|".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    return str(value)


def _normalize_zone_state(value: Any) -> str:
    state = str(value or "zone_active")
    if state not in ZONE_LIFECYCLE_STATES:
        raise ValueError(f"Unknown zone lifecycle state: {state}")
    return state


def _normalize_field_state(value: Any) -> str:
    state = str(value or "field_active")
    if state not in FIELD_LIFECYCLE_STATES:
        raise ValueError(f"Unknown field lifecycle state: {state}")
    return state


def _normalize_field_type(value: Any) -> str:
    field_type = str(value or "")
    if field_type not in FIELD_LIFECYCLE_TYPES:
        raise ValueError(f"Unknown field lifecycle type: {field_type}")
    return field_type


def _safe_int(value: Any) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "CONTEXT_FIELDS",
    "FIELD_LIFECYCLE_FIELDS",
    "FIELD_LIFECYCLE_STATES",
    "FIELD_LIFECYCLE_TYPES",
    "IDENTITY_FIELDS",
    "LIVE_MEMORY_TARGET_SIZE",
    "MARKET_CONTEXT_MEMORY_SIZE",
    "ZONE_LIFECYCLE_FIELDS",
    "ZONE_LIFECYCLE_STATES",
    "FieldLifecycleMemory",
    "FieldLifecycleRecord",
    "FieldLifecycleStats",
    "MarketContextMemory",
    "MemoryStats",
    "ZoneLifecycleMemory",
    "ZoneLifecycleRecord",
    "ZoneLifecycleStats",
    "build_context_record",
    "create_context_memory",
    "create_field_lifecycle_memory",
    "create_zone_lifecycle_memory",
]

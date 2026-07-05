"""Immutable abstract syntax tree contracts for scenario grammar programs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any

from .dimensions import BehavioralDimension
from .events import MechanicalEvent


GRAMMAR_SCHEMA_VERSION = "1"


class PhraseType(str, Enum):
    HOLD = "HOLD"
    RAMP = "RAMP"
    OSCILLATE = "OSCILLATE"
    APPROACH_ZONE = "APPROACH_ZONE"
    ENTER_ZONE = "ENTER_ZONE"
    PENETRATE = "PENETRATE"
    WITHDRAW = "WITHDRAW"
    HOLD_OUTSIDE = "HOLD_OUTSIDE"
    RECOVERY_GAP = "RECOVERY_GAP"
    BREAK_CANDIDATE = "BREAK_CANDIDATE"
    ACCEPTED_BREAK = "ACCEPTED_BREAK"
    RETEST_BOUNDARY = "RETEST_BOUNDARY"
    RECLAIM = "RECLAIM"
    COMPRESS = "COMPRESS"
    EXPAND = "EXPAND"
    TRANSFER_TO_ZONE = "TRANSFER_TO_ZONE"


def _freeze_canonical(value: Any, path: str) -> Any:
    if value is None or isinstance(value, (bool, int, str, Decimal, Enum)):
        return value
    if isinstance(value, tuple):
        return tuple(
            _freeze_canonical(item, f"{path}[{index}]")
            for index, item in enumerate(value)
        )
    raise TypeError(
        f"{path} contains unsupported mutable or non-canonical type: "
        f"{type(value).__name__}"
    )


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        normalized = value.normalize()
        text = "0" if normalized == 0 else format(normalized, "f")
        return {"type": "decimal", "value": text}
    if isinstance(value, Enum):
        return {
            "type": type(value).__name__,
            "value": value.value,
        }
    if isinstance(value, tuple):
        return [_canonical_value(item) for item in value]
    if isinstance(value, GrammarParameter):
        return {
            "name": value.name,
            "value": _canonical_value(value.value),
        }
    if isinstance(value, GrammarPhrase):
        return {
            "phrase_type": _canonical_value(value.phrase_type),
            "params": _canonical_value(value.params),
            "row_budget": value.row_budget,
            "target_zone": value.target_zone,
            "description": value.description,
        }
    return value


def _fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        {key: _canonical_value(payload[key]) for key in sorted(payload)},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


@dataclass(frozen=True)
class GrammarParameter:
    name: str
    value: Any

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("parameter name must not be empty")
        object.__setattr__(
            self,
            "value",
            _freeze_canonical(self.value, f"parameter.{self.name}"),
        )


@dataclass(frozen=True)
class GrammarPhrase:
    phrase_type: PhraseType
    params: tuple[GrammarParameter, ...]
    row_budget: int
    target_zone: str | None
    description: str

    def __post_init__(self) -> None:
        if not isinstance(self.phrase_type, PhraseType):
            raise TypeError("phrase_type must be PhraseType")
        if not isinstance(self.params, tuple):
            raise TypeError("params must be an immutable tuple")
        if not all(isinstance(param, GrammarParameter) for param in self.params):
            raise TypeError("params must contain GrammarParameter values")
        names = [param.name for param in self.params]
        if len(names) != len(set(names)):
            raise ValueError("phrase parameter names must be unique")
        if self.row_budget <= 0:
            raise ValueError("row_budget must be positive")
        if self.target_zone is not None and not self.target_zone.strip():
            raise ValueError("target_zone must not be blank")
        if not self.description.strip():
            raise ValueError("description must not be empty")
        object.__setattr__(
            self, "params", tuple(sorted(self.params, key=lambda item: item.name))
        )


@dataclass(frozen=True)
class GrammarProgram:
    program_id: str
    schema_version: str
    phrases: tuple[GrammarPhrase, ...]
    dimensions_declared: tuple[BehavioralDimension, ...]
    intended_events: tuple[MechanicalEvent, ...]
    notes: tuple[str, ...]
    program_fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.program_id.strip():
            raise ValueError("program_id must not be empty")
        if self.schema_version != GRAMMAR_SCHEMA_VERSION:
            raise ValueError("unsupported grammar schema version")
        if not isinstance(self.phrases, tuple) or not self.phrases:
            raise TypeError("phrases must be a non-empty immutable tuple")
        if not all(isinstance(phrase, GrammarPhrase) for phrase in self.phrases):
            raise TypeError("phrases must contain GrammarPhrase values")
        if not isinstance(self.dimensions_declared, tuple):
            raise TypeError("dimensions_declared must be an immutable tuple")
        if not all(
            isinstance(dimension, BehavioralDimension)
            for dimension in self.dimensions_declared
        ):
            raise TypeError("invalid behavioral dimension")
        if not isinstance(self.intended_events, tuple):
            raise TypeError("intended_events must be an immutable tuple")
        if not all(
            isinstance(event, MechanicalEvent)
            for event in self.intended_events
        ):
            raise TypeError("invalid intended event")
        if not isinstance(self.notes, tuple) or not all(
            isinstance(note, str) for note in self.notes
        ):
            raise TypeError("notes must be an immutable tuple of strings")

        dimensions = tuple(
            sorted(set(self.dimensions_declared), key=lambda item: item.value)
        )
        events = tuple(
            sorted(set(self.intended_events), key=lambda item: item.value)
        )
        object.__setattr__(self, "dimensions_declared", dimensions)
        object.__setattr__(self, "intended_events", events)
        object.__setattr__(
            self,
            "program_fingerprint",
            _fingerprint(
                {
                    "program_id": self.program_id,
                    "schema_version": self.schema_version,
                    "phrases": self.phrases,
                    "dimensions_declared": dimensions,
                    "intended_events": events,
                    "notes": self.notes,
                }
            ),
        )

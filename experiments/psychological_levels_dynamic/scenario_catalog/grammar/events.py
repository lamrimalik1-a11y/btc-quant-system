"""Mechanical event vocabulary for scenario authoring only.

These names describe intended synthetic price-path structures. They do not
claim that Stage 1-6 recognizes the events, and they carry no state labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


EVENT_SCHEMA_VERSION = "1"
GEOMETRY_NOTATION = (
    "Zone=[L,U]; width=W; direction=s; crossed boundary=B. "
    "Definitions use geometry-relative distance and row residence only."
)


class MechanicalEvent(str, Enum):
    BREAK_CANDIDATE = "BREAK_CANDIDATE"
    ACCEPTED_BREAK = "ACCEPTED_BREAK"
    FAILED_BREAK = "FAILED_BREAK"
    RETEST = "RETEST"
    FAILED_RETEST = "FAILED_RETEST"
    RECLAIM = "RECLAIM"
    ACCEPTANCE = "ACCEPTANCE"
    TRANSFER_TO_ZONE = "TRANSFER_TO_ZONE"
    ACCUMULATION = "ACCUMULATION"
    COMPRESSION = "COMPRESSION"
    EXPANSION = "EXPANSION"


@dataclass(frozen=True)
class MechanicalEventDefinition:
    event: MechanicalEvent
    schema_version: str
    definition: str
    required_components: tuple[str, ...]
    authoring_only: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != EVENT_SCHEMA_VERSION:
            raise ValueError("unsupported event schema version")
        if not self.definition.strip() or not self.required_components:
            raise ValueError("event definition must be complete")
        if not self.authoring_only:
            raise ValueError("version 1 events must remain authoring-only")


EVENT_DEFINITIONS = (
    MechanicalEventDefinition(
        MechanicalEvent.BREAK_CANDIDATE,
        EVENT_SCHEMA_VERSION,
        "Boundary crossing followed by clearance beyond boundary B.",
        ("boundary_crossing", "boundary_clearance"),
    ),
    MechanicalEventDefinition(
        MechanicalEvent.ACCEPTED_BREAK,
        EVENT_SCHEMA_VERSION,
        "Break candidate followed by the complete outside-residence contract.",
        ("break_candidate", "outside_residence"),
    ),
    MechanicalEventDefinition(
        MechanicalEvent.FAILED_BREAK,
        EVENT_SCHEMA_VERSION,
        "Break candidate returning through its entry side before acceptance.",
        ("break_candidate", "return_before_acceptance"),
    ),
    MechanicalEventDefinition(
        MechanicalEvent.RETEST,
        EVENT_SCHEMA_VERSION,
        "After accepted break, return from the far side into a retest envelope.",
        ("accepted_break", "retest_delay", "retest_envelope"),
    ),
    MechanicalEventDefinition(
        MechanicalEvent.FAILED_RETEST,
        EVENT_SCHEMA_VERSION,
        "Retest returning to the far side without completing reclaim.",
        ("retest", "far_side_return"),
    ),
    MechanicalEventDefinition(
        MechanicalEvent.RECLAIM,
        EVENT_SCHEMA_VERSION,
        "Cross back into the prior side and hold the reclaim residence.",
        ("boundary_crossing", "reclaim_depth", "reclaim_residence"),
    ),
    MechanicalEventDefinition(
        MechanicalEvent.ACCEPTANCE,
        EVENT_SCHEMA_VERSION,
        "Sustained outside residence at the declared boundary clearance.",
        ("boundary_clearance", "acceptance_duration"),
    ),
    MechanicalEventDefinition(
        MechanicalEvent.TRANSFER_TO_ZONE,
        EVENT_SCHEMA_VERSION,
        "Leave zone A and begin a distinct interaction with zone B.",
        ("source_zone", "target_zone", "distinct_interaction"),
    ),
    MechanicalEventDefinition(
        MechanicalEvent.ACCUMULATION,
        EVENT_SCHEMA_VERSION,
        "Bounded low-amplitude oscillation for a declared residence.",
        ("oscillation_amplitude", "oscillation_period", "residence"),
    ),
    MechanicalEventDefinition(
        MechanicalEvent.COMPRESSION,
        EVENT_SCHEMA_VERSION,
        "Oscillation amplitude decreases according to an immutable schedule.",
        ("compression_schedule",),
    ),
    MechanicalEventDefinition(
        MechanicalEvent.EXPANSION,
        EVENT_SCHEMA_VERSION,
        "Amplitude or departure distance increases by an immutable schedule.",
        ("expansion_schedule",),
    ),
)

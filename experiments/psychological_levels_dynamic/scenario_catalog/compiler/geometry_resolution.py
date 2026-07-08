"""Immutable geometry-resolution contracts; no resolution behavior.

Future geometry resolution consumes ExpansionResult + SchedulingResult +
GeometryContext. This is intentional: TimelineSegment owns row scheduling
metadata, while ExpandedInstruction preserves PrimitiveInstruction.parameters.
The future resolver must pair timeline.segments[i] with
expansion_result.expanded_instructions[i] after validating that
scheduling_result.expansion_fingerprint == expansion_result.expansion_fingerprint.

Units contract: depth, clearance, and distance are Decimal fractions of a
GeometryReference.half_width. No floats and no absolute deltas are accepted
except explicit geometry anchors.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from ..grammar.ast import GrammarParameter
from .diagnostics import CompilerDiagnostic
from .expansion import ExpandedInstruction
from .geometry import GeometryReference
from .primitives import PrimitiveType
from .timeline import TimelineSegment


GEOMETRY_RESOLVER_CONTRACT_VERSION = "GEOMETRY_RESOLUTION_CONTRACTS_V1"

GEOMETRY_RESOLUTION_DIAGNOSTIC_CODES = (
    "UPSTREAM_SCHEDULING_FAILED",
    "EXPANSION_SCHEDULING_FINGERPRINT_MISMATCH",
    "UNKNOWN_ZONE_ID",
    "MISSING_TARGET_ZONE",
    "MISSING_SOURCE_ZONE",
    "MISSING_SIDE",
    "MISSING_DEPTH",
    "MISSING_CLEARANCE",
    "INVALID_DISTANCE",
    "INVALID_DECIMAL_FRACTION",
    "UNSUPPORTED_PRIMITIVE_PARAMETER",
)


@dataclass(frozen=True)
class GeometryResolutionRole:
    """Placeholder contract for future primitive + macro-origin role rules."""

    primitive_type: PrimitiveType
    macro_origin: str | None
    required_parameters: tuple[str, ...]
    optional_parameters: tuple[str, ...] = ()
    requires_target_zone: bool = False
    requires_source_zone: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.primitive_type, PrimitiveType):
            raise TypeError("primitive_type must be PrimitiveType")
        if self.macro_origin is not None and not self.macro_origin.strip():
            raise ValueError("macro_origin must not be blank")
        if not isinstance(self.required_parameters, tuple) or not all(
            isinstance(value, str) and value.strip()
            for value in self.required_parameters
        ):
            raise TypeError("required_parameters must be non-empty strings")
        if not isinstance(self.optional_parameters, tuple) or not all(
            isinstance(value, str) and value.strip()
            for value in self.optional_parameters
        ):
            raise TypeError("optional_parameters must be strings")

    @property
    def role_key(self) -> tuple[PrimitiveType, str | None]:
        return (self.primitive_type, self.macro_origin)


@dataclass(frozen=True)
class ResolvedCoordinate:
    """Geometry anchor intent, not a materialized row value."""

    coordinate_type: str
    absolute_price: Decimal
    zone_id: str | None
    side: str | None
    offset_from_boundary: Decimal | None
    offset_from_center: Decimal | None

    def __post_init__(self) -> None:
        if not self.coordinate_type.strip():
            raise ValueError("coordinate_type must not be empty")
        if not isinstance(self.absolute_price, Decimal):
            raise TypeError("absolute_price must be Decimal")
        if self.zone_id is not None and not self.zone_id.strip():
            raise ValueError("zone_id must not be blank")
        if self.side is not None and not self.side.strip():
            raise ValueError("side must not be blank")
        for value in (self.offset_from_boundary, self.offset_from_center):
            if value is not None and not isinstance(value, Decimal):
                raise TypeError("offsets must be Decimal or None")


@dataclass(frozen=True)
class ResolvedSegment:
    timeline_segment: TimelineSegment
    expanded_instruction: ExpandedInstruction
    resolved_target_zone: GeometryReference | None
    resolved_source_zone: GeometryReference | None
    start_coordinate_intent: ResolvedCoordinate | None
    end_coordinate_intent: ResolvedCoordinate | None
    resolved_parameters: tuple[GrammarParameter, ...]
    source_parameters: tuple[GrammarParameter, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.timeline_segment, TimelineSegment):
            raise TypeError("timeline_segment must be TimelineSegment")
        if not isinstance(self.expanded_instruction, ExpandedInstruction):
            raise TypeError("expanded_instruction must be ExpandedInstruction")
        for value in (self.resolved_target_zone, self.resolved_source_zone):
            if value is not None and not isinstance(value, GeometryReference):
                raise TypeError("resolved zones must be GeometryReference or None")
        for value in (self.start_coordinate_intent, self.end_coordinate_intent):
            if value is not None and not isinstance(value, ResolvedCoordinate):
                raise TypeError("coordinate intents must be ResolvedCoordinate or None")
        for field_name in ("resolved_parameters", "source_parameters"):
            values = getattr(self, field_name)
            if not isinstance(values, tuple) or not all(
                isinstance(item, GrammarParameter) for item in values
            ):
                raise TypeError(f"{field_name} must be an immutable GrammarParameter tuple")


@dataclass(frozen=True)
class ResolvedTimeline:
    segments: tuple[ResolvedSegment, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.segments, tuple) or not all(
            isinstance(value, ResolvedSegment) for value in self.segments
        ):
            raise TypeError("segments must be an immutable ResolvedSegment tuple")
        if tuple(
            value.timeline_segment.segment_index for value in self.segments
        ) != tuple(range(len(self.segments))):
            raise ValueError("segments must preserve timeline segment order")


@dataclass(frozen=True)
class GeometryResolutionResult:
    success: bool
    resolved_timeline: ResolvedTimeline | None
    diagnostics: tuple[CompilerDiagnostic, ...]
    grammar_fingerprint: str
    expansion_fingerprint: str
    timeline_fingerprint: str
    geometry_fingerprint: str
    compiler_version: str
    resolver_version: str
    resolution_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")
        if self.success and self.resolved_timeline is None:
            raise ValueError("successful resolution must produce a resolved_timeline")
        if not self.success and self.resolved_timeline is not None:
            raise ValueError("failed resolution must not produce a resolved_timeline")
        if self.resolved_timeline is not None and not isinstance(
            self.resolved_timeline, ResolvedTimeline
        ):
            raise TypeError("resolved_timeline must be ResolvedTimeline or None")
        if not isinstance(self.diagnostics, tuple) or not all(
            isinstance(value, CompilerDiagnostic) for value in self.diagnostics
        ):
            raise TypeError("diagnostics must be an immutable CompilerDiagnostic tuple")
        for field_name in (
            "grammar_fingerprint",
            "expansion_fingerprint",
            "timeline_fingerprint",
            "geometry_fingerprint",
            "resolution_fingerprint",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.startswith("sha256:"):
                raise ValueError(f"{field_name} must be SHA-256")
        if not self.compiler_version.strip():
            raise ValueError("compiler_version must not be empty")
        if not self.resolver_version.strip():
            raise ValueError("resolver_version must not be empty")


def _decimal_text(value: Decimal) -> str:
    normalized = value.normalize()
    return "0" if normalized == 0 else format(normalized, "f")


def _canonical(value: Any) -> Any:
    if isinstance(value, Decimal):
        return {"type": "decimal", "value": _decimal_text(value)}
    if isinstance(value, Enum):
        return {"type": type(value).__name__, "value": value.value}
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    if isinstance(value, GrammarParameter):
        return {"name": value.name, "value": _canonical(value.value)}
    if isinstance(value, GeometryReference):
        return value.canonical_value()
    if isinstance(value, CompilerDiagnostic):
        return {
            "code": value.code,
            "severity": _canonical(value.severity),
            "message": value.message,
            "phrase_index": value.phrase_index,
            "parameter_name": value.parameter_name,
        }
    if isinstance(value, TimelineSegment):
        return {
            "segment_index": value.segment_index,
            "source_phrase_index": value.source_phrase_index,
            "primitive_type": _canonical(value.primitive_type),
            "row_start": value.row_start,
            "row_end": value.row_end,
            "row_count": value.row_count,
            "target_zone": value.target_zone,
            "macro_origin": value.macro_origin,
            "interpolation_policy": _canonical(value.interpolation_policy),
        }
    if isinstance(value, ExpandedInstruction):
        return {
            "instruction": _canonical(value.instruction),
            "row_budget": value.row_budget,
        }
    if hasattr(value, "__dataclass_fields__"):
        return {
            field_name: _canonical(getattr(value, field_name))
            for field_name in value.__dataclass_fields__
        }
    raise TypeError(f"unsupported canonical type: {type(value).__name__}")


def geometry_resolution_fingerprint(
    resolved_timeline: ResolvedTimeline | None,
    diagnostics: tuple[CompilerDiagnostic, ...],
    grammar_fingerprint: str,
    expansion_fingerprint: str,
    timeline_fingerprint: str,
    geometry_fingerprint: str,
    compiler_version: str,
    resolver_version: str,
) -> str:
    """Deterministic fingerprint helper for contract tests and future resolver.

    Future resolver logic should compute resolution_fingerprint from canonical
    content and provenance only. No timestamps or runtime state belong here.
    """

    payload = {
        "resolved_timeline": _canonical(resolved_timeline),
        "diagnostics": _canonical(tuple(sorted(diagnostics, key=lambda item: item.deterministic_key))),
        "grammar_fingerprint": grammar_fingerprint,
        "expansion_fingerprint": expansion_fingerprint,
        "timeline_fingerprint": timeline_fingerprint,
        "geometry_fingerprint": geometry_fingerprint,
        "compiler_version": compiler_version,
        "resolver_version": resolver_version,
    }
    canonical_json = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return "sha256:" + hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

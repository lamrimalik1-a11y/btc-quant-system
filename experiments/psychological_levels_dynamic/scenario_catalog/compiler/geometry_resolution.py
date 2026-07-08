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

# ---------------------------------------------------------------------------
# Geometry resolution logic. Contracts above remain unchanged.
# ---------------------------------------------------------------------------
from ..grammar.dimensions import Direction, RelativePosition, ZoneSide
from .expansion import ExpansionResult
from .geometry import GeometryContext
from .timeline_scheduler import SchedulingResult
from .diagnostics import DiagnosticSeverity

GEOMETRY_RESOLVER_VERSION = "GEOMETRY_RESOLVER_LOGIC_V1"
GEOMETRY_RESOLUTION_DIAGNOSTIC_CODES = tuple(dict.fromkeys(GEOMETRY_RESOLUTION_DIAGNOSTIC_CODES + (
    "UPSTREAM_EXPANSION_FAILED", "TIMELINE_EXPANSION_LENGTH_MISMATCH",
    "SEGMENT_INSTRUCTION_INDEX_MISMATCH", "INVALID_GEOMETRY_REFERENCE",
    "INVALID_SIDE", "INVALID_TRANSFER_DIRECTION",
    "PRIMITIVE_MACRO_ROLE_UNSUPPORTED", "UNSUPPORTED_PARAMETER_COMBINATION",
)))
_DISTANCE_PARAMETER_NAMES = frozenset({"amplitude", "clearance", "depth", "distance", "start_distance", "travel_distance", "withdrawal_distance"})

def _rr(primitive_type, macro_origin, required=(), optional=(), target=False, source=False):
    return GeometryResolutionRole(primitive_type, macro_origin, required, optional, target, source)

GEOMETRY_RESOLUTION_ROLES = (
    _rr(PrimitiveType.HOLD, None, ("position",), ("distance",), True),
    _rr(PrimitiveType.RAMP, None, ("distance", "direction"), ("smoothness",), True),
    _rr(PrimitiveType.OSCILLATE, None, ("amplitude", "period_rows"), (), True),
    _rr(PrimitiveType.APPROACH, None, ("side", "start_distance"), (), True),
    _rr(PrimitiveType.ENTER, None, ("side", "depth"), (), True),
    _rr(PrimitiveType.PENETRATE, None, ("depth",), ("side",), True),
    _rr(PrimitiveType.WITHDRAW, None, ("side", "distance"), (), True),
    _rr(PrimitiveType.HOLD_OUTSIDE, None, ("side", "clearance"), (), True),
    _rr(PrimitiveType.RECOVERY_GAP, None, ("withdrawal_distance",), ("side",), True),
    _rr(PrimitiveType.APPROACH, "ACCEPTED_BREAK", ("side", "clearance"), (), True),
    _rr(PrimitiveType.ENTER, "ACCEPTED_BREAK", ("side", "clearance"), (), True),
    _rr(PrimitiveType.PENETRATE, "ACCEPTED_BREAK", ("clearance",), ("side",), True),
    _rr(PrimitiveType.WITHDRAW, "ACCEPTED_BREAK", ("side", "clearance"), (), True),
    _rr(PrimitiveType.HOLD_OUTSIDE, "ACCEPTED_BREAK", ("side", "clearance"), ("acceptance_rows",), True),
    _rr(PrimitiveType.APPROACH, "RECLAIM", ("side", "depth"), (), True),
    _rr(PrimitiveType.ENTER, "RECLAIM", ("side", "depth"), (), True),
    _rr(PrimitiveType.PENETRATE, "RECLAIM", ("depth",), ("side",), True),
    _rr(PrimitiveType.HOLD, "RECLAIM", ("depth",), ("side", "residence_rows"), True),
    _rr(PrimitiveType.WITHDRAW, "TRANSFER_TO_ZONE", ("source_zone", "travel_distance"), (), True, True),
    _rr(PrimitiveType.RAMP, "TRANSFER_TO_ZONE", ("source_zone", "travel_distance"), (), True, True),
    _rr(PrimitiveType.APPROACH, "TRANSFER_TO_ZONE", ("source_zone", "travel_distance"), (), True, True),
    _rr(PrimitiveType.OSCILLATE, "COMPRESS", ("amplitude",), ("period_rows",), True),
    _rr(PrimitiveType.OSCILLATE, "EXPAND", ("amplitude",), ("period_rows",), True),
)
_ROLE_BY_KEY = {role.role_key: role for role in GEOMETRY_RESOLUTION_ROLES}
if len(_ROLE_BY_KEY) != len(GEOMETRY_RESOLUTION_ROLES):
    raise ValueError("duplicate geometry resolution role keys")

def _fatal(code, message, phrase_index=None, parameter_name=None):
    return CompilerDiagnostic(code, DiagnosticSeverity.FATAL, message, phrase_index, parameter_name)

def _resolution_result(success, resolved_timeline, diagnostics, expansion_result, scheduling_result, geometry_context, resolver_version):
    sorted_diagnostics = tuple(sorted(diagnostics, key=lambda item: item.deterministic_key))
    fingerprint = geometry_resolution_fingerprint(
        resolved_timeline, sorted_diagnostics, expansion_result.grammar_fingerprint,
        expansion_result.expansion_fingerprint, scheduling_result.timeline_fingerprint,
        geometry_context.geometry_fingerprint, expansion_result.compiler_version, resolver_version,
    )
    return GeometryResolutionResult(
        success=success,
        resolved_timeline=resolved_timeline,
        diagnostics=sorted_diagnostics,
        grammar_fingerprint=expansion_result.grammar_fingerprint,
        expansion_fingerprint=expansion_result.expansion_fingerprint,
        timeline_fingerprint=scheduling_result.timeline_fingerprint,
        geometry_fingerprint=geometry_context.geometry_fingerprint,
        compiler_version=expansion_result.compiler_version,
        resolver_version=resolver_version,
        resolution_fingerprint=fingerprint,
    )

def _params(parameters):
    return {param.name: param.value for param in parameters}

def _missing_code(name):
    if name == "side":
        return "MISSING_SIDE"
    if name == "depth":
        return "MISSING_DEPTH"
    if name == "clearance":
        return "MISSING_CLEARANCE"
    if name in _DISTANCE_PARAMETER_NAMES:
        return "INVALID_DISTANCE"
    return "UNSUPPORTED_PARAMETER_COMBINATION"

def _valid_fraction(value):
    return isinstance(value, Decimal) and value >= 0

def _side(value):
    if isinstance(value, ZoneSide):
        return value
    if isinstance(value, str):
        try:
            return ZoneSide(value)
        except ValueError:
            return None
    return None

def _direction(value):
    if isinstance(value, Direction):
        return value
    if isinstance(value, str):
        try:
            return Direction(value)
        except ValueError:
            return None
    return None

def _boundary(zone, side):
    return zone.upper_price if side == ZoneSide.UPPER else zone.lower_price

def _signed(side, amount):
    return amount if side == ZoneSide.UPPER else -amount

def _scaled(zone, fraction):
    return fraction * zone.half_width

def _coord(kind, zone, price, side=None):
    return ResolvedCoordinate(
        coordinate_type=kind,
        absolute_price=price,
        zone_id=zone.zone_id,
        side=None if side is None else side.value,
        offset_from_boundary=None if side is None else price - _boundary(zone, side),
        offset_from_center=price - zone.center_price,
    )

def _resolved_params(values):
    return tuple(GrammarParameter(name, value) for name, value in sorted(values.items()))

def _lookup_zone(zone_id, zones, missing_code, diagnostics, phrase_index):
    if zone_id is None or not str(zone_id).strip():
        diagnostics.append(_fatal(missing_code, "zone id is required", phrase_index))
        return None
    zone = zones.get(str(zone_id))
    if zone is None:
        diagnostics.append(_fatal("UNKNOWN_ZONE_ID", f"unknown zone_id {zone_id!r}", phrase_index))
        return None
    try:
        GeometryReference(zone.zone_id, zone.center_price, zone.lower_price, zone.upper_price, zone.half_width)
    except Exception as exc:
        diagnostics.append(_fatal("INVALID_GEOMETRY_REFERENCE", str(exc), phrase_index))
        return None
    return zone

def _hold(zone, params, diagnostics, phrase_index):
    position = params.get("position")
    if isinstance(position, str):
        try:
            position = RelativePosition(position)
        except ValueError:
            position = None
    if not isinstance(position, RelativePosition):
        diagnostics.append(_fatal("UNSUPPORTED_PARAMETER_COMBINATION", "HOLD requires a supported position", phrase_index, "position"))
        return None, None, {}
    side = None
    if position in {RelativePosition.CURRENT, RelativePosition.CENTER, RelativePosition.INSIDE_ZONE}:
        price = zone.center_price
    elif position == RelativePosition.LOWER_BOUNDARY:
        side = ZoneSide.LOWER
        price = zone.lower_price
    elif position == RelativePosition.UPPER_BOUNDARY:
        side = ZoneSide.UPPER
        price = zone.upper_price
    elif position in {RelativePosition.OUTSIDE_LOWER, RelativePosition.OUTSIDE_UPPER}:
        distance = params.get("distance")
        if not _valid_fraction(distance):
            diagnostics.append(_fatal("INVALID_DISTANCE", "outside HOLD requires explicit non-negative Decimal distance", phrase_index, "distance"))
            return None, None, {}
        side = ZoneSide.LOWER if position == RelativePosition.OUTSIDE_LOWER else ZoneSide.UPPER
        price = _boundary(zone, side) + _signed(side, _scaled(zone, distance))
    else:
        diagnostics.append(_fatal("UNSUPPORTED_PARAMETER_COMBINATION", "unsupported HOLD position", phrase_index, "position"))
        return None, None, {}
    coordinate = _coord(position.value, zone, price, side)
    return coordinate, coordinate, {"anchor_price": price}

def _side_distance(zone, side_value, distance, kind, diagnostics, phrase_index, parameter_name):
    side = _side(side_value)
    if side is None:
        diagnostics.append(_fatal("MISSING_SIDE" if side_value is None else "INVALID_SIDE", "valid side required", phrase_index, "side"))
        return None, None, {}
    if not _valid_fraction(distance):
        diagnostics.append(_fatal("INVALID_DECIMAL_FRACTION", f"{parameter_name} must be a non-negative Decimal fraction", phrase_index, parameter_name))
        return None, None, {}
    boundary = _boundary(zone, side)
    offset = _signed(side, _scaled(zone, distance))
    anchor = boundary + offset
    return _coord("BOUNDARY", zone, boundary, side), _coord(kind, zone, anchor, side), {"boundary_price": boundary, "absolute_offset": offset, "anchor_price": anchor}

def _penetration(zone, params, name, diagnostics, phrase_index):
    depth = params.get(name)
    if not _valid_fraction(depth):
        diagnostics.append(_fatal("INVALID_DECIMAL_FRACTION", f"{name} must be a non-negative Decimal fraction", phrase_index, name))
        return None, None, {}
    side = _side(params.get("side"))
    if side is None:
        diagnostics.append(_fatal("UNRESOLVABLE_PENETRATION_DIRECTION", "PENETRATE requires side to resolve depth into an absolute geometry anchor", phrase_index, "side"))
        return None, None, {}
    boundary = _boundary(zone, side)
    anchor = boundary - _signed(side, _scaled(zone, depth))
    return _coord("BOUNDARY", zone, boundary, side), _coord("PENETRATION_DEPTH", zone, anchor, side), {"boundary_price": boundary, "absolute_offset": anchor - boundary, "anchor_price": anchor}

def _transfer(primitive_type, target_zone, source_zone, destination_zone, params, diagnostics, phrase_index):
    distance = params.get("travel_distance")
    if not _valid_fraction(distance):
        diagnostics.append(_fatal("INVALID_DECIMAL_FRACTION", "travel_distance must be a non-negative Decimal fraction", phrase_index, "travel_distance"))
        return None, None, {}
    if destination_zone.center_price > source_zone.center_price:
        direction = Direction.UP
    elif destination_zone.center_price < source_zone.center_price:
        direction = Direction.DOWN
    else:
        diagnostics.append(_fatal("INVALID_TRANSFER_DIRECTION", "source and target centers are identical", phrase_index, "source_zone"))
        return None, None, {}
    source_side = ZoneSide.UPPER if direction == Direction.UP else ZoneSide.LOWER
    target_side = ZoneSide.LOWER if direction == Direction.UP else ZoneSide.UPPER
    if primitive_type == PrimitiveType.WITHDRAW:
        start = _coord("SOURCE_CENTER", source_zone, source_zone.center_price, None)
        end_price = _boundary(source_zone, source_side) + _signed(source_side, _scaled(source_zone, distance))
        end = _coord("SOURCE_WITHDRAWAL", source_zone, end_price, source_side)
        return start, end, {"inferred_direction": direction.value, "travel_distance_absolute": _scaled(source_zone, distance)}
    if primitive_type == PrimitiveType.RAMP:
        start = _coord("SOURCE_CENTER", source_zone, source_zone.center_price, None)
        end = _coord("TARGET_CENTER", target_zone, target_zone.center_price, None)
    else:
        start = _coord("TARGET_APPROACH_BOUNDARY", target_zone, _boundary(target_zone, target_side), target_side)
        end = _coord("TARGET_CENTER", target_zone, target_zone.center_price, None)
    return start, end, {"inferred_direction": direction.value, "travel_distance_absolute": _scaled(target_zone, distance)}
def _resolve_one(segment, expanded, target_zone, source_zone, destination_zone, diagnostics):
    instruction = expanded.instruction
    params = _params(instruction.parameters)
    phrase_index = instruction.source_phrase_index
    if instruction.macro_origin == "TRANSFER_TO_ZONE" and source_zone is not None:
        start, end, resolved = _transfer(instruction.primitive_type, target_zone, source_zone, destination_zone or target_zone, params, diagnostics, phrase_index)
    elif instruction.primitive_type == PrimitiveType.HOLD:
        if "position" in params:
            start, end, resolved = _hold(target_zone, params, diagnostics, phrase_index)
        else:
            start, end, resolved = _penetration(target_zone, params, "depth", diagnostics, phrase_index)
    elif instruction.primitive_type in {PrimitiveType.APPROACH, PrimitiveType.ENTER}:
        name = "start_distance" if "start_distance" in params else "clearance" if "clearance" in params else "depth"
        start, end, resolved = _side_distance(target_zone, params.get("side"), params.get(name), instruction.primitive_type.value, diagnostics, phrase_index, name)
    elif instruction.primitive_type == PrimitiveType.PENETRATE:
        start, end, resolved = _penetration(target_zone, params, "depth" if "depth" in params else "clearance", diagnostics, phrase_index)
    elif instruction.primitive_type == PrimitiveType.WITHDRAW:
        name = "distance" if "distance" in params else "clearance" if "clearance" in params else "withdrawal_distance"
        start, end, resolved = _side_distance(target_zone, params.get("side"), params.get(name), "WITHDRAWAL", diagnostics, phrase_index, name)
    elif instruction.primitive_type == PrimitiveType.HOLD_OUTSIDE:
        start, end, resolved = _side_distance(target_zone, params.get("side"), params.get("clearance"), "HOLD_OUTSIDE", diagnostics, phrase_index, "clearance")
    elif instruction.primitive_type == PrimitiveType.RECOVERY_GAP:
        start, end, resolved = _side_distance(target_zone, params.get("side", ZoneSide.UPPER), params.get("withdrawal_distance"), "RECOVERY_GAP", diagnostics, phrase_index, "withdrawal_distance")
    elif instruction.primitive_type == PrimitiveType.RAMP:
        direction = _direction(params.get("direction"))
        distance = params.get("distance")
        if direction is None:
            diagnostics.append(_fatal("UNSUPPORTED_PARAMETER_COMBINATION", "RAMP requires direction outside transfer macro", phrase_index, "direction"))
            return None
        side = ZoneSide.UPPER if direction == Direction.UP else ZoneSide.LOWER
        if not _valid_fraction(distance):
            diagnostics.append(_fatal("INVALID_DECIMAL_FRACTION", "distance must be a non-negative Decimal fraction", phrase_index, "distance"))
            return None
        offset = _signed(side, _scaled(target_zone, distance))
        start = _coord("CENTER", target_zone, target_zone.center_price, None)
        end = _coord("RAMP_DISTANCE", target_zone, target_zone.center_price + offset, side)
        resolved = {"direction": direction.value, "absolute_offset": offset}
    elif instruction.primitive_type == PrimitiveType.OSCILLATE:
        amplitude = params.get("amplitude")
        if not _valid_fraction(amplitude):
            diagnostics.append(_fatal("INVALID_DECIMAL_FRACTION", "amplitude must be a non-negative Decimal fraction", phrase_index, "amplitude"))
            return None
        start = _coord("OSCILLATION_CENTER", target_zone, target_zone.center_price, None)
        end = _coord("OSCILLATION_AMPLITUDE", target_zone, target_zone.center_price + _scaled(target_zone, amplitude), ZoneSide.UPPER)
        resolved = {"amplitude_absolute": _scaled(target_zone, amplitude)}
    else:
        diagnostics.append(_fatal("PRIMITIVE_MACRO_ROLE_UNSUPPORTED", "unsupported primitive", phrase_index))
        return None
    if diagnostics and diagnostics[-1].severity == DiagnosticSeverity.FATAL:
        return None
    return ResolvedSegment(segment, expanded, target_zone, source_zone, start, end, _resolved_params(resolved), instruction.parameters)

def resolve_geometry(expansion_result, scheduling_result, geometry_context, resolver_version=GEOMETRY_RESOLVER_VERSION):
    """Resolve geometry-relative intent into absolute geometry anchors only."""
    if not isinstance(expansion_result, ExpansionResult):
        raise TypeError("expansion_result must be ExpansionResult")
    if not isinstance(scheduling_result, SchedulingResult):
        raise TypeError("scheduling_result must be SchedulingResult")
    if not isinstance(geometry_context, GeometryContext):
        raise TypeError("geometry_context must be GeometryContext")

    diagnostics = []
    if not expansion_result.success:
        diagnostics.extend(expansion_result.diagnostics)
        diagnostics.append(_fatal("UPSTREAM_EXPANSION_FAILED", "expansion_result.success is False"))
    if not scheduling_result.success:
        diagnostics.extend(scheduling_result.diagnostics)
        diagnostics.append(_fatal("UPSTREAM_SCHEDULING_FAILED", "scheduling_result.success is False"))
    if expansion_result.expansion_fingerprint != scheduling_result.expansion_fingerprint:
        diagnostics.append(_fatal("EXPANSION_SCHEDULING_FINGERPRINT_MISMATCH", "expansion and scheduling fingerprints differ"))
    if diagnostics:
        return _resolution_result(False, None, diagnostics, expansion_result, scheduling_result, geometry_context, resolver_version)

    assert scheduling_result.timeline is not None
    segments = scheduling_result.timeline.segments
    expanded_items = expansion_result.expanded_instructions
    if len(segments) != len(expanded_items):
        diagnostics.append(_fatal("TIMELINE_EXPANSION_LENGTH_MISMATCH", "timeline segment count differs from expanded instruction count"))
        return _resolution_result(False, None, diagnostics, expansion_result, scheduling_result, geometry_context, resolver_version)

    zones = {reference.zone_id: reference for reference in geometry_context.references}
    transfer_destinations = {}
    for item in expanded_items:
        transfer_instruction = item.instruction
        transfer_params = _params(transfer_instruction.parameters)
        if transfer_instruction.macro_origin == "TRANSFER_TO_ZONE" and transfer_instruction.primitive_type != PrimitiveType.WITHDRAW:
            source_id = transfer_params.get("source_zone")
            if source_id is not None and transfer_instruction.target_zone is not None and transfer_instruction.target_zone != source_id:
                transfer_destinations[transfer_instruction.source_phrase_index] = transfer_instruction.target_zone
    resolved_segments = []
    for segment, expanded in zip(segments, expanded_items):
        instruction = expanded.instruction
        phrase_index = instruction.source_phrase_index
        if segment.segment_index != instruction.instruction_index or segment.primitive_type != instruction.primitive_type or segment.target_zone != instruction.target_zone:
            diagnostics.append(_fatal("SEGMENT_INSTRUCTION_INDEX_MISMATCH", "timeline segment does not match expanded instruction", phrase_index))
            continue
        role = _ROLE_BY_KEY.get((instruction.primitive_type, instruction.macro_origin))
        if role is None:
            diagnostics.append(_fatal("PRIMITIVE_MACRO_ROLE_UNSUPPORTED", f"unsupported role {(instruction.primitive_type.value, instruction.macro_origin)!r}", phrase_index))
            continue
        params = _params(instruction.parameters)
        unsupported = tuple(sorted(set(params) - set(role.required_parameters + role.optional_parameters)))
        if unsupported:
            diagnostics.append(_fatal("UNSUPPORTED_PARAMETER_COMBINATION", f"unsupported parameters: {unsupported}", phrase_index, unsupported[0]))
            continue
        missing = tuple(name for name in role.required_parameters if name not in params)
        if missing:
            for name in missing:
                diagnostics.append(_fatal(_missing_code(name), f"required parameter {name!r} is missing", phrase_index, name))
            continue
        invalid = False
        for name, value in params.items():
            if name in _DISTANCE_PARAMETER_NAMES and not _valid_fraction(value):
                diagnostics.append(_fatal("INVALID_DECIMAL_FRACTION", f"{name} must be a non-negative Decimal fraction", phrase_index, name))
                invalid = True
            if name == "side" and _side(value) is None:
                diagnostics.append(_fatal("INVALID_SIDE", "side must be LOWER or UPPER", phrase_index, "side"))
                invalid = True
        if invalid:
            continue
        target_zone = _lookup_zone(instruction.target_zone, zones, "MISSING_TARGET_ZONE", diagnostics, phrase_index) if role.requires_target_zone else None
        source_zone = None
        if role.requires_source_zone:
            source_zone = _lookup_zone(params.get("source_zone"), zones, "MISSING_SOURCE_ZONE", diagnostics, phrase_index)
        if role.requires_target_zone and target_zone is None:
            continue
        if role.requires_source_zone and source_zone is None:
            continue
        destination_zone = None
        if instruction.macro_origin == "TRANSFER_TO_ZONE":
            destination_zone_id = transfer_destinations.get(instruction.source_phrase_index, instruction.target_zone)
            destination_zone = _lookup_zone(destination_zone_id, zones, "MISSING_TARGET_ZONE", diagnostics, phrase_index)
            if destination_zone is None:
                continue
        resolved = _resolve_one(segment, expanded, target_zone, source_zone, destination_zone, diagnostics)
        if resolved is not None:
            resolved_segments.append(resolved)

    if diagnostics:
        return _resolution_result(False, None, diagnostics, expansion_result, scheduling_result, geometry_context, resolver_version)
    return _resolution_result(True, ResolvedTimeline(tuple(resolved_segments)), (), expansion_result, scheduling_result, geometry_context, resolver_version)

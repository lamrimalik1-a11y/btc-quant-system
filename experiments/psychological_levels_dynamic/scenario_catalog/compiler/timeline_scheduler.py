"""Deterministic timeline scheduler.

Consumes an ExpansionResult and produces a SchedulingResult wrapping a
MechanicalTimeline. Row allocation only: no geometry resolution, no price
generation, no interpolation derivation, no materialization.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..grammar.dimensions import PathSmoothness
from .diagnostics import CompilerDiagnostic, DiagnosticSeverity
from .expansion import ExpansionResult
from .timeline import MechanicalTimeline, TimelineSegment

SCHEDULER_INTERPOLATION_POLICY_V1 = PathSmoothness.STEP


@dataclass(frozen=True)
class SchedulingResult:
    success: bool
    timeline: MechanicalTimeline | None
    diagnostics: tuple[CompilerDiagnostic, ...]
    grammar_fingerprint: str
    compiler_version: str
    expansion_fingerprint: str
    timeline_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")
        if self.timeline is not None and not isinstance(self.timeline, MechanicalTimeline):
            raise TypeError("timeline must be MechanicalTimeline or None")
        if self.success and self.timeline is None:
            raise ValueError("successful scheduling must produce a timeline")
        if not self.success and self.timeline is not None:
            raise ValueError("failed scheduling must not produce a timeline")
        if not isinstance(self.diagnostics, tuple) or not all(
            isinstance(item, CompilerDiagnostic) for item in self.diagnostics
        ):
            raise TypeError("diagnostics must be an immutable CompilerDiagnostic tuple")
        if not self.grammar_fingerprint.startswith("sha256:"):
            raise ValueError("grammar_fingerprint must be SHA-256")
        if not self.expansion_fingerprint.startswith("sha256:"):
            raise ValueError("expansion_fingerprint must be SHA-256")
        if not self.timeline_fingerprint.startswith("sha256:"):
            raise ValueError("timeline_fingerprint must be SHA-256")
        if not self.compiler_version.strip():
            raise ValueError("compiler_version must not be empty")


def _fatal(code: str, message: str) -> CompilerDiagnostic:
    return CompilerDiagnostic(
        code=code,
        severity=DiagnosticSeverity.FATAL,
        message=message,
        phrase_index=None,
        parameter_name=None,
    )


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return {"type": type(value).__name__, "value": value.value}
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
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
    if isinstance(value, CompilerDiagnostic):
        return {
            "code": value.code,
            "severity": _canonical(value.severity),
            "message": value.message,
            "phrase_index": value.phrase_index,
            "parameter_name": value.parameter_name,
        }
    raise TypeError(f"unsupported type for fingerprint canonicalization: {type(value).__name__}")


def _timeline_fingerprint(
    segments: tuple[TimelineSegment, ...],
    grammar_fingerprint: str,
    compiler_version: str,
    expansion_fingerprint: str,
    diagnostics: tuple[CompilerDiagnostic, ...],
) -> str:
    payload = {
        "segments": _canonical(segments),
        "grammar_fingerprint": grammar_fingerprint,
        "compiler_version": compiler_version,
        "expansion_fingerprint": expansion_fingerprint,
        "diagnostics": _canonical(diagnostics),
    }
    canonical_json = json.dumps(
        payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    )
    return "sha256:" + hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def _failure(
    expansion_result: ExpansionResult, diagnostics: list[CompilerDiagnostic]
) -> SchedulingResult:
    sorted_diagnostics = tuple(sorted(diagnostics, key=lambda item: item.deterministic_key))
    timeline_fingerprint = _timeline_fingerprint(
        (),
        expansion_result.grammar_fingerprint,
        expansion_result.compiler_version,
        expansion_result.expansion_fingerprint,
        sorted_diagnostics,
    )
    return SchedulingResult(
        success=False,
        timeline=None,
        diagnostics=sorted_diagnostics,
        grammar_fingerprint=expansion_result.grammar_fingerprint,
        compiler_version=expansion_result.compiler_version,
        expansion_fingerprint=expansion_result.expansion_fingerprint,
        timeline_fingerprint=timeline_fingerprint,
    )


def schedule_expansion(expansion_result: ExpansionResult) -> SchedulingResult:
    if not isinstance(expansion_result, ExpansionResult):
        raise TypeError("expansion_result must be ExpansionResult")

    if not expansion_result.success:
        return _failure(
            expansion_result,
            list(expansion_result.diagnostics)
            + [
                _fatal(
                    "UPSTREAM_EXPANSION_FAILED",
                    "expansion_result.success is False",
                )
            ],
        )

    instructions = expansion_result.expanded_instructions
    if len(instructions) == 0:
        return _failure(
            expansion_result,
            [
                _fatal(
                    "EMPTY_EXPANSION_RESULT",
                    "expansion_result contains zero expanded instructions",
                )
            ],
        )

    indices = [item.instruction.instruction_index for item in instructions]
    if len(set(indices)) != len(indices):
        return _failure(
            expansion_result,
            [
                _fatal(
                    "DUPLICATE_INSTRUCTION_INDEX",
                    "duplicate instruction_index values in expansion_result",
                )
            ],
        )
    if tuple(indices) != tuple(range(len(indices))):
        return _failure(
            expansion_result,
            [
                _fatal(
                    "NON_CONTIGUOUS_INSTRUCTION_INDEX",
                    "instruction_index values are not contiguous from zero",
                )
            ],
        )
    for item in instructions:
        if item.row_budget <= 0:
            return _failure(
                expansion_result,
                [
                    _fatal(
                        "NON_POSITIVE_ROW_BUDGET",
                        "expanded instruction row_budget must be positive",
                    )
                ],
            )

    segments: list[TimelineSegment] = []
    current_row = 1
    for segment_index, item in enumerate(instructions):
        interpolation_policy = SCHEDULER_INTERPOLATION_POLICY_V1
        for parameter in item.instruction.parameters:
            if (
                parameter.name
                in {"smoothness", "interpolation", "interpolation_policy"}
                and isinstance(parameter.value, PathSmoothness)
            ):
                interpolation_policy = parameter.value
                break
        row_start = current_row
        row_end = row_start + item.row_budget - 1
        segments.append(
            TimelineSegment(
                segment_index=segment_index,
                source_phrase_index=item.instruction.source_phrase_index,
                primitive_type=item.instruction.primitive_type,
                row_start=row_start,
                row_end=row_end,
                row_count=item.row_budget,
                target_zone=item.instruction.target_zone,
                macro_origin=item.instruction.macro_origin,
                interpolation_policy=interpolation_policy,
            )
        )
        current_row = row_end + 1

    for previous, current in zip(segments, segments[1:]):
        if current.row_start != previous.row_end + 1:
            return _failure(
                expansion_result,
                [
                    _fatal(
                        "TIMELINE_CONTIGUITY_VIOLATION",
                        "segments are not gap-free and non-overlapping",
                    )
                ],
            )
    total_budget = sum(item.row_budget for item in instructions)
    if segments[-1].row_end != total_budget:
        return _failure(
            expansion_result,
            [
                _fatal(
                    "TIMELINE_CONTIGUITY_VIOLATION",
                    "final row does not equal sum(row_budget)",
                )
            ],
        )

    timeline = MechanicalTimeline(segments=tuple(segments))
    timeline_fingerprint = _timeline_fingerprint(
        timeline.segments,
        expansion_result.grammar_fingerprint,
        expansion_result.compiler_version,
        expansion_result.expansion_fingerprint,
        (),
    )
    return SchedulingResult(
        success=True,
        timeline=timeline,
        diagnostics=(),
        grammar_fingerprint=expansion_result.grammar_fingerprint,
        compiler_version=expansion_result.compiler_version,
        expansion_fingerprint=expansion_result.expansion_fingerprint,
        timeline_fingerprint=timeline_fingerprint,
    )

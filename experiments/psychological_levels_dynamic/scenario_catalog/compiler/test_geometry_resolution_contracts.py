"""Structural validation for geometry-resolution contracts only."""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_catalog.compiler.diagnostics import (
    CompilerDiagnostic,
    DiagnosticSeverity,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.expansion import (
    ExpandedInstruction,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.geometry import (
    GeometryReference,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.geometry_resolution import (
    GEOMETRY_RESOLVER_CONTRACT_VERSION,
    GEOMETRY_RESOLUTION_DIAGNOSTIC_CODES,
    GeometryResolutionResult,
    GeometryResolutionRole,
    ResolvedCoordinate,
    ResolvedSegment,
    ResolvedTimeline,
    geometry_resolution_fingerprint,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.primitives import (
    PrimitiveInstruction,
    PrimitiveType,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.timeline import (
    TimelineSegment,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.ast import (
    GrammarParameter,
    PhraseType,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    PathSmoothness,
    ZoneSide,
)


MODULE_PATH = Path(__file__).with_name("geometry_resolution.py")
FORBIDDEN_IMPORTS = (
    "scenario_runner",
    "scenario_contract",
    "scenario_registry",
    "scenario_primitives",
    "scenario_catalog.catalog",
    "scenario_catalog.families",
    "scenario_catalog.specifications",
    "scenario_catalog.test_scenario_catalog",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "core.",
    "engines.",
    "research.",
    "random",
)
FORBIDDEN_CONTRACTS = (
    "priceobservation",
    "scenariospecification",
    "dynamic_state",
    "research_",
    "def materialize",
    "def generate_price",
    "run_scenario",
)

DUMMY_GRAMMAR_FINGERPRINT = "sha256:" + "1" * 64
DUMMY_EXPANSION_FINGERPRINT = "sha256:" + "2" * 64
DUMMY_TIMELINE_FINGERPRINT = "sha256:" + "3" * 64
DUMMY_GEOMETRY_FINGERPRINT = "sha256:" + "4" * 64
DUMMY_COMPILER_VERSION = "GEOMETRY_CONTRACT_TEST_COMPILER_V1"


def _expect_raises(exception: type[BaseException], callable_: Any) -> None:
    try:
        callable_()
    except exception:
        return
    raise AssertionError(f"expected {exception.__name__}")


def _zone(zone_id: str = "ZONE_A") -> GeometryReference:
    return GeometryReference(
        zone_id=zone_id,
        center_price=Decimal("60400"),
        lower_price=Decimal("60375"),
        upper_price=Decimal("60425"),
        half_width=Decimal("25"),
    )


def _instruction(index: int = 0) -> PrimitiveInstruction:
    return PrimitiveInstruction(
        instruction_index=index,
        source_phrase_index=index,
        primitive_type=PrimitiveType.PENETRATE,
        parameters=(
            GrammarParameter("depth", Decimal("0.5")),
            GrammarParameter("side", ZoneSide.UPPER),
        ),
        target_zone="ZONE_A",
        macro_origin=PhraseType.ACCEPTED_BREAK.value,
    )


def _timeline_segment(index: int = 0) -> TimelineSegment:
    return TimelineSegment(
        segment_index=index,
        source_phrase_index=index,
        primitive_type=PrimitiveType.PENETRATE,
        row_start=1 + index,
        row_end=1 + index,
        row_count=1,
        target_zone="ZONE_A",
        macro_origin=PhraseType.ACCEPTED_BREAK.value,
        interpolation_policy=PathSmoothness.STEP,
    )


def _expanded(index: int = 0) -> ExpandedInstruction:
    return ExpandedInstruction(_instruction(index), 1)


def _coordinate(price: str = "60437.5") -> ResolvedCoordinate:
    return ResolvedCoordinate(
        coordinate_type="BOUNDARY_OFFSET",
        absolute_price=Decimal(price),
        zone_id="ZONE_A",
        side=ZoneSide.UPPER.value,
        offset_from_boundary=Decimal("12.5"),
        offset_from_center=Decimal("37.5"),
    )


def _resolved_segment(index: int = 0) -> ResolvedSegment:
    expanded = _expanded(index)
    return ResolvedSegment(
        timeline_segment=_timeline_segment(index),
        expanded_instruction=expanded,
        resolved_target_zone=_zone("ZONE_A"),
        resolved_source_zone=None,
        start_coordinate_intent=_coordinate("60425"),
        end_coordinate_intent=_coordinate("60437.5"),
        resolved_parameters=(GrammarParameter("depth_offset", Decimal("12.5")),),
        source_parameters=expanded.instruction.parameters,
    )


def _timeline() -> ResolvedTimeline:
    return ResolvedTimeline(segments=(_resolved_segment(),))


def _result(timeline: ResolvedTimeline | None = None) -> GeometryResolutionResult:
    diagnostics: tuple[CompilerDiagnostic, ...] = ()
    fingerprint = geometry_resolution_fingerprint(
        timeline,
        diagnostics,
        DUMMY_GRAMMAR_FINGERPRINT,
        DUMMY_EXPANSION_FINGERPRINT,
        DUMMY_TIMELINE_FINGERPRINT,
        DUMMY_GEOMETRY_FINGERPRINT,
        DUMMY_COMPILER_VERSION,
        GEOMETRY_RESOLVER_CONTRACT_VERSION,
    )
    return GeometryResolutionResult(
        success=timeline is not None,
        resolved_timeline=timeline,
        diagnostics=diagnostics,
        grammar_fingerprint=DUMMY_GRAMMAR_FINGERPRINT,
        expansion_fingerprint=DUMMY_EXPANSION_FINGERPRINT,
        timeline_fingerprint=DUMMY_TIMELINE_FINGERPRINT,
        geometry_fingerprint=DUMMY_GEOMETRY_FINGERPRINT,
        compiler_version=DUMMY_COMPILER_VERSION,
        resolver_version=GEOMETRY_RESOLVER_CONTRACT_VERSION,
        resolution_fingerprint=fingerprint,
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "geometry_resolution_contracts": False,
        "resolved_coordinate": False,
        "resolved_segment": False,
        "resolved_timeline": False,
        "resolution_result": False,
        "immutability": False,
        "determinism": False,
        "research_isolation": False,
    }

    try:
        coordinate = _coordinate()
        assert coordinate.absolute_price == Decimal("60437.5")
        assert coordinate.offset_from_boundary == Decimal("12.5")
        _expect_raises(
            TypeError,
            lambda: ResolvedCoordinate(
                coordinate_type="BAD_FLOAT",
                absolute_price=60437.5,  # type: ignore[arg-type]
                zone_id="ZONE_A",
                side=None,
                offset_from_boundary=None,
                offset_from_center=None,
            ),
        )
        checks["resolved_coordinate"] = True

        segment = _resolved_segment()
        assert isinstance(segment.timeline_segment, TimelineSegment)
        assert isinstance(segment.expanded_instruction, ExpandedInstruction)
        assert segment.timeline_segment.segment_index == 0
        assert segment.expanded_instruction.instruction.instruction_index == 0
        assert segment.source_parameters == segment.expanded_instruction.instruction.parameters
        assert segment.resolved_target_zone == _zone("ZONE_A")
        checks["resolved_segment"] = True

        timeline = ResolvedTimeline(segments=(segment,))
        assert timeline.segments[0] == segment
        _expect_raises(
            ValueError,
            lambda: ResolvedTimeline(segments=(_resolved_segment(1),)),
        )
        checks["resolved_timeline"] = True

        role = GeometryResolutionRole(
            primitive_type=PrimitiveType.PENETRATE,
            macro_origin=PhraseType.ACCEPTED_BREAK.value,
            required_parameters=("side", "depth"),
            optional_parameters=("clearance",),
            requires_target_zone=True,
        )
        assert role.role_key == (
            PrimitiveType.PENETRATE,
            PhraseType.ACCEPTED_BREAK.value,
        )
        assert "MISSING_TARGET_ZONE" in GEOMETRY_RESOLUTION_DIAGNOSTIC_CODES
        assert "EXPANSION_SCHEDULING_FINGERPRINT_MISMATCH" in GEOMETRY_RESOLUTION_DIAGNOSTIC_CODES
        checks["geometry_resolution_contracts"] = True

        result = _result(timeline)
        assert result.success is True
        assert result.resolved_timeline == timeline
        assert result.compiler_version == DUMMY_COMPILER_VERSION
        failure_diagnostic = CompilerDiagnostic(
            code="UPSTREAM_SCHEDULING_FAILED",
            severity=DiagnosticSeverity.FATAL,
            message="Scheduling failed before geometry resolution.",
        )
        failure_fingerprint = geometry_resolution_fingerprint(
            None,
            (failure_diagnostic,),
            DUMMY_GRAMMAR_FINGERPRINT,
            DUMMY_EXPANSION_FINGERPRINT,
            DUMMY_TIMELINE_FINGERPRINT,
            DUMMY_GEOMETRY_FINGERPRINT,
            DUMMY_COMPILER_VERSION,
            GEOMETRY_RESOLVER_CONTRACT_VERSION,
        )
        failure = GeometryResolutionResult(
            success=False,
            resolved_timeline=None,
            diagnostics=(failure_diagnostic,),
            grammar_fingerprint=DUMMY_GRAMMAR_FINGERPRINT,
            expansion_fingerprint=DUMMY_EXPANSION_FINGERPRINT,
            timeline_fingerprint=DUMMY_TIMELINE_FINGERPRINT,
            geometry_fingerprint=DUMMY_GEOMETRY_FINGERPRINT,
            compiler_version=DUMMY_COMPILER_VERSION,
            resolver_version=GEOMETRY_RESOLVER_CONTRACT_VERSION,
            resolution_fingerprint=failure_fingerprint,
        )
        assert failure.success is False
        assert failure.resolved_timeline is None
        checks["resolution_result"] = True

        for value, attribute, replacement in (
            (coordinate, "absolute_price", Decimal("1")),
            (segment, "resolved_source_zone", _zone("ZONE_B")),
            (timeline, "segments", ()),
            (result, "success", False),
            (role, "required_parameters", ()),
        ):
            _expect_raises(
                FrozenInstanceError,
                lambda value=value, attribute=attribute, replacement=replacement: setattr(
                    value,
                    attribute,
                    replacement,
                ),
            )
        checks["immutability"] = True

        repeat = _result(_timeline())
        assert repeat.resolution_fingerprint == result.resolution_fingerprint
        changed_timeline = ResolvedTimeline(
            segments=(
                ResolvedSegment(
                    timeline_segment=_timeline_segment(),
                    expanded_instruction=_expanded(),
                    resolved_target_zone=_zone("ZONE_A"),
                    resolved_source_zone=None,
                    start_coordinate_intent=_coordinate("60425"),
                    end_coordinate_intent=_coordinate("60450"),
                    resolved_parameters=(GrammarParameter("depth_offset", Decimal("25")),),
                    source_parameters=_expanded().instruction.parameters,
                ),
            )
        )
        changed_fingerprint = geometry_resolution_fingerprint(
            changed_timeline,
            (),
            DUMMY_GRAMMAR_FINGERPRINT,
            DUMMY_EXPANSION_FINGERPRINT,
            DUMMY_TIMELINE_FINGERPRINT,
            DUMMY_GEOMETRY_FINGERPRINT,
            DUMMY_COMPILER_VERSION,
            GEOMETRY_RESOLVER_CONTRACT_VERSION,
        )
        assert changed_fingerprint != result.resolution_fingerprint
        assert failure_fingerprint != result.resolution_fingerprint
        checks["determinism"] = True

        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        import_lines = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        assert not any(token in import_lines for token in FORBIDDEN_IMPORTS)
        assert not any(token in source for token in FORBIDDEN_CONTRACTS)
        assert "geometry anchor intent" in source
        assert "materialized row" in source
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    for field in (
        "geometry_resolution_contracts",
        "resolved_coordinate",
        "resolved_segment",
        "resolved_timeline",
        "resolution_result",
        "immutability",
        "determinism",
        "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

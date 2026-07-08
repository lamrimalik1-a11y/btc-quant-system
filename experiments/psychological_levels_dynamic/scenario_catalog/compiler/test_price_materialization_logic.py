"""Validation for deterministic price materialization logic only."""

from __future__ import annotations

import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_contract import PriceObservation
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.diagnostics import (
    CompilerDiagnostic,
    DiagnosticSeverity,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.expansion import (
    ExpandedInstruction,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.geometry import (
    GeometryContext,
    GeometryReference,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.geometry_resolution import (
    GeometryResolutionResult,
    ResolvedCoordinate,
    ResolvedSegment,
    ResolvedTimeline,
    resolve_geometry,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.macro_expansion import (
    expand_program,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.price_materialization import (
    PRICE_MATERIALIZER_VERSION,
    materialize_prices,
    observation_checksum,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.primitives import (
    PrimitiveInstruction,
    PrimitiveType,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.timeline import (
    TimelineSegment,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.timeline_scheduler import (
    schedule_expansion,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.ast import (
    GRAMMAR_SCHEMA_VERSION,
    GrammarProgram,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    PathSmoothness,
    RelativePosition,
    ZoneSide,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.phrases import (
    accepted_break,
    compress,
    expand,
    hold,
    reclaim,
    recovery_gap,
    transfer_to_zone,
)

MODULE_PATH = Path(__file__).with_name("price_materialization.py")
DUMMY_GRAMMAR_FINGERPRINT = "sha256:" + "1" * 64
DUMMY_EXPANSION_FINGERPRINT = "sha256:" + "2" * 64
DUMMY_TIMELINE_FINGERPRINT = "sha256:" + "3" * 64
DUMMY_GEOMETRY_FINGERPRINT = "sha256:" + "4" * 64
DUMMY_RESOLUTION_FINGERPRINT = "sha256:" + "5" * 64
DUMMY_COMPILER_VERSION = "PRICE_MATERIALIZATION_LOGIC_TEST_COMPILER_V1"

FORBIDDEN_IMPORTS = (
    "scenario_runner",
    "scenario_registry",
    "scenario_primitives",
    "scenario_catalog.catalog",
    "scenario_catalog.families",
    "scenario_catalog.specifications",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "core.",
    "engines.",
    "research.",
    "random",
)
FORBIDDEN_SOURCE = (
    "scenariospecification",
    "dynamic_state",
    "research_",
    "def generate_price",
    "run_scenario",
)


def _coord(price: str, kind: str = "TEST_ANCHOR") -> ResolvedCoordinate:
    return ResolvedCoordinate(
        coordinate_type=kind,
        absolute_price=Decimal(price),
        zone_id="TEST_ZONE",
        side=None,
        offset_from_boundary=None,
        offset_from_center=Decimal("0"),
    )


def _segment(
    *,
    row_start: int,
    row_count: int,
    start_price: str | None,
    end_price: str | None,
    policy: PathSmoothness,
) -> ResolvedSegment:
    timeline_segment = TimelineSegment(
        segment_index=0,
        source_phrase_index=0,
        primitive_type=PrimitiveType.RAMP,
        row_start=row_start,
        row_end=row_start + row_count - 1,
        row_count=row_count,
        target_zone="TEST_ZONE",
        macro_origin=None,
        interpolation_policy=policy,
    )
    instruction = PrimitiveInstruction(
        instruction_index=0,
        source_phrase_index=0,
        primitive_type=PrimitiveType.RAMP,
        parameters=(),
        target_zone="TEST_ZONE",
        macro_origin=None,
    )
    return ResolvedSegment(
        timeline_segment=timeline_segment,
        expanded_instruction=ExpandedInstruction(instruction, row_count),
        resolved_target_zone=None,
        resolved_source_zone=None,
        start_coordinate_intent=None if start_price is None else _coord(start_price, "START"),
        end_coordinate_intent=None if end_price is None else _coord(end_price, "END"),
        resolved_parameters=(),
        source_parameters=(),
    )


def _result(*segments: ResolvedSegment) -> GeometryResolutionResult:
    return GeometryResolutionResult(
        success=True,
        resolved_timeline=ResolvedTimeline(segments),
        diagnostics=(),
        grammar_fingerprint=DUMMY_GRAMMAR_FINGERPRINT,
        expansion_fingerprint=DUMMY_EXPANSION_FINGERPRINT,
        timeline_fingerprint=DUMMY_TIMELINE_FINGERPRINT,
        geometry_fingerprint=DUMMY_GEOMETRY_FINGERPRINT,
        compiler_version=DUMMY_COMPILER_VERSION,
        resolver_version="PRICE_MATERIALIZATION_LOGIC_TEST_RESOLVER_V1",
        resolution_fingerprint=DUMMY_RESOLUTION_FINGERPRINT,
    )


def _failed_geometry_result() -> GeometryResolutionResult:
    diagnostic = CompilerDiagnostic(
        code="GEOMETRY_FAILED_FOR_MATERIALIZATION_TEST",
        severity=DiagnosticSeverity.FATAL,
        message="Geometry resolution failed for materialization test.",
    )
    return GeometryResolutionResult(
        success=False,
        resolved_timeline=None,
        diagnostics=(diagnostic,),
        grammar_fingerprint=DUMMY_GRAMMAR_FINGERPRINT,
        expansion_fingerprint=DUMMY_EXPANSION_FINGERPRINT,
        timeline_fingerprint=DUMMY_TIMELINE_FINGERPRINT,
        geometry_fingerprint=DUMMY_GEOMETRY_FINGERPRINT,
        compiler_version=DUMMY_COMPILER_VERSION,
        resolver_version="PRICE_MATERIALIZATION_LOGIC_TEST_RESOLVER_V1",
        resolution_fingerprint=DUMMY_RESOLUTION_FINGERPRINT,
    )


def _codes(result) -> set[str]:
    return {diagnostic.code for diagnostic in result.diagnostics}


def _zone(zone_id: str, center: str) -> GeometryReference:
    center_price = Decimal(center)
    half_width = Decimal("25")
    return GeometryReference(
        zone_id=zone_id,
        center_price=center_price,
        lower_price=center_price - half_width,
        upper_price=center_price + half_width,
        half_width=half_width,
    )


def _end_to_end_geometry() -> GeometryContext:
    return GeometryContext(
        symbol="BTCUSDT",
        geometry_version="PRICE_MATERIALIZATION_END_TO_END_V1",
        references=(_zone("TARGET", "60400"),),
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "step_materialization": False,
        "linear_single_row": False,
        "linear_multi_row": False,
        "checksum_determinism": False,
        "fatal_rollback": False,
        "end_to_end_row_alignment": False,
        "cross_process_determinism": False,
        "research_isolation": False,
    }
    try:
        step = materialize_prices(
            _result(
                _segment(
                    row_start=1,
                    row_count=3,
                    start_price="100",
                    end_price="105",
                    policy=PathSmoothness.STEP,
                )
            )
        )
        assert step.success is True
        assert step.observations == (
            PriceObservation(1, Decimal("105")),
            PriceObservation(2, Decimal("105")),
            PriceObservation(3, Decimal("105")),
        )
        checks["step_materialization"] = True

        single = materialize_prices(
            _result(
                _segment(
                    row_start=7,
                    row_count=1,
                    start_price="100",
                    end_price="110",
                    policy=PathSmoothness.LINEAR,
                )
            )
        )
        assert single.success is True
        assert single.observations == (PriceObservation(7, Decimal("110")),)
        checks["linear_single_row"] = True

        linear = materialize_prices(
            _result(
                _segment(
                    row_start=10,
                    row_count=5,
                    start_price="100",
                    end_price="110",
                    policy=PathSmoothness.LINEAR,
                )
            )
        )
        assert linear.success is True
        assert linear.observations == (
            PriceObservation(10, Decimal("100")),
            PriceObservation(11, Decimal("102.5")),
            PriceObservation(12, Decimal("105")),
            PriceObservation(13, Decimal("107.5")),
            PriceObservation(14, Decimal("110")),
        )
        checks["linear_multi_row"] = True

        repeat = materialize_prices(
            _result(
                _segment(
                    row_start=10,
                    row_count=5,
                    start_price="100.0",
                    end_price="110.00",
                    policy=PathSmoothness.LINEAR,
                )
            )
        )
        assert repeat.observation_checksum == linear.observation_checksum
        assert repeat.materialization_fingerprint == linear.materialization_fingerprint
        changed = materialize_prices(
            _result(
                _segment(
                    row_start=10,
                    row_count=5,
                    start_price="100",
                    end_price="111",
                    policy=PathSmoothness.LINEAR,
                )
            )
        )
        assert changed.observation_checksum != linear.observation_checksum
        assert observation_checksum(linear.observations) == linear.observation_checksum
        checks["checksum_determinism"] = True

        upstream_failed = materialize_prices(_failed_geometry_result())
        assert upstream_failed.success is False
        assert upstream_failed.observations == ()
        assert upstream_failed.observation_checksum is None
        assert "UPSTREAM_GEOMETRY_RESOLUTION_FAILED" in _codes(upstream_failed)
        missing_coordinate = materialize_prices(
            _result(
                _segment(
                    row_start=0,
                    row_count=2,
                    start_price=None,
                    end_price="100",
                    policy=PathSmoothness.LINEAR,
                )
            )
        )
        assert missing_coordinate.success is False
        assert missing_coordinate.observations == ()
        assert missing_coordinate.observation_checksum is None
        assert "MISSING_OR_INVALID_COORDINATE" in _codes(missing_coordinate)
        checks["fatal_rollback"] = True

        # End-to-end regression: Grammar -> Expansion -> Scheduling ->
        # Geometry Resolution -> Materialization. Reproduces the exact
        # scenario that exposed the prior +1 row_index bug (two adjacent
        # segments; without the fix, row 1 is skipped and a phantom row
        # one past the true final row is produced instead).
        program = GrammarProgram(
            "PRICE_MATERIALIZATION_END_TO_END",
            GRAMMAR_SCHEMA_VERSION,
            (
                hold(3, RelativePosition.CENTER, "TARGET"),
                hold(2, RelativePosition.CENTER, "TARGET"),
            ),
            (),
            (),
            (),
        )
        end_to_end_expansion = expand_program(program, "PRICE_MATERIALIZATION_END_TO_END_V1")
        assert end_to_end_expansion.success is True
        end_to_end_scheduling = schedule_expansion(end_to_end_expansion)
        assert end_to_end_scheduling.success is True
        end_to_end_resolution = resolve_geometry(
            end_to_end_expansion, end_to_end_scheduling, _end_to_end_geometry()
        )
        assert end_to_end_resolution.success is True
        end_to_end_materialized = materialize_prices(end_to_end_resolution)
        assert end_to_end_materialized.success is True

        expected_row_indices: list[int] = []
        for resolved_segment in end_to_end_resolution.resolved_timeline.segments:
            timeline_segment = resolved_segment.timeline_segment
            expected_row_indices.extend(
                range(timeline_segment.row_start, timeline_segment.row_end + 1)
            )
        actual_row_indices = [
            observation.row_index for observation in end_to_end_materialized.observations
        ]
        assert actual_row_indices == expected_row_indices
        assert actual_row_indices == [1, 2, 3, 4, 5]
        checks["end_to_end_row_alignment"] = True

        if os.environ.get("PRICE_MATERIALIZATION_CHILD") == "1":
            checks["cross_process_determinism"] = True
        else:
            env = dict(os.environ)
            env["PRICE_MATERIALIZATION_CHILD"] = "1"
            first = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
            second = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
            assert first == second
            checks["cross_process_determinism"] = True

        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        assert not any(token in imports for token in FORBIDDEN_IMPORTS)
        assert not any(token in source for token in FORBIDDEN_SOURCE)
        assert "def materialize_prices" in source
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result}


def main() -> None:
    report = run()
    for field in (
        "step_materialization",
        "linear_single_row",
        "linear_multi_row",
        "checksum_determinism",
        "fatal_rollback",
        "end_to_end_row_alignment",
        "cross_process_determinism",
        "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
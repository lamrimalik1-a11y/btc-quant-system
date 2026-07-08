"""Validation for the thin full compiler orchestrator only."""

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

from experiments.psychological_levels_dynamic.scenario_catalog.compiler import full_compiler
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.diagnostics import (
    CompilerDiagnostic,
    DiagnosticSeverity,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.geometry import (
    GeometryContext,
    GeometryReference,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.price_materialization import (
    PRICE_MATERIALIZER_VERSION,
    MaterializationResult,
    materialization_fingerprint,
    observation_checksum,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.timeline_scheduler import (
    SchedulingResult,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.ast import (
    GRAMMAR_SCHEMA_VERSION,
    GrammarProgram,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    RelativePosition,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.phrases import (
    break_candidate,
    hold,
    penetrate,
)

MODULE_PATH = Path(__file__).with_name("full_compiler.py")
COMPILER_VERSION = "FULL_COMPILER_TEST_V1"
FORBIDDEN_IMPORTS = (
    "scenario_runner",
    "scenario_contract",
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


def _zone(zone_id: str = "ZONE_A", center: str = "60400") -> GeometryReference:
    center_price = Decimal(center)
    half_width = Decimal("25")
    return GeometryReference(
        zone_id=zone_id,
        center_price=center_price,
        lower_price=center_price - half_width,
        upper_price=center_price + half_width,
        half_width=half_width,
    )


def _geometry() -> GeometryContext:
    return GeometryContext(
        symbol="BTCUSDT",
        geometry_version="FULL_COMPILER_TEST_GEOMETRY_V1",
        references=(_zone(),),
    )


def _program(*phrases: Any, program_id: str = "FULL_COMPILER_TEST") -> GrammarProgram:
    return GrammarProgram(program_id, GRAMMAR_SCHEMA_VERSION, phrases, (), (), ())


def _success_program() -> GrammarProgram:
    return _program(hold(5, RelativePosition.CENTER, "ZONE_A"))


def _fatal(code: str) -> CompilerDiagnostic:
    return CompilerDiagnostic(
        code=code,
        severity=DiagnosticSeverity.FATAL,
        message=f"{code} for full compiler test.",
    )


def _codes(result) -> set[str]:
    return {diagnostic.code for diagnostic in result.diagnostics}


def _failed_materialization(geometry_result) -> MaterializationResult:
    diagnostics = (_fatal("MATERIALIZATION_FAILED_FOR_FULL_COMPILER_TEST"),)
    fingerprint = materialization_fingerprint(
        observation_checksum_value=None,
        diagnostics=diagnostics,
        grammar_fingerprint=geometry_result.grammar_fingerprint,
        expansion_fingerprint=geometry_result.expansion_fingerprint,
        timeline_fingerprint=geometry_result.timeline_fingerprint,
        geometry_fingerprint=geometry_result.geometry_fingerprint,
        resolution_fingerprint=geometry_result.resolution_fingerprint,
        compiler_version=geometry_result.compiler_version,
        materializer_version=PRICE_MATERIALIZER_VERSION,
    )
    return MaterializationResult(
        success=False,
        observations=(),
        diagnostics=diagnostics,
        observation_checksum=None,
        materialization_fingerprint=fingerprint,
        grammar_fingerprint=geometry_result.grammar_fingerprint,
        expansion_fingerprint=geometry_result.expansion_fingerprint,
        timeline_fingerprint=geometry_result.timeline_fingerprint,
        geometry_fingerprint=geometry_result.geometry_fingerprint,
        resolution_fingerprint=geometry_result.resolution_fingerprint,
        compiler_version=geometry_result.compiler_version,
        materializer_version=PRICE_MATERIALIZER_VERSION,
    )


def _failed_schedule(expansion_result) -> SchedulingResult:
    diagnostics = (_fatal("SCHEDULING_FAILED_FOR_FULL_COMPILER_TEST"),)
    return SchedulingResult(
        success=False,
        timeline=None,
        diagnostics=diagnostics,
        grammar_fingerprint=expansion_result.grammar_fingerprint,
        compiler_version=expansion_result.compiler_version,
        expansion_fingerprint=expansion_result.expansion_fingerprint,
        timeline_fingerprint="sha256:" + "6" * 64,
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "successful_compilation": False,
        "checksum_and_timeline": False,
        "diagnostics_preserved": False,
        "fatal_rollback": False,
        "determinism": False,
        "cross_process_determinism": False,
        "research_isolation": False,
    }
    try:
        geometry = _geometry()
        result = full_compiler.compile_program(
            _success_program(),
            geometry,
            COMPILER_VERSION,
        )
        assert result.success is True
        assert result.observations
        assert result.timeline is not None
        assert result.diagnostics == ()
        assert result.grammar_fingerprint == _success_program().program_fingerprint
        assert result.geometry_fingerprint == geometry.geometry_fingerprint
        assert result.compiler_version == COMPILER_VERSION
        checks["successful_compilation"] = True

        assert result.observation_checksum == observation_checksum(result.observations)
        expected_rows = sum(segment.row_count for segment in result.timeline.segments)
        assert expected_rows == len(result.observations)
        assert tuple(observation.row_index for observation in result.observations) == tuple(
            range(1, expected_rows + 1)
        )
        checks["checksum_and_timeline"] = True

        expansion_failed = full_compiler.compile_program(
            _program(
                break_candidate(5, "ZONE_A", __import__(
                    "experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions",
                    fromlist=["ZoneSide"],
                ).ZoneSide.UPPER, Decimal("1")),
                program_id="FULL_COMPILER_EXPANSION_FAILURE",
            ),
            geometry,
            COMPILER_VERSION,
        )
        assert expansion_failed.success is False
        assert expansion_failed.observations == ()
        assert expansion_failed.timeline is None
        assert expansion_failed.observation_checksum is None
        assert "MISSING_EXPANSION_RULE" in _codes(expansion_failed)
        keys = [diagnostic.deterministic_key for diagnostic in expansion_failed.diagnostics]
        assert keys == sorted(keys)
        checks["diagnostics_preserved"] = True

        original_scheduler = full_compiler.schedule_expansion
        full_compiler.schedule_expansion = _failed_schedule
        try:
            scheduling_failed = full_compiler.compile_program(
                _success_program(),
                geometry,
                COMPILER_VERSION,
            )
        finally:
            full_compiler.schedule_expansion = original_scheduler
        assert scheduling_failed.success is False
        assert scheduling_failed.observations == ()
        assert scheduling_failed.timeline is None
        assert scheduling_failed.observation_checksum is None
        assert "SCHEDULING_FAILED_FOR_FULL_COMPILER_TEST" in _codes(scheduling_failed)

        geometry_failed = full_compiler.compile_program(
            _program(penetrate(3, "ZONE_A", Decimal("0.5")), program_id="FULL_COMPILER_GEOMETRY_FAILURE"),
            geometry,
            COMPILER_VERSION,
        )
        assert geometry_failed.success is False
        assert geometry_failed.observations == ()
        assert geometry_failed.timeline is None
        assert geometry_failed.observation_checksum is None
        assert "UNRESOLVABLE_PENETRATION_DIRECTION" in _codes(geometry_failed)

        original_materializer = full_compiler.materialize_prices
        full_compiler.materialize_prices = _failed_materialization
        try:
            materialization_failed = full_compiler.compile_program(
                _success_program(),
                geometry,
                COMPILER_VERSION,
            )
        finally:
            full_compiler.materialize_prices = original_materializer
        assert materialization_failed.success is False
        assert materialization_failed.observations == ()
        assert materialization_failed.timeline is None
        assert materialization_failed.observation_checksum is None
        assert "MATERIALIZATION_FAILED_FOR_FULL_COMPILER_TEST" in _codes(materialization_failed)
        checks["fatal_rollback"] = True

        repeat = full_compiler.compile_program(_success_program(), geometry, COMPILER_VERSION)
        assert repeat == result
        changed = full_compiler.compile_program(
            _program(hold(6, RelativePosition.CENTER, "ZONE_A"), program_id="FULL_COMPILER_CHANGED"),
            geometry,
            COMPILER_VERSION,
        )
        assert changed.success is True
        assert changed.observation_checksum != result.observation_checksum
        checks["determinism"] = True

        if os.environ.get("FULL_COMPILER_CHILD") == "1":
            checks["cross_process_determinism"] = True
        else:
            env = dict(os.environ)
            env["FULL_COMPILER_CHILD"] = "1"
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
        assert "def compile_program" in source
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    for field in (
        "successful_compilation",
        "checksum_and_timeline",
        "diagnostics_preserved",
        "fatal_rollback",
        "determinism",
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
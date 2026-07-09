"""Validation for deterministic batch compilation of generated GrammarProgram objects."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_catalog.compiler.geometry import (
    GeometryContext,
    GeometryReference,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    RelativePosition,
)
from experiments.psychological_levels_dynamic.scenario_generation.batch_compiler import (
    BatchCompilationResult,
    compile_generation_batch,
)
from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    GrammarTemplate,
    ParameterAxis,
    PhraseSlot,
)
from experiments.psychological_levels_dynamic.scenario_generation.generator import (
    generate_programs,
)

MODULE_PATH = Path(__file__).with_name("batch_compiler.py")
COMPILER_VERSION = "PHASE2B_BATCH_COMPILER_TEST_COMPILER_V1"
BATCH_VERSION = "PHASE2B_BATCH_COMPILER_TEST_BATCH_V1"
FORBIDDEN_IMPORTS = (
    "assemble_specification",
    "scenario_runner",
    "scenario_contract",
    "scenario_registry",
    "scenario_primitives",
    "scenario_catalog.catalog",
    "scenario_catalog.families",
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
    "run_scenario",
    "scenariospecification",
    "stage1",
    "stage2",
    "stage3",
    "stage4",
    "stage5",
    "stage6",
    "dynamic_state",
    "research_stable",
    "research_attacker",
)


def _geometry_context() -> GeometryContext:
    center = Decimal("60400")
    half_width = Decimal("25")
    return GeometryContext(
        symbol="BTCUSDT",
        geometry_version="PHASE2B_BATCH_COMPILER_TEST_GEOMETRY_V1",
        references=(
            GeometryReference(
                zone_id="ZONE_A",
                center_price=center,
                lower_price=center - half_width,
                upper_price=center + half_width,
                half_width=half_width,
            ),
        ),
    )


def _success_template() -> GrammarTemplate:
    return GrammarTemplate(
        template_id="BATCH_CENTER_DWELL_TEMPLATE",
        template_version="1",
        family_tag="BATCH_CENTER_DWELL",
        description="Compile-safe center holds.",
        phrase_slots=(
            PhraseSlot(
                constructor_name="hold",
                fixed_params=(("position", RelativePosition.CENTER), ("target_zone", "ZONE_A")),
                axis_bound_params=(("row_budget", "dwell_rows"),),
            ),
        ),
        axes=(ParameterAxis("dwell_rows", (2, 3, 4)),),
        rules=(),
    )


def _failure_template() -> GrammarTemplate:
    return GrammarTemplate(
        template_id="BATCH_PENETRATION_FAILURE_TEMPLATE",
        template_version="1",
        family_tag="BATCH_FAILURE",
        description="Generated programs that fail geometry because side is unavailable.",
        phrase_slots=(
            PhraseSlot(
                constructor_name="penetrate",
                fixed_params=(("target_zone", "ZONE_A"),),
                axis_bound_params=(
                    ("row_budget", "rows"),
                    ("depth", "depth"),
                ),
            ),
        ),
        axes=(
            ParameterAxis("rows", (2,)),
            ParameterAxis("depth", (Decimal("0.5"),)),
        ),
        rules=(),
    )


def _mixed_generation():
    success_generation = generate_programs(_success_template(), "BATCH_GEN_V1")
    failure_generation = generate_programs(_failure_template(), "BATCH_GEN_V1")
    assert success_generation.success is True
    assert failure_generation.success is True
    return replace(
        success_generation,
        generated_programs=success_generation.generated_programs + failure_generation.generated_programs,
        generation_fingerprint="sha256:" + "2" * 64,
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "batch_success": False,
        "partial_failure": False,
        "determinism": False,
        "cross_process_determinism": False,
        "diagnostics_preserved": False,
        "research_isolation": False,
    }
    try:
        success_generation = generate_programs(_success_template(), "BATCH_GEN_V1")
        result = compile_generation_batch(
            success_generation,
            _geometry_context(),
            COMPILER_VERSION,
            BATCH_VERSION,
        )
        assert isinstance(result, BatchCompilationResult)
        assert result.success is True
        assert result.total_programs == 3
        assert result.compiled_programs == 3
        assert result.failed_programs == 0
        assert result.failed_program_ids == ()
        assert result.diagnostics == ()
        assert len(result.successful_results) == 3
        assert all(compilation.success for compilation in result.successful_results)
        assert all(compilation.observation_checksum is not None for compilation in result.successful_results)
        checks["batch_success"] = True

        mixed_result = compile_generation_batch(
            _mixed_generation(),
            _geometry_context(),
            COMPILER_VERSION,
            BATCH_VERSION,
        )
        assert mixed_result.success is False
        assert mixed_result.total_programs == 4
        assert mixed_result.compiled_programs == 3
        assert mixed_result.failed_programs == 1
        assert len(mixed_result.successful_results) == 3
        assert len(mixed_result.failed_program_ids) == 1
        checks["partial_failure"] = True

        assert any("COMPILATION_FAILED" in diagnostic for diagnostic in mixed_result.diagnostics)
        assert any("UNRESOLVABLE_PENETRATION_DIRECTION" in diagnostic for diagnostic in mixed_result.diagnostics)
        checks["diagnostics_preserved"] = True

        repeat = compile_generation_batch(
            success_generation,
            _geometry_context(),
            COMPILER_VERSION,
            BATCH_VERSION,
        )
        assert repeat == result
        assert repeat.batch_compilation_fingerprint == result.batch_compilation_fingerprint
        mixed_repeat = compile_generation_batch(
            _mixed_generation(),
            _geometry_context(),
            COMPILER_VERSION,
            BATCH_VERSION,
        )
        assert mixed_repeat == mixed_result
        assert mixed_result.batch_compilation_fingerprint != result.batch_compilation_fingerprint
        checks["determinism"] = True

        if os.environ.get("BATCH_COMPILER_CHILD") == "1":
            return {
                "child_success_fingerprint": result.batch_compilation_fingerprint,
                "child_mixed_fingerprint": mixed_result.batch_compilation_fingerprint,
                "result": "PASS",
            }
        env = dict(os.environ)
        env["BATCH_COMPILER_CHILD"] = "1"
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
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    if os.environ.get("BATCH_COMPILER_CHILD") == "1":
        print(f"success={report['child_success_fingerprint']}")
        print(f"mixed={report['child_mixed_fingerprint']}")
        print(f"result={report['result']}")
        if report["result"] != "PASS":
            raise SystemExit(1)
        return
    for field in (
        "batch_success",
        "partial_failure",
        "determinism",
        "cross_process_determinism",
        "diagnostics_preserved",
        "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
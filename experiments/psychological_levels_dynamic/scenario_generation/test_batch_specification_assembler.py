"""Validation for batch assembly of compiled grammar output."""

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
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.specification_assembler import (
    AssembledSpecification,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    RelativePosition,
)
from experiments.psychological_levels_dynamic.scenario_generation.batch_compiler import (
    compile_generation_batch,
)
from experiments.psychological_levels_dynamic.scenario_generation.batch_specification_assembler import (
    BatchAssemblyResult,
    assemble_batch,
)
from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    GrammarTemplate,
    ParameterAxis,
    PhraseSlot,
)
from experiments.psychological_levels_dynamic.scenario_generation.generator import (
    generate_programs,
)
from experiments.psychological_levels_dynamic.scenario_generation.runner_execution_context import (
    RunnerExecutionContext,
)

MODULES = (
    Path(__file__).with_name("runner_execution_context.py"),
    Path(__file__).with_name("batch_specification_assembler.py"),
)
COMPILER_VERSION = "PHASE2C_BATCH_ASSEMBLER_TEST_COMPILER_V1"
BATCH_VERSION = "PHASE2C_BATCH_ASSEMBLER_TEST_BATCH_V1"
ASSEMBLY_VERSION = "PHASE2C_BATCH_ASSEMBLER_TEST_ASSEMBLY_V1"
FORBIDDEN_IMPORTS = (
    "scenario_runner",
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
        geometry_version="PHASE2C_BATCH_ASSEMBLER_TEST_GEOMETRY_V1",
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


def _execution_context() -> RunnerExecutionContext:
    return RunnerExecutionContext(
        symbol="BTCUSDT",
        geometry_context=_geometry_context(),
        active_window=0,
        spacing=Decimal("200"),
        zone_half_width=Decimal("25"),
        market_timestamp=1_700_000_000_000,
        session_id="PHASE2C_BATCH_ASSEMBLER_TEST_SESSION",
        runner_version="PHASE2C_BATCH_ASSEMBLER_TEST_RUNNER_V1",
    )


def _success_template() -> GrammarTemplate:
    return GrammarTemplate(
        template_id="ASSEMBLER_CENTER_DWELL_TEMPLATE",
        template_version="1",
        family_tag="ASSEMBLER_CENTER_DWELL",
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
        template_id="ASSEMBLER_PENETRATION_FAILURE_TEMPLATE",
        template_version="1",
        family_tag="ASSEMBLER_FAILURE",
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


def _success_batch():
    generation = generate_programs(_success_template(), "ASSEMBLER_GEN_V1")
    assert generation.success is True
    return compile_generation_batch(generation, _geometry_context(), COMPILER_VERSION, BATCH_VERSION)


def _mixed_batch():
    success_generation = generate_programs(_success_template(), "ASSEMBLER_GEN_V1")
    failure_generation = generate_programs(_failure_template(), "ASSEMBLER_GEN_V1")
    assert success_generation.success is True
    assert failure_generation.success is True
    mixed_generation = replace(
        success_generation,
        generated_programs=success_generation.generated_programs + failure_generation.generated_programs,
        generation_fingerprint="sha256:" + "3" * 64,
    )
    return compile_generation_batch(mixed_generation, _geometry_context(), COMPILER_VERSION, BATCH_VERSION)


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "successful_batch": False,
        "partial_failure": False,
        "ordering_preserved": False,
        "runner_ready_geometry": False,
        "fingerprint_determinism": False,
        "cross_process_determinism": False,
        "research_isolation": False,
    }
    try:
        context = _execution_context()
        assert context.execution_context_fingerprint.startswith("sha256:")

        successful_batch = _success_batch()
        assembly = assemble_batch(successful_batch, context, ASSEMBLY_VERSION)
        assert isinstance(assembly, BatchAssemblyResult)
        assert assembly.success is True
        assert assembly.total_compilations == 3
        assert assembly.failed_program_ids == ()
        assert assembly.diagnostics == ()
        assert len(assembly.assembled_specifications) == 3
        assert all(isinstance(item, AssembledSpecification) for item in assembly.assembled_specifications)
        checks["successful_batch"] = True

        mixed = assemble_batch(_mixed_batch(), context, ASSEMBLY_VERSION)
        assert mixed.success is False
        assert mixed.total_compilations == 4
        assert len(mixed.assembled_specifications) == 3
        assert len(mixed.failed_program_ids) == 1
        assert any("SKIPPED_FAILED_COMPILATION" in diagnostic for diagnostic in mixed.diagnostics)
        assert any("COMPILATION_FAILED" in diagnostic for diagnostic in mixed.diagnostics)
        checks["partial_failure"] = True

        expected_checksums = tuple(
            result.observation_checksum for result in successful_batch.successful_results
        )
        assembled_checksums = tuple(
            item.specification.parameters["observation_checksum"]
            for item in assembly.assembled_specifications
        )
        assert assembled_checksums == expected_checksums
        assert tuple(
            item.compiled_observations is result.observations
            for item, result in zip(assembly.assembled_specifications, successful_batch.successful_results)
        ) == (True, True, True)
        checks["ordering_preserved"] = True

        for assembled in assembly.assembled_specifications:
            geometry_parameters = assembled.specification.geometry_parameters
            assert geometry_parameters["spacing"] == context.spacing
            assert geometry_parameters["zone_half_width"] == context.zone_half_width
            assert geometry_parameters["active_window"] == context.active_window
            assert geometry_parameters["symbol"] == context.symbol
            assert geometry_parameters["market_timestamp"] == context.market_timestamp
            assert geometry_parameters["session_id"] == context.session_id
        checks["runner_ready_geometry"] = True

        repeat = assemble_batch(_success_batch(), context, ASSEMBLY_VERSION)
        assert repeat == assembly
        assert repeat.batch_assembly_fingerprint == assembly.batch_assembly_fingerprint
        mixed_repeat = assemble_batch(_mixed_batch(), context, ASSEMBLY_VERSION)
        assert mixed_repeat == mixed
        assert mixed.batch_assembly_fingerprint != assembly.batch_assembly_fingerprint
        alternate_context = replace(context, session_id="PHASE2C_BATCH_ASSEMBLER_ALT_SESSION")
        alternate = assemble_batch(successful_batch, alternate_context, ASSEMBLY_VERSION)
        assert alternate.batch_assembly_fingerprint != assembly.batch_assembly_fingerprint
        checks["fingerprint_determinism"] = True

        if os.environ.get("BATCH_ASSEMBLER_CHILD") == "1":
            return {
                "child_success_fingerprint": assembly.batch_assembly_fingerprint,
                "child_mixed_fingerprint": mixed.batch_assembly_fingerprint,
                "result": "PASS",
            }
        env = dict(os.environ)
        env["BATCH_ASSEMBLER_CHILD"] = "1"
        first = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
        second = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
        assert first == second
        checks["cross_process_determinism"] = True

        for module_path in MODULES:
            source = module_path.read_text(encoding="utf-8").lower()
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
    if os.environ.get("BATCH_ASSEMBLER_CHILD") == "1":
        print(f"success={report['child_success_fingerprint']}")
        print(f"mixed={report['child_mixed_fingerprint']}")
        print(f"result={report['result']}")
        if report["result"] != "PASS":
            raise SystemExit(1)
        return
    for field in (
        "successful_batch",
        "partial_failure",
        "ordering_preserved",
        "runner_ready_geometry",
        "fingerprint_determinism",
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
"""PHASE2C_SMALL_BATCH_EXECUTION_PROOF.

End-to-end proof that a small, deterministically generated batch of grammar
scenarios flows through the full, existing Project 2 pipeline:

Generation -> Manifest Validation -> Batch Compilation -> Batch Specification
Assembly -> Batch Execution -> real Scenario Runner -> Stage 1-6.

Every stage is the existing, already-audited implementation, called exactly
as it is meant to be called from outside the scenario_generation package.
Nothing here modifies the Runner, Catalog, Stage 1-6, the compiler, or
Project 1 -- this file only orchestrates calls and asserts on their output.
"""

from __future__ import annotations

import os
import subprocess
import sys
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
    ZoneSide,
)
from experiments.psychological_levels_dynamic.scenario_generation.batch_compiler import (
    compile_generation_batch,
)
from experiments.psychological_levels_dynamic.scenario_generation.batch_execution import (
    execute_batch,
)
from experiments.psychological_levels_dynamic.scenario_generation.batch_specification_assembler import (
    assemble_batch,
)
from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    GrammarTemplate,
    ParameterAxis,
    PhraseSlot,
)
from experiments.psychological_levels_dynamic.scenario_generation.execution_contracts import (
    BatchExecutionResult,
)
from experiments.psychological_levels_dynamic.scenario_generation.generator import (
    generate_programs,
)
from experiments.psychological_levels_dynamic.scenario_generation.manifest_validation import (
    validate_manifest,
)
from experiments.psychological_levels_dynamic.scenario_generation.runner_execution_context import (
    RunnerExecutionContext,
)

MODULE_PATH = Path(__file__)
FORBIDDEN_IMPORTS = (
    "scenario_catalog.catalog",
    "scenario_catalog.families",
    "scenario_runner",
    "scenario_registry",
    "core.",
    "engines.",
    "research.",
    "random",
)

GENERATOR_VERSION = "PHASE2C_SMALL_BATCH_PROOF_GENERATOR_V1"
VALIDATOR_VERSION = "PHASE2C_SMALL_BATCH_PROOF_VALIDATOR_V1"
COMPILER_VERSION = "PHASE2C_SMALL_BATCH_PROOF_COMPILER_V1"
BATCH_COMPILER_VERSION = "PHASE2C_SMALL_BATCH_PROOF_BATCH_COMPILER_V1"
ASSEMBLY_VERSION = "PHASE2C_SMALL_BATCH_PROOF_ASSEMBLY_V1"
EXECUTION_VERSION = "PHASE2C_SMALL_BATCH_PROOF_EXECUTION_V1"
RUNNER_VERSION = "PHASE2C_SMALL_BATCH_PROOF_RUNNER_V1"
VISIT_CYCLES = 6
ZONE_ID = "ZONE_A"
ZONE_CENTER = Decimal("60400")
ZONE_HALF_WIDTH = Decimal("25")
SPACING = Decimal("200")
CLEARANCE_VALUES = (
    Decimal("0.30"),
    Decimal("0.35"),
    Decimal("0.40"),
    Decimal("0.45"),
    Decimal("0.50"),
    Decimal("0.55"),
    Decimal("0.60"),
)


def _template() -> GrammarTemplate:
    """VISIT_CYCLES repeats of (dwell inside ZONE_A, hold well outside it).

    Every combination shares the same 6-cycle in/out structure -- only the
    outside clearance varies -- so each of the CLEARANCE_VALUES combinations
    independently produces multiple completed visits, matching the pattern
    already proven in PHASE2A (a single in/out cycle only ever yields one
    completed visit and zero Stage 3/4 transitions, which would not
    meaningfully exercise Stage 3-6).
    """

    slots: list[PhraseSlot] = []
    for _ in range(VISIT_CYCLES):
        slots.append(
            PhraseSlot(
                constructor_name="hold",
                fixed_params=(
                    ("row_budget", 2),
                    ("position", RelativePosition.CENTER),
                    ("target_zone", ZONE_ID),
                ),
                axis_bound_params=(),
            )
        )
        slots.append(
            PhraseSlot(
                constructor_name="hold_outside",
                fixed_params=(
                    ("row_budget", 5),
                    ("target_zone", ZONE_ID),
                    ("side", ZoneSide.UPPER),
                ),
                axis_bound_params=(("clearance", "zone_clearance"),),
            )
        )
    return GrammarTemplate(
        template_id="SMALL_BATCH_PROOF_TEMPLATE",
        template_version="1",
        family_tag="SMALL_BATCH_PROOF",
        description=(
            "Deterministic small batch: repeated center-dwell / hold-outside "
            "cycles with a varying outside clearance, one completed-visit "
            "scenario per clearance value."
        ),
        phrase_slots=tuple(slots),
        axes=(ParameterAxis("zone_clearance", CLEARANCE_VALUES),),
        rules=(),
    )


def _geometry_context() -> GeometryContext:
    return GeometryContext(
        symbol="BTCUSDT",
        geometry_version="PHASE2C_SMALL_BATCH_PROOF_GEOMETRY_V1",
        references=(
            GeometryReference(
                zone_id=ZONE_ID,
                center_price=ZONE_CENTER,
                lower_price=ZONE_CENTER - ZONE_HALF_WIDTH,
                upper_price=ZONE_CENTER + ZONE_HALF_WIDTH,
                half_width=ZONE_HALF_WIDTH,
            ),
        ),
    )


def _execution_context() -> RunnerExecutionContext:
    return RunnerExecutionContext(
        symbol="BTCUSDT",
        geometry_context=_geometry_context(),
        active_window=0,
        spacing=SPACING,
        zone_half_width=ZONE_HALF_WIDTH,
        market_timestamp=1_700_000_000_000,
        session_id="PHASE2C_SMALL_BATCH_PROOF_SESSION",
        runner_version=RUNNER_VERSION,
    )


def _run_pipeline() -> dict[str, Any]:
    generation = generate_programs(_template(), GENERATOR_VERSION)
    if not generation.success:
        raise AssertionError(f"generation failed: {generation.diagnostics}")

    validation = validate_manifest(generation.manifest, VALIDATOR_VERSION)
    if not validation.success:
        raise AssertionError(f"manifest validation failed: {validation.diagnostics}")

    geometry_context = _geometry_context()
    compilation = compile_generation_batch(
        generation, geometry_context, COMPILER_VERSION, BATCH_COMPILER_VERSION
    )
    if not compilation.success:
        raise AssertionError(f"batch compilation failed: {compilation.diagnostics}")

    execution_context = _execution_context()
    assembly = assemble_batch(compilation, execution_context, ASSEMBLY_VERSION)
    if not assembly.success:
        raise AssertionError(f"batch assembly failed: {assembly.diagnostics}")

    execution = execute_batch(
        assembly.assembled_specifications,
        execution_context,
        EXECUTION_VERSION,
        source_manifest_fingerprint=generation.manifest.manifest_fingerprint,
        batch_compilation_fingerprint=compilation.batch_compilation_fingerprint,
        batch_assembly_fingerprint=assembly.batch_assembly_fingerprint,
    )
    return {
        "generation": generation,
        "validation": validation,
        "compilation": compilation,
        "assembly": assembly,
        "execution": execution,
    }


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "generated_5_to_10_scenarios": False,
        "manifest_validated": False,
        "batch_compiled": False,
        "specifications_assembled": False,
        "batch_executed": False,
        "ordering_preserved": False,
        "pass_fail_stored": False,
        "stage_summaries_present": False,
        "stage4_summary_present": False,
        "provenance_fingerprints_propagated": False,
        "determinism_confirmed": False,
        "cross_process_determinism": False,
        "research_isolation": False,
    }
    try:
        pipeline = _run_pipeline()
        generation = pipeline["generation"]
        validation = pipeline["validation"]
        compilation = pipeline["compilation"]
        assembly = pipeline["assembly"]
        execution: BatchExecutionResult = pipeline["execution"]
        total = len(generation.generated_programs)

        assert 5 <= total <= 10
        checks["generated_5_to_10_scenarios"] = True

        assert validation.success is True
        assert validation.diagnostics == ()
        checks["manifest_validated"] = True

        assert compilation.success is True
        assert compilation.compiled_programs == total
        assert compilation.failed_programs == 0
        checks["batch_compiled"] = True

        assert assembly.success is True
        assert len(assembly.assembled_specifications) == total
        checks["specifications_assembled"] = True

        assert isinstance(execution, BatchExecutionResult)
        assert execution.total_scenarios == total
        assert execution.executed_scenarios == total
        assert execution.failed_scenarios == 0
        assert execution.skipped_scenarios == 0
        checks["batch_executed"] = True

        for index in range(total):
            record = execution.scenario_results[index]
            assembled_spec = assembly.assembled_specifications[index].specification
            assert record.scenario_index == index
            assert record.specification_fingerprint == assembled_spec.specification_fingerprint
        checks["ordering_preserved"] = True

        assert all(
            record.runner_result in {"PASS", "FAIL"} for record in execution.scenario_results
        )
        assert execution.success is True
        assert execution.failed_scenario_ids == ()
        checks["pass_fail_stored"] = True

        for record in execution.scenario_results:
            result = record.scenario_run_result
            assert isinstance(result.stage3_transition_summary, dict)
            assert isinstance(result.stage4_graph_summary, dict)
            assert isinstance(result.stage5_trajectory_summary, dict)
            assert isinstance(result.stage6_hypothesis_summary, dict)
            assert result.completed_visits > 0
        checks["stage_summaries_present"] = True

        for record in execution.scenario_results:
            summary = dict(record.summary)
            assert "stage4_transitions_generated" in summary
            assert summary["stage4_transitions_generated"] is not None
            assert summary["stage4_transitions_generated"] == (
                record.scenario_run_result.stage4_graph_summary["transitions_generated"]
            )
        checks["stage4_summary_present"] = True

        assert execution.source_manifest_fingerprint == generation.manifest.manifest_fingerprint
        assert execution.batch_compilation_fingerprint == compilation.batch_compilation_fingerprint
        assert execution.batch_assembly_fingerprint == assembly.batch_assembly_fingerprint
        assert execution.batch_execution_fingerprint.startswith("sha256:")
        checks["provenance_fingerprints_propagated"] = True

        repeat_pipeline = _run_pipeline()
        repeat_generation = repeat_pipeline["generation"]
        repeat_compilation = repeat_pipeline["compilation"]
        repeat_assembly = repeat_pipeline["assembly"]
        repeat_execution: BatchExecutionResult = repeat_pipeline["execution"]
        assert repeat_generation.manifest.manifest_fingerprint == generation.manifest.manifest_fingerprint
        assert repeat_compilation.batch_compilation_fingerprint == compilation.batch_compilation_fingerprint
        assert repeat_assembly.batch_assembly_fingerprint == assembly.batch_assembly_fingerprint
        assert repeat_execution == execution
        assert repeat_execution.batch_execution_fingerprint == execution.batch_execution_fingerprint
        checks["determinism_confirmed"] = True

        if os.environ.get("SMALL_BATCH_PROOF_CHILD") == "1":
            return {
                "batch_execution_fingerprint": execution.batch_execution_fingerprint,
                "batch_compilation_fingerprint": compilation.batch_compilation_fingerprint,
                "batch_assembly_fingerprint": assembly.batch_assembly_fingerprint,
                "manifest_fingerprint": generation.manifest.manifest_fingerprint,
                "result": "PASS",
            }
        env = dict(os.environ)
        env["SMALL_BATCH_PROOF_CHILD"] = "1"
        child_one = subprocess.check_output([sys.executable, str(MODULE_PATH)], text=True, env=env)
        child_two = subprocess.check_output([sys.executable, str(MODULE_PATH)], text=True, env=env)
        assert child_one == child_two
        checks["cross_process_determinism"] = True

        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        assert not any(token in imports for token in FORBIDDEN_IMPORTS)
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    if os.environ.get("SMALL_BATCH_PROOF_CHILD") == "1":
        print(f"batch_execution_fingerprint={report.get('batch_execution_fingerprint')}")
        print(f"batch_compilation_fingerprint={report.get('batch_compilation_fingerprint')}")
        print(f"batch_assembly_fingerprint={report.get('batch_assembly_fingerprint')}")
        print(f"manifest_fingerprint={report.get('manifest_fingerprint')}")
        print(f"result={report.get('result')}")
        if report.get("result") != "PASS":
            raise SystemExit(1)
        return
    for field in (
        "generated_5_to_10_scenarios",
        "manifest_validated",
        "batch_compiled",
        "specifications_assembled",
        "batch_executed",
        "ordering_preserved",
        "pass_fail_stored",
        "stage_summaries_present",
        "stage4_summary_present",
        "provenance_fingerprints_propagated",
        "determinism_confirmed",
        "cross_process_determinism",
        "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)
    print()
    print("PHASE2C_SMALL_BATCH_EXECUTION_PROOF PASS")


if __name__ == "__main__":
    main()

"""Deterministic 10-scenario stability campaign for Project 2 batch execution."""

from __future__ import annotations

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
from experiments.psychological_levels_dynamic.scenario_generation.generator import (
    generate_programs,
)
from experiments.psychological_levels_dynamic.scenario_generation.manifest_validation import (
    validate_manifest,
)
from experiments.psychological_levels_dynamic.scenario_generation.runner_execution_context import (
    RunnerExecutionContext,
)

COMPILER_VERSION = "PHASE2C_STABILITY_10_COMPILER_V1"
BATCH_COMPILER_VERSION = "PHASE2C_STABILITY_10_BATCH_COMPILER_V1"
ASSEMBLY_VERSION = "PHASE2C_STABILITY_10_ASSEMBLY_V1"
BATCH_EXECUTION_VERSION = "PHASE2C_STABILITY_10_EXECUTION_V1"
GENERATOR_VERSION = "PHASE2C_STABILITY_10_GENERATOR_V1"
VALIDATOR_VERSION = "PHASE2C_STABILITY_10_VALIDATOR_V1"
EXPECTED_SCENARIOS = 10


def _geometry_context() -> GeometryContext:
    center = Decimal("60400")
    half_width = Decimal("25")
    return GeometryContext(
        symbol="BTCUSDT",
        geometry_version="PHASE2C_STABILITY_10_GEOMETRY_V1",
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
        session_id="PHASE2C_SMALL_BATCH_STABILITY_10_SESSION",
        runner_version="PHASE2C_STABILITY_10_RUNNER_V1",
    )


def _template() -> GrammarTemplate:
    return GrammarTemplate(
        template_id="STABILITY_10_CENTER_EXIT_TEMPLATE",
        template_version="1",
        family_tag="STABILITY_10_CENTER_EXIT",
        description="Ten deterministic center/external-lull interaction variants.",
        phrase_slots=(
            PhraseSlot(
                constructor_name="hold",
                fixed_params=(
                    ("position", RelativePosition.CENTER),
                    ("target_zone", "ZONE_A"),
                ),
                axis_bound_params=(("row_budget", "center_rows"),),
            ),
            PhraseSlot(
                constructor_name="hold_outside",
                fixed_params=(
                    ("target_zone", "ZONE_A"),
                    ("side", ZoneSide.UPPER),
                    ("clearance", Decimal("5")),
                ),
                axis_bound_params=(("row_budget", "outside_rows"),),
            ),
        ),
        axes=(
            ParameterAxis("center_rows", (2, 3, 4, 5, 6)),
            ParameterAxis("outside_rows", (4, 5)),
        ),
        rules=(),
    )


def _run_pipeline():
    generation = generate_programs(_template(), GENERATOR_VERSION)
    assert generation.success is True
    assert generation.manifest is not None
    assert len(generation.generated_programs) == EXPECTED_SCENARIOS

    manifest_validation = validate_manifest(generation.manifest, VALIDATOR_VERSION)
    assert manifest_validation.success is True

    compilation = compile_generation_batch(
        generation,
        _geometry_context(),
        COMPILER_VERSION,
        BATCH_COMPILER_VERSION,
    )
    assert compilation.success is True
    assert compilation.total_programs == EXPECTED_SCENARIOS
    assert compilation.compiled_programs == EXPECTED_SCENARIOS

    execution_context = _execution_context()
    assembly = assemble_batch(compilation, execution_context, ASSEMBLY_VERSION)
    assert assembly.success is True
    assert len(assembly.assembled_specifications) == EXPECTED_SCENARIOS

    execution = execute_batch(
        assembly.assembled_specifications,
        execution_context,
        BATCH_EXECUTION_VERSION,
        source_manifest_fingerprint=generation.manifest.manifest_fingerprint,
        batch_compilation_fingerprint=compilation.batch_compilation_fingerprint,
        batch_assembly_fingerprint=assembly.batch_assembly_fingerprint,
    )
    return generation, manifest_validation, compilation, assembly, execution


def _execution_summary(execution) -> tuple[tuple[str, Any], ...]:
    return tuple(
        (
            record.scenario_id,
            record.scenario_index,
            record.execution_status,
            record.runner_result,
            record.summary,
            record.execution_fingerprint,
        )
        for record in execution.scenario_results
    )


def _stage_payloads(execution) -> tuple[tuple[Any, Any, Any, Any], ...]:
    return tuple(
        (
            record.scenario_run_result.stage3_transition_summary,
            record.scenario_run_result.stage4_graph_summary,
            record.scenario_run_result.stage5_trajectory_summary,
            record.scenario_run_result.stage6_hypothesis_summary,
        )
        for record in execution.scenario_results
    )


def _campaign_summary(execution) -> dict[str, Any]:
    pass_count = sum(1 for record in execution.scenario_results if record.runner_result == "PASS")
    fail_count = sum(1 for record in execution.scenario_results if record.runner_result == "FAIL")
    return {
        "scenarios_generated": EXPECTED_SCENARIOS,
        "scenarios_executed": execution.executed_scenarios,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "skipped_count": execution.skipped_scenarios,
        "deterministic_fingerprints": tuple(record.execution_fingerprint for record in execution.scenario_results),
        "batch_execution_fingerprint": execution.batch_execution_fingerprint,
        "execution_duration": None,
    }


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "generated_exactly_10": False,
        "not_identical": False,
        "executed_twice": False,
        "identical_ordering": False,
        "identical_execution_summaries": False,
        "identical_stage_outputs": False,
        "identical_fingerprints": False,
        "identical_batch_fingerprints": False,
        "identical_provenance": False,
        "no_cross_scenario_contamination": False,
        "pass_fail_storage": False,
        "campaign_summary": False,
        "research_isolation": False,
    }
    try:
        generation, manifest_validation, compilation, assembly, execution = _run_pipeline()
        second_generation, second_validation, second_compilation, second_assembly, second_execution = _run_pipeline()
        checks["generated_exactly_10"] = len(generation.generated_programs) == EXPECTED_SCENARIOS
        checks["executed_twice"] = execution.total_scenarios == EXPECTED_SCENARIOS and second_execution.total_scenarios == EXPECTED_SCENARIOS

        observation_checksums = tuple(
            result.observation_checksum for result in compilation.successful_results
        )
        specification_fingerprints = tuple(
            assembled.specification.specification_fingerprint for assembled in assembly.assembled_specifications
        )
        checks["not_identical"] = len(set(observation_checksums)) == EXPECTED_SCENARIOS and len(set(specification_fingerprints)) == EXPECTED_SCENARIOS

        first_ordering = tuple(record.scenario_id for record in execution.scenario_results)
        second_ordering = tuple(record.scenario_id for record in second_execution.scenario_results)
        checks["identical_ordering"] = first_ordering == second_ordering

        checks["identical_execution_summaries"] = _execution_summary(execution) == _execution_summary(second_execution)
        checks["identical_stage_outputs"] = _stage_payloads(execution) == _stage_payloads(second_execution)
        checks["identical_fingerprints"] = tuple(record.execution_fingerprint for record in execution.scenario_results) == tuple(
            record.execution_fingerprint for record in second_execution.scenario_results
        )
        checks["identical_batch_fingerprints"] = execution.batch_execution_fingerprint == second_execution.batch_execution_fingerprint
        checks["identical_provenance"] = (
            generation.generation_fingerprint == second_generation.generation_fingerprint
            and manifest_validation.validation_fingerprint == second_validation.validation_fingerprint
            and compilation.batch_compilation_fingerprint == second_compilation.batch_compilation_fingerprint
            and assembly.batch_assembly_fingerprint == second_assembly.batch_assembly_fingerprint
            and execution.source_manifest_fingerprint == generation.manifest.manifest_fingerprint
            and execution.batch_compilation_fingerprint == compilation.batch_compilation_fingerprint
            and execution.batch_assembly_fingerprint == assembly.batch_assembly_fingerprint
            and second_execution.source_manifest_fingerprint == second_generation.manifest.manifest_fingerprint
            and second_execution.batch_compilation_fingerprint == second_compilation.batch_compilation_fingerprint
            and second_execution.batch_assembly_fingerprint == second_assembly.batch_assembly_fingerprint
        )

        checks["no_cross_scenario_contamination"] = (
            tuple(record.scenario_id for record in execution.scenario_results) == tuple(
                assembled.specification.scenario_id for assembled in assembly.assembled_specifications
            )
            and len(set(record.scenario_id for record in execution.scenario_results)) == EXPECTED_SCENARIOS
            and len(set(record.execution_fingerprint for record in execution.scenario_results)) == EXPECTED_SCENARIOS
            and all(record.scenario_run_result.scenario_id == record.scenario_id for record in execution.scenario_results)
        )
        checks["pass_fail_storage"] = all(
            record.execution_status == "EXECUTED" and record.runner_result in {"PASS", "FAIL"}
            for record in execution.scenario_results
        )

        summary = _campaign_summary(execution)
        checks["campaign_summary"] = (
            summary["scenarios_generated"] == EXPECTED_SCENARIOS
            and summary["scenarios_executed"] == EXPECTED_SCENARIOS
            and summary["pass_count"] + summary["fail_count"] == EXPECTED_SCENARIOS
            and summary["skipped_count"] == 0
            and len(summary["deterministic_fingerprints"]) == EXPECTED_SCENARIOS
            and summary["batch_execution_fingerprint"] == execution.batch_execution_fingerprint
            and "execution_duration" in summary
        )

        source = Path(__file__).read_text(encoding="utf-8").lower()
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        checks["research_isolation"] = not any(token in imports for token in ("core.", "engines.", "research."))
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    for field in (
        "generated_exactly_10",
        "not_identical",
        "executed_twice",
        "identical_ordering",
        "identical_execution_summaries",
        "identical_stage_outputs",
        "identical_fingerprints",
        "identical_batch_fingerprints",
        "identical_provenance",
        "no_cross_scenario_contamination",
        "pass_fail_storage",
        "campaign_summary",
        "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)
    print("PHASE2C_SMALL_BATCH_STABILITY_10 PASS")


if __name__ == "__main__":
    main()
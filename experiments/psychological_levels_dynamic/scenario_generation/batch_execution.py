"""Serial batch execution for already assembled compiled scenarios.

Uses the existing Scenario Runner exactly as-is. No compiler, catalog execution,
cross-scenario analysis or optimization logic lives here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from experiments.psychological_levels_dynamic.scenario_contract import (
    PriceObservation,
    ScenarioProviderMetadata,
    ScenarioSpecification,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.specification_assembler import (
    AssembledSpecification,
)
from experiments.psychological_levels_dynamic.scenario_generation.execution_contracts import (
    BatchExecutionResult,
    ScenarioExecutionRecord,
    execution_contract_fingerprint,
)
from experiments.psychological_levels_dynamic.scenario_generation.runner_execution_context import (
    RunnerExecutionContext,
)
from experiments.psychological_levels_dynamic.scenario_registry import ScenarioRegistry
from experiments.psychological_levels_dynamic.scenario_runner import (
    ScenarioRunResult,
    run_scenario,
)

BATCH_EXECUTION_VERSION = "PHASE2C_BATCH_EXECUTION_V1"
PROVIDER_VERSION = "PHASE2C_COMPILED_OBSERVATION_REPLAY_PROVIDER_V1"


@dataclass(frozen=True)
class _CompiledObservationProvider:
    specification: ScenarioSpecification
    observations: tuple[PriceObservation, ...]

    def metadata(self) -> ScenarioProviderMetadata:
        return ScenarioProviderMetadata(
            scenario_family=self.specification.scenario_family,
            provider_version=PROVIDER_VERSION,
            schema_version=self.specification.schema_version,
            price_only=True,
            research_only=True,
        )

    def validate_spec(self, spec: ScenarioSpecification) -> None:
        if spec != self.specification:
            raise ValueError("provider received unexpected ScenarioSpecification")
        if spec.row_count != len(self.observations):
            raise ValueError("compiled observation count does not match specification.row_count")
        if not self.observations:
            raise ValueError("compiled observations must not be empty")
        if self.observations[0].price != spec.start_price:
            raise ValueError("first compiled observation does not match specification.start_price")

    def generate(self, spec: ScenarioSpecification) -> Sequence[PriceObservation]:
        self.validate_spec(spec)
        return self.observations


def _summary_value(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def _compact_summary(result: ScenarioRunResult) -> tuple[tuple[str, Any], ...]:
    stage3 = result.stage3_transition_summary
    stage5 = result.stage5_trajectory_summary
    stage6 = result.stage6_hypothesis_summary
    return (
        ("completed_visits", result.completed_visits),
        ("zones_observed", result.zones_observed),
        ("transitions_generated", _summary_value(stage3, "transitions_generated")),
        ("trajectory_records", _summary_value(stage5, "trajectory_records")),
        ("eligible_hypotheses", _summary_value(stage6, "eligible_hypotheses")),
        ("confirmed_hypotheses", _summary_value(stage6, "confirmed_hypotheses")),
        ("pending_hypotheses", _summary_value(stage6, "pending_hypotheses")),
        ("runner_result", result.result),
    )


def _record_fingerprint(
    *,
    scenario_id: str,
    scenario_index: int,
    specification_fingerprint: str,
    execution_status: str,
    runner_result: str | None,
    summary: tuple[tuple[str, Any], ...],
    diagnostics: tuple[str, ...],
) -> str:
    return execution_contract_fingerprint(
        (
            scenario_id,
            scenario_index,
            specification_fingerprint,
            execution_status,
            runner_result,
            summary,
            diagnostics,
        )
    )


def _batch_fingerprint(
    *,
    scenario_results: tuple[ScenarioExecutionRecord, ...],
    diagnostics: tuple[str, ...],
    runner_version: str,
    batch_execution_version: str,
) -> str:
    return execution_contract_fingerprint(
        (
            tuple(record.execution_fingerprint for record in scenario_results),
            diagnostics,
            runner_version,
            batch_execution_version,
        )
    )


def _execute_one(
    assembled: AssembledSpecification,
    scenario_index: int,
) -> ScenarioExecutionRecord:
    spec = assembled.specification
    try:
        registry = ScenarioRegistry()
        registry.register(_CompiledObservationProvider(spec, assembled.compiled_observations))
        result = run_scenario(registry, spec)
        summary = _compact_summary(result)
        diagnostics: tuple[str, ...] = ()
        return ScenarioExecutionRecord(
            scenario_id=spec.scenario_id,
            scenario_index=scenario_index,
            specification_fingerprint=spec.specification_fingerprint,
            execution_status="EXECUTED",
            scenario_run_result=result,
            runner_result=result.result,
            summary=summary,
            diagnostics=diagnostics,
            execution_fingerprint=_record_fingerprint(
                scenario_id=spec.scenario_id,
                scenario_index=scenario_index,
                specification_fingerprint=spec.specification_fingerprint,
                execution_status="EXECUTED",
                runner_result=result.result,
                summary=summary,
                diagnostics=diagnostics,
            ),
        )
    except Exception as exc:
        diagnostics = (f"SCENARIO_EXECUTION_FAILED:{type(exc).__name__}:{exc}",)
        summary = (("runner_result", "NOT_AVAILABLE"),)
        return ScenarioExecutionRecord(
            scenario_id=spec.scenario_id,
            scenario_index=scenario_index,
            specification_fingerprint=spec.specification_fingerprint,
            execution_status="FAILED",
            scenario_run_result=None,
            runner_result=None,
            summary=summary,
            diagnostics=diagnostics,
            execution_fingerprint=_record_fingerprint(
                scenario_id=spec.scenario_id,
                scenario_index=scenario_index,
                specification_fingerprint=spec.specification_fingerprint,
                execution_status="FAILED",
                runner_result=None,
                summary=summary,
                diagnostics=diagnostics,
            ),
        )


def execute_batch(
    assembled_specifications: tuple[AssembledSpecification, ...],
    execution_context: RunnerExecutionContext,
    batch_execution_version: str = BATCH_EXECUTION_VERSION,
) -> BatchExecutionResult:
    if not isinstance(assembled_specifications, tuple):
        raise TypeError("assembled_specifications must be tuple")
    if not all(isinstance(value, AssembledSpecification) for value in assembled_specifications):
        raise TypeError("assembled_specifications must contain AssembledSpecification values")
    if not isinstance(execution_context, RunnerExecutionContext):
        raise TypeError("execution_context must be RunnerExecutionContext")
    if not batch_execution_version.strip():
        raise ValueError("batch_execution_version must not be empty")

    records = tuple(
        _execute_one(assembled, index)
        for index, assembled in enumerate(assembled_specifications)
    )
    failed_scenario_ids = tuple(
        record.scenario_id for record in records if record.execution_status == "FAILED"
    )
    skipped_scenario_ids: tuple[str, ...] = ()
    executed_scenarios = sum(1 for record in records if record.execution_status == "EXECUTED")
    failed_scenarios = len(failed_scenario_ids)
    skipped_scenarios = 0
    diagnostics = tuple(
        diagnostic
        for record in records
        for diagnostic in record.diagnostics
    )
    if any(record.execution_status == "EXECUTED" and record.runner_result == "FAIL" for record in records):
        diagnostics = diagnostics + ("BATCH_HAS_EXECUTED_RUNNER_FAIL",)
    success = not failed_scenarios and not skipped_scenarios and not diagnostics
    batch_fingerprint = _batch_fingerprint(
        scenario_results=records,
        diagnostics=diagnostics,
        runner_version=execution_context.runner_version,
        batch_execution_version=batch_execution_version,
    )
    return BatchExecutionResult(
        success=success,
        total_scenarios=len(records),
        executed_scenarios=executed_scenarios,
        failed_scenarios=failed_scenarios,
        skipped_scenarios=skipped_scenarios,
        scenario_results=records,
        failed_scenario_ids=failed_scenario_ids,
        skipped_scenario_ids=skipped_scenario_ids,
        diagnostics=diagnostics,
        source_manifest_fingerprint=None,
        batch_compilation_fingerprint=None,
        batch_assembly_fingerprint=None,
        batch_execution_fingerprint=batch_fingerprint,
        runner_version=execution_context.runner_version,
        batch_execution_version=batch_execution_version,
    )
"""Thin Project 2 campaign designer orchestration.

Runs the existing per-family Project 2 pipeline. It does not change generation,
compiler, runner, catalog, Stage 1-6, Project 1, or production behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from experiments.psychological_levels_dynamic.scenario_generation.batch_compiler import (
    BATCH_COMPILER_VERSION,
    BatchCompilationResult,
    compile_generation_batch,
)
from experiments.psychological_levels_dynamic.scenario_generation.batch_execution import (
    BATCH_EXECUTION_VERSION,
    execute_batch,
)
from experiments.psychological_levels_dynamic.scenario_generation.batch_specification_assembler import (
    BATCH_SPECIFICATION_ASSEMBLER_VERSION,
    BatchAssemblyResult,
    assemble_batch,
)
from experiments.psychological_levels_dynamic.scenario_generation.campaign_contracts import (
    CampaignFamilyResult,
    CampaignFamilySpec,
    CampaignResult,
    CampaignSpecification,
    campaign_result_fingerprint_payload,
)
from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    generation_contract_fingerprint,
)
from experiments.psychological_levels_dynamic.scenario_generation.generator import (
    GENERATOR_VERSION,
    GenerationResult,
    generate_programs,
)
from experiments.psychological_levels_dynamic.scenario_generation.manifest_validation import (
    VALIDATOR_VERSION,
    ManifestValidationResult,
    validate_manifest,
)
from experiments.psychological_levels_dynamic.scenario_generation.runner_execution_context import (
    RunnerExecutionContext,
)

CAMPAIGN_DESIGNER_VERSION = "PHASE2D_CAMPAIGN_DESIGNER_LOGIC_V1"
CAMPAIGN_COMPILER_VERSION = "PHASE2D_CAMPAIGN_DESIGNER_COMPILER_V1"


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_tuple(name: str, value: tuple[object, ...]) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{name} must be tuple")


def _require_fingerprint(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        raise ValueError(f"{name} must be SHA-256")


@dataclass(frozen=True)
class CampaignFamilyExecutionPayload:
    family_name: str
    coverage_tags: tuple[str, ...]
    generation_result: GenerationResult
    manifest_validation_result: ManifestValidationResult | None
    batch_compilation_result: BatchCompilationResult | None
    batch_assembly_result: BatchAssemblyResult | None
    batch_execution_result: Any | None
    family_pipeline_fingerprint: str
    diagnostics: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_non_empty("family_name", self.family_name)
        _require_tuple("coverage_tags", self.coverage_tags)
        if not all(isinstance(value, str) and value.strip() for value in self.coverage_tags):
            raise ValueError("coverage_tags must contain non-empty strings")
        if not isinstance(self.generation_result, GenerationResult):
            raise TypeError("generation_result must be GenerationResult")
        if self.manifest_validation_result is not None and not isinstance(self.manifest_validation_result, ManifestValidationResult):
            raise TypeError("manifest_validation_result must be ManifestValidationResult or None")
        if self.batch_compilation_result is not None and not isinstance(self.batch_compilation_result, BatchCompilationResult):
            raise TypeError("batch_compilation_result must be BatchCompilationResult or None")
        if self.batch_assembly_result is not None and not isinstance(self.batch_assembly_result, BatchAssemblyResult):
            raise TypeError("batch_assembly_result must be BatchAssemblyResult or None")
        _require_fingerprint("family_pipeline_fingerprint", self.family_pipeline_fingerprint)
        _require_tuple("diagnostics", self.diagnostics)
        if not all(isinstance(value, str) for value in self.diagnostics):
            raise TypeError("diagnostics must contain strings")


@dataclass(frozen=True)
class CampaignDesignerResult:
    success: bool
    campaign_specification: CampaignSpecification
    campaign_result: CampaignResult
    family_execution_payloads: tuple[CampaignFamilyExecutionPayload, ...]
    campaign_designer_fingerprint: str
    campaign_designer_version: str
    diagnostics: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")
        if not isinstance(self.campaign_specification, CampaignSpecification):
            raise TypeError("campaign_specification must be CampaignSpecification")
        if not isinstance(self.campaign_result, CampaignResult):
            raise TypeError("campaign_result must be CampaignResult")
        _require_tuple("family_execution_payloads", self.family_execution_payloads)
        if not all(isinstance(value, CampaignFamilyExecutionPayload) for value in self.family_execution_payloads):
            raise TypeError("family_execution_payloads must contain CampaignFamilyExecutionPayload values")
        if tuple(payload.family_name for payload in self.family_execution_payloads) != tuple(
            family.family_name for family in self.campaign_specification.families
        ):
            raise ValueError("family_execution_payloads must preserve campaign family ordering")
        if self.success != self.campaign_result.success:
            raise ValueError("success must mirror campaign_result.success")
        _require_fingerprint("campaign_designer_fingerprint", self.campaign_designer_fingerprint)
        _require_non_empty("campaign_designer_version", self.campaign_designer_version)
        _require_tuple("diagnostics", self.diagnostics)
        if not all(isinstance(value, str) for value in self.diagnostics):
            raise TypeError("diagnostics must contain strings")


def _pipeline_fingerprint(
    *,
    family_name: str,
    coverage_tags: tuple[str, ...],
    generation_result: GenerationResult,
    manifest_validation_result: ManifestValidationResult | None,
    batch_compilation_result: BatchCompilationResult | None,
    batch_assembly_result: BatchAssemblyResult | None,
    batch_execution_fingerprint: str | None,
    diagnostics: tuple[str, ...],
) -> str:
    return generation_contract_fingerprint(
        (
            family_name,
            coverage_tags,
            generation_result.generation_fingerprint,
            None if manifest_validation_result is None else manifest_validation_result.validation_fingerprint,
            None if batch_compilation_result is None else batch_compilation_result.batch_compilation_fingerprint,
            None if batch_assembly_result is None else batch_assembly_result.batch_assembly_fingerprint,
            batch_execution_fingerprint,
            diagnostics,
        )
    )


def _designer_fingerprint(
    *,
    campaign_specification: CampaignSpecification,
    campaign_result: CampaignResult,
    payloads: tuple[CampaignFamilyExecutionPayload, ...],
    diagnostics: tuple[str, ...],
    campaign_designer_version: str,
) -> str:
    return generation_contract_fingerprint(
        (
            campaign_specification.campaign_specification_fingerprint,
            campaign_result.campaign_fingerprint,
            tuple(payload.family_pipeline_fingerprint for payload in payloads),
            diagnostics,
            campaign_designer_version,
        )
    )


def _family_counts(
    *,
    generated_count: int,
    assembled_count: int,
    batch_execution_result: Any | None,
) -> tuple[int, int, int, int]:
    if batch_execution_result is None:
        return (0, 0, 0, generated_count)
    passed_count = sum(
        1
        for record in batch_execution_result.scenario_results
        if record.execution_status == "EXECUTED" and record.runner_result == "PASS"
    )
    executed_fail_count = sum(
        1
        for record in batch_execution_result.scenario_results
        if record.execution_status == "EXECUTED" and record.runner_result == "FAIL"
    )
    failed_count = batch_execution_result.failed_scenarios + executed_fail_count
    skipped_count = max(0, generated_count - assembled_count) + batch_execution_result.skipped_scenarios
    executed_count = passed_count + failed_count + skipped_count
    return executed_count, passed_count, failed_count, skipped_count


def _run_family(
    family: CampaignFamilySpec,
    execution_context: RunnerExecutionContext,
    *,
    generator_version: str,
    validator_version: str,
    compiler_version: str,
    batch_compiler_version: str,
    assembly_version: str,
    batch_execution_version: str,
) -> tuple[CampaignFamilyResult, CampaignFamilyExecutionPayload]:
    diagnostics: list[str] = []
    generation_result = generate_programs(family.template, generator_version)
    if len(generation_result.generated_programs) != family.target_count:
        diagnostics.append(
            f"FAMILY_TARGET_COUNT_MISMATCH:{family.family_name}:target={family.target_count}:generated={len(generation_result.generated_programs)}"
        )
    diagnostics.extend(generation_result.diagnostics)

    manifest_validation_result: ManifestValidationResult | None = None
    if generation_result.manifest is not None:
        manifest_validation_result = validate_manifest(generation_result.manifest, validator_version)
        diagnostics.extend(manifest_validation_result.diagnostics)
    else:
        diagnostics.append(f"FAMILY_GENERATION_WITHOUT_MANIFEST:{family.family_name}")

    batch_compilation_result: BatchCompilationResult | None = None
    batch_assembly_result: BatchAssemblyResult | None = None
    batch_execution_result = None
    if generation_result.success:
        batch_compilation_result = compile_generation_batch(
            generation_result,
            execution_context.geometry_context,
            compiler_version,
            batch_compiler_version,
        )
        diagnostics.extend(batch_compilation_result.diagnostics)
        batch_assembly_result = assemble_batch(
            batch_compilation_result,
            execution_context,
            assembly_version,
        )
        diagnostics.extend(batch_assembly_result.diagnostics)
        batch_execution_result = execute_batch(
            batch_assembly_result.assembled_specifications,
            execution_context,
            batch_execution_version,
            source_manifest_fingerprint=None if generation_result.manifest is None else generation_result.manifest.manifest_fingerprint,
            batch_compilation_fingerprint=batch_compilation_result.batch_compilation_fingerprint,
            batch_assembly_fingerprint=batch_assembly_result.batch_assembly_fingerprint,
        )
        diagnostics.extend(batch_execution_result.diagnostics)

    diagnostics_tuple = tuple(sorted(diagnostics))
    generated_count = len(generation_result.generated_programs)
    assembled_count = 0 if batch_assembly_result is None else len(batch_assembly_result.assembled_specifications)
    executed_count, passed_count, failed_count, skipped_count = _family_counts(
        generated_count=generated_count,
        assembled_count=assembled_count,
        batch_execution_result=batch_execution_result,
    )
    batch_execution_fingerprint = None if batch_execution_result is None else batch_execution_result.batch_execution_fingerprint
    family_result = CampaignFamilyResult(
        family_name=family.family_name,
        coverage_tags=family.coverage_tags,
        batch_execution_fingerprint=batch_execution_fingerprint,
        generated_count=generated_count,
        executed_count=executed_count,
        passed_count=passed_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
    )
    payload = CampaignFamilyExecutionPayload(
        family_name=family.family_name,
        coverage_tags=family.coverage_tags,
        generation_result=generation_result,
        manifest_validation_result=manifest_validation_result,
        batch_compilation_result=batch_compilation_result,
        batch_assembly_result=batch_assembly_result,
        batch_execution_result=batch_execution_result,
        family_pipeline_fingerprint=_pipeline_fingerprint(
            family_name=family.family_name,
            coverage_tags=family.coverage_tags,
            generation_result=generation_result,
            manifest_validation_result=manifest_validation_result,
            batch_compilation_result=batch_compilation_result,
            batch_assembly_result=batch_assembly_result,
            batch_execution_fingerprint=batch_execution_fingerprint,
            diagnostics=diagnostics_tuple,
        ),
        diagnostics=diagnostics_tuple,
    )
    return family_result, payload


def run_campaign(
    campaign_specification: CampaignSpecification,
    execution_context: RunnerExecutionContext,
    *,
    generator_version: str = GENERATOR_VERSION,
    validator_version: str = VALIDATOR_VERSION,
    compiler_version: str = CAMPAIGN_COMPILER_VERSION,
    batch_compiler_version: str = BATCH_COMPILER_VERSION,
    assembly_version: str = BATCH_SPECIFICATION_ASSEMBLER_VERSION,
    batch_execution_version: str = BATCH_EXECUTION_VERSION,
    campaign_designer_version: str = CAMPAIGN_DESIGNER_VERSION,
) -> CampaignDesignerResult:
    """Run each campaign family through the existing Project 2 pipeline."""

    if not isinstance(campaign_specification, CampaignSpecification):
        raise TypeError("campaign_specification must be CampaignSpecification")
    if not isinstance(execution_context, RunnerExecutionContext):
        raise TypeError("execution_context must be RunnerExecutionContext")
    for name, value in (
        ("generator_version", generator_version),
        ("validator_version", validator_version),
        ("compiler_version", compiler_version),
        ("batch_compiler_version", batch_compiler_version),
        ("assembly_version", assembly_version),
        ("batch_execution_version", batch_execution_version),
        ("campaign_designer_version", campaign_designer_version),
    ):
        _require_non_empty(name, value)

    family_results: list[CampaignFamilyResult] = []
    payloads: list[CampaignFamilyExecutionPayload] = []
    diagnostics: list[str] = []
    for family in campaign_specification.families:
        family_result, payload = _run_family(
            family,
            execution_context,
            generator_version=generator_version,
            validator_version=validator_version,
            compiler_version=compiler_version,
            batch_compiler_version=batch_compiler_version,
            assembly_version=assembly_version,
            batch_execution_version=batch_execution_version,
        )
        family_results.append(family_result)
        payloads.append(payload)
        diagnostics.extend(payload.diagnostics)

    family_results_tuple = tuple(family_results)
    payloads_tuple = tuple(payloads)
    diagnostics_tuple = tuple(sorted(diagnostics))
    total_generated = sum(item.generated_count for item in family_results_tuple)
    total_executed = sum(item.executed_count for item in family_results_tuple)
    total_passed = sum(item.passed_count for item in family_results_tuple)
    total_failed = sum(item.failed_count for item in family_results_tuple)
    total_skipped = sum(item.skipped_count for item in family_results_tuple)
    success = not total_failed and not total_skipped and not diagnostics_tuple
    campaign_fingerprint = campaign_result_fingerprint_payload(
        success=success,
        campaign_id=campaign_specification.campaign_id,
        total_generated=total_generated,
        total_executed=total_executed,
        total_passed=total_passed,
        total_failed=total_failed,
        total_skipped=total_skipped,
        family_results=family_results_tuple,
        campaign_designer_version=campaign_designer_version,
        diagnostics=diagnostics_tuple,
    )
    campaign_result = CampaignResult(
        success=success,
        campaign_id=campaign_specification.campaign_id,
        total_generated=total_generated,
        total_executed=total_executed,
        total_passed=total_passed,
        total_failed=total_failed,
        total_skipped=total_skipped,
        family_results=family_results_tuple,
        campaign_fingerprint=campaign_fingerprint,
        campaign_designer_version=campaign_designer_version,
        diagnostics=diagnostics_tuple,
    )
    designer_fingerprint = _designer_fingerprint(
        campaign_specification=campaign_specification,
        campaign_result=campaign_result,
        payloads=payloads_tuple,
        diagnostics=diagnostics_tuple,
        campaign_designer_version=campaign_designer_version,
    )
    return CampaignDesignerResult(
        success=success,
        campaign_specification=campaign_specification,
        campaign_result=campaign_result,
        family_execution_payloads=payloads_tuple,
        campaign_designer_fingerprint=designer_fingerprint,
        campaign_designer_version=campaign_designer_version,
        diagnostics=diagnostics_tuple,
    )
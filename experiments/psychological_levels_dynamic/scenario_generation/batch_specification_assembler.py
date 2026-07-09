"""Batch assembly of compiled grammar output into runnable specifications."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any

from experiments.psychological_levels_dynamic.scenario_catalog.compiler.specification_assembler import (
    AssembledSpecification,
    assemble_specification,
)

from .batch_compiler import BatchCompilationResult
from .runner_execution_context import RunnerExecutionContext

BATCH_SPECIFICATION_ASSEMBLER_VERSION = "PHASE2C_BATCH_SPECIFICATION_ASSEMBLER_V1"


@dataclass(frozen=True)
class BatchAssemblyResult:
    success: bool
    total_compilations: int
    assembled_specifications: tuple[AssembledSpecification, ...]
    failed_program_ids: tuple[str, ...]
    diagnostics: tuple[str, ...]
    batch_compilation_fingerprint: str
    batch_assembly_fingerprint: str
    assembly_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")
        if self.total_compilations < 0:
            raise ValueError("total_compilations must be non-negative")
        if not isinstance(self.assembled_specifications, tuple) or not all(
            isinstance(value, AssembledSpecification) for value in self.assembled_specifications
        ):
            raise TypeError("assembled_specifications must be AssembledSpecification tuple")
        if len(self.assembled_specifications) > self.total_compilations:
            raise ValueError("assembled specifications cannot exceed total compilations")
        if not isinstance(self.failed_program_ids, tuple) or not all(
            isinstance(value, str) for value in self.failed_program_ids
        ):
            raise TypeError("failed_program_ids must be tuple[str, ...]")
        if len(self.assembled_specifications) + len(self.failed_program_ids) > self.total_compilations:
            raise ValueError("assembled and failed counts cannot exceed total compilations")
        if not isinstance(self.diagnostics, tuple) or not all(
            isinstance(value, str) for value in self.diagnostics
        ):
            raise TypeError("diagnostics must be tuple[str, ...]")
        if self.success and self.failed_program_ids:
            raise ValueError("successful assembly cannot carry failed program IDs")
        if not self.success and not self.diagnostics:
            raise ValueError("failed assembly requires diagnostics")
        if not isinstance(self.batch_compilation_fingerprint, str) or not self.batch_compilation_fingerprint.startswith("sha256:"):
            raise ValueError("batch_compilation_fingerprint must be SHA-256")
        if not isinstance(self.batch_assembly_fingerprint, str) or not self.batch_assembly_fingerprint.startswith("sha256:"):
            raise ValueError("batch_assembly_fingerprint must be SHA-256")
        if not self.assembly_version.strip():
            raise ValueError("assembly_version must not be empty")


def _fingerprint_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _batch_assembly_fingerprint(
    *,
    batch_compilation_fingerprint: str,
    execution_context_fingerprint: str,
    specification_fingerprints: tuple[str, ...],
    failed_program_ids: tuple[str, ...],
    diagnostics: tuple[str, ...],
    assembly_version: str,
) -> str:
    return _fingerprint_payload(
        {
            "batch_compilation_fingerprint": batch_compilation_fingerprint,
            "execution_context_fingerprint": execution_context_fingerprint,
            "specification_fingerprints": specification_fingerprints,
            "failed_program_ids": failed_program_ids,
            "diagnostics": diagnostics,
            "assembly_version": assembly_version,
        }
    )


def _with_runner_context(
    assembled: AssembledSpecification,
    execution_context: RunnerExecutionContext,
) -> AssembledSpecification:
    geometry_parameters = dict(assembled.specification.geometry_parameters)
    geometry_parameters.update(
        {
            "spacing": execution_context.spacing,
            "zone_half_width": execution_context.zone_half_width,
            "active_window": execution_context.active_window,
            "symbol": execution_context.symbol,
            "market_timestamp": execution_context.market_timestamp,
            "session_id": execution_context.session_id,
        }
    )
    runner_ready_specification = replace(
        assembled.specification,
        geometry_parameters=geometry_parameters,
    )
    return replace(assembled, specification=runner_ready_specification)


def _specification_name(index: int, observation_checksum: str) -> str:
    suffix = observation_checksum.split(":", 1)[1][:12].upper()
    return f"COMPILED_BATCH_SPEC_{index:06d}_{suffix}"


def assemble_batch(
    batch_compilation_result: BatchCompilationResult,
    execution_context: RunnerExecutionContext,
    assembly_version: str = BATCH_SPECIFICATION_ASSEMBLER_VERSION,
) -> BatchAssemblyResult:
    if not isinstance(batch_compilation_result, BatchCompilationResult):
        raise TypeError("batch_compilation_result must be BatchCompilationResult")
    if not isinstance(execution_context, RunnerExecutionContext):
        raise TypeError("execution_context must be RunnerExecutionContext")
    if not assembly_version.strip():
        raise ValueError("assembly_version must not be empty")

    assembled: list[AssembledSpecification] = []
    diagnostics: list[str] = list(batch_compilation_result.diagnostics)

    for result_index, compilation_result in enumerate(batch_compilation_result.successful_results):
        try:
            if compilation_result.observation_checksum is None:
                raise ValueError("successful compilation missing observation_checksum")
            assembled_specification = assemble_specification(
                compilation_result,
                _specification_name(result_index, compilation_result.observation_checksum),
            )
            assembled.append(_with_runner_context(assembled_specification, execution_context))
        except Exception as exc:
            diagnostics.append(
                f"ASSEMBLY_{result_index:06d}:ASSEMBLY_FAILED:{type(exc).__name__}:{exc}"
            )

    diagnostics_tuple = tuple(sorted(diagnostics))
    failed_program_ids = batch_compilation_result.failed_program_ids
    success = not failed_program_ids and len(assembled) == len(batch_compilation_result.successful_results)
    if failed_program_ids:
        diagnostics_tuple = tuple(
            sorted(
                diagnostics_tuple
                + tuple(f"SKIPPED_FAILED_COMPILATION:{program_id}" for program_id in failed_program_ids)
            )
        )
    if len(assembled) != len(batch_compilation_result.successful_results):
        success = False

    specifications_tuple = tuple(assembled)
    specification_fingerprints = tuple(
        item.specification.specification_fingerprint for item in specifications_tuple
    )
    return BatchAssemblyResult(
        success=success,
        total_compilations=batch_compilation_result.total_programs,
        assembled_specifications=specifications_tuple,
        failed_program_ids=failed_program_ids,
        diagnostics=diagnostics_tuple,
        batch_compilation_fingerprint=batch_compilation_result.batch_compilation_fingerprint,
        batch_assembly_fingerprint=_batch_assembly_fingerprint(
            batch_compilation_fingerprint=batch_compilation_result.batch_compilation_fingerprint,
            execution_context_fingerprint=execution_context.execution_context_fingerprint,
            specification_fingerprints=specification_fingerprints,
            failed_program_ids=failed_program_ids,
            diagnostics=diagnostics_tuple,
            assembly_version=assembly_version,
        ),
        assembly_version=assembly_version,
    )
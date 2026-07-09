"""Batch compiler for generated GrammarProgram objects.

Compiler integration only: no assembler, no runner, no catalog, and no execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from experiments.psychological_levels_dynamic.scenario_catalog.compiler.contracts import (
    CompilationResult,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.full_compiler import (
    compile_program,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.geometry import (
    GeometryContext,
)

from .generator import GenerationResult

BATCH_COMPILER_VERSION = "PHASE2B_BATCH_COMPILER_V1"


@dataclass(frozen=True)
class BatchCompilationResult:
    success: bool
    total_programs: int
    compiled_programs: int
    failed_programs: int
    successful_results: tuple[CompilationResult, ...]
    failed_program_ids: tuple[str, ...]
    diagnostics: tuple[str, ...]
    batch_compilation_fingerprint: str
    compiler_version: str
    batch_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")
        if self.total_programs < 0 or self.compiled_programs < 0 or self.failed_programs < 0:
            raise ValueError("program counts must be non-negative")
        if self.compiled_programs + self.failed_programs != self.total_programs:
            raise ValueError("program counts must reconcile to total_programs")
        if not isinstance(self.successful_results, tuple) or not all(
            isinstance(value, CompilationResult) for value in self.successful_results
        ):
            raise TypeError("successful_results must be CompilationResult tuple")
        if len(self.successful_results) != self.compiled_programs:
            raise ValueError("successful_results must match compiled_programs")
        if not all(value.success for value in self.successful_results):
            raise ValueError("successful_results must contain only successful CompilationResult values")
        if not isinstance(self.failed_program_ids, tuple) or not all(
            isinstance(value, str) for value in self.failed_program_ids
        ):
            raise TypeError("failed_program_ids must be tuple[str, ...]")
        if len(self.failed_program_ids) != self.failed_programs:
            raise ValueError("failed_program_ids must match failed_programs")
        if not isinstance(self.diagnostics, tuple) or not all(
            isinstance(value, str) for value in self.diagnostics
        ):
            raise TypeError("diagnostics must be tuple[str, ...]")
        if self.success and self.failed_programs != 0:
            raise ValueError("successful batch cannot have failed programs")
        if not self.success and not self.diagnostics:
            raise ValueError("failed batch requires diagnostics")
        if not isinstance(self.batch_compilation_fingerprint, str) or not self.batch_compilation_fingerprint.startswith("sha256:"):
            raise ValueError("batch_compilation_fingerprint must be SHA-256")
        if not self.compiler_version.strip():
            raise ValueError("compiler_version must not be empty")
        if not self.batch_version.strip():
            raise ValueError("batch_version must not be empty")


def _fingerprint_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _batch_fingerprint(
    *,
    generation_fingerprint: str,
    observation_checksums: tuple[str | None, ...],
    program_fingerprints: tuple[str, ...],
    diagnostics: tuple[str, ...],
    compiler_version: str,
    batch_version: str,
) -> str:
    return _fingerprint_payload(
        {
            "generation_fingerprint": generation_fingerprint,
            "observation_checksums": observation_checksums,
            "program_fingerprints": program_fingerprints,
            "diagnostics": diagnostics,
            "compiler_version": compiler_version,
            "batch_version": batch_version,
        }
    )


def _diagnostic_strings(program_index: int, program_id: str, result: CompilationResult) -> tuple[str, ...]:
    return tuple(
        f"PROGRAM_{program_index:06d}:{program_id}:{diagnostic.code}:{diagnostic.message}"
        for diagnostic in result.diagnostics
    )


def compile_generation_batch(
    generation_result: GenerationResult,
    geometry_context: GeometryContext,
    compiler_version: str,
    batch_version: str = BATCH_COMPILER_VERSION,
) -> BatchCompilationResult:
    if not isinstance(generation_result, GenerationResult):
        raise TypeError("generation_result must be GenerationResult")
    if not isinstance(geometry_context, GeometryContext):
        raise TypeError("geometry_context must be GeometryContext")
    if not compiler_version.strip():
        raise ValueError("compiler_version must not be empty")
    if not batch_version.strip():
        raise ValueError("batch_version must not be empty")

    if not generation_result.success:
        diagnostics = tuple(sorted(generation_result.diagnostics + ("GENERATION_RESULT_FAILED",)))
        return BatchCompilationResult(
            success=False,
            total_programs=0,
            compiled_programs=0,
            failed_programs=0,
            successful_results=(),
            failed_program_ids=(),
            diagnostics=diagnostics,
            batch_compilation_fingerprint=_batch_fingerprint(
                generation_fingerprint=generation_result.generation_fingerprint,
                observation_checksums=(),
                program_fingerprints=(),
                diagnostics=diagnostics,
                compiler_version=compiler_version,
                batch_version=batch_version,
            ),
            compiler_version=compiler_version,
            batch_version=batch_version,
        )

    successful_results: list[CompilationResult] = []
    failed_program_ids: list[str] = []
    diagnostics: list[str] = []
    observation_checksums: list[str | None] = []
    program_fingerprints: list[str] = []

    for program_index, program in enumerate(generation_result.generated_programs):
        result = compile_program(program, geometry_context, compiler_version)
        observation_checksums.append(result.observation_checksum)
        program_fingerprints.append(program.program_fingerprint)
        if result.success:
            successful_results.append(result)
            continue
        failed_program_ids.append(program.program_id)
        diagnostics.append(f"PROGRAM_{program_index:06d}:{program.program_id}:COMPILATION_FAILED")
        diagnostics.extend(_diagnostic_strings(program_index, program.program_id, result))

    diagnostics_tuple = tuple(sorted(diagnostics))
    failed_program_ids_tuple = tuple(failed_program_ids)
    successful_results_tuple = tuple(successful_results)
    total_programs = len(generation_result.generated_programs)
    failed_programs = len(failed_program_ids_tuple)
    compiled_programs = len(successful_results_tuple)
    success = failed_programs == 0
    return BatchCompilationResult(
        success=success,
        total_programs=total_programs,
        compiled_programs=compiled_programs,
        failed_programs=failed_programs,
        successful_results=successful_results_tuple,
        failed_program_ids=failed_program_ids_tuple,
        diagnostics=diagnostics_tuple,
        batch_compilation_fingerprint=_batch_fingerprint(
            generation_fingerprint=generation_result.generation_fingerprint,
            observation_checksums=tuple(observation_checksums),
            program_fingerprints=tuple(program_fingerprints),
            diagnostics=diagnostics_tuple,
            compiler_version=compiler_version,
            batch_version=batch_version,
        ),
        compiler_version=compiler_version,
        batch_version=batch_version,
    )
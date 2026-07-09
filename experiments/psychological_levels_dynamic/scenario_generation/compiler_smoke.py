"""Compiler smoke validation for generated GrammarProgram objects.

Compiler integration only: no assembler, no runner, no catalog, and no stage execution.
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

SMOKE_VERSION = "PHASE2B_COMPILER_SMOKE_V1"


@dataclass(frozen=True)
class CompilerSmokeResult:
    success: bool
    compiled_programs: int
    failed_programs: int
    compilation_results: tuple[CompilationResult, ...]
    diagnostics: tuple[str, ...]
    smoke_fingerprint: str
    smoke_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")
        if self.compiled_programs < 0 or self.failed_programs < 0:
            raise ValueError("program counts must be non-negative")
        if not isinstance(self.compilation_results, tuple) or not all(
            isinstance(value, CompilationResult) for value in self.compilation_results
        ):
            raise TypeError("compilation_results must be CompilationResult tuple")
        if not isinstance(self.diagnostics, tuple) or not all(
            isinstance(value, str) for value in self.diagnostics
        ):
            raise TypeError("diagnostics must be tuple[str, ...]")
        if self.compiled_programs + self.failed_programs != len(self.compilation_results):
            raise ValueError("program counts must match compilation_results")
        if self.success and self.failed_programs != 0:
            raise ValueError("successful smoke cannot have failed programs")
        if not self.success and not self.diagnostics:
            raise ValueError("failed smoke requires diagnostics")
        if not isinstance(self.smoke_fingerprint, str) or not self.smoke_fingerprint.startswith("sha256:"):
            raise ValueError("smoke_fingerprint must be SHA-256")
        if not self.smoke_version.strip():
            raise ValueError("smoke_version must not be empty")


def _fingerprint_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _smoke_fingerprint(
    *,
    generation_fingerprint: str,
    observation_checksums: tuple[str | None, ...],
    diagnostics: tuple[str, ...],
    compiler_version: str,
    smoke_version: str,
) -> str:
    return _fingerprint_payload(
        {
            "generation_fingerprint": generation_fingerprint,
            "observation_checksums": observation_checksums,
            "diagnostics": diagnostics,
            "compiler_version": compiler_version,
            "smoke_version": smoke_version,
        }
    )


def _diagnostic_strings(program_index: int, result: CompilationResult) -> tuple[str, ...]:
    return tuple(
        f"PROGRAM_{program_index:06d}:{diagnostic.code}:{diagnostic.message}"
        for diagnostic in result.diagnostics
    )


def run_compiler_smoke(
    generation_result: GenerationResult,
    geometry_context: GeometryContext,
    compiler_version: str,
    smoke_version: str = SMOKE_VERSION,
) -> CompilerSmokeResult:
    if not isinstance(generation_result, GenerationResult):
        raise TypeError("generation_result must be GenerationResult")
    if not isinstance(geometry_context, GeometryContext):
        raise TypeError("geometry_context must be GeometryContext")
    if not compiler_version.strip():
        raise ValueError("compiler_version must not be empty")
    if not smoke_version.strip():
        raise ValueError("smoke_version must not be empty")

    if not generation_result.success:
        diagnostics = tuple(sorted(generation_result.diagnostics + ("GENERATION_RESULT_FAILED",)))
        return CompilerSmokeResult(
            success=False,
            compiled_programs=0,
            failed_programs=0,
            compilation_results=(),
            diagnostics=diagnostics,
            smoke_fingerprint=_smoke_fingerprint(
                generation_fingerprint=generation_result.generation_fingerprint,
                observation_checksums=(),
                diagnostics=diagnostics,
                compiler_version=compiler_version,
                smoke_version=smoke_version,
            ),
            smoke_version=smoke_version,
        )

    results: list[CompilationResult] = []
    diagnostics: list[str] = []
    for program_index, program in enumerate(generation_result.generated_programs):
        result = compile_program(program, geometry_context, compiler_version)
        results.append(result)
        if not result.success:
            diagnostics.append(f"PROGRAM_{program_index:06d}:COMPILATION_FAILED")
            diagnostics.extend(_diagnostic_strings(program_index, result))

    results_tuple = tuple(results)
    diagnostics_tuple = tuple(sorted(diagnostics))
    failed_programs = sum(1 for result in results_tuple if not result.success)
    compiled_programs = len(results_tuple) - failed_programs
    success = failed_programs == 0
    observation_checksums = tuple(result.observation_checksum for result in results_tuple)
    return CompilerSmokeResult(
        success=success,
        compiled_programs=compiled_programs,
        failed_programs=failed_programs,
        compilation_results=results_tuple,
        diagnostics=diagnostics_tuple,
        smoke_fingerprint=_smoke_fingerprint(
            generation_fingerprint=generation_result.generation_fingerprint,
            observation_checksums=observation_checksums,
            diagnostics=diagnostics_tuple,
            compiler_version=compiler_version,
            smoke_version=smoke_version,
        ),
        smoke_version=smoke_version,
    )
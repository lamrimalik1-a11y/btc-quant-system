"""Thin full-compiler orchestration for Chapter III Phase 1D.

This module wires together the already-stable compiler stages. It does not add
new grammar, scheduling, geometry, price, scenario, or research mechanics.
"""

from __future__ import annotations

from experiments.psychological_levels_dynamic.scenario_catalog.grammar.ast import (
    GrammarProgram,
)

from .contracts import CompilationResult
from .diagnostics import CompilerDiagnostic
from .geometry import GeometryContext
from .geometry_resolution import resolve_geometry
from .macro_expansion import expand_program
from .price_materialization import materialize_prices
from .timeline_scheduler import schedule_expansion


DEFAULT_COMPILER_VERSION = "PHASE1D_FULL_COMPILER_V1"


def _sorted_diagnostics(
    *diagnostic_groups: tuple[CompilerDiagnostic, ...]
) -> tuple[CompilerDiagnostic, ...]:
    diagnostics: list[CompilerDiagnostic] = []
    for group in diagnostic_groups:
        diagnostics.extend(group)
    return tuple(sorted(diagnostics, key=lambda item: item.deterministic_key))


def _result(
    *,
    success: bool,
    observations: tuple[object, ...],
    timeline: object | None,
    diagnostics: tuple[CompilerDiagnostic, ...],
    grammar_fingerprint: str,
    geometry_fingerprint: str,
    compiler_version: str,
    observation_checksum: str | None,
) -> CompilationResult:
    return CompilationResult(
        success=success,
        observations=observations if success else (),
        timeline=timeline if success else None,
        diagnostics=tuple(sorted(diagnostics, key=lambda item: item.deterministic_key)),
        grammar_fingerprint=grammar_fingerprint,
        geometry_fingerprint=geometry_fingerprint,
        compiler_version=compiler_version,
        observation_checksum=observation_checksum if success else None,
    )


def compile_program(
    program: GrammarProgram,
    geometry_context: GeometryContext,
    compiler_version: str = DEFAULT_COMPILER_VERSION,
) -> CompilationResult:
    """Compile a GrammarProgram into PriceObservation rows through stable stages."""

    if not isinstance(program, GrammarProgram):
        raise TypeError("program must be GrammarProgram")
    if not isinstance(geometry_context, GeometryContext):
        raise TypeError("geometry_context must be GeometryContext")
    if not compiler_version.strip():
        raise ValueError("compiler_version must not be empty")

    expansion_result = expand_program(program, compiler_version)
    if not expansion_result.success:
        return _result(
            success=False,
            observations=(),
            timeline=None,
            diagnostics=_sorted_diagnostics(expansion_result.diagnostics),
            grammar_fingerprint=program.program_fingerprint,
            geometry_fingerprint=geometry_context.geometry_fingerprint,
            compiler_version=compiler_version,
            observation_checksum=None,
        )

    scheduling_result = schedule_expansion(expansion_result)
    if not scheduling_result.success:
        return _result(
            success=False,
            observations=(),
            timeline=None,
            diagnostics=_sorted_diagnostics(
                expansion_result.diagnostics,
                scheduling_result.diagnostics,
            ),
            grammar_fingerprint=program.program_fingerprint,
            geometry_fingerprint=geometry_context.geometry_fingerprint,
            compiler_version=compiler_version,
            observation_checksum=None,
        )

    geometry_result = resolve_geometry(
        expansion_result,
        scheduling_result,
        geometry_context,
    )
    if not geometry_result.success:
        return _result(
            success=False,
            observations=(),
            timeline=None,
            diagnostics=_sorted_diagnostics(
                expansion_result.diagnostics,
                scheduling_result.diagnostics,
                geometry_result.diagnostics,
            ),
            grammar_fingerprint=program.program_fingerprint,
            geometry_fingerprint=geometry_context.geometry_fingerprint,
            compiler_version=compiler_version,
            observation_checksum=None,
        )

    materialization_result = materialize_prices(geometry_result)
    if not materialization_result.success:
        return _result(
            success=False,
            observations=(),
            timeline=None,
            diagnostics=_sorted_diagnostics(
                expansion_result.diagnostics,
                scheduling_result.diagnostics,
                geometry_result.diagnostics,
                materialization_result.diagnostics,
            ),
            grammar_fingerprint=program.program_fingerprint,
            geometry_fingerprint=geometry_context.geometry_fingerprint,
            compiler_version=compiler_version,
            observation_checksum=None,
        )

    return _result(
        success=True,
        observations=materialization_result.observations,
        timeline=scheduling_result.timeline,
        diagnostics=_sorted_diagnostics(
            expansion_result.diagnostics,
            scheduling_result.diagnostics,
            geometry_result.diagnostics,
            materialization_result.diagnostics,
        ),
        grammar_fingerprint=program.program_fingerprint,
        geometry_fingerprint=geometry_context.geometry_fingerprint,
        compiler_version=compiler_version,
        observation_checksum=materialization_result.observation_checksum,
    )
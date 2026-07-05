"""Immutable compilation boundary contracts; no compiler implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..grammar.ast import GrammarProgram
from .diagnostics import CompilerDiagnostic
from .geometry import GeometryContext
from .timeline import MechanicalTimeline


@dataclass(frozen=True)
class CompilationRequest:
    program: GrammarProgram
    geometry_context: GeometryContext
    compiler_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.program, GrammarProgram) or not isinstance(
            self.geometry_context, GeometryContext
        ):
            raise TypeError("invalid compilation request")
        if not self.compiler_version.strip():
            raise ValueError("compiler_version required")


@dataclass(frozen=True)
class CompilationResult:
    success: bool
    observations: tuple[Any, ...]
    timeline: MechanicalTimeline
    diagnostics: tuple[CompilerDiagnostic, ...]
    grammar_fingerprint: str
    geometry_fingerprint: str
    compiler_version: str
    observation_checksum: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.observations, tuple) or not isinstance(
            self.diagnostics, tuple
        ):
            raise TypeError("result collections must be immutable")
        if not all(
            isinstance(value, CompilerDiagnostic) for value in self.diagnostics
        ):
            raise TypeError("invalid diagnostics")
        if not self.grammar_fingerprint.startswith(
            "sha256:"
        ) or not self.geometry_fingerprint.startswith("sha256:"):
            raise ValueError("fingerprints must be SHA-256")

"""Immutable contracts for a future deterministic expansion layer."""

from __future__ import annotations

from dataclasses import dataclass

from ..grammar.ast import PhraseType
from .diagnostics import CompilerDiagnostic
from .primitives import PrimitiveInstruction, PrimitiveType


@dataclass(frozen=True)
class ExpandedInstruction:
    instruction: PrimitiveInstruction
    row_budget: int

    def __post_init__(self) -> None:
        if not isinstance(self.instruction, PrimitiveInstruction):
            raise TypeError("instruction must be PrimitiveInstruction")
        if self.row_budget <= 0:
            raise ValueError("row_budget must be positive")


@dataclass(frozen=True)
class ExpansionResult:
    success: bool
    expanded_instructions: tuple[ExpandedInstruction, ...]
    diagnostics: tuple[CompilerDiagnostic, ...]
    grammar_fingerprint: str
    compiler_version: str
    expansion_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")
        if not isinstance(self.expanded_instructions, tuple) or not all(
            isinstance(item, ExpandedInstruction)
            for item in self.expanded_instructions
        ):
            raise TypeError(
                "expanded_instructions must be an immutable "
                "ExpandedInstruction tuple"
            )
        if not isinstance(self.diagnostics, tuple) or not all(
            isinstance(item, CompilerDiagnostic) for item in self.diagnostics
        ):
            raise TypeError(
                "diagnostics must be an immutable CompilerDiagnostic tuple"
            )
        if not self.grammar_fingerprint.startswith("sha256:"):
            raise ValueError("grammar_fingerprint must be SHA-256")
        if not self.expansion_fingerprint.startswith("sha256:"):
            raise ValueError("expansion_fingerprint must be SHA-256")
        if not self.compiler_version.strip():
            raise ValueError("compiler_version must not be empty")


@dataclass(frozen=True)
class ExpansionRule:
    macro_type: PhraseType
    primitive_sequence: tuple[PrimitiveType, ...]
    allocation_rule_version: str
    recursive: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.macro_type, PhraseType):
            raise TypeError("macro_type must be PhraseType")
        if not isinstance(self.primitive_sequence, tuple) or not (
            self.primitive_sequence
        ):
            raise TypeError(
                "primitive_sequence must be a non-empty immutable tuple"
            )
        if not all(
            isinstance(item, PrimitiveType) for item in self.primitive_sequence
        ):
            raise TypeError("primitive_sequence contains an invalid primitive")
        if not self.allocation_rule_version.strip():
            raise ValueError("allocation_rule_version must not be empty")
        if self.recursive:
            raise ValueError("version 1 expansion rules must be non-recursive")


@dataclass(frozen=True)
class AllocationPolicy:
    policy_name: str
    policy_version: str
    description: str

    def __post_init__(self) -> None:
        if not self.policy_name.strip():
            raise ValueError("policy_name must not be empty")
        if not self.policy_version.strip():
            raise ValueError("policy_version must not be empty")
        if not self.description.strip():
            raise ValueError("description must not be empty")

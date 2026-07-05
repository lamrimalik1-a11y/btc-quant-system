"""Deterministic compiler diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DiagnosticSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


@dataclass(frozen=True)
class CompilerDiagnostic:
    code: str
    severity: DiagnosticSeverity
    message: str
    phrase_index: int | None = None
    parameter_name: str | None = None

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.message.strip():
            raise ValueError("code and message required")
        if not isinstance(self.severity, DiagnosticSeverity):
            raise TypeError("invalid severity")
        if self.phrase_index is not None and self.phrase_index < 0:
            raise ValueError("invalid phrase_index")

    @property
    def deterministic_key(self) -> tuple[str, str, int, str, str]:
        return (
            self.severity.value,
            self.code,
            -1 if self.phrase_index is None else self.phrase_index,
            self.parameter_name or "",
            self.message,
        )

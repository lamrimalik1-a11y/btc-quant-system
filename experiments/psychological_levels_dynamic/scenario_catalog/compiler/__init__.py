"""Immutable compiler foundation contracts."""

from .contracts import CompilationRequest, CompilationResult
from .diagnostics import CompilerDiagnostic, DiagnosticSeverity
from .geometry import GeometryContext, GeometryReference
from .primitives import PrimitiveInstruction, PrimitiveType
from .timeline import MechanicalTimeline, TimelineSegment

__all__ = (
    "CompilationRequest",
    "CompilationResult",
    "CompilerDiagnostic",
    "DiagnosticSeverity",
    "GeometryContext",
    "GeometryReference",
    "PrimitiveInstruction",
    "PrimitiveType",
    "MechanicalTimeline",
    "TimelineSegment",
)

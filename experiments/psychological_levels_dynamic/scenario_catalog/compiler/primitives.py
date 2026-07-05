"""Immutable primitive instruction contracts; no compilation behavior."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..grammar.ast import GrammarParameter


class PrimitiveType(str, Enum):
    HOLD = "HOLD"
    RAMP = "RAMP"
    OSCILLATE = "OSCILLATE"
    APPROACH = "APPROACH"
    ENTER = "ENTER"
    PENETRATE = "PENETRATE"
    WITHDRAW = "WITHDRAW"
    HOLD_OUTSIDE = "HOLD_OUTSIDE"
    RECOVERY_GAP = "RECOVERY_GAP"


@dataclass(frozen=True)
class PrimitiveInstruction:
    instruction_index: int
    source_phrase_index: int
    primitive_type: PrimitiveType
    parameters: tuple[GrammarParameter, ...]
    target_zone: str | None = None
    macro_origin: str | None = None

    def __post_init__(self) -> None:
        if self.instruction_index < 0 or self.source_phrase_index < 0:
            raise ValueError("indices must be non-negative")
        if not isinstance(self.parameters, tuple) or not all(
            isinstance(value, GrammarParameter) for value in self.parameters
        ):
            raise TypeError("parameters must be immutable")
        object.__setattr__(
            self,
            "parameters",
            tuple(sorted(self.parameters, key=lambda value: value.name)),
        )

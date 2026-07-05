"""Immutable mechanical timeline contracts; no scheduling behavior."""

from __future__ import annotations

from dataclasses import dataclass

from ..grammar.dimensions import PathSmoothness
from .primitives import PrimitiveType


@dataclass(frozen=True)
class TimelineSegment:
    segment_index: int
    source_phrase_index: int
    primitive_type: PrimitiveType
    row_start: int
    row_end: int
    row_count: int
    target_zone: str | None
    macro_origin: str | None
    interpolation_policy: PathSmoothness

    def __post_init__(self) -> None:
        if (
            self.segment_index < 0
            or self.source_phrase_index < 0
            or self.row_start < 0
            or self.row_end < self.row_start
        ):
            raise ValueError("invalid timeline bounds")
        if self.row_count != self.row_end - self.row_start + 1:
            raise ValueError("row_count mismatch")
        if not isinstance(self.interpolation_policy, PathSmoothness):
            raise TypeError("interpolation_policy must be PathSmoothness")


@dataclass(frozen=True)
class MechanicalTimeline:
    segments: tuple[TimelineSegment, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.segments, tuple) or not all(
            isinstance(value, TimelineSegment) for value in self.segments
        ):
            raise TypeError("segments must be immutable")
        if tuple(value.segment_index for value in self.segments) != tuple(
            range(len(self.segments))
        ):
            raise ValueError("segments must be ordered")

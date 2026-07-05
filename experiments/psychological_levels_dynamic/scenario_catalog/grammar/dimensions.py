"""Versioned behavioral-dimension taxonomy for scenario authoring."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


DIMENSION_SCHEMA_VERSION = "1"


class BehavioralDimension(str, Enum):
    TARGET_ZONE = "TARGET_ZONE"
    APPROACH_SIDE = "APPROACH_SIDE"
    PENETRATION_DEPTH = "PENETRATION_DEPTH"
    PENETRATION_DURATION = "PENETRATION_DURATION"
    INTER_VISIT_RECOVERY_GAP = "INTER_VISIT_RECOVERY_GAP"
    ATTACK_COUNT = "ATTACK_COUNT"
    DEPTH_TRAJECTORY = "DEPTH_TRAJECTORY"
    DURATION_TRAJECTORY = "DURATION_TRAJECTORY"
    INSIDE_ZONE_RESIDENCE = "INSIDE_ZONE_RESIDENCE"
    OUTSIDE_ZONE_RESIDENCE = "OUTSIDE_ZONE_RESIDENCE"
    WITHDRAWAL_DISTANCE = "WITHDRAWAL_DISTANCE"
    BOUNDARY_CLEARANCE = "BOUNDARY_CLEARANCE"
    ACCEPTANCE_DURATION = "ACCEPTANCE_DURATION"
    RETEST_DELAY = "RETEST_DELAY"
    RETEST_DEPTH = "RETEST_DEPTH"
    RECLAIM_DEPTH = "RECLAIM_DEPTH"
    RECLAIM_RESIDENCE = "RECLAIM_RESIDENCE"
    OSCILLATION_AMPLITUDE = "OSCILLATION_AMPLITUDE"
    OSCILLATION_PERIOD = "OSCILLATION_PERIOD"
    COMPRESSION_SCHEDULE = "COMPRESSION_SCHEDULE"
    EXPANSION_SCHEDULE = "EXPANSION_SCHEDULE"
    REGIME_PHASE_SEQUENCE = "REGIME_PHASE_SEQUENCE"
    MULTI_ZONE_TOPOLOGY = "MULTI_ZONE_TOPOLOGY"
    SPARSE_INTERACTION = "SPARSE_INTERACTION"
    PATH_SMOOTHNESS = "PATH_SMOOTHNESS"


class DeferredDimension(str, Enum):
    NESTED_GEOMETRY = "NESTED_GEOMETRY"
    LARGE_MULTI_ZONE_NETWORK = "LARGE_MULTI_ZONE_NETWORK"
    RANDOM_NOISE = "RANDOM_NOISE"
    LIQUIDITY_TERMINOLOGY = "LIQUIDITY_TERMINOLOGY"
    STOCHASTIC_GENERATION = "STOCHASTIC_GENERATION"


class ZoneSide(str, Enum):
    LOWER = "LOWER"
    UPPER = "UPPER"


class Direction(str, Enum):
    DOWN = "DOWN"
    UP = "UP"


class TrajectoryShape(str, Enum):
    CONSTANT = "CONSTANT"
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"


class RelativePosition(str, Enum):
    CURRENT = "CURRENT"
    OUTSIDE_LOWER = "OUTSIDE_LOWER"
    LOWER_BOUNDARY = "LOWER_BOUNDARY"
    INSIDE_ZONE = "INSIDE_ZONE"
    CENTER = "CENTER"
    UPPER_BOUNDARY = "UPPER_BOUNDARY"
    OUTSIDE_UPPER = "OUTSIDE_UPPER"


class PathSmoothness(str, Enum):
    STEP = "STEP"
    LINEAR = "LINEAR"


@dataclass(frozen=True)
class DimensionDefinition:
    dimension: BehavioralDimension | DeferredDimension
    schema_version: str
    description: str
    active: bool

    def __post_init__(self) -> None:
        if self.schema_version != DIMENSION_SCHEMA_VERSION:
            raise ValueError("unsupported dimension schema version")
        if not self.description.strip():
            raise ValueError("dimension description must not be empty")


ACTIVE_DIMENSIONS = tuple(
    DimensionDefinition(
        dimension=dimension,
        schema_version=DIMENSION_SCHEMA_VERSION,
        description=f"Version 1 behavioral dimension: {dimension.value}.",
        active=True,
    )
    for dimension in BehavioralDimension
)

DEFERRED_DIMENSIONS = tuple(
    DimensionDefinition(
        dimension=dimension,
        schema_version=DIMENSION_SCHEMA_VERSION,
        description=f"Deferred behavioral dimension: {dimension.value}.",
        active=False,
    )
    for dimension in DeferredDimension
)

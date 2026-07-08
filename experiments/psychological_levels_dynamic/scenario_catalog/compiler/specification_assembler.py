"""Assemble ScenarioSpecification values from successful compiler output only."""

from __future__ import annotations

from dataclasses import dataclass

from experiments.psychological_levels_dynamic.scenario_contract import (
    PriceObservation,
    ScenarioSpecification,
)

from .contracts import CompilationResult


SPECIFICATION_ASSEMBLER_VERSION = "PHASE1D_SPECIFICATION_ASSEMBLER_V1"
SCENARIO_FAMILY = "COMPILED_GRAMMAR_PROGRAM"
SCHEMA_VERSION = "1"


@dataclass(frozen=True)
class AssembledSpecification:
    """A ScenarioSpecification paired explicitly with its compiled observations.

    ScenarioSpecification itself carries no observations field and must not
    be modified; this wrapper declares compiled_observations as a real,
    equality-visible field instead of attaching it out of band.
    """

    specification: ScenarioSpecification
    compiled_observations: tuple[PriceObservation, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.specification, ScenarioSpecification):
            raise TypeError("specification must be ScenarioSpecification")
        if not isinstance(self.compiled_observations, tuple) or not all(
            isinstance(value, PriceObservation) for value in self.compiled_observations
        ):
            raise TypeError(
                "compiled_observations must be an immutable PriceObservation tuple"
            )
        if not self.compiled_observations:
            raise ValueError("compiled_observations must not be empty")


def assemble_specification(
    compilation_result: CompilationResult,
    specification_name: str,
) -> AssembledSpecification:
    """Wrap successful compiler output in the existing ScenarioSpecification."""

    if not isinstance(compilation_result, CompilationResult):
        raise TypeError("compilation_result must be CompilationResult")
    if not specification_name.strip():
        raise ValueError("specification_name must not be empty")
    if not compilation_result.success:
        raise ValueError("cannot assemble ScenarioSpecification from failed compilation")
    if not compilation_result.observations:
        raise ValueError("successful compilation must carry observations")
    if compilation_result.observation_checksum is None:
        raise ValueError("successful compilation must carry observation_checksum")

    observations = compilation_result.observations
    specification = ScenarioSpecification(
        scenario_id=specification_name,
        scenario_family=SCENARIO_FAMILY,
        schema_version=SCHEMA_VERSION,
        description="ScenarioSpecification assembled from successful compiler output.",
        parameters={
            "observation_checksum": compilation_result.observation_checksum,
            "compiler_version": compilation_result.compiler_version,
            "assembler_version": SPECIFICATION_ASSEMBLER_VERSION,
        },
        geometry_parameters={
            "geometry_fingerprint": compilation_result.geometry_fingerprint,
        },
        row_count=len(observations),
        start_price=observations[0].price,
        expected_behavior_notes=(
            "Compiler output only; no expected behavior labels are declared.",
        ),
        validation_metadata={
            "grammar_fingerprint": compilation_result.grammar_fingerprint,
            "geometry_fingerprint": compilation_result.geometry_fingerprint,
            "observation_checksum": compilation_result.observation_checksum,
            "diagnostic_count": len(compilation_result.diagnostics),
            "source": "CompilationResult",
        },
        seed_metadata=compilation_result.observation_checksum,
    )
    return AssembledSpecification(
        specification=specification,
        compiled_observations=observations,
    )

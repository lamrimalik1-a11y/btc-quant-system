"""Small deterministic GrammarProgram generator.

Generation only: no compiler calls, no runner calls, no execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from itertools import product
from typing import Any, Callable

from experiments.psychological_levels_dynamic.scenario_catalog.grammar.ast import (
    GRAMMAR_SCHEMA_VERSION,
    GrammarProgram,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.phrases import (
    accepted_break,
    approach_zone,
    compress,
    enter_zone,
    expand,
    hold,
    hold_outside,
    oscillate,
    penetrate,
    ramp,
    reclaim,
    recovery_gap,
    retest_boundary,
    transfer_to_zone,
    withdraw,
)

from .contracts import (
    GrammarTemplate,
    ManifestEntry,
    ScenarioManifest,
    generation_contract_fingerprint,
)

GENERATOR_VERSION = "PHASE2B_SMALL_DETERMINISTIC_GENERATOR_V1"
MAX_GENERATED_PROGRAMS = 10

_CONSTRUCTORS: dict[str, Callable[..., Any]] = {
    "accepted_break": accepted_break,
    "approach_zone": approach_zone,
    "compress": compress,
    "enter_zone": enter_zone,
    "expand": expand,
    "hold": hold,
    "hold_outside": hold_outside,
    "oscillate": oscillate,
    "penetrate": penetrate,
    "ramp": ramp,
    "reclaim": reclaim,
    "recovery_gap": recovery_gap,
    "retest_boundary": retest_boundary,
    "transfer_to_zone": transfer_to_zone,
    "withdraw": withdraw,
}


@dataclass(frozen=True)
class GenerationResult:
    success: bool
    generated_programs: tuple[GrammarProgram, ...]
    manifest: ScenarioManifest | None
    diagnostics: tuple[str, ...]
    generation_fingerprint: str
    generator_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")
        if not isinstance(self.generated_programs, tuple) or not all(
            isinstance(value, GrammarProgram) for value in self.generated_programs
        ):
            raise TypeError("generated_programs must be GrammarProgram tuple")
        if self.success:
            if self.manifest is None:
                raise ValueError("successful generation requires manifest")
        else:
            if self.generated_programs:
                raise ValueError("failed generation must not carry programs")
            if self.manifest is not None:
                raise ValueError("failed generation must not carry manifest")
            if not self.diagnostics:
                raise ValueError("failed generation requires diagnostics")
        if not isinstance(self.diagnostics, tuple) or not all(
            isinstance(value, str) for value in self.diagnostics
        ):
            raise TypeError("diagnostics must be tuple[str, ...]")
        if not isinstance(self.generation_fingerprint, str) or not self.generation_fingerprint.startswith("sha256:"):
            raise ValueError("generation_fingerprint must be SHA-256")
        if not self.generator_version.strip():
            raise ValueError("generator_version must not be empty")


def _fingerprint_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _generation_result_fingerprint(
    *,
    manifest_fingerprint: str | None,
    program_fingerprints: tuple[str, ...],
    generator_version: str,
    diagnostics: tuple[str, ...],
) -> str:
    return _fingerprint_payload(
        {
            "manifest_fingerprint": manifest_fingerprint,
            "program_fingerprints": program_fingerprints,
            "generator_version": generator_version,
            "diagnostics": diagnostics,
        }
    )


def _failure(generator_version: str, diagnostics: tuple[str, ...]) -> GenerationResult:
    return GenerationResult(
        success=False,
        generated_programs=(),
        manifest=None,
        diagnostics=diagnostics,
        generation_fingerprint=_generation_result_fingerprint(
            manifest_fingerprint=None,
            program_fingerprints=(),
            generator_version=generator_version,
            diagnostics=diagnostics,
        ),
        generator_version=generator_version,
    )


def _axis_combinations(template: GrammarTemplate) -> tuple[tuple[tuple[str, Any], ...], ...]:
    axes = template.axes
    if not axes:
        return ((),)
    axis_names = tuple(axis.axis_name for axis in axes)
    values = tuple(axis.values for axis in axes)
    return tuple(
        tuple(zip(axis_names, combination))
        for combination in product(*values)
    )


def _resolve_phrase(slot, combination: dict[str, Any]):
    constructor = _CONSTRUCTORS.get(slot.constructor_name)
    if constructor is None:
        raise ValueError(f"unknown phrase constructor: {slot.constructor_name}")
    parameters = {name: value for name, value in slot.fixed_params}
    for parameter_name, axis_name in slot.axis_bound_params:
        parameters[parameter_name] = combination[axis_name]
    return constructor(**parameters)


def _program_id(template: GrammarTemplate, phrases: tuple[Any, ...]) -> str:
    phrase_fingerprint = generation_contract_fingerprint(phrases)
    suffix = phrase_fingerprint.split(":", 1)[1][:12].upper()
    return f"{template.template_id}_{suffix}"


def _manifest_fingerprint(
    *,
    manifest_id: str,
    manifest_version: str,
    generation_spec_fingerprint: str,
    generator_version: str,
    template_ids: tuple[str, ...],
    entries: tuple[ManifestEntry, ...],
) -> str:
    return generation_contract_fingerprint(
        (
            manifest_id,
            manifest_version,
            generation_spec_fingerprint,
            generator_version,
            template_ids,
            entries,
        )
    )


def generate_programs(
    template: GrammarTemplate,
    generator_version: str = GENERATOR_VERSION,
) -> GenerationResult:
    if not isinstance(template, GrammarTemplate):
        raise TypeError("template must be GrammarTemplate")
    if not generator_version.strip():
        raise ValueError("generator_version must not be empty")

    combinations = _axis_combinations(template)
    if len(combinations) > MAX_GENERATED_PROGRAMS:
        return _failure(
            generator_version,
            (f"MAX_GENERATED_PROGRAMS_EXCEEDED:{len(combinations)}",),
        )

    entries: list[ManifestEntry] = []
    programs: list[GrammarProgram] = []
    seen_program_fingerprints: set[str] = set()
    diagnostics: tuple[str, ...] = ()

    for entry_index, resolved_parameters in enumerate(combinations):
        combination_fingerprint = generation_contract_fingerprint(resolved_parameters)
        combination = dict(resolved_parameters)
        try:
            phrases = tuple(
                _resolve_phrase(slot, combination)
                for slot in template.phrase_slots
            )
            program = GrammarProgram(
                program_id=_program_id(template, phrases),
                schema_version=GRAMMAR_SCHEMA_VERSION,
                phrases=phrases,
                dimensions_declared=(),
                intended_events=(),
                notes=(
                    f"Generated from template {template.template_id}.",
                ),
            )
            if program.program_fingerprint in seen_program_fingerprints:
                entries.append(
                    ManifestEntry(
                        entry_index=entry_index,
                        entry_id=f"ENTRY_{entry_index:06d}",
                        template_id=template.template_id,
                        family_tag=template.family_tag,
                        resolved_parameters=resolved_parameters,
                        combination_fingerprint=combination_fingerprint,
                        program_fingerprint=program.program_fingerprint,
                        generation_status="SKIPPED_DUPLICATE",
                        rejection_reason="DUPLICATE_PROGRAM_FINGERPRINT",
                        compilation_status="NOT_ATTEMPTED",
                        compilation_diagnostics=(),
                        geometry_fingerprint=None,
                        observation_checksum=None,
                        specification_fingerprint=None,
                    )
                )
                continue
            seen_program_fingerprints.add(program.program_fingerprint)
            programs.append(program)
            entries.append(
                ManifestEntry(
                    entry_index=entry_index,
                    entry_id=f"ENTRY_{entry_index:06d}",
                    template_id=template.template_id,
                    family_tag=template.family_tag,
                    resolved_parameters=resolved_parameters,
                    combination_fingerprint=combination_fingerprint,
                    program_fingerprint=program.program_fingerprint,
                    generation_status="GENERATED",
                    rejection_reason=None,
                    compilation_status="NOT_ATTEMPTED",
                    compilation_diagnostics=(),
                    geometry_fingerprint=None,
                    observation_checksum=None,
                    specification_fingerprint=None,
                )
            )
        except Exception as exc:
            entries.append(
                ManifestEntry(
                    entry_index=entry_index,
                    entry_id=f"ENTRY_{entry_index:06d}",
                    template_id=template.template_id,
                    family_tag=template.family_tag,
                    resolved_parameters=resolved_parameters,
                    combination_fingerprint=combination_fingerprint,
                    program_fingerprint=None,
                    generation_status="REJECTED_BY_RULE",
                    rejection_reason=f"{type(exc).__name__}:{exc}",
                    compilation_status="NOT_ATTEMPTED",
                    compilation_diagnostics=(),
                    geometry_fingerprint=None,
                    observation_checksum=None,
                    specification_fingerprint=None,
                )
            )

    generation_spec_fingerprint = generation_contract_fingerprint(template)
    manifest_id = f"MANIFEST_{template.template_id}_{generation_spec_fingerprint.split(':', 1)[1][:12].upper()}"
    entries_tuple = tuple(entries)
    manifest_fingerprint = _manifest_fingerprint(
        manifest_id=manifest_id,
        manifest_version="1",
        generation_spec_fingerprint=generation_spec_fingerprint,
        generator_version=generator_version,
        template_ids=(template.template_id,),
        entries=entries_tuple,
    )
    manifest = ScenarioManifest(
        manifest_id=manifest_id,
        manifest_version="1",
        campaign_id=None,
        generation_spec_fingerprint=generation_spec_fingerprint,
        generator_version=generator_version,
        template_ids=(template.template_id,),
        entries=entries_tuple,
        manifest_fingerprint=manifest_fingerprint,
    )
    program_fingerprints = tuple(program.program_fingerprint for program in programs)
    return GenerationResult(
        success=True,
        generated_programs=tuple(programs),
        manifest=manifest,
        diagnostics=diagnostics,
        generation_fingerprint=_generation_result_fingerprint(
            manifest_fingerprint=manifest.manifest_fingerprint,
            program_fingerprints=program_fingerprints,
            generator_version=generator_version,
            diagnostics=diagnostics,
        ),
        generator_version=generator_version,
    )
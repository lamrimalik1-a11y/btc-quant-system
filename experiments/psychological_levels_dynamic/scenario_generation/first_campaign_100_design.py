"""First 100-scenario Project 2 research campaign design.

Design/generation validation only: no compilation, assembly, batch execution,
Scenario Runner, Catalog execution, Stage 1-6, Project 1, or production calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    Direction,
    PathSmoothness,
    ZoneSide,
)
from experiments.psychological_levels_dynamic.scenario_generation.campaign_contracts import (
    CampaignFamilySpec,
    CampaignSpecification,
    campaign_specification_fingerprint_payload,
)
from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    GrammarTemplate,
    ParameterAxis,
    PhraseSlot,
    generation_contract_fingerprint,
)
from experiments.psychological_levels_dynamic.scenario_generation.generator import (
    GENERATOR_VERSION,
    MAX_GENERATED_PROGRAMS,
    GenerationResult,
    generate_programs,
)
from experiments.psychological_levels_dynamic.scenario_generation.manifest_validation import (
    VALIDATOR_VERSION,
    ManifestValidationResult,
    validate_manifest,
)

FIRST_CAMPAIGN_100_DESIGN_VERSION = "PHASE2D_SIGNAL_RICH_CAMPAIGN_100_DESIGN_V1"
FIRST_CAMPAIGN_ID = "PHASE2D_FIRST_RESEARCH_CAMPAIGN_100"
FIRST_CAMPAIGN_TARGET_COUNT = 100


@dataclass(frozen=True)
class CampaignFamilyDesignResult:
    family_name: str
    coverage_tags: tuple[str, ...]
    target_count: int
    generated_count: int
    manifest_validated: bool
    generation_result: GenerationResult
    manifest_validation_result: ManifestValidationResult
    family_design_fingerprint: str

    def __post_init__(self) -> None:
        if self.generated_count > MAX_GENERATED_PROGRAMS:
            raise ValueError("family generated_count exceeds MAX_GENERATED_PROGRAMS")
        if self.generated_count != self.target_count:
            raise ValueError("family generated_count must match target_count")


@dataclass(frozen=True)
class Campaign100DesignResult:
    success: bool
    campaign_specification: CampaignSpecification
    family_results: tuple[CampaignFamilyDesignResult, ...]
    total_generated: int
    campaign_design_fingerprint: str
    design_version: str
    diagnostics: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.total_generated != sum(family.generated_count for family in self.family_results):
            raise ValueError("family generated counts must reconcile to total_generated")
        if self.total_generated != self.campaign_specification.target_scenario_count:
            raise ValueError("total_generated must match campaign target_scenario_count")
        if self.success and self.diagnostics:
            raise ValueError("successful design cannot carry diagnostics")


def _slot(constructor_name: str, **params: object) -> PhraseSlot:
    return PhraseSlot(
        constructor_name=constructor_name,
        fixed_params=tuple(sorted(params.items())),
        axis_bound_params=(),
    )


def _axis_slot(
    constructor_name: str,
    *,
    axis_bindings: tuple[tuple[str, str], ...],
    **params: object,
) -> PhraseSlot:
    return PhraseSlot(
        constructor_name=constructor_name,
        fixed_params=tuple(sorted(params.items())),
        axis_bound_params=axis_bindings,
    )


def _outside(rows: int = 4, clearance: Decimal = Decimal("0.55")) -> PhraseSlot:
    return _slot(
        "hold_outside",
        row_budget=rows,
        target_zone="ZONE_A",
        side=ZoneSide.UPPER,
        clearance=clearance,
    )


def _enter(depth: Decimal = Decimal("0.20"), rows: int = 3) -> PhraseSlot:
    return _slot(
        "enter_zone",
        row_budget=rows,
        target_zone="ZONE_A",
        side=ZoneSide.LOWER,
        depth=depth,
    )


def _penetrate_axis(axis_name: str, rows: int = 4) -> PhraseSlot:
    return _axis_slot(
        "penetrate",
        axis_bindings=(("depth", axis_name),),
        row_budget=rows,
        target_zone="ZONE_A",
        side=ZoneSide.LOWER,
    )


def _penetrate_fixed(depth: Decimal, rows: int = 4) -> PhraseSlot:
    return _slot(
        "penetrate",
        row_budget=rows,
        target_zone="ZONE_A",
        side=ZoneSide.LOWER,
        depth=depth,
    )


def _penetration_cycle(depth_axis: str | None = None, *, fixed_depth: Decimal = Decimal("0.34")) -> tuple[PhraseSlot, ...]:
    penetrate_slot = _penetrate_axis(depth_axis) if depth_axis is not None else _penetrate_fixed(fixed_depth)
    return (_enter(), penetrate_slot, _outside())


def _repeat(pattern: tuple[PhraseSlot, ...], count: int) -> tuple[PhraseSlot, ...]:
    return tuple(slot for _ in range(count) for slot in pattern)


def _depth_axis(name: str, values: tuple[str, ...]) -> ParameterAxis:
    return ParameterAxis(name, tuple(Decimal(value) for value in values))


def _template(
    *,
    template_id: str,
    family_tag: str,
    description: str,
    phrase_slots: tuple[PhraseSlot, ...],
    axes: tuple[ParameterAxis, ...],
) -> GrammarTemplate:
    return GrammarTemplate(
        template_id=template_id,
        template_version="2",
        family_tag=family_tag,
        description=description,
        phrase_slots=phrase_slots,
        axes=axes,
        rules=(),
    )


def _family(
    *,
    family_name: str,
    template: GrammarTemplate,
    coverage_tags: tuple[str, ...],
    notes: str,
) -> CampaignFamilySpec:
    return CampaignFamilySpec(
        family_name=family_name,
        template=template,
        coverage_tags=coverage_tags,
        target_count=MAX_GENERATED_PROGRAMS,
        notes=notes,
    )


def _baseline_enter_exit() -> CampaignFamilySpec:
    return _family(
        family_name="BASELINE_ENTER_EXIT",
        template=_template(
            template_id="FIRST100_BASELINE_ENTER_EXIT_SIGNAL_RICH",
            family_tag="BASELINE_ENTER_EXIT",
            description="Repeated shallow enter/exit cycles kept within the viable entry envelope.",
            phrase_slots=_repeat((_axis_slot(
                "enter_zone",
                axis_bindings=(("depth", "depth"),),
                row_budget=3,
                target_zone="ZONE_A",
                side=ZoneSide.LOWER,
            ), _outside()), 5),
            axes=(_depth_axis("depth", ("0.10", "0.11", "0.12", "0.13", "0.14", "0.15", "0.16", "0.17", "0.18", "0.19")),),
        ),
        coverage_tags=("baseline_cycle", "repeated_enter_exit"),
        notes="Signal-rich baseline: five completed shallow enter/exit cycles per generated program.",
    )


def _direct_penetration() -> CampaignFamilySpec:
    return _family(
        family_name="DIRECT_PENETRATION",
        template=_template(
            template_id="FIRST100_DIRECT_PENETRATION_SIGNAL_RICH",
            family_tag="DIRECT_PENETRATION",
            description="Repeated enter/penetrate/exit cycles with one variable penetration depth.",
            phrase_slots=_repeat(_penetration_cycle("depth"), 5),
            axes=(_depth_axis("depth", ("0.22", "0.24", "0.26", "0.28", "0.30", "0.32", "0.34", "0.36", "0.38", "0.40")),),
        ),
        coverage_tags=("direct_penetration", "repeated_cycles"),
        notes="Main reliable signal mechanism: five repeated penetration visits.",
    )


def _progressive_penetration() -> CampaignFamilySpec:
    return _family(
        family_name="PROGRESSIVE_PENETRATION",
        template=_template(
            template_id="FIRST100_PROGRESSIVE_PENETRATION_SIGNAL_RICH",
            family_tag="PROGRESSIVE_PENETRATION",
            description="Five visits with increasing fixed penetration depths plus one variable final depth.",
            phrase_slots=(
                *_penetration_cycle(None, fixed_depth=Decimal("0.22")),
                *_penetration_cycle(None, fixed_depth=Decimal("0.26")),
                *_penetration_cycle(None, fixed_depth=Decimal("0.30")),
                *_penetration_cycle(None, fixed_depth=Decimal("0.34")),
                *_penetration_cycle("final_depth"),
            ),
            axes=(_depth_axis("final_depth", ("0.36", "0.38", "0.40", "0.42", "0.44", "0.46", "0.48", "0.50", "0.52", "0.54")),),
        ),
        coverage_tags=("progressive_depth", "penetration_sequence"),
        notes="Progressive within-scenario depth sequence with five complete visits.",
    )


def _weak_attacks() -> CampaignFamilySpec:
    return _family(
        family_name="WEAK_ATTACKS",
        template=_template(
            template_id="FIRST100_WEAK_ATTACKS_SIGNAL_RICH",
            family_tag="WEAK_ATTACKS",
            description="Repeated shallow penetration cycles inside the viable weak-depth envelope.",
            phrase_slots=_repeat(_penetration_cycle("depth"), 5),
            axes=(_depth_axis("depth", ("0.10", "0.11", "0.12", "0.13", "0.14", "0.15", "0.16", "0.17", "0.18", "0.19")),),
        ),
        coverage_tags=("weak_depth", "repeated_penetration"),
        notes="Weak attacks are shallow but repeated enough to produce completed visits.",
    )


def _strong_attacks() -> CampaignFamilySpec:
    return _family(
        family_name="STRONG_ATTACKS",
        template=_template(
            template_id="FIRST100_STRONG_ATTACKS_SIGNAL_RICH",
            family_tag="STRONG_ATTACKS",
            description="Repeated deeper penetration cycles.",
            phrase_slots=_repeat(_penetration_cycle("depth"), 5),
            axes=(_depth_axis("depth", ("0.42", "0.46", "0.50", "0.54", "0.58", "0.62", "0.66", "0.70", "0.74", "0.78")),),
        ),
        coverage_tags=("strong_depth", "repeated_penetration"),
        notes="Strong attacks use repeated complete penetration visits rather than single episodes.",
    )


def _accepted_break() -> CampaignFamilySpec:
    return _family(
        family_name="ACCEPTED_BREAK",
        template=_template(
            template_id="FIRST100_ACCEPTED_BREAK_SIGNAL_RICH",
            family_tag="ACCEPTED_BREAK",
            description="Repeated accepted-break macro cycles.",
            phrase_slots=_repeat((_axis_slot(
                "accepted_break",
                axis_bindings=(("clearance", "clearance"),),
                row_budget=12,
                target_zone="ZONE_A",
                side=ZoneSide.UPPER,
                acceptance_rows=4,
            ), _outside(rows=4, clearance=Decimal("0.60"))), 4),
            axes=(_depth_axis("clearance", ("0.22", "0.24", "0.26", "0.28", "0.30", "0.32", "0.34", "0.36", "0.38", "0.40")),),
        ),
        coverage_tags=("accepted_break", "repeated_macro_cycles"),
        notes="Accepted-break macro repeated four times with explicit outside residence.",
    )


def _reclaim() -> CampaignFamilySpec:
    return _family(
        family_name="RECLAIM",
        template=_template(
            template_id="FIRST100_RECLAIM_SIGNAL_RICH",
            family_tag="RECLAIM",
            description="Repeated reclaim macro cycles followed by clear outside exits.",
            phrase_slots=_repeat((_axis_slot(
                "reclaim",
                axis_bindings=(("depth", "depth"),),
                row_budget=12,
                target_zone="ZONE_A",
                side=ZoneSide.UPPER,
                residence_rows=4,
            ), _outside(rows=5, clearance=Decimal("0.55"))), 4),
            axes=(_depth_axis("depth", ("0.22", "0.24", "0.26", "0.28", "0.30", "0.32", "0.34", "0.36", "0.38", "0.40")),),
        ),
        coverage_tags=("reclaim", "repeated_macro_cycles"),
        notes="Reclaim macro repeated four times with clear post-reclaim exits.",
    )


def _ramp_to_entry() -> CampaignFamilySpec:
    return _family(
        family_name="RAMP_TO_ENTRY",
        template=_template(
            template_id="FIRST100_RAMP_TO_ENTRY_SIGNAL_RICH",
            family_tag="RAMP_TO_ENTRY",
            description="Ramp connector followed by repeated penetration cycles.",
            phrase_slots=(
                _axis_slot(
                    "ramp",
                    axis_bindings=(("distance", "distance"),),
                    row_budget=3,
                    target_zone="ZONE_A",
                    direction=Direction.UP,
                    smoothness=PathSmoothness.LINEAR,
                ),
                *_repeat(_penetration_cycle(None, fixed_depth=Decimal("0.30")), 4),
            ),
            axes=(_depth_axis("distance", ("0.02", "0.04", "0.06", "0.08", "0.10", "0.12", "0.14", "0.16", "0.18", "0.20")),),
        ),
        coverage_tags=("ramp_connector", "repeated_penetration"),
        notes="Ramp remains a connector; signal comes from repeated penetration cycles.",
    )


def _multi_return_cycles() -> CampaignFamilySpec:
    return _family(
        family_name="MULTI_RETURN_CYCLES",
        template=_template(
            template_id="FIRST100_MULTI_RETURN_CYCLES_SIGNAL_RICH",
            family_tag="MULTI_RETURN_CYCLES",
            description="Six repeated return cycles with viable shallow entries.",
            phrase_slots=_repeat((_axis_slot(
                "enter_zone",
                axis_bindings=(("depth", "depth"),),
                row_budget=3,
                target_zone="ZONE_A",
                side=ZoneSide.LOWER,
            ), _outside(rows=4, clearance=Decimal("0.55"))), 6),
            axes=(_depth_axis("depth", ("0.10", "0.11", "0.12", "0.13", "0.14", "0.15", "0.16", "0.17", "0.18", "0.19")),),
        ),
        coverage_tags=("multiple_returns", "repeated_visits"),
        notes="Multiple return-cycle coverage deliberately kept in the viable shallow range.",
    )


def _sparse_interaction() -> CampaignFamilySpec:
    return _family(
        family_name="SPARSE_INTERACTION",
        template=_template(
            template_id="FIRST100_SPARSE_INTERACTION_SIGNAL_RICH",
            family_tag="SPARSE_INTERACTION",
            description="Sparse but valid penetration visits separated by longer outside holds.",
            phrase_slots=(
                *_penetration_cycle(None, fixed_depth=Decimal("0.22")),
                _axis_slot(
                    "hold_outside",
                    axis_bindings=(("row_budget", "gap_rows"),),
                    target_zone="ZONE_A",
                    side=ZoneSide.UPPER,
                    clearance=Decimal("0.60"),
                ),
                *_penetration_cycle(None, fixed_depth=Decimal("0.26")),
                _axis_slot(
                    "hold_outside",
                    axis_bindings=(("row_budget", "gap_rows"),),
                    target_zone="ZONE_A",
                    side=ZoneSide.UPPER,
                    clearance=Decimal("0.60"),
                ),
                *_penetration_cycle(None, fixed_depth=Decimal("0.30")),
            ),
            axes=(ParameterAxis("gap_rows", (4, 5, 6, 7, 8, 9, 10, 11, 12, 13)),),
        ),
        coverage_tags=("sparse_interaction", "long_recovery_gap"),
        notes="Sparse interaction remains sparse but now has three complete visits per scenario.",
    )


def build_campaign_specification() -> CampaignSpecification:
    families = (
        _baseline_enter_exit(),
        _direct_penetration(),
        _progressive_penetration(),
        _weak_attacks(),
        _strong_attacks(),
        _accepted_break(),
        _reclaim(),
        _ramp_to_entry(),
        _multi_return_cycles(),
        _sparse_interaction(),
    )
    fingerprint = campaign_specification_fingerprint_payload(
        campaign_id=FIRST_CAMPAIGN_ID,
        campaign_version="2",
        campaign_goal="Design a signal-rich deterministic 100-scenario Project 2 research campaign.",
        families=families,
        target_scenario_count=FIRST_CAMPAIGN_TARGET_COUNT,
    )
    return CampaignSpecification(
        campaign_id=FIRST_CAMPAIGN_ID,
        campaign_version="2",
        campaign_goal="Design a signal-rich deterministic 100-scenario Project 2 research campaign.",
        families=families,
        target_scenario_count=FIRST_CAMPAIGN_TARGET_COUNT,
        campaign_specification_fingerprint=fingerprint,
    )


def _family_design_fingerprint(
    *,
    family: CampaignFamilySpec,
    generation: GenerationResult,
    validation: ManifestValidationResult,
) -> str:
    return generation_contract_fingerprint(
        (
            family.family_name,
            family.coverage_tags,
            generation.generation_fingerprint,
            validation.validation_fingerprint,
            FIRST_CAMPAIGN_100_DESIGN_VERSION,
        )
    )


def design_first_campaign_100(
    *,
    generator_version: str = GENERATOR_VERSION,
    validator_version: str = VALIDATOR_VERSION,
) -> Campaign100DesignResult:
    campaign = build_campaign_specification()
    family_results: list[CampaignFamilyDesignResult] = []
    diagnostics: list[str] = []

    for family in campaign.families:
        generation = generate_programs(family.template, generator_version)
        if generation.manifest is None:
            diagnostics.append(f"{family.family_name}:MISSING_MANIFEST")
            continue
        validation = validate_manifest(generation.manifest, validator_version)
        if not generation.success:
            diagnostics.extend(f"{family.family_name}:GENERATION:{item}" for item in generation.diagnostics)
        if not validation.success:
            diagnostics.extend(f"{family.family_name}:MANIFEST:{item}" for item in validation.diagnostics)
        family_results.append(
            CampaignFamilyDesignResult(
                family_name=family.family_name,
                coverage_tags=family.coverage_tags,
                target_count=family.target_count,
                generated_count=len(generation.generated_programs),
                manifest_validated=validation.success,
                generation_result=generation,
                manifest_validation_result=validation,
                family_design_fingerprint=_family_design_fingerprint(
                    family=family,
                    generation=generation,
                    validation=validation,
                ),
            )
        )

    total_generated = sum(family.generated_count for family in family_results)
    diagnostics_tuple = tuple(sorted(diagnostics))
    success = (
        len(family_results) == len(campaign.families)
        and total_generated == FIRST_CAMPAIGN_TARGET_COUNT
        and not diagnostics_tuple
        and all(family.manifest_validated for family in family_results)
    )
    campaign_design_fingerprint = generation_contract_fingerprint(
        (
            campaign.campaign_specification_fingerprint,
            tuple(family.family_design_fingerprint for family in family_results),
            total_generated,
            diagnostics_tuple,
            FIRST_CAMPAIGN_100_DESIGN_VERSION,
        )
    )
    return Campaign100DesignResult(
        success=success,
        campaign_specification=campaign,
        family_results=tuple(family_results),
        total_generated=total_generated,
        campaign_design_fingerprint=campaign_design_fingerprint,
        design_version=FIRST_CAMPAIGN_100_DESIGN_VERSION,
        diagnostics=diagnostics_tuple,
    )

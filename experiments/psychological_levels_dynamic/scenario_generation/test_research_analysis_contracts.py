"""Validation for immutable Project 2 research analysis contracts."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_generation.research_analysis_contracts import (
    ResearchAnalysisMetadata,
    ResearchCampaignAnalysis,
    ResearchCoverageAnalysis,
    ResearchFamilyAnalysis,
    ResearchHypothesisAnalysis,
    ResearchTrajectoryAnalysis,
    ResearchTransitionAnalysis,
    research_analysis_metadata_fingerprint_payload,
    research_campaign_analysis_fingerprint_payload,
    research_coverage_analysis_fingerprint_payload,
    research_family_analysis_fingerprint_payload,
    research_hypothesis_analysis_fingerprint_payload,
    research_trajectory_analysis_fingerprint_payload,
    research_transition_analysis_fingerprint_payload,
)

MODULE_PATH = Path(__file__).with_name("research_analysis_contracts.py")
FORBIDDEN_IMPORTS = (
    "campaign_designer",
    "campaign_contracts",
    "first_campaign_100_design",
    "generator",
    "manifest_validation",
    "batch_compiler",
    "batch_specification_assembler",
    "batch_execution",
    "research_report_generator",
    "research_report_contracts",
    "scenario_runner",
    "scenario_catalog.",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "core.",
    "engines.",
    "research.",
)
FORBIDDEN_SOURCE_TOKENS = (
    "run_campaign",
    "generate_programs",
    "validate_manifest",
    "compile_generation_batch",
    "assemble_batch",
    "execute_batch",
    "build_research_campaign_report",
    "ResearchCampaignReport",
    "CampaignDesignerResult",
    "ScenarioRunResult",
    "ScenarioExecutionRecord",
    "BatchExecutionResult",
    "GrammarTemplate",
    "ScenarioSpecification",
    "PriceObservation",
    "ResearchComparisonAnalysis",
)
BANNED_PROSE_FRAGMENTS = (
    "buy",
    "sell",
    "entry recommendation",
    "exit recommendation",
    "forecast",
    "strategy ranking",
    "machine learning",
    "learned threshold",
    "better",
    "stronger",
    "improved",
    "proven",
    "validated",
    "confirms",
    "suggests",
    "effect",
    "impact",
    "lift",
    "gain",
    "accuracy",
    "performance",
)


def _sha(label: str) -> str:
    return "sha256:" + label.lower().zfill(64)[-64:]


def _metadata() -> ResearchAnalysisMetadata:
    reports = (_sha("100"),)
    fingerprint = research_analysis_metadata_fingerprint_payload(
        analysis_id="ANALYSIS_A",
        analysis_version="1",
        analysis_engine_version="CONTRACT_ONLY",
        source_report_fingerprints=reports,
        source_campaign_result_fingerprint=_sha("101"),
        source_campaign_designer_fingerprint=_sha("102"),
    )
    return ResearchAnalysisMetadata(
        analysis_id="ANALYSIS_A",
        analysis_version="1",
        analysis_engine_version="CONTRACT_ONLY",
        source_report_fingerprints=reports,
        source_campaign_result_fingerprint=_sha("101"),
        source_campaign_designer_fingerprint=_sha("102"),
        metadata_fingerprint=fingerprint,
    )


def _family(
    name: str,
    tags: tuple[str, ...],
    *,
    visits: int,
    transitions: int,
    trajectories: int,
    eligible: int,
    confirmed: int,
    pending: int,
    richness: str,
) -> ResearchFamilyAnalysis:
    fingerprint = research_family_analysis_fingerprint_payload(
        family_name=name,
        coverage_tags=tags,
        scenarios_generated=10,
        scenarios_executed=10,
        pass_count=10,
        fail_count=0,
        skipped_count=0,
        completed_visits=visits,
        zero_visit_scenarios=0,
        scenarios_with_three_or_more_visits=10,
        transitions=transitions,
        trajectory_records=trajectories,
        eligible_hypotheses=eligible,
        confirmed_hypotheses=confirmed,
        pending_hypotheses=pending,
        visit_density=Decimal(visits) / Decimal("10"),
        transition_density=Decimal(transitions) / Decimal("10"),
        trajectory_density=Decimal(trajectories) / Decimal("10"),
        eligibility_rate=Decimal(eligible) / Decimal("10"),
        confirmation_rate=Decimal(confirmed) / Decimal(eligible) if eligible else None,
        pending_rate=Decimal(pending) / Decimal(eligible) if eligible else None,
        signal_dimension_count=sum(1 for value in (visits, transitions, trajectories, eligible) if value > 0),
        signal_richness_class=richness,
        sample_sufficiency_class="SUFFICIENT_SAMPLE" if eligible else "INSUFFICIENT_SAMPLE",
    )
    return ResearchFamilyAnalysis(
        family_name=name,
        coverage_tags=tags,
        scenarios_generated=10,
        scenarios_executed=10,
        pass_count=10,
        fail_count=0,
        skipped_count=0,
        completed_visits=visits,
        zero_visit_scenarios=0,
        scenarios_with_three_or_more_visits=10,
        transitions=transitions,
        trajectory_records=trajectories,
        eligible_hypotheses=eligible,
        confirmed_hypotheses=confirmed,
        pending_hypotheses=pending,
        visit_density=Decimal(visits) / Decimal("10"),
        transition_density=Decimal(transitions) / Decimal("10"),
        trajectory_density=Decimal(trajectories) / Decimal("10"),
        eligibility_rate=Decimal(eligible) / Decimal("10"),
        confirmation_rate=Decimal(confirmed) / Decimal(eligible) if eligible else None,
        pending_rate=Decimal(pending) / Decimal(eligible) if eligible else None,
        signal_dimension_count=sum(1 for value in (visits, transitions, trajectories, eligible) if value > 0),
        signal_richness_class=richness,
        sample_sufficiency_class="SUFFICIENT_SAMPLE" if eligible else "INSUFFICIENT_SAMPLE",
        family_analysis_fingerprint=fingerprint,
    )


def _families() -> tuple[ResearchFamilyAnalysis, ...]:
    return (
        _family(
            "ALPHA_FAMILY",
            ("alpha_tag", "shared_tag"),
            visits=46,
            transitions=26,
            trajectories=46,
            eligible=8,
            confirmed=2,
            pending=6,
            richness="RICH_SIGNAL",
        ),
        _family(
            "BETA_FAMILY",
            ("beta_tag", "shared_tag"),
            visits=40,
            transitions=20,
            trajectories=40,
            eligible=0,
            confirmed=0,
            pending=0,
            richness="MEDIUM_SIGNAL",
        ),
    )


def _coverage() -> ResearchCoverageAnalysis:
    fingerprint = research_coverage_analysis_fingerprint_payload(
        families_observed=2,
        scenarios_generated=20,
        scenarios_executed=20,
        zero_visit_scenarios=0,
        scenarios_with_three_or_more_visits=20,
        scenarios_with_transitions=20,
        zero_visit_rate=Decimal("0"),
        three_plus_visit_rate=Decimal("1"),
        transition_coverage_rate=Decimal("1"),
        coverage_tag_family_counts=(("alpha_tag", 1), ("beta_tag", 1), ("shared_tag", 2)),
        unique_coverage_tags=("alpha_tag", "beta_tag", "shared_tag"),
        shared_coverage_tags=("shared_tag",),
    )
    return ResearchCoverageAnalysis(
        families_observed=2,
        scenarios_generated=20,
        scenarios_executed=20,
        zero_visit_scenarios=0,
        scenarios_with_three_or_more_visits=20,
        scenarios_with_transitions=20,
        zero_visit_rate=Decimal("0"),
        three_plus_visit_rate=Decimal("1"),
        transition_coverage_rate=Decimal("1"),
        coverage_tag_family_counts=(("alpha_tag", 1), ("beta_tag", 1), ("shared_tag", 2)),
        unique_coverage_tags=("alpha_tag", "beta_tag", "shared_tag"),
        shared_coverage_tags=("shared_tag",),
        coverage_analysis_fingerprint=fingerprint,
    )


def _transition() -> ResearchTransitionAnalysis:
    rows = (("ALPHA_FAMILY", 26), ("BETA_FAMILY", 20))
    fingerprint = research_transition_analysis_fingerprint_payload(
        total_transitions=46,
        scenarios_with_transitions=20,
        per_family_transition_counts=rows,
        transition_density=Decimal("2.3"),
        top_transition_contributor_family_name="ALPHA_FAMILY",
        top_transition_contributor_share=Decimal(26) / Decimal(46),
        families_with_zero_transitions=(),
    )
    return ResearchTransitionAnalysis(
        total_transitions=46,
        scenarios_with_transitions=20,
        per_family_transition_counts=rows,
        transition_density=Decimal("2.3"),
        top_transition_contributor_family_name="ALPHA_FAMILY",
        top_transition_contributor_share=Decimal(26) / Decimal(46),
        families_with_zero_transitions=(),
        transition_analysis_fingerprint=fingerprint,
    )


def _trajectory() -> ResearchTrajectoryAnalysis:
    rows = (("ALPHA_FAMILY", 46), ("BETA_FAMILY", 40))
    fingerprint = research_trajectory_analysis_fingerprint_payload(
        total_trajectory_records=86,
        per_family_trajectory_records=rows,
        trajectory_density=Decimal("4.3"),
        top_trajectory_contributor_family_name="ALPHA_FAMILY",
        top_trajectory_contributor_share=Decimal(46) / Decimal(86),
        families_with_zero_trajectory_records=(),
    )
    return ResearchTrajectoryAnalysis(
        total_trajectory_records=86,
        per_family_trajectory_records=rows,
        trajectory_density=Decimal("4.3"),
        top_trajectory_contributor_family_name="ALPHA_FAMILY",
        top_trajectory_contributor_share=Decimal(46) / Decimal(86),
        families_with_zero_trajectory_records=(),
        trajectory_analysis_fingerprint=fingerprint,
    )


def _hypothesis() -> ResearchHypothesisAnalysis:
    rows = (("ALPHA_FAMILY", 8, 2, 6), ("BETA_FAMILY", 0, 0, 0))
    fingerprint = research_hypothesis_analysis_fingerprint_payload(
        eligible_hypotheses=8,
        confirmed_hypotheses=2,
        pending_hypotheses=6,
        per_family_hypothesis_counts=rows,
        eligibility_rate=Decimal("0.4"),
        confirmation_rate=Decimal("0.25"),
        pending_rate=Decimal("0.75"),
        top_eligible_hypothesis_family_name="ALPHA_FAMILY",
        top_eligible_hypothesis_family_share=Decimal("1"),
        families_with_no_eligible_hypotheses=("BETA_FAMILY",),
    )
    return ResearchHypothesisAnalysis(
        eligible_hypotheses=8,
        confirmed_hypotheses=2,
        pending_hypotheses=6,
        per_family_hypothesis_counts=rows,
        eligibility_rate=Decimal("0.4"),
        confirmation_rate=Decimal("0.25"),
        pending_rate=Decimal("0.75"),
        top_eligible_hypothesis_family_name="ALPHA_FAMILY",
        top_eligible_hypothesis_family_share=Decimal("1"),
        families_with_no_eligible_hypotheses=("BETA_FAMILY",),
        hypothesis_analysis_fingerprint=fingerprint,
    )


def _analysis() -> ResearchCampaignAnalysis:
    metadata = _metadata()
    families = _families()
    coverage = _coverage()
    transition = _transition()
    trajectory = _trajectory()
    hypothesis = _hypothesis()
    diagnostics: tuple[str, ...] = ()
    fingerprint = research_campaign_analysis_fingerprint_payload(
        metadata=metadata,
        family_analyses=families,
        coverage_analysis=coverage,
        transition_analysis=transition,
        trajectory_analysis=trajectory,
        hypothesis_analysis=hypothesis,
        diagnostics=diagnostics,
    )
    return ResearchCampaignAnalysis(
        metadata=metadata,
        family_analyses=families,
        coverage_analysis=coverage,
        transition_analysis=transition,
        trajectory_analysis=trajectory,
        hypothesis_analysis=hypothesis,
        diagnostics=diagnostics,
        campaign_analysis_fingerprint=fingerprint,
    )


def _zero_denominator_family() -> ResearchFamilyAnalysis:
    fingerprint = research_family_analysis_fingerprint_payload(
        family_name="ZERO_FAMILY",
        coverage_tags=("zero_tag",),
        scenarios_generated=0,
        scenarios_executed=0,
        pass_count=0,
        fail_count=0,
        skipped_count=0,
        completed_visits=0,
        zero_visit_scenarios=0,
        scenarios_with_three_or_more_visits=0,
        transitions=0,
        trajectory_records=0,
        eligible_hypotheses=0,
        confirmed_hypotheses=0,
        pending_hypotheses=0,
        visit_density=None,
        transition_density=None,
        trajectory_density=None,
        eligibility_rate=None,
        confirmation_rate=None,
        pending_rate=None,
        signal_dimension_count=0,
        signal_richness_class="NO_SIGNAL",
        sample_sufficiency_class="NOT_APPLICABLE",
    )
    return ResearchFamilyAnalysis(
        family_name="ZERO_FAMILY",
        coverage_tags=("zero_tag",),
        scenarios_generated=0,
        scenarios_executed=0,
        pass_count=0,
        fail_count=0,
        skipped_count=0,
        completed_visits=0,
        zero_visit_scenarios=0,
        scenarios_with_three_or_more_visits=0,
        transitions=0,
        trajectory_records=0,
        eligible_hypotheses=0,
        confirmed_hypotheses=0,
        pending_hypotheses=0,
        visit_density=None,
        transition_density=None,
        trajectory_density=None,
        eligibility_rate=None,
        confirmation_rate=None,
        pending_rate=None,
        signal_dimension_count=0,
        signal_richness_class="NO_SIGNAL",
        sample_sufficiency_class="NOT_APPLICABLE",
        family_analysis_fingerprint=fingerprint,
    )


def _contains_raw_upstream_object(value: Any) -> bool:
    type_name = type(value).__name__
    if type_name in {
        "ResearchCampaignReport",
        "CampaignDesignerResult",
        "ScenarioRunResult",
        "ScenarioExecutionRecord",
        "BatchExecutionResult",
    }:
        return True
    if isinstance(value, tuple):
        return any(_contains_raw_upstream_object(item) for item in value)
    if is_dataclass(value):
        return any(_contains_raw_upstream_object(getattr(value, field.name)) for field in fields(value))
    return False


def _cross_process_analysis_fingerprint() -> str:
    env = dict(os.environ)
    env["RESEARCH_ANALYSIS_CONTRACTS_CHILD"] = "1"
    return subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env).strip()


def _semantic_family(**overrides: Any) -> ResearchFamilyAnalysis:
    params = {
        "family_name": "ALPHA_FAMILY",
        "coverage_tags": ("alpha_tag", "shared_tag"),
        "scenarios_generated": 10,
        "scenarios_executed": 10,
        "pass_count": 10,
        "fail_count": 0,
        "skipped_count": 0,
        "completed_visits": 46,
        "zero_visit_scenarios": 0,
        "scenarios_with_three_or_more_visits": 10,
        "transitions": 26,
        "trajectory_records": 46,
        "eligible_hypotheses": 8,
        "confirmed_hypotheses": 2,
        "pending_hypotheses": 6,
        "visit_density": Decimal("4.6"),
        "transition_density": Decimal("2.6"),
        "trajectory_density": Decimal("4.6"),
        "eligibility_rate": Decimal("0.8"),
        "confirmation_rate": Decimal("0.25"),
        "pending_rate": Decimal("0.75"),
        "signal_dimension_count": 4,
        "signal_richness_class": "RICH_SIGNAL",
        "sample_sufficiency_class": "SUFFICIENT_SAMPLE",
    }
    params.update(overrides)
    params["family_analysis_fingerprint"] = research_family_analysis_fingerprint_payload(**params)
    return ResearchFamilyAnalysis(**params)


def _semantic_coverage(**overrides: Any) -> ResearchCoverageAnalysis:
    params = {
        "families_observed": 2,
        "scenarios_generated": 20,
        "scenarios_executed": 20,
        "zero_visit_scenarios": 0,
        "scenarios_with_three_or_more_visits": 20,
        "scenarios_with_transitions": 20,
        "zero_visit_rate": Decimal("0"),
        "three_plus_visit_rate": Decimal("1"),
        "transition_coverage_rate": Decimal("1"),
        "coverage_tag_family_counts": (("alpha_tag", 1), ("beta_tag", 1), ("shared_tag", 2)),
        "unique_coverage_tags": ("alpha_tag", "beta_tag", "shared_tag"),
        "shared_coverage_tags": ("shared_tag",),
    }
    params.update(overrides)
    params["coverage_analysis_fingerprint"] = research_coverage_analysis_fingerprint_payload(**params)
    return ResearchCoverageAnalysis(**params)


def _semantic_transition(**overrides: Any) -> ResearchTransitionAnalysis:
    params = {
        "total_transitions": 46,
        "scenarios_with_transitions": 20,
        "per_family_transition_counts": (("ALPHA_FAMILY", 26), ("BETA_FAMILY", 20)),
        "transition_density": Decimal("2.3"),
        "top_transition_contributor_family_name": "ALPHA_FAMILY",
        "top_transition_contributor_share": Decimal(26) / Decimal(46),
        "families_with_zero_transitions": (),
    }
    params.update(overrides)
    params["transition_analysis_fingerprint"] = research_transition_analysis_fingerprint_payload(**params)
    return ResearchTransitionAnalysis(**params)


def _semantic_trajectory(**overrides: Any) -> ResearchTrajectoryAnalysis:
    params = {
        "total_trajectory_records": 86,
        "per_family_trajectory_records": (("ALPHA_FAMILY", 46), ("BETA_FAMILY", 40)),
        "trajectory_density": Decimal("4.3"),
        "top_trajectory_contributor_family_name": "ALPHA_FAMILY",
        "top_trajectory_contributor_share": Decimal(46) / Decimal(86),
        "families_with_zero_trajectory_records": (),
    }
    params.update(overrides)
    params["trajectory_analysis_fingerprint"] = research_trajectory_analysis_fingerprint_payload(**params)
    return ResearchTrajectoryAnalysis(**params)


def _semantic_hypothesis(**overrides: Any) -> ResearchHypothesisAnalysis:
    params = {
        "eligible_hypotheses": 8,
        "confirmed_hypotheses": 2,
        "pending_hypotheses": 6,
        "per_family_hypothesis_counts": (("ALPHA_FAMILY", 8, 2, 6), ("BETA_FAMILY", 0, 0, 0)),
        "eligibility_rate": Decimal("0.4"),
        "confirmation_rate": Decimal("0.25"),
        "pending_rate": Decimal("0.75"),
        "top_eligible_hypothesis_family_name": "ALPHA_FAMILY",
        "top_eligible_hypothesis_family_share": Decimal("1"),
        "families_with_no_eligible_hypotheses": ("BETA_FAMILY",),
    }
    params.update(overrides)
    params["hypothesis_analysis_fingerprint"] = research_hypothesis_analysis_fingerprint_payload(**params)
    return ResearchHypothesisAnalysis(**params)


def _semantic_rejected(factory: Any) -> bool:
    try:
        factory()
    except ValueError:
        return True
    return False
def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "valid_construction": False,
        "invalid_fingerprint_rejection": False,
        "immutability": False,
        "tuple_only_containers": False,
        "deterministic_fingerprints": False,
        "canonical_ordering": False,
        "count_and_rate_reconciliation": False,
        "identity_level_family_reconciliation": False,
        "zero_denominator_rate_behavior": False,
        "classification_determinism": False,
        "cross_process_determinism": False,
        "forbidden_imports": False,
        "banned_language_scan": False,
        "no_execution_generation_report_regeneration_logic": False,
        "no_comparison_logic": False,
        "no_raw_upstream_objects_embedded": False,
        "research_isolation": False,
        "incorrect_visit_density_rejected": False,
        "incorrect_confirmation_rate_rejected": False,
        "incorrect_pending_rate_rejected": False,
        "incorrect_transition_density_rejected": False,
        "incorrect_trajectory_density_rejected": False,
        "incorrect_eligibility_rate_rejected": False,
        "incorrect_top_transition_contributor_rejected": False,
        "incorrect_top_trajectory_contributor_rejected": False,
        "incorrect_top_hypothesis_contributor_rejected": False,
        "inconsistent_coverage_tag_family_counts_rejected": False,
        "inconsistent_unique_shared_coverage_tags_rejected": False,
        "invalid_signal_dimension_count_rejected": False,
        "per_family_visit_coverage_reconciliation_rejected": False,
    }
    fingerprint = ""
    try:
        analysis = _analysis()
        assert isinstance(analysis.metadata, ResearchAnalysisMetadata)
        assert isinstance(analysis.coverage_analysis, ResearchCoverageAnalysis)
        assert isinstance(analysis.transition_analysis, ResearchTransitionAnalysis)
        assert isinstance(analysis.trajectory_analysis, ResearchTrajectoryAnalysis)
        assert isinstance(analysis.hypothesis_analysis, ResearchHypothesisAnalysis)
        checks["valid_construction"] = True

        try:
            ResearchAnalysisMetadata(
                analysis_id="BAD",
                analysis_version="1",
                analysis_engine_version="CONTRACT_ONLY",
                source_report_fingerprints=(_sha("1"),),
                source_campaign_result_fingerprint=_sha("2"),
                source_campaign_designer_fingerprint=_sha("3"),
                metadata_fingerprint="bad",
            )
        except ValueError:
            checks["invalid_fingerprint_rejection"] = True

        try:
            analysis.metadata.analysis_id = "MUTATE"
        except FrozenInstanceError:
            checks["immutability"] = True

        checks["tuple_only_containers"] = (
            isinstance(analysis.metadata.source_report_fingerprints, tuple)
            and isinstance(analysis.family_analyses, tuple)
            and isinstance(analysis.coverage_analysis.coverage_tag_family_counts, tuple)
            and isinstance(analysis.transition_analysis.per_family_transition_counts, tuple)
            and isinstance(analysis.hypothesis_analysis.per_family_hypothesis_counts, tuple)
        )

        repeat = _analysis()
        assert repeat == analysis
        assert repeat.campaign_analysis_fingerprint == analysis.campaign_analysis_fingerprint
        fingerprint = analysis.campaign_analysis_fingerprint
        checks["deterministic_fingerprints"] = True

        try:
            ResearchCoverageAnalysis(
                families_observed=1,
                scenarios_generated=1,
                scenarios_executed=1,
                zero_visit_scenarios=0,
                scenarios_with_three_or_more_visits=1,
                scenarios_with_transitions=1,
                zero_visit_rate=Decimal("0"),
                three_plus_visit_rate=Decimal("1"),
                transition_coverage_rate=Decimal("1"),
                coverage_tag_family_counts=(("z", 1), ("a", 1)),
                unique_coverage_tags=("a", "z"),
                shared_coverage_tags=(),
                coverage_analysis_fingerprint=_sha("9"),
            )
        except ValueError:
            checks["canonical_ordering"] = True

        try:
            ResearchCoverageAnalysis(
                families_observed=1,
                scenarios_generated=0,
                scenarios_executed=0,
                zero_visit_scenarios=0,
                scenarios_with_three_or_more_visits=0,
                scenarios_with_transitions=0,
                zero_visit_rate=Decimal("0"),
                three_plus_visit_rate=None,
                transition_coverage_rate=None,
                coverage_tag_family_counts=(),
                unique_coverage_tags=(),
                shared_coverage_tags=(),
                coverage_analysis_fingerprint=_sha("10"),
            )
        except ValueError:
            checks["count_and_rate_reconciliation"] = True

        try:
            wrong_hypothesis = ResearchHypothesisAnalysis(
                eligible_hypotheses=8,
                confirmed_hypotheses=2,
                pending_hypotheses=6,
                per_family_hypothesis_counts=(("ALPHA_FAMILY", 7, 2, 5), ("BETA_FAMILY", 1, 0, 1)),
                eligibility_rate=Decimal("0.4"),
                confirmation_rate=Decimal("0.25"),
                pending_rate=Decimal("0.75"),
                top_eligible_hypothesis_family_name="ALPHA_FAMILY",
                top_eligible_hypothesis_family_share=Decimal("0.875"),
                families_with_no_eligible_hypotheses=(),
                hypothesis_analysis_fingerprint=research_hypothesis_analysis_fingerprint_payload(
                    eligible_hypotheses=8,
                    confirmed_hypotheses=2,
                    pending_hypotheses=6,
                    per_family_hypothesis_counts=(("ALPHA_FAMILY", 7, 2, 5), ("BETA_FAMILY", 1, 0, 1)),
                    eligibility_rate=Decimal("0.4"),
                    confirmation_rate=Decimal("0.25"),
                    pending_rate=Decimal("0.75"),
                    top_eligible_hypothesis_family_name="ALPHA_FAMILY",
                    top_eligible_hypothesis_family_share=Decimal("0.875"),
                    families_with_no_eligible_hypotheses=(),
                ),
            )
            ResearchCampaignAnalysis(
                metadata=analysis.metadata,
                family_analyses=analysis.family_analyses,
                coverage_analysis=analysis.coverage_analysis,
                transition_analysis=analysis.transition_analysis,
                trajectory_analysis=analysis.trajectory_analysis,
                hypothesis_analysis=wrong_hypothesis,
                diagnostics=(),
                campaign_analysis_fingerprint=research_campaign_analysis_fingerprint_payload(
                    metadata=analysis.metadata,
                    family_analyses=analysis.family_analyses,
                    coverage_analysis=analysis.coverage_analysis,
                    transition_analysis=analysis.transition_analysis,
                    trajectory_analysis=analysis.trajectory_analysis,
                    hypothesis_analysis=wrong_hypothesis,
                    diagnostics=(),
                ),
            )
        except ValueError:
            checks["identity_level_family_reconciliation"] = True

        zero_family = _zero_denominator_family()
        checks["zero_denominator_rate_behavior"] = all(
            value is None
            for value in (
                zero_family.visit_density,
                zero_family.transition_density,
                zero_family.trajectory_density,
                zero_family.eligibility_rate,
                zero_family.confirmation_rate,
                zero_family.pending_rate,
            )
        )


        checks["incorrect_visit_density_rejected"] = _semantic_rejected(lambda: _semantic_family(visit_density=Decimal("4.7")))
        checks["incorrect_confirmation_rate_rejected"] = _semantic_rejected(lambda: _semantic_family(confirmation_rate=Decimal("0.30")))
        checks["incorrect_pending_rate_rejected"] = _semantic_rejected(lambda: _semantic_family(pending_rate=Decimal("0.70")))
        checks["incorrect_transition_density_rejected"] = _semantic_rejected(lambda: _semantic_family(transition_density=Decimal("2.7")))
        checks["incorrect_trajectory_density_rejected"] = _semantic_rejected(lambda: _semantic_family(trajectory_density=Decimal("4.7")))
        checks["incorrect_eligibility_rate_rejected"] = _semantic_rejected(lambda: _semantic_family(eligibility_rate=Decimal("0.9")))
        checks["incorrect_top_transition_contributor_rejected"] = _semantic_rejected(
            lambda: _semantic_transition(top_transition_contributor_family_name="BETA_FAMILY")
        )
        checks["incorrect_top_trajectory_contributor_rejected"] = _semantic_rejected(
            lambda: _semantic_trajectory(top_trajectory_contributor_family_name="BETA_FAMILY")
        )
        checks["incorrect_top_hypothesis_contributor_rejected"] = _semantic_rejected(
            lambda: _semantic_hypothesis(top_eligible_hypothesis_family_name="BETA_FAMILY")
        )
        bad_coverage_counts = _semantic_coverage(
            coverage_tag_family_counts=(("alpha_tag", 2), ("beta_tag", 1), ("shared_tag", 2))
        )
        checks["inconsistent_coverage_tag_family_counts_rejected"] = _semantic_rejected(
            lambda: ResearchCampaignAnalysis(
                metadata=analysis.metadata,
                family_analyses=analysis.family_analyses,
                coverage_analysis=bad_coverage_counts,
                transition_analysis=analysis.transition_analysis,
                trajectory_analysis=analysis.trajectory_analysis,
                hypothesis_analysis=analysis.hypothesis_analysis,
                diagnostics=(),
                campaign_analysis_fingerprint=research_campaign_analysis_fingerprint_payload(
                    metadata=analysis.metadata,
                    family_analyses=analysis.family_analyses,
                    coverage_analysis=bad_coverage_counts,
                    transition_analysis=analysis.transition_analysis,
                    trajectory_analysis=analysis.trajectory_analysis,
                    hypothesis_analysis=analysis.hypothesis_analysis,
                    diagnostics=(),
                ),
            )
        )
        bad_coverage_tags = _semantic_coverage(
            unique_coverage_tags=("alpha_tag", "beta_tag", "other_tag", "shared_tag"),
            shared_coverage_tags=("other_tag",),
        )
        checks["inconsistent_unique_shared_coverage_tags_rejected"] = _semantic_rejected(
            lambda: ResearchCampaignAnalysis(
                metadata=analysis.metadata,
                family_analyses=analysis.family_analyses,
                coverage_analysis=bad_coverage_tags,
                transition_analysis=analysis.transition_analysis,
                trajectory_analysis=analysis.trajectory_analysis,
                hypothesis_analysis=analysis.hypothesis_analysis,
                diagnostics=(),
                campaign_analysis_fingerprint=research_campaign_analysis_fingerprint_payload(
                    metadata=analysis.metadata,
                    family_analyses=analysis.family_analyses,
                    coverage_analysis=bad_coverage_tags,
                    transition_analysis=analysis.transition_analysis,
                    trajectory_analysis=analysis.trajectory_analysis,
                    hypothesis_analysis=analysis.hypothesis_analysis,
                    diagnostics=(),
                ),
            )
        )
        checks["invalid_signal_dimension_count_rejected"] = _semantic_rejected(lambda: _semantic_family(signal_dimension_count=5))
        bad_visit_coverage = _semantic_coverage(zero_visit_scenarios=1, zero_visit_rate=Decimal("0.05"))
        checks["per_family_visit_coverage_reconciliation_rejected"] = _semantic_rejected(
            lambda: ResearchCampaignAnalysis(
                metadata=analysis.metadata,
                family_analyses=analysis.family_analyses,
                coverage_analysis=bad_visit_coverage,
                transition_analysis=analysis.transition_analysis,
                trajectory_analysis=analysis.trajectory_analysis,
                hypothesis_analysis=analysis.hypothesis_analysis,
                diagnostics=(),
                campaign_analysis_fingerprint=research_campaign_analysis_fingerprint_payload(
                    metadata=analysis.metadata,
                    family_analyses=analysis.family_analyses,
                    coverage_analysis=bad_visit_coverage,
                    transition_analysis=analysis.transition_analysis,
                    trajectory_analysis=analysis.trajectory_analysis,
                    hypothesis_analysis=analysis.hypothesis_analysis,
                    diagnostics=(),
                ),
            )
        )

        bad_campaign_trajectory = _semantic_trajectory(trajectory_density=Decimal("4.4"))
        checks["campaign_trajectory_density_rejected"] = _semantic_rejected(
            lambda: ResearchCampaignAnalysis(
                metadata=analysis.metadata,
                family_analyses=analysis.family_analyses,
                coverage_analysis=analysis.coverage_analysis,
                transition_analysis=analysis.transition_analysis,
                trajectory_analysis=bad_campaign_trajectory,
                hypothesis_analysis=analysis.hypothesis_analysis,
                diagnostics=(),
                campaign_analysis_fingerprint=research_campaign_analysis_fingerprint_payload(
                    metadata=analysis.metadata,
                    family_analyses=analysis.family_analyses,
                    coverage_analysis=analysis.coverage_analysis,
                    transition_analysis=analysis.transition_analysis,
                    trajectory_analysis=bad_campaign_trajectory,
                    hypothesis_analysis=analysis.hypothesis_analysis,
                    diagnostics=(),
                ),
            )
        )
        bad_campaign_hypothesis = _semantic_hypothesis(eligibility_rate=Decimal("0.5"))
        checks["campaign_hypothesis_eligibility_rate_rejected"] = _semantic_rejected(
            lambda: ResearchCampaignAnalysis(
                metadata=analysis.metadata,
                family_analyses=analysis.family_analyses,
                coverage_analysis=analysis.coverage_analysis,
                transition_analysis=analysis.transition_analysis,
                trajectory_analysis=analysis.trajectory_analysis,
                hypothesis_analysis=bad_campaign_hypothesis,
                diagnostics=(),
                campaign_analysis_fingerprint=research_campaign_analysis_fingerprint_payload(
                    metadata=analysis.metadata,
                    family_analyses=analysis.family_analyses,
                    coverage_analysis=analysis.coverage_analysis,
                    transition_analysis=analysis.transition_analysis,
                    trajectory_analysis=analysis.trajectory_analysis,
                    hypothesis_analysis=bad_campaign_hypothesis,
                    diagnostics=(),
                ),
            )
        )
        checks["classification_determinism"] = tuple(
            family.signal_richness_class for family in _analysis().family_analyses
        ) == tuple(family.signal_richness_class for family in _analysis().family_analyses)

        if os.environ.get("RESEARCH_ANALYSIS_CONTRACTS_CHILD") == "1":
            checks["cross_process_determinism"] = True
        else:
            first = _cross_process_analysis_fingerprint()
            second = _cross_process_analysis_fingerprint()
            assert first == second == analysis.campaign_analysis_fingerprint
            checks["cross_process_determinism"] = True

        source = MODULE_PATH.read_text(encoding="utf-8")
        lower_source = source.lower()
        imports = "\n".join(
            line.strip()
            for line in lower_source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        checks["forbidden_imports"] = not any(token.lower() in imports for token in FORBIDDEN_IMPORTS)
        checks["no_execution_generation_report_regeneration_logic"] = not any(
            token.lower() in lower_source for token in FORBIDDEN_SOURCE_TOKENS
        )
        checks["no_comparison_logic"] = "researchcomparisonanalysis" not in lower_source and "compare_" not in lower_source
        checks["banned_language_scan"] = not any(fragment in lower_source for fragment in BANNED_PROSE_FRAGMENTS)
        checks["research_isolation"] = checks["forbidden_imports"] and checks["no_execution_generation_report_regeneration_logic"]
        checks["no_raw_upstream_objects_embedded"] = not _contains_raw_upstream_object(analysis)
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    return {
        "checks": checks,
        "errors": errors,
        "fingerprint": fingerprint,
        "result": "PASS" if all(checks.values()) and not errors else "FAIL",
    }


def main() -> None:
    report = run()
    if os.environ.get("RESEARCH_ANALYSIS_CONTRACTS_CHILD") == "1":
        print(report["fingerprint"])
        return
    for name, passed in report["checks"].items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"errors: {report['errors']}")
    print(f"fingerprint: {report['fingerprint']}")
    print(f"result: {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

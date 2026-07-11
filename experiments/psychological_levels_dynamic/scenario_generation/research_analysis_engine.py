"""Pure analysis construction for one Project 2 research campaign report.

Consumes only immutable ResearchCampaignReport contracts and returns immutable
ResearchCampaignAnalysis contracts. No campaign execution, report generation,
file I/O, raw stage payload inspection, or interpretive outputs.
"""

from __future__ import annotations

from decimal import Decimal

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
from experiments.psychological_levels_dynamic.scenario_generation.research_report_contracts import (
    ResearchCampaignReport,
)

RESEARCH_ANALYSIS_ENGINE_VERSION = "PHASE2E_RESEARCH_ANALYSIS_ENGINE_V1"


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _rate(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return Decimal(numerator) / Decimal(denominator)


def _signal_dimension_count(
    *,
    completed_visits: int,
    transitions: int,
    trajectory_records: int,
    eligible_hypotheses: int,
) -> int:
    return sum(
        1
        for value in (
            completed_visits,
            transitions,
            trajectory_records,
            eligible_hypotheses,
        )
        if value > 0
    )


def _signal_richness_class(signal_dimension_count: int) -> str:
    if signal_dimension_count == 0:
        return "NO_SIGNAL"
    if signal_dimension_count == 1:
        return "LOW_SIGNAL"
    if signal_dimension_count in (2, 3):
        return "MEDIUM_SIGNAL"
    return "RICH_SIGNAL"


def _sample_sufficiency_class(*, scenarios_generated: int, eligible_hypotheses: int) -> str:
    if scenarios_generated == 0:
        return "NOT_APPLICABLE"
    if eligible_hypotheses > 0:
        return "SUFFICIENT_SAMPLE"
    return "INSUFFICIENT_SAMPLE"


def _top_count_row(rows: tuple[tuple[str, int], ...]) -> tuple[str | None, int]:
    if not rows:
        return None, 0
    return max(rows, key=lambda item: (item[1], tuple(reversed(item[0]))))


def _metadata(
    *,
    report: ResearchCampaignReport,
    analysis_id: str,
    analysis_version: str,
    analysis_engine_version: str,
) -> ResearchAnalysisMetadata:
    source_report_fingerprints = (report.report_fingerprint,)
    fingerprint = research_analysis_metadata_fingerprint_payload(
        analysis_id=analysis_id,
        analysis_version=analysis_version,
        analysis_engine_version=analysis_engine_version,
        source_report_fingerprints=source_report_fingerprints,
        source_campaign_result_fingerprint=report.metadata.campaign_result_fingerprint,
        source_campaign_designer_fingerprint=report.metadata.campaign_designer_fingerprint,
    )
    return ResearchAnalysisMetadata(
        analysis_id=analysis_id,
        analysis_version=analysis_version,
        analysis_engine_version=analysis_engine_version,
        source_report_fingerprints=source_report_fingerprints,
        source_campaign_result_fingerprint=report.metadata.campaign_result_fingerprint,
        source_campaign_designer_fingerprint=report.metadata.campaign_designer_fingerprint,
        metadata_fingerprint=fingerprint,
    )


def _family_analysis(family: object) -> ResearchFamilyAnalysis:
    transitions = family.transitions_generated
    signal_count = _signal_dimension_count(
        completed_visits=family.completed_visits,
        transitions=transitions,
        trajectory_records=family.trajectory_records,
        eligible_hypotheses=family.eligible_hypotheses,
    )
    fingerprint = research_family_analysis_fingerprint_payload(
        family_name=family.family_name,
        coverage_tags=family.coverage_tags,
        scenarios_generated=family.scenarios_generated,
        scenarios_executed=family.scenarios_executed,
        pass_count=family.pass_count,
        fail_count=family.fail_count,
        skipped_count=family.skipped_count,
        completed_visits=family.completed_visits,
        zero_visit_scenarios=family.zero_visit_scenarios,
        scenarios_with_three_or_more_visits=family.scenarios_with_three_or_more_visits,
        transitions=transitions,
        trajectory_records=family.trajectory_records,
        eligible_hypotheses=family.eligible_hypotheses,
        confirmed_hypotheses=family.confirmed_hypotheses,
        pending_hypotheses=family.pending_hypotheses,
        visit_density=_rate(family.completed_visits, family.scenarios_generated),
        transition_density=_rate(transitions, family.scenarios_generated),
        trajectory_density=_rate(family.trajectory_records, family.scenarios_generated),
        eligibility_rate=_rate(family.eligible_hypotheses, family.scenarios_generated),
        confirmation_rate=_rate(family.confirmed_hypotheses, family.eligible_hypotheses),
        pending_rate=_rate(family.pending_hypotheses, family.eligible_hypotheses),
        signal_dimension_count=signal_count,
        signal_richness_class=_signal_richness_class(signal_count),
        sample_sufficiency_class=_sample_sufficiency_class(
            scenarios_generated=family.scenarios_generated,
            eligible_hypotheses=family.eligible_hypotheses,
        ),
    )
    return ResearchFamilyAnalysis(
        family_name=family.family_name,
        coverage_tags=family.coverage_tags,
        scenarios_generated=family.scenarios_generated,
        scenarios_executed=family.scenarios_executed,
        pass_count=family.pass_count,
        fail_count=family.fail_count,
        skipped_count=family.skipped_count,
        completed_visits=family.completed_visits,
        zero_visit_scenarios=family.zero_visit_scenarios,
        scenarios_with_three_or_more_visits=family.scenarios_with_three_or_more_visits,
        transitions=transitions,
        trajectory_records=family.trajectory_records,
        eligible_hypotheses=family.eligible_hypotheses,
        confirmed_hypotheses=family.confirmed_hypotheses,
        pending_hypotheses=family.pending_hypotheses,
        visit_density=_rate(family.completed_visits, family.scenarios_generated),
        transition_density=_rate(transitions, family.scenarios_generated),
        trajectory_density=_rate(family.trajectory_records, family.scenarios_generated),
        eligibility_rate=_rate(family.eligible_hypotheses, family.scenarios_generated),
        confirmation_rate=_rate(family.confirmed_hypotheses, family.eligible_hypotheses),
        pending_rate=_rate(family.pending_hypotheses, family.eligible_hypotheses),
        signal_dimension_count=signal_count,
        signal_richness_class=_signal_richness_class(signal_count),
        sample_sufficiency_class=_sample_sufficiency_class(
            scenarios_generated=family.scenarios_generated,
            eligible_hypotheses=family.eligible_hypotheses,
        ),
        family_analysis_fingerprint=fingerprint,
    )


def _coverage_analysis(
    *,
    report: ResearchCampaignReport,
    families: tuple[ResearchFamilyAnalysis, ...],
) -> ResearchCoverageAnalysis:
    coverage_counts: dict[str, int] = {}
    for family in families:
        for tag in family.coverage_tags:
            coverage_counts[tag] = coverage_counts.get(tag, 0) + 1
    scenarios_generated = sum(family.scenarios_generated for family in families)
    scenarios_executed = sum(family.scenarios_executed for family in families)
    zero_visit_scenarios = sum(family.zero_visit_scenarios for family in families)
    three_plus_scenarios = sum(family.scenarios_with_three_or_more_visits for family in families)
    scenarios_with_transitions = report.coverage_summary.scenarios_with_transitions
    fingerprint = research_coverage_analysis_fingerprint_payload(
        families_observed=len(families),
        scenarios_generated=scenarios_generated,
        scenarios_executed=scenarios_executed,
        zero_visit_scenarios=zero_visit_scenarios,
        scenarios_with_three_or_more_visits=three_plus_scenarios,
        scenarios_with_transitions=scenarios_with_transitions,
        zero_visit_rate=_rate(zero_visit_scenarios, scenarios_generated),
        three_plus_visit_rate=_rate(three_plus_scenarios, scenarios_generated),
        transition_coverage_rate=_rate(scenarios_with_transitions, scenarios_generated),
        coverage_tag_family_counts=tuple(sorted(coverage_counts.items())),
        unique_coverage_tags=tuple(sorted(coverage_counts)),
        shared_coverage_tags=tuple(sorted(tag for tag, count in coverage_counts.items() if count > 1)),
    )
    return ResearchCoverageAnalysis(
        families_observed=len(families),
        scenarios_generated=scenarios_generated,
        scenarios_executed=scenarios_executed,
        zero_visit_scenarios=zero_visit_scenarios,
        scenarios_with_three_or_more_visits=three_plus_scenarios,
        scenarios_with_transitions=scenarios_with_transitions,
        zero_visit_rate=_rate(zero_visit_scenarios, scenarios_generated),
        three_plus_visit_rate=_rate(three_plus_scenarios, scenarios_generated),
        transition_coverage_rate=_rate(scenarios_with_transitions, scenarios_generated),
        coverage_tag_family_counts=tuple(sorted(coverage_counts.items())),
        unique_coverage_tags=tuple(sorted(coverage_counts)),
        shared_coverage_tags=tuple(sorted(tag for tag, count in coverage_counts.items() if count > 1)),
        coverage_analysis_fingerprint=fingerprint,
    )


def _transition_analysis(
    *,
    report: ResearchCampaignReport,
    families: tuple[ResearchFamilyAnalysis, ...],
) -> ResearchTransitionAnalysis:
    rows = tuple((family.family_name, family.transitions) for family in families)
    top_family, top_count = _top_count_row(rows)
    total = report.transition_summary.total_transitions
    fingerprint = research_transition_analysis_fingerprint_payload(
        total_transitions=total,
        scenarios_with_transitions=report.transition_summary.scenarios_with_transitions,
        per_family_transition_counts=rows,
        transition_density=_rate(total, report.transition_summary.scenarios_with_transitions),
        top_transition_contributor_family_name=top_family,
        top_transition_contributor_share=_rate(top_count, total),
        families_with_zero_transitions=tuple(sorted(family.family_name for family in families if family.transitions == 0)),
    )
    return ResearchTransitionAnalysis(
        total_transitions=total,
        scenarios_with_transitions=report.transition_summary.scenarios_with_transitions,
        per_family_transition_counts=rows,
        transition_density=_rate(total, report.transition_summary.scenarios_with_transitions),
        top_transition_contributor_family_name=top_family,
        top_transition_contributor_share=_rate(top_count, total),
        families_with_zero_transitions=tuple(sorted(family.family_name for family in families if family.transitions == 0)),
        transition_analysis_fingerprint=fingerprint,
    )


def _trajectory_analysis(
    *,
    report: ResearchCampaignReport,
    families: tuple[ResearchFamilyAnalysis, ...],
) -> ResearchTrajectoryAnalysis:
    rows = tuple((family.family_name, family.trajectory_records) for family in families)
    top_family, top_count = _top_count_row(rows)
    total = report.trajectory_summary.total_trajectory_records
    scenarios_generated = sum(family.scenarios_generated for family in families)
    fingerprint = research_trajectory_analysis_fingerprint_payload(
        total_trajectory_records=total,
        per_family_trajectory_records=rows,
        trajectory_density=_rate(total, scenarios_generated),
        top_trajectory_contributor_family_name=top_family,
        top_trajectory_contributor_share=_rate(top_count, total),
        families_with_zero_trajectory_records=tuple(
            sorted(family.family_name for family in families if family.trajectory_records == 0)
        ),
    )
    return ResearchTrajectoryAnalysis(
        total_trajectory_records=total,
        per_family_trajectory_records=rows,
        trajectory_density=_rate(total, scenarios_generated),
        top_trajectory_contributor_family_name=top_family,
        top_trajectory_contributor_share=_rate(top_count, total),
        families_with_zero_trajectory_records=tuple(
            sorted(family.family_name for family in families if family.trajectory_records == 0)
        ),
        trajectory_analysis_fingerprint=fingerprint,
    )


def _hypothesis_analysis(
    *,
    report: ResearchCampaignReport,
    families: tuple[ResearchFamilyAnalysis, ...],
) -> ResearchHypothesisAnalysis:
    rows = tuple(
        (
            family.family_name,
            family.eligible_hypotheses,
            family.confirmed_hypotheses,
            family.pending_hypotheses,
        )
        for family in families
    )
    top_rows = tuple((family_name, eligible) for family_name, eligible, _, _ in rows)
    top_family, top_count = _top_count_row(top_rows)
    eligible = report.hypothesis_summary.eligible_hypotheses
    scenarios_generated = sum(family.scenarios_generated for family in families)
    fingerprint = research_hypothesis_analysis_fingerprint_payload(
        eligible_hypotheses=eligible,
        confirmed_hypotheses=report.hypothesis_summary.confirmed_hypotheses,
        pending_hypotheses=report.hypothesis_summary.pending_hypotheses,
        per_family_hypothesis_counts=rows,
        eligibility_rate=_rate(eligible, scenarios_generated),
        confirmation_rate=_rate(report.hypothesis_summary.confirmed_hypotheses, eligible),
        pending_rate=_rate(report.hypothesis_summary.pending_hypotheses, eligible),
        top_eligible_hypothesis_family_name=top_family,
        top_eligible_hypothesis_family_share=_rate(top_count, eligible),
        families_with_no_eligible_hypotheses=tuple(
            sorted(family.family_name for family in families if family.eligible_hypotheses == 0)
        ),
    )
    return ResearchHypothesisAnalysis(
        eligible_hypotheses=eligible,
        confirmed_hypotheses=report.hypothesis_summary.confirmed_hypotheses,
        pending_hypotheses=report.hypothesis_summary.pending_hypotheses,
        per_family_hypothesis_counts=rows,
        eligibility_rate=_rate(eligible, scenarios_generated),
        confirmation_rate=_rate(report.hypothesis_summary.confirmed_hypotheses, eligible),
        pending_rate=_rate(report.hypothesis_summary.pending_hypotheses, eligible),
        top_eligible_hypothesis_family_name=top_family,
        top_eligible_hypothesis_family_share=_rate(top_count, eligible),
        families_with_no_eligible_hypotheses=tuple(
            sorted(family.family_name for family in families if family.eligible_hypotheses == 0)
        ),
        hypothesis_analysis_fingerprint=fingerprint,
    )


def analyze_research_campaign_report(
    report: ResearchCampaignReport,
    analysis_id: str,
    analysis_version: str,
    analysis_engine_version: str,
) -> ResearchCampaignAnalysis:
    """Build deterministic descriptive analysis from one immutable campaign report."""

    if not isinstance(report, ResearchCampaignReport):
        raise TypeError("report must be ResearchCampaignReport")
    _require_non_empty("analysis_id", analysis_id)
    _require_non_empty("analysis_version", analysis_version)
    _require_non_empty("analysis_engine_version", analysis_engine_version)
    metadata = _metadata(
        report=report,
        analysis_id=analysis_id,
        analysis_version=analysis_version,
        analysis_engine_version=analysis_engine_version,
    )
    family_analyses = tuple(sorted((_family_analysis(family) for family in report.family_summaries), key=lambda family: family.family_name))
    coverage = _coverage_analysis(report=report, families=family_analyses)
    transitions = _transition_analysis(report=report, families=family_analyses)
    trajectories = _trajectory_analysis(report=report, families=family_analyses)
    hypotheses = _hypothesis_analysis(report=report, families=family_analyses)
    diagnostics = tuple(sorted(report.diagnostics + (f"ANALYSIS_ENGINE_VERSION:{analysis_engine_version}",)))
    fingerprint = research_campaign_analysis_fingerprint_payload(
        metadata=metadata,
        family_analyses=family_analyses,
        coverage_analysis=coverage,
        transition_analysis=transitions,
        trajectory_analysis=trajectories,
        hypothesis_analysis=hypotheses,
        diagnostics=diagnostics,
    )
    return ResearchCampaignAnalysis(
        metadata=metadata,
        family_analyses=family_analyses,
        coverage_analysis=coverage,
        transition_analysis=transitions,
        trajectory_analysis=trajectories,
        hypothesis_analysis=hypotheses,
        diagnostics=diagnostics,
        campaign_analysis_fingerprint=fingerprint,
    )

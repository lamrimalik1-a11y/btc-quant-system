"""Pure report generation for the first Project 2 research campaign.

Consumes an already-created CampaignDesignerResult-like object and produces
immutable report contracts. It does not execute campaigns, call the runner,
read/write files, render charts, or inspect raw Stage-native payloads.
"""

from __future__ import annotations

from typing import Any

from experiments.psychological_levels_dynamic.scenario_generation.research_report_contracts import (
    RESEARCH_REPORT_CONTRACTS_VERSION,
    ResearchCampaignReport,
    ResearchCoverageSummary,
    ResearchFamilySummary,
    ResearchHypothesisSummary,
    ResearchReportMetadata,
    ResearchTrajectorySummary,
    ResearchTransitionSummary,
    research_campaign_report_fingerprint_payload,
    research_coverage_summary_fingerprint_payload,
    research_family_summary_fingerprint_payload,
    research_hypothesis_summary_fingerprint_payload,
    research_report_metadata_fingerprint_payload,
    research_trajectory_summary_fingerprint_payload,
    research_transition_summary_fingerprint_payload,
)

RESEARCH_REPORT_GENERATOR_VERSION = "PHASE2D_FIRST_RESEARCH_CAMPAIGN_100_REPORT_GENERATOR_V1"


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _summary_dict(record: Any) -> dict[str, Any]:
    return dict(record.summary)


def _count_records(payload: Any) -> tuple[dict[str, Any], ...]:
    if payload.batch_execution_result is None:
        return ()
    return tuple(_summary_dict(record) for record in payload.batch_execution_result.scenario_results)


def _family_summary(payload: Any) -> ResearchFamilySummary:
    summaries = _count_records(payload)
    generated = len(payload.generation_result.generated_programs)
    assembled = 0 if payload.batch_assembly_result is None else len(payload.batch_assembly_result.assembled_specifications)
    failed = 0 if payload.batch_execution_result is None else payload.batch_execution_result.failed_scenarios
    skipped = (
        max(0, generated - assembled)
        + (0 if payload.batch_execution_result is None else payload.batch_execution_result.skipped_scenarios)
    )
    passed = sum(
        1
        for record in (() if payload.batch_execution_result is None else payload.batch_execution_result.scenario_results)
        if record.execution_status == "EXECUTED" and record.runner_result == "PASS"
    )
    runner_failures = sum(
        1
        for record in (() if payload.batch_execution_result is None else payload.batch_execution_result.scenario_results)
        if record.execution_status == "EXECUTED" and record.runner_result == "FAIL"
    )
    fail_count = failed + runner_failures
    executed = passed + fail_count + skipped
    completed_visits = sum(summary.get("completed_visits") or 0 for summary in summaries)
    zero_visit_scenarios = sum(1 for summary in summaries if (summary.get("completed_visits") or 0) == 0)
    scenarios_with_three_or_more_visits = sum(1 for summary in summaries if (summary.get("completed_visits") or 0) >= 3)
    transitions = sum(summary.get("transitions_generated") or 0 for summary in summaries)
    trajectory_records = sum(summary.get("trajectory_records") or 0 for summary in summaries)
    eligible = sum(summary.get("eligible_hypotheses") or 0 for summary in summaries)
    confirmed = sum(summary.get("confirmed_hypotheses") or 0 for summary in summaries)
    pending = sum(summary.get("pending_hypotheses") or 0 for summary in summaries)
    coverage_tags = tuple(sorted(payload.coverage_tags))
    batch_execution_fingerprint = (
        "sha256:" + "0" * 64
        if payload.batch_execution_result is None
        else payload.batch_execution_result.batch_execution_fingerprint
    )
    fingerprint = research_family_summary_fingerprint_payload(
        family_name=payload.family_name,
        coverage_tags=coverage_tags,
        scenarios_generated=generated,
        scenarios_executed=executed,
        pass_count=passed,
        fail_count=fail_count,
        skipped_count=skipped,
        completed_visits=completed_visits,
        zero_visit_scenarios=zero_visit_scenarios,
        scenarios_with_three_or_more_visits=scenarios_with_three_or_more_visits,
        transitions_generated=transitions,
        trajectory_records=trajectory_records,
        eligible_hypotheses=eligible,
        confirmed_hypotheses=confirmed,
        pending_hypotheses=pending,
        family_pipeline_fingerprint=payload.family_pipeline_fingerprint,
        batch_execution_fingerprint=batch_execution_fingerprint,
    )
    return ResearchFamilySummary(
        family_name=payload.family_name,
        coverage_tags=coverage_tags,
        scenarios_generated=generated,
        scenarios_executed=executed,
        pass_count=passed,
        fail_count=fail_count,
        skipped_count=skipped,
        completed_visits=completed_visits,
        zero_visit_scenarios=zero_visit_scenarios,
        scenarios_with_three_or_more_visits=scenarios_with_three_or_more_visits,
        transitions_generated=transitions,
        trajectory_records=trajectory_records,
        eligible_hypotheses=eligible,
        confirmed_hypotheses=confirmed,
        pending_hypotheses=pending,
        family_pipeline_fingerprint=payload.family_pipeline_fingerprint,
        batch_execution_fingerprint=batch_execution_fingerprint,
        family_fingerprint=fingerprint,
    )


def _metadata(
    *,
    campaign_designer_result: Any,
    family_summaries: tuple[ResearchFamilySummary, ...],
    report_id: str,
    report_version: str,
) -> ResearchReportMetadata:
    family_pipeline_fingerprints = tuple(family.family_pipeline_fingerprint for family in family_summaries)
    fingerprint = research_report_metadata_fingerprint_payload(
        report_id=report_id,
        report_version=report_version,
        report_contract_version=RESEARCH_REPORT_CONTRACTS_VERSION,
        campaign_specification_fingerprint=campaign_designer_result.campaign_specification.campaign_specification_fingerprint,
        campaign_result_fingerprint=campaign_designer_result.campaign_result.campaign_fingerprint,
        campaign_designer_fingerprint=campaign_designer_result.campaign_designer_fingerprint,
        family_pipeline_fingerprints=family_pipeline_fingerprints,
    )
    return ResearchReportMetadata(
        report_id=report_id,
        report_version=report_version,
        report_contract_version=RESEARCH_REPORT_CONTRACTS_VERSION,
        campaign_specification_fingerprint=campaign_designer_result.campaign_specification.campaign_specification_fingerprint,
        campaign_result_fingerprint=campaign_designer_result.campaign_result.campaign_fingerprint,
        campaign_designer_fingerprint=campaign_designer_result.campaign_designer_fingerprint,
        family_pipeline_fingerprints=family_pipeline_fingerprints,
        metadata_fingerprint=fingerprint,
    )


def _coverage_summary(
    family_summaries: tuple[ResearchFamilySummary, ...],
    scenarios_with_transitions: int,
) -> ResearchCoverageSummary:
    coverage_tags = tuple(sorted({tag for family in family_summaries for tag in family.coverage_tags}))
    total_scenarios = sum(family.scenarios_generated for family in family_summaries)
    executed = sum(family.scenarios_executed for family in family_summaries)
    passed = sum(family.pass_count for family in family_summaries)
    failed = sum(family.fail_count for family in family_summaries)
    skipped = sum(family.skipped_count for family in family_summaries)
    zero_visits = sum(family.zero_visit_scenarios for family in family_summaries)
    three_plus = sum(family.scenarios_with_three_or_more_visits for family in family_summaries)
    fingerprint = research_coverage_summary_fingerprint_payload(
        total_families=len(family_summaries),
        total_scenarios=total_scenarios,
        executed_scenarios=executed,
        passed_scenarios=passed,
        failed_scenarios=failed,
        skipped_scenarios=skipped,
        zero_visit_scenarios=zero_visits,
        scenarios_with_three_or_more_visits=three_plus,
        scenarios_with_transitions=scenarios_with_transitions,
        coverage_tags=coverage_tags,
    )
    return ResearchCoverageSummary(
        total_families=len(family_summaries),
        total_scenarios=total_scenarios,
        executed_scenarios=executed,
        passed_scenarios=passed,
        failed_scenarios=failed,
        skipped_scenarios=skipped,
        zero_visit_scenarios=zero_visits,
        scenarios_with_three_or_more_visits=three_plus,
        scenarios_with_transitions=scenarios_with_transitions,
        coverage_tags=coverage_tags,
        coverage_fingerprint=fingerprint,
    )


def _transition_summary(
    *,
    family_summaries: tuple[ResearchFamilySummary, ...],
    scenarios_with_transitions: int,
) -> ResearchTransitionSummary:
    per_family = tuple((family.family_name, family.transitions_generated) for family in family_summaries)
    total = sum(count for _, count in per_family)
    fingerprint = research_transition_summary_fingerprint_payload(
        total_transitions=total,
        scenarios_with_transitions=scenarios_with_transitions,
        transition_counts=(),
        per_family_transition_counts=per_family,
        rare_transition_types=(),
        absent_transition_types=(),
    )
    return ResearchTransitionSummary(
        total_transitions=total,
        scenarios_with_transitions=scenarios_with_transitions,
        transition_counts=(),
        per_family_transition_counts=per_family,
        rare_transition_types=(),
        absent_transition_types=(),
        transition_fingerprint=fingerprint,
    )


def _trajectory_summary(family_summaries: tuple[ResearchFamilySummary, ...]) -> ResearchTrajectorySummary:
    per_family = tuple((family.family_name, family.trajectory_records) for family in family_summaries)
    total = sum(count for _, count in per_family)
    fingerprint = research_trajectory_summary_fingerprint_payload(
        total_trajectory_records=total,
        per_family_trajectory_records=per_family,
        observed_states=(),
        unobserved_states=(),
        sample_sufficiency_counts=(),
        zones_with_no_transitions=(),
    )
    return ResearchTrajectorySummary(
        total_trajectory_records=total,
        per_family_trajectory_records=per_family,
        observed_states=(),
        unobserved_states=(),
        sample_sufficiency_counts=(),
        zones_with_no_transitions=(),
        trajectory_fingerprint=fingerprint,
    )


def _hypothesis_summary(family_summaries: tuple[ResearchFamilySummary, ...]) -> ResearchHypothesisSummary:
    rows = tuple(
        (
            family.family_name,
            family.eligible_hypotheses,
            family.confirmed_hypotheses,
            family.pending_hypotheses,
            0,
        )
        for family in family_summaries
    )
    eligible = sum(row[1] for row in rows)
    confirmed = sum(row[2] for row in rows)
    pending = sum(row[3] for row in rows)
    invalidated = sum(row[4] for row in rows)
    fingerprint = research_hypothesis_summary_fingerprint_payload(
        eligible_hypotheses=eligible,
        confirmed_hypotheses=confirmed,
        pending_hypotheses=pending,
        invalidated_hypotheses=invalidated,
        per_family_hypothesis_counts=rows,
        attacker_pressure_observed=False,
        predictions_generated=False,
    )
    return ResearchHypothesisSummary(
        eligible_hypotheses=eligible,
        confirmed_hypotheses=confirmed,
        pending_hypotheses=pending,
        invalidated_hypotheses=invalidated,
        per_family_hypothesis_counts=rows,
        attacker_pressure_observed=False,
        predictions_generated=False,
        hypothesis_fingerprint=fingerprint,
    )


def build_research_campaign_report(
    campaign_designer_result: Any,
    report_id: str,
    report_version: str,
    report_generator_version: str,
) -> ResearchCampaignReport:
    """Build a deterministic report contract from an existing campaign result."""

    _require_non_empty("report_id", report_id)
    _require_non_empty("report_version", report_version)
    _require_non_empty("report_generator_version", report_generator_version)
    family_summaries = tuple(
        sorted(
            (_family_summary(payload) for payload in campaign_designer_result.family_execution_payloads),
            key=lambda family: family.family_name,
        )
    )
    metadata = _metadata(
        campaign_designer_result=campaign_designer_result,
        family_summaries=family_summaries,
        report_id=report_id,
        report_version=report_version,
    )
    scenarios_with_transitions = sum(
        1
        for payload in campaign_designer_result.family_execution_payloads
        for summary in _count_records(payload)
        if (summary.get("transitions_generated") or 0) > 0
    )
    coverage = _coverage_summary(family_summaries, scenarios_with_transitions)
    transitions = _transition_summary(
        family_summaries=family_summaries,
        scenarios_with_transitions=coverage.scenarios_with_transitions,
    )
    trajectories = _trajectory_summary(family_summaries)
    hypotheses = _hypothesis_summary(family_summaries)
    diagnostics = tuple(sorted(campaign_designer_result.diagnostics + (f"REPORT_GENERATOR_VERSION:{report_generator_version}",)))
    fingerprint = research_campaign_report_fingerprint_payload(
        metadata=metadata,
        coverage_summary=coverage,
        family_summaries=family_summaries,
        transition_summary=transitions,
        trajectory_summary=trajectories,
        hypothesis_summary=hypotheses,
        diagnostics=diagnostics,
    )
    return ResearchCampaignReport(
        metadata=metadata,
        coverage_summary=coverage,
        family_summaries=family_summaries,
        transition_summary=transitions,
        trajectory_summary=trajectories,
        hypothesis_summary=hypotheses,
        diagnostics=diagnostics,
        report_fingerprint=fingerprint,
    )

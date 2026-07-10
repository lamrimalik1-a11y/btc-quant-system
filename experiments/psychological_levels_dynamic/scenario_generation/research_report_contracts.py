"""Immutable contracts for first Project 2 research campaign reports.

Contracts only: no campaign execution, report generation, statistics engine,
charts, raw observations, or analytical interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass

from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    generation_contract_fingerprint,
)

RESEARCH_REPORT_CONTRACTS_VERSION = "PHASE2D_FIRST_RESEARCH_CAMPAIGN_100_REPORT_CONTRACTS_V1"


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_fingerprint(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        raise ValueError(f"{name} must be SHA-256")


def _require_tuple(name: str, value: tuple[object, ...]) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{name} must be tuple")


def _require_non_negative_int(name: str, value: int) -> None:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _require_bool(name: str, value: bool) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")


def _require_string_tuple(name: str, value: tuple[str, ...], *, sorted_unique: bool) -> None:
    _require_tuple(name, value)
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{name} must contain non-empty strings")
    if sorted_unique and tuple(sorted(value)) != value:
        raise ValueError(f"{name} must be sorted canonically")
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must be unique")


def _require_count_pairs(name: str, value: tuple[tuple[str, int], ...]) -> None:
    _require_tuple(name, value)
    if tuple(sorted(value, key=lambda item: item[0])) != value:
        raise ValueError(f"{name} must be sorted by key")
    seen: set[str] = set()
    for key, count in value:
        _require_non_empty(f"{name} key", key)
        _require_non_negative_int(f"{name} count", count)
        if key in seen:
            raise ValueError(f"{name} keys must be unique")
        seen.add(key)


def _require_family_hypothesis_rows(
    name: str,
    value: tuple[tuple[str, int, int, int, int], ...],
) -> None:
    _require_tuple(name, value)
    if tuple(sorted(value, key=lambda item: item[0])) != value:
        raise ValueError(f"{name} must be sorted by family name")
    seen: set[str] = set()
    for row in value:
        if len(row) != 5:
            raise ValueError(f"{name} rows must have five fields")
        family_name, eligible, confirmed, pending, invalidated = row
        _require_non_empty("family_name", family_name)
        for field_name, count in (
            ("eligible", eligible),
            ("confirmed", confirmed),
            ("pending", pending),
            ("invalidated", invalidated),
        ):
            _require_non_negative_int(field_name, count)
        if confirmed + pending + invalidated > eligible:
            raise ValueError("family hypothesis counts cannot exceed eligible count")
        if family_name in seen:
            raise ValueError(f"{name} family names must be unique")
        seen.add(family_name)


def research_report_metadata_fingerprint_payload(
    *,
    report_id: str,
    report_version: str,
    report_contract_version: str,
    campaign_specification_fingerprint: str,
    campaign_result_fingerprint: str,
    campaign_designer_fingerprint: str,
    family_pipeline_fingerprints: tuple[str, ...],
) -> str:
    return generation_contract_fingerprint(
        (
            report_id,
            report_version,
            report_contract_version,
            campaign_specification_fingerprint,
            campaign_result_fingerprint,
            campaign_designer_fingerprint,
            family_pipeline_fingerprints,
        )
    )


def research_coverage_summary_fingerprint_payload(
    *,
    total_families: int,
    total_scenarios: int,
    executed_scenarios: int,
    passed_scenarios: int,
    failed_scenarios: int,
    skipped_scenarios: int,
    zero_visit_scenarios: int,
    scenarios_with_three_or_more_visits: int,
    scenarios_with_transitions: int,
    coverage_tags: tuple[str, ...],
) -> str:
    return generation_contract_fingerprint(
        (
            total_families,
            total_scenarios,
            executed_scenarios,
            passed_scenarios,
            failed_scenarios,
            skipped_scenarios,
            zero_visit_scenarios,
            scenarios_with_three_or_more_visits,
            scenarios_with_transitions,
            coverage_tags,
        )
    )


def research_family_summary_fingerprint_payload(
    *,
    family_name: str,
    coverage_tags: tuple[str, ...],
    scenarios_generated: int,
    scenarios_executed: int,
    pass_count: int,
    fail_count: int,
    skipped_count: int,
    completed_visits: int,
    zero_visit_scenarios: int,
    scenarios_with_three_or_more_visits: int,
    transitions_generated: int,
    trajectory_records: int,
    eligible_hypotheses: int,
    confirmed_hypotheses: int,
    pending_hypotheses: int,
    family_pipeline_fingerprint: str,
    batch_execution_fingerprint: str,
) -> str:
    return generation_contract_fingerprint(
        (
            family_name,
            coverage_tags,
            scenarios_generated,
            scenarios_executed,
            pass_count,
            fail_count,
            skipped_count,
            completed_visits,
            zero_visit_scenarios,
            scenarios_with_three_or_more_visits,
            transitions_generated,
            trajectory_records,
            eligible_hypotheses,
            confirmed_hypotheses,
            pending_hypotheses,
            family_pipeline_fingerprint,
            batch_execution_fingerprint,
        )
    )


def research_transition_summary_fingerprint_payload(
    *,
    total_transitions: int,
    scenarios_with_transitions: int,
    transition_counts: tuple[tuple[str, int], ...],
    per_family_transition_counts: tuple[tuple[str, int], ...],
    rare_transition_types: tuple[str, ...],
    absent_transition_types: tuple[str, ...],
) -> str:
    return generation_contract_fingerprint(
        (
            total_transitions,
            scenarios_with_transitions,
            transition_counts,
            per_family_transition_counts,
            rare_transition_types,
            absent_transition_types,
        )
    )


def research_trajectory_summary_fingerprint_payload(
    *,
    total_trajectory_records: int,
    per_family_trajectory_records: tuple[tuple[str, int], ...],
    observed_states: tuple[str, ...],
    unobserved_states: tuple[str, ...],
    sample_sufficiency_counts: tuple[tuple[str, int], ...],
    zones_with_no_transitions: tuple[str, ...],
) -> str:
    return generation_contract_fingerprint(
        (
            total_trajectory_records,
            per_family_trajectory_records,
            observed_states,
            unobserved_states,
            sample_sufficiency_counts,
            zones_with_no_transitions,
        )
    )


def research_hypothesis_summary_fingerprint_payload(
    *,
    eligible_hypotheses: int,
    confirmed_hypotheses: int,
    pending_hypotheses: int,
    invalidated_hypotheses: int,
    per_family_hypothesis_counts: tuple[tuple[str, int, int, int, int], ...],
    attacker_pressure_observed: bool,
    predictions_generated: bool,
) -> str:
    return generation_contract_fingerprint(
        (
            eligible_hypotheses,
            confirmed_hypotheses,
            pending_hypotheses,
            invalidated_hypotheses,
            per_family_hypothesis_counts,
            attacker_pressure_observed,
            predictions_generated,
        )
    )


def research_campaign_report_fingerprint_payload(
    *,
    metadata: "ResearchReportMetadata",
    coverage_summary: "ResearchCoverageSummary",
    family_summaries: tuple["ResearchFamilySummary", ...],
    transition_summary: "ResearchTransitionSummary",
    trajectory_summary: "ResearchTrajectorySummary",
    hypothesis_summary: "ResearchHypothesisSummary",
    diagnostics: tuple[str, ...],
) -> str:
    return generation_contract_fingerprint(
        (
            metadata,
            coverage_summary,
            family_summaries,
            transition_summary,
            trajectory_summary,
            hypothesis_summary,
            diagnostics,
        )
    )


@dataclass(frozen=True)
class ResearchReportMetadata:
    report_id: str
    report_version: str
    report_contract_version: str
    campaign_specification_fingerprint: str
    campaign_result_fingerprint: str
    campaign_designer_fingerprint: str
    family_pipeline_fingerprints: tuple[str, ...]
    metadata_fingerprint: str

    def __post_init__(self) -> None:
        _require_non_empty("report_id", self.report_id)
        _require_non_empty("report_version", self.report_version)
        _require_non_empty("report_contract_version", self.report_contract_version)
        for field_name in (
            "campaign_specification_fingerprint",
            "campaign_result_fingerprint",
            "campaign_designer_fingerprint",
            "metadata_fingerprint",
        ):
            _require_fingerprint(field_name, getattr(self, field_name))
        _require_tuple("family_pipeline_fingerprints", self.family_pipeline_fingerprints)
        if not self.family_pipeline_fingerprints:
            raise ValueError("family_pipeline_fingerprints must not be empty")
        for fingerprint in self.family_pipeline_fingerprints:
            _require_fingerprint("family_pipeline_fingerprints item", fingerprint)
        expected = research_report_metadata_fingerprint_payload(
            report_id=self.report_id,
            report_version=self.report_version,
            report_contract_version=self.report_contract_version,
            campaign_specification_fingerprint=self.campaign_specification_fingerprint,
            campaign_result_fingerprint=self.campaign_result_fingerprint,
            campaign_designer_fingerprint=self.campaign_designer_fingerprint,
            family_pipeline_fingerprints=self.family_pipeline_fingerprints,
        )
        if self.metadata_fingerprint != expected:
            raise ValueError("metadata_fingerprint does not match canonical content")


@dataclass(frozen=True)
class ResearchCoverageSummary:
    total_families: int
    total_scenarios: int
    executed_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    skipped_scenarios: int
    zero_visit_scenarios: int
    scenarios_with_three_or_more_visits: int
    scenarios_with_transitions: int
    coverage_tags: tuple[str, ...]
    coverage_fingerprint: str

    def __post_init__(self) -> None:
        for field_name in (
            "total_families",
            "total_scenarios",
            "executed_scenarios",
            "passed_scenarios",
            "failed_scenarios",
            "skipped_scenarios",
            "zero_visit_scenarios",
            "scenarios_with_three_or_more_visits",
            "scenarios_with_transitions",
        ):
            _require_non_negative_int(field_name, getattr(self, field_name))
        if self.passed_scenarios + self.failed_scenarios + self.skipped_scenarios != self.executed_scenarios:
            raise ValueError("scenario result counts must reconcile to executed_scenarios")
        if self.executed_scenarios > self.total_scenarios:
            raise ValueError("executed_scenarios cannot exceed total_scenarios")
        if self.zero_visit_scenarios > self.total_scenarios:
            raise ValueError("zero_visit_scenarios cannot exceed total_scenarios")
        if self.scenarios_with_three_or_more_visits > self.total_scenarios:
            raise ValueError("scenarios_with_three_or_more_visits cannot exceed total_scenarios")
        if self.scenarios_with_transitions > self.total_scenarios:
            raise ValueError("scenarios_with_transitions cannot exceed total_scenarios")
        _require_string_tuple("coverage_tags", self.coverage_tags, sorted_unique=True)
        _require_fingerprint("coverage_fingerprint", self.coverage_fingerprint)
        expected = research_coverage_summary_fingerprint_payload(
            total_families=self.total_families,
            total_scenarios=self.total_scenarios,
            executed_scenarios=self.executed_scenarios,
            passed_scenarios=self.passed_scenarios,
            failed_scenarios=self.failed_scenarios,
            skipped_scenarios=self.skipped_scenarios,
            zero_visit_scenarios=self.zero_visit_scenarios,
            scenarios_with_three_or_more_visits=self.scenarios_with_three_or_more_visits,
            scenarios_with_transitions=self.scenarios_with_transitions,
            coverage_tags=self.coverage_tags,
        )
        if self.coverage_fingerprint != expected:
            raise ValueError("coverage_fingerprint does not match canonical content")


@dataclass(frozen=True)
class ResearchFamilySummary:
    family_name: str
    coverage_tags: tuple[str, ...]
    scenarios_generated: int
    scenarios_executed: int
    pass_count: int
    fail_count: int
    skipped_count: int
    completed_visits: int
    zero_visit_scenarios: int
    scenarios_with_three_or_more_visits: int
    transitions_generated: int
    trajectory_records: int
    eligible_hypotheses: int
    confirmed_hypotheses: int
    pending_hypotheses: int
    family_pipeline_fingerprint: str
    batch_execution_fingerprint: str
    family_fingerprint: str

    def __post_init__(self) -> None:
        _require_non_empty("family_name", self.family_name)
        _require_string_tuple("coverage_tags", self.coverage_tags, sorted_unique=True)
        for field_name in (
            "scenarios_generated",
            "scenarios_executed",
            "pass_count",
            "fail_count",
            "skipped_count",
            "completed_visits",
            "zero_visit_scenarios",
            "scenarios_with_three_or_more_visits",
            "transitions_generated",
            "trajectory_records",
            "eligible_hypotheses",
            "confirmed_hypotheses",
            "pending_hypotheses",
        ):
            _require_non_negative_int(field_name, getattr(self, field_name))
        if self.pass_count + self.fail_count + self.skipped_count != self.scenarios_executed:
            raise ValueError("family scenario counts must reconcile to scenarios_executed")
        if self.scenarios_executed > self.scenarios_generated:
            raise ValueError("scenarios_executed cannot exceed scenarios_generated")
        if self.zero_visit_scenarios > self.scenarios_generated:
            raise ValueError("zero_visit_scenarios cannot exceed scenarios_generated")
        if self.scenarios_with_three_or_more_visits > self.scenarios_generated:
            raise ValueError("scenarios_with_three_or_more_visits cannot exceed scenarios_generated")
        if self.confirmed_hypotheses + self.pending_hypotheses > self.eligible_hypotheses:
            raise ValueError("family hypothesis counts cannot exceed eligible_hypotheses")
        for field_name in ("family_pipeline_fingerprint", "batch_execution_fingerprint", "family_fingerprint"):
            _require_fingerprint(field_name, getattr(self, field_name))
        expected = research_family_summary_fingerprint_payload(
            family_name=self.family_name,
            coverage_tags=self.coverage_tags,
            scenarios_generated=self.scenarios_generated,
            scenarios_executed=self.scenarios_executed,
            pass_count=self.pass_count,
            fail_count=self.fail_count,
            skipped_count=self.skipped_count,
            completed_visits=self.completed_visits,
            zero_visit_scenarios=self.zero_visit_scenarios,
            scenarios_with_three_or_more_visits=self.scenarios_with_three_or_more_visits,
            transitions_generated=self.transitions_generated,
            trajectory_records=self.trajectory_records,
            eligible_hypotheses=self.eligible_hypotheses,
            confirmed_hypotheses=self.confirmed_hypotheses,
            pending_hypotheses=self.pending_hypotheses,
            family_pipeline_fingerprint=self.family_pipeline_fingerprint,
            batch_execution_fingerprint=self.batch_execution_fingerprint,
        )
        if self.family_fingerprint != expected:
            raise ValueError("family_fingerprint does not match canonical content")


@dataclass(frozen=True)
class ResearchTransitionSummary:
    total_transitions: int
    scenarios_with_transitions: int
    transition_counts: tuple[tuple[str, int], ...]
    per_family_transition_counts: tuple[tuple[str, int], ...]
    rare_transition_types: tuple[str, ...]
    absent_transition_types: tuple[str, ...]
    transition_fingerprint: str

    def __post_init__(self) -> None:
        _require_non_negative_int("total_transitions", self.total_transitions)
        _require_non_negative_int("scenarios_with_transitions", self.scenarios_with_transitions)
        _require_count_pairs("transition_counts", self.transition_counts)
        _require_count_pairs("per_family_transition_counts", self.per_family_transition_counts)
        if self.transition_counts and sum(count for _, count in self.transition_counts) != self.total_transitions:
            raise ValueError("transition_counts must reconcile to total_transitions")
        if sum(count for _, count in self.per_family_transition_counts) != self.total_transitions:
            raise ValueError("per_family_transition_counts must reconcile to total_transitions")
        _require_string_tuple("rare_transition_types", self.rare_transition_types, sorted_unique=True)
        _require_string_tuple("absent_transition_types", self.absent_transition_types, sorted_unique=True)
        _require_fingerprint("transition_fingerprint", self.transition_fingerprint)
        expected = research_transition_summary_fingerprint_payload(
            total_transitions=self.total_transitions,
            scenarios_with_transitions=self.scenarios_with_transitions,
            transition_counts=self.transition_counts,
            per_family_transition_counts=self.per_family_transition_counts,
            rare_transition_types=self.rare_transition_types,
            absent_transition_types=self.absent_transition_types,
        )
        if self.transition_fingerprint != expected:
            raise ValueError("transition_fingerprint does not match canonical content")


@dataclass(frozen=True)
class ResearchTrajectorySummary:
    total_trajectory_records: int
    per_family_trajectory_records: tuple[tuple[str, int], ...]
    observed_states: tuple[str, ...]
    unobserved_states: tuple[str, ...]
    sample_sufficiency_counts: tuple[tuple[str, int], ...]
    zones_with_no_transitions: tuple[str, ...]
    trajectory_fingerprint: str

    def __post_init__(self) -> None:
        _require_non_negative_int("total_trajectory_records", self.total_trajectory_records)
        _require_count_pairs("per_family_trajectory_records", self.per_family_trajectory_records)
        if sum(count for _, count in self.per_family_trajectory_records) != self.total_trajectory_records:
            raise ValueError("per_family_trajectory_records must reconcile to total_trajectory_records")
        _require_string_tuple("observed_states", self.observed_states, sorted_unique=True)
        _require_string_tuple("unobserved_states", self.unobserved_states, sorted_unique=True)
        _require_count_pairs("sample_sufficiency_counts", self.sample_sufficiency_counts)
        _require_string_tuple("zones_with_no_transitions", self.zones_with_no_transitions, sorted_unique=True)
        _require_fingerprint("trajectory_fingerprint", self.trajectory_fingerprint)
        expected = research_trajectory_summary_fingerprint_payload(
            total_trajectory_records=self.total_trajectory_records,
            per_family_trajectory_records=self.per_family_trajectory_records,
            observed_states=self.observed_states,
            unobserved_states=self.unobserved_states,
            sample_sufficiency_counts=self.sample_sufficiency_counts,
            zones_with_no_transitions=self.zones_with_no_transitions,
        )
        if self.trajectory_fingerprint != expected:
            raise ValueError("trajectory_fingerprint does not match canonical content")


@dataclass(frozen=True)
class ResearchHypothesisSummary:
    eligible_hypotheses: int
    confirmed_hypotheses: int
    pending_hypotheses: int
    invalidated_hypotheses: int
    per_family_hypothesis_counts: tuple[tuple[str, int, int, int, int], ...]
    attacker_pressure_observed: bool
    predictions_generated: bool
    hypothesis_fingerprint: str

    def __post_init__(self) -> None:
        for field_name in (
            "eligible_hypotheses",
            "confirmed_hypotheses",
            "pending_hypotheses",
            "invalidated_hypotheses",
        ):
            _require_non_negative_int(field_name, getattr(self, field_name))
        if self.confirmed_hypotheses + self.pending_hypotheses + self.invalidated_hypotheses > self.eligible_hypotheses:
            raise ValueError("hypothesis counts cannot exceed eligible_hypotheses")
        _require_family_hypothesis_rows("per_family_hypothesis_counts", self.per_family_hypothesis_counts)
        if sum(row[1] for row in self.per_family_hypothesis_counts) != self.eligible_hypotheses:
            raise ValueError("family eligible counts must reconcile to eligible_hypotheses")
        if sum(row[2] for row in self.per_family_hypothesis_counts) != self.confirmed_hypotheses:
            raise ValueError("family confirmed counts must reconcile to confirmed_hypotheses")
        if sum(row[3] for row in self.per_family_hypothesis_counts) != self.pending_hypotheses:
            raise ValueError("family pending counts must reconcile to pending_hypotheses")
        if sum(row[4] for row in self.per_family_hypothesis_counts) != self.invalidated_hypotheses:
            raise ValueError("family invalidated counts must reconcile to invalidated_hypotheses")
        _require_bool("attacker_pressure_observed", self.attacker_pressure_observed)
        _require_bool("predictions_generated", self.predictions_generated)
        _require_fingerprint("hypothesis_fingerprint", self.hypothesis_fingerprint)
        expected = research_hypothesis_summary_fingerprint_payload(
            eligible_hypotheses=self.eligible_hypotheses,
            confirmed_hypotheses=self.confirmed_hypotheses,
            pending_hypotheses=self.pending_hypotheses,
            invalidated_hypotheses=self.invalidated_hypotheses,
            per_family_hypothesis_counts=self.per_family_hypothesis_counts,
            attacker_pressure_observed=self.attacker_pressure_observed,
            predictions_generated=self.predictions_generated,
        )
        if self.hypothesis_fingerprint != expected:
            raise ValueError("hypothesis_fingerprint does not match canonical content")


@dataclass(frozen=True)
class ResearchCampaignReport:
    metadata: ResearchReportMetadata
    coverage_summary: ResearchCoverageSummary
    family_summaries: tuple[ResearchFamilySummary, ...]
    transition_summary: ResearchTransitionSummary
    trajectory_summary: ResearchTrajectorySummary
    hypothesis_summary: ResearchHypothesisSummary
    diagnostics: tuple[str, ...]
    report_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.metadata, ResearchReportMetadata):
            raise TypeError("metadata must be ResearchReportMetadata")
        if not isinstance(self.coverage_summary, ResearchCoverageSummary):
            raise TypeError("coverage_summary must be ResearchCoverageSummary")
        _require_tuple("family_summaries", self.family_summaries)
        if not self.family_summaries:
            raise ValueError("family_summaries must not be empty")
        if not all(isinstance(item, ResearchFamilySummary) for item in self.family_summaries):
            raise TypeError("family_summaries must contain ResearchFamilySummary values")
        if tuple(sorted(self.family_summaries, key=lambda item: item.family_name)) != self.family_summaries:
            raise ValueError("family_summaries must be sorted by family_name")
        if not isinstance(self.transition_summary, ResearchTransitionSummary):
            raise TypeError("transition_summary must be ResearchTransitionSummary")
        if not isinstance(self.trajectory_summary, ResearchTrajectorySummary):
            raise TypeError("trajectory_summary must be ResearchTrajectorySummary")
        if not isinstance(self.hypothesis_summary, ResearchHypothesisSummary):
            raise TypeError("hypothesis_summary must be ResearchHypothesisSummary")
        _require_string_tuple("diagnostics", self.diagnostics, sorted_unique=True)
        _require_fingerprint("report_fingerprint", self.report_fingerprint)
        if len(self.family_summaries) != self.coverage_summary.total_families:
            raise ValueError("family_summaries count must match total_families")
        if len(self.metadata.family_pipeline_fingerprints) != len(self.family_summaries):
            raise ValueError("metadata family_pipeline_fingerprints count must match family_summaries")
        if tuple(item.family_pipeline_fingerprint for item in self.family_summaries) != self.metadata.family_pipeline_fingerprints:
            raise ValueError("family pipeline provenance must match family summaries")
        if sum(item.scenarios_generated for item in self.family_summaries) != self.coverage_summary.total_scenarios:
            raise ValueError("family generated counts must reconcile to coverage total_scenarios")
        if sum(item.scenarios_executed for item in self.family_summaries) != self.coverage_summary.executed_scenarios:
            raise ValueError("family executed counts must reconcile to coverage executed_scenarios")
        if sum(item.pass_count for item in self.family_summaries) != self.coverage_summary.passed_scenarios:
            raise ValueError("family pass counts must reconcile to coverage passed_scenarios")
        if sum(item.fail_count for item in self.family_summaries) != self.coverage_summary.failed_scenarios:
            raise ValueError("family fail counts must reconcile to coverage failed_scenarios")
        if sum(item.skipped_count for item in self.family_summaries) != self.coverage_summary.skipped_scenarios:
            raise ValueError("family skipped counts must reconcile to coverage skipped_scenarios")
        if sum(item.zero_visit_scenarios for item in self.family_summaries) != self.coverage_summary.zero_visit_scenarios:
            raise ValueError("family zero-visit counts must reconcile to coverage")
        if sum(item.scenarios_with_three_or_more_visits for item in self.family_summaries) != self.coverage_summary.scenarios_with_three_or_more_visits:
            raise ValueError("family three-plus visit counts must reconcile to coverage")
        if sum(item.transitions_generated for item in self.family_summaries) != self.transition_summary.total_transitions:
            raise ValueError("family transitions must reconcile to transition_summary")
        if sum(item.trajectory_records for item in self.family_summaries) != self.trajectory_summary.total_trajectory_records:
            raise ValueError("family trajectory records must reconcile to trajectory_summary")
        if self.coverage_summary.scenarios_with_transitions != self.transition_summary.scenarios_with_transitions:
            raise ValueError("coverage scenarios_with_transitions must reconcile to transition_summary")
        if sum(item.eligible_hypotheses for item in self.family_summaries) != self.hypothesis_summary.eligible_hypotheses:
            raise ValueError("family eligible hypotheses must reconcile to hypothesis_summary")
        if sum(item.confirmed_hypotheses for item in self.family_summaries) != self.hypothesis_summary.confirmed_hypotheses:
            raise ValueError("family confirmed hypotheses must reconcile to hypothesis_summary")
        if sum(item.pending_hypotheses for item in self.family_summaries) != self.hypothesis_summary.pending_hypotheses:
            raise ValueError("family pending hypotheses must reconcile to hypothesis_summary")
        _require_fingerprint("report_fingerprint", self.report_fingerprint)
        expected = research_campaign_report_fingerprint_payload(
            metadata=self.metadata,
            coverage_summary=self.coverage_summary,
            family_summaries=self.family_summaries,
            transition_summary=self.transition_summary,
            trajectory_summary=self.trajectory_summary,
            hypothesis_summary=self.hypothesis_summary,
            diagnostics=self.diagnostics,
        )
        if self.report_fingerprint != expected:
            raise ValueError("report_fingerprint does not match canonical content")

"""Immutable contracts for single-campaign Project 2 research analysis.

Contracts only: no campaign execution, report generation, comparison, export,
charts, raw observations, or upstream runtime objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    generation_contract_fingerprint,
)

RESEARCH_ANALYSIS_CONTRACTS_VERSION = "PHASE2E_RESEARCH_ANALYSIS_CONTRACTS_V1"

_ALLOWED_SIGNAL_RICHNESS = frozenset(
    {"RICH_SIGNAL", "MEDIUM_SIGNAL", "LOW_SIGNAL", "NO_SIGNAL"}
)
_ALLOWED_SAMPLE_SUFFICIENCY = frozenset(
    {"SUFFICIENT_SAMPLE", "INSUFFICIENT_SAMPLE", "NOT_APPLICABLE"}
)


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


def _require_rate(name: str, value: Decimal | None) -> None:
    if value is None:
        return
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be Decimal or None")
    if value < Decimal("0"):
        raise ValueError(f"{name} must be non-negative")


def _expected_rate(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return Decimal(numerator) / Decimal(denominator)


def _require_expected_rate(name: str, value: Decimal | None, numerator: int, denominator: int) -> None:
    _require_rate(name, value)
    expected = _expected_rate(numerator, denominator)
    if value != expected:
        raise ValueError(f"{name} does not match source counts")


def _require_string_tuple(name: str, value: tuple[str, ...], *, allow_empty: bool = True) -> None:
    _require_tuple(name, value)
    if not allow_empty and not value:
        raise ValueError(f"{name} must not be empty")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{name} must contain non-empty strings")


def _require_sorted_string_tuple(name: str, value: tuple[str, ...]) -> None:
    _require_string_tuple(name, value)
    if tuple(sorted(value)) != value:
        raise ValueError(f"{name} must be sorted canonically")
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must be unique")


def _require_count_pairs(name: str, value: tuple[tuple[str, int], ...]) -> None:
    _require_tuple(name, value)
    if tuple(sorted(value, key=lambda item: item[0])) != value:
        raise ValueError(f"{name} must be sorted by family name")
    seen: set[str] = set()
    for row in value:
        if not isinstance(row, tuple) or len(row) != 2:
            raise TypeError(f"{name} rows must be two-field tuples")
        family_name, count = row
        _require_non_empty(f"{name} family_name", family_name)
        _require_non_negative_int(f"{name} count", count)
        if family_name in seen:
            raise ValueError(f"{name} family names must be unique")
        seen.add(family_name)


def _require_family_hypothesis_rows(
    name: str,
    value: tuple[tuple[str, int, int, int], ...],
) -> None:
    _require_tuple(name, value)
    if tuple(sorted(value, key=lambda item: item[0])) != value:
        raise ValueError(f"{name} must be sorted by family name")
    seen: set[str] = set()
    for row in value:
        if not isinstance(row, tuple) or len(row) != 4:
            raise ValueError(f"{name} rows must have four fields")
        family_name, eligible, confirmed, pending = row
        _require_non_empty("family_name", family_name)
        for field_name, count in (
            ("eligible", eligible),
            ("confirmed", confirmed),
            ("pending", pending),
        ):
            _require_non_negative_int(field_name, count)
        if confirmed + pending > eligible:
            raise ValueError("family hypothesis counts cannot exceed eligible count")
        if family_name in seen:
            raise ValueError(f"{name} family names must be unique")
        seen.add(family_name)


def _require_optional_family_name(name: str, value: str | None) -> None:
    if value is not None:
        _require_non_empty(name, value)


def _top_count_row(rows: tuple[tuple[str, int], ...]) -> tuple[str | None, int]:
    if not rows:
        return None, 0
    family_name, count = max(rows, key=lambda item: (item[1], tuple(reversed(item[0]))))
    return family_name, count


def _require_top_contributor(
    *,
    field_prefix: str,
    total: int,
    rows: tuple[tuple[str, int], ...],
    top_family_name: str | None,
    top_share: Decimal | None,
) -> None:
    expected_name, top_count = _top_count_row(rows)
    expected_share = _expected_rate(top_count, total)
    if top_family_name != expected_name:
        raise ValueError(f"{field_prefix} top contributor family does not match source counts")
    if top_share != expected_share:
        raise ValueError(f"{field_prefix} top contributor share does not match source counts")


def _require_label(name: str, value: str, allowed: frozenset[str]) -> None:
    if value not in allowed:
        raise ValueError(f"{name} has invalid descriptive label")


def _active_signal_dimension_count(family: "ResearchFamilyAnalysis") -> int:
    return sum(
        1
        for value in (
            family.visit_density,
            family.transition_density,
            family.trajectory_density,
            family.eligibility_rate,
        )
        if value is not None and value > Decimal("0")
    )


def _signal_richness_for_count(signal_dimension_count: int) -> str:
    if signal_dimension_count == 0:
        return "NO_SIGNAL"
    if signal_dimension_count == 1:
        return "LOW_SIGNAL"
    if signal_dimension_count in (2, 3):
        return "MEDIUM_SIGNAL"
    if signal_dimension_count == 4:
        return "RICH_SIGNAL"
    raise ValueError("signal_dimension_count must be in the closed interval 0..4")


def _sample_sufficiency_for_family(family: "ResearchFamilyAnalysis") -> str:
    if family.scenarios_generated == 0:
        return "NOT_APPLICABLE"
    if family.eligible_hypotheses > 0:
        return "SUFFICIENT_SAMPLE"
    return "INSUFFICIENT_SAMPLE"


def research_analysis_metadata_fingerprint_payload(
    *,
    analysis_id: str,
    analysis_version: str,
    analysis_engine_version: str,
    source_report_fingerprints: tuple[str, ...],
    source_campaign_result_fingerprint: str,
    source_campaign_designer_fingerprint: str,
) -> str:
    return generation_contract_fingerprint(
        (
            analysis_id,
            analysis_version,
            analysis_engine_version,
            source_report_fingerprints,
            source_campaign_result_fingerprint,
            source_campaign_designer_fingerprint,
        )
    )


def research_family_analysis_fingerprint_payload(
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
    transitions: int,
    trajectory_records: int,
    eligible_hypotheses: int,
    confirmed_hypotheses: int,
    pending_hypotheses: int,
    visit_density: Decimal | None,
    transition_density: Decimal | None,
    trajectory_density: Decimal | None,
    eligibility_rate: Decimal | None,
    confirmation_rate: Decimal | None,
    pending_rate: Decimal | None,
    signal_dimension_count: int,
    signal_richness_class: str,
    sample_sufficiency_class: str,
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
            transitions,
            trajectory_records,
            eligible_hypotheses,
            confirmed_hypotheses,
            pending_hypotheses,
            visit_density,
            transition_density,
            trajectory_density,
            eligibility_rate,
            confirmation_rate,
            pending_rate,
            signal_dimension_count,
            signal_richness_class,
            sample_sufficiency_class,
        )
    )


def research_coverage_analysis_fingerprint_payload(
    *,
    families_observed: int,
    scenarios_generated: int,
    scenarios_executed: int,
    zero_visit_scenarios: int,
    scenarios_with_three_or_more_visits: int,
    scenarios_with_transitions: int,
    zero_visit_rate: Decimal | None,
    three_plus_visit_rate: Decimal | None,
    transition_coverage_rate: Decimal | None,
    coverage_tag_family_counts: tuple[tuple[str, int], ...],
    unique_coverage_tags: tuple[str, ...],
    shared_coverage_tags: tuple[str, ...],
) -> str:
    return generation_contract_fingerprint(
        (
            families_observed,
            scenarios_generated,
            scenarios_executed,
            zero_visit_scenarios,
            scenarios_with_three_or_more_visits,
            scenarios_with_transitions,
            zero_visit_rate,
            three_plus_visit_rate,
            transition_coverage_rate,
            coverage_tag_family_counts,
            unique_coverage_tags,
            shared_coverage_tags,
        )
    )


def research_transition_analysis_fingerprint_payload(
    *,
    total_transitions: int,
    scenarios_with_transitions: int,
    per_family_transition_counts: tuple[tuple[str, int], ...],
    transition_density: Decimal | None,
    top_transition_contributor_family_name: str | None,
    top_transition_contributor_share: Decimal | None,
    families_with_zero_transitions: tuple[str, ...],
) -> str:
    return generation_contract_fingerprint(
        (
            total_transitions,
            scenarios_with_transitions,
            per_family_transition_counts,
            transition_density,
            top_transition_contributor_family_name,
            top_transition_contributor_share,
            families_with_zero_transitions,
        )
    )


def research_trajectory_analysis_fingerprint_payload(
    *,
    total_trajectory_records: int,
    per_family_trajectory_records: tuple[tuple[str, int], ...],
    trajectory_density: Decimal | None,
    top_trajectory_contributor_family_name: str | None,
    top_trajectory_contributor_share: Decimal | None,
    families_with_zero_trajectory_records: tuple[str, ...],
) -> str:
    return generation_contract_fingerprint(
        (
            total_trajectory_records,
            per_family_trajectory_records,
            trajectory_density,
            top_trajectory_contributor_family_name,
            top_trajectory_contributor_share,
            families_with_zero_trajectory_records,
        )
    )


def research_hypothesis_analysis_fingerprint_payload(
    *,
    eligible_hypotheses: int,
    confirmed_hypotheses: int,
    pending_hypotheses: int,
    per_family_hypothesis_counts: tuple[tuple[str, int, int, int], ...],
    eligibility_rate: Decimal | None,
    confirmation_rate: Decimal | None,
    pending_rate: Decimal | None,
    top_eligible_hypothesis_family_name: str | None,
    top_eligible_hypothesis_family_share: Decimal | None,
    families_with_no_eligible_hypotheses: tuple[str, ...],
) -> str:
    return generation_contract_fingerprint(
        (
            eligible_hypotheses,
            confirmed_hypotheses,
            pending_hypotheses,
            per_family_hypothesis_counts,
            eligibility_rate,
            confirmation_rate,
            pending_rate,
            top_eligible_hypothesis_family_name,
            top_eligible_hypothesis_family_share,
            families_with_no_eligible_hypotheses,
        )
    )


def research_campaign_analysis_fingerprint_payload(
    *,
    metadata: "ResearchAnalysisMetadata",
    family_analyses: tuple["ResearchFamilyAnalysis", ...],
    coverage_analysis: "ResearchCoverageAnalysis",
    transition_analysis: "ResearchTransitionAnalysis",
    trajectory_analysis: "ResearchTrajectoryAnalysis",
    hypothesis_analysis: "ResearchHypothesisAnalysis",
    diagnostics: tuple[str, ...],
) -> str:
    return generation_contract_fingerprint(
        (
            metadata,
            family_analyses,
            coverage_analysis,
            transition_analysis,
            trajectory_analysis,
            hypothesis_analysis,
            diagnostics,
        )
    )


@dataclass(frozen=True)
class ResearchAnalysisMetadata:
    analysis_id: str
    analysis_version: str
    analysis_engine_version: str
    source_report_fingerprints: tuple[str, ...]
    source_campaign_result_fingerprint: str
    source_campaign_designer_fingerprint: str
    metadata_fingerprint: str

    def __post_init__(self) -> None:
        _require_non_empty("analysis_id", self.analysis_id)
        _require_non_empty("analysis_version", self.analysis_version)
        _require_non_empty("analysis_engine_version", self.analysis_engine_version)
        _require_tuple("source_report_fingerprints", self.source_report_fingerprints)
        if len(self.source_report_fingerprints) != 1:
            raise ValueError("source_report_fingerprints must contain exactly one item in Phase2E")
        for fingerprint in self.source_report_fingerprints:
            _require_fingerprint("source_report_fingerprints item", fingerprint)
        for field_name in (
            "source_campaign_result_fingerprint",
            "source_campaign_designer_fingerprint",
            "metadata_fingerprint",
        ):
            _require_fingerprint(field_name, getattr(self, field_name))
        expected = research_analysis_metadata_fingerprint_payload(
            analysis_id=self.analysis_id,
            analysis_version=self.analysis_version,
            analysis_engine_version=self.analysis_engine_version,
            source_report_fingerprints=self.source_report_fingerprints,
            source_campaign_result_fingerprint=self.source_campaign_result_fingerprint,
            source_campaign_designer_fingerprint=self.source_campaign_designer_fingerprint,
        )
        if self.metadata_fingerprint != expected:
            raise ValueError("metadata_fingerprint does not match canonical content")


@dataclass(frozen=True)
class ResearchFamilyAnalysis:
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
    transitions: int
    trajectory_records: int
    eligible_hypotheses: int
    confirmed_hypotheses: int
    pending_hypotheses: int
    visit_density: Decimal | None
    transition_density: Decimal | None
    trajectory_density: Decimal | None
    eligibility_rate: Decimal | None
    confirmation_rate: Decimal | None
    pending_rate: Decimal | None
    signal_dimension_count: int
    signal_richness_class: str
    sample_sufficiency_class: str
    family_analysis_fingerprint: str

    def __post_init__(self) -> None:
        _require_non_empty("family_name", self.family_name)
        _require_sorted_string_tuple("coverage_tags", self.coverage_tags)
        for field_name in (
            "scenarios_generated",
            "scenarios_executed",
            "pass_count",
            "fail_count",
            "skipped_count",
            "completed_visits",
            "zero_visit_scenarios",
            "scenarios_with_three_or_more_visits",
            "transitions",
            "trajectory_records",
            "eligible_hypotheses",
            "confirmed_hypotheses",
            "pending_hypotheses",
            "signal_dimension_count",
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
        _require_expected_rate("visit_density", self.visit_density, self.completed_visits, self.scenarios_generated)
        _require_expected_rate("transition_density", self.transition_density, self.transitions, self.scenarios_generated)
        _require_expected_rate("trajectory_density", self.trajectory_density, self.trajectory_records, self.scenarios_generated)
        _require_expected_rate("eligibility_rate", self.eligibility_rate, self.eligible_hypotheses, self.scenarios_generated)
        _require_expected_rate("confirmation_rate", self.confirmation_rate, self.confirmed_hypotheses, self.eligible_hypotheses)
        _require_expected_rate("pending_rate", self.pending_rate, self.pending_hypotheses, self.eligible_hypotheses)
        if self.signal_dimension_count > 4:
            raise ValueError("signal_dimension_count must be in the closed interval 0..4")
        _require_label("signal_richness_class", self.signal_richness_class, _ALLOWED_SIGNAL_RICHNESS)
        _require_label("sample_sufficiency_class", self.sample_sufficiency_class, _ALLOWED_SAMPLE_SUFFICIENCY)
        _require_fingerprint("family_analysis_fingerprint", self.family_analysis_fingerprint)
        expected = research_family_analysis_fingerprint_payload(
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
            transitions=self.transitions,
            trajectory_records=self.trajectory_records,
            eligible_hypotheses=self.eligible_hypotheses,
            confirmed_hypotheses=self.confirmed_hypotheses,
            pending_hypotheses=self.pending_hypotheses,
            visit_density=self.visit_density,
            transition_density=self.transition_density,
            trajectory_density=self.trajectory_density,
            eligibility_rate=self.eligibility_rate,
            confirmation_rate=self.confirmation_rate,
            pending_rate=self.pending_rate,
            signal_dimension_count=self.signal_dimension_count,
            signal_richness_class=self.signal_richness_class,
            sample_sufficiency_class=self.sample_sufficiency_class,
        )
        if self.family_analysis_fingerprint != expected:
            raise ValueError("family_analysis_fingerprint does not match canonical content")


@dataclass(frozen=True)
class ResearchCoverageAnalysis:
    families_observed: int
    scenarios_generated: int
    scenarios_executed: int
    zero_visit_scenarios: int
    scenarios_with_three_or_more_visits: int
    scenarios_with_transitions: int
    zero_visit_rate: Decimal | None
    three_plus_visit_rate: Decimal | None
    transition_coverage_rate: Decimal | None
    coverage_tag_family_counts: tuple[tuple[str, int], ...]
    unique_coverage_tags: tuple[str, ...]
    shared_coverage_tags: tuple[str, ...]
    coverage_analysis_fingerprint: str

    def __post_init__(self) -> None:
        for field_name in (
            "families_observed",
            "scenarios_generated",
            "scenarios_executed",
            "zero_visit_scenarios",
            "scenarios_with_three_or_more_visits",
            "scenarios_with_transitions",
        ):
            _require_non_negative_int(field_name, getattr(self, field_name))
        if self.scenarios_executed > self.scenarios_generated:
            raise ValueError("scenarios_executed cannot exceed scenarios_generated")
        for field_name in (
            "zero_visit_scenarios",
            "scenarios_with_three_or_more_visits",
            "scenarios_with_transitions",
        ):
            if getattr(self, field_name) > self.scenarios_generated:
                raise ValueError(f"{field_name} cannot exceed scenarios_generated")
        _require_expected_rate("zero_visit_rate", self.zero_visit_rate, self.zero_visit_scenarios, self.scenarios_generated)
        _require_expected_rate("three_plus_visit_rate", self.three_plus_visit_rate, self.scenarios_with_three_or_more_visits, self.scenarios_generated)
        _require_expected_rate("transition_coverage_rate", self.transition_coverage_rate, self.scenarios_with_transitions, self.scenarios_generated)
        _require_count_pairs("coverage_tag_family_counts", self.coverage_tag_family_counts)
        _require_sorted_string_tuple("unique_coverage_tags", self.unique_coverage_tags)
        _require_sorted_string_tuple("shared_coverage_tags", self.shared_coverage_tags)
        if not set(self.shared_coverage_tags).issubset(set(self.unique_coverage_tags)):
            raise ValueError("shared_coverage_tags must be a subset of unique_coverage_tags")
        _require_fingerprint("coverage_analysis_fingerprint", self.coverage_analysis_fingerprint)
        expected = research_coverage_analysis_fingerprint_payload(
            families_observed=self.families_observed,
            scenarios_generated=self.scenarios_generated,
            scenarios_executed=self.scenarios_executed,
            zero_visit_scenarios=self.zero_visit_scenarios,
            scenarios_with_three_or_more_visits=self.scenarios_with_three_or_more_visits,
            scenarios_with_transitions=self.scenarios_with_transitions,
            zero_visit_rate=self.zero_visit_rate,
            three_plus_visit_rate=self.three_plus_visit_rate,
            transition_coverage_rate=self.transition_coverage_rate,
            coverage_tag_family_counts=self.coverage_tag_family_counts,
            unique_coverage_tags=self.unique_coverage_tags,
            shared_coverage_tags=self.shared_coverage_tags,
        )
        if self.coverage_analysis_fingerprint != expected:
            raise ValueError("coverage_analysis_fingerprint does not match canonical content")


@dataclass(frozen=True)
class ResearchTransitionAnalysis:
    total_transitions: int
    scenarios_with_transitions: int
    per_family_transition_counts: tuple[tuple[str, int], ...]
    transition_density: Decimal | None
    top_transition_contributor_family_name: str | None
    top_transition_contributor_share: Decimal | None
    families_with_zero_transitions: tuple[str, ...]
    transition_analysis_fingerprint: str

    def __post_init__(self) -> None:
        _require_non_negative_int("total_transitions", self.total_transitions)
        _require_non_negative_int("scenarios_with_transitions", self.scenarios_with_transitions)
        _require_count_pairs("per_family_transition_counts", self.per_family_transition_counts)
        if sum(count for _, count in self.per_family_transition_counts) != self.total_transitions:
            raise ValueError("per_family_transition_counts must reconcile to total_transitions")
        _require_expected_rate("transition_density", self.transition_density, self.total_transitions, self.scenarios_with_transitions)
        _require_optional_family_name("top_transition_contributor_family_name", self.top_transition_contributor_family_name)
        _require_rate("top_transition_contributor_share", self.top_transition_contributor_share)
        _require_top_contributor(
            field_prefix="transition",
            total=self.total_transitions,
            rows=self.per_family_transition_counts,
            top_family_name=self.top_transition_contributor_family_name,
            top_share=self.top_transition_contributor_share,
        )
        _require_sorted_string_tuple("families_with_zero_transitions", self.families_with_zero_transitions)
        family_names = {name for name, _ in self.per_family_transition_counts}
        if not set(self.families_with_zero_transitions).issubset(family_names):
            raise ValueError("families_with_zero_transitions must be known families")
        _require_fingerprint("transition_analysis_fingerprint", self.transition_analysis_fingerprint)
        expected = research_transition_analysis_fingerprint_payload(
            total_transitions=self.total_transitions,
            scenarios_with_transitions=self.scenarios_with_transitions,
            per_family_transition_counts=self.per_family_transition_counts,
            transition_density=self.transition_density,
            top_transition_contributor_family_name=self.top_transition_contributor_family_name,
            top_transition_contributor_share=self.top_transition_contributor_share,
            families_with_zero_transitions=self.families_with_zero_transitions,
        )
        if self.transition_analysis_fingerprint != expected:
            raise ValueError("transition_analysis_fingerprint does not match canonical content")


@dataclass(frozen=True)
class ResearchTrajectoryAnalysis:
    total_trajectory_records: int
    per_family_trajectory_records: tuple[tuple[str, int], ...]
    trajectory_density: Decimal | None
    top_trajectory_contributor_family_name: str | None
    top_trajectory_contributor_share: Decimal | None
    families_with_zero_trajectory_records: tuple[str, ...]
    trajectory_analysis_fingerprint: str

    def __post_init__(self) -> None:
        _require_non_negative_int("total_trajectory_records", self.total_trajectory_records)
        _require_count_pairs("per_family_trajectory_records", self.per_family_trajectory_records)
        if sum(count for _, count in self.per_family_trajectory_records) != self.total_trajectory_records:
            raise ValueError("per_family_trajectory_records must reconcile to total_trajectory_records")
        _require_rate("trajectory_density", self.trajectory_density)
        _require_optional_family_name("top_trajectory_contributor_family_name", self.top_trajectory_contributor_family_name)
        _require_rate("top_trajectory_contributor_share", self.top_trajectory_contributor_share)
        _require_top_contributor(
            field_prefix="trajectory",
            total=self.total_trajectory_records,
            rows=self.per_family_trajectory_records,
            top_family_name=self.top_trajectory_contributor_family_name,
            top_share=self.top_trajectory_contributor_share,
        )
        _require_sorted_string_tuple("families_with_zero_trajectory_records", self.families_with_zero_trajectory_records)
        family_names = {name for name, _ in self.per_family_trajectory_records}
        if not set(self.families_with_zero_trajectory_records).issubset(family_names):
            raise ValueError("families_with_zero_trajectory_records must be known families")
        _require_fingerprint("trajectory_analysis_fingerprint", self.trajectory_analysis_fingerprint)
        expected = research_trajectory_analysis_fingerprint_payload(
            total_trajectory_records=self.total_trajectory_records,
            per_family_trajectory_records=self.per_family_trajectory_records,
            trajectory_density=self.trajectory_density,
            top_trajectory_contributor_family_name=self.top_trajectory_contributor_family_name,
            top_trajectory_contributor_share=self.top_trajectory_contributor_share,
            families_with_zero_trajectory_records=self.families_with_zero_trajectory_records,
        )
        if self.trajectory_analysis_fingerprint != expected:
            raise ValueError("trajectory_analysis_fingerprint does not match canonical content")


@dataclass(frozen=True)
class ResearchHypothesisAnalysis:
    eligible_hypotheses: int
    confirmed_hypotheses: int
    pending_hypotheses: int
    per_family_hypothesis_counts: tuple[tuple[str, int, int, int], ...]
    eligibility_rate: Decimal | None
    confirmation_rate: Decimal | None
    pending_rate: Decimal | None
    top_eligible_hypothesis_family_name: str | None
    top_eligible_hypothesis_family_share: Decimal | None
    families_with_no_eligible_hypotheses: tuple[str, ...]
    hypothesis_analysis_fingerprint: str

    def __post_init__(self) -> None:
        for field_name in ("eligible_hypotheses", "confirmed_hypotheses", "pending_hypotheses"):
            _require_non_negative_int(field_name, getattr(self, field_name))
        if self.confirmed_hypotheses + self.pending_hypotheses > self.eligible_hypotheses:
            raise ValueError("hypothesis counts cannot exceed eligible_hypotheses")
        _require_family_hypothesis_rows("per_family_hypothesis_counts", self.per_family_hypothesis_counts)
        if sum(row[1] for row in self.per_family_hypothesis_counts) != self.eligible_hypotheses:
            raise ValueError("per-family eligible counts must reconcile")
        if sum(row[2] for row in self.per_family_hypothesis_counts) != self.confirmed_hypotheses:
            raise ValueError("per-family confirmed counts must reconcile")
        if sum(row[3] for row in self.per_family_hypothesis_counts) != self.pending_hypotheses:
            raise ValueError("per-family pending counts must reconcile")
        _require_rate("eligibility_rate", self.eligibility_rate)
        _require_expected_rate("confirmation_rate", self.confirmation_rate, self.confirmed_hypotheses, self.eligible_hypotheses)
        _require_expected_rate("pending_rate", self.pending_rate, self.pending_hypotheses, self.eligible_hypotheses)
        _require_optional_family_name("top_eligible_hypothesis_family_name", self.top_eligible_hypothesis_family_name)
        _require_rate("top_eligible_hypothesis_family_share", self.top_eligible_hypothesis_family_share)
        _require_top_contributor(
            field_prefix="hypothesis",
            total=self.eligible_hypotheses,
            rows=tuple((family_name, eligible) for family_name, eligible, _, _ in self.per_family_hypothesis_counts),
            top_family_name=self.top_eligible_hypothesis_family_name,
            top_share=self.top_eligible_hypothesis_family_share,
        )
        _require_sorted_string_tuple("families_with_no_eligible_hypotheses", self.families_with_no_eligible_hypotheses)
        family_names = {row[0] for row in self.per_family_hypothesis_counts}
        if not set(self.families_with_no_eligible_hypotheses).issubset(family_names):
            raise ValueError("families_with_no_eligible_hypotheses must be known families")
        _require_fingerprint("hypothesis_analysis_fingerprint", self.hypothesis_analysis_fingerprint)
        expected = research_hypothesis_analysis_fingerprint_payload(
            eligible_hypotheses=self.eligible_hypotheses,
            confirmed_hypotheses=self.confirmed_hypotheses,
            pending_hypotheses=self.pending_hypotheses,
            per_family_hypothesis_counts=self.per_family_hypothesis_counts,
            eligibility_rate=self.eligibility_rate,
            confirmation_rate=self.confirmation_rate,
            pending_rate=self.pending_rate,
            top_eligible_hypothesis_family_name=self.top_eligible_hypothesis_family_name,
            top_eligible_hypothesis_family_share=self.top_eligible_hypothesis_family_share,
            families_with_no_eligible_hypotheses=self.families_with_no_eligible_hypotheses,
        )
        if self.hypothesis_analysis_fingerprint != expected:
            raise ValueError("hypothesis_analysis_fingerprint does not match canonical content")


@dataclass(frozen=True)
class ResearchCampaignAnalysis:
    metadata: ResearchAnalysisMetadata
    family_analyses: tuple[ResearchFamilyAnalysis, ...]
    coverage_analysis: ResearchCoverageAnalysis
    transition_analysis: ResearchTransitionAnalysis
    trajectory_analysis: ResearchTrajectoryAnalysis
    hypothesis_analysis: ResearchHypothesisAnalysis
    diagnostics: tuple[str, ...]
    campaign_analysis_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.metadata, ResearchAnalysisMetadata):
            raise TypeError("metadata must be ResearchAnalysisMetadata")
        _require_tuple("family_analyses", self.family_analyses)
        if not self.family_analyses:
            raise ValueError("family_analyses must not be empty")
        if not all(isinstance(value, ResearchFamilyAnalysis) for value in self.family_analyses):
            raise TypeError("family_analyses must contain ResearchFamilyAnalysis values")
        family_names = tuple(family.family_name for family in self.family_analyses)
        if tuple(sorted(family_names)) != family_names:
            raise ValueError("family_analyses must be sorted by family_name")
        if len(set(family_names)) != len(family_names):
            raise ValueError("family_analyses family names must be unique")
        if not isinstance(self.coverage_analysis, ResearchCoverageAnalysis):
            raise TypeError("coverage_analysis must be ResearchCoverageAnalysis")
        if not isinstance(self.transition_analysis, ResearchTransitionAnalysis):
            raise TypeError("transition_analysis must be ResearchTransitionAnalysis")
        if not isinstance(self.trajectory_analysis, ResearchTrajectoryAnalysis):
            raise TypeError("trajectory_analysis must be ResearchTrajectoryAnalysis")
        if not isinstance(self.hypothesis_analysis, ResearchHypothesisAnalysis):
            raise TypeError("hypothesis_analysis must be ResearchHypothesisAnalysis")
        _require_tuple("diagnostics", self.diagnostics)
        if not all(isinstance(value, str) for value in self.diagnostics):
            raise TypeError("diagnostics must contain strings")
        if tuple(sorted(self.diagnostics)) != self.diagnostics:
            raise ValueError("diagnostics must be sorted canonically")
        if self.coverage_analysis.families_observed != len(self.family_analyses):
            raise ValueError("coverage families_observed must reconcile")
        if self.coverage_analysis.scenarios_generated != sum(family.scenarios_generated for family in self.family_analyses):
            raise ValueError("coverage scenarios_generated must reconcile")
        if self.coverage_analysis.scenarios_executed != sum(family.scenarios_executed for family in self.family_analyses):
            raise ValueError("coverage scenarios_executed must reconcile")
        if self.coverage_analysis.zero_visit_scenarios != sum(family.zero_visit_scenarios for family in self.family_analyses):
            raise ValueError("coverage zero_visit_scenarios must reconcile")
        if self.coverage_analysis.scenarios_with_three_or_more_visits != sum(
            family.scenarios_with_three_or_more_visits for family in self.family_analyses
        ):
            raise ValueError("coverage scenarios_with_three_or_more_visits must reconcile")
        coverage_counts: dict[str, int] = {}
        for family in self.family_analyses:
            for tag in family.coverage_tags:
                coverage_counts[tag] = coverage_counts.get(tag, 0) + 1
        expected_coverage_tag_family_counts = tuple(sorted(coverage_counts.items()))
        expected_unique_coverage_tags = tuple(sorted(coverage_counts))
        expected_shared_coverage_tags = tuple(sorted(tag for tag, count in coverage_counts.items() if count > 1))
        if self.coverage_analysis.coverage_tag_family_counts != expected_coverage_tag_family_counts:
            raise ValueError("coverage_tag_family_counts must reconcile from family coverage_tags")
        if self.coverage_analysis.unique_coverage_tags != expected_unique_coverage_tags:
            raise ValueError("unique_coverage_tags must reconcile from family coverage_tags")
        if self.coverage_analysis.shared_coverage_tags != expected_shared_coverage_tags:
            raise ValueError("shared_coverage_tags must reconcile from family coverage_tags")
        if self.transition_analysis.total_transitions != sum(family.transitions for family in self.family_analyses):
            raise ValueError("transition totals must reconcile by family")
        if self.trajectory_analysis.total_trajectory_records != sum(family.trajectory_records for family in self.family_analyses):
            raise ValueError("trajectory totals must reconcile by family")
        for family in self.family_analyses:
            expected_signal_dimension_count = _active_signal_dimension_count(family)
            if family.signal_dimension_count != expected_signal_dimension_count:
                raise ValueError("family signal_dimension_count must reconcile from source dimensions")
            expected_signal_richness = _signal_richness_for_count(expected_signal_dimension_count)
            if family.signal_richness_class != expected_signal_richness:
                raise ValueError("family signal_richness_class must reconcile from signal_dimension_count")
            expected_sample_sufficiency = _sample_sufficiency_for_family(family)
            if family.sample_sufficiency_class != expected_sample_sufficiency:
                raise ValueError("family sample_sufficiency_class must reconcile from source counts")
        expected_zero_transition_families = tuple(
            sorted(family.family_name for family in self.family_analyses if family.transitions == 0)
        )
        if self.transition_analysis.families_with_zero_transitions != expected_zero_transition_families:
            raise ValueError("families_with_zero_transitions must exactly reconcile from family analyses")
        expected_zero_trajectory_families = tuple(
            sorted(family.family_name for family in self.family_analyses if family.trajectory_records == 0)
        )
        if self.trajectory_analysis.families_with_zero_trajectory_records != expected_zero_trajectory_families:
            raise ValueError("families_with_zero_trajectory_records must exactly reconcile from family analyses")
        expected_no_eligible_families = tuple(
            sorted(family.family_name for family in self.family_analyses if family.eligible_hypotheses == 0)
        )
        if self.hypothesis_analysis.families_with_no_eligible_hypotheses != expected_no_eligible_families:
            raise ValueError("families_with_no_eligible_hypotheses must exactly reconcile from family analyses")
        _require_expected_rate(
            "trajectory_analysis.trajectory_density",
            self.trajectory_analysis.trajectory_density,
            self.trajectory_analysis.total_trajectory_records,
            self.coverage_analysis.scenarios_generated,
        )
        _require_expected_rate(
            "hypothesis_analysis.eligibility_rate",
            self.hypothesis_analysis.eligibility_rate,
            self.hypothesis_analysis.eligible_hypotheses,
            self.coverage_analysis.scenarios_generated,
        )
        hypothesis_by_family = {row[0]: row for row in self.hypothesis_analysis.per_family_hypothesis_counts}
        if set(hypothesis_by_family) != set(family_names):
            raise ValueError("hypothesis family names must match family_analyses")
        for family in self.family_analyses:
            _, eligible, confirmed, pending = hypothesis_by_family[family.family_name]
            if (
                eligible != family.eligible_hypotheses
                or confirmed != family.confirmed_hypotheses
                or pending != family.pending_hypotheses
            ):
                raise ValueError("hypothesis counts must reconcile by family_name")
        _require_fingerprint("campaign_analysis_fingerprint", self.campaign_analysis_fingerprint)
        expected = research_campaign_analysis_fingerprint_payload(
            metadata=self.metadata,
            family_analyses=self.family_analyses,
            coverage_analysis=self.coverage_analysis,
            transition_analysis=self.transition_analysis,
            trajectory_analysis=self.trajectory_analysis,
            hypothesis_analysis=self.hypothesis_analysis,
            diagnostics=self.diagnostics,
        )
        if self.campaign_analysis_fingerprint != expected:
            raise ValueError("campaign_analysis_fingerprint does not match canonical content")

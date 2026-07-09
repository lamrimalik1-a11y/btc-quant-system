"""Contracts for the Project 2 Campaign Designer layer.

Contracts only: no generation calls, manifest validation, compilation, assembly,
batch execution, Scenario Runner, Catalog, Stage 1-6, Project 1, or production
coupling.
"""

from __future__ import annotations

from dataclasses import dataclass

from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    GrammarTemplate,
    generation_contract_fingerprint,
)

CAMPAIGN_CONTRACTS_VERSION = "PHASE2D_CAMPAIGN_CONTRACTS_V1"
_FORBIDDEN_COVERAGE_TOKENS = (
    "research_",
    "dynamic_state",
    "trajectory_label",
    "transition_label",
    "hypothesis_label",
    "expected_transition",
    "expected_trajectory",
    "expected_hypothesis",
    "confirmed_hypothesis",
    "pending_hypothesis",
    "attacker_pressure",
    "buy",
    "sell",
    "trade",
    "entry_signal",
    "exit_signal",
)


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_tuple(name: str, value: tuple[object, ...]) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{name} must be tuple")


def _require_non_negative_int(name: str, value: int) -> None:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _require_positive_int(name: str, value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _require_fingerprint(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        raise ValueError(f"{name} must be SHA-256")


def _require_optional_fingerprint(name: str, value: str | None) -> None:
    if value is not None:
        _require_fingerprint(name, value)


def _require_string_tuple(name: str, value: tuple[str, ...], *, allow_empty: bool) -> None:
    _require_tuple(name, value)
    if not allow_empty and not value:
        raise ValueError(f"{name} must not be empty")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{name} must contain non-empty strings")


def _validate_coverage_tags(tags: tuple[str, ...]) -> None:
    _require_string_tuple("coverage_tags", tags, allow_empty=False)
    normalized = tuple(tag.strip().lower() for tag in tags)
    if len(normalized) != len(set(normalized)):
        raise ValueError("coverage_tags must be unique")
    for tag in normalized:
        if any(token in tag for token in _FORBIDDEN_COVERAGE_TOKENS):
            raise ValueError("coverage_tags must describe authoring coverage only")


def campaign_specification_fingerprint_payload(
    *,
    campaign_id: str,
    campaign_version: str,
    campaign_goal: str,
    families: tuple["CampaignFamilySpec", ...],
    target_scenario_count: int,
) -> str:
    """Fingerprint CampaignSpecification content, excluding its own fingerprint."""

    return generation_contract_fingerprint(
        (
            campaign_id,
            campaign_version,
            campaign_goal,
            families,
            target_scenario_count,
        )
    )


def campaign_result_fingerprint_payload(
    *,
    success: bool,
    campaign_id: str,
    total_generated: int,
    total_executed: int,
    total_passed: int,
    total_failed: int,
    total_skipped: int,
    family_results: tuple["CampaignFamilyResult", ...],
    campaign_designer_version: str,
    diagnostics: tuple[str, ...],
) -> str:
    """Fingerprint CampaignResult content, excluding its own fingerprint."""

    return generation_contract_fingerprint(
        (
            success,
            campaign_id,
            total_generated,
            total_executed,
            total_passed,
            total_failed,
            total_skipped,
            family_results,
            campaign_designer_version,
            diagnostics,
        )
    )


@dataclass(frozen=True)
class CampaignFamilySpec:
    family_name: str
    template: GrammarTemplate
    coverage_tags: tuple[str, ...]
    target_count: int
    notes: str

    def __post_init__(self) -> None:
        _require_non_empty("family_name", self.family_name)
        if not isinstance(self.template, GrammarTemplate):
            raise TypeError("template must be GrammarTemplate")
        _validate_coverage_tags(self.coverage_tags)
        _require_positive_int("target_count", self.target_count)
        _require_non_empty("notes", self.notes)


@dataclass(frozen=True)
class CampaignSpecification:
    campaign_id: str
    campaign_version: str
    campaign_goal: str
    families: tuple[CampaignFamilySpec, ...]
    target_scenario_count: int
    campaign_specification_fingerprint: str

    def __post_init__(self) -> None:
        _require_non_empty("campaign_id", self.campaign_id)
        _require_non_empty("campaign_version", self.campaign_version)
        _require_non_empty("campaign_goal", self.campaign_goal)
        _require_tuple("families", self.families)
        if not self.families:
            raise ValueError("families must not be empty")
        if not all(isinstance(item, CampaignFamilySpec) for item in self.families):
            raise TypeError("families must contain CampaignFamilySpec values")
        _require_positive_int("target_scenario_count", self.target_scenario_count)
        family_names = tuple(family.family_name for family in self.families)
        if len(family_names) != len(set(family_names)):
            raise ValueError("family_name values must be unique")
        declared_total = sum(family.target_count for family in self.families)
        if declared_total != self.target_scenario_count:
            raise ValueError("family target_count values must reconcile to target_scenario_count")
        _require_fingerprint("campaign_specification_fingerprint", self.campaign_specification_fingerprint)
        expected = campaign_specification_fingerprint_payload(
            campaign_id=self.campaign_id,
            campaign_version=self.campaign_version,
            campaign_goal=self.campaign_goal,
            families=self.families,
            target_scenario_count=self.target_scenario_count,
        )
        if self.campaign_specification_fingerprint != expected:
            raise ValueError("campaign_specification_fingerprint does not match canonical content")


@dataclass(frozen=True)
class CampaignFamilyResult:
    family_name: str
    coverage_tags: tuple[str, ...]
    batch_execution_fingerprint: str | None
    generated_count: int
    executed_count: int
    passed_count: int
    failed_count: int
    skipped_count: int

    def __post_init__(self) -> None:
        _require_non_empty("family_name", self.family_name)
        _validate_coverage_tags(self.coverage_tags)
        _require_optional_fingerprint("batch_execution_fingerprint", self.batch_execution_fingerprint)
        for field_name in (
            "generated_count",
            "executed_count",
            "passed_count",
            "failed_count",
            "skipped_count",
        ):
            _require_non_negative_int(field_name, getattr(self, field_name))
        if self.passed_count + self.failed_count + self.skipped_count != self.executed_count:
            raise ValueError("family result counts must reconcile to executed_count")
        if self.executed_count > self.generated_count:
            raise ValueError("executed_count cannot exceed generated_count")


@dataclass(frozen=True)
class CampaignResult:
    success: bool
    campaign_id: str
    total_generated: int
    total_executed: int
    total_passed: int
    total_failed: int
    total_skipped: int
    family_results: tuple[CampaignFamilyResult, ...]
    campaign_fingerprint: str
    campaign_designer_version: str
    diagnostics: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")
        _require_non_empty("campaign_id", self.campaign_id)
        for field_name in (
            "total_generated",
            "total_executed",
            "total_passed",
            "total_failed",
            "total_skipped",
        ):
            _require_non_negative_int(field_name, getattr(self, field_name))
        _require_tuple("family_results", self.family_results)
        if not all(isinstance(item, CampaignFamilyResult) for item in self.family_results):
            raise TypeError("family_results must contain CampaignFamilyResult values")
        if sum(item.generated_count for item in self.family_results) != self.total_generated:
            raise ValueError("family generated counts must reconcile to total_generated")
        if sum(item.executed_count for item in self.family_results) != self.total_executed:
            raise ValueError("family executed counts must reconcile to total_executed")
        if sum(item.passed_count for item in self.family_results) != self.total_passed:
            raise ValueError("family passed counts must reconcile to total_passed")
        if sum(item.failed_count for item in self.family_results) != self.total_failed:
            raise ValueError("family failed counts must reconcile to total_failed")
        if sum(item.skipped_count for item in self.family_results) != self.total_skipped:
            raise ValueError("family skipped counts must reconcile to total_skipped")
        if self.total_passed + self.total_failed + self.total_skipped != self.total_executed:
            raise ValueError("campaign counts must reconcile to total_executed")
        _require_fingerprint("campaign_fingerprint", self.campaign_fingerprint)
        _require_non_empty("campaign_designer_version", self.campaign_designer_version)
        _require_string_tuple("diagnostics", self.diagnostics, allow_empty=True)
        if self.success and (self.total_failed or self.total_skipped or self.diagnostics):
            raise ValueError("successful campaign result cannot carry failures, skips, or diagnostics")
        if not self.success and not (self.total_failed or self.total_skipped or self.diagnostics):
            raise ValueError("failed campaign result requires failures, skips, or diagnostics")
        expected = campaign_result_fingerprint_payload(
            success=self.success,
            campaign_id=self.campaign_id,
            total_generated=self.total_generated,
            total_executed=self.total_executed,
            total_passed=self.total_passed,
            total_failed=self.total_failed,
            total_skipped=self.total_skipped,
            family_results=self.family_results,
            campaign_designer_version=self.campaign_designer_version,
            diagnostics=self.diagnostics,
        )
        if self.campaign_fingerprint != expected:
            raise ValueError("campaign_fingerprint does not match canonical content")
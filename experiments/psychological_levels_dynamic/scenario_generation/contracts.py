"""Immutable contracts for the Scenario Generation Engine foundation.

Contracts only: no generation logic, no compiler calls, no runner calls, and no
scenario execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

_ALLOWED_RULE_SEVERITIES = frozenset({"INFO", "WARNING", "REJECT"})
_ALLOWED_GENERATION_STATUS = frozenset(
    {"GENERATED", "SKIPPED_DUPLICATE", "REJECTED_BY_RULE"}
)
_ALLOWED_COMPILATION_STATUS = frozenset({"NOT_ATTEMPTED", "SUCCESS", "FAILED"})


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_tuple(name: str, value: tuple[Any, ...]) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{name} must be tuple")


def _require_pair_tuple(name: str, value: tuple[tuple[str, Any], ...]) -> None:
    _require_tuple(name, value)
    for pair in value:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise TypeError(f"{name} must contain immutable pairs")
        if not isinstance(pair[0], str) or not pair[0].strip():
            raise ValueError(f"{name} pair names must not be empty")


def _require_fingerprint(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        raise ValueError(f"{name} must be SHA-256")


def _require_optional_fingerprint(name: str, value: str | None) -> None:
    if value is not None:
        _require_fingerprint(name, value)


def _canonical(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, Decimal):
        normalized = value.normalize()
        return {"type": "decimal", "value": "0" if normalized == 0 else format(normalized, "f")}
    if isinstance(value, Enum):
        return {"type": type(value).__name__, "value": _canonical(value.value)}
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    if is_dataclass(value) and getattr(value, "__dataclass_params__").frozen:
        return {
            field.name: _canonical(getattr(value, field.name))
            for field in fields(value)
        }
    raise TypeError(f"unsupported canonical type: {type(value).__name__}")


def generation_contract_fingerprint(value: Any) -> str:
    """Deterministic canonical JSON + SHA-256 for generation contracts."""

    payload = _canonical(value)
    canonical_json = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return "sha256:" + hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class GenerationCampaign:
    campaign_id: str
    campaign_version: str
    description: str
    research_goal: str
    manifest_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_non_empty("campaign_id", self.campaign_id)
        _require_non_empty("campaign_version", self.campaign_version)
        _require_non_empty("description", self.description)
        _require_non_empty("research_goal", self.research_goal)
        _require_tuple("manifest_ids", self.manifest_ids)
        if not all(isinstance(value, str) and value.strip() for value in self.manifest_ids):
            raise ValueError("manifest_ids must contain non-empty strings")


@dataclass(frozen=True)
class ParameterAxis:
    axis_name: str
    values: tuple[Any, ...]

    def __post_init__(self) -> None:
        _require_non_empty("axis_name", self.axis_name)
        _require_tuple("values", self.values)
        if not self.values:
            raise ValueError("values must not be empty")
        for value in self.values:
            if isinstance(value, (list, set, dict)):
                raise TypeError("axis values must not be mutable containers")


@dataclass(frozen=True)
class PhraseSlot:
    constructor_name: str
    fixed_params: tuple[tuple[str, Any], ...]
    axis_bound_params: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _require_non_empty("constructor_name", self.constructor_name)
        _require_pair_tuple("fixed_params", self.fixed_params)
        _require_pair_tuple("axis_bound_params", self.axis_bound_params)
        fixed_names = {name for name, _ in self.fixed_params}
        axis_bound_names = {name for name, _ in self.axis_bound_params}
        collisions = fixed_names & axis_bound_names
        if collisions:
            raise ValueError("parameter cannot be both fixed and axis-bound")
        for parameter_name, axis_name in self.axis_bound_params:
            _require_non_empty("axis_bound parameter name", parameter_name)
            _require_non_empty("axis_bound axis name", axis_name)


@dataclass(frozen=True)
class GenerationRule:
    rule_id: str
    description: str
    severity: str

    def __post_init__(self) -> None:
        _require_non_empty("rule_id", self.rule_id)
        _require_non_empty("description", self.description)
        if self.severity not in _ALLOWED_RULE_SEVERITIES:
            raise ValueError("invalid rule severity")


@dataclass(frozen=True)
class GrammarTemplate:
    template_id: str
    template_version: str
    family_tag: str
    description: str
    phrase_slots: tuple[PhraseSlot, ...]
    axes: tuple[ParameterAxis, ...]
    rules: tuple[GenerationRule, ...]

    def __post_init__(self) -> None:
        _require_non_empty("template_id", self.template_id)
        _require_non_empty("template_version", self.template_version)
        _require_non_empty("family_tag", self.family_tag)
        _require_non_empty("description", self.description)
        _require_tuple("phrase_slots", self.phrase_slots)
        if not self.phrase_slots:
            raise ValueError("phrase_slots must not be empty")
        if not all(isinstance(value, PhraseSlot) for value in self.phrase_slots):
            raise TypeError("phrase_slots must contain PhraseSlot values")
        _require_tuple("axes", self.axes)
        if not all(isinstance(value, ParameterAxis) for value in self.axes):
            raise TypeError("axes must contain ParameterAxis values")
        _require_tuple("rules", self.rules)
        if not all(isinstance(value, GenerationRule) for value in self.rules):
            raise TypeError("rules must contain GenerationRule values")
        axis_names = {axis.axis_name for axis in self.axes}
        for slot in self.phrase_slots:
            for _, axis_name in slot.axis_bound_params:
                if axis_name not in axis_names:
                    raise ValueError("axis_bound_params references an unknown axis")


@dataclass(frozen=True)
class ManifestEntry:
    entry_index: int
    entry_id: str
    template_id: str
    family_tag: str
    resolved_parameters: tuple[tuple[str, Any], ...]
    combination_fingerprint: str
    program_fingerprint: str | None
    generation_status: str
    rejection_reason: str | None
    compilation_status: str
    compilation_diagnostics: tuple[str, ...]
    geometry_fingerprint: str | None
    observation_checksum: str | None
    specification_fingerprint: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.entry_index, int) or self.entry_index < 0:
            raise ValueError("entry_index must be non-negative")
        _require_non_empty("entry_id", self.entry_id)
        _require_non_empty("template_id", self.template_id)
        _require_non_empty("family_tag", self.family_tag)
        _require_pair_tuple("resolved_parameters", self.resolved_parameters)
        _require_fingerprint("combination_fingerprint", self.combination_fingerprint)
        _require_optional_fingerprint("program_fingerprint", self.program_fingerprint)
        if self.generation_status not in _ALLOWED_GENERATION_STATUS:
            raise ValueError("invalid generation_status")
        if self.rejection_reason is not None and not self.rejection_reason.strip():
            raise ValueError("rejection_reason must be non-empty when present")
        if self.compilation_status not in _ALLOWED_COMPILATION_STATUS:
            raise ValueError("invalid compilation_status")
        _require_tuple("compilation_diagnostics", self.compilation_diagnostics)
        if not all(isinstance(value, str) for value in self.compilation_diagnostics):
            raise TypeError("compilation_diagnostics must contain strings")
        _require_optional_fingerprint("geometry_fingerprint", self.geometry_fingerprint)
        _require_optional_fingerprint("observation_checksum", self.observation_checksum)
        _require_optional_fingerprint("specification_fingerprint", self.specification_fingerprint)


@dataclass(frozen=True)
class ScenarioManifest:
    manifest_id: str
    manifest_version: str
    campaign_id: str | None
    generation_spec_fingerprint: str
    generator_version: str
    template_ids: tuple[str, ...]
    entries: tuple[ManifestEntry, ...]
    manifest_fingerprint: str

    def __post_init__(self) -> None:
        _require_non_empty("manifest_id", self.manifest_id)
        _require_non_empty("manifest_version", self.manifest_version)
        if self.campaign_id is not None:
            _require_non_empty("campaign_id", self.campaign_id)
        _require_fingerprint("generation_spec_fingerprint", self.generation_spec_fingerprint)
        _require_non_empty("generator_version", self.generator_version)
        _require_tuple("template_ids", self.template_ids)
        if not all(isinstance(value, str) and value.strip() for value in self.template_ids):
            raise ValueError("template_ids must contain non-empty strings")
        _require_tuple("entries", self.entries)
        if not all(isinstance(value, ManifestEntry) for value in self.entries):
            raise TypeError("entries must contain ManifestEntry values")
        _require_fingerprint("manifest_fingerprint", self.manifest_fingerprint)


@dataclass(frozen=True)
class GenerationSummary:
    total_combinations_considered: int
    generated_count: int
    skipped_duplicate_count: int
    rejected_by_rule_count: int
    compiled_success_count: int
    compiled_failed_count: int
    coverage_report: tuple[tuple[str, Any], ...]

    def __post_init__(self) -> None:
        for field_name in (
            "total_combinations_considered",
            "generated_count",
            "skipped_duplicate_count",
            "rejected_by_rule_count",
            "compiled_success_count",
            "compiled_failed_count",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be non-negative")
        _require_pair_tuple("coverage_report", self.coverage_report)
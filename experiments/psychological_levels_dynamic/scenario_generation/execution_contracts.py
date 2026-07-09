"""Immutable contracts for future deterministic batch execution.

Contracts only: no runner calls, no compiler calls, no catalog calls, and no
scenario execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

_ALLOWED_EXECUTION_STATUS = frozenset({"EXECUTED", "FAILED", "SKIPPED"})
_ALLOWED_RUNNER_RESULT = frozenset({"PASS", "FAIL"})


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


def _is_frozen_dataclass(value: Any) -> bool:
    return is_dataclass(value) and bool(getattr(value, "__dataclass_params__").frozen)


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
    if _is_frozen_dataclass(value):
        return {
            field.name: _canonical(getattr(value, field.name))
            for field in fields(value)
        }
    raise TypeError(f"unsupported canonical type: {type(value).__name__}")


def execution_contract_fingerprint(value: Any) -> str:
    """Deterministic canonical JSON + SHA-256 for execution contracts."""

    payload = _canonical(value)
    canonical_json = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return "sha256:" + hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ScenarioExecutionRecord:
    scenario_id: str
    scenario_index: int
    specification_fingerprint: str
    execution_status: str
    scenario_run_result: Any | None
    runner_result: str | None
    summary: tuple[tuple[str, Any], ...]
    diagnostics: tuple[str, ...]
    execution_fingerprint: str

    def __post_init__(self) -> None:
        _require_non_empty("scenario_id", self.scenario_id)
        if not isinstance(self.scenario_index, int) or self.scenario_index < 0:
            raise ValueError("scenario_index must be non-negative")
        _require_fingerprint("specification_fingerprint", self.specification_fingerprint)
        if self.execution_status not in _ALLOWED_EXECUTION_STATUS:
            raise ValueError("invalid execution_status")
        if self.scenario_run_result is not None and not _is_frozen_dataclass(self.scenario_run_result):
            raise TypeError("scenario_run_result must be None or a frozen dataclass payload")
        _require_pair_tuple("summary", self.summary)
        _require_tuple("diagnostics", self.diagnostics)
        if not all(isinstance(value, str) for value in self.diagnostics):
            raise TypeError("diagnostics must contain strings")
        if self.execution_status == "EXECUTED":
            if self.scenario_run_result is None:
                raise ValueError("EXECUTED record requires scenario_run_result")
            if self.runner_result not in _ALLOWED_RUNNER_RESULT:
                raise ValueError("EXECUTED record requires runner_result PASS or FAIL")
            if self.diagnostics:
                raise ValueError("EXECUTED record must not carry diagnostics")
        elif self.execution_status in {"FAILED", "SKIPPED"}:
            if self.scenario_run_result is not None:
                raise ValueError("non-executed record must not carry scenario_run_result")
            if self.runner_result is not None:
                raise ValueError("FAILED/SKIPPED record must not carry runner_result")
            if not self.diagnostics:
                raise ValueError("FAILED/SKIPPED record requires diagnostics")
        _require_fingerprint("execution_fingerprint", self.execution_fingerprint)


@dataclass(frozen=True)
class BatchExecutionResult:
    success: bool
    total_scenarios: int
    executed_scenarios: int
    failed_scenarios: int
    skipped_scenarios: int
    scenario_results: tuple[ScenarioExecutionRecord, ...]
    failed_scenario_ids: tuple[str, ...]
    skipped_scenario_ids: tuple[str, ...]
    diagnostics: tuple[str, ...]
    source_manifest_fingerprint: str | None
    batch_compilation_fingerprint: str | None
    batch_assembly_fingerprint: str | None
    batch_execution_fingerprint: str
    runner_version: str
    batch_execution_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")
        for field_name in (
            "total_scenarios",
            "executed_scenarios",
            "failed_scenarios",
            "skipped_scenarios",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be non-negative")
        if self.executed_scenarios + self.failed_scenarios + self.skipped_scenarios != self.total_scenarios:
            raise ValueError("scenario counts must reconcile to total_scenarios")
        _require_tuple("scenario_results", self.scenario_results)
        if not all(isinstance(value, ScenarioExecutionRecord) for value in self.scenario_results):
            raise TypeError("scenario_results must contain ScenarioExecutionRecord values")
        if len(self.scenario_results) != self.total_scenarios:
            raise ValueError("scenario_results must match total_scenarios")
        expected_indices = tuple(range(len(self.scenario_results)))
        observed_indices = tuple(record.scenario_index for record in self.scenario_results)
        if observed_indices != expected_indices:
            raise ValueError("scenario_results must be in deterministic scenario_index order")
        _require_tuple("failed_scenario_ids", self.failed_scenario_ids)
        _require_tuple("skipped_scenario_ids", self.skipped_scenario_ids)
        if not all(isinstance(value, str) and value.strip() for value in self.failed_scenario_ids):
            raise ValueError("failed_scenario_ids must contain non-empty strings")
        if not all(isinstance(value, str) and value.strip() for value in self.skipped_scenario_ids):
            raise ValueError("skipped_scenario_ids must contain non-empty strings")
        if len(self.failed_scenario_ids) != self.failed_scenarios:
            raise ValueError("failed_scenario_ids must match failed_scenarios")
        if len(self.skipped_scenario_ids) != self.skipped_scenarios:
            raise ValueError("skipped_scenario_ids must match skipped_scenarios")
        failed_from_records = tuple(
            record.scenario_id
            for record in self.scenario_results
            if record.execution_status == "FAILED"
        )
        skipped_from_records = tuple(
            record.scenario_id
            for record in self.scenario_results
            if record.execution_status == "SKIPPED"
        )
        executed_from_records = sum(1 for record in self.scenario_results if record.execution_status == "EXECUTED")
        if failed_from_records != self.failed_scenario_ids:
            raise ValueError("failed_scenario_ids must match FAILED records")
        if skipped_from_records != self.skipped_scenario_ids:
            raise ValueError("skipped_scenario_ids must match SKIPPED records")
        if executed_from_records != self.executed_scenarios:
            raise ValueError("executed_scenarios must match EXECUTED records")
        _require_tuple("diagnostics", self.diagnostics)
        if not all(isinstance(value, str) for value in self.diagnostics):
            raise TypeError("diagnostics must contain strings")
        if self.success:
            if self.failed_scenarios or self.skipped_scenarios:
                raise ValueError("successful batch cannot have failed or skipped scenarios")
            if any(
                record.execution_status == "EXECUTED" and record.runner_result == "FAIL"
                for record in self.scenario_results
            ):
                raise ValueError("successful batch cannot contain executed FAIL runner results")
            if self.diagnostics:
                raise ValueError("successful batch must not carry diagnostics")
        elif not self.diagnostics:
            raise ValueError("failed batch requires diagnostics")
        _require_optional_fingerprint("source_manifest_fingerprint", self.source_manifest_fingerprint)
        _require_optional_fingerprint("batch_compilation_fingerprint", self.batch_compilation_fingerprint)
        _require_optional_fingerprint("batch_assembly_fingerprint", self.batch_assembly_fingerprint)
        _require_fingerprint("batch_execution_fingerprint", self.batch_execution_fingerprint)
        _require_non_empty("runner_version", self.runner_version)
        _require_non_empty("batch_execution_version", self.batch_execution_version)
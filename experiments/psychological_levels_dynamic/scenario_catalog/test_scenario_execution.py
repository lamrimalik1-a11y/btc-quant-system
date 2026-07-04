"""Project 2 Chapter II Phase 4 catalog scenario execution validation.

Executes each catalog specification independently through the unchanged
Scenario Runner. This is an execution and determinism test only: it performs
no cross-scenario comparison, aggregation, ranking, interpretation, storage,
or new analysis.
"""

from __future__ import annotations

import json
import sys
from dataclasses import fields
from pathlib import Path
from typing import Any


CATALOG_DIR = Path(__file__).resolve().parent
DYNAMIC_DIR = CATALOG_DIR.parent
for path in (CATALOG_DIR, DYNAMIC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from catalog import build_catalog_registry
from scenario_contract import _canonical_value
from scenario_runner import ScenarioRunResult, run_scenario
from specifications import (
    ADVERSARIAL_ESCALATING_PENETRATION_V1,
    BASELINE_TRIANGULAR_REFERENCE_V1,
    REGIME_QUIET_TO_PRESSURE_V1,
    REPEATED_ATTACKS_PARTIAL_RECOVERY_V1,
)


EXECUTION_ORDER = (
    BASELINE_TRIANGULAR_REFERENCE_V1,
    ADVERSARIAL_ESCALATING_PENETRATION_V1,
    REGIME_QUIET_TO_PRESSURE_V1,
    REPEATED_ATTACKS_PARTIAL_RECOVERY_V1,
)
DETERMINISM_RUNS = 3


def _canonical_result(result: ScenarioRunResult) -> str:
    payload = {
        field.name: _canonical_value(getattr(result, field.name))
        for field in fields(result)
    }
    return json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _execute_fresh(spec: Any) -> ScenarioRunResult:
    return run_scenario(build_catalog_registry(), spec)


def _validate_baseline_gate(result: ScenarioRunResult) -> None:
    assert result.result == "PASS"
    assert result.errors == ()
    assert result.observation_count == 3000
    assert result.completed_visits == 159
    assert result.zones_observed == 7

    stage3 = result.stage3_transition_summary
    assert stage3["zones_observed"] == 7
    assert stage3["completed_visits"] == 159
    assert stage3["transitions_generated"] == 145
    assert stage3["counts_consistent"] is True

    stage4 = result.stage4_graph_summary
    assert stage4["zones_observed"] == 7
    assert stage4["completed_visits"] == 159
    assert stage4["transitions_generated"] == 145
    assert stage4["transition_counts"] == {
        "RESEARCH_RECOVERING_TO_RESEARCH_STABLE": 60,
        "RESEARCH_STABLE_TO_RESEARCH_RECOVERING": 61,
        "RESEARCH_STABLE_TO_RESEARCH_STABLE": 24,
    }
    assert stage4["critical_transition_count"] == 0
    assert stage4["absorbing_states"] == []

    stage5 = result.stage5_trajectory_summary
    assert stage5["zones_observed"] == 7
    assert stage5["completed_visits"] == 159
    assert stage5["transitions_generated"] == 145
    assert stage5["trajectory_records_generated"] == 159
    assert stage5["unobserved_states"] == ["RESEARCH_ATTACKER_PRESSURE"]
    assert stage5["attacker_pressure_observed"] is False
    assert stage5["predictions_generated"] is False

    stage6 = result.stage6_hypothesis_summary
    assert stage6["zones_observed"] == 7
    assert stage6["completed_visits"] == 159
    assert stage6["hypotheses_generated"] == 152
    assert stage6["eligible_hypotheses"] == 110
    assert stage6["confirmed_count"] == 103
    assert stage6["invalidated_count"] == 0
    assert stage6["pending_count"] == 7
    assert stage6["forced_hypothesis_under_weak_evidence"] is False
    assert stage6["predictions_generated"] is False


def _validate_deterministic_execution(spec: Any) -> tuple[ScenarioRunResult, str]:
    results = tuple(_execute_fresh(spec) for _ in range(DETERMINISM_RUNS))
    first = results[0]
    canonical_reports = tuple(_canonical_result(result) for result in results)

    assert all(result == first for result in results[1:])
    assert all(
        result.observation_checksum == first.observation_checksum
        for result in results[1:]
    )
    assert all(result.run_id == first.run_id for result in results[1:])
    assert all(report == canonical_reports[0] for report in canonical_reports[1:])
    return first, canonical_reports[0]


def _selected_summary(summary: Any, keys: tuple[str, ...]) -> Any:
    if not isinstance(summary, dict):
        return summary
    return {key: summary[key] for key in keys if key in summary}


def _execution_report(
    result: ScenarioRunResult,
    canonical_report: str,
) -> dict[str, Any]:
    return {
        "scenario_id": result.scenario_id,
        "scenario_family": result.scenario_family,
        "observation_count": result.observation_count,
        "completed_visits": result.completed_visits,
        "zones_observed": result.zones_observed,
        "stage3_summary": _selected_summary(
            result.stage3_transition_summary,
            (
                "completed_visits",
                "zones_observed",
                "transitions_generated",
                "unique_transition_types",
                "most_common_transitions",
            ),
        ),
        "stage4_summary": _selected_summary(
            result.stage4_graph_summary,
            (
                "completed_visits",
                "zones_observed",
                "transitions_generated",
                "unique_states",
                "transition_counts",
                "critical_transition_count",
                "absorbing_states",
                "early_warning_paths_count",
            ),
        ),
        "stage5_summary": _selected_summary(
            result.stage5_trajectory_summary,
            (
                "completed_visits",
                "zones_observed",
                "transitions_generated",
                "trajectory_records_generated",
                "unobserved_states",
                "attacker_pressure_observed",
                "predictions_generated",
            ),
        ),
        "stage6_summary": _selected_summary(
            result.stage6_hypothesis_summary,
            (
                "completed_visits",
                "zones_observed",
                "hypotheses_generated",
                "eligible_hypotheses",
                "confirmed_count",
                "invalidated_count",
                "pending_count",
                "predictions_generated",
                "per_zone_sample_status",
            ),
        ),
        "determinism": "PASS",
        "observation_checksum": result.observation_checksum,
        "run_id": result.run_id,
        "canonical_report_identical": bool(canonical_report),
        "errors": list(result.errors),
        "result": result.result,
    }


def run() -> dict[str, Any]:
    reports: list[dict[str, Any]] = []
    errors: list[str] = []
    baseline_reproduction = "FAIL"

    try:
        baseline_result, baseline_canonical = _validate_deterministic_execution(
            EXECUTION_ORDER[0]
        )
        _validate_baseline_gate(baseline_result)
        baseline_reproduction = "PASS"
        reports.append(_execution_report(baseline_result, baseline_canonical))
    except Exception as exc:
        errors.append(f"BASELINE_GATE:{type(exc).__name__}:{exc}")
        return {
            "baseline_reproduction": baseline_reproduction,
            "scenarios": reports,
            "deterministic": False,
            "errors": errors,
            "result": "FAIL",
        }

    for spec in EXECUTION_ORDER[1:]:
        try:
            result, canonical = _validate_deterministic_execution(spec)
            reports.append(_execution_report(result, canonical))
        except Exception as exc:
            errors.append(f"{spec.scenario_id}:{type(exc).__name__}:{exc}")

    all_executed = len(reports) == len(EXECUTION_ORDER)
    deterministic = all_executed and all(
        report["determinism"] == "PASS" for report in reports
    )
    executions_passed = all_executed and all(
        report["result"] == "PASS" for report in reports
    )
    result = (
        "PASS"
        if deterministic and executions_passed and not errors
        else "FAIL"
    )
    return {
        "baseline_reproduction": baseline_reproduction,
        "scenarios": reports,
        "deterministic": deterministic,
        "errors": errors,
        "result": result,
    }


def main() -> None:
    report = run()
    print(
        json.dumps(
            _canonical_value(report),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
    )
    print("COMPARISON_PERFORMED = FALSE")
    print("REPORT_PERSISTED = FALSE")
    print("NEW_METRICS_CREATED = FALSE")
    print("PRODUCTION_EFFECTS = FALSE")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

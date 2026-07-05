"""Project 2 Chapter II Phase 5 descriptive cross-scenario comparison.

Arranges existing ScenarioRunResult fields side by side. It does not compute
scenario differences, averages, ratios, rankings, scores, interpretations,
or conclusions, and it does not persist reports.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
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
SCENARIO_DETERMINISM_RUNS = 3
COMPARISON_DETERMINISM_RUNS = 3
SAMPLE_STATUSES = (
    "NO_VISITS",
    "INSUFFICIENT_SAMPLE",
    "SUFFICIENT_SAMPLE",
)


def _canonical(value: Any) -> str:
    return json.dumps(
        _canonical_value(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _canonical_result(result: ScenarioRunResult) -> str:
    return _canonical(
        {
            field.name: getattr(result, field.name)
            for field in fields(result)
        }
    )


def _execute_fresh(spec: Any) -> ScenarioRunResult:
    return run_scenario(build_catalog_registry(), spec)


def _execute_deterministically(spec: Any) -> ScenarioRunResult:
    results = tuple(
        _execute_fresh(spec) for _ in range(SCENARIO_DETERMINISM_RUNS)
    )
    first = results[0]
    first_payload = _canonical_result(first)
    assert all(result == first for result in results[1:])
    assert all(
        result.run_id == first.run_id
        and result.observation_checksum == first.observation_checksum
        and _canonical_result(result) == first_payload
        for result in results[1:]
    )
    assert first.result == "PASS"
    assert first.errors == ()
    return first


def _validate_baseline_gate(result: ScenarioRunResult) -> None:
    assert result.scenario_id == "BASELINE_TRIANGULAR_REFERENCE_V1"
    assert result.observation_count == 3000
    assert result.zones_observed == 7
    assert result.completed_visits == 159

    stage3 = result.stage3_transition_summary
    assert stage3["transitions_generated"] == 145

    stage4 = result.stage4_graph_summary
    assert stage4["transition_counts"] == {
        "RESEARCH_RECOVERING_TO_RESEARCH_STABLE": 60,
        "RESEARCH_STABLE_TO_RESEARCH_RECOVERING": 61,
        "RESEARCH_STABLE_TO_RESEARCH_STABLE": 24,
    }

    stage5 = result.stage5_trajectory_summary
    assert stage5["trajectory_records_generated"] == 159

    stage6 = result.stage6_hypothesis_summary
    assert stage6["hypotheses_generated"] == 152
    assert stage6["eligible_hypotheses"] == 110
    assert stage6["confirmed_count"] == 103
    assert stage6["invalidated_count"] == 0
    assert stage6["pending_count"] == 7


def _sample_status_counts(stage6: dict[str, Any]) -> dict[str, int]:
    counts = Counter(stage6["per_zone_sample_status"].values())
    return {status: counts.get(status, 0) for status in SAMPLE_STATUSES}


def _warnings(result: ScenarioRunResult) -> list[str]:
    stage5 = result.stage5_trajectory_summary
    stage6 = result.stage6_hypothesis_summary
    statuses = tuple(stage6["per_zone_sample_status"].values())
    warnings = [
        "ONE_SPECIFICATION_PER_FAMILY",
        "UNEQUAL_VISIT_OPPORTUNITIES",
        "SERIAL_DEPENDENCE",
        "NO_FAMILY_LEVEL_INFERENCE",
    ]
    if "NO_VISITS" in statuses:
        warnings.append("NO_VISITS_PRESENT")
    if (
        result.completed_visits
        and "SUFFICIENT_SAMPLE" not in statuses
    ):
        warnings.append("LOW_COMPLETED_VISITS")
    if stage5["unobserved_states"]:
        warnings.append("MISSING_STATES_PRESENT")
    return warnings


def _scenario_report(result: ScenarioRunResult) -> dict[str, Any]:
    stage4 = result.stage4_graph_summary
    stage5 = result.stage5_trajectory_summary
    stage6 = result.stage6_hypothesis_summary
    return {
        "warnings": _warnings(result),
        "execution_summary": {
            "scenario": result.scenario_id,
            "family": result.scenario_family,
            "result": result.result,
            "determinism": "PASS",
            "errors": list(result.errors),
        },
        "provenance": {
            "scenario_id": result.scenario_id,
            "scenario_family": result.scenario_family,
            "specification_fingerprint": result.specification_fingerprint,
            "run_id": result.run_id,
            "observation_checksum": result.observation_checksum,
            "chain_version": result.chain_version,
            "chain_fingerprint": result.chain_fingerprint,
        },
        "exposure": {
            "rows": result.observation_count,
            "zones": result.zones_observed,
            "completed_visits": result.completed_visits,
            "transitions": stage4["transitions_generated"],
            "trajectory_records": stage5["trajectory_records_generated"],
            "hypotheses_generated": stage6["hypotheses_generated"],
            "eligible_hypotheses": stage6["eligible_hypotheses"],
        },
        "per_zone_sample_status": {
            "counts": _sample_status_counts(stage6),
            "zones": stage6["per_zone_sample_status"],
        },
        "state_presence": {
            "observed_states": stage4["unique_states"],
            "unobserved_states": stage5["unobserved_states"],
            "attacker_pressure_observed": stage5[
                "attacker_pressure_observed"
            ],
        },
        "transitions": stage4,
        "trajectory": stage5,
        "hypothesis_status": {
            "generated": stage6["hypotheses_generated"],
            "eligible": stage6["eligible_hypotheses"],
            "confirmed": stage6["confirmed_count"],
            "invalidated": stage6["invalidated_count"],
            "pending": stage6["pending_count"],
            "insufficient_sample": stage6["insufficient_sample_count"],
            "insufficient_evidence": stage6[
                "insufficient_evidence_count"
            ],
            "abstentions": stage6["abstention_count"],
        },
    }


def _build_comparison_report() -> dict[str, Any]:
    baseline = _execute_deterministically(EXECUTION_ORDER[0])
    _validate_baseline_gate(baseline)

    reports = [_scenario_report(baseline)]
    for spec in EXECUTION_ORDER[1:]:
        reports.append(_scenario_report(_execute_deterministically(spec)))

    return {
        "checkpoint": "PHASE1C_CROSS_SCENARIO_COMPARISON_STABLE",
        "baseline_gate": "PASS",
        "scenario_order": [spec.scenario_id for spec in EXECUTION_ORDER],
        "scenarios": reports,
        "comparison_performed": "DESCRIPTIVE_SIDE_BY_SIDE_ONLY",
        "family_level_inference": "NOT_AVAILABLE_SINGLE_SPECIFICATION",
        "rankings_created": False,
        "scores_created": False,
        "interpretations_created": False,
        "reports_persisted": False,
        "result": "PASS",
    }


def run() -> dict[str, Any]:
    reports = tuple(
        _build_comparison_report()
        for _ in range(COMPARISON_DETERMINISM_RUNS)
    )
    first = reports[0]
    deterministic = all(
        _canonical(report) == _canonical(first) for report in reports[1:]
    )
    assert deterministic
    result = dict(first)
    result["deterministic_across_runs"] = True
    return result


def main() -> None:
    report = run()
    print(json.dumps(_canonical_value(report), indent=2))
    print("CROSS_SCENARIO_ARITHMETIC = FALSE")
    print("RANKING = FALSE")
    print("SCORING = FALSE")
    print("INTERPRETATION = FALSE")
    print("PERSISTENCE = FALSE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

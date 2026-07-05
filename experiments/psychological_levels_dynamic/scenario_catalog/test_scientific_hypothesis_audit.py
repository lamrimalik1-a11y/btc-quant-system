"""Project 2 Chapter II Phase 6 scientific hypothesis audit.

Evaluates only the ex-ante expectations already stored in the Phase 3
ScenarioSpecifications. Phase 5 is the sole observation source. This module
does not call the Scenario Runner, recompute Stage outputs, create hypotheses,
or modify any scenario, threshold, or analytical component.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CATALOG_DIR = Path(__file__).resolve().parent
DYNAMIC_DIR = CATALOG_DIR.parent
for path in (CATALOG_DIR, DYNAMIC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from scenario_contract import ScenarioSpecification, _canonical_value
from specifications import ALL_SPECIFICATIONS
import test_cross_scenario_comparison as phase5


CHECKPOINT = "PHASE1C_SCIENTIFIC_HYPOTHESIS_AUDIT_STABLE"
HYPOTHESIS_VERSION = "1"
REPORT_SCHEMA_VERSION = "1"
REGISTRATION_EX_ANTE = "EX_ANTE"
ALLOWED_REGISTRATION_STATUSES = {"EX_ANTE", "POST_HOC"}
ALLOWED_DECISIONS = {
    "OBSERVED_CONSISTENT_WITH_HYPOTHESIS",
    "NOT_OBSERVED_IN_CURRENT_CATALOG",
    "INSUFFICIENT_EVIDENCE",
    "PARTIALLY_CONSISTENT",
    "INCONCLUSIVE",
    "NOT_TESTED",
}
DECISION_OBSERVED_CONSISTENT = "OBSERVED_CONSISTENT_WITH_HYPOTHESIS"
DECISION_NOT_OBSERVED = "NOT_OBSERVED_IN_CURRENT_CATALOG"
DECISION_INSUFFICIENT = "INSUFFICIENT_EVIDENCE"
DECISION_PARTIAL = "PARTIALLY_CONSISTENT"
DECISION_INCONCLUSIVE = "INCONCLUSIVE"
DECISION_NOT_TESTED = "NOT_TESTED"
BANNED_PATTERNS = (
    r"\bproven\b",
    r"\bvalidated\b",
    r"\btrue\b",
    r"\bfalsified\b",
    r"\balways\b",
    r"\bnever\b",
    r"\bgenerally\b",
    r"\btypically\b",
    r"\bmarket truth\b",
    r"\bproduction ready\b",
    r"\btrading accuracy\b",
    r"\bbetter\b",
    r"\bworse\b",
    r"\bwinner\b",
    r"\bscore\b",
    r"\brank\b",
    r"\bedge\b",
    r"\bsignal\b",
    r"\bbuy\b",
    r"\bsell\b",
    r"\bentry\b",
    r"\bexit\b",
    r"\bgeneralize\b",
    r"\bgeneralization\b",
    r"\bsuggests\b",
    r"\bconfirms\b",
    r"\bproves\b",
    r"\bstronger\b",
    r"\bweaker\b",
    r"\bimproved\b",
    r"\bdegraded\b",
    r"\beffect\b",
    r"\bimpact\b",
    r"\blift\b",
    r"\bgain\b",
    r"\baccuracy\b",
    r"\bperformance\b",
)
GLOBAL_LIMITATIONS = (
    "Synthetic scenarios only.",
    "Four specifications only.",
    "One specification per family.",
    "Pressure-heavy catalog.",
    "Unequal visit opportunities.",
    "Unequal zone coverage.",
    "Serial dependence.",
    "No real-market evaluation.",
    "No production readiness assessment.",
    "No trading applicability assessment.",
    "No family-level inference.",
    "No statistical significance assessment.",
    "No learning or tuning.",
)


@dataclass(frozen=True)
class ResearchHypothesis:
    hypothesis_id: str
    hypothesis_version: str
    registration_status: str
    source_scenario_id: str
    source_scenario_family: str
    source_specification_fingerprint: str
    hypothesis_statement: str
    mechanism_under_test: str
    expected_observation: tuple[str, ...]
    required_evidence: tuple[str, ...]


@dataclass(frozen=True)
class HypothesisEvaluation:
    hypothesis_id: str
    observed_evidence: tuple[tuple[str, Any], ...]
    contradictory_evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    decision: str
    decision_rule_id: str
    decision_rule_trace: tuple[str, ...]
    decision_scope: str
    limitations_applicable: tuple[str, ...]
    source_run_id: str
    observation_checksum: str
    chain_version: str
    chain_fingerprint: str


def _canonical(value: Any) -> str:
    return json.dumps(
        _canonical_value(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _mechanism(spec: ScenarioSpecification) -> str:
    metadata = spec.validation_metadata
    return str(
        metadata.get(
            "mechanism_under_test",
            metadata.get("mechanism", "NOT_AVAILABLE"),
        )
    )


def _hypothesis_from_spec(
    spec: ScenarioSpecification,
) -> ResearchHypothesis:
    return ResearchHypothesis(
        hypothesis_id=f"PHASE3::{spec.scenario_id}",
        hypothesis_version=HYPOTHESIS_VERSION,
        registration_status=REGISTRATION_EX_ANTE,
        source_scenario_id=spec.scenario_id,
        source_scenario_family=spec.scenario_family,
        source_specification_fingerprint=spec.specification_fingerprint,
        hypothesis_statement=spec.description,
        mechanism_under_test=_mechanism(spec),
        expected_observation=spec.expected_behavior_notes,
        required_evidence=(
            "MATCHING_PHASE5_SCENARIO_REPORT",
            "MATCHING_SPECIFICATION_FINGERPRINT",
            "MATCHING_RUN_PROVENANCE",
        ),
    )


def _hypothesis_payload(hypothesis: ResearchHypothesis) -> dict[str, Any]:
    return {
        "hypothesis_id": hypothesis.hypothesis_id,
        "hypothesis_version": hypothesis.hypothesis_version,
        "registration_status": hypothesis.registration_status,
        "source_scenario_id": hypothesis.source_scenario_id,
        "source_scenario_family": hypothesis.source_scenario_family,
        "source_specification_fingerprint": (
            hypothesis.source_specification_fingerprint
        ),
        "hypothesis_statement": hypothesis.hypothesis_statement,
        "mechanism_under_test": hypothesis.mechanism_under_test,
        "expected_observation": hypothesis.expected_observation,
        "required_evidence": hypothesis.required_evidence,
    }


def _evaluation_payload(
    evaluation: HypothesisEvaluation,
) -> dict[str, Any]:
    return {
        "hypothesis_id": evaluation.hypothesis_id,
        "observed_evidence": dict(evaluation.observed_evidence),
        "contradictory_evidence": evaluation.contradictory_evidence,
        "missing_evidence": evaluation.missing_evidence,
        "decision": evaluation.decision,
        "decision_rule_id": evaluation.decision_rule_id,
        "decision_rule_trace": evaluation.decision_rule_trace,
        "decision_scope": evaluation.decision_scope,
        "limitations_applicable": evaluation.limitations_applicable,
        "source_run_id": evaluation.source_run_id,
        "observation_checksum": evaluation.observation_checksum,
        "chain_version": evaluation.chain_version,
        "chain_fingerprint": evaluation.chain_fingerprint,
    }


def _provenance(report: dict[str, Any]) -> dict[str, Any]:
    return report["provenance"]


def _baseline_decision_rule(
    exposure: dict[str, Any],
    status: dict[str, Any],
    attacker_pressure_observed: bool,
) -> tuple[str, str, tuple[str, ...]]:
    expected_reference = (
        exposure["completed_visits"] == 159
        and exposure["transitions"] == 145
        and status["generated"] == 152
        and status["eligible"] == 110
        and status["confirmed"] == 103
        and status["invalidated"] == 0
        and status["pending"] == 7
        and attacker_pressure_observed is False
    )
    if exposure["completed_visits"] == 0:
        decision = DECISION_NOT_TESTED
    elif expected_reference:
        decision = DECISION_OBSERVED_CONSISTENT
    else:
        decision = DECISION_INCONCLUSIVE
    trace = (
        f"completed_visits={exposure['completed_visits']}",
        f"transitions={exposure['transitions']}",
        f"hypotheses_generated={status['generated']}",
        f"eligible_hypotheses={status['eligible']}",
        f"confirmed_hypotheses={status['confirmed']}",
        f"invalidated_hypotheses={status['invalidated']}",
        f"pending_hypotheses={status['pending']}",
        f"attacker_pressure_observed={attacker_pressure_observed}",
        f"expected_reference_match={expected_reference}",
    )
    return decision, "PHASE6_BASELINE_REFERENCE_RULE_V1", trace


def _adversarial_decision_rule(
    completed_visits: int,
    attacker_pressure_observed: bool,
    eligible_hypotheses: int,
) -> tuple[str, str, tuple[str, ...]]:
    if completed_visits == 0:
        decision = DECISION_NOT_TESTED
    elif attacker_pressure_observed and eligible_hypotheses == 0:
        decision = DECISION_PARTIAL
    elif attacker_pressure_observed and eligible_hypotheses > 0:
        decision = DECISION_OBSERVED_CONSISTENT
    elif eligible_hypotheses == 0:
        decision = DECISION_INSUFFICIENT
    else:
        decision = DECISION_NOT_OBSERVED
    trace = (
        f"completed_visits={completed_visits}",
        f"attacker_pressure_observed={attacker_pressure_observed}",
        f"eligible_hypotheses={eligible_hypotheses}",
    )
    return decision, "PHASE6_ADVERSARIAL_PRESSURE_RULE_V1", trace


def _regime_decision_rule(
    completed_visits: int,
    invalidated_hypotheses: int,
    eligible_hypotheses: int,
) -> tuple[str, str, tuple[str, ...]]:
    if completed_visits == 0:
        decision = DECISION_NOT_TESTED
    elif invalidated_hypotheses > 0 and eligible_hypotheses > 0:
        decision = DECISION_OBSERVED_CONSISTENT
    elif eligible_hypotheses == 0:
        decision = DECISION_INSUFFICIENT
    elif invalidated_hypotheses == 0:
        decision = DECISION_NOT_OBSERVED
    else:
        decision = DECISION_INCONCLUSIVE
    trace = (
        f"completed_visits={completed_visits}",
        f"invalidated_hypotheses={invalidated_hypotheses}",
        f"eligible_hypotheses={eligible_hypotheses}",
    )
    return decision, "PHASE6_REGIME_INVALIDATION_RULE_V1", trace


def _repeated_decision_rule(
    completed_visits: int,
    health_at_visit: dict[str, Any],
    omega_at_visit: dict[str, Any],
    attacker_pressure_observed: bool,
) -> tuple[str, str, tuple[str, ...]]:
    health_sample_count = int(health_at_visit["sample_count"])
    health_total_change = health_at_visit["total_change"]
    omega_total_change = omega_at_visit["total_change"]
    denominator_evidence = (
        health_sample_count > 0
        and health_total_change < 0
        and omega_total_change == 0
    )
    if completed_visits == 0:
        decision = DECISION_NOT_TESTED
    elif health_sample_count == 0:
        decision = DECISION_INSUFFICIENT
    elif denominator_evidence and attacker_pressure_observed is False:
        decision = DECISION_OBSERVED_CONSISTENT
    elif health_total_change >= 0:
        decision = DECISION_NOT_OBSERVED
    else:
        decision = DECISION_INCONCLUSIVE
    trace = (
        f"completed_visits={completed_visits}",
        f"health_sample_count={health_sample_count}",
        f"health_total_change={health_total_change}",
        f"omega_total_change={omega_total_change}",
        f"attacker_pressure_observed={attacker_pressure_observed}",
        f"denominator_evidence_present={denominator_evidence}",
    )
    return decision, "PHASE6_REPEATED_DENOMINATOR_RULE_V1", trace


def _baseline_evaluation(
    hypothesis: ResearchHypothesis, report: dict[str, Any]
) -> HypothesisEvaluation:
    exposure = report["exposure"]
    status = report["hypothesis_status"]
    attacker_pressure_observed = report["state_presence"][
        "attacker_pressure_observed"
    ]
    decision, rule_id, rule_trace = _baseline_decision_rule(
        exposure, status, attacker_pressure_observed
    )
    return HypothesisEvaluation(
        hypothesis_id=hypothesis.hypothesis_id,
        observed_evidence=(
            ("zones_observed", exposure["zones"]),
            ("completed_visits", exposure["completed_visits"]),
            ("transitions", exposure["transitions"]),
            ("hypotheses_generated", status["generated"]),
            ("eligible_hypotheses", status["eligible"]),
            ("confirmed_hypotheses", status["confirmed"]),
            ("invalidated_hypotheses", status["invalidated"]),
            ("pending_hypotheses", status["pending"]),
            (
                "attacker_pressure_observed",
                attacker_pressure_observed,
            ),
        ),
        contradictory_evidence=(),
        missing_evidence=(),
        decision=decision,
        decision_rule_id=rule_id,
        decision_rule_trace=rule_trace,
        decision_scope="BASELINE_TRIANGULAR_REFERENCE_V1_ONLY",
        limitations_applicable=(
            "REFERENCE_CONTROL_ONLY",
            "SYNTHETIC_PATH",
            "REFERENCE_SCOPE_ONLY",
        ),
        **_evaluation_provenance(report),
    )


def _adversarial_evaluation(
    hypothesis: ResearchHypothesis, report: dict[str, Any]
) -> HypothesisEvaluation:
    exposure = report["exposure"]
    status = report["hypothesis_status"]
    attacker_pressure_observed = report["state_presence"][
        "attacker_pressure_observed"
    ]
    decision, rule_id, rule_trace = _adversarial_decision_rule(
        exposure["completed_visits"],
        attacker_pressure_observed,
        status["eligible"],
    )
    missing_evidence = (
        ("ELIGIBLE_STAGE6_HYPOTHESIS",)
        if status["eligible"] == 0
        else ()
    )
    return HypothesisEvaluation(
        hypothesis_id=hypothesis.hypothesis_id,
        observed_evidence=(
            ("zones_observed", exposure["zones"]),
            ("completed_visits", exposure["completed_visits"]),
            (
                "attacker_pressure_observed",
                attacker_pressure_observed,
            ),
            ("stage6_eligible_hypotheses", status["eligible"]),
            (
                "per_zone_sample_status_counts",
                report["per_zone_sample_status"]["counts"],
            ),
        ),
        contradictory_evidence=(),
        missing_evidence=missing_evidence,
        decision=decision,
        decision_rule_id=rule_id,
        decision_rule_trace=rule_trace,
        decision_scope="ADVERSARIAL_ESCALATING_PENETRATION_V1_ONLY",
        limitations_applicable=(
            "TWO_COMPLETED_VISITS",
            "ZERO_ELIGIBLE_STAGE6_HYPOTHESES",
            "SIX_ZONES_WITH_NO_VISITS",
            "SYNTHETIC_PATH",
        ),
        **_evaluation_provenance(report),
    )


def _regime_evaluation(
    hypothesis: ResearchHypothesis, report: dict[str, Any]
) -> HypothesisEvaluation:
    exposure = report["exposure"]
    status = report["hypothesis_status"]
    attacker_pressure_observed = report["state_presence"][
        "attacker_pressure_observed"
    ]
    decision, rule_id, rule_trace = _regime_decision_rule(
        exposure["completed_visits"],
        status["invalidated"],
        status["eligible"],
    )
    return HypothesisEvaluation(
        hypothesis_id=hypothesis.hypothesis_id,
        observed_evidence=(
            ("zones_observed", exposure["zones"]),
            ("completed_visits", exposure["completed_visits"]),
            (
                "attacker_pressure_observed",
                attacker_pressure_observed,
            ),
            ("transitions", exposure["transitions"]),
            ("eligible_hypotheses", status["eligible"]),
            ("confirmed_hypotheses", status["confirmed"]),
            ("invalidated_hypotheses", status["invalidated"]),
            ("pending_hypotheses", status["pending"]),
            (
                "transition_counts",
                report["transitions"]["transition_counts"],
            ),
        ),
        contradictory_evidence=(),
        missing_evidence=(),
        decision=decision,
        decision_rule_id=rule_id,
        decision_rule_trace=rule_trace,
        decision_scope="REGIME_QUIET_TO_PRESSURE_V1_ONLY",
        limitations_applicable=(
            "ONE_INVALIDATED_HYPOTHESIS",
            "ONE_SPECIFICATION",
            "SIX_ZONES_WITH_NO_VISITS",
            "SYNTHETIC_PATH",
        ),
        **_evaluation_provenance(report),
    )


def _repeated_evaluation(
    hypothesis: ResearchHypothesis, report: dict[str, Any]
) -> HypothesisEvaluation:
    exposure = report["exposure"]
    stable_mechanics = report["trajectory"][
        "mechanical_evolution_by_state"
    ]["RESEARCH_STABLE"]["mechanics"]
    health_at_visit = stable_mechanics["health_at_visit"]
    omega_at_visit = stable_mechanics["omega_at_visit"]
    attacker_pressure_observed = report["state_presence"][
        "attacker_pressure_observed"
    ]
    decision, rule_id, rule_trace = _repeated_decision_rule(
        exposure["completed_visits"],
        health_at_visit,
        omega_at_visit,
        attacker_pressure_observed,
    )
    return HypothesisEvaluation(
        hypothesis_id=hypothesis.hypothesis_id,
        observed_evidence=(
            ("zones_observed", exposure["zones"]),
            ("completed_visits", exposure["completed_visits"]),
            (
                "health_at_visit",
                health_at_visit,
            ),
            (
                "omega_at_visit",
                omega_at_visit,
            ),
            (
                "attacker_pressure_observed",
                attacker_pressure_observed,
            ),
            (
                "per_zone_sample_status_counts",
                report["per_zone_sample_status"]["counts"],
            ),
        ),
        contradictory_evidence=(),
        missing_evidence=(),
        decision=decision,
        decision_rule_id=rule_id,
        decision_rule_trace=rule_trace,
        decision_scope="REPEATED_ATTACKS_PARTIAL_RECOVERY_V1_ONLY",
        limitations_applicable=(
            "SIX_COMPLETED_VISITS",
            "FIRST_VISIT_STATE_NOT_AVAILABLE",
            "ONE_SPECIFICATION",
            "SIX_ZONES_WITH_NO_VISITS",
            "SYNTHETIC_PATH",
        ),
        **_evaluation_provenance(report),
    )


def _evaluation_provenance(report: dict[str, Any]) -> dict[str, str]:
    provenance = _provenance(report)
    return {
        "source_run_id": provenance["run_id"],
        "observation_checksum": provenance["observation_checksum"],
        "chain_version": provenance["chain_version"],
        "chain_fingerprint": provenance["chain_fingerprint"],
    }


EVALUATORS = {
    "BASELINE_TRIANGULAR_REFERENCE_V1": _baseline_evaluation,
    "ADVERSARIAL_ESCALATING_PENETRATION_V1": (
        _adversarial_evaluation
    ),
    "REGIME_QUIET_TO_PRESSURE_V1": _regime_evaluation,
    "REPEATED_ATTACKS_PARTIAL_RECOVERY_V1": _repeated_evaluation,
}


def _authored_interpretation_prose(report: dict[str, Any]) -> tuple[str, ...]:
    prose: list[str] = []
    for evaluation in report["hypothesis_evaluations"]:
        prose.extend(evaluation["contradictory_evidence"])
        prose.extend(evaluation["missing_evidence"])
        prose.append(evaluation["decision_scope"])
        prose.extend(evaluation["limitations_applicable"])
    prose.extend(report["null_and_negative_results"])
    prose.extend(report["unresolved_questions"])
    prose.extend(report["future_research_directions"])
    return tuple(str(item) for item in prose)


def _banned_language_scan(report: dict[str, Any]) -> dict[str, Any]:
    violations: list[dict[str, str]] = []
    for text in _authored_interpretation_prose(report):
        for pattern in BANNED_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                violations.append({"pattern": pattern, "text": text})
    return {
        "scope": "PHASE6_AUTHORED_INTERPRETATION_PROSE_ONLY",
        "violations": violations,
        "passed": not violations,
    }


def _source_integrity(
    phase5_report: dict[str, Any],
    hypotheses: tuple[ResearchHypothesis, ...],
) -> dict[str, Any]:
    specs_by_id = {spec.scenario_id: spec for spec in ALL_SPECIFICATIONS}
    phase5_by_id = {
        report["provenance"]["scenario_id"]: report
        for report in phase5_report["scenarios"]
    }
    traceability = []
    for hypothesis in hypotheses:
        spec = specs_by_id[hypothesis.source_scenario_id]
        source_report = phase5_by_id[hypothesis.source_scenario_id]
        exact_source_match = (
            hypothesis.hypothesis_statement == spec.description
            and hypothesis.expected_observation
            == spec.expected_behavior_notes
            and hypothesis.source_specification_fingerprint
            == spec.specification_fingerprint
            and source_report["provenance"]["specification_fingerprint"]
            == spec.specification_fingerprint
        )
        traceability.append(
            {
                "hypothesis_id": hypothesis.hypothesis_id,
                "source_scenario_id": hypothesis.source_scenario_id,
                "exact_phase3_source_match": exact_source_match,
            }
        )

    expected_ids = tuple(spec.scenario_id for spec in ALL_SPECIFICATIONS)
    hypothesis_ids = tuple(
        hypothesis.source_scenario_id for hypothesis in hypotheses
    )
    return {
        "phase5_checkpoint": phase5_report["checkpoint"],
        "phase5_result": phase5_report["result"],
        "phase5_deterministic": phase5_report[
            "deterministic_across_runs"
        ],
        "hypothesis_count": len(hypotheses),
        "all_registration_statuses_allowed": all(
            hypothesis.registration_status
            in ALLOWED_REGISTRATION_STATUSES
            for hypothesis in hypotheses
        ),
        "all_hypotheses_ex_ante": all(
            hypothesis.registration_status == REGISTRATION_EX_ANTE
            for hypothesis in hypotheses
        ),
        "no_hypotheses_outside_phase3": hypothesis_ids == expected_ids,
        "phase3_traceability": traceability,
        "all_phase3_sources_exact": all(
            item["exact_phase3_source_match"] for item in traceability
        ),
    }


def _build_audit(phase5_report: dict[str, Any]) -> dict[str, Any]:
    hypotheses = tuple(
        _hypothesis_from_spec(spec) for spec in ALL_SPECIFICATIONS
    )
    reports_by_id = {
        report["provenance"]["scenario_id"]: report
        for report in phase5_report["scenarios"]
    }
    evaluations = tuple(
        EVALUATORS[hypothesis.source_scenario_id](
            hypothesis,
            reports_by_id[hypothesis.source_scenario_id],
        )
        for hypothesis in hypotheses
    )
    assert all(
        evaluation.decision in ALLOWED_DECISIONS
        and evaluation.decision_scope
        for evaluation in evaluations
    )

    report = {
        "checkpoint": CHECKPOINT,
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "research_boundary": (
            "RESEARCH_ONLY",
            "OFFLINE_ONLY",
            "SYNTHETIC_SCENARIO_SCOPE",
            "NO_PRODUCTION_ASSESSMENT",
            "NO_TRADING_ASSESSMENT",
            "NO_LEARNING",
            "NO_TUNING",
        ),
        "global_limitations": GLOBAL_LIMITATIONS,
        "source_integrity": _source_integrity(
            phase5_report, hypotheses
        ),
        "hypothesis_registry": tuple(
            _hypothesis_payload(hypothesis)
            for hypothesis in hypotheses
        ),
        "hypothesis_evaluations": tuple(
            _evaluation_payload(evaluation)
            for evaluation in evaluations
        ),
        "null_and_negative_results": (
            "Baseline reference has no RESEARCH_ATTACKER_PRESSURE observation.",
            "Adversarial Stage 6 eligible hypothesis count is zero.",
            (
                "Repeated-attacks RESEARCH_ATTACKER_PRESSURE observation is "
                "absent; its registered mechanism does not require that state."
            ),
        ),
        "unresolved_questions": (
            (
                "Whether these observations recur under additional "
                "preregistered specifications."
            ),
            (
                "Whether the synthetic observations recur in an independently "
                "defined research corpus."
            ),
        ),
        "future_research_directions": (
            "Preregister additional specifications before execution.",
            (
                "Add mechanism-matched controls without changing the current "
                "scenario specifications."
            ),
            "Retain null observations and insufficient evidence explicitly.",
        ),
        "provenance_appendix": tuple(
            report["provenance"]
            for report in phase5_report["scenarios"]
        ),
        "reports_persisted": False,
        "result": "PASS",
    }
    language_scan = _banned_language_scan(report)
    report["source_integrity"]["banned_language_scan"] = language_scan
    assert language_scan["passed"]
    assert report["source_integrity"]["all_phase3_sources_exact"]
    assert report["source_integrity"]["no_hypotheses_outside_phase3"]
    assert report["source_integrity"]["all_hypotheses_ex_ante"]
    return report


def run() -> dict[str, Any]:
    phase5_report = phase5.run()
    assert phase5_report["result"] == "PASS"
    assert phase5_report["deterministic_across_runs"]

    audits = tuple(_build_audit(phase5_report) for _ in range(3))
    first_payload = _canonical(audits[0])
    deterministic = all(
        _canonical(audit) == first_payload for audit in audits[1:]
    )
    assert deterministic
    report = dict(audits[0])
    report["deterministic_across_runs"] = True
    return report


def main() -> None:
    report = run()
    print(json.dumps(_canonical_value(report), indent=2))
    print("HYPOTHESES_INVENTED = FALSE")
    print("POST_HOC_HYPOTHESES_USED = FALSE")
    print("SCENARIOS_RERUN_DIRECTLY_BY_PHASE6 = FALSE")
    print("REPORTS_PERSISTED = FALSE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

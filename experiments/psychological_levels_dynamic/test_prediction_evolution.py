"""Phase 1B Stage 6 -- offline Project 2 hypothesis evolution research.

Generates descriptive next-state hypotheses from Stage 5 prefix records and
validates them later against the next completed visit. Generation and
validation are separate by function boundary. This is not production B10/B11,
market forecasting, trading, signals, or execution.
"""

from __future__ import annotations

import copy
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DYNAMIC_DIR = Path(__file__).resolve().parent
for path in (REPO_ROOT, DYNAMIC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from test_dynamic_state_transitions import collect_completed_visits
from test_trajectory_evolution import (
    MIN_TRANSITION_SAMPLES,
    NOT_AVAILABLE,
    build_trajectory_records,
)


EXPECTED_COMPLETED_VISITS = 159
MIN_DOMINANT_MARGIN = 0.15
MIN_HYPOTHESIS_CONFIDENCE = 0.35
RESEARCH_UNCERTAIN = "RESEARCH_UNCERTAIN"
HYPOTHESIS_CREATED = "RESEARCH_HYPOTHESIS_CREATED"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
POSSIBLE_RESEARCH_STATES = {
    "RESEARCH_ATTACKER_PRESSURE",
    "RESEARCH_RECOVERING",
    "RESEARCH_STABLE",
}
VALIDATION_FIELDS = {
    "validation_visit_index",
    "observed_next_research_state",
    "hypothesis_status",
}
GRADED_STATUSES = {"RESEARCH_CONFIRMED", "RESEARCH_INVALIDATED"}
ELIGIBLE_STATUSES = {*GRADED_STATUSES, "RESEARCH_PENDING"}


def _base_hypothesis(current_record: dict[str, Any]) -> dict[str, Any]:
    return {
        "global_zone_key": current_record["global_zone_key"],
        "visit_index": current_record["visit_index"],
        "hypothesis_created_at_visit": current_record["visit_index"],
        "input_research_state": current_record["current_research_state"],
        "expected_next_research_state": NOT_AVAILABLE,
        "trajectory_continuation_hypothesis": NOT_AVAILABLE,
        "supporting_transition_count": NOT_AVAILABLE,
        "eligible_transition_count": NOT_AVAILABLE,
        "descriptive_probability": NOT_AVAILABLE,
        "dominant_margin": NOT_AVAILABLE,
        "hypothesis_confidence": NOT_AVAILABLE,
        "generation_status": NOT_AVAILABLE,
    }


def _historical_destinations(
    prefix_records: list[dict[str, Any]], current_state: str
) -> list[str]:
    destinations: list[str] = []
    for source_record, destination_record in zip(
        prefix_records, prefix_records[1:]
    ):
        source = source_record["current_research_state"]
        destination = destination_record["current_research_state"]
        if source == NOT_AVAILABLE or destination == NOT_AVAILABLE:
            continue
        if source == current_state:
            destinations.append(destination)
    return destinations


def _confidence(
    destinations: list[str],
    top_destination: str,
    top_count: int,
    second_count: int,
) -> tuple[float, float, float]:
    eligible = len(destinations)
    probability = top_count / eligible
    margin = (top_count - second_count) / eligible
    recent = destinations[eligible // 2 :]
    recency_consistency = (
        sum(destination == top_destination for destination in recent)
        / len(recent)
    )
    sample_component = min(
        eligible / (MIN_TRANSITION_SAMPLES * 2), 1.0
    )
    confidence = min(
        sample_component,
        probability,
        margin,
        recency_consistency,
    )
    return probability, margin, confidence


def _abstain(
    hypothesis: dict[str, Any],
    status: str,
    eligible_count: int,
) -> dict[str, Any]:
    hypothesis["eligible_transition_count"] = eligible_count
    hypothesis["trajectory_continuation_hypothesis"] = RESEARCH_UNCERTAIN
    hypothesis["generation_status"] = status
    return hypothesis


def generate_hypothesis(
    prefix_only_records: list[dict[str, Any]],
    current_visit_record: dict[str, Any],
) -> dict[str, Any]:
    """Generate from records through visit N only.

    This function cannot receive full visits, future records, next visits,
    outcome labels, or validation targets.
    """
    hypothesis = _base_hypothesis(current_visit_record)
    if (
        not prefix_only_records
        or prefix_only_records[-1] != current_visit_record
    ):
        raise ValueError("prefix must end at current_visit_record")

    current_state = current_visit_record["current_research_state"]
    if current_state == NOT_AVAILABLE:
        return hypothesis
    if current_state not in POSSIBLE_RESEARCH_STATES:
        return _abstain(
            hypothesis, INSUFFICIENT_EVIDENCE, eligible_count=0
        )

    destinations = _historical_destinations(
        prefix_only_records, current_state
    )
    eligible_count = len(destinations)
    if eligible_count < MIN_TRANSITION_SAMPLES:
        return _abstain(
            hypothesis, "INSUFFICIENT_SAMPLE", eligible_count
        )

    ranked = sorted(
        Counter(destinations).items(),
        key=lambda item: (-item[1], item[0]),
    )
    top_destination, top_count = ranked[0]
    second_count = ranked[1][1] if len(ranked) > 1 else 0
    if second_count == top_count:
        return _abstain(
            hypothesis, INSUFFICIENT_EVIDENCE, eligible_count
        )

    probability, margin, confidence = _confidence(
        destinations, top_destination, top_count, second_count
    )
    hypothesis.update(
        {
            "supporting_transition_count": top_count,
            "eligible_transition_count": eligible_count,
            "descriptive_probability": probability,
            "dominant_margin": margin,
            "hypothesis_confidence": confidence,
        }
    )
    if (
        margin < MIN_DOMINANT_MARGIN
        or confidence < MIN_HYPOTHESIS_CONFIDENCE
    ):
        return _abstain(
            hypothesis, INSUFFICIENT_EVIDENCE, eligible_count
        )

    hypothesis.update(
        {
            "expected_next_research_state": top_destination,
            "trajectory_continuation_hypothesis": (
                f"{current_state}_EXPECTED_TO_{top_destination}"
            ),
            "generation_status": HYPOTHESIS_CREATED,
        }
    )
    return hypothesis


def validate_hypothesis(
    hypothesis: dict[str, Any],
    next_visit_record: dict[str, Any] | None,
) -> dict[str, Any]:
    """Validate an already-created hypothesis against visit N+1 only."""
    result = {
        **hypothesis,
        "validation_visit_index": NOT_AVAILABLE,
        "observed_next_research_state": NOT_AVAILABLE,
        "hypothesis_status": hypothesis["generation_status"],
    }
    if hypothesis["generation_status"] != HYPOTHESIS_CREATED:
        return result
    if next_visit_record is None:
        result["hypothesis_status"] = "RESEARCH_PENDING"
        return result

    observed = next_visit_record["current_research_state"]
    result["validation_visit_index"] = next_visit_record["visit_index"]
    result["observed_next_research_state"] = observed
    if observed == NOT_AVAILABLE:
        result["hypothesis_status"] = INSUFFICIENT_EVIDENCE
    elif observed == hypothesis["expected_next_research_state"]:
        result["hypothesis_status"] = "RESEARCH_CONFIRMED"
    else:
        result["hypothesis_status"] = "RESEARCH_INVALIDATED"
    return result


def generate_all_hypotheses(
    visits_by_zone: dict[str, list[dict]],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    generated: list[dict[str, Any]] = []
    full_records_by_zone: dict[str, list[dict[str, Any]]] = {}

    for zone in sorted(visits_by_zone):
        visits = visits_by_zone[zone]
        full_records_by_zone[zone] = build_trajectory_records({zone: visits})
        for index in range(len(visits)):
            prefix_records = build_trajectory_records(
                {zone: list(visits[: index + 1])}
            )
            generated.append(
                generate_hypothesis(prefix_records, prefix_records[-1])
            )
    return generated, full_records_by_zone


def validate_all_hypotheses(
    generated: list[dict[str, Any]],
    records_by_zone: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    for hypothesis in generated:
        zone_records = records_by_zone[hypothesis["global_zone_key"]]
        next_index = hypothesis["visit_index"]
        next_record = (
            zone_records[next_index]
            if next_index < len(zone_records)
            else None
        )
        validated.append(
            validate_hypothesis(hypothesis, next_record)
        )
    return validated


def _mutation_invariance(
    visits_by_zone: dict[str, list[dict]],
) -> tuple[bool, list[str], int]:
    violations: list[str] = []
    checks = 0
    for zone in sorted(visits_by_zone):
        visits = visits_by_zone[zone]
        representative = sorted(
            {min(5, len(visits) - 1), len(visits) // 2, len(visits) - 2}
        )
        for index in representative:
            if index < 0:
                continue
            original_prefix = build_trajectory_records(
                {zone: list(visits[: index + 1])}
            )
            original = generate_hypothesis(
                original_prefix, original_prefix[-1]
            )

            mutated = copy.deepcopy(visits)
            for future_index in range(index + 1, len(mutated)):
                future = mutated[future_index]
                future["health_at_visit"] = (
                    1_000_000 + future_index * 10_000
                )
                future["omega_at_visit"] = (
                    -1_000_000 - future_index * 20_000
                )
                future["attacker_force_at_visit"] = (
                    5_000_000 + future_index * 30_000
                )
                future["visit_end_row"] = 9_000_000 + future_index
            mutated_prefix = build_trajectory_records(
                {zone: list(mutated[: index + 1])}
            )
            mutated_result = generate_hypothesis(
                mutated_prefix, mutated_prefix[-1]
            )
            checks += 1
            if original != mutated_result:
                violations.append(f"{zone}:{index + 1}")
    return not violations, violations, checks


def _synthetic_records(states: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "global_zone_key": "SYNTHETIC_ZONE",
            "visit_index": index + 1,
            "current_research_state": state,
        }
        for index, state in enumerate(states)
    ]


def run_negative_controls() -> tuple[bool, list[str]]:
    failures: list[str] = []
    stable = "RESEARCH_STABLE"
    recovering = "RESEARCH_RECOVERING"

    tie_records = _synthetic_records(
        [stable, recovering, stable, recovering, stable, stable, stable]
    )
    tied = generate_hypothesis(tie_records, tie_records[-1])
    if not (
        tied["generation_status"] == INSUFFICIENT_EVIDENCE
        and tied["expected_next_research_state"] == NOT_AVAILABLE
    ):
        failures.append("tied_destination_history")

    low_margin_records = _synthetic_records(
        [
            stable,
            recovering,
            stable,
            recovering,
            stable,
            recovering,
            stable,
            recovering,
            stable,
            stable,
            stable,
            stable,
        ]
    )
    low_margin = generate_hypothesis(
        low_margin_records, low_margin_records[-1]
    )
    if not (
        low_margin["generation_status"] == INSUFFICIENT_EVIDENCE
        and low_margin["expected_next_research_state"] == NOT_AVAILABLE
    ):
        failures.append("low_margin_history")

    strong_records = _synthetic_records(
        [stable, recovering, stable, recovering, stable, recovering, stable]
    )
    strong = generate_hypothesis(strong_records, strong_records[-1])
    invalidated = validate_hypothesis(
        strong,
        {
            "visit_index": len(strong_records) + 1,
            "current_research_state": stable,
        },
    )
    if invalidated["hypothesis_status"] != "RESEARCH_INVALIDATED":
        failures.append("deliberate_invalidation")

    unsupported_records = _synthetic_records(["RESEARCH_UNOBSERVED"])
    unsupported = generate_hypothesis(
        unsupported_records, unsupported_records[-1]
    )
    if not (
        unsupported["generation_status"] == INSUFFICIENT_EVIDENCE
        and unsupported["expected_next_research_state"] == NOT_AVAILABLE
    ):
        failures.append("unsupported_current_state")

    pending = validate_hypothesis(strong, None)
    if pending["hypothesis_status"] != "RESEARCH_PENDING":
        failures.append("last_visit_pending")

    first_records = _synthetic_records([NOT_AVAILABLE])
    first = generate_hypothesis(first_records, first_records[-1])
    if first["generation_status"] != NOT_AVAILABLE:
        failures.append("first_visit_not_available")

    return not failures, failures


def validate_architecture(
    visits_by_zone: dict[str, list[dict]],
    generated: list[dict[str, Any]],
    validated: list[dict[str, Any]],
) -> dict[str, Any]:
    violations: list[str] = []
    generation_separated = all(
        not (VALIDATION_FIELDS & set(record)) for record in generated
    )

    generated_by_key = {
        (record["global_zone_key"], record["visit_index"]): record
        for record in generated
    }
    prefix_matches = True
    for zone, visits in visits_by_zone.items():
        for index in range(len(visits)):
            prefix = build_trajectory_records(
                {zone: list(visits[: index + 1])}
            )
            independent = generate_hypothesis(prefix, prefix[-1])
            recorded = generated_by_key[(zone, index + 1)]
            if independent != recorded:
                prefix_matches = False
                violations.append(f"prefix:{zone}:{index + 1}")

    validation_gap_ok = all(
        record["validation_visit_index"] == NOT_AVAILABLE
        or record["validation_visit_index"] == record["visit_index"] + 1
        for record in validated
    )
    if not validation_gap_ok:
        violations.append("validation_gap")

    mutation_ok, mutation_violations, mutation_checks = (
        _mutation_invariance(visits_by_zone)
    )
    violations.extend(
        f"future_mutation:{item}" for item in mutation_violations
    )
    negative_ok, negative_failures = run_negative_controls()
    violations.extend(
        f"negative_control:{item}" for item in negative_failures
    )

    forced_weak = any(
        record["generation_status"]
        in {"INSUFFICIENT_SAMPLE", INSUFFICIENT_EVIDENCE}
        and (
            record["expected_next_research_state"] != NOT_AVAILABLE
            or record["trajectory_continuation_hypothesis"]
            != RESEARCH_UNCERTAIN
        )
        for record in generated
        if record["generation_status"] != NOT_AVAILABLE
    )

    return {
        "generation_validation_separated": generation_separated,
        "hypothesis_uses_only_visits_leq_n": prefix_matches,
        "validation_target_is_exactly_visit_n_plus_1": validation_gap_ok,
        "future_mutation_invariance": mutation_ok,
        "future_mutation_checks": mutation_checks,
        "prefix_matches_independent_truncated_computation": prefix_matches,
        "stage4_full_probability_matrix_used": False,
        "cross_zone_pooling_used": False,
        "negative_controls_pass": negative_ok,
        "forced_hypothesis_under_weak_evidence": forced_weak,
        "leakage_violation_details": violations,
        "negative_control_failures": negative_failures,
    }


def analyze(visits_by_zone: dict[str, list[dict]]) -> dict[str, Any]:
    generated, records_by_zone = generate_all_hypotheses(visits_by_zone)
    validated = validate_all_hypotheses(generated, records_by_zone)
    architecture = validate_architecture(
        visits_by_zone, generated, validated
    )

    hypotheses_generated = sum(
        record["input_research_state"] != NOT_AVAILABLE
        for record in validated
    )
    insufficient_sample_count = sum(
        record["hypothesis_status"] == "INSUFFICIENT_SAMPLE"
        for record in validated
    )
    insufficient_evidence_count = sum(
        record["hypothesis_status"] == INSUFFICIENT_EVIDENCE
        for record in validated
    )
    confirmed_count = sum(
        record["hypothesis_status"] == "RESEARCH_CONFIRMED"
        for record in validated
    )
    invalidated_count = sum(
        record["hypothesis_status"] == "RESEARCH_INVALIDATED"
        for record in validated
    )
    pending_count = sum(
        record["hypothesis_status"] == "RESEARCH_PENDING"
        for record in validated
    )
    eligible_hypotheses = confirmed_count + invalidated_count + pending_count
    graded = confirmed_count + invalidated_count

    observed_states = {
        record["input_research_state"]
        for record in validated
        if record["input_research_state"] != NOT_AVAILABLE
    }
    total_visits = sum(len(visits) for visits in visits_by_zone.values())
    return {
        "zones_observed": len(visits_by_zone),
        "completed_visits": total_visits,
        "hypotheses_generated": hypotheses_generated,
        "eligible_hypotheses": eligible_hypotheses,
        "insufficient_sample_count": insufficient_sample_count,
        "insufficient_evidence_count": insufficient_evidence_count,
        "abstention_count": (
            insufficient_sample_count + insufficient_evidence_count
        ),
        "uncertain_count": sum(
            record["trajectory_continuation_hypothesis"]
            == RESEARCH_UNCERTAIN
            for record in validated
        ),
        "confirmed_count": confirmed_count,
        "invalidated_count": invalidated_count,
        "pending_count": pending_count,
        "coverage": (
            graded / hypotheses_generated
            if hypotheses_generated
            else NOT_AVAILABLE
        ),
        "descriptive_confirmation_rate": (
            confirmed_count / graded if graded else NOT_AVAILABLE
        ),
        "unsupported_states": sorted(
            POSSIBLE_RESEARCH_STATES - observed_states
        ),
        "attacker_pressure_observed": (
            "RESEARCH_ATTACKER_PRESSURE" in observed_states
        ),
        "generation_validation_separated": architecture[
            "generation_validation_separated"
        ],
        "future_mutation_invariance": architecture[
            "future_mutation_invariance"
        ],
        "negative_controls_pass": architecture[
            "negative_controls_pass"
        ],
        "forced_hypothesis_under_weak_evidence": architecture[
            "forced_hypothesis_under_weak_evidence"
        ],
        "leakage_violation_details": architecture[
            "leakage_violation_details"
        ],
        "negative_control_failures": architecture[
            "negative_control_failures"
        ],
        "future_leakage_validation": architecture,
        "hypothesis_records_count": len(validated),
        "records_match_completed_visits": len(validated) == total_visits,
        "predictions_generated": False,
    }


def run_once() -> dict[str, Any]:
    visits_by_zone, errors = collect_completed_visits()
    report = analyze(visits_by_zone)
    report["errors"] = errors
    return report


def _deterministic_payload(report: dict[str, Any]) -> str:
    return json.dumps(report, sort_keys=True, separators=(",", ":"))


def main() -> None:
    reports = [run_once() for _ in range(3)]
    first = reports[0]
    deterministic = all(
        _deterministic_payload(report) == _deterministic_payload(first)
        for report in reports[1:]
    )
    checks = [
        not first["errors"],
        first["completed_visits"] == EXPECTED_COMPLETED_VISITS,
        first["records_match_completed_visits"],
        first["generation_validation_separated"],
        first["future_mutation_invariance"],
        first["negative_controls_pass"],
        not first["forced_hypothesis_under_weak_evidence"],
        not first["leakage_violation_details"],
        not first["negative_control_failures"],
        "RESEARCH_ATTACKER_PRESSURE" in first["unsupported_states"],
        not first["attacker_pressure_observed"],
        not first["predictions_generated"],
        deterministic,
    ]
    result = "PASS" if all(checks) else "FAIL"

    print("===== PHASE 1B STAGE 6 -- HYPOTHESIS EVOLUTION RESEARCH =====")
    for field in (
        "zones_observed",
        "completed_visits",
        "hypotheses_generated",
        "eligible_hypotheses",
        "insufficient_sample_count",
        "insufficient_evidence_count",
        "abstention_count",
        "uncertain_count",
        "confirmed_count",
        "invalidated_count",
        "pending_count",
        "coverage",
        "descriptive_confirmation_rate",
        "unsupported_states",
        "attacker_pressure_observed",
        "generation_validation_separated",
        "future_mutation_invariance",
        "negative_controls_pass",
        "forced_hypothesis_under_weak_evidence",
        "leakage_violation_details",
        "negative_control_failures",
        "future_leakage_validation",
    ):
        print(f"{field} = {json.dumps(first[field], sort_keys=True)}")
    print(f"deterministic_across_runs = {deterministic}")
    print(f"errors = {json.dumps(first['errors'])}")
    print(f"result = {result}")
    print("DESCRIPTIVE_CONFIRMATION_RATE_IS_TRADING_ACCURACY = FALSE")
    print("DESCRIPTIVE_CONFIRMATION_RATE_IS_PRODUCTION_VALIDATION = FALSE")
    print("RESEARCH_ONLY = TRUE")
    print("OFFLINE_ONLY = TRUE")
    print("PROJECT_2_ONLY = TRUE")
    print("PREDICTIONS_GENERATED = FALSE")
    print("EXTERNAL_ENGINES_INTRODUCED = FALSE")
    print("PRODUCTION_EFFECTS = FALSE")
    if result != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

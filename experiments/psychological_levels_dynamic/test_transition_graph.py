"""Phase 1B Stage 4 -- offline Dynamic State transition graph research.

Consumes the Stage 3 completed-visit dataset and the existing Stage 1/2
compute_dynamics() labels unchanged. This module performs aggregate graph
analysis only; it does not calculate mechanics, classify new Dynamic States,
generate predictions, or touch production outputs.
"""

from __future__ import annotations

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

from dynamic_mechanics_test import compute_dynamics
from test_dynamic_state_transitions import collect_completed_visits


EXPECTED_TRANSITIONS = 145
EXPECTED_TRANSITION_COUNTS = {
    "RESEARCH_RECOVERING_TO_RESEARCH_STABLE": 60,
    "RESEARCH_STABLE_TO_RESEARCH_RECOVERING": 61,
    "RESEARCH_STABLE_TO_RESEARCH_STABLE": 24,
}
HIGH_RISK_STATES = {"RESEARCH_ATTACKER_PRESSURE"}
PROBABILITY_TOLERANCE = 1e-12


def _valid_labels(visits: list[dict]) -> list[str]:
    return [
        label
        for label in compute_dynamics(visits)["labels"]
        if label is not None
    ]


def _state_runs(labels: list[str]) -> list[tuple[str, int]]:
    if not labels:
        return []
    runs: list[tuple[str, int]] = []
    current = labels[0]
    length = 1
    for label in labels[1:]:
        if label == current:
            length += 1
            continue
        runs.append((current, length))
        current = label
        length = 1
    runs.append((current, length))
    return runs


def _summarize_lengths(lengths: list[int]) -> dict[str, int | float]:
    return {
        "mean_residence_time": sum(lengths) / len(lengths),
        "max_residence_time": max(lengths),
        "min_residence_time": min(lengths),
        "total_runs": len(lengths),
    }


def analyze_transition_graph(
    visits_by_zone: dict[str, list[dict]],
) -> dict[str, Any]:
    transition_counts: Counter[str] = Counter()
    edge_counts: dict[str, Counter[str]] = defaultdict(Counter)
    state_run_lengths: dict[str, list[int]] = defaultdict(list)
    zone_run_lengths: dict[str, dict[str, list[int]]] = {}
    labels_by_zone: dict[str, list[str]] = {}
    unique_states: set[str] = set()
    completed_visits = 0

    for zone_key in sorted(visits_by_zone):
        visits = visits_by_zone[zone_key]
        completed_visits += len(visits)
        labels = _valid_labels(visits)
        labels_by_zone[zone_key] = labels
        unique_states.update(labels)

        per_zone: dict[str, list[int]] = defaultdict(list)
        for state, run_length in _state_runs(labels):
            per_zone[state].append(run_length)
            state_run_lengths[state].append(run_length)
        zone_run_lengths[zone_key] = {
            state: lengths for state, lengths in sorted(per_zone.items())
        }

        for source, destination in zip(labels, labels[1:]):
            name = f"{source}_TO_{destination}"
            transition_counts[name] += 1
            edge_counts[source][destination] += 1

    probability_matrix: dict[str, dict[str, Any]] = {}
    persistence_summary: dict[str, dict[str, int | float]] = {}
    probability_rows_valid = True
    absorbing_states: list[str] = []

    for source in sorted(edge_counts):
        destinations = edge_counts[source]
        total_outgoing = sum(destinations.values())
        destinations_report = {
            destination: {
                "count": count,
                "probability": count / total_outgoing,
            }
            for destination, count in sorted(destinations.items())
        }
        probability_matrix[source] = {
            "total_outgoing_transitions": total_outgoing,
            "destination_state_count": len(destinations),
            "destinations": destinations_report,
        }
        probability_sum = sum(
            destination["probability"]
            for destination in destinations_report.values()
        )
        if abs(probability_sum - 1.0) > PROBABILITY_TOLERANCE:
            probability_rows_valid = False

        self_count = destinations.get(source, 0)
        persistence_probability = self_count / total_outgoing
        persistence_summary[source] = {
            "self_transition_count": self_count,
            "total_outgoing_transitions": total_outgoing,
            "persistence_probability": persistence_probability,
        }
        if persistence_probability >= 0.80 and len(destinations) <= 1:
            absorbing_states.append(source)

    residence_time_summary: dict[str, dict[str, Any]] = {}
    for state in sorted(state_run_lengths):
        lengths = state_run_lengths[state]
        residence_time_summary[state] = {
            **_summarize_lengths(lengths),
            "zones": {
                zone: {
                    "consecutive_run_lengths": states[state],
                    **_summarize_lengths(states[state]),
                }
                for zone, states in sorted(zone_run_lengths.items())
                if state in states
            },
        }

    cycle_pattern = (
        "RESEARCH_STABLE",
        "RESEARCH_RECOVERING",
        "RESEARCH_STABLE",
    )
    cycle_zones: set[str] = set()
    cycle_count = 0
    for zone_key, labels in labels_by_zone.items():
        for index in range(len(labels) - 2):
            if tuple(labels[index : index + 3]) == cycle_pattern:
                cycle_count += 1
                cycle_zones.add(zone_key)
    cycles_detected = [
        {
            "cycle_name": "RESEARCH_STABLE_TO_RESEARCH_RECOVERING_TO_RESEARCH_STABLE",
            "count": cycle_count,
            "zones": sorted(cycle_zones),
        }
    ]

    critical_transition_count = sum(
        count
        for source, destinations in edge_counts.items()
        for destination, count in destinations.items()
        if destination in HIGH_RISK_STATES and source != destination
    )

    early_warning_paths: Counter[str] = Counter()
    for labels in labels_by_zone.values():
        for index, destination in enumerate(labels):
            if destination not in HIGH_RISK_STATES:
                continue
            for path_length in (3, 4):
                start = index - path_length + 1
                if start >= 0:
                    early_warning_paths[" -> ".join(labels[start : index + 1])] += 1

    all_research_prefixed = all(
        state.startswith("RESEARCH_") for state in unique_states
    ) and all(
        name.startswith("RESEARCH_") and "_TO_RESEARCH_" in name
        for name in transition_counts
    )

    return {
        "zones_observed": len(visits_by_zone),
        "completed_visits": completed_visits,
        "transitions_generated": sum(transition_counts.values()),
        "unique_states": sorted(unique_states),
        "unique_transition_types": len(transition_counts),
        "transition_counts": dict(sorted(transition_counts.items())),
        "transition_probability_matrix": probability_matrix,
        "transition_probability_rows_valid": probability_rows_valid,
        "residence_time_summary": residence_time_summary,
        "persistence_summary": persistence_summary,
        "cycles_detected": cycles_detected,
        "critical_transition_count": critical_transition_count,
        "absorbing_states": absorbing_states,
        "early_warning_paths_count": sum(early_warning_paths.values()),
        "early_warning_paths": dict(sorted(early_warning_paths.items())),
        "all_research_prefixed": all_research_prefixed,
    }


def run_once() -> dict[str, Any]:
    visits_by_zone, errors = collect_completed_visits()
    report = analyze_transition_graph(visits_by_zone)
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

    assertions = [
        not first["errors"],
        first["transitions_generated"] == EXPECTED_TRANSITIONS,
        first["transition_counts"] == EXPECTED_TRANSITION_COUNTS,
        first["transition_probability_rows_valid"],
        first["all_research_prefixed"],
        deterministic,
    ]
    result = "PASS" if all(assertions) else "FAIL"

    print("===== PHASE 1B STAGE 4 -- TRANSITION GRAPH RESEARCH =====")
    for field in (
        "zones_observed",
        "completed_visits",
        "transitions_generated",
        "unique_states",
        "unique_transition_types",
        "transition_counts",
        "transition_probability_matrix",
        "residence_time_summary",
        "persistence_summary",
        "cycles_detected",
        "critical_transition_count",
        "absorbing_states",
        "early_warning_paths_count",
    ):
        print(f"{field} = {json.dumps(first[field], sort_keys=True)}")
    print(f"deterministic_across_runs = {deterministic}")
    print(f"errors = {json.dumps(first['errors'])}")
    print(f"result = {result}")
    print("RESEARCH_ONLY = TRUE")
    print("OFFLINE_ONLY = TRUE")
    print("PROJECT_2_ONLY = TRUE")
    print("PREDICTIONS_GENERATED = FALSE")
    print("PRODUCTION_EFFECTS = FALSE")

    if result != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Phase 1B Stage 5 -- offline Project 2 trajectory evolution research.

Reconstructs ordered visit trajectories from the unchanged Stage 3 completed
visits and Stage 1 compute_dynamics() output. This is descriptive research,
not production B10/B11, prediction, signals, or execution.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DYNAMIC_DIR = Path(__file__).resolve().parent
for path in (REPO_ROOT, DYNAMIC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dynamic_mechanics_test import compute_dynamics
from test_dynamic_state_transitions import collect_completed_visits


NOT_AVAILABLE = "NOT_AVAILABLE"
MIN_STATE_SAMPLES = 3
MIN_TRANSITION_SAMPLES = 3
MIN_ZONE_VISITS = 3
EXPECTED_COMPLETED_VISITS = 159
EXPECTED_TRANSITIONS = 145
EXPECTED_TRANSITION_COUNTS = {
    "RESEARCH_RECOVERING_TO_RESEARCH_STABLE": 60,
    "RESEARCH_STABLE_TO_RESEARCH_RECOVERING": 61,
    "RESEARCH_STABLE_TO_RESEARCH_STABLE": 24,
}
POSSIBLE_RESEARCH_STATES = {
    "RESEARCH_ATTACKER_PRESSURE",
    "RESEARCH_RECOVERING",
    "RESEARCH_STABLE",
}
MECHANICAL_FIELDS = (
    "health_at_visit",
    "omega_at_visit",
    "attacker_force_at_visit",
    "research_sdr",
    "first_derivative",
    "second_derivative",
    "integral",
)


def _available(value: Any) -> bool:
    return value is not None and value != NOT_AVAILABLE


def _number(value: Any) -> float | str:
    if not _available(value):
        return NOT_AVAILABLE
    if isinstance(value, Decimal):
        return float(value)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return NOT_AVAILABLE
    return number if math.isfinite(number) else NOT_AVAILABLE


def _dominant(values: list[str]) -> str:
    if not values:
        return NOT_AVAILABLE
    counts = Counter(values)
    return sorted(counts, key=lambda value: (-counts[value], value))[0]


def _longest_state_run(states: list[str]) -> tuple[str, int]:
    available = [state for state in states if state != NOT_AVAILABLE]
    if not available:
        return NOT_AVAILABLE, 0
    best_state = available[0]
    best_length = 1
    current_state = available[0]
    current_length = 1
    for state in available[1:]:
        if state == current_state:
            current_length += 1
        else:
            current_state = state
            current_length = 1
        if current_length > best_length:
            best_state = current_state
            best_length = current_length
    return best_state, best_length


def _describe(values: list[Any], minimum: int) -> dict[str, Any]:
    numeric = [
        float(value)
        for value in values
        if _available(value) and math.isfinite(float(value))
    ]
    status = "SUFFICIENT_SAMPLE" if len(numeric) >= minimum else "INSUFFICIENT_SAMPLE"
    if not numeric:
        return {
            "sample_count": 0,
            "sample_status": status,
            "mean": NOT_AVAILABLE,
            "min": NOT_AVAILABLE,
            "max": NOT_AVAILABLE,
            "first": NOT_AVAILABLE,
            "last": NOT_AVAILABLE,
            "total_change": NOT_AVAILABLE,
        }
    return {
        "sample_count": len(numeric),
        "sample_status": status,
        "mean": sum(numeric) / len(numeric),
        "min": min(numeric),
        "max": max(numeric),
        "first": numeric[0],
        "last": numeric[-1],
        "total_change": numeric[-1] - numeric[0],
    }


def build_trajectory_records(
    visits_by_zone: dict[str, list[dict]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for global_zone_key in sorted(visits_by_zone):
        visits = visits_by_zone[global_zone_key]
        dynamics = compute_dynamics(visits)
        residence_state: str | None = None
        residence_position = 0

        for index, visit in enumerate(visits):
            current = dynamics["labels"][index]
            previous = dynamics["labels"][index - 1] if index > 0 else None
            current_value = current or NOT_AVAILABLE
            previous_value = previous or NOT_AVAILABLE

            if current is None:
                residence_position_value: int | str = NOT_AVAILABLE
                residence_state = None
                residence_position = 0
            else:
                if current == residence_state:
                    residence_position += 1
                else:
                    residence_state = current
                    residence_position = 1
                residence_position_value = residence_position

            transition = (
                f"{previous}_TO_{current}"
                if previous is not None and current is not None
                else NOT_AVAILABLE
            )
            unsupported = (
                current is not None
                and current not in POSSIBLE_RESEARCH_STATES
            )
            zone_id = str(visit.get("visit_id", "")).split(":V", 1)[0]
            records.append(
                {
                    "global_zone_key": global_zone_key,
                    "zone_id": zone_id or NOT_AVAILABLE,
                    "visit_index": index + 1,
                    "row_index": visit.get("visit_end_row", NOT_AVAILABLE),
                    "current_research_state": current_value,
                    "previous_research_state": previous_value,
                    "transition_name": transition,
                    "first_derivative": _number(
                        dynamics["d1_health"][index]
                    ),
                    "second_derivative": _number(
                        dynamics["d2_health"][index]
                    ),
                    "integral": _number(
                        dynamics["integral_omega"][index]
                    ),
                    "research_sdr": _number(dynamics["sdr"][index]),
                    "health_at_visit": _number(
                        visit.get("health_at_visit")
                    ),
                    "omega_at_visit": _number(
                        visit.get("omega_at_visit")
                    ),
                    "attacker_force_at_visit": _number(
                        visit.get("attacker_force_at_visit")
                    ),
                    "residence_position": residence_position_value,
                    "trajectory_position": index + 1,
                    "is_first_visit": index == 0,
                    "is_transition_visit": transition != NOT_AVAILABLE,
                    "unsupported_state_flag": unsupported,
                }
            )
    return records


def _records_by_zone(
    records: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["global_zone_key"]].append(record)
    return {
        zone: sorted(rows, key=lambda row: row["visit_index"])
        for zone, rows in sorted(grouped.items())
    }


def build_per_zone_analysis(
    records: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    trajectory_summary: dict[str, Any] = {}
    signature_summary: dict[str, Any] = {}

    for zone, rows in _records_by_zone(records).items():
        states = [row["current_research_state"] for row in rows]
        valid_states = [state for state in states if state != NOT_AVAILABLE]
        transitions = [
            row["transition_name"]
            for row in rows
            if row["transition_name"] != NOT_AVAILABLE
        ]
        longest_state, longest_length = _longest_state_run(states)
        oscillation_count = sum(
            transition
            in {
                "RESEARCH_STABLE_TO_RESEARCH_RECOVERING",
                "RESEARCH_RECOVERING_TO_RESEARCH_STABLE",
            }
            for transition in transitions
        )
        sample_status = (
            "SUFFICIENT_SAMPLE"
            if len(rows) >= MIN_ZONE_VISITS
            else "INSUFFICIENT_SAMPLE"
        )

        trajectory_summary[zone] = {
            "ordered_visits": [row["visit_index"] for row in rows],
            "ordered_states": states,
            "ordered_transitions": transitions,
            "completed_visits": len(rows),
            "transitions": len(transitions),
            "first_state": valid_states[0] if valid_states else NOT_AVAILABLE,
            "last_state": valid_states[-1] if valid_states else NOT_AVAILABLE,
            "sample_status": sample_status,
        }
        signature_summary[zone] = {
            "state_sequence": states,
            "transition_sequence": transitions,
            "dominant_state": _dominant(valid_states),
            "dominant_transition": _dominant(transitions),
            "visit_count": len(rows),
            "transition_count": len(transitions),
            "longest_residence_state": longest_state,
            "longest_residence_length": longest_length,
            "oscillation_count": oscillation_count,
            "stable_to_recovering_count": transitions.count(
                "RESEARCH_STABLE_TO_RESEARCH_RECOVERING"
            ),
            "recovering_to_stable_count": transitions.count(
                "RESEARCH_RECOVERING_TO_RESEARCH_STABLE"
            ),
            "unsupported_state_count": sum(
                row["unsupported_state_flag"] for row in rows
            ),
            "sample_status": sample_status,
        }

    return trajectory_summary, signature_summary


def build_state_evolution(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    by_state: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        state = record["current_research_state"]
        if state != NOT_AVAILABLE:
            by_state[state].append(record)

    output: dict[str, Any] = {}
    for state in sorted(POSSIBLE_RESEARCH_STATES):
        rows = by_state.get(state, [])
        output[state] = {
            "sample_count": len(rows),
            "sample_status": (
                "SUFFICIENT_SAMPLE"
                if len(rows) >= MIN_STATE_SAMPLES
                else "INSUFFICIENT_SAMPLE"
            ),
            "mechanics": {
                field: _describe(
                    [row[field] for row in rows], MIN_STATE_SAMPLES
                )
                for field in MECHANICAL_FIELDS
            },
        }
    return output


def build_transition_evolution(
    records: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    transitions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    windows: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for zone, rows in _records_by_zone(records).items():
        for index, current in enumerate(rows):
            transition = current["transition_name"]
            if transition == NOT_AVAILABLE or index == 0:
                continue
            previous = rows[index - 1]
            event = {
                "global_zone_key": zone,
                "visit_index": current["visit_index"],
                "previous_visit_mechanics": {
                    field: previous[field] for field in MECHANICAL_FIELDS
                },
                "current_visit_mechanics": {
                    field: current[field] for field in MECHANICAL_FIELDS
                },
            }
            for field in (
                "health_at_visit",
                "omega_at_visit",
                "attacker_force_at_visit",
                "research_sdr",
                "integral",
            ):
                prior = previous[field]
                now = current[field]
                event[f"delta_{field}"] = (
                    now - prior
                    if _available(prior) and _available(now)
                    else NOT_AVAILABLE
                )
            transitions[transition].append(event)
            windows[transition].append(
                {
                    "previous_visit": previous,
                    "transition_visit": current,
                    "next_visit": (
                        rows[index + 1]
                        if index + 1 < len(rows)
                        else NOT_AVAILABLE
                    ),
                }
            )

    evolution_summary: dict[str, Any] = {}
    window_summary: dict[str, Any] = {}
    for transition in sorted(transitions):
        events = transitions[transition]
        evolution_summary[transition] = {
            "sample_count": len(events),
            "sample_status": (
                "SUFFICIENT_SAMPLE"
                if len(events) >= MIN_TRANSITION_SAMPLES
                else "INSUFFICIENT_SAMPLE"
            ),
            "delta_mechanics": {
                field: _describe(
                    [event[f"delta_{field}"] for event in events],
                    MIN_TRANSITION_SAMPLES,
                )
                for field in (
                    "health_at_visit",
                    "omega_at_visit",
                    "attacker_force_at_visit",
                    "research_sdr",
                    "integral",
                )
            },
        }
        window_rows = windows[transition]
        window_summary[transition] = {
            "sample_count": len(window_rows),
            "complete_previous_transition_next_windows": sum(
                window["next_visit"] != NOT_AVAILABLE
                for window in window_rows
            ),
            "sample_status": (
                "SUFFICIENT_SAMPLE"
                if len(window_rows) >= MIN_TRANSITION_SAMPLES
                else "INSUFFICIENT_SAMPLE"
            ),
        }
    return evolution_summary, window_summary


def build_cross_zone_comparison(
    signatures: dict[str, Any],
) -> dict[str, Any]:
    visit_distribution = {
        zone: signature["visit_count"]
        for zone, signature in sorted(signatures.items())
    }
    transition_distribution = {
        zone: signature["transition_count"]
        for zone, signature in sorted(signatures.items())
    }
    dominant_states = {
        zone: signature["dominant_state"]
        for zone, signature in sorted(signatures.items())
    }
    return {
        "number_of_zones": len(signatures),
        "visit_count_distribution": visit_distribution,
        "transition_count_distribution": transition_distribution,
        "dominant_states_by_zone": dominant_states,
        "high_oscillation_zones": sorted(
            zone
            for zone, signature in signatures.items()
            if signature["oscillation_count"] >= 3
        ),
        "single_state_zones": sorted(
            zone
            for zone, signature in signatures.items()
            if len(
                {
                    state
                    for state in signature["state_sequence"]
                    if state != NOT_AVAILABLE
                }
            )
            == 1
        ),
        "zones_with_no_transitions": sorted(
            zone
            for zone, signature in signatures.items()
            if signature["transition_count"] == 0
        ),
        "zones_with_unsupported_states": sorted(
            zone
            for zone, signature in signatures.items()
            if signature["unsupported_state_count"] > 0
        ),
    }


def analyze(visits_by_zone: dict[str, list[dict]]) -> dict[str, Any]:
    records = build_trajectory_records(visits_by_zone)
    trajectories, signatures = build_per_zone_analysis(records)
    state_evolution = build_state_evolution(records)
    transition_evolution, windows = build_transition_evolution(records)
    comparison = build_cross_zone_comparison(signatures)

    observed_states = sorted(
        {
            record["current_research_state"]
            for record in records
            if record["current_research_state"] != NOT_AVAILABLE
        }
    )
    unobserved_states = sorted(POSSIBLE_RESEARCH_STATES - set(observed_states))
    transition_counts = Counter(
        record["transition_name"]
        for record in records
        if record["transition_name"] != NOT_AVAILABLE
    )
    total_visits = sum(len(visits) for visits in visits_by_zone.values())
    labels_research_only = all(
        state.startswith("RESEARCH_") for state in observed_states
    ) and all(
        name.startswith("RESEARCH_") and "_TO_RESEARCH_" in name
        for name in transition_counts
    )
    not_available_respected = all(
        record["current_research_state"] != NOT_AVAILABLE
        or (
            record["first_derivative"] == NOT_AVAILABLE
            and record["second_derivative"] == NOT_AVAILABLE
            and record["research_sdr"] == NOT_AVAILABLE
            and record["transition_name"] == NOT_AVAILABLE
        )
        for record in records
    )

    sample_sufficiency = {
        "thresholds": {
            "min_state_samples": MIN_STATE_SAMPLES,
            "min_transition_samples": MIN_TRANSITION_SAMPLES,
            "min_zone_visits": MIN_ZONE_VISITS,
        },
        "states": {
            state: summary["sample_status"]
            for state, summary in state_evolution.items()
        },
        "transitions": {
            transition: summary["sample_status"]
            for transition, summary in transition_evolution.items()
        },
        "zones": {
            zone: summary["sample_status"]
            for zone, summary in trajectories.items()
        },
        "insufficient_sample_flags": sum(
            summary["sample_status"] == "INSUFFICIENT_SAMPLE"
            for summary in state_evolution.values()
        )
        + sum(
            summary["sample_status"] == "INSUFFICIENT_SAMPLE"
            for summary in transition_evolution.values()
        )
        + sum(
            summary["sample_status"] == "INSUFFICIENT_SAMPLE"
            for summary in trajectories.values()
        ),
    }

    return {
        "zones_observed": len(visits_by_zone),
        "trajectory_records_generated": len(records),
        "completed_visits": total_visits,
        "transitions_generated": sum(transition_counts.values()),
        "transition_counts": dict(sorted(transition_counts.items())),
        "observed_states": observed_states,
        "unobserved_states": unobserved_states,
        "attacker_pressure_observed": (
            "RESEARCH_ATTACKER_PRESSURE" in observed_states
        ),
        "unsupported_state_count": sum(
            record["unsupported_state_flag"] for record in records
        ),
        "per_zone_trajectory_summary": trajectories,
        "per_zone_signature_summary": signatures,
        "mechanical_evolution_by_state": state_evolution,
        "mechanical_evolution_by_transition": transition_evolution,
        "transition_window_summary": windows,
        "cross_zone_comparison": comparison,
        "sample_sufficiency_summary": sample_sufficiency,
        "per_zone_counts_consistent": (
            sum(item["completed_visits"] for item in trajectories.values())
            == len(records)
        ),
        "all_labels_research_prefixed": labels_research_only,
        "not_available_respected": not_available_respected,
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
        first["trajectory_records_generated"] == EXPECTED_COMPLETED_VISITS,
        first["trajectory_records_generated"] == first["completed_visits"],
        first["transitions_generated"] == EXPECTED_TRANSITIONS,
        first["transition_counts"] == EXPECTED_TRANSITION_COUNTS,
        first["per_zone_counts_consistent"],
        first["all_labels_research_prefixed"],
        first["not_available_respected"],
        "RESEARCH_ATTACKER_PRESSURE" in first["unobserved_states"],
        first["sample_sufficiency_summary"]["insufficient_sample_flags"] > 0,
        not first["predictions_generated"],
        deterministic,
    ]
    result = "PASS" if all(checks) else "FAIL"

    print("===== PHASE 1B STAGE 5 -- TRAJECTORY EVOLUTION RESEARCH =====")
    for field in (
        "zones_observed",
        "trajectory_records_generated",
        "completed_visits",
        "transitions_generated",
        "observed_states",
        "unobserved_states",
        "attacker_pressure_observed",
        "unsupported_state_count",
        "per_zone_trajectory_summary",
        "per_zone_signature_summary",
        "mechanical_evolution_by_state",
        "mechanical_evolution_by_transition",
        "transition_window_summary",
        "cross_zone_comparison",
        "sample_sufficiency_summary",
    ):
        print(f"{field} = {json.dumps(first[field], sort_keys=True)}")
    print(f"deterministic_across_runs = {deterministic}")
    print(f"errors = {json.dumps(first['errors'])}")
    print(f"result = {result}")
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

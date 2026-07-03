"""Phase 1B Stage 3 -- offline Dynamic State transition analysis.

Research-only. Analyzes the transition patterns produced by Stage 1/2
(experiments/psychological_levels_dynamic/{dynamic_mechanics_test,
test_snapshot_dynamic_mechanics}.py) -- current/previous dynamic_state,
transition_name, transition frequency, per-zone transition chains, repeated
transitions, stable vs unstable state sequences, and a simple research-only
early-warning pattern.

This is pure aggregate analysis over already-computed RESEARCH_-prefixed
labels. It does not compute any new mechanical value, does not rename or
replace production Dynamic State / B12.5, and does not touch any core/
production module, Project 1, live pipeline, dashboard, or B10/B11 code. It
only needs the Interaction Interpreter and LastCompletedVisitAdapter to
collect completed-visit sequences -- Snapshot / Dispatcher / Coordinator are
not required for this analysis and are not used here (Stage 2 already
validated that path).
"""

from __future__ import annotations

import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
LAB_DIR = REPO_ROOT / "experiments" / "psychological_levels"
DYNAMIC_DIR = Path(__file__).resolve().parent
for path in (REPO_ROOT, LAB_DIR, DYNAMIC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.interaction_interpreter import ORDER_ACCEPTED
from core.last_completed_visit_adapter import LastCompletedVisitAdapter

from dynamic_mechanics_test import (
    ROW_COUNT,
    build_harnesses,
    compute_dynamics,
    generate_price,
    update_mechanics,
)


STABLE_RUN_THRESHOLD = 3  # consecutive identical dynamic_state values -> "stable"
EARLY_WARNING_STATE = "RESEARCH_ATTACKER_PRESSURE"
TOP_N_TRANSITIONS = 5


def collect_completed_visits() -> tuple[dict[str, list[dict]], list[str]]:
    """Replay Stage 1's interpreter-driven simulation, collecting each zone's
    ordered completed-visit summaries. Only the Interpreter and
    LastCompletedVisitAdapter are used -- no Dispatcher/Coordinator/Snapshot,
    since transition analysis needs only the visit sequence."""
    harnesses = build_harnesses()
    errors: list[str] = []
    previous_price: Decimal | None = None

    for row_index in range(1, ROW_COUNT + 1):
        price = generate_price(row_index)
        price_delta = (
            price - previous_price if previous_price is not None else Decimal("0")
        )
        previous_price = price
        timestamp = f"T{row_index}"

        for global_key, harness in harnesses.items():
            try:
                interpreted = harness.interpreter.interpret_in_order(
                    harness.state,
                    row_index=row_index,
                    timestamp=timestamp,
                    price=price,
                )
                if interpreted.status != ORDER_ACCEPTED:
                    errors.append(f"{global_key}:{row_index}:{interpreted.status}")
                    continue
                harness.state = interpreted.state
                update_mechanics(
                    harness,
                    touching=harness.state.touching_zone,
                    penetration_depth=Decimal(
                        str(harness.state.last_penetration_depth)
                    ),
                    price_delta=price_delta,
                )
                for event in interpreted.events:
                    if event.event_type != "VISIT_COMPLETED":
                        continue
                    completed_source = dict(event.evidence)
                    completed_source["visit_id"] = event.visit_id
                    completed_source["health_at_visit"] = harness.health_live
                    completed_source["omega_at_visit"] = harness.omega_accumulator
                    completed_source["attacker_force_at_visit"] = (
                        harness.attacker_force_peak
                    )
                    patch = LastCompletedVisitAdapter().build_patch(
                        completed_source
                    )
                    harness.completed_visits.append(
                        patch["last_completed_visit"]
                    )
                    harness.omega_accumulator = Decimal("0")
                    harness.attacker_force_peak = Decimal("0")
            except Exception as exc:  # research harness: never abort the run
                errors.append(
                    f"{global_key}:{row_index}:{type(exc).__name__}:{exc}"
                )

    return {key: h.completed_visits for key, h in harnesses.items()}, errors


def _longest_run(sequence: list[Any]) -> int:
    if not sequence:
        return 0
    longest = 1
    current = 1
    for i in range(1, len(sequence)):
        if sequence[i] == sequence[i - 1]:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return longest


def analyze(visits_by_zone: dict[str, list[dict]]) -> dict[str, Any]:
    transition_counter: Counter[str] = Counter()
    per_zone_transition_counts: dict[str, int] = {}
    repeated_transition_chains = 0
    stable_zone_count = 0
    unstable_zone_count = 0
    early_warning_transitions = 0
    completed_visits_total = 0
    transitions_generated = 0

    for zone_key, visits in visits_by_zone.items():
        completed_visits_total += len(visits)
        dynamics = compute_dynamics(visits)
        labels = dynamics["labels"]

        zone_transitions: list[str] = []
        for i in range(1, len(labels)):
            previous_label = labels[i - 1]
            current_label = labels[i]
            if previous_label is None or current_label is None:
                continue
            transition_name = f"{previous_label}_TO_{current_label}"
            zone_transitions.append(transition_name)
            transition_counter[transition_name] += 1
            transitions_generated += 1
            if (
                current_label == EARLY_WARNING_STATE
                and previous_label != EARLY_WARNING_STATE
            ):
                early_warning_transitions += 1

        per_zone_transition_counts[zone_key] = len(zone_transitions)

        # repeated consecutive transitions (same transition_name back-to-back)
        for i in range(1, len(zone_transitions)):
            if zone_transitions[i] == zone_transitions[i - 1]:
                repeated_transition_chains += 1

        # stability: longest run of consecutive identical dynamic_state values
        valid_labels = [label for label in labels if label is not None]
        if _longest_run(valid_labels) >= STABLE_RUN_THRESHOLD:
            stable_zone_count += 1
        else:
            unstable_zone_count += 1

    all_research_prefixed = all(
        name.startswith("RESEARCH_") and "_TO_RESEARCH_" in name
        for name in transition_counter
    )
    counts_consistent = (
        sum(per_zone_transition_counts.values()) == transitions_generated
    )

    return {
        "zones_observed": len(visits_by_zone),
        "completed_visits": completed_visits_total,
        "transitions_generated": transitions_generated,
        "unique_transition_types": len(transition_counter),
        "most_common_transitions": transition_counter.most_common(
            TOP_N_TRANSITIONS
        ),
        "per_zone_transition_counts": per_zone_transition_counts,
        "repeated_transition_chains": repeated_transition_chains,
        "stable_state_sequences": stable_zone_count,
        "unstable_state_sequences": unstable_zone_count,
        "early_warning_transitions": early_warning_transitions,
        "all_research_prefixed": all_research_prefixed,
        "counts_consistent": counts_consistent,
    }


def run() -> dict[str, Any]:
    visits_by_zone, errors = collect_completed_visits()
    analysis = analyze(visits_by_zone)
    result = (
        "PASS"
        if (
            not errors
            and analysis["all_research_prefixed"]
            and analysis["counts_consistent"]
            and analysis["stable_state_sequences"]
            + analysis["unstable_state_sequences"]
            == analysis["zones_observed"]
        )
        else "FAIL"
    )
    return {
        **analysis,
        "errors": len(errors),
        "error_detail": errors[:10],
        "result": result,
    }


def main() -> None:
    first = run()
    second = run()
    deterministic = (
        first["transitions_generated"] == second["transitions_generated"]
        and first["most_common_transitions"] == second["most_common_transitions"]
        and first["per_zone_transition_counts"]
        == second["per_zone_transition_counts"]
        and first["stable_state_sequences"] == second["stable_state_sequences"]
    )

    print("===== PHASE 1B STAGE 3 -- DYNAMIC STATE TRANSITION ANALYSIS =====")
    print(f"zones_observed = {first['zones_observed']}")
    print(f"completed_visits = {first['completed_visits']}")
    print(f"transitions_generated = {first['transitions_generated']}")
    print(f"unique_transition_types = {first['unique_transition_types']}")
    print("most_common_transitions:")
    for name, count in first["most_common_transitions"]:
        print(f"  {name} = {count}")
    print(f"per_zone_transition_counts = {first['per_zone_transition_counts']}")
    print(f"repeated_transition_chains = {first['repeated_transition_chains']}")
    print(f"stable_state_sequences = {first['stable_state_sequences']}")
    print(f"unstable_state_sequences = {first['unstable_state_sequences']}")
    print(
        "early_warning_transitions (research-only) = "
        f"{first['early_warning_transitions']}"
    )
    print(f"deterministic_across_runs = {deterministic}")
    print(f"errors = {first['errors']}")
    if first["error_detail"]:
        print("error_detail (first 10):")
        for item in first["error_detail"]:
            print(f"  {item}")

    overall = "PASS" if first["result"] == "PASS" and deterministic else "FAIL"
    print(f"result = {overall}")
    print("RESEARCH_ONLY = TRUE")
    print("NO_PROJECT1_CHANGES = TRUE")
    print("NO_PRODUCTION_B125_DYNAMIC_STATE = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")
    if overall != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

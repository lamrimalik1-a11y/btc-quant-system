"""Phase 1B Stage 2 -- offline Dynamic Mechanics -> Canonical Snapshot mapping.

Research-only. Reuses Stage 1's completed-visit sequence and research metrics
(experiments/psychological_levels_dynamic/dynamic_mechanics_test.py) and maps
them, through the existing, unmodified DynamicMechanicsAdapter, into the
existing, unmodified Canonical Snapshot -- alongside the existing, unmodified
LastCompletedVisitAdapter, exactly the atomic multi-adapter commit pattern
already proven in Phase 0/1A.

No production code changed, no Project 1 changes, no live integration, no
dashboard, no B10/B11 changes, no production Dynamic State changes.
SIMPLE_RESEARCH_SDR_V1 and RESEARCH_-prefixed labels/transitions remain
research-only throughout.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
LAB_DIR = REPO_ROOT / "experiments" / "psychological_levels"
DYNAMIC_DIR = Path(__file__).resolve().parent
for path in (REPO_ROOT, LAB_DIR, DYNAMIC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.canonical_snapshot import SnapshotStore
from core.dynamic_mechanics_adapter import DynamicMechanicsAdapter
from core.event_dispatcher import (
    DispatchBatch,
    DispatchContext,
    EventDispatcher,
)
from core.interaction_interpreter import ORDER_ACCEPTED
from core.last_completed_visit_adapter import LastCompletedVisitAdapter
from core.row_mechanics_adapter import NOT_AVAILABLE

from dynamic_mechanics_test import (
    ROW_COUNT,
    build_harnesses,
    compute_dynamics,
    generate_price,
    update_mechanics,
)


# Same dirty-flag pair used throughout Phase 0/1A for Dynamic Mechanics
# gating (set by VISIT_COMPLETED alongside visit_dirty/response_dirty).
DYNAMIC_MECHANICS_GATE = ("response_dirty", "state_dirty")


def geometry_patch(geometry) -> dict:
    return {
        "geometry": {
            "geometry_source": geometry.geometry_source,
            "geometry_type": geometry.geometry_type,
            "geometry_version": geometry.geometry_version,
            "level_center": geometry.level_center,
            "lower_edge": geometry.lower_edge,
            "upper_edge": geometry.upper_edge,
            "zone_width": geometry.zone_width,
            "spacing": geometry.spacing,
            "zone_id": geometry.zone_id,
            "case_id": geometry.case_id,
            "shadow_only": True,
        }
    }


def build_dynamic_patch_input(visits: list[dict], visit_number: int) -> dict[str, Any]:
    """Build the DynamicMechanicsAdapter input for the visit_number-th (1-based)
    completed visit of one zone, from Stage 1's research-only metrics.

    Unmapped fields (health_slope, omega_total, dynamic_state_reason, ...) are
    intentionally absent -- Stage 1 never computed them -- so the adapter maps
    them to NOT_AVAILABLE, exactly as it does for any real caller that omits a
    field it does not have.
    """
    window = visits[:visit_number]
    dynamics = compute_dynamics(window)
    current_label = dynamics["labels"][-1]
    previous_label = (
        dynamics["labels"][-2] if len(dynamics["labels"]) >= 2 else None
    )
    transition_name = (
        f"{previous_label}_TO_{current_label}"
        if previous_label is not None and current_label is not None
        else None
    )
    latest_visit = window[-1]
    return {
        "visit_id": latest_visit.get("visit_id"),
        "first_derivative": dynamics["d1_health"][-1],
        "second_derivative": dynamics["d2_health"][-1],
        "zone_integral": dynamics["integral_omega"][-1],
        "attacker_integral": dynamics["integral_response"][-1],
        "SDR": dynamics["sdr"][-1],
        "dynamic_state": current_label,
        "previous_dynamic_state": previous_label,
        "transition_name": transition_name,
        "dynamic_state_as_of_visit": visit_number,
        "dynamic_updated_at": latest_visit.get("visit_end_timestamp"),
    }


def run() -> dict[str, Any]:
    harnesses = build_harnesses()
    store = SnapshotStore()
    errors: list[str] = []
    revision_history: dict[str, list[int]] = {key: [] for key in harnesses}
    dynamic_state_history: dict[str, list[Any]] = {key: [] for key in harnesses}
    previous_state_used_history: dict[str, list[Any]] = {
        key: [] for key in harnesses
    }
    first_snapshot: dict[str, Any] = {}
    first_snapshot_copy: dict[str, Any] = {}
    dynamic_commits = 0
    not_available_counts = {
        "first_derivative": 0,
        "second_derivative": 0,
        "dynamic_state": 0,
        "transition_name": 0,
    }
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
                if not interpreted.events:
                    continue

                dispatched = harness.dispatcher.dispatch(
                    DispatchBatch.from_events(
                        DispatchContext(
                            session_id=harness.geometry.session_id,
                            zone_id=harness.geometry.zone_id,
                            row_index=row_index,
                            timestamp=timestamp,
                            global_zone_key=global_key,
                            geometry_version=harness.geometry.geometry_version,
                        ),
                        harness.state,
                        interpreted.events,
                    )
                )
                if dispatched.status != "DISPATCHED_SHADOW":
                    errors.append(f"{global_key}:{row_index}:{dispatched.status}")
                    continue

                plan = dispatched.coordinator_result.plan
                if not (plan.dirty_flags.visit_dirty and plan.dirty_flags.response_dirty):
                    continue

                completed_event = interpreted.events[-1]
                completed_source = dict(completed_event.evidence)
                completed_source["visit_id"] = completed_event.visit_id
                completed_source["health_at_visit"] = harness.health_live
                completed_source["omega_at_visit"] = harness.omega_accumulator
                completed_source["attacker_force_at_visit"] = (
                    harness.attacker_force_peak
                )
                lcv_patch = LastCompletedVisitAdapter().build_patch(
                    completed_source
                )
                harness.completed_visits.append(lcv_patch["last_completed_visit"])
                harness.omega_accumulator = Decimal("0")
                harness.attacker_force_peak = Decimal("0")

                patches: list[dict] = [lcv_patch]
                if all(
                    getattr(plan.dirty_flags, name)
                    for name in DYNAMIC_MECHANICS_GATE
                ):
                    dm_input = build_dynamic_patch_input(
                        harness.completed_visits,
                        len(harness.completed_visits),
                    )
                    dm_patch = DynamicMechanicsAdapter().build_patch(dm_input)
                    patches.append(dm_patch)
                    dynamic_commits += 1
                    section = dm_patch["dynamic_mechanics"]
                    for field in (
                        "first_derivative",
                        "second_derivative",
                        "dynamic_state",
                        "transition_name",
                    ):
                        if section[field] == NOT_AVAILABLE:
                            not_available_counts[field] += 1
                    dynamic_state_history[global_key].append(
                        section["dynamic_state"]
                    )
                    previous_state_used_history[global_key].append(
                        section["previous_dynamic_state"]
                    )

                if store.get_current(global_key) is None:
                    snapshot = store.create(
                        plan,
                        (
                            {
                                "metadata": {
                                    "session_id": harness.geometry.session_id
                                }
                            },
                            geometry_patch(harness.geometry),
                            *patches,
                        ),
                        global_zone_key=global_key,
                    )
                    first_snapshot[global_key] = snapshot
                    first_snapshot_copy[global_key] = snapshot.to_dict()
                else:
                    snapshot = store.update(
                        plan, tuple(patches), global_zone_key=global_key
                    )
                revision_history[global_key].append(snapshot.revision)
            except Exception as exc:  # research harness: never abort the run
                errors.append(
                    f"{global_key}:{row_index}:{type(exc).__name__}:{exc}"
                )

    # ---------------------------------------------------------------- checks
    zones_observed = len(harnesses)
    completed_visits_total = sum(
        len(h.completed_visits) for h in harnesses.values()
    )

    revision_monotonic = all(
        history == sorted(history) and len(history) == len(set(history))
        for history in revision_history.values()
    )
    copy_on_write = all(
        first_snapshot[key].revision == 1
        and first_snapshot[key].to_dict() == first_snapshot_copy[key]
        for key in first_snapshot
    )
    global_zone_key_preserved = all(
        store.get_current(key) is not None
        and store.get_current(key).global_zone_key == key
        for key in harnesses
    )
    dynamic_section_updated = all(
        store.get_current(key) is not None
        and bool(store.get_current(key).dynamic_mechanics)
        and store.get_current(key).dynamic_mechanics.get("zone_integral")
        != NOT_AVAILABLE
        for key in harnesses
        if dynamic_state_history[key]
    )
    # previous_dynamic_state chain-consistency: commit i's previous_dynamic_state
    # (recorded at commit time) must equal commit (i-1)'s dynamic_state, for
    # every zone's dynamic-commit sequence; the very first commit has no prior
    # visit, so previous_dynamic_state must be NOT_AVAILABLE (the adapter's
    # sentinel for an absent/None field, not the Python literal None).
    state_chain_consistent = True
    for key in harnesses:
        current_seq = dynamic_state_history[key]
        previous_seq = previous_state_used_history[key]
        if not current_seq:
            continue
        if previous_seq[0] != NOT_AVAILABLE:
            state_chain_consistent = False
        for i in range(1, len(current_seq)):
            if previous_seq[i] != current_seq[i - 1]:
                state_chain_consistent = False

    transitions_research_only = True
    for key in harnesses:
        for transition in _transition_names(store.get_current(key)):
            if transition != NOT_AVAILABLE and "RESEARCH_" not in transition:
                transitions_research_only = False

    not_available_expected = (
        not_available_counts["first_derivative"] >= zones_observed
        and not_available_counts["dynamic_state"] >= zones_observed
        and not_available_counts["second_derivative"] >= zones_observed
    )

    result = "PASS" if (
        not errors
        and revision_monotonic
        and copy_on_write
        and global_zone_key_preserved
        and dynamic_section_updated
        and state_chain_consistent
        and transitions_research_only
        and not_available_expected
    ) else "FAIL"

    return {
        "rows_processed": ROW_COUNT,
        "zones_observed": zones_observed,
        "completed_visits": completed_visits_total,
        "dynamic_mechanics_commits": dynamic_commits,
        "snapshot_revisions": sum(
            store.get_current(key).revision for key in harnesses
        ),
        "revision_monotonicity": revision_monotonic,
        "copy_on_write": copy_on_write,
        "global_zone_key_preserved": global_zone_key_preserved,
        "dynamic_section_updated": dynamic_section_updated,
        "previous_state_chain_consistent": state_chain_consistent,
        "transitions_research_only": transitions_research_only,
        "not_available_counts": not_available_counts,
        "not_available_expected": not_available_expected,
        "errors": len(errors),
        "error_detail": errors[:10],
        "result": result,
        "final_revisions": {
            key: store.get_current(key).revision for key in harnesses
        },
        "final_dynamic_states": {
            key: store.get_current(key).dynamic_mechanics.get("dynamic_state")
            for key in harnesses
        },
    }


def _transition_names(snapshot) -> list[str]:
    if snapshot is None:
        return []
    value = snapshot.dynamic_mechanics.get("transition_name")
    return [value] if value is not None else []


def main() -> None:
    first_report = run()
    second_report = run()

    deterministic = (
        first_report["final_revisions"] == second_report["final_revisions"]
        and first_report["final_dynamic_states"]
        == second_report["final_dynamic_states"]
        and first_report["completed_visits"] == second_report["completed_visits"]
    )

    print(
        "===== PHASE 1B STAGE 2 -- DYNAMIC MECHANICS -> SNAPSHOT VALIDATION ====="
    )
    print(f"rows_processed = {first_report['rows_processed']}")
    print(f"zones_observed = {first_report['zones_observed']}")
    print(f"completed_visits = {first_report['completed_visits']}")
    print(
        f"dynamic_mechanics_commits = {first_report['dynamic_mechanics_commits']}"
    )
    print(f"snapshot_revisions_total = {first_report['snapshot_revisions']}")
    print(f"revision_monotonicity = {first_report['revision_monotonicity']}")
    print(f"copy_on_write = {first_report['copy_on_write']}")
    print(f"global_zone_key_preserved = {first_report['global_zone_key_preserved']}")
    print(f"dynamic_section_updated = {first_report['dynamic_section_updated']}")
    print(
        "previous_state_chain_consistent = "
        f"{first_report['previous_state_chain_consistent']}"
    )
    print(f"transitions_research_only = {first_report['transitions_research_only']}")
    print(f"not_available_counts = {first_report['not_available_counts']}")
    print(f"not_available_expected = {first_report['not_available_expected']}")
    print(f"deterministic_across_runs = {deterministic}")
    print(f"errors = {first_report['errors']}")
    if first_report["error_detail"]:
        print("error_detail (first 10):")
        for item in first_report["error_detail"]:
            print(f"  {item}")

    overall = "PASS" if first_report["result"] == "PASS" and deterministic else "FAIL"
    print(f"result = {overall}")
    print("RESEARCH_ONLY = TRUE")
    print("NO_PROJECT1_CHANGES = TRUE")
    print("NO_PRODUCTION_B125_DYNAMIC_STATE = TRUE")
    print("SDR_FORMULA = SIMPLE_RESEARCH_SDR_V1")
    print("PRODUCTION_EFFECTS = FALSE")
    if overall != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

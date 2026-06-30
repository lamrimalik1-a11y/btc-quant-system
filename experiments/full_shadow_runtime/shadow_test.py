"""End-to-end shadow runtime consolidation for the full RDM V2 shadow backbone.

One driver pushes synthetic market rows through every shadow component:

    Market Row
      -> Interaction Interpreter (interpret_in_order: row ordering guard)
      -> Event Dispatcher (identity / dedup / ordering validation)
      -> Mechanical Refresh Coordinator (RefreshPlan + dirty flags)
      -> RefreshPlan
      -> Row Mechanics / Open Visit / Last Completed Visit / Dynamic Mechanics /
         Prediction adapters (dirty-gated, mapping only)
      -> Merged Patch
      -> Canonical Snapshot (one atomic copy-on-write revision)

Shadow only: no production import, no calculations, no Dynamic State recompute,
no prediction generation, no Stage 2C, no persistence, no CSV writes.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.canonical_snapshot import SnapshotStore
from core.dynamic_mechanics_adapter import DynamicMechanicsAdapter
from core.event_dispatcher import (
    DispatchBatch,
    DispatchContext,
    EventDispatcher,
)
from core.interaction_interpreter import (
    ORDER_ACCEPTED,
    InteractionInterpreter,
)
from core.last_completed_visit_adapter import LastCompletedVisitAdapter
from core.mechanical_refresh_coordinator import RefreshPlan
from core.open_visit_adapter import OpenVisitAdapter
from core.prediction_adapter import PredictionAdapter
from core.row_mechanics_adapter import NOT_AVAILABLE, RowMechanicsAdapter


SESSION_ID = "BTCUSDT_2026-06-28_230000Z"
ZONE_ID = "RUNTIME_ZONE"
GLOBAL_KEY = f"{SESSION_ID}::{ZONE_ID}"

# Per-section dirty-flag gates (identical contract to the coordinator snapshot
# integration). Row / open use ANY; completed / dynamic / prediction use ALL.
ROW_MECHANICS_DIRTY = (
    "stress_dirty",
    "exposure_dirty",
    "fatigue_recovery_dirty",
    "health_dirty",
)
OPEN_VISIT_DIRTY = ("interaction_dirty",)
COMPLETED_VISIT_DIRTY = ("visit_dirty", "response_dirty")
DYNAMIC_DIRTY = ("response_dirty", "state_dirty")
PREDICTION_DIRTY = ("trajectory_dirty", "prediction_dirty")


def _any(plan: RefreshPlan, flags) -> bool:
    return any(getattr(plan.dirty_flags, flag) for flag in flags)


def _all(plan: RefreshPlan, flags) -> bool:
    return all(getattr(plan.dirty_flags, flag) for flag in flags)


def apply_refresh_adapters(
    store,
    plan,
    *,
    row=None,
    open_visit=None,
    completed_visit=None,
    dynamic_mechanics=None,
    prediction=None,
    seed_patches=(),
    row_adapter=None,
    open_visit_adapter=None,
    completed_visit_adapter=None,
    dynamic_mechanics_adapter=None,
    prediction_adapter=None,
):
    """Build every dirty-gated patch, then publish one atomic snapshot revision."""
    patches = []

    if _any(plan, ROW_MECHANICS_DIRTY):
        if row is None:
            raise ValueError("row mechanics input required by RefreshPlan")
        patches.append((row_adapter or RowMechanicsAdapter()).build_patch(row))

    if _any(plan, OPEN_VISIT_DIRTY):
        if open_visit is None:
            raise ValueError("open visit input required by RefreshPlan")
        patches.append(
            (open_visit_adapter or OpenVisitAdapter()).build_patch(open_visit)
        )

    if _all(plan, COMPLETED_VISIT_DIRTY):
        if completed_visit is None:
            raise ValueError("completed visit input required by RefreshPlan")
        patches.append(
            (completed_visit_adapter or LastCompletedVisitAdapter()).build_patch(
                completed_visit
            )
        )

    if _all(plan, DYNAMIC_DIRTY):
        if dynamic_mechanics is None:
            raise ValueError("dynamic mechanics input required by RefreshPlan")
        patches.append(
            (dynamic_mechanics_adapter or DynamicMechanicsAdapter()).build_patch(
                dynamic_mechanics
            )
        )

    if _all(plan, PREDICTION_DIRTY):
        # B11 is asynchronous to its VISIT_COMPLETED trigger: a missing input
        # maps a PENDING / NOT_AVAILABLE section instead of aborting the commit.
        prediction_input = (
            prediction
            if prediction is not None
            else {"prediction_status": "PENDING"}
        )
        patches.append(
            (prediction_adapter or PredictionAdapter()).build_patch(
                prediction_input
            )
        )

    if not patches:
        return None, ()

    sections = [next(iter(patch)) for patch in patches]
    assert len(sections) == len(set(sections))
    merged = tuple(patches)

    if store.get_current(GLOBAL_KEY) is None:
        snapshot = store.create(
            plan, (*seed_patches, *merged), global_zone_key=GLOBAL_KEY
        )
    else:
        snapshot = store.update(plan, merged, global_zone_key=GLOBAL_KEY)
    return snapshot, merged


class FailingOpenVisitAdapter:
    def build_patch(self, _visit):
        raise RuntimeError("synthetic open-visit adapter failure")


# --------------------------------------------------------------------------- #
# Runtime harness + per-row driver (the full backbone).
# --------------------------------------------------------------------------- #
@dataclass
class RowOutcome:
    accepted: bool
    status: str
    dispatched: bool
    plan: Any
    event_types: tuple
    snapshot: Any
    patches: tuple


class Runtime:
    def __init__(self) -> None:
        self.interpreter = InteractionInterpreter(
            zone_id=ZONE_ID,
            lower_edge=100.0,
            upper_edge=110.0,
            touch_tolerance=0.25,
        )
        self.dispatcher = EventDispatcher()
        self.store = SnapshotStore()
        self.state = self.interpreter.initial_state()
        self.plan_count = 0


def run_row(
    rt: Runtime,
    *,
    row_index,
    timestamp,
    price,
    return_eligible=False,
    seed_patches=(),
    **adapter_inputs,
) -> RowOutcome:
    """Drive one market row through the complete shadow backbone."""
    current = rt.store.get_current(GLOBAL_KEY)

    # 1. Interaction Interpreter with the Row Ordering guard.
    result = rt.interpreter.interpret_in_order(
        rt.state,
        row_index=row_index,
        timestamp=timestamp,
        price=price,
        return_eligible=return_eligible,
    )
    if result.status != ORDER_ACCEPTED:
        # Rejected row: no state change, no events, dispatcher/coordinator
        # skipped, snapshot unchanged.
        return RowOutcome(
            accepted=False,
            status=result.status,
            dispatched=False,
            plan=None,
            event_types=(),
            snapshot=current,
            patches=(),
        )

    rt.state = result.state
    events = result.events
    if not events:
        # Accepted but silent: no refresh, snapshot unchanged.
        return RowOutcome(
            accepted=True,
            status="ACCEPTED_NO_EVENTS",
            dispatched=False,
            plan=None,
            event_types=(),
            snapshot=current,
            patches=(),
        )

    # 2. Event Dispatcher -> Mechanical Refresh Coordinator -> RefreshPlan.
    context = DispatchContext(
        session_id=SESSION_ID,
        zone_id=ZONE_ID,
        row_index=row_index,
        timestamp=timestamp,
        global_zone_key=GLOBAL_KEY,
    )
    batch = DispatchBatch.from_events(context, rt.state, events)
    dispatch_result = rt.dispatcher.dispatch(batch)
    assert dispatch_result.status == "DISPATCHED_SHADOW", (
        dispatch_result.status,
        dispatch_result.error_code,
        dispatch_result.error_message,
    )
    plan = dispatch_result.coordinator_result.plan
    rt.plan_count += 1  # exactly one RefreshPlan per accepted, event-emitting row

    # 3. Adapters (dirty-gated) -> merged patch -> one atomic snapshot revision.
    snapshot, patches = apply_refresh_adapters(
        rt.store, plan, seed_patches=seed_patches, **adapter_inputs
    )
    return RowOutcome(
        accepted=True,
        status="DISPATCHED_SHADOW",
        dispatched=True,
        plan=plan,
        event_types=plan.event_types,
        snapshot=snapshot,
        patches=patches,
    )


# --------------------------------------------------------------------------- #
# Synthetic, already-computed input rows (mapping inputs only).
# --------------------------------------------------------------------------- #
def make_row(row_index, price, penetration):
    return {
        "price": price,
        "timestamp": f"ROW_{row_index}",
        "row_index": row_index,
        "inside_zone_flag": True,
        "zone_touch_flag": True,
        "distance_to_zone": 0.0,
        "zone_penetration_depth": penetration,
        "fleche_live": 0.4,
        "sigma_live": 18.5,
        "sigma_barre_zone": 24.0,
        "load_live": 38.0,
        "omega_stress_area": 91.0,
        "fatigue_live": 27.0,
        "recovery_live": 0.22,
        "rigidity_live": 73.0,
        "capacity_live": 68.0,
        "health_live": 81.0,
    }


def make_open_visit(visit_id, count, penetration, last_row_id):
    return {
        "visit_id": visit_id,
        "visit_status": "OPEN",
        "current_row_count": count,
        "max_penetration": penetration,
        "cumulative_omega": 110.0,
        "pressure_accumulation": 76.0,
        "attacker_force_current": 38.0,
        "inside_zone": True,
        "touch_active": True,
        "last_row_id": last_row_id,
    }


def make_completed(visit_id):
    return {
        "visit_id": visit_id,
        "visit_start_row": 5,
        "visit_end_row": 6,
        "visit_duration": 2,
        "visit_row_count": 2,
        "max_penetration": 5.0,
        "omega_at_visit": 110.0,
        "attacker_force_at_visit": 38.0,
        "health_at_visit": 80.0,
        "rigidity_at_visit": 73.0,
        "capacity_at_visit": 68.0,
        "fatigue_at_visit": 27.0,
        "recovery_at_visit": 0.22,
        "visit_result": "REFLECTION",
        "visit_classification": "PRECOMPUTED_REFLECTION",
        "reflection_flag": True,
    }


def make_dynamic(visit_id, state, sdr, visit_index):
    return {
        "visit_id": visit_id,
        "dynamic_state": state,
        "previous_dynamic_state": "RECOVERING",
        "transition_name": f"RECOVERING_TO_{state}",
        "first_derivative": 2.0,
        "second_derivative": 0.5,
        "zone_integral": 330.0,
        "attacker_integral": 280.0,
        "SDR": sdr,
        "health_slope": 1.25,
        "health_total_change": 7.0,
        "omega_total": 306.0,
        "omega_mean": 102.0,
        "dynamic_state_as_of_visit": visit_index,
        "dynamic_updated_at": "2026-06-28T00:00:20Z",
    }


def make_prediction(visit_id, status, visit_index):
    return {
        "structural_trajectory": "STABLE",
        "trajectory_direction": "HOLD",
        "trajectory_reason": "PRECOMPUTED_B10_REASON",
        "trajectory_confidence": "HIGH",
        "structural_prediction": "LIKELY_HOLD",
        "prediction_reason": "PRECOMPUTED_B11_REASON",
        "prediction_confidence": "MEDIUM",
        "prediction_version": "B11_V1",
        "emit_status": status,
        "dynamic_state": "STABLE",
        "visit_id": visit_id,
        "visit_index": visit_index,
        "analysis_run_utc": "2026-06-28T00:00:21Z",
    }


def main() -> None:
    rt = Runtime()
    V1 = "RUNTIME_ZONE:V000001"
    V2 = "RUNTIME_ZONE:V000002"

    # ===================== Scenario 1: simple row updates ==================== #
    o5 = run_row(
        rt,
        row_index=5,
        timestamp="T5",
        price=105.0,
        row=make_row(5, 105.0, 5.0),
        open_visit=make_open_visit(V1, 1, 5.0, 5),
        seed_patches=({"metadata": {"session_id": SESSION_ID}},),
    )
    assert o5.dispatched and o5.snapshot.revision == 1
    assert o5.snapshot.current_row_mechanics["row_id"] == 5
    assert o5.snapshot.open_visit["visit_id"] == V1
    assert {s for patch in o5.patches for s in patch} == {
        "current_row_mechanics",
        "open_visit",
    }
    rev1 = o5.snapshot  # retained for copy-on-write check
    assert o5.snapshot.global_zone_key == GLOBAL_KEY
    assert o5.snapshot.source_plan_id == o5.plan.plan_id
    assert o5.snapshot.current_row_mechanics["adapter_mode"] == "SHADOW_MAPPING_ONLY"

    o6 = run_row(
        rt,
        row_index=6,
        timestamp="T6",
        price=107.0,
        row=make_row(6, 107.0, 3.0),
        open_visit=make_open_visit(V1, 2, 7.0, 6),
    )
    assert o6.snapshot.revision == 2
    assert o6.snapshot.current_row_mechanics["row_id"] == 6
    assert o6.snapshot.open_visit["current_row_count"] == 2

    # Row 7 exits the zone (ZONE_EXIT -> open visit only).
    o7 = run_row(
        rt,
        row_index=7,
        timestamp="T7",
        price=111.0,
        open_visit=make_open_visit(V1, 2, 7.0, 7),
    )
    assert "ZONE_EXIT" in o7.event_types
    assert o7.snapshot.revision == 3

    # Row 8 is accepted but silent (no events) -> no refresh.
    o8 = run_row(rt, row_index=8, timestamp="T8", price=112.0)
    assert o8.accepted and o8.status == "ACCEPTED_NO_EVENTS"
    assert not o8.dispatched
    assert rt.store.get_current(GLOBAL_KEY).revision == 3

    # ============ Scenario 2: VISIT_COMPLETED with prediction data =========== #
    o9 = run_row(
        rt,
        row_index=9,
        timestamp="T9",
        price=113.0,
        completed_visit=make_completed(V1),
        dynamic_mechanics=make_dynamic(V1, "STABLE", 0.8485, 1),
        prediction=make_prediction(V1, "FINALIZED", 1),
    )
    assert o9.event_types == ("VISIT_COMPLETED",)
    assert o9.snapshot.revision == 4
    assert {s for patch in o9.patches for s in patch} == {
        "last_completed_visit",
        "dynamic_mechanics",
        "prediction",
    }
    assert o9.snapshot.last_completed_visit["visit_id"] == V1
    assert o9.snapshot.dynamic_mechanics["dynamic_state"] == "STABLE"
    assert o9.snapshot.dynamic_mechanics["SDR"] == 0.8485
    assert o9.snapshot.prediction["b11_prediction"] == "LIKELY_HOLD"
    assert o9.snapshot.prediction["prediction_status"] == "FINALIZED"
    assert o9.snapshot.prediction["adapter_mode"] == "SHADOW_MAPPING_ONLY"
    assert o9.snapshot.source_plan_id == o9.plan.plan_id
    # Row Mechanics / Open Visit carried over unchanged (copy-on-write merge).
    assert o9.snapshot.current_row_mechanics["row_id"] == 6

    # ============ Scenario 3: VISIT_COMPLETED with prediction pending ======== #
    o10 = run_row(
        rt,
        row_index=10,
        timestamp="T10",
        price=106.0,
        row=make_row(10, 106.0, 4.0),
        open_visit=make_open_visit(V2, 1, 4.0, 10),
    )
    assert "RETURN" in o10.event_types
    assert o10.snapshot.revision == 5

    o11 = run_row(
        rt,
        row_index=11,
        timestamp="T11",
        price=111.0,
        open_visit=make_open_visit(V2, 1, 4.0, 11),
    )
    assert "ZONE_EXIT" in o11.event_types
    assert o11.snapshot.revision == 6

    o12 = run_row(rt, row_index=12, timestamp="T12", price=112.0)
    assert o12.status == "ACCEPTED_NO_EVENTS"

    o13 = run_row(
        rt,
        row_index=13,
        timestamp="T13",
        price=113.0,
        completed_visit=make_completed(V2),
        dynamic_mechanics=make_dynamic(V2, "STABLE", 0.9, 2),
        # No prediction input -> B11 pending.
    )
    assert o13.event_types == ("VISIT_COMPLETED",)
    assert o13.snapshot.revision == 7
    # Prediction is PENDING / NOT_AVAILABLE...
    assert o13.snapshot.prediction["prediction_status"] == "PENDING"
    assert o13.snapshot.prediction["b11_prediction"] == NOT_AVAILABLE
    assert o13.snapshot.prediction["b10_trajectory"] == NOT_AVAILABLE
    # ...but Completed Visit and Dynamic Mechanics still committed.
    assert o13.snapshot.last_completed_visit["visit_id"] == V2
    assert o13.snapshot.dynamic_mechanics["dynamic_state"] == "STABLE"

    authoritative = rt.store.get_current(GLOBAL_KEY)
    assert authoritative.revision == 7

    # =================== Scenario 5: duplicate row rejected ================== #
    dup = run_row(rt, row_index=13, timestamp="T13_DUP", price=113.0)
    assert not dup.accepted and dup.status == "ROW_DUPLICATE"
    assert not dup.dispatched
    assert rt.store.get_current(GLOBAL_KEY) is authoritative
    assert rt.store.get_current(GLOBAL_KEY).revision == 7

    # ================== Scenario 6: out-of-order row rejected ================ #
    ooo = run_row(rt, row_index=9, timestamp="T9_OOO", price=105.0)
    assert not ooo.accepted and ooo.status == "ROW_OUT_OF_ORDER"
    assert not ooo.dispatched
    assert rt.store.get_current(GLOBAL_KEY) is authoritative
    assert rt.store.get_current(GLOBAL_KEY).revision == 7

    # ============= Scenario 4: injected adapter failure (no commit) ========== #
    plans_before_failure = rt.plan_count
    try:
        run_row(
            rt,
            row_index=14,
            timestamp="T14",
            price=105.0,
            row=make_row(14, 105.0, 5.0),
            open_visit=make_open_visit("RUNTIME_ZONE:V000003", 1, 5.0, 14),
            open_visit_adapter=FailingOpenVisitAdapter(),
        )
    except RuntimeError as error:
        assert "synthetic open-visit adapter failure" in str(error)
    else:
        raise AssertionError("Injected adapter failure was not raised")
    # The plan was created (row 14 accepted + dispatched) but no snapshot
    # committed: the previous revision remains authoritative.
    assert rt.plan_count == plans_before_failure + 1
    assert rt.store.get_current(GLOBAL_KEY) is authoritative
    assert rt.store.get_current(GLOBAL_KEY).revision == 7

    # ============================ Cross-cutting ============================== #
    # Copy-on-write: the very first revision object is still intact.
    assert rev1.revision == 1
    assert rev1.current_row_mechanics["row_id"] == 5
    assert rev1.open_visit["visit_id"] == V1
    # One RefreshPlan per accepted, event-emitting row (5,6,7,9,10,11,13,14 = 8).
    assert rt.plan_count == 8
    # 7 atomic revisions committed (row 14's was rolled back by the failure).
    assert rt.store.get_current(GLOBAL_KEY).revision == 7

    print("FULL_SHADOW_RUNTIME_CONSOLIDATION_TEST = PASS")
    print("SCENARIO_1_ROW_MECHANICS", o6.snapshot.current_row_mechanics["row_id"])
    print("SCENARIO_1_OPEN_VISIT", o6.snapshot.open_visit["current_row_count"])
    print("SCENARIO_2_COMPLETED_VISIT", o9.snapshot.last_completed_visit["visit_id"])
    print("SCENARIO_2_DYNAMIC_STATE", o9.snapshot.dynamic_mechanics["dynamic_state"])
    print("SCENARIO_2_PREDICTION", o9.snapshot.prediction["prediction_status"])
    print("SCENARIO_3_PREDICTION", o13.snapshot.prediction["prediction_status"])
    print("SCENARIO_3_COMPLETED_STILL_COMMITS", o13.snapshot.last_completed_visit["visit_id"])
    print("SCENARIO_4_FAILURE_AUTHORITATIVE_REVISION", rt.store.get_current(GLOBAL_KEY).revision)
    print("SCENARIO_5_DUPLICATE_STATUS", dup.status)
    print("SCENARIO_6_OUT_OF_ORDER_STATUS", ooo.status)
    print("REFRESH_PLANS_CREATED", rt.plan_count)
    print("FINAL_REVISION", rt.store.get_current(GLOBAL_KEY).revision)
    print("COPY_ON_WRITE_REV1_INTACT", rev1.revision == 1 and rev1.current_row_mechanics["row_id"] == 5)
    print("GLOBAL_ZONE_KEY", o9.snapshot.global_zone_key)
    print("SOURCE_PLAN_ID_PRESERVED", o9.snapshot.source_plan_id == o9.plan.plan_id)
    print("NO_CALCULATIONS = TRUE")
    print("NO_PREDICTION_GENERATION = TRUE")
    print("NO_DYNAMIC_STATE_RECOMPUTATION = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

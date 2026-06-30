"""Shadow integration: Coordinator -> Row Mechanics Adapter -> Canonical Snapshot.

When a RefreshPlan carries row-level / current-row dirty flags, the Row Mechanics
Adapter patch is applied into the Canonical Snapshot shadow store. This wires
three already-built shadow components end to end:

    MechanicalRefreshCoordinator.create_plan  (produces RefreshPlan + dirty flags)
        -> RowMechanicsAdapter.build_patch     (maps existing row values)
        -> SnapshotStore.create / update       (immutable copy-on-write revision)

Shadow only: no production import, no calculations, no Dynamic State, no B10/B11,
no Stage 2C, no dashboard, no CSV writes, no persistence.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.canonical_snapshot import SnapshotStore
from core.interaction_interpreter import InteractionInterpreter
from core.dynamic_mechanics_adapter import DynamicMechanicsAdapter
from core.last_completed_visit_adapter import LastCompletedVisitAdapter
from core.mechanical_refresh_coordinator import (
    MechanicalRefreshCoordinator,
    RefreshDirtyFlags,
    RefreshPlan,
)
from core.open_visit_adapter import OpenVisitAdapter
from core.prediction_adapter import PredictionAdapter
from core.row_mechanics_adapter import NOT_AVAILABLE, RowMechanicsAdapter


GLOBAL_KEY = "BTCUSDT_2026-06-28_230000Z::COORD_SNAPSHOT_ZONE"

# The row-level / current-row mechanical dirty flags that gate this integration.
# Set by TOUCH (stress) and PENETRATION_UPDATED (stress/exposure/fatigue/health);
# NOT set by VISIT_COMPLETED-style downstream events.
ROW_MECHANICS_DIRTY_FLAGS = (
    "stress_dirty",
    "exposure_dirty",
    "fatigue_recovery_dirty",
    "health_dirty",
)
OPEN_VISIT_DIRTY_FLAGS = ("interaction_dirty",)
COMPLETED_VISIT_DIRTY_FLAGS = ("visit_dirty", "response_dirty")
DYNAMIC_MECHANICS_DIRTY_FLAGS = ("response_dirty", "state_dirty")
# Prediction runs after Dynamic Mechanics; gated by ALL(trajectory_dirty,
# prediction_dirty) to encode the B10 trajectory -> B11 prediction dependency.
PREDICTION_DIRTY_FLAGS = ("trajectory_dirty", "prediction_dirty")


def plan_has_row_mechanics(plan: RefreshPlan) -> bool:
    return any(
        getattr(plan.dirty_flags, flag) for flag in ROW_MECHANICS_DIRTY_FLAGS
    )


def apply_row_mechanics(store, plan, row, *, seed_patches=()):
    """The shadow integration step under test.

    Only when the plan carries row-mechanics dirty flags does it run the adapter
    and apply the patch to the snapshot store (create first, then update).
    Returns the published snapshot, or None when the plan is skipped.
    """
    if not plan_has_row_mechanics(plan):
        return None
    row_patch = RowMechanicsAdapter().build_patch(row)
    if store.get_current(GLOBAL_KEY) is None:
        return store.create(
            plan, (*seed_patches, row_patch), global_zone_key=GLOBAL_KEY
        )
    return store.update(plan, (row_patch,), global_zone_key=GLOBAL_KEY)


def plan_has_open_visit(plan: RefreshPlan) -> bool:
    return any(
        getattr(plan.dirty_flags, flag) for flag in OPEN_VISIT_DIRTY_FLAGS
    )


def apply_row_and_open_visit(
    store,
    plan,
    row,
    visit,
    *,
    seed_patches=(),
    open_visit_adapter=None,
):
    """Build both independent patches, then publish one atomic revision."""
    if not plan_has_row_mechanics(plan) or not plan_has_open_visit(plan):
        return None, ()

    row_patch = RowMechanicsAdapter().build_patch(row)
    visit_adapter = open_visit_adapter or OpenVisitAdapter()
    visit_patch = visit_adapter.build_patch(visit)
    assert set(row_patch).isdisjoint(visit_patch)
    merged_patches = (row_patch, visit_patch)

    if store.get_current(GLOBAL_KEY) is None:
        snapshot = store.create(
            plan,
            (*seed_patches, *merged_patches),
            global_zone_key=GLOBAL_KEY,
        )
    else:
        snapshot = store.update(
            plan,
            merged_patches,
            global_zone_key=GLOBAL_KEY,
        )
    return snapshot, merged_patches


class FailingOpenVisitAdapter:
    def build_patch(self, _visit):
        raise RuntimeError("synthetic open-visit adapter failure")
def plan_has_completed_visit(plan: RefreshPlan) -> bool:
    return all(
        getattr(plan.dirty_flags, flag)
        for flag in COMPLETED_VISIT_DIRTY_FLAGS
    )

def plan_has_dynamic_mechanics(plan: RefreshPlan) -> bool:
    return all(
        getattr(plan.dirty_flags, flag)
        for flag in DYNAMIC_MECHANICS_DIRTY_FLAGS
    )


def plan_has_prediction(plan: RefreshPlan) -> bool:
    return all(
        getattr(plan.dirty_flags, flag)
        for flag in PREDICTION_DIRTY_FLAGS
    )


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
    """Build every dirty-gated patch before one atomic store publication."""
    patches = []

    if plan_has_row_mechanics(plan):
        if row is None:
            raise ValueError("row mechanics input required by RefreshPlan")
        patches.append(
            (row_adapter or RowMechanicsAdapter()).build_patch(row)
        )

    if plan_has_open_visit(plan):
        if open_visit is None:
            raise ValueError("open visit input required by RefreshPlan")
        patches.append(
            (open_visit_adapter or OpenVisitAdapter()).build_patch(
                open_visit
            )
        )

    if plan_has_completed_visit(plan):
        if completed_visit is None:
            raise ValueError("completed visit input required by RefreshPlan")
        patches.append(
            (
                completed_visit_adapter
                or LastCompletedVisitAdapter()
            ).build_patch(completed_visit)
        )

    if plan_has_dynamic_mechanics(plan):
        if dynamic_mechanics is None:
            raise ValueError("dynamic mechanics input required by RefreshPlan")
        patches.append(
            (
                dynamic_mechanics_adapter
                or DynamicMechanicsAdapter()
            ).build_patch(dynamic_mechanics)
        )

    if plan_has_prediction(plan):
        # B11 prediction is asynchronous to its VISIT_COMPLETED trigger. If the
        # prediction data is missing / B11 is pending, do NOT abort the atomic
        # update: map a PENDING / NOT_AVAILABLE prediction section instead, so
        # the ready sections (row/open/completed/dynamic) still commit. An
        # adapter that itself raises an unexpected error is NOT swallowed -- it
        # propagates and blocks the whole revision (no partial commit), matching
        # every other section's failure contract.
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

    section_names = [next(iter(patch)) for patch in patches]
    assert len(section_names) == len(set(section_names))
    merged_patches = tuple(patches)

    if store.get_current(GLOBAL_KEY) is None:
        snapshot = store.create(
            plan,
            (*seed_patches, *merged_patches),
            global_zone_key=GLOBAL_KEY,
        )
    else:
        snapshot = store.update(
            plan,
            merged_patches,
            global_zone_key=GLOBAL_KEY,
        )
    return snapshot, merged_patches


class FailingCompletedVisitAdapter:
    def build_patch(self, _visit):
        raise RuntimeError("synthetic completed-visit adapter failure")

class FailingDynamicMechanicsAdapter:
    def build_patch(self, _timeline_row):
        raise RuntimeError("synthetic dynamic-mechanics adapter failure")

class FailingPredictionAdapter:
    def build_patch(self, _prediction_row):
        raise RuntimeError("synthetic prediction adapter failure")


def main() -> None:
    interpreter = InteractionInterpreter(
        zone_id="COORD_SNAPSHOT_ZONE",
        lower_edge=100.0,
        upper_edge=110.0,
        touch_tolerance=0.25,
    )
    coordinator = MechanicalRefreshCoordinator()
    store = SnapshotStore()

    # --- Row 1: enters the zone -> plan carries row-mechanics dirty flags. ---
    state1, events1 = interpreter.interpret(
        interpreter.initial_state(),
        row_index=5,
        timestamp="2026-06-28T00:00:05Z",
        price=105.0,
    )
    plan1 = coordinator.create_plan(state1, events1)
    assert plan_has_row_mechanics(plan1), plan1.dirty_flags.active_names()

    row1 = {
        "price": 70180.0,
        "timestamp": "2026-06-28T00:10:00Z",
        "row_index": 1000,
        "inside_zone_flag": True,
        "zone_touch_flag": True,
        "distance_to_zone": 0.0,
        "zone_penetration_depth": 80.0,
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
    snap1 = apply_row_mechanics(
        store,
        plan1,
        row1,
        seed_patches=(
            {"metadata": {"session_id": "BTCUSDT_2026-06-28_230000Z"}},
        ),
    )
    assert snap1 is not None
    assert snap1.revision == 1
    # (6) current_row_mechanics section contains the mapped fields.
    crm1 = snap1.current_row_mechanics
    assert crm1["price"] == 70180.0
    assert crm1["row_id"] == 1000                  # from row_index alias
    assert crm1["penetration_depth"] == 80.0       # from zone_penetration_depth
    assert crm1["sigma_market_live"] == 18.5       # from sigma_live alias
    assert crm1["sigma_barre_zone_live"] == 24.0   # from sigma_barre_zone alias
    assert crm1["fatigue_live"] == 27.0
    assert crm1["health_live"] == 81.0
    assert crm1["source_fields"]["row_id"] == "row_index"
    assert crm1["adapter_mode"] == "SHADOW_MAPPING_ONLY"
    # The plan identity flowed into the snapshot provenance.
    assert snap1.source_plan_id == plan1.plan_id
    assert snap1.zone_id == "COORD_SNAPSHOT_ZONE"

    # --- Row 2: deeper penetration -> still row-mechanics dirty; updates. ---
    state2, events2 = interpreter.interpret(
        state1,
        row_index=6,
        timestamp="2026-06-28T00:00:06Z",
        price=107.0,
    )
    plan2 = coordinator.create_plan(state2, events2)
    assert plan_has_row_mechanics(plan2), plan2.dirty_flags.active_names()

    row2 = dict(row1)
    row2.update(
        {
            "timestamp": "2026-06-28T00:10:01Z",
            "row_index": 1001,
            "zone_penetration_depth": 110.0,
            "health_live": 80.0,
        }
    )
    snap2 = apply_row_mechanics(store, plan2, row2)
    # (5) snapshot revision increments.
    assert snap2.revision == 2
    assert snap2.current_row_mechanics["row_id"] == 1001
    assert snap2.current_row_mechanics["penetration_depth"] == 110.0
    assert snap2.current_row_mechanics["health_live"] == 80.0
    # Prior immutable revision is preserved (copy-on-write).
    assert snap1.revision == 1
    assert snap1.current_row_mechanics["row_id"] == 1000
    assert store.get_current(GLOBAL_KEY) is snap2

    # --- Negative control: a synthetic plan WITHOUT row-mechanics dirty flags
    #     (downstream visit/snapshot only) is correctly skipped. ---
    no_row_plan = RefreshPlan(
        plan_id="SHADOW:COORD_SNAPSHOT_ZONE:NO_ROW_MECHANICS",
        zone_id="COORD_SNAPSHOT_ZONE",
        event_ids=("COORD_SNAPSHOT_ZONE:7:VISIT_COMPLETED:01",),
        event_types=("VISIT_COMPLETED",),
        dirty_flags=RefreshDirtyFlags(visit_dirty=True, snapshot_dirty=True),
        execution_order=("visit_refresh", "snapshot_refresh"),
        audit_trace=("synthetic_no_row_mechanics",),
    )
    assert not plan_has_row_mechanics(no_row_plan)
    skipped = apply_row_mechanics(store, no_row_plan, row2)
    assert skipped is None
    # Snapshot is untouched: still revision 2, still the row-2 values.
    assert store.get_current(GLOBAL_KEY) is snap2
    assert store.get_current(GLOBAL_KEY).revision == 2

    # --- Multi-adapter integration: two patches, one atomic commit. ---
    multi_store = SnapshotStore()
    visit1 = {
        "visit_id": "COORD_SNAPSHOT_ZONE:V000001",
        "visit_status": "OPEN",
        "visit_start_row": 5,
        "visit_start_timestamp": "2026-06-28T00:00:05Z",
        "visit_start_price": 105.0,
        "current_row_count": 1,
        "max_penetration": 5.0,
        "cumulative_omega": 91.0,
        "pressure_accumulation": 38.0,
        "attacker_force_current": 38.0,
        "inside_zone": True,
        "touch_active": True,
        "last_event_id": plan1.event_ids[-1],
        "last_row_id": 1000,
    }
    multi1, merged1 = apply_row_and_open_visit(
        multi_store,
        plan1,
        row1,
        visit1,
        seed_patches=(
            {"metadata": {"session_id": "BTCUSDT_2026-06-28_230000Z"}},
        ),
    )
    assert multi1 is not None
    assert multi1.revision == 1
    assert len(merged1) == 2
    assert set(merged1[0]) == {"current_row_mechanics"}
    assert set(merged1[1]) == {"open_visit"}
    assert set(merged1[0]).isdisjoint(merged1[1])
    assert multi1.current_row_mechanics["row_id"] == 1000
    assert multi1.open_visit["visit_id"] == "COORD_SNAPSHOT_ZONE:V000001"
    assert multi1.global_zone_key == GLOBAL_KEY
    assert multi1.source_plan_id == plan1.plan_id
    assert multi1.current_row_mechanics["adapter_mode"] == "SHADOW_MAPPING_ONLY"
    assert multi1.open_visit["adapter_mode"] == "SHADOW_MAPPING_ONLY"
    assert multi1.current_row_mechanics["source_fields"]["row_id"] == "row_index"
    assert multi1.open_visit["source_fields"]["visit_id"] == "visit_id"

    visit2 = dict(visit1)
    visit2.update(
        {
            "current_row_count": 2,
            "max_penetration": 7.0,
            "cumulative_omega": 110.0,
            "last_event_id": plan2.event_ids[-1],
            "last_row_id": 1001,
        }
    )
    multi2, merged2 = apply_row_and_open_visit(
        multi_store,
        plan2,
        row2,
        visit2,
    )
    assert multi2.revision == multi1.revision + 1
    assert multi2.current_row_mechanics["row_id"] == 1001
    assert multi2.open_visit["current_row_count"] == 2
    assert multi2.global_zone_key == GLOBAL_KEY
    assert multi2.source_plan_id == plan2.plan_id
    assert multi1.revision == 1
    assert multi1.current_row_mechanics["row_id"] == 1000
    assert multi1.open_visit["current_row_count"] == 1
    assert len(merged2) == 2

    # Skip control: row mechanics is dirty, but Open Visit is not.
    no_open_plan = RefreshPlan(
        plan_id="SHADOW:COORD_SNAPSHOT_ZONE:NO_OPEN_VISIT",
        zone_id="COORD_SNAPSHOT_ZONE",
        event_ids=("COORD_SNAPSHOT_ZONE:8:PENETRATION_UPDATED:01",),
        event_types=("PENETRATION_UPDATED",),
        dirty_flags=RefreshDirtyFlags(
            stress_dirty=True,
            snapshot_dirty=True,
        ),
        execution_order=("stress_refresh", "snapshot_refresh"),
        audit_trace=("synthetic_no_open_visit",),
    )
    assert plan_has_row_mechanics(no_open_plan)
    assert not plan_has_open_visit(no_open_plan)
    skipped_multi, skipped_patches = apply_row_and_open_visit(
        multi_store,
        no_open_plan,
        row2,
        visit2,
    )
    assert skipped_multi is None
    assert skipped_patches == ()
    assert multi_store.get_current(GLOBAL_KEY) is multi2

    # Failure control: Row Mechanics patch is built first, then Open Visit
    # fails. No SnapshotStore.update call occurs, so no partial revision leaks.
    failing_plan = RefreshPlan(
        plan_id="SHADOW:COORD_SNAPSHOT_ZONE:OPEN_VISIT_FAILURE",
        zone_id="COORD_SNAPSHOT_ZONE",
        event_ids=("COORD_SNAPSHOT_ZONE:9:VISIT_STARTED:01",),
        event_types=("VISIT_STARTED",),
        dirty_flags=RefreshDirtyFlags(
            interaction_dirty=True,
            stress_dirty=True,
            visit_dirty=True,
            snapshot_dirty=True,
        ),
        execution_order=(
            "interaction_refresh",
            "stress_refresh",
            "visit_refresh",
            "snapshot_refresh",
        ),
        audit_trace=("synthetic_open_visit_failure",),
    )
    try:
        apply_row_and_open_visit(
            multi_store,
            failing_plan,
            row2,
            visit2,
            open_visit_adapter=FailingOpenVisitAdapter(),
        )
    except RuntimeError as error:
        assert "synthetic open-visit adapter failure" in str(error)
    else:
        raise AssertionError("Open Visit adapter failure was not raised")
    assert multi_store.get_current(GLOBAL_KEY) is multi2
    assert multi_store.get_current(GLOBAL_KEY).revision == 2
    assert multi_store.get_current(GLOBAL_KEY).current_row_mechanics["row_id"] == 1001
    assert multi_store.get_current(GLOBAL_KEY).open_visit["current_row_count"] == 2
    # --- Real VISIT_COMPLETED plan: three non-touch rows close the visit. ---
    state3, _events3 = interpreter.interpret(
        state2,
        row_index=7,
        timestamp="2026-06-28T00:00:07Z",
        price=111.0,
    )
    state4, _events4 = interpreter.interpret(
        state3,
        row_index=8,
        timestamp="2026-06-28T00:00:08Z",
        price=112.0,
    )
    state5, events5 = interpreter.interpret(
        state4,
        row_index=9,
        timestamp="2026-06-28T00:00:09Z",
        price=113.0,
    )
    completed_plan = coordinator.create_plan(state5, events5)
    assert completed_plan.event_types == ("VISIT_COMPLETED",)
    assert plan_has_completed_visit(completed_plan)
    assert not plan_has_row_mechanics(completed_plan)
    assert not plan_has_open_visit(completed_plan)
    assert plan_has_dynamic_mechanics(completed_plan)

    completed_visit1 = {
        "visit_id": "COORD_SNAPSHOT_ZONE:V000001",
        "visit_start_row": 5,
        "visit_end_row": 6,
        "visit_start_timestamp": "2026-06-28T00:00:05Z",
        "visit_end_timestamp": "2026-06-28T00:00:06Z",
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
        "absorption_flag": False,
        "reflection_flag": True,
        "reclaim_flag": False,
        "damage_flag": False,
        "growth_flag": True,
    }

    dynamic_visit1 = {
        "visit_id": "COORD_SNAPSHOT_ZONE:V000001",
        "dynamic_state": "STABLE",
        "previous_dynamic_state": "RECOVERING",
        "transition_name": "RECOVERING_TO_STABLE",
        "first_derivative": 2.0,
        "second_derivative": 0.5,
        "zone_integral": 330.0,
        "attacker_integral": 280.0,
        "SDR": 0.8485,
        "health_slope": 1.25,
        "health_total_change": 7.0,
        "omega_total": 306.0,
        "omega_mean": 102.0,
        "dynamic_state_reason": "PRECOMPUTED_DYNAMIC_REASON",
        "dynamic_state_confidence": 0.82,
        "dynamic_state_as_of_visit": 1,
        "dynamic_updated_at": "2026-06-28T00:00:10Z",
    }
    completed_store = SnapshotStore()
    completed_base, base_patches = apply_refresh_adapters(
        completed_store,
        plan1,
        row=row1,
        open_visit=visit1,
        seed_patches=(
            {"metadata": {"session_id": "BTCUSDT_2026-06-28_230000Z"}},
        ),
    )
    assert completed_base.revision == 1
    assert len(base_patches) == 2
    assert completed_base.last_completed_visit == {}

    completed1, completed_patches = apply_refresh_adapters(
        completed_store,
        completed_plan,
        completed_visit=completed_visit1,
        dynamic_mechanics=dynamic_visit1,
    )
    assert completed1.revision == completed_base.revision + 1
    # completed_plan is a real VISIT_COMPLETED -> trajectory_dirty +
    # prediction_dirty are set, but no prediction data was supplied, so a
    # PENDING prediction section commits alongside the ready sections.
    assert len(completed_patches) == 3
    assert tuple(next(iter(patch)) for patch in completed_patches) == (
        "last_completed_visit",
        "dynamic_mechanics",
        "prediction",
    )
    assert completed1.last_completed_visit["visit_id"] == (
        "COORD_SNAPSHOT_ZONE:V000001"
    )
    assert completed1.last_completed_visit["visit_result"] == "REFLECTION"
    assert completed1.last_completed_visit["adapter_mode"] == (
        "SHADOW_MAPPING_ONLY"
    )
    assert completed1.last_completed_visit["source_fields"]["visit_id"] == (
        "visit_id"
    )
    assert completed1.dynamic_mechanics["dynamic_state"] == "STABLE"
    assert completed1.dynamic_mechanics["SDR"] == 0.8485
    assert completed1.dynamic_mechanics["adapter_mode"] == (
        "SHADOW_MAPPING_ONLY"
    )
    assert completed1.dynamic_mechanics["source_fields"]["SDR"] == "SDR"
    # Pending B11: the prediction section commits as PENDING / NOT_AVAILABLE and
    # does NOT block the ready completed-visit and dynamic-mechanics sections.
    assert plan_has_prediction(completed_plan)
    assert completed1.prediction["prediction_status"] == "PENDING"
    assert completed1.prediction["b10_trajectory"] == NOT_AVAILABLE
    assert completed1.prediction["b11_prediction"] == NOT_AVAILABLE
    assert completed1.prediction["b11_confidence"] == NOT_AVAILABLE
    assert completed1.prediction["adapter_mode"] == "SHADOW_MAPPING_ONLY"
    assert completed1.global_zone_key == GLOBAL_KEY
    assert completed1.source_plan_id == completed_plan.plan_id
    assert completed_base.last_completed_visit == {}
    assert completed_base.prediction == {}

    # Row-only control: snapshot advances, completed-visit section does not.
    row_only, row_only_patches = apply_refresh_adapters(
        completed_store,
        no_open_plan,
        row=row2,
        completed_visit_adapter=FailingCompletedVisitAdapter(),
        dynamic_mechanics_adapter=FailingDynamicMechanicsAdapter(),
    )
    assert row_only.revision == completed1.revision + 1
    assert len(row_only_patches) == 1
    assert set(row_only_patches[0]) == {"current_row_mechanics"}
    assert row_only.current_row_mechanics["row_id"] == 1001
    assert row_only.last_completed_visit["visit_id"] == (
        completed1.last_completed_visit["visit_id"]
    )
    assert not plan_has_completed_visit(no_open_plan)
    assert not plan_has_dynamic_mechanics(no_open_plan)
    assert row_only.dynamic_mechanics["dynamic_state"] == (
        completed1.dynamic_mechanics["dynamic_state"]
    )
    assert row_only.dynamic_mechanics["SDR"] == completed1.dynamic_mechanics["SDR"]

    # Mixed cycle: row, open visit, and completed visit commit once.
    mixed_plan = RefreshPlan(
        plan_id="SHADOW:COORD_SNAPSHOT_ZONE:MIXED_COMPLETION",
        zone_id="COORD_SNAPSHOT_ZONE",
        event_ids=(
            "COORD_SNAPSHOT_ZONE:10:PENETRATION_UPDATED:01",
            "COORD_SNAPSHOT_ZONE:10:VISIT_COMPLETED:02",
        ),
        event_types=("PENETRATION_UPDATED", "VISIT_COMPLETED"),
        dirty_flags=RefreshDirtyFlags(
            interaction_dirty=True,
            stress_dirty=True,
            exposure_dirty=True,
            fatigue_recovery_dirty=True,
            health_dirty=True,
            visit_dirty=True,
            response_dirty=True,
            state_dirty=True,
            snapshot_dirty=True,
        ),
        execution_order=(
            "interaction_refresh",
            "stress_refresh",
            "exposure_refresh",
            "fatigue_recovery_refresh",
            "health_refresh",
            "visit_refresh",
            "response_refresh",
            "state_refresh",
            "snapshot_refresh",
        ),
        audit_trace=("synthetic_mixed_completion",),
    )
    completed_visit2 = dict(completed_visit1)
    completed_visit2.update(
        {
            "visit_id": "COORD_SNAPSHOT_ZONE:V000002",
            "visit_result": "ABSORPTION",
            "absorption_flag": True,
            "reflection_flag": False,
        }
    )
    dynamic_visit2 = dict(dynamic_visit1)
    dynamic_visit2.update(
        {
            "visit_id": "COORD_SNAPSHOT_ZONE:V000002",
            "dynamic_state": "ATTACKER_DOMINANT",
            "previous_dynamic_state": "STABLE",
            "transition_name": "STABLE_TO_ATTACKER_DOMINANT",
            "first_derivative": -4.0,
            "second_derivative": -6.0,
            "zone_integral": 402.0,
            "attacker_integral": 451.0,
            "SDR": 1.1219,
            "dynamic_state_as_of_visit": 2,
            "dynamic_updated_at": "2026-06-28T00:00:11Z",
        }
    )
    mixed, mixed_patches = apply_refresh_adapters(
        completed_store,
        mixed_plan,
        row=row2,
        open_visit=visit2,
        completed_visit=completed_visit2,
        dynamic_mechanics=dynamic_visit2,
    )
    assert mixed.revision == row_only.revision + 1
    assert tuple(next(iter(patch)) for patch in mixed_patches) == (
        "current_row_mechanics",
        "open_visit",
        "last_completed_visit",
        "dynamic_mechanics",
    )
    assert mixed.current_row_mechanics["row_id"] == 1001
    assert mixed.open_visit["current_row_count"] == 2
    assert mixed.last_completed_visit["visit_id"] == (
        "COORD_SNAPSHOT_ZONE:V000002"
    )
    assert mixed.dynamic_mechanics["dynamic_state"] == "ATTACKER_DOMINANT"
    assert mixed.dynamic_mechanics["SDR"] == 1.1219
    assert mixed.global_zone_key == GLOBAL_KEY
    assert mixed.source_plan_id == mixed_plan.plan_id

    # Failure after row/open patches are built: no partial revision commits.
    before_failure = mixed
    try:
        apply_refresh_adapters(
            completed_store,
            mixed_plan,
            row=row1,
            open_visit=visit1,
            completed_visit=completed_visit1,
            completed_visit_adapter=FailingCompletedVisitAdapter(),
        )
    except RuntimeError as error:
        assert "synthetic completed-visit adapter failure" in str(error)
    else:
        raise AssertionError("Completed Visit adapter failure was not raised")
    assert completed_store.get_current(GLOBAL_KEY) is before_failure
    assert completed_store.get_current(GLOBAL_KEY).revision == 4
    assert completed_store.get_current(GLOBAL_KEY).current_row_mechanics[
        "row_id"
    ] == 1001
    assert completed_store.get_current(GLOBAL_KEY).open_visit[
        "current_row_count"
    ] == 2
    assert completed_store.get_current(GLOBAL_KEY).last_completed_visit[
        "visit_id"
    ] == "COORD_SNAPSHOT_ZONE:V000002"

    # Dynamic failure occurs after row/open/completed patches are built.
    try:
        apply_refresh_adapters(
            completed_store,
            mixed_plan,
            row=row1,
            open_visit=visit1,
            completed_visit=completed_visit1,
            dynamic_mechanics=dynamic_visit1,
            dynamic_mechanics_adapter=FailingDynamicMechanicsAdapter(),
        )
    except RuntimeError as error:
        assert "synthetic dynamic-mechanics adapter failure" in str(error)
    else:
        raise AssertionError("Dynamic Mechanics adapter failure was not raised")
    assert completed_store.get_current(GLOBAL_KEY) is before_failure
    assert completed_store.get_current(GLOBAL_KEY).revision == 4
    assert completed_store.get_current(GLOBAL_KEY).dynamic_mechanics[
        "dynamic_state"
    ] == "ATTACKER_DOMINANT"
    assert completed_store.get_current(GLOBAL_KEY).dynamic_mechanics[
        "SDR"
    ] == 1.1219

    # ================================================================
    # Prediction integration: ALL(trajectory_dirty, prediction_dirty).
    # ================================================================
    # A prediction-only synthetic plan isolates the prediction branch.
    prediction_only_plan = RefreshPlan(
        plan_id="SHADOW:COORD_SNAPSHOT_ZONE:PREDICTION_ONLY",
        zone_id="COORD_SNAPSHOT_ZONE",
        event_ids=("COORD_SNAPSHOT_ZONE:11:VISIT_COMPLETED:01",),
        event_types=("VISIT_COMPLETED",),
        dirty_flags=RefreshDirtyFlags(
            trajectory_dirty=True,
            prediction_dirty=True,
            snapshot_dirty=True,
        ),
        execution_order=(
            "trajectory_refresh",
            "prediction_refresh",
            "snapshot_refresh",
        ),
        audit_trace=("synthetic_prediction_only",),
    )
    assert plan_has_prediction(prediction_only_plan)
    assert not plan_has_row_mechanics(prediction_only_plan)
    assert not plan_has_open_visit(prediction_only_plan)
    assert not plan_has_completed_visit(prediction_only_plan)
    assert not plan_has_dynamic_mechanics(prediction_only_plan)

    # (A) Prediction data present -> mapped normally into the prediction section.
    prediction_data = {
        "structural_trajectory": "STABLE",
        "trajectory_direction": "HOLD",
        "trajectory_reason": "PRECOMPUTED_B10_REASON",
        "trajectory_confidence": "HIGH",
        "structural_prediction": "LIKELY_HOLD",
        "b11_state": "PRECOMPUTED_B11_STATE",
        "prediction_reason": "PRECOMPUTED_B11_REASON",
        "prediction_confidence": "MEDIUM",
        "prediction_uncertainty": 0.2,
        "prediction_version": "B11_V1",
        "emit_status": "FINALIZED",
        "dynamic_state": "ATTACKER_DOMINANT",
        "visit_id": "COORD_SNAPSHOT_ZONE:V000002",
        "visit_index": 2,
        "analysis_run_utc": "2026-06-28T00:00:12Z",
    }
    pred_present, pred_present_patches = apply_refresh_adapters(
        completed_store,
        prediction_only_plan,
        prediction=prediction_data,
    )
    assert pred_present.revision == before_failure.revision + 1
    assert len(pred_present_patches) == 1
    assert set(pred_present_patches[0]) == {"prediction"}
    assert pred_present.prediction["b10_trajectory"] == "STABLE"
    assert pred_present.prediction["b11_prediction"] == "LIKELY_HOLD"
    assert pred_present.prediction["prediction_status"] == "FINALIZED"
    assert pred_present.prediction["prediction_uncertainty"] == 0.2
    assert pred_present.prediction["adapter_mode"] == "SHADOW_MAPPING_ONLY"
    assert pred_present.prediction["source_fields"]["b10_trajectory"] == (
        "structural_trajectory"
    )
    assert pred_present.global_zone_key == GLOBAL_KEY
    assert pred_present.source_plan_id == prediction_only_plan.plan_id
    # Ready sections from prior revisions are preserved (copy-on-write merge).
    assert pred_present.last_completed_visit["visit_id"] == (
        "COORD_SNAPSHOT_ZONE:V000002"
    )
    assert pred_present.dynamic_mechanics["dynamic_state"] == "ATTACKER_DOMINANT"
    assert pred_present.current_row_mechanics["row_id"] == 1001

    # (B) Prediction input missing / B11 pending -> PENDING section, no abort.
    pred_pending, pred_pending_patches = apply_refresh_adapters(
        completed_store,
        prediction_only_plan,
    )
    assert pred_pending.revision == pred_present.revision + 1
    assert len(pred_pending_patches) == 1
    assert set(pred_pending_patches[0]) == {"prediction"}
    assert pred_pending.prediction["prediction_status"] == "PENDING"
    assert pred_pending.prediction["b10_trajectory"] == NOT_AVAILABLE
    assert pred_pending.prediction["b11_prediction"] == NOT_AVAILABLE
    # Ready sections are NOT blocked by the pending prediction.
    assert pred_pending.last_completed_visit["visit_id"] == (
        "COORD_SNAPSHOT_ZONE:V000002"
    )
    assert pred_pending.dynamic_mechanics["dynamic_state"] == "ATTACKER_DOMINANT"
    assert pred_pending.current_row_mechanics["row_id"] == 1001

    # (C) Unexpected prediction adapter failure blocks the whole revision: even
    #     with ready row/open/completed/dynamic inputs, no partial commit leaks.
    full_plan = RefreshPlan(
        plan_id="SHADOW:COORD_SNAPSHOT_ZONE:FULL_PREDICTION_FAILURE",
        zone_id="COORD_SNAPSHOT_ZONE",
        event_ids=(
            "COORD_SNAPSHOT_ZONE:12:PENETRATION_UPDATED:01",
            "COORD_SNAPSHOT_ZONE:12:VISIT_COMPLETED:02",
        ),
        event_types=("PENETRATION_UPDATED", "VISIT_COMPLETED"),
        dirty_flags=RefreshDirtyFlags(
            interaction_dirty=True,
            stress_dirty=True,
            exposure_dirty=True,
            fatigue_recovery_dirty=True,
            health_dirty=True,
            visit_dirty=True,
            response_dirty=True,
            state_dirty=True,
            transition_dirty=True,
            trajectory_dirty=True,
            prediction_dirty=True,
            snapshot_dirty=True,
        ),
        execution_order=("snapshot_refresh",),
        audit_trace=("synthetic_full_prediction_failure",),
    )
    assert plan_has_row_mechanics(full_plan)
    assert plan_has_open_visit(full_plan)
    assert plan_has_completed_visit(full_plan)
    assert plan_has_dynamic_mechanics(full_plan)
    assert plan_has_prediction(full_plan)
    stable_before_pred_fail = completed_store.get_current(GLOBAL_KEY)
    try:
        apply_refresh_adapters(
            completed_store,
            full_plan,
            row=row1,
            open_visit=visit1,
            completed_visit=completed_visit1,
            dynamic_mechanics=dynamic_visit1,
            prediction=prediction_data,
            prediction_adapter=FailingPredictionAdapter(),
        )
    except RuntimeError as error:
        assert "synthetic prediction adapter failure" in str(error)
    else:
        raise AssertionError("Prediction adapter failure was not raised")
    # No partial commit: revision and all sections unchanged.
    assert completed_store.get_current(GLOBAL_KEY) is stable_before_pred_fail
    assert completed_store.get_current(GLOBAL_KEY).revision == (
        pred_pending.revision
    )
    assert completed_store.get_current(GLOBAL_KEY).prediction[
        "prediction_status"
    ] == "PENDING"

    print("COORDINATOR_SNAPSHOT_INTEGRATION_SHADOW_TEST = PASS")
    print("ROW1_PLAN_DIRTY", plan1.dirty_flags.active_names())
    print("ROW1_REVISION", snap1.revision)
    print("ROW2_REVISION", snap2.revision)
    print("MAPPED_ROW_ID", snap2.current_row_mechanics["row_id"])
    print("MAPPED_PENETRATION_DEPTH", snap2.current_row_mechanics["penetration_depth"])
    print("NO_ROW_MECHANICS_PLAN_SKIPPED", skipped is None)
    print("MULTI_ADAPTER_REVISION", multi2.revision)
    print("MERGED_SECTIONS", tuple(patch.keys() for patch in merged2))
    print("OPEN_VISIT_SKIP_PRESERVED_REVISION", skipped_multi is None)
    print("OPEN_VISIT_FAILURE_PRESERVED_REVISION", multi_store.get_current(GLOBAL_KEY) is multi2)
    print("COMPLETED_VISIT_PLAN_DIRTY", completed_plan.dirty_flags.active_names())
    print("COMPLETED_VISIT_REVISION", completed1.revision)
    print("ROW_ONLY_PRESERVED_COMPLETED_VISIT", row_only.last_completed_visit["visit_id"])
    print("MIXED_COMPLETION_REVISION", mixed.revision)
    print("COMPLETED_VISIT_FAILURE_PRESERVED_REVISION", completed_store.get_current(GLOBAL_KEY) is before_failure)
    print("DYNAMIC_MECHANICS_PLAN_DIRTY", plan_has_dynamic_mechanics(completed_plan))
    print("DYNAMIC_MECHANICS_STATE", completed1.dynamic_mechanics["dynamic_state"])
    print("ROW_ONLY_PRESERVED_DYNAMIC_STATE", row_only.dynamic_mechanics["dynamic_state"])
    print("MIXED_DYNAMIC_STATE", mixed.dynamic_mechanics["dynamic_state"])
    print("DYNAMIC_FAILURE_PRESERVED_REVISION", completed_store.get_current(GLOBAL_KEY) is before_failure)
    print("PREDICTION_PRESENT_STATUS", pred_present.prediction["prediction_status"])
    print("PREDICTION_PRESENT_B11", pred_present.prediction["b11_prediction"])
    print("PREDICTION_PENDING_STATUS", pred_pending.prediction["prediction_status"])
    print("PREDICTION_PENDING_B11", pred_pending.prediction["b11_prediction"])
    print("READY_SECTIONS_COMMIT_WHEN_PENDING", pred_pending.last_completed_visit["visit_id"])
    print("PREDICTION_FAILURE_PRESERVED_REVISION", completed_store.get_current(GLOBAL_KEY) is stable_before_pred_fail)
    print("NO_PREDICTION_GENERATION = TRUE")
    print("NO_DYNAMIC_STATE_RECOMPUTATION = TRUE")
    print("NO_CALCULATIONS = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

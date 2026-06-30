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
from core.mechanical_refresh_coordinator import (
    MechanicalRefreshCoordinator,
    RefreshDirtyFlags,
    RefreshPlan,
)
from core.row_mechanics_adapter import RowMechanicsAdapter


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

    print("COORDINATOR_SNAPSHOT_INTEGRATION_SHADOW_TEST = PASS")
    print("ROW1_PLAN_DIRTY", plan1.dirty_flags.active_names())
    print("ROW1_REVISION", snap1.revision)
    print("ROW2_REVISION", snap2.revision)
    print("MAPPED_ROW_ID", snap2.current_row_mechanics["row_id"])
    print("MAPPED_PENETRATION_DEPTH", snap2.current_row_mechanics["penetration_depth"])
    print("NO_ROW_MECHANICS_PLAN_SKIPPED", skipped is None)
    print("NO_CALCULATIONS = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

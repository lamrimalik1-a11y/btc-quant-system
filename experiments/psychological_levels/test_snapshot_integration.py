"""Offline Psychological Levels to Canonical Snapshot validation."""

from __future__ import annotations

import sys
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_DIR = Path(__file__).resolve().parent
for path in (REPO_ROOT, EXPERIMENT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.canonical_snapshot import SNAPSHOT_SECTIONS, SnapshotStore
from core.dynamic_mechanics_adapter import DynamicMechanicsAdapter
from core.event_dispatcher import (
    DispatchBatch,
    DispatchContext,
    EventDispatcher,
)
from core.interaction_interpreter import (
    AUDIT_ROW_DUPLICATE,
    ORDER_ACCEPTED,
    InteractionInterpreter,
)
from core.last_completed_visit_adapter import LastCompletedVisitAdapter
from core.open_visit_adapter import OpenVisitAdapter
from core.prediction_adapter import PredictionAdapter
from core.row_mechanics_adapter import NOT_AVAILABLE, RowMechanicsAdapter
from provider import GEOMETRY_SOURCE, PsychologicalLevelsProvider


SESSION_ID = "PSY_SNAPSHOT_TEST"
PRICE_PATH = (
    (1, Decimal("60350")),
    (2, Decimal("60376")),
    (3, Decimal("60400")),
    (4, Decimal("60430")),
    (5, Decimal("60435")),
    (6, Decimal("60440")),
    (7, Decimal("60445")),
)
ROW_DIRTY = (
    "stress_dirty",
    "exposure_dirty",
    "fatigue_recovery_dirty",
    "health_dirty",
)


def generated_60400_zone():
    zones = PsychologicalLevelsProvider().generate(
        price=Decimal("60341"),
        symbol="BTCUSDT",
        market_timestamp="2026-07-03T12:00:00Z",
        session_id=SESSION_ID,
    )
    return next(zone for zone in zones if zone.level_center == 60400)


def row_values(row_index: int, price: Decimal) -> dict:
    return {
        "row_index": row_index,
        "timestamp": f"T{row_index}",
        "price": price,
        "inside_zone_flag": Decimal("60375") <= price <= Decimal("60425"),
        "zone_touch_flag": Decimal("60370") <= price <= Decimal("60430"),
        "distance_to_zone": Decimal("0"),
        "zone_penetration_depth": Decimal("1"),
        "sigma_live": Decimal("18.5"),
        "load_live": Decimal("10"),
        "fatigue_live": Decimal("2"),
        "recovery_live": Decimal("0"),
        "rigidity_live": Decimal("80"),
        "capacity_live": Decimal("75"),
        "health_live": Decimal("90"),
    }


def native_geometry_patch(zone) -> dict:
    return {
        "geometry": {
            "geometry_source": zone.geometry_source,
            "geometry_type": zone.geometry_type,
            "geometry_version": zone.geometry_version,
            "symbol": zone.symbol,
            "level_center": zone.level_center,
            "lower_edge": zone.lower_edge,
            "upper_edge": zone.upper_edge,
            "zone_width": zone.zone_width,
            "zone_half_width": zone.zone_half_width,
            "spacing": zone.spacing,
            "zone_id": zone.zone_id,
            "case_id": zone.case_id,
            "shadow_only": zone.shadow_only,
        }
    }


def build_requested_patches(plan, state, row, events):
    patches = []
    if any(getattr(plan.dirty_flags, name) for name in ROW_DIRTY):
        patches.append(RowMechanicsAdapter().build_patch(row))
    if plan.dirty_flags.interaction_dirty:
        open_source = asdict(state)
        open_source.update(row)
        patches.append(OpenVisitAdapter().build_patch(open_source))
    if (
        plan.dirty_flags.visit_dirty
        and plan.dirty_flags.response_dirty
    ):
        completed = dict(events[-1].evidence)
        completed["visit_id"] = events[-1].visit_id
        patches.append(
            LastCompletedVisitAdapter().build_patch(completed)
        )
    if (
        plan.dirty_flags.response_dirty
        and plan.dirty_flags.state_dirty
    ):
        patches.append(
            DynamicMechanicsAdapter().build_patch(
                {
                    "visit_id": events[-1].visit_id,
                    "dynamic_state": NOT_AVAILABLE,
                    "dynamic_state_reason": NOT_AVAILABLE,
                }
            )
        )
    if (
        plan.dirty_flags.trajectory_dirty
        and plan.dirty_flags.prediction_dirty
    ):
        patches.append(
            PredictionAdapter().build_patch(
                {"prediction_status": NOT_AVAILABLE}
            )
        )
    sections = tuple(next(iter(patch)) for patch in patches)
    assert len(sections) == len(set(sections))
    return tuple(patches), sections


def changed_sections(previous, current):
    return {
        section
        for section in SNAPSHOT_SECTIONS
        if section != "metadata"
        and dict(getattr(previous, section))
        != dict(getattr(current, section))
    }


def run_pipeline():
    zone = generated_60400_zone()
    interpreter = InteractionInterpreter(
        zone_id=zone.zone_id,
        lower_edge=zone.lower_edge,
        upper_edge=zone.upper_edge,
        touch_tolerance=5,
        visit_lull_rows=3,
    )
    dispatcher = EventDispatcher()
    store = SnapshotStore()
    state = interpreter.initial_state()
    snapshots = []
    plan_sections = []

    for row_index, price in PRICE_PATH:
        row = row_values(row_index, price)
        interpreted = interpreter.interpret_in_order(
            state,
            row_index=row_index,
            timestamp=row["timestamp"],
            price=price,
        )
        assert interpreted.status == ORDER_ACCEPTED
        state = interpreted.state
        if not interpreted.events:
            continue

        dispatched = dispatcher.dispatch(
            DispatchBatch.from_events(
                DispatchContext(
                    session_id=zone.session_id,
                    zone_id=zone.zone_id,
                    row_index=row_index,
                    timestamp=row["timestamp"],
                    global_zone_key=zone.global_zone_key,
                    geometry_version=zone.geometry_version,
                ),
                state,
                interpreted.events,
            )
        )
        assert dispatched.status == "DISPATCHED_SHADOW"
        coordinator_result = dispatched.coordinator_result
        assert coordinator_result.status == "PLANNED_NOT_EXECUTED"
        plan = coordinator_result.plan
        patches, requested_sections = build_requested_patches(
            plan,
            state,
            row,
            interpreted.events,
        )
        plan_sections.append(requested_sections)

        if store.get_current(zone.global_zone_key) is None:
            snapshot = store.create(
                plan,
                (
                    {"metadata": {"session_id": zone.session_id}},
                    native_geometry_patch(zone),
                    *patches,
                ),
                global_zone_key=zone.global_zone_key,
            )
        else:
            previous = store.get_current(zone.global_zone_key)
            snapshot = store.update(
                plan,
                patches,
                global_zone_key=zone.global_zone_key,
            )
            actual_changes = changed_sections(previous, snapshot)
            assert actual_changes == set(requested_sections), (
                row_index,
                actual_changes,
                set(requested_sections),
            )
        snapshots.append(snapshot)

    return zone, interpreter, state, store, tuple(snapshots), tuple(plan_sections)


def test_coordinator_and_requested_sections() -> None:
    _, _, _, _, snapshots, sections = run_pipeline()
    assert len(snapshots) == 4
    assert sections == (
        ("current_row_mechanics", "open_visit"),
        ("current_row_mechanics", "open_visit"),
        ("open_visit",),
        (
            "last_completed_visit",
            "dynamic_mechanics",
            "prediction",
        ),
    )
    print("COORDINATOR_AND_DIRTY_SECTIONS = PASS")


def test_copy_on_write_and_revisions() -> None:
    _, _, _, store, snapshots, _ = run_pipeline()
    assert tuple(snapshot.revision for snapshot in snapshots) == (1, 2, 3, 4)
    assert len({id(snapshot) for snapshot in snapshots}) == 4
    assert snapshots[0].revision == 1
    assert snapshots[0].current_row_mechanics["row_id"] == 2
    assert store.get_current(snapshots[-1].global_zone_key) is snapshots[-1]
    print("COPY_ON_WRITE_REVISIONS = PASS")


def test_identity_geometry_and_project_boundaries() -> None:
    zone, _, _, _, snapshots, _ = run_pipeline()
    final = snapshots[-1]
    assert final.global_zone_key == zone.global_zone_key
    assert final.geometry["geometry_source"] == GEOMETRY_SOURCE
    assert final.geometry["geometry_source"] == "PSYCHOLOGICAL_LEVELS_TEST"
    assert final.geometry["lower_edge"] == Decimal("60375")
    assert final.geometry["upper_edge"] == Decimal("60425")
    forbidden = {
        "formation_low",
        "formation_high",
        "formation_width",
        "active_core_low",
        "active_core_high",
        "active_core_width",
        "density_band_low",
        "density_band_high",
        "density_band_width",
    }
    assert forbidden.isdisjoint(final.geometry)
    print("IDENTITY_AND_PROJECT_BOUNDARIES = PASS")


def test_duplicate_does_not_create_revision() -> None:
    zone, interpreter, state, store, snapshots, _ = run_pipeline()
    authoritative = store.get_current(zone.global_zone_key)
    duplicate = interpreter.interpret_in_order(
        state,
        row_index=7,
        timestamp="T7_DUPLICATE",
        price=Decimal("60445"),
    )
    assert duplicate.status == AUDIT_ROW_DUPLICATE
    assert duplicate.events == ()
    assert store.get_current(zone.global_zone_key) is authoritative
    assert authoritative.revision == snapshots[-1].revision == 4
    print("DUPLICATE_CREATES_NO_REVISION = PASS")


def test_snapshot_determinism() -> None:
    first = run_pipeline()[4]
    second = run_pipeline()[4]
    assert tuple(snapshot.to_dict() for snapshot in first) == tuple(
        snapshot.to_dict() for snapshot in second
    )
    print("SNAPSHOT_CONTENT_DETERMINISM = PASS")


def main() -> None:
    test_coordinator_and_requested_sections()
    test_copy_on_write_and_revisions()
    test_identity_geometry_and_project_boundaries()
    test_duplicate_does_not_create_revision()
    test_snapshot_determinism()
    print("PSYCHOLOGICAL_LEVELS_SNAPSHOT_INTEGRATION_TEST = PASS")
    print("OFFLINE_ONLY = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

"""Offline 10,000-row Psychological Levels mechanical pipeline stress test."""

from __future__ import annotations

import sys
import time
import tracemalloc
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_DIR = Path(__file__).resolve().parent
for path in (REPO_ROOT, EXPERIMENT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.canonical_snapshot import SnapshotStore
from core.event_dispatcher import (
    DispatchBatch,
    DispatchContext,
    EventDispatcher,
)
from core.interaction_interpreter import (
    AUDIT_ROW_DUPLICATE,
    AUDIT_ROW_OUT_OF_ORDER,
    ORDER_ACCEPTED,
    InteractionInterpreter,
)
from core.last_completed_visit_adapter import LastCompletedVisitAdapter
from core.open_visit_adapter import OpenVisitAdapter
from core.row_mechanics_adapter import RowMechanicsAdapter
from provider import PsychologicalLevelsProvider


ROW_COUNT = 10_000
SESSION_ID = "PSY_STRESS_TEST"
ROW_DIRTY = (
    "stress_dirty",
    "exposure_dirty",
    "fatigue_recovery_dirty",
    "health_dirty",
)


@dataclass
class ZoneHarness:
    geometry: Any
    interpreter: InteractionInterpreter
    dispatcher: EventDispatcher
    state: Any
    first_snapshot: Any = None
    first_snapshot_copy: Any = None


@dataclass(frozen=True)
class StressResult:
    rows_processed: int
    events_generated: int
    refresh_plans: int
    snapshot_revisions: int
    distinct_zones: int
    maximum_active_zones: int
    final_revisions: tuple[tuple[str, int], ...]
    final_snapshots: tuple[tuple[str, dict], ...]
    revision_monotonicity: bool
    copy_on_write: bool
    identity_integrity: bool
    duplicate_protection: bool
    out_of_order_protection: bool
    snapshot_consistency: bool


def generate_price(row_index: int) -> Decimal:
    """Deterministic triangular path through all seven level zones."""
    lower = 59_740
    upper = 61_060
    step = 10
    span_steps = (upper - lower) // step
    phase = (row_index - 1) % (span_steps * 2)
    offset = phase if phase <= span_steps else span_steps * 2 - phase
    return Decimal(lower + offset * step)


def build_harnesses() -> dict[str, ZoneHarness]:
    geometries = PsychologicalLevelsProvider(
        spacing=Decimal("200"),
        zone_half_width=Decimal("25"),
        active_window=3,
    ).generate(
        price=Decimal("60341"),
        symbol="BTCUSDT",
        market_timestamp="2026-07-03T12:00:00Z",
        session_id=SESSION_ID,
    )
    harnesses = {}
    for geometry in geometries:
        interpreter = InteractionInterpreter(
            zone_id=geometry.zone_id,
            lower_edge=geometry.lower_edge,
            upper_edge=geometry.upper_edge,
            touch_tolerance=5,
            visit_lull_rows=3,
        )
        harnesses[geometry.global_zone_key] = ZoneHarness(
            geometry=geometry,
            interpreter=interpreter,
            dispatcher=EventDispatcher(),
            state=interpreter.initial_state(),
        )
    return harnesses


def row_values(row_index: int, price: Decimal) -> dict[str, Any]:
    return {
        "row_index": row_index,
        "timestamp": f"T{row_index}",
        "price": price,
        "sigma_live": Decimal("1"),
        "load_live": Decimal("1"),
        "fatigue_live": Decimal("0"),
        "recovery_live": Decimal("0"),
        "rigidity_live": Decimal("1"),
        "capacity_live": Decimal("1"),
        "health_live": Decimal("1"),
    }


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


def build_patches(plan, state, row, events) -> tuple[dict, ...]:
    patches = []
    if any(getattr(plan.dirty_flags, name) for name in ROW_DIRTY):
        patches.append(RowMechanicsAdapter().build_patch(row))
    if plan.dirty_flags.interaction_dirty:
        source = asdict(state)
        source.update(row)
        patches.append(OpenVisitAdapter().build_patch(source))
    if plan.dirty_flags.visit_dirty and plan.dirty_flags.response_dirty:
        completed = dict(events[-1].evidence)
        completed["visit_id"] = events[-1].visit_id
        patches.append(
            LastCompletedVisitAdapter().build_patch(completed)
        )
    assert patches
    sections = tuple(next(iter(patch)) for patch in patches)
    assert len(sections) == len(set(sections))
    return tuple(patches)


def run_stress(
    *,
    capture_memory: bool,
) -> tuple[StressResult, tuple[int, ...], int]:
    harnesses = build_harnesses()
    store = SnapshotStore()
    events_generated = 0
    refresh_plans = 0
    maximum_active_zones = 0
    revision_history = {key: [] for key in harnesses}
    memory_trend = []

    for row_index in range(1, ROW_COUNT + 1):
        price = generate_price(row_index)
        row = row_values(row_index, price)

        for global_key, harness in harnesses.items():
            interpreted = harness.interpreter.interpret_in_order(
                harness.state,
                row_index=row_index,
                timestamp=row["timestamp"],
                price=price,
            )
            assert interpreted.status == ORDER_ACCEPTED
            harness.state = interpreted.state
            events_generated += len(interpreted.events)
            if not interpreted.events:
                continue

            dispatched = harness.dispatcher.dispatch(
                DispatchBatch.from_events(
                    DispatchContext(
                        session_id=harness.geometry.session_id,
                        zone_id=harness.geometry.zone_id,
                        row_index=row_index,
                        timestamp=row["timestamp"],
                        global_zone_key=global_key,
                        geometry_version=(
                            harness.geometry.geometry_version
                        ),
                    ),
                    harness.state,
                    interpreted.events,
                )
            )
            assert dispatched.status == "DISPATCHED_SHADOW"
            coordinator_result = dispatched.coordinator_result
            assert coordinator_result.status == "PLANNED_NOT_EXECUTED"
            plan = coordinator_result.plan
            patches = build_patches(
                plan,
                harness.state,
                row,
                interpreted.events,
            )

            if store.get_current(global_key) is None:
                snapshot = store.create(
                    plan,
                    (
                        {
                            "metadata": {
                                "session_id": (
                                    harness.geometry.session_id
                                )
                            }
                        },
                        geometry_patch(harness.geometry),
                        *patches,
                    ),
                    global_zone_key=global_key,
                )
                harness.first_snapshot = snapshot
                harness.first_snapshot_copy = snapshot.to_dict()
            else:
                snapshot = store.update(
                    plan,
                    patches,
                    global_zone_key=global_key,
                )
            refresh_plans += 1
            revision_history[global_key].append(snapshot.revision)

        maximum_active_zones = max(
            maximum_active_zones,
            sum(
                bool(harness.state.active_visit_id)
                for harness in harnesses.values()
            ),
        )
        if capture_memory and row_index % 1000 == 0:
            current, _ = tracemalloc.get_traced_memory()
            memory_trend.append(current)

    revisions = tuple(
        sorted(
            (
                key,
                store.get_current(key).revision,
            )
            for key in harnesses
        )
    )
    final_snapshots = tuple(
        sorted(
            (
                key,
                store.get_current(key).to_dict(),
            )
            for key in harnesses
        )
    )
    monotonic = all(
        history == list(range(1, len(history) + 1))
        for history in revision_history.values()
    )
    copy_on_write = all(
        harness.first_snapshot.revision == 1
        and harness.first_snapshot.to_dict()
        == harness.first_snapshot_copy
        for harness in harnesses.values()
    )
    identity_integrity = all(
        store.get_current(key).global_zone_key == key
        and store.get_current(key).zone_id == harness.geometry.zone_id
        for key, harness in harnesses.items()
    )
    snapshot_consistency = all(
        store.get_current(key).geometry["geometry_source"]
        == "PSYCHOLOGICAL_LEVELS_TEST"
        and store.get_current(key).geometry["zone_id"]
        == harness.geometry.zone_id
        for key, harness in harnesses.items()
    )

    guard_harness = next(iter(harnesses.values()))
    guard_key = guard_harness.geometry.global_zone_key
    authoritative = store.get_current(guard_key)
    duplicate = guard_harness.interpreter.interpret_in_order(
        guard_harness.state,
        row_index=ROW_COUNT,
        timestamp="DUPLICATE",
        price=generate_price(ROW_COUNT),
    )
    older = guard_harness.interpreter.interpret_in_order(
        guard_harness.state,
        row_index=ROW_COUNT - 1,
        timestamp="OUT_OF_ORDER",
        price=generate_price(ROW_COUNT - 1),
    )
    duplicate_protection = (
        duplicate.status == AUDIT_ROW_DUPLICATE
        and duplicate.events == ()
        and store.get_current(guard_key) is authoritative
    )
    out_of_order_protection = (
        older.status == AUDIT_ROW_OUT_OF_ORDER
        and older.events == ()
        and store.get_current(guard_key) is authoritative
    )

    result = StressResult(
        rows_processed=ROW_COUNT,
        events_generated=events_generated,
        refresh_plans=refresh_plans,
        snapshot_revisions=sum(value for _, value in revisions),
        distinct_zones=len(harnesses),
        maximum_active_zones=maximum_active_zones,
        final_revisions=revisions,
        final_snapshots=final_snapshots,
        revision_monotonicity=monotonic,
        copy_on_write=copy_on_write,
        identity_integrity=identity_integrity,
        duplicate_protection=duplicate_protection,
        out_of_order_protection=out_of_order_protection,
        snapshot_consistency=snapshot_consistency,
    )
    peak = tracemalloc.get_traced_memory()[1] if capture_memory else 0
    return result, tuple(memory_trend), peak


def main() -> None:
    tracemalloc.start()
    started = time.perf_counter()
    first, memory_trend, peak_memory = run_stress(capture_memory=True)
    processing_time = time.perf_counter() - started
    tracemalloc.stop()

    second, _, _ = run_stress(capture_memory=False)
    deterministic = first == second
    revision_growth = tuple(value for _, value in first.final_revisions)
    overall = all(
        (
            deterministic,
            first.copy_on_write,
            first.identity_integrity,
            first.revision_monotonicity,
            first.duplicate_protection,
            first.out_of_order_protection,
            first.snapshot_consistency,
            first.snapshot_revisions == first.refresh_plans,
            first.distinct_zones == 7,
            first.maximum_active_zones <= 7,
            peak_memory < 128 * 1024 * 1024,
        )
    )

    print("Rows processed:", first.rows_processed)
    print("Events generated:", first.events_generated)
    print("Refresh Plans:", first.refresh_plans)
    print("Snapshot revisions:", first.snapshot_revisions)
    print("Distinct zones:", first.distinct_zones)
    print("Maximum active zones:", first.maximum_active_zones)
    print("Processing time seconds:", round(processing_time, 6))
    print("Peak traced memory bytes:", peak_memory)
    print("Memory trend bytes:", memory_trend)
    print("Revision growth by zone:", revision_growth)
    print("Deterministic:", "PASS" if deterministic else "FAIL")
    print(
        "Copy-on-write:",
        "PASS" if first.copy_on_write else "FAIL",
    )
    print(
        "Identity:",
        "PASS" if first.identity_integrity else "FAIL",
    )
    print(
        "Revision monotonicity:",
        "PASS" if first.revision_monotonicity else "FAIL",
    )
    print(
        "Duplicate protection:",
        "PASS" if first.duplicate_protection else "FAIL",
    )
    print(
        "Out-of-order protection:",
        "PASS" if first.out_of_order_protection else "FAIL",
    )
    print(
        "Snapshot consistency:",
        "PASS" if first.snapshot_consistency else "FAIL",
    )
    print("Overall result:", "PASS" if overall else "FAIL")
    print("OFFLINE_ONLY = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")
    if not overall:
        raise AssertionError("Psychological Levels stress test failed")


if __name__ == "__main__":
    main()

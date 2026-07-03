"""Phase 1B Stage 1 -- offline Dynamic Mechanics research validation.

Research-only. Computes simple, clearly-labeled first derivative / integral /
second derivative / SDR metrics from sequences of completed visits generated
via the Phase 1A Psychological Levels test geometry (experiments/
psychological_levels/ is reused as the input laboratory, unmodified).

This is NOT the production B12.5 Dynamic State pipeline. It does not reuse,
duplicate, approximate, or modify any Project 1 RDM formula, Snapshot
architecture, Worker/Queue/Bootstrap, or B10/B11 production code. The per-row
"health/omega/attacker_force" mechanics below are a small, deterministic,
clearly-labeled research proxy invented for this experiment only -- the
Interaction Interpreter's own VISIT_COMPLETED evidence carries only
geometric/timing fields (visit_start_row, visit_end_price, lull_rows, ...),
no mechanical values, so a proxy is required to produce a non-trivial
completed-visit series to differentiate/integrate over.

SDR here means SIMPLE_RESEARCH_SDR_V1 = |delta omega| / health -- a basic,
independent, versioned research ratio. It is explicitly NOT the production
Structural Dynamic Response formula used elsewhere in this codebase.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
LAB_DIR = REPO_ROOT / "experiments" / "psychological_levels"
for path in (REPO_ROOT, LAB_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.event_dispatcher import (
    DispatchBatch,
    DispatchContext,
    EventDispatcher,
)
from core.interaction_interpreter import ORDER_ACCEPTED, InteractionInterpreter
from core.last_completed_visit_adapter import LastCompletedVisitAdapter
from provider import PsychologicalLevelsProvider


ROW_COUNT = 3_000
SESSION_ID = "PSY_DYNAMIC_STAGE1"
EPSILON = Decimal("0.000001")
SDR_LABEL_THRESHOLD = Decimal("0.5")
SDR_FORMULA_VERSION = "SIMPLE_RESEARCH_SDR_V1"

# Simple, deterministic, research-only per-row mechanical proxies. Not a
# Project 1 formula -- invented for this offline experiment only.
HEALTH_START = Decimal("100")
HEALTH_DECAY_PER_PENETRATION = Decimal("0.6")
HEALTH_RECOVERY_PER_ROW = Decimal("0.4")


@dataclass
class ZoneHarness:
    geometry: Any
    interpreter: InteractionInterpreter
    dispatcher: EventDispatcher
    state: Any
    health_live: Decimal = HEALTH_START
    omega_accumulator: Decimal = Decimal("0")
    attacker_force_peak: Decimal = Decimal("0")
    completed_visits: list = field(default_factory=list)


def generate_price(row_index: int) -> Decimal:
    """Deterministic triangular path through all seven level zones (same
    generator shape as Phase 1A's stress test, reused for continuity)."""
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
    harnesses: dict[str, ZoneHarness] = {}
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


def update_mechanics(
    harness: ZoneHarness,
    *,
    touching: bool,
    penetration_depth: Decimal,
    price_delta: Decimal,
) -> None:
    """Advance the simple per-row research mechanics proxy for one zone."""
    if touching:
        harness.health_live = max(
            harness.health_live - penetration_depth * HEALTH_DECAY_PER_PENETRATION,
            Decimal("0"),
        )
        harness.omega_accumulator += penetration_depth
        harness.attacker_force_peak = max(
            harness.attacker_force_peak, abs(price_delta)
        )
    else:
        harness.health_live = min(
            harness.health_live + HEALTH_RECOVERY_PER_ROW,
            Decimal("100"),
        )


def compute_dynamics(visits: list[dict]) -> dict[str, list]:
    """Research-only first/second derivative, integral, and SDR series
    across one zone's ordered completed-visit summaries."""
    health = [v["health_at_visit"] for v in visits]
    omega = [v["omega_at_visit"] for v in visits]
    response = [v["attacker_force_at_visit"] for v in visits]

    d1_health = [None] + [
        health[i] - health[i - 1] for i in range(1, len(health))
    ]
    d1_omega = [None] + [
        omega[i] - omega[i - 1] for i in range(1, len(omega))
    ]
    d1_response = [None] + [
        response[i] - response[i - 1] for i in range(1, len(response))
    ]
    d2_health = [None, None] + [
        d1_health[i] - d1_health[i - 1] for i in range(2, len(d1_health))
    ]

    integral_omega: list[Decimal] = []
    running = Decimal("0")
    for value in omega:
        running += value
        integral_omega.append(running)

    integral_response: list[Decimal] = []
    running = Decimal("0")
    for value in response:
        running += value
        integral_response.append(running)

    sdr: list[Decimal | None] = [None]
    for i in range(1, len(omega)):
        sdr.append(abs(d1_omega[i]) / max(health[i], EPSILON))

    labels: list[str | None] = [None]
    for i in range(1, len(visits)):
        if d1_health[i] < 0 and sdr[i] is not None and sdr[i] > SDR_LABEL_THRESHOLD:
            labels.append("RESEARCH_ATTACKER_PRESSURE")
        elif d1_health[i] > 0:
            labels.append("RESEARCH_RECOVERING")
        else:
            labels.append("RESEARCH_STABLE")

    return {
        "d1_health": d1_health,
        "d1_omega": d1_omega,
        "d1_response": d1_response,
        "d2_health": d2_health,
        "integral_omega": integral_omega,
        "integral_response": integral_response,
        "sdr": sdr,
        "labels": labels,
    }


def run() -> dict[str, Any]:
    harnesses = build_harnesses()
    errors: list[str] = []
    rows_processed = 0
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
                if plan.dirty_flags.visit_dirty and plan.dirty_flags.response_dirty:
                    completed_event = interpreted.events[-1]
                    completed_source = dict(completed_event.evidence)
                    completed_source["visit_id"] = completed_event.visit_id
                    completed_source["health_at_visit"] = harness.health_live
                    completed_source["omega_at_visit"] = harness.omega_accumulator
                    completed_source["attacker_force_at_visit"] = (
                        harness.attacker_force_peak
                    )
                    patch = LastCompletedVisitAdapter().build_patch(
                        completed_source
                    )
                    harness.completed_visits.append(patch["last_completed_visit"])
                    harness.omega_accumulator = Decimal("0")
                    harness.attacker_force_peak = Decimal("0")
            except Exception as exc:  # research harness: never abort the run
                errors.append(
                    f"{global_key}:{row_index}:{type(exc).__name__}:{exc}"
                )

        rows_processed = row_index

    first_derivatives = 0
    integrals = 0
    second_derivatives = 0
    sdr_values = 0
    dynamic_labels = 0
    completed_visits_total = 0

    for harness in harnesses.values():
        visits = harness.completed_visits
        completed_visits_total += len(visits)
        dynamics = compute_dynamics(visits)
        first_derivatives += sum(
            1 for v in dynamics["d1_health"] if v is not None
        )
        integrals += sum(1 for v in dynamics["integral_omega"] if v is not None)
        second_derivatives += sum(
            1 for v in dynamics["d2_health"] if v is not None
        )
        sdr_values += sum(1 for v in dynamics["sdr"] if v is not None)
        dynamic_labels += sum(1 for v in dynamics["labels"] if v is not None)

    result = "PASS" if not errors else "FAIL"

    return {
        "rows_processed": rows_processed,
        "zones_observed": len(harnesses),
        "completed_visits": completed_visits_total,
        "first_derivatives_generated": first_derivatives,
        "integrals_generated": integrals,
        "second_derivatives_generated": second_derivatives,
        "sdr_values_generated": sdr_values,
        "dynamic_labels_generated": dynamic_labels,
        "errors": len(errors),
        "error_detail": errors[:10],
        "result": result,
    }


def main() -> None:
    report = run()
    print("===== PHASE 1B STAGE 1 -- DYNAMIC MECHANICS OFFLINE VALIDATION =====")
    print(f"rows_processed = {report['rows_processed']}")
    print(f"zones_observed = {report['zones_observed']}")
    print(f"completed_visits = {report['completed_visits']}")
    print(f"first_derivatives_generated = {report['first_derivatives_generated']}")
    print(f"integrals_generated = {report['integrals_generated']}")
    print(
        f"second_derivatives_generated = {report['second_derivatives_generated']}"
    )
    print(f"sdr_values_generated = {report['sdr_values_generated']}")
    print(f"sdr_formula = {SDR_FORMULA_VERSION}")
    print(f"dynamic_labels_generated = {report['dynamic_labels_generated']}")
    print(f"errors = {report['errors']}")
    if report["error_detail"]:
        print("error_detail (first 10):")
        for item in report["error_detail"]:
            print(f"  {item}")
    print(f"result = {report['result']}")
    print("RESEARCH_ONLY = TRUE")
    print("NO_PROJECT1_FORMULAS_REUSED = TRUE")
    print("NO_PRODUCTION_B125_DYNAMIC_STATE = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

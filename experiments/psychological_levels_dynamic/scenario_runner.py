"""Project 2 Chapter II Phase 2 -- Scenario Runner.

Thin, additive orchestrator connecting the Chapter II Scenario Generator
(scenario_contract.py / scenario_registry.py / scenario_primitives.py) to the
unmodified Chapter I analytical path (Stage 1 plus Stages 3-6). Executes exactly one
ScenarioSpecification at a time and returns one immutable ScenarioRunResult
wrapping each executed stage's existing analysis output verbatim. No new
metrics, no cross-scenario comparison, no batch execution, no storage by
default, no Stage 2 Snapshot integration (that already validated Snapshot
plumbing structurally, once, and is not part of the per-scenario research
payload Chapter II compares across scenarios).

Reused unchanged: Stage 1's ZoneHarness / update_mechanics / compute_dynamics;
the shared Project 2 InteractionInterpreter / LastCompletedVisitAdapter /
EventDispatcher plumbing; PsychologicalLevelsProvider; Stage 3/4/5/6's own
top-level analyze functions, imported under qualified module names (Stage
4/5/6 each define a function literally named `analyze`, so star-imports are
never used here). Does NOT call Stage 1's generate_price()/build_harnesses()/
run() or Stage 3's collect_completed_visits() -- those are tied to the fixed
triangular corpus and have no scenario injection point; calling them would
silently ignore the scenario. The only duplicated structure is the thin
per-row driving loop itself, which mirrors Stage 3's own completed-visit
collection pattern (Interpreter + LastCompletedVisitAdapter only -- no
Dispatcher/Coordinator/Snapshot, matching the decision to skip Stage 2).
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, fields
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
LAB_DIR = REPO_ROOT / "experiments" / "psychological_levels"
DYNAMIC_DIR = Path(__file__).resolve().parent
for path in (REPO_ROOT, LAB_DIR, DYNAMIC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.event_dispatcher import EventDispatcher
from core.interaction_interpreter import ORDER_ACCEPTED, InteractionInterpreter
from core.last_completed_visit_adapter import LastCompletedVisitAdapter
from provider import PsychologicalLevelsProvider

from dynamic_mechanics_test import ZoneHarness, update_mechanics
from scenario_contract import (
    PriceObservation,
    ScenarioSpecification,
    _canonical_value,
)
from scenario_registry import ScenarioRegistry

import test_dynamic_state_transitions as stage3
import test_transition_graph as stage4
import test_trajectory_evolution as stage5
import test_prediction_evolution as stage6


NOT_AVAILABLE = "NOT_AVAILABLE"
CHAIN_VERSION = "PHASE1B_STAGE1_AND_STAGE3_TO_STAGE6_STABLE"
CHAIN_STAGE_FILENAMES = (
    "dynamic_mechanics_test.py",
    "test_snapshot_dynamic_mechanics.py",
    "test_dynamic_state_transitions.py",
    "test_transition_graph.py",
    "test_trajectory_evolution.py",
    "test_prediction_evolution.py",
)
_REQUIRED_GEOMETRY_KEYS = (
    "spacing",
    "zone_half_width",
    "active_window",
    "symbol",
    "market_timestamp",
    "session_id",
)


def normalized_source_hash(path: Path) -> str:
    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def _build_chain_fingerprint() -> str:
    payload = {
        filename: normalized_source_hash(DYNAMIC_DIR / filename)
        for filename in CHAIN_STAGE_FILENAMES
    }
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


CHAIN_FINGERPRINT = _build_chain_fingerprint()


@dataclass(frozen=True)
class PriceOnlyValidation:
    contiguous_row_ordering: bool
    finite_price_validation: bool
    price_only_contract_validation: bool
    row_count_matches_specification: bool

    @property
    def passed(self) -> bool:
        return (
            self.contiguous_row_ordering
            and self.finite_price_validation
            and self.price_only_contract_validation
            and self.row_count_matches_specification
        )


@dataclass(frozen=True)
class ScenarioRunResult:
    # Provenance
    scenario_id: str
    scenario_family: str
    specification_fingerprint: str
    provider_version: str
    scenario_schema_version: str
    chain_version: str
    chain_fingerprint: str
    run_id: str
    row_count: int
    observation_checksum: str
    # Execution integrity
    observation_count: int
    first_price: Decimal
    last_price: Decimal
    contiguous_row_ordering: bool
    finite_price_validation: bool
    price_only_contract_validation: bool
    deterministic_generation: bool
    errors: tuple[str, ...]
    result: str
    # Stage outputs (verbatim wraps of each stage's own analyze() output)
    completed_visits: int
    zones_observed: int
    stage3_transition_summary: Any
    stage4_graph_summary: Any
    stage5_trajectory_summary: Any
    stage6_hypothesis_summary: Any


def _geometry_value(geometry_parameters: Mapping[str, Any], key: str) -> Any:
    if key not in geometry_parameters:
        raise ValueError(f"geometry_parameters missing required key: {key}")
    return geometry_parameters[key]


def _observation_checksum(observations: Sequence[PriceObservation]) -> str:
    canonical = json.dumps(
        [
            {
                "row_index": observation.row_index,
                "price": _canonical_value(observation.price),
            }
            for observation in observations
        ],
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _run_id(
    specification_fingerprint: str,
    provider_version: str,
    chain_version: str,
    chain_fingerprint: str,
    observation_checksum: str,
) -> str:
    payload = "|".join(
        (
            specification_fingerprint,
            provider_version,
            chain_version,
            chain_fingerprint,
            observation_checksum,
        )
    )
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def validate_price_only_observations(
    spec: ScenarioSpecification,
    observations: Sequence[PriceObservation],
) -> PriceOnlyValidation:
    """Structural, not merely conventional: PriceObservation is a frozen
    dataclass with exactly two fields, so this also confirms no label,
    mechanics, transition, or hypothesis value could have been smuggled in --
    there is no field to hold one."""
    contiguous = all(
        observation.row_index == index
        for index, observation in enumerate(observations, start=1)
    )
    finite = all(
        isinstance(observation.price, Decimal) and observation.price.is_finite()
        for observation in observations
    )
    price_only = all(
        tuple(field.name for field in fields(observation)) == ("row_index", "price")
        for observation in observations
    )
    row_count_matches = len(observations) == spec.row_count
    return PriceOnlyValidation(
        contiguous_row_ordering=contiguous,
        finite_price_validation=finite,
        price_only_contract_validation=price_only,
        row_count_matches_specification=row_count_matches,
    )


def build_scenario_harnesses(spec: ScenarioSpecification) -> dict[str, ZoneHarness]:
    geometry_parameters = spec.geometry_parameters
    for key in _REQUIRED_GEOMETRY_KEYS:
        _geometry_value(geometry_parameters, key)

    geometries = PsychologicalLevelsProvider(
        spacing=Decimal(str(geometry_parameters["spacing"])),
        zone_half_width=Decimal(str(geometry_parameters["zone_half_width"])),
        active_window=int(geometry_parameters["active_window"]),
    ).generate(
        price=spec.start_price,
        symbol=str(geometry_parameters["symbol"]),
        market_timestamp=str(geometry_parameters["market_timestamp"]),
        session_id=str(geometry_parameters["session_id"]),
    )
    touch_tolerance = int(geometry_parameters.get("touch_tolerance", 5))
    visit_lull_rows = int(geometry_parameters.get("visit_lull_rows", 3))

    harnesses: dict[str, ZoneHarness] = {}
    for geometry in geometries:
        interpreter = InteractionInterpreter(
            zone_id=geometry.zone_id,
            lower_edge=geometry.lower_edge,
            upper_edge=geometry.upper_edge,
            touch_tolerance=touch_tolerance,
            visit_lull_rows=visit_lull_rows,
        )
        harnesses[geometry.global_zone_key] = ZoneHarness(
            geometry=geometry,
            interpreter=interpreter,
            dispatcher=EventDispatcher(),
            state=interpreter.initial_state(),
        )
    return harnesses


def run_scenario_chain(
    spec: ScenarioSpecification,
    observations: Sequence[PriceObservation],
) -> tuple[dict[str, list[dict]], list[str]]:
    """The one deliberately duplicated piece of structure: a thin per-row
    driving loop mirroring Stage 3's collect_completed_visits(), sourcing
    price/row_index from scenario-generated observations instead of Stage 1's
    hardcoded generate_price(). ZoneHarness, update_mechanics, the
    Interpreter, and LastCompletedVisitAdapter are all imported unchanged --
    no Dynamic Mechanics or Dynamic State formula is reimplemented here."""
    harnesses = build_scenario_harnesses(spec)
    errors: list[str] = []
    previous_price: Decimal | None = None

    for observation in observations:
        row_index = observation.row_index
        price = observation.price
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

    visits_by_zone = {
        global_key: harness.completed_visits
        for global_key, harness in harnesses.items()
    }
    return visits_by_zone, errors


def run_scenario(
    registry: ScenarioRegistry, spec: ScenarioSpecification
) -> ScenarioRunResult:
    errors: list[str] = []

    registry.validate(spec)
    first_observations = tuple(registry.generate(spec))
    second_observations = tuple(registry.generate(spec))
    deterministic_generation = tuple(
        (observation.row_index, observation.price)
        for observation in first_observations
    ) == tuple(
        (observation.row_index, observation.price)
        for observation in second_observations
    )
    if not deterministic_generation:
        errors.append("scenario provider produced non-deterministic observations")

    observations = first_observations
    price_only_validation = validate_price_only_observations(spec, observations)
    if not price_only_validation.passed:
        errors.append("price-only observation validation failed")

    visits_by_zone, chain_errors = run_scenario_chain(spec, observations)
    errors.extend(chain_errors)

    def _run_stage(label: str, callable_: Any) -> Any:
        try:
            return callable_(visits_by_zone)
        except Exception as exc:  # never let one stage abort the others
            errors.append(f"{label}:{type(exc).__name__}:{exc}")
            return NOT_AVAILABLE

    stage3_summary = _run_stage("stage3", stage3.analyze)
    stage4_summary = _run_stage("stage4", stage4.analyze_transition_graph)
    stage5_summary = _run_stage("stage5", stage5.analyze)
    stage6_summary = _run_stage("stage6", stage6.analyze)

    provider_version = registry.get(spec.scenario_family).metadata().provider_version
    observation_checksum = _observation_checksum(observations)
    run_id = _run_id(
        spec.specification_fingerprint,
        provider_version,
        CHAIN_VERSION,
        CHAIN_FINGERPRINT,
        observation_checksum,
    )

    completed_visits = sum(len(visits) for visits in visits_by_zone.values())
    zones_observed = len(visits_by_zone)

    result = (
        "PASS"
        if not errors and price_only_validation.passed and deterministic_generation
        else "FAIL"
    )

    return ScenarioRunResult(
        scenario_id=spec.scenario_id,
        scenario_family=spec.scenario_family,
        specification_fingerprint=spec.specification_fingerprint,
        provider_version=provider_version,
        scenario_schema_version=spec.schema_version,
        chain_version=CHAIN_VERSION,
        chain_fingerprint=CHAIN_FINGERPRINT,
        run_id=run_id,
        row_count=spec.row_count,
        observation_checksum=observation_checksum,
        observation_count=len(observations),
        first_price=observations[0].price,
        last_price=observations[-1].price,
        contiguous_row_ordering=price_only_validation.contiguous_row_ordering,
        finite_price_validation=price_only_validation.finite_price_validation,
        price_only_contract_validation=(
            price_only_validation.price_only_contract_validation
        ),
        deterministic_generation=deterministic_generation,
        errors=tuple(errors),
        result=result,
        completed_visits=completed_visits,
        zones_observed=zones_observed,
        stage3_transition_summary=stage3_summary,
        stage4_graph_summary=stage4_summary,
        stage5_trajectory_summary=stage5_summary,
        stage6_hypothesis_summary=stage6_summary,
    )

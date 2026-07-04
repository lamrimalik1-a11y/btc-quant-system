"""Project 2 Chapter II Phase 2 scenario-runner validation.

Reproduces the exact Chapter I triangular price corpus through the Scenario
Runner (rather than Stage 1's hardcoded generate_price()/build_harnesses())
so that the already-independently-verified Chapter I numbers -- 159
completed visits, 145 transitions, 152 Stage 6 hypotheses, zero
RESEARCH_ATTACKER_PRESSURE observations -- can be used as ground truth to
prove the runner's driving loop is a faithful, bug-free bridge, not just "a
loop that runs without crashing."
"""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any


EXPERIMENT_DIR = Path(__file__).resolve().parent
if str(EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_DIR))

from scenario_contract import (
    PriceObservation,
    ScenarioProviderMetadata,
    ScenarioSpecification,
    _canonical_value,
)
from scenario_primitives import triangular_wave
from scenario_registry import ScenarioRegistry
from scenario_runner import (
    CHAIN_FINGERPRINT,
    CHAIN_VERSION,
    ScenarioRunResult,
    normalized_source_hash,
    run_scenario,
    validate_price_only_observations,
)


# SHA-256 of each frozen Chapter I file, captured from the already-committed
# PHASE1B_PREDICTION_EVOLUTION_STAGE6_STABLE state. Any future accidental
# edit to these files changes their hash and fails this test -- a self-
# contained, git-independent guard, not merely a convention.
_FROZEN_STAGE_FILE_HASHES = {
    "dynamic_mechanics_test.py": "1386eb0ce7a9783414c294c8cd460ada07f661fd2ddd06be3ee14faf78119969",
    "test_snapshot_dynamic_mechanics.py": "75996a24b69298f06db7dc7db6d6932b45c37db4990dbad48818a4c416293b19",
    "test_dynamic_state_transitions.py": "ad35d1207a366ebeefa860d2cf2d0796ad5caf09df857b813dddc2ee47a17656",
    "test_transition_graph.py": "33c6f598bf53d5487f3419003c60640340ec1f0190364e464f885b6d3d534560",
    "test_trajectory_evolution.py": "34f666f6b1f1c829ee54133070d93dae365509ae8555f68a581c3797d0f53f3c",
    "test_prediction_evolution.py": "9f0f740a9755d9b053907f4181ba556d10e1480e3985fa916110f1ad8971f811",
}


class RunnerBaselineProvider:
    """Test-only provider. Reproduces the exact Chapter I triangular wave
    shape via the reusable, tested scenario_primitives.triangular_wave()
    primitive, so the Runner's output can be checked against already-
    verified Chapter I analytical-path ground truth rather than fresh numbers."""

    def metadata(self) -> ScenarioProviderMetadata:
        return ScenarioProviderMetadata(
            scenario_family="RUNNER_VALIDATION_BASELINE",
            provider_version="1",
            schema_version="1",
        )

    def validate_spec(self, spec: ScenarioSpecification) -> None:
        if spec.scenario_family != "RUNNER_VALIDATION_BASELINE":
            raise ValueError("wrong scenario family")
        if spec.schema_version != "1":
            raise ValueError("unsupported schema version")

    def generate(self, spec: ScenarioSpecification) -> tuple[PriceObservation, ...]:
        prices = triangular_wave(
            spec.row_count,
            Decimal(str(spec.parameters["lower"])),
            Decimal(str(spec.parameters["upper"])),
            int(spec.parameters["half_period_rows"]),
        )
        return tuple(
            PriceObservation(row_index=index, price=price)
            for index, price in enumerate(prices, start=1)
        )


def _spec() -> ScenarioSpecification:
    return ScenarioSpecification(
        scenario_id="CH2_PHASE2_RUNNER_BASELINE",
        scenario_family="RUNNER_VALIDATION_BASELINE",
        schema_version="1",
        description=(
            "Runner validation baseline reproducing the exact Chapter I "
            "triangular corpus shape, used only to cross-check runner "
            "wiring against Stage 1 plus Stages 3-6 ground truth."
        ),
        parameters={
            "lower": Decimal("59740"),
            "upper": Decimal("61060"),
            "half_period_rows": 132,
        },
        geometry_parameters={
            "spacing": Decimal("200"),
            "zone_half_width": Decimal("25"),
            "active_window": 3,
            "symbol": "BTCUSDT",
            "market_timestamp": "2026-07-03T12:00:00Z",
            "session_id": "CH2_PHASE2_SCENARIO_RUNNER_VALIDATION",
        },
        row_count=3000,
        start_price=Decimal("60341"),
        expected_behavior_notes=(
            "Deterministic reproduction of the Chapter I triangular corpus; "
            "expected to reproduce 159 completed visits / 145 transitions / "
            "152 Stage 6 hypotheses exactly.",
        ),
        validation_metadata={"chapter": 2, "phase": 2},
        seed_metadata="UNUSED_NO_PRNG",
    )



def _variant_spec() -> ScenarioSpecification:
    return ScenarioSpecification(
        scenario_id="CH2_PHASE2_RUNNER_PARAMETER_VARIANT",
        scenario_family="RUNNER_VALIDATION_BASELINE",
        schema_version="1",
        description="Small parameter variant proving scenario injection.",
        parameters={
            "lower": Decimal("59740"),
            "upper": Decimal("61060"),
            "half_period_rows": 100,
        },
        geometry_parameters={
            "spacing": Decimal("200"),
            "zone_half_width": Decimal("25"),
            "active_window": 3,
            "symbol": "BTCUSDT",
            "market_timestamp": "2026-07-04T12:00:00Z",
            "session_id": "CH2_PHASE2_PARAMETER_VARIANT",
        },
        row_count=600,
        start_price=Decimal("60341"),
        expected_behavior_notes=("Distinct deterministic runner fixture.",),
        validation_metadata={"chapter": 2, "phase": 2, "fixture": "variant"},
        seed_metadata="UNUSED_NO_PRNG",
    )

def _registry() -> ScenarioRegistry:
    registry = ScenarioRegistry()
    registry.register(RunnerBaselineProvider())
    return registry


def _result_canonical_payload(result: ScenarioRunResult) -> str:
    payload = {
        field: _canonical_value(getattr(result, field))
        for field in result.__dataclass_fields__
    }
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _check_frozen_stage_files() -> tuple[bool, list[str]]:
    mismatches: list[str] = []
    for filename, expected_hash in _FROZEN_STAGE_FILE_HASHES.items():
        path = EXPERIMENT_DIR / filename
        try:
            actual_hash = normalized_source_hash(path)
        except FileNotFoundError:
            mismatches.append(f"{filename}:MISSING")
            continue
        if actual_hash != expected_hash:
            mismatches.append(f"{filename}:HASH_MISMATCH")
    return not mismatches, mismatches


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "scenario_runner": False,
        "visits_by_zone_generated": False,
        "stage3": False,
        "stage4": False,
        "stage5": False,
        "stage6": False,
        "determinism": False,
        "price_only_validation": False,
        "parameterized_case": False,
        "no_stage_files_modified": False,
    }

    try:
        spec = _spec()
        registry = _registry()

        results = [run_scenario(registry, spec) for _ in range(3)]
        first = results[0]

        assert first.errors == ()
        assert first.result == "PASS"
        assert first.chain_version == CHAIN_VERSION
        assert first.chain_fingerprint == CHAIN_FINGERPRINT
        assert first.row_count == 3000
        assert first.observation_count == 3000
        checks["scenario_runner"] = True

        assert first.zones_observed == 7
        assert first.completed_visits == 159
        checks["visits_by_zone_generated"] = True

        stage3_summary = first.stage3_transition_summary
        assert stage3_summary["zones_observed"] == 7
        assert stage3_summary["completed_visits"] == 159
        assert stage3_summary["transitions_generated"] == 145
        assert stage3_summary["all_research_prefixed"] is True
        assert stage3_summary["counts_consistent"] is True
        checks["stage3"] = True

        stage4_summary = first.stage4_graph_summary
        assert stage4_summary["zones_observed"] == 7
        assert stage4_summary["transitions_generated"] == 145
        assert stage4_summary["transition_counts"] == {
            "RESEARCH_RECOVERING_TO_RESEARCH_STABLE": 60,
            "RESEARCH_STABLE_TO_RESEARCH_RECOVERING": 61,
            "RESEARCH_STABLE_TO_RESEARCH_STABLE": 24,
        }
        assert stage4_summary["critical_transition_count"] == 0
        assert stage4_summary["absorbing_states"] == []
        checks["stage4"] = True

        stage5_summary = first.stage5_trajectory_summary
        assert stage5_summary["trajectory_records_generated"] == 159
        assert stage5_summary["completed_visits"] == 159
        assert stage5_summary["transitions_generated"] == 145
        assert stage5_summary["unobserved_states"] == ["RESEARCH_ATTACKER_PRESSURE"]
        assert stage5_summary["attacker_pressure_observed"] is False
        assert stage5_summary["predictions_generated"] is False
        checks["stage5"] = True

        stage6_summary = first.stage6_hypothesis_summary
        assert stage6_summary["completed_visits"] == 159
        assert stage6_summary["hypotheses_generated"] == 152
        assert stage6_summary["eligible_hypotheses"] == 110
        assert stage6_summary["confirmed_count"] == 103
        assert stage6_summary["invalidated_count"] == 0
        assert stage6_summary["pending_count"] == 7
        assert stage6_summary["forced_hypothesis_under_weak_evidence"] is False
        assert stage6_summary["predictions_generated"] is False
        checks["stage6"] = True

        payloads = [_result_canonical_payload(result) for result in results]
        deterministic = all(payload == payloads[0] for payload in payloads[1:])
        assert deterministic
        assert all(result.run_id == first.run_id for result in results)
        assert all(
            result.observation_checksum == first.observation_checksum
            for result in results
        )
        checks["determinism"] = True

        observations = tuple(registry.generate(spec))
        price_only = validate_price_only_observations(spec, observations)
        assert price_only.passed
        assert first.contiguous_row_ordering is True
        assert first.finite_price_validation is True
        assert first.price_only_contract_validation is True
        checks["price_only_validation"] = True

        variant_results = [
            run_scenario(registry, _variant_spec()) for _ in range(2)
        ]
        variant_first = variant_results[0]
        assert variant_first.result == "PASS"
        assert variant_first.errors == ()
        assert variant_first.observation_count == 600
        assert variant_first.specification_fingerprint != first.specification_fingerprint
        assert variant_first.observation_checksum != first.observation_checksum
        assert variant_first.run_id != first.run_id
        assert (
            _result_canonical_payload(variant_results[0])
            == _result_canonical_payload(variant_results[1])
        )
        checks["parameterized_case"] = True

        frozen_ok, frozen_mismatches = _check_frozen_stage_files()
        if not frozen_ok:
            errors.extend(f"frozen_file:{item}" for item in frozen_mismatches)
        assert frozen_ok
        checks["no_stage_files_modified"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result}


def main() -> None:
    report = run()
    for field in (
        "scenario_runner",
        "visits_by_zone_generated",
        "stage3",
        "stage4",
        "stage5",
        "stage6",
        "determinism",
        "price_only_validation",
        "parameterized_case",
        "no_stage_files_modified",
    ):
        value = "PASS" if report[field] else "FAIL"
        print(f"{field} = {value}")
    print("chain_adapter = NOT_SEPARATED (integrated into scenario_runner.py)")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Validation for Phase2C serial batch execution over assembled specifications."""

from __future__ import annotations

import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_contract import (
    PriceObservation,
    ScenarioSpecification,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.specification_assembler import (
    AssembledSpecification,
)
from experiments.psychological_levels_dynamic.scenario_generation.batch_execution import (
    execute_batch,
)
from experiments.psychological_levels_dynamic.scenario_generation.execution_contracts import (
    BatchExecutionResult,
)
from experiments.psychological_levels_dynamic.scenario_generation.runner_execution_context import (
    RunnerExecutionContext,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.geometry import (
    GeometryContext,
    GeometryReference,
)

MODULE_PATH = Path(__file__).with_name("batch_execution.py")
FORBIDDEN_IMPORTS = (
    "scenario_catalog.catalog",
    "scenario_catalog.families",
    "compile_program",
    "batch_compiler",
    "batch_specification_assembler",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "core.",
    "engines.",
    "research.",
    "random",
)
FORBIDDEN_SOURCE = (
    "compare",
    "ranking",
    "optimize",
    "learning",
    "catalog scenarios",
)


def _geometry_context() -> GeometryContext:
    center = Decimal("60400")
    half_width = Decimal("25")
    return GeometryContext(
        symbol="BTCUSDT",
        geometry_version="PHASE2C_BATCH_EXECUTION_TEST_GEOMETRY_V1",
        references=(
            GeometryReference(
                zone_id="ZONE_A",
                center_price=center,
                lower_price=center - half_width,
                upper_price=center + half_width,
                half_width=half_width,
            ),
        ),
    )


def _execution_context() -> RunnerExecutionContext:
    return RunnerExecutionContext(
        symbol="BTCUSDT",
        geometry_context=_geometry_context(),
        active_window=0,
        spacing=Decimal("200"),
        zone_half_width=Decimal("25"),
        market_timestamp=1_700_000_000_000,
        session_id="PHASE2C_BATCH_EXECUTION_TEST_SESSION",
        runner_version="PHASE2C_BATCH_EXECUTION_TEST_RUNNER_V1",
    )


def _observations(row_indices: tuple[int, ...] = (1, 2, 3, 4, 5)) -> tuple[PriceObservation, ...]:
    prices = (Decimal("60400"), Decimal("60430"), Decimal("60435"), Decimal("60440"), Decimal("60445"))
    return tuple(
        PriceObservation(row_index=row_index, price=price)
        for row_index, price in zip(row_indices, prices)
    )


def _specification(
    scenario_id: str,
    observations: tuple[PriceObservation, ...],
    include_required_geometry: bool = True,
) -> ScenarioSpecification:
    geometry_parameters: dict[str, Any] = {
        "geometry_fingerprint": "sha256:" + "9" * 64,
        "spacing": Decimal("200"),
        "zone_half_width": Decimal("25"),
        "symbol": "BTCUSDT",
        "market_timestamp": 1_700_000_000_000,
        "session_id": "PHASE2C_BATCH_EXECUTION_TEST_SESSION",
    }
    if include_required_geometry:
        geometry_parameters["active_window"] = 0
    return ScenarioSpecification(
        scenario_id=scenario_id,
        scenario_family="COMPILED_GRAMMAR_PROGRAM",
        schema_version="1",
        description="Batch execution test specification.",
        parameters={"observation_checksum": "sha256:" + scenario_id[-1] * 64},
        geometry_parameters=geometry_parameters,
        row_count=len(observations),
        start_price=observations[0].price,
        expected_behavior_notes=("No expected behavior labels are declared.",),
        validation_metadata={"source": "test_batch_execution"},
        seed_metadata="sha256:" + scenario_id[-1] * 64,
    )


def _assembled(
    scenario_id: str,
    row_indices: tuple[int, ...] = (1, 2, 3, 4, 5),
    include_required_geometry: bool = True,
) -> AssembledSpecification:
    observations = _observations(row_indices)
    return AssembledSpecification(
        specification=_specification(scenario_id, observations, include_required_geometry),
        compiled_observations=observations,
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "successful_batch_execution": False,
        "partial_failure": False,
        "ordering_preserved": False,
        "runner_result_preserved": False,
        "summary_generation": False,
        "fingerprint_determinism": False,
        "cross_process_determinism": False,
        "research_isolation": False,
    }
    try:
        context = _execution_context()
        first = _assembled("SCENARIO_001")
        second = _assembled("SCENARIO_002")
        success_batch = execute_batch((first, second), context, "PHASE2C_BATCH_EXECUTION_TEST_V1")
        assert isinstance(success_batch, BatchExecutionResult)
        assert success_batch.total_scenarios == 2
        assert success_batch.executed_scenarios == 2
        assert success_batch.failed_scenarios == 0
        assert success_batch.skipped_scenarios == 0
        assert success_batch.failed_scenario_ids == ()
        assert all(record.execution_status == "EXECUTED" for record in success_batch.scenario_results)
        checks["successful_batch_execution"] = True

        bad_geometry = _assembled("SCENARIO_003", include_required_geometry=False)
        partial = execute_batch((first, bad_geometry, second), context, "PHASE2C_BATCH_EXECUTION_TEST_V1")
        assert partial.total_scenarios == 3
        assert partial.executed_scenarios == 2
        assert partial.failed_scenarios == 1
        assert partial.failed_scenario_ids == ("SCENARIO_003",)
        assert partial.scenario_results[1].execution_status == "FAILED"
        assert partial.scenario_results[2].scenario_id == "SCENARIO_002"
        checks["partial_failure"] = True

        assert tuple(record.scenario_index for record in partial.scenario_results) == (0, 1, 2)
        assert tuple(record.scenario_id for record in partial.scenario_results) == (
            "SCENARIO_001",
            "SCENARIO_003",
            "SCENARIO_002",
        )
        checks["ordering_preserved"] = True

        bad_rows = _assembled("SCENARIO_004", row_indices=(1, 2, 2, 4, 5))
        runner_fail_batch = execute_batch((bad_rows,), context, "PHASE2C_BATCH_EXECUTION_TEST_V1")
        assert runner_fail_batch.success is False
        assert runner_fail_batch.executed_scenarios == 1
        assert runner_fail_batch.failed_scenarios == 0
        assert runner_fail_batch.scenario_results[0].execution_status == "EXECUTED"
        assert runner_fail_batch.scenario_results[0].runner_result == "FAIL"
        assert "BATCH_HAS_EXECUTED_RUNNER_FAIL" in runner_fail_batch.diagnostics
        checks["runner_result_preserved"] = True

        summary_keys = tuple(key for key, _ in success_batch.scenario_results[0].summary)
        assert summary_keys == (
            "completed_visits",
            "zones_observed",
            "transitions_generated",
            "trajectory_records",
            "eligible_hypotheses",
            "confirmed_hypotheses",
            "pending_hypotheses",
            "runner_result",
        )
        assert success_batch.scenario_results[0].summary[-1][1] in {"PASS", "FAIL"}
        checks["summary_generation"] = True

        repeat = execute_batch((first, second), context, "PHASE2C_BATCH_EXECUTION_TEST_V1")
        assert repeat == success_batch
        assert repeat.batch_execution_fingerprint == success_batch.batch_execution_fingerprint
        partial_repeat = execute_batch((first, bad_geometry, second), context, "PHASE2C_BATCH_EXECUTION_TEST_V1")
        assert partial_repeat == partial
        assert partial.batch_execution_fingerprint != success_batch.batch_execution_fingerprint
        assert runner_fail_batch.batch_execution_fingerprint != success_batch.batch_execution_fingerprint
        checks["fingerprint_determinism"] = True

        if os.environ.get("BATCH_EXECUTION_CHILD") == "1":
            return {
                "success_fingerprint": success_batch.batch_execution_fingerprint,
                "partial_fingerprint": partial.batch_execution_fingerprint,
                "runner_fail_fingerprint": runner_fail_batch.batch_execution_fingerprint,
                "result": "PASS",
            }
        env = dict(os.environ)
        env["BATCH_EXECUTION_CHILD"] = "1"
        child_one = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
        child_two = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
        assert child_one == child_two
        checks["cross_process_determinism"] = True

        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        assert not any(token in imports for token in FORBIDDEN_IMPORTS)
        assert not any(token in source for token in FORBIDDEN_SOURCE)
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    if os.environ.get("BATCH_EXECUTION_CHILD") == "1":
        print(f"success={report['success_fingerprint']}")
        print(f"partial={report['partial_fingerprint']}")
        print(f"runner_fail={report['runner_fail_fingerprint']}")
        print(f"result={report['result']}")
        if report["result"] != "PASS":
            raise SystemExit(1)
        return
    for field in (
        "successful_batch_execution",
        "partial_failure",
        "ordering_preserved",
        "runner_result_preserved",
        "summary_generation",
        "fingerprint_determinism",
        "cross_process_determinism",
        "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
"""Validation for Phase2C execution contracts only."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import FrozenInstanceError, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_generation.execution_contracts import (
    BatchExecutionResult,
    ScenarioExecutionRecord,
    execution_contract_fingerprint,
)

MODULE_PATH = Path(__file__).with_name("execution_contracts.py")
FORBIDDEN_IMPORTS = (
    "scenario_runner",
    "scenario_registry",
    "scenario_primitives",
    "scenario_catalog.catalog",
    "scenario_catalog.families",
    "compiler",
    "batch_compiler",
    "compile_program",
    "assemble_specification",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "core.",
    "engines.",
    "research.",
    "random",
    "time",
    "datetime",
)
FORBIDDEN_SOURCE = (
    "run_scenario",
    "compile_generation_batch",
    "assemble_batch",
    "dynamic_state",
    "research_stable",
    "research_attacker",
)
SHA_1 = "sha256:" + "1" * 64
SHA_2 = "sha256:" + "2" * 64
SHA_3 = "sha256:" + "3" * 64
SHA_4 = "sha256:" + "4" * 64
SHA_5 = "sha256:" + "5" * 64
SHA_6 = "sha256:" + "6" * 64
SHA_7 = "sha256:" + "7" * 64


@dataclass(frozen=True)
class DummyScenarioRunResult:
    completed_visits: int
    transition_count: int
    result: str


def _expect_raises(exception: type[BaseException], callable_: Any) -> None:
    try:
        callable_()
    except exception:
        return
    raise AssertionError(f"expected {exception.__name__}")


def _executed_record(
    index: int = 0,
    scenario_id: str = "SCENARIO_000",
    runner_result: str = "PASS",
) -> ScenarioExecutionRecord:
    run_result = DummyScenarioRunResult(
        completed_visits=3,
        transition_count=2,
        result=runner_result,
    )
    summary = (
        ("completed_visits", 3),
        ("transition_count", 2),
        ("result", runner_result),
    )
    return ScenarioExecutionRecord(
        scenario_id=scenario_id,
        scenario_index=index,
        specification_fingerprint=SHA_1,
        execution_status="EXECUTED",
        scenario_run_result=run_result,
        runner_result=runner_result,
        summary=summary,
        diagnostics=(),
        execution_fingerprint=execution_contract_fingerprint(
            (scenario_id, index, SHA_1, "EXECUTED", runner_result, run_result, summary, ())
        ),
    )


def _failed_record(index: int = 1, scenario_id: str = "SCENARIO_001") -> ScenarioExecutionRecord:
    diagnostics = ("SCENARIO_EXECUTION_FAILED:ValueError",)
    summary = (("result", "FAILED"),)
    return ScenarioExecutionRecord(
        scenario_id=scenario_id,
        scenario_index=index,
        specification_fingerprint=SHA_2,
        execution_status="FAILED",
        scenario_run_result=None,
        runner_result=None,
        summary=summary,
        diagnostics=diagnostics,
        execution_fingerprint=execution_contract_fingerprint(
            (scenario_id, index, SHA_2, "FAILED", None, summary, diagnostics)
        ),
    )


def _skipped_record(index: int = 2, scenario_id: str = "SCENARIO_002") -> ScenarioExecutionRecord:
    diagnostics = ("SCENARIO_SKIPPED:UPSTREAM_FAILURE",)
    summary = (("result", "SKIPPED"),)
    return ScenarioExecutionRecord(
        scenario_id=scenario_id,
        scenario_index=index,
        specification_fingerprint=SHA_3,
        execution_status="SKIPPED",
        scenario_run_result=None,
        runner_result=None,
        summary=summary,
        diagnostics=diagnostics,
        execution_fingerprint=execution_contract_fingerprint(
            (scenario_id, index, SHA_3, "SKIPPED", None, summary, diagnostics)
        ),
    )


def _successful_batch() -> BatchExecutionResult:
    record = _executed_record()
    return BatchExecutionResult(
        success=True,
        total_scenarios=1,
        executed_scenarios=1,
        failed_scenarios=0,
        skipped_scenarios=0,
        scenario_results=(record,),
        failed_scenario_ids=(),
        skipped_scenario_ids=(),
        diagnostics=(),
        source_manifest_fingerprint=SHA_4,
        batch_compilation_fingerprint=SHA_5,
        batch_assembly_fingerprint=SHA_6,
        batch_execution_fingerprint=execution_contract_fingerprint((record, SHA_4, SHA_5, SHA_6)),
        runner_version="EXECUTION_CONTRACTS_TEST_RUNNER_V1",
        batch_execution_version="EXECUTION_CONTRACTS_TEST_BATCH_V1",
    )


def _mixed_batch() -> BatchExecutionResult:
    records = (_executed_record(0, "SCENARIO_000"), _failed_record(1), _skipped_record(2))
    diagnostics = ("BATCH_EXECUTION_INCOMPLETE",)
    return BatchExecutionResult(
        success=False,
        total_scenarios=3,
        executed_scenarios=1,
        failed_scenarios=1,
        skipped_scenarios=1,
        scenario_results=records,
        failed_scenario_ids=("SCENARIO_001",),
        skipped_scenario_ids=("SCENARIO_002",),
        diagnostics=diagnostics,
        source_manifest_fingerprint=SHA_4,
        batch_compilation_fingerprint=SHA_5,
        batch_assembly_fingerprint=SHA_6,
        batch_execution_fingerprint=execution_contract_fingerprint((records, diagnostics, SHA_4, SHA_5, SHA_6)),
        runner_version="EXECUTION_CONTRACTS_TEST_RUNNER_V1",
        batch_execution_version="EXECUTION_CONTRACTS_TEST_BATCH_V1",
    )


def _executed_runner_fail_batch(success: bool) -> BatchExecutionResult:
    record = _executed_record(runner_result="FAIL")
    diagnostics = () if success else ("BATCH_HAS_EXECUTED_RUNNER_FAIL",)
    return BatchExecutionResult(
        success=success,
        total_scenarios=1,
        executed_scenarios=1,
        failed_scenarios=0,
        skipped_scenarios=0,
        scenario_results=(record,),
        failed_scenario_ids=(),
        skipped_scenario_ids=(),
        diagnostics=diagnostics,
        source_manifest_fingerprint=SHA_4,
        batch_compilation_fingerprint=SHA_5,
        batch_assembly_fingerprint=SHA_6,
        batch_execution_fingerprint=execution_contract_fingerprint((record, diagnostics, SHA_4, SHA_5, SHA_6)),
        runner_version="EXECUTION_CONTRACTS_TEST_RUNNER_V1",
        batch_execution_version="EXECUTION_CONTRACTS_TEST_BATCH_V1",
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "scenario_execution_record": False,
        "batch_execution_result": False,
        "runner_result_guard": False,
        "fingerprint_determinism": False,
        "immutability": False,
        "research_isolation": False,
        "cross_process_determinism": False,
    }
    try:
        executed = _executed_record()
        assert executed.execution_status == "EXECUTED"
        assert executed.runner_result == "PASS"
        assert isinstance(executed.scenario_run_result, DummyScenarioRunResult)
        _expect_raises(ValueError, lambda: ScenarioExecutionRecord("", 0, SHA_1, "EXECUTED", executed.scenario_run_result, "PASS", (), (), SHA_7))
        _expect_raises(ValueError, lambda: ScenarioExecutionRecord("S", -1, SHA_1, "EXECUTED", executed.scenario_run_result, "PASS", (), (), SHA_7))
        _expect_raises(ValueError, lambda: ScenarioExecutionRecord("S", 0, "bad", "EXECUTED", executed.scenario_run_result, "PASS", (), (), SHA_7))
        _expect_raises(ValueError, lambda: ScenarioExecutionRecord("S", 0, SHA_1, "BAD", None, None, (), (), SHA_7))
        _expect_raises(TypeError, lambda: ScenarioExecutionRecord("S", 0, SHA_1, "EXECUTED", {"mutable": True}, "PASS", (), (), SHA_7))
        _expect_raises(ValueError, lambda: ScenarioExecutionRecord("S", 0, SHA_1, "EXECUTED", None, "PASS", (), (), SHA_7))
        _expect_raises(ValueError, lambda: ScenarioExecutionRecord("S", 0, SHA_1, "EXECUTED", executed.scenario_run_result, None, (), (), SHA_7))
        _expect_raises(ValueError, lambda: ScenarioExecutionRecord("S", 0, SHA_1, "EXECUTED", executed.scenario_run_result, "UNKNOWN", (), (), SHA_7))
        _expect_raises(ValueError, lambda: ScenarioExecutionRecord("S", 0, SHA_1, "FAILED", executed.scenario_run_result, None, (), ("x",), SHA_7))
        _expect_raises(ValueError, lambda: ScenarioExecutionRecord("S", 0, SHA_1, "FAILED", None, "FAIL", (), ("x",), SHA_7))
        _expect_raises(ValueError, lambda: ScenarioExecutionRecord("S", 0, SHA_1, "FAILED", None, None, (), (), SHA_7))
        checks["scenario_execution_record"] = True

        successful = _successful_batch()
        assert successful.success is True
        assert successful.total_scenarios == 1
        assert successful.scenario_results == (executed,)
        mixed = _mixed_batch()
        assert mixed.success is False
        assert mixed.failed_scenario_ids == ("SCENARIO_001",)
        assert mixed.skipped_scenario_ids == ("SCENARIO_002",)
        _expect_raises(ValueError, lambda: BatchExecutionResult(True, 2, 1, 0, 0, (executed,), (), (), (), SHA_4, SHA_5, SHA_6, SHA_7, "R", "B"))
        _expect_raises(ValueError, lambda: BatchExecutionResult(True, 1, 1, 0, 0, (_failed_record(0, "SCENARIO_000"),), (), (), (), SHA_4, SHA_5, SHA_6, SHA_7, "R", "B"))
        _expect_raises(ValueError, lambda: BatchExecutionResult(False, 1, 0, 1, 0, (_failed_record(0, "SCENARIO_000"),), (), (), ("x",), SHA_4, SHA_5, SHA_6, SHA_7, "R", "B"))
        _expect_raises(ValueError, lambda: BatchExecutionResult(False, 1, 0, 1, 0, (_failed_record(0, "SCENARIO_000"),), ("SCENARIO_000",), (), (), SHA_4, SHA_5, SHA_6, SHA_7, "R", "B"))
        _expect_raises(ValueError, lambda: BatchExecutionResult(True, 1, 1, 0, 0, (executed,), (), (), (), "bad", SHA_5, SHA_6, SHA_7, "R", "B"))
        checks["batch_execution_result"] = True

        _expect_raises(ValueError, lambda: _executed_runner_fail_batch(success=True))
        failed_runner_batch = _executed_runner_fail_batch(success=False)
        assert failed_runner_batch.success is False
        assert failed_runner_batch.executed_scenarios == 1
        assert failed_runner_batch.scenario_results[0].runner_result == "FAIL"
        checks["runner_result_guard"] = True

        fp1 = execution_contract_fingerprint(successful)
        fp2 = execution_contract_fingerprint(_successful_batch())
        fp3 = execution_contract_fingerprint(mixed)
        runner_fail_fp = execution_contract_fingerprint(failed_runner_batch)
        assert fp1 == fp2
        assert fp1 != fp3
        assert fp1 != runner_fail_fp
        assert execution_contract_fingerprint(Decimal("1.0")) == execution_contract_fingerprint(Decimal("1.00"))
        _expect_raises(TypeError, lambda: execution_contract_fingerprint({"not": "canonical"}))
        checks["fingerprint_determinism"] = True

        _expect_raises(FrozenInstanceError, lambda: setattr(executed, "scenario_id", "X"))
        _expect_raises(FrozenInstanceError, lambda: setattr(successful, "success", False))
        checks["immutability"] = True

        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        assert not any(token in imports for token in FORBIDDEN_IMPORTS)
        assert not any(token in source for token in FORBIDDEN_SOURCE)
        checks["research_isolation"] = True

        if os.environ.get("EXECUTION_CONTRACTS_CHILD") == "1":
            return {
                "success_fingerprint": execution_contract_fingerprint(successful),
                "mixed_fingerprint": execution_contract_fingerprint(mixed),
                "runner_fail_fingerprint": execution_contract_fingerprint(failed_runner_batch),
                "result": "PASS",
            }
        env = dict(os.environ)
        env["EXECUTION_CONTRACTS_CHILD"] = "1"
        first = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
        second = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
        assert first == second
        checks["cross_process_determinism"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    if os.environ.get("EXECUTION_CONTRACTS_CHILD") == "1":
        print(f"success={report['success_fingerprint']}")
        print(f"mixed={report['mixed_fingerprint']}")
        print(f"runner_fail={report['runner_fail_fingerprint']}")
        print(f"result={report['result']}")
        if report["result"] != "PASS":
            raise SystemExit(1)
        return
    for field in (
        "scenario_execution_record",
        "batch_execution_result",
        "runner_result_guard",
        "fingerprint_determinism",
        "immutability",
        "research_isolation",
        "cross_process_determinism",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
"""Validation for pure Project 2 research campaign report generation."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_generation.research_report_contracts import (
    ResearchCampaignReport,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_report_generator import (
    RESEARCH_REPORT_GENERATOR_VERSION,
    build_research_campaign_report,
)
from experiments.psychological_levels_dynamic.scenario_generation.test_first_research_campaign_100_execution import (
    _execute_campaign,
)

MODULE_PATH = Path(__file__).with_name("research_report_generator.py")
FORBIDDEN_IMPORTS = (
    "campaign_designer",
    "first_campaign_100_design",
    "generator",
    "manifest_validation",
    "batch_compiler",
    "batch_specification_assembler",
    "batch_execution",
    "scenario_runner",
    "scenario_catalog.",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "core.",
    "engines.",
    "research.",
)
FORBIDDEN_SOURCE_TOKENS = (
    "run_campaign",
    "generate_programs",
    "validate_manifest",
    "compile_generation_batch",
    "assemble_batch",
    "execute_batch",
    "open(",
    "write_text",
    "read_text",
    "ScenarioRunResult",
    "ScenarioExecutionRecord",
    "BatchExecutionResult",
)



def _synthetic_payload(*, generated_count: int, assembled_count: int, passed_count: int, execution_skipped: int) -> Any:
    records = tuple(
        SimpleNamespace(
            execution_status="EXECUTED",
            runner_result="PASS",
            summary=(
                ("completed_visits", 3),
                ("zones_observed", 1),
                ("transitions_generated", 1),
                ("stage4_transitions_generated", 1),
                ("trajectory_records", 3),
                ("eligible_hypotheses", 0),
                ("confirmed_hypotheses", 0),
                ("pending_hypotheses", 0),
                ("runner_result", "PASS"),
            ),
        )
        for _ in range(passed_count)
    )
    return SimpleNamespace(
        family_name="SYNTHETIC_FAMILY",
        coverage_tags=("synthetic",),
        family_pipeline_fingerprint="sha256:" + "1" * 64,
        generation_result=SimpleNamespace(generated_programs=tuple(range(generated_count))),
        batch_assembly_result=SimpleNamespace(assembled_specifications=tuple(range(assembled_count))),
        batch_execution_result=SimpleNamespace(
            executed_scenarios=passed_count,
            failed_scenarios=0,
            skipped_scenarios=execution_skipped,
            scenario_results=records,
            batch_execution_fingerprint="sha256:" + "2" * 64,
        ),
    )
def _report() -> ResearchCampaignReport:
    return build_research_campaign_report(
        _execute_campaign(),
        report_id="PHASE2D_FIRST_RESEARCH_CAMPAIGN_100_REPORT",
        report_version="1",
        report_generator_version=RESEARCH_REPORT_GENERATOR_VERSION,
    )


def _cross_process_report_fingerprint() -> str:
    env = dict(os.environ)
    env["RESEARCH_REPORT_GENERATOR_CHILD"] = "1"
    return subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env).strip()


def _contains_raw_execution_object(value: Any) -> bool:
    type_name = type(value).__name__
    if type_name in {"ScenarioRunResult", "ScenarioExecutionRecord", "BatchExecutionResult"}:
        return True
    if isinstance(value, tuple):
        return any(_contains_raw_execution_object(item) for item in value)
    if is_dataclass(value):
        return any(_contains_raw_execution_object(getattr(value, field.name)) for field in fields(value))
    return False


def _per_family_reconciles(report: ResearchCampaignReport) -> bool:
    families = report.family_summaries
    hypothesis_rows = {
        row[0]: {
            "eligible": row[1],
            "confirmed": row[2],
            "pending": row[3],
            "invalidated": row[4],
        }
        for row in report.hypothesis_summary.per_family_hypothesis_counts
    }
    return all(
        hypothesis_rows[family.family_name]["eligible"] == family.eligible_hypotheses
        and hypothesis_rows[family.family_name]["confirmed"] == family.confirmed_hypotheses
        and hypothesis_rows[family.family_name]["pending"] == family.pending_hypotheses
        and hypothesis_rows[family.family_name]["invalidated"] == 0
        for family in families
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "build_from_real_campaign_execution": False,
        "exact_totals": False,
        "per_family_reconciliation": False,
        "hypothesis_family_name_reconciliation": False,
        "deterministic_fingerprints": False,
        "cross_process_determinism": False,
        "no_reexecution_inside_report_generator": False,
        "research_isolation": False,
        "raw_execution_objects_absent": False,
        "pre_assembly_skips_preserved": False,
    }
    fingerprint = ""
    totals: dict[str, Any] = {}
    try:
        report = _report()
        assert isinstance(report, ResearchCampaignReport)
        checks["build_from_real_campaign_execution"] = True

        totals = {
            "generated": report.coverage_summary.total_scenarios,
            "executed": report.coverage_summary.executed_scenarios,
            "passed": report.coverage_summary.passed_scenarios,
            "failed": report.coverage_summary.failed_scenarios,
            "skipped": report.coverage_summary.skipped_scenarios,
            "zero_visit_scenarios": report.coverage_summary.zero_visit_scenarios,
            "scenarios_with_three_or_more_visits": report.coverage_summary.scenarios_with_three_or_more_visits,
            "scenarios_with_transitions": report.coverage_summary.scenarios_with_transitions,
            "transitions": report.transition_summary.total_transitions,
            "eligible_hypotheses": report.hypothesis_summary.eligible_hypotheses,
        }
        assert totals == {
            "generated": 100,
            "executed": 100,
            "passed": 100,
            "failed": 0,
            "skipped": 0,
            "zero_visit_scenarios": 0,
            "scenarios_with_three_or_more_visits": 100,
            "scenarios_with_transitions": 100,
            "transitions": 260,
            "eligible_hypotheses": 63,
        }
        checks["exact_totals"] = True

        checks["per_family_reconciliation"] = (
            sum(family.scenarios_generated for family in report.family_summaries) == report.coverage_summary.total_scenarios
            and sum(family.scenarios_executed for family in report.family_summaries) == report.coverage_summary.executed_scenarios
            and sum(family.transitions_generated for family in report.family_summaries) == report.transition_summary.total_transitions
            and sum(family.trajectory_records for family in report.family_summaries) == report.trajectory_summary.total_trajectory_records
            and sum(family.eligible_hypotheses for family in report.family_summaries) == report.hypothesis_summary.eligible_hypotheses
        )
        checks["hypothesis_family_name_reconciliation"] = _per_family_reconciles(report)

        repeat = _report()
        assert repeat == report
        assert repeat.report_fingerprint == report.report_fingerprint
        fingerprint = report.report_fingerprint
        checks["deterministic_fingerprints"] = True

        if os.environ.get("RESEARCH_REPORT_GENERATOR_CHILD") == "1":
            checks["cross_process_determinism"] = True
        else:
            first = _cross_process_report_fingerprint()
            second = _cross_process_report_fingerprint()
            assert first == second == report.report_fingerprint
            checks["cross_process_determinism"] = True

        source = MODULE_PATH.read_text(encoding="utf-8")
        lower_source = source.lower()
        imports = "\n".join(
            line.strip()
            for line in lower_source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        assert not any(token.lower() in imports for token in FORBIDDEN_IMPORTS)
        checks["research_isolation"] = True
        assert not any(token in source for token in FORBIDDEN_SOURCE_TOKENS)
        checks["no_reexecution_inside_report_generator"] = True
        checks["raw_execution_objects_absent"] = not _contains_raw_execution_object(report)
        synthetic_family = build_research_campaign_report.__globals__["_family_summary"](
            _synthetic_payload(
                generated_count=10,
                assembled_count=8,
                passed_count=8,
                execution_skipped=0,
            )
        )
        checks["pre_assembly_skips_preserved"] = (
            synthetic_family.scenarios_generated == 10
            and synthetic_family.scenarios_executed == 10
            and synthetic_family.pass_count == 8
            and synthetic_family.fail_count == 0
            and synthetic_family.skipped_count == 2
        )
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {
        **checks,
        "totals": totals,
        "report_fingerprint": fingerprint,
        "errors": errors,
        "result": result_status,
    }


def main() -> None:
    if os.environ.get("RESEARCH_REPORT_GENERATOR_CHILD") == "1":
        print(_report().report_fingerprint)
        return
    report = run()
    for field in (
        "build_from_real_campaign_execution",
        "exact_totals",
        "per_family_reconciliation",
        "hypothesis_family_name_reconciliation",
        "deterministic_fingerprints",
        "cross_process_determinism",
        "no_reexecution_inside_report_generator",
        "research_isolation",
        "raw_execution_objects_absent",
        "pre_assembly_skips_preserved",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"totals = {report['totals']}")
    print(f"report_fingerprint = {report['report_fingerprint']}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)
    print("PHASE2D_FIRST_RESEARCH_CAMPAIGN_100_REPORT_GENERATION PASS")


if __name__ == "__main__":
    main()

"""Execute the first 100-scenario Project 2 campaign through the full pipeline."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_catalog.compiler.geometry import (
    GeometryContext,
    GeometryReference,
)
from experiments.psychological_levels_dynamic.scenario_generation.campaign_designer import (
    CampaignDesignerResult,
    run_campaign,
)
from experiments.psychological_levels_dynamic.scenario_generation.first_campaign_100_design import (
    FIRST_CAMPAIGN_TARGET_COUNT,
    build_campaign_specification,
)
from experiments.psychological_levels_dynamic.scenario_generation.runner_execution_context import (
    RunnerExecutionContext,
)

EXPECTED_FAMILIES = (
    "BASELINE_ENTER_EXIT",
    "DIRECT_PENETRATION",
    "PROGRESSIVE_PENETRATION",
    "WEAK_ATTACKS",
    "STRONG_ATTACKS",
    "ACCEPTED_BREAK",
    "RECLAIM",
    "RAMP_TO_ENTRY",
    "MULTI_RETURN_CYCLES",
    "SPARSE_INTERACTION",
)
MODULE_PATH = Path(__file__)
FORBIDDEN_IMPORTS = (
    "core.",
    "engines.",
    "research.",
    "scenario_catalog.catalog",
    "scenario_catalog.families",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
)


def _geometry_context() -> GeometryContext:
    center = Decimal("60400")
    half_width = Decimal("25")
    return GeometryContext(
        symbol="BTCUSDT",
        geometry_version="PHASE2D_SIGNAL_RICH_CAMPAIGN_100_GEOMETRY_V1",
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
        session_id="PHASE2D_SIGNAL_RICH_CAMPAIGN_100_SESSION",
        runner_version="PHASE2D_SIGNAL_RICH_CAMPAIGN_100_RUNNER_V1",
    )


def _execute_campaign() -> CampaignDesignerResult:
    return run_campaign(build_campaign_specification(), _execution_context())


def _record_signature(result: CampaignDesignerResult) -> tuple[Any, ...]:
    return tuple(
        (
            payload.family_name,
            payload.family_pipeline_fingerprint,
            None if payload.batch_execution_result is None else payload.batch_execution_result.batch_execution_fingerprint,
            tuple(
                (
                    record.scenario_id,
                    record.scenario_index,
                    record.execution_status,
                    record.runner_result,
                    record.summary,
                    record.execution_fingerprint,
                )
                for record in (() if payload.batch_execution_result is None else payload.batch_execution_result.scenario_results)
            ),
        )
        for payload in result.family_execution_payloads
    )


def _stage_signature(result: CampaignDesignerResult) -> tuple[Any, ...]:
    signatures: list[Any] = []
    for payload in result.family_execution_payloads:
        if payload.batch_execution_result is None:
            signatures.append((payload.family_name, None))
            continue
        signatures.append(
            (
                payload.family_name,
                tuple(
                    (
                        None if record.scenario_run_result is None else record.scenario_run_result.stage3_transition_summary,
                        None if record.scenario_run_result is None else record.scenario_run_result.stage4_graph_summary,
                        None if record.scenario_run_result is None else record.scenario_run_result.stage5_trajectory_summary,
                        None if record.scenario_run_result is None else record.scenario_run_result.stage6_hypothesis_summary,
                    )
                    for record in payload.batch_execution_result.scenario_results
                ),
            )
        )
    return tuple(signatures)


def _family_batch_fingerprints(result: CampaignDesignerResult) -> tuple[str, ...]:
    return tuple(
        payload.batch_execution_result.batch_execution_fingerprint
        for payload in result.family_execution_payloads
        if payload.batch_execution_result is not None
    )


def _family_pipeline_fingerprints(result: CampaignDesignerResult) -> tuple[str, ...]:
    return tuple(payload.family_pipeline_fingerprint for payload in result.family_execution_payloads)


def _coverage_tags_do_not_leak(result: CampaignDesignerResult) -> bool:
    for payload in result.family_execution_payloads:
        tags = set(payload.coverage_tags)
        if payload.batch_assembly_result is None or payload.batch_execution_result is None:
            return False
        for assembled in payload.batch_assembly_result.assembled_specifications:
            spec = assembled.specification
            if any(tag in spec.scenario_id for tag in tags):
                return False
            if any(tag in spec.geometry_parameters for tag in tags):
                return False
            if any(tag in repr(spec.expected_behavior_notes) for tag in tags):
                return False
        for record in payload.batch_execution_result.scenario_results:
            if any(tag in repr(record.summary) for tag in tags):
                return False
    return True


def _executed_stage_outputs_present(result: CampaignDesignerResult) -> bool:
    compact_keys = {
        "completed_visits",
        "zones_observed",
        "transitions_generated",
        "stage4_transitions_generated",
        "trajectory_records",
        "eligible_hypotheses",
        "confirmed_hypotheses",
        "pending_hypotheses",
        "runner_result",
    }
    for payload in result.family_execution_payloads:
        if payload.batch_execution_result is None:
            return False
        for record in payload.batch_execution_result.scenario_results:
            if record.execution_status != "EXECUTED":
                continue
            if record.scenario_run_result is None:
                return False
            if record.runner_result not in {"PASS", "FAIL"}:
                return False
            if set(dict(record.summary)) != compact_keys:
                return False
            if record.scenario_run_result.stage3_transition_summary is None:
                return False
            if record.scenario_run_result.stage4_graph_summary is None:
                return False
            if record.scenario_run_result.stage5_trajectory_summary is None:
                return False
            if record.scenario_run_result.stage6_hypothesis_summary is None:
                return False
    return True


def _counts_reconcile(result: CampaignDesignerResult) -> bool:
    compact = result.campaign_result
    return (
        compact.total_generated == sum(item.generated_count for item in compact.family_results)
        and compact.total_executed == sum(item.executed_count for item in compact.family_results)
        and compact.total_passed == sum(item.passed_count for item in compact.family_results)
        and compact.total_failed == sum(item.failed_count for item in compact.family_results)
        and compact.total_skipped == sum(item.skipped_count for item in compact.family_results)
        and compact.total_passed + compact.total_failed + compact.total_skipped == compact.total_executed
    )


def _family_signal_report(result: CampaignDesignerResult) -> tuple[tuple[str, Any], ...]:
    rows: list[tuple[str, Any]] = []
    for payload in result.family_execution_payloads:
        summaries = tuple(dict(record.summary) for record in payload.batch_execution_result.scenario_results)
        completed_visits = sum(summary.get("completed_visits") or 0 for summary in summaries)
        transitions = sum(summary.get("transitions_generated") or 0 for summary in summaries)
        trajectories = sum(summary.get("trajectory_records") or 0 for summary in summaries)
        eligible = sum(summary.get("eligible_hypotheses") or 0 for summary in summaries)
        confirmed = sum(summary.get("confirmed_hypotheses") or 0 for summary in summaries)
        pending = sum(summary.get("pending_hypotheses") or 0 for summary in summaries)
        zero_visit_scenarios = sum(1 for summary in summaries if (summary.get("completed_visits") or 0) == 0)
        scenarios_with_three_or_more_visits = sum(1 for summary in summaries if (summary.get("completed_visits") or 0) >= 3)
        scenarios_with_transitions = sum(1 for summary in summaries if (summary.get("transitions_generated") or 0) > 0)
        rows.append(
            (
                payload.family_name,
                len(summaries),
                completed_visits,
                zero_visit_scenarios,
                scenarios_with_three_or_more_visits,
                transitions,
                scenarios_with_transitions,
                trajectories,
                eligible,
                confirmed,
                pending,
            )
        )
    return tuple(rows)


def _signal_targets(report: tuple[tuple[str, Any], ...]) -> dict[str, Any]:
    return {
        "zero_visit_scenarios": sum(row[3] for row in report),
        "scenarios_with_three_or_more_visits": sum(row[4] for row in report),
        "scenarios_with_transitions": sum(row[6] for row in report),
        "total_transitions": sum(row[5] for row in report),
        "total_eligible_hypotheses": sum(row[8] for row in report),
    }


def _research_isolated() -> bool:
    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    imports = "\n".join(
        line.strip()
        for line in source.splitlines()
        if line.lstrip().startswith(("from ", "import "))
    )
    return not any(token in imports for token in FORBIDDEN_IMPORTS)


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "all_10_families_executed": False,
        "exactly_100_generated": False,
        "family_ordering_preserved": False,
        "family_payloads_preserved": False,
        "campaign_counts_reconcile": False,
        "per_family_batch_execution_present": False,
        "stage_outputs_present": False,
        "deterministic_campaign_result_fingerprint": False,
        "deterministic_campaign_designer_fingerprint": False,
        "deterministic_family_pipeline_fingerprints": False,
        "deterministic_batch_execution_fingerprints": False,
        "deterministic_stage_outputs": False,
        "coverage_tags_do_not_leak": False,
        "zero_visit_scenarios_minimized": False,
        "majority_three_or_more_visits": False,
        "transitions_across_many_scenarios": False,
        "per_family_signal_report_present": False,
        "research_isolation": False,
    }
    summary: dict[str, Any] = {}
    family_signal_report: tuple[tuple[str, Any], ...] = ()
    try:
        result = _execute_campaign()
        repeat = _execute_campaign()

        family_names = tuple(payload.family_name for payload in result.family_execution_payloads)
        checks["all_10_families_executed"] = family_names == EXPECTED_FAMILIES and len(family_names) == 10
        checks["exactly_100_generated"] = result.campaign_result.total_generated == FIRST_CAMPAIGN_TARGET_COUNT
        checks["family_ordering_preserved"] = (
            family_names
            == tuple(family.family_name for family in result.campaign_specification.families)
            == tuple(item.family_name for item in result.campaign_result.family_results)
        )
        checks["family_payloads_preserved"] = all(
            payload.generation_result is not None
            and payload.manifest_validation_result is not None
            and payload.batch_compilation_result is not None
            and payload.batch_assembly_result is not None
            and payload.batch_execution_result is not None
            for payload in result.family_execution_payloads
        )
        checks["campaign_counts_reconcile"] = _counts_reconcile(result)
        checks["per_family_batch_execution_present"] = all(
            payload.batch_execution_result is not None
            and payload.batch_execution_result.total_scenarios == 10
            for payload in result.family_execution_payloads
        )
        checks["stage_outputs_present"] = _executed_stage_outputs_present(result)
        checks["deterministic_campaign_result_fingerprint"] = (
            result.campaign_result.campaign_fingerprint == repeat.campaign_result.campaign_fingerprint
        )
        checks["deterministic_campaign_designer_fingerprint"] = (
            result.campaign_designer_fingerprint == repeat.campaign_designer_fingerprint
        )
        checks["deterministic_family_pipeline_fingerprints"] = (
            _family_pipeline_fingerprints(result) == _family_pipeline_fingerprints(repeat)
        )
        checks["deterministic_batch_execution_fingerprints"] = (
            _family_batch_fingerprints(result) == _family_batch_fingerprints(repeat)
        )
        checks["deterministic_stage_outputs"] = (
            _record_signature(result) == _record_signature(repeat)
            and _stage_signature(result) == _stage_signature(repeat)
        )
        checks["coverage_tags_do_not_leak"] = _coverage_tags_do_not_leak(result)
        family_signal_report = _family_signal_report(result)
        signal_targets = _signal_targets(family_signal_report)
        checks["zero_visit_scenarios_minimized"] = signal_targets["zero_visit_scenarios"] == 0
        checks["majority_three_or_more_visits"] = signal_targets["scenarios_with_three_or_more_visits"] >= 51
        checks["transitions_across_many_scenarios"] = signal_targets["scenarios_with_transitions"] >= 80
        checks["per_family_signal_report_present"] = (
            len(family_signal_report) == 10
            and all(row[1] == 10 for row in family_signal_report)
            and signal_targets["total_transitions"] > 0
        )
        checks["research_isolation"] = _research_isolated()

        summary = {
            "campaign_success": result.success,
            "total_generated": result.campaign_result.total_generated,
            "total_executed": result.campaign_result.total_executed,
            "total_passed": result.campaign_result.total_passed,
            "total_failed": result.campaign_result.total_failed,
            "total_skipped": result.campaign_result.total_skipped,
            "campaign_result_fingerprint": result.campaign_result.campaign_fingerprint,
            "campaign_designer_fingerprint": result.campaign_designer_fingerprint,
            "family_pipeline_fingerprints": _family_pipeline_fingerprints(result),
            "batch_execution_fingerprints": _family_batch_fingerprints(result),
            "signal_targets": signal_targets,
        }
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "summary": summary, "family_signal_report": family_signal_report, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    for field in (
        "all_10_families_executed",
        "exactly_100_generated",
        "family_ordering_preserved",
        "family_payloads_preserved",
        "campaign_counts_reconcile",
        "per_family_batch_execution_present",
        "stage_outputs_present",
        "deterministic_campaign_result_fingerprint",
        "deterministic_campaign_designer_fingerprint",
        "deterministic_family_pipeline_fingerprints",
        "deterministic_batch_execution_fingerprints",
        "deterministic_stage_outputs",
        "coverage_tags_do_not_leak",
        "zero_visit_scenarios_minimized",
        "majority_three_or_more_visits",
        "transitions_across_many_scenarios",
        "per_family_signal_report_present",
        "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print("family_signal_report columns = family, scenarios, visits, zero_visit_scenarios, scenarios_gte3_visits, transitions, scenarios_with_transitions, trajectory_records, eligible_hypotheses, confirmed_hypotheses, pending_hypotheses")
    for row in report["family_signal_report"]:
        print(f"family_signal_report = {row}")
    print(f"summary = {report['summary']}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)
    print("PHASE2D_SIGNAL_RICH_CAMPAIGN_100_REDESIGN PASS")


if __name__ == "__main__":
    main()

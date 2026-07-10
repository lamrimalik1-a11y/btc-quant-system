"""Validation for immutable Project 2 research report contracts."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_generation.research_report_contracts import (
    RESEARCH_REPORT_CONTRACTS_VERSION,
    ResearchCampaignReport,
    ResearchCoverageSummary,
    ResearchFamilySummary,
    ResearchHypothesisSummary,
    ResearchReportMetadata,
    ResearchTrajectorySummary,
    ResearchTransitionSummary,
    research_campaign_report_fingerprint_payload,
    research_coverage_summary_fingerprint_payload,
    research_family_summary_fingerprint_payload,
    research_hypothesis_summary_fingerprint_payload,
    research_report_metadata_fingerprint_payload,
    research_trajectory_summary_fingerprint_payload,
    research_transition_summary_fingerprint_payload,
)

MODULE_PATH = Path(__file__).with_name("research_report_contracts.py")
FORBIDDEN_IMPORTS = (
    "campaign_designer",
    "campaign_contracts",
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
    "ScenarioRunResult",
    "ScenarioExecutionRecord",
    "BatchExecutionResult",
    "GrammarTemplate",
    "ScenarioSpecification",
    "PriceObservation",
)


def _sha(label: str) -> str:
    return "sha256:" + label.lower().zfill(64)[-64:]


def _metadata() -> ResearchReportMetadata:
    family_fingerprints = (_sha("10"), _sha("20"))
    fingerprint = research_report_metadata_fingerprint_payload(
        report_id="REPORT_A",
        report_version="1",
        report_contract_version=RESEARCH_REPORT_CONTRACTS_VERSION,
        campaign_specification_fingerprint=_sha("1"),
        campaign_result_fingerprint=_sha("2"),
        campaign_designer_fingerprint=_sha("3"),
        family_pipeline_fingerprints=family_fingerprints,
    )
    return ResearchReportMetadata(
        report_id="REPORT_A",
        report_version="1",
        report_contract_version=RESEARCH_REPORT_CONTRACTS_VERSION,
        campaign_specification_fingerprint=_sha("1"),
        campaign_result_fingerprint=_sha("2"),
        campaign_designer_fingerprint=_sha("3"),
        family_pipeline_fingerprints=family_fingerprints,
        metadata_fingerprint=fingerprint,
    )


def _coverage() -> ResearchCoverageSummary:
    tags = ("baseline_cycle", "direct_penetration")
    fingerprint = research_coverage_summary_fingerprint_payload(
        total_families=2,
        total_scenarios=20,
        executed_scenarios=20,
        passed_scenarios=20,
        failed_scenarios=0,
        skipped_scenarios=0,
        zero_visit_scenarios=0,
        scenarios_with_three_or_more_visits=20,
        scenarios_with_transitions=20,
        coverage_tags=tags,
    )
    return ResearchCoverageSummary(
        total_families=2,
        total_scenarios=20,
        executed_scenarios=20,
        passed_scenarios=20,
        failed_scenarios=0,
        skipped_scenarios=0,
        zero_visit_scenarios=0,
        scenarios_with_three_or_more_visits=20,
        scenarios_with_transitions=20,
        coverage_tags=tags,
        coverage_fingerprint=fingerprint,
    )


def _family(
    name: str,
    tags: tuple[str, ...],
    pipeline_fingerprint: str,
    batch_fingerprint: str,
    transitions: int,
    trajectories: int,
    eligible: int,
    pending: int,
) -> ResearchFamilySummary:
    fingerprint = research_family_summary_fingerprint_payload(
        family_name=name,
        coverage_tags=tags,
        scenarios_generated=10,
        scenarios_executed=10,
        pass_count=10,
        fail_count=0,
        skipped_count=0,
        completed_visits=50,
        zero_visit_scenarios=0,
        scenarios_with_three_or_more_visits=10,
        transitions_generated=transitions,
        trajectory_records=trajectories,
        eligible_hypotheses=eligible,
        confirmed_hypotheses=0,
        pending_hypotheses=pending,
        family_pipeline_fingerprint=pipeline_fingerprint,
        batch_execution_fingerprint=batch_fingerprint,
    )
    return ResearchFamilySummary(
        family_name=name,
        coverage_tags=tags,
        scenarios_generated=10,
        scenarios_executed=10,
        pass_count=10,
        fail_count=0,
        skipped_count=0,
        completed_visits=50,
        zero_visit_scenarios=0,
        scenarios_with_three_or_more_visits=10,
        transitions_generated=transitions,
        trajectory_records=trajectories,
        eligible_hypotheses=eligible,
        confirmed_hypotheses=0,
        pending_hypotheses=pending,
        family_pipeline_fingerprint=pipeline_fingerprint,
        batch_execution_fingerprint=batch_fingerprint,
        family_fingerprint=fingerprint,
    )


def _families() -> tuple[ResearchFamilySummary, ...]:
    return (
        _family("BASELINE_ENTER_EXIT", ("baseline_cycle",), _sha("10"), _sha("11"), 30, 50, 10, 10),
        _family("DIRECT_PENETRATION", ("direct_penetration",), _sha("20"), _sha("21"), 30, 50, 10, 10),
    )


def _transition_summary() -> ResearchTransitionSummary:
    fingerprint = research_transition_summary_fingerprint_payload(
        total_transitions=60,
        scenarios_with_transitions=20,
        transition_counts=(("RESEARCH_STABLE_TO_RESEARCH_STABLE", 60),),
        per_family_transition_counts=(("BASELINE_ENTER_EXIT", 30), ("DIRECT_PENETRATION", 30)),
        rare_transition_types=(),
        absent_transition_types=("RESEARCH_STABLE_TO_RESEARCH_RECOVERING",),
    )
    return ResearchTransitionSummary(
        total_transitions=60,
        scenarios_with_transitions=20,
        transition_counts=(("RESEARCH_STABLE_TO_RESEARCH_STABLE", 60),),
        per_family_transition_counts=(("BASELINE_ENTER_EXIT", 30), ("DIRECT_PENETRATION", 30)),
        rare_transition_types=(),
        absent_transition_types=("RESEARCH_STABLE_TO_RESEARCH_RECOVERING",),
        transition_fingerprint=fingerprint,
    )


def _trajectory_summary() -> ResearchTrajectorySummary:
    fingerprint = research_trajectory_summary_fingerprint_payload(
        total_trajectory_records=100,
        per_family_trajectory_records=(("BASELINE_ENTER_EXIT", 50), ("DIRECT_PENETRATION", 50)),
        observed_states=("RESEARCH_STABLE",),
        unobserved_states=("RESEARCH_ATTACKER_PRESSURE", "RESEARCH_RECOVERING"),
        sample_sufficiency_counts=(("INSUFFICIENT_SAMPLE", 0), ("SUFFICIENT_SAMPLE", 20)),
        zones_with_no_transitions=(),
    )
    return ResearchTrajectorySummary(
        total_trajectory_records=100,
        per_family_trajectory_records=(("BASELINE_ENTER_EXIT", 50), ("DIRECT_PENETRATION", 50)),
        observed_states=("RESEARCH_STABLE",),
        unobserved_states=("RESEARCH_ATTACKER_PRESSURE", "RESEARCH_RECOVERING"),
        sample_sufficiency_counts=(("INSUFFICIENT_SAMPLE", 0), ("SUFFICIENT_SAMPLE", 20)),
        zones_with_no_transitions=(),
        trajectory_fingerprint=fingerprint,
    )


def _hypothesis_summary() -> ResearchHypothesisSummary:
    rows = (("BASELINE_ENTER_EXIT", 10, 0, 10, 0), ("DIRECT_PENETRATION", 10, 0, 10, 0))
    fingerprint = research_hypothesis_summary_fingerprint_payload(
        eligible_hypotheses=20,
        confirmed_hypotheses=0,
        pending_hypotheses=20,
        invalidated_hypotheses=0,
        per_family_hypothesis_counts=rows,
        attacker_pressure_observed=False,
        predictions_generated=False,
    )
    return ResearchHypothesisSummary(
        eligible_hypotheses=20,
        confirmed_hypotheses=0,
        pending_hypotheses=20,
        invalidated_hypotheses=0,
        per_family_hypothesis_counts=rows,
        attacker_pressure_observed=False,
        predictions_generated=False,
        hypothesis_fingerprint=fingerprint,
    )


def _report() -> ResearchCampaignReport:
    metadata = _metadata()
    coverage = _coverage()
    families = _families()
    transitions = _transition_summary()
    trajectories = _trajectory_summary()
    hypotheses = _hypothesis_summary()
    diagnostics: tuple[str, ...] = ()
    fingerprint = research_campaign_report_fingerprint_payload(
        metadata=metadata,
        coverage_summary=coverage,
        family_summaries=families,
        transition_summary=transitions,
        trajectory_summary=trajectories,
        hypothesis_summary=hypotheses,
        diagnostics=diagnostics,
    )
    return ResearchCampaignReport(
        metadata=metadata,
        coverage_summary=coverage,
        family_summaries=families,
        transition_summary=transitions,
        trajectory_summary=trajectories,
        hypothesis_summary=hypotheses,
        diagnostics=diagnostics,
        report_fingerprint=fingerprint,
    )


def _cross_process_report_fingerprint() -> str:
    env = dict(os.environ)
    env["RESEARCH_REPORT_CONTRACTS_CHILD"] = "1"
    return subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env).strip()


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "valid_construction": False,
        "invalid_fingerprints_rejected": False,
        "immutability": False,
        "deterministic_fingerprints": False,
        "canonical_ordering": False,
        "count_reconciliation": False,
        "report_hypothesis_reconciliation": False,
        "report_transition_coverage_reconciliation": False,
        "cross_process_determinism": False,
        "research_isolation": False,
        "no_execution_generation_report_logic": False,
    }
    fingerprint = ""
    try:
        report = _report()
        assert isinstance(report.metadata, ResearchReportMetadata)
        assert isinstance(report.coverage_summary, ResearchCoverageSummary)
        assert isinstance(report.transition_summary, ResearchTransitionSummary)
        assert isinstance(report.trajectory_summary, ResearchTrajectorySummary)
        assert isinstance(report.hypothesis_summary, ResearchHypothesisSummary)
        checks["valid_construction"] = True

        try:
            ResearchCoverageSummary(
                total_families=1,
                total_scenarios=1,
                executed_scenarios=1,
                passed_scenarios=1,
                failed_scenarios=0,
                skipped_scenarios=0,
                zero_visit_scenarios=0,
                scenarios_with_three_or_more_visits=1,
                scenarios_with_transitions=1,
                coverage_tags=("tag",),
                coverage_fingerprint="bad",
            )
        except ValueError:
            checks["invalid_fingerprints_rejected"] = True

        try:
            report.metadata.report_id = "MUTATE"
        except FrozenInstanceError:
            checks["immutability"] = True

        repeat = _report()
        assert repeat == report
        assert repeat.report_fingerprint == report.report_fingerprint
        fingerprint = report.report_fingerprint
        checks["deterministic_fingerprints"] = True

        try:
            ResearchCoverageSummary(
                total_families=1,
                total_scenarios=1,
                executed_scenarios=1,
                passed_scenarios=1,
                failed_scenarios=0,
                skipped_scenarios=0,
                zero_visit_scenarios=0,
                scenarios_with_three_or_more_visits=1,
                scenarios_with_transitions=1,
                coverage_tags=("z_tag", "a_tag"),
                coverage_fingerprint=_sha("badcafe"),
            )
        except ValueError:
            checks["canonical_ordering"] = True

        try:
            ResearchCoverageSummary(
                total_families=1,
                total_scenarios=2,
                executed_scenarios=2,
                passed_scenarios=2,
                failed_scenarios=1,
                skipped_scenarios=0,
                zero_visit_scenarios=0,
                scenarios_with_three_or_more_visits=2,
                scenarios_with_transitions=2,
                coverage_tags=("tag",),
                coverage_fingerprint=_sha("badf00d"),
            )
        except ValueError:
            checks["count_reconciliation"] = True


        metadata = _metadata()
        coverage = _coverage()
        families = _families()
        transitions = _transition_summary()
        trajectories = _trajectory_summary()
        diagnostics: tuple[str, ...] = ()

        bad_hypotheses = ResearchHypothesisSummary(
            eligible_hypotheses=20,
            confirmed_hypotheses=1,
            pending_hypotheses=19,
            invalidated_hypotheses=0,
            per_family_hypothesis_counts=(
                ("BASELINE_ENTER_EXIT", 10, 1, 9, 0),
                ("DIRECT_PENETRATION", 10, 0, 10, 0),
            ),
            attacker_pressure_observed=False,
            predictions_generated=False,
            hypothesis_fingerprint=research_hypothesis_summary_fingerprint_payload(
                eligible_hypotheses=20,
                confirmed_hypotheses=1,
                pending_hypotheses=19,
                invalidated_hypotheses=0,
                per_family_hypothesis_counts=(
                    ("BASELINE_ENTER_EXIT", 10, 1, 9, 0),
                    ("DIRECT_PENETRATION", 10, 0, 10, 0),
                ),
                attacker_pressure_observed=False,
                predictions_generated=False,
            ),
        )
        try:
            ResearchCampaignReport(
                metadata=metadata,
                coverage_summary=coverage,
                family_summaries=families,
                transition_summary=transitions,
                trajectory_summary=trajectories,
                hypothesis_summary=bad_hypotheses,
                diagnostics=diagnostics,
                report_fingerprint=research_campaign_report_fingerprint_payload(
                    metadata=metadata,
                    coverage_summary=coverage,
                    family_summaries=families,
                    transition_summary=transitions,
                    trajectory_summary=trajectories,
                    hypothesis_summary=bad_hypotheses,
                    diagnostics=diagnostics,
                ),
            )
        except ValueError:
            checks["report_hypothesis_reconciliation"] = True

        bad_transition_fingerprint = research_transition_summary_fingerprint_payload(
            total_transitions=60,
            scenarios_with_transitions=19,
            transition_counts=(("RESEARCH_STABLE_TO_RESEARCH_STABLE", 60),),
            per_family_transition_counts=(("BASELINE_ENTER_EXIT", 30), ("DIRECT_PENETRATION", 30)),
            rare_transition_types=(),
            absent_transition_types=("RESEARCH_STABLE_TO_RESEARCH_RECOVERING",),
        )
        bad_transitions = ResearchTransitionSummary(
            total_transitions=60,
            scenarios_with_transitions=19,
            transition_counts=(("RESEARCH_STABLE_TO_RESEARCH_STABLE", 60),),
            per_family_transition_counts=(("BASELINE_ENTER_EXIT", 30), ("DIRECT_PENETRATION", 30)),
            rare_transition_types=(),
            absent_transition_types=("RESEARCH_STABLE_TO_RESEARCH_RECOVERING",),
            transition_fingerprint=bad_transition_fingerprint,
        )
        try:
            ResearchCampaignReport(
                metadata=metadata,
                coverage_summary=coverage,
                family_summaries=families,
                transition_summary=bad_transitions,
                trajectory_summary=trajectories,
                hypothesis_summary=_hypothesis_summary(),
                diagnostics=diagnostics,
                report_fingerprint=research_campaign_report_fingerprint_payload(
                    metadata=metadata,
                    coverage_summary=coverage,
                    family_summaries=families,
                    transition_summary=bad_transitions,
                    trajectory_summary=trajectories,
                    hypothesis_summary=_hypothesis_summary(),
                    diagnostics=diagnostics,
                ),
            )
        except ValueError:
            checks["report_transition_coverage_reconciliation"] = True
        if os.environ.get("RESEARCH_REPORT_CONTRACTS_CHILD") == "1":
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
        checks["no_execution_generation_report_logic"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "report_fingerprint": fingerprint, "errors": errors, "result": result_status}


def main() -> None:
    if os.environ.get("RESEARCH_REPORT_CONTRACTS_CHILD") == "1":
        print(_report().report_fingerprint)
        return
    report = run()
    for field in (
        "valid_construction",
        "invalid_fingerprints_rejected",
        "immutability",
        "deterministic_fingerprints",
        "canonical_ordering",
        "count_reconciliation",
        "report_hypothesis_reconciliation",
        "report_transition_coverage_reconciliation",
        "cross_process_determinism",
        "research_isolation",
        "no_execution_generation_report_logic",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"report_fingerprint = {report['report_fingerprint']}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)
    print("PHASE2D_FIRST_RESEARCH_CAMPAIGN_100_REPORT_CONTRACTS PASS")


if __name__ == "__main__":
    main()

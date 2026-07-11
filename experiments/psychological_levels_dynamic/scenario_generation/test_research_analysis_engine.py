"""Validation for pure Project 2 research analysis engine."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_generation.research_analysis_contracts import (
    ResearchCampaignAnalysis,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_analysis_engine import (
    RESEARCH_ANALYSIS_ENGINE_VERSION,
    analyze_research_campaign_report,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_report_generator import (
    RESEARCH_REPORT_GENERATOR_VERSION,
    build_research_campaign_report,
)
from experiments.psychological_levels_dynamic.scenario_generation.test_first_research_campaign_100_execution import (
    _execute_campaign,
)

MODULE_PATH = Path(__file__).with_name("research_analysis_engine.py")
FORBIDDEN_IMPORTS = (
    "campaign_designer",
    "campaign_contracts",
    "first_campaign_100_design",
    "generator",
    "manifest_validation",
    "batch_compiler",
    "batch_specification_assembler",
    "batch_execution",
    "research_report_generator",
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
    "build_research_campaign_report",
    "CampaignDesignerResult",
    "CampaignResult",
    "CampaignFamilyExecutionPayload",
    "BatchExecutionResult",
    "ScenarioExecutionRecord",
    "ScenarioRunResult",
    "PriceObservation",
    "ResearchComparisonAnalysis",
)
BANNED_PROSE_FRAGMENTS = (
    "buy",
    "sell",
    "entry recommendation",
    "exit recommendation",
    "forecast",
    "strategy ranking",
    "machine learning",
    "learned threshold",
    "better",
    "stronger",
    "improved",
    "proven",
    "confirms",
    "suggests",
    "effect",
    "impact",
    "lift",
    "gain",
    "accuracy",
    "performance",
)


def _report() -> Any:
    return build_research_campaign_report(
        _execute_campaign(),
        report_id="PHASE2D_FIRST_RESEARCH_CAMPAIGN_100_REPORT",
        report_version="1",
        report_generator_version=RESEARCH_REPORT_GENERATOR_VERSION,
    )


def _analysis() -> ResearchCampaignAnalysis:
    return analyze_research_campaign_report(
        _report(),
        analysis_id="PHASE2E_RESEARCH_ANALYSIS_ENGINE",
        analysis_version="1",
        analysis_engine_version=RESEARCH_ANALYSIS_ENGINE_VERSION,
    )


def _cross_process_analysis_fingerprint() -> str:
    env = dict(os.environ)
    env["RESEARCH_ANALYSIS_ENGINE_CHILD"] = "1"
    return subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env).strip()


def _contains_raw_upstream_object(value: Any) -> bool:
    type_name = type(value).__name__
    if type_name in {
        "ResearchCampaignReport",
        "CampaignDesignerResult",
        "ScenarioRunResult",
        "ScenarioExecutionRecord",
        "BatchExecutionResult",
    }:
        return True
    if isinstance(value, tuple):
        return any(_contains_raw_upstream_object(item) for item in value)
    if is_dataclass(value):
        return any(_contains_raw_upstream_object(getattr(value, field.name)) for field in fields(value))
    return False


def _expected_rate(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return Decimal(numerator) / Decimal(denominator)


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "build_analysis_from_committed_report": False,
        "copied_totals_preserved": False,
        "computed_densities_verified": False,
        "computed_rates_verified": False,
        "family_reconciliation_by_family_name": False,
        "coverage_reconciliation": False,
        "top_contributor_calculations": False,
        "classification_rules": False,
        "zero_denominator_none_behavior": False,
        "deterministic_fingerprints": False,
        "cross_process_determinism": False,
        "canonical_ordering": False,
        "no_raw_upstream_objects_embedded": False,
        "no_report_regeneration_or_execution": False,
        "no_comparison_logic": False,
        "forbidden_imports": False,
        "banned_language_scan": False,
        "research_isolation": False,
    }
    fingerprint = ""
    totals: dict[str, Any] = {}
    try:
        report = _report()
        analysis = analyze_research_campaign_report(
            report,
            analysis_id="PHASE2E_RESEARCH_ANALYSIS_ENGINE",
            analysis_version="1",
            analysis_engine_version=RESEARCH_ANALYSIS_ENGINE_VERSION,
        )
        assert isinstance(analysis, ResearchCampaignAnalysis)
        checks["build_analysis_from_committed_report"] = True

        totals = {
            "generated": analysis.coverage_analysis.scenarios_generated,
            "executed": analysis.coverage_analysis.scenarios_executed,
            "zero_visit_scenarios": analysis.coverage_analysis.zero_visit_scenarios,
            "scenarios_with_three_or_more_visits": analysis.coverage_analysis.scenarios_with_three_or_more_visits,
            "scenarios_with_transitions": analysis.coverage_analysis.scenarios_with_transitions,
            "transitions": analysis.transition_analysis.total_transitions,
            "trajectory_records": analysis.trajectory_analysis.total_trajectory_records,
            "eligible_hypotheses": analysis.hypothesis_analysis.eligible_hypotheses,
            "confirmed_hypotheses": analysis.hypothesis_analysis.confirmed_hypotheses,
            "pending_hypotheses": analysis.hypothesis_analysis.pending_hypotheses,
        }
        assert totals == {
            "generated": 100,
            "executed": 100,
            "zero_visit_scenarios": 0,
            "scenarios_with_three_or_more_visits": 100,
            "scenarios_with_transitions": 100,
            "transitions": 260,
            "trajectory_records": 460,
            "eligible_hypotheses": 63,
            "confirmed_hypotheses": 10,
            "pending_hypotheses": 53,
        }
        checks["copied_totals_preserved"] = (
            analysis.metadata.source_report_fingerprints == (report.report_fingerprint,)
            and analysis.metadata.source_campaign_result_fingerprint == report.metadata.campaign_result_fingerprint
            and analysis.metadata.source_campaign_designer_fingerprint == report.metadata.campaign_designer_fingerprint
            and analysis.coverage_analysis.scenarios_generated == report.coverage_summary.total_scenarios
            and analysis.transition_analysis.total_transitions == report.transition_summary.total_transitions
            and analysis.trajectory_analysis.total_trajectory_records == report.trajectory_summary.total_trajectory_records
            and analysis.hypothesis_analysis.eligible_hypotheses == report.hypothesis_summary.eligible_hypotheses
        )

        checks["computed_densities_verified"] = all(
            family.visit_density == _expected_rate(family.completed_visits, family.scenarios_generated)
            and family.transition_density == _expected_rate(family.transitions, family.scenarios_generated)
            and family.trajectory_density == _expected_rate(family.trajectory_records, family.scenarios_generated)
            for family in analysis.family_analyses
        ) and (
            analysis.transition_analysis.transition_density
            == _expected_rate(
                analysis.transition_analysis.total_transitions,
                analysis.transition_analysis.scenarios_with_transitions,
            )
            and analysis.trajectory_analysis.trajectory_density
            == _expected_rate(
                analysis.trajectory_analysis.total_trajectory_records,
                analysis.coverage_analysis.scenarios_generated,
            )
        )
        checks["computed_rates_verified"] = all(
            family.eligibility_rate == _expected_rate(family.eligible_hypotheses, family.scenarios_generated)
            and family.confirmation_rate == _expected_rate(family.confirmed_hypotheses, family.eligible_hypotheses)
            and family.pending_rate == _expected_rate(family.pending_hypotheses, family.eligible_hypotheses)
            for family in analysis.family_analyses
        ) and (
            analysis.coverage_analysis.zero_visit_rate == Decimal("0")
            and analysis.coverage_analysis.three_plus_visit_rate == Decimal("1")
            and analysis.coverage_analysis.transition_coverage_rate == Decimal("1")
            and analysis.hypothesis_analysis.eligibility_rate == Decimal("0.63")
            and analysis.hypothesis_analysis.confirmation_rate == Decimal(10) / Decimal(63)
            and analysis.hypothesis_analysis.pending_rate == Decimal(53) / Decimal(63)
        )

        family_map = {family.family_name: family for family in analysis.family_analyses}
        hypothesis_map = {row[0]: row for row in analysis.hypothesis_analysis.per_family_hypothesis_counts}
        checks["family_reconciliation_by_family_name"] = set(family_map) == set(hypothesis_map) and all(
            hypothesis_map[name][1:] == (
                family.eligible_hypotheses,
                family.confirmed_hypotheses,
                family.pending_hypotheses,
            )
            for name, family in family_map.items()
        )
        coverage_counts: dict[str, int] = {}
        for family in analysis.family_analyses:
            for tag in family.coverage_tags:
                coverage_counts[tag] = coverage_counts.get(tag, 0) + 1
        checks["coverage_reconciliation"] = (
            analysis.coverage_analysis.coverage_tag_family_counts == tuple(sorted(coverage_counts.items()))
            and analysis.coverage_analysis.unique_coverage_tags == tuple(sorted(coverage_counts))
            and analysis.coverage_analysis.shared_coverage_tags
            == tuple(sorted(tag for tag, count in coverage_counts.items() if count > 1))
        )

        top_transition = max(
            analysis.transition_analysis.per_family_transition_counts,
            key=lambda item: (item[1], tuple(reversed(item[0]))),
        )
        top_trajectory = max(
            analysis.trajectory_analysis.per_family_trajectory_records,
            key=lambda item: (item[1], tuple(reversed(item[0]))),
        )
        top_hypothesis = max(
            ((row[0], row[1]) for row in analysis.hypothesis_analysis.per_family_hypothesis_counts),
            key=lambda item: (item[1], tuple(reversed(item[0]))),
        )
        checks["top_contributor_calculations"] = (
            analysis.transition_analysis.top_transition_contributor_family_name == top_transition[0]
            and analysis.transition_analysis.top_transition_contributor_share
            == _expected_rate(top_transition[1], analysis.transition_analysis.total_transitions)
            and analysis.trajectory_analysis.top_trajectory_contributor_family_name == top_trajectory[0]
            and analysis.trajectory_analysis.top_trajectory_contributor_share
            == _expected_rate(top_trajectory[1], analysis.trajectory_analysis.total_trajectory_records)
            and analysis.hypothesis_analysis.top_eligible_hypothesis_family_name == top_hypothesis[0]
            and analysis.hypothesis_analysis.top_eligible_hypothesis_family_share
            == _expected_rate(top_hypothesis[1], analysis.hypothesis_analysis.eligible_hypotheses)
        )
        expected_richness = {0: "NO_SIGNAL", 1: "LOW_SIGNAL", 2: "MEDIUM_SIGNAL", 3: "MEDIUM_SIGNAL", 4: "RICH_SIGNAL"}
        checks["classification_rules"] = all(
            family.signal_dimension_count
            == sum(
                1
                for value in (
                    family.completed_visits,
                    family.transitions,
                    family.trajectory_records,
                    family.eligible_hypotheses,
                )
                if value > 0
            )
            and family.signal_richness_class == expected_richness[family.signal_dimension_count]
            and (
                (family.eligible_hypotheses > 0 and family.sample_sufficiency_class == "SUFFICIENT_SAMPLE")
                or (family.eligible_hypotheses == 0 and family.sample_sufficiency_class == "INSUFFICIENT_SAMPLE")
            )
            for family in analysis.family_analyses
        )

        zero_report = build_research_campaign_report.__globals__["_family_summary"]
        synthetic_family = zero_report(
            type(
                "Payload",
                (),
                {
                    "family_name": "ZERO_SIGNAL_FAMILY",
                    "coverage_tags": ("zero_signal",),
                    "family_pipeline_fingerprint": "sha256:" + "1" * 64,
                    "generation_result": type("Generation", (), {"generated_programs": ()})(),
                    "batch_assembly_result": type("Assembly", (), {"assembled_specifications": ()})(),
                    "batch_execution_result": type(
                        "Execution",
                        (),
                        {
                            "failed_scenarios": 0,
                            "skipped_scenarios": 0,
                            "scenario_results": (),
                            "batch_execution_fingerprint": "sha256:" + "2" * 64,
                        },
                    )(),
                },
            )()
        )
        zero_analysis = analyze_research_campaign_report(
            build_research_campaign_report(
                type(
                    "Campaign",
                    (),
                    {
                        "family_execution_payloads": (
                            type(
                                "Payload",
                                (),
                                {
                                    "family_name": synthetic_family.family_name,
                                    "coverage_tags": synthetic_family.coverage_tags,
                                    "family_pipeline_fingerprint": synthetic_family.family_pipeline_fingerprint,
                                    "generation_result": type("Generation", (), {"generated_programs": ()})(),
                                    "batch_assembly_result": type("Assembly", (), {"assembled_specifications": ()})(),
                                    "batch_execution_result": type(
                                        "Execution",
                                        (),
                                        {
                                            "failed_scenarios": 0,
                                            "skipped_scenarios": 0,
                                            "scenario_results": (),
                                            "batch_execution_fingerprint": synthetic_family.batch_execution_fingerprint,
                                        },
                                    )(),
                                },
                            )(),
                        ),
                        "campaign_specification": type(
                            "Spec",
                            (),
                            {"campaign_specification_fingerprint": "sha256:" + "3" * 64},
                        )(),
                        "campaign_result": type("Result", (), {"campaign_fingerprint": "sha256:" + "4" * 64})(),
                        "campaign_designer_fingerprint": "sha256:" + "5" * 64,
                        "diagnostics": (),
                    },
                )(),
                report_id="ZERO_SIGNAL_REPORT",
                report_version="1",
                report_generator_version=RESEARCH_REPORT_GENERATOR_VERSION,
            ),
            analysis_id="ZERO_SIGNAL_ANALYSIS",
            analysis_version="1",
            analysis_engine_version=RESEARCH_ANALYSIS_ENGINE_VERSION,
        )
        zero_family_analysis = zero_analysis.family_analyses[0]
        checks["zero_denominator_none_behavior"] = (
            zero_family_analysis.visit_density is None
            and zero_family_analysis.transition_density is None
            and zero_family_analysis.trajectory_density is None
            and zero_family_analysis.eligibility_rate is None
            and zero_family_analysis.confirmation_rate is None
            and zero_family_analysis.pending_rate is None
            and zero_family_analysis.signal_richness_class == "NO_SIGNAL"
            and zero_family_analysis.sample_sufficiency_class == "NOT_APPLICABLE"
        )

        repeat = analyze_research_campaign_report(
            report,
            analysis_id="PHASE2E_RESEARCH_ANALYSIS_ENGINE",
            analysis_version="1",
            analysis_engine_version=RESEARCH_ANALYSIS_ENGINE_VERSION,
        )
        assert repeat == analysis
        fingerprint = analysis.campaign_analysis_fingerprint
        checks["deterministic_fingerprints"] = repeat.campaign_analysis_fingerprint == fingerprint

        if os.environ.get("RESEARCH_ANALYSIS_ENGINE_CHILD") == "1":
            checks["cross_process_determinism"] = True
        else:
            first = _cross_process_analysis_fingerprint()
            second = _cross_process_analysis_fingerprint()
            assert first == second == fingerprint
            checks["cross_process_determinism"] = True

        checks["canonical_ordering"] = (
            tuple(family.family_name for family in analysis.family_analyses)
            == tuple(sorted(family.family_name for family in analysis.family_analyses))
            and analysis.diagnostics == tuple(sorted(analysis.diagnostics))
        )
        checks["no_raw_upstream_objects_embedded"] = not _contains_raw_upstream_object(analysis)

        source = MODULE_PATH.read_text(encoding="utf-8")
        lower_source = source.lower()
        imports = "\n".join(
            line.strip()
            for line in lower_source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        checks["forbidden_imports"] = not any(token.lower() in imports for token in FORBIDDEN_IMPORTS)
        checks["no_report_regeneration_or_execution"] = not any(token.lower() in lower_source for token in FORBIDDEN_SOURCE_TOKENS)
        checks["no_comparison_logic"] = "researchcomparisonanalysis" not in lower_source and "compare_" not in lower_source
        checks["banned_language_scan"] = not any(fragment in lower_source for fragment in BANNED_PROSE_FRAGMENTS)
        checks["research_isolation"] = checks["forbidden_imports"] and checks["no_report_regeneration_or_execution"]
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    return {
        "checks": checks,
        "errors": errors,
        "totals": totals,
        "fingerprint": fingerprint,
        "result": "PASS" if all(checks.values()) and not errors else "FAIL",
    }


def main() -> None:
    report = run()
    if os.environ.get("RESEARCH_ANALYSIS_ENGINE_CHILD") == "1":
        print(report["fingerprint"])
        return
    for name, passed in report["checks"].items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"totals: {report['totals']}")
    print(f"errors: {report['errors']}")
    print(f"fingerprint: {report['fingerprint']}")
    print(f"result: {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)
    print("PHASE2E_RESEARCH_ANALYSIS_ENGINE_STABLE PASS")


if __name__ == "__main__":
    main()

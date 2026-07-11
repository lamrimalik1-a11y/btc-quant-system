"""Validation for pure canonical JSON rendering of ResearchArtifact."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_generation.research_analysis_contracts import (
    ResearchAnalysisMetadata,
    ResearchCampaignAnalysis,
    ResearchCoverageAnalysis,
    ResearchFamilyAnalysis,
    ResearchHypothesisAnalysis,
    ResearchTrajectoryAnalysis,
    ResearchTransitionAnalysis,
    research_analysis_metadata_fingerprint_payload,
    research_campaign_analysis_fingerprint_payload,
    research_coverage_analysis_fingerprint_payload,
    research_family_analysis_fingerprint_payload,
    research_hypothesis_analysis_fingerprint_payload,
    research_trajectory_analysis_fingerprint_payload,
    research_transition_analysis_fingerprint_payload,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_contracts import (
    ResearchArtifact,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_generator import (
    RESEARCH_ARTIFACT_GENERATOR_VERSION,
    build_research_artifact,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_json_renderer import (
    render_research_artifact_json,
    research_artifact_json_render_fingerprint,
)
from experiments.psychological_levels_dynamic.scenario_generation.test_research_artifact_generator import (
    _artifact,
)

MODULE_PATH = Path(__file__).with_name("research_artifact_json_renderer.py")
EXPECTED_RENDER_FINGERPRINT = (
    "sha256:c9ccc23f8294b22a1228af054b38b0a1aa29d0e7862eb6cc54c417d7a7c2d2b5"
)
FORBIDDEN_IMPORTS = (
    "research_artifact_generator",
    "research_analysis_engine",
    "research_report_generator",
    "campaign_designer",
    "campaign_contracts",
    "batch_execution",
    "generator",
    "compiler",
    "assembly",
    "scenario_runner",
    "scenario_catalog.",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "core.",
    "engines.",
    "research.",
    "os",
    "pathlib",
    "tempfile",
    "datetime",
    "time",
    "random",
    "locale",
)
FORBIDDEN_SOURCE_TOKENS = (
    "open(",
    "read_text",
    "write_text",
    "write_bytes",
    "mkdir",
    "tempfile",
    "subprocess",
    "markdown",
    "html",
    "pdf",
    "export",
    "run_campaign",
    "generate_programs",
    "validate_manifest",
    "compile_generation_batch",
    "assemble_batch",
    "execute_batch",
    "build_research_campaign_report",
    "analyze_research_campaign_report",
    "ResearchCampaignReport",
    "CampaignDesignerResult",
    "CampaignResult",
    "ScenarioRunResult",
    "ScenarioExecutionRecord",
    "BatchExecutionResult",
    "PriceObservation",
)
BANNED_WORDS = (
    "buy",
    "sell",
    "trade",
    "prediction",
    "forecast",
    "ranking",
    "optimization",
    "machine learning",
    "learned threshold",
    "better",
    "stronger",
    "weaker",
    "improved",
    "degraded",
    "proven",
    "proves",
    "validated",
    "confirms",
    "suggests",
    "causal",
    "effect",
    "impact",
    "lift",
    "gain",
    "accuracy",
    "performance",
    "falsified",
    "generalize",
    "generalization",
)


def _word_boundary_hit(source: str, phrase: str) -> bool:
    escaped = re.escape(phrase)
    pattern = r"(?<![A-Za-z0-9_])" + escaped + r"(?![A-Za-z0-9_])"
    return re.search(pattern, source, flags=re.IGNORECASE) is not None


def _contains_raw_upstream_object(value: Any) -> bool:
    if type(value).__name__ in {
        "ResearchCampaignReport",
        "CampaignDesignerResult",
        "CampaignResult",
        "ScenarioRunResult",
        "ScenarioExecutionRecord",
        "BatchExecutionResult",
        "PriceObservation",
    }:
        return True
    if isinstance(value, tuple):
        return any(_contains_raw_upstream_object(item) for item in value)
    if is_dataclass(value):
        return any(_contains_raw_upstream_object(getattr(value, field.name)) for field in fields(value))
    return False


def _rejected(factory: Any) -> bool:
    try:
        factory()
    except (TypeError, ValueError):
        return True
    return False


def _cross_process_render() -> str:
    env = dict(os.environ)
    env["RESEARCH_ARTIFACT_JSON_RENDERER_CHILD"] = "1"
    return subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env).strip()


def _zero_denominator_analysis() -> ResearchCampaignAnalysis:
    metadata_fingerprint = research_analysis_metadata_fingerprint_payload(
        analysis_id="ZERO_DENOMINATOR_ANALYSIS",
        analysis_version="1",
        analysis_engine_version="ZERO_DENOMINATOR_TEST",
        source_report_fingerprints=("sha256:" + "1" * 64,),
        source_campaign_result_fingerprint="sha256:" + "2" * 64,
        source_campaign_designer_fingerprint="sha256:" + "3" * 64,
    )
    metadata = ResearchAnalysisMetadata(
        analysis_id="ZERO_DENOMINATOR_ANALYSIS",
        analysis_version="1",
        analysis_engine_version="ZERO_DENOMINATOR_TEST",
        source_report_fingerprints=("sha256:" + "1" * 64,),
        source_campaign_result_fingerprint="sha256:" + "2" * 64,
        source_campaign_designer_fingerprint="sha256:" + "3" * 64,
        metadata_fingerprint=metadata_fingerprint,
    )
    family_fingerprint = research_family_analysis_fingerprint_payload(
        family_name="ZERO_FAMILY",
        coverage_tags=("ZERO_TAG",),
        scenarios_generated=0,
        scenarios_executed=0,
        pass_count=0,
        fail_count=0,
        skipped_count=0,
        completed_visits=0,
        zero_visit_scenarios=0,
        scenarios_with_three_or_more_visits=0,
        transitions=0,
        trajectory_records=0,
        eligible_hypotheses=0,
        confirmed_hypotheses=0,
        pending_hypotheses=0,
        visit_density=None,
        transition_density=None,
        trajectory_density=None,
        eligibility_rate=None,
        confirmation_rate=None,
        pending_rate=None,
        signal_dimension_count=0,
        signal_richness_class="NO_SIGNAL",
        sample_sufficiency_class="NOT_APPLICABLE",
    )
    family = ResearchFamilyAnalysis(
        family_name="ZERO_FAMILY",
        coverage_tags=("ZERO_TAG",),
        scenarios_generated=0,
        scenarios_executed=0,
        pass_count=0,
        fail_count=0,
        skipped_count=0,
        completed_visits=0,
        zero_visit_scenarios=0,
        scenarios_with_three_or_more_visits=0,
        transitions=0,
        trajectory_records=0,
        eligible_hypotheses=0,
        confirmed_hypotheses=0,
        pending_hypotheses=0,
        visit_density=None,
        transition_density=None,
        trajectory_density=None,
        eligibility_rate=None,
        confirmation_rate=None,
        pending_rate=None,
        signal_dimension_count=0,
        signal_richness_class="NO_SIGNAL",
        sample_sufficiency_class="NOT_APPLICABLE",
        family_analysis_fingerprint=family_fingerprint,
    )
    coverage_fingerprint = research_coverage_analysis_fingerprint_payload(
        families_observed=1,
        scenarios_generated=0,
        scenarios_executed=0,
        zero_visit_scenarios=0,
        scenarios_with_three_or_more_visits=0,
        scenarios_with_transitions=0,
        zero_visit_rate=None,
        three_plus_visit_rate=None,
        transition_coverage_rate=None,
        coverage_tag_family_counts=(("ZERO_TAG", 1),),
        unique_coverage_tags=("ZERO_TAG",),
        shared_coverage_tags=(),
    )
    coverage = ResearchCoverageAnalysis(
        families_observed=1,
        scenarios_generated=0,
        scenarios_executed=0,
        zero_visit_scenarios=0,
        scenarios_with_three_or_more_visits=0,
        scenarios_with_transitions=0,
        zero_visit_rate=None,
        three_plus_visit_rate=None,
        transition_coverage_rate=None,
        coverage_tag_family_counts=(("ZERO_TAG", 1),),
        unique_coverage_tags=("ZERO_TAG",),
        shared_coverage_tags=(),
        coverage_analysis_fingerprint=coverage_fingerprint,
    )
    transition_fingerprint = research_transition_analysis_fingerprint_payload(
        total_transitions=0,
        scenarios_with_transitions=0,
        per_family_transition_counts=(("ZERO_FAMILY", 0),),
        transition_density=None,
        top_transition_contributor_family_name="ZERO_FAMILY",
        top_transition_contributor_share=None,
        families_with_zero_transitions=("ZERO_FAMILY",),
    )
    transition = ResearchTransitionAnalysis(
        total_transitions=0,
        scenarios_with_transitions=0,
        per_family_transition_counts=(("ZERO_FAMILY", 0),),
        transition_density=None,
        top_transition_contributor_family_name="ZERO_FAMILY",
        top_transition_contributor_share=None,
        families_with_zero_transitions=("ZERO_FAMILY",),
        transition_analysis_fingerprint=transition_fingerprint,
    )
    trajectory_fingerprint = research_trajectory_analysis_fingerprint_payload(
        total_trajectory_records=0,
        per_family_trajectory_records=(("ZERO_FAMILY", 0),),
        trajectory_density=None,
        top_trajectory_contributor_family_name="ZERO_FAMILY",
        top_trajectory_contributor_share=None,
        families_with_zero_trajectory_records=("ZERO_FAMILY",),
    )
    trajectory = ResearchTrajectoryAnalysis(
        total_trajectory_records=0,
        per_family_trajectory_records=(("ZERO_FAMILY", 0),),
        trajectory_density=None,
        top_trajectory_contributor_family_name="ZERO_FAMILY",
        top_trajectory_contributor_share=None,
        families_with_zero_trajectory_records=("ZERO_FAMILY",),
        trajectory_analysis_fingerprint=trajectory_fingerprint,
    )
    hypothesis_fingerprint = research_hypothesis_analysis_fingerprint_payload(
        eligible_hypotheses=0,
        confirmed_hypotheses=0,
        pending_hypotheses=0,
        per_family_hypothesis_counts=(("ZERO_FAMILY", 0, 0, 0),),
        eligibility_rate=None,
        confirmation_rate=None,
        pending_rate=None,
        top_eligible_hypothesis_family_name="ZERO_FAMILY",
        top_eligible_hypothesis_family_share=None,
        families_with_no_eligible_hypotheses=("ZERO_FAMILY",),
    )
    hypothesis = ResearchHypothesisAnalysis(
        eligible_hypotheses=0,
        confirmed_hypotheses=0,
        pending_hypotheses=0,
        per_family_hypothesis_counts=(("ZERO_FAMILY", 0, 0, 0),),
        eligibility_rate=None,
        confirmation_rate=None,
        pending_rate=None,
        top_eligible_hypothesis_family_name="ZERO_FAMILY",
        top_eligible_hypothesis_family_share=None,
        families_with_no_eligible_hypotheses=("ZERO_FAMILY",),
        hypothesis_analysis_fingerprint=hypothesis_fingerprint,
    )
    campaign_fingerprint = research_campaign_analysis_fingerprint_payload(
        metadata=metadata,
        family_analyses=(family,),
        coverage_analysis=coverage,
        transition_analysis=transition,
        trajectory_analysis=trajectory,
        hypothesis_analysis=hypothesis,
        diagnostics=(),
    )
    return ResearchCampaignAnalysis(
        metadata=metadata,
        family_analyses=(family,),
        coverage_analysis=coverage,
        transition_analysis=transition,
        trajectory_analysis=trajectory,
        hypothesis_analysis=hypothesis,
        diagnostics=(),
        campaign_analysis_fingerprint=campaign_fingerprint,
    )


def _is_sorted_mapping(value: Any) -> bool:
    if isinstance(value, dict):
        keys = list(value)
        return keys == sorted(keys) and all(_is_sorted_mapping(item) for item in value.values())
    if isinstance(value, list):
        return all(_is_sorted_mapping(item) for item in value)
    return True


def run() -> dict[str, Any]:
    checks = {
        "real_artifact_fixture": False,
        "returns_bytes": False,
        "strict_utf8_decode": False,
        "no_utf8_bom": False,
        "no_cr_bytes": False,
        "single_trailing_lf": False,
        "compact_json": False,
        "sorted_keys": False,
        "deterministic_repeated_render": False,
        "cross_process_byte_determinism": False,
        "render_fingerprint": False,
        "pinned_render_fingerprint": False,
        "artifact_fingerprint_in_json": False,
        "renderer_does_not_mutate_artifact": False,
        "decimal_canonical_strings": False,
        "tuple_ordering_preserved": False,
        "none_serializes_to_null": False,
        "semantic_round_trip": False,
        "zero_denominator_none": False,
        "parse_and_rerender_idempotence": False,
        "invalid_input_rejected": False,
        "no_file_io": False,
        "no_exporter_write_function": False,
        "forbidden_imports": False,
        "no_execution_report_or_analysis_regeneration": False,
        "no_raw_upstream_objects": False,
        "banned_language_scan": False,
        "research_isolation": False,
    }
    errors: list[str] = []
    render_fingerprint = ""
    try:
        artifact = _artifact()
        assert isinstance(artifact, ResearchArtifact)
        checks["real_artifact_fixture"] = True
        before = artifact
        rendered = render_research_artifact_json(artifact)
        parsed = json.loads(rendered.decode("utf-8"))
        render_fingerprint = research_artifact_json_render_fingerprint(rendered)

        checks["returns_bytes"] = isinstance(rendered, bytes)
        checks["strict_utf8_decode"] = isinstance(rendered.decode("utf-8", errors="strict"), str)
        checks["no_utf8_bom"] = not rendered.startswith(b"\xef\xbb\xbf")
        checks["no_cr_bytes"] = b"\r" not in rendered
        checks["single_trailing_lf"] = rendered.endswith(b"\n") and not rendered.endswith(b"\n\n")
        canonical_again = json.dumps(
            parsed,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8") + b"\n"
        checks["compact_json"] = b"\n" not in rendered[:-1] and canonical_again == rendered
        checks["sorted_keys"] = _is_sorted_mapping(parsed)
        repeat = render_research_artifact_json(artifact)
        checks["deterministic_repeated_render"] = repeat == rendered
        if os.environ.get("RESEARCH_ARTIFACT_JSON_RENDERER_CHILD") == "1":
            checks["cross_process_byte_determinism"] = True
        else:
            first = _cross_process_render()
            second = _cross_process_render()
            assert first == second == render_fingerprint
            checks["cross_process_byte_determinism"] = True
        expected_fingerprint = "sha256:" + hashlib.sha256(rendered).hexdigest()
        checks["render_fingerprint"] = render_fingerprint == expected_fingerprint
        checks["pinned_render_fingerprint"] = render_fingerprint == EXPECTED_RENDER_FINGERPRINT
        checks["artifact_fingerprint_in_json"] = parsed["artifact_fingerprint"] == artifact.artifact_fingerprint
        checks["renderer_does_not_mutate_artifact"] = artifact == before
        checks["decimal_canonical_strings"] = (
            parsed["analysis"]["family_analyses"][0]["visit_density"]["type"] == "decimal"
            and isinstance(parsed["analysis"]["family_analyses"][0]["visit_density"]["value"], str)
            and not isinstance(parsed["analysis"]["family_analyses"][0]["visit_density"]["value"], float)
        )
        checks["tuple_ordering_preserved"] = [
            item["family_name"] for item in parsed["analysis"]["family_analyses"]
        ] == [family.family_name for family in artifact.analysis.family_analyses]
        checks["none_serializes_to_null"] = parsed["analysis"]["transition_analysis"][
            "families_with_zero_transitions"
        ] == []
        checks["semantic_round_trip"] = (
            parsed["artifact_fingerprint"] == artifact.artifact_fingerprint
            and parsed["metadata"]["metadata_fingerprint"] == artifact.metadata.metadata_fingerprint
            and parsed["analysis"]["coverage_analysis"]["scenarios_generated"] == 100
            and parsed["analysis"]["coverage_analysis"]["scenarios_executed"] == 100
            and [item["family_name"] for item in parsed["analysis"]["family_analyses"]]
            == [family.family_name for family in artifact.analysis.family_analyses]
            and parsed["diagnostics"] == list(artifact.diagnostics)
            and parsed["known_limitations"] == list(artifact.known_limitations)
            and parsed["deferred_research_questions"] == list(artifact.deferred_research_questions)
        )

        zero_artifact = build_research_artifact(
            _zero_denominator_analysis(),
            artifact_id="ZERO_DENOMINATOR_ARTIFACT",
            artifact_version="1",
            artifact_generator_version=RESEARCH_ARTIFACT_GENERATOR_VERSION,
        )
        zero_parsed = json.loads(render_research_artifact_json(zero_artifact).decode("utf-8"))
        checks["zero_denominator_none"] = (
            zero_parsed["analysis"]["family_analyses"][0]["visit_density"] is None
            and zero_parsed["analysis"]["coverage_analysis"]["zero_visit_rate"] is None
            and zero_parsed["analysis"]["trajectory_analysis"]["trajectory_density"] is None
            and zero_parsed["analysis"]["hypothesis_analysis"]["eligibility_rate"] is None
        )
        checks["parse_and_rerender_idempotence"] = canonical_again == rendered
        checks["invalid_input_rejected"] = _rejected(lambda: render_research_artifact_json(object()))
        checks["no_raw_upstream_objects"] = not _contains_raw_upstream_object(artifact)

        source = MODULE_PATH.read_text(encoding="utf-8")
        lower_source = source.lower()
        imports = "\n".join(
            line.strip()
            for line in lower_source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        checks["forbidden_imports"] = not any(token.lower() in imports for token in FORBIDDEN_IMPORTS)
        checks["no_file_io"] = not any(
            token.lower() in lower_source
            for token in (
                "open(",
                "read_text",
                "write_text",
                "write_bytes",
                "pathlib",
                "tempfile",
                "mkdir",
            )
        )
        checks["no_exporter_write_function"] = not any(
            token.lower() in lower_source
            for token in ("export", "write_", "destination", "overwrite", "atomic")
        )
        checks["no_execution_report_or_analysis_regeneration"] = not any(
            token.lower() in lower_source
            for token in (
                "run_campaign",
                "execute_batch",
                "scenario_runner",
                "build_research_campaign_report",
                "analyze_research_campaign_report",
            )
        )
        checks["banned_language_scan"] = not any(
            _word_boundary_hit(source, phrase) for phrase in BANNED_WORDS
        )
        checks["research_isolation"] = (
            checks["forbidden_imports"]
            and checks["no_file_io"]
            and checks["no_exporter_write_function"]
            and checks["no_execution_report_or_analysis_regeneration"]
            and checks["no_raw_upstream_objects"]
        )
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    return {
        "checks": checks,
        "errors": errors,
        "render_fingerprint": render_fingerprint,
        "result": "PASS" if all(checks.values()) and not errors else "FAIL",
    }


def main() -> None:
    report = run()
    if os.environ.get("RESEARCH_ARTIFACT_JSON_RENDERER_CHILD") == "1":
        print(report["render_fingerprint"])
        return
    for name, passed in report["checks"].items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"errors: {report['errors']}")
    print(f"render_fingerprint: {report['render_fingerprint']}")
    print(f"result: {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)
    print("PHASE2F_RESEARCH_ARTIFACT_JSON_RENDERER_STABLE PASS")


if __name__ == "__main__":
    main()

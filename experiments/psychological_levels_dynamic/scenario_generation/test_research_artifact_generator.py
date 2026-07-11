"""Validation for pure Project 2 research artifact generation."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_generation.research_analysis_engine import (
    RESEARCH_ANALYSIS_ENGINE_VERSION,
    analyze_research_campaign_report,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_contracts import (
    ResearchArtifact,
    research_artifact_fingerprint_payload,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_generator import (
    RESEARCH_ARTIFACT_DEFERRED_RESEARCH_QUESTIONS,
    RESEARCH_ARTIFACT_GENERATOR_VERSION,
    RESEARCH_ARTIFACT_KNOWN_LIMITATIONS,
    build_research_artifact,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_report_generator import (
    RESEARCH_REPORT_GENERATOR_VERSION,
    build_research_campaign_report,
)
from experiments.psychological_levels_dynamic.scenario_generation.test_first_research_campaign_100_execution import (
    _execute_campaign,
)

MODULE_PATH = Path(__file__).with_name("research_artifact_generator.py")
FORBIDDEN_IMPORTS = (
    "research_report_contracts",
    "research_report_generator",
    "research_analysis_engine",
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
    "json",
)
FORBIDDEN_SOURCE_TOKENS = (
    "open(",
    "read_text",
    "write_text",
    "json",
    "markdown",
    "render",
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


def _analysis() -> Any:
    report = build_research_campaign_report(
        _execute_campaign(),
        report_id="PHASE2D_FIRST_RESEARCH_CAMPAIGN_100_REPORT",
        report_version="1",
        report_generator_version=RESEARCH_REPORT_GENERATOR_VERSION,
    )
    return analyze_research_campaign_report(
        report,
        analysis_id="PHASE2E_RESEARCH_ANALYSIS_ENGINE",
        analysis_version="1",
        analysis_engine_version=RESEARCH_ANALYSIS_ENGINE_VERSION,
    )


def _artifact() -> ResearchArtifact:
    return build_research_artifact(
        _analysis(),
        artifact_id="PHASE2F_RESEARCH_ARTIFACT",
        artifact_version="1",
        artifact_generator_version=RESEARCH_ARTIFACT_GENERATOR_VERSION,
    )


def _cross_process_artifact_fingerprint() -> str:
    env = dict(os.environ)
    env["RESEARCH_ARTIFACT_GENERATOR_CHILD"] = "1"
    return subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env).strip()


def _contains_raw_upstream_object(value: Any) -> bool:
    type_name = type(value).__name__
    if type_name in {
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


def _word_boundary_hit(source: str, phrase: str) -> bool:
    escaped = re.escape(phrase)
    pattern = r"(?<![A-Za-z0-9_])" + escaped + r"(?![A-Za-z0-9_])"
    return re.search(pattern, source, flags=re.IGNORECASE) is not None


def _rejected(factory: Any) -> bool:
    try:
        factory()
    except (TypeError, ValueError):
        return True
    return False


def run() -> dict[str, Any]:
    checks = {
        "real_end_to_end_construction": False,
        "analysis_identity": False,
        "provenance_copied": False,
        "diagnostics_exact": False,
        "limitations_exact": False,
        "deferred_questions_exact": False,
        "limitation_prefixes": False,
        "deferred_question_prefixes": False,
        "deterministic_repeated_construction": False,
        "cross_process_determinism": False,
        "invalid_input_type_rejected": False,
        "empty_identity_version_rejected": False,
        "artifact_fingerprint_payload": False,
        "no_raw_upstream_objects_embedded": False,
        "no_report_regeneration": False,
        "no_analysis_recomputation": False,
        "no_execution": False,
        "no_exporter_json_markdown_file_io": False,
        "forbidden_imports": False,
        "research_isolation": False,
        "banned_language_scan": False,
    }
    errors: list[str] = []
    fingerprint = ""
    try:
        analysis = _analysis()
        artifact = build_research_artifact(
            analysis,
            artifact_id="PHASE2F_RESEARCH_ARTIFACT",
            artifact_version="1",
            artifact_generator_version=RESEARCH_ARTIFACT_GENERATOR_VERSION,
        )
        assert isinstance(artifact, ResearchArtifact)
        checks["real_end_to_end_construction"] = True
        checks["analysis_identity"] = artifact.analysis is analysis
        checks["provenance_copied"] = (
            artifact.metadata.source_analysis_fingerprint == analysis.campaign_analysis_fingerprint
            and artifact.metadata.source_report_fingerprint == analysis.metadata.source_report_fingerprints[0]
            and artifact.metadata.source_campaign_result_fingerprint
            == analysis.metadata.source_campaign_result_fingerprint
            and artifact.metadata.source_campaign_designer_fingerprint
            == analysis.metadata.source_campaign_designer_fingerprint
        )
        expected_diagnostics = tuple(
            sorted(
                set(
                    analysis.diagnostics
                    + (f"ARTIFACT_GENERATOR_VERSION:{RESEARCH_ARTIFACT_GENERATOR_VERSION}",)
                )
            )
        )
        checks["diagnostics_exact"] = artifact.diagnostics == expected_diagnostics
        checks["limitations_exact"] = artifact.known_limitations == RESEARCH_ARTIFACT_KNOWN_LIMITATIONS
        checks["deferred_questions_exact"] = (
            artifact.deferred_research_questions == RESEARCH_ARTIFACT_DEFERRED_RESEARCH_QUESTIONS
        )
        checks["limitation_prefixes"] = all(
            value.startswith("NOT_TRACKED:") for value in artifact.known_limitations
        )
        checks["deferred_question_prefixes"] = all(
            value.startswith("DEFERRED:") for value in artifact.deferred_research_questions
        )
        repeat = build_research_artifact(
            analysis,
            artifact_id="PHASE2F_RESEARCH_ARTIFACT",
            artifact_version="1",
            artifact_generator_version=RESEARCH_ARTIFACT_GENERATOR_VERSION,
        )
        assert repeat == artifact
        fingerprint = artifact.artifact_fingerprint
        checks["deterministic_repeated_construction"] = repeat.artifact_fingerprint == fingerprint
        if os.environ.get("RESEARCH_ARTIFACT_GENERATOR_CHILD") == "1":
            checks["cross_process_determinism"] = True
        else:
            first = _cross_process_artifact_fingerprint()
            second = _cross_process_artifact_fingerprint()
            assert first == second == fingerprint
            checks["cross_process_determinism"] = True
        checks["invalid_input_type_rejected"] = _rejected(
            lambda: build_research_artifact(
                object(),
                artifact_id="BAD",
                artifact_version="1",
                artifact_generator_version=RESEARCH_ARTIFACT_GENERATOR_VERSION,
            )
        )
        checks["empty_identity_version_rejected"] = all(
            (
                _rejected(
                    lambda: build_research_artifact(
                        analysis,
                        artifact_id="",
                        artifact_version="1",
                        artifact_generator_version=RESEARCH_ARTIFACT_GENERATOR_VERSION,
                    )
                ),
                _rejected(
                    lambda: build_research_artifact(
                        analysis,
                        artifact_id="PHASE2F_RESEARCH_ARTIFACT",
                        artifact_version="",
                        artifact_generator_version=RESEARCH_ARTIFACT_GENERATOR_VERSION,
                    )
                ),
                _rejected(
                    lambda: build_research_artifact(
                        analysis,
                        artifact_id="PHASE2F_RESEARCH_ARTIFACT",
                        artifact_version="1",
                        artifact_generator_version="",
                    )
                ),
            )
        )
        expected_fingerprint = research_artifact_fingerprint_payload(
            artifact_contract_version=artifact.metadata.artifact_contract_version,
            metadata_fingerprint=artifact.metadata.metadata_fingerprint,
            analysis_fingerprint=analysis.campaign_analysis_fingerprint,
            diagnostics=artifact.diagnostics,
            known_limitations=artifact.known_limitations,
            deferred_research_questions=artifact.deferred_research_questions,
        )
        checks["artifact_fingerprint_payload"] = artifact.artifact_fingerprint == expected_fingerprint
        checks["no_raw_upstream_objects_embedded"] = not _contains_raw_upstream_object(artifact)

        source = MODULE_PATH.read_text(encoding="utf-8")
        lower_source = source.lower()
        imports = "\n".join(
            line.strip()
            for line in lower_source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        checks["forbidden_imports"] = not any(token.lower() in imports for token in FORBIDDEN_IMPORTS)
        checks["no_report_regeneration"] = "build_research_campaign_report" not in source
        checks["no_analysis_recomputation"] = "analyze_research_campaign_report" not in source
        checks["no_execution"] = not any(
            token.lower() in lower_source
            for token in (
                "run_campaign",
                "execute_batch",
                "scenario_runner",
                "stage",
            )
        )
        checks["no_exporter_json_markdown_file_io"] = not any(
            token.lower() in lower_source
            for token in (
                "open(",
                "read_text",
                "write_text",
                "json",
                "markdown",
                "render",
                "pathlib",
            )
        )
        checks["research_isolation"] = (
            checks["forbidden_imports"]
            and checks["no_report_regeneration"]
            and checks["no_analysis_recomputation"]
            and checks["no_execution"]
            and checks["no_exporter_json_markdown_file_io"]
        )
        checks["banned_language_scan"] = not any(
            _word_boundary_hit(source, phrase) for phrase in BANNED_WORDS
        )
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    return {
        "checks": checks,
        "errors": errors,
        "artifact_fingerprint": fingerprint,
        "result": "PASS" if all(checks.values()) and not errors else "FAIL",
    }


def main() -> None:
    report = run()
    if os.environ.get("RESEARCH_ARTIFACT_GENERATOR_CHILD") == "1":
        print(report["artifact_fingerprint"])
        return
    for name, passed in report["checks"].items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"errors: {report['errors']}")
    print(f"artifact_fingerprint: {report['artifact_fingerprint']}")
    print(f"result: {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)
    print("PHASE2F_RESEARCH_ARTIFACT_GENERATOR_STABLE PASS")


if __name__ == "__main__":
    main()

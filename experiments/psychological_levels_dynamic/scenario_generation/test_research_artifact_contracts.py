"""Validation for immutable Project 2 research artifact contracts."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import FrozenInstanceError, fields, is_dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_contracts import (
    RESEARCH_ARTIFACT_CONTRACTS_VERSION,
    ResearchArtifact,
    ResearchArtifactMetadata,
    research_artifact_fingerprint_payload,
    research_artifact_metadata_fingerprint_payload,
)
from experiments.psychological_levels_dynamic.scenario_generation.test_research_analysis_contracts import (
    _analysis,
)

MODULE_PATH = Path(__file__).with_name("research_artifact_contracts.py")
FORBIDDEN_IMPORTS = (
    "campaign_designer",
    "campaign_contracts",
    "first_campaign_100_design",
    "generator",
    "manifest_validation",
    "batch_compiler",
    "batch_specification_assembler",
    "batch_execution",
    "research_report_contracts",
    "research_report_generator",
    "research_analysis_engine",
    "scenario_runner",
    "scenario_catalog.",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "core.",
    "engines.",
    "research.",
    "pathlib",
    "os",
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
    "CampaignDesignerResult",
    "CampaignResult",
    "ResearchCampaignReport",
    "ScenarioRunResult",
    "ScenarioExecutionRecord",
    "BatchExecutionResult",
    "PriceObservation",
)
BANNED_PROSE_FRAGMENTS = (
    "buy",
    "sell",
    "entry recommendation",
    "exit recommendation",
    "forecast",
    "strategy ranking",
    "generalize",
    "generalization",
    "proves",
    "confirms",
    "suggests",
    "stronger",
    "weaker",
    "improved",
    "degraded",
    "effect",
    "impact",
    "lift",
    "gain",
    "accuracy",
    "performance",
)


def _metadata() -> ResearchArtifactMetadata:
    analysis = _analysis()
    source_report_fingerprint = analysis.metadata.source_report_fingerprints[0]
    fingerprint = research_artifact_metadata_fingerprint_payload(
        artifact_id="PHASE2F_RESEARCH_ARTIFACT",
        artifact_version="1",
        artifact_generator_version="CONTRACT_ONLY",
        artifact_contract_version=RESEARCH_ARTIFACT_CONTRACTS_VERSION,
        source_analysis_fingerprint=analysis.campaign_analysis_fingerprint,
        source_report_fingerprint=source_report_fingerprint,
        source_campaign_result_fingerprint=analysis.metadata.source_campaign_result_fingerprint,
        source_campaign_designer_fingerprint=analysis.metadata.source_campaign_designer_fingerprint,
    )
    return ResearchArtifactMetadata(
        artifact_id="PHASE2F_RESEARCH_ARTIFACT",
        artifact_version="1",
        artifact_generator_version="CONTRACT_ONLY",
        artifact_contract_version=RESEARCH_ARTIFACT_CONTRACTS_VERSION,
        source_analysis_fingerprint=analysis.campaign_analysis_fingerprint,
        source_report_fingerprint=source_report_fingerprint,
        source_campaign_result_fingerprint=analysis.metadata.source_campaign_result_fingerprint,
        source_campaign_designer_fingerprint=analysis.metadata.source_campaign_designer_fingerprint,
        metadata_fingerprint=fingerprint,
    )


def _artifact(
    *,
    diagnostics: tuple[str, ...] = ("ARTIFACT_CONTRACT_ONLY",),
    known_limitations: tuple[str, ...] = (
        "NOT_TRACKED: raw observations are outside artifact contracts",
        "NOT_TRACKED: rendered files are outside artifact contracts",
    ),
    deferred_research_questions: tuple[str, ...] = (
        "DEFERRED: cross-campaign comparison requires a second campaign",
        "DEFERRED: deterministic exporters are future work",
    ),
    metadata: ResearchArtifactMetadata | None = None,
) -> ResearchArtifact:
    analysis = _analysis()
    actual_metadata = _metadata() if metadata is None else metadata
    fingerprint = research_artifact_fingerprint_payload(
        artifact_contract_version=actual_metadata.artifact_contract_version,
        metadata_fingerprint=actual_metadata.metadata_fingerprint,
        analysis_fingerprint=analysis.campaign_analysis_fingerprint,
        diagnostics=diagnostics,
        known_limitations=known_limitations,
        deferred_research_questions=deferred_research_questions,
    )
    return ResearchArtifact(
        metadata=actual_metadata,
        analysis=analysis,
        diagnostics=diagnostics,
        known_limitations=known_limitations,
        deferred_research_questions=deferred_research_questions,
        artifact_fingerprint=fingerprint,
    )


def _cross_process_artifact_fingerprint() -> str:
    env = dict(os.environ)
    env["RESEARCH_ARTIFACT_CONTRACTS_CHILD"] = "1"
    return subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env).strip()


def _contains_raw_upstream_object(value: Any) -> bool:
    type_name = type(value).__name__
    if type_name in {
        "ResearchCampaignReport",
        "CampaignDesignerResult",
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


def run() -> dict[str, Any]:
    checks = {
        "valid_construction": False,
        "immutability": False,
        "tuple_only_containers": False,
        "deterministic_fingerprints": False,
        "cross_process_determinism": False,
        "canonical_ordering": False,
        "invalid_fingerprint_rejection": False,
        "duplicate_limitation_rejection": False,
        "duplicate_deferred_question_rejection": False,
        "analysis_identity_preservation": False,
        "analysis_fingerprint_consistency": False,
        "no_raw_execution_objects_embedded": False,
        "forbidden_imports": False,
        "banned_language_scan": False,
        "research_isolation": False,
        "no_generator_exporter_rendering_logic": False,
    }
    errors: list[str] = []
    fingerprint = ""
    try:
        artifact = _artifact()
        assert isinstance(artifact.metadata, ResearchArtifactMetadata)
        assert artifact.analysis == _analysis()
        checks["valid_construction"] = True

        try:
            artifact.metadata.artifact_id = "MUTATE"
        except FrozenInstanceError:
            checks["immutability"] = True

        checks["tuple_only_containers"] = (
            isinstance(artifact.diagnostics, tuple)
            and isinstance(artifact.known_limitations, tuple)
            and isinstance(artifact.deferred_research_questions, tuple)
        )

        repeat = _artifact()
        assert repeat == artifact
        assert repeat.artifact_fingerprint == artifact.artifact_fingerprint
        fingerprint = artifact.artifact_fingerprint
        checks["deterministic_fingerprints"] = True

        if os.environ.get("RESEARCH_ARTIFACT_CONTRACTS_CHILD") == "1":
            checks["cross_process_determinism"] = True
        else:
            first = _cross_process_artifact_fingerprint()
            second = _cross_process_artifact_fingerprint()
            assert first == second == artifact.artifact_fingerprint
            checks["cross_process_determinism"] = True

        checks["canonical_ordering"] = _rejected(
            lambda: _artifact(
                diagnostics=("Z_DIAGNOSTIC", "A_DIAGNOSTIC"),
            )
        )
        checks["invalid_fingerprint_rejection"] = _rejected(
            lambda: ResearchArtifactMetadata(
                artifact_id="BAD",
                artifact_version="1",
                artifact_generator_version="CONTRACT_ONLY",
                artifact_contract_version=RESEARCH_ARTIFACT_CONTRACTS_VERSION,
                source_analysis_fingerprint="bad",
                source_report_fingerprint=_metadata().source_report_fingerprint,
                source_campaign_result_fingerprint=_metadata().source_campaign_result_fingerprint,
                source_campaign_designer_fingerprint=_metadata().source_campaign_designer_fingerprint,
                metadata_fingerprint=_metadata().metadata_fingerprint,
            )
        )
        checks["duplicate_limitation_rejection"] = _rejected(
            lambda: _artifact(
                known_limitations=(
                    "NOT_TRACKED: raw observations are outside artifact contracts",
                    "NOT_TRACKED: raw observations are outside artifact contracts",
                )
            )
        )
        checks["duplicate_deferred_question_rejection"] = _rejected(
            lambda: _artifact(
                deferred_research_questions=(
                    "DEFERRED: deterministic exporters are future work",
                    "DEFERRED: deterministic exporters are future work",
                )
            )
        )
        checks["analysis_identity_preservation"] = artifact.analysis == _analysis()
        checks["analysis_fingerprint_consistency"] = (
            artifact.metadata.source_analysis_fingerprint == artifact.analysis.campaign_analysis_fingerprint
            and artifact.metadata.source_report_fingerprint == artifact.analysis.metadata.source_report_fingerprints[0]
            and artifact.metadata.source_campaign_result_fingerprint
            == artifact.analysis.metadata.source_campaign_result_fingerprint
            and artifact.metadata.source_campaign_designer_fingerprint
            == artifact.analysis.metadata.source_campaign_designer_fingerprint
        )
        checks["no_raw_execution_objects_embedded"] = not _contains_raw_upstream_object(artifact)

        source = MODULE_PATH.read_text(encoding="utf-8")
        lower_source = source.lower()
        imports = "\n".join(
            line.strip()
            for line in lower_source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        checks["forbidden_imports"] = not any(token.lower() in imports for token in FORBIDDEN_IMPORTS)
        checks["no_generator_exporter_rendering_logic"] = not any(
            token.lower() in lower_source for token in FORBIDDEN_SOURCE_TOKENS
        )
        checks["banned_language_scan"] = not any(fragment in lower_source for fragment in BANNED_PROSE_FRAGMENTS)
        checks["research_isolation"] = checks["forbidden_imports"] and checks["no_generator_exporter_rendering_logic"]
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
    if os.environ.get("RESEARCH_ARTIFACT_CONTRACTS_CHILD") == "1":
        print(report["artifact_fingerprint"])
        return
    for name, passed in report["checks"].items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"errors: {report['errors']}")
    print(f"artifact_fingerprint: {report['artifact_fingerprint']}")
    print(f"result: {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

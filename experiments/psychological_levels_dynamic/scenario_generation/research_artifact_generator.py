"""Pure ResearchArtifact constructor."""

from __future__ import annotations

from experiments.psychological_levels_dynamic.scenario_generation.research_analysis_contracts import (
    ResearchCampaignAnalysis,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_artifact_contracts import (
    RESEARCH_ARTIFACT_CONTRACTS_VERSION,
    ResearchArtifact,
    ResearchArtifactMetadata,
    research_artifact_fingerprint_payload,
    research_artifact_metadata_fingerprint_payload,
)

RESEARCH_ARTIFACT_GENERATOR_VERSION = "PHASE2F_RESEARCH_ARTIFACT_GENERATOR_V1"

RESEARCH_ARTIFACT_KNOWN_LIMITATIONS = (
    "NOT_TRACKED: FILE_OUTPUTS",
    "NOT_TRACKED: RAW_OBSERVATIONS",
    "NOT_TRACKED: RAW_PAYLOADS",
)

RESEARCH_ARTIFACT_DEFERRED_RESEARCH_QUESTIONS = (
    "DEFERRED: ARTIFACT_EXPORTER",
    "DEFERRED: MULTI_CAMPAIGN_REVIEW",
)


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def build_research_artifact(
    analysis: ResearchCampaignAnalysis,
    artifact_id: str,
    artifact_version: str,
    artifact_generator_version: str,
) -> ResearchArtifact:
    if not isinstance(analysis, ResearchCampaignAnalysis):
        raise TypeError("analysis must be ResearchCampaignAnalysis")
    _require_non_empty("artifact_id", artifact_id)
    _require_non_empty("artifact_version", artifact_version)
    _require_non_empty("artifact_generator_version", artifact_generator_version)

    source_report_fingerprint = analysis.metadata.source_report_fingerprints[0]
    metadata_fingerprint = research_artifact_metadata_fingerprint_payload(
        artifact_id=artifact_id,
        artifact_version=artifact_version,
        artifact_generator_version=artifact_generator_version,
        artifact_contract_version=RESEARCH_ARTIFACT_CONTRACTS_VERSION,
        source_analysis_fingerprint=analysis.campaign_analysis_fingerprint,
        source_report_fingerprint=source_report_fingerprint,
        source_campaign_result_fingerprint=analysis.metadata.source_campaign_result_fingerprint,
        source_campaign_designer_fingerprint=analysis.metadata.source_campaign_designer_fingerprint,
    )
    metadata = ResearchArtifactMetadata(
        artifact_id=artifact_id,
        artifact_version=artifact_version,
        artifact_generator_version=artifact_generator_version,
        artifact_contract_version=RESEARCH_ARTIFACT_CONTRACTS_VERSION,
        source_analysis_fingerprint=analysis.campaign_analysis_fingerprint,
        source_report_fingerprint=source_report_fingerprint,
        source_campaign_result_fingerprint=analysis.metadata.source_campaign_result_fingerprint,
        source_campaign_designer_fingerprint=analysis.metadata.source_campaign_designer_fingerprint,
        metadata_fingerprint=metadata_fingerprint,
    )
    diagnostics = tuple(
        sorted(
            set(
                analysis.diagnostics
                + (f"ARTIFACT_GENERATOR_VERSION:{artifact_generator_version}",)
            )
        )
    )
    artifact_fingerprint = research_artifact_fingerprint_payload(
        artifact_contract_version=metadata.artifact_contract_version,
        metadata_fingerprint=metadata.metadata_fingerprint,
        analysis_fingerprint=analysis.campaign_analysis_fingerprint,
        diagnostics=diagnostics,
        known_limitations=RESEARCH_ARTIFACT_KNOWN_LIMITATIONS,
        deferred_research_questions=RESEARCH_ARTIFACT_DEFERRED_RESEARCH_QUESTIONS,
    )
    return ResearchArtifact(
        metadata=metadata,
        analysis=analysis,
        diagnostics=diagnostics,
        known_limitations=RESEARCH_ARTIFACT_KNOWN_LIMITATIONS,
        deferred_research_questions=RESEARCH_ARTIFACT_DEFERRED_RESEARCH_QUESTIONS,
        artifact_fingerprint=artifact_fingerprint,
    )

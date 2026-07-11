"""Immutable contracts for Project 2 research artifacts.

Contracts only: no artifact generation, export, file I/O, report
regeneration, execution, comparison, or interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass

from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    generation_contract_fingerprint,
)
from experiments.psychological_levels_dynamic.scenario_generation.research_analysis_contracts import (
    ResearchCampaignAnalysis,
)

RESEARCH_ARTIFACT_CONTRACTS_VERSION = "PHASE2F_RESEARCH_ARTIFACT_CONTRACTS_V1"


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_fingerprint(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        raise ValueError(f"{name} must be SHA-256")


def _require_tuple(name: str, value: tuple[object, ...]) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{name} must be tuple")


def _require_sorted_string_tuple(name: str, value: tuple[str, ...]) -> None:
    _require_tuple(name, value)
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{name} must contain non-empty strings")
    if tuple(sorted(value)) != value:
        raise ValueError(f"{name} must be sorted canonically")
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must be unique")


def research_artifact_metadata_fingerprint_payload(
    *,
    artifact_id: str,
    artifact_version: str,
    artifact_generator_version: str,
    artifact_contract_version: str,
    source_analysis_fingerprint: str,
    source_report_fingerprint: str,
    source_campaign_result_fingerprint: str,
    source_campaign_designer_fingerprint: str,
) -> str:
    return generation_contract_fingerprint(
        (
            artifact_id,
            artifact_version,
            artifact_generator_version,
            artifact_contract_version,
            source_analysis_fingerprint,
            source_report_fingerprint,
            source_campaign_result_fingerprint,
            source_campaign_designer_fingerprint,
        )
    )


def research_artifact_fingerprint_payload(
    *,
    artifact_contract_version: str,
    metadata_fingerprint: str,
    analysis_fingerprint: str,
    diagnostics: tuple[str, ...],
    known_limitations: tuple[str, ...],
    deferred_research_questions: tuple[str, ...],
) -> str:
    return generation_contract_fingerprint(
        (
            artifact_contract_version,
            metadata_fingerprint,
            analysis_fingerprint,
            diagnostics,
            known_limitations,
            deferred_research_questions,
        )
    )


@dataclass(frozen=True)
class ResearchArtifactMetadata:
    artifact_id: str
    artifact_version: str
    artifact_generator_version: str
    artifact_contract_version: str
    source_analysis_fingerprint: str
    source_report_fingerprint: str
    source_campaign_result_fingerprint: str
    source_campaign_designer_fingerprint: str
    metadata_fingerprint: str

    def __post_init__(self) -> None:
        for field_name in (
            "artifact_id",
            "artifact_version",
            "artifact_generator_version",
            "artifact_contract_version",
        ):
            _require_non_empty(field_name, getattr(self, field_name))
        for field_name in (
            "source_analysis_fingerprint",
            "source_report_fingerprint",
            "source_campaign_result_fingerprint",
            "source_campaign_designer_fingerprint",
            "metadata_fingerprint",
        ):
            _require_fingerprint(field_name, getattr(self, field_name))
        expected = research_artifact_metadata_fingerprint_payload(
            artifact_id=self.artifact_id,
            artifact_version=self.artifact_version,
            artifact_generator_version=self.artifact_generator_version,
            artifact_contract_version=self.artifact_contract_version,
            source_analysis_fingerprint=self.source_analysis_fingerprint,
            source_report_fingerprint=self.source_report_fingerprint,
            source_campaign_result_fingerprint=self.source_campaign_result_fingerprint,
            source_campaign_designer_fingerprint=self.source_campaign_designer_fingerprint,
        )
        if self.metadata_fingerprint != expected:
            raise ValueError("metadata_fingerprint does not match canonical content")


@dataclass(frozen=True)
class ResearchArtifact:
    metadata: ResearchArtifactMetadata
    analysis: ResearchCampaignAnalysis
    diagnostics: tuple[str, ...]
    known_limitations: tuple[str, ...]
    deferred_research_questions: tuple[str, ...]
    artifact_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.metadata, ResearchArtifactMetadata):
            raise TypeError("metadata must be ResearchArtifactMetadata")
        if not isinstance(self.analysis, ResearchCampaignAnalysis):
            raise TypeError("analysis must be ResearchCampaignAnalysis")
        for field_name in (
            "diagnostics",
            "known_limitations",
            "deferred_research_questions",
        ):
            _require_sorted_string_tuple(field_name, getattr(self, field_name))
        if self.metadata.artifact_contract_version != RESEARCH_ARTIFACT_CONTRACTS_VERSION:
            raise ValueError("artifact_contract_version must match contract version")
        if self.metadata.source_analysis_fingerprint != self.analysis.campaign_analysis_fingerprint:
            raise ValueError("source_analysis_fingerprint must match analysis")
        if self.metadata.source_report_fingerprint != self.analysis.metadata.source_report_fingerprints[0]:
            raise ValueError("source_report_fingerprint must match analysis provenance")
        if (
            self.metadata.source_campaign_result_fingerprint
            != self.analysis.metadata.source_campaign_result_fingerprint
        ):
            raise ValueError("source_campaign_result_fingerprint must match analysis provenance")
        if (
            self.metadata.source_campaign_designer_fingerprint
            != self.analysis.metadata.source_campaign_designer_fingerprint
        ):
            raise ValueError("source_campaign_designer_fingerprint must match analysis provenance")
        _require_fingerprint("artifact_fingerprint", self.artifact_fingerprint)
        expected = research_artifact_fingerprint_payload(
            artifact_contract_version=self.metadata.artifact_contract_version,
            metadata_fingerprint=self.metadata.metadata_fingerprint,
            analysis_fingerprint=self.analysis.campaign_analysis_fingerprint,
            diagnostics=self.diagnostics,
            known_limitations=self.known_limitations,
            deferred_research_questions=self.deferred_research_questions,
        )
        if self.artifact_fingerprint != expected:
            raise ValueError("artifact_fingerprint does not match canonical content")

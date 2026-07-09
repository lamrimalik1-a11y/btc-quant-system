"""Deterministic ScenarioManifest integrity validation.

Validation only: no Grammar semantics, no compiler calls, no runner calls,
and no execution. Every check operates purely on the fields already present
on a ScenarioManifest / ManifestEntry -- nothing here constructs a grammar
program, calls a phrase constructor, or inspects grammar internals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import (
    GenerationSummary,
    ManifestEntry,
    ScenarioManifest,
    generation_contract_fingerprint,
)

VALIDATOR_VERSION = "PHASE2B_MANIFEST_VALIDATION_V1"


def _is_sha256(value: str | None) -> bool:
    return isinstance(value, str) and value.startswith("sha256:")


@dataclass(frozen=True)
class ManifestValidationResult:
    success: bool
    validated_manifest: ScenarioManifest | None
    diagnostics: tuple[str, ...]
    validation_summary: GenerationSummary
    validation_fingerprint: str
    validator_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")
        if self.validated_manifest is not None and not isinstance(
            self.validated_manifest, ScenarioManifest
        ):
            raise TypeError("validated_manifest must be ScenarioManifest or None")
        if not isinstance(self.diagnostics, tuple) or not all(
            isinstance(value, str) for value in self.diagnostics
        ):
            raise TypeError("diagnostics must be tuple[str, ...]")
        if not isinstance(self.validation_summary, GenerationSummary):
            raise TypeError("validation_summary must be GenerationSummary")
        if not _is_sha256(self.validation_fingerprint):
            raise ValueError("validation_fingerprint must be SHA-256")
        if not self.validator_version.strip():
            raise ValueError("validator_version must not be empty")
        if self.success:
            if self.validated_manifest is None:
                raise ValueError("successful validation requires validated_manifest")
        else:
            if self.validated_manifest is not None:
                raise ValueError("failed validation must not carry validated_manifest")
            if not self.diagnostics:
                raise ValueError("failed validation requires diagnostics")


def _check_entry_id_uniqueness(entries: tuple[ManifestEntry, ...]) -> list[str]:
    diagnostics: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        if entry.entry_id in seen:
            diagnostics.append(f"DUPLICATE_ENTRY_ID:{entry.entry_id}")
        seen.add(entry.entry_id)
    return diagnostics


def _check_entry_index_contiguous(entries: tuple[ManifestEntry, ...]) -> list[str]:
    indices = sorted(entry.entry_index for entry in entries)
    if indices != list(range(len(entries))):
        return [f"ENTRY_INDEX_NOT_CONTIGUOUS:{indices}"]
    return []


def _check_entry_ordering(entries: tuple[ManifestEntry, ...]) -> list[str]:
    diagnostics: list[str] = []
    for position, entry in enumerate(entries):
        if entry.entry_index != position:
            diagnostics.append(
                f"ENTRY_ORDER_MISMATCH:position={position}:entry_index={entry.entry_index}"
            )
    return diagnostics


def _check_duplicate_program_fingerprints(entries: tuple[ManifestEntry, ...]) -> list[str]:
    diagnostics: list[str] = []
    generated_fingerprints: dict[str, str] = {}
    for entry in entries:
        if entry.generation_status != "GENERATED":
            continue
        if entry.program_fingerprint in generated_fingerprints:
            diagnostics.append(
                f"DUPLICATE_PROGRAM_FINGERPRINT_AMONG_GENERATED:{entry.program_fingerprint}"
            )
        else:
            generated_fingerprints[entry.program_fingerprint] = entry.entry_id
    for entry in entries:
        if entry.generation_status != "SKIPPED_DUPLICATE":
            continue
        if entry.program_fingerprint is None or entry.program_fingerprint not in generated_fingerprints:
            diagnostics.append(f"ORPHANED_DUPLICATE_ENTRY:{entry.entry_id}")
    return diagnostics


def _check_duplicate_combination_fingerprints(entries: tuple[ManifestEntry, ...]) -> list[str]:
    diagnostics: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        if entry.combination_fingerprint in seen:
            diagnostics.append(
                f"DUPLICATE_COMBINATION_FINGERPRINT:{entry.combination_fingerprint}"
            )
        seen.add(entry.combination_fingerprint)
    return diagnostics


def _check_status_consistency(entries: tuple[ManifestEntry, ...]) -> list[str]:
    diagnostics: list[str] = []
    for entry in entries:
        if entry.generation_status == "GENERATED":
            if entry.program_fingerprint is None:
                diagnostics.append(f"MISSING_PROGRAM_FINGERPRINT_FOR_GENERATED:{entry.entry_id}")
            if entry.rejection_reason is not None:
                diagnostics.append(f"UNEXPECTED_REJECTION_REASON_FOR_GENERATED:{entry.entry_id}")
        elif entry.generation_status == "SKIPPED_DUPLICATE":
            if entry.program_fingerprint is None:
                diagnostics.append(f"MISSING_PROGRAM_FINGERPRINT_FOR_DUPLICATE:{entry.entry_id}")
            if entry.rejection_reason is None:
                diagnostics.append(f"MISSING_REJECTION_REASON_FOR_DUPLICATE:{entry.entry_id}")
        elif entry.generation_status == "REJECTED_BY_RULE":
            if entry.rejection_reason is None:
                diagnostics.append(f"MISSING_REJECTION_REASON_FOR_REJECTED:{entry.entry_id}")

        if entry.compilation_status == "NOT_ATTEMPTED":
            if (
                entry.geometry_fingerprint is not None
                or entry.observation_checksum is not None
                or entry.specification_fingerprint is not None
            ):
                diagnostics.append(
                    f"UNEXPECTED_COMPILATION_FINGERPRINTS_FOR_NOT_ATTEMPTED:{entry.entry_id}"
                )
            if entry.compilation_diagnostics:
                diagnostics.append(
                    f"UNEXPECTED_COMPILATION_DIAGNOSTICS_FOR_NOT_ATTEMPTED:{entry.entry_id}"
                )
        elif entry.compilation_status == "SUCCESS":
            if (
                entry.geometry_fingerprint is None
                or entry.observation_checksum is None
                or entry.specification_fingerprint is None
            ):
                diagnostics.append(
                    f"MISSING_COMPILATION_FINGERPRINTS_FOR_SUCCESS:{entry.entry_id}"
                )
        elif entry.compilation_status == "FAILED":
            if not entry.compilation_diagnostics:
                diagnostics.append(
                    f"MISSING_COMPILATION_DIAGNOSTICS_FOR_FAILED:{entry.entry_id}"
                )
    return diagnostics


def _check_required_fingerprints(manifest: ScenarioManifest) -> list[str]:
    diagnostics: list[str] = []
    if not _is_sha256(manifest.manifest_fingerprint):
        diagnostics.append("MISSING_MANIFEST_FINGERPRINT")
    if not _is_sha256(manifest.generation_spec_fingerprint):
        diagnostics.append("MISSING_GENERATION_SPEC_FINGERPRINT")
    for entry in manifest.entries:
        if not _is_sha256(entry.combination_fingerprint):
            diagnostics.append(f"MISSING_COMBINATION_FINGERPRINT:{entry.entry_id}")
        if entry.program_fingerprint is not None and not _is_sha256(entry.program_fingerprint):
            diagnostics.append(f"MALFORMED_PROGRAM_FINGERPRINT:{entry.entry_id}")
        if entry.geometry_fingerprint is not None and not _is_sha256(entry.geometry_fingerprint):
            diagnostics.append(f"MALFORMED_GEOMETRY_FINGERPRINT:{entry.entry_id}")
        if entry.observation_checksum is not None and not _is_sha256(entry.observation_checksum):
            diagnostics.append(f"MALFORMED_OBSERVATION_CHECKSUM:{entry.entry_id}")
        if entry.specification_fingerprint is not None and not _is_sha256(
            entry.specification_fingerprint
        ):
            diagnostics.append(f"MALFORMED_SPECIFICATION_FINGERPRINT:{entry.entry_id}")
    return diagnostics


def _compute_summary(manifest: ScenarioManifest) -> GenerationSummary:
    entries = manifest.entries
    by_template: dict[str, int] = {}
    by_family: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for entry in entries:
        by_template[entry.template_id] = by_template.get(entry.template_id, 0) + 1
        by_family[entry.family_tag] = by_family.get(entry.family_tag, 0) + 1
        by_status[entry.generation_status] = by_status.get(entry.generation_status, 0) + 1

    coverage_report: tuple[tuple[str, Any], ...] = (
        ("by_template", tuple(sorted(by_template.items()))),
        ("by_family", tuple(sorted(by_family.items()))),
        ("by_status", tuple(sorted(by_status.items()))),
    )
    return GenerationSummary(
        total_combinations_considered=len(entries),
        generated_count=sum(1 for e in entries if e.generation_status == "GENERATED"),
        skipped_duplicate_count=sum(
            1 for e in entries if e.generation_status == "SKIPPED_DUPLICATE"
        ),
        rejected_by_rule_count=sum(
            1 for e in entries if e.generation_status == "REJECTED_BY_RULE"
        ),
        compiled_success_count=sum(1 for e in entries if e.compilation_status == "SUCCESS"),
        compiled_failed_count=sum(1 for e in entries if e.compilation_status == "FAILED"),
        coverage_report=coverage_report,
    )


def _check_summary_counts(manifest: ScenarioManifest, summary: GenerationSummary) -> list[str]:
    diagnostics: list[str] = []
    if summary.total_combinations_considered != len(manifest.entries):
        diagnostics.append("SUMMARY_TOTAL_MISMATCH")
    if (
        summary.generated_count + summary.skipped_duplicate_count + summary.rejected_by_rule_count
        != summary.total_combinations_considered
    ):
        diagnostics.append("SUMMARY_COUNT_MISMATCH")
    declared_templates = set(manifest.template_ids)
    for entry in manifest.entries:
        if entry.template_id not in declared_templates:
            diagnostics.append(f"TEMPLATE_ID_NOT_DECLARED:{entry.entry_id}")
    return diagnostics


def _check_manifest_fingerprint(manifest: ScenarioManifest) -> list[str]:
    recomputed = generation_contract_fingerprint(
        (
            manifest.manifest_id,
            manifest.manifest_version,
            manifest.generation_spec_fingerprint,
            manifest.generator_version,
            manifest.template_ids,
            manifest.entries,
        )
    )
    if recomputed != manifest.manifest_fingerprint:
        return ["MANIFEST_FINGERPRINT_MISMATCH"]
    return []


def validate_manifest(
    manifest: ScenarioManifest,
    validator_version: str = VALIDATOR_VERSION,
) -> ManifestValidationResult:
    """Validate ScenarioManifest integrity only. No Grammar, no compiler, no execution."""

    if not isinstance(manifest, ScenarioManifest):
        raise TypeError("manifest must be ScenarioManifest")
    if not validator_version.strip():
        raise ValueError("validator_version must not be empty")

    entries = manifest.entries
    diagnostics: list[str] = []
    diagnostics += _check_entry_id_uniqueness(entries)
    diagnostics += _check_entry_index_contiguous(entries)
    diagnostics += _check_entry_ordering(entries)
    diagnostics += _check_duplicate_program_fingerprints(entries)
    diagnostics += _check_duplicate_combination_fingerprints(entries)
    diagnostics += _check_status_consistency(entries)
    diagnostics += _check_required_fingerprints(manifest)

    summary = _compute_summary(manifest)
    diagnostics += _check_summary_counts(manifest, summary)
    diagnostics += _check_manifest_fingerprint(manifest)

    diagnostics_tuple = tuple(sorted(diagnostics))
    success = not diagnostics_tuple

    validation_fingerprint = generation_contract_fingerprint(
        (
            manifest.manifest_fingerprint,
            summary,
            diagnostics_tuple,
            validator_version,
        )
    )

    return ManifestValidationResult(
        success=success,
        validated_manifest=manifest if success else None,
        diagnostics=diagnostics_tuple,
        validation_summary=summary,
        validation_fingerprint=validation_fingerprint,
        validator_version=validator_version,
    )

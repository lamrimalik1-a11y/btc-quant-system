"""Validation for deterministic ScenarioManifest integrity checks."""

from __future__ import annotations

import dataclasses
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    RelativePosition,
)
from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    GrammarTemplate,
    ParameterAxis,
    PhraseSlot,
    generation_contract_fingerprint,
)
from experiments.psychological_levels_dynamic.scenario_generation.generator import (
    generate_programs,
)
from experiments.psychological_levels_dynamic.scenario_generation.manifest_validation import (
    ManifestValidationResult,
    validate_manifest,
)

MODULE_PATH = Path(__file__).with_name("manifest_validation.py")
FORBIDDEN_IMPORTS = (
    "compile_program",
    "assemble_specification",
    "scenario_runner",
    "scenario_contract",
    "scenario_registry",
    "scenario_primitives",
    "scenario_catalog.catalog",
    "scenario_catalog.families",
    "scenario_catalog.grammar",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "core.",
    "engines.",
    "research.",
    "random",
)
FORBIDDEN_SOURCE = (
    "run_scenario",
    "compile_program(",
    "scenariospecification",
    "priceobservation",
    "grammarprogram",
    "dynamic_state",
    "research_stable",
    "research_attacker",
)


def _template_single_axis() -> GrammarTemplate:
    return GrammarTemplate(
        template_id="VALIDATION_CENTER_DWELL_TEMPLATE",
        template_version="1",
        family_tag="VALIDATION_CENTER_DWELL",
        description="Generate center holds with variable row budgets.",
        phrase_slots=(
            PhraseSlot(
                constructor_name="hold",
                fixed_params=(("position", RelativePosition.CENTER), ("target_zone", "ZONE_A")),
                axis_bound_params=(("row_budget", "dwell_rows"),),
            ),
        ),
        axes=(ParameterAxis("dwell_rows", (2, 3, 4)),),
        rules=(),
    )


def _template_with_duplicate() -> GrammarTemplate:
    return GrammarTemplate(
        template_id="VALIDATION_DUPLICATE_TEMPLATE",
        template_version="1",
        family_tag="VALIDATION_DUPLICATE",
        description="Two axis values produce identical programs.",
        phrase_slots=(
            PhraseSlot(
                constructor_name="hold",
                fixed_params=(
                    ("row_budget", 2),
                    ("position", RelativePosition.CENTER),
                    ("target_zone", "ZONE_A"),
                ),
                axis_bound_params=(),
            ),
        ),
        axes=(ParameterAxis("unused_axis", (1, 2)),),
        rules=(),
    )


def _recompute_manifest_fingerprint(manifest) -> str:
    return generation_contract_fingerprint(
        (
            manifest.manifest_id,
            manifest.manifest_version,
            manifest.generation_spec_fingerprint,
            manifest.generator_version,
            manifest.template_ids,
            manifest.entries,
        )
    )


def _rebuild_with_entries(manifest, entries: tuple[Any, ...]):
    rebuilt = dataclasses.replace(manifest, entries=entries)
    return dataclasses.replace(
        rebuilt, manifest_fingerprint=_recompute_manifest_fingerprint(rebuilt)
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "valid_manifest": False,
        "duplicate_entry_ids": False,
        "duplicate_program_fingerprints": False,
        "duplicate_combination_fingerprints": False,
        "summary_validation": False,
        "fingerprint_determinism": False,
        "cross_process_determinism": False,
        "research_isolation": False,
    }
    try:
        base_result = generate_programs(_template_single_axis(), "VALIDATION_TEST_GEN_V1")
        assert base_result.success is True
        manifest = base_result.manifest

        valid = validate_manifest(manifest, "VALIDATION_TEST_V1")
        assert isinstance(valid, ManifestValidationResult)
        assert valid.success is True
        assert valid.diagnostics == ()
        assert valid.validated_manifest == manifest
        assert valid.validation_summary.generated_count == 3
        assert valid.validation_summary.total_combinations_considered == 3
        checks["valid_manifest"] = True

        duplicate_id_entries = manifest.entries[:1] + (
            dataclasses.replace(manifest.entries[1], entry_id=manifest.entries[0].entry_id),
        ) + manifest.entries[2:]
        duplicate_id_manifest = _rebuild_with_entries(manifest, duplicate_id_entries)
        duplicate_id_result = validate_manifest(duplicate_id_manifest, "VALIDATION_TEST_V1")
        assert duplicate_id_result.success is False
        assert duplicate_id_result.validated_manifest is None
        assert any(d.startswith("DUPLICATE_ENTRY_ID:") for d in duplicate_id_result.diagnostics)
        checks["duplicate_entry_ids"] = True

        duplicate_program_entries = manifest.entries[:1] + (
            dataclasses.replace(
                manifest.entries[1],
                program_fingerprint=manifest.entries[0].program_fingerprint,
            ),
        ) + manifest.entries[2:]
        duplicate_program_manifest = _rebuild_with_entries(manifest, duplicate_program_entries)
        duplicate_program_result = validate_manifest(duplicate_program_manifest, "VALIDATION_TEST_V1")
        assert duplicate_program_result.success is False
        assert any(
            d.startswith("DUPLICATE_PROGRAM_FINGERPRINT_AMONG_GENERATED:")
            for d in duplicate_program_result.diagnostics
        )
        checks["duplicate_program_fingerprints"] = True

        duplicate_combination_entries = manifest.entries[:1] + (
            dataclasses.replace(
                manifest.entries[1],
                combination_fingerprint=manifest.entries[0].combination_fingerprint,
            ),
        ) + manifest.entries[2:]
        duplicate_combination_manifest = _rebuild_with_entries(
            manifest, duplicate_combination_entries
        )
        duplicate_combination_result = validate_manifest(
            duplicate_combination_manifest, "VALIDATION_TEST_V1"
        )
        assert duplicate_combination_result.success is False
        assert any(
            d.startswith("DUPLICATE_COMBINATION_FINGERPRINT:")
            for d in duplicate_combination_result.diagnostics
        )
        checks["duplicate_combination_fingerprints"] = True

        dup_result = generate_programs(_template_with_duplicate(), "VALIDATION_TEST_GEN_V1")
        assert dup_result.success is True
        dup_manifest = dup_result.manifest
        dup_validation = validate_manifest(dup_manifest, "VALIDATION_TEST_V1")
        assert dup_validation.success is True
        assert dup_validation.validation_summary.generated_count == 1
        assert dup_validation.validation_summary.skipped_duplicate_count == 1
        assert dup_validation.validation_summary.total_combinations_considered == 2
        by_status = dict(
            next(v for k, v in dup_validation.validation_summary.coverage_report if k == "by_status")
        )
        assert by_status.get("GENERATED") == 1
        assert by_status.get("SKIPPED_DUPLICATE") == 1
        by_template = dict(
            next(
                v for k, v in dup_validation.validation_summary.coverage_report if k == "by_template"
            )
        )
        assert by_template.get("VALIDATION_DUPLICATE_TEMPLATE") == 2
        checks["summary_validation"] = True

        repeat_valid = validate_manifest(manifest, "VALIDATION_TEST_V1")
        assert repeat_valid == valid
        assert repeat_valid.validation_fingerprint == valid.validation_fingerprint
        assert dup_validation.validation_fingerprint != valid.validation_fingerprint

        tampered_manifest = dataclasses.replace(
            manifest, manifest_fingerprint="sha256:" + "0" * 64
        )
        tampered_result = validate_manifest(tampered_manifest, "VALIDATION_TEST_V1")
        assert tampered_result.success is False
        assert "MANIFEST_FINGERPRINT_MISMATCH" in tampered_result.diagnostics
        checks["fingerprint_determinism"] = True

        if os.environ.get("MANIFEST_VALIDATION_CHILD") == "1":
            checks["cross_process_determinism"] = True
        else:
            env = dict(os.environ)
            env["MANIFEST_VALIDATION_CHILD"] = "1"
            first = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
            second = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
            assert first == second
            checks["cross_process_determinism"] = True

        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        assert not any(token in imports for token in FORBIDDEN_IMPORTS)
        assert not any(token in source for token in FORBIDDEN_SOURCE)
        assert "def validate_manifest" in source
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    for field in (
        "valid_manifest",
        "duplicate_entry_ids",
        "duplicate_program_fingerprints",
        "duplicate_combination_fingerprints",
        "summary_validation",
        "fingerprint_determinism",
        "cross_process_determinism",
        "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

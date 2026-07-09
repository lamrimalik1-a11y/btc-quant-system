"""Validation for the first 100-scenario Project 2 campaign design."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_catalog.grammar.ast import PhraseType
from experiments.psychological_levels_dynamic.scenario_generation.first_campaign_100_design import (
    FIRST_CAMPAIGN_TARGET_COUNT,
    build_campaign_specification,
    design_first_campaign_100,
)
from experiments.psychological_levels_dynamic.scenario_generation.generator import (
    MAX_GENERATED_PROGRAMS,
)

MODULE_PATH = Path(__file__).with_name("first_campaign_100_design.py")
TEST_PATH = Path(__file__)
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
FORBIDDEN_IMPORTS = (
    "batch_execution",
    "batch_compiler",
    "batch_specification_assembler",
    "scenario_runner",
    "scenario_catalog.catalog",
    "scenario_catalog.families",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "core.",
    "engines.",
    "research.",
)


def _all_phrase_types(result: Any) -> tuple[PhraseType, ...]:
    phrase_types: list[PhraseType] = []
    for family in result.family_results:
        for program in family.generation_result.generated_programs:
            phrase_types.extend(phrase.phrase_type for phrase in program.phrases)
    return tuple(phrase_types)


def _summary(result: Any) -> tuple[Any, ...]:
    return (
        result.success,
        result.campaign_specification,
        tuple(
            (
                family.family_name,
                family.coverage_tags,
                family.generated_count,
                family.manifest_validated,
                family.generation_result.generation_fingerprint,
                family.manifest_validation_result.validation_fingerprint,
                family.family_design_fingerprint,
            )
            for family in result.family_results
        ),
        result.total_generated,
        result.campaign_design_fingerprint,
        result.diagnostics,
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "campaign_specification_valid": False,
        "exactly_100_generated": False,
        "family_cap_respected": False,
        "deterministic_ordering": False,
        "family_coverage_preserved": False,
        "campaign_fingerprints_deterministic": False,
        "manifest_validation_pass": False,
        "no_retest_boundary_usage": False,
        "generation_only_boundary": False,
        "cross_process_determinism": False,
    }
    fingerprints: dict[str, Any] = {}
    family_counts: dict[str, int] = {}
    try:
        campaign = build_campaign_specification()
        result = design_first_campaign_100()
        assert campaign == result.campaign_specification
        assert campaign.target_scenario_count == FIRST_CAMPAIGN_TARGET_COUNT
        assert tuple(family.family_name for family in campaign.families) == EXPECTED_FAMILIES
        assert tuple(family.target_count for family in campaign.families) == (10,) * 10
        checks["campaign_specification_valid"] = True

        assert result.success is True
        assert result.total_generated == 100
        assert len(result.family_results) == 10
        assert sum(family.generated_count for family in result.family_results) == 100
        checks["exactly_100_generated"] = True

        assert all(family.generated_count <= MAX_GENERATED_PROGRAMS for family in result.family_results)
        assert all(family.generated_count == family.target_count == 10 for family in result.family_results)
        family_counts = {family.family_name: family.generated_count for family in result.family_results}
        checks["family_cap_respected"] = True

        assert tuple(family.family_name for family in result.family_results) == EXPECTED_FAMILIES
        for family in result.family_results:
            assert tuple(entry.entry_index for entry in family.generation_result.manifest.entries) == tuple(range(10))
            assert tuple(entry.generation_status for entry in family.generation_result.manifest.entries) == ("GENERATED",) * 10
        checks["deterministic_ordering"] = True

        coverage = tuple(
            (family.family_name, family.coverage_tags)
            for family in result.campaign_specification.families
        )
        assert len(coverage) == 10
        assert all(tags for _, tags in coverage)
        assert ("RAMP_TO_ENTRY", ("ramp_connector", "entry_after_connector")) in coverage
        checks["family_coverage_preserved"] = True

        repeated = design_first_campaign_100()
        assert _summary(repeated) == _summary(result)
        fingerprints = {
            "campaign_specification": result.campaign_specification.campaign_specification_fingerprint,
            "campaign_design": result.campaign_design_fingerprint,
            "families": tuple(
                (family.family_name, family.family_design_fingerprint)
                for family in result.family_results
            ),
        }
        checks["campaign_fingerprints_deterministic"] = True

        assert all(family.manifest_validated for family in result.family_results)
        assert all(family.manifest_validation_result.success for family in result.family_results)
        checks["manifest_validation_pass"] = True

        phrase_types = _all_phrase_types(result)
        assert PhraseType.RETEST_BOUNDARY not in phrase_types
        assert PhraseType.RAMP in phrase_types
        assert PhraseType.ENTER_ZONE in phrase_types
        assert PhraseType.PENETRATE in phrase_types
        assert PhraseType.ACCEPTED_BREAK in phrase_types
        assert PhraseType.RECLAIM in phrase_types
        checks["no_retest_boundary_usage"] = True

        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        assert not any(token in imports for token in FORBIDDEN_IMPORTS)
        assert "execute_batch(" not in source
        assert "compile_generation_batch(" not in source
        assert "assemble_batch(" not in source
        assert "run_campaign(" not in source
        checks["generation_only_boundary"] = True

        if os.environ.get("FIRST_CAMPAIGN_100_DESIGN_CHILD") == "1":
            checks["cross_process_determinism"] = True
        else:
            env = dict(os.environ)
            env["FIRST_CAMPAIGN_100_DESIGN_CHILD"] = "1"
            first = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
            second = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
            assert first == second
            checks["cross_process_determinism"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {
        **checks,
        "family_counts": family_counts,
        "fingerprints": fingerprints,
        "errors": errors,
        "result": result_status,
    }


def main() -> None:
    report = run()
    for field in (
        "campaign_specification_valid",
        "exactly_100_generated",
        "family_cap_respected",
        "deterministic_ordering",
        "family_coverage_preserved",
        "campaign_fingerprints_deterministic",
        "manifest_validation_pass",
        "no_retest_boundary_usage",
        "generation_only_boundary",
        "cross_process_determinism",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"family_counts = {report['family_counts']}")
    print(f"fingerprints = {report['fingerprints']}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)
    print("PHASE2D_FIRST_CAMPAIGN_100_DESIGN PASS")


if __name__ == "__main__":
    main()


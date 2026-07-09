"""Validation for Project 2 campaign designer contracts only."""

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

from experiments.psychological_levels_dynamic.scenario_generation.campaign_contracts import (
    CAMPAIGN_CONTRACTS_VERSION,
    CampaignFamilyResult,
    CampaignFamilySpec,
    CampaignResult,
    CampaignSpecification,
    campaign_result_fingerprint_payload,
    campaign_specification_fingerprint_payload,
)
from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    GrammarTemplate,
    ParameterAxis,
    PhraseSlot,
    generation_contract_fingerprint,
)

MODULE_PATH = Path(__file__).with_name("campaign_contracts.py")
FORBIDDEN_IMPORTS = (
    "batch_execution",
    "compile_generation_batch",
    "compile_program",
    "manifest_validation",
    "assemble_batch",
    "scenario_runner",
    "scenario_contract",
    "scenario_registry",
    "scenario_catalog.catalog",
    "scenario_catalog.families",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "core.",
    "engines.",
    "research.",
    "random",
    "time",
    "datetime",
)
SHA_1 = "sha256:" + "1" * 64
SHA_2 = "sha256:" + "2" * 64


def _expect_raises(exception: type[BaseException], callable_: Any) -> None:
    try:
        callable_()
    except exception:
        return
    raise AssertionError(f"expected {exception.__name__}")


def _template(template_id: str = "CAMPAIGN_ENTER_TEMPLATE") -> GrammarTemplate:
    return GrammarTemplate(
        template_id=template_id,
        template_version="1",
        family_tag="CAMPAIGN_CONTRACT_FAMILY",
        description="Campaign contract template, not executed.",
        phrase_slots=(
            PhraseSlot(
                constructor_name="enter_zone",
                fixed_params=(("target_zone", "ZONE_A"), ("side", "LOWER"), ("depth", "0.40")),
                axis_bound_params=(("row_budget", "rows"),),
            ),
        ),
        axes=(ParameterAxis("rows", (4, 6)),),
        rules=(),
    )


def _family(name: str = "ENTER_ZONE_FAMILY", count: int = 10) -> CampaignFamilySpec:
    return CampaignFamilySpec(
        family_name=name,
        template=_template(f"{name}_TEMPLATE"),
        coverage_tags=("repeated_visits", "zone_interaction"),
        target_count=count,
        notes="Authoring coverage metadata only.",
    )


def _spec(*families: CampaignFamilySpec) -> CampaignSpecification:
    if not families:
        families = (_family(),)
    total = sum(family.target_count for family in families)
    fingerprint = campaign_specification_fingerprint_payload(
        campaign_id="PHASE2D_CAMPAIGN_CONTRACT_TEST",
        campaign_version="1",
        campaign_goal="Validate campaign designer contracts only.",
        families=families,
        target_scenario_count=total,
    )
    return CampaignSpecification(
        campaign_id="PHASE2D_CAMPAIGN_CONTRACT_TEST",
        campaign_version="1",
        campaign_goal="Validate campaign designer contracts only.",
        families=families,
        target_scenario_count=total,
        campaign_specification_fingerprint=fingerprint,
    )


def _family_result(
    name: str = "ENTER_ZONE_FAMILY",
    *,
    generated: int = 10,
    executed: int = 10,
    passed: int = 10,
    failed: int = 0,
    skipped: int = 0,
) -> CampaignFamilyResult:
    return CampaignFamilyResult(
        family_name=name,
        coverage_tags=("repeated_visits", "zone_interaction"),
        batch_execution_fingerprint=SHA_1,
        generated_count=generated,
        executed_count=executed,
        passed_count=passed,
        failed_count=failed,
        skipped_count=skipped,
    )


def _campaign_result(
    family_results: tuple[CampaignFamilyResult, ...],
    *,
    success: bool = True,
    diagnostics: tuple[str, ...] = (),
) -> CampaignResult:
    total_generated = sum(item.generated_count for item in family_results)
    total_executed = sum(item.executed_count for item in family_results)
    total_passed = sum(item.passed_count for item in family_results)
    total_failed = sum(item.failed_count for item in family_results)
    total_skipped = sum(item.skipped_count for item in family_results)
    fingerprint = campaign_result_fingerprint_payload(
        success=success,
        campaign_id="PHASE2D_CAMPAIGN_CONTRACT_TEST",
        total_generated=total_generated,
        total_executed=total_executed,
        total_passed=total_passed,
        total_failed=total_failed,
        total_skipped=total_skipped,
        family_results=family_results,
        campaign_designer_version=CAMPAIGN_CONTRACTS_VERSION,
        diagnostics=diagnostics,
    )
    return CampaignResult(
        success=success,
        campaign_id="PHASE2D_CAMPAIGN_CONTRACT_TEST",
        total_generated=total_generated,
        total_executed=total_executed,
        total_passed=total_passed,
        total_failed=total_failed,
        total_skipped=total_skipped,
        family_results=family_results,
        campaign_fingerprint=fingerprint,
        campaign_designer_version=CAMPAIGN_CONTRACTS_VERSION,
        diagnostics=diagnostics,
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "valid_campaign_specification": False,
        "invalid_empty_campaign": False,
        "count_reconciliation": False,
        "coverage_tags_metadata_only": False,
        "deterministic_fingerprints": False,
        "immutability": False,
        "cross_process_determinism": False,
        "research_isolation": False,
    }
    fingerprints: dict[str, str] = {}
    try:
        family_a = _family("ENTER_ZONE_FAMILY", 10)
        family_b = _family("RECLAIM_FAMILY", 10)
        spec = _spec(family_a, family_b)
        assert spec.target_scenario_count == 20
        assert spec.families == (family_a, family_b)
        assert spec.campaign_specification_fingerprint == campaign_specification_fingerprint_payload(
            campaign_id=spec.campaign_id,
            campaign_version=spec.campaign_version,
            campaign_goal=spec.campaign_goal,
            families=spec.families,
            target_scenario_count=spec.target_scenario_count,
        )
        checks["valid_campaign_specification"] = True

        _expect_raises(
            ValueError,
            lambda: CampaignSpecification("C", "1", "goal", (), 0, SHA_2),
        )
        checks["invalid_empty_campaign"] = True

        _expect_raises(
            ValueError,
            lambda: CampaignFamilyResult("F", ("tag",), SHA_1, 4, 5, 5, 0, 0),
        )
        _expect_raises(
            ValueError,
            lambda: CampaignFamilyResult("F", ("tag",), SHA_1, 4, 4, 3, 0, 0),
        )
        _expect_raises(
            ValueError,
            lambda: CampaignSpecification("C", "1", "goal", (family_a,), 11, SHA_2),
        )
        failed_family = _family_result("FAILED_FAMILY", generated=10, executed=10, passed=8, failed=2)
        failed_result = _campaign_result((failed_family,), success=False, diagnostics=("FAMILY_FAILED",))
        assert failed_result.total_failed == 2
        _expect_raises(
            ValueError,
            lambda: _campaign_result((failed_family,), success=True),
        )
        checks["count_reconciliation"] = True

        assert family_a.coverage_tags == ("repeated_visits", "zone_interaction")
        assert "coverage_tags" not in generation_contract_fingerprint(family_a.template)
        _expect_raises(
            ValueError,
            lambda: CampaignFamilySpec("BAD", _template("BAD_TEMPLATE"), ("RESEARCH_ATTACKER_PRESSURE",), 1, "bad"),
        )
        _expect_raises(
            ValueError,
            lambda: CampaignFamilySpec("BAD", _template("BAD_TEMPLATE"), ("tag", "tag"), 1, "bad"),
        )
        checks["coverage_tags_metadata_only"] = True

        spec_repeat = _spec(family_a, family_b)
        result = _campaign_result((_family_result("ENTER_ZONE_FAMILY"), _family_result("RECLAIM_FAMILY")))
        result_repeat = _campaign_result((_family_result("ENTER_ZONE_FAMILY"), _family_result("RECLAIM_FAMILY")))
        changed_spec = _spec(_family("ENTER_ZONE_FAMILY", 9), family_b)
        assert spec_repeat == spec
        assert spec_repeat.campaign_specification_fingerprint == spec.campaign_specification_fingerprint
        assert changed_spec.campaign_specification_fingerprint != spec.campaign_specification_fingerprint
        assert result_repeat == result
        assert result_repeat.campaign_fingerprint == result.campaign_fingerprint
        fingerprints = {
            "campaign_specification": spec.campaign_specification_fingerprint,
            "campaign_result": result.campaign_fingerprint,
        }
        checks["deterministic_fingerprints"] = True

        for value, attribute, replacement in (
            (family_a, "family_name", "X"),
            (spec, "campaign_id", "X"),
            (_family_result(), "generated_count", 99),
            (result, "total_generated", 99),
        ):
            _expect_raises(
                FrozenInstanceError,
                lambda value=value, attribute=attribute, replacement=replacement: setattr(value, attribute, replacement),
            )
        checks["immutability"] = True

        if os.environ.get("CAMPAIGN_CONTRACTS_CHILD") == "1":
            checks["cross_process_determinism"] = True
        else:
            env = dict(os.environ)
            env["CAMPAIGN_CONTRACTS_CHILD"] = "1"
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
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "fingerprints": fingerprints, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    for field in (
        "valid_campaign_specification",
        "invalid_empty_campaign",
        "count_reconciliation",
        "coverage_tags_metadata_only",
        "deterministic_fingerprints",
        "immutability",
        "cross_process_determinism",
        "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"fingerprints = {report['fingerprints']}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
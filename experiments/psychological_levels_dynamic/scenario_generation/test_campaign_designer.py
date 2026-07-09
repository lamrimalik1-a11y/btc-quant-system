"""Validation for Project 2 campaign designer orchestration."""

from __future__ import annotations

import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_catalog.compiler.geometry import (
    GeometryContext,
    GeometryReference,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    Direction,
    PathSmoothness,
    ZoneSide,
)
from experiments.psychological_levels_dynamic.scenario_generation.campaign_contracts import (
    CampaignFamilySpec,
    CampaignSpecification,
    campaign_specification_fingerprint_payload,
)
from experiments.psychological_levels_dynamic.scenario_generation.campaign_designer import (
    CAMPAIGN_DESIGNER_VERSION,
    CampaignDesignerResult,
    run_campaign,
)
from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    GrammarTemplate,
    ParameterAxis,
    PhraseSlot,
)
from experiments.psychological_levels_dynamic.scenario_generation.runner_execution_context import (
    RunnerExecutionContext,
)

MODULE_PATH = Path(__file__).with_name("campaign_designer.py")
FORBIDDEN_DIRECT_IMPORTS = (
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
)


def _geometry_context() -> GeometryContext:
    center = Decimal("60400")
    half_width = Decimal("25")
    return GeometryContext(
        symbol="BTCUSDT",
        geometry_version="PHASE2D_CAMPAIGN_DESIGNER_GEOMETRY_V1",
        references=(
            GeometryReference(
                zone_id="ZONE_A",
                center_price=center,
                lower_price=center - half_width,
                upper_price=center + half_width,
                half_width=half_width,
            ),
        ),
    )


def _execution_context() -> RunnerExecutionContext:
    return RunnerExecutionContext(
        symbol="BTCUSDT",
        geometry_context=_geometry_context(),
        active_window=0,
        spacing=Decimal("200"),
        zone_half_width=Decimal("25"),
        market_timestamp=1_700_000_000_000,
        session_id="PHASE2D_CAMPAIGN_DESIGNER_SESSION",
        runner_version="PHASE2D_CAMPAIGN_DESIGNER_RUNNER_V1",
    )


def _slot(constructor_name: str, **params: Any) -> PhraseSlot:
    return PhraseSlot(
        constructor_name=constructor_name,
        fixed_params=tuple(sorted(params.items())),
        axis_bound_params=(),
    )


def _axis_slot(constructor_name: str, axis_name: str, **params: Any) -> PhraseSlot:
    return PhraseSlot(
        constructor_name=constructor_name,
        fixed_params=tuple(sorted(params.items())),
        axis_bound_params=(("depth", axis_name),),
    )


def _outside(rows: int = 4, clearance: str = "0.50") -> PhraseSlot:
    return _slot(
        "hold_outside",
        row_budget=rows,
        target_zone="ZONE_A",
        side=ZoneSide.UPPER,
        clearance=Decimal(clearance),
    )


def _cycles(pattern: tuple[PhraseSlot, ...], count: int = 6) -> tuple[PhraseSlot, ...]:
    return tuple(slot for _ in range(count) for slot in pattern + (_outside(),))


def _enter_template(template_id: str = "CAMPAIGN_ENTER_TEMPLATE") -> GrammarTemplate:
    return GrammarTemplate(
        template_id=template_id,
        template_version="1",
        family_tag="CAMPAIGN_ENTER",
        description="Two generated enter-zone campaign proofs.",
        phrase_slots=_cycles((
            _axis_slot("enter_zone", "depth", row_budget=4, target_zone="ZONE_A", side=ZoneSide.LOWER),
        )),
        axes=(ParameterAxis("depth", (Decimal("0.30"), Decimal("0.40"))),),
        rules=(),
    )


def _penetrate_template(template_id: str = "CAMPAIGN_PENETRATE_TEMPLATE") -> GrammarTemplate:
    return GrammarTemplate(
        template_id=template_id,
        template_version="1",
        family_tag="CAMPAIGN_PENETRATE",
        description="Two generated side-authored penetrate campaign proofs.",
        phrase_slots=_cycles((
            _slot("enter_zone", row_budget=4, target_zone="ZONE_A", side=ZoneSide.LOWER, depth=Decimal("0.30")),
            _axis_slot("penetrate", "depth", row_budget=4, target_zone="ZONE_A", side=ZoneSide.LOWER),
        )),
        axes=(ParameterAxis("depth", (Decimal("0.30"), Decimal("0.40"))),),
        rules=(),
    )


def _legacy_ramp_failure_template() -> GrammarTemplate:
    return GrammarTemplate(
        template_id="CAMPAIGN_LEGACY_RAMP_FAILURE_TEMPLATE",
        template_version="1",
        family_tag="CAMPAIGN_LEGACY_RAMP_FAILURE",
        description="One generated but unassembled legacy ramp without target_zone.",
        phrase_slots=(
            _slot("ramp", row_budget=4, distance=Decimal("0.40"), direction=Direction.UP, smoothness=PathSmoothness.LINEAR),
        ),
        axes=(),
        rules=(),
    )


def _family(name: str, template: GrammarTemplate, target_count: int, tags: tuple[str, ...]) -> CampaignFamilySpec:
    return CampaignFamilySpec(
        family_name=name,
        template=template,
        coverage_tags=tags,
        target_count=target_count,
        notes="Campaign designer test metadata only.",
    )


def _campaign(*families: CampaignFamilySpec, campaign_id: str = "PHASE2D_CAMPAIGN_DESIGNER_TEST") -> CampaignSpecification:
    target = sum(family.target_count for family in families)
    fingerprint = campaign_specification_fingerprint_payload(
        campaign_id=campaign_id,
        campaign_version="1",
        campaign_goal="Validate thin per-family Project 2 campaign orchestration.",
        families=families,
        target_scenario_count=target,
    )
    return CampaignSpecification(
        campaign_id=campaign_id,
        campaign_version="1",
        campaign_goal="Validate thin per-family Project 2 campaign orchestration.",
        families=families,
        target_scenario_count=target,
        campaign_specification_fingerprint=fingerprint,
    )


def _successful_campaign() -> CampaignSpecification:
    return _campaign(
        _family("ENTER_FAMILY", _enter_template(), 2, ("repeated_visits", "enter_zone")),
        _family("PENETRATE_FAMILY", _penetrate_template(), 2, ("repeated_visits", "penetration")),
    )


def _failure_campaign() -> CampaignSpecification:
    return _campaign(
        _family("ENTER_FAMILY", _enter_template("CAMPAIGN_ENTER_TEMPLATE_FAILURE_PROOF"), 2, ("repeated_visits", "enter_zone")),
        _family("LEGACY_RAMP_FAILURE", _legacy_ramp_failure_template(), 1, ("connector_path", "legacy_ramp")),
        campaign_id="PHASE2D_CAMPAIGN_DESIGNER_FAILURE_TEST",
    )


def _summary_tuple(result: CampaignDesignerResult) -> tuple[Any, ...]:
    return (
        result.success,
        result.campaign_result,
        tuple(payload.family_pipeline_fingerprint for payload in result.family_execution_payloads),
        tuple(
            None if payload.batch_execution_result is None else payload.batch_execution_result.batch_execution_fingerprint
            for payload in result.family_execution_payloads
        ),
        result.campaign_designer_fingerprint,
        result.diagnostics,
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "multi_family_success_proof": False,
        "companion_payload_preserved": False,
        "family_ordering_preserved": False,
        "campaign_result_counts_reconcile": False,
        "critical_count_mapping": False,
        "whole_family_failure_isolated": False,
        "determinism": False,
        "cross_process_determinism": False,
        "coverage_tags_do_not_leak": False,
        "research_isolation": False,
    }
    fingerprints: dict[str, str] = {}
    try:
        execution_context = _execution_context()
        campaign = _successful_campaign()
        result = run_campaign(campaign, execution_context)
        assert result.success is True
        assert result.campaign_result.success is True
        assert result.campaign_result.total_generated == 4
        assert result.campaign_result.total_passed == 4
        assert result.campaign_result.total_failed == 0
        assert result.campaign_result.total_skipped == 0
        assert len(result.family_execution_payloads) == 2
        assert isinstance(result, CampaignDesignerResult)
        checks["multi_family_success_proof"] = True

        for payload in result.family_execution_payloads:
            assert payload.generation_result is not None
            assert payload.manifest_validation_result is not None
            assert payload.batch_compilation_result is not None
            assert payload.batch_assembly_result is not None
            assert payload.batch_execution_result is not None
            assert payload.batch_execution_result.batch_execution_fingerprint == payload.family_pipeline_fingerprint or payload.family_pipeline_fingerprint.startswith("sha256:")
            assert payload.batch_execution_result.source_manifest_fingerprint == payload.generation_result.manifest.manifest_fingerprint
        checks["companion_payload_preserved"] = True

        assert tuple(payload.family_name for payload in result.family_execution_payloads) == ("ENTER_FAMILY", "PENETRATE_FAMILY")
        assert tuple(item.family_name for item in result.campaign_result.family_results) == ("ENTER_FAMILY", "PENETRATE_FAMILY")
        checks["family_ordering_preserved"] = True

        compact = result.campaign_result
        assert compact.total_generated == sum(item.generated_count for item in compact.family_results)
        assert compact.total_executed == sum(item.executed_count for item in compact.family_results)
        assert compact.total_passed == sum(item.passed_count for item in compact.family_results)
        assert compact.total_failed == sum(item.failed_count for item in compact.family_results)
        assert compact.total_skipped == sum(item.skipped_count for item in compact.family_results)
        checks["campaign_result_counts_reconcile"] = True

        failure_result = run_campaign(_failure_campaign(), execution_context)
        failed_family = failure_result.campaign_result.family_results[1]
        failed_payload = failure_result.family_execution_payloads[1]
        assert failure_result.success is False
        assert failed_family.generated_count == 1
        assert failed_payload.batch_execution_result is not None
        assert failed_payload.batch_execution_result.executed_scenarios == 0
        assert failed_family.passed_count == 0
        assert failed_family.failed_count == 0
        assert failed_family.skipped_count == 1
        assert failed_family.executed_count == 1
        checks["critical_count_mapping"] = True

        good_family = failure_result.campaign_result.family_results[0]
        good_payload = failure_result.family_execution_payloads[0]
        assert good_family.passed_count == 2
        assert good_payload.batch_execution_result is not None
        assert good_payload.batch_execution_result.total_scenarios == 2
        assert failure_result.campaign_result.total_generated == 3
        assert failure_result.campaign_result.total_skipped == 1
        assert failure_result.family_execution_payloads[1].generation_result is not failure_result.family_execution_payloads[0].generation_result
        checks["whole_family_failure_isolated"] = True

        repeat = run_campaign(_successful_campaign(), _execution_context())
        assert _summary_tuple(repeat) == _summary_tuple(result)
        fingerprints = {
            "campaign_result": result.campaign_result.campaign_fingerprint,
            "campaign_designer": result.campaign_designer_fingerprint,
            "enter_family": result.family_execution_payloads[0].family_pipeline_fingerprint,
            "penetrate_family": result.family_execution_payloads[1].family_pipeline_fingerprint,
        }
        checks["determinism"] = True

        if os.environ.get("CAMPAIGN_DESIGNER_CHILD") == "1":
            checks["cross_process_determinism"] = True
        else:
            env = dict(os.environ)
            env["CAMPAIGN_DESIGNER_CHILD"] = "1"
            first = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
            second = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
            assert first == second
            checks["cross_process_determinism"] = True

        forbidden_values = set()
        for payload in result.family_execution_payloads:
            forbidden_values.update(payload.coverage_tags)
            for assembled in payload.batch_assembly_result.assembled_specifications:
                spec = assembled.specification
                assert not any(tag in spec.geometry_parameters for tag in payload.coverage_tags)
                assert not any(tag in spec.scenario_id for tag in payload.coverage_tags)
            for record in payload.batch_execution_result.scenario_results:
                summary_text = repr(record.summary)
                assert not any(tag in summary_text for tag in payload.coverage_tags)
        assert forbidden_values == {"repeated_visits", "enter_zone", "penetration"}
        checks["coverage_tags_do_not_leak"] = True

        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        assert not any(token in imports for token in FORBIDDEN_DIRECT_IMPORTS)
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "fingerprints": fingerprints, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    for field in (
        "multi_family_success_proof",
        "companion_payload_preserved",
        "family_ordering_preserved",
        "campaign_result_counts_reconcile",
        "critical_count_mapping",
        "whole_family_failure_isolated",
        "determinism",
        "cross_process_determinism",
        "coverage_tags_do_not_leak",
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
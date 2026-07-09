"""Validation for scenario generation contracts only."""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    GenerationCampaign,
    GenerationRule,
    GenerationSummary,
    GrammarTemplate,
    ManifestEntry,
    ParameterAxis,
    PhraseSlot,
    ScenarioManifest,
    generation_contract_fingerprint,
)

MODULE_PATH = Path(__file__).with_name("contracts.py")
FORBIDDEN_IMPORTS = (
    "compiler",
    "compile_program",
    "assemble_specification",
    "scenario_runner",
    "scenario_contract",
    "scenario_registry",
    "scenario_primitives",
    "scenario_catalog.catalog",
    "scenario_catalog.families",
    "stage",
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
FORBIDDEN_SOURCE = (
    "dynamic_state",
    "research_stable",
    "research_attacker",
    "run_scenario",
    "priceobservation",
    "scenariospecification",
    "grammarprogram",
)
SHA_1 = "sha256:" + "1" * 64
SHA_2 = "sha256:" + "2" * 64
SHA_3 = "sha256:" + "3" * 64
SHA_4 = "sha256:" + "4" * 64
SHA_5 = "sha256:" + "5" * 64


def _expect_raises(exception: type[BaseException], callable_: Any) -> None:
    try:
        callable_()
    except exception:
        return
    raise AssertionError(f"expected {exception.__name__}")


def _axis() -> ParameterAxis:
    return ParameterAxis("dwell_rows", (2, 4, 6))


def _slot() -> PhraseSlot:
    return PhraseSlot(
        constructor_name="hold",
        fixed_params=(("position", "CENTER"),),
        axis_bound_params=(("row_budget", "dwell_rows"),),
    )


def _rule() -> GenerationRule:
    return GenerationRule(
        rule_id="MIN_ROWS",
        description="Rows must satisfy the declared minimum.",
        severity="REJECT",
    )


def _template() -> GrammarTemplate:
    return GrammarTemplate(
        template_id="CENTER_DWELL_EXIT_TEMPLATE",
        template_version="1",
        family_tag="CENTER_DWELL_EXIT",
        description="Fixed center dwell template contract.",
        phrase_slots=(_slot(),),
        axes=(_axis(),),
        rules=(_rule(),),
    )


def _entry() -> ManifestEntry:
    return ManifestEntry(
        entry_index=0,
        entry_id="ENTRY_000001",
        template_id="CENTER_DWELL_EXIT_TEMPLATE",
        family_tag="CENTER_DWELL_EXIT",
        resolved_parameters=(("dwell_rows", 4),),
        combination_fingerprint=SHA_1,
        program_fingerprint=SHA_2,
        generation_status="GENERATED",
        rejection_reason=None,
        compilation_status="NOT_ATTEMPTED",
        compilation_diagnostics=(),
        geometry_fingerprint=None,
        observation_checksum=None,
        specification_fingerprint=None,
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "generation_campaign": False,
        "parameter_axis": False,
        "phrase_slot": False,
        "generation_rule": False,
        "grammar_template": False,
        "manifest_entry": False,
        "scenario_manifest": False,
        "generation_summary": False,
        "fingerprint_determinism": False,
        "immutability": False,
        "research_isolation": False,
    }
    try:
        campaign = GenerationCampaign(
            campaign_id="CENTER_DWELL_EXIT_CAMPAIGN",
            campaign_version="1",
            description="Campaign contract.",
            research_goal="Validate generation contract grouping.",
            manifest_ids=("MANIFEST_1",),
        )
        assert campaign.manifest_ids == ("MANIFEST_1",)
        _expect_raises(ValueError, lambda: GenerationCampaign("", "1", "d", "g", ()))
        checks["generation_campaign"] = True

        axis = _axis()
        assert axis.values == (2, 4, 6)
        _expect_raises(ValueError, lambda: ParameterAxis("", (1,)))
        _expect_raises(ValueError, lambda: ParameterAxis("x", ()))
        _expect_raises(TypeError, lambda: ParameterAxis("x", [1, 2]))
        _expect_raises(TypeError, lambda: ParameterAxis("x", ([1],)))
        checks["parameter_axis"] = True

        slot = _slot()
        assert slot.constructor_name == "hold"
        _expect_raises(ValueError, lambda: PhraseSlot("", (), ()))
        _expect_raises(TypeError, lambda: PhraseSlot("hold", [("x", 1)], ()))
        _expect_raises(TypeError, lambda: PhraseSlot("hold", (), (("x",),)))
        _expect_raises(
            ValueError,
            lambda: PhraseSlot("hold", (("row_budget", 2),), (("row_budget", "dwell_rows"),)),
        )
        checks["phrase_slot"] = True

        rule = _rule()
        assert rule.severity == "REJECT"
        _expect_raises(ValueError, lambda: GenerationRule("", "desc", "INFO"))
        _expect_raises(ValueError, lambda: GenerationRule("R", "", "INFO"))
        _expect_raises(ValueError, lambda: GenerationRule("R", "desc", "FATAL"))
        checks["generation_rule"] = True

        template = _template()
        assert template.phrase_slots == (slot,)
        _expect_raises(ValueError, lambda: GrammarTemplate("", "1", "F", "d", (slot,), (), ()))
        _expect_raises(ValueError, lambda: GrammarTemplate("T", "1", "F", "d", (), (), ()))
        _expect_raises(TypeError, lambda: GrammarTemplate("T", "1", "F", "d", ("slot",), (), ()))
        _expect_raises(
            ValueError,
            lambda: GrammarTemplate(
                "T",
                "1",
                "F",
                "d",
                (PhraseSlot("hold", (), (("row_budget", "missing_axis"),)),),
                (_axis(),),
                (),
            ),
        )
        checks["grammar_template"] = True

        entry = _entry()
        assert entry.generation_status == "GENERATED"
        _expect_raises(ValueError, lambda: ManifestEntry(-1, "E", "T", "F", (), SHA_1, None, "GENERATED", None, "NOT_ATTEMPTED", (), None, None, None))
        _expect_raises(ValueError, lambda: ManifestEntry(0, "", "T", "F", (), SHA_1, None, "GENERATED", None, "NOT_ATTEMPTED", (), None, None, None))
        _expect_raises(ValueError, lambda: ManifestEntry(0, "E", "T", "F", (), None, None, "GENERATED", None, "NOT_ATTEMPTED", (), None, None, None))
        _expect_raises(ValueError, lambda: ManifestEntry(0, "E", "T", "F", (), "bad", None, "GENERATED", None, "NOT_ATTEMPTED", (), None, None, None))
        _expect_raises(ValueError, lambda: ManifestEntry(0, "E", "T", "F", (), SHA_1, None, "BAD", None, "NOT_ATTEMPTED", (), None, None, None))
        _expect_raises(ValueError, lambda: ManifestEntry(0, "E", "T", "F", (), SHA_1, None, "GENERATED", None, "BAD", (), None, None, None))
        checks["manifest_entry"] = True

        manifest = ScenarioManifest(
            manifest_id="MANIFEST_1",
            manifest_version="1",
            campaign_id=campaign.campaign_id,
            generation_spec_fingerprint=SHA_3,
            generator_version="GENERATOR_CONTRACTS_ONLY_V1",
            template_ids=(template.template_id,),
            entries=(entry,),
            manifest_fingerprint=SHA_4,
        )
        assert manifest.entries == (entry,)
        _expect_raises(ValueError, lambda: ScenarioManifest("", "1", None, SHA_3, "G", (), (), SHA_4))
        _expect_raises(ValueError, lambda: ScenarioManifest("M", "1", None, None, "G", (), (), SHA_4))
        _expect_raises(ValueError, lambda: ScenarioManifest("M", "1", None, "bad", "G", (), (), SHA_4))
        _expect_raises(ValueError, lambda: ScenarioManifest("M", "1", None, SHA_3, "G", (), (), None))
        _expect_raises(TypeError, lambda: ScenarioManifest("M", "1", None, SHA_3, "G", (), ("entry",), SHA_4))
        checks["scenario_manifest"] = True

        summary = GenerationSummary(
            total_combinations_considered=3,
            generated_count=1,
            skipped_duplicate_count=1,
            rejected_by_rule_count=1,
            compiled_success_count=0,
            compiled_failed_count=0,
            coverage_report=(("family", "CENTER_DWELL_EXIT"),),
        )
        assert summary.generated_count == 1
        _expect_raises(ValueError, lambda: GenerationSummary(-1, 0, 0, 0, 0, 0, ()))
        _expect_raises(TypeError, lambda: GenerationSummary(0, 0, 0, 0, 0, 0, [("x", 1)]))
        checks["generation_summary"] = True

        fp1 = generation_contract_fingerprint(manifest)
        fp2 = generation_contract_fingerprint(manifest)
        changed = ScenarioManifest(
            manifest_id="MANIFEST_2",
            manifest_version="1",
            campaign_id=campaign.campaign_id,
            generation_spec_fingerprint=SHA_3,
            generator_version="GENERATOR_CONTRACTS_ONLY_V1",
            template_ids=(template.template_id,),
            entries=(entry,),
            manifest_fingerprint=SHA_5,
        )
        assert fp1 == fp2
        assert fp1 != generation_contract_fingerprint(changed)
        assert generation_contract_fingerprint(Decimal("1.0")) == generation_contract_fingerprint(Decimal("1.00"))
        _expect_raises(TypeError, lambda: generation_contract_fingerprint({"not": "canonical"}))
        checks["fingerprint_determinism"] = True

        for value, attribute, replacement in (
            (campaign, "campaign_id", "X"),
            (axis, "values", (1,)),
            (slot, "constructor_name", "x"),
            (rule, "severity", "INFO"),
            (template, "template_id", "X"),
            (entry, "entry_id", "X"),
            (manifest, "manifest_id", "X"),
            (summary, "generated_count", 99),
        ):
            _expect_raises(
                FrozenInstanceError,
                lambda value=value, attribute=attribute, replacement=replacement: setattr(value, attribute, replacement),
            )
        checks["immutability"] = True

        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        assert not any(token in imports for token in FORBIDDEN_IMPORTS)
        assert not any(token in source for token in FORBIDDEN_SOURCE)
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    for field in (
        "generation_campaign",
        "parameter_axis",
        "phrase_slot",
        "generation_rule",
        "grammar_template",
        "manifest_entry",
        "scenario_manifest",
        "generation_summary",
        "fingerprint_determinism",
        "immutability",
        "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
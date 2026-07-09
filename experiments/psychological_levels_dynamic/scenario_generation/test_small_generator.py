"""Validation for the small deterministic GrammarProgram generator."""

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

from experiments.psychological_levels_dynamic.scenario_catalog.grammar.ast import GrammarProgram
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    RelativePosition,
    ZoneSide,
)
from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    GenerationRule,
    GrammarTemplate,
    ParameterAxis,
    PhraseSlot,
)
from experiments.psychological_levels_dynamic.scenario_generation.generator import (
    MAX_GENERATED_PROGRAMS,
    GenerationResult,
    generate_programs,
)

MODULE_PATH = Path(__file__).with_name("generator.py")
FORBIDDEN_IMPORTS = (
    "compile_program",
    "assemble_specification",
    "scenario_runner",
    "scenario_contract",
    "scenario_registry",
    "scenario_primitives",
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
)
FORBIDDEN_SOURCE = (
    "run_scenario",
    "scenariospecification",
    "priceobservation",
    "dynamic_state",
    "research_stable",
    "research_attacker",
)


def _template_single_axis() -> GrammarTemplate:
    return GrammarTemplate(
        template_id="CENTER_DWELL_TEMPLATE",
        template_version="1",
        family_tag="CENTER_DWELL",
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


def _template_multi_axis() -> GrammarTemplate:
    return GrammarTemplate(
        template_id="CENTER_EXIT_TEMPLATE",
        template_version="1",
        family_tag="CENTER_EXIT",
        description="Generate center then outside holds.",
        phrase_slots=(
            PhraseSlot(
                constructor_name="hold",
                fixed_params=(("position", RelativePosition.CENTER), ("target_zone", "ZONE_A")),
                axis_bound_params=(("row_budget", "inside_rows"),),
            ),
            PhraseSlot(
                constructor_name="hold_outside",
                fixed_params=(("target_zone", "ZONE_A"), ("side", ZoneSide.UPPER)),
                axis_bound_params=(
                    ("row_budget", "outside_rows"),
                    ("clearance", "clearance"),
                ),
            ),
        ),
        axes=(
            ParameterAxis("inside_rows", (2, 3)),
            ParameterAxis("outside_rows", (4,)),
            ParameterAxis("clearance", (Decimal("0.4"), Decimal("0.8"))),
        ),
        rules=(GenerationRule("NO_RULE_LOGIC", "Declarative only.", "INFO"),),
    )


def _template_duplicate() -> GrammarTemplate:
    return GrammarTemplate(
        template_id="DUPLICATE_TEMPLATE",
        template_version="1",
        family_tag="DUPLICATE_CHECK",
        description="Two axis values produce identical programs.",
        phrase_slots=(
            PhraseSlot(
                constructor_name="hold",
                fixed_params=(("row_budget", 2), ("position", RelativePosition.CENTER), ("target_zone", "ZONE_A")),
                axis_bound_params=(),
            ),
        ),
        axes=(ParameterAxis("unused_axis", (1, 2)),),
        rules=(),
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "single_axis_generation": False,
        "multi_axis_generation": False,
        "deterministic_order": False,
        "duplicate_detection": False,
        "manifest_generation": False,
        "grammar_program_validity": False,
        "fingerprint_determinism": False,
        "cross_process_determinism": False,
        "research_isolation": False,
    }
    try:
        single = generate_programs(_template_single_axis(), "GEN_TEST_V1")
        assert isinstance(single, GenerationResult)
        assert single.success is True
        assert len(single.generated_programs) == 3
        assert tuple(program.phrases[0].row_budget for program in single.generated_programs) == (2, 3, 4)
        checks["single_axis_generation"] = True

        multi = generate_programs(_template_multi_axis(), "GEN_TEST_V1")
        assert multi.success is True
        assert len(multi.generated_programs) == 4
        assert len(multi.manifest.entries) == 4
        checks["multi_axis_generation"] = True

        first_params = tuple(entry.resolved_parameters for entry in multi.manifest.entries)
        assert first_params == (
            (("inside_rows", 2), ("outside_rows", 4), ("clearance", Decimal("0.4"))),
            (("inside_rows", 2), ("outside_rows", 4), ("clearance", Decimal("0.8"))),
            (("inside_rows", 3), ("outside_rows", 4), ("clearance", Decimal("0.4"))),
            (("inside_rows", 3), ("outside_rows", 4), ("clearance", Decimal("0.8"))),
        )
        checks["deterministic_order"] = True

        duplicate = generate_programs(_template_duplicate(), "GEN_TEST_V1")
        assert duplicate.success is True
        assert len(duplicate.generated_programs) == 1
        statuses = tuple(entry.generation_status for entry in duplicate.manifest.entries)
        assert statuses == ("GENERATED", "SKIPPED_DUPLICATE")
        checks["duplicate_detection"] = True

        assert multi.manifest.manifest_fingerprint.startswith("sha256:")
        assert multi.manifest.generation_spec_fingerprint.startswith("sha256:")
        assert tuple(entry.compilation_status for entry in multi.manifest.entries) == ("NOT_ATTEMPTED",) * 4
        assert tuple(entry.generation_status for entry in multi.manifest.entries) == ("GENERATED",) * 4
        checks["manifest_generation"] = True

        assert all(isinstance(program, GrammarProgram) for program in multi.generated_programs)
        assert all(program.program_fingerprint.startswith("sha256:") for program in multi.generated_programs)
        too_many = GrammarTemplate(
            template_id="TOO_MANY_TEMPLATE",
            template_version="1",
            family_tag="LIMIT_CHECK",
            description="Reject more than ten combinations.",
            phrase_slots=_template_single_axis().phrase_slots,
            axes=(ParameterAxis("dwell_rows", tuple(range(MAX_GENERATED_PROGRAMS + 1))),),
            rules=(),
        )
        rejected = generate_programs(too_many, "GEN_TEST_V1")
        assert rejected.success is False
        assert rejected.generated_programs == ()
        assert rejected.manifest is None
        assert rejected.diagnostics
        checks["grammar_program_validity"] = True

        repeat = generate_programs(_template_multi_axis(), "GEN_TEST_V1")
        assert repeat == multi
        assert repeat.generation_fingerprint == multi.generation_fingerprint
        changed = generate_programs(_template_single_axis(), "GEN_TEST_V1")
        assert changed.generation_fingerprint != multi.generation_fingerprint
        checks["fingerprint_determinism"] = True

        if os.environ.get("SMALL_GENERATOR_CHILD") == "1":
            checks["cross_process_determinism"] = True
        else:
            env = dict(os.environ)
            env["SMALL_GENERATOR_CHILD"] = "1"
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
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    for field in (
        "single_axis_generation",
        "multi_axis_generation",
        "deterministic_order",
        "duplicate_detection",
        "manifest_generation",
        "grammar_program_validity",
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
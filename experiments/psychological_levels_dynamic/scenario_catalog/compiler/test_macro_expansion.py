"""Validation for the deterministic macro expansion engine only."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_catalog.compiler.diagnostics import (
    DiagnosticSeverity,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.macro_expansion import (
    expand_program,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.primitives import (
    PrimitiveType,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.ast import (
    GRAMMAR_SCHEMA_VERSION,
    GrammarParameter,
    GrammarPhrase,
    GrammarProgram,
    PhraseType,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    Direction,
    RelativePosition,
    ZoneSide,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.phrases import (
    accepted_break,
    approach_zone,
    break_candidate,
    compress,
    enter_zone,
    expand,
    hold,
    hold_outside,
    oscillate,
    penetrate,
    ramp,
    reclaim,
    recovery_gap,
    transfer_to_zone,
    withdraw,
)

MODULE_PATH = Path(__file__).with_name("macro_expansion.py")
FORBIDDEN_IMPORTS = (
    "scenario_runner", "scenario_contract", "scenario_registry",
    "scenario_primitives", "test_dynamic_state_transitions",
    "test_transition_graph", "test_trajectory_evolution",
    "test_prediction_evolution", "core.", "engines.", "research.", "random",
)
FORBIDDEN_CONTRACTS = (
    "priceobservation", "scenariospecification", "mechanicaltimeline(",
    "geometrycontext(", "timelinesegment(", "dynamic_state", "research_",
)


def _program(*phrases: Any, program_id: str = "MACRO_TEST") -> GrammarProgram:
    return GrammarProgram(program_id, GRAMMAR_SCHEMA_VERSION, phrases, (), (), ())


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "atomic_passthrough": False,
        "macro_expansion": False,
        "budget_conservation": False,
        "instruction_ordering": False,
        "diagnostics_ordering": False,
        "fingerprint_determinism": False,
        "fatal_diagnostics": False,
        "research_isolation": False,
    }

    try:
        # --- atomic passthrough (all 9 mappings) ---
        atomic_cases = (
            (hold(5, RelativePosition.CENTER), PrimitiveType.HOLD),
            (ramp(5, Decimal("10"), Direction.UP), PrimitiveType.RAMP),
            (oscillate(5, Decimal("3"), 4), PrimitiveType.OSCILLATE),
            (
                approach_zone(5, "ZONE_A", ZoneSide.UPPER, Decimal("20")),
                PrimitiveType.APPROACH,
            ),
            (
                enter_zone(5, "ZONE_A", ZoneSide.UPPER, Decimal("2")),
                PrimitiveType.ENTER,
            ),
            (penetrate(5, "ZONE_A", Decimal("1")), PrimitiveType.PENETRATE),
            (
                withdraw(5, "ZONE_A", ZoneSide.UPPER, Decimal("3")),
                PrimitiveType.WITHDRAW,
            ),
            (
                hold_outside(5, "ZONE_A", ZoneSide.UPPER, Decimal("2")),
                PrimitiveType.HOLD_OUTSIDE,
            ),
            (
                recovery_gap(5, "ZONE_A", Decimal("3")),
                PrimitiveType.RECOVERY_GAP,
            ),
        )
        for phrase, expected_primitive in atomic_cases:
            result = expand_program(_program(phrase), "MACRO_V1")
            assert result.success is True
            assert len(result.expanded_instructions) == 1
            item = result.expanded_instructions[0]
            assert item.instruction.primitive_type == expected_primitive
            assert item.row_budget == 5
            assert item.instruction.parameters == phrase.params
        checks["atomic_passthrough"] = True

        # --- combined macro-expansion program (hand-verified allocations) ---
        phrase_0 = hold(10, RelativePosition.CENTER)
        phrase_1 = recovery_gap(4, "ZONE_A", Decimal("3"))
        phrase_2 = accepted_break(15, "ZONE_A", ZoneSide.UPPER, Decimal("5"), 3)
        phrase_3 = reclaim(9, "ZONE_A", ZoneSide.UPPER, Decimal("2"), 4)
        phrase_4 = transfer_to_zone(6, "ZONE_A", "ZONE_B", Decimal("100"))
        phrase_5 = compress(
            7, "ZONE_B", (Decimal("10"), Decimal("5"), Decimal("2"))
        )
        phrase_6 = expand(5, "ZONE_B", (Decimal("1"), Decimal("2")))
        program = _program(
            phrase_0, phrase_1, phrase_2, phrase_3, phrase_4, phrase_5, phrase_6
        )
        result = expand_program(program, "MACRO_V1")
        assert result.success is True, result.diagnostics
        assert len(result.expanded_instructions) == 19

        expected_primitive_types = (
            PrimitiveType.HOLD,
            PrimitiveType.RECOVERY_GAP,
            PrimitiveType.APPROACH, PrimitiveType.ENTER, PrimitiveType.PENETRATE,
            PrimitiveType.WITHDRAW, PrimitiveType.HOLD_OUTSIDE,
            PrimitiveType.APPROACH, PrimitiveType.ENTER, PrimitiveType.PENETRATE,
            PrimitiveType.HOLD,
            PrimitiveType.WITHDRAW, PrimitiveType.RAMP, PrimitiveType.APPROACH,
            PrimitiveType.OSCILLATE, PrimitiveType.OSCILLATE, PrimitiveType.OSCILLATE,
            PrimitiveType.OSCILLATE, PrimitiveType.OSCILLATE,
        )
        actual_primitive_types = tuple(
            item.instruction.primitive_type for item in result.expanded_instructions
        )
        assert actual_primitive_types == expected_primitive_types

        expected_row_budgets = (
            10, 4,
            3, 3, 3, 3, 3,
            2, 2, 1, 4,
            2, 2, 2,
            3, 2, 2,
            3, 2,
        )
        actual_row_budgets = tuple(
            item.row_budget for item in result.expanded_instructions
        )
        assert actual_row_budgets == expected_row_budgets
        accepted_items = result.expanded_instructions[2:7]
        reclaim_items = result.expanded_instructions[7:11]
        accepted_penetrate_params = dict((p.name, p.value) for p in accepted_items[2].instruction.parameters)
        reclaim_penetrate_params = dict((p.name, p.value) for p in reclaim_items[2].instruction.parameters)
        assert accepted_penetrate_params["side"] == ZoneSide.UPPER
        assert reclaim_penetrate_params["side"] == ZoneSide.UPPER
        assert accepted_items[-1].row_budget == 3
        assert reclaim_items[-1].row_budget == 4
        assert dict((p.name, p.value) for p in accepted_items[-1].instruction.parameters)["acceptance_rows"] == 3
        assert dict((p.name, p.value) for p in reclaim_items[-1].instruction.parameters)["residence_rows"] == 4

        transfer_items = result.expanded_instructions[11:14]
        assert transfer_items[0].instruction.target_zone == "ZONE_A"
        assert dict((p.name, p.value) for p in transfer_items[0].instruction.parameters)["source_zone"] == "ZONE_A"

        compress_amplitudes = tuple(
            dict((p.name, p.value) for p in item.instruction.parameters)["amplitude"]
            for item in result.expanded_instructions[14:17]
        )
        expand_amplitudes = tuple(
            dict((p.name, p.value) for p in item.instruction.parameters)["amplitude"]
            for item in result.expanded_instructions[17:19]
        )
        assert compress_amplitudes == (Decimal("10"), Decimal("5"), Decimal("2"))
        assert expand_amplitudes == (Decimal("1"), Decimal("2"))

        # reserved-row allocation distinguished from naive equal division:
        # naive divmod(20, 5) would give (4,4,4,4,4); reserved acceptance_rows=8
        # must instead reserve exactly 8 for HOLD_OUTSIDE and divide the
        # remaining 12 rows across the other 4 primitives.
        distinguishing_result = expand_program(
            _program(accepted_break(20, "ZONE_A", ZoneSide.UPPER, Decimal("5"), 8)),
            "MACRO_V1",
        )
        assert distinguishing_result.success is True
        assert tuple(
            item.row_budget for item in distinguishing_result.expanded_instructions
        ) == (3, 3, 3, 3, 8)
        checks["macro_expansion"] = True

        # --- budget conservation, grouped by source phrase ---
        phrase_budgets = {
            0: phrase_0.row_budget, 1: phrase_1.row_budget, 2: phrase_2.row_budget,
            3: phrase_3.row_budget, 4: phrase_4.row_budget, 5: phrase_5.row_budget,
            6: phrase_6.row_budget,
        }
        totals: dict[int, int] = {}
        for item in result.expanded_instructions:
            totals[item.instruction.source_phrase_index] = (
                totals.get(item.instruction.source_phrase_index, 0) + item.row_budget
            )
        assert totals == phrase_budgets
        checks["budget_conservation"] = True

        # --- instruction ordering (strict, never sorted) ---
        expected_source_phrase_indices = (
            0, 1,
            2, 2, 2, 2, 2,
            3, 3, 3, 3,
            4, 4, 4,
            5, 5, 5,
            6, 6,
        )
        actual_source_phrase_indices = tuple(
            item.instruction.source_phrase_index for item in result.expanded_instructions
        )
        assert actual_source_phrase_indices == expected_source_phrase_indices
        actual_indices = tuple(
            item.instruction.instruction_index for item in result.expanded_instructions
        )
        assert actual_indices == tuple(range(19))
        checks["instruction_ordering"] = True

        # --- diagnostics ordering: append order (by phrase index) differs
        # from deterministic_key sort order (by code), proving real sorting ---
        unordered_program = _program(
            break_candidate(5, "ZONE_A", ZoneSide.UPPER, Decimal("2")),
            accepted_break(2, "ZONE_A", ZoneSide.UPPER, Decimal("5"), 3),
        )
        unordered_result = expand_program(unordered_program, "MACRO_V1")
        assert unordered_result.success is False
        assert unordered_result.expanded_instructions == ()
        codes = tuple(diag.code for diag in unordered_result.diagnostics)
        assert codes == ("ALLOCATION_MISMATCH", "MISSING_EXPANSION_RULE")
        assert all(
            diag.severity == DiagnosticSeverity.FATAL
            for diag in unordered_result.diagnostics
        )
        keys = [diag.deterministic_key for diag in unordered_result.diagnostics]
        assert keys == sorted(keys)
        checks["diagnostics_ordering"] = True

        # --- fingerprint determinism ---
        repeat_result = expand_program(
            _program(
                phrase_0, phrase_1, phrase_2, phrase_3, phrase_4, phrase_5, phrase_6
            ),
            "MACRO_V1",
        )
        assert repeat_result.expansion_fingerprint == result.expansion_fingerprint
        assert repeat_result == result

        different_program = _program(hold(11, RelativePosition.CENTER))
        different_result = expand_program(different_program, "MACRO_V1")
        assert different_result.expansion_fingerprint != result.expansion_fingerprint
        checks["fingerprint_determinism"] = True

        # --- fatal diagnostics: unregistered V1 macros ---
        break_result = expand_program(
            _program(break_candidate(5, "ZONE_A", ZoneSide.UPPER, Decimal("2"))),
            "MACRO_V1",
        )
        assert break_result.success is False
        assert break_result.expanded_instructions == ()
        assert break_result.diagnostics[0].code == "MISSING_EXPANSION_RULE"

        empty_schedule_result = expand_program(
            _program(compress(5, "ZONE_A", ())), "MACRO_V1"
        )
        assert empty_schedule_result.success is False
        assert empty_schedule_result.expanded_instructions == ()
        assert (
            empty_schedule_result.diagnostics[0].code
            == "MISSING_REQUIRED_GRAMMAR_PARAMETER"
        )

        # raw construction bypassing accepted_break(): acceptance_rows absent
        missing_acceptance_phrase = GrammarPhrase(
            phrase_type=PhraseType.ACCEPTED_BREAK,
            params=(
                GrammarParameter("clearance", Decimal("5")),
                GrammarParameter("side", ZoneSide.UPPER),
            ),
            row_budget=15,
            target_zone="ZONE_A",
            description="raw construction, no acceptance_rows",
        )
        missing_acceptance_result = expand_program(
            _program(missing_acceptance_phrase), "MACRO_V1"
        )
        assert missing_acceptance_result.success is False
        assert missing_acceptance_result.expanded_instructions == ()
        assert (
            missing_acceptance_result.diagnostics[0].code
            == "MISSING_REQUIRED_GRAMMAR_PARAMETER"
        )

        # raw construction bypassing reclaim(): residence_rows absent
        missing_residence_phrase = GrammarPhrase(
            phrase_type=PhraseType.RECLAIM,
            params=(
                GrammarParameter("depth", Decimal("2")),
                GrammarParameter("side", ZoneSide.UPPER),
            ),
            row_budget=9,
            target_zone="ZONE_A",
            description="raw construction, no residence_rows",
        )
        missing_residence_result = expand_program(
            _program(missing_residence_phrase), "MACRO_V1"
        )
        assert missing_residence_result.success is False
        assert missing_residence_result.expanded_instructions == ()
        assert (
            missing_residence_result.diagnostics[0].code
            == "MISSING_REQUIRED_GRAMMAR_PARAMETER"
        )
        checks["fatal_diagnostics"] = True

        # --- research isolation ---
        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        import_lines = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        assert not any(token in import_lines for token in FORBIDDEN_IMPORTS)
        assert not any(token in source for token in FORBIDDEN_CONTRACTS)
        assert "def run_scenario" not in source
        assert "row_start" not in source
        assert "row_end" not in source
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    for field in (
        "atomic_passthrough", "macro_expansion", "budget_conservation",
        "instruction_ordering", "diagnostics_ordering", "fingerprint_determinism",
        "fatal_diagnostics", "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

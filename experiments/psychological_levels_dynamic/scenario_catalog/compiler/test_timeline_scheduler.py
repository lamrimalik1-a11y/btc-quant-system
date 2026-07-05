"""Validation for the deterministic timeline scheduler only."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_catalog.compiler.diagnostics import (
    CompilerDiagnostic,
    DiagnosticSeverity,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.expansion import (
    ExpandedInstruction,
    ExpansionResult,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.macro_expansion import (
    expand_program,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.primitives import (
    PrimitiveInstruction,
    PrimitiveType,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.timeline_scheduler import (
    schedule_expansion,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.ast import (
    GRAMMAR_SCHEMA_VERSION,
    GrammarParameter,
    GrammarProgram,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    PathSmoothness,
    RelativePosition,
    ZoneSide,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.phrases import (
    accepted_break,
    compress,
    expand,
    hold,
    reclaim,
    recovery_gap,
    transfer_to_zone,
)

MODULE_PATH = Path(__file__).with_name("timeline_scheduler.py")
FORBIDDEN_IMPORTS = (
    "scenario_runner", "scenario_contract", "scenario_registry",
    "scenario_primitives", "test_dynamic_state_transitions",
    "test_transition_graph", "test_trajectory_evolution",
    "test_prediction_evolution", "core.", "engines.", "research.", "random",
)
FORBIDDEN_CONTRACTS = (
    "priceobservation", "scenariospecification", "geometrycontext(",
    "geometryreference(", "dynamic_state", "research_", "decimal",
    "def generate_price",
)

DUMMY_GRAMMAR_FINGERPRINT = "sha256:" + "1" * 64
DUMMY_EXPANSION_FINGERPRINT = "sha256:" + "2" * 64


def _instruction(
    instruction_index: int,
    source_phrase_index: int,
    primitive_type: PrimitiveType,
    target_zone: str | None = None,
    macro_origin: str | None = None,
    parameters: tuple[GrammarParameter, ...] = (),
) -> PrimitiveInstruction:
    return PrimitiveInstruction(
        instruction_index=instruction_index,
        source_phrase_index=source_phrase_index,
        primitive_type=primitive_type,
        parameters=parameters,
        target_zone=target_zone,
        macro_origin=macro_origin,
    )


def _expanded(index: int, primitive_type: PrimitiveType, row_budget: int) -> ExpandedInstruction:
    return ExpandedInstruction(_instruction(index, index, primitive_type), row_budget)


def _expansion_result(
    expanded_instructions: tuple[ExpandedInstruction, ...],
    success: bool = True,
    compiler_version: str = "SCHED_TEST_V1",
    diagnostics: tuple[CompilerDiagnostic, ...] = (),
) -> ExpansionResult:
    return ExpansionResult(
        success=success,
        expanded_instructions=expanded_instructions,
        diagnostics=diagnostics,
        grammar_fingerprint=DUMMY_GRAMMAR_FINGERPRINT,
        compiler_version=compiler_version,
        expansion_fingerprint=DUMMY_EXPANSION_FINGERPRINT,
    )


def _program(*phrases: Any) -> GrammarProgram:
    return GrammarProgram("SCHEDULER_TEST", GRAMMAR_SCHEMA_VERSION, phrases, (), (), ())


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "sequential_scheduling": False,
        "gap_overlap_freedom": False,
        "final_row_correctness": False,
        "fingerprint_determinism": False,
        "fatal_rollback": False,
        "instruction_preservation": False,
        "research_isolation": False,
    }

    try:
        # --- sequential scheduling: the spec's own literal example ---
        example = _expansion_result(
            (
                _expanded(0, PrimitiveType.HOLD, 3),
                _expanded(1, PrimitiveType.RAMP, 2),
                _expanded(2, PrimitiveType.OSCILLATE, 4),
            )
        )
        example_scheduled = schedule_expansion(example)
        assert example_scheduled.success is True
        example_segments = example_scheduled.timeline.segments
        assert (example_segments[0].row_start, example_segments[0].row_end) == (1, 3)
        assert (example_segments[1].row_start, example_segments[1].row_end) == (4, 5)
        assert (example_segments[2].row_start, example_segments[2].row_end) == (6, 9)
        assert example_segments[0].segment_index == 0
        assert example_segments[2].segment_index == 2
        linear_ramp = _expansion_result(
            (
                ExpandedInstruction(
                    _instruction(
                        0,
                        0,
                        PrimitiveType.RAMP,
                        parameters=(
                            GrammarParameter("smoothness", PathSmoothness.LINEAR),
                        ),
                    ),
                    2,
                ),
            )
        )
        assert (
            schedule_expansion(linear_ramp)
            .timeline.segments[0]
            .interpolation_policy
            == PathSmoothness.LINEAR
        )
        checks["sequential_scheduling"] = True

        # --- multi-segment gap/overlap freedom + final row correctness,
        # verified independently of the scheduler's own internal checks ---
        budgets = (5, 1, 7, 2, 3, 4)
        multi = _expansion_result(
            tuple(
                _expanded(i, PrimitiveType.HOLD, budget)
                for i, budget in enumerate(budgets)
            )
        )
        multi_scheduled = schedule_expansion(multi)
        assert multi_scheduled.success is True
        segments = multi_scheduled.timeline.segments
        assert len(segments) == len(budgets)
        assert segments[0].row_start == 1
        for previous, current in zip(segments, segments[1:]):
            assert current.row_start == previous.row_end + 1
        checks["gap_overlap_freedom"] = True

        assert segments[-1].row_end == sum(budgets)
        for segment, budget in zip(segments, budgets):
            assert segment.row_count == budget
            assert segment.row_end - segment.row_start + 1 == budget
        checks["final_row_correctness"] = True

        # --- no instruction may disappear, split, or merge ---
        assert len(segments) == len(multi.expanded_instructions)
        for segment, item in zip(segments, multi.expanded_instructions):
            assert segment.source_phrase_index == item.instruction.source_phrase_index
            assert segment.primitive_type == item.instruction.primitive_type
            assert segment.target_zone == item.instruction.target_zone
            assert segment.macro_origin == item.instruction.macro_origin
            assert segment.row_count == item.row_budget
        checks["instruction_preservation"] = True

        # --- fingerprint determinism ---
        repeat_scheduled = schedule_expansion(
            _expansion_result(
                tuple(
                    _expanded(i, PrimitiveType.HOLD, budget)
                    for i, budget in enumerate(budgets)
                )
            )
        )
        assert repeat_scheduled.timeline_fingerprint == multi_scheduled.timeline_fingerprint
        assert repeat_scheduled == multi_scheduled

        different_scheduled = schedule_expansion(
            _expansion_result((_expanded(0, PrimitiveType.HOLD, 99),))
        )
        assert different_scheduled.timeline_fingerprint != multi_scheduled.timeline_fingerprint
        checks["fingerprint_determinism"] = True

        # --- fatal rollback: every reject case produces success=False,
        # timeline=None, and the documented diagnostic code ---
        upstream_diagnostic = CompilerDiagnostic(
            code="UPSTREAM_TEST_FAILURE",
            severity=DiagnosticSeverity.FATAL,
            message="Preserve this upstream diagnostic.",
        )
        upstream_failed = schedule_expansion(
            _expansion_result(
                (),
                success=False,
                diagnostics=(upstream_diagnostic,),
            )
        )
        assert upstream_failed.success is False
        assert upstream_failed.timeline is None
        assert {item.code for item in upstream_failed.diagnostics} == {
            "UPSTREAM_EXPANSION_FAILED",
            "UPSTREAM_TEST_FAILURE",
        }

        empty_result = schedule_expansion(_expansion_result(()))
        assert empty_result.success is False
        assert empty_result.timeline is None
        assert empty_result.diagnostics[0].code == "EMPTY_EXPANSION_RESULT"
        assert (
            upstream_failed.timeline_fingerprint
            != empty_result.timeline_fingerprint
        )

        duplicate_indices = _expansion_result(
            (
                _expanded(0, PrimitiveType.HOLD, 3),
                ExpandedInstruction(
                    _instruction(0, 1, PrimitiveType.RAMP), 2
                ),
            )
        )
        duplicate_result = schedule_expansion(duplicate_indices)
        assert duplicate_result.success is False
        assert duplicate_result.timeline is None
        assert duplicate_result.diagnostics[0].code == "DUPLICATE_INSTRUCTION_INDEX"

        non_contiguous = _expansion_result(
            (
                _expanded(0, PrimitiveType.HOLD, 3),
                _expanded(1, PrimitiveType.RAMP, 2),
                ExpandedInstruction(
                    _instruction(3, 2, PrimitiveType.OSCILLATE), 4
                ),
            )
        )
        non_contiguous_result = schedule_expansion(non_contiguous)
        assert non_contiguous_result.success is False
        assert non_contiguous_result.timeline is None
        assert non_contiguous_result.diagnostics[0].code == "NON_CONTIGUOUS_INSTRUCTION_INDEX"

        reordered = _expansion_result(
            (
                ExpandedInstruction(_instruction(1, 0, PrimitiveType.HOLD), 3),
                ExpandedInstruction(_instruction(0, 1, PrimitiveType.RAMP), 2),
            )
        )
        reordered_result = schedule_expansion(reordered)
        assert reordered_result.success is False
        assert reordered_result.timeline is None
        assert reordered_result.diagnostics[0].code == "NON_CONTIGUOUS_INSTRUCTION_INDEX"
        assert (
            duplicate_result.timeline_fingerprint
            != non_contiguous_result.timeline_fingerprint
        )

        # Note: "instruction row_budget <= 0" is a documented reject case but
        # is structurally unreachable through the public API: ExpandedInstruction
        # itself raises ValueError for row_budget <= 0 at construction time, so
        # no ExpansionResult can ever carry one. The NON_POSITIVE_ROW_BUDGET
        # check in the scheduler exists purely as defense-in-depth and cannot
        # be exercised without bypassing an already-frozen contract.
        checks["fatal_rollback"] = True

        # --- end-to-end integration: real expand_program() output scheduled ---
        real_program = _program(
            hold(10, RelativePosition.CENTER),
            recovery_gap(4, "ZONE_A", Decimal("3")),
            accepted_break(15, "ZONE_A", ZoneSide.UPPER, Decimal("5"), 3),
            reclaim(9, "ZONE_A", ZoneSide.UPPER, Decimal("2"), 4),
            transfer_to_zone(6, "ZONE_A", "ZONE_B", Decimal("100")),
            compress(7, "ZONE_B", (Decimal("10"), Decimal("5"), Decimal("2"))),
            expand(5, "ZONE_B", (Decimal("1"), Decimal("2"))),
        )
        real_expansion = expand_program(real_program, "MACRO_V1")
        assert real_expansion.success is True
        real_scheduled = schedule_expansion(real_expansion)
        assert real_scheduled.success is True
        assert len(real_scheduled.timeline.segments) == 19
        assert real_scheduled.timeline.segments[-1].row_end == 56
        assert real_scheduled.compiler_version == "MACRO_V1"
        assert real_scheduled.grammar_fingerprint == real_expansion.grammar_fingerprint
        assert real_scheduled.expansion_fingerprint == real_expansion.expansion_fingerprint

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
        assert "def materialize" not in source
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    for field in (
        "sequential_scheduling", "gap_overlap_freedom", "final_row_correctness",
        "fingerprint_determinism", "fatal_rollback", "instruction_preservation",
        "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

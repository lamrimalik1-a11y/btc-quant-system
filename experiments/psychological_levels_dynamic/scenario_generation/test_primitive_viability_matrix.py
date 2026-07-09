"""Primitive and macro viability matrix for the Project 2 pipeline.

Diagnostic only: runs minimal generated scenarios through the existing Project 2
pipeline and reports which grammar constructors are viable end-to-end. It does
not patch primitive behavior, modify compiler semantics, or treat weak Stage
output as failure.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
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
    RelativePosition,
    ZoneSide,
)
from experiments.psychological_levels_dynamic.scenario_generation.batch_compiler import (
    compile_generation_batch,
)
from experiments.psychological_levels_dynamic.scenario_generation.batch_execution import (
    execute_batch,
)
from experiments.psychological_levels_dynamic.scenario_generation.batch_specification_assembler import (
    assemble_batch,
)
from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    GrammarTemplate,
    PhraseSlot,
)
from experiments.psychological_levels_dynamic.scenario_generation.generator import (
    generate_programs,
)
from experiments.psychological_levels_dynamic.scenario_generation.manifest_validation import (
    validate_manifest,
)
from experiments.psychological_levels_dynamic.scenario_generation.runner_execution_context import (
    RunnerExecutionContext,
)

COMPILER_VERSION = "PHASE2D_PRIMITIVE_MATRIX_COMPILER_V1"
BATCH_COMPILER_VERSION = "PHASE2D_PRIMITIVE_MATRIX_BATCH_COMPILER_V1"
ASSEMBLY_VERSION = "PHASE2D_PRIMITIVE_MATRIX_ASSEMBLY_V1"
BATCH_EXECUTION_VERSION = "PHASE2D_PRIMITIVE_MATRIX_EXECUTION_V1"
GENERATOR_VERSION = "PHASE2D_PRIMITIVE_MATRIX_GENERATOR_V1"
VALIDATOR_VERSION = "PHASE2D_PRIMITIVE_MATRIX_VALIDATOR_V1"

SUPPORTED_CONSTRUCTORS = (
    "hold",
    "hold_outside",
    "approach_zone",
    "enter_zone",
    "penetrate",
    "withdraw",
    "recovery_gap",
    "ramp",
    "oscillate",
    "accepted_break",
    "reclaim",
    "compress",
    "expand",
    "transfer_to_zone",
    "retest_boundary",
)


@dataclass(frozen=True)
class MatrixCase:
    primitive_or_macro_name: str
    phrase_slots: tuple[PhraseSlot, ...]


def _geometry_context() -> GeometryContext:
    half_width = Decimal("25")
    return GeometryContext(
        symbol="BTCUSDT",
        geometry_version="PHASE2D_PRIMITIVE_MATRIX_GEOMETRY_V1",
        references=(
            GeometryReference(
                zone_id="ZONE_A",
                center_price=Decimal("60400"),
                lower_price=Decimal("60400") - half_width,
                upper_price=Decimal("60400") + half_width,
                half_width=half_width,
            ),
            GeometryReference(
                zone_id="ZONE_B",
                center_price=Decimal("60600"),
                lower_price=Decimal("60600") - half_width,
                upper_price=Decimal("60600") + half_width,
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
        session_id="PHASE2D_PRIMITIVE_VIABILITY_MATRIX_SESSION",
        runner_version="PHASE2D_PRIMITIVE_MATRIX_RUNNER_V1",
    )


def _slot(constructor_name: str, **params: Any) -> PhraseSlot:
    return PhraseSlot(
        constructor_name=constructor_name,
        fixed_params=tuple(sorted(params.items())),
        axis_bound_params=(),
    )


def _outside(rows: int = 4, zone: str = "ZONE_A") -> PhraseSlot:
    return _slot(
        "hold_outside",
        row_budget=rows,
        target_zone=zone,
        side=ZoneSide.UPPER,
        clearance=Decimal("0.20"),
    )


def _cycles(pattern: tuple[PhraseSlot, ...], count: int = 6) -> tuple[PhraseSlot, ...]:
    return tuple(slot for _ in range(count) for slot in (pattern + (_outside(),)))


def _template(case: MatrixCase) -> GrammarTemplate:
    return GrammarTemplate(
        template_id=f"PRIMITIVE_MATRIX_{case.primitive_or_macro_name.upper()}",
        template_version="1",
        family_tag="PHASE2D_PRIMITIVE_VIABILITY_MATRIX",
        description=f"Minimal diagnostic case for {case.primitive_or_macro_name}.",
        phrase_slots=case.phrase_slots,
        axes=(),
        rules=(),
    )


def _cases() -> tuple[MatrixCase, ...]:
    return (
        MatrixCase(
            "hold",
            _cycles((_slot("hold", row_budget=6, position=RelativePosition.CENTER, target_zone="ZONE_A"),)),
        ),
        MatrixCase(
            "hold_outside",
            (_outside(6),),
        ),
        MatrixCase(
            "approach_zone",
            (
                _slot("approach_zone", row_budget=4, target_zone="ZONE_A", side=ZoneSide.LOWER, start_distance=Decimal("0.40")),
                _outside(4),
            ),
        ),
        MatrixCase(
            "enter_zone",
            _cycles((_slot("enter_zone", row_budget=4, target_zone="ZONE_A", side=ZoneSide.LOWER, depth=Decimal("0.40")),)),
        ),
        MatrixCase(
            "penetrate",
            _cycles((
                _slot("enter_zone", row_budget=4, target_zone="ZONE_A", side=ZoneSide.LOWER, depth=Decimal("0.40")),
                _slot("penetrate", row_budget=4, target_zone="ZONE_A", depth=Decimal("0.40"), side=ZoneSide.LOWER),
            )),
        ),
        MatrixCase(
            "withdraw",
            (_slot("withdraw", row_budget=4, target_zone="ZONE_A", side=ZoneSide.UPPER, distance=Decimal("0.40")),),
        ),
        MatrixCase(
            "recovery_gap",
            (_slot("recovery_gap", row_budget=4, target_zone="ZONE_A", withdrawal_distance=Decimal("0.40")),),
        ),
        MatrixCase(
            "ramp",
            (_slot("ramp", row_budget=4, distance=Decimal("0.40"), direction=Direction.UP, smoothness=PathSmoothness.LINEAR),),
        ),
        MatrixCase(
            "oscillate",
            _cycles((_slot("oscillate", row_budget=6, target_zone="ZONE_A", amplitude=Decimal("0.20"), period_rows=2),)),
        ),
        MatrixCase(
            "accepted_break",
            (_slot("accepted_break", row_budget=10, target_zone="ZONE_A", side=ZoneSide.UPPER, clearance=Decimal("0.40"), acceptance_rows=3),),
        ),
        MatrixCase(
            "reclaim",
            (
                _slot("reclaim", row_budget=10, target_zone="ZONE_A", side=ZoneSide.UPPER, depth=Decimal("0.40"), residence_rows=3),
                _outside(4),
            ),
        ),
        MatrixCase(
            "compress",
            _cycles((_slot("compress", row_budget=6, target_zone="ZONE_A", amplitude_schedule=(Decimal("0.30"), Decimal("0.20"), Decimal("0.10"))),)),
        ),
        MatrixCase(
            "expand",
            _cycles((_slot("expand", row_budget=6, target_zone="ZONE_A", amplitude_schedule=(Decimal("0.10"), Decimal("0.20"), Decimal("0.30"))),)),
        ),
        MatrixCase(
            "transfer_to_zone",
            (
                _slot("transfer_to_zone", row_budget=9, source_zone="ZONE_A", target_zone="ZONE_B", travel_distance=Decimal("0.40")),
                _outside(4, "ZONE_B"),
            ),
        ),
        MatrixCase(
            "retest_boundary",
            (_slot("retest_boundary", row_budget=6, target_zone="ZONE_A", side=ZoneSide.UPPER, delay_rows=2, depth=Decimal("0.40")),),
        ),
    )


def _summary_dict(record: Any | None) -> dict[str, Any]:
    if record is None:
        return {}
    return dict(record.summary)


def _diagnostics(*values: Any) -> tuple[str, ...]:
    collected: list[str] = []
    for value in values:
        diagnostics = getattr(value, "diagnostics", ())
        collected.extend(str(item) for item in diagnostics)
    return tuple(collected)


def _status(row: dict[str, Any]) -> str:
    if row["generated"] != "YES":
        return "NOT_AUTHORABLE"
    if row["compiled"] != "YES" or row["assembled"] != "YES" or row["executed"] != "YES":
        return "NOT_VIABLE"
    if row["runner_result"] not in {"PASS", "FAIL"}:
        return "NOT_VIABLE"
    if any(
        value not in (None, 0, "NOT_AVAILABLE")
        for value in (
            row["completed_visits"],
            row["transitions_generated"],
            row["trajectory_records"],
            row["confirmed_hypotheses"],
            row["pending_hypotheses"],
        )
    ):
        return "VIABLE_NON_TRIVIAL"
    return "VIABLE_EMPTY"


def _evaluate_case(case: MatrixCase) -> dict[str, Any]:
    generation = generate_programs(_template(case), GENERATOR_VERSION)
    manifest_validation = validate_manifest(generation.manifest, VALIDATOR_VERSION) if generation.manifest else None
    compilation = compile_generation_batch(generation, _geometry_context(), COMPILER_VERSION, BATCH_COMPILER_VERSION)
    execution_context = _execution_context()
    assembly = assemble_batch(compilation, execution_context, ASSEMBLY_VERSION)
    execution = execute_batch(
        assembly.assembled_specifications,
        execution_context,
        BATCH_EXECUTION_VERSION,
        source_manifest_fingerprint=None if generation.manifest is None else generation.manifest.manifest_fingerprint,
        batch_compilation_fingerprint=compilation.batch_compilation_fingerprint,
        batch_assembly_fingerprint=assembly.batch_assembly_fingerprint,
    )
    record = execution.scenario_results[0] if execution.scenario_results else None
    summary = _summary_dict(record)
    row = {
        "primitive_or_macro_name": case.primitive_or_macro_name,
        "generated": "YES" if generation.success and len(generation.generated_programs) == 1 else "NO",
        "manifest_validated": "YES" if manifest_validation is not None and manifest_validation.success else "NO",
        "compiled": "YES" if compilation.success and compilation.compiled_programs == 1 else "NO",
        "assembled": "YES" if assembly.success and len(assembly.assembled_specifications) == 1 else "NO",
        "executed": "YES" if record is not None and record.execution_status == "EXECUTED" else "NO",
        "runner_result": None if record is None else record.runner_result,
        "completed_visits": summary.get("completed_visits"),
        "transitions_generated": summary.get("transitions_generated"),
        "trajectory_records": summary.get("trajectory_records"),
        "confirmed_hypotheses": summary.get("confirmed_hypotheses"),
        "pending_hypotheses": summary.get("pending_hypotheses"),
        "diagnostics": _diagnostics(generation, manifest_validation, compilation, assembly, execution),
    }
    row["viability_status"] = _status(row)
    return row


def _matrix() -> tuple[dict[str, Any], ...]:
    return tuple(_evaluate_case(case) for case in _cases())


def _render_matrix(matrix: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    columns = (
        "primitive_or_macro_name",
        "generated",
        "manifest_validated",
        "compiled",
        "assembled",
        "executed",
        "runner_result",
        "completed_visits",
        "transitions_generated",
        "trajectory_records",
        "confirmed_hypotheses",
        "pending_hypotheses",
        "viability_status",
    )
    lines = [" | ".join(columns)]
    for row in matrix:
        lines.append(" | ".join(str(row.get(column)) for column in columns))
    return tuple(lines)


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "supported_constructors_covered": False,
        "matrix_produced": False,
        "deterministic_matrix": False,
        "deterministic_ordering": False,
        "explicit_non_viable_status": False,
        "non_trivial_activity_detected": False,
        "weak_outputs_do_not_fail": False,
        "research_isolation": False,
    }
    matrix: tuple[dict[str, Any], ...] = ()
    try:
        matrix = _matrix()
        second_matrix = _matrix()
        names = tuple(row["primitive_or_macro_name"] for row in matrix)
        checks["supported_constructors_covered"] = names == SUPPORTED_CONSTRUCTORS
        checks["matrix_produced"] = len(matrix) == len(SUPPORTED_CONSTRUCTORS)
        checks["deterministic_matrix"] = matrix == second_matrix
        checks["deterministic_ordering"] = names == SUPPORTED_CONSTRUCTORS
        checks["explicit_non_viable_status"] = any(row["viability_status"] == "NOT_VIABLE" for row in matrix)
        checks["non_trivial_activity_detected"] = any(row["viability_status"] == "VIABLE_NON_TRIVIAL" for row in matrix)
        checks["weak_outputs_do_not_fail"] = any(row["viability_status"] == "VIABLE_EMPTY" for row in matrix)
        source = Path(__file__).read_text(encoding="utf-8").lower()
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        checks["research_isolation"] = not any(token in imports for token in ("core.", "engines.", "research."))
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {
        **checks,
        "matrix": matrix,
        "rendered_matrix": _render_matrix(matrix) if matrix else (),
        "errors": errors,
        "result": result_status,
    }


def main() -> None:
    report = run()
    print("primitive_or_macro_name | generated | manifest_validated | compiled | assembled | executed | runner_result | completed_visits | transitions_generated | trajectory_records | confirmed_hypotheses | pending_hypotheses | viability_status")
    for line in report["rendered_matrix"][1:]:
        print(line)
    for field in (
        "supported_constructors_covered",
        "matrix_produced",
        "deterministic_matrix",
        "deterministic_ordering",
        "explicit_non_viable_status",
        "non_trivial_activity_detected",
        "weak_outputs_do_not_fail",
        "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)
    print("PHASE2D_PRIMITIVE_VIABILITY_MATRIX PASS")


if __name__ == "__main__":
    main()
"""Validation for geometry resolution logic only."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_catalog.compiler.expansion import ExpandedInstruction, ExpansionResult
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.geometry import GeometryContext, GeometryReference
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.geometry_resolution import resolve_geometry
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.macro_expansion import expand_program
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.primitives import PrimitiveInstruction, PrimitiveType
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.timeline_scheduler import schedule_expansion
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.ast import GRAMMAR_SCHEMA_VERSION, GrammarParameter, GrammarProgram
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import RelativePosition, ZoneSide
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.phrases import hold, transfer_to_zone

MODULE_PATH = Path(__file__).with_name("geometry_resolution.py")
FORBIDDEN_IMPORTS = (
    "scenario_runner", "scenario_contract", "scenario_registry",
    "scenario_primitives", "test_dynamic_state_transitions",
    "test_transition_graph", "test_trajectory_evolution",
    "test_prediction_evolution", "core.", "engines.", "research.", "random",
)
FORBIDDEN_CONTRACTS = (
    "priceobservation", "scenariospecification", "dynamic_state", "research_",
    "def materialize", "def generate_price", "run_scenario",
)


def _zone(zone_id: str, center: str) -> GeometryReference:
    center_price = Decimal(center)
    half_width = Decimal("25")
    return GeometryReference(
        zone_id=zone_id,
        center_price=center_price,
        lower_price=center_price - half_width,
        upper_price=center_price + half_width,
        half_width=half_width,
    )


def _geometry(same_center: bool = False) -> GeometryContext:
    target_center = "60000" if same_center else "60400"
    return GeometryContext(
        symbol="BTCUSDT",
        geometry_version="GEOMETRY_RESOLUTION_TEST_V1",
        references=(_zone("SOURCE", "60000"), _zone("TARGET", target_center)),
    )


def _program(*phrases: Any) -> GrammarProgram:
    return GrammarProgram("GEOMETRY_RESOLUTION_TEST", GRAMMAR_SCHEMA_VERSION, phrases, (), (), ())


def _expand_schedule(program: GrammarProgram):
    expansion = expand_program(program, "GEOMETRY_RESOLUTION_TEST_COMPILER_V1")
    scheduling = schedule_expansion(expansion)
    assert expansion.success is True
    assert scheduling.success is True
    return expansion, scheduling


def _raw_expansion(instruction: PrimitiveInstruction) -> ExpansionResult:
    item = ExpandedInstruction(instruction, 1)
    # Reuse a real successful expansion fingerprint shape by expanding a tiny
    # program, then replace only the instruction payload for isolated edge tests.
    base, _ = _expand_schedule(_program(hold(1, RelativePosition.CENTER, "TARGET")))
    return ExpansionResult(
        success=True,
        expanded_instructions=(item,),
        diagnostics=(),
        grammar_fingerprint=base.grammar_fingerprint,
        compiler_version=base.compiler_version,
        expansion_fingerprint="sha256:" + "9" * 64,
    )


def _raw_schedule(expansion: ExpansionResult):
    return schedule_expansion(expansion)


def _codes(result) -> set[str]:
    return {diagnostic.code for diagnostic in result.diagnostics}


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "basic_resolution": False,
        "transfer_resolution": False,
        "fatal_diagnostics": False,
        "fingerprint_determinism": False,
        "cross_process_determinism": False,
        "research_isolation": False,
    }
    try:
        expansion, scheduling = _expand_schedule(_program(hold(3, RelativePosition.CENTER, "TARGET")))
        resolved = resolve_geometry(expansion, scheduling, _geometry())
        assert resolved.success is True
        assert len(resolved.resolved_timeline.segments) == 1
        segment = resolved.resolved_timeline.segments[0]
        assert segment.start_coordinate_intent.absolute_price == Decimal("60400")
        assert segment.end_coordinate_intent.absolute_price == Decimal("60400")
        assert segment.resolved_target_zone.zone_id == "TARGET"
        checks["basic_resolution"] = True

        transfer_expansion, transfer_scheduling = _expand_schedule(_program(transfer_to_zone(6, "SOURCE", "TARGET", Decimal("1"))))
        transfer = resolve_geometry(transfer_expansion, transfer_scheduling, _geometry())
        assert transfer.success is True
        transfer_segments = transfer.resolved_timeline.segments
        assert transfer_segments[0].expanded_instruction.instruction.primitive_type == PrimitiveType.WITHDRAW
        assert transfer_segments[0].resolved_source_zone.zone_id == "SOURCE"
        assert transfer_segments[0].end_coordinate_intent.zone_id == "SOURCE"
        assert transfer_segments[0].end_coordinate_intent.absolute_price == Decimal("60050")
        ramp_direction = {param.name: param.value for param in transfer_segments[1].resolved_parameters}["inferred_direction"]
        assert ramp_direction == "UP"
        same_center = resolve_geometry(transfer_expansion, transfer_scheduling, _geometry(same_center=True))
        assert same_center.success is False
        assert "INVALID_TRANSFER_DIRECTION" in _codes(same_center)
        checks["transfer_resolution"] = True

        bad_instruction = PrimitiveInstruction(
            instruction_index=0,
            source_phrase_index=0,
            primitive_type=PrimitiveType.HOLD,
            parameters=(GrammarParameter("position", RelativePosition.OUTSIDE_UPPER),),
            target_zone="TARGET",
            macro_origin=None,
        )
        bad_expansion = _raw_expansion(bad_instruction)
        bad_scheduling = _raw_schedule(bad_expansion)
        bad_hold = resolve_geometry(bad_expansion, bad_scheduling, _geometry())
        assert bad_hold.success is False
        assert "INVALID_DISTANCE" in _codes(bad_hold)
        no_side_penetration = PrimitiveInstruction(
            instruction_index=0,
            source_phrase_index=0,
            primitive_type=PrimitiveType.PENETRATE,
            parameters=(GrammarParameter("depth", Decimal("0.5")),),
            target_zone="TARGET",
            macro_origin=None,
        )
        no_side_expansion = _raw_expansion(no_side_penetration)
        no_side_scheduling = _raw_schedule(no_side_expansion)
        no_side_result = resolve_geometry(no_side_expansion, no_side_scheduling, _geometry())
        assert no_side_result.success is False
        assert no_side_result.resolved_timeline is None
        assert "UNRESOLVABLE_PENETRATION_DIRECTION" in _codes(no_side_result)
        mismatch = resolve_geometry(
            transfer_expansion,
            replace(transfer_scheduling, expansion_fingerprint="sha256:" + "8" * 64),
            _geometry(),
        )
        assert mismatch.success is False
        assert "EXPANSION_SCHEDULING_FINGERPRINT_MISMATCH" in _codes(mismatch)
        checks["fatal_diagnostics"] = True

        repeat = resolve_geometry(expansion, scheduling, _geometry())
        assert repeat.resolution_fingerprint == resolved.resolution_fingerprint
        assert repeat == resolved
        changed = resolve_geometry(expansion, scheduling, GeometryContext("BTCUSDT", "GEOMETRY_RESOLUTION_TEST_V2", (_zone("TARGET", "60400"),)))
        assert changed.resolution_fingerprint != resolved.resolution_fingerprint
        checks["fingerprint_determinism"] = True

        if os.environ.get("GEOMETRY_RESOLUTION_CHILD") == "1":
            checks["cross_process_determinism"] = True
        else:
            env = dict(os.environ)
            env["GEOMETRY_RESOLUTION_CHILD"] = "1"
            first = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
            second = subprocess.check_output([sys.executable, str(Path(__file__))], text=True, env=env)
            assert first == second
            checks["cross_process_determinism"] = True

        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        imports = "\n".join(line.strip() for line in source.splitlines() if line.lstrip().startswith(("from ", "import ")))
        assert not any(token in imports for token in FORBIDDEN_IMPORTS)
        assert not any(token in source for token in FORBIDDEN_CONTRACTS)
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result}


def main() -> None:
    report = run()
    for field in (
        "basic_resolution", "transfer_resolution", "fatal_diagnostics",
        "fingerprint_determinism", "cross_process_determinism", "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

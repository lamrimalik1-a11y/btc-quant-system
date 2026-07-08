"""Validation for ScenarioSpecification assembly from compiler output only."""

from __future__ import annotations

import dataclasses
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_contract import (
    PriceObservation,
    ScenarioSpecification,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.full_compiler import (
    compile_program,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.geometry import (
    GeometryContext,
    GeometryReference,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.specification_assembler import (
    AssembledSpecification,
    assemble_specification,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.ast import (
    GRAMMAR_SCHEMA_VERSION,
    GrammarProgram,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    RelativePosition,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.phrases import (
    hold,
    penetrate,
)

MODULE_PATH = Path(__file__).with_name("specification_assembler.py")
COMPILER_VERSION = "SPECIFICATION_ASSEMBLER_TEST_COMPILER_V1"
FORBIDDEN_IMPORTS = (
    "scenario_runner",
    "scenario_registry",
    "scenario_primitives",
    "scenario_catalog.catalog",
    "scenario_catalog.families",
    "scenario_catalog.specifications",
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
    "dynamic_state",
    "research_",
    "def generate_price",
    "run_scenario",
    "compile_program(",
    "materialize_prices",
    "resolve_geometry",
    "schedule_expansion",
    "expand_program",
    "object.__setattr__",
)


def _expect_raises(exception: type[BaseException], callable_: Any) -> None:
    try:
        callable_()
    except exception:
        return
    raise AssertionError(f"expected {exception.__name__}")


def _zone() -> GeometryReference:
    center = Decimal("60400")
    half_width = Decimal("25")
    return GeometryReference(
        zone_id="ZONE_A",
        center_price=center,
        lower_price=center - half_width,
        upper_price=center + half_width,
        half_width=half_width,
    )


def _geometry() -> GeometryContext:
    return GeometryContext(
        symbol="BTCUSDT",
        geometry_version="SPECIFICATION_ASSEMBLER_TEST_GEOMETRY_V1",
        references=(_zone(),),
    )


def _program(*phrases: Any, program_id: str = "SPECIFICATION_ASSEMBLER_TEST") -> GrammarProgram:
    return GrammarProgram(program_id, GRAMMAR_SCHEMA_VERSION, phrases, (), (), ())


def _successful_compilation():
    return compile_program(
        _program(hold(4, RelativePosition.CENTER, "ZONE_A")),
        _geometry(),
        COMPILER_VERSION,
    )


def _failed_compilation():
    return compile_program(
        _program(
            penetrate(3, "ZONE_A", Decimal("0.5")),
            program_id="SPECIFICATION_ASSEMBLER_FAILURE_TEST",
        ),
        _geometry(),
        COMPILER_VERSION,
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "successful_assembly": False,
        "observation_reuse": False,
        "failure_rejects": False,
        "determinism": False,
        "cross_process_determinism": False,
        "research_isolation": False,
    }
    try:
        compilation = _successful_compilation()
        assert compilation.success is True
        assembled = assemble_specification(compilation, "ASSEMBLED_SPEC_TEST")
        assert isinstance(assembled, AssembledSpecification)
        assert isinstance(assembled.specification, ScenarioSpecification)
        spec = assembled.specification
        assert spec.scenario_id == "ASSEMBLED_SPEC_TEST"
        assert spec.scenario_family == "COMPILED_GRAMMAR_PROGRAM"
        assert spec.schema_version == "1"
        assert spec.row_count == len(compilation.observations)
        assert spec.start_price == compilation.observations[0].price
        assert spec.seed_metadata == compilation.observation_checksum
        assert spec.validation_metadata["grammar_fingerprint"] == compilation.grammar_fingerprint
        assert spec.validation_metadata["geometry_fingerprint"] == compilation.geometry_fingerprint
        assert spec.validation_metadata["observation_checksum"] == compilation.observation_checksum
        checks["successful_assembly"] = True

        assert assembled.compiled_observations is compilation.observations
        assert all(
            item is original
            for item, original in zip(
                assembled.compiled_observations,
                compilation.observations,
            )
        )
        assert spec.parameters["observation_checksum"] == compilation.observation_checksum
        field_names = {field.name for field in dataclasses.fields(AssembledSpecification)}
        assert "compiled_observations" in field_names
        assert "specification" in field_names
        checks["observation_reuse"] = True

        failed = _failed_compilation()
        assert failed.success is False
        _expect_raises(
            ValueError,
            lambda: assemble_specification(failed, "FAILED_SPEC_TEST"),
        )
        _expect_raises(
            ValueError,
            lambda: assemble_specification(compilation, ""),
        )
        _expect_raises(
            TypeError,
            lambda: AssembledSpecification(specification=spec, compiled_observations=("not_an_observation",)),
        )
        _expect_raises(
            ValueError,
            lambda: AssembledSpecification(specification=spec, compiled_observations=()),
        )
        checks["failure_rejects"] = True

        repeat = assemble_specification(_successful_compilation(), "ASSEMBLED_SPEC_TEST")
        assert repeat == assembled
        assert repeat.compiled_observations == assembled.compiled_observations
        changed_name = assemble_specification(compilation, "ASSEMBLED_SPEC_TEST_ALT")
        assert changed_name.specification.specification_fingerprint != spec.specification_fingerprint

        # Equality must actually detect a different compiled_observations tuple,
        # not silently ignore it (the defect this patch fixes).
        forged = AssembledSpecification(
            specification=spec,
            compiled_observations=(PriceObservation(1, Decimal("999999")),),
        )
        assert forged != assembled
        assert forged.compiled_observations != assembled.compiled_observations

        # dataclasses.replace() must preserve compiled_observations when not
        # explicitly overridden, and only change what is explicitly passed.
        renamed_spec = dataclasses.replace(spec, scenario_id="RENAMED_SPEC")
        replaced = dataclasses.replace(assembled, specification=renamed_spec)
        assert replaced.compiled_observations == assembled.compiled_observations
        assert replaced.specification.scenario_id == "RENAMED_SPEC"
        checks["determinism"] = True

        if os.environ.get("SPECIFICATION_ASSEMBLER_CHILD") == "1":
            checks["cross_process_determinism"] = True
        else:
            env = dict(os.environ)
            env["SPECIFICATION_ASSEMBLER_CHILD"] = "1"
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
        assert "def assemble_specification" in source
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    for field in (
        "successful_assembly",
        "observation_reuse",
        "failure_rejects",
        "determinism",
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

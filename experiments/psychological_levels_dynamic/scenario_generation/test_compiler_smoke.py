"""Validation for compiler smoke checks over generated GrammarProgram objects."""

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
    RelativePosition,
)
from experiments.psychological_levels_dynamic.scenario_generation.compiler_smoke import (
    CompilerSmokeResult,
    run_compiler_smoke,
)
from experiments.psychological_levels_dynamic.scenario_generation.contracts import (
    GrammarTemplate,
    ParameterAxis,
    PhraseSlot,
)
from experiments.psychological_levels_dynamic.scenario_generation.generator import (
    generate_programs,
)

MODULE_PATH = Path(__file__).with_name("compiler_smoke.py")
COMPILER_VERSION = "PHASE2B_COMPILER_SMOKE_TEST_COMPILER_V1"
FORBIDDEN_IMPORTS = (
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
    "stage1",
    "stage2",
    "stage3",
    "stage4",
    "stage5",
    "stage6",
    "dynamic_state",
    "research_stable",
    "research_attacker",
)


def _geometry_context() -> GeometryContext:
    center = Decimal("60400")
    half_width = Decimal("25")
    return GeometryContext(
        symbol="BTCUSDT",
        geometry_version="PHASE2B_COMPILER_SMOKE_TEST_GEOMETRY_V1",
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


def _success_template() -> GrammarTemplate:
    return GrammarTemplate(
        template_id="SMOKE_CENTER_DWELL_TEMPLATE",
        template_version="1",
        family_tag="SMOKE_CENTER_DWELL",
        description="Compile-safe center holds.",
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


def _failure_template() -> GrammarTemplate:
    return GrammarTemplate(
        template_id="SMOKE_PENETRATION_FAILURE_TEMPLATE",
        template_version="1",
        family_tag="SMOKE_FAILURE",
        description="Generated programs that fail geometry because side is unavailable.",
        phrase_slots=(
            PhraseSlot(
                constructor_name="penetrate",
                fixed_params=(("target_zone", "ZONE_A"),),
                axis_bound_params=(
                    ("row_budget", "rows"),
                    ("depth", "depth"),
                ),
            ),
        ),
        axes=(
            ParameterAxis("rows", (2,)),
            ParameterAxis("depth", (Decimal("0.5"),)),
        ),
        rules=(),
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "all_compile_success": False,
        "compilation_failure": False,
        "diagnostics_preserved": False,
        "determinism": False,
        "cross_process_determinism": False,
        "research_isolation": False,
    }
    try:
        success_generation = generate_programs(_success_template(), "SMOKE_GEN_V1")
        assert success_generation.success is True
        smoke = run_compiler_smoke(
            success_generation,
            _geometry_context(),
            COMPILER_VERSION,
            "SMOKE_TEST_V1",
        )
        assert isinstance(smoke, CompilerSmokeResult)
        assert smoke.success is True
        assert smoke.compiled_programs == 3
        assert smoke.failed_programs == 0
        assert len(smoke.compilation_results) == 3
        assert all(result.success for result in smoke.compilation_results)
        assert all(result.observation_checksum is not None for result in smoke.compilation_results)
        checks["all_compile_success"] = True

        failure_generation = generate_programs(_failure_template(), "SMOKE_GEN_V1")
        assert failure_generation.success is True
        failure_smoke = run_compiler_smoke(
            failure_generation,
            _geometry_context(),
            COMPILER_VERSION,
            "SMOKE_TEST_V1",
        )
        assert failure_smoke.success is False
        assert failure_smoke.compiled_programs == 0
        assert failure_smoke.failed_programs == 1
        assert len(failure_smoke.compilation_results) == 1
        assert failure_smoke.compilation_results[0].success is False
        checks["compilation_failure"] = True

        assert any("COMPILATION_FAILED" in diagnostic for diagnostic in failure_smoke.diagnostics)
        assert any("UNRESOLVABLE_PENETRATION_DIRECTION" in diagnostic for diagnostic in failure_smoke.diagnostics)
        checks["diagnostics_preserved"] = True

        repeat = run_compiler_smoke(
            success_generation,
            _geometry_context(),
            COMPILER_VERSION,
            "SMOKE_TEST_V1",
        )
        assert repeat == smoke
        assert repeat.smoke_fingerprint == smoke.smoke_fingerprint
        assert failure_smoke.smoke_fingerprint != smoke.smoke_fingerprint
        checks["determinism"] = True

        if os.environ.get("COMPILER_SMOKE_CHILD") == "1":
            return {
                "child_success_fingerprint": smoke.smoke_fingerprint,
                "child_failure_fingerprint": failure_smoke.smoke_fingerprint,
                "result": "PASS",
            }
        else:
            env = dict(os.environ)
            env["COMPILER_SMOKE_CHILD"] = "1"
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
    if os.environ.get("COMPILER_SMOKE_CHILD") == "1":
        print(f"success={report['child_success_fingerprint']}")
        print(f"failure={report['child_failure_fingerprint']}")
        print(f"result={report['result']}")
        if report["result"] != "PASS":
            raise SystemExit(1)
        return
    for field in (
        "all_compile_success",
        "compilation_failure",
        "diagnostics_preserved",
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
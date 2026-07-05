"""Structural validation for expansion contracts only."""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
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
    AllocationPolicy,
    ExpandedInstruction,
    ExpansionResult,
    ExpansionRule,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.primitives import (
    PrimitiveInstruction,
    PrimitiveType,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.ast import (
    PhraseType,
)


EXPANSION_MODULE = Path(__file__).with_name("expansion.py")
FORBIDDEN_IMPORTS = (
    "scenario_runner",
    "scenario_contract",
    "scenario_registry",
    "scenario_primitives",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "core.",
    "engines.",
    "research.",
    "random",
)
FORBIDDEN_CONTRACTS = (
    "priceobservation",
    "scenariospecification",
    "mechanicaltimeline",
    "geometrycontext",
    "dynamic_state",
    "research_",
)


def _expect_raises(exception: type[BaseException], callable_: Any) -> None:
    try:
        callable_()
    except exception:
        return
    raise AssertionError(f"expected {exception.__name__}")


def _instruction() -> PrimitiveInstruction:
    return PrimitiveInstruction(
        instruction_index=0,
        source_phrase_index=2,
        primitive_type=PrimitiveType.APPROACH,
        parameters=(),
        target_zone="ZONE_A",
        macro_origin=PhraseType.ACCEPTED_BREAK.value,
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "expanded_instruction": False,
        "expansion_result": False,
        "allocation_contract": False,
        "rule_contract": False,
        "immutability": False,
        "determinism": False,
        "research_isolation": False,
    }

    try:
        expanded = ExpandedInstruction(_instruction(), 5)
        assert expanded.row_budget == 5
        _expect_raises(
            ValueError, lambda: ExpandedInstruction(_instruction(), 0)
        )
        checks["expanded_instruction"] = True

        diagnostic = CompilerDiagnostic(
            code="EXPANSION_CONTRACT_INFO",
            severity=DiagnosticSeverity.INFO,
            message="Expansion contract test.",
            phrase_index=2,
        )
        result = ExpansionResult(
            success=True,
            expanded_instructions=(expanded,),
            diagnostics=(diagnostic,),
            grammar_fingerprint="sha256:" + "1" * 64,
            compiler_version="COMPILER_V1",
            expansion_fingerprint="sha256:" + "2" * 64,
        )
        assert result.expanded_instructions == (expanded,)
        checks["expansion_result"] = True

        policy = AllocationPolicy(
            policy_name="DECLARED_STATIC_BUDGET",
            policy_version="1",
            description="Future allocation contract; no allocation behavior.",
        )
        assert policy.policy_version == "1"
        checks["allocation_contract"] = True

        rule = ExpansionRule(
            macro_type=PhraseType.ACCEPTED_BREAK,
            primitive_sequence=(
                PrimitiveType.APPROACH,
                PrimitiveType.ENTER,
                PrimitiveType.PENETRATE,
                PrimitiveType.WITHDRAW,
                PrimitiveType.HOLD_OUTSIDE,
            ),
            allocation_rule_version=policy.policy_version,
        )
        assert rule.recursive is False
        _expect_raises(
            ValueError,
            lambda: ExpansionRule(
                macro_type=PhraseType.ACCEPTED_BREAK,
                primitive_sequence=(PrimitiveType.APPROACH,),
                allocation_rule_version="1",
                recursive=True,
            ),
        )
        checks["rule_contract"] = True

        for value, attribute, replacement in (
            (expanded, "row_budget", 9),
            (result, "success", False),
            (policy, "policy_version", "2"),
            (rule, "recursive", True),
        ):
            _expect_raises(
                FrozenInstanceError,
                lambda value=value, attribute=attribute, replacement=replacement: setattr(
                    value, attribute, replacement
                ),
            )
        checks["immutability"] = True

        assert expanded == ExpandedInstruction(_instruction(), 5)
        assert result == ExpansionResult(
            success=True,
            expanded_instructions=(ExpandedInstruction(_instruction(), 5),),
            diagnostics=(diagnostic,),
            grammar_fingerprint="sha256:" + "1" * 64,
            compiler_version="COMPILER_V1",
            expansion_fingerprint="sha256:" + "2" * 64,
        )
        checks["determinism"] = True

        source = EXPANSION_MODULE.read_text(encoding="utf-8").lower()
        import_lines = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        assert not any(token in import_lines for token in FORBIDDEN_IMPORTS)
        assert not any(token in source for token in FORBIDDEN_CONTRACTS)
        assert "def expand" not in source
        assert "def allocate" not in source
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result}


def main() -> None:
    report = run()
    for field in (
        "expanded_instruction",
        "expansion_result",
        "allocation_contract",
        "rule_contract",
        "immutability",
        "determinism",
        "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

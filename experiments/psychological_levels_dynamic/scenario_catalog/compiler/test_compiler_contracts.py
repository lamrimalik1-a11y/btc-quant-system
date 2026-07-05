"""Validation for compiler contracts only."""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.psychological_levels_dynamic.scenario_catalog.compiler import (
    CompilationRequest,
    CompilationResult,
    CompilerDiagnostic,
    DiagnosticSeverity,
    GeometryContext,
    GeometryReference,
    MechanicalTimeline,
    PrimitiveInstruction,
    PrimitiveType,
    TimelineSegment,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.ast import (
    GRAMMAR_SCHEMA_VERSION,
    GrammarProgram,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    PathSmoothness,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.phrases import (
    penetrate,
)


def geometry(center: str = "60400") -> GeometryContext:
    center_price = Decimal(center)
    return GeometryContext(
        "BTCUSDT",
        "PSY_V1",
        (
            GeometryReference(
                "ZONE_" + center,
                center_price,
                center_price - 25,
                center_price + 25,
                Decimal(25),
            ),
        ),
    )


def program() -> GrammarProgram:
    return GrammarProgram(
        "CONTRACT_TEST",
        GRAMMAR_SCHEMA_VERSION,
        (penetrate(3, "ZONE_60400", Decimal("0.25")),),
        (),
        (),
        ("Contract only.",),
    )


def raises(kind: type[BaseException], fn) -> None:
    try:
        fn()
    except kind:
        return
    raise AssertionError(kind.__name__)


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        key: False
        for key in (
            "compiler_contracts",
            "geometry",
            "timeline",
            "diagnostics",
            "contracts",
            "immutability",
            "determinism",
            "research_isolation",
        )
    }
    try:
        g = geometry()
        g2 = geometry()
        g3 = geometry("60600")
        assert (
            g.geometry_fingerprint == g2.geometry_fingerprint != g3.geometry_fingerprint
        )
        checks["geometry"] = True

        p = PrimitiveInstruction(0, 0, PrimitiveType.PENETRATE, (), "ZONE_60400")
        s = TimelineSegment(
            0, 0, p.primitive_type, 0, 2, 3, p.target_zone, None, PathSmoothness.LINEAR
        )
        t = MechanicalTimeline((s,))
        checks["timeline"] = True

        d = CompilerDiagnostic(
            "TEST", DiagnosticSeverity.INFO, "Contract test.", 0, "depth"
        )
        assert (
            d.deterministic_key
            == CompilerDiagnostic(
                "TEST", DiagnosticSeverity.INFO, "Contract test.", 0, "depth"
            ).deterministic_key
        )
        checks["diagnostics"] = True

        q = CompilationRequest(program(), g, "V1")
        r = CompilationResult(
            False,
            (),
            t,
            (d,),
            q.program.program_fingerprint,
            g.geometry_fingerprint,
            "V1",
            None,
        )
        assert r.observations == ()
        checks["contracts"] = checks["compiler_contracts"] = True

        for value, name, new in (
            (g, "symbol", "X"),
            (p, "instruction_index", 2),
            (t, "segments", ()),
            (d, "message", "X"),
            (q, "compiler_version", "X"),
            (r, "success", True),
        ):
            raises(
                FrozenInstanceError,
                lambda value=value, name=name, new=new: setattr(value, name, new),
            )
        checks["immutability"] = True
        checks["determinism"] = True

        forbidden = (
            "scenario_runner",
            "scenario_contract",
            "scenario_registry",
            "scenario_primitives",
            "test_prediction_evolution",
            "core.",
            "engines.",
            "research.",
            "random",
            "research_",
            "dynamic_state",
            "generate_price",
            "priceobservation(",
        )
        for path in Path(__file__).parent.glob("*.py"):
            if path.name == Path(__file__).name:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for token in forbidden:
                assert token not in text, f"{path.name}:{token}"
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    return {
        **checks,
        "errors": errors,
        "result": "PASS" if all(checks.values()) and not errors else "FAIL",
    }


def main() -> None:
    report = run()
    for key in (
        "compiler_contracts",
        "geometry",
        "timeline",
        "diagnostics",
        "contracts",
        "immutability",
        "determinism",
        "research_isolation",
    ):
        print(f"{key} = {'PASS' if report[key] else 'FAIL'}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

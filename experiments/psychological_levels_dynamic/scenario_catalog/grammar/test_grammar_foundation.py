"""Structural validation for the Mechanical Scenario Language foundation."""

from __future__ import annotations

import sys
from pathlib import Path


GRAMMAR_DIR = Path(__file__).resolve().parent
sys.path = [
    entry
    for entry in sys.path
    if Path(entry or ".").resolve() != GRAMMAR_DIR
]

from dataclasses import FrozenInstanceError
from decimal import Decimal
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_catalog.grammar.ast import (
    GRAMMAR_SCHEMA_VERSION,
    GrammarParameter,
    GrammarPhrase,
    GrammarProgram,
    PhraseType,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    ACTIVE_DIMENSIONS,
    DEFERRED_DIMENSIONS,
    BehavioralDimension,
    DeferredDimension,
    Direction,
    PathSmoothness,
    ZoneSide,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.events import (
    EVENT_DEFINITIONS,
    MechanicalEvent,
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
    retest_boundary,
    transfer_to_zone,
    withdraw,
)
from experiments.psychological_levels_dynamic.scenario_catalog.grammar.dimensions import (
    RelativePosition,
)


FOUNDATION_MODULES = (
    GRAMMAR_DIR / "dimensions.py",
    GRAMMAR_DIR / "events.py",
    GRAMMAR_DIR / "ast.py",
    GRAMMAR_DIR / "phrases.py",
)
FORBIDDEN_IMPORT_TOKENS = (
    "scenario_primitives",
    "scenario_runner",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "core.",
    "engines.",
    "research.",
    "random",
)


def _program() -> GrammarProgram:
    phrases = (
        hold(5, RelativePosition.OUTSIDE_LOWER, "ZONE_A"),
        approach_zone(4, "ZONE_A", ZoneSide.LOWER, Decimal("0.5")),
        penetrate(6, "ZONE_A", Decimal("0.25")),
        withdraw(5, "ZONE_A", ZoneSide.LOWER, Decimal("0.75")),
        recovery_gap(8, "ZONE_A", Decimal("1.0")),
        break_candidate(3, "ZONE_A", ZoneSide.UPPER, Decimal("0.2")),
        accepted_break(
            7,
            "ZONE_A",
            ZoneSide.UPPER,
            Decimal("0.3"),
            5,
        ),
        retest_boundary(
            6,
            "ZONE_A",
            ZoneSide.UPPER,
            4,
            Decimal("0.1"),
        ),
        reclaim(5, "ZONE_A", ZoneSide.UPPER, Decimal("0.2"), 3),
        compress(
            9,
            "ZONE_A",
            (Decimal("0.4"), Decimal("0.2"), Decimal("0.1")),
        ),
        expand(
            9,
            "ZONE_A",
            (Decimal("0.1"), Decimal("0.3"), Decimal("0.6")),
        ),
        transfer_to_zone(10, "ZONE_A", "ZONE_B", Decimal("4")),
    )
    return GrammarProgram(
        program_id="GRAMMAR_FOUNDATION_REFERENCE_V1",
        schema_version=GRAMMAR_SCHEMA_VERSION,
        phrases=phrases,
        dimensions_declared=(
            BehavioralDimension.TARGET_ZONE,
            BehavioralDimension.PENETRATION_DEPTH,
            BehavioralDimension.INTER_VISIT_RECOVERY_GAP,
            BehavioralDimension.BOUNDARY_CLEARANCE,
        ),
        intended_events=(
            MechanicalEvent.BREAK_CANDIDATE,
            MechanicalEvent.ACCEPTED_BREAK,
            MechanicalEvent.RETEST,
            MechanicalEvent.RECLAIM,
        ),
        notes=("Research-only immutable grammar reference.",),
    )


def _expect_raises(exception: type[BaseException], callable_: Any) -> None:
    try:
        callable_()
    except exception:
        return
    raise AssertionError(f"expected {exception.__name__}")


def _research_isolation_errors() -> list[str]:
    errors: list[str] = []
    for path in FOUNDATION_MODULES:
        source = path.read_text(encoding="utf-8")
        lowered = source.lower()
        import_lines = "\n".join(
            line.strip()
            for line in lowered.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        for token in FORBIDDEN_IMPORT_TOKENS:
            if token.lower() in import_lines:
                errors.append(f"{path.name}:forbidden:{token}")
        if "priceobservation" in lowered:
            errors.append(f"{path.name}:price_output_contract")
        if "research_" in lowered:
            errors.append(f"{path.name}:research_label")
    return errors


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "grammar_foundation": False,
        "dimensions": False,
        "events": False,
        "ast": False,
        "phrases": False,
        "immutability": False,
        "determinism": False,
        "research_isolation": False,
    }
    fingerprints: dict[str, str] = {}

    try:
        program = _program()
        checks["grammar_foundation"] = True

        active_names = [item.dimension.value for item in ACTIVE_DIMENSIONS]
        deferred_names = [
            item.dimension.value for item in DEFERRED_DIMENSIONS
        ]
        assert len(active_names) == len(BehavioralDimension)
        assert len(active_names) == len(set(active_names))
        assert len(deferred_names) == len(DeferredDimension)
        assert len(deferred_names) == len(set(deferred_names))
        assert not set(active_names) & set(deferred_names)
        checks["dimensions"] = True

        event_names = [event.value for event in MechanicalEvent]
        assert len(event_names) == len(set(event_names))
        assert len(EVENT_DEFINITIONS) == len(MechanicalEvent)
        assert all(definition.authoring_only for definition in EVENT_DEFINITIONS)
        checks["events"] = True

        phrase_names = [phrase.value for phrase in PhraseType]
        assert len(phrase_names) == len(set(phrase_names))
        assert all(isinstance(phrase, GrammarPhrase) for phrase in program.phrases)
        assert all(
            isinstance(param, GrammarParameter)
            for phrase in program.phrases
            for param in phrase.params
        )
        checks["ast"] = True

        constructors = (
            hold(2, RelativePosition.CENTER, "ZONE_A"),
            ramp(
                2,
                Decimal("1"),
                Direction.UP,
                PathSmoothness.LINEAR,
            ),
            oscillate(4, Decimal("0.2"), 2, "ZONE_A"),
            approach_zone(2, "ZONE_A", ZoneSide.LOWER, Decimal("1")),
            enter_zone(2, "ZONE_A", ZoneSide.LOWER, Decimal("0.1")),
            penetrate(2, "ZONE_A", Decimal("0.2")),
            penetrate(2, "ZONE_A", Decimal("0.2"), ZoneSide.UPPER),
            withdraw(2, "ZONE_A", ZoneSide.LOWER, Decimal("1")),
            hold_outside(
                2, "ZONE_A", ZoneSide.UPPER, Decimal("0.1")
            ),
            recovery_gap(2, "ZONE_A", Decimal("1")),
            break_candidate(2, "ZONE_A", ZoneSide.UPPER, Decimal("0.1")),
            accepted_break(
                3, "ZONE_A", ZoneSide.UPPER, Decimal("0.1"), 2
            ),
            retest_boundary(
                3, "ZONE_A", ZoneSide.UPPER, 2, Decimal("0.1")
            ),
            reclaim(3, "ZONE_A", ZoneSide.UPPER, Decimal("0.1"), 2),
            compress(3, "ZONE_A", (Decimal("0.2"), Decimal("0.1"))),
            expand(3, "ZONE_A", (Decimal("0.1"), Decimal("0.2"))),
            transfer_to_zone(3, "ZONE_A", "ZONE_B", Decimal("4")),
        )
        legacy_penetrate = penetrate(2, "ZONE_A", Decimal("0.2"))
        sided_penetrate = penetrate(2, "ZONE_A", Decimal("0.2"), ZoneSide.UPPER)
        assert tuple(param.name for param in legacy_penetrate.params) == ("depth",)
        assert dict((param.name, param.value) for param in sided_penetrate.params)["side"] == ZoneSide.UPPER
        assert all(isinstance(item, GrammarPhrase) for item in constructors)
        assert not any(
            hasattr(item, attribute)
            for item in constructors
            for attribute in ("generate", "compile", "run")
        )
        checks["phrases"] = True

        _expect_raises(
            FrozenInstanceError,
            lambda: setattr(program, "program_id", "MUTATED"),
        )
        _expect_raises(
            TypeError,
            lambda: GrammarParameter("mutable", [1, 2]),
        )
        _expect_raises(
            TypeError,
            lambda: GrammarParameter("mutable", {"value": 1}),
        )
        _expect_raises(
            TypeError,
            lambda: GrammarPhrase(
                PhraseType.HOLD,
                [GrammarParameter("value", 1)],  # type: ignore[arg-type]
                1,
                None,
                "Mutable params are forbidden.",
            ),
        )
        checks["immutability"] = True

        identical = _program()
        changed = GrammarProgram(
            program_id=program.program_id,
            schema_version=program.schema_version,
            phrases=program.phrases
            + (hold(1, RelativePosition.CENTER, "ZONE_A"),),
            dimensions_declared=program.dimensions_declared,
            intended_events=program.intended_events,
            notes=program.notes,
        )
        assert program == identical
        assert program.program_fingerprint == identical.program_fingerprint
        assert program.program_fingerprint != changed.program_fingerprint
        fingerprints = {
            "reference": program.program_fingerprint,
            "changed": changed.program_fingerprint,
        }
        checks["determinism"] = True

        isolation_errors = _research_isolation_errors()
        if isolation_errors:
            errors.extend(isolation_errors)
        assert not isolation_errors
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {
        **checks,
        "fingerprints": fingerprints,
        "errors": errors,
        "result": result,
    }


def main() -> None:
    report = run()
    for field in (
        "grammar_foundation",
        "dimensions",
        "events",
        "ast",
        "phrases",
        "immutability",
        "determinism",
        "research_isolation",
    ):
        print(f"{field} = {'PASS' if report[field] else 'FAIL'}")
    print(f"fingerprints = {report['fingerprints']}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    print("COMPILER_PRESENT = FALSE")
    print("GENERATED_SCENARIOS_PRESENT = FALSE")
    print("EXECUTION_PRESENT = FALSE")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

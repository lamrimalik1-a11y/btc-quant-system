"""Structural validation for price-materialization contracts only."""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.psychological_levels_dynamic.scenario_contract import (
    PriceObservation,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.diagnostics import (
    CompilerDiagnostic,
    DiagnosticSeverity,
)
from experiments.psychological_levels_dynamic.scenario_catalog.compiler.price_materialization import (
    MATERIALIZATION_CONTRACT_VERSION,
    MaterializationResult,
    materialization_fingerprint,
    observation_checksum,
)


MODULE_PATH = Path(__file__).with_name("price_materialization.py")
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

# price_materialization.py now holds both these contracts and the V1
# materialization logic (Geometry Resolution precedent: one module, two
# checkpoints). "pathsmoothness"/"linear"/"interpolation"/
# "def materialize_prices" are legitimate logic-phase vocabulary now and
# are intentionally no longer banned here; the remaining tokens still mark
# real boundary violations.
FORBIDDEN_CONTRACTS = (
    "scenariospecification",
    "dynamic_state",
    "research_",
    "def materialize(",
    "def generate_price",
    "run_scenario",
)

DUMMY_GRAMMAR_FINGERPRINT = "sha256:" + "1" * 64
DUMMY_EXPANSION_FINGERPRINT = "sha256:" + "2" * 64
DUMMY_TIMELINE_FINGERPRINT = "sha256:" + "3" * 64
DUMMY_GEOMETRY_FINGERPRINT = "sha256:" + "4" * 64
DUMMY_RESOLUTION_FINGERPRINT = "sha256:" + "5" * 64
DUMMY_COMPILER_VERSION = "PRICE_MATERIALIZATION_CONTRACT_TEST_COMPILER_V1"


def _expect_raises(exception: type[BaseException], callable_: Any) -> None:
    try:
        callable_()
    except exception:
        return
    raise AssertionError(f"expected {exception.__name__}")


def _observations(price: str = "60400", row_index: int = 1) -> tuple[PriceObservation, ...]:
    return (PriceObservation(row_index=row_index, price=Decimal(price)),)


def _fatal() -> CompilerDiagnostic:
    return CompilerDiagnostic(
        code="MATERIALIZATION_CONTRACT_FATAL",
        severity=DiagnosticSeverity.FATAL,
        message="Materialization contract failure.",
    )


def _fingerprint(
    checksum: str | None,
    diagnostics: tuple[CompilerDiagnostic, ...] = (),
    geometry_fingerprint: str = DUMMY_GEOMETRY_FINGERPRINT,
) -> str:
    return materialization_fingerprint(
        observation_checksum_value=checksum,
        diagnostics=diagnostics,
        grammar_fingerprint=DUMMY_GRAMMAR_FINGERPRINT,
        expansion_fingerprint=DUMMY_EXPANSION_FINGERPRINT,
        timeline_fingerprint=DUMMY_TIMELINE_FINGERPRINT,
        geometry_fingerprint=geometry_fingerprint,
        resolution_fingerprint=DUMMY_RESOLUTION_FINGERPRINT,
        compiler_version=DUMMY_COMPILER_VERSION,
        materializer_version=MATERIALIZATION_CONTRACT_VERSION,
    )


def _success_result(observations: tuple[PriceObservation, ...] | None = None) -> MaterializationResult:
    values = _observations() if observations is None else observations
    checksum = observation_checksum(values)
    return MaterializationResult(
        success=True,
        observations=values,
        diagnostics=(),
        observation_checksum=checksum,
        materialization_fingerprint=_fingerprint(checksum),
        grammar_fingerprint=DUMMY_GRAMMAR_FINGERPRINT,
        expansion_fingerprint=DUMMY_EXPANSION_FINGERPRINT,
        timeline_fingerprint=DUMMY_TIMELINE_FINGERPRINT,
        geometry_fingerprint=DUMMY_GEOMETRY_FINGERPRINT,
        resolution_fingerprint=DUMMY_RESOLUTION_FINGERPRINT,
        compiler_version=DUMMY_COMPILER_VERSION,
        materializer_version=MATERIALIZATION_CONTRACT_VERSION,
    )


def _failure_result() -> MaterializationResult:
    diagnostics = (_fatal(),)
    return MaterializationResult(
        success=False,
        observations=(),
        diagnostics=diagnostics,
        observation_checksum=None,
        materialization_fingerprint=_fingerprint(None, diagnostics),
        grammar_fingerprint=DUMMY_GRAMMAR_FINGERPRINT,
        expansion_fingerprint=DUMMY_EXPANSION_FINGERPRINT,
        timeline_fingerprint=DUMMY_TIMELINE_FINGERPRINT,
        geometry_fingerprint=DUMMY_GEOMETRY_FINGERPRINT,
        resolution_fingerprint=DUMMY_RESOLUTION_FINGERPRINT,
        compiler_version=DUMMY_COMPILER_VERSION,
        materializer_version=MATERIALIZATION_CONTRACT_VERSION,
    )


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "materialization_contracts": False,
        "materialization_result": False,
        "observation_checksum": False,
        "materialization_fingerprint": False,
        "immutability": False,
        "determinism": False,
        "research_isolation": False,
    }

    try:
        success = _success_result()
        assert success.success is True
        assert success.observations == _observations()
        assert success.observation_checksum is not None
        failure = _failure_result()
        assert failure.success is False
        assert failure.observations == ()
        assert failure.observation_checksum is None
        _expect_raises(ValueError, lambda: _success_result(()))
        _expect_raises(
            ValueError,
            lambda: MaterializationResult(
                success=True,
                observations=_observations(),
                diagnostics=(),
                observation_checksum=None,
                materialization_fingerprint=_fingerprint(None),
                grammar_fingerprint=DUMMY_GRAMMAR_FINGERPRINT,
                expansion_fingerprint=DUMMY_EXPANSION_FINGERPRINT,
                timeline_fingerprint=DUMMY_TIMELINE_FINGERPRINT,
                geometry_fingerprint=DUMMY_GEOMETRY_FINGERPRINT,
                resolution_fingerprint=DUMMY_RESOLUTION_FINGERPRINT,
                compiler_version=DUMMY_COMPILER_VERSION,
                materializer_version=MATERIALIZATION_CONTRACT_VERSION,
            ),
        )
        _expect_raises(
            ValueError,
            lambda: MaterializationResult(
                success=False,
                observations=_observations(),
                diagnostics=(_fatal(),),
                observation_checksum=None,
                materialization_fingerprint=_fingerprint(None, (_fatal(),)),
                grammar_fingerprint=DUMMY_GRAMMAR_FINGERPRINT,
                expansion_fingerprint=DUMMY_EXPANSION_FINGERPRINT,
                timeline_fingerprint=DUMMY_TIMELINE_FINGERPRINT,
                geometry_fingerprint=DUMMY_GEOMETRY_FINGERPRINT,
                resolution_fingerprint=DUMMY_RESOLUTION_FINGERPRINT,
                compiler_version=DUMMY_COMPILER_VERSION,
                materializer_version=MATERIALIZATION_CONTRACT_VERSION,
            ),
        )
        _expect_raises(
            ValueError,
            lambda: MaterializationResult(
                success=False,
                observations=(),
                diagnostics=(),
                observation_checksum=None,
                materialization_fingerprint=_fingerprint(None),
                grammar_fingerprint=DUMMY_GRAMMAR_FINGERPRINT,
                expansion_fingerprint=DUMMY_EXPANSION_FINGERPRINT,
                timeline_fingerprint=DUMMY_TIMELINE_FINGERPRINT,
                geometry_fingerprint=DUMMY_GEOMETRY_FINGERPRINT,
                resolution_fingerprint=DUMMY_RESOLUTION_FINGERPRINT,
                compiler_version=DUMMY_COMPILER_VERSION,
                materializer_version=MATERIALIZATION_CONTRACT_VERSION,
            ),
        )
        # Regression: a failed materialization must not carry a checksum,
        # symmetric to the existing "must not carry observations" guard.
        stray_checksum = observation_checksum(_observations())
        _expect_raises(
            ValueError,
            lambda: MaterializationResult(
                success=False,
                observations=(),
                diagnostics=(_fatal(),),
                observation_checksum=stray_checksum,
                materialization_fingerprint=_fingerprint(stray_checksum, (_fatal(),)),
                grammar_fingerprint=DUMMY_GRAMMAR_FINGERPRINT,
                expansion_fingerprint=DUMMY_EXPANSION_FINGERPRINT,
                timeline_fingerprint=DUMMY_TIMELINE_FINGERPRINT,
                geometry_fingerprint=DUMMY_GEOMETRY_FINGERPRINT,
                resolution_fingerprint=DUMMY_RESOLUTION_FINGERPRINT,
                compiler_version=DUMMY_COMPILER_VERSION,
                materializer_version=MATERIALIZATION_CONTRACT_VERSION,
            ),
        )
        checks["materialization_result"] = True

        checksum = observation_checksum(_observations())
        assert checksum == observation_checksum(_observations())
        assert checksum != observation_checksum(_observations("60401"))
        assert checksum != observation_checksum(_observations("60400", row_index=2))
        checks["observation_checksum"] = True

        fingerprint = _fingerprint(checksum)
        assert fingerprint == _fingerprint(checksum)
        assert fingerprint != _fingerprint(
            checksum,
            geometry_fingerprint="sha256:" + "6" * 64,
        )
        checks["materialization_fingerprint"] = True

        assert PriceObservation.__dataclass_fields__.keys() == {"row_index", "price"}
        checks["materialization_contracts"] = True

        for value, attribute, replacement in (
            (success, "success", False),
            (failure, "diagnostics", ()),
            (_observations()[0], "price", Decimal("1")),
        ):
            _expect_raises(
                FrozenInstanceError,
                lambda value=value, attribute=attribute, replacement=replacement: setattr(
                    value,
                    attribute,
                    replacement,
                ),
            )
        checks["immutability"] = True

        assert _success_result() == success
        assert observation_checksum(
            (
                PriceObservation(1, Decimal("60400.0")),
                PriceObservation(2, Decimal("60401.00")),
            )
        ) == observation_checksum(
            (
                PriceObservation(1, Decimal("60400")),
                PriceObservation(2, Decimal("60401")),
            )
        )
        checks["determinism"] = True

        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        import_lines = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        )
        assert not any(token in import_lines for token in FORBIDDEN_IMPORTS)
        assert not any(token in source for token in FORBIDDEN_CONTRACTS)
        assert "def observation_checksum" in source
        assert "def materialization_fingerprint" in source
        checks["research_isolation"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result_status = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result_status}


def main() -> None:
    report = run()
    for field in (
        "materialization_contracts",
        "materialization_result",
        "observation_checksum",
        "materialization_fingerprint",
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

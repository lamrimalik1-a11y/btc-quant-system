"""Project 2 Chapter II Phase 1 scenario-foundation validation."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parent
if str(EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_DIR))

from scenario_contract import (
    PriceObservation,
    ScenarioProvider,
    ScenarioProviderMetadata,
    ScenarioSpecification,
)
from scenario_primitives import (
    bounded_range,
    linear_trend,
    step_pattern,
    triangular_wave,
)
from scenario_registry import ScenarioRegistry


class TriangularTestProvider:
    def metadata(self) -> ScenarioProviderMetadata:
        return ScenarioProviderMetadata(
            scenario_family="TRIANGULAR_TEST",
            provider_version="1",
            schema_version="1",
        )

    def validate_spec(self, spec: ScenarioSpecification) -> None:
        if spec.scenario_family != "TRIANGULAR_TEST":
            raise ValueError("wrong scenario family")
        if spec.schema_version != "1":
            raise ValueError("unsupported schema version")

    def generate(
        self, spec: ScenarioSpecification
    ) -> tuple[PriceObservation, ...]:
        prices = triangular_wave(
            spec.row_count,
            Decimal(str(spec.parameters["lower"])),
            Decimal(str(spec.parameters["upper"])),
            int(spec.parameters["half_period_rows"]),
        )
        return tuple(
            PriceObservation(row_index=index, price=price)
            for index, price in enumerate(prices, start=1)
        )


def _spec() -> ScenarioSpecification:
    return ScenarioSpecification(
        scenario_id="CH2_FOUNDATION_TRIANGLE",
        scenario_family="TRIANGULAR_TEST",
        schema_version="1",
        description="Foundation-only deterministic triangle",
        parameters={
            "lower": Decimal("100"),
            "upper": Decimal("120"),
            "half_period_rows": 2,
            "nested": {"immutable": True},
        },
        geometry_parameters={"spacing": Decimal("20")},
        row_count=8,
        start_price=Decimal("100"),
        expected_behavior_notes=("Deterministic foundation fixture",),
        validation_metadata={"chapter": 2, "phase": 1},
        seed_metadata="UNUSED_NO_PRNG",
    )


def _verify_immutable(spec: ScenarioSpecification) -> None:
    try:
        spec.row_count = 99
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("frozen specification accepted assignment")
    try:
        spec.parameters["new"] = "value"
    except TypeError:
        pass
    else:
        raise AssertionError("parameters mapping is mutable")
    try:
        spec.parameters["nested"]["immutable"] = False
    except TypeError:
        pass
    else:
        raise AssertionError("nested parameters mapping is mutable")



def _verify_fingerprint(spec: ScenarioSpecification) -> None:
    repeated = _spec()
    reordered = ScenarioSpecification(
        scenario_id=spec.scenario_id,
        scenario_family=spec.scenario_family,
        schema_version=spec.schema_version,
        description=spec.description,
        parameters={
            "nested": {"immutable": True},
            "half_period_rows": 2,
            "upper": Decimal("120.0"),
            "lower": Decimal("100.00"),
        },
        geometry_parameters={"spacing": Decimal("20.0")},
        row_count=spec.row_count,
        start_price=Decimal("100.0"),
        expected_behavior_notes=spec.expected_behavior_notes,
        validation_metadata={"phase": 1, "chapter": 2},
        seed_metadata=spec.seed_metadata,
    )
    changed = ScenarioSpecification(
        scenario_id=spec.scenario_id,
        scenario_family=spec.scenario_family,
        schema_version=spec.schema_version,
        description=spec.description,
        parameters={
            **dict(spec.parameters),
            "upper": Decimal("121"),
        },
        geometry_parameters=dict(spec.geometry_parameters),
        row_count=spec.row_count,
        start_price=spec.start_price,
        expected_behavior_notes=spec.expected_behavior_notes,
        validation_metadata=dict(spec.validation_metadata),
        seed_metadata=spec.seed_metadata,
    )
    assert spec.specification_fingerprint == repeated.specification_fingerprint
    assert spec.specification_fingerprint == reordered.specification_fingerprint
    assert spec.specification_fingerprint != changed.specification_fingerprint
    assert spec.specification_fingerprint.startswith("sha256:")

    for unsupported in (1.5, object(), {"mutable"}):
        try:
            ScenarioSpecification(
                scenario_id="INVALID",
                scenario_family="TRIANGULAR_TEST",
                schema_version="1",
                description="Invalid parameter fixture",
                parameters={"unsupported": unsupported},
                geometry_parameters={},
                row_count=1,
                start_price=Decimal("1"),
                expected_behavior_notes=(),
                validation_metadata={},
            )
        except TypeError:
            pass
        else:
            raise AssertionError("unsupported parameter type accepted")


def _verify_registry_self_contained() -> None:
    registry_path = EXPERIMENT_DIR / "scenario_registry.py"
    saved_path = list(sys.path)
    saved_contract = sys.modules.pop("scenario_contract", None)
    try:
        sys.path[:] = [
            item
            for item in sys.path
            if Path(item or ".").resolve() != EXPERIMENT_DIR
        ]
        module_spec = importlib.util.spec_from_file_location(
            "isolated_scenario_registry", registry_path
        )
        assert module_spec is not None and module_spec.loader is not None
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        assert hasattr(module, "ScenarioRegistry")
    finally:
        sys.path[:] = saved_path
        if saved_contract is not None:
            sys.modules["scenario_contract"] = saved_contract

def _verify_no_stage_imports() -> None:
    forbidden = (
        "dynamic_mechanics_test",
        "test_snapshot_dynamic_mechanics",
        "test_dynamic_state_transitions",
        "test_transition_graph",
        "test_trajectory_evolution",
        "test_prediction_evolution",
    )
    for module in (
        sys.modules["scenario_contract"],
        sys.modules["scenario_registry"],
        sys.modules["scenario_primitives"],
    ):
        source = inspect.getsource(module)
        import_lines = [
            line.strip()
            for line in source.splitlines()
            if line.lstrip().startswith(("from ", "import "))
        ]
        if any(name in line for name in forbidden for line in import_lines):
            raise AssertionError(f"forbidden Stage 1-6 import in {module}")


def run() -> dict[str, object]:
    errors: list[str] = []
    checks = {
        "scenario_contract": False,
        "registry": False,
        "primitives": False,
        "determinism": False,
        "price_only_output": False,
        "research_only": False,
    }
    try:
        spec = _spec()
        _verify_immutable(spec)
        _verify_fingerprint(spec)
        checks["scenario_contract"] = True

        provider = TriangularTestProvider()
        assert isinstance(provider, ScenarioProvider)
        registry = ScenarioRegistry()
        registry.register(provider)
        assert registry.list_families() == ("TRIANGULAR_TEST",)
        assert registry.get("TRIANGULAR_TEST") is provider
        try:
            registry.register(provider)
        except ValueError:
            pass
        else:
            raise AssertionError("duplicate provider registration accepted")
        _verify_registry_self_contained()
        checks["registry"] = True

        triangle = triangular_wave(
            8, Decimal("100"), Decimal("120"), 2
        )
        trend = linear_trend(8, Decimal("100"), Decimal("2"))
        ranged = bounded_range(8, Decimal("115"), Decimal("5"))
        stepped = step_pattern(
            8,
            Decimal("100"),
            ((3, Decimal("110")), (6, Decimal("90"))),
        )
        assert triangle == (
            Decimal("100"),
            Decimal("110"),
            Decimal("120"),
            Decimal("110"),
            Decimal("100"),
            Decimal("110"),
            Decimal("120"),
            Decimal("110"),
        )
        assert len({triangle, trend, ranged, stepped}) == 4
        checks["primitives"] = True

        first = tuple(registry.generate(spec))
        second = tuple(registry.generate(spec))
        assert first == second
        assert tuple(item.price for item in first) == triangle
        checks["determinism"] = True

        assert all(
            tuple(field.name for field in fields(item))
            == ("row_index", "price")
            for item in first
        )
        assert all(isinstance(item.price, Decimal) for item in first)
        checks["price_only_output"] = True

        _verify_no_stage_imports()
        metadata = provider.metadata()
        assert metadata.price_only and metadata.research_only
        checks["research_only"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result}


def main() -> None:
    report = run()
    for field in (
        "scenario_contract",
        "registry",
        "primitives",
        "determinism",
        "price_only_output",
        "research_only",
    ):
        value = "PASS" if report[field] else "FAIL"
        print(f"{field} = {value}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

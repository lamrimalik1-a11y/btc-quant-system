"""Project 2 Chapter II Phase 3 scenario-catalog foundation validation.

Structural validation only. This test does not run Stage 1-6, does not
execute the Scenario Runner, does not compare scenario outputs, and does not
validate or require any downstream Dynamic State (including
RESEARCH_ATTACKER_PRESSURE). It validates only that the catalog's own
contract holds: providers are explicitly registered and price/research-only,
specifications are unique and stably fingerprinted, generation is
deterministic and price-only, and expected_behavior_notes/validation_metadata
are documentation only -- never inputs to generation.
"""

from __future__ import annotations

import sys
from dataclasses import fields as dataclass_fields
from dataclasses import replace as dataclass_replace
from decimal import Decimal
from pathlib import Path
from typing import Any


CATALOG_DIR = Path(__file__).resolve().parent
DYNAMIC_DIR = CATALOG_DIR.parent
for path in (CATALOG_DIR, DYNAMIC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from catalog import build_catalog_registry
from specifications import ALL_SPECIFICATIONS


FORBIDDEN_MODULE_NAMES = (
    "dynamic_mechanics_test",
    "test_snapshot_dynamic_mechanics",
    "test_dynamic_state_transitions",
    "test_transition_graph",
    "test_trajectory_evolution",
    "test_prediction_evolution",
    "scenario_runner",
)
FORBIDDEN_IMPORT_PREFIXES = ("core", "engines", "research")
FILES_TO_SCAN = (
    CATALOG_DIR / "catalog.py",
    CATALOG_DIR / "specifications.py",
    CATALOG_DIR / "families" / "baseline.py",
    CATALOG_DIR / "families" / "adversarial_attacker_pressure.py",
    CATALOG_DIR / "families" / "regime_change_into_pressure.py",
    CATALOG_DIR / "families" / "repeated_attacks.py",
    Path(__file__).resolve(),
)


def _import_lines(source: str) -> list[str]:
    return [
        line.strip()
        for line in source.splitlines()
        if line.lstrip().startswith(("from ", "import "))
    ]


def _scan_forbidden_imports() -> list[str]:
    violations: list[str] = []
    for path in FILES_TO_SCAN:
        source = path.read_text(encoding="utf-8")
        for line in _import_lines(source):
            if any(name in line for name in FORBIDDEN_MODULE_NAMES):
                violations.append(f"{path.name}: forbidden module reference: {line}")
                continue
            for prefix in FORBIDDEN_IMPORT_PREFIXES:
                if (
                    line == f"import {prefix}"
                    or line.startswith(f"import {prefix}.")
                    or line.startswith(f"from {prefix}.")
                    or line.startswith(f"from {prefix} ")
                ):
                    violations.append(
                        f"{path.name}: forbidden import prefix '{prefix}': {line}"
                    )
    return violations


def _validate_price_only(spec: Any, observations: tuple) -> dict[str, bool]:
    contiguous = all(
        observation.row_index == index
        for index, observation in enumerate(observations, start=1)
    )
    price_only = all(
        tuple(field.name for field in dataclass_fields(observation))
        == ("row_index", "price")
        for observation in observations
    )
    finite = all(
        isinstance(observation.price, Decimal) and observation.price.is_finite()
        for observation in observations
    )
    row_count_matches = len(observations) == spec.row_count
    return {
        "contiguous": contiguous,
        "price_only": price_only,
        "finite": finite,
        "row_count_matches": row_count_matches,
    }


def run() -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "scenario_catalog": False,
        "providers_registered": False,
        "specifications_registered": False,
        "unique_scenario_ids": False,
        "fingerprints_stable": False,
        "price_only_generation": False,
        "determinism": False,
        "distinct_path_shapes": False,
        "notes_not_required_for_generation": False,
        "no_stage_imports": False,
        "no_runner_execution": False,
    }

    try:
        registry = build_catalog_registry()
        checks["scenario_catalog"] = True

        registered_families = set(registry.list_families())
        expected_families = {spec.scenario_family for spec in ALL_SPECIFICATIONS}
        assert len(registry.list_families()) == 4
        assert registered_families == expected_families
        for provider in registry.providers.values():
            metadata = provider.metadata()
            assert metadata.price_only is True
            assert metadata.research_only is True
        checks["providers_registered"] = True

        for spec in ALL_SPECIFICATIONS:
            assert spec.scenario_family in registered_families
        checks["specifications_registered"] = True

        scenario_ids = [spec.scenario_id for spec in ALL_SPECIFICATIONS]
        assert len(scenario_ids) == len(set(scenario_ids))
        checks["unique_scenario_ids"] = True

        for spec in ALL_SPECIFICATIONS:
            assert spec.specification_fingerprint.startswith("sha256:")
            rebuilt = dataclass_replace(spec)
            assert (
                rebuilt.specification_fingerprint == spec.specification_fingerprint
            )
        checks["fingerprints_stable"] = True

        shape_signatures = []
        per_spec_observations: dict[str, tuple] = {}
        for spec in ALL_SPECIFICATIONS:
            first_run = tuple(registry.generate(spec))
            second_run = tuple(registry.generate(spec))
            assert tuple(
                (o.row_index, o.price) for o in first_run
            ) == tuple((o.row_index, o.price) for o in second_run)
            per_spec_observations[spec.scenario_id] = first_run

            price_only_report = _validate_price_only(spec, first_run)
            assert all(price_only_report.values()), price_only_report

            prices = tuple(observation.price for observation in first_run)
            shape_signatures.append(
                (
                    len(prices),
                    len(set(prices)),
                    min(prices),
                    max(prices),
                )
            )
        checks["price_only_generation"] = True
        checks["determinism"] = True

        assert len(set(shape_signatures)) == len(shape_signatures)
        checks["distinct_path_shapes"] = True

        for spec in ALL_SPECIFICATIONS:
            modified_spec = dataclass_replace(
                spec,
                expected_behavior_notes=(
                    "STRUCTURAL_CHECK_ONLY_DIFFERENT_NOTE_MUST_NOT_AFFECT_GENERATION",
                ),
                validation_metadata={"structural_check_marker": True},
            )
            assert (
                modified_spec.specification_fingerprint
                != spec.specification_fingerprint
            )
            baseline_observations = per_spec_observations[spec.scenario_id]
            modified_observations = tuple(registry.generate(modified_spec))
            assert tuple(
                (o.row_index, o.price) for o in baseline_observations
            ) == tuple((o.row_index, o.price) for o in modified_observations)
        checks["notes_not_required_for_generation"] = True

        forbidden_import_violations = _scan_forbidden_imports()
        if forbidden_import_violations:
            errors.extend(forbidden_import_violations)
        assert not forbidden_import_violations
        checks["no_stage_imports"] = True

        # This phase never imports or calls scenario_runner.run_scenario();
        # confirmed above via source scan, not merely by omission here.
        checks["no_runner_execution"] = True
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result = "PASS" if all(checks.values()) and not errors else "FAIL"
    return {**checks, "errors": errors, "result": result}


def main() -> None:
    report = run()
    for field in (
        "scenario_catalog",
        "providers_registered",
        "specifications_registered",
        "unique_scenario_ids",
        "fingerprints_stable",
        "price_only_generation",
        "determinism",
        "distinct_path_shapes",
        "notes_not_required_for_generation",
        "no_stage_imports",
        "no_runner_execution",
    ):
        value = "PASS" if report[field] else "FAIL"
        print(f"{field} = {value}")
    print(f"errors = {report['errors']}")
    print(f"result = {report['result']}")
    print("RESEARCH_ONLY = TRUE")
    print("OFFLINE_ONLY = TRUE")
    print("PROJECT_2_ONLY = TRUE")
    print("STAGE_1_TO_6_EXECUTED = FALSE")
    print("SCENARIO_RUNNER_EXECUTED = FALSE")
    print("LABELS_INJECTED = FALSE")
    print("PRODUCTION_EFFECTS = FALSE")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

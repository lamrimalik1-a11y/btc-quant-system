"""Scenario Catalog family: regime change into pressure.

Concatenates a quiet, mildly-oscillating regime (repeated shallow in/out
touches of one zone, via the existing bounded_range() primitive) with the
same shallow-probe-then-deep-penetration shape used by the
adversarial_attacker_pressure family (via step_pattern()), targeting the
same zone. This preserves continuous per-zone trajectory history so later
Stage 6 per-zone hypothesis evaluation remains mechanically meaningful.

The purpose is descriptive, not predictive: a later phase may observe
whether a walk-forward hypothesis formed from the quiet-regime prefix is
challenged once the corpus shifts into the pressure regime -- this is
currently the only way to exercise a real (non-synthetic) invalidation in
Stage 6, since every corpus tried so far has produced zero invalidations.
This provider does not inject, require, or validate any such outcome; it
only constructs the price-only regime shift. Uses only the existing,
unchanged bounded_range() and step_pattern() primitives.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path


DYNAMIC_DIR = Path(__file__).resolve().parents[2]
if str(DYNAMIC_DIR) not in sys.path:
    sys.path.insert(0, str(DYNAMIC_DIR))

from scenario_contract import (
    PriceObservation,
    ScenarioProviderMetadata,
    ScenarioSpecification,
)
from scenario_primitives import bounded_range, step_pattern


FAMILY_NAME = "REGIME_CHANGE_INTO_PRESSURE"


class RegimeQuietToPressureProvider:
    def metadata(self) -> ScenarioProviderMetadata:
        return ScenarioProviderMetadata(
            scenario_family=FAMILY_NAME,
            provider_version="1",
            schema_version="1",
        )

    def validate_spec(self, spec: ScenarioSpecification) -> None:
        if spec.scenario_family != FAMILY_NAME:
            raise ValueError("wrong scenario family")
        if spec.schema_version != "1":
            raise ValueError("unsupported schema version")
        if int(spec.parameters["quiet_row_count"]) >= spec.row_count:
            raise ValueError("quiet_row_count must be less than row_count")

    def generate(
        self, spec: ScenarioSpecification
    ) -> tuple[PriceObservation, ...]:
        quiet_row_count = int(spec.parameters["quiet_row_count"])
        pressure_row_count = spec.row_count - quiet_row_count

        quiet_prices = bounded_range(
            quiet_row_count,
            Decimal(str(spec.parameters["quiet_center"])),
            Decimal(str(spec.parameters["quiet_amplitude"])),
        )
        pressure_prices = step_pattern(
            pressure_row_count,
            Decimal(str(spec.parameters["pressure_baseline_price"])),
            tuple(
                (int(row), Decimal(str(price)))
                for row, price in spec.parameters["pressure_changes"]
            ),
        )
        prices = quiet_prices + pressure_prices
        return tuple(
            PriceObservation(row_index=index, price=price)
            for index, price in enumerate(prices, start=1)
        )

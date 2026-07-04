"""Scenario Catalog family: baseline reference control.

Preserves the exact Chapter I triangular price shape as a catalog scenario,
so every later family can be compared against the same reference corpus
Stage 1-6 have already been independently verified against. Uses only the
existing, unchanged triangular_wave() primitive -- no new mechanics.
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
from scenario_primitives import triangular_wave


FAMILY_NAME = "BASELINE"


class BaselineTriangularProvider:
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

"""Scenario Catalog family: repeated attacks with partial recovery.

Mechanism-derived: rather than a single dramatically deeper visit
(adversarial_attacker_pressure's route), this family constructs several
equal-depth penetrations into the same zone separated by short withdrawal
gaps -- short enough that HEALTH_RECOVERY_PER_ROW cannot fully restore
health between touches. This is a distinct route to a shrinking SDR
denominator (health) across a sequence, deliberately kept separate from the
numerator-spiking route so the two mechanisms are not conflated in any
later comparison. Uses only the existing, unchanged step_pattern()
primitive.
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
from scenario_primitives import step_pattern


FAMILY_NAME = "REPEATED_ATTACKS"


class RepeatedAttacksPartialRecoveryProvider:
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
        prices = step_pattern(
            spec.row_count,
            Decimal(str(spec.parameters["baseline_price"])),
            tuple(
                (int(row), Decimal(str(price)))
                for row, price in spec.parameters["changes"]
            ),
        )
        return tuple(
            PriceObservation(row_index=index, price=price)
            for index, price in enumerate(prices, start=1)
        )

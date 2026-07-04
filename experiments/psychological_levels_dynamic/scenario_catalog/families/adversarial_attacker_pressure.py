"""Scenario Catalog family: adversarial attacker pressure.

Mechanism-derived, not vocabulary-derived. Stage 1's RESEARCH_ATTACKER_PRESSURE
label requires, at a completed-visit level:

    d1_health < 0  AND  |delta_omega| / health > SDR_LABEL_THRESHOLD (0.5)

omega_at_visit is the penetration accumulated during one visit and resets
between visits, so a visit dramatically DEEPER than its immediate
predecessor produces a large delta_omega relative to health -- unlike a
periodic wave, where consecutive visits to the same zone tend to have
similar depth (which is why this state never occurs in the Chapter I
baseline corpus).

This family constructs exactly that precondition in price-only terms: a
shallow, brief probe into a zone, full withdrawal (allowing a completed
visit and partial recovery), then a much deeper, longer sustained
penetration into the same zone. Whether this actually crosses the SDR
threshold is an empirical question left to a later phase to observe -- this
provider does not require, inject, or validate RESEARCH_ATTACKER_PRESSURE;
it only constructs the price-only mechanical precondition the existing,
unmodified formula depends on. Uses only the existing, unchanged
step_pattern() primitive.
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


FAMILY_NAME = "ADVERSARIAL_ATTACKER_PRESSURE"


class AdversarialEscalatingPenetrationProvider:
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

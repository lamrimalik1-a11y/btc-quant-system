"""Scenario Catalog registry wiring -- Phase 3 foundation.

Builds one ScenarioRegistry containing exactly the four Phase 3 families.
Explicit registration only -- no directory scanning, no reflection, no
plugin loading, no dynamic imports. This module does not run the Scenario
Runner and does not import anything from Stage 1-6, Project 1, or
production code.
"""

from __future__ import annotations

import sys
from pathlib import Path


CATALOG_DIR = Path(__file__).resolve().parent
DYNAMIC_DIR = CATALOG_DIR.parent
for path in (CATALOG_DIR, DYNAMIC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from scenario_registry import ScenarioRegistry

from families.baseline import BaselineTriangularProvider
from families.adversarial_attacker_pressure import (
    AdversarialEscalatingPenetrationProvider,
)
from families.regime_change_into_pressure import (
    RegimeQuietToPressureProvider,
)
from families.repeated_attacks import RepeatedAttacksPartialRecoveryProvider


def build_catalog_registry() -> ScenarioRegistry:
    registry = ScenarioRegistry()
    registry.register(BaselineTriangularProvider())
    registry.register(AdversarialEscalatingPenetrationProvider())
    registry.register(RegimeQuietToPressureProvider())
    registry.register(RepeatedAttacksPartialRecoveryProvider())
    return registry

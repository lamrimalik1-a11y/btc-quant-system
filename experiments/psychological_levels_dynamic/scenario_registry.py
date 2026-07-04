"""Explicit provider registry for the Project 2 scenario laboratory."""

from __future__ import annotations

import sys
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


EXPERIMENT_DIR = Path(__file__).resolve().parent
if str(EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_DIR))

from scenario_contract import ScenarioProvider, ScenarioSpecification


class ScenarioRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ScenarioProvider] = {}

    def register(self, provider: ScenarioProvider) -> None:
        if not isinstance(provider, ScenarioProvider):
            raise TypeError("provider does not satisfy ScenarioProvider")
        metadata = provider.metadata()
        family = str(metadata.scenario_family).strip()
        if not family:
            raise ValueError("scenario_family must not be empty")
        if family in self._providers:
            raise ValueError(f"scenario family already registered: {family}")
        # Intentional V1 boundary; relax only through schema/version review.
        if not metadata.price_only or not metadata.research_only:
            raise ValueError("providers must be price-only and research-only")
        self._providers[family] = provider

    def get(self, scenario_family: str) -> ScenarioProvider:
        try:
            return self._providers[scenario_family]
        except KeyError as exc:
            raise KeyError(
                f"scenario family is not registered: {scenario_family}"
            ) from exc

    def validate(self, spec: ScenarioSpecification) -> None:
        self.get(spec.scenario_family).validate_spec(spec)

    def generate(self, spec: ScenarioSpecification):
        provider = self.get(spec.scenario_family)
        provider.validate_spec(spec)
        return provider.generate(spec)

    def list_families(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))

    @property
    def providers(self) -> Mapping[str, ScenarioProvider]:
        return MappingProxyType(dict(self._providers))

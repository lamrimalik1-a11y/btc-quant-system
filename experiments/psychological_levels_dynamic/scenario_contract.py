"""Research-only contracts for deterministic synthetic price scenarios."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable


def _freeze(value: Any, path: str = "value") -> Any:
    if value is None or isinstance(value, (bool, int, str, Decimal)):
        return value
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError(f"{path} mapping keys must be strings")
        return MappingProxyType(
            {
                key: _freeze(item, f"{path}.{key}")
                for key, item in value.items()
            }
        )
    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze(item, f"{path}[{index}]")
            for index, item in enumerate(value)
        )
    raise TypeError(
        f"{path} contains unsupported non-canonical type: "
        f"{type(value).__name__}"
    )


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        normalized = value.normalize()
        text = "0" if normalized == 0 else format(normalized, "f")
        return {"type": "decimal", "value": text}
    if isinstance(value, Mapping):
        return {
            key: _canonical_value(value[key])
            for key in sorted(value)
        }
    if isinstance(value, tuple):
        return [_canonical_value(item) for item in value]
    return value


def _fingerprint(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        _canonical_value(payload),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


@dataclass(frozen=True)
class ScenarioSpecification:
    scenario_id: str
    scenario_family: str
    schema_version: str
    description: str
    parameters: Mapping[str, Any]
    geometry_parameters: Mapping[str, Any]
    row_count: int
    start_price: Decimal
    expected_behavior_notes: tuple[str, ...]
    validation_metadata: Mapping[str, Any]
    seed_metadata: str | None = None
    specification_fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        for field_name in (
            "scenario_id",
            "scenario_family",
            "schema_version",
            "description",
        ):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} must not be empty")
        if self.row_count <= 0:
            raise ValueError("row_count must be positive")
        if not isinstance(self.start_price, Decimal):
            raise TypeError("start_price must be Decimal")
        if not self.start_price.is_finite():
            raise ValueError("start_price must be finite")

        object.__setattr__(
            self, "parameters", _freeze(self.parameters, "parameters")
        )
        object.__setattr__(
            self,
            "geometry_parameters",
            _freeze(self.geometry_parameters, "geometry_parameters"),
        )
        object.__setattr__(
            self,
            "expected_behavior_notes",
            tuple(str(note) for note in self.expected_behavior_notes),
        )
        object.__setattr__(
            self,
            "validation_metadata",
            _freeze(self.validation_metadata, "validation_metadata"),
        )
        object.__setattr__(
            self,
            "specification_fingerprint",
            _fingerprint(
                {
                    "scenario_id": self.scenario_id,
                    "scenario_family": self.scenario_family,
                    "schema_version": self.schema_version,
                    "description": self.description,
                    "parameters": self.parameters,
                    "geometry_parameters": self.geometry_parameters,
                    "row_count": self.row_count,
                    "start_price": self.start_price,
                    "expected_behavior_notes": self.expected_behavior_notes,
                    "validation_metadata": self.validation_metadata,
                    "seed_metadata": self.seed_metadata,
                }
            ),
        )


@dataclass(frozen=True)
class PriceObservation:
    row_index: int
    price: Decimal

    def __post_init__(self) -> None:
        if self.row_index < 1:
            raise ValueError("row_index must start at 1")
        if not isinstance(self.price, Decimal):
            raise TypeError("price must be Decimal")
        if not self.price.is_finite():
            raise ValueError("price must be finite")


@dataclass(frozen=True)
class ScenarioProviderMetadata:
    scenario_family: str
    provider_version: str
    schema_version: str
    price_only: bool = True
    research_only: bool = True


@runtime_checkable
class ScenarioProvider(Protocol):
    def metadata(self) -> ScenarioProviderMetadata:
        ...

    def validate_spec(self, spec: ScenarioSpecification) -> None:
        ...

    def generate(
        self, spec: ScenarioSpecification
    ) -> Sequence[PriceObservation]:
        ...

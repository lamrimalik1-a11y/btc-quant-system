"""Price-materialization contracts and deterministic materialization logic.

The materializer consumes only GeometryResolutionResult and emits immutable
PriceObservation rows. It owns STEP/LINEAR row generation, checksums,
materialization diagnostics, and rollback. It does not own grammar, expansion,
scheduling, geometry resolution, runner execution, catalog behavior, or research
analysis.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from experiments.psychological_levels_dynamic.scenario_contract import (
    PriceObservation,
)

from ..grammar.dimensions import PathSmoothness
from .diagnostics import CompilerDiagnostic, DiagnosticSeverity
from .geometry_resolution import GeometryResolutionResult, ResolvedCoordinate


MATERIALIZATION_CONTRACT_VERSION = "MATERIALIZATION_CONTRACTS_V1"
PRICE_MATERIALIZER_VERSION = "PRICE_MATERIALIZER_LOGIC_V1"


def _decimal_text(value: Decimal) -> str:
    normalized = value.normalize()
    return "0" if normalized == 0 else format(normalized, "f")


def _canonical(value: Any) -> Any:
    if isinstance(value, Decimal):
        return {"type": "decimal", "value": _decimal_text(value)}
    if isinstance(value, Enum):
        return {"type": type(value).__name__, "value": value.value}
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    if isinstance(value, PriceObservation):
        return {
            "row_index": value.row_index,
            "price": _canonical(value.price),
        }
    if isinstance(value, CompilerDiagnostic):
        return {
            "code": value.code,
            "severity": _canonical(value.severity),
            "message": value.message,
            "phrase_index": value.phrase_index,
            "parameter_name": value.parameter_name,
        }
    raise TypeError(f"unsupported canonical type: {type(value).__name__}")


def observation_checksum(
    observations: tuple[PriceObservation, ...],
) -> str:
    """Hash only the generated price path: row_index and price."""

    if not isinstance(observations, tuple) or not all(
        isinstance(value, PriceObservation) for value in observations
    ):
        raise TypeError("observations must be an immutable PriceObservation tuple")
    canonical_json = json.dumps(
        _canonical(observations),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return "sha256:" + hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def materialization_fingerprint(
    *,
    observation_checksum_value: str | None,
    diagnostics: tuple[CompilerDiagnostic, ...],
    grammar_fingerprint: str,
    expansion_fingerprint: str,
    timeline_fingerprint: str,
    geometry_fingerprint: str,
    resolution_fingerprint: str,
    compiler_version: str,
    materializer_version: str,
) -> str:
    """Hash materialization provenance and diagnostics, never timestamps."""

    if not isinstance(diagnostics, tuple) or not all(
        isinstance(value, CompilerDiagnostic) for value in diagnostics
    ):
        raise TypeError("diagnostics must be an immutable CompilerDiagnostic tuple")
    payload = {
        "observation_checksum": observation_checksum_value,
        "diagnostics": _canonical(
            tuple(sorted(diagnostics, key=lambda item: item.deterministic_key))
        ),
        "grammar_fingerprint": grammar_fingerprint,
        "expansion_fingerprint": expansion_fingerprint,
        "timeline_fingerprint": timeline_fingerprint,
        "geometry_fingerprint": geometry_fingerprint,
        "resolution_fingerprint": resolution_fingerprint,
        "compiler_version": compiler_version,
        "materializer_version": materializer_version,
    }
    canonical_json = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return "sha256:" + hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MaterializationResult:
    success: bool
    observations: tuple[PriceObservation, ...]
    diagnostics: tuple[CompilerDiagnostic, ...]
    observation_checksum: str | None
    materialization_fingerprint: str
    grammar_fingerprint: str
    expansion_fingerprint: str
    timeline_fingerprint: str
    geometry_fingerprint: str
    resolution_fingerprint: str
    compiler_version: str
    materializer_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")
        if not isinstance(self.observations, tuple) or not all(
            isinstance(value, PriceObservation) for value in self.observations
        ):
            raise TypeError("observations must be an immutable PriceObservation tuple")
        if not isinstance(self.diagnostics, tuple) or not all(
            isinstance(value, CompilerDiagnostic) for value in self.diagnostics
        ):
            raise TypeError("diagnostics must be an immutable CompilerDiagnostic tuple")
        if self.success:
            if not self.observations:
                raise ValueError("successful materialization requires observations")
            if self.observation_checksum is None:
                raise ValueError("successful materialization requires observation_checksum")
        else:
            if self.observations:
                raise ValueError("failed materialization must not carry observations")
            if self.observation_checksum is not None:
                raise ValueError(
                    "failed materialization must not carry an observation_checksum"
                )
            if not any(
                value.severity == DiagnosticSeverity.FATAL
                for value in self.diagnostics
            ):
                raise ValueError("failed materialization requires a FATAL diagnostic")
        for field_name in (
            "materialization_fingerprint",
            "grammar_fingerprint",
            "expansion_fingerprint",
            "timeline_fingerprint",
            "geometry_fingerprint",
            "resolution_fingerprint",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.startswith("sha256:"):
                raise ValueError(f"{field_name} must be SHA-256")
        if self.observation_checksum is not None and not self.observation_checksum.startswith(
            "sha256:"
        ):
            raise ValueError("observation_checksum must be SHA-256 or None")
        if not self.compiler_version.strip():
            raise ValueError("compiler_version must not be empty")
        if not self.materializer_version.strip():
            raise ValueError("materializer_version must not be empty")


def _fatal(
    code: str,
    message: str,
    phrase_index: int | None = None,
    parameter_name: str | None = None,
) -> CompilerDiagnostic:
    return CompilerDiagnostic(
        code=code,
        severity=DiagnosticSeverity.FATAL,
        message=message,
        phrase_index=phrase_index,
        parameter_name=parameter_name,
    )


def _result(
    *,
    geometry_result: GeometryResolutionResult,
    observations: tuple[PriceObservation, ...],
    diagnostics: tuple[CompilerDiagnostic, ...],
    materializer_version: str,
) -> MaterializationResult:
    sorted_diagnostics = tuple(sorted(diagnostics, key=lambda item: item.deterministic_key))
    success = not any(
        diagnostic.severity == DiagnosticSeverity.FATAL
        for diagnostic in sorted_diagnostics
    )
    checksum = observation_checksum(observations) if success else None
    fingerprint = materialization_fingerprint(
        observation_checksum_value=checksum,
        diagnostics=sorted_diagnostics,
        grammar_fingerprint=geometry_result.grammar_fingerprint,
        expansion_fingerprint=geometry_result.expansion_fingerprint,
        timeline_fingerprint=geometry_result.timeline_fingerprint,
        geometry_fingerprint=geometry_result.geometry_fingerprint,
        resolution_fingerprint=geometry_result.resolution_fingerprint,
        compiler_version=geometry_result.compiler_version,
        materializer_version=materializer_version,
    )
    return MaterializationResult(
        success=success,
        observations=observations if success else (),
        diagnostics=sorted_diagnostics,
        observation_checksum=checksum,
        materialization_fingerprint=fingerprint,
        grammar_fingerprint=geometry_result.grammar_fingerprint,
        expansion_fingerprint=geometry_result.expansion_fingerprint,
        timeline_fingerprint=geometry_result.timeline_fingerprint,
        geometry_fingerprint=geometry_result.geometry_fingerprint,
        resolution_fingerprint=geometry_result.resolution_fingerprint,
        compiler_version=geometry_result.compiler_version,
        materializer_version=materializer_version,
    )


def _valid_price(coordinate: ResolvedCoordinate | None) -> Decimal | None:
    if coordinate is None:
        return None
    price = coordinate.absolute_price
    if not isinstance(price, Decimal) or not price.is_finite():
        return None
    return price


def _step_prices(end_price: Decimal, row_count: int) -> tuple[Decimal, ...]:
    return tuple(end_price for _ in range(row_count))


def _linear_prices(start_price: Decimal, end_price: Decimal, row_count: int) -> tuple[Decimal, ...]:
    if row_count == 1:
        return (end_price,)
    denominator = Decimal(row_count - 1)
    return tuple(
        start_price + (end_price - start_price) * Decimal(offset) / denominator
        for offset in range(row_count)
    )


def materialize_prices(
    geometry_result: GeometryResolutionResult,
    materializer_version: str = PRICE_MATERIALIZER_VERSION,
) -> MaterializationResult:
    """Generate deterministic PriceObservation rows from resolved geometry."""

    if not isinstance(geometry_result, GeometryResolutionResult):
        raise TypeError("geometry_result must be GeometryResolutionResult")
    if not materializer_version.strip():
        raise ValueError("materializer_version must not be empty")

    diagnostics: list[CompilerDiagnostic] = []
    observations: list[PriceObservation] = []
    if not geometry_result.success:
        diagnostics.extend(geometry_result.diagnostics)
        diagnostics.append(
            _fatal(
                "UPSTREAM_GEOMETRY_RESOLUTION_FAILED",
                "geometry_result.success is False",
            )
        )
        return _result(
            geometry_result=geometry_result,
            observations=(),
            diagnostics=tuple(diagnostics),
            materializer_version=materializer_version,
        )
    if geometry_result.resolved_timeline is None:
        diagnostics.append(
            _fatal(
                "MISSING_RESOLVED_TIMELINE",
                "successful geometry resolution did not provide a resolved timeline",
            )
        )
        return _result(
            geometry_result=geometry_result,
            observations=(),
            diagnostics=tuple(diagnostics),
            materializer_version=materializer_version,
        )

    for resolved_segment in geometry_result.resolved_timeline.segments:
        segment = resolved_segment.timeline_segment
        phrase_index = segment.source_phrase_index
        if segment.row_count <= 0:
            diagnostics.append(
                _fatal(
                    "INVALID_ROW_COUNT",
                    "timeline segment row_count must be positive",
                    phrase_index,
                    "row_count",
                )
            )
            continue
        start_price = _valid_price(resolved_segment.start_coordinate_intent)
        end_price = _valid_price(resolved_segment.end_coordinate_intent)
        if start_price is None or end_price is None:
            diagnostics.append(
                _fatal(
                    "MISSING_OR_INVALID_COORDINATE",
                    "resolved segment requires finite Decimal start and end coordinates",
                    phrase_index,
                    "coordinate",
                )
            )
            continue
        if segment.interpolation_policy == PathSmoothness.STEP:
            prices = _step_prices(end_price, segment.row_count)
        elif segment.interpolation_policy == PathSmoothness.LINEAR:
            prices = _linear_prices(start_price, end_price, segment.row_count)
        else:
            diagnostics.append(
                _fatal(
                    "UNSUPPORTED_INTERPOLATION_POLICY",
                    "only STEP and LINEAR materialization are supported",
                    phrase_index,
                    "interpolation_policy",
                )
            )
            continue
        observations.extend(
            PriceObservation(row_index=segment.row_start + offset, price=price)
            for offset, price in enumerate(prices)
        )

    return _result(
        geometry_result=geometry_result,
        observations=tuple(observations),
        diagnostics=tuple(diagnostics),
        materializer_version=materializer_version,
    )
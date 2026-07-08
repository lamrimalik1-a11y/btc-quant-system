"""Immutable price-materialization contracts; no materialization behavior.

This module defines only the future Price Materializer boundary. It stores
immutable result/provenance contracts and deterministic hashes, with no row
generation or downstream orchestration.
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

from .diagnostics import CompilerDiagnostic, DiagnosticSeverity


MATERIALIZATION_CONTRACT_VERSION = "MATERIALIZATION_CONTRACTS_V1"


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

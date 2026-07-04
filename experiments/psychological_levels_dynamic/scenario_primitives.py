"""Pure Decimal-based mathematical primitives for synthetic price paths."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable


def _validate_row_count(row_count: int) -> None:
    if row_count <= 0:
        raise ValueError("row_count must be positive")


def linear_trend(
    row_count: int,
    start_price: Decimal,
    step: Decimal,
) -> tuple[Decimal, ...]:
    _validate_row_count(row_count)
    return tuple(
        start_price + step * index for index in range(row_count)
    )


def triangular_wave(
    row_count: int,
    lower: Decimal,
    upper: Decimal,
    half_period_rows: int,
) -> tuple[Decimal, ...]:
    _validate_row_count(row_count)
    if upper <= lower:
        raise ValueError("upper must be greater than lower")
    if half_period_rows <= 0:
        raise ValueError("half_period_rows must be positive")

    span = upper - lower
    full_period = half_period_rows * 2
    values: list[Decimal] = []
    for index in range(row_count):
        phase = index % full_period
        distance = (
            phase if phase <= half_period_rows else full_period - phase
        )
        values.append(
            lower
            + span * Decimal(distance) / Decimal(half_period_rows)
        )
    return tuple(values)


def bounded_range(
    row_count: int,
    center: Decimal,
    amplitude: Decimal,
) -> tuple[Decimal, ...]:
    _validate_row_count(row_count)
    if amplitude <= 0:
        raise ValueError("amplitude must be positive")
    offsets = (
        -amplitude,
        Decimal("0"),
        amplitude,
        Decimal("0"),
    )
    return tuple(center + offsets[index % 4] for index in range(row_count))


def step_pattern(
    row_count: int,
    initial_price: Decimal,
    changes: Iterable[tuple[int, Decimal]],
) -> tuple[Decimal, ...]:
    _validate_row_count(row_count)
    ordered = tuple(changes)
    indices = [index for index, _ in ordered]
    if indices != sorted(indices) or len(indices) != len(set(indices)):
        raise ValueError("step indices must be unique and ordered")
    if any(index < 1 or index > row_count for index in indices):
        raise ValueError("step index is outside the generated row range")

    change_map = dict(ordered)
    current = initial_price
    values: list[Decimal] = []
    for row_index in range(1, row_count + 1):
        current = change_map.get(row_index, current)
        values.append(current)
    return tuple(values)

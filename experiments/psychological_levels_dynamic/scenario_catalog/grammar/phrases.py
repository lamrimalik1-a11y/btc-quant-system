"""Constructor-only grammar phrases.

These functions only assemble immutable AST values. They do not compile
programs, generate prices, execute scenarios, or invoke analytical stages.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any

from .ast import GrammarParameter, GrammarPhrase, PhraseType
from .dimensions import Direction, PathSmoothness, RelativePosition, ZoneSide


def _phrase(
    phrase_type: PhraseType,
    row_budget: int,
    target_zone: str | None,
    description: str,
    **params: Any,
) -> GrammarPhrase:
    return GrammarPhrase(
        phrase_type=phrase_type,
        params=tuple(
            GrammarParameter(name=name, value=value)
            for name, value in sorted(params.items())
        ),
        row_budget=row_budget,
        target_zone=target_zone,
        description=description,
    )


def hold(
    row_budget: int,
    position: RelativePosition,
    target_zone: str | None = None,
) -> GrammarPhrase:
    return _phrase(
        PhraseType.HOLD,
        row_budget,
        target_zone,
        "Hold a declared geometry-relative position.",
        position=position,
    )


def ramp(
    row_budget: int,
    distance: Decimal,
    direction: Direction,
    smoothness: PathSmoothness = PathSmoothness.LINEAR,
) -> GrammarPhrase:
    return _phrase(
        PhraseType.RAMP,
        row_budget,
        None,
        "Move by a declared distance and direction.",
        direction=direction,
        distance=distance,
        smoothness=smoothness,
    )


def oscillate(
    row_budget: int,
    amplitude: Decimal,
    period_rows: int,
    target_zone: str | None = None,
) -> GrammarPhrase:
    return _phrase(
        PhraseType.OSCILLATE,
        row_budget,
        target_zone,
        "Describe bounded oscillation around a reference.",
        amplitude=amplitude,
        period_rows=period_rows,
    )


def approach_zone(
    row_budget: int,
    target_zone: str,
    side: ZoneSide,
    start_distance: Decimal,
) -> GrammarPhrase:
    return _phrase(
        PhraseType.APPROACH_ZONE,
        row_budget,
        target_zone,
        "Approach a target zone from a declared side.",
        side=side,
        start_distance=start_distance,
    )


def enter_zone(
    row_budget: int,
    target_zone: str,
    side: ZoneSide,
    depth: Decimal,
) -> GrammarPhrase:
    return _phrase(
        PhraseType.ENTER_ZONE,
        row_budget,
        target_zone,
        "Enter a target zone from a declared side.",
        depth=depth,
        side=side,
    )


def penetrate(
    row_budget: int,
    target_zone: str,
    depth: Decimal,
    side: ZoneSide | None = None,
) -> GrammarPhrase:
    params: dict[str, Any] = {"depth": depth}
    if side is not None:
        params["side"] = side
    return _phrase(
        PhraseType.PENETRATE,
        row_budget,
        target_zone,
        "Hold a declared geometry-relative penetration depth.",
        **params,
    )


def withdraw(
    row_budget: int,
    target_zone: str,
    side: ZoneSide,
    distance: Decimal,
) -> GrammarPhrase:
    return _phrase(
        PhraseType.WITHDRAW,
        row_budget,
        target_zone,
        "Withdraw from a target zone by a declared distance.",
        distance=distance,
        side=side,
    )


def hold_outside(
    row_budget: int,
    target_zone: str,
    side: ZoneSide,
    clearance: Decimal,
) -> GrammarPhrase:
    return _phrase(
        PhraseType.HOLD_OUTSIDE,
        row_budget,
        target_zone,
        "Hold outside a boundary at the declared clearance.",
        clearance=clearance,
        side=side,
    )


def recovery_gap(
    row_budget: int,
    target_zone: str,
    withdrawal_distance: Decimal,
) -> GrammarPhrase:
    return _phrase(
        PhraseType.RECOVERY_GAP,
        row_budget,
        target_zone,
        "Declare an outside-zone inter-visit recovery gap.",
        withdrawal_distance=withdrawal_distance,
    )


def break_candidate(
    row_budget: int,
    target_zone: str,
    side: ZoneSide,
    clearance: Decimal,
) -> GrammarPhrase:
    return _phrase(
        PhraseType.BREAK_CANDIDATE,
        row_budget,
        target_zone,
        "Cross a boundary and reach the declared clearance.",
        clearance=clearance,
        side=side,
    )


def accepted_break(
    row_budget: int,
    target_zone: str,
    side: ZoneSide,
    clearance: Decimal,
    acceptance_rows: int,
) -> GrammarPhrase:
    return _phrase(
        PhraseType.ACCEPTED_BREAK,
        row_budget,
        target_zone,
        "Describe a candidate plus its outside-residence contract.",
        acceptance_rows=acceptance_rows,
        clearance=clearance,
        side=side,
    )


def retest_boundary(
    row_budget: int,
    target_zone: str,
    side: ZoneSide,
    delay_rows: int,
    depth: Decimal,
) -> GrammarPhrase:
    return _phrase(
        PhraseType.RETEST_BOUNDARY,
        row_budget,
        target_zone,
        "Return from the far side into a retest envelope.",
        delay_rows=delay_rows,
        depth=depth,
        side=side,
    )


def reclaim(
    row_budget: int,
    target_zone: str,
    side: ZoneSide,
    depth: Decimal,
    residence_rows: int,
) -> GrammarPhrase:
    return _phrase(
        PhraseType.RECLAIM,
        row_budget,
        target_zone,
        "Cross into the prior side and hold reclaim residence.",
        depth=depth,
        residence_rows=residence_rows,
        side=side,
    )


def compress(
    row_budget: int,
    target_zone: str,
    amplitude_schedule: tuple[Decimal, ...],
) -> GrammarPhrase:
    return _phrase(
        PhraseType.COMPRESS,
        row_budget,
        target_zone,
        "Declare a decreasing immutable amplitude schedule.",
        amplitude_schedule=amplitude_schedule,
    )


def expand(
    row_budget: int,
    target_zone: str,
    amplitude_schedule: tuple[Decimal, ...],
) -> GrammarPhrase:
    return _phrase(
        PhraseType.EXPAND,
        row_budget,
        target_zone,
        "Declare an increasing immutable amplitude schedule.",
        amplitude_schedule=amplitude_schedule,
    )


def transfer_to_zone(
    row_budget: int,
    source_zone: str,
    target_zone: str,
    travel_distance: Decimal,
) -> GrammarPhrase:
    return _phrase(
        PhraseType.TRANSFER_TO_ZONE,
        row_budget,
        target_zone,
        "Leave a source zone and approach a distinct target zone.",
        source_zone=source_zone,
        travel_distance=travel_distance,
    )

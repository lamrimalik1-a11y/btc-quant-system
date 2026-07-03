"""Offline validation for the Psychological Levels experimental provider."""

from __future__ import annotations

from decimal import Decimal

from provider import (
    GEOMETRY_SOURCE,
    GEOMETRY_TYPE,
    PsychologicalLevelsProvider,
    canonical_decimal,
)


EXPECTED_CENTERS = tuple(
    Decimal(value)
    for value in (
        "59800",
        "60000",
        "60200",
        "60400",
        "60600",
        "60800",
        "61000",
    )
)


def generate(session_id: str = "BTCUSDT_2026-07-03_000000Z"):
    provider = PsychologicalLevelsProvider(
        spacing=Decimal("200"),
        zone_half_width=Decimal("25"),
        active_window=3,
    )
    return provider.generate(
        price=Decimal("60341"),
        symbol="BTCUSDT",
        market_timestamp="2026-07-03T12:00:00Z",
        session_id=session_id,
    )


def test_expected_geometry() -> None:
    zones = generate()
    assert len(zones) == 7
    assert tuple(zone.level_center for zone in zones) == EXPECTED_CENTERS
    assert all(zone.anchor_level == Decimal("60400") for zone in zones)
    assert tuple(zone.level_index for zone in zones) == (
        -3,
        -2,
        -1,
        0,
        1,
        2,
        3,
    )

    zone = next(item for item in zones if item.level_center == 60000)
    assert zone.lower_edge == Decimal("59975")
    assert zone.upper_edge == Decimal("60025")
    assert zone.zone_width == Decimal("50")
    assert zone.geometry_source == GEOMETRY_SOURCE
    assert zone.geometry_type == GEOMETRY_TYPE
    assert zone.shadow_only is True
    print("EXPECTED_GEOMETRY = PASS")


def test_stable_identity() -> None:
    first = generate()
    second = generate()
    assert tuple(zone.zone_id for zone in first) == tuple(
        zone.zone_id for zone in second
    )
    assert tuple(zone.case_id for zone in first) == tuple(
        zone.case_id for zone in second
    )
    assert tuple(zone.global_zone_key for zone in first) == tuple(
        zone.global_zone_key for zone in second
    )
    assert first[1].zone_id == "PSY_BTCUSDT_60000"
    assert first[1].case_id == "PSY_CASE_BTCUSDT_60000"
    print("STABLE_IDENTITY = PASS")


def test_session_scoped_identity() -> None:
    first = generate("SESSION_A")
    second = generate("SESSION_B")
    assert tuple(zone.zone_id for zone in first) == tuple(
        zone.zone_id for zone in second
    )
    assert all(
        left.global_zone_key != right.global_zone_key
        for left, right in zip(first, second)
    )
    print("SESSION_SCOPED_IDENTITY = PASS")


def test_deterministic_order() -> None:
    centers = tuple(zone.level_center for zone in generate())
    assert centers == tuple(sorted(centers))
    assert centers == EXPECTED_CENTERS
    print("DETERMINISTIC_ORDER = PASS")


def test_invalid_configuration() -> None:
    invalid = (
        {"spacing": 0},
        {"spacing": -200},
        {"zone_half_width": 0},
        {"zone_half_width": -25},
        {"spacing": 50, "zone_half_width": 25},
        {"spacing": 40, "zone_half_width": 25},
    )
    for kwargs in invalid:
        try:
            PsychologicalLevelsProvider(**kwargs)
        except ValueError:
            continue
        raise AssertionError(f"invalid configuration accepted: {kwargs}")
    print("INVALID_CONFIGURATION_REJECTED = PASS")


def test_decimal_canonical_identity() -> None:
    assert canonical_decimal(Decimal("60000")) == "60000"
    assert canonical_decimal(Decimal("60000.0")) == "60000"
    assert canonical_decimal(Decimal("60000.000")) == "60000"
    assert canonical_decimal(Decimal("6.0000E+4")) == "60000"
    assert canonical_decimal(Decimal("-0.000")) == "0"

    integer_input = PsychologicalLevelsProvider().generate(
        price=60341,
        symbol="btcusdt",
        market_timestamp=1,
        session_id="SESSION",
    )
    decimal_input = PsychologicalLevelsProvider().generate(
        price=Decimal("60341.000"),
        symbol="BTCUSDT",
        market_timestamp=1,
        session_id="SESSION",
    )
    assert tuple(zone.zone_id for zone in integer_input) == tuple(
        zone.zone_id for zone in decimal_input
    )
    print("DECIMAL_CANONICAL_IDENTITY = PASS")


def main() -> None:
    test_expected_geometry()
    test_stable_identity()
    test_session_scoped_identity()
    test_deterministic_order()
    test_invalid_configuration()
    test_decimal_canonical_identity()
    print("PSYCHOLOGICAL_LEVELS_PROVIDER_TEST = PASS")
    print("OFFLINE_ONLY = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

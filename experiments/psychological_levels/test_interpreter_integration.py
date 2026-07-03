"""Offline Psychological Levels to Interaction Interpreter validation."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_DIR = Path(__file__).resolve().parent
for path in (REPO_ROOT, EXPERIMENT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.interaction_interpreter import (
    AUDIT_ROW_DUPLICATE,
    AUDIT_ROW_OUT_OF_ORDER,
    ORDER_ACCEPTED,
    InteractionInterpreter,
)
from provider import PsychologicalLevelsProvider


def generated_60400_zone():
    provider = PsychologicalLevelsProvider(
        spacing=Decimal("200"),
        zone_half_width=Decimal("25"),
        active_window=3,
    )
    zones = provider.generate(
        price=Decimal("60341"),
        symbol="BTCUSDT",
        market_timestamp="2026-07-03T12:00:00Z",
        session_id="PSY_INTERPRETER_TEST",
    )
    return next(zone for zone in zones if zone.level_center == 60400)


def test_psychological_level_interaction_sequence() -> None:
    zone = generated_60400_zone()
    assert zone.lower_edge == Decimal("60375")
    assert zone.level_center == Decimal("60400")
    assert zone.upper_edge == Decimal("60425")

    # Five dollars keeps the first row above the zone attached to the active
    # visit. The following three non-touching rows then complete the visit.
    interpreter = InteractionInterpreter(
        zone_id=zone.zone_id,
        lower_edge=zone.lower_edge,
        upper_edge=zone.upper_edge,
        touch_tolerance=5,
        visit_lull_rows=3,
    )
    state = interpreter.initial_state()
    price_path = (
        (1, Decimal("60350")),
        (2, Decimal("60376")),
        (3, Decimal("60400")),
        (4, Decimal("60430")),
        (5, Decimal("60435")),
        (6, Decimal("60440")),
        (7, Decimal("60445")),
    )

    events_by_row: dict[int, tuple[str, ...]] = {}
    for row_index, price in price_path:
        result = interpreter.interpret_in_order(
            state,
            row_index=row_index,
            timestamp=f"T{row_index}",
            price=price,
        )
        assert result.status == ORDER_ACCEPTED
        state = result.state
        events_by_row[row_index] = tuple(
            event.event_type for event in result.events
        )

    assert events_by_row[1] == ()
    assert events_by_row[2] == (
        "TOUCH",
        "ZONE_ENTER",
        "VISIT_STARTED",
        "PENETRATION_UPDATED",
    )
    assert events_by_row[3] == ("PENETRATION_UPDATED",)
    assert events_by_row[4] == ("ZONE_EXIT",)
    assert events_by_row[5] == ()
    assert events_by_row[6] == ()
    assert events_by_row[7] == ("VISIT_COMPLETED",)
    assert state.completed_visit_count == 1
    assert state.active_visit_id == ""
    print("PSYCHOLOGICAL_INTERACTION_SEQUENCE = PASS")


def test_row_ordering_contract() -> None:
    zone = generated_60400_zone()
    interpreter = InteractionInterpreter(
        zone_id=zone.zone_id,
        lower_edge=zone.lower_edge,
        upper_edge=zone.upper_edge,
    )
    initial = interpreter.initial_state()
    accepted = interpreter.interpret_in_order(
        initial,
        row_index=10,
        timestamp="T10",
        price=Decimal("60376"),
    )
    assert accepted.status == ORDER_ACCEPTED

    duplicate = interpreter.interpret_in_order(
        accepted.state,
        row_index=10,
        timestamp="T10_DUPLICATE",
        price=Decimal("60400"),
    )
    assert duplicate.status == AUDIT_ROW_DUPLICATE
    assert duplicate.state is accepted.state
    assert duplicate.events == ()

    older = interpreter.interpret_in_order(
        accepted.state,
        row_index=9,
        timestamp="T9_OLDER",
        price=Decimal("60400"),
    )
    assert older.status == AUDIT_ROW_OUT_OF_ORDER
    assert older.state is accepted.state
    assert older.events == ()
    print("ROW_ORDERING_CONTRACT = PASS")


def test_no_project1_geometry_required() -> None:
    zone = generated_60400_zone()
    forbidden_project1_fields = (
        "preparation_low_price",
        "preparation_high_price",
        "formation_lower_edge",
        "formation_upper_edge",
        "interaction_core_lower_edge",
        "interaction_core_upper_edge",
        "interaction_density_lower_band",
        "interaction_density_upper_band",
    )
    assert all(
        not hasattr(zone, field_name)
        for field_name in forbidden_project1_fields
    )
    print("NO_PROJECT1_FIELDS_REQUIRED = PASS")


def main() -> None:
    test_psychological_level_interaction_sequence()
    test_row_ordering_contract()
    test_no_project1_geometry_required()
    print("PSYCHOLOGICAL_LEVELS_INTERPRETER_INTEGRATION_TEST = PASS")
    print("OFFLINE_ONLY = TRUE")
    print("PRODUCTION_EFFECTS = FALSE")


if __name__ == "__main__":
    main()

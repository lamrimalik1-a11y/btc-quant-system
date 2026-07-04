"""Scenario Catalog specifications -- Phase 3 foundation.

Plain, immutable ScenarioSpecification data for the four highest-priority
families (baseline, adversarial_attacker_pressure, regime_change_into_pressure,
repeated_attacks). Providers live in families/*.py; this module only
constructs the concrete parameter values for each scenario_id. Adding a new
specification to an existing family means adding one entry here -- it never
requires touching a provider.

expected_behavior_notes and validation_metadata below are preregistration /
documentation only, written from the known SIMPLE_RESEARCH_SDR_V1 mechanics
formula before any downstream execution. Providers in families/*.py never
read these two fields -- test_scenario_catalog.py verifies this structurally,
not just by convention.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path


CATALOG_DIR = Path(__file__).resolve().parent
DYNAMIC_DIR = CATALOG_DIR.parent
for path in (CATALOG_DIR, DYNAMIC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from scenario_contract import ScenarioSpecification

from families.baseline import FAMILY_NAME as BASELINE_FAMILY
from families.adversarial_attacker_pressure import (
    FAMILY_NAME as ADVERSARIAL_FAMILY,
)
from families.regime_change_into_pressure import (
    FAMILY_NAME as REGIME_CHANGE_FAMILY,
)
from families.repeated_attacks import FAMILY_NAME as REPEATED_ATTACKS_FAMILY


_COMMON_GEOMETRY = {
    "spacing": Decimal("200"),
    "zone_half_width": Decimal("25"),
    "active_window": 3,
    "symbol": "BTCUSDT",
}


BASELINE_TRIANGULAR_REFERENCE_V1 = ScenarioSpecification(
    scenario_id="BASELINE_TRIANGULAR_REFERENCE_V1",
    scenario_family=BASELINE_FAMILY,
    schema_version="1",
    description=(
        "Reference control reproducing the exact Chapter I triangular price "
        "shape, preserved as a catalog scenario for later comparison."
    ),
    parameters={
        "lower": Decimal("59740"),
        "upper": Decimal("61060"),
        "half_period_rows": 132,
    },
    geometry_parameters={
        **_COMMON_GEOMETRY,
        "market_timestamp": "2026-07-03T12:00:00Z",
        "session_id": "CH2_PHASE3_BASELINE",
    },
    row_count=3000,
    start_price=Decimal("60341"),
    expected_behavior_notes=(
        "Preserves Chapter I's already-verified behavior: 159 completed "
        "visits across 7 zones, 145 transitions, zero "
        "RESEARCH_ATTACKER_PRESSURE observations. Reference point only -- "
        "not itself expected to reveal anything new.",
    ),
    validation_metadata={
        "chapter": 2,
        "phase": 3,
        "mechanism": "periodic_triangular_reference",
        "outcome_required": False,
    },
    seed_metadata="UNUSED_NO_PRNG",
)


ADVERSARIAL_ESCALATING_PENETRATION_V1 = ScenarioSpecification(
    scenario_id="ADVERSARIAL_ESCALATING_PENETRATION_V1",
    scenario_family=ADVERSARIAL_FAMILY,
    schema_version="1",
    description=(
        "Shallow probe into a zone, full withdrawal, then a much deeper and "
        "longer sustained penetration into the same zone -- constructed to "
        "make delta_omega large relative to health, per the existing SDR "
        "formula."
    ),
    parameters={
        "baseline_price": Decimal("60300"),
        "changes": (
            (11, Decimal("60385")),
            (16, Decimal("60300")),
            (61, Decimal("60420")),
            (91, Decimal("60300")),
        ),
    },
    geometry_parameters={
        **_COMMON_GEOMETRY,
        "market_timestamp": "2026-07-03T12:00:00Z",
        "session_id": "CH2_PHASE3_ADVERSARIAL_ATTACKER_PRESSURE",
    },
    row_count=300,
    start_price=Decimal("60341"),
    expected_behavior_notes=(
        "Mechanism hypothesis, not a required outcome: the shallow probe "
        "(rows 11-15, ~10 price units past the targeted zone's lower edge) "
        "should decay health only slightly; the deep sustained penetration "
        "(rows 61-90, ~45 units past the same edge, held 6x longer) should "
        "accumulate a much larger omega than the shallow probe did, making "
        "delta_omega large relative to the health remaining at that visit. "
        "Whether this actually crosses SDR_LABEL_THRESHOLD is an empirical "
        "question for a later phase -- not required or validated here.",
    ),
    validation_metadata={
        "chapter": 2,
        "phase": 3,
        "mechanism": "escalating_penetration_depth",
        "targets_downstream_state": "RESEARCH_ATTACKER_PRESSURE",
        "outcome_required": False,
    },
    seed_metadata="UNUSED_NO_PRNG",
)


REGIME_QUIET_TO_PRESSURE_V1 = ScenarioSpecification(
    scenario_id="REGIME_QUIET_TO_PRESSURE_V1",
    scenario_family=REGIME_CHANGE_FAMILY,
    schema_version="1",
    description=(
        "A quiet, mildly-oscillating regime (repeated shallow in/out "
        "touches of one zone) followed by a shift into the same "
        "escalating-penetration shape used by adversarial_attacker_pressure, "
        "targeting the SAME zone -- required so Stage 6's strictly per-zone "
        "walk-forward history spans both regimes continuously."
    ),
    parameters={
        "quiet_row_count": 200,
        "quiet_center": Decimal("60450"),
        "quiet_amplitude": Decimal("70"),
        "pressure_baseline_price": Decimal("60300"),
        "pressure_changes": (
            (11, Decimal("60385")),
            (16, Decimal("60300")),
            (61, Decimal("60420")),
            (91, Decimal("60300")),
        ),
    },
    geometry_parameters={
        **_COMMON_GEOMETRY,
        "market_timestamp": "2026-07-03T12:00:00Z",
        "session_id": "CH2_PHASE3_REGIME_CHANGE_INTO_PRESSURE",
    },
    row_count=400,
    start_price=Decimal("60341"),
    expected_behavior_notes=(
        "Mechanism hypothesis, not a required outcome: bounded_range's fixed "
        "4-value cycle (center-amplitude, center, center+amplitude, center) "
        "is centered so that only the center-amplitude value (60380, ~5 "
        "units past the targeted zone's lower edge) falls inside the zone, "
        "while center (60450) and center+amplitude (60520) both fall clearly "
        "outside it -- so each cycle is one brief touch followed by three "
        "consecutive outside rows, closing a separate completed visit every "
        "4 rows (verified: 50 visits across the 200-row quiet phase, health "
        "declining smoothly from ~98 to ~10 with no premature floor, all in "
        "the same zone the pressure phase later escalates into). The final "
        "200 rows shift to the same escalating-penetration shape used by "
        "ADVERSARIAL_ESCALATING_PENETRATION_V1, targeting that same zone. "
        "Whether any earlier hypothesis is invalidated by the regime shift "
        "is an empirical question for a later phase -- not required or "
        "validated here.",
    ),
    validation_metadata={
        "chapter": 2,
        "phase": 3,
        "mechanism": "regime_shift_quiet_to_escalating_penetration",
        "targets_downstream_state": "RESEARCH_ATTACKER_PRESSURE",
        "targets_downstream_behavior": "hypothesis_invalidation",
        "same_zone_both_phases": True,
        "outcome_required": False,
    },
    seed_metadata="UNUSED_NO_PRNG",
)


REPEATED_ATTACKS_PARTIAL_RECOVERY_V1 = ScenarioSpecification(
    scenario_id="REPEATED_ATTACKS_PARTIAL_RECOVERY_V1",
    scenario_family=REPEATED_ATTACKS_FAMILY,
    schema_version="1",
    description=(
        "Six equal-depth penetrations into the same zone separated by "
        "short withdrawal gaps, too short for full health recovery between "
        "touches -- a denominator-shrinking route to SDR stress, distinct "
        "from the numerator-spiking route in adversarial_attacker_pressure."
    ),
    parameters={
        "baseline_price": Decimal("60300"),
        "changes": tuple(
            entry
            for cycle in range(6)
            for entry in (
                (1 + cycle * 20, Decimal("60378")),
                (6 + cycle * 20, Decimal("60300")),
            )
        ),
    },
    geometry_parameters={
        **_COMMON_GEOMETRY,
        "market_timestamp": "2026-07-03T12:00:00Z",
        "session_id": "CH2_PHASE3_REPEATED_ATTACKS",
    },
    row_count=120,
    start_price=Decimal("60341"),
    expected_behavior_notes=(
        "Mechanism hypothesis, not a required outcome: six identical 5-row "
        "touches to a shallow, fixed depth (60378, ~3 units past the "
        "targeted zone's lower edge), each separated by a 15-row withdrawal "
        "(HEALTH_RECOVERY_PER_ROW=0.4 per row caps recovery at ~6.0 health "
        "per gap, below the ~9.0 decayed per 5-row touch at this depth) -- "
        "health should decline gradually and monotonically across the "
        "sequence rather than flooring on the first visit, even though no "
        "single visit is deeper than another (verified: health_at_visit "
        "declines 92.2 -> 89.2 -> 86.2 -> 83.2 -> 80.2 -> 77.2 across the six "
        "visits, omega_at_visit constant at 15.0 each time). Whether this "
        "crosses SDR_LABEL_THRESHOLD is an empirical question for a later "
        "phase -- not required or validated here; delta_omega is zero by "
        "construction in this specification, so the demonstration is of the "
        "denominator (health) shrinking under incomplete recovery, not of "
        "an SDR threshold crossing. This scenario is not expected to force "
        "RESEARCH_ATTACKER_PRESSURE by itself; it tests whether repeated "
        "equal-depth attacks with incomplete recovery degrade health over "
        "repeated visits.",
    ),
    validation_metadata={
        "chapter": 2,
        "phase": 3,
        "mechanism": "repeated_penetration_partial_recovery",
        "mechanism_under_test": "DENOMINATOR_DEGRADATION_PARTIAL_RECOVERY",
        "expected_downstream_state": "NOT_PREDECLARED",
        "outcome_required": False,
    },
    seed_metadata="UNUSED_NO_PRNG",
)


ALL_SPECIFICATIONS = (
    BASELINE_TRIANGULAR_REFERENCE_V1,
    ADVERSARIAL_ESCALATING_PENETRATION_V1,
    REGIME_QUIET_TO_PRESSURE_V1,
    REPEATED_ATTACKS_PARTIAL_RECOVERY_V1,
)

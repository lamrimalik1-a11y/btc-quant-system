# Phase 1B+ Zone Mechanics Research Design

Status: Research design only

Scope:

- Observation only
- No live signals
- No execution
- No scoring changes
- No Phase 2

## Purpose

This design translates the civil engineering / RDM analogy into a research-only
zone mechanics classification layer. The goal is to study how preparation zones
respond to market pressure after return/revisit events.

The layer is intended to use:

- Dashboard V2 Research Layer
- ZoneLifecycleMemory
- FieldLifecycleMemory
- Research Cycle 2 / 2B / 2C / 2D outputs

It does not create entries, exits, decisions, or execution instructions.

## Candidate Variables

### zone_penetration_depth

Measures how deeply price re-enters or crosses the preparation zone after a
return. Deeper penetration may indicate structural weakness if expansion does
not follow.

Research inputs:

- return_price
- preparation_low_price
- preparation_high_price
- preparation_mid_price
- max_move_after_return

### zone_reaction_strength

Measures the quality of the response after return to preparation.

Research inputs:

- expansion_after_return
- max_move_after_return
- expansion_strength
- expansion_type
- return_reaction_quality

### zone_load_pressure

Measures pressure applied to the zone during or after revisit.

Research inputs:

- peak_delta_zscore
- delta_extreme_after_context
- peak_primary_context
- peak_conditions
- field lifecycle states

### zone_fatigue_count

Counts repeated revisit / test / rejection behavior.

Research inputs:

- zone_revisit_count
- test_count
- rejection_count
- field_exhausted events

### zone_recovery_strength

Measures whether the zone recovers after being tested.

Research inputs:

- zone_reclaimed
- field_recovered
- expansion_strength
- no immediate reversal
- successful return classification

### zone_rupture_risk

Measures whether the zone appears likely to fail after revisit.

Research inputs:

- zone_rejected
- field_exhausted
- failed_after_return
- direct_reversal_flag
- weak_zone_reaction
- confidence_collapse

### zone_mechanical_state

Final research classification for the zone reaction.

Allowed states:

- ELASTIC_ZONE
- PLASTIC_ZONE
- FATIGUE_ZONE
- RUPTURE_ZONE
- RECOVERED_ZONE
- EXHAUSTED_ZONE

## Mechanical State Definitions

### ELASTIC_ZONE

Price returns to the zone, reacts cleanly, and the zone remains structurally
valid. Reaction is strong enough to imply the zone absorbed pressure without
decay.

Research signature:

- return_to_preparation = True
- zone_reaction_weak = False
- field_exhausted = False
- immediate reversal = False

### PLASTIC_ZONE

Zone deforms under pressure. Some reaction occurs, but the response is mixed or
delayed. It may still hold, but not cleanly.

Research signature:

- return_to_preparation = True
- expansion_then_reversal or mixed return behavior
- elevated zone_revisit_count
- no immediate full rejection

### FATIGUE_ZONE

Zone is repeatedly tested or revisited and begins losing reaction quality.

Research signature:

- zone_revisit_count elevated
- repeated zone_tested events
- weakening / exhaustion field states begin appearing
- reaction delay increases

### RUPTURE_ZONE

Zone fails after return. Price revisits preparation, but reaction quality is
weak and reversal appears quickly.

Research signature:

- zone_rejected
- field_exhausted
- failed_after_return = True
- direct_reversal_flag = True
- weak_zone_reaction = True

### RECOVERED_ZONE

Zone is tested and then reclaimed. Field behavior recovers after the return.

Research signature:

- zone_reclaimed
- field_recovered
- successful return
- no immediate reversal

### EXHAUSTED_ZONE

Zone may still produce movement, but the reaction is followed by exhaustion or
failed continuation. This is between fatigue and rupture.

Research signature:

- field_exhausted appears
- expansion fails or reverses
- return reaction is not clean
- may include expansion then exhaustion

## Current Case Mapping Notes

- CASE_00035 currently maps to RUPTURE_ZONE / TRUE_FAILED_RETURN.
- CASE_00041 currently maps to EXHAUSTED_ZONE or RUPTURE_ZONE depending on
  whether the expansion leg is interpreted as usable movement before exhaustion.
- CASE_00036 is the current available successful reference and maps to
  RECOVERED_ZONE.
- CASE_00044 was requested as a possible successful example, but it is not
  present in the current research log. It should remain pending until a replay
  window produces that case.

## Research Questions

1. Does zone_rejected + field_exhausted reliably identify failed-return reversal?
2. Does zone_reclaimed + field_recovered identify successful return?
3. Does zone_revisit_count separate fatigue from rupture?
4. Does reaction delay increase before failed return?
5. Does delta extreme pressure increase rupture risk?
6. Can zone_mechanical_state improve manual observation without changing scoring?

## Next Research Step

Validate this mechanical classification on larger replay windows and compare:

- RUPTURE_ZONE vs RECOVERED_ZONE
- FATIGUE_ZONE vs PLASTIC_ZONE
- EXHAUSTED_ZONE vs TRUE_FAILED_RETURN

Research only. No live signals. No scoring changes.

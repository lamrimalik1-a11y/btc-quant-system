# RDM Market Mechanics Status

## Overview

RDM Market Mechanics is a research-only structural interpretation layer.
Civil-engineering-inspired: fleche, moment, capacity, sigma, fatigue, recovery, rupture.

Does not affect Dashboard V2 scoring. Does not generate trading signals.

## V1.1 - V1.5

Foundation layer. Stable.
Checkpoint: PHASE1B_RDM_MARKET_MECHANICS_V1_5

## V1.6 — Full Series (COMPLETED)

### V1.6-A: Numerical Foundation
42 new rdm_v16_* columns. Birth / Current / Live / Final metrics.

### V1.6-B1: Attacker Force Basics
Attacker force normalization, zone-relative scoring.
Output: zone_attacker_evolution.csv

### V1.6-B3.5-A/B: Attempt Segmentation
Contiguous + force-lull segmentation. Mean attempts: 2.46 per zone.

### V1.6-B4-A: Zone Strength Score (ZSS)
Composite [0-100]. Components: capacity_ratio, rigidity_ratio, fatigue_inverse,
recovery_ratio, stress_availability.
Output: zone_strength_profile.csv

### V1.6-B4-B: Zone vs Attacker
AFS (Attacker Force Score) + Force Ratio = AFS / ZSS.
Output: zone_vs_attacker_profile.csv

### V1.6-B5 / B5.5: Anomaly Physics + Trajectory Context
expected_balance vs observed_balance. Trajectory gate.
Output: zone_anomaly_profile.csv

### V1.6-B6: Elastic Reinforcement Physics
capacity_growth_factor, rigidity_growth_factor, reinforcement_score.
Design review: reinforcement_mode = reformulation of zone_mechanical_state.
Output: zone_reinforcement_profile.csv

### V1.6-B7: Attacker Conversion Physics
CORE FINDING: Force != Damage. Conversion can be zero.
Output: attacker_conversion_profile.csv

### V1.6-B7.5-B: Force Allocation Physics
Growth Channel vs Damage Channel. Force allocation balance.
Output: force_allocation_profile.csv

### V1.6-B7.6-A through D: Exposure Physics

CORE VALIDATED FINDING:
    sigma_at_return x zone_penetration_depth vs omega_stress_area
    r = 0.9935   (n=31)

Omega is the primary Deep Structural Exposure variable.

Structural engagement chain (CONFIRMED):
    Force -> sigma_barre filter -> Penetration -> Omega -> mechanical_family -> Growth or Damage

sigma_barre driven by structural memory (reclaim_history r=0.69, memory_score r=0.67).
Force input barely correlates with engagement (r=0.12).

### V1.6-B7.6-E/F: Surface Damage Validation

HYPOTHESIS REJECTED. Zero-omega damage is:
    rigidity_live = rigidity_birth - row_progress x zone_strength_decay x 0.55
Time-based temporal decay formula. Not independent market physics.

### V1.6-B7.7: Structural Exposure Physics

Cyclic metrics insufficient variance in current dataset.
Not validated. Future research only.

### V1.6-B8: Zone Visit Timeline
Per-visit structural records. 729 visits across 276 zones.
Output: zone_visit_timeline.csv

### V1.6-B9: Zone Health Evolution
Health trajectory across visits: slope, total_change, health_state.
Output: zone_health_evolution.csv

### V1.6-B10: Structural Trajectory Classification
STRENGTHENING / STABLE / DEGRADING / ACCELERATING_FAILURE / TERMINAL / UNKNOWN.
B10 fix: HEALTH_STABLE evaluated before DEGRADING gate.
Output: zone_structural_trajectory.csv

### V1.6-B11: Structural Engagement Prediction
HOLD / FAIL / UNCERTAIN / NO_PREDICTION + prediction_confidence.
Output: zone_structural_prediction.csv

## Phase 1 Synthesis Engine (NEW — PHASE1B_SYNTHESIS_ENGINE_STABLE)

Connects all B1-B11 outputs with statistical episode context.
Produces one MarketInterpretation per zone case.

Components:
    Taxonomy Register (role + scope per field)
    Bundle Assembler (B10 + B11 + episode statistical context)
    Priority Rules (3 rules: STRUCTURAL > CURRENT, STRUCTURE > CONTEXT)
    Genuine Conflict Check (binary flag)
    3-Gate Synthesis Check
    4-Level Coherence Label (STRONG / MODERATE / WEAK / INSUFFICIENT)
    Field Compressors (6 simple threshold-based compressors)
    Template Engine (3 templates + catch-all)

Output: zone_synthesis.csv (276 rows, 13 columns)

Interpretation example:
    "TERMINAL zone under opposing flow — failure confirmed."
    "STRENGTHENING zone after 3 visits — hold confirmed."
    "STABLE zone with zone dominant — hold expected."

Postponed to after B12 backtesting:
    Numeric Coherence Score (0-100)
    Redundancy Detection
    Advanced Conflict Types
    Correlation Analysis

## Validated Physics Chain

```
Attacker Force
    | filtered by sigma_barre_zone (structural memory driven)
Structural Engagement (penetration > 0)
    | sigma x penetration -> omega  (r = 0.9935)
Omega Stress Area
    | routed by mechanical_family
    +-- ELASTIC_FAMILY  --> Growth (+16 rig, +20 cap, constant)
    +-- DEGRADED_FAMILY --> Damage (fatigue + decay, scales with omega)
```

## Rejected Hypotheses

- reinforcement_mode (B6): reformulation of zone_mechanical_state
- Growth Rate (B7.5-A): formula artifact (16/interaction_count)
- Force Allocation (B7.5-B): reformulation of zone_mechanical_state
- Surface Damage (B7.6-F): temporal decay formula, not physics
- Cyclic Exposure (B7.7): insufficient variance in current dataset

## Current Stable Checkpoint

PHASE1B_SYNTHESIS_ENGINE_STABLE

## Next: B12 + Data Collection

Before B12 can be meaningful:
- 45-60 days of data must be collected
- Full pipeline rebuild on extended dataset
- B12 validates structural_prediction vs observed market outcome
- Numeric Coherence Score calibrated from B12 accuracy data

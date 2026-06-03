# RDM Market Mechanics Status

## Overview

RDM Market Mechanics is a research-only structural interpretation layer. It studies zone behavior using civil-engineering-inspired concepts such as fleche, moment, capacity, sigma stress, fatigue, recovery, rupture, and lifecycle memory.

It does not affect Dashboard V2 scoring. It does not generate trading signals.

## V1.1 - V1.5

Foundation layer. Completed and stable.

Checkpoint: `PHASE1B_RDM_MARKET_MECHANICS_V1_5`

## V1.6 — Complete Series

### V1.6-A — Numerical Foundation

Status: COMPLETED

42 new `rdm_v16_*` columns. Birth / Current / Live / Final metrics for all structural families.

### V1.6-B1 — Attacker Force Basics

Status: COMPLETED

Attacker force normalization, zone-relative scoring, persistence, trend slope.

### V1.6-B3.5-A / B3.5-B — Attempt Segmentation

Status: COMPLETED

Contiguous and force-lull based segmentation. Mean attempts per zone: 2.46.

### V1.6-B4-A — Zone Strength Foundation (ZSS)

Status: COMPLETED

Composite Zone Strength Score [0-100]. Drives Zone vs Attacker comparison.

### V1.6-B4-B — Zone vs Attacker

Status: COMPLETED

Attacker Force Score (AFS). Force Ratio = AFS / ZSS.

### V1.6-B5 / B5.5 — Anomaly Physics + Trajectory Context

Status: COMPLETED

expected_balance vs observed_balance. ACTIVE_DEGRADATION / STABLE_ZONE / RECOVERING_ZONE gate.

### V1.6-B6 — Elastic Reinforcement Physics

Status: COMPLETED / DESIGN REVIEW COMPLETED

reinforcement_mode is NOT independent from zone_mechanical_state. Reformulation of same categorical information.

### V1.6-B7 — Attacker Conversion Physics

Status: COMPLETED

Output: `research/attacker_conversion_profile.csv`

Core finding: Force != Damage. Conversion can be zero even with large force input.

### V1.6-B7.5-A / B7.5-B — Elastic Growth Rate and Force Allocation

Status: COMPLETED

Growth rate is a formula artifact (constant 16/interaction_count for ELASTIC). Force allocation confirms binary channel split but is another reformulation of zone_mechanical_state.

### V1.6-B7.6-A — Absorption vs Reflection Physics

Status: COMPLETED

HIGH_OMEGA = absorption-dominant, LOW_OMEGA = reflection-dominant. Distinguished by overstress_ratio, sigma_failure_risk, penetration_depth.

### V1.6-B7.6-B — Structural Engagement Physics

Status: COMPLETED

sigma_barre_zone is driven by structural memory (reclaim_history r=+0.69, mechanical_memory_score r=+0.67). Force input barely correlates with engagement (r=+0.12).

Best binary predictor: sigma_barre < Q50 OR force_ratio > 0.80 → 77.4% accuracy.

### V1.6-B7.6-C through D — Stress Exposure Physics and Omega Validation

Status: COMPLETED

CORE FINDING:

```
sigma_at_return × zone_penetration_depth  vs  omega_stress_area
r = 0.9935   (n=31)
```

Omega is the primary Deep Structural Exposure variable.

### V1.6-B7.6-E / F — Surface Damage Review and Validation

Status: COMPLETED — HYPOTHESIS REJECTED

Zero-omega damage in RIGID zones is NOT independent physics. It is the live structural evolution formula:

```python
rigidity_live = rigidity_birth - row_progress × zone_strength_decay × 0.55 + repair_effect × 8.0
```

Discrete values 7.7 and 4.95 = 14 × 0.55 and 9 × 0.55 (from field_exhausted/field_weakening lifecycle events).

### V1.6-B7.7 — Structural Exposure Physics

Status: COMPLETED

Cyclic metrics (force_lull_attempt_count, zone_test_count, interaction_count) have insufficient variance in the current 50-zone dataset to validate the Deep + Cyclic framework. Future research only.

## Validated Physics Chain

```
Attacker Force
    | filtered by sigma_barre_zone
    | sigma_barre driven by structural memory (reclaim_history, mechanical_memory_score)
Structural Engagement (penetration > 0)
    | sigma_at_return x penetration_depth
Omega Stress Area  ~=  sigma x penetration  (r = 0.9935)
    | routed by mechanical_family
    +-- ELASTIC_FAMILY  -->  Growth (+16 rigidity, +20 capacity, constant)
    +-- DEGRADED_FAMILY -->  Damage (fatigue + structural decay, scales with omega)
```

## Rejected Hypotheses

- reinforcement_mode (B6): reformulation of zone_mechanical_state
- Growth rate sign (B7.5-A): formula artifact, not protective mechanism
- Force allocation balance (B7.5-B): reformulation of zone_mechanical_state
- Surface damage (B7.6-F): time-based temporal decay formula, not independent physics
- Cyclic exposure (B7.7): insufficient dataset variance to validate

## Current Stable Checkpoint

Tag: `PHASE1B_HYBRID_DOWNLOADER_STABLE`

Prior: `PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE`

## Active Work

Next: rebuild 634-row RDM research dataset using new 3-tier downloader, then continue RDM V1.6 development.

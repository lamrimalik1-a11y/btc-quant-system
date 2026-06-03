# RDM Market Mechanics Status

## Overview

RDM Market Mechanics is a research-only structural interpretation layer. It studies zone behavior using civil-engineering-inspired concepts such as flèche, moment, capacity, sigma stress, fatigue, recovery, rupture, and lifecycle memory.

It does not affect Dashboard V2 scoring. It does not generate trading signals.

## V1.1 — V1.5

RDM V1.1 through V1.5 established the mechanical foundation:

- Flèche / Moment / Capacity / Sigma / ELS / ELU
- Recovery / Fatigue / Rigidity
- Real Zone Geometry
- Birth vs Live Tracking
- Live RDM Evolution
- Interaction Core Geometry
- Interaction Density Mapping
- Structural Lifecycle Calibration
- Mechanical Memory
- Overlay calibration

Stable checkpoint: `PHASE1B_RDM_MARKET_MECHANICS_V1_5`

## V1.6-A — Numerical Foundation

Status: COMPLETED

- 42 new `rdm_v16_*` columns
- Birth / Current / Live / Final absolute metrics
- Delta from Birth for all metric families
- Percentage Change from Birth for all metric families

## V1.6-B — Attacker Physics Series

### B1 — Attacker Force Basics

Status: COMPLETED

- Attacker force mean / peak / zone-normalized
- Attacker persistence, trend slope
- Force cycle normalization

### B3.5-A — Attack Attempt Segmentation

Status: COMPLETED

- Contiguous gap-based segmentation of attacker sessions

### B3.5-B — Force-Lull Attempt Segmentation

Status: COMPLETED

- Sub-session segmentation using force lull thresholds
- ATTACKER_LULL_THRESHOLD_RATIO = 0.50
- Mean attempts per zone: 2.46 (was 1 before)

### B4-A — Zone Strength Foundation (ZSS)

Status: COMPLETED

- Composite Zone Strength Score [0-100]
- Components: capacity_ratio, rigidity_ratio, fatigue_inverse, recovery_ratio, stress_availability

### B4-B — Zone vs Attacker

Status: COMPLETED

- Attacker Force Score (AFS)
- Force Ratio = AFS / ZSS
- Zone vs Attacker profile CSV

### B5 — Anomaly Physics

Status: COMPLETED

- expected_balance vs observed_balance
- balance_gap = observed - expected
- anomaly_direction: ZONE_STRONGER_THAN_RESULT / BALANCED / ATTACKER_STRONGER_THAN_RESULT

### B5.5 — Trajectory Context

Status: COMPLETED

- trajectory_context: ACTIVE_DEGRADATION / STABLE_ZONE / RECOVERING_ZONE
- anomaly_direction_gated: adds EXPECTED_DEGRADATION gate

### B6 — Elastic Reinforcement Physics

Status: COMPLETED

- capacity_growth_factor, rigidity_growth_factor
- reinforcement_score [0-100], reinforcement_mode

Design review result:

reinforcement_mode is NOT independent from zone_mechanical_state. It is a quantitative reformulation of the same categorical information. All ELASTIC/RECOVERED zones = STRONG_REINFORCEMENT; all RIGID/EXHAUSTED = NO_REINFORCEMENT.

### B7 — Attacker Conversion Physics

Status: COMPLETED

Output: `research/attacker_conversion_profile.csv`

Key finding: Force ≠ Damage.

```
attacker_force_input (678 for CASE_00085) → total_damage = 0.0
```

Conversion_mode: INEFFICIENT_ATTACKER / NORMAL_CONVERSION / HIGH_CONVERSION.

### B7.5-A — Elastic Growth Rate Test

Status: COMPLETED

Growth rate = 16/interaction_count for ELASTIC zones. This is a formula identity, not a structural measurement. The sign of growth rate (positive/negative) perfectly separates zero-damage from damaged cases but only because it mirrors zone_mechanical_state.

### B7.5-B — Force Allocation Physics

Status: COMPLETED

Output: `research/force_allocation_profile.csv`

Two channels:
- GROWTH_DOMINANT: total_growth=36 (constant), total_damage=0, damage_ratio=0
- DAMAGE_DOMINANT: total_growth=0, total_damage varies

Key finding: total_growth = 36.0 for ALL 22 GROWTH_DOMINANT cases — a model constant, not market-measured. Force allocation balance is another reformulation of zone_mechanical_state.

### B7.6-A — Absorption vs Reflection Physics

Status: COMPLETED

LOW_OMEGA (omega ≤ 100) = REFLECTION_DOMINANT:
- sigma_failure_risk = 100% NONE
- overstress_ratio < 0.5
- penetration ≈ 0

HIGH_OMEGA (omega > 100) = ABSORPTION_DOMINANT:
- sigma_failure_risk = all MEDIUM/HIGH
- overstress_ratio mean 10.3
- penetration 7-181 units

### B7.6-B — Structural Engagement Physics

Status: COMPLETED

Correlation with overstress_ratio (log-space):
- penetration_depth: r = +0.64 (attacker success at reaching interior)
- sigma_barre_zone: r = -0.49 (higher barre = lower overstress)
- force_input: r = -0.13 (essentially no relationship)

sigma_barre_zone driven by:
- reclaim_history: r = +0.686
- mechanical_memory_score: r = +0.672
- repair_cycles: r = +0.540

Best predictor: sigma_barre < Q50 OR force_ratio > 0.80 → 77.4% accuracy

### B7.6-C — Stress Exposure Physics

Status: COMPLETED (conceptual review only)

Engineering analogy: Arias Intensity (integral of squared acceleration over time).

omega_stress_area IS the RDM equivalent of Arias Intensity.

### B7.6-D — Omega Validation

Status: COMPLETED

CORE FINDING:

```
sigma_at_return × zone_penetration_depth  vs  omega_stress_area
r = 0.9935   (n=31)
```

omega = sigma × penetration to within 10% for ELASTIC and EXHAUSTED zones.
RECOVERED zones: sigma × pen overestimates omega by ~2× (recovery mechanism dissipates some stress).

Omega vs force_input as predictor:
- stress_utilization: r(omega)=0.946, r(force)=0.230
- fatigue: r(log_omega)=0.495, r(force)=0.136

Omega is the central Deep Structural Exposure variable.

### B7.6-E — Surface Damage Physics Review

Status: COMPLETED (conceptual review)

Hypothesis: zero-omega damage in RIGID zones represents surface contact fatigue (Hertz, fretting).

### B7.6-F — Surface Damage Validation

Status: COMPLETED — HYPOTHESIS REJECTED

Zero-omega damage is produced by the live structural evolution formula:

```python
rigidity_live = rigidity_birth - row_progress × zone_strength_decay × 0.55 + repair_effect × 8.0
capacity_live = capacity_birth - row_progress × zone_strength_decay × 0.08 + repair_effect × 10.0
```

zone_strength_decay = count(field_exhausted) × 14 + count(field_weakening) × 9 ...

Discrete values 7.7 and 4.95 = 14 × 0.55 and 9 × 0.55 respectively.

This is TIME-BASED structural aging, not market surface contact physics.

### B7.7 — Structural Exposure Physics

Status: COMPLETED

Cyclic exposure metrics (interaction_count, force_lull_attempt_count, zone_test_count) have insufficient variance in the current 50-zone dataset to validate the Deep + Cyclic exposure framework.

Best existing cyclic proxy: force_lull_attempt_count (conceptually closest to S-N cycle count).

Regression improvement from adding cyclic metrics to log_omega: negligible (max +0.023 R²).

Conclusion: Omega alone is sufficient for the current dataset. Cyclic dimension is future research only.

## Validated Physics Chain

```
Attacker Force
    ↓  [filtered by sigma_barre_zone]
    ↓  sigma_barre is driven by reclaim_history + mechanical_memory_score
Structural Engagement
    ↓  [penetration depth drives sigma_at_return]
Omega Stress Area  ≈  sigma_at_return × penetration_depth
    ↓  [routed by mechanical_family]
    ├── ELASTIC_FAMILY  →  Growth (+16 rigidity, +20 capacity — constant)
    └── DEGRADED_FAMILY →  Damage (fatigue + structural decay — scales with omega)
```

## Geometry Hierarchy

Context / Formation Range != Active RDM Zone != Interaction Density Band

## Current Stable Checkpoint

Tag: `PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE`

Secondary: `PHASE1B_DOWNLOAD_STABILITY_FIX_STABLE`

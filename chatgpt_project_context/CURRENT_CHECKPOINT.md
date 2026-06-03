# Current Checkpoint

## Active Checkpoint

Checkpoint:

PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE

Tag:

`PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE`

Status:

- Research only
- Observation only
- No Phase 2
- No execution
- No entries
- No live signals
- No scoring changes
- No Dashboard V2 scoring changes
- No RDM formula changes
- No lifecycle changes

## Secondary Checkpoint

PHASE1B_DOWNLOAD_STABILITY_FIX_STABLE

Completed:

- Binance historical downloader stability improvements
- Timeout raised: 120s -> 150s
- Max retries raised: 10 -> 15
- Extended backoff sequence
- Retry jitter (±30%)
- WinError 10060 detection and longer backoff
- Session retry counter
- Resume deduplication
- Periodic checkpoint progress logs
- Final download verification (row count, first/last timestamp, duplicate check)
- New CLI flags: `--max-retries`, `--timeout`

## RDM V1.6 Exposure Physics — Completed Series

### B1 — Attacker Force Basics

Completed. Attacker force normalization and zone-relative scoring.

### B3.5-A — Attack Attempt Segmentation

Completed. Contiguous attacker session segmentation.

### B3.5-B — Force-Lull Attempt Segmentation

Completed. Sub-session segmentation using force lull thresholds.
Mean attempts after B3.5-B: 2.46 per zone (was 1 before).

### B4-A — Zone Strength Foundation (ZSS)

Completed. Composite zone strength score from capacity, rigidity, fatigue_inverse, recovery, stress_availability.

### B4-B — Zone vs Attacker

Completed. AFS vs ZSS framework. Force ratio. Anomaly detection baseline.

### B5 — Anomaly Physics

Completed. expected_balance vs observed_balance. Balance gap. Anomaly direction.

### B5.5 — Trajectory Context

Completed. ACTIVE_DEGRADATION / STABLE_ZONE / RECOVERING_ZONE gate for anomaly detection.

### B6 — Elastic Reinforcement Physics

Completed. capacity_growth_factor, rigidity_growth_factor, reinforcement_score, reinforcement_mode.

Design review: reinforcement_mode is a reformulation of zone_mechanical_state — not independent.

### B7 — Attacker Conversion Physics

Completed. `research/attacker_conversion_profile.csv`.

Key finding: Force ≠ Damage. Attacker force does not predict structural damage.

### B7.5-A — Elastic Growth Rate Test

Completed. Growth rate is a symptom, not a mechanism. The sign separation is perfect but growth rate = 16/interaction_count for elastic zones — a formula artifact.

### B7.5-B — Force Allocation Physics

Completed. `research/force_allocation_profile.csv`.

Two channels: Growth Channel and Damage Channel.

Key finding: total_growth = 36.0 for ALL growth-dominant cases (constant, not market-measured). Force allocation confirms the binary channel split but is another reformulation of zone_mechanical_state.

### B7.6 Series — Exposure Physics

#### B7.6-A — Absorption vs Reflection

Completed. HIGH_OMEGA vs LOW_OMEGA GROWTH_DOMINANT split confirmed.

Two physical families:
- REFLECTION_DOMINANT: omega near zero, overstress < 1, sigma_failure_risk = NONE
- ABSORPTION_DOMINANT: omega high, overstress > 1, sigma_failure_risk active

#### B7.6-B — Structural Engagement Physics

Completed. Force alone does not explain engagement.

Key correlations (n=31):
- sigma_barre vs overstress_ratio: r = -0.49 (high barre = lower overstress)
- penetration_depth vs overstress_ratio: r = +0.64

Engagement is controlled by:
- sigma_barre_zone (driven by structural memory: reclaim_history r=+0.69, mechanical_memory_score r=+0.67)
- NOT by force_input (r ≈ 0.12)

Best binary predictor: sigma_barre < Q50 OR force_ratio > 0.80 → 77.4% accuracy.

#### B7.6-C — Stress Exposure Physics

Completed. Conceptual review only.

Engineering analog: Arias Intensity (stress × time integral). omega_stress_area IS the structural equivalent of this integral.

Best definition of Stress Exposure: sigma × penetration × cycles (per-cycle version of omega).

#### B7.6-D — Omega Validation

Completed. Core empirical finding.

sigma × penetration vs omega: r = 0.9935

Omega is the primary Deep Structural Exposure variable.

#### B7.6-E — Surface Damage Physics Review

Completed. Conceptual review.

Hypothesis: RIGID zones with omega=0 and damage>0 represent surface contact fatigue (Hertz contact, fretting).

#### B7.6-F — Surface Damage Validation

Completed. Hypothesis REJECTED.

Zero-omega damage in RIGID zones is NOT independent market physics. It comes from:

```
rigidity_live = rigidity_birth - row_progress × zone_strength_decay × 0.55 + repair_effect × 8.0
capacity_live = capacity_birth - row_progress × zone_strength_decay × 0.08 + repair_effect × 10.0
```

The discrete 7.7 and 4.95 values are:
- 14.0 × 0.55 = 7.7 (one field_exhausted event)
- 9.0  × 0.55 = 4.95 (one field_weakening event)

This is a time-based temporal decay formula, not independent structural damage from market force.

### B7.7 — Structural Exposure Physics

Completed. Cyclic exposure review.

Key findings:
- Cyclic metrics (interaction_count, force_lull_attempt_count, zone_test_count) have low variance in the current dataset (interaction_count range: 101-114).
- No cyclic metric improves R² beyond log_omega alone.
- omega_per_test pattern is suggestive (GROWTH cases: more cycles at lower omega each; DAMAGE cases: fewer cycles at higher omega each) but confounded by mechanical_family.
- Not validated with current dataset — future research only.

## Confirmed RDM Physics Chain

```
Attacker Force
    ↓  [filtered by sigma_barre_zone]
Structural Engagement (penetration > 0)
    ↓  [× sigma_at_return]
Omega Stress Area  (stress × penetration = deep exposure)
    ↓  [routed by mechanical_family]
    ├── ELASTIC_FAMILY  →  Growth channel (+16 rigidity, +20 capacity, constant)
    └── DEGRADED_FAMILY →  Damage channel (fatigue + rigidity loss, scales with omega)
```

sigma_barre_zone is driven by structural memory (reclaim_history, repair_cycles, mechanical_memory_score) — NOT by current structural dimensions alone.

## Research CSVs Generated

- `research/zone_strength_profile.csv`
- `research/zone_vs_attacker_profile.csv`
- `research/zone_anomaly_profile.csv`
- `research/zone_reinforcement_profile.csv`
- `research/attacker_conversion_profile.csv`
- `research/force_allocation_profile.csv`
- `research/attacker_conversion_profile.csv`

## Prior Checkpoints (preserved)

- `PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK`
- `PHASE1B_RDM_VISUALIZATION_STABLE`
- `PHASE1B_RDM_MARKET_MECHANICS_V1_5`

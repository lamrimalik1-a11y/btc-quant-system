# RDM Market Mechanics Status

## Overview

RDM Market Mechanics is a research-only structural interpretation layer. It studies zone behavior using civil-engineering-inspired concepts such as flèche, moment, capacity, sigma stress, fatigue, recovery, rupture, and lifecycle memory.

It does not affect Dashboard V2 scoring. It does not generate trading signals.

## V1.1

RDM V1.1 stabilized the first mechanical layer:

- Flèche Model
- Signed Moment
- Capacity Layer
- Adaptive Sigma Barre
- ELS / ELU
- Timeline
- Mechanical Families
- Recovery
- Fatigue
- Rigidity
- Dashboard RDM Panels

Classification rule:

Variables -> Family -> Subtype -> State

Cases are reference-only.

## V1.3

RDM V1.3 added:

- Adaptive Sigma
- Sigma Aging
- Mechanical Capacity
- Verestchaguine Dynamic Flèche
- Zero Stress Protection
- Dormant Preparation
- Birth Registry
- Death Registry
- Mechanical Memory
- Birth Calibration
- Zone Evolution Chart
- Downloader robustness

## V1.4

RDM V1.4 added the dashboard result layer:

- RDM Result Layer
- Final Dashboard Result Block
- Zone Status Interpretation
- Health Score
- Risk Level
- Confidence Layer
- Short Reason
- Watch Action
- Section Result Summaries

Fields:

- `rdm_zone_status`
- `rdm_health_score`
- `rdm_risk_level`
- `rdm_confidence`
- `rdm_short_reason`
- `rdm_watch_action`

## V1.5

RDM V1.5 added and validated:

- Real Zone Geometry
- Birth vs Live Tracking
- Live RDM Evolution
- Calibration Guards
- Interaction Core Geometry
- Spatial Clamp
- Temporal Interaction Window
- True Lifecycle Guard
- Adaptive Recovery / Healing
- Regime-Normalized Sigma
- Interaction Density Mapping
- Weighted Interaction Center
- Density Bands
- Structural Lifecycle Calibration
- Recovery Persistence
- Fatigue Realism
- Rupture Persistence
- Mechanical Memory
- Birth / Return / Final comparison
- Overlay calibration
- Context vs Active Zone separation

## Geometry Model

Important distinction:

Context / Formation Range
!=
Active RDM Zone
!=
Interaction Density Band

Definitions:

- Context / Formation Range = broad historical formation area that created the zone.
- Active RDM Zone = compressed interaction core used as the primary active mechanical zone.
- Interaction Density Band = weighted concentration area inside the Active RDM Zone where touches, returns, rejection, stress, recovery, fatigue, and load cluster.

## Calibration Conclusions

Current conclusions after V1.5:

- Previous pessimistic collapse bias fixed.
- Recovery now has meaningful structural effect.
- Rupture persistence calibrated.
- One-row breach / rupture behavior is guarded.
- Interaction core compressed successfully.
- Active RDM Zone is smaller than Context / Formation Range.
- Density mapping is operational.
- Weighted interaction center is operational.
- Density bands are operational.
- Structure behaves more realistically as an evolving lifecycle.

## Current Limitations

Known limitations:

- RDM mechanics remain research-only and unproven as predictive tools.
- Density mapping requires more replay windows.
- Current sample size is still small.
- Score 5 and Score 6 samples need expansion.
- Live observation is allowed, but no execution or decision logic is allowed.
- The overlay is an observation aid, not a signal system.

## Current Stable Checkpoint

Checkpoint:

`PHASE1B_RDM_MARKET_MECHANICS_V1_5`

Commit:

`b04a781`

Tag:

`PHASE1B_RDM_MARKET_MECHANICS_V1_5`

## Performance Diagnostic + Safe Optimization

Status:

COMPLETED / READY TO SAVE

Completed work:

- Performance profiling
- `outputs/performance_profile_report.md`
- `outputs/performance_profile.json`
- `outputs/performance_optimization_plan.md`
- Episode Research Index Cache
- RDM Per-Case Cache
- Shared Interaction Mask Cache
- Live evolution row-window optimization
- Profiling logs
- Cache reuse metrics

Measured results:

- Episode research runtime: `24.55s -> 17.23s`
- Research analysis: `23.89s -> 16.38s`
- Latest research run after continued optimization: `16.41s total`, `15.83s cached analysis`
- RDM runtime: `14.78s -> 14.66s`
- Interaction core: `2.92s -> 1.96s`
- Live evolution: `4.55s -> 4.36s`
- Density: `~1.95s unchanged`

Current conclusions:

- Bottleneck mainly `CPU_PROCESSING + RDM_CALCULATOR`.
- Repeated scans were partially reduced successfully.
- Internet / Binance download is not the primary bottleneck for local research runs.
- Density mapping remains computationally heavy.
- The next safe speed wins are vectorization, optional cached storage, and batch write modes.

Optimization state:

- Episode research uses indexed row lookup.
- RDM calculator caches live evolution rows by case.
- Shared interaction masks are reused by interaction core, density, and lifecycle stages.
- Live evolution row-window extraction uses sorted row_id lookup.

Future targets:

- Vectorize safe numeric calculations.
- Prototype optional Parquet / DuckDB cache.
- Add validation write modes.
- Consider optional multiprocessing only after deterministic output diff checks.

Rules:

- No behavior changes
- No scoring changes
- No RDM logic changes
- No Dashboard logic changes
- No trading logic
- No Phase 2

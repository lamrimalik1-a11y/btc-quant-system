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

`PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK`

Commit:

See latest repository commit for the replay consistency checkpoint.

Tag:

`PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK`

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

## Replay Consistency Lock + Source Isolation

Status:

STABLE

Base:

`PHASE1B_RDM_MARKET_MECHANICS_V1_5`

Completed:

- Data Integrity Diagnostic for Episode 75 / CASE_00075
- Source data verified
- Timezone verified
- Dashboard mapping verified
- Episode row alignment verified
- Stale artifacts detected
- Explicit source modes: `LIVE_MODE` and `HISTORICAL_REPLAY_MODE`
- Historical replay source guards
- Dashboard blocks live/default files in historical replay mode
- No silent fallback to stale live files
- Overlay loader accepts `source_mode`
- Replay banner
- Per-episode source audit
- Dashboard footer: `ACTIVE SOURCE: historical replay / live`
- Replay consistency validator

Reports / tools:

- `tools/diagnose_episode_75_integrity.py`
- `outputs/data_integrity_episode_75_report.md`
- `outputs/data_integrity_episode_75.json`
- `tools/validate_replay_consistency.py`
- `outputs/replay_consistency_report.md`
- `outputs/replay_consistency_report.json`

Validator result:

- `MIXED_SOURCE_USAGE_DETECTED: False`
- `STALE_LIVE_FILES_FOUND: True`
- `TIMESTAMP_INCONSISTENCIES_FOUND: False`
- `REPLAY_LIVE_OVERLAP_FOUND: False`
- `HISTORICAL_REPLAY_SOURCES_PRESENT: True`

Conclusion:

Historical replay mode is isolated. Stale live files may exist, but they are explicitly blocked from contaminating historical replay mode. Replay, RDM, Dashboard, and Overlay rendering are traceable to explicit historical replay sources.

## V1.6

RDM V1.6 is the first phase of active development beyond the replay consistency lock.

Philosophy:

Numerical First. No HIGH/LOW labels only. Numbers, deltas, percentages alongside all existing categorical labels. The research layer becomes quantitatively inspectable.

### V1.6-A Numerical Foundation

Status:

COMPLETED

Scope:

Research only. Additive extension of RDM V1.5. Zero formula changes. Zero lifecycle changes. Zero scoring changes.

Implemented:

- 42 new `rdm_v16_*` columns added to `zone_mechanics_cycle3_results.csv`
- Numerical Foundation layer
- Birth / Current / Live / Final absolute metric values
- Delta from Birth for all tracked metric families
- Percentage Change from Birth for all tracked metric families

Metric Families:

- Rigidity
- Sigma
- Flèche
- Capacity
- Fatigue
- Recovery
- Stress Utilization (current state)
- Moment Utilization (current state)
- Interaction Density

Validation:

- py_compile passed
- zone_mechanics_calculator.py executed successfully
- 634 rows generated

Example — Episode 622:

Rigidity: Birth=50.0 / Current=50.0 / Delta=0.0

Sigma: Birth=19.194501 / Current=7.276244 / Delta=-11.918257 / Change=-62.092039%

Rules Preserved:

- No scoring changes
- No lifecycle changes
- No Dashboard V2 scoring impact
- No RDM formula changes
- No Phase 2
- No execution
- No entries
- No live signals

### V1.6-B — Next Target

RDM V1.6-B Attacker Definition

Goal:

Define the attacker as a first-class object. Measure attacker force from zone_live_rdm_evolution data. Track attacker force trend and persistence. Build toward Zone vs Attacker comparative framework.

Status:

DESIGN PHASE — Not yet implemented.

## Current RDM Active Phase

PHASE 1B+ Research Expansion

Active work:

RDM V1.6 Development

Completed:

- V1.6-A Numerical Foundation

Next:

- V1.6-B Attacker Definition

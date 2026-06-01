# Current Checkpoint

Checkpoint:

PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK

Commit:

See latest repository commit for the replay consistency checkpoint.

Tag:

`PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK`

Status:

- Research only
- Observation only
- No Phase 2
- No execution
- No entries
- No live signals
- No scoring changes
- No Dashboard V2 scoring changes

Includes:

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

Geometry hierarchy:

Context / Formation Range
!=
Active RDM Zone
!=
Interaction Density Band

Current conclusion:

The RDM layer is more realistic after V1.5. It no longer behaves like a permanent pessimistic collapse detector. Recovery can matter, rupture requires persistence, fatigue is less instant, and interaction density can now be observed inside the Active RDM Zone.

## Performance Diagnostic + Safe Optimization Checkpoint

Checkpoint extension:

Performance diagnostics and safe optimization pass.

Completed:

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

Profiling conclusions:

- Bottleneck mainly `CPU_PROCESSING + RDM_CALCULATOR`.
- Repeated dataframe scans were partially reduced successfully.
- Internet / Binance download is not the primary bottleneck for local research runs.
- Density mapping remains computationally heavy.

Latest optimization state:

- Episode research uses indexed historical row lookup.
- RDM calculator caches live evolution rows by case.
- Interaction masks are built once and reused.
- Live evolution row-window extraction uses sorted row_id lookup.

Future optimization targets:

- Vectorization
- Optional Parquet / DuckDB migration
- Batch write modes
- Optional multiprocessing later

Rules remain:

- Research only
- No behavior changes
- No scoring changes
- No RDM logic changes
- No Dashboard logic changes
- No trading logic

## Replay Consistency Lock

Base:

`PHASE1B_RDM_MARKET_MECHANICS_V1_5`

Completed:

- Data Integrity Diagnostic for Episode 75 / CASE_00075
- Source data verified
- Timezone verified
- Dashboard mapping verified
- Episode row alignment verified
- Stale artifacts detected and documented
- Explicit source modes:
  - `LIVE_MODE`
  - `HISTORICAL_REPLAY_MODE`
- Historical replay source guards
- Dashboard blocks live/default files in historical replay mode
- No silent fallback to stale live/default files
- Overlay loader accepts `source_mode`
- Replay banner and per-episode source audit
- Dashboard footer: `ACTIVE SOURCE: historical replay / live`
- Replay consistency validator

Reports / tools:

- `tools/diagnose_episode_75_integrity.py`
- `outputs/data_integrity_episode_75_report.md`
- `outputs/data_integrity_episode_75.json`
- `tools/validate_replay_consistency.py`
- `outputs/replay_consistency_report.md`
- `outputs/replay_consistency_report.json`

Latest validator result:

- `MIXED_SOURCE_USAGE_DETECTED: False`
- `STALE_LIVE_FILES_FOUND: True`
- `TIMESTAMP_INCONSISTENCIES_FOUND: False`
- `REPLAY_LIVE_OVERLAP_FOUND: False`
- `HISTORICAL_REPLAY_SOURCES_PRESENT: True`

Important conclusion:

Historical replay mode is now isolated. Stale live files may exist, but they are explicitly blocked from contaminating historical replay mode. Replay / RDM / Dashboard / Overlay rendering are traceable to explicit historical replay sources.

## RDM V1.6-A Numerical Foundation

Checkpoint:

`RDM_V1.6-A_NUMERICAL_FOUNDATION`

Status:

COMPLETED

Scope:

Research only. Extension of RDM V1.5. No formula changes. No lifecycle changes. No scoring changes.

Implemented:

- 42 new `rdm_v16_*` columns added to `zone_mechanics_cycle3_results.csv`
- Numerical Foundation layer
- Birth / Current / Live / Final absolute metrics
- Delta from Birth for all tracked metric families
- Percentage Change from Birth for all tracked metric families

Metric Families covered:

- Rigidity
- Sigma
- Flèche
- Capacity
- Fatigue
- Recovery
- Stress Utilization (current)
- Moment Utilization (current)
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

## Current Active Phase

PHASE 1B+ Research Expansion

Active Work:

RDM V1.6 Development

Completed:

- RDM V1.6-A Numerical Foundation

Next Target:

- RDM V1.6-B Attacker Definition

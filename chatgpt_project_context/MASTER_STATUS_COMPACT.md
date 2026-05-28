# Master Status Compact

## Current Stable Status

The project is stable at:

PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK

Commit:

See latest repository commit for the replay consistency checkpoint.

Tag:

`PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK`

Current system status:

- Dashboard V2 = stable
- Dashboard V2 replay = operational
- Dashboard V2 UI = operational
- Research Agent V1 = stable
- RDM Market Mechanics V1.5 = validated
- Interaction Density Mapping = operational
- Structural lifecycle calibration = operational
- Replay Consistency Lock = stable
- Source Isolation = stable
- Data Integrity Diagnostic = completed

## Completed Phases / Modules

Completed:

- Dashboard V2 statistical layer
- Dashboard V2 replay events / episodes
- Dashboard V2 Streamlit display
- Phase 1B Episode Research Assistant
- Research Dashboard
- Hypothesis 02 support
- Preparation Detector V1
- Reversal Lab
- Expansion Lab
- Comparison Lab
- Preparation Quality Lab
- Research cleanup and status tracking
- Dashboard V2 research mapping
- RDM Market Mechanics V1.1 through V1.5
- Context memory layer
- Zone lifecycle memory
- Field lifecycle memory
- Lifecycle event persistence

## Active Phase

PHASE 1B+ Research Expansion

Active work:

- Observation / calibration
- Replay validation
- Historical validation
- False positive review
- Live observation
- RDM mechanics refinement

## Latest Stable Checkpoint

Latest tag:

`PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK`

Checkpoint content:

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
- Replay Consistency Lock
- Source Isolation
- Episode 75 Data Integrity Diagnostic

## Next Steps

Recommended next steps:

- Pull only today's data first for observation.
- Review Dashboard V2 episodes and RDM overlay.
- Validate interaction density behavior on fresh data.
- Compare false positives vs successful structures.
- Only after current work is complete, pull a larger 10-day replay window.

Do not:

- Enter Phase 2
- Add execution
- Add entries
- Add live signals
- Change Dashboard V2 scoring
- Convert research labels into trade decisions

## Performance Diagnostic + Safe Optimization Checkpoint

Status:

COMPLETED / READY TO SAVE

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

Current conclusions:

- Bottleneck mainly `CPU_PROCESSING + RDM_CALCULATOR`.
- Repeated scans were partially reduced successfully.
- Internet / Binance download is not the primary bottleneck for local research runs.
- Density mapping remains computationally heavy.

Future optimization targets:

- Vectorization
- Optional Parquet / DuckDB research cache
- Batch write modes
- Optional multiprocessing later after deterministic output checks

Latest optimization state:

- Episode research uses indexed row lookup.
- RDM calculator caches live evolution rows by case.
- Interaction masks are cached and reused.
- Live evolution row-window extraction uses sorted row_id lookup.

Rules remain:

- No behavior changes
- No scoring changes
- No RDM logic changes
- No Dashboard logic changes
- No trading logic

## Replay Consistency Lock

Checkpoint:

`PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK`

Completed:

- Episode 75 / CASE_00075 data integrity diagnostic
- Explicit source modes: `LIVE_MODE` and `HISTORICAL_REPLAY_MODE`
- Historical replay source guards
- Dashboard blocks live/default files in historical replay mode
- No silent fallback to stale live/default files
- Overlay loader accepts `source_mode`
- Replay banner:
  - `REPLAY MODE ACTIVE`
  - Replay Source
  - Replay Date
  - Replay UTC Window
  - Episode Row Range
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

Historical replay mode is isolated. Stale live files may exist, but they are explicitly blocked from contaminating historical replay mode. Replay, RDM, Dashboard, and Overlay are traceable to explicit historical replay sources.

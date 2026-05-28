# Current Checkpoint

Checkpoint:

PHASE1B_RDM_MARKET_MECHANICS_V1_5

Commit:

`b04a781`

Tag:

`PHASE1B_RDM_MARKET_MECHANICS_V1_5`

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

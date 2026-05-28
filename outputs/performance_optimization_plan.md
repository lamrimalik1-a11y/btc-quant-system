# Performance Optimization Plan

Research-only planning document.

No optimization has been implemented in this file.

## Profiling Summary

Latest measured local run:

### Phase 1B Episode Research

- Total runtime: 24.55s
- Slowest step: `research_analysis_time = 23.89s`
- Likely bottleneck: `CPU_PROCESSING`
- Episodes analyzed: 53
- Historical rows loaded: 3018
- Peak Python heap: 6.07 MB

### RDM Zone Mechanics Calculator

- Total runtime: 14.78s
- Slowest steps:
  - `rdm_live_evolution = 4.55s`
  - `rdm_interaction_core = 2.92s`
  - `rdm_density = 1.98s`
  - `csv_write_rdm_outputs = 1.33s`
  - `rdm_base_mechanics = 1.26s`
- Likely bottleneck: `RDM_CALCULATOR`
- RDM rows processed: 53
- Live evolution rows: 3454
- Historical rows loaded: 3018
- Peak Python heap: 13.24 MB

## Why Episode Research Is Slow

The episode research assistant is slow mostly because it repeatedly scans historical rows per episode.

Likely causes:

- Each episode computes multiple future horizons: 1m, 5m, 15m, 30m, 1h, 2h, 4h, and day end.
- Each episode also computes max moves, adverse moves, return detection, reversal context, and expansion/reversal split.
- These operations appear to repeatedly filter or scan the same `historical_observation_rows.csv` data.
- The current structure favors clarity and research traceability over indexed lookup speed.
- CSV read/write is not the main issue for this run; research analysis time dominates.

Conclusion:

The bottleneck is not file size or memory. It is repeated per-episode CPU scanning.

## Why RDM Live Evolution / Core / Density Are Slow

The RDM calculator now builds several derived mechanical views:

- Live RDM evolution
- Interaction core geometry
- Interaction density mapping
- True lifecycle tracking

These are slow because they likely perform per-case scans over historical/live rows:

- `rdm_live_evolution` builds row-level evolution windows per zone/case.
- `rdm_interaction_core` scans live evolution rows again to find interaction points.
- `rdm_density` scans rows inside each final Active RDM Zone and computes weighted bucket density.
- `rdm_true_lifecycle` scans latest interaction rows and lifecycle state again.

The current architecture is correct for research, but the same row subsets are being re-used across several stages without a shared cache.

Conclusion:

RDM bottleneck is repeated per-case pandas filtering and row-wise `.iterrows()` / `.apply()` style processing.

## What Can Be Optimized Safely

Safe optimizations are those that preserve output values exactly or nearly exactly while reducing repeated work.

### 1. Cache Loaded DataFrames

Current issue:

- Different tools read the same CSV files independently.
- During validation, research assistant and RDM calculator both load historical rows.

Safe plan:

- Add a small read-through cache helper for script-local use.
- Cache by absolute path + modified time.
- Keep each script independent.
- Do not introduce global engine state.

Expected speedup:

- Small for single script runs.
- Moderate for combined validation workflows.

Risk:

- Low, if cache is script-local and invalidated by file modified time.

### 2. Pre-index Historical Rows

Current issue:

- Episode research repeatedly searches by timestamp and row id.

Safe plan:

- Build once:
  - `rows_by_row_id`
  - sorted timestamp arrays
  - close/price arrays
  - day buckets
- Use binary search for nearest future rows instead of repeated dataframe filters.

Expected speedup:

- High for episode research.
- Likely biggest first win.

Risk:

- Low to medium. Must preserve edge cases for missing timestamps and day-end lookup.

### 3. Precompute Future Horizon Lookups

Current issue:

- Each episode asks for multiple future prices and movement windows.

Safe plan:

- Convert timestamp column to monotonic datetime/int array once.
- For each episode end time, use `searchsorted` for all target horizons.
- Compute move windows using array slices.

Expected speedup:

- High.

Risk:

- Medium. Need careful comparison against current CSV output for a replay window.

### 4. Cache Per-Case Live Evolution Subsets

Current issue:

- RDM stages repeatedly filter `live_evolution_df` by `case_id`.

Safe plan:

- Build:
  - `live_by_case = {case_id: dataframe}`
- Pass this dictionary into interaction core, density, and lifecycle builders.
- Avoid rebuilding group dictionaries multiple times.

Expected speedup:

- Moderate.

Risk:

- Low. It is a structural cache, not a logic change.

### 5. Reuse Interaction Masks

Current issue:

- Interaction core and density both compute inside/touch/return/breach/stress masks.

Safe plan:

- Add internal columns in a temporary dataframe:
  - `is_interaction_point`
  - `is_inside_active_core`
  - `density_weight`
- Use the same computed columns across core and density stages.

Expected speedup:

- Moderate.

Risk:

- Medium if the mask definitions are accidentally changed.

### 6. Reduce CSV Writes During Validation

Current issue:

- RDM calculator writes many CSV and note files every run.

Safe plan:

- Add a diagnostics-only or validation option later:
  - `--skip-notes`
  - `--write-core-only`
  - `--no-write`
- Default behavior must remain unchanged.

Expected speedup:

- Low to moderate.
- Current CSV write cost is around 1.33s.

Risk:

- Low if optional and default remains current behavior.

### 7. Vectorize RDM Loops Where Safe

Current issue:

- Several RDM calculations are row-wise and can be vectorized.

Safe candidates:

- Numeric ratio fields
- State classification from thresholds
- Simple boolean flags
- Width/efficiency calculations

Expected speedup:

- Moderate.

Risk:

- Medium. Must compare output before/after.

## What Must Not Be Changed

Do not change:

- Dashboard V2 scoring
- Dashboard V2 layer logic
- Replay event logic
- Replay episode logic
- RDM classification definitions
- RDM thresholds unless doing a separate calibration task
- Research labels
- Interaction density weighting behavior
- Active RDM Zone / Context Range separation
- Any execution, entry, exit, BUY / SELL, or live signal behavior

The optimization pass must preserve outputs unless explicitly marked as an intentional calibration.

## Priority Order

### Priority 1: Episode Research Indexing

Implement first:

- Pre-index historical rows by timestamp and row id.
- Replace repeated future-horizon dataframe scans with binary search.
- Keep output comparison tests.

Expected speedup:

- 2x to 5x for episode research.

Why first:

- It is the largest measured bottleneck: 23.89s out of 24.55s.

### Priority 2: RDM Per-Case Cache

Implement second:

- Build `live_by_case` once.
- Reuse for interaction core, density, and true lifecycle.
- Avoid repeated dataframe group/filter work.

Expected speedup:

- 20% to 40% for RDM calculator.

Why second:

- Low-risk structural improvement.

### Priority 3: Interaction Core / Density Shared Masks

Implement third:

- Compute interaction masks and density weights once per case.
- Reuse across core geometry and density map.

Expected speedup:

- 15% to 30% for RDM calculator.

Risk:

- Medium; requires careful field-by-field output diff.

### Priority 4: Optional Validation Write Modes

Implement fourth:

- Add optional `--no-write` or `--profile-only` mode for diagnostics.
- Default must still write all files.

Expected speedup:

- Saves around 1-2 seconds on current sample.
- More useful on larger replay windows.

Risk:

- Low.

### Priority 5: Vectorization

Implement after output diff harness exists.

Expected speedup:

- Moderate to high on larger windows.

Risk:

- Medium to high if done broadly.

## High-Risk Optimizations

Avoid for now:

- Rewriting research logic around a new dataframe model.
- Replacing pandas calculations wholesale.
- Changing thresholds while optimizing.
- Changing interaction density weighting.
- Changing core compression logic.
- Parallel execution without deterministic output checks.
- Streaming partial outputs while modifying lifecycle state.

These can introduce silent research drift.

## Optional Future Migration

### Parquet

Potential benefits:

- Faster read/write than CSV.
- Better typed columns.
- Smaller files.

Use later for:

- `historical_observation_rows`
- RDM output tables
- research logs

Risk:

- Medium. Current workflow and dashboard expect CSV.

Recommended approach:

- Add Parquet as optional cache, not replacement.

### DuckDB

Potential benefits:

- Fast SQL over large historical rows.
- Efficient time-window queries.
- Good for multi-day / 10-day replay windows.

Use later for:

- Future horizon lookup
- Per-case window extraction
- Density bucket aggregation

Risk:

- Medium. Adds dependency and a new query layer.

Recommended approach:

- Prototype research-only after current pandas indexing optimization.

## Safest First Implementation

First implementation should be:

Episode Research Index Cache.

Scope:

- `tools/analyze_phase1b_episode_research.py`
- Build timestamp arrays once after `prepare_rows`.
- Use cached arrays for:
  - nearest close at or after target time
  - future movement windows
  - day-end close
- Add output diff validation against current generated research log.

Expected result:

- Biggest speedup with limited behavioral risk.

## Validation Required Before Any Optimization Is Accepted

For each optimization:

1. Run baseline before change.
2. Run optimized version.
3. Compare key CSV outputs.
4. Confirm row counts unchanged.
5. Confirm classification counts unchanged.
6. Confirm RDM state counts unchanged if RDM code touched.
7. Confirm no scoring files changed.
8. Confirm no Dashboard V2 scoring changes.

Rules remain:

- Diagnostics / optimization only
- No Phase 2
- No execution
- No entries
- No live signals
- No trading logic
- No Dashboard V2 scoring changes

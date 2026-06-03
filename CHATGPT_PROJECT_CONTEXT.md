# ChatGPT Project Context

Current stable checkpoint:

`PHASE1B_RDM_VISUALIZATION_STABLE`

Commit:

`f818d5f`

Status:

- Research only
- Observation only
- No Phase 2
- No execution
- No entries
- No live signals
- No scoring changes
- No Dashboard V2 scoring changes
- Mechanics-first
- Cases reference-only

## Latest Stable Work

### Preparation Watch Fix

- Research coverage expanded from `93` rows to `634` rows.
- Current replay / research coverage: `2026-05-25 -> 2026-06-01`.
- Preparation candidates: `338`.
- Research coverage is now `100%` across the replay episode set.

### RDM Coverage Fix

- RDM coverage increased from `35.48%` to `100%`.
- `634 / 634` Dashboard V2 episodes are mapped.
- The previous `None` / `N/A` coverage issue for mapped RDM fields is resolved.

### Dashboard Improvements

- Show All controls added.
- Row limit controls added.
- Date filters added.
- Sort order controls added.
- Preparation Watch supports multi-day research rows.
- Dashboard V2 Research Mapping panels support multi-day rows across:
  - PREPARATION
  - EXPANSION
  - REVERSAL
  - COMPARISON
  - HYPOTHESIS

### Timezone Support

- Algeria timezone display support added: `UTC+1`.
- UTC display remains available.
- This is display-only.
- Stored timestamps, replay data, research data, and calculations remain unchanged.

### RDM Mapping Fix

- `resistance_live` mapping added.
- Dashboard RDM fields now map to regenerated full research / RDM coverage.

### RDM Price Overlay

New dashboard component:

`RDM Price Overlay - Research Only`

Uses existing fields only:

- Formation Range
- Active Core
- Interaction Density Band
- Birth Price

Display:

- Absolute BTC price axis
- Nested horizontal price bands
- Birth price reference line
- Reference table with exact lower / upper / width values
- Core / Formation ratio
- Density / Formation ratio

No calculations were changed.

## Important RDM Visualization Discovery

Formation Range
!=
Active RDM Zone
!=
Interaction Density

Current interpretation:

- Formation = Context
- Active Core = Operational Zone
- Density = Interaction Heart

Binance comparison observation:

Active Core and Density Band appear to match the real market zone better than the full Formation Range.

This is an observation only. It is not a signal and not a trading rule.

## Episode 622 Validation

Episode:

- `episode_id`: `622`
- `case_id`: `CASE_00622`
- `episode_start_time_utc`: `2026-06-01 08:42:27`
- Algeria time: `2026-06-01 09:42:27`

Birth Price:

`72698.42`

Formation:

- Lower: `72612.24`
- Upper: `72864.36`
- Width: `252.12`

Active Core:

- Lower: `72787.66`
- Upper: `72850.70`
- Width: `63.03`

Density Band:

- Lower: `72823.68`
- Upper: `72832.69`
- Width: `9.00`

Ratios:

- Core / Formation: `0.2500`
- Density / Formation: `0.0357`

## What Did Not Change

- RDM formulas
- Dashboard scoring
- Dashboard V2 scoring
- Replay generation
- Research logic
- Downloads
- Binance pulls
- Live execution
- Signal logic

## RDM V1.6 — Completed Series

### V1.6-A Numerical Foundation

Status: COMPLETED

- 42 new `rdm_v16_*` columns
- Birth / Current / Live / Final metrics for all structural families

### V1.6-B1 through B7.7 — Attacker and Exposure Physics

Status: COMPLETED

Key validated finding:

```
sigma_at_return × zone_penetration_depth ≈ omega_stress_area
r = 0.9935
```

Omega is the primary Deep Structural Exposure variable.

Structural engagement chain:

```
Force → sigma_barre filter → Penetration → Omega → mechanical_family → Growth or Damage
```

sigma_barre is driven by structural memory (reclaim_history, mechanical_memory_score) — NOT by force.

Surface Damage hypothesis (B7.6-E/F): REJECTED. Zero-omega damage is time-based temporal decay.

### Downloader Stability Fix

Status: COMPLETED

- Timeout: 120s -> 150s
- Retries: 10 -> 15
- Extended backoff, jitter, WinError 10060 detection
- Session retry tracking, resume deduplication
- New CLI: `--max-retries`, `--timeout`

## 3-Tier Hybrid Downloader

Status: COMPLETED

Tier 1 (local cache) + Tier 2 (Binance ZIP) + Tier 3 (API fallback).

Priority per UTC day:

1. archives/{SYMBOL}/raw-trades/{date}.csv -> CACHE HIT (zero network)
2. data.binance.vision ZIP (date >= 2 days old) -> ZIP HIT -> save to cache
3. Binance aggTrades API -> API DOWNLOAD -> save to cache

Key: Binance ZIP timestamps are microseconds. Converted to milliseconds (// 1000) inside download_day_from_binance_zip.

Validated: BTCUSDT 2026-05-25 — 542,386 trades, 7.7 MB, 2.7 sec via ZIP.

New CLI: --no-local-cache, --no-zip

Standard command:

python tools/generate_binance_historical_replay.py --start "2026-05-20 00:00:00" --end "2026-06-02 00:00:00" --symbol BTCUSDT --row-size 500

Use --slow-mode only for recent-date API fallback on unstable networks, not for historical downloads.

## Phase 1 Synthesis Engine

Status: COMPLETED

File:    research/synthesis_engine.py (NEW)
Output:  research/zone_synthesis.csv (276 rows, 13 columns)

Phase 1 is now structurally coherent. The Synthesis Engine connects all
Phase 1 layers (Statistical Engine, Dashboard V2, RDM B1-B11) into one
MarketInterpretation per zone case:

    context | structure | engagement | flow | prediction | coherence | interpretation

Architecture (6 components, minimal professional version):
    Taxonomy Register (role + scope per field)
    Bundle Assembler (B10 + B11 + episode context)
    Priority Rules (STRUCTURAL > CURRENT, STRUCTURE > CONTEXT)
    Genuine Conflict Check (binary flag)
    3-Gate Synthesis Check
    4-Level Coherence Label (STRONG / MODERATE / WEAK / INSUFFICIENT)

Example: "TERMINAL zone under opposing flow - failure confirmed."
Example: "STRENGTHENING zone after 3 visits - hold confirmed."

## Current Active Phase

PHASE 1B+ Research Expansion

Current checkpoint: PHASE1B_SYNTHESIS_ENGINE_STABLE

Prior checkpoints:
- PHASE1B_HYBRID_DOWNLOADER_STABLE
- PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE
- PHASE1B_DOWNLOAD_STABILITY_FIX_STABLE

Rules preserved:
- No scoring changes
- No lifecycle changes
- No Dashboard V2 scoring impact
- No RDM formula changes
- No replay formula changes
- No Phase 2 / No execution / No entries / No live signals

Next task: 45-60 day data collection, then B12 prediction validation.

Do not advance to Phase 2.

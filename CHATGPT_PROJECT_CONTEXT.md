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

## Next Step

Validate:

- Formation
- Active Core
- Density Band

Across multiple episodes.

Then return to:

- Prepare Zone TRUE > 4
- Continue RDM Market Mechanics:
  - Rigidity
  - Fatigue
  - Recovery
  - Attacker behavior

Do not advance to Phase 2.

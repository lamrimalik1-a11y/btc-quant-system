# BTC Quant Project Overview

## System Philosophy

This repository is currently a Phase 1B / Phase 1B+ observation and research system.

The system studies market rarity, abnormality, confluence, replay behavior, and
research-only mechanical interpretations of market zones. It is not a trading bot.
It does not create entries, exits, BUY / SELL signals, execution actions, or live
trading decisions.

Core philosophy:

- Observe before deciding.
- Preserve replay compatibility.
- Keep Dashboard V2 locked.
- Keep research modules separate from live calculations and scoring.
- Treat all hypotheses as unproven until validated across larger data windows.
- Mechanics-first: variables -> family -> subtype -> state -> case examples.
- Cases are reference-only, never hardcoded classification rules.
- Phase 1 must be coherent before any backtesting begins.

## Phase 1 Is Now Structurally Coherent

As of PHASE1B_SYNTHESIS_ENGINE_STABLE, the system produces a single unified
interpretation per zone case instead of 100+ isolated fields.

The Phase 1 Synthesis Engine connects:

    Statistical Engine (9 Dashboard V2 layers)
    RDM B1-B11 (structural zone mechanics)
    Preparation Research
    Zone / Field Lifecycle

...into one MarketInterpretation object:

    context | structure | engagement | flow | prediction | coherence | interpretation

## Global Architecture

```
STRATUM 1 — OBSERVATION (real-time, per bar)
    core/row_builder.py, engines/phase1_engine.py
    OHLCV, delta, velocity, volume, spread, RVI

STRATUM 2 — CONTEXT (statistical significance, per bar/session)
    core/statistics.py, engines/statistics_engine.py
    Distribution, Gaussian, ZScores, Tail, Extreme Events
    Volatility Regime, Velocity, Delta, Dashboard V2

STRATUM 3 — STRUCTURE (zone mechanics, multi-session)
    context_memory.py (ZoneLifecycleMemory, FieldLifecycleMemory)
    research/zone_mechanics_calculator.py (RDM B1-B11)
    Zone geometry, mechanical state, omega, sigma_barre

STRATUM 4 — ENGAGEMENT (zone interaction, per visit)
    RDM B8: Zone Visit Timeline
    RDM B9: Zone Health Evolution
    RDM B10: Structural Trajectory Classification
    RDM B11: Structural Engagement Prediction

STRATUM 5 — SYNTHESIS (unified interpretation, per zone case)
    research/synthesis_engine.py
    MarketInterpretation -> research/zone_synthesis.csv

STRATUM 6 — VALIDATION (prediction accuracy, future)
    B12: Prediction Validation (not yet implemented)
    Requires 45-60 day data collection first
```

## Important Files

- `research/synthesis_engine.py` — Phase 1 Synthesis Engine
- `research/zone_mechanics_calculator.py` — RDM B1-B11 + Synthesis
- `research/zone_synthesis.csv` — MarketInterpretation output
- `tools/generate_binance_historical_replay.py` — 3-tier hybrid downloader
- `core/statistics.py` — Full statistical engine
- `context_memory.py` — Zone / Field lifecycle memory
- `dashboard_app.py` — Observation dashboard

## Current Checkpoint

PHASE1B_SYNTHESIS_ENGINE_STABLE

## Hard Rules

Do not advance to Phase 2.

Do not add:
- Execution / Entries / Exits
- BUY / SELL logic
- Live signals
- Scoring changes
- Dashboard V2 scoring changes
- RDM formula changes
- Lifecycle logic changes
- Replay formula changes

All current work remains research-only.
The next task is data collection, then B12 backtesting validation.

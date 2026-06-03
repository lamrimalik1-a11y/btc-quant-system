# BTC Quant Project Overview

## System Philosophy

This repository is currently a Phase 1B / Phase 1B+ observation and research system.

The system studies market rarity, abnormality, confluence, replay behavior, and research-only mechanical interpretations of market zones. It is not a trading bot. It does not create entries, exits, BUY / SELL signals, execution actions, or live trading decisions.

Core philosophy:

- Observe before deciding.
- Preserve replay compatibility.
- Keep Dashboard V2 locked unless explicitly calibrating research-only outputs.
- Keep research modules separate from live calculations and scoring.
- Treat all hypotheses as unproven until validated across larger replay windows.
- Mechanics-first classification: variables -> family -> subtype -> state -> case examples.
- Cases are reference-only, never hardcoded classification rules.

## Global Architecture

Major areas:

- Dashboard V2 statistical context layer
- Historical replay generation (3-tier hybrid downloader)
- Phase 1B Episode Research Assistant
- Research dashboard / observation UI
- Dashboard V2 research mapping layer
- Context memory and lifecycle memory
- RDM Market Mechanics research layer (V1.1 through V1.6-B7.7)
- Streamlit dashboard for replay and research observation

Important files:

- `tools/generate_binance_historical_replay.py` — 3-tier downloader (local cache / ZIP / API)
- `dashboard_app.py`
- `dashboard/research_mapping.py`
- `dashboard/overlay_renderer.py`
- `research/zone_mechanics_calculator.py`
- `tools/analyze_phase1b_episode_research.py`
- `context_memory.py`
- `MASTER_STATUS.md`

## Current Phase

PHASE 1B+ Research Expansion

Current focus:

- Historical dataset rebuild using new hybrid downloader
- RDM V1.6 development (series A through B7.7 complete, next steps pending full dataset)

## Current Checkpoint

PHASE1B_HYBRID_DOWNLOADER_STABLE

Prior:

- PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE
- PHASE1B_DOWNLOAD_STABILITY_FIX_STABLE
- PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK

## Hard Rules

Do not advance to Phase 2.

Do not add:

- Execution
- Entries / Exits
- BUY / SELL logic
- Live signals
- Decision engine
- Risk engine
- Scoring changes
- Dashboard V2 scoring changes
- RDM formula changes
- Lifecycle logic changes
- Replay formula changes

All current work remains research-only.

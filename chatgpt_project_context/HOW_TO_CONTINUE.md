# How To Continue In A New ChatGPT Project

## What To Upload

Upload these files:
- chatgpt_project_context/PROJECT_OVERVIEW.md
- chatgpt_project_context/MASTER_STATUS_COMPACT.md
- chatgpt_project_context/RDM_MARKET_MECHANICS_STATUS.md
- chatgpt_project_context/HOW_TO_CONTINUE.md
- chatgpt_project_context/RUN_COMMANDS.md
- chatgpt_project_context/CURRENT_CHECKPOINT.md

Recommended additional source files:
- MASTER_STATUS.md
- research/synthesis_engine.py
- research/zone_mechanics_calculator.py
- tools/generate_binance_historical_replay.py
- core/statistics.py
- context_memory.py

## First Message

```text
You are working on my BTC Quant repo in PHASE 1B+ Research Expansion.
Current checkpoint: PHASE1B_STREAMING_REPLAY_STABLE.

Rules:
- Research only, no Phase 2, no execution, no entries, no live signals
- No scoring changes, no RDM formula changes, no lifecycle changes

Current state:
- tools/generate_binance_historical_replay.py has a new, additive,
  opt-in --stream flag: a bounded-memory rebuild path for long
  continuous multi-month windows (target: 2026-02-01 -> 2026-06-06,
  126 days, zero window seams).
- --stream Stages 1-3 (CLI flag + streaming reader + streaming
  consumer with persistent tick_buffer / continuous StatisticsEngine /
  warmup deque / incremental CSV writes / row-count invariants) are
  implemented and additive-verified (compiles, 0 deletions, old path
  unchanged).
- --stream run on April reproduced the known-good April B12v2 numbers
  (808 zone cases, r=0.9966, 97.8% accuracy) -- metric-level verified.
  The formal byte-identical sha256 comparison vs the in-memory path was
  not completed (the in-memory run OOMed on this 24GB machine during
  that test -- cause unconfirmed, see CURRENT_CHECKPOINT.md).
- **--stream is now REQUIRED on this machine for all replay rebuilds,
  including single months** -- the old in-memory path is unreliable
  here. Always snapshot outputs/ before any run that writes to it (see
  RUN_COMMANDS.md "Pre-run snapshot rule").
- All datasets from generate_binance_historical_replay.py (in-memory or
  --stream) are REPLAY_AGGTRADE (500 aggTrades/row), distinct from LIVE
  (500 raw @trade/row). core/live_b12_validation.py (B12 Live
  Validation) remains active on LIVE data, unchanged.
- Synthesis Engine (research/synthesis_engine.py) still connects all
  B1-B11 outputs into one MarketInterpretation per zone case
  (research/zone_synthesis.csv). NOTE: the 276-row/12-day-archive
  figures from the prior checkpoint predate later
  March/April/May/B12v2 work -- re-check the CSV before citing counts.

Next task:
- Snapshot outputs/ (permanent rule, see RUN_COMMANDS.md)
- Run the 126-day continuous rebuild (2026-02-01 -> 2026-06-06) with
  --stream (see RUN_COMMANDS.md "Next Task: Full Continuous Window
  Rebuild")
- After that rebuild: re-run B9-B12v2 / Synthesis on the unified dataset

Key validated finding:
- Omega = sigma x penetration (r=0.9935)
- Structural engagement chain confirmed (Force -> sigma_barre -> Omega -> Outcome)
- Surface damage rejected (temporal decay formula only)
```

## Priority Workflow (next session)

### Step 0: Snapshot outputs/ and run the 126-day continuous rebuild

Snapshot `outputs/` first (permanent rule, see RUN_COMMANDS.md "Pre-run
snapshot rule"), then run the full continuous window with `--stream`
(required on this machine -- see RUN_COMMANDS.md "Next Task: Full
Continuous Window Rebuild"):

```powershell
python tools/generate_binance_historical_replay.py --start "2026-02-01 00:00:00" --end "2026-06-06 00:00:00" --symbol BTCUSDT --row-size 500 --stream
```

Pre-condition: all days in the window (plus warmup lookback) must
already be in the Tier-1 raw-trade cache -- `--stream` raises on any
missing day rather than downloading.

### Step 1: Extended Data Collection (additional days, if needed)

```powershell
python tools/generate_binance_historical_replay.py \
  --start "2026-05-01 00:00:00" \
  --end "2026-07-01 00:00:00" \
  --symbol BTCUSDT --row-size 500
```

The 3-tier downloader will:
- Use Tier 1 local cache for any days already downloaded
- Use Tier 2 Binance ZIP for older dates (2+ days)
- Use Tier 3 API only for very recent dates

Note: this non-stream command is for populating the Tier-1 cache only.
Once cached, rebuild with `--stream` (Step 0) -- the in-memory path is
unreliable on this machine.

### Step 2: Rebuild Research Dataset

```powershell
python tools/analyze_phase1b_episode_research.py --mode score4plus
python research/zone_mechanics_calculator.py
```

After 45+ days: expect 1000+ zone cases instead of 276.

### Step 3: B12 Implementation (future)

B12 = Prediction Validation:
- Compare structural_prediction from zone_synthesis.csv against actual market outcomes
- Compute accuracy per trajectory class, confidence level, regime
- Use B12 accuracy data to calibrate numeric coherence score

## What Not To Do

- Phase 2 (execution, entries, exits, BUY/SELL, live signals)
- Change Dashboard V2 scoring
- Change RDM formulas
- Change lifecycle logic
- Add new indicators before validating existing ones

## Synthesis Engine Notes

The synthesis engine is research/synthesis_engine.py.
It reads from:
    zone_structural_trajectory.csv (B10)
    zone_structural_prediction.csv (B11)
    outputs/historical_replay_dashboard_v2_episodes.csv (statistical context)

It writes to:
    research/zone_synthesis.csv (276 rows, 13 columns)

It is called automatically by zone_mechanics_calculator.py as the final step.
No separate command needed.

Postponed components (after B12):
- Numeric Coherence Score (0-100) with calibrated weights
- Redundancy Detection between correlated statistical signals
- Advanced Conflict Classification (4-type instead of binary)

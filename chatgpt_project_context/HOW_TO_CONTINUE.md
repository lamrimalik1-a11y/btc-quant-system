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
- --stream Stages 1-2 (CLI flag + streaming reader + streaming
  consumer with persistent tick_buffer / continuous StatisticsEngine /
  warmup deque / incremental CSV writes / row-count invariants) are
  implemented and additive-verified (compiles, 0 deletions, old path
  unchanged).
- --stream Stage 3 (April 2026-04-01 -> 2026-05-01 byte-identical
  sha256 equivalence test vs the old in-memory path) is PENDING --
  not yet confirmed. --stream is EXPERIMENTAL until that passes; do
  not use it for any dataset feeding B9-B12/Synthesis yet.
- Synthesis Engine (research/synthesis_engine.py) still connects all
  B1-B11 outputs into one MarketInterpretation per zone case
  (research/zone_synthesis.csv). NOTE: the 276-row/12-day-archive
  figures from the prior checkpoint predate later
  March/April/May/B12v2 work -- re-check the CSV before citing counts.

Next task:
- Confirm Stage 3 streaming equivalence (see RUN_COMMANDS.md "Stage 3
  equivalence test")
- If PASS: make --stream the default and run the 126-day continuous
  rebuild
- After that rebuild: re-run B9-B12v2 / Synthesis on the unified dataset

Key validated finding:
- Omega = sigma x penetration (r=0.9935)
- Structural engagement chain confirmed (Force -> sigma_barre -> Omega -> Outcome)
- Surface damage rejected (temporal decay formula only)
```

## Priority Workflow (next session)

### Step 0: Confirm --stream Stage 3 equivalence (PENDING)

Run the April equivalence test in RUN_COMMANDS.md ("Stage 3
equivalence test"). PASS = all 3 sha256 hash pairs
(historical_observation_rows.csv, historical_market_rows.csv,
historical_replay_dashboard_v2_episodes.csv) identical between the
old in-memory run and the --stream run. Only after PASS: proceed to
make --stream the default and run the 126-day rebuild (Step 1 below
becomes the streaming version of this command).

### Step 1: Extended Data Collection (45-60 days)

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

# Current Checkpoint

## Active Checkpoint

Checkpoint: PHASE1B_B125_DYNAMIC_TIMELINE_STABLE

What this checkpoint adds:
- B12.5 Full Post-Return Visit Timeline Engine (3 stages)
- zone_visit_timeline_dynamic.csv: 14,512 rows, 2,980 returning zones
- Dynamic state classification: SDR-led rules, 86.6% accuracy
- Physics confirmed: SDR >= 1 → 99.6% FAIL (deterministic)
- Gold tier: STRONG_HOLD → 100% HOLD (743 cases)
- ATTACKER_DOMINANT → 99.6% FAIL (528 cases)

B12.5 Three stages:
  Stage 1: Extended live_row_window by 500 post-return rows (hard cap)
           zone_live_rdm_evolution: 1.8M → 3.3M rows
  Stage 2: Built zone_visit_timeline_dynamic.csv
           14,512 post-return visits across 2,980 zones
  Stage 3: Added derivative + integral + SDR + dynamic_state
           Calibrated percentile-based thresholds from pre-return data

Dynamic state accuracy (vs B12v2 outcomes, n=2,430):
  STRONG_HOLD       → 100.0% HOLD  (n=743)
  ATTACKER_DOMINANT → 99.6%  FAIL  (n=528)
  STABLE            → 91.6%  HOLD  (n=383)
  PEAK_WARNING      → 100.0% FAIL  (n=40)
  RECOVERING        → 100.0% FAIL  (n=26)
  CRITICAL          → 100.0% FAIL  (n=8)
  DEGRADING         → 88.1%  FAIL  (n=42)
  PROBABLE_HOLD     → 56.5%  FAIL  (n=657) ← needs refinement
  Overall accuracy: 86.6% (was 74.4% before calibration)

Mathematical layers per visit:
  first_derivative  = health(k) - health(k-1)
  second_derivative = first_derivative(k) - first_derivative(k-1)
  slope_short       = regression slope over last 2 visits
  slope_medium      = regression slope over last 3-5 visits
  zone_integral     = I(k-1) * 0.98 + health(k)
  attacker_integral = I(k-1) * 0.98 + attacker_force(k)
  SDR               = attacker_integral / zone_integral

Calibrated thresholds (percentile-based, from pre-return data):
  slope_pos=3.894, slope_neg=-1.248,
  integral_high=410.68, integral_low=76.85, sdr_high=1.079

Next steps:
  - Rename PROBABLE_HOLD to neutral label (needs more live data first)
  - Collect live aggTrade data (stream switched to @aggTrade)
  - Validate dynamic_state on live data vs replay
  - Build B13 Dynamic State Engine (Markov-ready)

Prior checkpoints (preserved):
  - PHASE1B_UNIFIED_ARCHIVE_STABLE
  - PHASE1B_STREAMING_REPLAY_STABLE
  - PHASE1B_B12_LIVE_VALIDATION
  - PHASE1B_SYNTHESIS_ENGINE_STABLE

---

## Previous Active Checkpoint

Checkpoint:

PHASE1B_UNIFIED_ARCHIVE_STABLE

Status:

- Research only
- Observation only
- No Phase 2
- No execution
- No entries
- No live signals
- No scoring changes
- No Dashboard V2 scoring changes
- No RDM formula changes
- No lifecycle changes
- No replay formula changes
- PERMANENT RULE: always take a snapshot/backup of outputs/ BEFORE any
  run that writes to it (especially with --overwrite). See
  RUN_COMMANDS.md "Pre-run snapshot rule".

---

## What this checkpoint adds

- Unified continuous archive: Feb 01 → Jun 05 2026 (126 days, zero seams)
- 4,859 zones (was 808 April-only / 1,219 March-only)
- B12v2 validation: 98.8% accuracy, lift +41.4%, evaluable 2,441
- HOLD F1: 0.989 / FAIL F1: 0.986
- Physics: sigma x penetration r=0.9991 (n=2,977) — strongest yet
- Zero leakage, zero Phase 1 code changes
- Streaming replay (--stream) required on this machine (24 GB RAM)

## Key findings

- STRENGTHENING trajectory: 100% accuracy (n=1,372)
- TERMINAL trajectory: 100% accuracy (n=748)
- All 10 False HOLDs came from STABLE trajectory only
- STABLE trajectory remains the weak point (44.4% hold rate)
- Fully prospective test (no prior breakdown): 98.2%, lift +15.5%

## Pipeline that produced this

1. python tools\generate_binance_historical_replay.py
     --start "2026-02-01 00:00:00" --end "2026-06-06 00:00:00"
     --symbol BTCUSDT --row-size 500 --no-zip --overwrite --stream
2. Build unified episodes from existing observation rows (one-liner)
3. python -m tools.analyze_phase1b_episode_research
4. python research/zone_mechanics_calculator.py
5. python -m research.run_b12v2_validation

## Next steps

- Extend archive to a second independent period (regime generalization)
- Investigate STABLE trajectory false HOLDs
- Calibrate B11 thresholds using B12v2 precision/recall data
- Build B12.5 (full post-return visit timeline)
- Build B13 (dynamic state updater)

## Prior checkpoints (preserved)

- PHASE1B_STREAMING_REPLAY_STABLE
- PHASE1B_B12_LIVE_VALIDATION
- PHASE1B_SYNTHESIS_ENGINE_STABLE
- PHASE1B_RDM_MARKET_MECHANICS_V1_5

(Full checkpoint history is in `git log` and prior research reports.)

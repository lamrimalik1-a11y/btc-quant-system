# Current Checkpoint

## Active Checkpoint

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

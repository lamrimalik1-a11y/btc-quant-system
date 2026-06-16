# Current Checkpoint

## Active Checkpoint

Checkpoint:

PHASE1B_STREAMING_REPLAY_STABLE

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

## Streaming Replay Refactor (`--stream`) — now REQUIRED

`tools/generate_binance_historical_replay.py` has an additive
`--stream` flag: a bounded-memory rebuild path for long, continuous,
multi-month windows.

Delivered in 3 verifiable stages, each additive-only (0 deletions at
every stage, confirmed via `git diff --stat`):

- **Stage 1** — `--stream` CLI flag + `stream_cached_day_trades()`
  reader. Reads the Tier-1 raw-trade cache
  (`archives/{SYMBOL}/raw-trades/{date}.csv`) one UTC day at a time ->
  O(one day) memory instead of O(window).
- **Stage 2** — `run_streaming_pipeline()`, the streaming consumer:
  persistent `tick_buffer` across day-file boundaries (flushed only at
  `row_size`, never at a day seam), ONE continuous `StatisticsEngine` /
  `RenkoEngine` / observation state for the whole window, warmup primed
  via `deque(maxlen=500)`, incremental CSV writes, row-count invariant
  assertions (`rows == ceil(target_trades/500)`, non-final rows have
  `tick_count == 500`).
- **Stage 3 spec** — byte-identical sha256 equivalence test for April
  [2026-04-01 -> 2026-05-01] vs the old in-memory path (commands in
  RUN_COMMANDS.md).

ZERO changes to: `build_trade_row()`, `StatisticsEngine`,
`RenkoEngine`, `agg_trade_to_tick`, `build_observation_row`,
`reset_observation_state`, `calculate_adaptive_window`,
`update_history`, and all B1-B11 / Synthesis / RDM / scoring /
lifecycle code. The default (no `--stream`) CLI path is byte-for-byte
identical to before the refactor.

### Verification result: metric-level reproduction (April)

`--stream` run on April reproduced the known-good April B12v2 research
numbers:

- 808 zone cases
- physics correlation r = 0.9966
- B12v2 accuracy = 97.8%

These match the prior in-memory April rebuild (post rigidity-fallback
fix) exactly. This is strong evidence that `--stream` is computing the
same thing as the in-memory path at the research-output level.

**Important caveat**: the formal Stage 3 *byte-identical sha256*
comparison (`historical_observation_rows.csv`,
`historical_market_rows.csv`,
`historical_replay_dashboard_v2_episodes.csv`, file-for-file identical)
has NOT been separately run/confirmed. It may not be practically
runnable on this machine going forward (see OOM finding below — the
in-memory side of that comparison now OOMs on April). Metric-level
reproduction is the available evidence and is treated as sufficient to
proceed, but is not the same guarantee as a byte-identical hash match.

### NEW FINDING: in-memory path OOMs on April (24 GB machine)

The in-memory path OOMed on April on this machine during the Stage 3
equivalence test (~25.5M trades). The cause is unconfirmed — possibly
the machine had less free RAM available at that moment (other
processes, prior run residual memory). Do not attribute this to the
Stage 1+2 code changes. Practical consequence:

- **`--stream` is required going forward on this machine, regardless of
  cause, since it eliminates the OOM risk entirely by design — for ANY
  window, including single months.**
- All future replay rebuilds (April-sized or larger) MUST use
  `--stream`.
- The in-memory path remains in the code (byte-for-byte unchanged,
  per the additive-only guarantee) but should be treated as
  unreliable on this hardware until/unless memory headroom is confirmed.
- The earlier 126-day (2026-02-01 -> 2026-06-06) in-memory OOM estimate
  (~60-75 GB) remains valid and unchanged by this finding — it was
  already far beyond the 24GB limit regardless of cause.

---

## Next Task: Full Continuous Window Rebuild

Target: single continuous, zero-seam rebuild covering
2026-02-01 -> 2026-06-06 (126 days), using `--stream`.

```powershell
python tools/generate_binance_historical_replay.py --start "2026-02-01 00:00:00" --end "2026-06-06 00:00:00" --symbol BTCUSDT --row-size 500 --stream
```

Pre-conditions:
- All days in [2026-02-01 - WARMUP_LOOKBACK, 2026-06-06] must already be
  present in the Tier-1 raw-trade cache (`--stream` raises on any
  missing day rather than downloading).
- Take an outputs/ snapshot first (permanent rule, see
  RUN_COMMANDS.md).

After the rebuild: re-run B9-B12v2 / Synthesis on the unified dataset
(all months on current code, addressing the previously-flagged
cross-month code-version inconsistency).

---

## B12 Live Validation — still active

`core/live_b12_validation.py` (B12 Live Validation) remains active from
the prior checkpoint. No changes made to it in this checkpoint. Live
validation continues to run against LIVE (raw `@trade`) data, separate
from the REPLAY_AGGTRADE research pipeline below.

---

## Research Data Labeling: REPLAY_AGGTRADE

All research datasets produced by
`tools/generate_binance_historical_replay.py` (in-memory or
`--stream`) are built from Binance **aggTrades** (500
aggTrades/row) — label these datasets **REPLAY_AGGTRADE** to
distinguish them from LIVE, which uses 500 raw `@trade`
executions/row. This labeling distinction was established earlier
(the LIVE/REPLAY unit parity gap) and is NOT affected by the
streaming refactor — `--stream` produces REPLAY_AGGTRADE data, same as
the in-memory path.

---

## Prior Checkpoints (preserved)

History since the last documented checkpoint in this file
(PHASE1B_SYNTHESIS_ENGINE_STABLE) includes several checkpoints not yet
written up here in detail — see `git log` and
`research/feb2026_*report*.md` / `EXTREME_EVENT_ARCHITECTURE_REPORT.md`
for specifics:

- PHASE1B_LIVE_ZONE_ENGINE_STABLE
- PHASE1B_RIGIDITY_FALLBACK_FIX_STABLE
- PHASE1B March/April/May generalization + Formation Model + Active
  Core B12v2
- PHASE1B_STABLE_CHECKPOINT
- PHASE1B_SYNTHESIS_ENGINE_STABLE
- PHASE1B_HYBRID_DOWNLOADER_STABLE
- PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE
- PHASE1B_DOWNLOAD_STABILITY_FIX_STABLE
- PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK
- PHASE1B_RDM_VISUALIZATION_STABLE
- PHASE1B_RDM_MARKET_MECHANICS_V1_5

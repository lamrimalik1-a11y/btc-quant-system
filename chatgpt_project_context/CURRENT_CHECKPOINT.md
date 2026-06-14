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

---

## Streaming Replay Refactor (`--stream`)

`tools/generate_binance_historical_replay.py` gained an additive,
opt-in `--stream` flag: a bounded-memory rebuild path for long,
continuous, multi-month windows (target use case: a single-pass
2026-02-01 -> 2026-06-06 rebuild without window seams).

Delivered in 3 verifiable stages, each additive-only (0 deletions at
every stage, confirmed via `git diff --stat`):

- **Stage 1** — `--stream` CLI flag + `stream_cached_day_trades()`
  reader. Reads the Tier-1 raw-trade cache (`archives/{SYMBOL}/raw-trades/{date}.csv`)
  one UTC day at a time -> O(one day) memory instead of O(window).
  Reuses `try_load_raw_trade_cache` / `_verify_raw_trades` /
  `_iter_utc_days` / `_day_ms_range` unchanged. A Stage-2 placeholder
  guard initially made `--stream` exit immediately so no half-built
  path could emit output.
- **Stage 2** — `run_streaming_pipeline()`, the streaming consumer:
  - ONE persistent `tick_buffer` across day-file boundaries — flushed
    only when `len(tick_buffer) == row_size` (500), never at a day
    seam. A row can legitimately span two day-files.
  - ONE continuous `StatisticsEngine` / `RenkoEngine` / observation
    state for the whole window (`reset_observation_state()` called
    exactly once, at the start).
  - Warmup primed via `deque(maxlen=WARMUP_TARGET_ROWS)` (500 rows),
    each primed through `process_historical_row`; `tick_buffer` is
    reset at the warmup -> target boundary (matches the old
    two-separate-calls behaviour, so target row 1 starts at the first
    target trade).
  - Incremental CSV writes for `historical_market_rows.csv` and
    `historical_observation_rows.csv` via `csv.DictWriter` opened
    once, row-by-row — no in-memory accumulation of all rows.
  - Trailing partial row (< row_size ticks) handled at end of stream,
    matching `build_historical_rows`.
  - **Row-count invariant assertions** (anti-seam proof): raises
    `AssertionError` unless `rows_written == ceil(target_trades /
    row_size)` AND every non-final row has `tick_count == row_size`.
  - V1/V2 replay events + episodes: re-reads the just-written
    observation CSV via `pd.read_csv`, then calls the UNCHANGED
    `build_replay_observation` / `build_replay_observation_v2` /
    `write_dict_rows`, followed by the existing (unchanged)
    `archive_historical_outputs` step.
  - `--save-raw` + `--stream` together raise `SystemExit` (out of
    scope for this refactor).
- **Stage 3** — byte-identical equivalence test SPEC for April
  [2026-04-01 -> 2026-05-01]: run the OLD in-memory path (no
  `--stream`) and the NEW `--stream` path into separate output copies,
  then sha256-compare `historical_observation_rows.csv`,
  `historical_market_rows.csv`, and
  `historical_replay_dashboard_v2_episodes.csv`. Exact commands in
  `RUN_COMMANDS.md`.

ZERO changes to: `build_trade_row()`, `StatisticsEngine`,
`RenkoEngine`, `agg_trade_to_tick`, `build_observation_row`,
`reset_observation_state`, `calculate_adaptive_window`,
`update_history`, and all B1-B11 / Synthesis / RDM / scoring /
lifecycle code. The default (no `--stream`) CLI path is byte-for-byte
identical to before the refactor (0 deletions across all 3 stages).

### Outstanding before `--stream` is trusted for research data

- **Stage 3 equivalence result is PENDING** — Lamri runs the April
  sha256 comparison. Until that comes back PASS (all 3 hash pairs
  identical), `--stream` is experimental and must NOT be used to
  produce any dataset that feeds B9-B12 / Synthesis / research logs.
- If only `historical_replay_dashboard_v2_episodes.csv` mismatches
  while the market-rows / observation-rows CSVs match: the suspected
  cause is the `pd.read_csv` read-back vs `pd.DataFrame(list_of_dicts)`
  dtype difference — specifically boolean fields becoming the truthy
  string `"False"` after a CSV round trip, empty-string vs NaN, or
  int -> float promotion on a blank cell. Fix (if needed) would be in
  the `pd.read_csv(...)` call inside `run_streaming_pipeline`, NOT in
  `build_replay_observation_v2`.
- Only after Stage 3 passes: discuss making `--stream` the default and
  running the full 126-day window.

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

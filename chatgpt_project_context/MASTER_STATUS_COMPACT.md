# Master Status Compact

## Current Stable Status

Current checkpoint: PHASE1B_B125_AUTOTRIGGER_STABLE

B12.5 auto-triggers on every new zone detection:
  - Wired into core/live_rdm.py inside compute_live_rdm_for_case()
  - Fires immediately after _persist_record(); wrapped in try/except: pass
  - Runtime confirmed <2s; failure never blocks main live pipeline

Dashboard filter: calendar-day selector (Today / Yesterday / Last 3 days)
  - Default: Today; boundary = Algeria midnight converted to UTC
  - Auto-refresh: cache TTL 10s, fragment run_every 15s (was 30s/60s)
  - New zones appear on dashboard within 15s, zero manual action

Both dashboards:
  streamlit run dashboard_app.py
  streamlit run dashboard_live_zones.py --server.port 8502

Live stream: python -m engines.stream_manager
  (prevent sleep first: powercfg /change standby-timeout-ac 0)

Next: run LIVE stream continuously → accumulate post-return visits →
validate LIVE vs REPLAY dynamic_state → B13.

---

## Prior Stable Status (PHASE1B_B125_LIVE_DASHBOARD_STABLE)

Current checkpoint: PHASE1B_B125_LIVE_DASHBOARD_STABLE

B12.5 wired into LIVE pipeline:
  - run_zone_visit_timeline_dynamic_live + add_dynamic_layers_to_timeline_live
  - Fixed REPLAY-calibrated thresholds (LIVE/REPLAY comparability guaranteed)
  - research/live_zone_visit_timeline_dynamic.csv: 50 zones, 8 post-return visits
  - 3 days live data (Jun 17-19), stream not yet continuous

New dashboard: dashboard_live_zones.py (port 8502)
  - Density Bands as primary decision zone; Active Core = context only
  - Prediction reasoning per card (reuses _classify_dynamic_state rules)
  - Expandable "More Information": full visit history + outcome tracking
  - Algeria timezone throughout, auto-refresh every 60s

---

## Prior Stable Status (PHASE1B_B125_DYNAMIC_TIMELINE_STABLE)

Current checkpoint: PHASE1B_B125_DYNAMIC_TIMELINE_STABLE

B12.5 complete (3 stages):
  - 14,512 post-return visits, 2,980 zones
  - SDR-led dynamic state: 86.6% accuracy
  - STRONG_HOLD=100% HOLD, ATTACKER_DOMINANT=99.6% FAIL
  - SDR >= 1 → 99.6% FAIL (near-deterministic)
  - Mathematical layers: derivative + integral + SDR per visit
  - Thresholds: percentile-calibrated from pre-return data

Live stream: switched to @aggTrade (matches REPLAY unit).
Archive: Feb-Jun 2026, 4,859 zones, B12v2 98.8% accuracy, r=0.9991.
Streaming replay (--stream) required on this machine (24 GB RAM).

---

## Prior Stable Status (PHASE1B_UNIFIED_ARCHIVE_STABLE)

Current checkpoint: PHASE1B_UNIFIED_ARCHIVE_STABLE

Archive: Feb 01 → Jun 05 2026, continuous (zero seams), 4,859 zones.
B12v2: 98.8% accuracy, HOLD F1=0.989, FAIL F1=0.986, evaluable=2,441.
Physics: r=0.9991 (sigma x penetration, n=2,977) — strongest yet.
Streaming replay (--stream) required on this machine (24 GB RAM).

Weak point identified: STABLE trajectory (44.4% hold rate, all 10 false
HOLDs). All other trajectories: STRENGTHENING/TERMINAL = 100% accuracy.

Next: regime generalization (second independent period) + B12.5 + B13.

Prior checkpoints (not all individually detailed here — see git log /
CURRENT_CHECKPOINT.md "Prior Checkpoints"):
- PHASE1B_STREAMING_REPLAY_STABLE
- PHASE1B_B12_LIVE_VALIDATION
- PHASE1B_LIVE_ZONE_ENGINE_STABLE
- PHASE1B_RIGIDITY_FALLBACK_FIX_STABLE
- PHASE1B March/April/May generalization + Formation Model + Active Core B12v2
- PHASE1B_STABLE_CHECKPOINT
- PHASE1B_SYNTHESIS_ENGINE_STABLE
- PHASE1B_HYBRID_DOWNLOADER_STABLE
- PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE
- PHASE1B_DOWNLOAD_STABILITY_FIX_STABLE

## Streaming Replay Refactor (`--stream`)

`tools/generate_binance_historical_replay.py`:
- New flag `--stream` (default off; old path byte-for-byte unchanged
  when absent).
- New reader `stream_cached_day_trades()` — yields aggTrades from the
  Tier-1 raw-trade cache one UTC day at a time (O(one day) memory).
- New consumer `run_streaming_pipeline()`:
  - Persistent `tick_buffer` across day-file boundaries, flushed only
    at `row_size` (500 ticks) — never at a day seam.
  - ONE continuous `StatisticsEngine` / `RenkoEngine` / observation
    state for the whole window.
  - Warmup primed via `deque(maxlen=500)`, tick_buffer reset at the
    warmup -> target boundary.
  - Incremental CSV writes for market-rows and observation-rows.
  - Row-count invariant assertions (`rows == ceil(target_trades/500)`,
    non-final rows have `tick_count == 500`) — raises on violation.
  - V1/V2 replay events/episodes + archiving reuse the existing
    (unchanged) functions, fed by re-reading the observation CSV.
- `--save-raw` is not supported together with `--stream`.

STATUS: Stages 1-3 implemented and additive-verified (compiles, 0
deletions, old path unchanged). `--stream` run on April reproduced the
known-good April B12v2 numbers (808 zone cases, r=0.9966, 97.8%
accuracy) — metric-level verified. The formal Stage 3 byte-identical
sha256 comparison was not separately confirmed (the in-memory side
OOMed on this machine during that test — see "Known Issue" below).

**`--stream` is now REQUIRED on this machine for all replay rebuilds,
including single months** — the in-memory path is unreliable here (see
"Known Issue"). Treat `--stream` output as the research dataset going
forward; it is REPLAY_AGGTRADE data, same as the in-memory path (see
CURRENT_CHECKPOINT.md "Research Data Labeling").

## Known Issue: in-memory path OOM on this machine

During the Stage 3 equivalence test, the old in-memory path OOMed on
April (~25.5M trades) on this 24GB machine. Cause unconfirmed (possibly
low free RAM at that moment — other processes, prior run residual
memory). `--stream` avoids this entirely by design and is required
going forward regardless of cause. The 126-day (2026-02-01 ->
2026-06-06) in-memory OOM estimate (~60-75GB) remains valid/unchanged.

## Permanent Rule: outputs/ snapshot before writes

Always take a snapshot/backup of `outputs/` BEFORE any run that writes
to it (especially with `--overwrite`). See RUN_COMMANDS.md "Pre-run
snapshot rule".

## B12 Live Validation — still active

`core/live_b12_validation.py` remains active, unchanged, running
against LIVE (raw `@trade`) data, separate from the REPLAY_AGGTRADE
research pipeline above.

## What Phase 1 Now Produces (carried from prior checkpoint)

Every zone case produces one MarketInterpretation:

```
context:        regime + confluence + flow direction
structure:      trajectory + confidence + health state
engagement:     visits + omega class + force balance
flow:           direction + intensity
prediction:     HOLD / FAIL / UNCERTAIN / NO_PREDICTION + confidence
coherence:      STRONG / MODERATE / WEAK / INSUFFICIENT
interpretation: one sentence (max 80 chars)
```

Output file: research/zone_synthesis.csv

NOTE: the exact row/column counts and prediction distribution recorded
in the prior PHASE1B_SYNTHESIS_ENGINE_STABLE checkpoint (276 rows, 13
columns) predate the March/April/May generalization and B12v2 work —
do not treat those numbers as current without re-checking
research/zone_synthesis.csv.

## Completed Phases / Modules

- Dashboard V2 statistical layer (9 layers, confluence scoring)
- Historical replay infrastructure (3-tier hybrid downloader + Tier-1
  raw-trade cache + new bounded-memory streaming path)
- Phase 1B Episode Research Assistant
- RDM Market Mechanics V1.1 through V1.5
- RDM V1.6-A Numerical Foundation
- RDM V1.6-B1 through B11 (full attacker + exposure + structural
  prediction series)
- Phase 1 Synthesis Engine (connects all layers into one coherent
  output)
- Downloader stability (Tier 1 cache / Tier 2 ZIP / Tier 3 API
  fallback)
- B12 / B12v2 prediction validation, Formation/Active Core zone
  geometry work (see CURRENT_CHECKPOINT.md prior checkpoints)
- B12.5 Dynamic State Engine (REPLAY + LIVE pipeline)
- Live Zone Dashboard (dashboard_live_zones.py, port 8502)

## Validated RDM Physics

sigma x penetration vs omega: r = 0.9935
Structural engagement chain: Force -> sigma_barre filter -> Penetration -> Omega -> mechanical_family -> Growth or Damage
Surface Damage hypothesis: REJECTED (temporal decay formula, not market physics)

## Next Steps

Priority:
1. Run LIVE stream continuously to accumulate post-return visits.
2. Validate LIVE dynamic_state distribution vs REPLAY (need 30+ days).
3. Snapshot `outputs/` before any run that writes to it (permanent rule).

Do not:
- Enter Phase 2
- Add execution / entries / exits / BUY / SELL
- Change Dashboard V2 scoring
- Change RDM formulas
- Change lifecycle logic
- Run any replay rebuild without `--stream` on this machine
- Touch `outputs/` without taking a snapshot first
- Implement B13 (deferred)

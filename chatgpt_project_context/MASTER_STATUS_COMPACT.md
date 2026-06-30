# Master Status Compact

## Current Stable Status

Current checkpoint: RDM_V2_RESTART_DURABILITY_CONTRACT_ACCEPTED

Restart / Durability Contract (ACCEPTED — architecture decision only, NO code):
- The append-only ordered row log is the source of truth.
- Persist-before-process (durably append row before InteractionState advances).
- Rebuild-from-history is the primary recovery mechanism.
- The snapshot is a cache / projection only — never the source of truth.
- Watermark = InteractionState.previous_row_index (single recovery anchor).
- Geometry-in-effect must be pinned (geometry_version + bounds) or replay diverges.
- Checkpoints are an optimization, not correctness.
- No production code changed.

Primary (must persist): ordered row log, session_id, global_zone_key,
geometry-in-effect. Everything else is DERIVED and rebuildable from history.

Next: Restart / Durability implementation decision.

---

## Prior Stable Status (RDM_V2_ROW_ORDERING_CONTRACT_STABLE)

Current checkpoint: RDM_V2_ROW_ORDERING_CONTRACT_STABLE

Row Ordering Contract in the Interaction Interpreter (shadow-only):
- New interpret_in_order() enforces ordering BEFORE any transition; delegates to
  the existing pure interpret() only on accept.
- New OrderingResult (status + audit + state + events).
- Statuses: ORDER_ACCEPTED, ROW_DUPLICATE, ROW_OUT_OF_ORDER.
- InteractionState remains the single ordering watermark (previous_row_index).
- No dispatcher watermark. No coordinator watermark.
- row_index is authoritative; timestamp is informational only.
- No events are emitted for duplicate / out-of-order rows; unchanged state
  returned on rejection.
- Existing interpret() remains unchanged.
- No production behavior changed (interaction_interpreter is shadow-only).

Validation: py_compile of core + both shadow tests OK; existing interpreter
shadow test PASS; new row ordering shadow test PASS (all 6 cases); full
shadow-suite regression (11 tests) PASS; git diff --check clean.

Next: Restart / Durability Contract review.

---

## Prior Stable Status (RDM_V2_SNAPSHOT_IDENTITY_CONTRACT_STABLE)

Current checkpoint: RDM_V2_SNAPSHOT_IDENTITY_CONTRACT_STABLE

Canonical Snapshot identity contract fix (shadow-only):
- Canonical Snapshot identity is now global_zone_key.
- zone_id is descriptive metadata only (no longer determines identity).
- SnapshotStore keyed by global_zone_key (was: bare zone_id).
- Session-scoped identity matches the Event Dispatcher identity contract.
- Snapshot revision model unchanged; copy-on-write unchanged; sections unchanged.
- Production behavior unchanged (canonical_snapshot is shadow-only; only
  experiment shadow tests import it).

Validation: py_compile OK; all 8 Canonical Snapshot / adapter shadow tests PASS;
identity-collision shadow test PASS (same zone_id reused across two sessions ->
two independent snapshots, no collision, no overwrite); git diff --check clean.

Next: Row Ordering Guard architectural review.

---

## Prior Stable Status (PHASE1B_B125_AUTOTRIGGER_STABLE)

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

---

## Active Checkpoint: PHASE1B_RDM_V2_MECHANICAL_ARCHITECTURE_STABLE

Status: STABLE RESEARCH CHECKPOINT

This checkpoint consolidates the current RDM V2 mechanical architecture after Stage 5H.

Included stages:
- Stage 5D Dynamic State signature analysis
- Stage 5E transition analysis
- Stage 5F transition family discovery
- Stage 5G attacker force causality analysis
- Stage 5H mechanical dependency graph

New spec:
- docs/RDM_V2_MECHANICAL_ARCHITECTURE_SPEC.md

Stage 5H graph summary:
- 49 variables classified
- 113 dependency edges
- 21 dependency layers
- max dependency depth = 20
- direct dependency loops = 0

Core conclusion:
The implemented mechanical engine is feed-forward at artifact-generation time. It has temporal memory through integrals, guards, health evolution, sigma evolution, and structural damage, but no same-step algebraic dependency loop was confirmed.

Important research conclusions:
- Stage 2C acute pressure + chronic structural damage is mechanically superior to frozen post-return behavior.
- ATTACKER_DOMINANT has a distinct mechanical signature and is the strongest continuation-bearing Dynamic State so far.
- STABLE / PROBABLE_HOLD are more rejection-biased.
- Attacker Force and Omega are common first movers.
- Fatigue is the clearest deterioration precursor.
- Attacker Force is interaction-conditioned, not raw-delta-only.

Project state:
- Project 1 remains Phase 1B+ research expansion.
- Project 2 has not begun; when approved, it should replace only the Geometry Engine while reusing replay, statistics, dashboard, research infrastructure, and validation methodology.

Rules:
No Phase 2, no Footprint, no execution, no entries/exits, no BUY/SELL, no live signals, no scoring changes, no RDM formula changes, no Dynamic State threshold changes.


---

## Active Checkpoint: RDM_V2_EVENT_DRIVEN_SHADOW_FOUNDATION

Status: VALIDATED SHADOW CHECKPOINT

Purpose:
Create an explicit event-driven RDM V2 foundation without changing
production behavior.

Components:
- Interaction Interpreter:
  market row + geometry -> deterministic MechanicalEvent records.
- Mechanical Refresh Coordinator:
  InteractionState + events -> dirty flags -> ordered RefreshPlan.
- Shadow Chain Test:
  deterministic end-to-end validation with zero mismatches.

Supported shadow events:
TOUCH, ZONE_ENTER, ZONE_EXIT, RETURN, PENETRATION_UPDATED,
VISIT_STARTED, VISIT_COMPLETED.

Validation:
- Requested modules compile: PASS
- Shadow chain test: PASS
- Deterministic replay: PASS
- Mismatches: NONE
- Production effects: FALSE

Isolation:
Shadow mode only. No production or LIVE consumer, no RDM execution,
no Stage 2C integration, no snapshots, no dashboard changes, and no
formula or Dynamic State changes.

Next:
Await architectural decision before production integration.


---

## Active Checkpoint: RDM_V2_EVENT_DRIVEN_BACKBONE_STABLE

Status: VALIDATED SHADOW CHECKPOINT

Shadow backbone:

```text
Interaction Interpreter
    -> Event Dispatcher
    -> Mechanical Refresh Coordinator
```

Responsibilities:
- Interpreter: market row + geometry -> normalized MechanicalEvent records.
- Dispatcher: identity/order validation, event-ID deduplication, atomic
  shadow batch delivery.
- Coordinator: events -> dirty flags -> ordered RefreshPlan.

Validation:
- Valid ordered dispatch: PASS
- Duplicate/replayed IDs: PASS
- Invalid order rejection: PASS
- Zone mismatch rejection: PASS
- Shadow coordinator plan: PASS
- Production effects: FALSE

Boundary:
All three components are shadow-only. No production consumer, LIVE
integration, RDM execution, Stage 2C, Dynamic State, dashboard, snapshot,
or runtime file writes were added.

Next:
Await Canonical Snapshot implementation approval.


---

## Active Checkpoint: RDM_V2_CANONICAL_SNAPSHOT_SHADOW_STABLE

Status: VALIDATED SHADOW CHECKPOINT

Implemented:
- CanonicalZoneSnapshot
- SnapshotBuilder
- SnapshotStore

Initial sections:
- Metadata
- Geometry
- Current Row Mechanics
- Open Visit

Revision behavior:
- In-memory copy-on-write
- Revision starts at 1
- Successful updates increment revision
- Failed updates preserve the previous immutable revision

Boundary:
Shadow only. No persistence, production consumer, LIVE integration,
dashboard integration, Stage 2C, Dynamic State, transitions, B10/B11,
prediction, or formula changes.

Validation:
- Module and shadow test compile: PASS
- Creation/update/revision tests: PASS
- Failed-update preservation: PASS
- Production effects: FALSE

Next:
Await first mechanical component integration approval.


---

## Active Checkpoint: RDM_V2_ROW_MECHANICS_ADAPTER_SHADOW_STABLE

Status: VALIDATED SHADOW CHECKPOINT

Files:
- core/row_mechanics_adapter.py
- experiments/row_mechanics_adapter/shadow_test.py

Implemented:
- 17 current-row mechanical fields mapped
- Explicit source-field provenance
- NOT_AVAILABLE missing-field handling
- Zero and False preserved as valid values
- Canonical Snapshot patch compatibility

Boundary:
Mapping only. No arithmetic, coercion, normalization, fallback mechanical
derivation, production consumer, LIVE integration, RDM changes, Dynamic
State, Stage 2C, B10/B11, dashboard, CSV writes, or persistence.

Validation:
- Module and shadow test compile: PASS
- Normal and missing-field mapping: PASS
- No calculations: PASS
- Snapshot-store application: PASS
- Production effects: FALSE

Next:
Await next mechanical adapter approval.


---

## Active Checkpoint: RDM_V2_OPEN_VISIT_ADAPTER_SHADOW_STABLE

Status: VALIDATED SHADOW CHECKPOINT

Files:
- core/open_visit_adapter.py
- experiments/open_visit_adapter/shadow_test.py

Implemented:
- Existing InteractionState/visit values -> Open Visit snapshot patch
- active_visit_flag
- Source-field provenance
- NOT_AVAILABLE handling
- Canonical Snapshot patch compatibility

Inactive visit:
active_visit_flag is False; visit-specific fields are NOT_AVAILABLE while
available interaction booleans remain unchanged.

Boundary:
Mapping only. No accumulation, inferred mechanics, production consumer,
LIVE integration, Dynamic State, Stage 2C, B10/B11, dashboard, CSV writes,
or persistence.

Validation:
- Module and shadow test compile: PASS
- Active/inactive visit mapping: PASS
- Missing fields and no-calculation proof: PASS
- Snapshot-store application: PASS
- Production effects: FALSE

Next:
Await next adapter approval.


---

## Active Checkpoint: RDM_V2_LAST_COMPLETED_VISIT_ADAPTER_SHADOW_STABLE

Status: VALIDATED SHADOW CHECKPOINT

Files:
- core/canonical_snapshot.py
- core/last_completed_visit_adapter.py
- experiments/last_completed_visit_adapter/shadow_test.py

Implemented:
- Canonical snapshot last_completed_visit section
- 22 completed-visit fields mapped
- Current visit-timeline aliases supported
- Source-field provenance
- NOT_AVAILABLE handling
- Zero and False preserved
- Snapshot patch compatibility

Boundary:
Mapping only. No duration calculation, visit classification, inferred flags,
production consumer, LIVE integration, Dynamic State, Stage 2C, B10/B11,
dashboard, CSV writes, or persistence.

Validation:
- All requested compile checks: PASS
- Adapter mapping and missing handling: PASS
- Existing snapshot regression: PASS
- No calculations: PASS
- Production effects: FALSE

Next:
Await Dynamic Mechanics Adapter approval.


---

## Active Checkpoint: RDM_V2_DYNAMIC_MECHANICS_ADAPTER_SHADOW_STABLE

Status: VALIDATED SHADOW CHECKPOINT

Files:
- core/canonical_snapshot.py
- core/dynamic_mechanics_adapter.py
- experiments/dynamic_mechanics_adapter/shadow_test.py
- Canonical Snapshot regression fixture update

Implemented:
- Canonical snapshot dynamic_mechanics section
- 16 dynamic timeline fields mapped
- SDR, derivatives, integrals, and Dynamic State mapping only
- Alias and source-field provenance
- NOT_AVAILABLE handling
- Snapshot patch compatibility

Boundary:
No derivative, integral, SDR, or Dynamic State calculation. No production
consumer, LIVE integration, Stage 2C, B10/B11, dashboard, CSV writes, or
persistence.

Validation:
- All requested compile checks: PASS
- Adapter mapping, aliases, and missing handling: PASS
- Existing snapshot and completed-visit regressions: PASS
- No calculations: PASS
- Production effects: FALSE

Next:
Await prediction adapter approval.


---

## Active Checkpoint: RDM_V2_PREDICTION_ADAPTER_SHADOW_STABLE

Status: VALIDATED SHADOW CHECKPOINT

Files:
- core/canonical_snapshot.py
- core/prediction_adapter.py
- experiments/prediction_adapter/shadow_test.py

Implemented:
- Canonical snapshot prediction section
- 14 existing B10/B11 fields mapped
- Semantic aliases and source-field provenance
- NOT_AVAILABLE handling
- Snapshot patch compatibility

Boundary:
Mapping only. No B10, B11, prediction, confidence, or Dynamic State
calculation. No production consumer, LIVE integration, Stage 2C, dashboard,
CSV writes, or persistence.

Validation:
- All requested compile checks: PASS
- Prediction mapping, aliases, and missing handling: PASS
- Snapshot, Dynamic Mechanics, and completed-visit regressions: PASS
- No calculations: PASS
- Production effects: FALSE

Next:
Await Canonical Snapshot V1 consolidation approval.


---

## Active Checkpoint: RDM_V2_CANONICAL_SNAPSHOT_V1_CONSOLIDATED_SHADOW_STABLE

Status: VALIDATED SHADOW CHECKPOINT

Complete sections:
Metadata, Geometry, Current Row Mechanics, Open Visit, Last Completed Visit,
Dynamic Mechanics, Prediction.

Adapters consolidated:
Geometry, Row Mechanics, Open Visit, Last Completed Visit, Dynamic Mechanics,
Prediction.

Revision behavior:
- Revision 1 -> 2
- Copy-on-write
- Deep immutability
- Failed update preserves the prior revision

Integrity:
- NOT_AVAILABLE validated
- Existing values preserved exactly
- No geometry or mechanical calculations
- No Dynamic State, B10, or B11 calculation

Artifact:
- experiments/canonical_snapshot_v1/consolidation_test.py

Reproducibility:
The accepted Geometry Snapshot Adapter and its shadow test are included as
direct dependencies of the consolidation test.

Boundary:
Shadow only. No production consumer, LIVE integration, dashboard, Stage 2C,
CSV writes, persistence, formulas, or production behavior changes.

Next:
Await first shadow integration pipeline approval.

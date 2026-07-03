# Master Status Compact

## Current Stable Status

Current checkpoint: PHASE1B_DYNAMIC_MECHANICS_SNAPSHOT_STAGE2_STABLE

Stage 2 mapped Stage 1's research Dynamic Mechanics outputs into the Canonical
Snapshot dynamic_mechanics section (research-only, no production behavior
changed).
- Mapped research Dynamic Mechanics into Canonical Snapshot dynamic_mechanics
  section via the existing, unmodified DynamicMechanicsAdapter.build_patch().
- Offline only; no production/Project 1/live/dashboard/B10/B11 changes.
- Reused Stage 1 logic unmodified; committed LastCompletedVisit +
  DynamicMechanics patches atomically into SnapshotStore (multi-adapter
  pattern proven in Phase 0/1A).
- SIMPLE_RESEARCH_SDR_V1 remains research-only; RESEARCH_ labels only.
- NOT_AVAILABLE behavior validated.

Results (deterministic across three runs): rows_processed=3000,
zones_observed=7, completed_visits=159, dynamic_mechanics_commits=159,
snapshot_revisions_total=159, revision_monotonicity=True, copy_on_write=True,
global_zone_key_preserved=True, dynamic_section_updated=True,
previous_state_chain_consistent=True, transitions_research_only=True,
not_available_counts={first_derivative:7, second_derivative:14,
dynamic_state:7, transition_name:14}, not_available_expected=True,
deterministic_across_runs=True, errors=0, result=PASS.

Validation: py_compile OK; run PASS; git diff --check clean.

Next: Stage 3 Dynamic State transition analysis approval.

---

## Prior Stable Status (PHASE1B_DYNAMIC_MECHANICS_STAGE1_OFFLINE_STABLE)

Current checkpoint: PHASE1B_DYNAMIC_MECHANICS_STAGE1_OFFLINE_STABLE

First Phase 1B offline validation: Dynamic Mechanics research metrics computed
from Project 2 Psychological Levels completed-visit sequences (research-only,
no production behavior changed).
- Project 2 Psychological Levels used as offline research geometry (reuses
  experiments/psychological_levels/provider.py, Phase 1A, unmodified).
- Real Interpreter -> Dispatcher -> Coordinator -> LastCompletedVisitAdapter
  path reused, unmodified. No core/production modifications.
- Research-only deterministic proxy mechanics: health_live, omega_accumulator,
  attacker_force_peak -- not a Project 1 formula. Production formulas not
  changed.
- SIMPLE_RESEARCH_SDR_V1 is research-only (|delta omega| / health), NOT the
  production Structural Dynamic Response formula.
- RESEARCH_ labels only, not production B12.5 Dynamic State.
- SnapshotStore deliberately not used in Stage 1.

Results: rows_processed=3000, zones_observed=7, completed_visits=159,
first_derivatives_generated=152, integrals_generated=159,
second_derivatives_generated=145, sdr_values_generated=152,
dynamic_labels_generated=152, errors=0, result=PASS (deterministic, reproduced
on a second run).

Validation: py_compile OK; run PASS; git diff --check clean.

Next: Stage 2 snapshot dynamic mechanics approval.

---

## Prior Stable Status (RDM_V2_PHASE0_PASSIVE_SHADOW_PRODUCTION_SAFE)

Current checkpoint: RDM_V2_PHASE0_PASSIVE_SHADOW_PRODUCTION_SAFE

PHASE 0 CLOSED — PRODUCTION SAFE (final Phase 0 checkpoint; deliberately
distinct from "PRODUCTION VALIDATED" — correctness under load is proven by the
Replay Soak; the LIVE soaks prove safety alongside real production).

Journey: Safety Modules -> Runtime Emitter -> Live Tap -> Passive Worker ->
Runtime Connection -> Parity Logging -> Bootstrap -> Repository Integrity Fix
-> Replay Soak PASS -> Controlled LIVE Soak PASS -> Extended LIVE Soak
INCONCLUSIVE (market_event_scarcity, shadow pipeline not at fault).

- Replay soak: PASS. Controlled LIVE soak: PASS.
- Extended LIVE soak: INCONCLUSIVE due to MARKET_EVENT_SCARCITY (60 min hard
  cap, zero failures of any kind, zero payloads because none were available,
  not because any were lost).
- Confirmed by direct evidence: live_return_detection.csv and
  live_rdm_results.csv show zero new rows during the soak AND for the full
  week preceding it (compute_live_rdm_for_case only runs on return_found,
  which never fired); live_preparation_zones.csv's last activity predates the
  soak by hours; no emitter DISABLED/DROPPED/ERROR; stderr empty the whole
  hour. Shadow pipeline not at fault -- Project 1 produced no Preparation/
  Return case.
- Production safety verified over 60 continuous real minutes: no exception, no
  drop, no desync, no breaker trip, no parity path violation, no memory growth.

Phase 0 infrastructure: COMPLETE. Phase 0 policy: FROZEN except critical
production bug fixes. Not allowed: new Phase 0 architecture, refactoring,
snapshot/queue/worker/bootstrap/contract/coordinator redesign.

Future payload-rich validation runs opportunistically when Project 1 emits
enough cases -- not a blocking gate.

Next: Phase 1 -- System Intelligence.

---

## Prior Stable Status (RDM_V2_FIRST_CONTROLLED_LIVE_PASSIVE_SHADOW_SOAK_PASS)

Current checkpoint: RDM_V2_FIRST_CONTROLLED_LIVE_PASSIVE_SHADOW_SOAK_PASS

First controlled LIVE passive shadow soak (SHADOW_RUNTIME_ENABLED=1,
SHADOW_DRY_RUN=1, SHADOW_SAMPLE_RATE=0.05, kill switch disabled) run against the
real production stream_manager.

Results: duration=00:00:05, payloads_received=10, payloads_processed=9,
parity_records=20, failed=0, dropped=0, desynchronized=0, production_errors=0,
CPU=1.41s, memory=101.3MB, result=PASS.

- First controlled LIVE passive shadow soak PASSED.
- Passive shadow tap emitted real LIVE payloads; worker processed them
  end-to-end; parity logging produced records (research/shadow_parity/ only).
- No production errors, drops, desynchronization, or worker failures.
- No production output replacement, dashboard changes, formula changes, Stage
  2C, or Dynamic State recomputation.
- One payload difference (received=10, processed=9) — likely one in-flight
  payload at forced stop; not a failure since failed/dropped/desync stayed zero.

Validation: git diff --check clean; only the 5 checkpoint docs staged.

Next: extended live soak decision.

---

## Prior Stable Status (RDM_V2_LIVE_ACTIVATION_WIRING_STABLE)

Current checkpoint: RDM_V2_LIVE_ACTIVATION_WIRING_STABLE

Resolves the Final Architectural Review blocker: live tap/emitter/worker/runtime
existed but nothing in the committed tree ever STARTED the passive worker.
Fix: isolated startup/shutdown hook in engines/stream_manager.py main() (the
file's only diff hunk):
- start before start_stream(); stop in finally (drain_timeout_seconds=2.0).
- fail-safe try/except around both; shadow failure can never block start_stream().
- flag default OFF (SHADOW_RUNTIME_ENABLED unset/"0" -> DISABLED, no worker).
- no unrelated stream_manager changes mixed in.

Validation: py_compile stream_manager + bootstrap OK; bootstrap test PASS; flag
OFF/0 verified to start no worker; git diff --check clean.

Next: first live payload contract validation.

---

## Prior Stable Status (RDM_V2_PASSIVE_SHADOW_BOOTSTRAP_REPOSITORY_FIX)

Current checkpoint: RDM_V2_PASSIVE_SHADOW_BOOTSTRAP_REPOSITORY_FIX

Repository integrity fix (shadow-only, no production behavior changed):
- Problem: committed tools/passive_shadow_replay_soak.py imported
  core/passive_shadow_bootstrap.py, which was implemented/run locally (Phase 0F)
  but never committed -> fresh clone could not run the committed soak.
- Fix: committed the 2 missing Phase 0F bootstrap files as an isolated checkpoint
  (core/passive_shadow_bootstrap.py — fail-safe, flag-gated default OFF,
  kill-switch protected, imports only committed core modules; and
  experiments/passive_shadow_worker/bootstrap_test.py).
- Scope: ONLY the 2 files (+ docs); daily_session.py, live_rdm pre-existing hunks,
  and other unrelated changes NOT staged.
- Validation: py_compile bootstrap + test + soak OK; bootstrap test PASS; replay
  soak import smoke OK; git diff --check clean.
- Result: committed soak no longer depends on untracked code.

(Doc order: Codex recorded Phase 0E-1/0E-2/0E-3 + replay-soak-PASS at the BOTTOM
of the full docs; this fix is prepended at the top.)

Next: Final Architectural Review.

---

## Prior Stable Status (RDM_V2_PHASE0D_MINIMAL_LIVE_TAP_STABLE)

Current checkpoint: RDM_V2_PHASE0D_MINIMAL_LIVE_TAP_STABLE

Phase 0D: first (minimal) production wiring of the Passive Shadow Runtime — one
flag-gated, isolated tap:
- one minimal flag-gated tap in compute_live_rdm_for_case (core/live_rdm.py);
  only production line is _shadow_emit(record).
- after _persist_record / B12.5 hook, before return record.
- local import (load-time import graph unchanged).
- try/except isolated (never blocks LIVE, never mutates record/outputs).
- default OFF; no-op with flag OFF -> no production behavior change with flag OFF.
- unrelated live_rdm hunks excluded (patch-staging; 5 pre-existing hunks left
  unstaged + unmodified).

Validation: py_compile live_rdm + emitter OK; import smoke OK; emitter shadow test
PASS; flag OFF -> no queue activity; git diff --check clean; staged diff = tap only.

Next: passive shadow runtime worker approval.

---

## Prior Stable Status (RDM_V2_PHASE0C_SHADOW_EMITTER_STABLE)

Current checkpoint: RDM_V2_PHASE0C_SHADOW_EMITTER_STABLE

Phase 0C standalone shadow emitter (core/shadow_runtime_emitter.py; imports only
Phase 0A core/shadow_safety; built BEFORE the LIVE tap):
- standalone shadow_runtime_emitter (emit + ShadowPayload / EmitResult).
- flags default OFF -> no-op (DISABLED).
- kill switch blocks emit (KILLED).
- bounded queue non-blocking (full -> DROPPED, never blocks).
- deep-copied immutable payload (deepcopy + frozen ShadowPayload).
- global_zone_key = session_id::zone_id (session falls back to UNKNOWN_SESSION).
- geometry_version synthesized from pinned geometry edges (GEOMv1:<hex>).
- bad record never raises (-> ERROR).
No live tap (live_rdm.py untouched); no production imports; no production
behavior changed.

Validation: py_compile emitter + test OK; shadow emitter test PASS; git diff
--check clean.

Next: Phase 0D live tap approval.

---

## Prior Stable Status (RDM_V2_PHASE0A_SHADOW_SAFETY_MODULES_STABLE)

Current checkpoint: RDM_V2_PHASE0A_SHADOW_SAFETY_MODULES_STABLE

Phase 0A safety scaffolding (standalone, shadow-only; built BEFORE any LIVE tap).
New package core/shadow_safety/ (fail-closed):
- feature flags default OFF (feature_flag.py): explicit opt-in only.
- kill switch / circuit breaker (kill_switch.py): latches KILLED on trip / N
  consecutive failures; reset() only; manual env/file kill; fail-closed.
- bounded non-blocking queue (bounded_queue.py): offer drops on full + counts,
  never blocks / raises.
- isolated worker wrapper (isolated_worker.py): swallows + counts exceptions
  (re-raises only KeyboardInterrupt/SystemExit).
- parity log writer confined to research/shadow_parity/ (parity_log.py).
No live tap (live_rdm.py untouched); no production imports; no production
behavior changed.

Validation: py_compile all modules + test OK; shadow safety test PASS; git diff
--check clean.

Next: Phase 0B tap point review.

---

## Prior Stable Status (RDM_V2_FULL_SHADOW_RUNTIME_STABLE)

Current checkpoint: RDM_V2_FULL_SHADOW_RUNTIME_STABLE

Consolidation of the entire RDM V2 shadow architecture phase (shadow-only):
- Event-Driven Backbone complete: Market Row -> Interaction Interpreter ->
  Event Dispatcher -> Mechanical Refresh Coordinator -> Canonical Snapshot
  (interaction_interpreter, event_dispatcher, mechanical_refresh_coordinator,
  canonical_snapshot).
- Contracts: Snapshot Identity (global_zone_key canonical, zone_id metadata,
  no cross-session collision); Row Ordering (interpret_in_order;
  previous_row_index sole watermark; row_index authoritative; duplicate ->
  ROW_DUPLICATE; older -> ROW_OUT_OF_ORDER); Restart/Durability (append-only row
  log is truth; persist-before-process; rebuild-from-history; snapshot is
  cache/projection; geometry pinned; checkpoints optimization not correctness).
- Canonical Snapshot sections: Metadata, Geometry, Current Row Mechanics, Open
  Visit, Last Completed Visit, Dynamic Mechanics, Prediction. Copy-on-write;
  immutable revisions; one atomic revision per commit; previous preserved on
  failure; keyed by global_zone_key.
- Six shadow adapters (geometry, row_mechanics, open_visit,
  last_completed_visit, dynamic_mechanics, prediction): pure mapping,
  NOT_AVAILABLE-aware, alias-aware, no production consumers.
- Shadow integrations: experiments/coordinator_snapshot_integration/shadow_test.py
  and experiments/full_shadow_runtime/shadow_test.py.
- Full runtime guarantees: one plan per accepted event row; one atomic revision
  per committed plan; duplicate/out-of-order rejected before refresh; adapter
  failure preserves previous revision; no partial commit; prediction PENDING does
  not block completed/dynamic; global_zone_key + source_plan_id + provenance +
  copy-on-write preserved; no calculations; no prediction generation; no Dynamic
  State recompute; no Stage 2C; no production behavior changed.

Validation: py_compile OK; full shadow runtime test PASS (6 scenarios; 8 plans ->
7 committed revisions); git diff --check clean.

Next: production integration strategy.

---

## Prior Stable Status (RDM_V2_PREDICTION_SNAPSHOT_INTEGRATION_SHADOW_STABLE)

Current checkpoint: RDM_V2_PREDICTION_SNAPSHOT_INTEGRATION_SHADOW_STABLE

Prediction Adapter integrated into the coordinator snapshot integration test:
- Prediction Adapter integrated into the multi-adapter atomic orchestrator.
- Gate = ALL(trajectory_dirty, prediction_dirty) (B10 -> B11 dependency).
- Prediction runs logically after Dynamic Mechanics.
- Missing prediction input produces PENDING / NOT_AVAILABLE (no abort).
- Pending prediction does not block completed_visit or dynamic_mechanics.
- Unexpected prediction adapter failure prevents partial commit.
- One atomic revision per merged commit; global_zone_key + source_plan_id preserved.
- No calculations; no prediction generation; no production behavior changed.

Validation: py_compile integration test OK; integration test PASS; git diff
--check clean.

Next: full shadow runtime consolidation approval.

---

## Prior Stable Status (RDM_V2_CANONICAL_SNAPSHOT_ADAPTERS_COMPLETE)

Current checkpoint: RDM_V2_CANONICAL_SNAPSHOT_ADAPTERS_COMPLETE

All six Canonical Snapshot adapters are now shadow-ready (one per section):
geometry, current row mechanics, open visit, last completed visit, dynamic
mechanics, prediction.

Shared properties (all six):
- Pure mapping only (value pass-through via ordered source aliases).
- No calculations (no Dynamic State recompute, derivatives, integrals, SDR,
  classifier, thresholds, B10/B11, Stage 2C, dashboard, CSV, persistence).
- NOT_AVAILABLE for absent / None / empty / NaN (no defaulting).
- Snapshot compatibility: the six consolidate into one immutable copy-on-write
  snapshot.
- No production behavior changed.

Recent additive work folded in: DynamicMechanicsAdapter +transition_name;
PredictionAdapter +prediction_uncertainty.

Validation: py_compile all six adapters + tests OK; all adapter shadow tests
PASS; consolidation test PASS; git diff --check clean.

Next: first real mechanical integration decision.

---

## Prior Stable Status (RDM_V2_LAST_COMPLETED_VISIT_ADAPTER_SHADOW_STABLE)

Current checkpoint: RDM_V2_LAST_COMPLETED_VISIT_ADAPTER_SHADOW_STABLE

Last Completed Visit Adapter Stage 1 (shadow-only):
- Extended the existing adapter additively (committed aefec1c); existing target
  names/behavior untouched, dependent consolidation test stays green.
- Maps existing completed-visit fields into the Canonical Snapshot
  "last_completed_visit" section (projection only, no rebuild, no inference).
- Adds max_penetration_ratio and defender_state (plus visit_start_price /
  visit_end_price).
- Supports aliases (completed_visit_id, visit_final_omega, visit_health, etc.).
- NOT_AVAILABLE behavior for absent / None / empty / NaN (no defaulting).
- No calculations; snapshot compatibility validated.
- No production behavior changed.

Validation: py_compile adapter + test OK; extended shadow test PASS;
consolidation test PASS; git diff --check clean.

Next: Dynamic Mechanics Adapter approval.

---

## Prior Stable Status (RDM_V2_RESTART_DURABILITY_CONTRACT_ACCEPTED)

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


---

## Active Checkpoint: RDM_V2_COORDINATOR_ROW_MECHANICS_SNAPSHOT_INTEGRATION_SHADOW_STABLE

Status: VALIDATED SHADOW INTEGRATION CHECKPOINT

Artifact:
- experiments/coordinator_snapshot_integration/shadow_test.py

Chain:
MechanicalRefreshCoordinator -> dirty flags -> RowMechanicsAdapter ->
Canonical Snapshot.

Validated:
- Dirty flags gate Row Mechanics mapping
- Snapshot revisions 1 -> 2
- Copy-on-write preserves the prior revision
- Negative-control plan skips the update
- global_zone_key remains the canonical identity
- No calculations
- Production effects: FALSE

Boundary:
Shadow only. No production consumer, LIVE integration, dashboard, Stage 2C,
B10/B11, CSV writes, or persistence.

Next:
Await multi-adapter shadow integration approval.


---

## Active Checkpoint: RDM_V2_MULTI_ADAPTER_SNAPSHOT_INTEGRATION_SHADOW_STABLE

Status: VALIDATED SHADOW INTEGRATION CHECKPOINT

Chain:
RefreshPlan -> Row Mechanics Adapter + Open Visit Adapter -> merged patches
-> one Canonical Snapshot commit.

Validated:
- Both adapters execute in one refresh cycle
- Patches merge before publication
- Exactly one revision per merged commit
- Copy-on-write preserves prior revisions
- Skip or Open Visit failure produces no partial commit
- Previous revision remains authoritative after failure
- global_zone_key and source_plan_id are preserved
- Adapter provenance is preserved
- No calculations
- Production effects: FALSE

Boundary:
Shadow only. No production consumer, LIVE integration, Dynamic State,
Stage 2C, B10/B11, dashboard, CSV writes, or persistence.

Next:
Await next integration approval.


---

## Active Checkpoint: RDM_V2_COMPLETED_VISIT_SNAPSHOT_INTEGRATION_SHADOW_STABLE

Status: VALIDATED SHADOW INTEGRATION CHECKPOINT

Validated:
- VISIT_COMPLETED supplies visit_dirty + response_dirty
- Last Completed Visit Adapter is gated only by completed-visit flags
- Row/Open adapters can participate in the same cycle
- Three patches commit as one atomic snapshot revision
- Row-only updates preserve last_completed_visit
- Adapter failure prevents partial commit
- Prior revision remains authoritative
- global_zone_key and source_plan_id are preserved
- No calculations
- Production effects: FALSE

Boundary:
Shadow only. No production consumer, LIVE integration, Dynamic State,
Stage 2C, B10/B11, dashboard, CSV writes, or persistence.

Next:
Await Dynamic Mechanics integration approval.

---

## Active Checkpoint: RDM_V2_PHASE0E1_PASSIVE_SHADOW_WORKER_SKELETON_STABLE

Status: VALIDATED SHADOW SAFETY CHECKPOINT

Implemented:
- Passive shadow worker skeleton
- Feature flag gated
- Kill-switch protected
- Bounded queue draining
- Exception isolation
- Counters: received, processed, dropped, failed, killed, desynchronized
- No-op handler only

Boundary:
No full shadow runtime, snapshots, adapters, parity logs, production outputs,
or production behavior changes.

Next:
Await Phase 0E-2 runtime connection approval.

---

## Active Checkpoint: RDM_V2_PHASE0E2_PASSIVE_WORKER_RUNTIME_CONNECTION_STABLE

Status: VALIDATED SHADOW RUNTIME CONNECTION

Validated:
- Passive worker executes payload -> interpreter -> dispatcher -> coordinator
  -> adapters -> internal Canonical Snapshot
- Duplicate/out-of-order rejection
- Adapter failure rollback
- Worker counters and kill switch
- Copy-on-write and global_zone_key preservation

Boundary:
No production outputs, dashboard, parity log, formulas, Stage 2C, Dynamic
State recomputation, prediction generation, or production behavior changes.

Next:
Await Phase 0E-3 parity logging approval.

---

## Active Checkpoint: RDM_V2_PHASE0E3_PARITY_LOGGING_STABLE

Status: VALIDATED SHADOW PARITY LOGGING

Validated:
- Shadow-only JSONL parity records under research/shadow_parity/
- Successful payload and pending prediction logging
- Failure logging preserves the authoritative snapshot
- Logger failure is non-fatal
- Path confinement enforced

Boundary:
No production CSV writes, dashboard, formulas, Stage 2C, Dynamic State
recomputation, prediction generation, or production behavior changes.

Next:
Await passive shadow soak test plan.

---

## Active Checkpoint: RDM_V2_PASSIVE_SHADOW_REPLAY_SOAK_PASS

Status: END-TO-END REPLAY SHADOW SOAK PASS

Summary:
- Bootstrap STARTED
- 10 attempted / 10 enqueued / 10 processed
- 0 dropped / 0 failed / 0 desynchronized
- Queue depth 0
- 10 parity records / 10 success / 0 failed
- Result: PASS

Confirmed:
Bootstrap, worker, emitter, runtime, dispatcher, coordinator, dirty-gated
adapters, Canonical Snapshot, copy-on-write revisions, global_zone_key, row
ordering, snapshot identity, and parity logging are operational. Restart and
durability architecture remains unchanged.

Conclusion:
The earlier LIVE soak was inconclusive because no finalized LIVE RDM payload
was emitted. Replay confirms the complete passive shadow pipeline works when
finalized payloads are available.

Boundary:
No production formulas or outputs, dashboard, Stage 2C, Dynamic State
recomputation, or prediction generation changes. Shadow remains diagnostic.

Next:
Await next production integration decision.

---

## Active Checkpoint: PHASE1A_PSYCHOLOGICAL_LEVELS_PROVIDER_STAGE1_STABLE

Status: EXPERIMENTAL PROJECT 2 PROVIDER VALIDATED

Validated:
- experiments/psychological_levels/ only; no core promotion
- spacing 200, half-width 25, active window +/-3
- Decimal arithmetic and immutable PsychologicalLevelGeometry
- Stable zone_id, case_id, and session-scoped global_zone_key
- Price 60341 generated 59800 through 61000 in deterministic 200 increments
- All provider tests PASS

Boundary:
Offline only. No RDM, Snapshot, Worker, LIVE, dashboard, Project 1, formula,
or production behavior changes.

Next:
Await Stage 2 Interaction Interpreter validation.

---

## Active Checkpoint: PHASE1A_PSYCHOLOGICAL_LEVELS_SNAPSHOT_INTEGRATION_STABLE

Status: PROJECT 2 OFFLINE SNAPSHOT INTEGRATION VALIDATED

Validated:
- Psychological Levels configuration: spacing 200, half-width 25, window +/-3
- Stage 1 Provider PASS
- Stage 2 Interaction Interpreter PASS
- Stage 3 Event Dispatcher PASS
- Stage 4 Coordinator + Canonical Snapshot PASS
- geometry_source remains PSYCHOLOGICAL_LEVELS_TEST
- global_zone_key, copy-on-write, deterministic snapshots, and duplicate guards preserved
- No Project 1 Formation, Active Core, or Density Band terminology injected

Boundary:
Experimental offline only. No Project 1, production, Worker, LIVE, dashboard,
or formula changes.

Next:
Await Stage 5 stress-test approval.

---

## Active Checkpoint: PHASE1A_PSYCHOLOGICAL_LEVELS_STRESS_TEST_STABLE

Status: STAGE 5 OFFLINE STRESS VALIDATION PASS

Results:
- 10,000 rows; 5,823 events; 4,240 plans and snapshot revisions
- 7 zones; maximum active zones 1
- 10.86s processing; 3,189,856-byte peak traced memory
- Revisions: 600, 600, 608, 608, 608, 608, 608
- Determinism, copy-on-write, identity, revision monotonicity,
  duplicate/out-of-order protection, and snapshot consistency: PASS

Boundary:
Offline Project 2 experiment only. No Project 1 or production behavior changes.

Next:
Await Phase 1B Dynamic Mechanics offline validation approval.

---

## Active Checkpoint: PHASE1B_AUTHORIZED

Status: READY FOR PHASE 1B

Gate result:
- Independent architectural review PASS
- Phase 0 PRODUCTION_SAFE / FROZEN
- Phase 1A STABLE / COMPLETE
- Shared RDM architecture confirmed geometry-agnostic
- Identity, copy-on-write, revision monotonicity, and snapshot contracts preserved
- No redesign required

Phase 1B research order:
Dynamic Mechanics -> Dynamic State -> SDR -> B10 -> B11 -> Offline Validation
-> Statistical Analysis.

Frozen:
Geometry Provider, Interaction Interpreter, Event Dispatcher, Refresh
Coordinator, Canonical Snapshot, Identity Model, Revision Model, copy-on-write.
Changes require a documented architectural reason.

Boundary:
Offline mechanical-intelligence research only. No production integration or
infrastructure redesign.

Next:
Await Dynamic Mechanics design.
---

## Active Checkpoint: DAILY_SESSION_IDENTITY_STABLE

Status: STABLE - READY FOR PHASE 1B

- Stale and malformed manifests recover safely.
- Algeria boundaries use exchange timestamps.
- One identity propagates preparation -> return -> RDM -> evolution -> dynamic.
- Same-session restart counters recover from existing episode records.
- Live dynamic joins use global_case_id; legacy rows remain isolated.
- Five fields propagate: session_id, market_date, session_episode_id,
  global_episode_key, global_case_id.
- CSV migrations use atomic replacement and preserve union schemas.
- No Project 1 formulas, Phase 1A, dashboard, Snapshot, Worker, Queue,
  Bootstrap, Project 2, or B10/B11 changes.
- Scoped compile, focused identity validation, and diff checks: PASS.

Next:
Begin Phase 1B Dynamic Mechanics design.

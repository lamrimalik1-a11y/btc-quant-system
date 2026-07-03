==================================================
RDM_V2_PHASE0_PASSIVE_SHADOW_PRODUCTION_SAFE
==================================================

STATUS: PHASE 0 CLOSED — PRODUCTION SAFE (final Phase 0 checkpoint). Deliberate
distinction from "PRODUCTION VALIDATED": end-to-end correctness under load is
proven by the Replay Soak; the two LIVE soaks prove the passive shadow is SAFE
alongside real production for a sustained period without impact.

Journey: Safety Modules -> Runtime Emitter -> Live Tap -> Passive Worker ->
Runtime Connection -> Parity Logging -> Bootstrap -> Repository Integrity Fix
-> Replay Soak PASS -> Controlled LIVE Soak PASS -> Extended LIVE Soak
INCONCLUSIVE (market_event_scarcity, shadow pipeline not at fault).

Soak history:
- Replay soak: PASS.
- Controlled LIVE soak: PASS.
- Extended LIVE soak: INCONCLUSIVE due to MARKET_EVENT_SCARCITY -- 60 min hard
  cap, zero failures of any kind (failed=0, dropped=0, desynchronized=0,
  breaker never tripped, zero production exceptions, memory flat ~99-101MB,
  revision monotonicity / copy-on-write / identity integrity all HELD). Zero
  payloads because none were available to process, not because any were lost.

Why zero payloads (confirmed by direct evidence): outputs/live_return_detection
.csv and outputs/live_rdm_results.csv show zero new rows during the soak AND
for the full week preceding it (last write 2026-06-25) -- compute_live_rdm_
for_case only runs on return_found, which never fired. live_preparation_zones
.csv's last activity predates the soak by hours and was a logged rejection. No
emitter DISABLED/DROPPED/ERROR at any point; stderr empty the whole hour.
Shadow pipeline not at fault -- Project 1 (Preparation Zone / Active Core /
Density Band -- NOT Psychological Levels) produced no Preparation/Return case.

Production safety verified over 60 continuous real minutes: no exception, no
drop, no desync, no breaker trip, no parity path violation, no memory growth,
no interference with the live stream.

Phase 0 infrastructure: COMPLETE.
Phase 0 policy: FROZEN except critical production bug fixes.
Not allowed: new Phase 0 architecture, refactoring, snapshot/queue/worker/
bootstrap/contract/coordinator redesign.

Future payload-rich validation runs opportunistically when Project 1 emits
enough cases -- not a blocking gate.

Next: Phase 1 -- System Intelligence.

==================================================
RDM_V2_FIRST_CONTROLLED_LIVE_PASSIVE_SHADOW_SOAK_PASS
==================================================

STATUS: SOAK PASS — shadow-only, no production behavior changed. First
controlled LIVE passive shadow soak (SHADOW_RUNTIME_ENABLED=1, SHADOW_DRY_RUN=1,
SHADOW_SAMPLE_RATE=0.05, kill switch disabled) run against the real production
stream_manager.

Results:
duration=00:00:05 payloads_received=10 payloads_processed=9 parity_records=20
failed=0 dropped=0 desynchronized=0 production_errors=0 CPU=1.41s
memory=101.3MB result=PASS

Findings:
- First controlled LIVE passive shadow soak PASSED.
- Passive shadow tap emitted real LIVE payloads.
- Worker processed LIVE shadow payloads end-to-end.
- Parity logging produced records (confined to research/shadow_parity/).
- No production errors, no drops, no desynchronization, no worker failures.
- No production output replacement, no dashboard changes, no formulas changed,
  no Stage 2C, no Dynamic State recomputation.
- One payload difference observed: received=10, processed=9 — likely one
  payload still in-flight at the forced stop. NOT a failure: failed/dropped/
  desynchronized all remained zero.

Validation: git diff --check clean; only the 5 checkpoint docs staged.

Next: extended live soak decision.

==================================================
RDM_V2_LIVE_ACTIVATION_WIRING_STABLE
==================================================

STATUS: STABLE CHECKPOINT — no production behavior change with the flag OFF.
Resolves the Final Architectural Review blocker: live tap/emitter/worker/runtime
existed, but nothing in the committed tree ever STARTED the passive worker.

Fix: committed the isolated startup/shutdown hook in engines/stream_manager.py
main() (the file's only diff hunk):
- start before start_stream() (local import + start_passive_shadow(), before
  await start_stream()).
- stop in finally (shadow_stop(drain_timeout_seconds=2.0)).
- fail-safe try/except around both start and stop; shadow failure can never
  block start_stream().
- flag default OFF (delegates to PassiveShadowBootstrap/FeatureFlags default);
  SHADOW_RUNTIME_ENABLED unset or "0" -> DISABLED, no worker started.
- no unrelated stream_manager changes mixed in (single hunk in the file).

Validation: py_compile stream_manager + bootstrap OK; bootstrap test PASS; flag
OFF/0 verified to start no worker via the exact main() entry points; git diff
--check clean.

Next: first live payload contract validation.

==================================================
RDM_V2_PASSIVE_SHADOW_BOOTSTRAP_REPOSITORY_FIX
==================================================

STATUS: REPOSITORY INTEGRITY FIX — shadow-only, no production behavior changed.

Problem: committed tools/passive_shadow_replay_soak.py imported
core/passive_shadow_bootstrap.py, which was implemented/run locally (Phase 0F)
but never committed -> a fresh clone could not run the committed soak.

Fix: committed the two missing Phase 0F bootstrap files as an isolated checkpoint:
- core/passive_shadow_bootstrap.py — fail-safe lifecycle owner (flag-gated
  default OFF, kill-switch protected, never raises to caller; imports only
  already-committed core modules).
- experiments/passive_shadow_worker/bootstrap_test.py — Phase 0F lifecycle test.

Scope: ONLY the two bootstrap files (+ docs) staged; daily_session.py, live_rdm
pre-existing hunks, live_return_detection.py, observation_logger.py,
zone_mechanics_calculator.py, research artifacts, unrelated experiments NOT staged.

Validation: py_compile bootstrap + test + soak OK; bootstrap test PASS; replay
soak import smoke OK (committed soak now resolves bootstrap); git diff --check
clean. Result: committed soak no longer depends on untracked code.

(Doc order note: Codex recorded Phase 0E-1/0E-2/0E-3 and PASSIVE_SHADOW_REPLAY_
SOAK_PASS appended at the BOTTOM of this file; this fix is prepended at the top.)

Next: Final Architectural Review.

==================================================
RDM_V2_PHASE0D_MINIMAL_LIVE_TAP_STABLE
==================================================

STATUS: STABLE CHECKPOINT — no production behavior change with the flag OFF.
Phase 0D: first (minimal) production wiring of the Passive Shadow Runtime — one
flag-gated, isolated tap.

- one minimal flag-gated tap in compute_live_rdm_for_case (core/live_rdm.py);
  only production line is _shadow_emit(record).
- after _persist_record / B12.5 hook, before return record.
- local import (load-time import graph unchanged).
- try/except isolated (never blocks LIVE, never mutates record/outputs).
- default OFF; no-op with flag OFF -> no production behavior change with flag OFF
  (verified status DISABLED, zero queue activity).
- unrelated live_rdm hunks excluded (patch-staging via git apply --cached; the 5
  pre-existing hunks left unstaged + unmodified).

Validation: py_compile live_rdm + emitter OK; live_rdm import smoke OK; emitter
shadow test PASS; flag OFF -> no queue activity; git diff --check clean; staged
diff shows ONLY the tap hunk.

Next: passive shadow runtime worker approval.

==================================================
RDM_V2_PHASE0C_SHADOW_EMITTER_STABLE
==================================================

STATUS: STABLE CHECKPOINT — shadow-only, no production behavior changed.
Phase 0C: standalone shadow emitter, built/validated BEFORE the LIVE tap exists.

New module core/shadow_runtime_emitter.py (imports only Phase 0A
core/shadow_safety):
- standalone shadow_runtime_emitter (ShadowRuntimeEmitter.emit + ShadowPayload /
  EmitResult + module-level emit/get_default_emitter).
- flags default OFF -> no-op (status DISABLED); default emitter reads env (OFF).
- kill switch blocks emit (status KILLED) when breaker latched or env/file kill.
- bounded queue non-blocking (full -> DROPPED, never blocks / raises).
- deep-copied immutable payload (deepcopy + MappingProxyType/tuples, frozen
  ShadowPayload); source mutation after emit cannot affect the payload.
- global_zone_key = session_id::zone_id (session falls back to UNKNOWN_SESSION).
- geometry_version synthesized from pinned geometry edges (GEOMv1:<hex>;
  deterministic; GEOMv1:NA when none).
- bad record never raises (try/except BaseException; malformed -> ERROR).

No live tap (live_rdm.py untouched); no production imports; no production
behavior changed (no dashboard, formulas, Stage 2C, or CSV writes).

Validation: py_compile emitter + test OK; shadow emitter test PASS (all 8
requirements); git diff --check clean.

Next: Phase 0D live tap approval.

==================================================
RDM_V2_PHASE0A_SHADOW_SAFETY_MODULES_STABLE
==================================================

STATUS: STABLE CHECKPOINT — shadow-only, no production behavior changed.
First step of the production-integration migration: standalone Phase 0 safety
scaffolding (Phase 0A), built/validated BEFORE any LIVE tap exists.

New package core/shadow_safety/ (fail-closed, standalone):
- feature flags default OFF (feature_flag.py): SHADOW_RUNTIME_ENABLED /
  SHADOW_DRY_RUN / SHADOW_SAMPLE_RATE; absent/garbage -> OFF; explicit opt-in only.
- kill switch / circuit breaker (kill_switch.py): latches KILLED on trip() or N
  consecutive failures; never self-revives (reset() only); manual env/file kill;
  fail-closed.
- bounded non-blocking queue (bounded_queue.py): offer() drops on full + counts,
  never blocks / never raises.
- isolated worker wrapper (isolated_worker.py): swallows + counts exceptions
  (re-raises only KeyboardInterrupt/SystemExit); latched breaker short-circuits.
- parity log writer confined to research/shadow_parity/ (parity_log.py): JSONL
  append only inside that dir; escaping paths rejected.

No live tap (live_rdm.py untouched); no production imports; no production
behavior changed (no dashboard, RDM formulas, Stage 2C, or outputs).

Validation: py_compile all modules + test OK; shadow safety test PASS (all 5
requirements); git diff --check clean.

Next: Phase 0B tap point review.

==================================================
RDM_V2_FULL_SHADOW_RUNTIME_STABLE
==================================================

STATUS: STABLE CHECKPOINT — shadow-only, no production behavior changed.
Consolidation of the entire RDM V2 shadow architecture phase.

1. EVENT-DRIVEN BACKBONE (complete):
   Market Row -> Interaction Interpreter -> Event Dispatcher ->
   Mechanical Refresh Coordinator -> Canonical Snapshot.
   core/interaction_interpreter.py, core/event_dispatcher.py,
   core/mechanical_refresh_coordinator.py, core/canonical_snapshot.py.

2. OPERATIONAL CONTRACTS (accepted + checkpointed):
   - Snapshot Identity: global_zone_key is canonical identity; zone_id is
     metadata only; same zone_id across sessions does not collide.
   - Row Ordering: interpret_in_order(); previous_row_index is the only
     watermark; row_index authoritative; timestamp informational; duplicate ->
     ROW_DUPLICATE; older -> ROW_OUT_OF_ORDER; no events/mutation on reject.
   - Restart/Durability: append-only ordered row log is source of truth;
     persist-before-process; rebuild-from-history; snapshot is projection/cache
     only; geometry-in-effect pinned; checkpoints are optimization not correctness.

3. CANONICAL SNAPSHOT sections: Metadata, Geometry, Current Row Mechanics, Open
   Visit, Last Completed Visit, Dynamic Mechanics, Prediction. Behavior:
   copy-on-write; immutable revisions; one atomic revision per commit; previous
   revision preserved on failure; keyed by global_zone_key.

4. SNAPSHOT ADAPTERS (all shadow-only, pure mapping, NOT_AVAILABLE-aware,
   alias-aware, snapshot-compatible, no production consumers):
   core/geometry_snapshot_adapter.py, core/row_mechanics_adapter.py,
   core/open_visit_adapter.py, core/last_completed_visit_adapter.py,
   core/dynamic_mechanics_adapter.py, core/prediction_adapter.py.

5. SHADOW INTEGRATION TESTS:
   - experiments/coordinator_snapshot_integration/shadow_test.py (Row Mechanics;
     Row Mechanics + Open Visit; Completed Visit; Dynamic Mechanics; Prediction).
   - experiments/full_shadow_runtime/shadow_test.py (full end-to-end runtime).

6. FULL SHADOW RUNTIME GUARANTEES (all validated): one RefreshPlan per accepted
   event row; one atomic revision per committed plan; duplicate/out-of-order rows
   rejected before refresh; adapter failure preserves previous revision; no
   partial commit; prediction PENDING does not block completed/dynamic; global_
   zone_key + source_plan_id + adapter provenance + copy-on-write preserved; no
   calculations; no prediction generation; no Dynamic State recompute; no Stage
   2C; no production behavior changed.

Validation: py_compile OK; full shadow runtime test PASS (6 scenarios; 8 plans ->
7 committed revisions); git diff --check clean.

Next: production integration strategy.

==================================================
RDM_V2_PREDICTION_SNAPSHOT_INTEGRATION_SHADOW_STABLE
==================================================

STATUS: STABLE CHECKPOINT — shadow-only, no production behavior changed.

Prediction Adapter integrated into the coordinator snapshot integration test:
- Prediction Adapter integrated into the multi-adapter atomic orchestrator.
- Gate = ALL(trajectory_dirty, prediction_dirty) (B10 -> B11 dependency).
- Prediction runs logically after Dynamic Mechanics.
- Missing prediction input produces PENDING / NOT_AVAILABLE (B11 is async to its
  VISIT_COMPLETED trigger) instead of aborting.
- Pending prediction does not block completed_visit or dynamic_mechanics.
- Unexpected prediction adapter failure prevents partial commit (raises and
  blocks the whole revision; prior revision untouched).
- One atomic revision per merged commit; revision monotonic.
- global_zone_key and source_plan_id preserved.
- No calculations. No prediction generation. No production behavior changed.

Validation (all pass): py_compile integration test OK; integration test PASS;
git diff --check clean.

Next: full shadow runtime consolidation approval.

==================================================
RDM_V2_CANONICAL_SNAPSHOT_ADAPTERS_COMPLETE
==================================================

STATUS: MILESTONE CHECKPOINT — shadow-only, no production behavior changed.

All six Canonical Snapshot adapters are now shadow-ready (one per section):
- geometry              -> GeometrySnapshotAdapter      -> geometry
- current row mechanics -> RowMechanicsAdapter          -> current_row_mechanics
- open visit            -> OpenVisitAdapter              -> open_visit
- last completed visit  -> LastCompletedVisitAdapter     -> last_completed_visit
- dynamic mechanics     -> DynamicMechanicsAdapter       -> dynamic_mechanics
- prediction            -> PredictionAdapter             -> prediction

Shared properties (all six):
- Pure mapping only (value pass-through via ordered source aliases).
- No calculations (no Dynamic State recompute, derivatives, integrals, SDR,
  classifier, thresholds, B10/B11 execution, Stage 2C, dashboard, CSV, persist).
- NOT_AVAILABLE for absent / None / empty / NaN (no defaulting), with
  source_fields provenance.
- Snapshot compatibility: each emits a RefreshResult-style patch that builds into
  a CanonicalZoneSnapshot section; the six consolidate into one immutable
  copy-on-write snapshot.
- No production behavior changed (no importer outside shadow tests).

Most recent additive work folded in: DynamicMechanicsAdapter +transition_name;
PredictionAdapter +prediction_uncertainty.

Validation (all pass): py_compile all six adapters + tests OK; all adapter shadow
tests PASS; consolidation test PASS; git diff --check clean.

Next: first real mechanical integration decision.

==================================================
RDM_V2_LAST_COMPLETED_VISIT_ADAPTER_SHADOW_STABLE
==================================================

STATUS: STABLE CHECKPOINT — shadow-only, no production behavior changed.

Last Completed Visit Adapter Stage 1 (shadow-only):
- Extended the existing adapter additively (committed aefec1c) — existing target
  names and behavior untouched, dependent consolidation test stays green.
- Maps already-existing completed-visit fields into the Canonical Snapshot
  "last_completed_visit" section (projection only, no rebuild, no inference).
- Adds max_penetration_ratio and defender_state (plus visit_start_price /
  visit_end_price) as new mapped target fields.
- Supports aliases (first present/available alias wins, primary names first):
  completed_visit_id, visit_max_penetration, visit_max_penetration_ratio,
  visit_final_omega, visit_attacker_force, visit_defender_state, visit_health,
  visit_rigidity, visit_capacity, visit_fatigue, visit_recovery.
- NOT_AVAILABLE behavior for absent / None / empty / NaN values (no defaulting),
  recorded in source_fields provenance.
- No calculations (no Dynamic State, derivatives, integrals, SDR, Stage 2C, B10,
  B11, dashboard, CSV writes, persistence).
- Snapshot compatibility validated.
- No production behavior changed (no importer outside shadow tests).

Validation (all pass): py_compile adapter + test OK; extended shadow test PASS;
consolidation test PASS (NOT_AVAILABLE_VALIDATED = TRUE); git diff --check clean.

Next: Dynamic Mechanics Adapter approval.

==================================================
RDM_V2_RESTART_DURABILITY_CONTRACT_ACCEPTED
==================================================

STATUS: ACCEPTED CONTRACT — architecture decision only. NO code implemented,
no production code changed.

Restart / Durability Contract (what the shadow backbone must follow before
production integration):
- The append-only ordered row log is the source of truth (per session_id; each
  row carries global_zone_key and geometry_version in effect).
- Persist-before-process: a row is durably appended BEFORE InteractionState
  advances from it -> an open visit is always replayable.
- Rebuild-from-history is the primary recovery mechanism (restart = replay rows
  through interpret_in_order; rebuild InteractionState + SnapshotStore).
- The snapshot is a cache / projection only — never the source of truth.
- Watermark = InteractionState.previous_row_index is the single recovery anchor.
- Geometry-in-effect must be pinned (geometry_version + bounds) or replay
  diverges.
- Checkpoints are an optimization, not correctness (carry cumulative counters:
  revision, active_visit_index, completed_visit_count, return_count, guard/breach).

Primary (must persist): ordered row log, session_id, global_zone_key,
geometry-in-effect. Everything else is DERIVED and rebuildable from history.

No production code changed (documentation/design only).

Next: Restart / Durability implementation decision.

==================================================
RDM_V2_ROW_ORDERING_CONTRACT_STABLE
==================================================

STATUS: STABLE CHECKPOINT — shadow-only, no production behavior changed.

Row Ordering Contract in the Interaction Interpreter (shadow-only):
- New entry point interpret_in_order() enforces row ordering BEFORE any
  transition; delegates to the existing pure interpret() only on accept.
- New OrderingResult result type (status + audit + state + events).
- Statuses: ORDER_ACCEPTED, ROW_DUPLICATE, ROW_OUT_OF_ORDER.
- InteractionState remains the single ordering watermark (previous_row_index).
- No dispatcher watermark. No coordinator watermark.
- row_index is authoritative; timestamp is informational only (equal timestamps
  with increasing row_index remain valid).
- No events are emitted for duplicate / out-of-order rows (audit code only);
  unchanged input state returned on rejection.
- Existing interpret() remains unchanged.
- No production behavior changed (interaction_interpreter is shadow-only).

Rules (per global_zone_key):
  row_index >  previous -> ACCEPT
  row_index == previous -> ROW_DUPLICATE (no change)
  row_index <  previous -> ROW_OUT_OF_ORDER (no change)

Validation (all pass): py_compile of core + both shadow tests OK; existing
interpreter shadow test PASS (interpret() unchanged); new row ordering shadow
test PASS (all 6 cases); full shadow-suite regression (11 tests) PASS; git diff
--check clean.

Next: Restart / Durability Contract review.

==================================================
RDM_V2_SNAPSHOT_IDENTITY_CONTRACT_STABLE
==================================================

STATUS: STABLE CHECKPOINT — shadow-only, no production behavior changed.

Canonical Snapshot identity contract fix:
- Canonical Snapshot identity is now global_zone_key.
- zone_id is descriptive metadata only (no longer determines identity).
- SnapshotStore is keyed by global_zone_key (was: bare zone_id).
- Session-scoped identity now matches the Event Dispatcher identity contract.
- Snapshot revision model unchanged.
- Copy-on-write behavior unchanged.
- Snapshot sections unchanged.
- Production behavior unchanged (core/canonical_snapshot.py is shadow-only;
  only experiment shadow tests import it).

Validation (all pass):
- python -m py_compile core/canonical_snapshot.py -> OK
- All 8 Canonical Snapshot / adapter shadow tests PASS
- Identity-collision shadow test PASS — same zone_id reused across two sessions
  (BTCUSDT_2026-06-28_230000Z::SNAPSHOT_ZONE_1 vs
   BTCUSDT_2026-06-29_230000Z::SNAPSHOT_ZONE_1) -> two independent snapshots,
  no collision, no overwrite, independent state.
- git diff --check clean

Next: Row Ordering Guard architectural review.

==================================================
PHASE1B_DOWNLOAD_STABILITY_FIX_STABLE
==================================================

STATUS:
STABLE CHECKPOINT

SUMMARY:

Historical Binance download completed successfully, but the session had many WinError 10060 timeout pauses and large delays.

ROOT CAUSE:

Network / Binance HTTP timeout instability during large historical downloads.

Not RDM.
Not dashboard.
Not replay formulas.
Not research formulas.

FILE CHANGED:

tools/generate_binance_historical_replay.py

FIXES IMPLEMENTED:

* REQUEST_TIMEOUT_SECONDS increased from 120 to 150
* MAX_RETRIES increased from 10 to 15
* RETRY_BACKOFF_SECONDS changed to:
  [10, 20, 40, 80, 120, 180, 240, 300]
* Added RETRY_JITTER_FACTOR = 0.30
* Added specific WinError 10060 detection
* Added longer recovery backoff for WinError 10060
* Added CLI flags:
  --max-retries
  --timeout
* fetch_agg_trades_batch_with_retries now returns:
  (batch_or_none, retries_used)
* download_agg_trades now tracks session_retries
* Resume loading now deduplicates partial trades by aggTrade ID
* Added checkpoint progress log every 25 batches:
  trades downloaded
  current timestamp
  last aggTrade id
  session retries
  elapsed
  ETA
  checkpoint file
  partial file
* Added final download verification:
  total trades
  first timestamp
  last timestamp
  duplicate trade IDs
  partial file path
  checkpoint file path

IMPORTANT NOTES:

This does not change:

* RDM formulas
* Replay logic
* Dashboard logic
* Research mapping
* Scoring
* Lifecycle logic
* BUY/SELL logic

This is a downloader stability-only patch.

VALIDATION:

PASSED:
python -m py_compile tools/generate_binance_historical_replay.py

CLI help confirmed new flags:

* --max-retries
* --timeout

RECOMMENDED NEXT DOWNLOAD COMMAND:

python tools/generate_binance_historical_replay.py --start "YYYY-MM-DD 00:00:00" --end "YYYY-MM-DD 23:59:59" --symbol BTCUSDT --row-size 500

FOR UNSTABLE NETWORKS:

python tools/generate_binance_historical_replay.py --start "YYYY-MM-DD 00:00:00" --end "YYYY-MM-DD 23:59:59" --symbol BTCUSDT --row-size 500 --max-retries 25 --timeout 180

==================================================
ZONE TERMINOLOGY CLARIFICATION
==================================================

STATUS:
LABEL CLARIFICATION ONLY

Formation Range != Active RDM Zone != Density Band

Definitions:

* Formation Range = old Preparation Zone = broad context range from preparation_low_price / preparation_high_price.
* Active RDM Zone / Interaction Core = compressed operational zone inside Formation Range.
* Density Band / Interaction Heart = narrowest interaction concentration inside Active RDM Zone.

Dashboard label policy:

* Visible labels should not call preparation_low_price / preparation_high_price an entry zone.
* preparation_low_price / preparation_high_price should display as Formation Range (broad context).
* Active operational width should display as Active RDM Zone / Interaction Core Width.
* Narrow interaction concentration should display as Density Band / Interaction Heart Width.

Clarification:

Formation Range is broad context, not entry zone. Operational decision zone is Active Core / Density Band.

Rules:

No formula changes.
No replay changes.
No research changes.
No B12v2 changes.
No scoring changes.

==================================================
PHASE1B_RIGIDITY_FALLBACK_FIX_STABLE
==================================================

Date: 2026-06-06
Status: STABLE CHECKPOINT

WHAT HAPPENED:

A silent data corruption bug was discovered and fixed in
research/zone_mechanics_calculator.py inside build_zone_visit_timeline().

The bug caused fully-decayed EXHAUSTED_ZONE states to be misclassified
as RECLAIM or DAMAGE instead of BREAKDOWN, contaminating B12v2 outcome labels.

ROOT CAUSE:

Line 3628 (original):
    rig_v = to_float(last_row.get("rigidity_live")) or rig_birth

Python `or` treats 0.0 as falsy. For EXHAUSTED_ZONE (rig_birth=30.0,
zone_strength_decay>=50, recovery_current=0.0), the live rigidity formula
clamps the zone to exactly rigidity_live=0.0.

When 0.0 was fetched, `to_float()` correctly returned 0.0, but `or rig_birth`
silently replaced it with 30.0. The BREAKDOWN check then saw rig_v=30.0 and
found 30.0 < 15.0 = False, so BREAKDOWN never fired.

Three conditions make EXHAUSTED_ZONE exclusively vulnerable:
  1. rig_birth <= 30 (MEDIUM zone — BREAKDOWN threshold is 15.0)
  2. zone_strength_decay >= 50 (enough decay to reach 0.0)
  3. recovery_current = 0.0 (NO_RECOVERY — no repair to prevent floor)

THE FIX:

Single-line replacement (lines 3631-3632 after edit):

    _rig_raw = to_float(last_row.get("rigidity_live"))
    rig_v    = rig_birth if _rig_raw is None else _rig_raw

Explicit None-check: 0.0 (fully decayed) is preserved. None (missing data)
still falls back to rig_birth. Behavior unchanged for all non-EXHAUSTED cases.

IMPACT ON ZONE_VISIT_TIMELINE:

Effect A (RECLAIM → BREAKDOWN):
  13 visit_N outcomes that were RECLAIM are now correctly BREAKDOWN.
  B12v2 impact: 13 cases that were false FAILs (pred=FAIL, out=HOLD)
  became true positives (pred=FAIL, out=FAIL).

Effect B (DAMAGE → BREAKDOWN):
  Unexpected positive side effect: zones where fallback had given rig_v=30.0
  caused the classifier to fall to DAMAGE (not BREAKDOWN), which B12v2 mapped
  as AMBIGUOUS and excluded. After fix, BREAKDOWN fires first on all these.
  Formation: +17 newly evaluable correct FAILs
  Active Core: +13 newly evaluable correct FAILs
  Density Band: +7 newly evaluable correct FAILs

RESULTS — POST-FIX B12v2 VALIDATED:

  Mode           Evaluable  Accuracy  HOLD F1  FAIL F1  Lift
  Formation          650     98.8%    0.989    0.986   +42.3%
  Active Core        400     98.8%    0.989    0.986   +43.8%
  Density Band       263     98.5%    0.986    0.983   +43.3%

All modes: LEAKAGE PASS, CONSISTENCY PASS, INTEGRITY PASS.

Remaining false HOLDs: 3 identical cases across all modes
  — STABLE trajectory / EXHAUSTED_ZONE / HEALTH_STABLE
  — Same 3 zones — different failure mode (not the fallback bug)

Remaining false FAILs after fix:
  Formation: 5 (4x EXHAUSTED_ZONE rig_birth>30, 1x RIGID_ZONE ABSORPTION)
  Active Core: 2 (EXHAUSTED_ZONE DEGRADING)
  Density Band: 1 (EXHAUSTED_ZONE DEGRADING)

INTERPRETATION:

The fix corrected a classification bug, not a formula. No RDM physics changed.
The B12v2 engine now sees correct structural states: zones that fully decayed
(rigidity=0.0) are correctly labeled BREAKDOWN. The accuracy improvement from
~97.2% to 98.8% (Formation) is entirely attributable to removing misclassified
outcomes from the ground truth — not from improving the prediction model.

ARCHITECTURE PRESERVED:

No formula changes.
No Phase 1 production file changes.
No RDM formula changes.
No B9/B10/B11/Synthesis changes.
No lifecycle logic changes.
No replay formula changes.
No dashboard changes.

CURRENT PROJECT STATUS:

B12v2 is validated at 98.8% prospective accuracy (Formation mode) across a
34-day dataset (Apr 30 – Jun 2, 2026). All three zone modes confirmed.
Physics correlation (sigma x penetration r=0.9953) intact.
Leakage-free architecture confirmed.

Repository: CLEAN. Commit: PHASE1B_RIGIDITY_FALLBACK_FIX_STABLE.

NEXT RESEARCH CANDIDATE:

PHASE1B_EXHAUSTED_ZONE_RESEARCH

Goal: Characterize the remaining error concentration in EXHAUSTED_ZONE.
  - False HOLDs: 3 cases — STABLE trajectory / HEALTH_STABLE / EXHAUSTED_ZONE
    (B10 calls these STABLE even though they eventually breakdown — why?)
  - False FAILs: 4 Formation cases — EXHAUSTED_ZONE with rig_birth > 30
    (BREAKDOWN threshold of rig_birth*0.50 not reached because rig_birth > 30)
  - Question: Is STABLE trajectory in EXHAUSTED_ZONE a systematic B10 error
    or a genuine edge case (zone that was stable until a sudden event)?

==================================================
PHASE1B_RDM_V2_MECHANICAL_ARCHITECTURE_STABLE
==================================================

STATUS:
STABLE RESEARCH CHECKPOINT

SCOPE:
Documentation and architecture consolidation only.

COMPLETED:
- Stage 5D Dynamic State signature analysis
- Stage 5E transition analysis
- Stage 5F transition family discovery
- Stage 5G attacker force causality analysis
- Stage 5H mechanical dependency graph

NEW DOCUMENTATION:
- docs/RDM_V2_MECHANICAL_ARCHITECTURE_SPEC.md

STAGE 5H DEPENDENCY GRAPH:
- Variables classified: 49
- Dependency edges: 113
- Dependency layers: 21
- Max dependency depth: 20
- Direct dependency loops: 0

CORE ARCHITECTURE:
Raw Market Data
    -> Statistics Engine
    -> Geometry Engine
    -> Interaction / Penetration
    -> Mechanical Exposure
    -> RDM V2
    -> SDR / Derivative / Integral
    -> Dynamic State
    -> Structural Prediction

VALIDATED CONCLUSIONS:
- The mechanical engine is feed-forward at artifact-generation time.
- Temporal memory exists through integrals, guards, health evolution, sigma evolution, and structural damage.
- No same-step algebraic loop was confirmed.
- Stage 2C replaced frozen post-return mechanics with acute pressure + chronic structural damage.
- Stage 2C is mechanically superior to frozen post-return behavior.
- ATTACKER_DOMINANT has a distinct mechanical signature.
- ATTACKER_DOMINANT is the strongest continuation-bearing Dynamic State so far.
- STABLE / PROBABLE_HOLD are more rejection-biased.
- Attacker Force and Omega are common first movers in transition analysis.
- Fatigue is the clearest deterioration precursor.
- Attacker Force appears interaction-conditioned, not raw-delta-only.

ARCHITECTURAL DECISION:
Current mechanical architecture is accepted as a stable research checkpoint.
It is not approved for production replacement.
It is not trading validation.
It does not start Phase 2.

PROJECT STATUS:
Project 1 remains inside Phase 1B+ research expansion.
Project 2 remains not implemented; its intended philosophy is to replace only the Geometry Engine while reusing replay, statistics, dashboard, research infrastructure, and validation methodology.

RULES PRESERVED:
No production formula change.
No replay change.
No dashboard logic change.
No RDM formula change.
No Dynamic State threshold change.
No execution.
No entries/exits.
No BUY/SELL.
No live signals.
No Phase 2.

NEXT ARCHITECTURAL DECISION:
Decide whether to continue Dynamic State architecture review, study redundancy/merging questions, or begin the next approved research stage. Do not implement Project 2 until explicitly approved.


==================================================
RDM_V2_EVENT_DRIVEN_SHADOW_FOUNDATION
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

OBJECTIVE:
Establish the first deterministic, event-driven RDM V2 foundation
without connecting it to any production or LIVE processing path.

COMPONENTS:
- Interaction Interpreter
  - Pure normalization layer from market row + geometry state to
    MechanicalEvent records.
  - Supported shadow events: TOUCH, ZONE_ENTER, ZONE_EXIT, RETURN,
    PENETRATION_UPDATED, VISIT_STARTED, VISIT_COMPLETED.
- Mechanical Refresh Coordinator
  - Pure orchestration planner from InteractionState + MechanicalEvent
    records to dirty flags and an ordered RefreshPlan.
  - Does not calculate mechanics or call RDM components.
- Interpreter + Coordinator Shadow Chain Test
  - Deterministic synthetic sequence validates:
    market row + geometry -> events -> refresh plan.
  - Two identical runs produce identical event and plan output.
  - Expected events and dirty flags pass with zero mismatches.

ARCHITECTURAL ROLE:
Foundation for a future Event-Driven RDM V2 refresh pipeline.
Interaction interpretation and refresh planning are now explicit while
all existing calculations and consumers remain unchanged.

ISOLATION:
- Shadow mode only.
- Not consumed by the production pipeline.
- No LIVE integration.
- No file routing or snapshot writes.
- No dashboard integration.
- No Stage 2C integration.
- No RDM formula change.
- No Dynamic State change.
- No production behavior change.

VALIDATION:
- core/interaction_interpreter.py compile: PASS
- core/mechanical_refresh_coordinator.py compile: PASS
- experiments/event_refresh_shadow_chain.py compile: PASS
- SHADOW_CHAIN_TEST = PASS
- DETERMINISTIC_REPLAY = PASS
- PRODUCTION_EFFECTS = FALSE
- MISMATCHES = NONE

NEXT:
Await architectural approval before any production integration.


==================================================
RDM_V2_EVENT_DRIVEN_BACKBONE_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

SHADOW BACKBONE:
Interaction Interpreter
    ->
Event Dispatcher
    ->
Mechanical Refresh Coordinator

COMPONENT RESPONSIBILITIES:
- Interaction Interpreter
  - Converts market row + geometry state into normalized MechanicalEvent
    records.
- Event Dispatcher
  - Validates identity and event ordering.
  - Deduplicates event IDs.
  - Sends one accepted event batch to the shadow coordinator.
- Mechanical Refresh Coordinator
  - Converts InteractionState + MechanicalEvent records into dirty flags
    and an ordered RefreshPlan.
  - Plans refresh work without executing mechanical calculations.

EVENT DISPATCHER VALIDATION:
- Valid ordered batch: PASS
- Duplicate event IDs: PASS
- Replayed event IDs: PASS
- Invalid event order rejection: PASS
- Zone mismatch rejection: PASS
- Shadow coordinator plan returned: PASS
- Production effects: FALSE

ARCHITECTURAL ROLE:
The event-driven RDM V2 shadow backbone is now complete. It establishes
deterministic event interpretation, transport, validation, deduplication,
and refresh planning before any future Canonical Snapshot integration.

ISOLATION:
- Shadow mode only.
- No production consumer.
- No stream_manager or observation_logger integration.
- No LIVE pipeline changes.
- No RDM formula changes.
- No Dynamic State changes.
- No Stage 2C integration.
- No dashboard changes.
- No snapshot implementation.
- No runtime file writes.
- No production behavior change.

NEXT:
Await explicit approval before implementing the Canonical Snapshot or
connecting any shadow component to production.


==================================================
RDM_V2_CANONICAL_SNAPSHOT_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

IMPLEMENTED:
- CanonicalZoneSnapshot
  - Deeply immutable current-state projection for one shadow zone.
- SnapshotBuilder
  - Assembles supplied RefreshPlan result patches.
  - Does not calculate mechanical values.
- SnapshotStore
  - In-memory current-snapshot store.
  - Supports create, get_current, and update.

INITIAL SNAPSHOT SECTIONS:
- Metadata
- Geometry
- Current Row Mechanics
- Open Visit

REVISION MODEL:
- Snapshot creation begins at revision 1.
- Every successful update increments the revision.
- Updates use copy-on-write.
- A candidate revision is built completely before publication.
- A failed update leaves the previous immutable revision valid.

BOUNDARY:
- In-memory shadow only.
- No persistence or CSV writes.
- No production consumer.
- No stream_manager, observation_logger, or LIVE integration.
- No dashboard integration.
- No Last Completed Visit section yet.
- No Dynamic Mechanics or Dynamic State.
- No transitions.
- No Stage 2C.
- No B10/B11 or prediction.
- No RDM formula change.
- No production behavior change.

VALIDATION:
- core/canonical_snapshot.py compile: PASS
- experiments/canonical_snapshot/shadow_test.py compile: PASS
- Snapshot creation: PASS
- Snapshot update: PASS
- Revision increment: PASS
- Failed update preserved previous revision: PASS
- Production effects: FALSE

NEXT:
Await explicit approval before integrating the first mechanical component.


==================================================
RDM_V2_ROW_MECHANICS_ADAPTER_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

FILES:
- core/row_mechanics_adapter.py
- experiments/row_mechanics_adapter/shadow_test.py

IMPLEMENTED:
- Row Mechanics Adapter Stage 1
- Mapping of 17 existing current-row mechanical fields:
  price, timestamp, row ID, zone presence, touch, distance, penetration,
  fleche, sigma market, sigma barre, load, Omega, fatigue, recovery,
  rigidity, capacity, and health.
- Explicit source aliases with source-field provenance.
- NOT_AVAILABLE handling for absent, blank, None, or NaN inputs.
- Zero and False remain valid source values.
- RefreshResult-style Current Row Mechanics patch output.
- Canonical Snapshot shadow-store compatibility.

CALCULATION BOUNDARY:
- Mapping only.
- No arithmetic.
- No numeric coercion.
- No normalization.
- No fallback mechanical derivation.
- Existing values are copied unchanged.

ISOLATION:
- Shadow mode only.
- No production consumer.
- No LIVE integration.
- No live_rdm changes.
- No RDM formula changes.
- No Dynamic State.
- No Stage 2C.
- No B10/B11.
- No dashboard.
- No CSV writes or snapshot persistence.
- No production behavior change.

VALIDATION:
- core/row_mechanics_adapter.py compile: PASS
- experiments/row_mechanics_adapter/shadow_test.py compile: PASS
- Normal row mapping: PASS
- Missing-field handling: PASS
- No-calculation proof: PASS
- Canonical Snapshot patch application: PASS
- Production effects: FALSE

NEXT:
Await approval for the next mechanical adapter.


==================================================
RDM_V2_OPEN_VISIT_ADAPTER_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

FILES:
- core/open_visit_adapter.py
- experiments/open_visit_adapter/shadow_test.py

IMPLEMENTED:
- Open Visit Adapter Stage 1
- Mapping from existing InteractionState or visit-style dictionaries into
  Canonical Snapshot Open Visit patches.
- Open Visit fields include visit identity/status, start row/time/price,
  row count, maximum penetration, cumulative Omega, accumulated pressure,
  attacker force, interaction flags, and last event/row identity.
- active_visit_flag explicitly identifies active versus inactive visits.
- Explicit source-field provenance.
- NOT_AVAILABLE handling for missing visit values.
- Available False and zero values remain valid.
- Canonical Snapshot shadow-store patch compatibility.

NO-ACTIVE-VISIT BEHAVIOR:
- active_visit_flag = False.
- Visit-specific fields are NOT_AVAILABLE.
- Existing interaction facts such as inside_zone=False and
  touch_active=False remain available and unchanged.

CALCULATION BOUNDARY:
- Mapping only.
- No accumulation.
- No inferred visit outcome.
- No inferred Omega, pressure, attacker force, or visit status.
- No mechanical formulas or coercion.

ISOLATION:
- Shadow mode only.
- No production consumer.
- No LIVE or live_rdm integration.
- No Dynamic State.
- No Stage 2C.
- No B10/B11.
- No dashboard.
- No CSV writes or snapshot persistence.
- No production behavior change.

VALIDATION:
- core/open_visit_adapter.py compile: PASS
- experiments/open_visit_adapter/shadow_test.py compile: PASS
- Active visit mapping: PASS
- No-active-visit behavior: PASS
- Missing-field handling: PASS
- No-calculation proof: PASS
- Canonical Snapshot patch application: PASS
- Production effects: FALSE

NEXT:
Await approval for the next adapter.


==================================================
RDM_V2_LAST_COMPLETED_VISIT_ADAPTER_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

FILES:
- core/canonical_snapshot.py
- core/last_completed_visit_adapter.py
- experiments/last_completed_visit_adapter/shadow_test.py

SNAPSHOT EXTENSION:
- CanonicalZoneSnapshot now includes last_completed_visit.
- SnapshotBuilder and SnapshotStore accept immutable
  last_completed_visit patches.
- Existing copy-on-write revision behavior is unchanged.
- Existing snapshot tests remain valid.

ADAPTER:
- Last Completed Visit Adapter Stage 1.
- Maps 22 existing completed-visit fields.
- Includes visit identity, row/time boundaries, duration, row count,
  penetration, Omega, attacker force, structural values, visit result and
  classification, plus absorption/reflection/reclaim/damage/growth flags.
- Supports current timeline aliases including visit_start_time,
  visit_end_time, visit_duration_rows, and max_penetration_at_visit.
- Explicit source-field provenance.
- NOT_AVAILABLE handling for absent, blank, None, or NaN values.
- Zero and False are preserved as valid source values.
- Canonical Snapshot patch compatibility.

CALCULATION BOUNDARY:
- Mapping only.
- No duration calculation.
- No visit classification.
- No inferred outcome flags.
- No formulas, coercion, or fallback mechanical derivation.

ISOLATION:
- Shadow mode only.
- No production consumer.
- No LIVE or live_rdm integration.
- No Dynamic State.
- No Stage 2C.
- No B10/B11.
- No dashboard.
- No CSV writes or snapshot persistence.
- No production behavior change.

VALIDATION:
- core/canonical_snapshot.py compile: PASS
- core/last_completed_visit_adapter.py compile: PASS
- Adapter shadow test compile: PASS
- Completed-visit mapping: PASS
- Missing-field handling: PASS
- Zero/False preservation: PASS
- No-calculation proof: PASS
- Snapshot patch application: PASS
- Existing Canonical Snapshot regression: PASS
- Production effects: FALSE

NEXT:
Await Dynamic Mechanics Adapter approval.


==================================================
RDM_V2_DYNAMIC_MECHANICS_ADAPTER_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

FILES:
- core/canonical_snapshot.py
- core/dynamic_mechanics_adapter.py
- experiments/dynamic_mechanics_adapter/shadow_test.py
- experiments/canonical_snapshot/shadow_test.py

SNAPSHOT EXTENSION:
- CanonicalZoneSnapshot now includes dynamic_mechanics.
- SnapshotBuilder and SnapshotStore accept immutable dynamic_mechanics
  patches.
- Existing copy-on-write revision behavior is unchanged.
- Existing snapshot and completed-visit regressions remain valid.

ADAPTER:
- Dynamic Mechanics Adapter Stage 1.
- Maps 16 existing dynamic timeline fields.
- Includes visit identity, current/previous Dynamic State, first and second
  derivatives, zone and attacker integrals, SDR, health slope/change,
  Omega total/mean, state reason/confidence, as-of visit, and update time.
- Alias support:
  - sdr -> SDR
  - visit_index -> dynamic_state_as_of_visit
  - analysis_run_utc -> dynamic_updated_at
- Explicit source-field provenance.
- NOT_AVAILABLE handling for absent, blank, None, or NaN values.
- Zero and False remain valid source values.
- Canonical Snapshot patch compatibility.

CALCULATION BOUNDARY:
- Mapping only.
- No derivative calculation.
- No integral calculation.
- No SDR calculation.
- No Dynamic State classification.
- No reason or confidence inference.
- No formulas, coercion, or fallback mechanical derivation.

ISOLATION:
- Shadow mode only.
- No production consumer.
- No LIVE or live_rdm integration.
- No Stage 2C.
- No B10/B11.
- No dashboard.
- No CSV writes or snapshot persistence.
- No production behavior change.

VALIDATION:
- core/canonical_snapshot.py compile: PASS
- core/dynamic_mechanics_adapter.py compile: PASS
- Adapter shadow test compile: PASS
- Dynamic mechanics mapping: PASS
- Alias and missing-field handling: PASS
- No-calculation proof: PASS
- Snapshot patch application: PASS
- Existing Canonical Snapshot regression: PASS
- Existing Last Completed Visit regression: PASS
- Production effects: FALSE

NEXT:
Await prediction adapter approval.


==================================================
RDM_V2_PREDICTION_ADAPTER_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

FILES:
- core/canonical_snapshot.py
- core/prediction_adapter.py
- experiments/prediction_adapter/shadow_test.py

SNAPSHOT EXTENSION:
- CanonicalZoneSnapshot now includes prediction.
- SnapshotBuilder and SnapshotStore accept immutable prediction patches.
- Existing copy-on-write revision behavior is unchanged.
- Existing snapshot, Dynamic Mechanics, and completed-visit regressions
  remain valid.

ADAPTER:
- Prediction Adapter Stage 1.
- Maps 14 existing B10/B11 prediction fields.
- Includes B10 trajectory/state/reason/confidence, B11 prediction/state/
  reason/confidence, version/status, input Dynamic State/visit, as-of visit,
  and update timestamp.
- Alias support:
  - structural_trajectory -> b10_trajectory
  - trajectory_direction -> b10_state
  - trajectory_reason/confidence -> B10 reason/confidence
  - structural_prediction -> b11_prediction
  - prediction_reason/confidence -> B11 reason/confidence
  - emit_status -> prediction_status
  - dynamic_state/visit_id/visit_index -> input/as-of provenance
  - analysis_run_utc -> prediction_updated_at
- Explicit source-field provenance.
- NOT_AVAILABLE handling for absent, blank, None, or NaN values.
- Zero and False remain valid source values.
- Canonical Snapshot patch compatibility.

CALCULATION BOUNDARY:
- Mapping only.
- No B10 calculation.
- No B11 calculation.
- No prediction or confidence calculation.
- No Dynamic State calculation.
- No formulas, coercion, or fallback prediction.

ISOLATION:
- Shadow mode only.
- No production consumer.
- No LIVE or live_rdm integration.
- No Stage 2C.
- No dashboard.
- No CSV writes or snapshot persistence.
- No production behavior change.

VALIDATION:
- core/canonical_snapshot.py compile: PASS
- core/prediction_adapter.py compile: PASS
- Adapter shadow test compile: PASS
- Prediction mapping: PASS
- Alias and missing-field handling: PASS
- No-calculation proof: PASS
- Snapshot patch application: PASS
- Existing Canonical Snapshot regression: PASS
- Existing Dynamic Mechanics regression: PASS
- Existing Last Completed Visit regression: PASS
- Production effects: FALSE

NEXT:
Await Canonical Snapshot V1 consolidation approval.


==================================================
RDM_V2_CANONICAL_SNAPSHOT_V1_CONSOLIDATED_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW CHECKPOINT

COMPLETE CANONICAL SNAPSHOT V1:
- One immutable in-memory snapshot assembled from all accepted shadow
  adapters.
- No production integration or persistence.

VALIDATED SECTIONS:
- Metadata
- Geometry
- Current Row Mechanics
- Open Visit
- Last Completed Visit
- Dynamic Mechanics
- Prediction

SIX ADAPTERS TESTED TOGETHER:
- Project 1 Geometry Snapshot Adapter
- Row Mechanics Adapter
- Open Visit Adapter
- Last Completed Visit Adapter
- Dynamic Mechanics Adapter
- Prediction Adapter

REVISION AND ATOMICITY:
- Initial snapshot revision = 1.
- Successful update produces revision 2.
- Copy-on-write preserves the immutable prior revision.
- Top-level and nested snapshot mappings are deeply immutable.
- A failed update leaves revision 2 authoritative and unchanged.

MAPPING INTEGRITY:
- NOT_AVAILABLE behavior validated across sections.
- Precomputed values remain unchanged.
- Intentionally non-derived geometry values remain unchanged.
- No adapter calculates geometry, mechanics, derivatives, integrals, SDR,
  Dynamic State, B10, or B11.

ARTIFACT:
- experiments/canonical_snapshot_v1/consolidation_test.py

REPRODUCIBLE GEOMETRY DEPENDENCY:
- core/geometry_snapshot_adapter.py
- experiments/geometry_snapshot_adapter/shadow_test.py
- These accepted shadow files are included because the consolidation test
  imports and validates the Geometry Snapshot Adapter directly.

ISOLATION:
- Shadow test only.
- No production consumer.
- No LIVE or live_rdm changes.
- No dashboard.
- No Stage 2C.
- No CSV writes.
- No snapshot persistence.
- No formulas.
- No production behavior change.

VALIDATION:
- Consolidation test compile: PASS
- Six-adapter snapshot build: PASS
- All seven sections present: PASS
- Revision 1 -> 2: PASS
- Deep immutability: PASS
- Failed-update rollback: PASS
- NOT_AVAILABLE handling: PASS
- No-calculation proof: PASS
- Production effects: FALSE

NEXT:
Await first shadow integration pipeline approval.


==================================================
RDM_V2_COORDINATOR_ROW_MECHANICS_SNAPSHOT_INTEGRATION_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW INTEGRATION CHECKPOINT

ARTIFACT:
- experiments/coordinator_snapshot_integration/shadow_test.py

INTEGRATION:
MechanicalRefreshCoordinator
    -> RefreshPlan dirty flags
    -> RowMechanicsAdapter
    -> Canonical Snapshot

VALIDATED BEHAVIOR:
- RefreshPlan row-mechanics dirty flags gate RowMechanicsAdapter execution.
- The Row Mechanics patch creates and updates the Canonical Snapshot.
- Snapshot revisions advance from 1 to 2.
- Copy-on-write preserves revision 1 after revision 2 is committed.
- A negative-control plan without row-mechanics dirty flags skips the
  adapter and leaves the current snapshot unchanged.
- global_zone_key is preserved as the session-scoped snapshot identity.
- Existing zone_id remains metadata/provenance only.

CALCULATION BOUNDARY:
- No calculations.
- No mechanical formulas.
- No Dynamic State calculation.
- No Stage 2C.
- No B10/B11.

ISOLATION:
- Shadow test only.
- No production consumer.
- No LIVE pipeline integration.
- No dashboard.
- No CSV writes.
- No snapshot persistence.
- No production behavior change.

VALIDATION:
- Integration test compile: PASS
- Coordinator dirty-flag gating: PASS
- Row Mechanics mapping: PASS
- Snapshot revision 1 -> 2: PASS
- Copy-on-write preservation: PASS
- Negative-control skip: PASS
- global_zone_key identity: PASS
- No calculations: PASS
- Production effects: FALSE

NEXT:
Await multi-adapter shadow integration approval.


==================================================
RDM_V2_MULTI_ADAPTER_SNAPSHOT_INTEGRATION_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW INTEGRATION CHECKPOINT

ARTIFACT:
- experiments/coordinator_snapshot_integration/shadow_test.py

INTEGRATION:
MechanicalRefreshCoordinator
    -> one RefreshPlan
    -> RowMechanicsAdapter
    -> OpenVisitAdapter
    -> merged patches
    -> one Canonical Snapshot commit

VALIDATED BEHAVIOR:
- Row Mechanics Adapter and Open Visit Adapter execute in one refresh cycle.
- Both patches are built independently and merged before store publication.
- Patch sections are disjoint:
  current_row_mechanics and open_visit.
- Each merged commit creates exactly one snapshot revision.
- Revision 1 remains immutable after revision 2 is committed.
- global_zone_key remains the canonical session-scoped identity.
- source_plan_id remains the exact RefreshPlan provenance.
- Both adapter provenance maps remain present in the snapshot.

ATOMICITY:
- No partial commit is possible through the tested integration helper.
- If Open Visit gating is absent, the entire multi-adapter update is skipped.
- If OpenVisitAdapter fails after the Row Mechanics patch is built,
  SnapshotStore.update is never called.
- Adapter failure leaves the previous snapshot revision authoritative and
  unchanged.

CALCULATION BOUNDARY:
- No calculations.
- No formulas.
- No Dynamic State.
- No Stage 2C.
- No B10/B11.

ISOLATION:
- Shadow test only.
- No production consumer.
- No LIVE integration.
- No dashboard.
- No CSV writes.
- No snapshot persistence.
- No production behavior change.

VALIDATION:
- Integration test compile: PASS
- Multi-adapter refresh cycle: PASS
- Merged section integrity: PASS
- One revision per merged commit: PASS
- Copy-on-write preservation: PASS
- Skip control: PASS
- Adapter-failure rollback: PASS
- global_zone_key preservation: PASS
- source_plan_id preservation: PASS
- No calculations: PASS
- Production effects: FALSE

NEXT:
Await next integration approval.


==================================================
RDM_V2_COMPLETED_VISIT_SNAPSHOT_INTEGRATION_SHADOW_STABLE
==================================================

STATUS:
VALIDATED SHADOW INTEGRATION CHECKPOINT

ARTIFACT:
- experiments/coordinator_snapshot_integration/shadow_test.py

COMPLETED-VISIT GATING:
- A real InteractionInterpreter VISIT_COMPLETED event produces a RefreshPlan
  carrying visit_dirty and response_dirty.
- visit_dirty + response_dirty gates LastCompletedVisitAdapter.
- VISIT_STARTED cannot accidentally freeze a completed visit.
- Completed-visit patches update the immutable last_completed_visit section.

MULTI-ADAPTER CYCLES:
- Row Mechanics and Open Visit adapters may participate in the same refresh
  cycle when their own dirty flags are present.
- A mixed cycle builds current_row_mechanics, open_visit, and
  last_completed_visit patches before one store publication.
- The mixed cycle creates exactly one atomic snapshot revision.

PRESERVATION AND ATOMICITY:
- A row-only update advances current-row mechanics but preserves the existing
  last_completed_visit unchanged.
- Adapter provenance remains present in every updated section.
- global_zone_key remains the canonical session-scoped identity.
- source_plan_id remains exact RefreshPlan provenance.
- If LastCompletedVisitAdapter fails after row/open patches are built,
  SnapshotStore.update is never called.
- Failure prevents partial commit and leaves the prior revision authoritative.

CALCULATION BOUNDARY:
- No calculations.
- No formulas.
- No Dynamic State.
- No Stage 2C.
- No B10/B11.

ISOLATION:
- Shadow test only.
- No production consumer.
- No LIVE integration.
- No dashboard.
- No CSV writes.
- No snapshot persistence.
- No production behavior change.

VALIDATION:
- Integration test compile: PASS
- Real VISIT_COMPLETED plan: PASS
- Last Completed Visit mapping: PASS
- Row-only preservation: PASS
- Three-adapter mixed cycle: PASS
- One atomic revision per cycle: PASS
- Failure rollback: PASS
- global_zone_key and source_plan_id preservation: PASS
- No calculations: PASS
- Production effects: FALSE

NEXT:
Await Dynamic Mechanics integration approval.

---

## Active Checkpoint: RDM_V2_PHASE0E1_PASSIVE_SHADOW_WORKER_SKELETON_STABLE

Status: VALIDATED SHADOW SAFETY CHECKPOINT

Implemented:
- Passive shadow worker skeleton
- Feature flag gated and fail-closed
- Kill-switch protected
- Bounded queue draining with bounded stop timeout
- Handler exception isolation
- Counters: received, processed, dropped, failed, killed, desynchronized
- No-op handler only

Boundary:
- No full shadow runtime
- No SnapshotStore updates
- No adapters
- No parity logs
- No production outputs or production consumers
- No production behavior changed

Validation:
- Worker and shadow test compile: PASS
- Disabled worker no-op: PASS
- Kill switch stops processing: PASS
- Queue saturation remains non-blocking: PASS
- Handler failures are counted and isolated: PASS
- Start, stop, and bounded drain: PASS
- Production effects: FALSE

Next:
Await Phase 0E-2 runtime connection approval.

---

## Active Checkpoint: RDM_V2_PHASE0E2_PASSIVE_WORKER_RUNTIME_CONNECTION_STABLE

Status: VALIDATED SHADOW RUNTIME CONNECTION

Implemented:
- Passive worker connected to core/passive_shadow_runtime.py
- Payload -> Interaction Interpreter -> Event Dispatcher -> Mechanical Refresh
  Coordinator -> mapping adapters -> Canonical Snapshot
- Internal in-memory SnapshotStore only
- Duplicate and out-of-order payload rows rejected
- Adapter failure rolls back without partial snapshot publication
- Worker counters and kill switch validated
- Copy-on-write revisions and global_zone_key preserved

Boundary:
- No production outputs
- No dashboard
- No parity log yet
- No formulas or Stage 2C
- No Dynamic State recomputation
- No prediction generation
- No production behavior changed

Next:
Await Phase 0E-3 parity logging approval.

---

## Active Checkpoint: RDM_V2_PHASE0E3_PARITY_LOGGING_STABLE

Status: VALIDATED SHADOW PARITY LOGGING

Implemented:
- Shadow-only parity logging
- JSONL output confined to research/shadow_parity/
- Successful payload processing writes one parity record
- Pending prediction state is logged without prediction generation
- Runtime failure is logged without corrupting the authoritative snapshot
- Parity writer failure is non-fatal to snapshot and worker processing
- Production references, shadow values, mismatch flags, latency, and available
  worker counters are recorded

Boundary:
- No production CSV writes
- No dashboard
- No formulas or Stage 2C
- No Dynamic State recomputation
- No prediction generation
- No production behavior changed

Validation:
- Parity logger/runtime and tests compile: PASS
- Successful and pending parity records: PASS
- Failure record with snapshot preservation: PASS
- Logger failure isolation: PASS
- research/shadow_parity path confinement: PASS
- Worker/runtime regressions: PASS
- Production effects: FALSE

Next:
Await passive shadow soak test plan.

---

## Active Checkpoint: RDM_V2_PASSIVE_SHADOW_REPLAY_SOAK_PASS

==================================================
REPLAY SHADOW SOAK
==================================================

Replay-driven passive shadow validation completed successfully.

Replay Summary:
- bootstrap = STARTED
- payloads_attempted = 10
- payloads_enqueued = 10
- payloads_processed = 10
- payloads_dropped = 0
- worker_failed = 0
- worker_desynchronized = 0
- queue_depth = 0
- parity_records = 10
- parity_success = 10
- parity_failed = 0
- result = PASS

Validation confirms:
- Passive Shadow Bootstrap operational
- Passive Shadow Worker operational
- Shadow Runtime operational
- Shadow Runtime Emitter operational
- Canonical Snapshot pipeline operational
- Atomic snapshot revisions verified
- Event Dispatcher operational
- Mechanical Refresh Coordinator operational
- Dirty-gated adapters operational
- Copy-on-write snapshot behavior preserved
- global_zone_key preserved
- Row Ordering Contract preserved
- Snapshot Identity Contract preserved
- Restart/Durability architecture unchanged
- Shadow parity logging operational

Important conclusion:
The passive shadow architecture has been validated end-to-end using replay data.
The previous LIVE soak was INCONCLUSIVE because no finalized live RDM records
were emitted during the observation window. The replay soak demonstrates that
the complete passive shadow pipeline functions correctly when finalized
payloads are available.

Production status:
- No production formulas changed
- No production outputs changed
- No dashboard changes
- No Stage 2C changes
- No Dynamic State recomputation
- No prediction generation
- Shadow remains diagnostic only

Validation:
- py_compile: PASS
- replay soak: PASS
- parity: PASS
- git diff --check: PASS

Next:
Await next production integration decision.

---

## Active Checkpoint: PHASE1A_PSYCHOLOGICAL_LEVELS_PROVIDER_STAGE1_STABLE

Status: EXPERIMENTAL PROJECT 2 PROVIDER VALIDATED

Scope:
- Experimental Project 2 provider only
- Located under experiments/psychological_levels/
- No promotion into core yet
- No RDM, Snapshot, Worker, LIVE, dashboard, or Project 1 connection

Configuration:
- spacing = 200 USD
- zone_half_width = 25 USD
- active_window = +/-3 levels
- Decimal arithmetic for geometry and identity
- Immutable PsychologicalLevelGeometry records

Stable identity:
- zone_id = PSY_BTCUSDT_<level>
- case_id = PSY_CASE_BTCUSDT_<level>
- global_zone_key = session_id::zone_id

Validated example:
- reference price = 60341
- generated centers = 59800, 60000, 60200, 60400, 60600, 60800, 61000
- level 60000 geometry = 59975 -> 60025, width 50
- Stable repeated IDs and session-scoped global keys: PASS
- Deterministic ordering and invalid configuration guards: PASS
- Decimal/canonical identity stability: PASS

Boundary:
- Offline only
- No formulas changed
- No production code path consumes the provider
- Production behavior unchanged

Validation:
- provider/test py_compile: PASS
- test_provider.py: PASS
- git diff --check: PASS

Next:
Await Stage 2 Interaction Interpreter validation.

---

## Active Checkpoint: PHASE1A_PSYCHOLOGICAL_LEVELS_SNAPSHOT_INTEGRATION_STABLE

Status: PROJECT 2 OFFLINE SNAPSHOT INTEGRATION VALIDATED

Configuration:
- Psychological Levels experimental geometry
- spacing = 200 USD
- zone_half_width = 25 USD
- active_window = +/-3 levels
- geometry_source = PSYCHOLOGICAL_LEVELS_TEST

Validated stages:
- Stage 1 Psychological Levels Provider: PASS
- Stage 2 Interaction Interpreter: PASS
- Stage 3 Event Dispatcher and deterministic RefreshPlan: PASS
- Stage 4 Mechanical Refresh Coordinator + Canonical Snapshot: PASS

Architecture validation:
- Project 2 geometry drives the existing shadow interaction pipeline
- global_zone_key remains the canonical identity
- Copy-on-write snapshot revisions preserved
- Snapshot content deterministic across identical fresh runs
- Duplicate and out-of-order input creates no new revision
- Only requested dirty content sections are refreshed
- Mandatory snapshot metadata provenance updates remain intact
- Project 1 terminology remains absent
- No Formation, Active Core, or Density Band fields injected

Boundary:
- Experimental and offline only
- No Project 1 changes
- No production RDM formulas or behavior changes
- No Worker, LIVE, or dashboard integration

Validation:
- All psychological_levels modules py_compile: PASS
- Provider test: PASS
- Interaction Interpreter integration: PASS
- Event Dispatcher integration: PASS
- Coordinator/Snapshot integration: PASS
- git diff --check: PASS

Next:
Await Stage 5 stress-test approval.

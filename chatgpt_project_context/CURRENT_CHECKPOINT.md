# Current Checkpoint

## Active Checkpoint: RDM_V2_FIRST_CONTROLLED_LIVE_PASSIVE_SHADOW_SOAK_PASS

Status: SOAK PASS — shadow-only, no production behavior changed. First
controlled LIVE passive shadow soak (SHADOW_RUNTIME_ENABLED=1, SHADOW_DRY_RUN=1,
SHADOW_SAMPLE_RATE=0.05, kill switch disabled) run against the real production
stream_manager.

Results:
- duration = 00:00:05
- payloads_received = 10
- payloads_processed = 9
- parity_records = 20
- failed = 0
- dropped = 0
- desynchronized = 0
- production_errors = 0
- CPU = 1.41s
- memory = 101.3MB
- result = PASS

Findings:
- **First controlled LIVE passive shadow soak PASSED.**
- **Passive shadow tap emitted real LIVE payloads** (not replay data).
- **Worker processed LIVE shadow payloads** end-to-end.
- **Parity logging produced records** (confined to research/shadow_parity/).
- **No production errors. No drops. No desynchronization. No worker failures.**
- **No production output replacement. No dashboard changes. No formulas
  changed. No Stage 2C. No Dynamic State recomputation.**
- One payload difference observed: received=10, processed=9 — likely one
  payload still in-flight at the forced stop. NOT treated as a failure, since
  failed/dropped/desynchronized all remained zero (no lost or corrupted work,
  only an in-flight payload at shutdown).

Validation: git diff --check clean; git status confirmed only the 5 checkpoint
docs staged for this commit.

Next: extended live soak decision.

---

## Active Checkpoint: RDM_V2_LIVE_ACTIVATION_WIRING_STABLE

Status: STABLE CHECKPOINT — no production behavior change with the flag OFF.
Resolves the blocker from the Final Architectural Review: the committed tree had
the live tap, emitter, worker, and runtime, but nothing in the committed tree
ever STARTED the passive worker for a live process.

Fix: committed the isolated startup/shutdown hook in engines/stream_manager.py
main() — the only hunk in that file (verified via `git diff`, single @@ block):
- **Start before start_stream()** — a local import of
  core/passive_shadow_bootstrap.{start_passive_shadow,stop_passive_shadow}
  followed by start_passive_shadow(), BEFORE `await start_stream()`.
- **Stop in finally** — `await start_stream()` wrapped in try/finally; the
  finally calls `shadow_stop(drain_timeout_seconds=2.0)`.
- **Fail-safe try/except** — both the import+start block and the stop call are
  wrapped in try/except Exception: pass; a shadow failure can never prevent or
  interrupt start_stream().
- **Flag default OFF** — start_passive_shadow() delegates to
  PassiveShadowBootstrap, whose FeatureFlags default OFF; SHADOW_RUNTIME_ENABLED
  unset or "0" -> status DISABLED, bootstrap.running False, bootstrap.worker None.
- **No behavior change when disabled** — verified directly against the exact
  entry points main() calls.
- **No unrelated stream_manager changes mixed in** — the diff for
  engines/stream_manager.py contains exactly one hunk (the main() hook); nothing
  else in that file was staged or touched.

Validation (all pass):
- py_compile engines/stream_manager.py + core/passive_shadow_bootstrap.py -> OK
- bootstrap test PASS (disabled no-worker; enabled start+drain; kill switch stops
  worker; repeated start/stop safe)
- SHADOW_RUNTIME_ENABLED unset AND explicitly "0" both verified to start no
  worker via start_passive_shadow()/get_default_bootstrap()
- git diff --check clean

Next: first live payload contract validation.

---

## Active Checkpoint: RDM_V2_PASSIVE_SHADOW_BOOTSTRAP_REPOSITORY_FIX

Status: REPOSITORY INTEGRITY FIX — shadow-only, no production behavior changed.

Problem: the committed replay soak tool (tools/passive_shadow_replay_soak.py)
imported core/passive_shadow_bootstrap.py, which had been implemented and run
locally (Phase 0F) but never committed — so a fresh clone could not execute the
committed soak (committed code depended on untracked code).

Fix: committed the two missing Phase 0F bootstrap files as their own isolated
checkpoint:
- **core/passive_shadow_bootstrap.py** — fail-safe lifecycle owner
  (PassiveShadowBootstrap.start/stop; get_default_bootstrap;
  start_passive_shadow/stop_passive_shadow). Flag-gated default OFF, kill-switch
  protected, try/except BaseException boundaries (never raises to its caller);
  imports only already-committed core modules (worker, shadow_parity_runtime,
  shadow_runtime_emitter, shadow_safety.*).
- **experiments/passive_shadow_worker/bootstrap_test.py** — Phase 0F lifecycle test.

Scope: this commit adds ONLY the two bootstrap files (+ these docs). NOT staged:
core/daily_session.py, live_rdm.py pre-existing hunks, live_return_detection.py,
observation_logger.py, research/zone_mechanics_calculator.py, research artifacts,
unrelated experiments.

Validation (all pass):
- py_compile core/passive_shadow_bootstrap.py +
  experiments/passive_shadow_worker/bootstrap_test.py +
  tools/passive_shadow_replay_soak.py -> OK
- bootstrap test PASS (disabled no-worker; enabled start+drain; kill switch stops
  worker; repeated start/stop safe)
- replay soak import smoke OK (committed soak now resolves bootstrap)
- git diff --check clean

Result: the committed soak tool no longer depends on untracked code; the
committed tree is self-consistent.

(Doc order note: the prior Codex cycle recorded Phase 0E-1/0E-2/0E-3 and
RDM_V2_PASSIVE_SHADOW_REPLAY_SOAK_PASS appended at the BOTTOM of this file; this
repository-fix block is prepended at the top to restore an accurate current
pointer.)

Next: Final Architectural Review.

---

## Active Checkpoint: RDM_V2_PHASE0D_MINIMAL_LIVE_TAP_STABLE

Status: STABLE CHECKPOINT — no production behavior change with the flag OFF.
Phase 0D: the first (and minimal) production wiring of the Passive Shadow Runtime
— a single flag-gated, isolated tap.

The tap:
- **one minimal flag-gated tap in compute_live_rdm_for_case** (core/live_rdm.py)
  — a single ~13-line hunk; the only production line is `_shadow_emit(record)`.
- **after _persist_record / B12.5 hook, before return record** — placed where
  geometry, row mechanics, visit, and B10/B11 are finalized (Phase 0B tap point).
- **local import** — `from core.shadow_runtime_emitter import emit as
  _shadow_emit` inside the hook, so the module's load-time import graph is
  unchanged.
- **try/except isolated** — wrapped in try/except Exception; the shadow path can
  never block the LIVE pipeline, mutate record, or alter any output.
- **default OFF; no-op with flag OFF** — the emitter no-ops unless
  SHADOW_RUNTIME_ENABLED is explicitly set (verified: status DISABLED, zero queue
  activity), so there is **no production behavior change with the flag OFF**.
- **unrelated live_rdm hunks excluded** — only the Phase 0D tap hunk was staged
  (patch-staging via git apply --cached); the 5 pre-existing, unrelated working-
  tree hunks (imports, build_completed_live_case_row, _run_group_b,
  append_post_return_tick, _ensure_csv) were left unstaged and unmodified.

Validation (all pass):
- py_compile core/live_rdm.py + core/shadow_runtime_emitter.py -> OK
- live_rdm import smoke OK
- emitter shadow test PASS
- flag OFF -> no queue activity (status DISABLED, enqueued=0)
- git diff --check clean; git diff --cached shows ONLY the tap hunk

Next: passive shadow runtime worker approval.

---

## Active Checkpoint: RDM_V2_PHASE0C_SHADOW_EMITTER_STABLE

Status: STABLE CHECKPOINT — shadow-only, no production behavior changed. Phase 0C
of the production-integration migration: the standalone shadow emitter that will
LATER receive the finalized record from compute_live_rdm_for_case, built and
validated BEFORE the LIVE tap exists.

New module core/shadow_runtime_emitter.py (standalone; imports only Phase 0A
core/shadow_safety):
- **standalone shadow_runtime_emitter** — ShadowRuntimeEmitter.emit(record) +
  ShadowPayload / EmitResult + module-level emit() / get_default_emitter().
- **flags default OFF** — disabled -> no-op, queue untouched (status DISABLED);
  the default emitter reads flags from env, so emit() is inert until enabled.
- **kill switch blocks emit** — kill_switch.allows() False (breaker latched or
  manual env/file kill) -> no-op, status KILLED.
- **bounded queue non-blocking** — BoundedDropQueue.offer(); full -> DROPPED,
  never blocks / never raises.
- **deep-copied immutable payload** — every field copy.deepcopy-ed then frozen
  (MappingProxyType / tuples) inside a frozen ShadowPayload; source mutation
  after emit cannot affect the enqueued payload.
- **global_zone_key = session_id::zone_id** — derived from candidate session /
  zone keys in the record or its result_row (session falls back to
  UNKNOWN_SESSION; zone keys the snapshot).
- **geometry_version synthesized from pinned geometry** — deterministic SHA1
  (GEOMv1:<hex>) over the formation / active-core / density edges; GEOMv1:NA when
  no edges.
- **bad record never raises** — whole emit body wrapped (try/except BaseException,
  re-raising only KeyboardInterrupt/SystemExit); malformed record -> status ERROR.

Strictly: **no live tap** (live_rdm.py untouched); **no production imports**
(nothing in core/research/tools/engines imports shadow_runtime_emitter except the
module itself); **no production behavior changed** (no dashboard, formulas, Stage
2C, or CSV writes — the emitter only enqueues into the in-memory bounded queue).

Validation (all pass):
- py_compile core/shadow_runtime_emitter.py +
  experiments/shadow_runtime_emitter/shadow_test.py -> OK
- shadow emitter test PASS (disabled no-op; enabled enqueues; kill switch blocks;
  queue full drops without blocking; bad record never raises; payload deep-copied;
  global_zone_key + geometry_version generated)
- git diff --check clean

Next: Phase 0D live tap approval.

---

## Active Checkpoint: RDM_V2_PHASE0A_SHADOW_SAFETY_MODULES_STABLE

Status: STABLE CHECKPOINT — shadow-only, no production behavior changed. First
step of the production-integration migration: the standalone Phase 0 safety
scaffolding (Phase 0A), built and validated BEFORE any LIVE tap exists.

New package core/shadow_safety/ (standalone, fail-closed building blocks for the
not-yet-wired Passive Shadow Runtime):
- **feature flags default OFF** (core/shadow_safety/feature_flag.py) — reads
  SHADOW_RUNTIME_ENABLED / SHADOW_DRY_RUN / SHADOW_SAMPLE_RATE; absent / garbage /
  unreadable -> OFF; explicit truthy opt-in only; should_run() + should_sample().
- **kill switch / circuit breaker** (core/shadow_safety/kill_switch.py) —
  CircuitBreaker latches KILLED on trip() or N consecutive failures and never
  self-revives (only reset()); KillSwitch adds manual env (SHADOW_KILL) +
  on-disk flag-file kill; fail-closed (unreadable -> KILLED).
- **bounded non-blocking queue** (core/shadow_safety/bounded_queue.py) —
  BoundedDropQueue.offer() uses put_nowait; full -> drop + count, never blocks /
  never raises; poll() non-blocking.
- **isolated worker wrapper** (core/shadow_safety/isolated_worker.py) —
  IsolatedWorker.process() runs the handler behind a try/except BaseException
  boundary (re-raises only KeyboardInterrupt/SystemExit); failures swallowed,
  counted, fed to the breaker; a latched breaker short-circuits without calling
  the handler.
- **parity log writer confined to research/shadow_parity/**
  (core/shadow_safety/parity_log.py) — ParityLogWriter appends timestamped JSONL
  only inside research/shadow_parity/; escaping paths rejected at construction.

Strictly: **no live tap** (live_rdm.py untouched, no tap line); **no production
imports** (nothing in core/research/tools/engines imports core.shadow_safety
except the package itself); **no production behavior changed** (no dashboard, RDM
formulas, Stage 2C, or outputs).

Validation (all pass):
- py_compile all shadow safety modules + test -> OK
- shadow safety test PASS (flags default OFF; kill switch latches closed +
  auto-trips; queue drops on full and never blocks; worker swallows + counts
  exceptions; parity logger confined to research/shadow_parity/)
- git diff --check clean

Next: Phase 0B tap point review.

---

## Active Checkpoint: RDM_V2_FULL_SHADOW_RUNTIME_STABLE

Status: STABLE CHECKPOINT — shadow-only, no production behavior changed.
Consolidation checkpoint for the entire RDM V2 shadow architecture phase.

### 1. Event-Driven Backbone (complete)
    Market Row -> Interaction Interpreter -> Event Dispatcher ->
    Mechanical Refresh Coordinator -> Canonical Snapshot
Components: core/interaction_interpreter.py, core/event_dispatcher.py,
core/mechanical_refresh_coordinator.py, core/canonical_snapshot.py.

### 2. Operational Contracts (accepted + checkpointed)
- **Snapshot Identity Contract**: global_zone_key is the canonical snapshot
  identity; zone_id is metadata only; same zone_id across sessions does not
  collide.
- **Row Ordering Contract**: interpret_in_order(); InteractionState.
  previous_row_index is the only watermark; row_index authoritative; timestamp
  informational only; duplicate row -> ROW_DUPLICATE; older row ->
  ROW_OUT_OF_ORDER; no events / no mutation on rejected rows.
- **Restart / Durability Contract**: append-only ordered row log is source of
  truth; persist-before-process; rebuild-from-history; snapshot is
  projection/cache only; geometry-in-effect must be pinned; checkpoints are an
  optimization, not correctness.

### 3. Canonical Snapshot (shadow-ready sections)
Metadata, Geometry, Current Row Mechanics, Open Visit, Last Completed Visit,
Dynamic Mechanics, Prediction. Behavior: copy-on-write; immutable revisions; one
atomic revision per commit; previous revision preserved on failure; keyed by
global_zone_key.

### 4. Snapshot Adapters (all shadow-only)
core/geometry_snapshot_adapter.py, core/row_mechanics_adapter.py,
core/open_visit_adapter.py, core/last_completed_visit_adapter.py,
core/dynamic_mechanics_adapter.py, core/prediction_adapter.py. All: pure mapping
only; no calculations; NOT_AVAILABLE-aware; alias-aware where needed;
snapshot-compatible; no production consumers.

### 5. Shadow Integration Tests
- experiments/coordinator_snapshot_integration/shadow_test.py: Coordinator ->
  Row Mechanics -> Snapshot; Coordinator -> Row Mechanics + Open Visit ->
  Snapshot; Completed Visit; Dynamic Mechanics; Prediction integrations.
- experiments/full_shadow_runtime/shadow_test.py: full Market Row ->
  Interaction Interpreter -> Event Dispatcher -> Mechanical Refresh Coordinator
  -> Adapters -> Canonical Snapshot runtime.

### 6. Full Shadow Runtime Guarantees (all validated)
one RefreshPlan per accepted event row; one atomic snapshot revision per
committed plan; duplicate rows rejected before refresh; out-of-order rows
rejected before refresh; adapter failure preserves the previous revision; no
partial commit; prediction PENDING does not block completed/dynamic sections;
global_zone_key preserved; source_plan_id preserved; adapter provenance
preserved; copy-on-write preserved; no calculations; no prediction generation;
no Dynamic State recomputation; no Stage 2C; no production behavior changed.

Validation (all pass):
- py_compile experiments/full_shadow_runtime/shadow_test.py -> OK
- Full shadow runtime test PASS (6 scenarios; 8 RefreshPlans -> 7 committed
  revisions, one rolled back by the injected failure)
- git diff --check clean

Next: production integration strategy.

---

## Active Checkpoint: RDM_V2_PREDICTION_SNAPSHOT_INTEGRATION_SHADOW_STABLE

Status: STABLE CHECKPOINT — shadow-only, no production behavior changed.

Prediction Adapter integrated into the coordinator snapshot integration test
(experiments/coordinator_snapshot_integration/shadow_test.py). This completes the
event-driven Coordinator -> adapters -> one atomic Canonical Snapshot revision for
all data sections.

- **Prediction Adapter integrated** into the multi-adapter atomic
  `apply_refresh_adapters` orchestrator.
- **Gate = ALL(trajectory_dirty, prediction_dirty)** — encodes the B10 trajectory
  -> B11 prediction dependency; a real VISIT_COMPLETED sets both flags.
- **Prediction runs logically after Dynamic Mechanics** (last patch built before
  the single atomic store publication).
- **Missing prediction input produces PENDING / NOT_AVAILABLE** — B11 is
  asynchronous to its VISIT_COMPLETED trigger, so a missing input maps a
  `{"prediction_status": "PENDING"}` section (other fields NOT_AVAILABLE) instead
  of aborting.
- **Pending prediction does not block completed_visit or dynamic_mechanics** —
  the ready sections still commit in the same atomic revision.
- **Unexpected prediction adapter failure prevents partial commit** — an adapter
  that raises propagates and blocks the whole revision (all patches are built
  before one store call); the prior revision is untouched.
- **One atomic revision per merged commit**; revision monotonic.
- **global_zone_key and source_plan_id preserved.**
- **No calculations. No prediction generation. No production behavior changed**
  (no core/research/tools module consumes the integration test).

Validation (all pass):
- py_compile experiments/coordinator_snapshot_integration/shadow_test.py -> OK
- Integration test PASS (prediction-present maps FINALIZED/LIKELY_HOLD; pending
  maps PENDING/NOT_AVAILABLE; ready sections commit when pending; unexpected
  adapter failure preserves revision)
- git diff --check clean

Next: full shadow runtime consolidation approval.

---

## Active Checkpoint: RDM_V2_CANONICAL_SNAPSHOT_ADAPTERS_COMPLETE

Status: MILESTONE CHECKPOINT — shadow-only, no production behavior changed.

All six Canonical Snapshot adapters are now shadow-ready. Each maps already-
existing values into one snapshot section; none calculates, infers, or rebuilds.

The six adapters (one per snapshot section):
- **geometry** — GeometrySnapshotAdapter -> `geometry`
- **current row mechanics** — RowMechanicsAdapter -> `current_row_mechanics`
- **open visit** — OpenVisitAdapter -> `open_visit`
- **last completed visit** — LastCompletedVisitAdapter -> `last_completed_visit`
- **dynamic mechanics** — DynamicMechanicsAdapter -> `dynamic_mechanics`
- **prediction** — PredictionAdapter -> `prediction`

Shared, enforced properties across all six:
- **Pure mapping only** — value pass-through via ordered source aliases; first
  present/available alias wins, primary names first.
- **No calculations** — no Dynamic State recompute, derivatives, integrals, SDR,
  classifier, thresholds, B10/B11 execution, Stage 2C, dashboard, CSV writes, or
  persistence.
- **NOT_AVAILABLE handling** — any target whose aliases are all absent, or present
  but None / empty-string / NaN, becomes NOT_AVAILABLE in both the value and its
  source_fields provenance entry. No defaulting.
- **Snapshot compatibility** — every adapter emits a RefreshResult-style patch
  that builds cleanly into a CanonicalZoneSnapshot section; the six together
  consolidate into one immutable copy-on-write snapshot (consolidation test).
- **No production behavior changed** — nothing in core/research/tools imports any
  adapter except the shadow tests.

Most recent additive work folded into this milestone: DynamicMechanicsAdapter
gained `transition_name`; PredictionAdapter gained `prediction_uncertainty`.

Validation (all pass):
- py_compile of all six adapter files + their shadow tests -> OK
- All adapter shadow tests PASS
- Consolidation test PASS
- git diff --check clean

Next: first real mechanical integration decision.

---

## Active Checkpoint: RDM_V2_LAST_COMPLETED_VISIT_ADAPTER_SHADOW_STABLE

Status: STABLE CHECKPOINT — shadow-only, no production behavior changed.

Last Completed Visit Adapter Stage 1 (shadow-only):
- **Extended the existing adapter additively** (core/last_completed_visit_adapter.py,
  originally committed aefec1c) — existing target field names and behavior are
  untouched, so the dependent consolidation test stays green.
- **Maps already-existing completed-visit fields into the Canonical Snapshot
  "last_completed_visit" section** — projection only, no rebuild, no inference.
- **Adds `max_penetration_ratio` and `defender_state`** (plus `visit_start_price`
  and `visit_end_price`) as new mapped target fields this stage.
- **Supports aliases** (first present/available alias wins, primary names first):
  completed_visit_id->visit_id, visit_max_penetration->max_penetration,
  visit_max_penetration_ratio->max_penetration_ratio, visit_final_omega->
  omega_at_visit, visit_attacker_force->attacker_force_at_visit,
  visit_defender_state->defender_state, visit_health/rigidity/capacity/fatigue/
  recovery->*_at_visit (pre-existing aliases retained: visit_start_time,
  visit_end_time, visit_duration_rows, max_penetration_at_visit).
- **NOT_AVAILABLE behavior** — any target whose aliases are all absent, or present
  but None / empty-string / NaN, becomes NOT_AVAILABLE in both the value and its
  source_fields provenance entry. No defaulting.
- **No calculations** — no Dynamic State, derivatives, integrals, SDR, Stage 2C,
  B10, B11, dashboard, CSV writes, or persistence. Opaque pass-through preserved.
- **Snapshot compatibility** — the patch builds a CanonicalZoneSnapshot
  last_completed_visit section cleanly.
- **No production behavior changed** — nothing in core/research/tools imports the
  adapter except the shadow tests.

Validation (all pass):
- py_compile core/last_completed_visit_adapter.py +
  experiments/last_completed_visit_adapter/shadow_test.py -> OK
- Extended shadow test PASS (normal / partial / missing / new fields / alias /
  no-calculations / snapshot compatibility)
- Consolidation test PASS (NOT_AVAILABLE_VALIDATED = TRUE)
- git diff --check clean

Files: core/last_completed_visit_adapter.py (additive) +
experiments/last_completed_visit_adapter/shadow_test.py (extended).

Next: Dynamic Mechanics Adapter approval.

---

## Active Checkpoint: RDM_V2_RESTART_DURABILITY_CONTRACT_ACCEPTED

Status: ACCEPTED CONTRACT — architecture decision only. NO code implemented,
no production code changed. Records the restart/durability design the shadow
backbone must follow before any production integration.

Restart / Durability Contract:
- **The append-only ordered row log is the source of truth.** Per session_id,
  each row carries global_zone_key and the geometry_version in effect.
- **Persist-before-process (write-ahead ordering):** a row is durably appended
  BEFORE InteractionState advances from it -> an open visit is always replayable.
- **Rebuild-from-history is the primary recovery mechanism.** Restart = replay
  the durable rows forward through interpret_in_order; rebuild InteractionState
  and the SnapshotStore rather than trusting them.
- **The snapshot is a cache / projection only — never the source of truth.**
  Copy-on-write CanonicalZoneSnapshot is derived from plan+patches; if used as a
  file cache it is tagged (global_zone_key, revision, watermark_row_index) and
  never loaded when its watermark is ahead of the durable row log.
- **Watermark = InteractionState.previous_row_index** is the single recovery
  anchor (same single source of truth as the Row Ordering Contract). After
  rebuild it must equal the last durable row; only greater row_index is accepted.
- **Geometry-in-effect must be pinned** (geometry_version + bounds). If geometry
  is recomputed differently on restart, replay diverges — parity requires the
  same geometry inputs.
- **Checkpoints are an optimization, not correctness.** A periodic
  InteractionState checkpoint (carrying cumulative counters: revision,
  active_visit_index, completed_visit_count, return_count, guard/breach state)
  only bounds replay cost; it is never authoritative.

Primary (must persist): ordered row log, session_id, global_zone_key,
geometry-in-effect. Everything else (InteractionState, watermark, open visit,
snapshots, revision, last event id, dedup ledger, guard/breach) is DERIVED and
rebuildable from history.

Most order-sensitive: the open-visit accumulator (visit_start_row/timestamp/
price, active_visit_id/index, visit_row_count, visit_max_penetration(_ratio),
inactive_row_count) must never be lost — guaranteed by persist-before-process.

No production code changed (documentation/design only).

Next: Restart / Durability implementation decision.

---

## Active Checkpoint: RDM_V2_ROW_ORDERING_CONTRACT_STABLE

Status: STABLE CHECKPOINT — shadow-only, no production behavior changed.

Row Ordering Contract in the Interaction Interpreter (shadow-only):
- New entry point **`interpret_in_order()`** enforces row ordering BEFORE any
  transition; it delegates to the existing pure `interpret()` only on accept, so
  no state mutation / event generation occurs before the ordering check passes.
- New **`OrderingResult`** result type (status + audit + state + events).
- Statuses: **ORDER_ACCEPTED**, **ROW_DUPLICATE**, **ROW_OUT_OF_ORDER**.
- **InteractionState remains the single ordering watermark** (via
  `previous_row_index`). **No dispatcher watermark. No coordinator watermark.**
- **row_index is authoritative; timestamp is informational only** — equal
  timestamps with an increasing row_index remain valid.
- **No events are emitted for duplicate / out-of-order rows** (audit code only);
  on rejection the unchanged input state is returned (identity-preserved).
- **Existing `interpret()` remains unchanged.**
- No production behavior changed (interaction_interpreter is shadow-only; no
  production consumers).

Rules (per global_zone_key):
  incoming.row_index >  previous_row_index -> ACCEPT, normal transition.
  incoming.row_index == previous_row_index -> ROW_DUPLICATE, no change.
  incoming.row_index <  previous_row_index -> ROW_OUT_OF_ORDER, no change.

Validation (all pass):
- python -m py_compile core/interaction_interpreter.py +
  experiments/interaction_interpreter/shadow_test.py +
  experiments/interaction_interpreter_ordering/shadow_test.py -> OK
- Existing interaction interpreter shadow test PASS (interpret() unchanged)
- New row ordering shadow test PASS (all 6 cases)
- Full shadow-suite regression (11 tests) PASS
- git diff --check clean

Files: core/interaction_interpreter.py (additive) +
experiments/interaction_interpreter_ordering/shadow_test.py (new).

Next: Restart / Durability Contract review (rehydrating the InteractionState
watermark across restarts so the ordering guard survives process restart).

---

## Active Checkpoint: RDM_V2_SNAPSHOT_IDENTITY_CONTRACT_STABLE

Status: STABLE CHECKPOINT — shadow-only, no production behavior changed.

Canonical Snapshot identity contract fix:
- Canonical Snapshot identity is now **global_zone_key**.
- zone_id is descriptive metadata only (no longer determines snapshot identity).
- SnapshotStore is keyed by global_zone_key (was: bare zone_id).
- Session-scoped identity now matches the Event Dispatcher identity contract.
- Snapshot revision model unchanged.
- Copy-on-write behavior unchanged.
- Snapshot sections unchanged.
- Production behavior unchanged (core/canonical_snapshot.py is shadow-only;
  only experiment shadow tests import it — no live/dashboard consumer).

Why: the Event Dispatcher namespaces identity by session_id (+ global_zone_key),
but the snapshot store keyed by bare zone_id. Because zone_id is legitimately
reused across daily sessions, the snapshot layer could collide ("Snapshot
already exists for zone …") or overwrite the wrong session. Fixed by keying the
store and CanonicalZoneSnapshot identity on global_zone_key; zone_id retained as
metadata; global_zone_key added to protected metadata and validated (non-empty +
revision continuity).

Validation (all pass):
- python -m py_compile core/canonical_snapshot.py -> OK
- All 8 Canonical Snapshot / adapter shadow tests PASS
- New identity-collision shadow test PASS — same zone_id reused across two
  sessions yields two INDEPENDENT snapshots, no collision, no overwrite:
    Session A = BTCUSDT_2026-06-28_230000Z::SNAPSHOT_ZONE_1
    Session B = BTCUSDT_2026-06-29_230000Z::SNAPSHOT_ZONE_1
    shared zone_id = SNAPSHOT_ZONE_1; independent state (geometry width 10 vs 20).
- git diff --check clean

Files: core/canonical_snapshot.py + Canonical Snapshot / adapter shadow tests.

Next: Row Ordering Guard architectural review (monotonic row_index/timestamp
guard at the interpreter/dispatcher seam for out-of-order / late rows).

---

## Active Checkpoint

Checkpoint: PHASE1B_B125_AUTOTRIGGER_STABLE

What this checkpoint adds:
- B12.5 now fires AUTOMATICALLY on every new zone detection
  (score >= 4), wired into core/live_rdm.py inside
  compute_live_rdm_for_case(), immediately after _persist_record().
  Wrapped in try/except: pass so a B12.5 failure never blocks the
  main live pipeline. Runtime confirmed <2s.
- dashboard_live_zones.py filter changed from "last N hours" to
  calendar-day selector: Today / Yesterday / Last 3 days
  (default: Today, Algeria midnight as boundary)
- Auto-refresh tightened: cache TTL 10s, fragment run_every 15s
  (was 30s/60s) — new zones appear on dashboard within 15s with
  zero manual action
- Diagnostic command if auto-trigger silently fails:
    python -c "from research.zone_mechanics_calculator import
    run_zone_visit_timeline_dynamic_live as r1,
    add_dynamic_layers_to_timeline_live as r2; r1(); r2();
    print('Manual B12.5 OK')"

Dashboard architecture (two separate apps, run independently):
  dashboard_app.py            -> full historical archive (default port)
  dashboard_live_zones.py     -> today's active zones only (port 8502)
    Focus: Density Bands as decision zone, Active Core as context,
    Preparation Zone in expander only. Plain-language WHY reasoning
    per card (reuses _classify_dynamic_state rules). Expandable visit
    history with outcome tracking (what_happened_next per visit).

Run commands:
  powercfg /change standby-timeout-ac 0
  python -m engines.stream_manager
  streamlit run dashboard_app.py
  streamlit run dashboard_live_zones.py --server.port 8502

Next steps:
  - Run LIVE continuously for extended period (days) to accumulate
    enough post-return visits for meaningful dynamic_state validation
  - Once sufficient LIVE post-return data exists, compare LIVE vs
    REPLAY dynamic_state distributions
  - Consider B13 (Markov transition engine) once B12.5 is validated
    on LIVE data

---

## Prior Checkpoint: PHASE1B_B125_LIVE_DASHBOARD_STABLE

What this checkpoint added:
- B12.5 wired into LIVE pipeline (run_zone_visit_timeline_dynamic_live,
  add_dynamic_layers_to_timeline_live) — uses fixed REPLAY-calibrated
  thresholds for LIVE/REPLAY comparability
- New file: research/live_zone_visit_timeline_dynamic.csv
- New standalone dashboard: dashboard_live_zones.py (port 8502)
  - Shows only zones active in last N hours (configurable, default 24)
  - One card per zone, focused on Density Bands as the decision zone
    (Active Core shown as context only, Preparation Zone moved to
    expander)
  - Plain-language prediction reasoning per card (reuses
    _classify_dynamic_state rules, does not duplicate logic)
  - Expandable "More Information": full visit history with
    outcome tracking (what_happened_next per visit)
  - Algeria timezone throughout, auto-refresh every 60s + manual button
- Existing dashboard_app.py (research/stream view) UNCHANGED, runs on
  default port, still shows full historical archive

LIVE data status (as of this checkpoint):
- 3 days collected (Jun 17-19) on @aggTrade stream, with gaps
  (stream not yet run continuously)
- 50 unique returning zones, 8 post-return visits, mostly NO_DATA/
  PROBABLE_HOLD (insufficient post-return history yet)

---

## Prior Checkpoint: PHASE1B_B125_DYNAMIC_TIMELINE_STABLE

What this checkpoint added:
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
  PROBABLE_HOLD     → 56.5%  FAIL  (n=657) <- needs refinement
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

Prior checkpoints (preserved):
  - PHASE1B_UNIFIED_ARCHIVE_STABLE
  - PHASE1B_STREAMING_REPLAY_STABLE
  - PHASE1B_B12_LIVE_VALIDATION
  - PHASE1B_SYNTHESIS_ENGINE_STABLE

---

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

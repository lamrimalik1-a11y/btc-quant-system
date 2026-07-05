# Current Checkpoint

## Active Checkpoint: PHASE1C_SCIENTIFIC_HYPOTHESIS_AUDIT_STABLE

Commit: `b381ce99b0199856242e104c06a8fe139a8def63`

Status: STABLE AND VALIDATED.

Chapter I is complete and stable:
- Stage 1 Dynamic Mechanics
- Stage 2 Snapshot Dynamic Mechanics
- Stage 3 Dynamic State Transitions
- Stage 4 Transition Graph
- Stage 5 Trajectory Evolution
- Stage 6 Prediction Evolution Research

Project 2 Chapter II, stable through Phase 6:
- Phase 1 Scenario Generator Foundation: STABLE
- Phase 2 Scenario Runner: STABLE
- Phase 3 Scenario Catalog Foundation: STABLE
- Phase 4 Scenario Execution: PASS after the Stage 6 empty-zone robustness fix
- Phase 5 Cross-Scenario Descriptive Comparison: STABLE
- Phase 6 Scientific Hypothesis Audit: STABLE

Stable checkpoint chain:
- `PHASE1C_SCENARIO_GENERATOR_FOUNDATION_STABLE`
  (`ca71902f74ba42ce54b217f3488c10da24a2d0f4`)
- `PHASE1C_SCENARIO_RUNNER_STABLE`
  (`34641e3c1cda4a19972a48752446785132e7ccbd`)
- `PHASE1C_SCENARIO_CATALOG_FOUNDATION_STABLE`
  (`5a2d4a718f0072f86556e2b2347eedbeaf8ae061`)
- `PHASE1C_SCENARIO_CATALOG_PROVENANCE_FIX`
  (`a2c52feb5b7472450b543f6de3b46a6562520d5a`)
- `PHASE1C_SCENARIO_EXECUTION_STAGE6_EMPTY_ZONE_FIX`
  (`add1fcfe37f68d41437594d4b424f1eddd08214d`)
- `PHASE1C_CROSS_SCENARIO_COMPARISON_STABLE`
  (`660f459ea9a5a34d6aa95a2a395f1ea93302ea57`)
- `PHASE1C_SCIENTIFIC_HYPOTHESIS_AUDIT_STABLE`
  (`b381ce99b0199856242e104c06a8fe139a8def63`)

Summary:
- Phase 6 implemented as a preregistered scientific hypothesis audit.
- Decisions are derived from explicit evidence-based decision rules.
- Exact Phase 3 hypothesis traceability verified.
- Phase 5 remains the sole source of observed evidence.
- Caveats precede evaluations.
- Null and contradictory evidence preserved.
- Automated banned-language scan added.
- Deterministic scientific audit verified.
- No Scenario Runner changes.
- No Scenario Catalog changes.
- No Stage 1-6 changes.
- No Project 1 changes.
- No Production changes.

Independent verification performed before this checkpoint was documented:
- Each hypothesis evaluation carries `decision_rule_id` and
  `decision_rule_trace` (e.g. adversarial's rule reads
  `completed_visits=2, attacker_pressure_observed=True,
  eligible_hypotheses=0` and derives `PARTIALLY_CONSISTENT`) -- decisions
  are computed, not hardcoded, confirmed by tracing the rule logic against
  independently-known evidence values.
- `all_hypotheses_ex_ante = True`, `no_hypotheses_outside_phase3 = True`,
  `all_phase3_sources_exact = True` -- all four hypotheses trace exactly to
  Phase 3's committed `expected_behavior_notes`/`description` text, no
  rewritten or invented hypotheses.
- `banned_language_scan.passed = True` against an expanded pattern list
  (proven, validated, falsified, generalize/generalization, suggests,
  confirms, proves, stronger, weaker, improved, degraded, effect, impact,
  lift, gain, accuracy, performance, and more), scoped only to Phase 6's own
  authored prose -- never the quoted Phase 3 preregistered text.
- Imports confirmed limited to `scenario_contract`, `specifications`, and
  `test_cross_scenario_comparison` (Phase 5, reused unchanged) -- no
  Scenario Runner, Stage 1-6, `core.`/`engines.`/`research.` imports.
- Deterministic across two independent process invocations (byte-identical
  output).
- `git diff 660f459..b381ce9` touches exactly one file; zero modification
  to Scenario Runner, Scenario Catalog, Stage 1-6, Project 1, or production
  code.

---

## Active Checkpoint: PHASE1C_SCENARIO_EXECUTION_STAGE6_EMPTY_ZONE_FIX

Commit: `add1fcfe37f68d41437594d4b424f1eddd08214d`

Status: STABLE AND VALIDATED.

Chapter I is complete and stable:
- Stage 1 Dynamic Mechanics
- Stage 2 Snapshot Dynamic Mechanics
- Stage 3 Dynamic State Transitions
- Stage 4 Transition Graph
- Stage 5 Trajectory Evolution
- Stage 6 Prediction Evolution Research

Project 2 Chapter II Phase 1C:
- Phase 1 Scenario Generator Foundation: STABLE
- Phase 2 Scenario Runner: STABLE
- Phase 3 Scenario Catalog Foundation: STABLE
- Phase 4 Scenario Execution: PASS after the Stage 6 empty-zone robustness fix

Stable checkpoint chain:
- `PHASE1C_SCENARIO_GENERATOR_FOUNDATION_STABLE`
  (`ca71902f74ba42ce54b217f3488c10da24a2d0f4`)
- `PHASE1C_SCENARIO_RUNNER_STABLE`
  (`34641e3c1cda4a19972a48752446785132e7ccbd`)
- `PHASE1C_SCENARIO_CATALOG_FOUNDATION_STABLE`
  (`5a2d4a718f0072f86556e2b2347eedbeaf8ae061`)
- `PHASE1C_SCENARIO_CATALOG_PROVENANCE_FIX`
  (`a2c52feb5b7472450b543f6de3b46a6562520d5a`)
- `PHASE1C_SCENARIO_EXECUTION_STAGE6_EMPTY_ZONE_FIX`
  (`add1fcfe37f68d41437594d4b424f1eddd08214d`)

Stage 6 now handles empty zones explicitly:
- `NO_VISITS`: zone exists with zero completed visits.
- `INSUFFICIENT_SAMPLE`: zone has visits but no eligible hypothesis.
- `SUFFICIENT_SAMPLE`: zone produced at least one eligible hypothesis.

Phase 4 deterministic execution:
- Baseline: PASS, 159 visits
- Adversarial: PASS, 2 visits
- Regime change: PASS, 52 visits
- Repeated attacks: PASS, 6 visits
- Determinism: PASS

No Scenario Runner or Scenario Catalog implementation changed. No Project 1
or production behavior changed.

---

## Prior Stable Checkpoint: PHASE1C_SCENARIO_CATALOG_PROVENANCE_FIX

Status: IMPLEMENTED AND VALIDATED.

Scientific provenance correction only:
- No architecture changed.
- No scenario parameters changed.
- No generated price paths changed; specification fingerprints changed only
  where corrected metadata/documentation is part of the immutable
  specification.
- REPEATED_ATTACKS_PARTIAL_RECOVERY_V1 is documented as a denominator-
  degradation / partial-recovery experiment, not a direct
  RESEARCH_ATTACKER_PRESSURE target. Its downstream state is not
  predeclared.
- REGIME_CHANGE_INTO_PRESSURE is consistently documented as a same-zone
  quiet-to-pressure transition, preserving per-zone trajectory history for
  later Stage 6 evaluation.
- No Stage 1-6, Scenario Runner, Project 1, or production behavior changed.

Files updated:
- experiments/psychological_levels_dynamic/scenario_catalog/specifications.py
- experiments/psychological_levels_dynamic/scenario_catalog/families/regime_change_into_pressure.py
- chatgpt_project_context/CURRENT_CHECKPOINT.md
- chatgpt_project_context/MASTER_STATUS_COMPACT.md

Validation:
- `python -m py_compile` on catalog.py, specifications.py, all four family
  providers, and test_scenario_catalog.py
- `python experiments/psychological_levels_dynamic/scenario_catalog/test_scenario_catalog.py`
- Generated observation sequences compared with commit 5a2d4a7: unchanged
- `git diff --check`
- `git status`

---

## Prior Stable Checkpoint: PHASE1C_SCENARIO_CATALOG_FOUNDATION_STABLE

Status: IMPLEMENTED AND VALIDATED - awaiting review before commit.
Research-only, offline-only, Project 2 Chapter II Phase 3.

Implemented:
- Small, explicit Scenario Catalog with exactly four highest-priority
  families: BASELINE, ADVERSARIAL_ATTACKER_PRESSURE,
  REGIME_CHANGE_INTO_PRESSURE, REPEATED_ATTACKS. No batch execution, no
  cross-scenario comparison, no sensitivity analysis, no learning, no
  storage, no new analytical layer.
- Each family is one provider (families/*.py) implementing the existing
  ScenarioProvider Protocol unchanged, composing only the existing, unchanged
  scenario_primitives functions (triangular_wave, step_pattern,
  bounded_range) -- no new mechanics introduced.
- Mechanism-derived, not vocabulary-derived: ADVERSARIAL_ATTACKER_PRESSURE
  constructs a shallow probe then a much deeper sustained penetration into
  the same zone (targets the SDR formula's numerator via a large delta_omega
  relative to health); REPEATED_ATTACKS constructs six equal-depth
  penetrations separated by short, incomplete-recovery withdrawal gaps
  (targets the same formula's denominator via cumulative health decline) --
  a deliberately distinct, non-conflated mechanism from
  ADVERSARIAL_ATTACKER_PRESSURE; REGIME_CHANGE_INTO_PRESSURE concatenates a
  quiet, mildly-oscillating regime with the same escalating-penetration
  shape, targeting the same zone.
- One specification per family (four total) in specifications.py, each with
  a semantic, versioned scenario_id, and expected_behavior_notes /
  validation_metadata written as preregistered, formula-derived hypotheses
  (not required outcomes) before any downstream execution.
- Catalog does not run Stage 1-6 and does not execute the Scenario Runner --
  confirmed both declaratively and via an automated source-import scan
  across every catalog file for the six Stage 1-6 module names,
  "scenario_runner", and any "core."/"engines."/"research." import prefix.
- Structurally verified (not merely by convention) that
  expected_behavior_notes and validation_metadata are never read by any
  provider's generate(): each specification is rebuilt with different notes/
  metadata and confirmed to produce byte-identical observations.
- Structural price-only validation identical in spirit to Phase 2's:
  contiguous row ordering, finite Decimal prices, row count matches
  specification, and a dataclass-field check confirming PriceObservation
  carries only row_index/price.
- Distinct path shapes verified via a (length, unique price count, min,
  max) signature compared across all four specifications.

Post-audit revision (parameter-only, providers/catalog/registry/contract/
runner untouched):
- REPEATED_ATTACKS_PARTIAL_RECOVERY_V1: touch depth/duration reduced
  (60395 for 10 rows -> 60378 for 5 rows) and withdrawal lengthened (8 rows
  -> 15 rows, cycle length 18 -> 20, row_count 108 -> 120) after an audit
  diagnostic showed the original parameters floored health on visit 1 and
  stayed flat for all 6 visits, contradicting the "gradual decline" the
  specification described. Empirically re-verified: health_at_visit now
  declines monotonically 92.2 -> 89.2 -> 86.2 -> 83.2 -> 80.2 -> 77.2 across
  the six visits, omega_at_visit constant at 15.0 (no floor reached).
- REGIME_QUIET_TO_PRESSURE_V1: quiet phase's bounded_range center/amplitude
  changed (center=60200, amplitude=40 -> center=60450, amplitude=70) after
  an audit diagnostic showed the original parameters (a) touched a
  different zone (60200) than the pressure phase (60400), which Stage 6's
  strictly per-zone hypothesis logic can never connect, and (b) collapsed
  into one continuous 200-row visit instead of several small ones. The new
  values position bounded_range's fixed 4-cycle so only one of its four
  values falls inside the same zone the pressure phase later escalates
  into, with the other three clearly outside -- empirically re-verified:
  50 separate completed visits across the 200-row quiet phase, all in the
  same zone as the pressure phase, health declining smoothly 98.2 -> 10.0
  with no premature floor.
- Both fixes are confined to the `parameters` field (and the accompanying
  expected_behavior_notes/validation_metadata text, corrected to match) in
  specifications.py. No provider, no catalog.py, no registry, no contract,
  no Scenario Runner, and no Stage 1-6 file was touched.
- Full catalog test suite re-run after the fix: all checks PASS, identical
  in structure to the pre-fix run.

Files:
- Created:
  experiments/psychological_levels_dynamic/scenario_catalog/__init__.py
  experiments/psychological_levels_dynamic/scenario_catalog/catalog.py
  experiments/psychological_levels_dynamic/scenario_catalog/specifications.py
  experiments/psychological_levels_dynamic/scenario_catalog/families/__init__.py
  experiments/psychological_levels_dynamic/scenario_catalog/families/baseline.py
  experiments/psychological_levels_dynamic/scenario_catalog/families/adversarial_attacker_pressure.py
  experiments/psychological_levels_dynamic/scenario_catalog/families/regime_change_into_pressure.py
  experiments/psychological_levels_dynamic/scenario_catalog/families/repeated_attacks.py
  experiments/psychological_levels_dynamic/scenario_catalog/test_scenario_catalog.py
- Updated:
  chatgpt_project_context/CURRENT_CHECKPOINT.md
  chatgpt_project_context/MASTER_STATUS_COMPACT.md

No optional Scenario Runner smoke check was used, to keep this phase
strictly to catalog construction -- reported as
"no_runner_execution = PASS" (no smoke check used).

Exact deterministic results:
- families_registered = 4 (BASELINE, ADVERSARIAL_ATTACKER_PRESSURE,
  REGIME_CHANGE_INTO_PRESSURE, REPEATED_ATTACKS)
- specifications_registered = 4 (BASELINE_TRIANGULAR_REFERENCE_V1,
  ADVERSARIAL_ESCALATING_PENETRATION_V1, REGIME_QUIET_TO_PRESSURE_V1,
  REPEATED_ATTACKS_PARTIAL_RECOVERY_V1)
- providers_registered = PASS (all price_only=True, research_only=True)
- specifications_registered = PASS
- unique_scenario_ids = PASS
- fingerprints_stable = PASS
- price_only_generation = PASS
- determinism = PASS
- distinct_path_shapes = PASS
- notes_not_required_for_generation = PASS
- no_stage_imports = PASS
- no_runner_execution = PASS
- errors = []
- result = PASS
- Confirmed identical when run from the repo root and from the catalog's
  own directory (self-contained sys.path bootstrap on every file).

Exact validation commands:
- python -m py_compile on catalog.py, specifications.py, all four
  families/*.py, and test_scenario_catalog.py
- python experiments/psychological_levels_dynamic/scenario_catalog/test_scenario_catalog.py
- git diff --check
- git status
- git diff --name-only -- core/ research/ engines/

Boundary:
- Catalog only; defines experimental inputs only. Does not run Stage 1-6,
  does not execute the Scenario Runner, does not compare scenario outputs,
  does not validate or require RESEARCH_ATTACKER_PRESSURE or any other
  downstream Dynamic State.
- No Stage 1-6 file modified. No Scenario Runner logic modified.
- No Project 1, production, dashboard, live pipeline, Snapshot architecture,
  Worker, Queue, Bootstrap, or RDM formula changes.
- No Phase 2 trading, execution, BUY/SELL, HOLD/FAIL, or live signals.
- No production behavior changed.

Next:
Await Scenario Catalog Foundation review and commit approval.

---

## Active Checkpoint: PHASE1C_SCENARIO_RUNNER_STABLE

Status: IMPLEMENTED AND VALIDATED - awaiting review before commit.
Research-only, offline-only, Project 2 Chapter II Phase 2.

Implemented:
- Thin, additive Scenario Runner executing exactly one ScenarioSpecification
  at a time. No batch execution, no cross-scenario comparison, no
  sensitivity analysis, no learning, no storage by default.
- Reuses ZoneHarness / update_mechanics() / compute_dynamics() from Stage 1
  unchanged; InteractionInterpreter / EventDispatcher / ORDER_ACCEPTED /
  LastCompletedVisitAdapter unchanged; PsychologicalLevelsProvider
  unchanged, parameterized from scenario geometry_parameters instead of
  Stage 1's hardcoded constants.
- The only duplicated structure is a thin per-row driving loop mirroring
  Stage 3's completed-visit collection pattern (Interpreter +
  LastCompletedVisitAdapter only -- no Dispatcher/Coordinator/Snapshot).
- The per-scenario analytical path is explicitly Stage 1 mechanics and
  completed-visit collection plus Stage 3 transition analysis, Stage 4
  graph analysis, Stage 5 trajectory analysis, and Stage 6 hypothesis
  evaluation. Stage 2 Snapshot compatibility remains prevalidated and is
  intentionally not rerun per scenario.
- Does not call Stage 1 generate_price()/build_harnesses()/run() or Stage 3
  collect_completed_visits() -- each is tied to the fixed triangular corpus
  with no scenario injection point.
- Calls Stage 3 analyze(), Stage 4 analyze_transition_graph(), Stage 5
  analyze(), Stage 6 analyze() directly and unchanged via qualified module
  imports (stage3/stage4/stage5/stage6 aliases) -- no star imports, since
  Stage 4/5/6 each define a function named analyze. Wraps each stage's
  existing output verbatim; invents no new analytical metric.
- Structural price-only validation: contiguous row ordering, finite Decimal
  prices, row count matches specification, and a dataclass-field check
  confirming PriceObservation carries only row_index/price (no label,
  mechanics, transition, or hypothesis field exists to smuggle one into).
- Immutable ScenarioRunResult with full provenance: scenario_id,
  scenario_family, specification_fingerprint, provider_version,
  scenario_schema_version, chain_version, run_id, row_count,
  observation_checksum -- run_id and observation_checksum computed via the
  same canonical-JSON + SHA-256 helper (_canonical_value) already built in
  Phase 1, reused unchanged rather than re-implemented.
- Per-run internal determinism self-check (observations generated twice and
  compared) plus a separate three-run, cross-run canonical-JSON equality
  check in the test file.
- Self-contained frozen-file provenance and drift guard: line endings are
  normalized before hashing, making checks stable across CRLF/LF
  environments. The normalized hashes also form chain_fingerprint, which
  is recorded in ScenarioRunResult and included in run_id.

Files:
- Created:
  experiments/psychological_levels_dynamic/scenario_runner.py
  experiments/psychological_levels_dynamic/test_scenario_runner.py
- Updated:
  chatgpt_project_context/CURRENT_CHECKPOINT.md
  chatgpt_project_context/MASTER_STATUS_COMPACT.md

No separate scenario_chain_adapter.py was created -- the harness-
construction, driving loop, and orchestration are cohesive enough to keep in
one file at this scale; reported as
"chain_adapter = NOT_SEPARATED (integrated into scenario_runner.py)".

Exact deterministic results (cross-checked against already-verified
Chapter I ground truth, reproduced by feeding the identical triangular price
shape through the Scenario Runner instead of Stage 1's hardcoded generator):
- zones_observed = 7
- completed_visits = 159
- observation_count = 3000
- row_count = 3000
- chain_version = PHASE1B_STAGE1_AND_STAGE3_TO_STAGE6_STABLE
- chain_fingerprint is normalized-source SHA-256 provenance
- stage3: transitions_generated = 145, all_research_prefixed = True,
  counts_consistent = True
- stage4: transitions_generated = 145, transition_counts matches
  {RECOVERING_TO_STABLE: 60, STABLE_TO_RECOVERING: 61, STABLE_TO_STABLE: 24},
  critical_transition_count = 0, absorbing_states = []
- stage5: trajectory_records_generated = 159, unobserved_states =
  [RESEARCH_ATTACKER_PRESSURE], attacker_pressure_observed = False,
  predictions_generated = False
- stage6: hypotheses_generated = 152, eligible_hypotheses = 110,
  confirmed_count = 103, invalidated_count = 0, pending_count = 7,
  forced_hypothesis_under_weak_evidence = False,
  predictions_generated = False
- contiguous_row_ordering = True, finite_price_validation = True,
  price_only_contract_validation = True, deterministic_generation = True
- run_id and observation_checksum identical across 3 independent runs and
  across 2 separate process invocations
- second parameterized 600-row case = PASS and deterministic across 2 runs
- variant fingerprint, checksum, and run_id differ from baseline
- errors = []
- result = PASS

Exact validation commands:
- python -m py_compile
  experiments/psychological_levels_dynamic/scenario_runner.py
- python -m py_compile
  experiments/psychological_levels_dynamic/test_scenario_runner.py
- python experiments/psychological_levels_dynamic/test_scenario_runner.py
- git diff --check
- git status
- git diff --name-only -- core/ research/ engines/

Boundary:
- Runner only; no new analytical layer, no batch execution, no
  cross-scenario comparison, no sensitivity analysis, no learning.
- No Chapter I Stage 1-6 file modified (confirmed via git diff and the
  normalized frozen-file provenance/drift guard).
- No Project 1, production, dashboard, live pipeline, Snapshot architecture,
  Worker, Queue, Bootstrap, or RDM formula changes.
- No Phase 2 trading, execution, BUY/SELL, HOLD/FAIL, or live signals.
- No production behavior changed.

Next:
Await Scenario Runner review and commit approval.

---

## Active Checkpoint: PHASE1C_SCENARIO_GENERATOR_FOUNDATION_STABLE

Status: IMPLEMENTED AND VALIDATED - awaiting review before commit.
Research-only, offline-only, Project 2 Chapter II foundation.

Implemented:
- Frozen ScenarioSpecification with deeply immutable parameter,
  geometry-parameter, and validation-metadata mappings.
- Frozen PriceObservation containing row_index and price only.
- Runtime-checkable ScenarioProvider Protocol exposing metadata(),
  validate_spec(), and generate().
- Explicit ScenarioRegistry with duplicate protection, no scanning,
  reflection, plugin loading, or dynamic imports.
- Registry import is self-contained through the established local-directory
  bootstrap and does not rely on caller sys.path preparation.
- Canonical SHA-256 specification fingerprint for provenance and drift
  detection.
- Parameters are restricted to deterministic canonical immutable scalar and
  container types; floats, sets, and arbitrary custom objects are rejected.
- Pure Decimal mathematical primitives:
  triangular_wave(), linear_trend(), bounded_range(), step_pattern().
- Foundation-only local test provider; no scenario runner and no connection
  to the Stage 1-6 chain.

Files created:
- experiments/psychological_levels_dynamic/scenario_contract.py
- experiments/psychological_levels_dynamic/scenario_registry.py
- experiments/psychological_levels_dynamic/scenario_primitives.py
- experiments/psychological_levels_dynamic/test_scenario_foundation.py

Files updated:
- chatgpt_project_context/CURRENT_CHECKPOINT.md
- chatgpt_project_context/MASTER_STATUS_COMPACT.md

Deterministic foundation results:
- scenario_contract = PASS
- registry = PASS
- primitives = PASS
- determinism = PASS
- price_only_output = PASS
- research_only = PASS
- errors = []
- result = PASS
- repeated provider generation is identical
- equivalent reordered specifications have identical fingerprints
- changed specifications have different fingerprints
- isolated self-contained registry import = PASS
- triangle path = 100, 110, 120, 110, 100, 110, 120, 110
- linear, bounded-range, step, and triangular paths are distinct
- generated observations contain only row_index and Decimal price
- random and seeded PRNG generation are not used

Exact validation commands:
- python -m py_compile
  experiments/psychological_levels_dynamic/scenario_contract.py
  experiments/psychological_levels_dynamic/scenario_registry.py
  experiments/psychological_levels_dynamic/scenario_primitives.py
  experiments/psychological_levels_dynamic/test_scenario_foundation.py
- python
  experiments/psychological_levels_dynamic/test_scenario_foundation.py
- git diff --check
- git status

Boundary:
- Foundation only; no Scenario Runner.
- No scenario is executed through Dynamic Mechanics.
- No Stage 1-6 files changed or imported by the foundation.
- No Project 1, production, dashboard, live pipeline, Snapshot architecture,
  Worker, Queue, Bootstrap, RDM, or production B10/B11 changes.
- No trading, execution, or Phase 2.
- No production behavior changed.

Next:
Await Chapter II Phase 1 review. Do not commit yet.

---

## Active Checkpoint: PHASE1B_PREDICTION_EVOLUTION_STAGE6_STABLE

Status: REVISED AND VALIDATED - awaiting review before commit.
Research-only, offline-only, Project 2 only.

Architecture:
- Hypothesis generation and validation are structurally separate.
- generate_hypothesis() receives only Stage 5 prefix records through visit N
  and the current visit N record.
- validate_hypothesis() receives only an already-created hypothesis and visit
  N+1 when available.
- The generator has no outcome, next-visit, full-label, or future-visit input.
- Stage 4's full-corpus probability matrix is not imported or used.
- Evidence is per-zone only; no cross-zone pooling.

Weak-evidence guards:
- MIN_TRANSITION_SAMPLES = 3
- MIN_DOMINANT_MARGIN = 0.15
- MIN_HYPOTHESIS_CONFIDENCE = 0.35
- Ties, low margins, low confidence, unsupported states, and absent outgoing
  evidence abstain instead of forcing an expected state.
- Abstention uses expected_next_research_state=NOT_AVAILABLE and
  trajectory_continuation_hypothesis=RESEARCH_UNCERTAIN.
- Abstained hypotheses are never graded confirmed or invalidated.

Leakage validation:
- Independent prefix recomputation checks every generated hypothesis.
- 21 representative future-mutation checks aggressively alter all visits
  after N; hypothesis N remains dict-equivalent.
- Validation targets exactly visit N+1.
- Generation records contain no validation/outcome fields.
- All leakage violation lists are empty.

Negative controls:
- Tied destination history abstains.
- Low-margin history abstains.
- Deliberately wrong next state becomes RESEARCH_INVALIDATED.
- Unsupported current state abstains without guessing.
- Eligible final visit remains RESEARCH_PENDING.
- First unavailable visit remains NOT_AVAILABLE.
- negative_controls_pass = True

Files:
- Created/revised:
  experiments/psychological_levels_dynamic/test_prediction_evolution.py
- Updated:
  chatgpt_project_context/CURRENT_CHECKPOINT.md
  chatgpt_project_context/MASTER_STATUS_COMPACT.md

Exact revised deterministic results:
- zones_observed = 7
- completed_visits = 159
- hypotheses_generated = 152
- eligible_hypotheses = 110
- insufficient_sample_count = 39
- insufficient_evidence_count = 3
- abstention_count = 42
- uncertain_count = 42
- confirmed_count = 103
- invalidated_count = 0
- pending_count = 7
- coverage = 0.6776315789473685
- descriptive_confirmation_rate = 1.0
- unsupported_states = RESEARCH_ATTACKER_PRESSURE
- attacker_pressure_observed = False
- generation_validation_separated = True
- future_mutation_invariance = True
- future_mutation_checks = 21
- negative_controls_pass = True
- forced_hypothesis_under_weak_evidence = False
- leakage_violation_details = []
- negative_control_failures = []
- deterministic_across_runs = True
- errors = []
- result = PASS

Result changes after abstention:
- eligible_hypotheses: 113 -> 110
- insufficient_evidence_count: 0 -> 3
- abstention_count: 39 -> 42
- confirmed_count: 106 -> 103
- coverage: 0.6973684210526315 -> 0.6776315789473685

The descriptive confirmation rate is not trading accuracy and is not
production validation. It is only a research metric on this deterministic
synthetic corpus.

Exact validation commands:
- python -m py_compile
  experiments/psychological_levels_dynamic/test_prediction_evolution.py
- python
  experiments/psychological_levels_dynamic/test_prediction_evolution.py
- git diff --check
- git status
- git diff --name-only -- core/ research/ engines/

Boundary:
- No Project 1, production, dashboard, live pipeline, Snapshot architecture,
  Worker, Queue, Bootstrap, RDM formula, or production B10/B11 changes.
- No Entropy, Footprint, Structure, Statistics, Gaussian, Context, Decision,
  or Execution engine introduced.
- No trading, execution, BUY/SELL, HOLD/FAIL, entries/exits, or live signals.
- No production behavior changed.

Next:
Await revised Stage 6 review. Do not commit yet.

---

## Active Checkpoint: PHASE1B_TRAJECTORY_EVOLUTION_STAGE5_STABLE

Status: STABLE CHECKPOINT - research-only, offline-only, Project 2 only.
Stage 5 reconstructs visit-by-visit trajectory evolution from unchanged
Stage 3 completed visits and Stage 1 Dynamic Mechanics.

Implemented:
- One canonical ordered research record per completed zone visit.
- Per-zone visit, state, and transition trajectory reconstruction.
- Descriptive mechanical evolution by research state.
- Descriptive mechanical deltas around each observed transition.
- Previous/transition/next local transition windows.
- Per-zone trajectory signatures and cross-zone comparison.
- Research sample-sufficiency guards.
- Explicit unobserved-state and NOT_AVAILABLE reporting.
- Three-run deterministic validation.

Files:
- Created:
  experiments/psychological_levels_dynamic/test_trajectory_evolution.py
- Updated:
  chatgpt_project_context/CURRENT_CHECKPOINT.md
  chatgpt_project_context/MASTER_STATUS_COMPACT.md

Exact deterministic results:
- zones_observed = 7
- trajectory_records_generated = 159
- completed_visits = 159
- transitions_generated = 145
- per-zone visit counts = 23, 23, 23, 23, 23, 22, 22
- per-zone transition counts = 21, 21, 21, 21, 21, 20, 20
- observed_states = RESEARCH_RECOVERING, RESEARCH_STABLE
- state samples: RECOVERING=61, STABLE=91
- unobserved_states = RESEARCH_ATTACKER_PRESSURE
- attacker_pressure_observed = False
- unsupported_state_count = 0
- initial NOT_AVAILABLE state records = 7
- RESEARCH_STABLE_TO_RESEARCH_RECOVERING = 61
- RESEARCH_RECOVERING_TO_RESEARCH_STABLE = 60
- RESEARCH_STABLE_TO_RESEARCH_STABLE = 24
- transition-window complete next visits = 60, 55, 23 respectively
- high_oscillation_zones = 6
- single_state_zones = 1 (PSY_BTCUSDT_60400)
- zones_with_no_transitions = 0
- zones_with_unsupported_states = 0
- insufficient_sample_flags = 1
- RESEARCH_ATTACKER_PRESSURE sample status = INSUFFICIENT_SAMPLE
- all observed states and transitions remain RESEARCH_ prefixed
- NOT_AVAILABLE behavior validated
- deterministic_across_runs = True
- errors = []
- result = PASS

Exact validation commands:
- python -m py_compile
  experiments/psychological_levels_dynamic/test_trajectory_evolution.py
- python
  experiments/psychological_levels_dynamic/test_trajectory_evolution.py
- git diff --check
- git status

Boundary:
- Descriptive trajectory research only; no prediction or causal claims.
- No production B10/B11 or Dynamic State changes.
- No Project 1, production, dashboard, live pipeline, Snapshot architecture,
  Worker, Queue, Bootstrap, or RDM formula changes.
- No Entropy, Footprint, Structure, Statistics, Gaussian, Context, Decision,
  or Execution engine introduced.
- No production behavior changed.

Next:
Await Stage 5 review and the next Phase 1B research approval.

---

## Active Checkpoint: PHASE1B_TRANSITION_GRAPH_STAGE4_STABLE

Status: STABLE CHECKPOINT - research-only, offline-only, Project 2 only.
Stage 4 builds a Transition Graph over the unchanged Stage 3 Dynamic State
visit sequences.

Implemented:
- Transition probability matrix with outgoing and destination counts.
- Per-zone and per-state residence run lengths with mean, min, max, and total
  runs.
- State self-transition persistence probabilities.
- Simple cycle detection for
  RESEARCH_STABLE -> RESEARCH_RECOVERING -> RESEARCH_STABLE.
- Research-only critical transitions into RESEARCH_ATTACKER_PRESSURE.
- Absorbing-like state detection.
- Multi-step early-warning paths ending in RESEARCH_ATTACKER_PRESSURE.
- Three-run deterministic validation.

Files:
- Created:
  experiments/psychological_levels_dynamic/test_transition_graph.py
- Updated:
  chatgpt_project_context/CURRENT_CHECKPOINT.md
  chatgpt_project_context/MASTER_STATUS_COMPACT.md

Exact deterministic results:
- zones_observed = 7
- completed_visits = 159
- transitions_generated = 145
- unique_states = RESEARCH_RECOVERING, RESEARCH_STABLE
- unique_transition_types = 3
- RESEARCH_STABLE_TO_RESEARCH_RECOVERING = 61
- RESEARCH_RECOVERING_TO_RESEARCH_STABLE = 60
- RESEARCH_STABLE_TO_RESEARCH_STABLE = 24
- P(RECOVERING -> STABLE) = 1.0
- P(STABLE -> RECOVERING) = 0.7176470588235294
- P(STABLE -> STABLE) = 0.2823529411764706
- RECOVERING residence: mean=1.0, min=1, max=1, total_runs=61
- STABLE residence: mean=1.3582089552238805, min=1, max=22,
  total_runs=67
- RECOVERING persistence = 0.0 (0 / 60)
- STABLE persistence = 0.2823529411764706 (24 / 85)
- STABLE -> RECOVERING -> STABLE cycle count = 60 across 6 zones
- critical_transition_count = 0
- absorbing_states = []
- early_warning_paths_count = 0
- probability rows sum to 1.0 within tolerance
- all labels remain RESEARCH_ prefixed
- deterministic_across_runs = True
- errors = []
- result = PASS

Exact validation commands:
- python -m py_compile
  experiments/psychological_levels_dynamic/test_transition_graph.py
- python experiments/psychological_levels_dynamic/test_transition_graph.py
- git diff --check

Boundary:
- Graph analysis only; no prediction generation or Dynamic State changes.
- No Project 1, production, dashboard, live pipeline, Worker, Queue,
  Bootstrap, Snapshot architecture, RDM formula, B10, or B11 changes.
- No production behavior changed.

Next:
Await the next Phase 1B research-stage approval.

---

## Active Checkpoint: PHASE1B_DYNAMIC_STATE_TRANSITION_STAGE3_STABLE

Status: STABLE CHECKPOINT — research-only, no production behavior changed.
Stage 3 analyzes transitions between research Dynamic States produced by
Stage 1/2.

- **Stage 3 analyzes research Dynamic State transitions** — current/previous
  dynamic_state, transition_name, transition frequency, per-zone chains,
  repeated transitions, stable vs unstable sequences, and a simple
  research-only early-warning pattern.
- **Uses Stage 1 Dynamic Mechanics unchanged** — build_harnesses,
  generate_price, update_mechanics, compute_dynamics imported directly from
  dynamic_mechanics_test.py, no duplication.
- **Interpreter-driven completed visits reused** — only the Interaction
  Interpreter and LastCompletedVisitAdapter are used to collect completed-visit
  sequences; Dispatcher/Coordinator/Snapshot are not needed for this analysis
  and are not used (Stage 2 already validated that path).
- **No production changes. No Project 1 changes. No live integration. No
  dashboard. No Snapshot modifications. No B10/B11 changes.**
- **All labels remain RESEARCH_ prefixed** — every transition_name verified
  RESEARCH_-prefixed on both sides.

Results (deterministic across three independent runs):
- zones_observed = 7
- completed_visits = 159
- transitions_generated = 145
- unique_transition_types = 3

Transition frequencies:
- RESEARCH_STABLE_TO_RESEARCH_RECOVERING = 61
- RESEARCH_RECOVERING_TO_RESEARCH_STABLE = 60
- RESEARCH_STABLE_TO_RESEARCH_STABLE = 24

- per_zone_transition_counts validated (sums exactly to transitions_generated)
- repeated_transition_chains = 20
- stable_state_sequences = 1
- unstable_state_sequences = 6
- research-only early_warning_transitions = 0
- deterministic across three runs
- errors = 0
- result = PASS

Validation (all pass):
- py_compile
  experiments/psychological_levels_dynamic/test_dynamic_state_transitions.py
  -> OK
- run -> PASS (reproduced across three independent runs)
- git diff --check clean

Next: Phase 1B Stage 4 trajectory evolution research.

---

## Active Checkpoint: PHASE1B_DYNAMIC_MECHANICS_SNAPSHOT_STAGE2_STABLE

Status: STABLE CHECKPOINT — research-only, no production behavior changed.
Stage 2 mapped Stage 1's research Dynamic Mechanics outputs into the Canonical
Snapshot dynamic_mechanics section.

- **Stage 2 mapped research Dynamic Mechanics into Canonical Snapshot
  dynamic_mechanics section** via the existing, unmodified
  DynamicMechanicsAdapter.build_patch().
- **Offline only.** No production changes. No Project 1 changes. No
  live/dashboard/B10/B11 changes.
- **Reused Stage 1 logic unmodified** — build_harnesses, generate_price,
  update_mechanics, compute_dynamics imported directly from
  experiments/psychological_levels_dynamic/dynamic_mechanics_test.py, no
  duplication.
- **Committed LastCompletedVisit + DynamicMechanics patches atomically** into
  SnapshotStore, mirroring the exact multi-adapter commit pattern already
  proven in Phase 0 / Phase 1A.
- **SIMPLE_RESEARCH_SDR_V1 remains research-only.**
- **RESEARCH_ labels only** — dynamic_state/previous_dynamic_state/
  transition_name all trace to RESEARCH_-prefixed values, never production
  B12.5 Dynamic State.
- **NOT_AVAILABLE behavior validated** — fields Stage 1 never computed
  (health_slope, omega_total, dynamic_state_reason, ...) map to NOT_AVAILABLE
  automatically; first-visit-per-zone derivative/state fields also correctly
  NOT_AVAILABLE (no prior visit to differentiate against yet).

Results (deterministic across three independent runs):
- rows_processed = 3000
- zones_observed = 7
- completed_visits = 159
- dynamic_mechanics_commits = 159
- snapshot_revisions_total = 159
- revision_monotonicity = True
- copy_on_write = True
- global_zone_key_preserved = True
- dynamic_section_updated = True
- previous_state_chain_consistent = True
- transitions_research_only = True
- not_available_counts = {first_derivative: 7, second_derivative: 14,
  dynamic_state: 7, transition_name: 14}
- not_available_expected = True
- deterministic_across_runs = True
- errors = 0
- result = PASS

Validation (all pass):
- py_compile
  experiments/psychological_levels_dynamic/test_snapshot_dynamic_mechanics.py
  -> OK
- run -> PASS (reproduced across three runs)
- git diff --check clean

Next: Stage 3 Dynamic State transition analysis approval.

---

## Active Checkpoint: PHASE1B_DYNAMIC_MECHANICS_STAGE1_OFFLINE_STABLE

Status: STABLE CHECKPOINT — research-only, no production behavior changed.
First Phase 1B offline validation: Dynamic Mechanics research metrics computed
from Project 2 Psychological Levels completed-visit sequences.

- **Project 2 Psychological Levels used as offline research geometry** —
  reuses experiments/psychological_levels/provider.py (Phase 1A, unmodified)
  as the input laboratory; same triangular price-sweep shape for continuity.
- **Real Interpreter -> Dispatcher -> Coordinator -> LastCompletedVisitAdapter
  path reused**, unmodified — core.interaction_interpreter,
  core.event_dispatcher, and core.last_completed_visit_adapter are the same,
  unmodified components validated throughout Phase 0 / Phase 1A.
- **No core/production modifications** — verified via git status: zero
  core/, research/, or engines/ file touched by this task.
- **Research-only deterministic proxy mechanics** — since the interpreter's
  own VISIT_COMPLETED evidence carries only geometric/timing fields, not
  mechanical values, a small deterministic per-row proxy tracks:
  health_live, omega_accumulator, attacker_force_peak
  clearly labeled as invented for this experiment only, not a Project 1
  formula, feeding health_at_visit/omega_at_visit/attacker_force_at_visit
  into the unmodified LastCompletedVisitAdapter at each visit completion.
- **Production formulas not changed.**
- **SIMPLE_RESEARCH_SDR_V1 is research-only** — `|delta omega| / health`, an
  explicitly versioned, independent research ratio, NOT the production
  Structural Dynamic Response formula used elsewhere in this codebase.
- **RESEARCH_ labels only** (RESEARCH_ATTACKER_PRESSURE /
  RESEARCH_RECOVERING / RESEARCH_STABLE), not production B12.5 Dynamic State.
- **SnapshotStore deliberately not used in Stage 1** — only the derived
  completed-visit series is needed; can be added in a later stage if
  snapshot-level Dynamic Mechanics patches need testing.

Results (deterministic, reproduced identically on a second run):
- rows_processed = 3000
- zones_observed = 7
- completed_visits = 159
- first_derivatives_generated = 152
- integrals_generated = 159
- second_derivatives_generated = 145
- sdr_values_generated = 152
- dynamic_labels_generated = 152
- errors = 0
- result = PASS

Validation (all pass): py_compile
experiments/psychological_levels_dynamic/dynamic_mechanics_test.py -> OK; run
-> PASS (reproduced on a second run); git diff --check clean.

Next: Stage 2 snapshot dynamic mechanics approval.

---

## Active Checkpoint: RDM_V2_PHASE0_PASSIVE_SHADOW_PRODUCTION_SAFE

Status: PHASE 0 CLOSED — PRODUCTION SAFE. This is the final Phase 0 checkpoint.
Note the deliberate distinction from "PRODUCTION VALIDATED": the shadow
pipeline's end-to-end correctness under load is proven by the Replay Soak;
what the two LIVE soaks add is proof that the passive shadow is SAFE to run
alongside real production for a sustained period without any impact.

Journey summary: Safety Modules -> Runtime Emitter -> Live Tap -> Passive
Worker -> Runtime Connection -> Parity Logging -> Bootstrap -> Repository
Integrity Fix -> Replay Soak PASS -> Controlled LIVE Soak PASS -> Extended
LIVE Soak INCONCLUSIVE (market_event_scarcity, shadow pipeline not at fault).

Soak history:
- **Replay soak: PASS** — full shadow runtime validated end-to-end against
  research replay data (identity, ordering, atomic revisions, adapters).
- **Controlled LIVE soak: PASS** — first real-production run of the passive
  tap; payloads received/processed/parity all clean.
- **Extended LIVE soak: INCONCLUSIVE due to MARKET_EVENT_SCARCITY** — 60
  minutes at the hard cap, zero failures of any kind (failed=0, dropped=0,
  desynchronized=0, breaker never tripped, zero production exceptions, memory
  flat ~99-101MB, revision monotonicity / copy-on-write / identity integrity
  all HELD vacuously). processed=0 because zero payloads were available to
  process, not because any were lost or mishandled.

Why zero payloads, confirmed by direct evidence (not inferred): checked
outputs/live_preparation_zones.csv, outputs/live_return_detection.csv, and
outputs/live_rdm_results.csv directly.
- live_return_detection.csv and live_rdm_results.csv: zero new rows during the
  soak AND zero new rows for the full week preceding it (last write
  2026-06-25) -- consistent, since compute_live_rdm_for_case is only called on
  return_found, and return_found never fired.
- live_preparation_zones.csv: last preparation-candidate activity predates the
  soak window by several hours, and even those rows were logged rejections
  ("No preparation candidate: ... conditions were not aligned").
- No emitter DISABLED/DROPPED/ERROR status at any point -- the tap was armed
  (SHADOW_RUNTIME_ENABLED=1) for the full run; stderr was empty (0 lines) the
  entire hour. The emitter/queue/worker/runtime/parity chain was never given a
  payload to process; it did not fail to receive or handle one.
- **Shadow pipeline not at fault.** No payloads because Project 1
  (Preparation Zone / Active Core / Density Band geometry -- NOT Psychological
  Levels) produced no Preparation/Return case during the window.

Production safety verified over 60 continuous real minutes: no production
exception, no drop, no desynchronization, no breaker trip, no parity path
violation, no memory growth, no interference with the live stream at any point.

Phase 0 infrastructure: **COMPLETE.**

Phase 0 policy: **FROZEN**, except critical production bug fixes.
- Allowed: critical production bug fixes only.
- Not allowed: new Phase 0 architecture, refactoring, snapshot redesign, queue
  redesign, worker redesign, bootstrap redesign, contract redesign, coordinator
  redesign.

Future payload-rich validation may run opportunistically whenever Project 1
emits enough Preparation/Return cases -- not a blocking gate on further work.

Next: Phase 1 -- System Intelligence.

---

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

Identity guarantees:
- Stale manifests rebuild safely.
- Malformed manifests recover safely without crashing live processing.
- Algeria session boundaries use exchange timestamps.
- Identity is created once and inherited through preparation -> return -> RDM
  -> evolution -> dynamic outputs.
- Same-session restart counters recover from existing episode records.
- Live dynamic joins use global_case_id.
- Legacy rows are isolated and never mixed with session-identified rows.

Propagated fields:
- session_id
- market_date
- session_episode_id
- global_episode_key
- global_case_id

CSV safety:
- Schema migrations use atomic temporary-file replacement.
- Migrations preserve the union of existing and new columns.

Boundary:
- No Project 1 formulas changed.
- No Phase 1A files changed.
- No dashboard, Snapshot, Worker, Queue, Bootstrap, Project 2, or B10/B11
  changes.

Validation:
- Scoped py_compile: PASS
- Focused identity validation: PASS
- git diff --check: PASS

Next:
Begin Phase 1B Dynamic Mechanics design.

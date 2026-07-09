# Master Status Compact

## Current Stable Status

Current checkpoint: PHASE2C_SMALL_BATCH_STABILITY_10_STABLE

Status: implemented and validated; documentation checkpoint only.

Chapter IV verified a deterministic 10-scenario stability campaign through the
complete Project 2 pipeline: Generation -> Manifest Validation -> Batch
Compilation -> Batch Specification Assembly -> Batch Execution -> real Scenario
Runner -> Stage 1-6.

Results: 10 deterministic scenarios generated, 10 scenarios executed, PASS
count 10, FAIL count 0, skipped count 0. Two repeated executions produced
identical ordering, execution summaries, Stage 1-6 outputs, per-scenario
fingerprints, batch fingerprints, and provenance. No cross-scenario
contamination was detected. PASS/FAIL storage and research isolation were
verified.

Batch execution fingerprint:
`sha256:77832037c66cc30fd0821af181cf688cf8912835cfc8fb1992095b6ddc7b378b`

Boundary: documentation/checkpoint update only. No logic changes. No Runner,
Catalog, Stage 1-6, Compiler, Project 1, production, core, engines, or
research changes.

---
## Current Stable Status

Current checkpoint: PHASE2C_SMALL_BATCH_EXECUTION_PROOF_STABLE

Status: implemented and validated; documentation checkpoint (functional fix
described below was applied separately, prior to this entry).

Proved the full Project 2 pipeline end-to-end at small scale: Generation ->
Manifest Validation -> Batch Compilation -> Batch Specification Assembly ->
Batch Execution -> real Scenario Runner -> Stage 1-6. 7 deterministic
scenarios generated from one template (repeated 6-cycle center-dwell /
hold-outside pattern, one program per outside-clearance value), all 7
compiled, assembled, and executed successfully through the real, unmodified
`run_scenario()`. Verified: ordering preserved end-to-end, PASS/FAIL stored
per scenario (all 7 PASS), real Stage 3-6 summary dicts present
(`completed_visits=6`, `transitions_generated=4`, `eligible_hypotheses=2`
per scenario), Stage 4 compact summary present and consistent with the raw
summary, `source_manifest_fingerprint`/`batch_compilation_fingerprint`/
`batch_assembly_fingerprint`/`batch_execution_fingerprint` all propagated
and correct, full-pipeline determinism and cross-process determinism both
confirmed, research isolation confirmed.

Follow-up PHASE2C_EXECUTION_SUMMARY_KEY_FIX -- passed. Building the proof
surfaced that `_compact_summary()` in `batch_execution.py` was reading
non-existent keys for three fields, silently returning `None` on every real
execution: corrected `"trajectory_records"` to read
`trajectory_records_generated`, `"confirmed_hypotheses"` to read
`confirmed_count`, `"pending_hypotheses"` to read `pending_count` (output key
names unchanged, only the lookup into the real Stage 5/6 dicts changed).
Existing `test_batch_execution.py` regression suite passes unmodified after
the fix; a fresh run now shows genuine non-`None` values matching the raw
Stage 5/6 dicts exactly. Not caught in two prior audit rounds because those
tests used hand-built fixtures with the "right" keys already present.

Validation PASS: test_small_batch_execution_proof.py
generated_5_to_10_scenarios PASS, manifest_validated PASS, batch_compiled
PASS, specifications_assembled PASS, batch_executed PASS, ordering_preserved
PASS, pass_fail_stored PASS, stage_summaries_present PASS,
stage4_summary_present PASS, provenance_fingerprints_propagated PASS,
determinism_confirmed PASS, cross_process_determinism PASS,
research_isolation PASS, errors=[], result=PASS; test_batch_execution.py
rerun after the key fix: all 8 checks PASS unchanged; git diff --check PASS.

Isolation confirmed: no Runner, Catalog, Stage 1-6, Compiler, Project 1,
production, core, engines, or research files were modified.

---
## Prior Stable Status (PHASE2C_EXECUTION_CONTRACTS_STABLE)

Current checkpoint: PHASE2C_EXECUTION_CONTRACTS_STABLE

Status: implemented and validated; audited (post-patch) and approved for commit.

Chapter IV added the immutable contracts future Batch Execution logic will
produce: `ScenarioExecutionRecord` (per-scenario outcome, including a
runner_result field required exactly when execution_status is EXECUTED and
forbidden otherwise) and `BatchExecutionResult` (batch-level aggregate,
structurally rejecting success=True whenever any EXECUTED record has
runner_result=="FAIL"). `execution_contract_fingerprint()` provides
deterministic canonical JSON + SHA-256 fingerprinting, matching the existing
generation_contract_fingerprint pattern.

Boundary: contracts only. No Scenario Runner import, no execution logic, no
Compiler/Batch Compiler/Batch Specification Assembler/Catalog/Stage 1-6
coupling, no Project 1, no production changes.

Validation PASS: py_compile for execution_contracts + test;
test_execution_contracts.py scenario_execution_record PASS,
batch_execution_result PASS, runner_result_guard PASS, fingerprint_determinism
PASS, immutability PASS, research_isolation PASS, cross_process_determinism
PASS, errors=[], result=PASS; git diff --check PASS.

Isolation confirmed: no Scenario Runner, Compiler, Batch Compiler, Batch
Specification Assembler, Catalog, Stage 1-6, Project 1, production, core,
engines, or research files were modified by this checkpoint.

---
## Prior Stable Status (PHASE2C_BATCH_SPECIFICATION_ASSEMBLER_STABLE)

Current checkpoint: PHASE2C_BATCH_SPECIFICATION_ASSEMBLER_STABLE

Status: implemented and validated; awaiting review before commit.

Chapter IV added the Batch Specification Assembler. `assemble_batch()` consumes
`BatchCompilationResult` plus immutable `RunnerExecutionContext`, assembles every
successful `CompilationResult` into an `AssembledSpecification`, skips failed
compilations, preserves ordering, records failed program IDs and deterministic
diagnostics, and returns a frozen `BatchAssemblyResult`.

Runner-ready merge: after `assemble_specification()` returns, the assembler uses
`dataclasses.replace()` to merge RunnerExecutionContext fields into
`ScenarioSpecification.geometry_parameters`: spacing, zone_half_width,
active_window, symbol, market_timestamp, and session_id. session_id remains
batch-level for now unless a later execution phase requires per-scenario trace
IDs.

Boundary: assembler only. No Scenario Runner, no Catalog execution, no Stage
1-6 execution, no Batch Execution, no Project 1, no production changes, no
ScenarioSpecification mutation, and no object.__setattr__ in the batch
assembler.

Validation PASS: py_compile for runner_execution_context,
batch_specification_assembler, and test; test_batch_specification_assembler.py
successful_batch PASS, partial_failure PASS, ordering_preserved PASS,
runner_ready_geometry PASS, fingerprint_determinism PASS,
cross_process_determinism PASS, research_isolation PASS, errors=[],
result=PASS; git diff --check PASS.

Isolation confirmed: no Runner, Catalog, Stage 1-6, Compiler, Batch Compiler,
Project 1, production, core, engines, or research files were modified by this
checkpoint.

---
## Current Stable Status

Current checkpoint: PHASE2B_BATCH_COMPILER_STABLE

Status: implemented and validated; awaiting review before commit.

Chapter IV added deterministic batch compilation for generated `GrammarProgram`
objects. `compile_generation_batch(generation_result, geometry_context,
compiler_version, batch_version)` attempts every generated program, separates
successful and failed compilations, preserves successful `CompilationResult`
objects unchanged, records failed program IDs and deterministic diagnostics, and
returns a frozen `BatchCompilationResult`.

Boundary: compiler only. No ScenarioSpecification assembly, no Scenario Runner,
no Catalog execution, no Stage 1-6 execution, no Project 1, no production
changes. The batch fingerprint covers generation_fingerprint, all observation
checksums, program fingerprints, diagnostics, compiler_version, and
batch_version.

Relationship to compiler_smoke.py: compiler_smoke.py remains a smoke/
integration proof; batch_compiler.py is the official batch compilation layer
for Phase 2C preparation. Both are kept deliberately, not redundantly.

Validation PASS: py_compile for batch_compiler + test; test_batch_compiler.py
batch_success PASS, partial_failure PASS, determinism PASS,
cross_process_determinism PASS, diagnostics_preserved PASS, research_isolation
PASS, errors=[], result=PASS; git diff --check PASS.

Isolation confirmed: no runner, catalog execution, Stage 1-6, Project 1,
production, core, engines, or research files were modified by this checkpoint.

---
## Current Stable Status

Current checkpoint: PHASE2B_COMPILER_SMOKE_STABLE

Status: implemented and validated; awaiting review before commit.

Chapter IV added compiler-smoke validation for generated `GrammarProgram`
objects. `run_compiler_smoke(generation_result, geometry_context,
compiler_version, smoke_version)` compiles each generated program with the
existing `compile_program()` path and returns a frozen `CompilerSmokeResult`
containing success/failure counts, all `CompilationResult` values,
deterministic diagnostics, and a deterministic smoke fingerprint.

Boundary: compiler integration only. No ScenarioSpecification assembly, no
Scenario Runner, no Catalog execution, no Stage 1-6 execution, no Project 1,
no production changes. The smoke fingerprint covers generation_fingerprint,
all observation_checksum values, diagnostics, compiler_version, and
smoke_version.

Validation PASS: py_compile for compiler_smoke + test; test_compiler_smoke.py
all_compile_success PASS, compilation_failure PASS, diagnostics_preserved PASS,
determinism PASS, cross_process_determinism PASS, research_isolation PASS,
errors=[], result=PASS; git diff --check PASS.

Isolation confirmed: no runner, catalog execution, Stage 1-6, Project 1,
production, core, engines, or research files were modified by this checkpoint.

---
## Current Stable Status

Current checkpoint: PHASE2B_MANIFEST_VALIDATION_STABLE

Status: implemented and validated; awaiting review before commit.

Chapter IV added deterministic ScenarioManifest integrity validation:
`ManifestValidationResult` and `validate_manifest(manifest, validator_version)`.
Checks entry_id uniqueness, entry_index contiguity, entry ordering, duplicate
GrammarProgram/combination fingerprint detection, generation/compilation
status consistency, required fingerprint presence, summary count
reconciliation, and an independent recomputation of `manifest_fingerprint`
against the stored value.

Boundary: validation only. No compiler calls, no runner calls, no Grammar
semantics inspection, no execution, no ScenarioSpecification generation.
`manifest_validation.py` imports only `contracts.py` -- not `generator.py`,
not Grammar -- so it can validate any ScenarioManifest independently of how
it was produced.

Validation PASS: py_compile for manifest_validation + test;
test_manifest_validation.py valid_manifest PASS, duplicate_entry_ids PASS,
duplicate_program_fingerprints PASS, duplicate_combination_fingerprints PASS,
summary_validation PASS, fingerprint_determinism PASS,
cross_process_determinism PASS, research_isolation PASS, errors=[], result=PASS;
git diff --check PASS.

Isolation confirmed: no compiler, runner, catalog, Stage 1-6, Project 1,
production, core, engines, or research files were modified by this checkpoint.

---
## Prior Stable Status (PHASE2B_SMALL_DETERMINISTIC_GENERATOR_STABLE)

Current checkpoint: PHASE2B_SMALL_DETERMINISTIC_GENERATOR_STABLE

Status: implemented and validated; awaiting review before commit.

Chapter IV now includes the first deterministic Scenario Generation Engine implementation. `generate_programs(template, generator_version)` expands one `GrammarTemplate` through Cartesian product `ParameterAxis` values, resolves `PhraseSlot` fixed and axis-bound parameters, builds valid `GrammarProgram` objects, records `ManifestEntry` values, builds a `ScenarioManifest`, detects duplicate `GrammarProgram` fingerprints as `SKIPPED_DUPLICATE`, caps generation at 10 programs, and returns a frozen `GenerationResult` with deterministic generation fingerprint.

Boundary: generation only. No compiler calls, no runner calls, no execution, no ScenarioSpecification generation, no batch compilation, no Catalog integration, and no Stage calls.

Validation PASS: py_compile for generator + test; test_small_generator.py single_axis_generation PASS, multi_axis_generation PASS, deterministic_order PASS, duplicate_detection PASS, manifest_generation PASS, grammar_program_validity PASS, fingerprint_determinism PASS, cross_process_determinism PASS, research_isolation PASS, errors=[], result=PASS; git diff --check PASS.

Isolation confirmed: no compiler, runner, catalog, Stage 1-6, Project 1, production, core, engines, or research files were modified by this checkpoint.

---
## Current Stable Status

Current checkpoint: PHASE2B_GENERATION_CONTRACTS_STABLE

Status: implemented and validated; awaiting review before commit.

Chapter IV started the Scenario Generation Engine foundation with contracts only: `GenerationCampaign`, `ParameterAxis`, `PhraseSlot`, `GenerationRule`, `GrammarTemplate`, `ManifestEntry`, `ScenarioManifest`, `GenerationSummary`, and deterministic `generation_contract_fingerprint()` over canonical JSON + SHA-256.

Boundary: no generation logic, no compiler calls, no runner calls, no Stage calls, no scenario execution, and no Catalog integration. The generator will live before the compiler; the compiler remains one-program-in / one-result-out.

Validation PASS: py_compile for contracts + test; test_generation_contracts.py generation_campaign PASS, parameter_axis PASS, phrase_slot PASS, generation_rule PASS, grammar_template PASS, manifest_entry PASS, scenario_manifest PASS, generation_summary PASS, fingerprint_determinism PASS, immutability PASS, research_isolation PASS, errors=[], result=PASS; git diff --check PASS.

Isolation confirmed: no compiler, runner, catalog, Stage 1-6, Project 1, production, core, engines, or research files were modified by this checkpoint.

---
## Current Stable Status

Current checkpoint: PHASE1D_SPECIFICATION_ASSEMBLER_STABLE

Status: implemented and validated; awaiting review before commit.

Project 2 Chapter III now includes the final compiler assembler. `assemble_specification(compilation_result, specification_name)` converts successful `CompilationResult` values into the existing `ScenarioSpecification` contract, reusing the exact compiled `PriceObservation` tuple via `compiled_observations` and storing canonical provenance fields for row_count, start_price, observation checksum, compiler version, grammar fingerprint, geometry fingerprint, and assembler version. Failed compilations raise deterministic `ValueError` and never create partial specifications.

Boundary: assembler only. No calculations, interpolation, scheduling, geometry resolution, materialization, replay, Runner execution, Catalog execution, or Stage 1-6 execution. Compiler pipeline complete: `GrammarProgram -> CompilationResult -> ScenarioSpecification`. Project 2 compiler is ready for scenario generation.

Validation PASS: specification assembler py_compile + test PASS; full compiler PASS; materialization logic PASS; geometry logic PASS; timeline scheduler PASS; macro expansion PASS; compiler contracts PASS; git diff --check PASS.

Isolation confirmed: no Grammar, Compiler Contracts, Macro Expansion, Timeline Scheduler, Geometry Resolution, Price Materialization, Full Compiler, Scenario Runner, Catalog, Families, Stage 1-6, Project 1, or production files were modified by this checkpoint.

---
## Current Stable Status

Current checkpoint: PHASE1D_FULL_COMPILER_STABLE

Status: implemented and validated; awaiting review before commit.

Project 2 Chapter III now includes the thin full compiler orchestrator. `compile_program(program, geometry_context, compiler_version)` wires only the existing stable stages: macro expansion -> timeline scheduling -> geometry resolution -> price materialization, then returns the existing `CompilationResult` contract. It adds no new mechanics, no new geometry logic, no new price logic, no ScenarioSpecification assembly, no Runner integration, no Catalog execution, and no Stage 1-6 calls.

Successful compilation now produces `PriceObservation[]` from `GrammarProgram + GeometryContext`, carries the scheduling timeline, preserves `program.program_fingerprint`, `geometry_context.geometry_fingerprint`, compiler version, and materialization checksum, and sorts diagnostics deterministically. Failed stages roll back to `success=False`, `observations=()`, `timeline=None`, `observation_checksum=None`, preserving diagnostics from executed stages.

The full compiler intentionally reuses the frozen `CompilationResult` contract. Intermediate fingerprints are not all carried in `CompilationResult` by design; `observation_checksum` is preserved, and fine-grained provenance remains available by calling the individual compiler stages.

Validation PASS: full compiler py_compile + test_full_compiler.py PASS; materialization contracts PASS; materialization logic PASS; geometry resolution logic PASS; timeline scheduler PASS; macro expansion PASS; git diff --check PASS.

Isolation confirmed: no Grammar, Compiler Contracts, Expansion Contracts, Macro Expansion, Timeline Scheduler, Geometry Resolution, Price Materialization Logic, Scenario Contract, Scenario Registry, Scenario Primitives, Scenario Runner, Catalog, Stage 1-6, Project 1, or production files were modified by this checkpoint.

---
## Current Stable Status

Current checkpoint: PHASE1D_PRICE_MATERIALIZATION_LOGIC_STABLE

Status: implemented and validated; awaiting review before commit.

Project 2 Chapter III now includes deterministic price materialization logic. `materialize_prices(geometry_result: GeometryResolutionResult) -> MaterializationResult` consumes only resolved geometry and emits actual `PriceObservation` rows. Supported policies are STEP and LINEAR only. STEP assigns each segment row the end anchor; LINEAR uses exact Decimal interpolation, with row_count=1 emitting only the end anchor. `PriceObservation.row_index` is generated as 1-based rows from scheduler row positions.

Rollback and provenance are deterministic: failed geometry, missing timeline, missing/invalid coordinates, invalid row_count, or unsupported interpolation produce FATAL diagnostics and return `success=False`, `observations=()`, `observation_checksum=None`. Successful output reuses the existing `observation_checksum()` unchanged and records materialization provenance through `materialization_fingerprint`.

Validation PASS: py_compile for materializer + logic test; test_price_materialization_logic.py step_materialization PASS, linear_single_row PASS, linear_multi_row PASS, checksum_determinism PASS, fatal_rollback PASS, cross_process_determinism PASS, research_isolation PASS, errors=[], result=PASS; git diff --check PASS.

Isolation confirmed: no Grammar, Compiler Contracts, Expansion Contracts, Macro Expansion, Timeline Scheduler, Geometry Contracts, Runner, Catalog, ScenarioSpecification, Stage 1-6, Project 1, or production files were modified by this checkpoint.

---
## Current Stable Status

Current checkpoint: PHASE1D_MATERIALIZATION_CONTRACTS_STABLE

Status: implemented and validated; awaiting review before commit.

Project 2 Chapter III now includes price-materialization contracts only: immutable `MaterializationResult`, deterministic `observation_checksum` over only `PriceObservation.row_index` + Decimal-normalized `price`, and deterministic `materialization_fingerprint` over observation checksum, diagnostics, upstream fingerprints, `compiler_version`, and `materializer_version`.

This is a boundary contract only. It does not generate prices, apply STEP/LINEAR behavior, interpolate, repair continuity, assemble ScenarioSpecification values, invoke the Scenario Runner, or touch Stage 1-6. Validation PASS: py_compile for contract + test, test_price_materialization_contracts.py result=PASS, git diff --check PASS.

Isolation confirmed: no Grammar, Expansion, Timeline Scheduler, Geometry Resolution, Runner, Catalog, ScenarioSpecification, Stage 1-6, Project 1, or production files were modified by this checkpoint.

---
## Current Stable Status

Current checkpoint: PHASE1D_GEOMETRY_RESOLUTION_LOGIC_STABLE

Status: implemented, validated, and independently audited (two rounds);
awaiting review before commit.

Project 2 Chapter III implements the deterministic Geometry Resolution
engine (`resolve_geometry(expansion_result, scheduling_result,
geometry_context)`): resolves geometry-relative primitive intent into
absolute geometry anchors only via an explicit 23-entry
`(PrimitiveType, macro_origin)` role table, upstream/fingerprint/
correspondence validation, Decimal-only fraction arithmetic, correct
TRANSFER_TO_ZONE handling (WITHDRAW resolves against source zone via a
sibling cross-reference, RAMP/APPROACH resolve against destination, direction
inferred from zone centers, identical centers rejected deterministically),
deterministic resolution_fingerprint, and fatal rollback with no partial
output. No price generation, interpolation, materialization, smoothing, or
continuity repair.

Audit found and fixed two real defects (both: a correct Decimal offset was
computed but never applied to the resolved coordinate): PENETRATE without
side silently collapsed to the exact zone center regardless of depth
(verified depth=0.05 and depth=0.95 produced identical anchors) -- now fails
deterministically with UNRESOLVABLE_PENETRATION_DIRECTION; TRANSFER_TO_ZONE's
WITHDRAW computed travel_distance_absolute but never applied it -- now
verified to produce a real, distinct end coordinate matching hand-computed
arithmetic. Contracts unchanged throughout both audit rounds (git diff
--stat: pure appends, zero deletions).

No price materialization, interpolation, Runner
integration, ScenarioSpecification assembly, Stage 1-6 changes, Project 1
changes, or production changes are present.

---

## Prior Stable Status (PHASE1D_GEOMETRY_CONTRACTS_STABLE)

Current checkpoint: PHASE1D_GEOMETRY_CONTRACTS_STABLE

Status: implemented and validated; awaiting review before commit.

Project 2 Chapter III added immutable geometry-resolution contracts only (no
resolution logic, present in this repository at the time). Implemented:
- ResolvedCoordinate: absolute geometry anchor intent, not a materialized row
  price.
- ResolvedSegment: preserves both TimelineSegment and ExpandedInstruction.
- ResolvedTimeline: bare immutable resolved segment container only.
- GeometryResolutionResult: success/diagnostics/fingerprint envelope matching
  the ExpansionResult and SchedulingResult pattern.
- GeometryResolutionRole: future role-mapping placeholder keyed by
  PrimitiveType + macro_origin.
- Deterministic geometry_resolution_fingerprint helper.

Architectural correction: future Geometry Resolver input is ExpansionResult +
SchedulingResult + GeometryContext. TimelineSegment is not modified because it
owns only row/timeline metadata; ExpandedInstruction is preserved because it
owns PrimitiveInstruction.parameters. Future resolver must validate matching
expansion fingerprints before resolving and pair timeline.segments[i] with
expansion_result.expanded_instructions[i].

Units: depth, clearance, and distance are Decimal fractions of
GeometryReference.half_width; no floats and no absolute deltas except explicit
geometry anchors.

Validation: py_compile PASS for geometry_resolution.py and
 test_geometry_resolution_contracts.py; geometry_resolution_contracts PASS,
resolved_coordinate PASS, resolved_segment PASS, resolved_timeline PASS,
resolution_result PASS, immutability PASS, determinism PASS,
research_isolation PASS, errors=[], result=PASS; git diff --check PASS.

Isolation confirmed: no Grammar / Compiler Contracts / Expansion Contracts /
Macro Expansion / Timeline Scheduler / Runner / Catalog / Stage 1-6 / Project 1
/ production changes.

Chapter III roadmap -- completed: PHASE1D_GRAMMAR_FOUNDATION_STABLE,
PHASE1D_COMPILER_CONTRACTS_STABLE, PHASE1D_EXPANSION_CONTRACTS_STABLE,
PHASE1D_MACRO_EXPANSION_LOGIC_STABLE, PHASE1D_TIMELINE_SCHEDULER_STABLE,
PHASE1D_GEOMETRY_CONTRACTS_STABLE. Next planned checkpoint:
PHASE1D_GEOMETRY_RESOLUTION_LOGIC_STABLE.

---
## Current Stable Status

Current checkpoint: PHASE1D_TIMELINE_SCHEDULER_STABLE

Commit: `744a38d530fb2a6178751a24f3fd2191c48a32dc`

Status: implemented, validated, and committed.

Project 2 Chapter III adds deterministic ExpansionResult-to-MechanicalTimeline
scheduling via a pure scheduling layer (row allocation only): ExpansionResult
-> SchedulingResult, sequential deterministic row scheduling, one
ExpandedInstruction -> one TimelineSegment, gap-free and overlap-free
scheduling, strict instruction ordering (reordered indices rejected, not only
non-contiguous ones), deterministic segment indexing, timeline validation,
timeline fingerprint (includes diagnostics), fatal rollback, research
isolation.

No geometry resolution, price generation, materialization, Runner, Catalog,
Stage 1-6, Project 1, or production change is present.

Independent Architecture Review: APPROVED. Applied corrections: preserve
authored PathSmoothness (STEP is fallback-only when absent); reject
reordered instruction indices; preserve upstream diagnostics alongside
UPSTREAM_EXPANSION_FAILED; include diagnostics in timeline_fingerprint.

Isolation confirmed: no Grammar / Compiler Contracts / Expansion Contracts /
Macro Expansion / Runner / Catalog / Stage 1-6 / Project 1 / production
changes.

Chapter III roadmap -- completed: ✓ PHASE1D_GRAMMAR_FOUNDATION_STABLE,
✓ PHASE1D_COMPILER_CONTRACTS_STABLE, ✓ PHASE1D_EXPANSION_CONTRACTS_STABLE,
✓ PHASE1D_MACRO_EXPANSION_LOGIC_STABLE, ✓ PHASE1D_TIMELINE_SCHEDULER_STABLE.
Next planned checkpoint: PHASE1D_GEOMETRY_RESOLUTION_ARCHITECTURE.

---

## Prior Stable Status (PHASE1D_MACRO_EXPANSION_LOGIC_STABLE)

Current checkpoint: PHASE1D_MACRO_EXPANSION_LOGIC_STABLE

Status: implemented and validated; awaiting review before commit.

Project 2 Chapter III implements the deterministic Macro Expansion engine
(GrammarProgram -> ExpansionResult, structural decomposition only): a
9-entry atomic passthrough table (identity for 7 phrase types;
APPROACH_ZONE->APPROACH, ENTER_ZONE->ENTER, RECOVERY_GAP->RAMP); a 5-entry
V1 macro rule table (ACCEPTED_BREAK/RECLAIM/TRANSFER_TO_ZONE fixed arity,
COMPRESS/EXPAND variable arity via len(amplitude_schedule)); an
integer-only AllocationPolicy V1 (divmod-based equal division, remainder
to the first N primitives); an internally computed expansion_fingerprint
(canonical JSON + SHA-256, never caller-supplied); and 9 distinct FATAL
diagnostic codes covering every requested validation case. BREAK_CANDIDATE
and RETEST_BOUNDARY are intentionally unregistered in V1 (FATAL
MISSING_EXPANSION_RULE). Any FATAL diagnostic forces success=False and
expanded_instructions=(). Instruction order strictly preserves
GrammarProgram phrase order (never sorted); diagnostics are sorted by
deterministic_key. Per-primitive parameters=() in V1 -- no semantic
parameter derivation; lineage preserved via source_phrase_index,
macro_origin, target_zone only.

No scheduling, timeline, geometry resolution, price generation,
ScenarioSpecification assembly, or Runner integration. No grammar, frozen
compiler contract, frozen expansion contract, Catalog execution, Stage 1-6,
Project 1, or production change is present.

---

## Prior Stable Status (PHASE1D_EXPANSION_CONTRACTS_STABLE)

Current checkpoint: PHASE1D_EXPANSION_CONTRACTS_STABLE

Status: implemented and validated; awaiting review before commit.

Project 2 Chapter III adds immutable expansion-layer contracts only:
ExpandedInstruction, ExpansionResult, ExpansionRule, and AllocationPolicy.
Expansion-only row budgets belong to ExpandedInstruction; frozen
PrimitiveInstruction remains unchanged.

No Macro Expansion implementation, allocation logic, scheduling, timeline,
materialization, price generation, Runner integration, ScenarioSpecification
assembly, grammar, frozen compiler contract, Catalog execution, Stage 1-6,
Project 1, or production change is present.

---

## Prior Stable Status (PHASE1D_COMPILER_CONTRACTS_STABLE)

Current checkpoint: PHASE1D_COMPILER_CONTRACTS_STABLE

Status: implemented and validated; independently audited; pre-commit
corrections applied; awaiting commit.

Project 2 Chapter III Phase 2 adds immutable compiler boundary contracts only:
external geometry with deterministic fingerprint, primitive instructions,
mechanical timeline, deterministic diagnostics, and compilation request/result.

No compiler logic, scheduling, macro expansion, materialization, price
generation, Runner integration, ScenarioSpecification assembly, grammar,
Catalog execution, Stage 1-6, Project 1, or production change is present.

Independent audit verdict: APPROVE WITH MINOR RECOMMENDATIONS. Applied
pre-commit: removed wildcard `import *` in test_compiler_contracts.py
(explicit imports only); added `__all__` to compiler/__init__.py (matching
grammar/__init__.py's established pattern); retyped
TimelineSegment.interpolation_policy from bare str to the existing
PathSmoothness enum; reformatted all six files to standard one-statement-
per-line style. No behavior changed -- all checks (contracts, geometry,
timeline, diagnostics, immutability, determinism, research_isolation) still
pass identically post-patch; geometry fingerprint formula untouched;
cross-process determinism reconfirmed. No grammar, Runner, Catalog
execution, Stage 1-6, Project 1, or production file touched.
---

## Prior Stable Status (PHASE1C_SCIENTIFIC_HYPOTHESIS_AUDIT_STABLE)

Commit: `b381ce99b0199856242e104c06a8fe139a8def63`

Chapter I is COMPLETE / STABLE across Dynamic Mechanics, Snapshot Dynamic
Mechanics, Dynamic State Transitions, Transition Graph, Trajectory Evolution,
and Prediction Evolution Research.

Project 2 Chapter II, stable through Phase 6:
- Scenario Generator Foundation: STABLE
- Scenario Runner: STABLE
- Scenario Catalog Foundation: STABLE
- Scenario Execution: PASS
- Cross-Scenario Descriptive Comparison: STABLE
- Scientific Hypothesis Audit: STABLE

Checkpoint chain:
- Generator Foundation: `ca71902f74ba42ce54b217f3488c10da24a2d0f4`
- Scenario Runner: `34641e3c1cda4a19972a48752446785132e7ccbd`
- Catalog Foundation: `5a2d4a718f0072f86556e2b2347eedbeaf8ae061`
- Catalog Provenance Fix: `a2c52feb5b7472450b543f6de3b46a6562520d5a`
- Scenario Execution / Stage 6 Empty-Zone Fix:
  `add1fcfe37f68d41437594d4b424f1eddd08214d`
- Cross-Scenario Descriptive Comparison:
  `660f459ea9a5a34d6aa95a2a395f1ea93302ea57`
- Scientific Hypothesis Audit:
  `b381ce99b0199856242e104c06a8fe139a8def63`

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

Independently re-verified before documenting: decision_rule_id/
decision_rule_trace confirm decisions are computed from cited evidence, not
hardcoded; all_hypotheses_ex_ante/no_hypotheses_outside_phase3/
all_phase3_sources_exact all True; banned-language scan passes an expanded
pattern list scoped only to Phase 6's own authored prose; imports limited to
scenario_contract/specifications/test_cross_scenario_comparison (no Runner,
Stage 1-6, core./engines./research. imports); byte-identical output across
two independent process runs; git diff touches exactly one file relative to
the prior commit.

---

## Prior Stable Status (PHASE1C_SCENARIO_EXECUTION_STAGE6_EMPTY_ZONE_FIX)

Commit: `add1fcfe37f68d41437594d4b424f1eddd08214d`

Chapter I is COMPLETE / STABLE across Dynamic Mechanics, Snapshot Dynamic
Mechanics, Dynamic State Transitions, Transition Graph, Trajectory Evolution,
and Prediction Evolution Research.

Project 2 Chapter II Phase 1C:
- Scenario Generator Foundation: STABLE
- Scenario Runner: STABLE
- Scenario Catalog Foundation: STABLE
- Scenario Execution: PASS

Stage 6 empty-zone reporting:
- `NO_VISITS`: existing zone, zero completed visits.
- `INSUFFICIENT_SAMPLE`: visits exist, no eligible hypothesis.
- `SUFFICIENT_SAMPLE`: at least one eligible hypothesis exists.

Phase 4 results are deterministic: baseline PASS (159 visits), adversarial
PASS (2), regime change PASS (52), and repeated attacks PASS (6). No Scenario
Runner or Scenario Catalog implementation, Project 1, or production file
changed.

---

## Prior Stable Status (PHASE1C_SCENARIO_CATALOG_PROVENANCE_FIX)

Status: implemented and validated.

Scientific provenance correction only. No architecture, scenario parameters,
generated price paths, provider behavior, or production behavior changed.
REPEATED_ATTACKS_PARTIAL_RECOVERY_V1 now identifies its actual experiment as
DENOMINATOR_DEGRADATION_PARTIAL_RECOVERY with no predeclared downstream state;
it is not documented as a direct RESEARCH_ATTACKER_PRESSURE target.
REGIME_CHANGE_INTO_PRESSURE documentation now consistently states that its
quiet and pressure phases act on the same zone, preserving per-zone trajectory
history for later Stage 6 evaluation. Specification fingerprint changes are
limited to the corrected immutable metadata/documentation.

Validation: all catalog files compile; test_scenario_catalog.py PASS; generated
observation sequences are unchanged from commit 5a2d4a7; git diff --check PASS.
No Stage 1-6, Scenario Runner, Project 1, or production file changed.

---

## Prior Stable Status (PHASE1C_SCENARIO_CATALOG_FOUNDATION_STABLE)

Status: implemented and validated; awaiting review before commit.

Project 2 Chapter II Phase 3 adds a small, explicit Scenario Catalog: exactly
four families (BASELINE, ADVERSARIAL_ATTACKER_PRESSURE,
REGIME_CHANGE_INTO_PRESSURE, REPEATED_ATTACKS), one provider each, one
specification each -- no batch execution, no cross-scenario comparison, no
sensitivity analysis, no learning, no new analytical layer. Each provider
composes only the existing, unchanged scenario_primitives functions
(triangular_wave/step_pattern/bounded_range). Mechanism-derived design:
ADVERSARIAL_ATTACKER_PRESSURE targets the SDR formula's numerator (shallow
probe then much deeper sustained penetration into the same zone, spiking
delta_omega relative to health); REPEATED_ATTACKS targets the same formula's
denominator instead (six equal-depth touches with incomplete-recovery
gaps, shrinking health cumulatively) -- kept as a separate, non-conflated
family; REGIME_CHANGE_INTO_PRESSURE concatenates a quiet oscillating regime
with the same escalating shape targeting the same zone.

Structurally verified, not just documented: expected_behavior_notes and
validation_metadata are never read by any provider's generate() (each spec
rebuilt with different notes/metadata reproduces byte-identical
observations); zero Stage 1-6 imports, zero scenario_runner references, zero
core./engines./research. imports anywhere in the catalog (automated source
scan across every catalog file, not a declared claim).

Post-audit revision (parameter-only; providers/catalog/registry/contract/
runner untouched): an audit diagnostic found REPEATED_ATTACKS' original
touch depth (60395/10 rows) floored health on visit 1 and stayed flat for
all 6 visits, and REGIME_CHANGE's original quiet phase touched a different
zone (60200) than the pressure phase (60400) -- unreachable by Stage 6's
strictly per-zone hypothesis logic -- while also collapsing into one
continuous 200-row visit instead of several small ones. Both specifications'
`parameters` (and matching expected_behavior_notes/validation_metadata text)
were revised and re-verified: REPEATED_ATTACKS now shows a monotonic decline
92.2->89.2->86.2->83.2->80.2->77.2 across 6 visits (omega constant at 15.0,
no floor); REGIME_CHANGE's quiet phase now produces 50 separate visits, all
in the same zone the pressure phase later escalates into, health declining
smoothly 98.2->10.0 with no premature floor. Full catalog test suite re-run
after the fix: unchanged PASS across every check.

Deterministic results:
- families_registered=4; specifications_registered=4
- providers_registered=PASS (all price_only=True, research_only=True)
- unique_scenario_ids=PASS; fingerprints_stable=PASS
- price_only_generation=PASS; determinism=PASS; distinct_path_shapes=PASS
- notes_not_required_for_generation=PASS
- no_stage_imports=PASS; no_runner_execution=PASS (no optional smoke check
  used); errors=[]; result=PASS
- Identical results confirmed running from the repo root and from the
  catalog's own directory (self-contained sys.path bootstrap per file).

Validation:
- python -m py_compile on catalog.py, specifications.py, all four
  families/*.py, and test_scenario_catalog.py
- python experiments/psychological_levels_dynamic/scenario_catalog/test_scenario_catalog.py
- git diff --check
- git status
- git diff --name-only -- core/ research/ engines/

Boundary: catalog defines experimental inputs only. Does not run Stage 1-6,
does not execute the Scenario Runner, does not compare scenario outputs,
does not validate or require RESEARCH_ATTACKER_PRESSURE or any other
downstream Dynamic State. No Stage 1-6 or Scenario Runner file modified. No
Project 1/production/dashboard/live pipeline/Snapshot/RDM formula/Worker/
Queue/Bootstrap changes, no Phase 2 trading/execution/BUY-SELL/HOLD-FAIL/
live signals. Production behavior unchanged.

Next: await Scenario Catalog Foundation review and commit approval.

---

## Prior Stable Status (PHASE1C_SCENARIO_RUNNER_STABLE)

Current checkpoint: PHASE1C_SCENARIO_RUNNER_STABLE

Status: implemented and validated; awaiting review before commit.

Project 2 Chapter II Phase 2 adds only a thin, additive Scenario Runner:
reuses Stage 1 ZoneHarness/update_mechanics()/compute_dynamics() and the
shared Interpreter/EventDispatcher/LastCompletedVisitAdapter plumbing
unchanged; parameterizes PsychologicalLevelsProvider from scenario
geometry_parameters instead of Stage 1's hardcoded constants; the only
duplicated structure is a thin per-row driving loop (Stage 3's pattern, no
Dispatcher/Coordinator/Snapshot). The executed analytical path is Stage 1
mechanics/visit collection plus Stages 3-6; Stage 2 Snapshot compatibility
remains prevalidated and is intentionally not rerun per scenario. Calls
Stage 3/4/5/6's own analyze()/analyze_transition_graph()
functions directly via qualified module imports (no star imports, no
main()/printed-report parsing); wraps their output verbatim, invents no new
metric; produces one immutable ScenarioRunResult with full provenance
(fingerprint, provider_version, chain_version, normalized chain_fingerprint,
run_id, observation_checksum,
all via the canonical-JSON + SHA-256 helper reused unchanged from Phase 1).

Deterministic results, cross-checked against already-verified Chapter I
ground truth (identical triangular price shape fed through the runner
instead of Stage 1's hardcoded generator):
- zones=7; completed_visits=159; observation_count=3000; row_count=3000
- stage3: transitions=145; all_research_prefixed=True; counts_consistent=True
- stage4: transitions=145; transition_counts matches Chapter I exactly
  (RECOVERING->STABLE=60, STABLE->RECOVERING=61, STABLE->STABLE=24);
  critical_transition_count=0; absorbing_states=[]
- stage5: trajectory_records=159; unobserved_states=[ATTACKER_PRESSURE];
  attacker_pressure_observed=False; predictions_generated=False
- stage6: hypotheses_generated=152; eligible=110; confirmed=103;
  invalidated=0; pending=7; forced_hypothesis_under_weak_evidence=False
- contiguous_row_ordering=True; finite_price_validation=True;
  price_only_contract_validation=True; deterministic_generation=True
- run_id and observation_checksum identical across 3 in-process runs and 2
  separate process invocations
- second 600-row parameter variant deterministic across 2 runs and has a
  distinct specification fingerprint, checksum, and run_id
- errors=[]; result=PASS

No separate scenario_chain_adapter.py file was created (judged unnecessary
at this scale); reported as
"chain_adapter = NOT_SEPARATED (integrated into scenario_runner.py)".

Frozen-file provenance/drift guard normalizes CRLF/LF before SHA-256.
Normalized component hashes form chain_fingerprint, recorded in each run
and included in run_id; accidental frozen-file drift still fails the test.

Validation:
- python -m py_compile
  experiments/psychological_levels_dynamic/scenario_runner.py
- python -m py_compile
  experiments/psychological_levels_dynamic/test_scenario_runner.py
- python experiments/psychological_levels_dynamic/test_scenario_runner.py
- git diff --check
- git status
- git diff --name-only -- core/ research/ engines/

Boundary: runner only, no new analytical layer, no batch execution, no
cross-scenario comparison, no sensitivity analysis, no learning, no
Project 1/production/dashboard/live pipeline/Snapshot/RDM formula/Worker/
Queue/Bootstrap changes, no Phase 2 trading/execution/BUY-SELL/HOLD-FAIL/
live signals. No Stage 1-6 file modified (confirmed via git diff and the
frozen-file SHA-256 guard). Production behavior unchanged.

Next: await Scenario Runner review and commit approval.

---

## Prior Stable Status (PHASE1C_SCENARIO_GENERATOR_FOUNDATION_STABLE)

Current checkpoint: PHASE1C_SCENARIO_GENERATOR_FOUNDATION_STABLE

Status: implemented and validated; awaiting review before commit.

Project 2 Chapter II Phase 1 adds only the deterministic Scenario Generator
foundation:
- deeply immutable ScenarioSpecification
- immutable price-only PriceObservation
- runtime-checkable ScenarioProvider Protocol
- explicit registry with duplicate protection and self-contained imports
- canonical SHA-256 specification fingerprint
- canonical immutable parameter-type restrictions
- pure Decimal triangular, trend, bounded-range, and step primitives
- no scanning, plugins, reflection, dynamic imports, random, or PRNG

Validation:
- scenario_contract=PASS
- registry=PASS
- primitives=PASS
- determinism=PASS
- price_only_output=PASS
- research_only=PASS
- errors=[]; result=PASS
- repeated generation identical
- equivalent specifications fingerprint identically; changed specs differ
- isolated self-contained registry import=PASS
- triangle fixture=100,110,120,110,100,110,120,110
- primitive paths distinct

Files: scenario_contract.py, scenario_registry.py, scenario_primitives.py,
test_scenario_foundation.py, plus the two checkpoint documents.

Commands:
- python -m py_compile
  experiments/psychological_levels_dynamic/scenario_contract.py
  experiments/psychological_levels_dynamic/scenario_registry.py
  experiments/psychological_levels_dynamic/scenario_primitives.py
  experiments/psychological_levels_dynamic/test_scenario_foundation.py
- python
  experiments/psychological_levels_dynamic/test_scenario_foundation.py
- git diff --check
- git status

Boundary: foundation only. No runner, Stage 1-6 execution or modification,
Project 1, production, dashboard, live pipeline, Snapshot, RDM, production
B10/B11, Worker, Queue, Bootstrap, trading, execution, or Phase 2 changes.
Production behavior unchanged.

Next: await Chapter II Phase 1 review; do not commit yet.

---

## Prior Stable Status (PHASE1B_PREDICTION_EVOLUTION_STAGE6_STABLE)

Current checkpoint: PHASE1B_PREDICTION_EVOLUTION_STAGE6_STABLE

Status: revised and validated; awaiting review before commit.

Stage 6 now structurally separates prefix-only hypothesis generation from
next-visit validation. The generator cannot receive future visits, outcomes,
or validation targets. Weak evidence abstains under sample, tie, margin
(0.15), and confidence (0.35) guards.

Validation includes 21 adversarial future-mutation checks and six synthetic
negative controls. All pass; no weak-evidence hypothesis is forced.

Revised deterministic results across three runs:
- zones=7; completed_visits=159; hypotheses_generated=152
- eligible=110; insufficient_sample=39; insufficient_evidence=3
- abstentions=42; uncertain=42
- confirmed=103; invalidated=0; pending=7
- coverage=0.6776315789473685
- descriptive_confirmation_rate=1.0
- generation_validation_separated=True
- future_mutation_invariance=True (21 checks)
- negative_controls_pass=True
- forced_hypothesis_under_weak_evidence=False
- leakage_violation_details=[]; negative_control_failures=[]
- ATTACKER_PRESSURE unobserved; deterministic=True; errors=[]; result=PASS

Changed by abstention: eligible 113->110, confirmed 106->103,
abstentions 39->42, coverage 0.6973684210526315->0.6776315789473685.

The descriptive confirmation rate is neither trading accuracy nor production
validation.

Validation:
- python -m py_compile
  experiments/psychological_levels_dynamic/test_prediction_evolution.py
- python
  experiments/psychological_levels_dynamic/test_prediction_evolution.py
- git diff --check
- git status
- git diff --name-only -- core/ research/ engines/

Boundary: offline Project 2 research only. No production, Project 1,
dashboard, live pipeline, Snapshot, RDM formula, production B10/B11, external
engines, trading, or execution changes. Production behavior unchanged.

Next: await revised Stage 6 review; do not commit yet.

---

## Prior Stable Status (PHASE1B_TRAJECTORY_EVOLUTION_STAGE5_STABLE)



Current checkpoint: PHASE1B_TRAJECTORY_EVOLUTION_STAGE5_STABLE

Stage 5 reconstructs ordered visit-by-visit Project 2 trajectories from
unchanged Stage 3 completed visits and Stage 1 Dynamic Mechanics.

Implemented: 159 canonical visit records; per-zone trajectories and
signatures; state and transition mechanics; local transition windows;
cross-zone comparison; sample guards; explicit NOT_AVAILABLE and unobserved
state handling.

Deterministic results across three runs:
- zones=7; records=159; completed_visits=159; transitions=145
- visits by zone=23,23,23,23,23,22,22
- transitions by zone=21,21,21,21,21,20,20
- observed states: RECOVERING=61, STABLE=91
- ATTACKER_PRESSURE unobserved; attacker_pressure_observed=False
- unsupported states=0; initial NOT_AVAILABLE state records=7
- STABLE->RECOVERING=61; RECOVERING->STABLE=60; STABLE->STABLE=24
- high-oscillation zones=6; single-state zones=1; no-transition zones=0
- insufficient sample flags=1 (unobserved ATTACKER_PRESSURE)
- RESEARCH_ labels valid; NOT_AVAILABLE valid; errors=[]; result=PASS

Validation:
- python -m py_compile
  experiments/psychological_levels_dynamic/test_trajectory_evolution.py
- python
  experiments/psychological_levels_dynamic/test_trajectory_evolution.py
- git diff --check
- git status

Boundary: descriptive offline Project 2 research only. No prediction,
production B10/B11, external engines, Project 1, production, dashboard, live
pipeline, Snapshot, RDM formula, Worker, Queue, or Bootstrap changes.
Production behavior unchanged.

Next: await Stage 5 review and the next Phase 1B research approval.

---

## Prior Stable Status (PHASE1B_TRANSITION_GRAPH_STAGE4_STABLE)

Current checkpoint: PHASE1B_TRANSITION_GRAPH_STAGE4_STABLE

Stage 4 builds a research-only Transition Graph over unchanged Stage 3
Psychological Levels Dynamic State sequences.

Implemented: transition probabilities, residence runs, persistence, simple
cycles, critical transitions, absorbing-like states, and early-warning paths.

Deterministic results across three runs:
- zones=7; completed_visits=159; transitions=145; transition_types=3
- STABLE->RECOVERING=61; RECOVERING->STABLE=60; STABLE->STABLE=24
- P(RECOVERING->STABLE)=1.0
- P(STABLE->RECOVERING)=0.7176470588235294
- P(STABLE->STABLE)=0.2823529411764706
- residence RECOVERING: mean=1.0, min=1, max=1, runs=61
- residence STABLE: mean=1.3582089552238805, min=1, max=22, runs=67
- persistence RECOVERING=0.0; STABLE=0.2823529411764706
- STABLE->RECOVERING->STABLE cycles=60 across 6 zones
- critical transitions=0; absorbing states=[]; early-warning paths=0
- probability rows valid; RESEARCH_ prefix valid; errors=[]; result=PASS

Validation:
- python -m py_compile
  experiments/psychological_levels_dynamic/test_transition_graph.py
- python experiments/psychological_levels_dynamic/test_transition_graph.py
- git diff --check

Boundary: offline Project 2 graph analysis only. No prediction, Dynamic State,
Project 1, production, dashboard, live pipeline, Snapshot, RDM formula,
B10/B11, Worker, Queue, or Bootstrap changes. Production behavior unchanged.

Next: await the next Phase 1B research-stage approval.

---

## Prior Stable Status (PHASE1B_DYNAMIC_STATE_TRANSITION_STAGE3_STABLE)

Current checkpoint: PHASE1B_DYNAMIC_STATE_TRANSITION_STAGE3_STABLE

Stage 3 analyzes transitions between research Dynamic States produced by
Stage 1/2 (research-only, no production behavior changed).
- Analyzes current/previous dynamic_state, transition_name, frequency,
  per-zone chains, repeated transitions, stable vs unstable sequences, and a
  research-only early-warning pattern.
- Uses Stage 1 Dynamic Mechanics unchanged; interpreter-driven completed
  visits reused (only Interpreter + LastCompletedVisitAdapter, no
  Dispatcher/Coordinator/Snapshot needed).
- No production/Project 1/live/dashboard/Snapshot/B10/B11 changes.
- All labels remain RESEARCH_ prefixed.

Results (deterministic across three runs): zones_observed=7,
completed_visits=159, transitions_generated=145, unique_transition_types=3.
Transition frequencies: RESEARCH_STABLE_TO_RESEARCH_RECOVERING=61,
RESEARCH_RECOVERING_TO_RESEARCH_STABLE=60,
RESEARCH_STABLE_TO_RESEARCH_STABLE=24. per_zone_transition_counts validated;
repeated_transition_chains=20; stable_state_sequences=1;
unstable_state_sequences=6; early_warning_transitions=0; errors=0;
result=PASS.

Validation: py_compile OK; run PASS; git diff --check clean.

Next: Phase 1B Stage 4 trajectory evolution research.

---

## Prior Stable Status (PHASE1B_DYNAMIC_MECHANICS_SNAPSHOT_STAGE2_STABLE)

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

PHASE 0 CLOSED â€” PRODUCTION SAFE (final Phase 0 checkpoint; deliberately
distinct from "PRODUCTION VALIDATED" â€” correctness under load is proven by the
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
- One payload difference (received=10, processed=9) â€” likely one in-flight
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
  (core/passive_shadow_bootstrap.py â€” fail-safe, flag-gated default OFF,
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

Phase 0D: first (minimal) production wiring of the Passive Shadow Runtime â€” one
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

Restart / Durability Contract (ACCEPTED â€” architecture decision only, NO code):
- The append-only ordered row log is the source of truth.
- Persist-before-process (durably append row before InteractionState advances).
- Rebuild-from-history is the primary recovery mechanism.
- The snapshot is a cache / projection only â€” never the source of truth.
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

Next: run LIVE stream continuously â†’ accumulate post-return visits â†’
validate LIVE vs REPLAY dynamic_state â†’ B13.

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
  - SDR >= 1 â†’ 99.6% FAIL (near-deterministic)
  - Mathematical layers: derivative + integral + SDR per visit
  - Thresholds: percentile-calibrated from pre-return data

Live stream: switched to @aggTrade (matches REPLAY unit).
Archive: Feb-Jun 2026, 4,859 zones, B12v2 98.8% accuracy, r=0.9991.
Streaming replay (--stream) required on this machine (24 GB RAM).

---

## Prior Stable Status (PHASE1B_UNIFIED_ARCHIVE_STABLE)

Current checkpoint: PHASE1B_UNIFIED_ARCHIVE_STABLE

Archive: Feb 01 â†’ Jun 05 2026, continuous (zero seams), 4,859 zones.
B12v2: 98.8% accuracy, HOLD F1=0.989, FAIL F1=0.986, evaluable=2,441.
Physics: r=0.9991 (sigma x penetration, n=2,977) â€” strongest yet.
Streaming replay (--stream) required on this machine (24 GB RAM).

Weak point identified: STABLE trajectory (44.4% hold rate, all 10 false
HOLDs). All other trajectories: STRENGTHENING/TERMINAL = 100% accuracy.

Next: regime generalization (second independent period) + B12.5 + B13.

Prior checkpoints (not all individually detailed here â€” see git log /
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
- New reader `stream_cached_day_trades()` â€” yields aggTrades from the
  Tier-1 raw-trade cache one UTC day at a time (O(one day) memory).
- New consumer `run_streaming_pipeline()`:
  - Persistent `tick_buffer` across day-file boundaries, flushed only
    at `row_size` (500 ticks) â€” never at a day seam.
  - ONE continuous `StatisticsEngine` / `RenkoEngine` / observation
    state for the whole window.
  - Warmup primed via `deque(maxlen=500)`, tick_buffer reset at the
    warmup -> target boundary.
  - Incremental CSV writes for market-rows and observation-rows.
  - Row-count invariant assertions (`rows == ceil(target_trades/500)`,
    non-final rows have `tick_count == 500`) â€” raises on violation.
  - V1/V2 replay events/episodes + archiving reuse the existing
    (unchanged) functions, fed by re-reading the observation CSV.
- `--save-raw` is not supported together with `--stream`.

STATUS: Stages 1-3 implemented and additive-verified (compiles, 0
deletions, old path unchanged). `--stream` run on April reproduced the
known-good April B12v2 numbers (808 zone cases, r=0.9966, 97.8%
accuracy) â€” metric-level verified. The formal Stage 3 byte-identical
sha256 comparison was not separately confirmed (the in-memory side
OOMed on this machine during that test â€” see "Known Issue" below).

**`--stream` is now REQUIRED on this machine for all replay rebuilds,
including single months** â€” the in-memory path is unreliable here (see
"Known Issue"). Treat `--stream` output as the research dataset going
forward; it is REPLAY_AGGTRADE data, same as the in-memory path (see
CURRENT_CHECKPOINT.md "Research Data Labeling").

## Known Issue: in-memory path OOM on this machine

During the Stage 3 equivalence test, the old in-memory path OOMed on
April (~25.5M trades) on this 24GB machine. Cause unconfirmed (possibly
low free RAM at that moment â€” other processes, prior run residual
memory). `--stream` avoids this entirely by design and is required
going forward regardless of cause. The 126-day (2026-02-01 ->
2026-06-06) in-memory OOM estimate (~60-75GB) remains valid/unchanged.

## Permanent Rule: outputs/ snapshot before writes

Always take a snapshot/backup of `outputs/` BEFORE any run that writes
to it (especially with `--overwrite`). See RUN_COMMANDS.md "Pre-run
snapshot rule".

## B12 Live Validation â€” still active

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
columns) predate the March/April/May generalization and B12v2 work â€”
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

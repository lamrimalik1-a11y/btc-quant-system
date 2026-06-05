# B12v2 — Penultimate-State Validation Architecture
**Date:** 2026-06-05  
**Status:** DESIGN ONLY — no coding, no formula changes, no implementation yet.

---

## 1. WHAT THIS DESIGN SOLVES

The current B12 evaluation is circular because B10 uses `final_visit_result` (visit N outcome) to assign trajectory, and B12 measures outcome from the same visit N result. The solution is to compute the entire prediction chain from visits 1..N-1, then evaluate against visit N.

This is an evaluation harness design. **No Phase 1 production code changes.**

---

## 2. CORE PRINCIPLE

```
Prediction = f(visits 1..N-1)
Outcome    = g(visit N)

I(t)     = {visit_1, visit_2, ..., visit_{N-1}}
O(t+1)   = {visit_N}
I(t) ∩ O(t+1) = empty set

No field used in Prediction may contain any data from visit N.
```

The prediction chain (Statistics → Preparation → Lifecycle → RDM → Synthesis) is fully preserved. It is executed on truncated input data, not modified.

---

## 3. DATA FLOW

```
┌─────────────────────────────────────────────────────────────────┐
│  READ-ONLY  (existing Phase 1 outputs — NEVER modified)         │
│                                                                  │
│  zone_visit_timeline.csv         (source of all visit rows)     │
│  zone_mechanics_cycle3_results.csv (zone RDM properties)        │
│  zone_vs_attacker_profile.csv    (B4/B7 force data)             │
│  historical_replay_dashboard_v2_episodes.csv  (statistical ctx) │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│  B12v2 HARNESS  (run_b12v2_validation.py)                      │
│                                                                 │
│  Step 1 — Split                                                 │
│    For each case_id with max(visit_index) >= 2:                 │
│      vt_prior = rows where visit_index < max(visit_index)       │
│      visit_N  = row  where visit_index == max(visit_index)      │
│                                                                 │
│  Step 2 — Recompute B9 on vt_prior                             │
│    build_zone_health_evolution(results_df, vt_prior, run_utc)  │
│    → he_prior_df                                                │
│                                                                 │
│  Step 3 — Recompute B10 on he_prior                            │
│    build_zone_structural_trajectory(results_df, he_prior_df,   │
│                                     run_utc)                    │
│    → traj_prior_df                                              │
│                                                                 │
│  Step 4 — Recompute B11 on traj_prior                          │
│    build_zone_structural_prediction(results_df, traj_prior_df, │
│                                     vs_attacker_df, run_utc)   │
│    → pred_prior_df                                              │
│                                                                 │
│  Step 5 — Recompute Synthesis on pred_prior                    │
│    build_zone_synthesis(results_df, traj_prior_df,             │
│                         pred_prior_df, episodes_df, run_utc)   │
│    → syn_prior_df                                              │
│                                                                 │
│  Step 6 — Classify outcome from visit_N.visit_result only      │
│    HOLD if visit_N.visit_result in                             │
│          {GROWTH, ABSORPTION, REFLECTION, RECLAIM}             │
│    FAIL if visit_N.visit_result == BREAKDOWN                   │
│    AMBIGUOUS if visit_N.visit_result == DAMAGE                 │
│                                                                 │
│  Step 7 — Evaluate: pred_prior_df vs visit_N outcomes          │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│  NEW OUTPUTS (never overwrite existing files)                 │
│                                                               │
│  b12v2_penultimate_predictions.csv                            │
│  b12v2_case_results.csv                                       │
│  b12v2_report.md                                              │
│  b12v2_report.csv                                             │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. HOW TO BUILD THE PENULTIMATE-STATE DATASET

### 4.1 Visit Split

Input: `zone_visit_timeline.csv`

For each `case_id`:
1. Compute `N = max(visit_index)` for that case
2. If `N < 2`: mark as `SINGLE_VISIT_EXCLUDED`; do not proceed
3. If `N >= 2`:
   - `vt_prior` = all rows where `visit_index < N`  (visits 1..N-1)
   - `outcome_row` = the single row where `visit_index == N` (visit N only)

The split is implemented in the harness. No modification to `zone_visit_timeline.csv`.

### 4.2 Constructing the truncated visit DataFrame

`vt_prior` retains all original columns of `zone_visit_timeline.csv`:
- `case_id`, `episode_id`, `zone_id`, `zone_mechanical_state`
- `visit_index`, `visit_start_time`, `visit_end_time`, `visit_duration_rows`
- `rigidity_at_visit`, `capacity_at_visit`, `fatigue_at_visit`, `recovery_at_visit`
- `sigma_at_visit`, `health_at_visit`, `penetration_at_visit`, `omega_at_visit`
- `attacker_force_at_visit`
- `visit_result`
- etc.

All values in `vt_prior` come from visits 1..N-1. **Visit N does not appear in `vt_prior`.**

### 4.3 Outcome classification

Outcome is derived from `outcome_row.visit_result` only:

| visit_N result | B12v2 outcome |
|---|---|
| GROWTH | HOLD |
| ABSORPTION | HOLD |
| REFLECTION | HOLD |
| RECLAIM | HOLD |
| BREAKDOWN | FAIL |
| DAMAGE | AMBIGUOUS (excluded from evaluable) |

No cumulative `breakdown_count` is used in the outcome definition.  
No `health_last_visit` threshold is used in the outcome definition.  
The outcome is determined entirely from the single visit N event.

---

## 5. RECOMPUTATION OF B9, B10, B11, SYNTHESIS

### 5.1 Functions to reuse (exact signatures)

All four functions accept DataFrames as parameters. The harness passes truncated data without modifying the function code.

```
B9:  build_zone_health_evolution(
         results_df,           ← zone_mechanics_cycle3_results.csv  [unchanged]
         visit_timeline_df,    ← vt_prior  [truncated, visits 1..N-1]
         run_utc
     ) → he_prior_df

B10: build_zone_structural_trajectory(
         results_df,           ← zone_mechanics_cycle3_results.csv  [unchanged]
         health_evolution_df,  ← he_prior_df  [B9 output from truncated data]
         run_utc
     ) → traj_prior_df

B11: build_zone_structural_prediction(
         results_df,           ← zone_mechanics_cycle3_results.csv  [unchanged]
         trajectory_df,        ← traj_prior_df  [B10 output from truncated data]
         vs_attacker_df,       ← zone_vs_attacker_profile.csv  [unchanged]
         run_utc
     ) → pred_prior_df

SYN: build_zone_synthesis(
         results_df,           ← zone_mechanics_cycle3_results.csv  [unchanged]
         trajectory_df,        ← traj_prior_df  [B10 from truncated data]
         prediction_df,        ← pred_prior_df  [B11 from truncated data]
         episodes_df,          ← historical_replay_dashboard_v2_episodes.csv  [unchanged]
         run_utc
     ) → syn_prior_df
```

### 5.2 No function modifications required

The existing B9/B10/B11/Synthesis functions operate correctly when given truncated input. The harness controls what data they receive. No `truncate_last_visit=True` parameter is needed.

This is the safest approach: zero changes to production code.

### 5.3 The `results_df` (zone_mechanics_cycle3_results.csv)

This file contains zone structural properties computed from the replay mechanics (sigma_barre, capacity, rigidity, fleche, omega_stress_area, etc.). These are derived from price action during the episode, NOT from visit outcome labels. They do not contain `visit_result` or `breakdown_count` from visit N.

**Safe to use unchanged in B12v2.** No leakage path through `results_df`.

### 5.4 The `vs_attacker_df` (zone_vs_attacker_profile.csv)

Contains B4 attacker force scores (`rdm_v16b4_force_ratio`, etc.). These are computed from the episode's mechanical load data, not from visit outcomes. 

**Safe to use unchanged in B12v2.** No leakage path.

### 5.5 The `episodes_df` (historical_replay_dashboard_v2_episodes.csv)

Contains episode statistical context (`peak_state`, `peak_layer_count`, etc.) used by Synthesis for the Bundle A context layer. These are episode-level aggregate statistics from the preparation phase, not visit outcomes.

**Safe to use unchanged in B12v2.** No leakage path.

---

## 6. LEAKAGE PROOF

### 6.1 Formal statement

Let `t` represent the moment in time just before visit N is observed.

```
I(t) — prediction information set:
    All rows in zone_visit_timeline.csv with visit_index < N
    All columns in zone_mechanics_cycle3_results.csv
    All columns in zone_vs_attacker_profile.csv
    All columns in historical_replay_dashboard_v2_episodes.csv
    B9 health evolution computed from vt_prior only
    B10 trajectory computed from B9(vt_prior) only
    B11 prediction computed from B10(vt_prior) only
    Synthesis output computed from B11(vt_prior) only

O(t+1) — outcome information set:
    visit_result of the single row where visit_index == N
```

### 6.2 Intersection check — field by field

| Field used in prediction | Contains visit N data? | Verdict |
|---|---|---|
| vt_prior rows | visit_index < N only | CLEAN |
| vt_prior.final_visit_result (internal to B10) | = result of visit N-1 | CLEAN |
| vt_prior.breakdown_count | breakdowns in visits 1..N-1 | CLEAN |
| vt_prior.health_last_visit | health at visit N-1 | CLEAN |
| results_df columns | replay mechanics, not visit outcomes | CLEAN |
| vs_attacker_df columns | B4 attacker force, not visit outcomes | CLEAN |
| episodes_df columns | episode preparation statistics | CLEAN |
| B9(vt_prior) outputs | derived from vt_prior only | CLEAN |
| B10(he_prior) outputs | derived from B9(vt_prior) only | CLEAN |
| B11(traj_prior) outputs | derived from B10(vt_prior) only | CLEAN |
| Synthesis(pred_prior) outputs | derived from B11(vt_prior) only | CLEAN |

**I(t) ∩ O(t+1) = empty set.** No prediction field contains visit N data.

### 6.3 What changes from B12 to B12v2

| B12 (circular) | B12v2 (non-circular) |
|---|---|
| B10 sees visit N → classifies TERMINAL if visit N = BREAKDOWN | B10 sees only visits 1..N-1 → cannot observe visit N result |
| B11 FAIL inherits TERMINAL from visit N | B11 FAIL is based on PENULTIMATE structural state |
| B12 outcome uses same visit N breakdown | B12v2 outcome uses visit N result ONLY |

---

## 7. EXPECTED POPULATION

### 7.1 From current visit timeline data

| Segment | Count |
|---|---|
| Total cases | 793 |
| Single-visit (N=1) — excluded | 312 |
| Multi-visit (N>=2) — B12v2 eligible | **481** |
| N=2 | 113 |
| N=3 | 110 |
| N=4 | 127 |
| N=5 | 88 |
| N>=6 | 43 |

### 7.2 Visit N outcome distribution (prospective, from data)

For the 481 multi-visit zones, the visit N result distribution is:

| Visit N result | B12v2 outcome | Count |
|---|---|---|
| GROWTH | HOLD | 279 |
| ABSORPTION | HOLD | 2 |
| RECLAIM | HOLD | 8 |
| BREAKDOWN | FAIL | **162** |
| DAMAGE | AMBIGUOUS (excl) | 30 |
| **Total** | | **481** |
| **HOLD + FAIL evaluable** | | **451** |
| **Baserate HOLD** | | 289/451 = 64.1% |
| **Baserate FAIL** | | 162/451 = 35.9% |

### 7.3 Penultimate visit (N-1) result distribution

The penultimate visit shows the state of the zone JUST before visit N:

| Visit N-1 result | Count |
|---|---|
| GROWTH | 279 |
| BREAKDOWN | 97 |
| DAMAGE | 88 |
| ABSORPTION | 16 |
| REFLECTION | 1 |

This means 97 zones already had a breakdown at visit N-1. After truncation, these zones will have `breakdown_count >= 1` in vt_prior → B11 will predict FAIL for most of them. These are NOT circular (prior breakdown is a valid predictor; visit N is the independent outcome).

### 7.4 Estimated evaluable population (before running)

After recomputing B11 from vt_prior, the prediction distribution will differ from the current B11 predictions:
- Zones currently TERMINAL (breakdown at visit N) → will shift to their penultimate trajectory (STRENGTHENING, DEGRADING, ACCELERATING_FAILURE, or STABLE depending on visits 1..N-1)
- Zones with prior breakdowns in visits 1..N-1 → will still get B11 FAIL via `breakdown_count >= 1` rule
- Zones with no prior breakdowns → will get HOLD, UNCERTAIN, or ACCELERATING_FAILURE→FAIL

Expected evaluable population (rough estimate): **250–350 cases** depending on prediction coverage from penultimate state. Full count only available after running.

---

## 8. OUTCOME DEFINITION (FROZEN)

B12v2 outcome is based SOLELY on visit N `visit_result`:

```
HOLD      = visit_N.visit_result in {GROWTH, ABSORPTION, REFLECTION, RECLAIM}
FAIL      = visit_N.visit_result == BREAKDOWN
AMBIGUOUS = visit_N.visit_result == DAMAGE
CENSORED  = case_id has N < 2 (no visit N exists to evaluate)
```

**This definition does NOT use:**
- Cumulative `breakdown_count` (including visit N)
- `health_last_visit` from visit N
- Any threshold on structural indicators

This is the purest prospective test: "what happened at the next interaction?"

---

## 9. PREDICTION DEFINITION (FROZEN)

B12v2 prediction is the B11 `structural_prediction` label produced from vt_prior (visits 1..N-1):

```
HOLD         = zone expected to hold at next interaction
FAIL         = zone expected to fail at next interaction
UNCERTAIN    = mixed structural signals (EXCLUDED from evaluable)
NO_PREDICTION = data quality insufficient (EXCLUDED from evaluable)
```

**This definition does NOT use:**
- visit N result
- `final_visit_result` from the full timeline (only from vt_prior)
- `breakdown_count` including visit N
- `health_last_visit` including visit N

---

## 10. FILES TO CREATE

| File | Description |
|---|---|
| `research/run_b12v2_validation.py` | Main harness script |
| `research/b12v2_penultimate_predictions.csv` | B11 predictions from vt_prior (one row per multi-visit case) |
| `research/b12v2_synthesis.csv` | Synthesis outputs from vt_prior (optional, for coherence validation) |
| `research/b12v2_case_results.csv` | Per-case: prediction vs visit N outcome, all metrics |
| `research/b12v2_report.md` | Narrative validation report |
| `research/b12v2_report.csv` | Summary metrics (accuracy, F1, physics, etc.) |

---

## 11. FILES THAT MUST NEVER BE MODIFIED

| File | Reason |
|---|---|
| `research/zone_visit_timeline.csv` | Source data — read only |
| `research/zone_mechanics_cycle3_results.csv` | Phase 1 RDM outputs — read only |
| `research/zone_structural_prediction.csv` | Phase 1 B11 outputs (full N visits) |
| `research/zone_synthesis.csv` | Phase 1 Synthesis outputs (full N visits) |
| `research/zone_structural_trajectory.csv` | Phase 1 B10 outputs (full N visits) |
| `research/zone_health_evolution.csv` | Phase 1 B9 outputs (full N visits) |
| `research/zone_mechanics_calculator.py` | Phase 1 code — no changes |
| `research/synthesis_engine.py` | Phase 1 code — no changes |
| `outputs/historical_observation_rows.csv` | Replay outputs — read only |
| `outputs/historical_replay_dashboard_v2_episodes.csv` | Replay outputs — read only |

B12v2 outputs are isolated in `b12v2_*` files. Existing Phase 1 outputs are untouched.

---

## 12. FUNCTIONS TO REUSE (EXACT)

All functions are called without modification:

```python
from research.zone_mechanics_calculator import (
    build_zone_health_evolution,        # B9
    build_zone_structural_trajectory,   # B10
    build_zone_structural_prediction,   # B11
)
from research.synthesis_engine import build_zone_synthesis  # Synthesis
```

No new parameters. No wrappers. No subclasses.  
The harness constructs the correct DataFrames and passes them to existing functions.

---

## 13. FUNCTIONS THAT DO NOT NEED CHANGES

| Function | Why unchanged |
|---|---|
| `build_zone_health_evolution()` | Accepts any `visit_timeline_df` — harness passes vt_prior |
| `build_zone_structural_trajectory()` | Accepts any `health_evolution_df` — harness passes B9(vt_prior) |
| `build_zone_structural_prediction()` | Accepts any `trajectory_df` — harness passes B10(vt_prior) |
| `build_zone_synthesis()` | Accepts any B10/B11 dfs — harness passes from truncated chain |
| `_structural_trajectory_label()` | Internal to B10; behaves correctly on truncated data |
| `_structural_prediction_label()` | Internal to B11; behaves correctly on truncated data |
| `compute_coherence_label()` | Internal to Synthesis; behaves correctly |

---

## 14. METRICS TO COMPUTE (design, no implementation yet)

After B12v2 runs, these metrics will be computed:

### Population
- Total cases, N>=2 cases, excluded (N=1), AMBIGUOUS visit N, evaluable (HOLD/FAIL pred + HOLD/FAIL outcome)
- Baserate HOLD, baserate FAIL
- Regime shift (first half vs second half)

### Overall
- Correct predictions, incorrect predictions
- Overall accuracy, lift vs naive baseline

### HOLD analysis
- Precision, Recall, F1, lift vs baserate
- False HOLD count and rate (predicted HOLD, visit N = BREAKDOWN)
- Broken down by: trajectory, mechanical state, coherence, visit count, health state

### FAIL analysis
- Precision, Recall, F1, lift vs baserate
- False FAIL count and rate (predicted FAIL, visit N = HOLD)
- Broken down by: trajectory, mechanical state, coherence, visit count, health state

### Coherence validation
- STRONG, MODERATE, WEAK, INSUFFICIENT case counts
- Accuracy per tier
- Verify STRONG > MODERATE > INSUFFICIENT (or explain if not)

### Trajectory validation
- Per-trajectory: case count, accuracy, HOLD%, FAIL%, lift vs baserate
- Identify: useful trajectories (lift > 5pp), non-useful trajectories (lift < 0)
- Special attention: ACCELERATING_FAILURE (the non-circular FAIL signal)

### Synthesis contribution
- Coherence filtering: does STRONG accuracy > full population accuracy?
- NO_PREDICTION removal: does excluding these improve precision?
- Integrated chain vs raw B10 trajectory only

### Physics (unchanged from B12)
- sigma x penetration vs omega
- sigma_barre vs reclaim_history
- sigma_barre vs memory_score

### Error analysis
- Most dangerous false HOLD groups (by trajectory, mechanical state, coherence)
- Most dangerous false FAIL groups

---

## 15. HOW TO AVOID CHANGING LIVE/REPLAY/RDM BEHAVIOR

Three isolation principles:

**1. All B12v2 outputs use distinct file prefixes.**  
Files are named `b12v2_*`. No existing filename is overwritten.

**2. B12v2 calls existing functions but does not import from them destructively.**  
It reads, it calls, it produces new DataFrames. It does not write to existing CSV paths.

**3. B12v2 runs in complete isolation.**  
The production pipeline (zone_mechanics_calculator.py main block) is never called. B12v2 directly calls the individual build functions with controlled inputs.

---

## 16. IMPLEMENTATION SEQUENCE

When implementation is authorized:

```
Step 1 — Harness setup
  Create research/run_b12v2_validation.py
  Load: zone_visit_timeline.csv, zone_mechanics_cycle3_results.csv,
        zone_vs_attacker_profile.csv, historical_replay_dashboard_v2_episodes.csv

Step 2 — Visit split
  Group by case_id
  Identify N = max(visit_index) per case
  Split: vt_prior = visit_index < N; outcome_row = visit_index == N
  Filter: only cases with N >= 2

Step 3 — Outcome classification
  For each outcome_row: classify HOLD / FAIL / AMBIGUOUS from visit_result only
  Store in outcome_df: case_id, visit_N_result, b12v2_outcome

Step 4 — Recompute B9 on vt_prior
  build_zone_health_evolution(results_df, vt_prior, run_utc)
  Verify: he_prior_df has same case_id set as multi-visit cases

Step 5 — Recompute B10 on he_prior
  build_zone_structural_trajectory(results_df, he_prior_df, run_utc)

Step 6 — Recompute B11 on traj_prior
  build_zone_structural_prediction(results_df, traj_prior_df, vs_attacker_df, run_utc)

Step 7 — Recompute Synthesis
  build_zone_synthesis(results_df, traj_prior_df, pred_prior_df, episodes_df, run_utc)

Step 8 — Leakage check (automated assertion)
  Assert: no column in pred_prior_df uses visit N data
  Assert: no visit N visit_result appears in vt_prior

Step 9 — Merge predictions with outcomes
  evaluable = merge(pred_prior_df, outcome_df, on='case_id')
  Filter: pred_label in {HOLD, FAIL} AND b12v2_outcome in {HOLD, FAIL}

Step 10 — Compute all validation metrics
  Accuracy, F1, coherence, trajectory, error analysis, physics

Step 11 — Save outputs
  b12v2_penultimate_predictions.csv
  b12v2_case_results.csv
  b12v2_report.md
  b12v2_report.csv
```

---

## 17. RISKS

| Risk | Probability | Mitigation |
|---|---|---|
| B9 returns empty rows for some cases with only 1 truncated visit | LOW | build_zone_health_evolution handles N=1 visit (slope = NaN, state = UNKNOWN) — these get NO_PREDICTION and are excluded from evaluable |
| B10 UNKNOWN trajectory for all penultimate states → low coverage | MEDIUM | Expected. DEGRADING zones that were TERMINAL in full-history will shift to UNCERTAIN/NO_PREDICTION. Coverage may be 40–60% of 481 multi-visit zones. |
| vs_attacker_df is missing some cases | LOW | Already verified: 793 rows, all case_ids present |
| Synthesis gate rejects many cases → low coverage | LOW | Synthesis gate primarily checks visit_count and confidence; penultimate states still have valid data |
| N=2 zones with 1 prior visit produce weak B9/B10 outputs | MEDIUM | Valid behavior — UNKNOWN trajectory → NO_PREDICTION → excluded from evaluable. Not a bug. |
| Prior breakdown (visits 1..N-1) creates a soft leakage path | PRESENT | This is ACCEPTED and documented. Prior breakdown is a valid prospective predictor. The outcome is visit N (a different event). This is non-circular. |

---

## 18. SELF REVIEW

### What assumptions are confirmed by this design?

1. Existing B9/B10/B11/Synthesis functions can be called with truncated data — CONFIRMED by code inspection (all accept DataFrames as parameters, no global state reads from filesystem during execution)

2. `results_df` does not contain visit-outcome-dependent fields — CONFIRMED by column analysis (sigma_barre, capacity, rigidity are computed from price mechanics replay, not from visit_result labels)

3. `vs_attacker_df` contains only B4 force scores, not visit outcomes — CONFIRMED (793 rows, all force-related columns)

4. `episodes_df` contains only preparation-phase statistics — CONFIRMED (peak_state, peak_layer_count are episode-level, not visit-outcome-level)

5. The visit split (vt_prior = visit_index < N, outcome_row = visit_index == N) is deterministic and complete — CONFIRMED for all 793 cases

6. Multi-visit zones: 481 of 793 (60.7%) — CONFIRMED from data

7. Visit N HOLD+FAIL evaluable: 451 of 481 (93.8%) — CONFIRMED from data

### What assumptions are rejected?

1. ~~Pop-2 (prior_breakdown==0) is sufficient for non-circular evaluation~~ — REJECTED. Even in Pop-2, TERMINAL zones in B10 use `final_visit_result == "BREAKDOWN"` from the full timeline. The entire current B12 evaluation design was circular.

2. ~~No optional parameters are needed in B9/B10/B11~~ — CONFIRMED CORRECT. The harness approach (pass truncated DataFrames) is simpler than adding parameters and avoids any risk of modifying production code.

### What remains unverified until implementation?

1. The actual prediction distribution after recomputing B11 from penultimate states. How many of the 481 multi-visit cases will produce HOLD or FAIL predictions (vs UNCERTAIN/NO_PREDICTION)?

2. The ACCELERATING_FAILURE count in the penultimate state. This is the most important non-circular FAIL signal. Its count is unknown until B10 is run on truncated data.

3. Whether zones that are currently TERMINAL (breakdown at visit N) had ACCELERATING_FAILURE penultimate states (which would make B12v2 FAIL predictions genuinely non-circular) vs STRENGTHENING states (which would appear as false HOLDs).

4. Whether the sigma_barre vs reclaim_history correlation degradation (r=0.209 on n=793) is genuine or an artifact of the dataset distribution.

---

## 19. GREEN FLAGS

- All four B9/B10/B11/Synthesis functions accept DataFrame parameters and require zero modification
- Visit N data is completely isolated in `outcome_row` — no risk of contamination if harness is written correctly
- 481 multi-visit zones provide sufficient sample for meaningful evaluation
- 451 evaluable (HOLD+FAIL) visit N outcomes — 93.8% of multi-visit zones have a clean outcome (only 30 DAMAGE final visits excluded as AMBIGUOUS)
- Baserate for B12v2: HOLD=64.1%, FAIL=35.9% — nearly identical to B12 baserate (63.3%/36.7%), confirming the evaluation populations are comparable
- The integrated Phase 1 chain (Statistics → Preparation → Lifecycle → RDM → Synthesis) is fully preserved in the recomputed path
- Physics validation (sigma × penetration) is unaffected — carried forward unchanged from B12
- `vs_attacker_df` does not require regeneration
- `episodes_df` does not require regeneration

## 20. YELLOW FLAGS

- ACCELERATING_FAILURE count in penultimate states is unknown until B12v2 runs. It could be as low as 4–20 cases, which may be statistically insufficient for FAIL-specific analysis.
- N=2 zones (113 cases) will have only 1 prior visit. B9 health slope will be NaN (only 1 point). B10 trajectory may be UNKNOWN → NO_PREDICTION. Coverage for N=2 cases may be very low.
- Zones that were TERMINAL (in current B10) due to a first-time breakdown at visit N: their penultimate state may be STRENGTHENING → B11 HOLD prediction → false HOLD in B12v2. This is the most important group to analyze.
- The prediction distribution will be materially different from current B11 (fewer TERMINAL → FAIL, more UNCERTAIN/NO_PREDICTION). The evaluable population size is uncertain.
- Prior breakdowns (visits 1..N-1) feeding B11 FAIL are technically non-circular (different visit from the measured outcome) but represent a "semi-prospective" test — the model already observed a breakdown before. The performance on THESE cases is meaningful but easier than predicting first-time breakdowns.

## 21. RED FLAGS

- None identified for the B12v2 design itself.
- If the evaluable population from B12v2 is < 50 cases (possible if most multi-visit zones get NO_PREDICTION from penultimate state), statistical conclusions will be fragile.
- This risk is mitigated by: 481 total multi-visit zones and 451 evaluable visit N outcomes. Even at 30% prediction coverage, evaluable population = 135.

---

## 22. STATUS

| Check | Result |
|---|---|
| No contradiction with B12 leakage review | PASS |
| No contradiction with current implementation | PASS |
| No feature creep | PASS |
| No bypass of integrated Phase 1 chain | PASS |
| No hidden future information | PASS |
| No circular validation path | PASS |
| No changes to Phase 1 production files | PASS |

**CONSISTENCY STATUS: PASS**  
**LEAKAGE STATUS: PASS** (design eliminates all identified circular paths)  
**ARCHITECTURAL STATUS: PASS**  

---

## 23. FINAL RECOMMENDATION

B12v2 can be implemented in a single file (`research/run_b12v2_validation.py`) with no changes to any existing Phase 1 code.

The implementation requires:
1. A visit split loop (group by case_id, separate visit N)
2. Four sequential function calls (B9 → B10 → B11 → Synthesis) on vt_prior
3. An outcome classification step (visit N visit_result only)
4. Standard metric computation (accuracy, F1, coherence, trajectory)

Estimated implementation effort: 1 session.

**Authorize implementation when ready.**

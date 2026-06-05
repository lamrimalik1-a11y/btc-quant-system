# B12 Leakage Review
**Date:** 2026-06-05  
**Status:** PRE-B12 — investigation only. No final accuracy numbers produced.

---

## 1. EXECUTIVE SUMMARY

The B12 evaluation design has a structural data leakage problem.

**B10/B11/Synthesis code is NOT corrupted.**  
The code computes correct predictions from whatever visit data it receives.

**The B12 evaluation methodology IS circular.**  
B10/B11 are computed from the complete visit history (visits 1..N). B12 then evaluates those predictions against outcomes derived from the same complete visit history. This produces near-100% accuracy by construction, not by genuine predictive performance.

**Root cause:**  
`final_visit_result` (the result of visit N) appears in both:
- B10 TERMINAL classification rule (line 3998)
- B12 FAIL outcome definition

These two uses of the same field create a closed loop.

**The contamination is an evaluation design problem — not a model bug.**

---

## 2. LEAKAGE CHAIN TRACING

### What is "future information"?

In a prospective validation, "future information" means any data from visit N (the visit being predicted), as opposed to visits 1..N-1 (the observable history before the prediction is made).

The contaminated fields are:
- `final_visit_result` — the result of the most recent visit in the dataset (= visit N)
- `breakdown_visit_count` — cumulative, includes visit N if visit N was a BREAKDOWN
- `health_last_visit` — health value computed at visit N
- `health_slope` — derived from all health values including visit N

### Contamination entry point: B8

B8 (`build_zone_visit_timeline`) records all visits including visit N.  
When it computes `final_visit_result`, this IS the result of visit N.

This is correct behavior for a live deployment where the system processes data up to the current moment. But in B12 retrospective evaluation, visit N is the "future" we are trying to predict.

**The contamination enters the evaluation design at B8, not at B10 or B11.**

### Propagation through the chain:

```
B8: records all N visits
    final_visit_result = result of visit N  <-- contaminated input
    breakdown_visit_count includes visit N  <-- contaminated input

B9: reads B8 outputs
    health_last_visit = health at visit N   <-- contaminated
    health_slope uses all N visits           <-- contaminated
    breakdown_visit_count forwarded          <-- contaminated

B10: reads B9 outputs
    _structural_trajectory_label() line 3998:
      if final_visit_result == "BREAKDOWN" or breakdown_count >= 2:
          return "TERMINAL"                 <-- DIRECT contamination
    (also at line 4022: RECOVERY uses final_visit_result)

B11: reads B10 outputs
    _structural_prediction_label() line 4315:
      if structural_trajectory in _FAIL_TRAJECTORIES  <- from B10
          or breakdown_count >= 1                      <-- contaminated
          return "FAIL"

Synthesis: reads B11 outputs
    compute_coherence_label() uses:
      structural_trajectory (from B10)     <-- contaminated via B10
      structural_prediction (from B11)     <-- contaminated via B11
      trajectory_confidence (from B10)     <-- derived from B10
    Synthesis itself has no direct contamination — it inherits it via B10/B11.

B12 FAIL outcome definition:
    (final_visit_result == "BREAKDOWN")    <-- same field as B10 line 3998
    OR (breakdown_count >= 2               <-- same field as B10 line 3998
        AND health_last_visit < 20)
```

The loop closes at B12:
- B10 assigns TERMINAL because `final_visit_result == "BREAKDOWN"` (visit N result)
- B11 assigns FAIL because trajectory is TERMINAL
- B12 observes FAIL because `final_visit_result == "BREAKDOWN"` (same visit N result)

---

## 3. LAYER-BY-LAYER CONTAMINATION STATUS

### B10 — Structural Trajectory

**Status: CONTAMINATED for retrospective B12. Clean in live use.**

Contamination source: `final_visit_result` in the TERMINAL rule.

```python
# zone_mechanics_calculator.py line 3998
if final_visit_result == "BREAKDOWN" or breakdown_count >= 2:
    return "TERMINAL"
```

In live use: `final_visit_result` = result of the most recent completed visit. The system has not yet seen the next visit. This is a valid historical signal — "the zone's last interaction was a breakdown."

In retrospective B12 evaluation: the "most recent visit" IS the visit whose outcome we are trying to predict. The prediction and the evaluation are based on the same visit.

Secondary contamination: The RECOVERY rule at line 4022 uses `final_visit_result == "GROWTH"`. Same issue but less severe (RECOVERY → HOLD prediction; HOLD outcome requires GROWTH final visit — partially correlated but not identical, since RECOVERY also requires `damage_count > 0` and `slope_pos`).

**Trajectories contaminated:** TERMINAL (severe), RECOVERY (partial)  
**Trajectories NOT contaminated:** ACCELERATING_FAILURE, STABLE, DEGRADING, STRENGTHENING, UNKNOWN

ACCELERATING_FAILURE uses: `health_state == HEALTH_COLLAPSING` AND `damage_count >= 2` AND `slope_neg`. None of these use `final_visit_result`. This is the only trajectory capable of producing a non-circular FAIL prediction.

### B11 — Structural Prediction

**Status: CONTAMINATED for retrospective B12 via B10. Clean in live use.**

Contamination paths:
1. `structural_trajectory in _FAIL_TRAJECTORIES` — if B10 is TERMINAL (contaminated), B11 inherits
2. `breakdown_count >= 1` — contaminated if visit N was a breakdown
3. `health_state == HEALTH_COLLAPSING` — partially contaminated (health slope uses visit N data)

The B11 HOLD condition at line 4321:
```python
if (structural_trajectory in _HOLD_TRAJECTORIES
        and breakdown_count == 0
        and (health_last_visit >= 20)):
    return "HOLD"
```
`breakdown_count == 0` is not contaminated by visit N IF visit N is not a breakdown. Since HOLD outcomes have no breakdown (`breakdown_count == 0` from B12 HOLD definition), this condition is satisfied consistently — but not by circular definition. It's shared between prediction and outcome but not tautological.

### Synthesis Engine

**Status: CONTAMINATED for retrospective B12 via B10/B11 inheritance. Code itself is clean.**

The coherence computation uses:
- `structural_trajectory` (from B10) — contaminated via TERMINAL rule
- `structural_prediction` (from B11) — contaminated via B10
- `trajectory_confidence`, `prediction_confidence` — derived scores, contaminated via B10/B11
- `visit_count` — clean (total count, not outcome-dependent)

The Synthesis coherence logic itself contains no direct reference to `final_visit_result` or `breakdown_count`. The contamination arrives only via B10/B11 inputs.

---

## 4. IMPACT BY PREDICTION TYPE

### FAIL Predictions — SEVERELY CONTAMINATED

**For TERMINAL zones (assigned via `final_visit_result == "BREAKDOWN"`):**

The circular loop is closed completely:
```
final_visit_result == "BREAKDOWN"
  → B10: TERMINAL
  → B11: FAIL
  → B12 outcome: FAIL  (because final_visit_result == "BREAKDOWN")
```
100% of cases in this sub-group will match. Not evidence of predictive value.

**For TERMINAL zones (assigned via `breakdown_count >= 2`):**

Nearly circular:
```
breakdown_count >= 2
  → B10: TERMINAL
  → B11: FAIL
  → B12 outcome: FAIL if (final_visit_result == "BREAKDOWN") OR (breakdown_count >= 2 AND health < 20)
```
The B12 health condition (`health < 20`) adds a non-circular filter, but in practice zones with `breakdown_count >= 2` almost always meet it or have a BREAKDOWN final visit as well. This accounts for the 0 false FAILs in the retrospective result.

**For ACCELERATING_FAILURE zones (no breakdowns):**

The FAIL prediction comes from:
```
health_state == HEALTH_COLLAPSING AND damage_count >= 2 AND health_slope < 0
  → B10: ACCELERATING_FAILURE
  → B11: FAIL
  → B12 outcome: FAIL requires final_visit_result == "BREAKDOWN"
```
This is NOT circular. B11 predicts FAIL from structural deterioration signals (health state, damage accumulation, slope). B12 observes FAIL only if the final visit was a breakdown. These are different conditions.

The 4 false predictions in the retrospective result (FAIL predicted, HOLD observed) are all from this group. These are the only genuine non-circular predictions in the current dataset.

**Summary for FAIL:** Contaminated for all TERMINAL zones. Non-circular for ACCELERATING_FAILURE zones only.

### HOLD Predictions — PARTIALLY CONTAMINATED

**For STRENGTHENING zones:**

```
health_state == HEALTH_STRENGTHENING AND growth_count >= damage_count AND breakdown_count == 0
  → B10: STRENGTHENING
  → B11: HOLD
  → B12 outcome: HOLD if final_vr in {GROWTH, ABSORPTION, REFLECTION, RECLAIM} AND breakdown_count == 0
```

Both require `breakdown_count == 0` — this is a shared constraint but not circular.  
`HEALTH_STRENGTHENING` (B10) and `final_vr in HOLD_OUTCOMES` (B12) are different conditions.

A STRENGTHENING zone COULD have a DAMAGE final visit → AMBIGUOUS outcome → excluded from evaluable, not a false HOLD.  
A STRENGTHENING zone COULD have a BREAKDOWN final visit → excluded from STRENGTHENING by definition (`breakdown_count == 0` required). Only possible if visit N is the FIRST breakdown. B10 then becomes TERMINAL (via `final_visit_result == BREAKDOWN`), not STRENGTHENING, so the B11 prediction changes to FAIL. The zone would appear as a false FAIL in B12, not a false HOLD.

**The 0 false HOLDs in the retrospective result is NOT purely circular** — it reflects that the system correctly identifies structural strengthening zones. However, it is impossible to distinguish genuine predictive accuracy from selection bias (AMBIGUOUS cases excluded) in the current design.

**Summary for HOLD:** Partially contaminated via the `breakdown_count == 0` shared constraint. Stronger contamination comes from the AMBIGUOUS exclusion mechanism (288 cases excluded, many of which are likely zones with DAMAGE final visits that could have been false HOLDs).

### Coherence — CONTAMINATED BY INHERITANCE

Coherence is computed from B10 trajectory + B11 prediction. If those are contaminated, coherence inherits the contamination. The coherence metric cannot be validated against outcomes when the outcomes are circular. The STRONG vs MODERATE comparison showing 100% vs 100% confirms this — it is not a useful signal in the current B12 design.

### Interpretation Text — CONTAMINATED BY INHERITANCE

Interpretation strings use `structural_trajectory` and `structural_prediction` as inputs. The text correctly reflects the structural characterization, but cannot be validated as prospective predictions when the characterization is circular.

---

## 5. THE 4 GENUINE NON-CIRCULAR OBSERVATIONS

The retrospective confusion matrix shows 4 incorrect predictions: FAIL predicted, HOLD observed.

These are the ONLY cases where B11 made a non-circular prediction. Specifically:

- B11 predicted FAIL from ACCELERATING_FAILURE trajectory
- ACCELERATING_FAILURE uses: `HEALTH_COLLAPSING AND damage_count >= 2 AND slope_neg`
- None of these conditions use `final_visit_result`
- B12 observed HOLD because the final visit was GROWTH/ABSORPTION/REFLECTION/RECLAIM

This means B11's ACCELERATING_FAILURE prediction was wrong in 4 cases: the structural deterioration signals fired (collapsing health, accumulated damage, negative slope) but the zone recovered at its final visit.

**These 4 cases are the first genuine prospective data points from Phase 1.**

To measure the ACCELERATING_FAILURE prediction accuracy:
- Need to identify ALL zones assigned ACCELERATING_FAILURE trajectory
- Count how many had their final visit = BREAKDOWN (true FAIL) vs HOLD outcome
- Those with AMBIGUOUS final visits (DAMAGE) are genuinely ambiguous — neither confirmed nor denied

---

## 6. PROPOSED B12v2 METHODOLOGY — PENULTIMATE-STATE DESIGN

### Design

For each zone with N visits (require N >= 2):

**Step 1 — Truncate.**  
Create a view of the visit timeline with only visits 1..N-1 (excluding visit N).

**Step 2 — Recompute.**  
Run B9/B10/B11 on the truncated visit timeline.  
In the truncated dataset, `final_visit_result` = result of visit N-1, not visit N.  
`breakdown_count` = breakdowns in visits 1..N-1 only.  
`health_last_visit` = health at visit N-1.

**Step 3 — Predict.**  
The B11 label produced from truncated data is the PROSPECTIVE prediction.

**Step 4 — Observe.**  
Visit N result = `HOLD`, `FAIL`, or `AMBIGUOUS` per the frozen outcome definitions.

**Step 5 — Evaluate.**  
Compare B11 (from visits 1..N-1) against visit N outcome.

This eliminates the circular dependency completely:
- `final_visit_result` in B10 = result of visit N-1 (known before visit N)
- B12 outcome = result of visit N (genuinely future relative to the prediction)

### Why this is mathematically valid

The prediction is made from the information set I(t) = {visits 1..N-1}. The outcome is visit N, which belongs to I(t+1) but NOT to I(t). The prediction and the outcome are derived from disjoint data.

Formally: prediction(I(t)) is evaluated against outcome(I(t+1) \ I(t)). No element of I(t+1) \ I(t) appears in prediction(I(t)). No circular dependency exists.

### Required implementation

A `hold_final_visit=True` flag added to `build_zone_structural_trajectory()` and `build_zone_structural_prediction()` that uses `visits.iloc[:-1]` instead of `visits` when computing trajectory inputs.

The flag requires passing it through from a new `run_b12v2_validation.py` that:
1. Loads zone_visit_timeline.csv
2. For each zone with N >= 2 visits, creates a truncated visit slice
3. Recomputes B9/B10/B11 on the truncated slice
4. Stores penultimate-state predictions
5. Compares against visit N outcomes

This is NOT a change to the Phase 1 pipeline — it is a validation harness extension.

### Single-visit zones

Zones with N = 1 visit have no penultimate state. They cannot be evaluated prospectively. They are excluded from B12v2. Current count: 312 of 793 cases (39.3%).

---

## 7. METRICS THAT REMAIN TRUSTWORTHY (current B12)

These metrics do not involve circular dependencies and are valid regardless of the evaluation design:

| Metric | Value | Why Trustworthy |
|---|---|---|
| Integrity check (all 6) | PASS | No outcome labels involved |
| Total cases | 793 | Count only |
| Baserate HOLD | 63.3% | Observed outcomes, not predictions |
| Baserate FAIL | 36.7% | Observed outcomes, not predictions |
| Regime shift (FAIL rate first vs second half) | 2.9% — STABLE | Observed outcomes vs time |
| Population split (HOLD/FAIL/AMBIGUOUS/NO_PRED) | documented | Count only |
| Physics: sigma x penetration vs omega | r=0.9978, n=459 | No visit outcomes involved |
| Physics: sigma_barre vs reclaim_history | r=0.2095, n=793 | No visit outcomes involved |
| Physics: sigma_barre vs memory_score | r=0.5758, n=793 | No visit outcomes involved |
| ACCELERATING_FAILURE zone count | 4 false FAILs | Non-circular per §5 above |
| NO_PREDICTION coverage | 312/793 = 39.3% | System abstention rate |
| AMBIGUOUS outcome count | 288/793 = 36.3% | Evaluation design limitation |

### Physics correlation note:

The sigma_barre correlations degraded from prior small-sample values (n=31):
- `sigma_barre vs reclaim_history`: 0.686 → 0.2095
- `sigma_barre vs memory_score`: 0.672 → 0.5758

This is not alarming. The prior values were from n=31 (the first validation batch), which is insufficient for stable correlation estimates. Small-sample Pearson r has large upward bias. The n=793 values are the authoritative estimates. The memory score correlation (r=0.5758) remains meaningful. The reclaim_history correlation (r=0.2095) is weak on the full dataset and should be re-evaluated.

---

## 8. METRICS THAT MUST BE DISCARDED (current B12)

These metrics are circular and cannot be interpreted as evidence of predictive performance:

| Metric | Contamination Level | Why Discarded |
|---|---|---|
| Retrospective accuracy (99.1%) | SEVERE | TERMINAL prediction = circular |
| Prospective Pop-2 accuracy (100%) | SEVERE | TERMINAL in Pop-2 still circular |
| HOLD precision/recall/F1 (retrospective) | MODERATE | Shared breakdown_count==0 + AMBIGUOUS exclusion |
| FAIL precision/recall/F1 (retrospective) | SEVERE | TERMINAL prediction is circular |
| Coherence accuracy by tier | SEVERE | Inherits B10/B11 contamination |
| Trajectory accuracy by tier | SEVERE | Inherits B10/B11 contamination |
| False HOLD count (0) | MODERATE | Partial artifact of AMBIGUOUS exclusion |
| False FAIL count (0) | SEVERE | TERMINAL zones are circular |
| Lift vs baseline (all) | SEVERE | Based on circular accuracy |

---

## 9. FINAL REVIEW — HIDDEN LEAKAGE CHECK

### Previous architectural reports

The pre-backtest architecture review (PHASE1B_SYNTHESIS_ENGINE_STABLE commit) did not explicitly address the B12 evaluation design leakage. The architecture was documented as a characterization system, which is correct. The validation methodology was not specified in detail at that point.

No previous report incorrectly claimed that retrospective accuracy == prospective predictive power.

**Leakage from previous reports: NONE INTRODUCED.**

### Implementation reports

The B10 STABLE priority fix (added `if health_state == "HEALTH_STABLE": return "STABLE"` before DEGRADING check) did not introduce contamination. Health state is derived from health slope, total change, and visit counts — none of which directly use `final_visit_result` for STABLE classification.

The B7.6-D omega validation (r=0.9935) was a physics validation, not an outcome prediction. It remains uncontaminated.

**Leakage from implementation changes: NONE INTRODUCED.**

### Current codebase

The contamination is confined to the interaction between:
1. `final_visit_result` in `_structural_trajectory_label()` at line 3998
2. `final_visit_result` in the B12 FAIL outcome definition

No other hidden leakage paths were identified:
- Sigma, omega, fleche, fatigue, rigidity — all computed from price mechanics, not from visit outcome labels
- sigma_barre is computed at zone birth from structural properties, not from visit outcomes
- Coherence is computed from trajectory direction and confidence levels, not from visit outcome labels
- The NO_PREDICTION gate filters LOW confidence and UNKNOWN trajectory — neither of which uses `final_visit_result`

**One potential secondary leakage: RECOVERY trajectory**  
Line 4022: `if final_visit_result == "GROWTH" and damage_count > 0 and slope_pos: return "RECOVERY"`

RECOVERY → B11 HOLD prediction  
B12 HOLD outcome: final_vr in {GROWTH, ABSORPTION, REFLECTION, RECLAIM}

Both use `final_visit_result`. But RECOVERY requires `final_visit_result == "GROWTH"` specifically, while HOLD outcome accepts any of the four positive states. These are correlated but not identical.

For a zone with RECOVERY trajectory (final_vr == "GROWTH"), the HOLD outcome definition is satisfied (GROWTH is in the HOLD set). This creates a soft circular path for RECOVERY → HOLD predictions.

**This is an additional source of circularity for HOLD predictions.** It is less severe than TERMINAL (which has hard identity), but real.

**Fully listed hidden leakage paths:**
1. TERMINAL → FAIL (hard circular, via `final_visit_result == "BREAKDOWN"`)
2. RECOVERY → HOLD (soft circular, via `final_visit_result == "GROWTH"`)
3. STRENGTHENING → HOLD (partial, via shared `breakdown_count == 0`)

No others identified.

---

## 10. FLAGS

### GREEN FLAGS

- Physics core (sigma x penetration vs omega) r=0.9978 on n=459 is CONFIRMED and improved
- Integrity: all 6 checks PASS, 793 cases, no duplicates, no mismatches
- Architecture chain B8→B9→B10→B11→Synthesis is intact; no bypass of any layer
- Baserate is stable (regime shift 2.9pp); the B12v2 population will have a stable prior
- B10/B11 code logic is SOUND for live use; contamination is evaluation-only
- The 4 false FAIL predictions (ACCELERATING_FAILURE → HOLD outcome) are valid non-circular signal
- ACCELERATING_FAILURE trajectory is a genuine prospective FAIL predictor; it just has n=4 in the current dataset
- B12v2 methodology is clearly defined and feasible with a one-pass pipeline re-run

### YELLOW FLAGS

- sigma_barre vs reclaim_history dropped from 0.686 (n=31) to 0.2095 (n=793). The n=793 value is authoritative. The B7.6-C/D reclaim correlation hypothesis needs to be re-examined on the full dataset.
- 288 AMBIGUOUS outcomes (36.3%) remain outside the evaluation boundary. Many are zones with DAMAGE final visits — this is a fundamental limitation of the visit outcome classification (DAMAGE is neither HOLD nor FAIL).
- ACCELERATING_FAILURE zones have n=0 in the evaluable retrospective population, meaning the only genuine prospective test produces 4 data points — statistically insufficient.
- Single-visit zones (312 / 39.3%) cannot participate in B12v2.
- RECOVERY trajectory has soft leakage via `final_visit_result == "GROWTH"`.

### RED FLAGS

- TERMINAL trajectory FAIL prediction is perfectly circular in the current evaluation design.
- Pop-2 prospective design does NOT escape the circularity for TERMINAL zones.
- 100% retrospective accuracy and 100% Pop-2 prospective accuracy are artifacts, not evidence.
- sigma_barre vs reclaim_history r=0.2095 on n=793 is materially weaker than the n=31 estimate; the B7.6-C structural memory hypothesis may need revision.

---

## 11. FINAL LEAKAGE STATUS

| Layer | Status | Reason |
|---|---|---|
| B10 code | CLEAN | Valid for live deployment |
| B11 code | CLEAN | Valid for live deployment |
| Synthesis code | CLEAN | No direct use of outcome labels |
| B12 retrospective evaluation | FAIL | TERMINAL circular, RECOVERY soft circular |
| B12 prospective Pop-2 design | FAIL | TERMINAL still circular in Pop-2 |
| B12v2 penultimate-state design | VALID | Removes all circular dependencies |

**FINAL LEAKAGE STATUS: FAIL for current B12 evaluation design.**  
The Phase 1 model code is clean. The evaluation methodology is not valid.

B12v2 with the penultimate-state design is required before a valid accuracy number can be reported.

---

## 12. RECOMMENDED NEXT STEPS

1. Implement `run_b12v2_validation.py` with penultimate-state design (N-1 visit truncation)
2. Minimum required change: a `truncate_final_visit=True` parameter to `build_zone_structural_trajectory()` and `build_zone_structural_prediction()`
3. Run B12v2 on all zones with N >= 2 (481 zones)
4. Separately report ACCELERATING_FAILURE prediction accuracy (the most robust non-circular signal)
5. Re-examine sigma_barre vs reclaim_history on n=793 — the small-sample correlation hypothesis may need revision

**Do NOT run B12 final validation until B12v2 is implemented.**

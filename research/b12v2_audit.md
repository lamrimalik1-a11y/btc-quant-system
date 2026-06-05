# B12v2 — Too-Good-To-Be-True Audit
**Date:** 2026-06-05
**Results under review:** Accuracy=99.0%, False HOLD=0, False FAIL=3

---

## 1. QUESTION UNDER INVESTIGATION

B12v2 reported 99.0% prospective accuracy with 0 false HOLDs and only 3 false FAILs.
This audit determines whether that result reflects:
(A) Genuine predictive power, or
(B) High selectivity masking a narrower actual signal.

---

## 2. COVERAGE ANALYSIS

### 2.1 Full population accounting

| Population | Count | % of eligible |
|---|---|---|
| Multi-visit eligible (N>=2) | 481 | 100% |
| HOLD predicted | 223 | 46.4% |
| FAIL predicted | 90 | 18.7% |
| UNCERTAIN (excluded) | 55 | 11.4% |
| NO_PREDICTION (excluded) | 113 | 23.5% |
| **Total with predictions** | **313** | **65.1%** |
| **Coverage (HOLD+FAIL / non-ambiguous)** | **306/451** | **67.8%** |

Of the 481 eligible zones, only 313 received a prediction (65.1%).
Of the 451 with unambiguous visit N outcomes (HOLD or FAIL), only 306 are in
the evaluable population (67.8%).

**The system withholds predictions for 32.2% of evaluable cases.**

### 2.2 What happens to the 168 excluded zones?

| B11 label | Visit N outcome | Count | Implication |
|---|---|---|---|
| NO_PREDICTION | HOLD | 65 | System withheld; would have been correct HOLD |
| UNCERTAIN | FAIL | 48 | System withheld; actually failed |
| NO_PREDICTION | FAIL | 29 | System withheld; actually failed |
| NO_PREDICTION | AMBIGUOUS | 19 | No verdict possible |
| UNCERTAIN | AMBIGUOUS | 4 | No verdict possible |
| UNCERTAIN | HOLD | 3 | System withheld; would have been correct HOLD |

The most consequential exclusion:
- **48 UNCERTAIN zones had FAIL outcomes** — B11 said "uncertain" but the zone broke
- **29 NO_PREDICTION zones had FAIL outcomes** — B11 said "no prediction" but the zone broke
- Total missed FAIL signals: **77 out of 162 actual FAIL events** (47.5% of all FAILs undetected)

---

## 3. B10 TRAJECTORY DETERMINISM

B10 trajectory label vs visit N outcome (all 481 zones):

| Trajectory | HOLD outcomes | FAIL outcomes | AMBIG | Total | FAIL rate |
|---|---|---|---|---|---|
| STRENGTHENING | 216 | 0 | 0 | 216 | 0% |
| TERMINAL | 5 | 88 | 4 | 97 | 90.7% |
| DEGRADING | 3 | 70 | 18 | 91 | 76.9% (of HOLD+FAIL) |
| UNKNOWN | 63 | 0 | 1 | 64 | 0% |
| STABLE | 2 | 3 | 7 | 12 | 60% (of HOLD+FAIL) |
| ACCELERATING_FAILURE | 0 | 1 | 0 | 1 | 100% |

**STRENGTHENING is perfectly predictive of HOLD** (216/216 — 0 FAIL outcomes).
**TERMINAL is highly predictive of FAIL** (88/93 HOLD+FAIL — 94.6% FAIL rate).
**DEGRADING is highly predictive of FAIL** (70/73 HOLD+FAIL — 95.9% FAIL rate).

DEGRADING's 95.9% FAIL rate is nearly as strong as TERMINAL's 94.6%, but B11
outputs UNCERTAIN or NO_PREDICTION for all 91 DEGRADING zones. These zones are
the largest missed opportunity.

---

## 4. B11 IS LARGELY A RELAY OF B10

B10 trajectory to B11 prediction mapping (complete):

| B10 Trajectory | HOLD | FAIL | UNCERTAIN | NO_PREDICTION |
|---|---|---|---|---|
| STRENGTHENING (216) | 216 (100%) | 0 | 0 | 0 |
| TERMINAL (97) | 0 | 89 (91.8%) | 0 | 8 (8.2%) |
| DEGRADING (91) | 0 | 0 | 53 (58.2%) | 38 (41.8%) |
| UNKNOWN (64) | 0 | 0 | 0 | 64 (100%) |
| STABLE (12) | 7 (58.3%) | 0 | 2 (16.7%) | 3 (25.0%) |
| ACCELERATING_FAILURE (1) | 0 | 1 (100%) | 0 | 0 |

B11 adds the following on top of B10:
1. Converts 8 TERMINAL to NO_PREDICTION when trajectory_confidence == LOW
2. Converts 53 DEGRADING to UNCERTAIN (not FAIL) — conservative design choice
3. Converts 38 DEGRADING to NO_PREDICTION when confidence == LOW
4. Retains 7 STABLE as HOLD

**B11 FAIL predictions are 100% sourced from zones with prior breakdown
(breakdown_count >= 1 in vt_prior):**

- FAIL predictions: 90 total
- From TERMINAL trajectory: 89
- From ACCELERATING_FAILURE: 1
- breakdown_count == 0: 0 (no FAIL prediction without prior breakdown)

B11 does not predict FAIL for zones without prior breakdowns, regardless of
structural deterioration severity. DEGRADING zones (no prior breakdowns, 95.9%
FAIL rate) are all excluded.

---

## 5. WHERE DOES THE 99% ACCURACY COME FROM?

### 5.1 Decomposition of the 306 evaluable cases

| Component | N | Accuracy | Mechanism |
|---|---|---|---|
| STRENGTHENING to HOLD (no prior breakdown) | 216 | 100% | Structural persistence: zones without breakdowns rarely first-break at visit N |
| TERMINAL to FAIL (prior breakdown) | 87 | 96.6% | Structural persistence: zones with breakdowns tend to continue breaking |
| STABLE to HOLD | 2 | 100% | Stable zones hold |
| ACCELERATING_FAILURE to FAIL | 1 | 100% | Single case |

### 5.2 Is the 100% HOLD rate for STRENGTHENING real or circular?

STRENGTHENING requires `breakdown_count == 0` from vt_prior (visits 1..N-1).
B12v2 HOLD outcome requires visit N result in {GROWTH, ABSORPTION, REFLECTION, RECLAIM}.
These are DIFFERENT conditions — not circular.

**The 100% is real**: 216 STRENGTHENING zones at their penultimate state had zero
BREAKDOWN events at visit N. First-time breakdowns almost never happen in a single
step after consistent growth — there is typically a deterioration phase (DEGRADING
trajectory) before the first breakdown. The 0 false HOLDs confirm this.

### 5.3 Is the 96.6% FAIL rate for TERMINAL real or circular?

TERMINAL requires `breakdown_count >= 1` from vt_prior (visits 1..N-1).
B12v2 FAIL outcome requires visit N result = BREAKDOWN.
These use DIFFERENT visits (N-1 vs N) — confirmed non-circular.

The 96.6% means: when a zone has already broken down at least once in its prior
history, there is a 96.6% chance it breaks again at visit N, and 3.4% chance it
recovers. This is a genuine structural persistence signal.

---

## 6. THE REAL ACCURACY VS SELECTIVITY TRADEOFF

### 6.1 Accuracy at different coverage levels

| Population | Coverage | Accuracy | Baseline | Lift |
|---|---|---|---|---|
| Evaluable (B12v2) | 67.8% | 99.0% | 72.2% | +26.8pp |
| If DEGRADING forced FAIL (adds 73) | ~84% | ~96.7% | ~70.7% | ~+26pp |
| If all 451 forced (best-guess) | 100% | ~84% | 72.2% | ~+12pp |

The high 99% accuracy is partially a consequence of excluding the most difficult
cases (DEGRADING and UNKNOWN). If the system were forced to predict on all 451
evaluable zones, accuracy would fall to approximately 84%.

### 6.2 The DEGRADING opportunity

91 DEGRADING zones (19% of eligible multi-visit zones) are entirely excluded:
- 70 eventually FAIL (95.9% FAIL rate on HOLD+FAIL subset)
- 3 eventually HOLD (4.1%)
- 18 AMBIGUOUS (DAMAGE final visit)

If B11 predicted FAIL for all DEGRADING zones:
- True positives: ~67 additional
- False positives: ~3 additional
- Precision: ~95.9%
- FAIL recall would rise from 52.5% to approximately 94%

B11's conservative UNCERTAIN/NO_PREDICTION for DEGRADING is an intentional
design choice that preserves high precision at the cost of recall.

---

## 7. TRUE PRACTICAL COVERAGE AND LIVE DEPLOYMENT IMPLICATIONS

### 7.1 What a live deployment would see per 100 multi-visit zones

- ~29 zones: HOLD prediction (all STRENGTHENING; 0 false HOLDs expected)
- ~19 zones: FAIL prediction (96.6% precision; ~1 false FAIL per 29 FAIL predictions)
- ~19 zones: UNCERTAIN — deterioration detected, verdict withheld
- ~24 zones: NO_PREDICTION — insufficient confidence
- ~9 zones: AMBIGUOUS visit N outcome (DAMAGE) — no verdict possible

**Effective action rate: ~48%** of zones reaching a second visit get actionable predictions.

### 7.2 The undetected FAIL risk

Of all 162 actual FAIL events at visit N:
- 85 detected (52.5% recall) — TERMINAL zones with FAIL prediction
- 48 missed as UNCERTAIN — DEGRADING zones (deterioration seen, verdict withheld)
- 29 missed as NO_PREDICTION — low-confidence zones (no prediction emitted)

**FAIL recall = 52.5%** — the system detects slightly more than half of actual failures.
**HOLD recall = 98.6%** — the system catches nearly all actual holds.

This asymmetry is the defining characteristic of the current B11 design:
- HOLD: over-detected (precision 100%, recall 98.6%)
- FAIL: under-detected (precision 96.6%, recall 52.5%)

---

## 8. SUMMARY: REAL PREDICTIVE POWER OR HIGH SELECTIVITY?

**Answer: BOTH, in different proportions.**

**Real predictive power (these results are genuine):**
- STRENGTHENING to HOLD persistence (216/216): genuine structural momentum
- TERMINAL to FAIL persistence (85/88): genuine structural continuation
- DEGRADING has 95.9% FAIL rate on excluded zones — the physics is detecting deterioration correctly, B11 is just not converting it to a FAIL prediction
- The 3 false FAILs are genuine recovery events (TERMINAL zones that recovered)
- Physics: sigma x penetration r=0.9978 confirms the mathematical foundation

**Selectivity contributing to the 99%:**
- 32.2% of evaluable cases excluded via UNCERTAIN/NO_PREDICTION
- Excluded cases include 77 undetected FAIL events (47.5% of all FAILs)
- If forced to predict on all 451 cases, accuracy would fall to ~84%
- The hardest cases — DEGRADING zones — are all excluded

**Practical coverage assessment:**
- Within covered cases: **precision is excellent** (99.0%)
- Across all eligible cases: **FAIL recall is moderate** (52.5%)
- In live deployment: **48% of zones receive actionable predictions**

---

## 9. GREEN FLAGS

- STRENGTHENING to HOLD persistence (216/216) is a genuine structural property, not circular
- TERMINAL to FAIL persistence (85/88) is a genuine semi-prospective signal, not circular
- DEGRADING zones (excluded) show 95.9% FAIL rate — the physics IS detecting structural deterioration correctly
- Physics core: sigma x penetration r=0.9978 confirmed on n=459
- Leakage assertion PASS (I(t) intersect O(t+1) = empty, verified with 0 violations)
- The 99% accuracy calculation is correct — no arithmetic errors
- The 3 false FAILs are interpretable (structural recovery events)
- UNKNOWN zones (64 cases, 63/64 HOLD outcomes) confirm NO_PREDICTION is appropriate for insufficient data

## 10. YELLOW FLAGS

- FAIL recall = 52.5% — system misses nearly half of actual failures
- 77 FAIL events undetected (48 UNCERTAIN + 29 NO_PREDICTION)
- DEGRADING zones (95.9% FAIL rate) are all excluded via UNCERTAIN/NO_PREDICTION — largest missed opportunity
- Coverage = 67.8% — 1 in 3 evaluable cases receives no prediction
- B11 FAIL is 100% sourced from prior breakdowns; ACCELERATING_FAILURE (true early-warning signal) has n=1
- First-breakdown early warning (predicting FAIL before any breakdown has occurred) is effectively untested
- Single 34-day period — regime generalizability unverified

## 11. RED FLAGS

- **FAIL recall 52.5%** is the critical practical limitation — nearly half of zone failures go unwarned
- B11 treats DEGRADING as UNCERTAIN despite 95.9% FAIL rate for those zones — conservative by design, but material missed signal
- The 99% accuracy headline requires context: it applies to 67.8% coverage only; the full-population number is ~84%

---

## 12. FINAL AUDIT STATUS

| Dimension | Result |
|---|---|
| Is the 99% accuracy mathematically correct? | YES |
| Is the 99% accuracy circular or artifact? | NO — leakage is eliminated |
| Does the 99% reflect genuine predictive power? | PARTIALLY — real signal + selectivity |
| What is true practical coverage? | 67.8% of evaluable, 65.1% of eligible |
| What is FAIL recall? | 52.5% — moderate |
| What is HOLD recall? | 98.6% — excellent |
| Does the system add value beyond naive baseline? | YES — +26.8pp lift on covered cases |
| Main limitation? | DEGRADING zones excluded; FAIL recall moderate |
| Would this work in live deployment? | Yes, with known limitations |

**FINAL AUDIT STATUS: PASS WITH MATERIAL CAVEATS**

The B12v2 result is valid and non-circular. The 99% accuracy is real for the
covered population. It must be read alongside the 67.8% coverage and 52.5% FAIL
recall to understand the full picture.

The system is a **high-precision, moderate-recall predictor**:
- It correctly identifies structural continuation with near-certainty
- It misses ~47% of FAIL events (DEGRADING zones excluded by conservative B11 design)
- Coverage is 67.8% — 1 in 3 evaluable zones gets no prediction

The Phase 1 architecture is validated. The structural physics correctly identifies
both structural persistence (STRENGTHENING to HOLD) and collapse continuation
(TERMINAL to FAIL). The primary development opportunity is DEGRADING zone coverage
— extending B11 to emit FAIL for DEGRADING zones would raise FAIL recall from
52.5% to approximately 94%, at the cost of approximately 3-4pp precision reduction.

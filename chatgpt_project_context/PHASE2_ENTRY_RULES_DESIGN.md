================================================================================
WEAKNESS ANALYSIS & CORRECTIVE FIXES — PHASE 1B+ (B12.5)
================================================================================
Based on: PHASE1B_B125_DYNAMIC_TIMELINE_STABLE (14,512 rows, 2,980 zones)
Target: PROBABLE_HOLD (657 cases, 56.5% FAIL) & STABLE trajectory (44.4% HOLD)
Action: Research-only recalibration. No RDM formula changes. No lifecycle changes.

================================================================================
1.  WEAKNESS #1 — PROBABLE_HOLD (56.5% FAIL)
================================================================================

ANALYSIS:
---------
PROBABLE_HOLD is the "grey zone" catch-all. It occurs when:
- zone_integral is moderate (not high enough for STRONG_HOLD).
- slope_medium is positive but weak (not strong enough to confirm trend).
- SDR is near 1.0 (zone and attacker forces are balanced).

This state is effectively a coin toss. Trading on it would produce
random results.

FIXES (apply in order):
-----------------------
1) RENAME: PROBABLE_HOLD → UNCERTAIN
   (Removes false confidence implied by "HOLD" in the name.)

2) DEADBAND: If 0.90 <= SDR <= 1.10 → FORCE UNCERTAIN
   (When zone_strength ≈ attacker_force, outcome is random.)

3) THRESHOLD LOCK: Only STRONG_HOLD and ATTACKER_DOMINANT
   are allowed to produce directional predictions (HOLD/FAIL).

RESULT:
-------
- PROBABLE_HOLD (657 cases) → reclassified as UNCERTAIN.
- Directional trades (HOLD/FAIL) are restricted to high-conviction zones only.
- Accuracy of remaining directional predictions remains at 99%+.

================================================================================
2.  WEAKNESS #2 — STABLE trajectory (44.4% HOLD, ALL False HOLDs)
================================================================================

ANALYSIS:
---------
STABLE trajectory means the zone is in equilibrium:
- No acceleration (second derivative near zero).
- No clear strengthening or degrading.
- The system lacks information about "intent" (only reads structure).

All recorded False HOLDs occurred exclusively in STABLE zones.
The model guesses "HOLD" based on weak structural signals, but the
attacker often breaks the equilibrium without warning.

FIXES (apply in order):
-----------------------
1) TEMPORARY BLOCK: Set ALL STABLE predictions to NO_PREDICTION
   until the zone exits STABLE (either to STRENGTHENING or DEGRADING).

2) VISIT MINIMUM: If visits_since_return < 3 → NO_PREDICTION
   (Require at least 3 post-return visits before evaluating STABLE.)

3) INTEGRAL TREND: For STABLE zones, require strict conditions:
   - integral must rise for 3 consecutive visits (slope_medium > threshold).
   - If integral is flat or falling → NO_PREDICTION.

RESULT:
-------
- False HOLDs eliminated (0% false HOLDs on STABLE).
- STABLE zones stop producing directional predictions entirely.
- They become "observation only" until stronger signals appear.

================================================================================
3.  FINAL FILTER RULES (Apply to ALL cases)
================================================================================

VALID PREDICTIONS (allowed in Phase 2 execution, when built):
--------------------------------------------------------------
STRONG_HOLD        → HOLD (100% historical accuracy)
ATTACKER_DOMINANT  → FAIL (99.6% historical accuracy)
RECOVERING         → FAIL (100% accuracy, n=26)
PEAK_WARNING       → FAIL (if used) (100% accuracy, n=40)
CRITICAL           → FAIL (if used) (100% accuracy, n=8)

INVALID PREDICTIONS (blocked / ignored):
----------------------------------------
PROBABLE_HOLD      → Reclassified as UNCERTAIN → NO_PREDICTION
STABLE (ANY)       → Forced to NO_PREDICTION
DEGRADING          → NO_PREDICTION (88.1% FAIL, but not 99%+)
UNCERTAIN          → NO_PREDICTION
NO_PREDICTION      → NO_PREDICTION (already safe)

Rule: If it's not 99%+ accurate in B12.5, it does NOT generate a
directional prediction. It becomes "observation only".

================================================================================
4.  CODE IMPLEMENTATION (Add to DynamicStateUpdater / zone_mechanics_calculator.py)
================================================================================
[FUTURE PHASE 2 REFERENCE — NOT IMPLEMENTED IN PHASE 1B+]

# ==================================================
# B12.5 FILTER & RECALIBRATION PATCH
# Applied after dynamic_state and SDR calculation.
# ==================================================

# 1. Constants
SDR_DEADBAND = 0.10   # +/- 10% around 1.0
MIN_VISITS_FOR_HOLD = 3
INTEGRAL_RISE_THRESHOLD = 0.02  # minimum slope for STABLE to consider HOLD

def apply_weakness_fixes(dynamic_state, trajectory, sdr, visits_since_return,
                         slope_medium, zone_integral):
    """
    Recalibrates weak states (PROBABLE_HOLD, STABLE) to UNCERTAIN / NO_PREDICTION.
    Returns: (final_state, final_prediction, confidence_override)
    """

    # --- FIX 1: RENAME PROBABLE_HOLD ---
    if dynamic_state == "PROBABLE_HOLD":
        dynamic_state = "UNCERTAIN"
        final_prediction = "NO_PREDICTION"
        confidence_override = 0.0
        return dynamic_state, final_prediction, confidence_override

    # --- FIX 2: SDR DEADBAND (Zone vs Attacker tie) ---
    if 1.0 - SDR_DEADBAND <= sdr <= 1.0 + SDR_DEADBAND:
        if dynamic_state in ["STABLE", "UNCERTAIN", "PROBABLE_HOLD"]:
            dynamic_state = "UNCERTAIN"
            final_prediction = "NO_PREDICTION"
            confidence_override = 0.0
            return dynamic_state, final_prediction, confidence_override

    # --- FIX 3: STABLE TRAJECTORY BLOCK ---
    if trajectory == "STABLE":
        if dynamic_state in ["STRONG_HOLD", "HOLD", "PROBABLE_HOLD"]:
            dynamic_state = "UNCERTAIN"
            final_prediction = "NO_PREDICTION"
            confidence_override = 0.0
            return dynamic_state, final_prediction, confidence_override

        if visits_since_return < MIN_VISITS_FOR_HOLD:
            dynamic_state = "UNCERTAIN"
            final_prediction = "NO_PREDICTION"
            confidence_override = 0.0
            return dynamic_state, final_prediction, confidence_override

        if slope_medium < INTEGRAL_RISE_THRESHOLD:
            dynamic_state = "UNCERTAIN"
            final_prediction = "NO_PREDICTION"
            confidence_override = 0.0
            return dynamic_state, final_prediction, confidence_override

        final_prediction = "NO_PREDICTION"
        confidence_override = 0.0
        return dynamic_state, final_prediction, confidence_override

    # --- FIX 4: ENFORCE 99%+ ONLY ---
    if dynamic_state == "STRONG_HOLD":
        final_prediction = "HOLD"
        confidence_override = 100.0
    elif dynamic_state == "ATTACKER_DOMINANT":
        final_prediction = "FAIL"
        confidence_override = 99.6
    elif dynamic_state == "RECOVERING":
        final_prediction = "FAIL"
        confidence_override = 100.0  # 100% accuracy (n=26)
    elif dynamic_state == "PEAK_WARNING" or dynamic_state == "CRITICAL":
        final_prediction = "FAIL"
        confidence_override = 100.0  # 100% accuracy (n=40, n=8)
    else:
        final_prediction = "NO_PREDICTION"
        confidence_override = 0.0

    return dynamic_state, final_prediction, confidence_override

================================================================================
SUMMARY OF CHANGES
================================================================================
Original State        | New State    | New Prediction  | Reason
PROBABLE_HOLD          | UNCERTAIN    | NO_PREDICTION    | 56.5% FAIL rate -> coin toss
STABLE (any)           | UNCERTAIN*   | NO_PREDICTION    | Source of all False HOLDs
DEGRADING              | DEGRADING    | NO_PREDICTION    | 88% accurate, but not 99%+
STRONG_HOLD            | STRONG_HOLD  | HOLD             | 100% accurate (743 cases)
ATTACKER_DOMINANT      | ATTACKER_DOMINANT | FAIL        | 99.6% accurate (528 cases)
RECOVERING             | RECOVERING   | FAIL             | 100% accurate (26 cases)
PEAK_WARNING/CRITICAL  | PEAK_WARNING/CRITICAL | FAIL    | 100% accurate (40+8 cases)
*STABLE may remain STABLE in research logs, but its prediction is forced to NO_PREDICTION.

================================================================================
PHASE 2 ENTRY RULES (future implementation)
================================================================================
When Phase 2 (Execution Engine) is built, these are the only allowed signals:

ENTRY (LONG):
  dynamic_state == "STRONG_HOLD" AND trajectory != "STABLE"

ENTRY (SHORT) / EXIT:
  dynamic_state in ["ATTACKER_DOMINANT", "PEAK_WARNING", "CRITICAL", "RECOVERING"]

NEVER ENTRY / BLOCK:
  dynamic_state in ["UNCERTAIN", "NO_PREDICTION", "DEGRADING"]
  trajectory == "STABLE"
  SDR in DEADBAND (0.9-1.1)

These rules ensure that live execution only uses the 99%+ accuracy tiers.
All grey zones become observation-only research material.

================================================================================
EXPECTED IMPACT ON ACCURACY
================================================================================
Before fix (B12.5): 86.6% overall accuracy, 56.5% FAIL on PROBABLE_HOLD
After fix: Directional predictions (HOLD/FAIL) remain at 99%+ accuracy.
PROBABLE_HOLD and STABLE are removed from decision space.
Effective "Tradable Accuracy" = 99.6% (on filtered signal set).
Filtered-out cases become "observation only" until more data.
This reduces the number of actionable signals (fewer entries) but ensures
every actionable signal is highly reliable. Quality over quantity.

================================================================================
STATUS: DESIGN DOCUMENT ONLY — NOT IMPLEMENTED.
This describes Phase 2 (Execution Engine) rules. Phase 1B+ remains
research-only. No code in zone_mechanics_calculator.py implements
apply_weakness_fixes() yet. This is a reference for when Phase 2 begins.
================================================================================
End of weakness analysis and fixes.

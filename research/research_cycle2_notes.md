# Phase 1B Research Cycle 2 Notes

- Run UTC: 2026-05-25T16:30:17+00:00
- Scope: Score 4 / Score 5 / Score 6 only
- Mode: Observation research only
- No live signals, no execution, no scoring changes, no Phase 2

## Summary
- Cases reviewed: 12
- Preparation candidates: 4
- Return to preparation: 4
- Promising expansion/context patterns: 3
- False/noisy patterns: 9

## Score Comparison
- SCORE_4: cases=10, pure_expansion=2, expansion_then_reversal=1, direct_reversal=6, failed_expansion=1, avg_max_abs_move_4h=462.239
- SCORE_5: cases=1, pure_expansion=0, expansion_then_reversal=0, direct_reversal=1, failed_expansion=0, avg_max_abs_move_4h=174.68
- SCORE_6: cases=1, pure_expansion=0, expansion_then_reversal=0, direct_reversal=1, failed_expansion=0, avg_max_abs_move_4h=1120.45

## Promising Preparation / Expansion Patterns
- CASE_00015: SCORE_4 / DELTA_ZSCORE_EXTREME / PURE_EXPANSION / MOMENTUM_PRECURSOR
- CASE_00036: SCORE_4 / DELTA_ZSCORE_EXTREME / PURE_EXPANSION / REVERSAL_WARNING
- CASE_00002: SCORE_4 / DELTA_ZSCORE_EXTREME / EXPANSION_THEN_REVERSAL / CONTEXT_ONLY

## False / Noise Patterns
- CASE_00021: SCORE_6 / DELTA_ZSCORE_EXTREME / DIRECT_REVERSAL / DIRECT_REVERSAL / REVERSAL_WARNING
- CASE_00045: SCORE_4 / DELTA_ZSCORE_EXTREME / DIRECT_REVERSAL / FAILED_RETURN_REVERSAL / REVERSAL_WARNING
- CASE_00041: SCORE_4 / DELTA_ZSCORE_EXTREME / DIRECT_REVERSAL / FAILED_RETURN_REVERSAL / ACCUMULATION
- CASE_00018: SCORE_4 / MULTI_ZSCORE_CONTEXT / DIRECT_REVERSAL / UNKNOWN_DIRECTION_REVERSAL / REVERSAL_WARNING
- CASE_00035: SCORE_4 / UNSTABLE_EXTREME_CONTEXT / DIRECT_REVERSAL / FAILED_RETURN_REVERSAL / REVERSAL_WARNING

## Research Interpretation
- Score 4 has the largest sample in the current research log and contains both expansion and reversal/noise cases.
- Score 5 and Score 6 are too sparse in this file set for strong conclusions.
- Preparation candidates that return to preparation still require manual chart review because return can precede expansion or failed-return reversal.
- HYPOTHESIS_01 remains unproven.


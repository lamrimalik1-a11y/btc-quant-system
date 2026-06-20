# Zone Mechanics Capacity Notes

- Run UTC: 2026-06-16T22:03:16+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Capacity State Counts
- SAFE: 2149
- WARNING: 853
- ELU_LIMIT: 1292
- HIGH_LOAD: 555
- ELS_LIMIT: 10

## Dynamic ELU State Counts
- ELS_SAFE: 1882
- WARNING: 853
- ELU_LIMIT: 1294
- HIGH_LOAD: 555
- SAFE: 267
- ELS_LIMIT: 8

## Mechanical Regime Context Counts
- NORMAL_CONTEXT: 3009
- RECOVERY_CONTEXT: 372
- EXPANSION_EXHAUSTION_CONTEXT: 1478

## Capacity Calibration State Counts
- NO_ACTIVE_LOAD_PROTECTED: 1882
- RECOVERY_PROTECTED: 1683
- EXPANSION_PROTECTED: 1294

## Interpretation
- M_applied is represented by mechanical_load_score.
- M_capacity is represented by remaining zone moment capacity.
- Capacity ratio = M_applied / M_capacity.
- Regime-adjusted capacity applies context-only volatility and recovery multipliers.
- Adaptive capacity threshold is the failure threshold after regime calibration.
- Dynamic ELU combines capacity ratio, fatigue, residual strength, and strength decay.

Research-only note: capacity states are not live signals and do not affect scoring.

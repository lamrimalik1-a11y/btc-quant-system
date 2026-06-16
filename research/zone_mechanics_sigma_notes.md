# Zone Mechanics Sigma Barre Notes

- Run UTC: 2026-06-16T07:33:07+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Sigma State Counts
- SAFE_STRESS: 2239
- ELU_STRESS_CRITICAL: 1311
- SIGMA_RUPTURE_RISK: 1218
- ELS_STRESS_WARNING: 91

## Sigma Failure Risk Counts
- NONE: 2239
- MEDIUM: 1323
- HIGH: 1206
- LOW: 91

## Interpretation
- sigma_barre_zone is the per-zone allowable stress proxy.
- sigma_market is the observed research stress proxy.
- stress_utilization = sigma_market / sigma_barre_zone.
- Volatility modifier raises allowable stress during high-volatility context.
- Fatigue factor lowers allowable stress as lifecycle decay accumulates.

Research-only note: sigma states are not live signals and do not affect scoring.

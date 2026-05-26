# Zone Mechanics Sigma Barre Notes

- Run UTC: 2026-05-26T21:44:45+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Sigma State Counts
- SAFE_STRESS: 9
- SIGMA_RUPTURE_RISK: 1
- ELU_STRESS_CRITICAL: 2

## Sigma Failure Risk Counts
- NONE: 9
- HIGH: 1
- MEDIUM: 2

## Interpretation
- sigma_barre_zone is the per-zone allowable stress proxy.
- sigma_market is the observed research stress proxy.
- stress_utilization = sigma_market / sigma_barre_zone.
- Volatility modifier raises allowable stress during high-volatility context.
- Fatigue factor lowers allowable stress as lifecycle decay accumulates.

Research-only note: sigma states are not live signals and do not affect scoring.

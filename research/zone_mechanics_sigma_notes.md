# Zone Mechanics Sigma Barre Notes

- Run UTC: 2026-06-02T22:36:36+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Sigma State Counts
- SAFE_STRESS: 24
- ELU_STRESS_CRITICAL: 17
- ELS_STRESS_WARNING: 2
- SIGMA_RUPTURE_RISK: 7

## Sigma Failure Risk Counts
- NONE: 24
- MEDIUM: 20
- LOW: 2
- HIGH: 4

## Interpretation
- sigma_barre_zone is the per-zone allowable stress proxy.
- sigma_market is the observed research stress proxy.
- stress_utilization = sigma_market / sigma_barre_zone.
- Volatility modifier raises allowable stress during high-volatility context.
- Fatigue factor lowers allowable stress as lifecycle decay accumulates.

Research-only note: sigma states are not live signals and do not affect scoring.

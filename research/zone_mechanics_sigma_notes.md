# Zone Mechanics Sigma Barre Notes

- Run UTC: 2026-05-28T09:01:30+00:00
- Mode: Research only
- No live signals
- No execution
- No Dashboard V2 scoring changes
- No Phase 2

## Sigma State Counts
- SAFE_STRESS: 19
- ELU_STRESS_CRITICAL: 4
- SIGMA_RUPTURE_RISK: 2

## Sigma Failure Risk Counts
- NONE: 19
- MEDIUM: 4
- HIGH: 2

## Interpretation
- sigma_barre_zone is the per-zone allowable stress proxy.
- sigma_market is the observed research stress proxy.
- stress_utilization = sigma_market / sigma_barre_zone.
- Volatility modifier raises allowable stress during high-volatility context.
- Fatigue factor lowers allowable stress as lifecycle decay accumulates.

Research-only note: sigma states are not live signals and do not affect scoring.

# Zone Mechanics Sigma Evolution Notes

- Run UTC: 2026-05-27T12:38:05+00:00
- Mode: Research only
- No live signals
- No execution
- No entries
- No Dashboard V2 scoring changes
- No Phase 2

## Sigma Memory State Counts
- FRESH_SIGMA: 12
- FATIGUED_SIGMA: 10
- CRITICAL_SIGMA: 2
- REPAIRED_SIGMA: 1
- INSTITUTIONAL_SIGMA: 2

## Interpretation
- Sigma evolution extends sigma_barre_zone with age, tests, repair cycles, and memory.
- adaptive_sigma_barre_v2 = sigma_barre_zone * memory_multiplier * repair_multiplier / aging_penalty.
- Recovered and reclaimed zones can gain repair bonus.
- Old, repeatedly tested, or fatigued zones lose allowable stress through sigma_age_factor.

Research-only note: sigma memory states are not live signals and do not affect scoring.

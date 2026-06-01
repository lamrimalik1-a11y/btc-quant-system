# Zone Mechanics Sigma Evolution Notes

- Run UTC: 2026-06-01T12:03:18+00:00
- Mode: Research only
- No live signals
- No execution
- No entries
- No Dashboard V2 scoring changes
- No Phase 2

## Sigma Memory State Counts
- FRESH_SIGMA: 296
- REPAIRED_SIGMA: 45
- FATIGUED_SIGMA: 277
- AGED_SIGMA: 1
- INSTITUTIONAL_SIGMA: 15

## Interpretation
- Sigma evolution extends sigma_barre_zone with age, tests, repair cycles, and memory.
- adaptive_sigma_barre_v2 = sigma_barre_zone * memory_multiplier * repair_multiplier / aging_penalty.
- Recovered and reclaimed zones can gain repair bonus.
- Old, repeatedly tested, or fatigued zones lose allowable stress through sigma_age_factor.

Research-only note: sigma memory states are not live signals and do not affect scoring.

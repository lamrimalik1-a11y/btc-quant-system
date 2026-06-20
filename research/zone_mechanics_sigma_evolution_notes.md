# Zone Mechanics Sigma Evolution Notes

- Run UTC: 2026-06-16T22:03:16+00:00
- Mode: Research only
- No live signals
- No execution
- No entries
- No Dashboard V2 scoring changes
- No Phase 2

## Sigma Memory State Counts
- FRESH_SIGMA: 1874
- REPAIRED_SIGMA: 372
- FATIGUED_SIGMA: 2520
- INSTITUTIONAL_SIGMA: 88
- AGED_SIGMA: 5

## Interpretation
- Sigma evolution extends sigma_barre_zone with age, tests, repair cycles, and memory.
- adaptive_sigma_barre_v2 = sigma_barre_zone * memory_multiplier * repair_multiplier / aging_penalty.
- Recovered and reclaimed zones can gain repair bonus.
- Old, repeatedly tested, or fatigued zones lose allowable stress through sigma_age_factor.

Research-only note: sigma memory states are not live signals and do not affect scoring.

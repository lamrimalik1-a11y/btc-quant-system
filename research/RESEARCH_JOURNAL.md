
==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-24 19:32:00
Replay window: 2026-05-24
Mode: candidates
Episodes analyzed: 20
Research candidates: 20

Classification counts:
- MOMENTUM_PRECURSOR: 1
- ACCELERATION_ZONE: 1
- PRE_EXPANSION: 2
- CONTEXT_ONLY: 6
- REVERSAL_WARNING: 7
- ACCUMULATION: 1
- ABSORPTION: 0
- FAILED_CONTEXT: 2
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00021 | episode_id=21 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1120.45
- CASE_00008 | episode_id=8 | classification=ACCELERATION_ZONE | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=754.36
- CASE_00023 | episode_id=23 | classification=REVERSAL_WARNING | layers=2 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=680.84
- CASE_00015 | episode_id=15 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=606.51
- CASE_00018 | episode_id=18 | classification=REVERSAL_WARNING | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=552.93

Counterexamples:
- CASE_00030 | episode_id=30 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=316.6
- CASE_00029 | episode_id=29 | classification=FAILED_CONTEXT | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=306.59

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B+ RDM MARKET MECHANICS V1.4 CHECKPOINT
==================================================

Status:
VALIDATED CHECKPOINT

Added after V1.3:
- RDM Result Layer
- Final Dashboard Result Block
- Zone Status Interpretation
- Health Score
- Risk Level
- Confidence Layer
- Short Reason
- Watch Action
- Section Result Summaries

New fields:
- rdm_zone_status
- rdm_health_score
- rdm_risk_level
- rdm_confidence
- rdm_short_reason
- rdm_watch_action

Current counts:
- DORMANT = 11
- FATIGUED = 10
- EXHAUSTED = 3
- RUPTURED = 2
- RECOVERING = 1

Dashboard structure:
- Layer 1 = Final Result
- Layer 2 = Deep Mechanics
- Final result states = Alive, Recovering, Fatigued, Critical, Exhausted, Ruptured, Dead, Dormant
- Deep mechanics = Family, Subtype, Fleche, Moment, Sigma, Capacity, Memory, Evolution, Death

Rules:
- Research only
- Observation only
- No Phase 2
- No execution
- No entries
- No live signals
- No scoring changes
- No Dashboard V2 scoring changes
- Mechanics-first
- Cases reference-only

Next step:
- Observation / Calibration
- Replay validation
- Historical validation
- False positive review
- Live observation
- DO NOT ADVANCE PHASES


==================================================
PHASE 1B+ RDM MARKET MECHANICS V1.3 CHECKPOINT
==================================================

Run UTC: 2026-05-27
Status: VALIDATED
Mode: Research only

Included:
- Adaptive Sigma
- Sigma Aging
- Mechanical Capacity
- Verestchaguine Dynamic Fleche
- Zero Stress Protection
- Dormant Preparation
- Birth Registry
- Death Registry
- Mechanical Memory
- Birth Calibration
- Zone Evolution Chart
- Binance historical downloader robustness

Validation summary:
- ELASTIC_FAMILY = 11
- FATIGUE_FAMILY = 10
- EXHAUSTION_FAMILY = 3
- RUPTURE_FAMILY = 2
- RECOVERY_FAMILY = 1
- RIGID_ZONE = 11
- FATIGUE_ZONE = 10
- EXHAUSTED_ZONE = 3
- RUPTURE_ZONE = 2
- RECOVERED_ZONE = 1
- SAFE = 12
- WARNING = 7
- ELU_LIMIT = 3
- CAPACITY_FAILURE = 2
- HIGH_LOAD = 2
- ELS_LIMIT = 1
- RIGID_BIRTH = 8
- ELASTIC_BIRTH = 7
- EXPANSION_BIRTH = 5
- INSTITUTIONAL_BIRTH = 3
- UNKNOWN_BIRTH = 4
- DORMANT_EXPIRED = 11
- RUPTURE = 11
- EXHAUSTION = 3
- RECOVERY_COMPLETE = 1
- FATIGUE = 1

Artifacts:
- Birth rows = 27
- Death rows = 27
- Memory zones = 27
- Evolution rows = 27
- Evolution history = 139
- Lifecycle rows = 89

Downloader robustness:
- timeout = 120 seconds
- retry = 10
- exponential backoff
- checkpoint
- resume
- partial aggTrades persistence

Rules:
- Research only
- No Phase 2
- No execution
- No entries
- No live signals
- No scoring changes
- Mechanics-first
- Cases reference-only

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-24 19:36:45
Replay window: 2026-05-24
Mode: candidates
Episodes analyzed: 20
Research candidates: 20

Classification counts:
- MOMENTUM_PRECURSOR: 1
- ACCELERATION_ZONE: 1
- PRE_EXPANSION: 2
- CONTEXT_ONLY: 6
- REVERSAL_WARNING: 7
- ACCUMULATION: 1
- ABSORPTION: 0
- FAILED_CONTEXT: 2
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00021 | episode_id=21 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1120.45
- CASE_00008 | episode_id=8 | classification=ACCELERATION_ZONE | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=754.36
- CASE_00023 | episode_id=23 | classification=REVERSAL_WARNING | layers=2 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=680.84
- CASE_00015 | episode_id=15 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=606.51
- CASE_00018 | episode_id=18 | classification=REVERSAL_WARNING | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=552.93

Counterexamples:
- CASE_00030 | episode_id=30 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=316.6
- CASE_00029 | episode_id=29 | classification=FAILED_CONTEXT | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=306.59

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-24 19:36:53
Replay window: 2026-05-24
Mode: all
Episodes analyzed: 40
Research candidates: 20

Classification counts:
- MOMENTUM_PRECURSOR: 11
- ACCELERATION_ZONE: 2
- PRE_EXPANSION: 2
- CONTEXT_ONLY: 9
- REVERSAL_WARNING: 12
- ACCUMULATION: 2
- ABSORPTION: 0
- FAILED_CONTEXT: 2
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00021 | episode_id=21 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1120.45
- CASE_00022 | episode_id=22 | classification=CONTEXT_ONLY | layers=2 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=968.71
- CASE_00020 | episode_id=20 | classification=ACCELERATION_ZONE | layers=2 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=783.8
- CASE_00011 | episode_id=11 | classification=MOMENTUM_PRECURSOR | layers=3 | context=COMPRESSION_REGIME_TO_LOW_VOLATILITY | max_abs_4h=772.93
- CASE_00008 | episode_id=8 | classification=ACCELERATION_ZONE | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=754.36

Counterexamples:
- CASE_00030 | episode_id=30 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=316.6
- CASE_00029 | episode_id=29 | classification=FAILED_CONTEXT | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=306.59

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-24 19:39:25
Replay window: 2026-05-24
Mode: all
Episodes analyzed: 40
Research candidates: 20

Classification counts:
- MOMENTUM_PRECURSOR: 11
- ACCELERATION_ZONE: 2
- PRE_EXPANSION: 2
- CONTEXT_ONLY: 9
- REVERSAL_WARNING: 12
- ACCUMULATION: 2
- ABSORPTION: 0
- FAILED_CONTEXT: 2
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00021 | episode_id=21 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1120.45
- CASE_00022 | episode_id=22 | classification=CONTEXT_ONLY | layers=2 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=968.71
- CASE_00020 | episode_id=20 | classification=ACCELERATION_ZONE | layers=2 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=783.8
- CASE_00011 | episode_id=11 | classification=MOMENTUM_PRECURSOR | layers=3 | context=COMPRESSION_REGIME_TO_LOW_VOLATILITY | max_abs_4h=772.93
- CASE_00008 | episode_id=8 | classification=ACCELERATION_ZONE | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=754.36

Counterexamples:
- CASE_00030 | episode_id=30 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=316.6
- CASE_00029 | episode_id=29 | classification=FAILED_CONTEXT | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=306.59

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-24 20:01:17
Replay window: 2026-05-24
Mode: score4plus
Episodes total: 40
Episodes analyzed: 9
Score >= 4 episodes: 9
Research candidates: 9

Classification counts:
- MOMENTUM_PRECURSOR: 1
- ACCELERATION_ZONE: 0
- PRE_EXPANSION: 0
- CONTEXT_ONLY: 2
- REVERSAL_WARNING: 4
- ACCUMULATION: 1
- ABSORPTION: 0
- FAILED_CONTEXT: 1
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00021 | episode_id=21 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1120.45
- CASE_00015 | episode_id=15 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=606.51
- CASE_00018 | episode_id=18 | classification=REVERSAL_WARNING | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=552.93
- CASE_00035 | episode_id=35 | classification=REVERSAL_WARNING | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=409.89
- CASE_00006 | episode_id=6 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=365.76

Counterexamples:
- CASE_00030 | episode_id=30 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=316.6

Preparation zone summary:
- Preparation zones found: 0
- MOMENTUM_PRECURSOR with preparation: 0
- REVERSAL_WARNING with preparation: 0
- FAILED_CONTEXT with preparation: 0
- PRE_EXPANSION with preparation: 0

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-24 21:32:18
Replay window: 2026-05-24
Mode: score4plus
Episodes total: 40
Episodes analyzed: 9
Score >= 4 episodes: 9
Research candidates: 9

Classification counts:
- MOMENTUM_PRECURSOR: 1
- ACCELERATION_ZONE: 0
- PRE_EXPANSION: 0
- CONTEXT_ONLY: 2
- REVERSAL_WARNING: 4
- ACCUMULATION: 1
- ABSORPTION: 0
- FAILED_CONTEXT: 1
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00021 | episode_id=21 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1120.45
- CASE_00015 | episode_id=15 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=606.51
- CASE_00018 | episode_id=18 | classification=REVERSAL_WARNING | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=552.93
- CASE_00035 | episode_id=35 | classification=REVERSAL_WARNING | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=409.89
- CASE_00006 | episode_id=6 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=365.76

Counterexamples:
- CASE_00030 | episode_id=30 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=316.6

Preparation zone summary:
- Preparation candidates: 2
- Preparation zones found: 2
- HIGH preparation count: 0
- EXTREME preparation count: 2
- MOMENTUM_PRECURSOR with preparation: 0
- REVERSAL_WARNING with preparation: 2
- FAILED_CONTEXT with preparation: 0
- PRE_EXPANSION with preparation: 0

HYPOTHESIS_02 revisit summary:
- Return count: 2
- Return success count: 2
- Return failure count: 0
- Agreement true: 2
- Agreement false: 6
- Agreement unknown: 1
- High expansion count: 4
- Extreme expansion count: 3
- Average quiet score: 78.55555556
- Average range ratio: 0.72753143
- Best preparation cases: CASE_00035|CASE_00036
- Failed preparation cases: 

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-24 22:02:31
Replay window: 2026-05-24
Mode: score4plus
Episodes total: 40
Episodes analyzed: 9
Score >= 4 episodes: 9
Research candidates: 9

Classification counts:
- MOMENTUM_PRECURSOR: 1
- ACCELERATION_ZONE: 0
- PRE_EXPANSION: 0
- CONTEXT_ONLY: 2
- REVERSAL_WARNING: 4
- ACCUMULATION: 1
- ABSORPTION: 0
- FAILED_CONTEXT: 1
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00021 | episode_id=21 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1120.45
- CASE_00015 | episode_id=15 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=606.51
- CASE_00018 | episode_id=18 | classification=REVERSAL_WARNING | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=552.93
- CASE_00035 | episode_id=35 | classification=REVERSAL_WARNING | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=409.89
- CASE_00006 | episode_id=6 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=365.76

Counterexamples:
- CASE_00030 | episode_id=30 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=316.6

Preparation zone summary:
- Preparation candidates: 2
- Preparation zones found: 2
- HIGH preparation count: 0
- EXTREME preparation count: 2
- MOMENTUM_PRECURSOR with preparation: 0
- REVERSAL_WARNING with preparation: 2
- FAILED_CONTEXT with preparation: 0
- PRE_EXPANSION with preparation: 0

HYPOTHESIS_02 revisit summary:
- Return count: 2
- Return success count: 2
- Return failure count: 0
- Agreement true: 2
- Agreement false: 6
- Agreement unknown: 1
- High expansion count: 4
- Extreme expansion count: 3
- Average quiet score: 78.55555556
- Average range ratio: 0.72753143
- Best preparation cases: CASE_00035|CASE_00036
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 5
- Late reversals: 2
- Reversal after preparation return: 1
- Failed after return: 1
- HIGH reversal count: 3
- EXTREME reversal count: 2
- Average time to reversal: 23.39486905

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-24 22:21:13
Replay window: 2026-05-24
Mode: score4plus
Episodes total: 40
Episodes analyzed: 9
Score >= 4 episodes: 9
Research candidates: 9

Classification counts:
- MOMENTUM_PRECURSOR: 1
- ACCELERATION_ZONE: 0
- PRE_EXPANSION: 0
- CONTEXT_ONLY: 2
- REVERSAL_WARNING: 4
- ACCUMULATION: 1
- ABSORPTION: 0
- FAILED_CONTEXT: 1
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00021 | episode_id=21 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1120.45
- CASE_00015 | episode_id=15 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=606.51
- CASE_00018 | episode_id=18 | classification=REVERSAL_WARNING | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=552.93
- CASE_00035 | episode_id=35 | classification=REVERSAL_WARNING | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=409.89
- CASE_00006 | episode_id=6 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=365.76

Counterexamples:
- CASE_00030 | episode_id=30 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=316.6

Preparation zone summary:
- Preparation candidates: 2
- Preparation zones found: 2
- HIGH preparation count: 0
- EXTREME preparation count: 2
- MOMENTUM_PRECURSOR with preparation: 0
- REVERSAL_WARNING with preparation: 2
- FAILED_CONTEXT with preparation: 0
- PRE_EXPANSION with preparation: 0

HYPOTHESIS_02 revisit summary:
- Return count: 2
- Return success count: 2
- Return failure count: 0
- Agreement true: 2
- Agreement false: 6
- Agreement unknown: 1
- High expansion count: 1
- Extreme expansion count: 1
- Average quiet score: 78.55555556
- Average range ratio: 0.72753143
- Best preparation cases: CASE_00035|CASE_00036
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 5
- Late reversals: 2
- Reversal after preparation return: 1
- Failed after return: 1
- HIGH reversal count: 3
- EXTREME reversal count: 2
- Average time to reversal: 23.39486905

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 2
- Expansion then reversal: 1
- Failed expansions: 1
- Direct reversals: 5
- Average expansion strength: 1.66666667
- Average expansion to reversal ratio: 26.00944013

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-24 22:30:12
Replay window: 2026-05-24
Mode: score4plus
Episodes total: 40
Episodes analyzed: 9
Score >= 4 episodes: 9
Research candidates: 9

Classification counts:
- MOMENTUM_PRECURSOR: 1
- ACCELERATION_ZONE: 0
- PRE_EXPANSION: 0
- CONTEXT_ONLY: 2
- REVERSAL_WARNING: 4
- ACCUMULATION: 1
- ABSORPTION: 0
- FAILED_CONTEXT: 1
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00021 | episode_id=21 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1120.45
- CASE_00015 | episode_id=15 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=606.51
- CASE_00018 | episode_id=18 | classification=REVERSAL_WARNING | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=552.93
- CASE_00035 | episode_id=35 | classification=REVERSAL_WARNING | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=409.89
- CASE_00006 | episode_id=6 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=365.76

Counterexamples:
- CASE_00030 | episode_id=30 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=316.6

Preparation zone summary:
- Preparation candidates: 2
- Preparation zones found: 2
- HIGH preparation count: 0
- EXTREME preparation count: 2
- MOMENTUM_PRECURSOR with preparation: 0
- REVERSAL_WARNING with preparation: 2
- FAILED_CONTEXT with preparation: 0
- PRE_EXPANSION with preparation: 0

HYPOTHESIS_02 revisit summary:
- Return count: 2
- Return success count: 2
- Return failure count: 0
- Agreement true: 2
- Agreement false: 6
- Agreement unknown: 1
- High expansion count: 1
- Extreme expansion count: 1
- Average quiet score: 78.55555556
- Average range ratio: 0.72753143
- Best preparation cases: CASE_00035|CASE_00036
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 5
- Late reversals: 2
- Reversal after preparation return: 1
- Failed after return: 1
- HIGH reversal count: 3
- EXTREME reversal count: 2
- Average time to reversal: 23.39486905

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 2
- Expansion then reversal: 1
- Failed expansions: 1
- Direct reversals: 5
- Average expansion strength: 1.66666667
- Average expansion to reversal ratio: 26.00944013

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-25 08:37:06
Replay window: 2026-05-24
Mode: score4plus
Episodes total: 57
Episodes analyzed: 12
Score >= 4 episodes: 12
Research candidates: 12

Classification counts:
- MOMENTUM_PRECURSOR: 1
- ACCELERATION_ZONE: 0
- PRE_EXPANSION: 0
- CONTEXT_ONLY: 2
- REVERSAL_WARNING: 5
- ACCUMULATION: 2
- ABSORPTION: 0
- FAILED_CONTEXT: 2
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00021 | episode_id=21 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1120.45
- CASE_00045 | episode_id=45 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=927.51
- CASE_00015 | episode_id=15 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=606.51
- CASE_00041 | episode_id=41 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=587.67
- CASE_00018 | episode_id=18 | classification=REVERSAL_WARNING | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=552.93

Counterexamples:
- CASE_00030 | episode_id=30 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=316.6
- CASE_00050 | episode_id=50 | classification=FAILED_CONTEXT | layers=4 | context=EXTREME_VELOCITY_EXHAUSTION | max_abs_4h=294.15

Preparation zone summary:
- Preparation candidates: 4
- Preparation zones found: 4
- HIGH preparation count: 0
- EXTREME preparation count: 3
- MOMENTUM_PRECURSOR with preparation: 0
- REVERSAL_WARNING with preparation: 3
- FAILED_CONTEXT with preparation: 0
- PRE_EXPANSION with preparation: 0

HYPOTHESIS_02 revisit summary:
- Return count: 4
- Return success count: 4
- Return failure count: 0
- Agreement true: 2
- Agreement false: 9
- Agreement unknown: 1
- High expansion count: 1
- Extreme expansion count: 2
- Average quiet score: 79.75
- Average range ratio: 0.69654197
- Best preparation cases: CASE_00045|CASE_00041|CASE_00035|CASE_00036
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 8
- Late reversals: 2
- Reversal after preparation return: 2
- Failed after return: 3
- HIGH reversal count: 4
- EXTREME reversal count: 4
- Average time to reversal: 16.77462333

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 2
- Expansion then reversal: 1
- Failed expansions: 1
- Direct reversals: 8
- Average expansion strength: 1.83333333
- Average expansion to reversal ratio: 19.07336607

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-25 16:50:36
Replay window: 2026-05-24
Mode: score4plus
Episodes total: 57
Episodes analyzed: 12
Score >= 4 episodes: 12
Research candidates: 12

Classification counts:
- MOMENTUM_PRECURSOR: 1
- ACCELERATION_ZONE: 0
- PRE_EXPANSION: 0
- CONTEXT_ONLY: 2
- REVERSAL_WARNING: 5
- ACCUMULATION: 2
- ABSORPTION: 0
- FAILED_CONTEXT: 2
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00021 | episode_id=21 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1120.45
- CASE_00045 | episode_id=45 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=927.51
- CASE_00015 | episode_id=15 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=606.51
- CASE_00041 | episode_id=41 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=587.67
- CASE_00018 | episode_id=18 | classification=REVERSAL_WARNING | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=552.93

Counterexamples:
- CASE_00030 | episode_id=30 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=316.6
- CASE_00050 | episode_id=50 | classification=FAILED_CONTEXT | layers=4 | context=EXTREME_VELOCITY_EXHAUSTION | max_abs_4h=294.15

Preparation zone summary:
- Preparation candidates: 4
- Preparation zones found: 4
- HIGH preparation count: 0
- EXTREME preparation count: 3
- MOMENTUM_PRECURSOR with preparation: 0
- REVERSAL_WARNING with preparation: 3
- FAILED_CONTEXT with preparation: 0
- PRE_EXPANSION with preparation: 0

HYPOTHESIS_02 revisit summary:
- Return count: 4
- Return success count: 4
- Return failure count: 0
- Agreement true: 2
- Agreement false: 9
- Agreement unknown: 1
- High expansion count: 1
- Extreme expansion count: 2
- Average quiet score: 79.75
- Average range ratio: 0.69654197
- Best preparation cases: CASE_00045|CASE_00041|CASE_00035|CASE_00036
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 8
- Late reversals: 2
- Reversal after preparation return: 2
- Failed after return: 3
- HIGH reversal count: 4
- EXTREME reversal count: 4
- Average time to reversal: 16.77462333

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 2
- Expansion then reversal: 1
- Failed expansions: 1
- Direct reversals: 8
- Average expansion strength: 1.83333333
- Average expansion to reversal ratio: 19.07336607

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-27 00:00:42
Replay window: 2026-05-26
Mode: score4plus
Episodes total: 101
Episodes analyzed: 27
Score >= 4 episodes: 27
Research candidates: 27

Classification counts:
- MOMENTUM_PRECURSOR: 4
- ACCELERATION_ZONE: 0
- PRE_EXPANSION: 2
- CONTEXT_ONLY: 6
- REVERSAL_WARNING: 6
- ACCUMULATION: 7
- ABSORPTION: 0
- FAILED_CONTEXT: 2
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00057 | episode_id=57 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2106.89
- CASE_00056 | episode_id=56 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2011.16
- CASE_00054 | episode_id=54 | classification=REVERSAL_WARNING | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1742.89
- CASE_00061 | episode_id=61 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1627.11
- CASE_00046 | episode_id=46 | classification=REVERSAL_WARNING | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1221.06

Counterexamples:
- CASE_00088 | episode_id=88 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=314.5
- CASE_00095 | episode_id=95 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=154.38

Preparation zone summary:
- Preparation candidates: 16
- Preparation zones found: 16
- HIGH preparation count: 12
- EXTREME preparation count: 3
- MOMENTUM_PRECURSOR with preparation: 2
- REVERSAL_WARNING with preparation: 2
- FAILED_CONTEXT with preparation: 1
- PRE_EXPANSION with preparation: 2

HYPOTHESIS_02 revisit summary:
- Return count: 16
- Return success count: 16
- Return failure count: 0
- Agreement true: 8
- Agreement false: 13
- Agreement unknown: 6
- High expansion count: 6
- Extreme expansion count: 5
- Average quiet score: 82.03703704
- Average range ratio: 0.54870875
- Best preparation cases: CASE_00061|CASE_00046|CASE_00071|CASE_00073|CASE_00074
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 24
- Late reversals: 2
- Reversal after preparation return: 11
- Failed after return: 5
- HIGH reversal count: 10
- EXTREME reversal count: 11
- Average time to reversal: 9.10129615

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 1
- Expansion then reversal: 2
- Failed expansions: 0
- Direct reversals: 24
- Average expansion strength: 1.96296296
- Average expansion to reversal ratio: 0.69242554

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-27 16:50:12
Replay window: 2026-05-27
Mode: score4plus
Episodes total: 82
Episodes analyzed: 25
Score >= 4 episodes: 25
Research candidates: 25

Classification counts:
- MOMENTUM_PRECURSOR: 3
- ACCELERATION_ZONE: 1
- PRE_EXPANSION: 7
- CONTEXT_ONLY: 4
- REVERSAL_WARNING: 6
- ACCUMULATION: 3
- ABSORPTION: 1
- FAILED_CONTEXT: 0
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00040 | episode_id=40 | classification=ACCUMULATION | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=1171.38
- CASE_00039 | episode_id=39 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1152.34
- CASE_00047 | episode_id=47 | classification=MOMENTUM_PRECURSOR | layers=4 | context=GAUSSIAN_OUTER | max_abs_4h=1005.36
- CASE_00048 | episode_id=48 | classification=REVERSAL_WARNING | layers=6 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1001.74
- CASE_00002 | episode_id=2 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=770.98

Counterexamples:
- None

Preparation zone summary:
- Preparation candidates: 8
- Preparation zones found: 8
- HIGH preparation count: 4
- EXTREME preparation count: 2
- MOMENTUM_PRECURSOR with preparation: 1
- REVERSAL_WARNING with preparation: 0
- FAILED_CONTEXT with preparation: 0
- PRE_EXPANSION with preparation: 3

HYPOTHESIS_02 revisit summary:
- Return count: 8
- Return success count: 8
- Return failure count: 0
- Agreement true: 7
- Agreement false: 13
- Agreement unknown: 5
- High expansion count: 8
- Extreme expansion count: 2
- Average quiet score: 77.0
- Average range ratio: 0.70305907
- Best preparation cases: CASE_00040|CASE_00039|CASE_00070|CASE_00064|CASE_00022
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 18
- Late reversals: 7
- Reversal after preparation return: 7
- Failed after return: 4
- HIGH reversal count: 7
- EXTREME reversal count: 11
- Average time to reversal: 18.62254267

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 2
- Expansion then reversal: 4
- Failed expansions: 2
- Direct reversals: 16
- Average expansion strength: 1.76
- Average expansion to reversal ratio: 1.09209023

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-28 10:25:26
Replay window: 2026-05-27 -> 2026-05-28
Mode: score4plus
Episodes total: 167
Episodes analyzed: 53
Score >= 4 episodes: 53
Research candidates: 53

Classification counts:
- MOMENTUM_PRECURSOR: 4
- ACCELERATION_ZONE: 3
- PRE_EXPANSION: 13
- CONTEXT_ONLY: 7
- REVERSAL_WARNING: 12
- ACCUMULATION: 8
- ABSORPTION: 1
- FAILED_CONTEXT: 5
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00129 | episode_id=129 | classification=ACCELERATION_ZONE | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1345.39
- CASE_00130 | episode_id=130 | classification=MOMENTUM_PRECURSOR | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1248.67
- CASE_00040 | episode_id=40 | classification=ACCUMULATION | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=1171.38
- CASE_00039 | episode_id=39 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1152.34
- CASE_00121 | episode_id=121 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1089.34

Counterexamples:
- CASE_00110 | episode_id=110 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=400.37
- CASE_00145 | episode_id=145 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=398.83
- CASE_00144 | episode_id=144 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=479.39
- CASE_00146 | episode_id=146 | classification=FAILED_CONTEXT | layers=4 | context=DISTRIBUTION_SHIFT | max_abs_4h=387.98
- CASE_00147 | episode_id=147 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=391.94

Preparation zone summary:
- Preparation candidates: 30
- Preparation zones found: 30
- HIGH preparation count: 11
- EXTREME preparation count: 4
- MOMENTUM_PRECURSOR with preparation: 2
- REVERSAL_WARNING with preparation: 5
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 8

HYPOTHESIS_02 revisit summary:
- Return count: 28
- Return success count: 27
- Return failure count: 1
- Agreement true: 15
- Agreement false: 26
- Agreement unknown: 12
- High expansion count: 18
- Extreme expansion count: 9
- Average quiet score: 82.58490566
- Average range ratio: 0.61777669
- Best preparation cases: CASE_00040|CASE_00039|CASE_00121|CASE_00122|CASE_00103
- Failed preparation cases: CASE_00129|CASE_00130|CASE_00164

REVERSAL ANALYZER V1 summary:
- Direct reversals: 41
- Late reversals: 11
- Reversal after preparation return: 26
- Failed after return: 16
- HIGH reversal count: 20
- EXTREME reversal count: 22
- Average time to reversal: 19.23742019

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 4
- Expansion then reversal: 8
- Failed expansions: 2
- Direct reversals: 38
- Average expansion strength: 2.03773585
- Average expansion to reversal ratio: 1.29361919

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-28 10:31:26
Replay window: 2026-05-27 -> 2026-05-28
Mode: score4plus
Episodes total: 167
Episodes analyzed: 53
Score >= 4 episodes: 53
Research candidates: 53

Classification counts:
- MOMENTUM_PRECURSOR: 4
- ACCELERATION_ZONE: 3
- PRE_EXPANSION: 13
- CONTEXT_ONLY: 7
- REVERSAL_WARNING: 12
- ACCUMULATION: 8
- ABSORPTION: 1
- FAILED_CONTEXT: 5
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00129 | episode_id=129 | classification=ACCELERATION_ZONE | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1345.39
- CASE_00130 | episode_id=130 | classification=MOMENTUM_PRECURSOR | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1248.67
- CASE_00040 | episode_id=40 | classification=ACCUMULATION | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=1171.38
- CASE_00039 | episode_id=39 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1152.34
- CASE_00121 | episode_id=121 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1089.34

Counterexamples:
- CASE_00110 | episode_id=110 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=400.37
- CASE_00145 | episode_id=145 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=398.83
- CASE_00144 | episode_id=144 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=479.39
- CASE_00146 | episode_id=146 | classification=FAILED_CONTEXT | layers=4 | context=DISTRIBUTION_SHIFT | max_abs_4h=387.98
- CASE_00147 | episode_id=147 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=391.94

Preparation zone summary:
- Preparation candidates: 30
- Preparation zones found: 30
- HIGH preparation count: 11
- EXTREME preparation count: 4
- MOMENTUM_PRECURSOR with preparation: 2
- REVERSAL_WARNING with preparation: 5
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 8

HYPOTHESIS_02 revisit summary:
- Return count: 28
- Return success count: 27
- Return failure count: 1
- Agreement true: 15
- Agreement false: 26
- Agreement unknown: 12
- High expansion count: 18
- Extreme expansion count: 9
- Average quiet score: 82.58490566
- Average range ratio: 0.61777669
- Best preparation cases: CASE_00040|CASE_00039|CASE_00121|CASE_00122|CASE_00103
- Failed preparation cases: CASE_00129|CASE_00130|CASE_00164

REVERSAL ANALYZER V1 summary:
- Direct reversals: 41
- Late reversals: 11
- Reversal after preparation return: 26
- Failed after return: 16
- HIGH reversal count: 20
- EXTREME reversal count: 22
- Average time to reversal: 19.23742019

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 4
- Expansion then reversal: 8
- Failed expansions: 2
- Direct reversals: 38
- Average expansion strength: 2.03773585
- Average expansion to reversal ratio: 1.29361919

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-28 10:59:51
Replay window: 2026-05-27 -> 2026-05-28
Mode: score4plus
Episodes total: 167
Episodes analyzed: 53
Score >= 4 episodes: 53
Research candidates: 53

Classification counts:
- MOMENTUM_PRECURSOR: 4
- ACCELERATION_ZONE: 3
- PRE_EXPANSION: 13
- CONTEXT_ONLY: 7
- REVERSAL_WARNING: 12
- ACCUMULATION: 8
- ABSORPTION: 1
- FAILED_CONTEXT: 5
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00129 | episode_id=129 | classification=ACCELERATION_ZONE | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1345.39
- CASE_00130 | episode_id=130 | classification=MOMENTUM_PRECURSOR | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1248.67
- CASE_00040 | episode_id=40 | classification=ACCUMULATION | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=1171.38
- CASE_00039 | episode_id=39 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1152.34
- CASE_00121 | episode_id=121 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1089.34

Counterexamples:
- CASE_00110 | episode_id=110 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=400.37
- CASE_00145 | episode_id=145 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=398.83
- CASE_00144 | episode_id=144 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=479.39
- CASE_00146 | episode_id=146 | classification=FAILED_CONTEXT | layers=4 | context=DISTRIBUTION_SHIFT | max_abs_4h=387.98
- CASE_00147 | episode_id=147 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=391.94

Preparation zone summary:
- Preparation candidates: 30
- Preparation zones found: 30
- HIGH preparation count: 11
- EXTREME preparation count: 4
- MOMENTUM_PRECURSOR with preparation: 2
- REVERSAL_WARNING with preparation: 5
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 8

HYPOTHESIS_02 revisit summary:
- Return count: 28
- Return success count: 27
- Return failure count: 1
- Agreement true: 15
- Agreement false: 26
- Agreement unknown: 12
- High expansion count: 18
- Extreme expansion count: 9
- Average quiet score: 82.58490566
- Average range ratio: 0.61777669
- Best preparation cases: CASE_00040|CASE_00039|CASE_00121|CASE_00122|CASE_00103
- Failed preparation cases: CASE_00129|CASE_00130|CASE_00164

REVERSAL ANALYZER V1 summary:
- Direct reversals: 41
- Late reversals: 11
- Reversal after preparation return: 26
- Failed after return: 16
- HIGH reversal count: 20
- EXTREME reversal count: 22
- Average time to reversal: 19.23742019

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 4
- Expansion then reversal: 8
- Failed expansions: 2
- Direct reversals: 38
- Average expansion strength: 2.03773585
- Average expansion to reversal ratio: 1.29361919

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-28 11:09:52
Replay window: 2026-05-27 -> 2026-05-28
Mode: score4plus
Episodes total: 167
Episodes analyzed: 53
Score >= 4 episodes: 53
Research candidates: 53

Classification counts:
- MOMENTUM_PRECURSOR: 4
- ACCELERATION_ZONE: 3
- PRE_EXPANSION: 13
- CONTEXT_ONLY: 7
- REVERSAL_WARNING: 12
- ACCUMULATION: 8
- ABSORPTION: 1
- FAILED_CONTEXT: 5
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00129 | episode_id=129 | classification=ACCELERATION_ZONE | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1345.39
- CASE_00130 | episode_id=130 | classification=MOMENTUM_PRECURSOR | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1248.67
- CASE_00040 | episode_id=40 | classification=ACCUMULATION | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=1171.38
- CASE_00039 | episode_id=39 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1152.34
- CASE_00121 | episode_id=121 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1089.34

Counterexamples:
- CASE_00110 | episode_id=110 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=400.37
- CASE_00145 | episode_id=145 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=398.83
- CASE_00144 | episode_id=144 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=479.39
- CASE_00146 | episode_id=146 | classification=FAILED_CONTEXT | layers=4 | context=DISTRIBUTION_SHIFT | max_abs_4h=387.98
- CASE_00147 | episode_id=147 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=391.94

Preparation zone summary:
- Preparation candidates: 30
- Preparation zones found: 30
- HIGH preparation count: 11
- EXTREME preparation count: 4
- MOMENTUM_PRECURSOR with preparation: 2
- REVERSAL_WARNING with preparation: 5
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 8

HYPOTHESIS_02 revisit summary:
- Return count: 28
- Return success count: 27
- Return failure count: 1
- Agreement true: 15
- Agreement false: 26
- Agreement unknown: 12
- High expansion count: 18
- Extreme expansion count: 9
- Average quiet score: 82.58490566
- Average range ratio: 0.61777669
- Best preparation cases: CASE_00040|CASE_00039|CASE_00121|CASE_00122|CASE_00103
- Failed preparation cases: CASE_00129|CASE_00130|CASE_00164

REVERSAL ANALYZER V1 summary:
- Direct reversals: 41
- Late reversals: 11
- Reversal after preparation return: 26
- Failed after return: 16
- HIGH reversal count: 20
- EXTREME reversal count: 22
- Average time to reversal: 19.23742019

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 4
- Expansion then reversal: 8
- Failed expansions: 2
- Direct reversals: 38
- Average expansion strength: 2.03773585
- Average expansion to reversal ratio: 1.29361919

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-28 14:58:09
Replay window: 2026-05-28
Mode: score4plus
Episodes total: 86
Episodes analyzed: 27
Score >= 4 episodes: 27
Research candidates: 27

Classification counts:
- MOMENTUM_PRECURSOR: 3
- ACCELERATION_ZONE: 1
- PRE_EXPANSION: 9
- CONTEXT_ONLY: 1
- REVERSAL_WARNING: 4
- ACCUMULATION: 4
- ABSORPTION: 0
- FAILED_CONTEXT: 5
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00005 | episode_id=5 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1483.18
- CASE_00010 | episode_id=10 | classification=MOMENTUM_PRECURSOR | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1413.7
- CASE_00013 | episode_id=13 | classification=MOMENTUM_PRECURSOR | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1271.26
- CASE_00075 | episode_id=75 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=907.81
- CASE_00056 | episode_id=56 | classification=CONTEXT_ONLY | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=812.12

Counterexamples:
- CASE_00026 | episode_id=26 | classification=FAILED_CONTEXT | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=410.42
- CASE_00025 | episode_id=25 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=435.27
- CASE_00027 | episode_id=27 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=388.0
- CASE_00028 | episode_id=28 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=382.29
- CASE_00029 | episode_id=29 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=538.1

Preparation zone summary:
- Preparation candidates: 16
- Preparation zones found: 16
- HIGH preparation count: 8
- EXTREME preparation count: 1
- MOMENTUM_PRECURSOR with preparation: 2
- REVERSAL_WARNING with preparation: 1
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 6

HYPOTHESIS_02 revisit summary:
- Return count: 15
- Return success count: 15
- Return failure count: 0
- Agreement true: 12
- Agreement false: 11
- Agreement unknown: 4
- High expansion count: 3
- Extreme expansion count: 10
- Average quiet score: 80.25925926
- Average range ratio: 0.5948432
- Best preparation cases: CASE_00010|CASE_00056|CASE_00075|CASE_00017|CASE_00048
- Failed preparation cases: CASE_00013

REVERSAL ANALYZER V1 summary:
- Direct reversals: 22
- Late reversals: 3
- Reversal after preparation return: 9
- Failed after return: 4
- HIGH reversal count: 8
- EXTREME reversal count: 10
- Average time to reversal: 12.54427

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 5
- Expansion then reversal: 1
- Failed expansions: 1
- Direct reversals: 20
- Average expansion strength: 2.22222222
- Average expansion to reversal ratio: 2.47620812

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-28 18:10:58
Replay window: 2026-05-28
Mode: score4plus
Episodes total: 108
Episodes analyzed: 32
Score >= 4 episodes: 32
Research candidates: 32

Classification counts:
- MOMENTUM_PRECURSOR: 4
- ACCELERATION_ZONE: 1
- PRE_EXPANSION: 11
- CONTEXT_ONLY: 0
- REVERSAL_WARNING: 5
- ACCUMULATION: 6
- ABSORPTION: 0
- FAILED_CONTEXT: 5
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00005 | episode_id=5 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1483.18
- CASE_00010 | episode_id=10 | classification=MOMENTUM_PRECURSOR | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1413.7
- CASE_00013 | episode_id=13 | classification=MOMENTUM_PRECURSOR | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1271.26
- CASE_00075 | episode_id=75 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1050.56
- CASE_00056 | episode_id=56 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=812.12

Counterexamples:
- CASE_00026 | episode_id=26 | classification=FAILED_CONTEXT | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=410.42
- CASE_00025 | episode_id=25 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=435.27
- CASE_00027 | episode_id=27 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=388.0
- CASE_00028 | episode_id=28 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=382.29
- CASE_00029 | episode_id=29 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=538.1

Preparation zone summary:
- Preparation candidates: 19
- Preparation zones found: 19
- HIGH preparation count: 11
- EXTREME preparation count: 1
- MOMENTUM_PRECURSOR with preparation: 3
- REVERSAL_WARNING with preparation: 2
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 16
- Return success count: 16
- Return failure count: 0
- Agreement true: 16
- Agreement false: 12
- Agreement unknown: 4
- High expansion count: 5
- Extreme expansion count: 12
- Average quiet score: 80.5
- Average range ratio: 0.60005053
- Best preparation cases: CASE_00010|CASE_00075|CASE_00056|CASE_00017|CASE_00048
- Failed preparation cases: CASE_00013|CASE_00090|CASE_00091

REVERSAL ANALYZER V1 summary:
- Direct reversals: 25
- Late reversals: 3
- Reversal after preparation return: 9
- Failed after return: 4
- HIGH reversal count: 9
- EXTREME reversal count: 10
- Average time to reversal: 11.97562381

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 8
- Expansion then reversal: 1
- Failed expansions: 1
- Direct reversals: 22
- Average expansion strength: 2.40625
- Average expansion to reversal ratio: 3.20239276

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-28 20:56:44
Replay window: 2026-05-28
Mode: score4plus
Episodes total: 110
Episodes analyzed: 32
Score >= 4 episodes: 32
Research candidates: 32

Classification counts:
- MOMENTUM_PRECURSOR: 3
- ACCELERATION_ZONE: 1
- PRE_EXPANSION: 11
- CONTEXT_ONLY: 0
- REVERSAL_WARNING: 5
- ACCUMULATION: 7
- ABSORPTION: 0
- FAILED_CONTEXT: 5
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00005 | episode_id=5 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1483.18
- CASE_00010 | episode_id=10 | classification=MOMENTUM_PRECURSOR | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1413.7
- CASE_00013 | episode_id=13 | classification=MOMENTUM_PRECURSOR | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1271.26
- CASE_00075 | episode_id=75 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1050.56
- CASE_00056 | episode_id=56 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=812.12

Counterexamples:
- CASE_00026 | episode_id=26 | classification=FAILED_CONTEXT | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=410.42
- CASE_00025 | episode_id=25 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=435.27
- CASE_00027 | episode_id=27 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=388.0
- CASE_00028 | episode_id=28 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=382.29
- CASE_00029 | episode_id=29 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=538.1

Preparation zone summary:
- Preparation candidates: 19
- Preparation zones found: 19
- HIGH preparation count: 11
- EXTREME preparation count: 1
- MOMENTUM_PRECURSOR with preparation: 2
- REVERSAL_WARNING with preparation: 2
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 16
- Return success count: 16
- Return failure count: 0
- Agreement true: 15
- Agreement false: 13
- Agreement unknown: 4
- High expansion count: 5
- Extreme expansion count: 12
- Average quiet score: 80.5
- Average range ratio: 0.60005053
- Best preparation cases: CASE_00010|CASE_00075|CASE_00056|CASE_00017|CASE_00048
- Failed preparation cases: CASE_00013|CASE_00090|CASE_00091

REVERSAL ANALYZER V1 summary:
- Direct reversals: 25
- Late reversals: 3
- Reversal after preparation return: 9
- Failed after return: 5
- HIGH reversal count: 10
- EXTREME reversal count: 10
- Average time to reversal: 11.97562381

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 7
- Expansion then reversal: 1
- Failed expansions: 1
- Direct reversals: 23
- Average expansion strength: 2.4375
- Average expansion to reversal ratio: 3.12002518

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-29 09:39:20
Replay window: 2026-05-29
Mode: score4plus
Episodes total: 22
Episodes analyzed: 8
Score >= 4 episodes: 8
Research candidates: 8

Classification counts:
- MOMENTUM_PRECURSOR: 1
- ACCELERATION_ZONE: 1
- PRE_EXPANSION: 2
- CONTEXT_ONLY: 1
- REVERSAL_WARNING: 2
- ACCUMULATION: 1
- ABSORPTION: 0
- FAILED_CONTEXT: 0
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00001 | episode_id=1 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=566.69
- CASE_00007 | episode_id=7 | classification=PRE_EXPANSION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=526.51
- CASE_00018 | episode_id=18 | classification=ACCELERATION_ZONE | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=436.68
- CASE_00017 | episode_id=17 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=430.78
- CASE_00002 | episode_id=2 | classification=PRE_EXPANSION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=427.95

Counterexamples:
- None

Preparation zone summary:
- Preparation candidates: 0
- Preparation zones found: 0
- HIGH preparation count: 0
- EXTREME preparation count: 0
- MOMENTUM_PRECURSOR with preparation: 0
- REVERSAL_WARNING with preparation: 0
- FAILED_CONTEXT with preparation: 0
- PRE_EXPANSION with preparation: 0

HYPOTHESIS_02 revisit summary:
- Return count: 0
- Return success count: 0
- Return failure count: 0
- Agreement true: 4
- Agreement false: 4
- Agreement unknown: 0
- High expansion count: 4
- Extreme expansion count: 0
- Average quiet score: 68.625
- Average range ratio: 0.89010383
- Best preparation cases: 
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 3
- Late reversals: 4
- Reversal after preparation return: 0
- Failed after return: 0
- HIGH reversal count: 2
- EXTREME reversal count: 2
- Average time to reversal: 56.00258095

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 3
- Expansion then reversal: 2
- Failed expansions: 0
- Direct reversals: 3
- Average expansion strength: 2.25
- Average expansion to reversal ratio: 4.77158893

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-29 10:32:23
Replay window: 2026-05-29
Mode: score4plus
Episodes total: 22
Episodes analyzed: 8
Score >= 4 episodes: 8
Research candidates: 8

Classification counts:
- MOMENTUM_PRECURSOR: 1
- ACCELERATION_ZONE: 1
- PRE_EXPANSION: 2
- CONTEXT_ONLY: 1
- REVERSAL_WARNING: 2
- ACCUMULATION: 1
- ABSORPTION: 0
- FAILED_CONTEXT: 0
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00001 | episode_id=1 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=566.69
- CASE_00007 | episode_id=7 | classification=PRE_EXPANSION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=526.51
- CASE_00018 | episode_id=18 | classification=ACCELERATION_ZONE | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=436.68
- CASE_00017 | episode_id=17 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=430.78
- CASE_00002 | episode_id=2 | classification=PRE_EXPANSION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=427.95

Counterexamples:
- None

Preparation zone summary:
- Preparation candidates: 0
- Preparation zones found: 0
- HIGH preparation count: 0
- EXTREME preparation count: 0
- MOMENTUM_PRECURSOR with preparation: 0
- REVERSAL_WARNING with preparation: 0
- FAILED_CONTEXT with preparation: 0
- PRE_EXPANSION with preparation: 0

HYPOTHESIS_02 revisit summary:
- Return count: 0
- Return success count: 0
- Return failure count: 0
- Agreement true: 4
- Agreement false: 4
- Agreement unknown: 0
- High expansion count: 4
- Extreme expansion count: 0
- Average quiet score: 68.625
- Average range ratio: 0.89010383
- Best preparation cases: 
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 3
- Late reversals: 4
- Reversal after preparation return: 0
- Failed after return: 0
- HIGH reversal count: 2
- EXTREME reversal count: 2
- Average time to reversal: 56.00258095

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 3
- Expansion then reversal: 2
- Failed expansions: 0
- Direct reversals: 3
- Average expansion strength: 2.25
- Average expansion to reversal ratio: 4.77158893

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-29 11:27:40
Replay window: 2026-05-28 -> 2026-05-29
Mode: score4plus
Episodes total: 145
Episodes analyzed: 40
Score >= 4 episodes: 40
Research candidates: 40

Classification counts:
- MOMENTUM_PRECURSOR: 4
- ACCELERATION_ZONE: 2
- PRE_EXPANSION: 11
- CONTEXT_ONLY: 1
- REVERSAL_WARNING: 7
- ACCUMULATION: 10
- ABSORPTION: 0
- FAILED_CONTEXT: 5
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00005 | episode_id=5 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1483.18
- CASE_00010 | episode_id=10 | classification=MOMENTUM_PRECURSOR | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1413.7
- CASE_00013 | episode_id=13 | classification=MOMENTUM_PRECURSOR | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1271.26
- CASE_00075 | episode_id=75 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1050.56
- CASE_00056 | episode_id=56 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=812.12

Counterexamples:
- CASE_00026 | episode_id=26 | classification=FAILED_CONTEXT | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=410.42
- CASE_00025 | episode_id=25 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=435.27
- CASE_00027 | episode_id=27 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=388.0
- CASE_00028 | episode_id=28 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=382.29
- CASE_00029 | episode_id=29 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=538.1

Preparation zone summary:
- Preparation candidates: 23
- Preparation zones found: 23
- HIGH preparation count: 13
- EXTREME preparation count: 1
- MOMENTUM_PRECURSOR with preparation: 3
- REVERSAL_WARNING with preparation: 2
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 20
- Return success count: 20
- Return failure count: 0
- Agreement true: 20
- Agreement false: 16
- Agreement unknown: 4
- High expansion count: 10
- Extreme expansion count: 12
- Average quiet score: 80.925
- Average range ratio: 0.607192
- Best preparation cases: CASE_00010|CASE_00075|CASE_00056|CASE_00017|CASE_00048
- Failed preparation cases: CASE_00013|CASE_00090|CASE_00091

REVERSAL ANALYZER V1 summary:
- Direct reversals: 29
- Late reversals: 6
- Reversal after preparation return: 12
- Failed after return: 5
- HIGH reversal count: 12
- EXTREME reversal count: 12
- Average time to reversal: 20.59605619

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 10
- Expansion then reversal: 2
- Failed expansions: 1
- Direct reversals: 27
- Average expansion strength: 2.4
- Average expansion to reversal ratio: 3.33796618

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-29 18:02:19
Replay window: 2026-05-28 -> 2026-05-29
Mode: score4plus
Episodes total: 163
Episodes analyzed: 46
Score >= 4 episodes: 46
Research candidates: 46

Classification counts:
- MOMENTUM_PRECURSOR: 7
- ACCELERATION_ZONE: 2
- PRE_EXPANSION: 13
- CONTEXT_ONLY: 1
- REVERSAL_WARNING: 7
- ACCUMULATION: 10
- ABSORPTION: 0
- FAILED_CONTEXT: 6
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00005 | episode_id=5 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1483.18
- CASE_00010 | episode_id=10 | classification=MOMENTUM_PRECURSOR | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1413.7
- CASE_00013 | episode_id=13 | classification=MOMENTUM_PRECURSOR | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1271.26
- CASE_00075 | episode_id=75 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1050.56
- CASE_00056 | episode_id=56 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=812.12

Counterexamples:
- CASE_00162 | episode_id=162 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=210.11
- CASE_00026 | episode_id=26 | classification=FAILED_CONTEXT | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=410.42
- CASE_00025 | episode_id=25 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=435.27
- CASE_00027 | episode_id=27 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=388.0
- CASE_00028 | episode_id=28 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=382.29

Preparation zone summary:
- Preparation candidates: 27
- Preparation zones found: 27
- HIGH preparation count: 14
- EXTREME preparation count: 1
- MOMENTUM_PRECURSOR with preparation: 4
- REVERSAL_WARNING with preparation: 2
- FAILED_CONTEXT with preparation: 3
- PRE_EXPANSION with preparation: 9

HYPOTHESIS_02 revisit summary:
- Return count: 25
- Return success count: 25
- Return failure count: 0
- Agreement true: 25
- Agreement false: 17
- Agreement unknown: 4
- High expansion count: 13
- Extreme expansion count: 14
- Average quiet score: 80.93478261
- Average range ratio: 0.60394534
- Best preparation cases: CASE_00010|CASE_00075|CASE_00056|CASE_00017|CASE_00048
- Failed preparation cases: CASE_00013|CASE_00160

REVERSAL ANALYZER V1 summary:
- Direct reversals: 33
- Late reversals: 7
- Reversal after preparation return: 13
- Failed after return: 7
- HIGH reversal count: 14
- EXTREME reversal count: 12
- Average time to reversal: 18.52320917

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 13
- Expansion then reversal: 2
- Failed expansions: 1
- Direct reversals: 30
- Average expansion strength: 2.47826087
- Average expansion to reversal ratio: 4.57519924

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-30 14:21:54
Replay window: 2026-05-29
Mode: score4plus
Episodes total: 88
Episodes analyzed: 33
Score >= 4 episodes: 33
Research candidates: 33

Classification counts:
- MOMENTUM_PRECURSOR: 5
- ACCELERATION_ZONE: 1
- PRE_EXPANSION: 6
- CONTEXT_ONLY: 4
- REVERSAL_WARNING: 7
- ACCUMULATION: 9
- ABSORPTION: 0
- FAILED_CONTEXT: 1
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00042 | episode_id=42 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1767.87
- CASE_00040 | episode_id=40 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1596.85
- CASE_00038 | episode_id=38 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1468.38
- CASE_00035 | episode_id=35 | classification=ACCUMULATION | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=1423.86
- CASE_00047 | episode_id=47 | classification=MOMENTUM_PRECURSOR | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1315.72

Counterexamples:
- CASE_00085 | episode_id=85 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=148.9

Preparation zone summary:
- Preparation candidates: 15
- Preparation zones found: 15
- HIGH preparation count: 9
- EXTREME preparation count: 2
- MOMENTUM_PRECURSOR with preparation: 1
- REVERSAL_WARNING with preparation: 4
- FAILED_CONTEXT with preparation: 1
- PRE_EXPANSION with preparation: 2

HYPOTHESIS_02 revisit summary:
- Return count: 15
- Return success count: 15
- Return failure count: 0
- Agreement true: 14
- Agreement false: 19
- Agreement unknown: 0
- High expansion count: 13
- Extreme expansion count: 8
- Average quiet score: 77.21212121
- Average range ratio: 0.66456701
- Best preparation cases: CASE_00042|CASE_00040|CASE_00038|CASE_00035|CASE_00069
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 20
- Late reversals: 10
- Reversal after preparation return: 9
- Failed after return: 9
- HIGH reversal count: 6
- EXTREME reversal count: 16
- Average time to reversal: 23.80677556

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 8
- Expansion then reversal: 7
- Failed expansions: 0
- Direct reversals: 18
- Average expansion strength: 2.6969697
- Average expansion to reversal ratio: 3.54670769

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-31 20:12:52
Replay window: 2026-05-29
Mode: all
Episodes total: 93
Episodes analyzed: 93
Score >= 4 episodes: 33
Research candidates: 50

Classification counts:
- MOMENTUM_PRECURSOR: 28
- ACCELERATION_ZONE: 4
- PRE_EXPANSION: 15
- CONTEXT_ONLY: 16
- REVERSAL_WARNING: 15
- ACCUMULATION: 14
- ABSORPTION: 0
- FAILED_CONTEXT: 1
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00047 | episode_id=47 | classification=MOMENTUM_PRECURSOR | layers=3 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=1751.47
- CASE_00045 | episode_id=45 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1731.35
- CASE_00046 | episode_id=46 | classification=MOMENTUM_PRECURSOR | layers=2 | context=COMPRESSION_REGIME_TO_LOW_VOLATILITY | max_abs_4h=1676.23
- CASE_00044 | episode_id=44 | classification=REVERSAL_WARNING | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1649.0
- CASE_00043 | episode_id=43 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1582.63

Counterexamples:
- CASE_00089 | episode_id=89 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=145.0

Preparation zone summary:
- Preparation candidates: 46
- Preparation zones found: 46
- HIGH preparation count: 22
- EXTREME preparation count: 3
- MOMENTUM_PRECURSOR with preparation: 10
- REVERSAL_WARNING with preparation: 9
- FAILED_CONTEXT with preparation: 1
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 44
- Return success count: 43
- Return failure count: 1
- Agreement true: 25
- Agreement false: 23
- Agreement unknown: 45
- High expansion count: 22
- Extreme expansion count: 14
- Average quiet score: 78.75268817
- Average range ratio: 0.65738177
- Best preparation cases: CASE_00047|CASE_00046|CASE_00045|CASE_00044|CASE_00042
- Failed preparation cases: CASE_00048|CASE_00078|CASE_00092

REVERSAL ANALYZER V1 summary:
- Direct reversals: 73
- Late reversals: 16
- Reversal after preparation return: 36
- Failed after return: 14
- HIGH reversal count: 13
- EXTREME reversal count: 56
- Average time to reversal: 16.50283258

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 12
- Expansion then reversal: 10
- Failed expansions: 0
- Direct reversals: 71
- Average expansion strength: 1.53763441
- Average expansion to reversal ratio: 1.94161617

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-31 22:04:37
Replay window: 2026-05-29
Mode: all
Episodes total: 93
Episodes analyzed: 93
Score >= 4 episodes: 33
Research candidates: 50

Classification counts:
- MOMENTUM_PRECURSOR: 28
- ACCELERATION_ZONE: 4
- PRE_EXPANSION: 15
- CONTEXT_ONLY: 16
- REVERSAL_WARNING: 15
- ACCUMULATION: 14
- ABSORPTION: 0
- FAILED_CONTEXT: 1
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00047 | episode_id=47 | classification=MOMENTUM_PRECURSOR | layers=3 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=1751.47
- CASE_00045 | episode_id=45 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1731.35
- CASE_00046 | episode_id=46 | classification=MOMENTUM_PRECURSOR | layers=2 | context=COMPRESSION_REGIME_TO_LOW_VOLATILITY | max_abs_4h=1676.23
- CASE_00044 | episode_id=44 | classification=REVERSAL_WARNING | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1649.0
- CASE_00043 | episode_id=43 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1582.63

Counterexamples:
- CASE_00089 | episode_id=89 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=145.0

Preparation zone summary:
- Preparation candidates: 46
- Preparation zones found: 46
- HIGH preparation count: 22
- EXTREME preparation count: 3
- MOMENTUM_PRECURSOR with preparation: 10
- REVERSAL_WARNING with preparation: 9
- FAILED_CONTEXT with preparation: 1
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 44
- Return success count: 43
- Return failure count: 1
- Agreement true: 25
- Agreement false: 23
- Agreement unknown: 45
- High expansion count: 22
- Extreme expansion count: 14
- Average quiet score: 78.75268817
- Average range ratio: 0.65738177
- Best preparation cases: CASE_00047|CASE_00046|CASE_00045|CASE_00044|CASE_00042
- Failed preparation cases: CASE_00048|CASE_00078|CASE_00092

REVERSAL ANALYZER V1 summary:
- Direct reversals: 73
- Late reversals: 16
- Reversal after preparation return: 36
- Failed after return: 14
- HIGH reversal count: 13
- EXTREME reversal count: 56
- Average time to reversal: 16.50283258

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 12
- Expansion then reversal: 10
- Failed expansions: 0
- Direct reversals: 71
- Average expansion strength: 1.53763441
- Average expansion to reversal ratio: 1.94161617

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-31 22:42:59
Replay window: 2026-05-26
Mode: all
Episodes total: 114
Episodes analyzed: 114
Score >= 4 episodes: 27
Research candidates: 52

Classification counts:
- MOMENTUM_PRECURSOR: 40
- ACCELERATION_ZONE: 4
- PRE_EXPANSION: 10
- CONTEXT_ONLY: 21
- REVERSAL_WARNING: 18
- ACCUMULATION: 16
- ABSORPTION: 0
- FAILED_CONTEXT: 5
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00067 | episode_id=67 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2104.89
- CASE_00068 | episode_id=68 | classification=MOMENTUM_PRECURSOR | layers=2 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=2036.04
- CASE_00066 | episode_id=66 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2006.09
- CASE_00064 | episode_id=64 | classification=REVERSAL_WARNING | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1748.14
- CASE_00069 | episode_id=69 | classification=ACCUMULATION | layers=2 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1688.95

Counterexamples:
- CASE_00096 | episode_id=96 | classification=FAILED_CONTEXT | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=309.22
- CASE_00103 | episode_id=103 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=188.77
- CASE_00097 | episode_id=97 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=345.88
- CASE_00104 | episode_id=104 | classification=FAILED_CONTEXT | layers=3 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=194.56
- CASE_00114 | episode_id=114 | classification=FAILED_CONTEXT | layers=2 | context=CLIMACTIC_VOLUME | max_abs_4h=73.18

Preparation zone summary:
- Preparation candidates: 50
- Preparation zones found: 50
- HIGH preparation count: 35
- EXTREME preparation count: 5
- MOMENTUM_PRECURSOR with preparation: 20
- REVERSAL_WARNING with preparation: 6
- FAILED_CONTEXT with preparation: 1
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 50
- Return success count: 49
- Return failure count: 1
- Agreement true: 23
- Agreement false: 17
- Agreement unknown: 74
- High expansion count: 11
- Extreme expansion count: 15
- Average quiet score: 78.96491228
- Average range ratio: 0.63009218
- Best preparation cases: CASE_00070|CASE_00071|CASE_00057|CASE_00059|CASE_00056
- Failed preparation cases: CASE_00114

REVERSAL ANALYZER V1 summary:
- Direct reversals: 101
- Late reversals: 10
- Reversal after preparation return: 38
- Failed after return: 6
- HIGH reversal count: 33
- EXTREME reversal count: 58
- Average time to reversal: 11.18207477

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 5
- Expansion then reversal: 8
- Failed expansions: 1
- Direct reversals: 99
- Average expansion strength: 0.99122807
- Average expansion to reversal ratio: 0.50067493

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-31 23:01:18
Replay window: 2026-05-27
Mode: all
Episodes total: 116
Episodes analyzed: 116
Score >= 4 episodes: 36
Research candidates: 54

Classification counts:
- MOMENTUM_PRECURSOR: 28
- ACCELERATION_ZONE: 1
- PRE_EXPANSION: 16
- CONTEXT_ONLY: 23
- REVERSAL_WARNING: 25
- ACCUMULATION: 18
- ABSORPTION: 1
- FAILED_CONTEXT: 4
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00050 | episode_id=50 | classification=REVERSAL_WARNING | layers=3 | context=EXTREME_VELOCITY_EXHAUSTION | max_abs_4h=1326.14
- CASE_00049 | episode_id=49 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1266.65
- CASE_00037 | episode_id=37 | classification=MOMENTUM_PRECURSOR | layers=2 | context=DISTRIBUTION_SHIFT | max_abs_4h=1218.99
- CASE_00036 | episode_id=36 | classification=MOMENTUM_PRECURSOR | layers=3 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=1217.68
- CASE_00042 | episode_id=42 | classification=ACCELERATION_ZONE | layers=2 | context=COMPRESSION_REGIME_TO_LOW_VOLATILITY | max_abs_4h=1209.33

Counterexamples:
- CASE_00057 | episode_id=57 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=451.11
- CASE_00105 | episode_id=105 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=253.42
- CASE_00114 | episode_id=114 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=110.74
- CASE_00116 | episode_id=116 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=98.82

Preparation zone summary:
- Preparation candidates: 55
- Preparation zones found: 55
- HIGH preparation count: 22
- EXTREME preparation count: 9
- MOMENTUM_PRECURSOR with preparation: 10
- REVERSAL_WARNING with preparation: 8
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 55
- Return success count: 55
- Return failure count: 0
- Agreement true: 19
- Agreement false: 30
- Agreement unknown: 67
- High expansion count: 19
- Extreme expansion count: 9
- Average quiet score: 80.68695652
- Average range ratio: 0.65882608
- Best preparation cases: CASE_00043|CASE_00041|CASE_00042|CASE_00040|CASE_00039
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 95
- Late reversals: 18
- Reversal after preparation return: 51
- Failed after return: 17
- HIGH reversal count: 47
- EXTREME reversal count: 47
- Average time to reversal: 11.7748146

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 6
- Expansion then reversal: 13
- Failed expansions: 5
- Direct reversals: 91
- Average expansion strength: 1.10344828
- Average expansion to reversal ratio: 0.96942152

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-31 23:37:56
Replay window: 2026-05-28
Mode: all
Episodes total: 98
Episodes analyzed: 98
Score >= 4 episodes: 25
Research candidates: 58

Classification counts:
- MOMENTUM_PRECURSOR: 27
- ACCELERATION_ZONE: 9
- PRE_EXPANSION: 20
- CONTEXT_ONLY: 12
- REVERSAL_WARNING: 13
- ACCUMULATION: 12
- ABSORPTION: 0
- FAILED_CONTEXT: 5
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00002 | episode_id=2 | classification=ACCUMULATION | layers=2 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1784.63
- CASE_00001 | episode_id=1 | classification=MOMENTUM_PRECURSOR | layers=2 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=1708.16
- CASE_00005 | episode_id=5 | classification=REVERSAL_WARNING | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1619.61
- CASE_00006 | episode_id=6 | classification=MOMENTUM_PRECURSOR | layers=2 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1598.52
- CASE_00007 | episode_id=7 | classification=ACCUMULATION | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1482.03

Counterexamples:
- CASE_00023 | episode_id=23 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=491.26
- CASE_00026 | episode_id=26 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=556.66
- CASE_00022 | episode_id=22 | classification=FAILED_CONTEXT | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=486.62
- CASE_00024 | episode_id=24 | classification=FAILED_CONTEXT | layers=3 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=428.61
- CASE_00025 | episode_id=25 | classification=FAILED_CONTEXT | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=422.6

Preparation zone summary:
- Preparation candidates: 57
- Preparation zones found: 57
- HIGH preparation count: 39
- EXTREME preparation count: 1
- MOMENTUM_PRECURSOR with preparation: 12
- REVERSAL_WARNING with preparation: 7
- FAILED_CONTEXT with preparation: 4
- PRE_EXPANSION with preparation: 9

HYPOTHESIS_02 revisit summary:
- Return count: 53
- Return success count: 53
- Return failure count: 0
- Agreement true: 24
- Agreement false: 19
- Agreement unknown: 55
- High expansion count: 9
- Extreme expansion count: 17
- Average quiet score: 81.55102041
- Average range ratio: 0.63491287
- Best preparation cases: CASE_00008|CASE_00009|CASE_00067|CASE_00066|CASE_00065
- Failed preparation cases: CASE_00010|CASE_00011|CASE_00077|CASE_00078

REVERSAL ANALYZER V1 summary:
- Direct reversals: 86
- Late reversals: 6
- Reversal after preparation return: 43
- Failed after return: 9
- HIGH reversal count: 27
- EXTREME reversal count: 54
- Average time to reversal: 5.24731612

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 10
- Expansion then reversal: 4
- Failed expansions: 1
- Direct reversals: 83
- Average expansion strength: 1.17346939
- Average expansion to reversal ratio: 1.87697954

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-31 23:38:24
Replay window: 2026-05-28
Mode: all
Episodes total: 98
Episodes analyzed: 98
Score >= 4 episodes: 25
Research candidates: 58

Classification counts:
- MOMENTUM_PRECURSOR: 27
- ACCELERATION_ZONE: 9
- PRE_EXPANSION: 20
- CONTEXT_ONLY: 12
- REVERSAL_WARNING: 13
- ACCUMULATION: 12
- ABSORPTION: 0
- FAILED_CONTEXT: 5
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00002 | episode_id=2 | classification=ACCUMULATION | layers=2 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1784.63
- CASE_00001 | episode_id=1 | classification=MOMENTUM_PRECURSOR | layers=2 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=1708.16
- CASE_00005 | episode_id=5 | classification=REVERSAL_WARNING | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1619.61
- CASE_00006 | episode_id=6 | classification=MOMENTUM_PRECURSOR | layers=2 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1598.52
- CASE_00007 | episode_id=7 | classification=ACCUMULATION | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1482.03

Counterexamples:
- CASE_00023 | episode_id=23 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=491.26
- CASE_00026 | episode_id=26 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=556.66
- CASE_00022 | episode_id=22 | classification=FAILED_CONTEXT | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=486.62
- CASE_00024 | episode_id=24 | classification=FAILED_CONTEXT | layers=3 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=428.61
- CASE_00025 | episode_id=25 | classification=FAILED_CONTEXT | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=422.6

Preparation zone summary:
- Preparation candidates: 57
- Preparation zones found: 57
- HIGH preparation count: 39
- EXTREME preparation count: 1
- MOMENTUM_PRECURSOR with preparation: 12
- REVERSAL_WARNING with preparation: 7
- FAILED_CONTEXT with preparation: 4
- PRE_EXPANSION with preparation: 9

HYPOTHESIS_02 revisit summary:
- Return count: 53
- Return success count: 53
- Return failure count: 0
- Agreement true: 24
- Agreement false: 19
- Agreement unknown: 55
- High expansion count: 9
- Extreme expansion count: 17
- Average quiet score: 81.55102041
- Average range ratio: 0.63491287
- Best preparation cases: CASE_00008|CASE_00009|CASE_00067|CASE_00066|CASE_00065
- Failed preparation cases: CASE_00010|CASE_00011|CASE_00077|CASE_00078

REVERSAL ANALYZER V1 summary:
- Direct reversals: 86
- Late reversals: 6
- Reversal after preparation return: 43
- Failed after return: 9
- HIGH reversal count: 27
- EXTREME reversal count: 54
- Average time to reversal: 5.24731612

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 10
- Expansion then reversal: 4
- Failed expansions: 1
- Direct reversals: 83
- Average expansion strength: 1.17346939
- Average expansion to reversal ratio: 1.87697954

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-05-31 23:59:15
Replay window: 2026-05-30
Mode: all
Episodes total: 47
Episodes analyzed: 47
Score >= 4 episodes: 13
Research candidates: 27

Classification counts:
- MOMENTUM_PRECURSOR: 12
- ACCELERATION_ZONE: 0
- PRE_EXPANSION: 14
- CONTEXT_ONLY: 4
- REVERSAL_WARNING: 5
- ACCUMULATION: 9
- ABSORPTION: 0
- FAILED_CONTEXT: 3
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00006 | episode_id=6 | classification=MOMENTUM_PRECURSOR | layers=2 | context=GAUSSIAN_OUTER | max_abs_4h=544.61
- CASE_00007 | episode_id=7 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=509.35
- CASE_00025 | episode_id=25 | classification=ACCUMULATION | layers=2 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=507.36
- CASE_00026 | episode_id=26 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=497.88
- CASE_00008 | episode_id=8 | classification=MOMENTUM_PRECURSOR | layers=2 | context=DISTRIBUTION_SHIFT | max_abs_4h=497.58

Counterexamples:
- CASE_00016 | episode_id=16 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=120.17
- CASE_00046 | episode_id=46 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=82.06
- CASE_00047 | episode_id=47 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=51.55

Preparation zone summary:
- Preparation candidates: 24
- Preparation zones found: 24
- HIGH preparation count: 11
- EXTREME preparation count: 5
- MOMENTUM_PRECURSOR with preparation: 6
- REVERSAL_WARNING with preparation: 2
- FAILED_CONTEXT with preparation: 0
- PRE_EXPANSION with preparation: 8

HYPOTHESIS_02 revisit summary:
- Return count: 24
- Return success count: 23
- Return failure count: 1
- Agreement true: 9
- Agreement false: 10
- Agreement unknown: 28
- High expansion count: 5
- Extreme expansion count: 0
- Average quiet score: 80.65957447
- Average range ratio: 0.69390485
- Best preparation cases: CASE_00024|CASE_00025|CASE_00026|CASE_00023|CASE_00027
- Failed preparation cases: CASE_00042

REVERSAL ANALYZER V1 summary:
- Direct reversals: 34
- Late reversals: 10
- Reversal after preparation return: 17
- Failed after return: 3
- HIGH reversal count: 16
- EXTREME reversal count: 3
- Average time to reversal: 12.70797424

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 7
- Expansion then reversal: 1
- Failed expansions: 7
- Direct reversals: 30
- Average expansion strength: 0.78723404
- Average expansion to reversal ratio: 1.89471947

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-01 00:38:36
Replay window: 2026-05-29
Mode: all
Episodes total: 93
Episodes analyzed: 93
Score >= 4 episodes: 33
Research candidates: 50

Classification counts:
- MOMENTUM_PRECURSOR: 28
- ACCELERATION_ZONE: 4
- PRE_EXPANSION: 15
- CONTEXT_ONLY: 16
- REVERSAL_WARNING: 15
- ACCUMULATION: 14
- ABSORPTION: 0
- FAILED_CONTEXT: 1
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00047 | episode_id=47 | classification=MOMENTUM_PRECURSOR | layers=3 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=1751.47
- CASE_00045 | episode_id=45 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1731.35
- CASE_00046 | episode_id=46 | classification=MOMENTUM_PRECURSOR | layers=2 | context=COMPRESSION_REGIME_TO_LOW_VOLATILITY | max_abs_4h=1676.23
- CASE_00044 | episode_id=44 | classification=REVERSAL_WARNING | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1649.0
- CASE_00043 | episode_id=43 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1582.63

Counterexamples:
- CASE_00089 | episode_id=89 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=145.0

Preparation zone summary:
- Preparation candidates: 46
- Preparation zones found: 46
- HIGH preparation count: 22
- EXTREME preparation count: 3
- MOMENTUM_PRECURSOR with preparation: 10
- REVERSAL_WARNING with preparation: 9
- FAILED_CONTEXT with preparation: 1
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 44
- Return success count: 43
- Return failure count: 1
- Agreement true: 25
- Agreement false: 23
- Agreement unknown: 45
- High expansion count: 22
- Extreme expansion count: 14
- Average quiet score: 78.75268817
- Average range ratio: 0.65738177
- Best preparation cases: CASE_00047|CASE_00046|CASE_00045|CASE_00044|CASE_00042
- Failed preparation cases: CASE_00048|CASE_00078|CASE_00092

REVERSAL ANALYZER V1 summary:
- Direct reversals: 73
- Late reversals: 16
- Reversal after preparation return: 36
- Failed after return: 14
- HIGH reversal count: 13
- EXTREME reversal count: 56
- Average time to reversal: 16.50283258

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 12
- Expansion then reversal: 10
- Failed expansions: 0
- Direct reversals: 71
- Average expansion strength: 1.53763441
- Average expansion to reversal ratio: 1.94161617

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-01 00:38:43
Replay window: 2026-05-29
Mode: all
Episodes total: 93
Episodes analyzed: 93
Score >= 4 episodes: 33
Research candidates: 50

Classification counts:
- MOMENTUM_PRECURSOR: 28
- ACCELERATION_ZONE: 4
- PRE_EXPANSION: 15
- CONTEXT_ONLY: 16
- REVERSAL_WARNING: 15
- ACCUMULATION: 14
- ABSORPTION: 0
- FAILED_CONTEXT: 1
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00047 | episode_id=47 | classification=MOMENTUM_PRECURSOR | layers=3 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=1751.47
- CASE_00045 | episode_id=45 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1731.35
- CASE_00046 | episode_id=46 | classification=MOMENTUM_PRECURSOR | layers=2 | context=COMPRESSION_REGIME_TO_LOW_VOLATILITY | max_abs_4h=1676.23
- CASE_00044 | episode_id=44 | classification=REVERSAL_WARNING | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1649.0
- CASE_00043 | episode_id=43 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1582.63

Counterexamples:
- CASE_00089 | episode_id=89 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=145.0

Preparation zone summary:
- Preparation candidates: 46
- Preparation zones found: 46
- HIGH preparation count: 22
- EXTREME preparation count: 3
- MOMENTUM_PRECURSOR with preparation: 10
- REVERSAL_WARNING with preparation: 9
- FAILED_CONTEXT with preparation: 1
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 44
- Return success count: 43
- Return failure count: 1
- Agreement true: 25
- Agreement false: 23
- Agreement unknown: 45
- High expansion count: 22
- Extreme expansion count: 14
- Average quiet score: 78.75268817
- Average range ratio: 0.65738177
- Best preparation cases: CASE_00047|CASE_00046|CASE_00045|CASE_00044|CASE_00042
- Failed preparation cases: CASE_00048|CASE_00078|CASE_00092

REVERSAL ANALYZER V1 summary:
- Direct reversals: 73
- Late reversals: 16
- Reversal after preparation return: 36
- Failed after return: 14
- HIGH reversal count: 13
- EXTREME reversal count: 56
- Average time to reversal: 16.50283258

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 12
- Expansion then reversal: 10
- Failed expansions: 0
- Direct reversals: 71
- Average expansion strength: 1.53763441
- Average expansion to reversal ratio: 1.94161617

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-01 01:10:06
Replay window: 2026-05-26
Mode: all
Episodes total: 114
Episodes analyzed: 114
Score >= 4 episodes: 27
Research candidates: 52

Classification counts:
- MOMENTUM_PRECURSOR: 40
- ACCELERATION_ZONE: 4
- PRE_EXPANSION: 10
- CONTEXT_ONLY: 21
- REVERSAL_WARNING: 18
- ACCUMULATION: 16
- ABSORPTION: 0
- FAILED_CONTEXT: 5
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00067 | episode_id=67 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2104.89
- CASE_00068 | episode_id=68 | classification=MOMENTUM_PRECURSOR | layers=2 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=2036.04
- CASE_00066 | episode_id=66 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2006.09
- CASE_00064 | episode_id=64 | classification=REVERSAL_WARNING | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1748.14
- CASE_00069 | episode_id=69 | classification=ACCUMULATION | layers=2 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1688.95

Counterexamples:
- CASE_00096 | episode_id=96 | classification=FAILED_CONTEXT | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=309.22
- CASE_00103 | episode_id=103 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=188.77
- CASE_00097 | episode_id=97 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=345.88
- CASE_00104 | episode_id=104 | classification=FAILED_CONTEXT | layers=3 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=194.56
- CASE_00114 | episode_id=114 | classification=FAILED_CONTEXT | layers=2 | context=CLIMACTIC_VOLUME | max_abs_4h=73.18

Preparation zone summary:
- Preparation candidates: 50
- Preparation zones found: 50
- HIGH preparation count: 35
- EXTREME preparation count: 5
- MOMENTUM_PRECURSOR with preparation: 20
- REVERSAL_WARNING with preparation: 6
- FAILED_CONTEXT with preparation: 1
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 50
- Return success count: 49
- Return failure count: 1
- Agreement true: 23
- Agreement false: 17
- Agreement unknown: 74
- High expansion count: 11
- Extreme expansion count: 15
- Average quiet score: 78.96491228
- Average range ratio: 0.63009218
- Best preparation cases: CASE_00070|CASE_00071|CASE_00057|CASE_00059|CASE_00056
- Failed preparation cases: CASE_00114

REVERSAL ANALYZER V1 summary:
- Direct reversals: 101
- Late reversals: 10
- Reversal after preparation return: 38
- Failed after return: 6
- HIGH reversal count: 33
- EXTREME reversal count: 58
- Average time to reversal: 11.18207477

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 5
- Expansion then reversal: 8
- Failed expansions: 1
- Direct reversals: 99
- Average expansion strength: 0.99122807
- Average expansion to reversal ratio: 0.50067493

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-01 01:10:28
Replay window: 2026-05-26
Mode: all
Episodes total: 114
Episodes analyzed: 114
Score >= 4 episodes: 27
Research candidates: 52

Classification counts:
- MOMENTUM_PRECURSOR: 40
- ACCELERATION_ZONE: 4
- PRE_EXPANSION: 10
- CONTEXT_ONLY: 21
- REVERSAL_WARNING: 18
- ACCUMULATION: 16
- ABSORPTION: 0
- FAILED_CONTEXT: 5
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00067 | episode_id=67 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2104.89
- CASE_00068 | episode_id=68 | classification=MOMENTUM_PRECURSOR | layers=2 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=2036.04
- CASE_00066 | episode_id=66 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2006.09
- CASE_00064 | episode_id=64 | classification=REVERSAL_WARNING | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1748.14
- CASE_00069 | episode_id=69 | classification=ACCUMULATION | layers=2 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1688.95

Counterexamples:
- CASE_00096 | episode_id=96 | classification=FAILED_CONTEXT | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=309.22
- CASE_00103 | episode_id=103 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=188.77
- CASE_00097 | episode_id=97 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=345.88
- CASE_00104 | episode_id=104 | classification=FAILED_CONTEXT | layers=3 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=194.56
- CASE_00114 | episode_id=114 | classification=FAILED_CONTEXT | layers=2 | context=CLIMACTIC_VOLUME | max_abs_4h=73.18

Preparation zone summary:
- Preparation candidates: 50
- Preparation zones found: 50
- HIGH preparation count: 35
- EXTREME preparation count: 5
- MOMENTUM_PRECURSOR with preparation: 20
- REVERSAL_WARNING with preparation: 6
- FAILED_CONTEXT with preparation: 1
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 50
- Return success count: 49
- Return failure count: 1
- Agreement true: 23
- Agreement false: 17
- Agreement unknown: 74
- High expansion count: 11
- Extreme expansion count: 15
- Average quiet score: 78.96491228
- Average range ratio: 0.63009218
- Best preparation cases: CASE_00070|CASE_00071|CASE_00057|CASE_00059|CASE_00056
- Failed preparation cases: CASE_00114

REVERSAL ANALYZER V1 summary:
- Direct reversals: 101
- Late reversals: 10
- Reversal after preparation return: 38
- Failed after return: 6
- HIGH reversal count: 33
- EXTREME reversal count: 58
- Average time to reversal: 11.18207477

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 5
- Expansion then reversal: 8
- Failed expansions: 1
- Direct reversals: 99
- Average expansion strength: 0.99122807
- Average expansion to reversal ratio: 0.50067493

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-01 01:33:37
Replay window: 2026-05-26
Mode: all
Episodes total: 114
Episodes analyzed: 114
Score >= 4 episodes: 27
Research candidates: 52

Classification counts:
- MOMENTUM_PRECURSOR: 40
- ACCELERATION_ZONE: 4
- PRE_EXPANSION: 10
- CONTEXT_ONLY: 21
- REVERSAL_WARNING: 18
- ACCUMULATION: 16
- ABSORPTION: 0
- FAILED_CONTEXT: 5
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00067 | episode_id=67 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2104.89
- CASE_00068 | episode_id=68 | classification=MOMENTUM_PRECURSOR | layers=2 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=2036.04
- CASE_00066 | episode_id=66 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2006.09
- CASE_00064 | episode_id=64 | classification=REVERSAL_WARNING | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1748.14
- CASE_00069 | episode_id=69 | classification=ACCUMULATION | layers=2 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1688.95

Counterexamples:
- CASE_00096 | episode_id=96 | classification=FAILED_CONTEXT | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=309.22
- CASE_00103 | episode_id=103 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=188.77
- CASE_00097 | episode_id=97 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=345.88
- CASE_00104 | episode_id=104 | classification=FAILED_CONTEXT | layers=3 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=194.56
- CASE_00114 | episode_id=114 | classification=FAILED_CONTEXT | layers=2 | context=CLIMACTIC_VOLUME | max_abs_4h=73.18

Preparation zone summary:
- Preparation candidates: 50
- Preparation zones found: 50
- HIGH preparation count: 35
- EXTREME preparation count: 5
- MOMENTUM_PRECURSOR with preparation: 20
- REVERSAL_WARNING with preparation: 6
- FAILED_CONTEXT with preparation: 1
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 50
- Return success count: 49
- Return failure count: 1
- Agreement true: 23
- Agreement false: 17
- Agreement unknown: 74
- High expansion count: 11
- Extreme expansion count: 15
- Average quiet score: 78.96491228
- Average range ratio: 0.63009218
- Best preparation cases: CASE_00070|CASE_00071|CASE_00057|CASE_00059|CASE_00056
- Failed preparation cases: CASE_00114

REVERSAL ANALYZER V1 summary:
- Direct reversals: 101
- Late reversals: 10
- Reversal after preparation return: 38
- Failed after return: 6
- HIGH reversal count: 33
- EXTREME reversal count: 58
- Average time to reversal: 11.18207477

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 5
- Expansion then reversal: 8
- Failed expansions: 1
- Direct reversals: 99
- Average expansion strength: 0.99122807
- Average expansion to reversal ratio: 0.50067493

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-01 01:59:10
Replay window: 2026-05-29
Mode: all
Episodes total: 93
Episodes analyzed: 93
Score >= 4 episodes: 33
Research candidates: 50

Classification counts:
- MOMENTUM_PRECURSOR: 28
- ACCELERATION_ZONE: 4
- PRE_EXPANSION: 15
- CONTEXT_ONLY: 16
- REVERSAL_WARNING: 15
- ACCUMULATION: 14
- ABSORPTION: 0
- FAILED_CONTEXT: 1
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00047 | episode_id=47 | classification=MOMENTUM_PRECURSOR | layers=3 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=1751.47
- CASE_00045 | episode_id=45 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1731.35
- CASE_00046 | episode_id=46 | classification=MOMENTUM_PRECURSOR | layers=2 | context=COMPRESSION_REGIME_TO_LOW_VOLATILITY | max_abs_4h=1676.23
- CASE_00044 | episode_id=44 | classification=REVERSAL_WARNING | layers=3 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1649.0
- CASE_00043 | episode_id=43 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1582.63

Counterexamples:
- CASE_00089 | episode_id=89 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=145.0

Preparation zone summary:
- Preparation candidates: 46
- Preparation zones found: 46
- HIGH preparation count: 22
- EXTREME preparation count: 3
- MOMENTUM_PRECURSOR with preparation: 10
- REVERSAL_WARNING with preparation: 9
- FAILED_CONTEXT with preparation: 1
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 44
- Return success count: 43
- Return failure count: 1
- Agreement true: 25
- Agreement false: 23
- Agreement unknown: 45
- High expansion count: 22
- Extreme expansion count: 14
- Average quiet score: 78.75268817
- Average range ratio: 0.65738177
- Best preparation cases: CASE_00047|CASE_00046|CASE_00045|CASE_00044|CASE_00042
- Failed preparation cases: CASE_00048|CASE_00078|CASE_00092

REVERSAL ANALYZER V1 summary:
- Direct reversals: 73
- Late reversals: 16
- Reversal after preparation return: 36
- Failed after return: 14
- HIGH reversal count: 13
- EXTREME reversal count: 56
- Average time to reversal: 16.50283258

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 12
- Expansion then reversal: 10
- Failed expansions: 0
- Direct reversals: 71
- Average expansion strength: 1.53763441
- Average expansion to reversal ratio: 1.94161617

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-01 11:57:00
Replay window: 2026-05-25 -> 2026-06-01
Mode: all
Episodes total: 634
Episodes analyzed: 634
Score >= 4 episodes: 177
Research candidates: 305

Classification counts:
- MOMENTUM_PRECURSOR: 173
- ACCELERATION_ZONE: 18
- PRE_EXPANSION: 109
- CONTEXT_ONLY: 120
- REVERSAL_WARNING: 104
- ACCUMULATION: 103
- ABSORPTION: 1
- FAILED_CONTEXT: 6
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00108 | episode_id=108 | classification=ACCELERATION_ZONE | layers=2 | context=DISTRIBUTION_SHIFT | max_abs_4h=2095.63
- CASE_00107 | episode_id=107 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2079.64
- CASE_00109 | episode_id=109 | classification=MOMENTUM_PRECURSOR | layers=2 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=2046.3
- CASE_00106 | episode_id=106 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1952.53
- CASE_00433 | episode_id=433 | classification=MOMENTUM_PRECURSOR | layers=3 | context=DISTRIBUTION_COMPRESSION_SHIFT | max_abs_4h=1856.15

Counterexamples:
- CASE_00271 | episode_id=271 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=300.49
- CASE_00492 | episode_id=492 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=125.39
- CASE_00226 | episode_id=226 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=440.88
- CASE_00309 | episode_id=309 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=552.85
- CASE_00508 | episode_id=508 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=150.99

Preparation zone summary:
- Preparation candidates: 338
- Preparation zones found: 338
- HIGH preparation count: 162
- EXTREME preparation count: 25
- MOMENTUM_PRECURSOR with preparation: 95
- REVERSAL_WARNING with preparation: 51
- FAILED_CONTEXT with preparation: 3
- PRE_EXPANSION with preparation: 54

HYPOTHESIS_02 revisit summary:
- Return count: 337
- Return success count: 337
- Return failure count: 0
- Agreement true: 127
- Agreement false: 128
- Agreement unknown: 379
- High expansion count: 86
- Extreme expansion count: 65
- Average quiet score: 81.06309148
- Average range ratio: 0.63100127
- Best preparation cases: CASE_00433|CASE_00434|CASE_00432|CASE_00281|CASE_00431
- Failed preparation cases: CASE_00600

REVERSAL ANALYZER V1 summary:
- Direct reversals: 526
- Late reversals: 82
- Reversal after preparation return: 266
- Failed after return: 61
- HIGH reversal count: 213
- EXTREME reversal count: 281
- Average time to reversal: 10.55521557

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 47
- Expansion then reversal: 47
- Failed expansions: 29
- Direct reversals: 511
- Average expansion strength: 1.06309148
- Average expansion to reversal ratio: 3.60383642

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-02 19:51:57
Replay window: 2026-06-02
Mode: score4plus
Episodes total: 148
Episodes analyzed: 50
Score >= 4 episodes: 50
Research candidates: 50

Classification counts:
- MOMENTUM_PRECURSOR: 8
- ACCELERATION_ZONE: 4
- PRE_EXPANSION: 8
- CONTEXT_ONLY: 4
- REVERSAL_WARNING: 10
- ACCUMULATION: 14
- ABSORPTION: 0
- FAILED_CONTEXT: 2
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00062 | episode_id=62 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2315.24
- CASE_00061 | episode_id=61 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2262.58
- CASE_00063 | episode_id=63 | classification=REVERSAL_WARNING | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=2130.65
- CASE_00065 | episode_id=65 | classification=ACCUMULATION | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1959.52
- CASE_00057 | episode_id=57 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1869.11

Counterexamples:
- CASE_00146 | episode_id=146 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=499.58
- CASE_00145 | episode_id=145 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=321.04

Preparation zone summary:
- Preparation candidates: 34
- Preparation zones found: 34
- HIGH preparation count: 12
- EXTREME preparation count: 4
- MOMENTUM_PRECURSOR with preparation: 5
- REVERSAL_WARNING with preparation: 7
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 5

HYPOTHESIS_02 revisit summary:
- Return count: 31
- Return success count: 30
- Return failure count: 1
- Agreement true: 25
- Agreement false: 21
- Agreement unknown: 4
- High expansion count: 3
- Extreme expansion count: 26
- Average quiet score: 85.18
- Average range ratio: 0.58291269
- Best preparation cases: CASE_00061|CASE_00057|CASE_00073|CASE_00075|CASE_00076
- Failed preparation cases: CASE_00071|CASE_00084|CASE_00143|CASE_00145

REVERSAL ANALYZER V1 summary:
- Direct reversals: 35
- Late reversals: 8
- Reversal after preparation return: 21
- Failed after return: 16
- HIGH reversal count: 4
- EXTREME reversal count: 25
- Average time to reversal: 13.77234419

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 13
- Expansion then reversal: 5
- Failed expansions: 1
- Direct reversals: 31
- Average expansion strength: 2.64
- Average expansion to reversal ratio: 10.50018955

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-03 17:36:22
Replay window: 2026-05-20 -> 2026-06-01
Mode: score4plus
Episodes total: 1041
Episodes analyzed: 276
Score >= 4 episodes: 276
Research candidates: 276

Classification counts:
- MOMENTUM_PRECURSOR: 37
- ACCELERATION_ZONE: 17
- PRE_EXPANSION: 52
- CONTEXT_ONLY: 36
- REVERSAL_WARNING: 51
- ACCUMULATION: 66
- ABSORPTION: 2
- FAILED_CONTEXT: 15
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00478 | episode_id=478 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2100.36
- CASE_00477 | episode_id=477 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1947.38
- CASE_00780 | episode_id=780 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1802.64
- CASE_00474 | episode_id=474 | classification=REVERSAL_WARNING | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1785.27
- CASE_00473 | episode_id=473 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1674.87

Counterexamples:
- CASE_00514 | episode_id=514 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=281.26
- CASE_00632 | episode_id=632 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=395.02
- CASE_00591 | episode_id=591 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=451.49
- CASE_00841 | episode_id=841 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=126.43
- CASE_00218 | episode_id=218 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=303.68

Preparation zone summary:
- Preparation candidates: 147
- Preparation zones found: 147
- HIGH preparation count: 64
- EXTREME preparation count: 16
- MOMENTUM_PRECURSOR with preparation: 18
- REVERSAL_WARNING with preparation: 22
- FAILED_CONTEXT with preparation: 5
- PRE_EXPANSION with preparation: 33

HYPOTHESIS_02 revisit summary:
- Return count: 147
- Return success count: 147
- Return failure count: 0
- Agreement true: 116
- Agreement false: 128
- Agreement unknown: 32
- High expansion count: 66
- Extreme expansion count: 73
- Average quiet score: 80.47101449
- Average range ratio: 0.63283424
- Best preparation cases: CASE_00780|CASE_00481|CASE_00778|CASE_00774|CASE_00287
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 203
- Late reversals: 56
- Reversal after preparation return: 113
- Failed after return: 68
- HIGH reversal count: 96
- EXTREME reversal count: 84
- Average time to reversal: 16.30225309

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 38
- Expansion then reversal: 41
- Failed expansions: 9
- Direct reversals: 188
- Average expansion strength: 2.34782609
- Average expansion to reversal ratio: 4.04623967

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 13:39:52
Replay window: 2026-04-30 -> 2026-05-02
Mode: score4plus
Episodes total: 194
Episodes analyzed: 48
Score >= 4 episodes: 48
Research candidates: 48

Classification counts:
- MOMENTUM_PRECURSOR: 7
- ACCELERATION_ZONE: 0
- PRE_EXPANSION: 12
- CONTEXT_ONLY: 3
- REVERSAL_WARNING: 13
- ACCUMULATION: 11
- ABSORPTION: 0
- FAILED_CONTEXT: 2
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00009 | episode_id=9 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1032.15
- CASE_00070 | episode_id=70 | classification=MOMENTUM_PRECURSOR | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1021.87
- CASE_00071 | episode_id=71 | classification=REVERSAL_WARNING | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=986.97
- CASE_00072 | episode_id=72 | classification=ACCUMULATION | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=936.61
- CASE_00073 | episode_id=73 | classification=REVERSAL_WARNING | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=918.69

Counterexamples:
- CASE_00079 | episode_id=79 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=511.62
- CASE_00011 | episode_id=11 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=362.47

Preparation zone summary:
- Preparation candidates: 24
- Preparation zones found: 24
- HIGH preparation count: 12
- EXTREME preparation count: 1
- MOMENTUM_PRECURSOR with preparation: 2
- REVERSAL_WARNING with preparation: 8
- FAILED_CONTEXT with preparation: 0
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 22
- Return success count: 22
- Return failure count: 0
- Agreement true: 15
- Agreement false: 21
- Agreement unknown: 12
- High expansion count: 8
- Extreme expansion count: 8
- Average quiet score: 79.91666667
- Average range ratio: 0.65037961
- Best preparation cases: CASE_00024|CASE_00189|CASE_00103|CASE_00192|CASE_00019
- Failed preparation cases: CASE_00100|CASE_00193

REVERSAL ANALYZER V1 summary:
- Direct reversals: 34
- Late reversals: 11
- Reversal after preparation return: 18
- Failed after return: 7
- HIGH reversal count: 17
- EXTREME reversal count: 13
- Average time to reversal: 16.34358889

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 9
- Expansion then reversal: 3
- Failed expansions: 6
- Direct reversals: 30
- Average expansion strength: 1.70833333
- Average expansion to reversal ratio: 1.30048693

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 13:43:16
Replay window: 2026-05-03 -> 2026-05-05
Mode: score4plus
Episodes total: 271
Episodes analyzed: 71
Score >= 4 episodes: 71
Research candidates: 71

Classification counts:
- MOMENTUM_PRECURSOR: 9
- ACCELERATION_ZONE: 1
- PRE_EXPANSION: 9
- CONTEXT_ONLY: 9
- REVERSAL_WARNING: 15
- ACCUMULATION: 14
- ABSORPTION: 1
- FAILED_CONTEXT: 13
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00055 | episode_id=55 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2254.08
- CASE_00045 | episode_id=45 | classification=MOMENTUM_PRECURSOR | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1851.01
- CASE_00095 | episode_id=95 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1738.28
- CASE_00043 | episode_id=43 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1706.17
- CASE_00101 | episode_id=101 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1647.04

Counterexamples:
- CASE_00109 | episode_id=109 | classification=FAILED_CONTEXT | layers=5 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=635.56
- CASE_00139 | episode_id=139 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=741.27
- CASE_00114 | episode_id=114 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=976.73
- CASE_00061 | episode_id=61 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=832.91
- CASE_00064 | episode_id=64 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=617.47

Preparation zone summary:
- Preparation candidates: 37
- Preparation zones found: 37
- HIGH preparation count: 14
- EXTREME preparation count: 3
- MOMENTUM_PRECURSOR with preparation: 4
- REVERSAL_WARNING with preparation: 7
- FAILED_CONTEXT with preparation: 7
- PRE_EXPANSION with preparation: 5

HYPOTHESIS_02 revisit summary:
- Return count: 37
- Return success count: 37
- Return failure count: 0
- Agreement true: 23
- Agreement false: 33
- Agreement unknown: 15
- High expansion count: 11
- Extreme expansion count: 21
- Average quiet score: 80.50704225
- Average range ratio: 0.65263724
- Best preparation cases: CASE_00055|CASE_00095|CASE_00124|CASE_00101|CASE_00129
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 55
- Late reversals: 13
- Reversal after preparation return: 27
- Failed after return: 17
- HIGH reversal count: 12
- EXTREME reversal count: 42
- Average time to reversal: 6.62562819

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 8
- Expansion then reversal: 8
- Failed expansions: 3
- Direct reversals: 52
- Average expansion strength: 2.09859155
- Average expansion to reversal ratio: 2.14606307

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 13:47:19
Replay window: 2026-05-06 -> 2026-05-08
Mode: score4plus
Episodes total: 263
Episodes analyzed: 70
Score >= 4 episodes: 70
Research candidates: 70

Classification counts:
- MOMENTUM_PRECURSOR: 9
- ACCELERATION_ZONE: 2
- PRE_EXPANSION: 16
- CONTEXT_ONLY: 6
- REVERSAL_WARNING: 18
- ACCUMULATION: 16
- ABSORPTION: 0
- FAILED_CONTEXT: 3
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00054 | episode_id=54 | classification=REVERSAL_WARNING | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1462.05
- CASE_00051 | episode_id=51 | classification=MOMENTUM_PRECURSOR | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1213.73
- CASE_00137 | episode_id=137 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1162.33
- CASE_00033 | episode_id=33 | classification=ACCUMULATION | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=1125.62
- CASE_00028 | episode_id=28 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1089.7

Counterexamples:
- CASE_00242 | episode_id=242 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=245.94
- CASE_00099 | episode_id=99 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=281.34
- CASE_00263 | episode_id=263 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=13.42

Preparation zone summary:
- Preparation candidates: 42
- Preparation zones found: 42
- HIGH preparation count: 23
- EXTREME preparation count: 0
- MOMENTUM_PRECURSOR with preparation: 6
- REVERSAL_WARNING with preparation: 11
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 11

HYPOTHESIS_02 revisit summary:
- Return count: 42
- Return success count: 40
- Return failure count: 2
- Agreement true: 33
- Agreement false: 26
- Agreement unknown: 11
- High expansion count: 16
- Extreme expansion count: 21
- Average quiet score: 84.18571429
- Average range ratio: 0.62308855
- Best preparation cases: CASE_00054|CASE_00137|CASE_00051|CASE_00049|CASE_00050
- Failed preparation cases: CASE_00261|CASE_00263

REVERSAL ANALYZER V1 summary:
- Direct reversals: 50
- Late reversals: 14
- Reversal after preparation return: 28
- Failed after return: 18
- HIGH reversal count: 16
- EXTREME reversal count: 27
- Average time to reversal: 13.8478026

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 8
- Expansion then reversal: 12
- Failed expansions: 1
- Direct reversals: 48
- Average expansion strength: 2.37142857
- Average expansion to reversal ratio: 4.23702005

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 13:50:22
Replay window: 2026-05-06 -> 2026-05-08
Mode: score4plus
Episodes total: 263
Episodes analyzed: 70
Score >= 4 episodes: 70
Research candidates: 70

Classification counts:
- MOMENTUM_PRECURSOR: 9
- ACCELERATION_ZONE: 2
- PRE_EXPANSION: 16
- CONTEXT_ONLY: 6
- REVERSAL_WARNING: 18
- ACCUMULATION: 16
- ABSORPTION: 0
- FAILED_CONTEXT: 3
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00054 | episode_id=54 | classification=REVERSAL_WARNING | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1462.05
- CASE_00051 | episode_id=51 | classification=MOMENTUM_PRECURSOR | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1213.73
- CASE_00137 | episode_id=137 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1162.33
- CASE_00033 | episode_id=33 | classification=ACCUMULATION | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=1125.62
- CASE_00028 | episode_id=28 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1089.7

Counterexamples:
- CASE_00242 | episode_id=242 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=245.94
- CASE_00099 | episode_id=99 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=281.34
- CASE_00263 | episode_id=263 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=13.42

Preparation zone summary:
- Preparation candidates: 42
- Preparation zones found: 42
- HIGH preparation count: 23
- EXTREME preparation count: 0
- MOMENTUM_PRECURSOR with preparation: 6
- REVERSAL_WARNING with preparation: 11
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 11

HYPOTHESIS_02 revisit summary:
- Return count: 42
- Return success count: 40
- Return failure count: 2
- Agreement true: 33
- Agreement false: 26
- Agreement unknown: 11
- High expansion count: 16
- Extreme expansion count: 21
- Average quiet score: 84.18571429
- Average range ratio: 0.62308855
- Best preparation cases: CASE_00054|CASE_00137|CASE_00051|CASE_00049|CASE_00050
- Failed preparation cases: CASE_00261|CASE_00263

REVERSAL ANALYZER V1 summary:
- Direct reversals: 50
- Late reversals: 14
- Reversal after preparation return: 28
- Failed after return: 18
- HIGH reversal count: 16
- EXTREME reversal count: 27
- Average time to reversal: 13.8478026

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 8
- Expansion then reversal: 12
- Failed expansions: 1
- Direct reversals: 48
- Average expansion strength: 2.37142857
- Average expansion to reversal ratio: 4.23702005

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 13:51:39
Replay window: 2026-05-09 -> 2026-05-11
Mode: score4plus
Episodes total: 198
Episodes analyzed: 43
Score >= 4 episodes: 43
Research candidates: 43

Classification counts:
- MOMENTUM_PRECURSOR: 6
- ACCELERATION_ZONE: 2
- PRE_EXPANSION: 6
- CONTEXT_ONLY: 6
- REVERSAL_WARNING: 10
- ACCUMULATION: 11
- ABSORPTION: 0
- FAILED_CONTEXT: 2
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00077 | episode_id=77 | classification=ACCUMULATION | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1909.18
- CASE_00160 | episode_id=160 | classification=REVERSAL_WARNING | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1561.21
- CASE_00076 | episode_id=76 | classification=ACCELERATION_ZONE | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1462.99
- CASE_00069 | episode_id=69 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1233.02
- CASE_00086 | episode_id=86 | classification=MOMENTUM_PRECURSOR | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1204.48

Counterexamples:
- CASE_00125 | episode_id=125 | classification=FAILED_CONTEXT | layers=7 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=371.92
- CASE_00126 | episode_id=126 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=416.91

Preparation zone summary:
- Preparation candidates: 27
- Preparation zones found: 27
- HIGH preparation count: 14
- EXTREME preparation count: 0
- MOMENTUM_PRECURSOR with preparation: 3
- REVERSAL_WARNING with preparation: 7
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 4

HYPOTHESIS_02 revisit summary:
- Return count: 27
- Return success count: 27
- Return failure count: 0
- Agreement true: 20
- Agreement false: 16
- Agreement unknown: 7
- High expansion count: 6
- Extreme expansion count: 13
- Average quiet score: 84.60465116
- Average range ratio: 0.61070451
- Best preparation cases: CASE_00076|CASE_00086|CASE_00069|CASE_00111|CASE_00087
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 27
- Late reversals: 14
- Reversal after preparation return: 25
- Failed after return: 13
- HIGH reversal count: 12
- EXTREME reversal count: 12
- Average time to reversal: 31.92833455

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 10
- Expansion then reversal: 8
- Failed expansions: 1
- Direct reversals: 24
- Average expansion strength: 2.1627907
- Average expansion to reversal ratio: 2.47913728

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 13:54:50
Replay window: 2026-05-09 -> 2026-05-11
Mode: score4plus
Episodes total: 198
Episodes analyzed: 43
Score >= 4 episodes: 43
Research candidates: 43

Classification counts:
- MOMENTUM_PRECURSOR: 6
- ACCELERATION_ZONE: 2
- PRE_EXPANSION: 6
- CONTEXT_ONLY: 6
- REVERSAL_WARNING: 10
- ACCUMULATION: 11
- ABSORPTION: 0
- FAILED_CONTEXT: 2
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00077 | episode_id=77 | classification=ACCUMULATION | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1909.18
- CASE_00160 | episode_id=160 | classification=REVERSAL_WARNING | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1561.21
- CASE_00076 | episode_id=76 | classification=ACCELERATION_ZONE | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1462.99
- CASE_00069 | episode_id=69 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1233.02
- CASE_00086 | episode_id=86 | classification=MOMENTUM_PRECURSOR | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1204.48

Counterexamples:
- CASE_00125 | episode_id=125 | classification=FAILED_CONTEXT | layers=7 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=371.92
- CASE_00126 | episode_id=126 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=416.91

Preparation zone summary:
- Preparation candidates: 27
- Preparation zones found: 27
- HIGH preparation count: 14
- EXTREME preparation count: 0
- MOMENTUM_PRECURSOR with preparation: 3
- REVERSAL_WARNING with preparation: 7
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 4

HYPOTHESIS_02 revisit summary:
- Return count: 27
- Return success count: 27
- Return failure count: 0
- Agreement true: 20
- Agreement false: 16
- Agreement unknown: 7
- High expansion count: 6
- Extreme expansion count: 13
- Average quiet score: 84.60465116
- Average range ratio: 0.61070451
- Best preparation cases: CASE_00076|CASE_00086|CASE_00069|CASE_00111|CASE_00087
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 27
- Late reversals: 14
- Reversal after preparation return: 25
- Failed after return: 13
- HIGH reversal count: 12
- EXTREME reversal count: 12
- Average time to reversal: 31.92833455

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 10
- Expansion then reversal: 8
- Failed expansions: 1
- Direct reversals: 24
- Average expansion strength: 2.1627907
- Average expansion to reversal ratio: 2.47913728

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 13:56:57
Replay window: 2026-05-12 -> 2026-05-14
Mode: score4plus
Episodes total: 226
Episodes analyzed: 69
Score >= 4 episodes: 69
Research candidates: 69

Classification counts:
- MOMENTUM_PRECURSOR: 10
- ACCELERATION_ZONE: 3
- PRE_EXPANSION: 14
- CONTEXT_ONLY: 10
- REVERSAL_WARNING: 14
- ACCUMULATION: 15
- ABSORPTION: 0
- FAILED_CONTEXT: 3
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00189 | episode_id=189 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2266.94
- CASE_00188 | episode_id=188 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2123.78
- CASE_00193 | episode_id=193 | classification=ACCUMULATION | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2114.43
- CASE_00197 | episode_id=197 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1843.13
- CASE_00187 | episode_id=187 | classification=MOMENTUM_PRECURSOR | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1831.91

Counterexamples:
- CASE_00094 | episode_id=94 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=246.27
- CASE_00215 | episode_id=215 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=546.93
- CASE_00225 | episode_id=225 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=172.13

Preparation zone summary:
- Preparation candidates: 36
- Preparation zones found: 36
- HIGH preparation count: 16
- EXTREME preparation count: 7
- MOMENTUM_PRECURSOR with preparation: 5
- REVERSAL_WARNING with preparation: 8
- FAILED_CONTEXT with preparation: 1
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 36
- Return success count: 36
- Return failure count: 0
- Agreement true: 26
- Agreement false: 29
- Agreement unknown: 14
- High expansion count: 14
- Extreme expansion count: 17
- Average quiet score: 82.31884058
- Average range ratio: 0.63789156
- Best preparation cases: CASE_00120|CASE_00184|CASE_00124|CASE_00203|CASE_00128
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 49
- Late reversals: 14
- Reversal after preparation return: 23
- Failed after return: 14
- HIGH reversal count: 20
- EXTREME reversal count: 29
- Average time to reversal: 13.22723148

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 8
- Expansion then reversal: 11
- Failed expansions: 3
- Direct reversals: 47
- Average expansion strength: 2.11594203
- Average expansion to reversal ratio: 4.68254658

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 13:59:51
Replay window: 2026-05-12 -> 2026-05-14
Mode: score4plus
Episodes total: 226
Episodes analyzed: 69
Score >= 4 episodes: 69
Research candidates: 69

Classification counts:
- MOMENTUM_PRECURSOR: 10
- ACCELERATION_ZONE: 3
- PRE_EXPANSION: 14
- CONTEXT_ONLY: 10
- REVERSAL_WARNING: 14
- ACCUMULATION: 15
- ABSORPTION: 0
- FAILED_CONTEXT: 3
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00189 | episode_id=189 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2266.94
- CASE_00188 | episode_id=188 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2123.78
- CASE_00193 | episode_id=193 | classification=ACCUMULATION | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2114.43
- CASE_00197 | episode_id=197 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1843.13
- CASE_00187 | episode_id=187 | classification=MOMENTUM_PRECURSOR | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1831.91

Counterexamples:
- CASE_00094 | episode_id=94 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=246.27
- CASE_00215 | episode_id=215 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=546.93
- CASE_00225 | episode_id=225 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=172.13

Preparation zone summary:
- Preparation candidates: 36
- Preparation zones found: 36
- HIGH preparation count: 16
- EXTREME preparation count: 7
- MOMENTUM_PRECURSOR with preparation: 5
- REVERSAL_WARNING with preparation: 8
- FAILED_CONTEXT with preparation: 1
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 36
- Return success count: 36
- Return failure count: 0
- Agreement true: 26
- Agreement false: 29
- Agreement unknown: 14
- High expansion count: 14
- Extreme expansion count: 17
- Average quiet score: 82.31884058
- Average range ratio: 0.63789156
- Best preparation cases: CASE_00120|CASE_00184|CASE_00124|CASE_00203|CASE_00128
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 49
- Late reversals: 14
- Reversal after preparation return: 23
- Failed after return: 14
- HIGH reversal count: 20
- EXTREME reversal count: 29
- Average time to reversal: 13.22723148

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 8
- Expansion then reversal: 11
- Failed expansions: 3
- Direct reversals: 47
- Average expansion strength: 2.11594203
- Average expansion to reversal ratio: 4.68254658

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 14:01:54
Replay window: 2026-05-15 -> 2026-05-17
Mode: score4plus
Episodes total: 205
Episodes analyzed: 58
Score >= 4 episodes: 58
Research candidates: 58

Classification counts:
- MOMENTUM_PRECURSOR: 6
- ACCELERATION_ZONE: 5
- PRE_EXPANSION: 9
- CONTEXT_ONLY: 8
- REVERSAL_WARNING: 13
- ACCUMULATION: 12
- ABSORPTION: 1
- FAILED_CONTEXT: 4
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00037 | episode_id=37 | classification=REVERSAL_WARNING | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1731.08
- CASE_00192 | episode_id=192 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1654.9
- CASE_00185 | episode_id=185 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1651.57
- CASE_00038 | episode_id=38 | classification=MOMENTUM_PRECURSOR | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1549.38
- CASE_00039 | episode_id=39 | classification=ACCELERATION_ZONE | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1478.14

Counterexamples:
- CASE_00049 | episode_id=49 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=615.48
- CASE_00048 | episode_id=48 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=503.61
- CASE_00055 | episode_id=55 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=747.19
- CASE_00204 | episode_id=204 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=341.2

Preparation zone summary:
- Preparation candidates: 35
- Preparation zones found: 35
- HIGH preparation count: 11
- EXTREME preparation count: 3
- MOMENTUM_PRECURSOR with preparation: 2
- REVERSAL_WARNING with preparation: 10
- FAILED_CONTEXT with preparation: 3
- PRE_EXPANSION with preparation: 5

HYPOTHESIS_02 revisit summary:
- Return count: 33
- Return success count: 33
- Return failure count: 0
- Agreement true: 21
- Agreement false: 28
- Agreement unknown: 9
- High expansion count: 11
- Extreme expansion count: 9
- Average quiet score: 82.10344828
- Average range ratio: 0.64756466
- Best preparation cases: CASE_00037|CASE_00185|CASE_00055|CASE_00023|CASE_00168
- Failed preparation cases: CASE_00038|CASE_00202

REVERSAL ANALYZER V1 summary:
- Direct reversals: 43
- Late reversals: 12
- Reversal after preparation return: 26
- Failed after return: 15
- HIGH reversal count: 10
- EXTREME reversal count: 22
- Average time to reversal: 21.09246788

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 7
- Expansion then reversal: 9
- Failed expansions: 1
- Direct reversals: 41
- Average expansion strength: 1.9137931
- Average expansion to reversal ratio: 2.35778638

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 14:06:24
Replay window: 2026-05-15 -> 2026-05-17
Mode: score4plus
Episodes total: 205
Episodes analyzed: 58
Score >= 4 episodes: 58
Research candidates: 58

Classification counts:
- MOMENTUM_PRECURSOR: 6
- ACCELERATION_ZONE: 5
- PRE_EXPANSION: 9
- CONTEXT_ONLY: 8
- REVERSAL_WARNING: 13
- ACCUMULATION: 12
- ABSORPTION: 1
- FAILED_CONTEXT: 4
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00037 | episode_id=37 | classification=REVERSAL_WARNING | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1731.08
- CASE_00192 | episode_id=192 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1654.9
- CASE_00185 | episode_id=185 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1651.57
- CASE_00038 | episode_id=38 | classification=MOMENTUM_PRECURSOR | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1549.38
- CASE_00039 | episode_id=39 | classification=ACCELERATION_ZONE | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1478.14

Counterexamples:
- CASE_00049 | episode_id=49 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=615.48
- CASE_00048 | episode_id=48 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=503.61
- CASE_00055 | episode_id=55 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=747.19
- CASE_00204 | episode_id=204 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=341.2

Preparation zone summary:
- Preparation candidates: 35
- Preparation zones found: 35
- HIGH preparation count: 11
- EXTREME preparation count: 3
- MOMENTUM_PRECURSOR with preparation: 2
- REVERSAL_WARNING with preparation: 10
- FAILED_CONTEXT with preparation: 3
- PRE_EXPANSION with preparation: 5

HYPOTHESIS_02 revisit summary:
- Return count: 33
- Return success count: 33
- Return failure count: 0
- Agreement true: 21
- Agreement false: 28
- Agreement unknown: 9
- High expansion count: 11
- Extreme expansion count: 9
- Average quiet score: 82.10344828
- Average range ratio: 0.64756466
- Best preparation cases: CASE_00037|CASE_00185|CASE_00055|CASE_00023|CASE_00168
- Failed preparation cases: CASE_00038|CASE_00202

REVERSAL ANALYZER V1 summary:
- Direct reversals: 43
- Late reversals: 12
- Reversal after preparation return: 26
- Failed after return: 15
- HIGH reversal count: 10
- EXTREME reversal count: 22
- Average time to reversal: 21.09246788

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 7
- Expansion then reversal: 9
- Failed expansions: 1
- Direct reversals: 41
- Average expansion strength: 1.9137931
- Average expansion to reversal ratio: 2.35778638

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 14:09:27
Replay window: 2026-05-15 -> 2026-05-17
Mode: score4plus
Episodes total: 205
Episodes analyzed: 58
Score >= 4 episodes: 58
Research candidates: 58

Classification counts:
- MOMENTUM_PRECURSOR: 1
- ACCELERATION_ZONE: 4
- PRE_EXPANSION: 0
- CONTEXT_ONLY: 0
- REVERSAL_WARNING: 1
- ACCUMULATION: 0
- ABSORPTION: 13
- FAILED_CONTEXT: 39
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00192 | episode_id=192 | classification=ACCELERATION_ZONE | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1651.88
- CASE_00198 | episode_id=198 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1195.96
- CASE_00197 | episode_id=197 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1134.99
- CASE_00199 | episode_id=199 | classification=ACCELERATION_ZONE | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1041.71
- CASE_00204 | episode_id=204 | classification=ACCELERATION_ZONE | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=486.6

Counterexamples:
- CASE_00044 | episode_id=44 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=
- CASE_00086 | episode_id=86 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=
- CASE_00004 | episode_id=4 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=
- CASE_00033 | episode_id=33 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=
- CASE_00040 | episode_id=40 | classification=FAILED_CONTEXT | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=

Preparation zone summary:
- Preparation candidates: 26
- Preparation zones found: 26
- HIGH preparation count: 6
- EXTREME preparation count: 4
- MOMENTUM_PRECURSOR with preparation: 0
- REVERSAL_WARNING with preparation: 0
- FAILED_CONTEXT with preparation: 19
- PRE_EXPANSION with preparation: 0

HYPOTHESIS_02 revisit summary:
- Return count: 26
- Return success count: 26
- Return failure count: 0
- Agreement true: 23
- Agreement false: 26
- Agreement unknown: 9
- High expansion count: 2
- Extreme expansion count: 3
- Average quiet score: 78.4137931
- Average range ratio: 0.66932359
- Best preparation cases: CASE_00042|CASE_00040|CASE_00044|CASE_00204|CASE_00202
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 0
- Late reversals: 3
- Reversal after preparation return: 1
- Failed after return: 11
- HIGH reversal count: 2
- EXTREME reversal count: 1
- Average time to reversal: 57.88076667

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 3
- Expansion then reversal: 1
- Failed expansions: 2
- Direct reversals: 0
- Average expansion strength: 0.31034483
- Average expansion to reversal ratio: 0.41348523

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 14:11:37
Replay window: 2026-05-18 -> 2026-05-20
Mode: score4plus
Episodes total: 272
Episodes analyzed: 75
Score >= 4 episodes: 75
Research candidates: 75

Classification counts:
- MOMENTUM_PRECURSOR: 13
- ACCELERATION_ZONE: 1
- PRE_EXPANSION: 14
- CONTEXT_ONLY: 8
- REVERSAL_WARNING: 14
- ACCUMULATION: 16
- ABSORPTION: 2
- FAILED_CONTEXT: 7
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00066 | episode_id=66 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DISTRIBUTION_SHIFT | max_abs_4h=1655.68
- CASE_00065 | episode_id=65 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1508.41
- CASE_00063 | episode_id=63 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1377.95
- CASE_00068 | episode_id=68 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1355.85
- CASE_00064 | episode_id=64 | classification=REVERSAL_WARNING | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1259.92

Counterexamples:
- CASE_00132 | episode_id=132 | classification=FAILED_CONTEXT | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=338.48
- CASE_00180 | episode_id=180 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=166.98
- CASE_00235 | episode_id=235 | classification=FAILED_CONTEXT | layers=5 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=461.99
- CASE_00005 | episode_id=5 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=316.39
- CASE_00231 | episode_id=231 | classification=FAILED_CONTEXT | layers=4 | context=CLIMACTIC_VOLUME | max_abs_4h=452.13

Preparation zone summary:
- Preparation candidates: 37
- Preparation zones found: 37
- HIGH preparation count: 16
- EXTREME preparation count: 1
- MOMENTUM_PRECURSOR with preparation: 9
- REVERSAL_WARNING with preparation: 7
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 37
- Return success count: 37
- Return failure count: 0
- Agreement true: 36
- Agreement false: 33
- Agreement unknown: 6
- High expansion count: 24
- Extreme expansion count: 14
- Average quiet score: 81.73333333
- Average range ratio: 0.64944234
- Best preparation cases: CASE_00066|CASE_00068|CASE_00070|CASE_00163|CASE_00081
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 59
- Late reversals: 10
- Reversal after preparation return: 29
- Failed after return: 14
- HIGH reversal count: 24
- EXTREME reversal count: 22
- Average time to reversal: 13.14049638

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 9
- Expansion then reversal: 7
- Failed expansions: 2
- Direct reversals: 57
- Average expansion strength: 2.29333333
- Average expansion to reversal ratio: 25.34667456

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 14:17:03
Replay window: 2026-05-18 -> 2026-05-20
Mode: score4plus
Episodes total: 272
Episodes analyzed: 75
Score >= 4 episodes: 75
Research candidates: 75

Classification counts:
- MOMENTUM_PRECURSOR: 13
- ACCELERATION_ZONE: 1
- PRE_EXPANSION: 14
- CONTEXT_ONLY: 8
- REVERSAL_WARNING: 14
- ACCUMULATION: 16
- ABSORPTION: 2
- FAILED_CONTEXT: 7
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00066 | episode_id=66 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DISTRIBUTION_SHIFT | max_abs_4h=1655.68
- CASE_00065 | episode_id=65 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1508.41
- CASE_00063 | episode_id=63 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1377.95
- CASE_00068 | episode_id=68 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1355.85
- CASE_00064 | episode_id=64 | classification=REVERSAL_WARNING | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1259.92

Counterexamples:
- CASE_00132 | episode_id=132 | classification=FAILED_CONTEXT | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=338.48
- CASE_00180 | episode_id=180 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=166.98
- CASE_00235 | episode_id=235 | classification=FAILED_CONTEXT | layers=5 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=461.99
- CASE_00005 | episode_id=5 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=316.39
- CASE_00231 | episode_id=231 | classification=FAILED_CONTEXT | layers=4 | context=CLIMACTIC_VOLUME | max_abs_4h=452.13

Preparation zone summary:
- Preparation candidates: 37
- Preparation zones found: 37
- HIGH preparation count: 16
- EXTREME preparation count: 1
- MOMENTUM_PRECURSOR with preparation: 9
- REVERSAL_WARNING with preparation: 7
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 37
- Return success count: 37
- Return failure count: 0
- Agreement true: 36
- Agreement false: 33
- Agreement unknown: 6
- High expansion count: 24
- Extreme expansion count: 14
- Average quiet score: 81.73333333
- Average range ratio: 0.64944234
- Best preparation cases: CASE_00066|CASE_00068|CASE_00070|CASE_00163|CASE_00081
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 59
- Late reversals: 10
- Reversal after preparation return: 29
- Failed after return: 14
- HIGH reversal count: 24
- EXTREME reversal count: 22
- Average time to reversal: 13.14049638

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 9
- Expansion then reversal: 7
- Failed expansions: 2
- Direct reversals: 57
- Average expansion strength: 2.29333333
- Average expansion to reversal ratio: 25.34667456

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 14:18:43
Replay window: 2026-05-18 -> 2026-05-20
Mode: score4plus
Episodes total: 272
Episodes analyzed: 75
Score >= 4 episodes: 75
Research candidates: 75

Classification counts:
- MOMENTUM_PRECURSOR: 13
- ACCELERATION_ZONE: 1
- PRE_EXPANSION: 14
- CONTEXT_ONLY: 8
- REVERSAL_WARNING: 14
- ACCUMULATION: 16
- ABSORPTION: 2
- FAILED_CONTEXT: 7
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00066 | episode_id=66 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DISTRIBUTION_SHIFT | max_abs_4h=1655.68
- CASE_00065 | episode_id=65 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1508.41
- CASE_00063 | episode_id=63 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1377.95
- CASE_00068 | episode_id=68 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1355.85
- CASE_00064 | episode_id=64 | classification=REVERSAL_WARNING | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1259.92

Counterexamples:
- CASE_00132 | episode_id=132 | classification=FAILED_CONTEXT | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=338.48
- CASE_00180 | episode_id=180 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=166.98
- CASE_00235 | episode_id=235 | classification=FAILED_CONTEXT | layers=5 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=461.99
- CASE_00005 | episode_id=5 | classification=FAILED_CONTEXT | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=316.39
- CASE_00231 | episode_id=231 | classification=FAILED_CONTEXT | layers=4 | context=CLIMACTIC_VOLUME | max_abs_4h=452.13

Preparation zone summary:
- Preparation candidates: 37
- Preparation zones found: 37
- HIGH preparation count: 16
- EXTREME preparation count: 1
- MOMENTUM_PRECURSOR with preparation: 9
- REVERSAL_WARNING with preparation: 7
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 7

HYPOTHESIS_02 revisit summary:
- Return count: 37
- Return success count: 37
- Return failure count: 0
- Agreement true: 36
- Agreement false: 33
- Agreement unknown: 6
- High expansion count: 24
- Extreme expansion count: 14
- Average quiet score: 81.73333333
- Average range ratio: 0.64944234
- Best preparation cases: CASE_00066|CASE_00068|CASE_00070|CASE_00163|CASE_00081
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 59
- Late reversals: 10
- Reversal after preparation return: 29
- Failed after return: 14
- HIGH reversal count: 24
- EXTREME reversal count: 22
- Average time to reversal: 13.14049638

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 9
- Expansion then reversal: 7
- Failed expansions: 2
- Direct reversals: 57
- Average expansion strength: 2.29333333
- Average expansion to reversal ratio: 25.34667456

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 14:22:19
Replay window: 2026-05-18 -> 2026-05-20
Mode: score4plus
Episodes total: 272
Episodes analyzed: 75
Score >= 4 episodes: 75
Research candidates: 75

Classification counts:
- MOMENTUM_PRECURSOR: 1
- ACCELERATION_ZONE: 0
- PRE_EXPANSION: 0
- CONTEXT_ONLY: 0
- REVERSAL_WARNING: 1
- ACCUMULATION: 1
- ABSORPTION: 15
- FAILED_CONTEXT: 57
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00271 | episode_id=271 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=829.89
- CASE_00269 | episode_id=269 | classification=REVERSAL_WARNING | layers=4 | context=UNSTABLE_EXTREME_CONTEXT | max_abs_4h=822.17
- CASE_00268 | episode_id=268 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=702.12
- CASE_00265 | episode_id=265 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=86.19
- CASE_00263 | episode_id=263 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=36.5

Counterexamples:
- CASE_00033 | episode_id=33 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=
- CASE_00077 | episode_id=77 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=
- CASE_00221 | episode_id=221 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=
- CASE_00223 | episode_id=223 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=
- CASE_00174 | episode_id=174 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=

Preparation zone summary:
- Preparation candidates: 46
- Preparation zones found: 46
- HIGH preparation count: 20
- EXTREME preparation count: 12
- MOMENTUM_PRECURSOR with preparation: 1
- REVERSAL_WARNING with preparation: 1
- FAILED_CONTEXT with preparation: 34
- PRE_EXPANSION with preparation: 0

HYPOTHESIS_02 revisit summary:
- Return count: 46
- Return success count: 46
- Return failure count: 0
- Agreement true: 28
- Agreement false: 32
- Agreement unknown: 15
- High expansion count: 0
- Extreme expansion count: 0
- Average quiet score: 83.68
- Average range ratio: 0.57849132
- Best preparation cases: CASE_00268|CASE_00265|CASE_00263|CASE_00260|CASE_00251
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 0
- Late reversals: 4
- Reversal after preparation return: 0
- Failed after return: 22
- HIGH reversal count: 0
- EXTREME reversal count: 3
- Average time to reversal: 140.14139167

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 0
- Expansion then reversal: 0
- Failed expansions: 3
- Direct reversals: 0
- Average expansion strength: 0.02666667
- Average expansion to reversal ratio: 0.19329388

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 14:24:53
Replay window: 2026-05-21 -> 2026-05-23
Mode: score4plus
Episodes total: 223
Episodes analyzed: 63
Score >= 4 episodes: 63
Research candidates: 63

Classification counts:
- MOMENTUM_PRECURSOR: 6
- ACCELERATION_ZONE: 5
- PRE_EXPANSION: 13
- CONTEXT_ONLY: 11
- REVERSAL_WARNING: 9
- ACCUMULATION: 14
- ABSORPTION: 1
- FAILED_CONTEXT: 4
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00198 | episode_id=198 | classification=MOMENTUM_PRECURSOR | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1408.33
- CASE_00116 | episode_id=116 | classification=MOMENTUM_PRECURSOR | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1304.33
- CASE_00156 | episode_id=156 | classification=ACCUMULATION | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1286.85
- CASE_00121 | episode_id=121 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1191.0
- CASE_00036 | episode_id=36 | classification=REVERSAL_WARNING | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1128.42

Counterexamples:
- CASE_00223 | episode_id=223 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=190.28
- CASE_00004 | episode_id=4 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=212.46
- CASE_00005 | episode_id=5 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=244.48
- CASE_00206 | episode_id=206 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=720.85

Preparation zone summary:
- Preparation candidates: 32
- Preparation zones found: 32
- HIGH preparation count: 15
- EXTREME preparation count: 3
- MOMENTUM_PRECURSOR with preparation: 4
- REVERSAL_WARNING with preparation: 6
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 5

HYPOTHESIS_02 revisit summary:
- Return count: 31
- Return success count: 31
- Return failure count: 0
- Agreement true: 26
- Agreement false: 27
- Agreement unknown: 10
- High expansion count: 9
- Extreme expansion count: 19
- Average quiet score: 78.92063492
- Average range ratio: 0.65858615
- Best preparation cases: CASE_00198|CASE_00116|CASE_00156|CASE_00126|CASE_00121
- Failed preparation cases: CASE_00186

REVERSAL ANALYZER V1 summary:
- Direct reversals: 53
- Late reversals: 7
- Reversal after preparation return: 25
- Failed after return: 15
- HIGH reversal count: 19
- EXTREME reversal count: 18
- Average time to reversal: 6.57563389

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 10
- Expansion then reversal: 3
- Failed expansions: 4
- Direct reversals: 46
- Average expansion strength: 2.0952381
- Average expansion to reversal ratio: 4.25010326

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 14:25:00
Replay window: 2026-05-21 -> 2026-05-23
Mode: score4plus
Episodes total: 223
Episodes analyzed: 63
Score >= 4 episodes: 63
Research candidates: 63

Classification counts:
- MOMENTUM_PRECURSOR: 6
- ACCELERATION_ZONE: 5
- PRE_EXPANSION: 13
- CONTEXT_ONLY: 11
- REVERSAL_WARNING: 9
- ACCUMULATION: 14
- ABSORPTION: 1
- FAILED_CONTEXT: 4
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00198 | episode_id=198 | classification=MOMENTUM_PRECURSOR | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1408.33
- CASE_00116 | episode_id=116 | classification=MOMENTUM_PRECURSOR | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1304.33
- CASE_00156 | episode_id=156 | classification=ACCUMULATION | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1286.85
- CASE_00121 | episode_id=121 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1191.0
- CASE_00036 | episode_id=36 | classification=REVERSAL_WARNING | layers=5 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=1128.42

Counterexamples:
- CASE_00223 | episode_id=223 | classification=FAILED_CONTEXT | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=190.28
- CASE_00004 | episode_id=4 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=212.46
- CASE_00005 | episode_id=5 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=244.48
- CASE_00206 | episode_id=206 | classification=FAILED_CONTEXT | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=720.85

Preparation zone summary:
- Preparation candidates: 32
- Preparation zones found: 32
- HIGH preparation count: 15
- EXTREME preparation count: 3
- MOMENTUM_PRECURSOR with preparation: 4
- REVERSAL_WARNING with preparation: 6
- FAILED_CONTEXT with preparation: 2
- PRE_EXPANSION with preparation: 5

HYPOTHESIS_02 revisit summary:
- Return count: 31
- Return success count: 31
- Return failure count: 0
- Agreement true: 26
- Agreement false: 27
- Agreement unknown: 10
- High expansion count: 9
- Extreme expansion count: 19
- Average quiet score: 78.92063492
- Average range ratio: 0.65858615
- Best preparation cases: CASE_00198|CASE_00116|CASE_00156|CASE_00126|CASE_00121
- Failed preparation cases: CASE_00186

REVERSAL ANALYZER V1 summary:
- Direct reversals: 53
- Late reversals: 7
- Reversal after preparation return: 25
- Failed after return: 15
- HIGH reversal count: 19
- EXTREME reversal count: 18
- Average time to reversal: 6.57563389

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 10
- Expansion then reversal: 3
- Failed expansions: 4
- Direct reversals: 46
- Average expansion strength: 2.0952381
- Average expansion to reversal ratio: 4.25010326

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-04 21:40:17
Replay window: 2026-04-30 -> 2026-06-02
Mode: score4plus
Episodes total: 2782
Episodes analyzed: 793
Score >= 4 episodes: 793
Research candidates: 793

Classification counts:
- MOMENTUM_PRECURSOR: 107
- ACCELERATION_ZONE: 25
- PRE_EXPANSION: 151
- CONTEXT_ONLY: 90
- REVERSAL_WARNING: 171
- ACCUMULATION: 203
- ABSORPTION: 3
- FAILED_CONTEXT: 43
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_02666 | episode_id=2666 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2291.22
- CASE_02668 | episode_id=2668 | classification=REVERSAL_WARNING | layers=4 | context=DISTRIBUTION_SHIFT | max_abs_4h=2139.18
- CASE_01103 | episode_id=1103 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2134.07
- CASE_01097 | episode_id=1097 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2111.24
- CASE_02028 | episode_id=2028 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2088.54

Counterexamples:
- CASE_00079 | episode_id=79 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=511.62
- CASE_00997 | episode_id=997 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=229.33
- CASE_00851 | episode_id=851 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=388.38
- CASE_02217 | episode_id=2217 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=477.4
- CASE_02187 | episode_id=2187 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=378.44

Preparation zone summary:
- Preparation candidates: 465
- Preparation zones found: 465
- HIGH preparation count: 200
- EXTREME preparation count: 38
- MOMENTUM_PRECURSOR with preparation: 63
- REVERSAL_WARNING with preparation: 91
- FAILED_CONTEXT with preparation: 21
- PRE_EXPANSION with preparation: 81

HYPOTHESIS_02 revisit summary:
- Return count: 459
- Return success count: 459
- Return failure count: 0
- Agreement true: 318
- Agreement false: 339
- Agreement unknown: 136
- High expansion count: 171
- Extreme expansion count: 205
- Average quiet score: 82.95460277
- Average range ratio: 0.61576764
- Best preparation cases: CASE_00754|CASE_02672|CASE_02673|CASE_01188|CASE_01190
- Failed preparation cases: CASE_02510|CASE_02617|CASE_02618|CASE_02639|CASE_02678

REVERSAL ANALYZER V1 summary:
- Direct reversals: 581
- Late reversals: 161
- Reversal after preparation return: 330
- Failed after return: 183
- HIGH reversal count: 226
- EXTREME reversal count: 297
- Average time to reversal: 15.14046316

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 115
- Expansion then reversal: 97
- Failed expansions: 38
- Direct reversals: 542
- Average expansion strength: 2.17276166
- Average expansion to reversal ratio: 8.81030431

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-05 13:34:20
Replay window: 2026-04-01 -> 2026-04-30
Mode: score4plus
Episodes total: 2849
Episodes analyzed: 808
Score >= 4 episodes: 808
Research candidates: 808

Classification counts:
- MOMENTUM_PRECURSOR: 88
- ACCELERATION_ZONE: 31
- PRE_EXPANSION: 165
- CONTEXT_ONLY: 127
- REVERSAL_WARNING: 172
- ACCUMULATION: 187
- ABSORPTION: 3
- FAILED_CONTEXT: 35
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00780 | episode_id=780 | classification=MOMENTUM_PRECURSOR | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=3778.95
- CASE_00781 | episode_id=781 | classification=MOMENTUM_PRECURSOR | layers=4 | context=STRONG_VELOCITY_EXHAUSTION | max_abs_4h=3403.8
- CASE_00774 | episode_id=774 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=3171.75
- CASE_00787 | episode_id=787 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=3063.26
- CASE_00771 | episode_id=771 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2894.35

Counterexamples:
- CASE_01568 | episode_id=1568 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=600.25
- CASE_01253 | episode_id=1253 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=642.13
- CASE_01040 | episode_id=1040 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=405.08
- CASE_02609 | episode_id=2609 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=472.63
- CASE_01588 | episode_id=1588 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=333.18

Preparation zone summary:
- Preparation candidates: 493
- Preparation zones found: 493
- HIGH preparation count: 195
- EXTREME preparation count: 54
- MOMENTUM_PRECURSOR with preparation: 54
- REVERSAL_WARNING with preparation: 103
- FAILED_CONTEXT with preparation: 15
- PRE_EXPANSION with preparation: 101

HYPOTHESIS_02 revisit summary:
- Return count: 490
- Return success count: 486
- Return failure count: 4
- Agreement true: 342
- Agreement false: 352
- Agreement unknown: 114
- High expansion count: 176
- Extreme expansion count: 251
- Average quiet score: 83.48514851
- Average range ratio: 0.60769733
- Best preparation cases: CASE_00774|CASE_00787|CASE_00764|CASE_00771|CASE_00790
- Failed preparation cases: CASE_00293|CASE_00294|CASE_00296|CASE_00297|CASE_00406

REVERSAL ANALYZER V1 summary:
- Direct reversals: 600
- Late reversals: 151
- Reversal after preparation return: 342
- Failed after return: 221
- HIGH reversal count: 231
- EXTREME reversal count: 317
- Average time to reversal: 13.04059086

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 115
- Expansion then reversal: 115
- Failed expansions: 14
- Direct reversals: 560
- Average expansion strength: 2.36757426
- Average expansion to reversal ratio: 4.05630564

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-05 20:56:11
Replay window: 2026-03-01 -> 2026-03-31
Mode: score4plus
Episodes total: 3850
Episodes analyzed: 1219
Score >= 4 episodes: 1219
Research candidates: 1219

Classification counts:
- MOMENTUM_PRECURSOR: 127
- ACCELERATION_ZONE: 51
- PRE_EXPANSION: 211
- CONTEXT_ONLY: 172
- REVERSAL_WARNING: 252
- ACCUMULATION: 323
- ABSORPTION: 2
- FAILED_CONTEXT: 81
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00290 | episode_id=290 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=4510.59
- CASE_00288 | episode_id=288 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=4134.58
- CASE_00287 | episode_id=287 | classification=ACCUMULATION | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=4096.14
- CASE_00297 | episode_id=297 | classification=MOMENTUM_PRECURSOR | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=4070.37
- CASE_00299 | episode_id=299 | classification=MOMENTUM_PRECURSOR | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=3965.47

Counterexamples:
- CASE_00128 | episode_id=128 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=773.56
- CASE_00540 | episode_id=540 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=629.66
- CASE_03022 | episode_id=3022 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1441.48
- CASE_03017 | episode_id=3017 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=1593.43
- CASE_02647 | episode_id=2647 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=445.27

Preparation zone summary:
- Preparation candidates: 739
- Preparation zones found: 739
- HIGH preparation count: 320
- EXTREME preparation count: 87
- MOMENTUM_PRECURSOR with preparation: 82
- REVERSAL_WARNING with preparation: 173
- FAILED_CONTEXT with preparation: 48
- PRE_EXPANSION with preparation: 119

HYPOTHESIS_02 revisit summary:
- Return count: 736
- Return success count: 736
- Return failure count: 0
- Agreement true: 533
- Agreement false: 539
- Agreement unknown: 147
- High expansion count: 260
- Extreme expansion count: 510
- Average quiet score: 84.2337982
- Average range ratio: 0.59996125
- Best preparation cases: CASE_00290|CASE_00288|CASE_00616|CASE_00301|CASE_00619
- Failed preparation cases: CASE_02456|CASE_03307|CASE_03316

REVERSAL ANALYZER V1 summary:
- Direct reversals: 968
- Late reversals: 186
- Reversal after preparation return: 555
- Failed after return: 327
- HIGH reversal count: 260
- EXTREME reversal count: 643
- Average time to reversal: 12.37938601

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 155
- Expansion then reversal: 147
- Failed expansions: 10
- Direct reversals: 907
- Average expansion strength: 2.66201805
- Average expansion to reversal ratio: 6.95399623

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-13 23:43:28
Replay window: 2026-04-01 -> 2026-04-30
Mode: score4plus
Episodes total: 2849
Episodes analyzed: 808
Score >= 4 episodes: 808
Research candidates: 808

Classification counts:
- MOMENTUM_PRECURSOR: 88
- ACCELERATION_ZONE: 31
- PRE_EXPANSION: 165
- CONTEXT_ONLY: 127
- REVERSAL_WARNING: 172
- ACCUMULATION: 187
- ABSORPTION: 3
- FAILED_CONTEXT: 35
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00780 | episode_id=780 | classification=MOMENTUM_PRECURSOR | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=3778.95
- CASE_00781 | episode_id=781 | classification=MOMENTUM_PRECURSOR | layers=4 | context=STRONG_VELOCITY_EXHAUSTION | max_abs_4h=3403.8
- CASE_00774 | episode_id=774 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=3171.75
- CASE_00787 | episode_id=787 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=3063.26
- CASE_00771 | episode_id=771 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2894.35

Counterexamples:
- CASE_01568 | episode_id=1568 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=600.25
- CASE_01253 | episode_id=1253 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=642.13
- CASE_01040 | episode_id=1040 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=405.08
- CASE_02609 | episode_id=2609 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=472.63
- CASE_01588 | episode_id=1588 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=333.18

Preparation zone summary:
- Preparation candidates: 493
- Preparation zones found: 493
- HIGH preparation count: 195
- EXTREME preparation count: 54
- MOMENTUM_PRECURSOR with preparation: 54
- REVERSAL_WARNING with preparation: 103
- FAILED_CONTEXT with preparation: 15
- PRE_EXPANSION with preparation: 101

HYPOTHESIS_02 revisit summary:
- Return count: 490
- Return success count: 486
- Return failure count: 4
- Agreement true: 342
- Agreement false: 352
- Agreement unknown: 114
- High expansion count: 176
- Extreme expansion count: 251
- Average quiet score: 83.48514851
- Average range ratio: 0.60769733
- Best preparation cases: CASE_00774|CASE_00787|CASE_00764|CASE_00771|CASE_00790
- Failed preparation cases: CASE_00293|CASE_00294|CASE_00296|CASE_00297|CASE_00406

REVERSAL ANALYZER V1 summary:
- Direct reversals: 600
- Late reversals: 151
- Reversal after preparation return: 342
- Failed after return: 221
- HIGH reversal count: 231
- EXTREME reversal count: 317
- Average time to reversal: 13.04059086

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 115
- Expansion then reversal: 115
- Failed expansions: 14
- Direct reversals: 560
- Average expansion strength: 2.36757426
- Average expansion to reversal ratio: 4.05630564

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-14 12:58:31
Replay window: 2026-04-01 -> 2026-04-30
Mode: score4plus
Episodes total: 2849
Episodes analyzed: 808
Score >= 4 episodes: 808
Research candidates: 808

Classification counts:
- MOMENTUM_PRECURSOR: 88
- ACCELERATION_ZONE: 31
- PRE_EXPANSION: 165
- CONTEXT_ONLY: 127
- REVERSAL_WARNING: 172
- ACCUMULATION: 187
- ABSORPTION: 3
- FAILED_CONTEXT: 35
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00780 | episode_id=780 | classification=MOMENTUM_PRECURSOR | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=3778.95
- CASE_00781 | episode_id=781 | classification=MOMENTUM_PRECURSOR | layers=4 | context=STRONG_VELOCITY_EXHAUSTION | max_abs_4h=3403.8
- CASE_00774 | episode_id=774 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=3171.75
- CASE_00787 | episode_id=787 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=3063.26
- CASE_00771 | episode_id=771 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2894.35

Counterexamples:
- CASE_01568 | episode_id=1568 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=600.25
- CASE_01253 | episode_id=1253 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=642.13
- CASE_01040 | episode_id=1040 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=405.08
- CASE_02609 | episode_id=2609 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=472.63
- CASE_01588 | episode_id=1588 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=333.18

Preparation zone summary:
- Preparation candidates: 493
- Preparation zones found: 493
- HIGH preparation count: 195
- EXTREME preparation count: 54
- MOMENTUM_PRECURSOR with preparation: 54
- REVERSAL_WARNING with preparation: 103
- FAILED_CONTEXT with preparation: 15
- PRE_EXPANSION with preparation: 101

HYPOTHESIS_02 revisit summary:
- Return count: 490
- Return success count: 486
- Return failure count: 4
- Agreement true: 342
- Agreement false: 352
- Agreement unknown: 114
- High expansion count: 176
- Extreme expansion count: 251
- Average quiet score: 83.48514851
- Average range ratio: 0.60769733
- Best preparation cases: CASE_00774|CASE_00787|CASE_00764|CASE_00771|CASE_00790
- Failed preparation cases: CASE_00293|CASE_00294|CASE_00296|CASE_00297|CASE_00406

REVERSAL ANALYZER V1 summary:
- Direct reversals: 600
- Late reversals: 151
- Reversal after preparation return: 342
- Failed after return: 221
- HIGH reversal count: 231
- EXTREME reversal count: 317
- Average time to reversal: 13.04059086

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 115
- Expansion then reversal: 115
- Failed expansions: 14
- Direct reversals: 560
- Average expansion strength: 2.36757426
- Average expansion to reversal ratio: 4.05630564

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-14 19:51:28
Replay window: 2026-04-01 -> 2026-04-30
Mode: score4plus
Episodes total: 2849
Episodes analyzed: 808
Score >= 4 episodes: 808
Research candidates: 808

Classification counts:
- MOMENTUM_PRECURSOR: 87
- ACCELERATION_ZONE: 28
- PRE_EXPANSION: 164
- CONTEXT_ONLY: 130
- REVERSAL_WARNING: 174
- ACCUMULATION: 188
- ABSORPTION: 2
- FAILED_CONTEXT: 35
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_00780 | episode_id=780 | classification=MOMENTUM_PRECURSOR | layers=4 | context=MULTI_ZSCORE_CONTEXT | max_abs_4h=3777.84
- CASE_00781 | episode_id=781 | classification=MOMENTUM_PRECURSOR | layers=4 | context=STRONG_VELOCITY_EXHAUSTION | max_abs_4h=3402.69
- CASE_00774 | episode_id=774 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=3165.86
- CASE_00787 | episode_id=787 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=3062.15
- CASE_00771 | episode_id=771 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=2896.34

Counterexamples:
- CASE_01568 | episode_id=1568 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=603.17
- CASE_01253 | episode_id=1253 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=633.38
- CASE_01040 | episode_id=1040 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=408.06
- CASE_02609 | episode_id=2609 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=473.24
- CASE_01588 | episode_id=1588 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=330.0

Preparation zone summary:
- Preparation candidates: 477
- Preparation zones found: 477
- HIGH preparation count: 219
- EXTREME preparation count: 49
- MOMENTUM_PRECURSOR with preparation: 57
- REVERSAL_WARNING with preparation: 103
- FAILED_CONTEXT with preparation: 20
- PRE_EXPANSION with preparation: 79

HYPOTHESIS_02 revisit summary:
- Return count: 477
- Return success count: 477
- Return failure count: 0
- Agreement true: 342
- Agreement false: 352
- Agreement unknown: 114
- High expansion count: 177
- Extreme expansion count: 253
- Average quiet score: 83.125
- Average range ratio: 0.60206587
- Best preparation cases: CASE_01584|CASE_01473|CASE_01539|CASE_01547|CASE_01653
- Failed preparation cases: 

REVERSAL ANALYZER V1 summary:
- Direct reversals: 600
- Late reversals: 151
- Reversal after preparation return: 3
- Failed after return: 211
- HIGH reversal count: 232
- EXTREME reversal count: 318
- Average time to reversal: 13.13152166

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 114
- Expansion then reversal: 114
- Failed expansions: 14
- Direct reversals: 562
- Average expansion strength: 2.38613861
- Average expansion to reversal ratio: 228.14835385

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

==================================================
PHASE 1B EPISODE RESEARCH RUN
==================================================

Run UTC: 2026-06-15 20:34:02
Replay window: 2026-02-01 -> 2026-06-05
Mode: score4plus
Episodes total: 15925
Episodes analyzed: 4859
Score >= 4 episodes: 4859
Research candidates: 4859

Classification counts:
- MOMENTUM_PRECURSOR: 515
- ACCELERATION_ZONE: 169
- PRE_EXPANSION: 875
- CONTEXT_ONLY: 734
- REVERSAL_WARNING: 948
- ACCUMULATION: 1345
- ABSORPTION: 8
- FAILED_CONTEXT: 265
- RANGE_NOISE: 0
- UNKNOWN: 0

Strongest examples:
- CASE_01448 | episode_id=1448 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=5985.51
- CASE_01193 | episode_id=1193 | classification=REVERSAL_WARNING | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=5956.17
- CASE_01449 | episode_id=1449 | classification=ACCUMULATION | layers=5 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=5934.48
- CASE_01195 | episode_id=1195 | classification=REVERSAL_WARNING | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=5932.12
- CASE_01443 | episode_id=1443 | classification=ACCUMULATION | layers=4 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=5890.69

Counterexamples:
- CASE_13118 | episode_id=13118 | classification=FAILED_CONTEXT | layers=7 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=374.29
- CASE_15840 | episode_id=15840 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=981.99
- CASE_13968 | episode_id=13968 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=621.28
- CASE_13274 | episode_id=13274 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=226.23
- CASE_02455 | episode_id=2455 | classification=FAILED_CONTEXT | layers=6 | context=DELTA_ZSCORE_EXTREME | max_abs_4h=774.52

Preparation zone summary:
- Preparation candidates: 2991
- Preparation zones found: 2991
- HIGH preparation count: 1248
- EXTREME preparation count: 305
- MOMENTUM_PRECURSOR with preparation: 321
- REVERSAL_WARNING with preparation: 592
- FAILED_CONTEXT with preparation: 160
- PRE_EXPANSION with preparation: 519

HYPOTHESIS_02 revisit summary:
- Return count: 2980
- Return success count: 2976
- Return failure count: 4
- Agreement true: 2060
- Agreement false: 2115
- Agreement unknown: 684
- High expansion count: 890
- Extreme expansion count: 2011
- Average quiet score: 83.79275571
- Average range ratio: 0.60365323
- Best preparation cases: CASE_01443|CASE_01442|CASE_01439|CASE_01435|CASE_01431
- Failed preparation cases: CASE_09835|CASE_09838|CASE_09839|CASE_13465|CASE_13588

REVERSAL ANALYZER V1 summary:
- Direct reversals: 3879
- Late reversals: 727
- Reversal after preparation return: 2175
- Failed after return: 1296
- HIGH reversal count: 1076
- EXTREME reversal count: 2549
- Average time to reversal: 11.57220535

EXPANSION / REVERSAL SPLIT V1 summary:
- Pure expansions: 556
- Expansion then reversal: 546
- Failed expansions: 68
- Direct reversals: 3687
- Average expansion strength: 2.58160115
- Average expansion to reversal ratio: 5.98313862

Note:
HYPOTHESIS_01 remains unproven.
No trading interpretation.

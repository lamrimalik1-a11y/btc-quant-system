# Performance Profile Report

Updated UTC: 2026-06-04 21:51:17

## phase1b_episode_research

- Total runtime: 648.509385s
- Slowest function / step: research_analysis_time_after_cache (644.845554s)
- Bottleneck likely: CPU_PROCESSING
- Peak Python heap: 75.322 MB

### Top Bottlenecks

- research_analysis_time_after_cache: 644.845554s
- csv_read_observation_rows: 1.117899s
- research_prepare_rows: 0.614245s
- jsonl_write_lifecycle_events: 0.484457s
- csv_write_research_log: 0.459032s
- research_lifecycle_memory: 0.455039s
- research_summary_build: 0.147985s
- csv_write_preparation_zones: 0.086063s
- index_build_time: 0.081395s
- csv_read_episodes: 0.061678s

### Metrics

- indexed_episode_count: 793
- indexed_case_count: 793
- episodes_loaded: 2782
- rows_loaded: 49175
- episodes_analyzed: 793
- score4plus_episodes: 793
- research_candidates: 793

### CSV File Sizes

- outputs\historical_replay_dashboard_v2_episodes.csv: 1.273 MB
- outputs\historical_observation_rows.csv: 63.944 MB
- research\phase1b_episode_research_log.csv: 1.372 MB
- research\phase1b_preparation_zones.csv: 0.194 MB
- research\phase1b_research_summary.csv: 0.002 MB

## rdm_zone_mechanics_calculator

- Total runtime: 355.457118s
- Slowest function / step: rdm_v16b_attacker_basics (82.568815s)
- Bottleneck likely: RDM_CALCULATOR
- Peak Python heap: 311.939 MB

### Top Bottlenecks

- rdm_v16b_attacker_basics: 82.568815s
- rdm_live_evolution_after_cache: 73.31808s
- csv_write_rdm_outputs: 40.781926s
- rdm_interaction_core_after_cache: 36.115648s
- rdm_density_after_cache: 25.79462s
- rdm_v16b8_zone_visit_timeline: 17.225924s
- rdm_base_mechanics: 13.633947s
- interaction_mask_build_time: 13.028804s
- rdm_v16b9_zone_health_evolution: 10.618565s
- rdm_true_lifecycle: 10.559522s

### Metrics

- rdm_case_cache_count: 793
- interaction_mask_reuse_count: 793
- rows_processed: 793
- historical_rows_loaded: 49175
- live_evolution_rows: 93647
- attacker_evolution_rows: 793
- zone_strength_profile_rows: 793
- zone_vs_attacker_rows: 793
- zone_anomaly_rows: 793
- zone_reinforcement_rows: 793
- attacker_conversion_rows: 793
- force_allocation_rows: 793
- zone_visit_timeline_rows: 2083
- zone_health_evolution_rows: 793
- zone_structural_trajectory_rows: 793
- zone_structural_prediction_rows: 793
- zone_synthesis_rows: 793
- interaction_core_rows: 793
- interaction_density_rows: 793
- timeline_rows: 793
- lifecycle_rows: 2492

### CSV File Sizes

- research\zone_mechanics_cycle3_results.csv: 2.577 MB
- research\zone_mechanics_cycle3_summary.csv: 0.002 MB
- research\zone_mechanics_timeline.csv: 0.186 MB
- research\zone_mechanics_lifecycle.csv: 0.351 MB
- research\zone_mechanics_capacity.csv: 0.245 MB
- research\zone_mechanics_sigma.csv: 0.154 MB
- research\zone_mechanics_sigma_evolution.csv: 0.144 MB
- research\zone_mechanics_verestchaguine.csv: 0.134 MB
- research\zone_real_geometry_tracking.csv: 0.527 MB
- research\zone_live_rdm_evolution.csv: 49.486 MB
- research\zone_interaction_core_geometry.csv: 0.288 MB
- research\zone_interaction_density_map.csv: 0.162 MB
- research\zone_true_lifecycle_tracking.csv: 0.256 MB
- research\zone_birth_registry.csv: 0.34 MB
- research\zone_death_registry.csv: 0.19 MB
- research\zone_evolution_chart.csv: 0.279 MB
- research\zone_evolution_history.csv: 0.603 MB

## historical_replay_generation

- Total runtime: 3872.366728s
- Slowest function / step: download_total (1596.891987s)
- Bottleneck likely: RAM_LIMIT
- Peak Python heap: 15731.282 MB

### Top Bottlenecks

- download_total: 1596.891987s
- observation_row_build: 1415.350512s
- aggregation_replay_row_build: 567.834102s
- download_batch: 420.932031s
- http_wait: 340.443386s
- parse_batch: 79.777044s
- replay_v1_build: 69.557819s
- replay_v2_build: 52.942252s
- archive_historical_outputs: 44.172717s
- csv_write_observation_rows: 10.856974s

### Metrics

- trades_processed: 24587001
- warmup_trades_processed: 789739
- warmup_rows_used: 500
- rows_processed: 49175
- observation_rows_processed: 49175
- v1_events: 17279
- v1_episodes: 1969
- v2_events: 16662
- v2_episodes: 2782
- archive_days: 34
- archive_files_written: 136

### CSV File Sizes

- outputs\historical_market_rows.csv: 8.897 MB
- outputs\historical_observation_rows.csv: 63.944 MB
- outputs\historical_replay_observation_events.csv: 3.67 MB
- outputs\historical_replay_dashboard_episodes.csv: 0.356 MB
- outputs\historical_replay_observation_v2_events.csv: 6.926 MB
- outputs\historical_replay_dashboard_v2_episodes.csv: 1.273 MB

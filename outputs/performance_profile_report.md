# Performance Profile Report

Updated UTC: 2026-06-02 22:36:36

## phase1b_episode_research

- Total runtime: 11.899318s
- Slowest function / step: research_analysis_time_after_cache (11.227058s)
- Bottleneck likely: CPU_PROCESSING
- Peak Python heap: 7.027 MB

### Top Bottlenecks

- research_analysis_time_after_cache: 11.227058s
- research_summary_build: 0.150896s
- csv_read_observation_rows: 0.099806s
- research_prepare_rows: 0.078602s
- research_lifecycle_memory: 0.054378s
- research_journal_append: 0.04895s
- jsonl_write_lifecycle_events: 0.048832s
- csv_write_research_log: 0.048434s
- csv_read_episodes: 0.020635s
- pandas_dataframe_build: 0.019494s

### Metrics

- indexed_episode_count: 50
- indexed_case_count: 50
- episodes_loaded: 148
- rows_loaded: 2611
- episodes_analyzed: 50
- score4plus_episodes: 50
- research_candidates: 50

### CSV File Sizes

- outputs\historical_replay_dashboard_v2_episodes.csv: 0.07 MB
- outputs\historical_observation_rows.csv: 3.47 MB
- research\phase1b_episode_research_log.csv: 0.09 MB
- research\phase1b_preparation_zones.csv: 0.015 MB
- research\phase1b_research_summary.csv: 0.002 MB

## rdm_zone_mechanics_calculator

- Total runtime: 18.941796s
- Slowest function / step: rdm_v16b_attacker_basics (5.700369s)
- Bottleneck likely: RDM_CALCULATOR
- Peak Python heap: 17.649 MB

### Top Bottlenecks

- rdm_v16b_attacker_basics: 5.700369s
- rdm_live_evolution_after_cache: 3.963501s
- csv_write_rdm_outputs: 1.493406s
- rdm_density_after_cache: 1.460656s
- rdm_interaction_core_after_cache: 1.366656s
- rdm_base_mechanics: 0.949134s
- rdm_true_lifecycle: 0.690465s
- interaction_mask_build_time: 0.581687s
- rdm_v16_numeric_foundation: 0.415369s
- rdm_birth_death_memory: 0.275156s

### Metrics

- rdm_case_cache_count: 50
- interaction_mask_reuse_count: 50
- rows_processed: 50
- historical_rows_loaded: 2611
- live_evolution_rows: 4236
- attacker_evolution_rows: 50
- zone_strength_profile_rows: 50
- zone_vs_attacker_rows: 50
- zone_anomaly_rows: 50
- zone_reinforcement_rows: 50
- attacker_conversion_rows: 50
- force_allocation_rows: 50
- interaction_core_rows: 50
- interaction_density_rows: 50
- timeline_rows: 50
- lifecycle_rows: 152

### CSV File Sizes

- research\zone_mechanics_cycle3_results.csv: 0.17 MB
- research\zone_mechanics_cycle3_summary.csv: 0.002 MB
- research\zone_mechanics_timeline.csv: 0.012 MB
- research\zone_mechanics_lifecycle.csv: 0.022 MB
- research\zone_mechanics_capacity.csv: 0.016 MB
- research\zone_mechanics_sigma.csv: 0.01 MB
- research\zone_mechanics_sigma_evolution.csv: 0.009 MB
- research\zone_mechanics_verestchaguine.csv: 0.009 MB
- research\zone_real_geometry_tracking.csv: 0.035 MB
- research\zone_live_rdm_evolution.csv: 2.329 MB
- research\zone_interaction_core_geometry.csv: 0.019 MB
- research\zone_interaction_density_map.csv: 0.011 MB
- research\zone_true_lifecycle_tracking.csv: 0.016 MB
- research\zone_birth_registry.csv: 0.022 MB
- research\zone_death_registry.csv: 0.012 MB
- research\zone_evolution_chart.csv: 0.018 MB
- research\zone_evolution_history.csv: 0.037 MB

## historical_replay_generation

- Total runtime: 6298.412175s
- Slowest function / step: download_total (6212.078693s)
- Bottleneck likely: DOWNLOAD
- Peak Python heap: 1275.763 MB

### Top Bottlenecks

- download_total: 6212.078693s
- download_batch: 4817.731849s
- http_wait: 1126.462824s
- observation_row_build: 58.349374s
- parse_batch: 49.219992s
- aggregation_replay_row_build: 10.204178s
- archive_historical_outputs: 3.560502s
- replay_v1_build: 3.149829s
- replay_v2_build: 3.076035s
- pandas_dataframe_build: 0.620213s

### Metrics

- trades_processed: 1305457
- warmup_trades_processed: 1196334
- warmup_rows_used: 500
- rows_processed: 2611
- observation_rows_processed: 2611
- v1_events: 1005
- v1_episodes: 113
- v2_events: 1001
- v2_episodes: 148
- archive_days: 1
- archive_files_written: 4

### CSV File Sizes

- outputs\historical_market_rows.csv: 0.467 MB
- outputs\historical_observation_rows.csv: 3.47 MB
- outputs\historical_replay_observation_events.csv: 0.212 MB
- outputs\historical_replay_dashboard_episodes.csv: 0.02 MB
- outputs\historical_replay_observation_v2_events.csv: 0.423 MB
- outputs\historical_replay_dashboard_v2_episodes.csv: 0.07 MB

# Performance Profile Report

Updated UTC: 2026-05-28 14:58:29

## phase1b_episode_research

- Total runtime: 13.702289s
- Slowest function / step: research_analysis_time_after_cache (12.386992s)
- Bottleneck likely: CPU_PROCESSING
- Peak Python heap: 6.324 MB

### Top Bottlenecks

- research_analysis_time_after_cache: 12.386992s
- research_summary_build: 0.315861s
- csv_read_observation_rows: 0.213658s
- research_prepare_rows: 0.128s
- research_journal_append: 0.125057s
- csv_write_research_log: 0.122916s
- csv_read_episodes: 0.089528s
- jsonl_write_lifecycle_events: 0.072086s
- research_lifecycle_memory: 0.04614s
- csv_write_research_summary: 0.035162s

### Metrics

- indexed_episode_count: 27
- indexed_case_count: 27
- episodes_loaded: 86
- rows_loaded: 1562
- episodes_analyzed: 27
- score4plus_episodes: 27
- research_candidates: 27

### CSV File Sizes

- outputs\historical_replay_dashboard_v2_episodes.csv: 0.038 MB
- outputs\historical_observation_rows.csv: 1.969 MB
- research\phase1b_episode_research_log.csv: 0.044 MB
- research\phase1b_preparation_zones.csv: 0.005 MB
- research\phase1b_research_summary.csv: 0.002 MB

## rdm_zone_mechanics_calculator

- Total runtime: 14.81261s
- Slowest function / step: rdm_live_evolution_after_cache (4.62172s)
- Bottleneck likely: RDM_CALCULATOR
- Peak Python heap: 14.015 MB

### Top Bottlenecks

- rdm_live_evolution_after_cache: 4.62172s
- rdm_density_after_cache: 1.976788s
- rdm_interaction_core_after_cache: 1.729689s
- csv_write_rdm_outputs: 1.618177s
- rdm_base_mechanics: 0.959475s
- rdm_true_lifecycle: 0.956875s
- interaction_mask_build_time: 0.559864s
- rdm_summary_notes_build: 0.343092s
- csv_read_rdm_inputs: 0.321002s
- rdm_birth_death_memory: 0.285867s

### Metrics

- rdm_case_cache_count: 27
- interaction_mask_reuse_count: 27
- rows_processed: 27
- historical_rows_loaded: 1562
- live_evolution_rows: 2739
- interaction_core_rows: 27
- interaction_density_rows: 27
- timeline_rows: 27
- lifecycle_rows: 79

### CSV File Sizes

- research\zone_mechanics_cycle3_results.csv: 0.087 MB
- research\zone_mechanics_cycle3_summary.csv: 0.002 MB
- research\zone_mechanics_timeline.csv: 0.007 MB
- research\zone_mechanics_lifecycle.csv: 0.011 MB
- research\zone_mechanics_capacity.csv: 0.009 MB
- research\zone_mechanics_sigma.csv: 0.005 MB
- research\zone_mechanics_sigma_evolution.csv: 0.005 MB
- research\zone_mechanics_verestchaguine.csv: 0.005 MB
- research\zone_real_geometry_tracking.csv: 0.019 MB
- research\zone_live_rdm_evolution.csv: 1.457 MB
- research\zone_interaction_core_geometry.csv: 0.011 MB
- research\zone_interaction_density_map.csv: 0.006 MB
- research\zone_true_lifecycle_tracking.csv: 0.009 MB
- research\zone_birth_registry.csv: 0.012 MB
- research\zone_death_registry.csv: 0.007 MB
- research\zone_evolution_chart.csv: 0.01 MB
- research\zone_evolution_history.csv: 0.019 MB

## historical_replay_generation

- Total runtime: 1251.143445s
- Slowest function / step: download_total (1203.932634s)
- Bottleneck likely: DOWNLOAD
- Peak Python heap: 398.731 MB

### Top Bottlenecks

- download_total: 1203.932634s
- download_batch: 518.939626s
- http_wait: 480.990828s
- observation_row_build: 36.052476s
- parse_batch: 34.832174s
- aggregation_replay_row_build: 4.539065s
- replay_v2_build: 2.961173s
- replay_v1_build: 2.953453s
- csv_write_observation_rows: 0.242973s
- pandas_dataframe_build: 0.216071s

### Metrics

- trades_processed: 780563
- rows_processed: 1562
- observation_rows_processed: 1562
- v1_events: 497
- v1_episodes: 61
- v2_events: 517
- v2_episodes: 86

### CSV File Sizes

- outputs\historical_market_rows.csv: 0.279 MB
- outputs\historical_observation_rows.csv: 1.969 MB
- outputs\historical_replay_observation_events.csv: 0.104 MB
- outputs\historical_replay_dashboard_episodes.csv: 0.011 MB
- outputs\historical_replay_observation_v2_events.csv: 0.209 MB
- outputs\historical_replay_dashboard_v2_episodes.csv: 0.038 MB

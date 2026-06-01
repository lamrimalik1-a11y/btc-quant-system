# Performance Profile Report

Updated UTC: 2026-06-01 15:12:02

## phase1b_episode_research

- Total runtime: 361.652975s
- Slowest function / step: research_analysis_time_after_cache (359.245182s)
- Bottleneck likely: CPU_PROCESSING
- Peak Python heap: 30.404 MB

### Top Bottlenecks

- research_analysis_time_after_cache: 359.245182s
- csv_read_observation_rows: 0.513443s
- jsonl_write_lifecycle_events: 0.453346s
- research_lifecycle_memory: 0.417165s
- csv_write_research_log: 0.399368s
- research_prepare_rows: 0.192862s
- research_summary_build: 0.14198s
- csv_write_preparation_zones: 0.066552s
- research_journal_append: 0.062692s
- pandas_dataframe_build: 0.042131s

### Metrics

- indexed_episode_count: 634
- indexed_case_count: 634
- episodes_loaded: 634
- rows_loaded: 11181
- episodes_analyzed: 634
- score4plus_episodes: 177
- research_candidates: 305

### CSV File Sizes

- outputs\historical_replay_dashboard_v2_episodes.csv: 0.289 MB
- outputs\historical_observation_rows.csv: 14.565 MB
- research\phase1b_episode_research_log.csv: 0.986 MB
- research\phase1b_preparation_zones.csv: 0.141 MB
- research\phase1b_research_summary.csv: 0.002 MB

## rdm_zone_mechanics_calculator

- Total runtime: 181.023981s
- Slowest function / step: rdm_live_evolution_after_cache (59.24864s)
- Bottleneck likely: RDM_CALCULATOR
- Peak Python heap: 167.357 MB

### Top Bottlenecks

- rdm_live_evolution_after_cache: 59.24864s
- rdm_interaction_core_after_cache: 23.138265s
- rdm_density_after_cache: 21.937228s
- csv_write_rdm_outputs: 20.050261s
- rdm_base_mechanics: 15.267788s
- rdm_true_lifecycle: 11.603105s
- interaction_mask_build_time: 9.509758s
- rdm_v16_numeric_foundation: 5.638164s
- rdm_birth_death_memory: 3.996532s
- rdm_summary_notes_build: 1.770268s

### Metrics

- rdm_case_cache_count: 634
- interaction_mask_reuse_count: 634
- rows_processed: 634
- historical_rows_loaded: 11181
- live_evolution_rows: 51824
- interaction_core_rows: 634
- interaction_density_rows: 634
- timeline_rows: 634
- lifecycle_rows: 1867

### CSV File Sizes

- research\zone_mechanics_cycle3_results.csv: 2.028 MB
- research\zone_mechanics_cycle3_summary.csv: 0.002 MB
- research\zone_mechanics_timeline.csv: 0.148 MB
- research\zone_mechanics_lifecycle.csv: 0.263 MB
- research\zone_mechanics_capacity.csv: 0.193 MB
- research\zone_mechanics_sigma.csv: 0.121 MB
- research\zone_mechanics_sigma_evolution.csv: 0.114 MB
- research\zone_mechanics_verestchaguine.csv: 0.105 MB
- research\zone_real_geometry_tracking.csv: 0.413 MB
- research\zone_live_rdm_evolution.csv: 27.493 MB
- research\zone_interaction_core_geometry.csv: 0.228 MB
- research\zone_interaction_density_map.csv: 0.128 MB
- research\zone_true_lifecycle_tracking.csv: 0.199 MB
- research\zone_birth_registry.csv: 0.267 MB
- research\zone_death_registry.csv: 0.147 MB
- research\zone_evolution_chart.csv: 0.222 MB
- research\zone_evolution_history.csv: 0.467 MB

## historical_replay_generation

- Total runtime: 9444.718719s
- Slowest function / step: download_total (9142.65846s)
- Bottleneck likely: RAM_LIMIT
- Peak Python heap: 3146.469 MB

### Top Bottlenecks

- download_total: 9142.65846s
- download_batch: 5771.607996s
- http_wait: 2630.266995s
- observation_row_build: 233.042138s
- parse_batch: 112.366126s
- aggregation_replay_row_build: 24.417337s
- replay_v1_build: 12.555121s
- replay_v2_build: 10.913124s
- pandas_dataframe_build: 2.165273s
- csv_write_observation_rows: 1.439666s

### Metrics

- trades_processed: 5590419
- warmup_trades_processed: 496314
- warmup_rows_used: 500
- rows_processed: 11181
- observation_rows_processed: 11181
- v1_events: 3992
- v1_episodes: 454
- v2_events: 3795
- v2_episodes: 634

### CSV File Sizes

- outputs\historical_market_rows.csv: 2.012 MB
- outputs\historical_observation_rows.csv: 14.565 MB
- outputs\historical_replay_observation_events.csv: 0.843 MB
- outputs\historical_replay_dashboard_episodes.csv: 0.081 MB
- outputs\historical_replay_observation_v2_events.csv: 1.569 MB
- outputs\historical_replay_dashboard_v2_episodes.csv: 0.289 MB

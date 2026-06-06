# Performance Profile Report

Updated UTC: 2026-06-05 21:47:45

## phase1b_episode_research

- Total runtime: 2847.007605s
- Slowest function / step: research_analysis_time_after_cache (2840.849432s)
- Bottleneck likely: CPU_PROCESSING
- Peak Python heap: 126.658 MB

### Top Bottlenecks

- research_analysis_time_after_cache: 2840.849432s
- csv_read_observation_rows: 1.886202s
- jsonl_write_lifecycle_events: 1.057206s
- research_prepare_rows: 0.927966s
- csv_write_research_log: 0.783896s
- research_lifecycle_memory: 0.734065s
- research_summary_build: 0.26752s
- csv_write_preparation_zones: 0.13647s
- index_build_time: 0.130089s
- research_journal_append: 0.077446s

### Metrics

- indexed_episode_count: 1219
- indexed_case_count: 1219
- episodes_loaded: 3850
- rows_loaded: 76699
- episodes_analyzed: 1219
- score4plus_episodes: 1219
- research_candidates: 1219

### CSV File Sizes

- outputs\historical_replay_dashboard_v2_episodes.csv: 1.789 MB
- outputs\historical_observation_rows.csv: 96.675 MB
- research\phase1b_episode_research_log.csv: 2.126 MB
- research\phase1b_preparation_zones.csv: 0.309 MB
- research\phase1b_research_summary.csv: 0.002 MB

## rdm_zone_mechanics_calculator

- Total runtime: 690.341286s
- Slowest function / step: rdm_v16b_attacker_basics (182.94303s)
- Bottleneck likely: RDM_CALCULATOR
- Peak Python heap: 541.412 MB

### Top Bottlenecks

- rdm_v16b_attacker_basics: 182.94303s
- rdm_live_evolution_after_cache: 179.84469s
- csv_write_rdm_outputs: 62.839517s
- rdm_density_after_cache: 44.542064s
- rdm_interaction_core_after_cache: 44.111478s
- rdm_v16b8_zone_visit_timeline: 39.711267s
- rdm_base_mechanics: 29.887681s
- rdm_true_lifecycle: 22.021174s
- rdm_v16b9_zone_health_evolution: 18.992806s
- interaction_mask_build_time: 18.414548s

### Metrics

- rdm_case_cache_count: 1219
- interaction_mask_reuse_count: 1219
- rows_processed: 1219
- historical_rows_loaded: 76699
- live_evolution_rows: 163976
- attacker_evolution_rows: 1219
- zone_strength_profile_rows: 1219
- zone_vs_attacker_rows: 1219
- zone_anomaly_rows: 1219
- zone_reinforcement_rows: 1219
- attacker_conversion_rows: 1219
- force_allocation_rows: 1219
- zone_visit_timeline_rows: 3841
- zone_health_evolution_rows: 1219
- zone_structural_trajectory_rows: 1219
- zone_structural_prediction_rows: 1219
- zone_synthesis_rows: 1219
- interaction_core_rows: 1219
- interaction_density_rows: 1219
- timeline_rows: 1219
- lifecycle_rows: 3883

### CSV File Sizes

- research\zone_mechanics_cycle3_results.csv: 3.981 MB
- research\zone_mechanics_cycle3_summary.csv: 0.002 MB
- research\zone_mechanics_timeline.csv: 0.29 MB
- research\zone_mechanics_lifecycle.csv: 0.559 MB
- research\zone_mechanics_capacity.csv: 0.377 MB
- research\zone_mechanics_sigma.csv: 0.239 MB
- research\zone_mechanics_sigma_evolution.csv: 0.222 MB
- research\zone_mechanics_verestchaguine.csv: 0.207 MB
- research\zone_real_geometry_tracking.csv: 0.815 MB
- research\zone_live_rdm_evolution.csv: 87.653 MB
- research\zone_interaction_core_geometry.csv: 0.443 MB
- research\zone_interaction_density_map.csv: 0.25 MB
- research\zone_true_lifecycle_tracking.csv: 0.399 MB
- research\zone_birth_registry.csv: 0.527 MB
- research\zone_death_registry.csv: 0.295 MB
- research\zone_evolution_chart.csv: 0.432 MB
- research\zone_evolution_history.csv: 0.938 MB

## historical_replay_generation

- Total runtime: 1169.9148s
- Slowest function / step: download_total (908.736405s)
- Bottleneck likely: RAM_LIMIT
- Peak Python heap: 4682.964 MB

### Top Bottlenecks

- download_total: 908.736405s
- download_batch: 315.380401s
- http_wait: 308.400947s
- observation_row_build: 202.895365s
- aggregation_replay_row_build: 21.836552s
- replay_v1_build: 11.517955s
- replay_v2_build: 10.255735s
- archive_historical_outputs: 8.554445s
- parse_batch: 6.111447s
- csv_write_observation_rows: 0.791155s

### Metrics

- trades_processed: 4452994
- warmup_trades_processed: 1677041
- warmup_rows_used: 500
- rows_processed: 8906
- observation_rows_processed: 8906
- v1_events: 3158
- v1_episodes: 365
- v2_events: 3296
- v2_episodes: 525
- archive_days: 2
- archive_files_written: 8

### CSV File Sizes

- outputs\historical_market_rows.csv: 1.587 MB
- outputs\historical_observation_rows.csv: 11.649 MB
- outputs\historical_replay_observation_events.csv: 0.666 MB
- outputs\historical_replay_dashboard_episodes.csv: 0.064 MB
- outputs\historical_replay_observation_v2_events.csv: 1.376 MB
- outputs\historical_replay_dashboard_v2_episodes.csv: 0.242 MB

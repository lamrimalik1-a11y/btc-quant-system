# Performance Profile Report

Updated UTC: 2026-06-16 07:33:07

## phase1b_episode_research

- Total runtime: 16593.443628s
- Slowest function / step: research_analysis_time_after_cache (16572.121585s)
- Bottleneck likely: CPU_PROCESSING
- Peak Python heap: 406.352 MB

### Top Bottlenecks

- research_analysis_time_after_cache: 16572.121585s
- csv_read_observation_rows: 6.988588s
- research_prepare_rows: 3.443916s
- jsonl_write_lifecycle_events: 3.056183s
- csv_write_research_log: 2.939916s
- research_lifecycle_memory: 2.867223s
- csv_write_preparation_zones: 0.577371s
- index_build_time: 0.510149s
- research_summary_build: 0.379758s
- pandas_dataframe_build: 0.255044s

### Metrics

- indexed_episode_count: 4859
- indexed_case_count: 4859
- episodes_loaded: 15925
- rows_loaded: 295822
- episodes_analyzed: 4859
- score4plus_episodes: 4859
- research_candidates: 4859

### CSV File Sizes

- outputs\historical_replay_dashboard_v2_episodes.csv: 7.407 MB
- outputs\historical_observation_rows.csv: 380.045 MB
- research\phase1b_episode_research_log.csv: 8.562 MB
- research\phase1b_preparation_zones.csv: 1.252 MB
- research\phase1b_research_summary.csv: 0.002 MB

## rdm_zone_mechanics_calculator

- Total runtime: 2957.247753s
- Slowest function / step: rdm_live_evolution_after_cache (1046.502867s)
- Bottleneck likely: RAM_LIMIT
- Peak Python heap: 1681.091 MB

### Top Bottlenecks

- rdm_live_evolution_after_cache: 1046.502867s
- rdm_v16b_attacker_basics: 530.133847s
- csv_write_rdm_outputs: 514.789198s
- rdm_v16b8_zone_visit_timeline: 155.576833s
- rdm_interaction_core_after_cache: 131.761679s
- rdm_density_after_cache: 130.940607s
- rdm_base_mechanics: 91.029328s
- rdm_true_lifecycle: 69.924131s
- interaction_mask_build_time: 60.785809s
- rdm_v16b9_zone_health_evolution: 60.036262s

### Metrics

- rdm_case_cache_count: 4859
- interaction_mask_reuse_count: 4859
- rows_processed: 4859
- historical_rows_loaded: 295822
- live_evolution_rows: 1809010
- attacker_evolution_rows: 4859
- zone_strength_profile_rows: 4859
- zone_vs_attacker_rows: 4859
- zone_anomaly_rows: 4859
- zone_reinforcement_rows: 4859
- attacker_conversion_rows: 4859
- force_allocation_rows: 4859
- zone_visit_timeline_rows: 14083
- zone_health_evolution_rows: 4859
- zone_structural_trajectory_rows: 4859
- zone_structural_prediction_rows: 4859
- zone_synthesis_rows: 4859
- interaction_core_rows: 4859
- interaction_density_rows: 4859
- timeline_rows: 4859
- lifecycle_rows: 15768

### CSV File Sizes

- research\zone_mechanics_cycle3_results.csv: 16.05 MB
- research\zone_mechanics_cycle3_summary.csv: 0.002 MB
- research\zone_mechanics_timeline.csv: 1.16 MB
- research\zone_mechanics_lifecycle.csv: 2.276 MB
- research\zone_mechanics_capacity.csv: 1.498 MB
- research\zone_mechanics_sigma.csv: 0.952 MB
- research\zone_mechanics_sigma_evolution.csv: 0.884 MB
- research\zone_mechanics_verestchaguine.csv: 0.828 MB
- research\zone_real_geometry_tracking.csv: 3.251 MB
- research\zone_live_rdm_evolution.csv: 950.274 MB
- research\zone_interaction_core_geometry.csv: 1.903 MB
- research\zone_interaction_density_map.csv: 1.022 MB
- research\zone_true_lifecycle_tracking.csv: 1.608 MB
- research\zone_birth_registry.csv: 2.097 MB
- research\zone_death_registry.csv: 1.184 MB
- research\zone_evolution_chart.csv: 1.731 MB
- research\zone_evolution_history.csv: 3.787 MB

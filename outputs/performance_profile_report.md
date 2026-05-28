# Performance Profile Report

Updated UTC: 2026-05-28 11:10:25

## phase1b_episode_research

- Total runtime: 16.410588s
- Slowest function / step: research_analysis_time_after_cache (15.827497s)
- Bottleneck likely: CPU_PROCESSING
- Peak Python heap: 7.083 MB

### Top Bottlenecks

- research_analysis_time_after_cache: 15.827497s
- csv_read_observation_rows: 0.133235s
- research_summary_build: 0.098207s
- research_prepare_rows: 0.069539s
- jsonl_write_lifecycle_events: 0.049102s
- research_journal_append: 0.045458s
- csv_write_research_log: 0.040367s
- research_lifecycle_memory: 0.039975s
- csv_read_episodes: 0.026734s
- pandas_dataframe_build: 0.019609s

### Metrics

- indexed_episode_count: 53
- indexed_case_count: 53
- episodes_loaded: 167
- rows_loaded: 3018
- episodes_analyzed: 53
- score4plus_episodes: 53
- research_candidates: 53

### CSV File Sizes

- outputs\historical_replay_dashboard_v2_episodes.csv: 0.078 MB
- outputs\historical_observation_rows.csv: 3.893 MB
- research\phase1b_episode_research_log.csv: 0.086 MB
- research\phase1b_preparation_zones.csv: 0.009 MB
- research\phase1b_research_summary.csv: 0.002 MB

## rdm_zone_mechanics_calculator

- Total runtime: 14.659851s
- Slowest function / step: rdm_live_evolution_after_cache (4.361965s)
- Bottleneck likely: RDM_CALCULATOR
- Peak Python heap: 16.885 MB

### Top Bottlenecks

- rdm_live_evolution_after_cache: 4.361965s
- rdm_interaction_core_after_cache: 1.961055s
- rdm_density_after_cache: 1.953991s
- csv_write_rdm_outputs: 1.433947s
- rdm_base_mechanics: 1.425445s
- rdm_true_lifecycle: 0.921031s
- interaction_mask_build_time: 0.870054s
- csv_read_rdm_inputs: 0.241402s
- rdm_birth_death_memory: 0.218149s
- rdm_summary_notes_build: 0.207568s

### Metrics

- rdm_case_cache_count: 53
- interaction_mask_reuse_count: 53
- rows_processed: 53
- historical_rows_loaded: 3018
- live_evolution_rows: 3454
- interaction_core_rows: 53
- interaction_density_rows: 53
- timeline_rows: 53
- lifecycle_rows: 156

### CSV File Sizes

- research\zone_mechanics_cycle3_results.csv: 0.165 MB
- research\zone_mechanics_cycle3_summary.csv: 0.002 MB
- research\zone_mechanics_timeline.csv: 0.013 MB
- research\zone_mechanics_lifecycle.csv: 0.022 MB
- research\zone_mechanics_capacity.csv: 0.017 MB
- research\zone_mechanics_sigma.csv: 0.01 MB
- research\zone_mechanics_sigma_evolution.csv: 0.01 MB
- research\zone_mechanics_verestchaguine.csv: 0.009 MB
- research\zone_real_geometry_tracking.csv: 0.036 MB
- research\zone_live_rdm_evolution.csv: 1.917 MB
- research\zone_interaction_core_geometry.csv: 0.02 MB
- research\zone_interaction_density_map.csv: 0.011 MB
- research\zone_true_lifecycle_tracking.csv: 0.018 MB
- research\zone_birth_registry.csv: 0.023 MB
- research\zone_death_registry.csv: 0.013 MB
- research\zone_evolution_chart.csv: 0.019 MB
- research\zone_evolution_history.csv: 0.038 MB

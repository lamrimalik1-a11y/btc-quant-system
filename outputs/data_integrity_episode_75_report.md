# Data Integrity Diagnostic - Episode 75

Episode: 75
Case: CASE_00075
Target: 2026-05-28 14:05:00 UTC

## Conclusions

- SOURCE_DATA_OK
- TIMEZONE_OK
- DASHBOARD_MAPPING_OK
- EPISODE_ROW_ALIGNMENT_OK
- STALE_ARTIFACTS_FOUND

## Episode Metadata

- episode_id: 75
- episode_start_timestamp_utc: 1779977134856
- episode_end_timestamp_utc: 1779977138211
- duration_seconds: 3.355
- start_row_id: 1345
- end_row_id: 1347
- peak_state: EXTREME_LAYER_CONFLUENCE
- peak_layer_count: 4
- peak_max_severity: HIGH
- peak_primary_context: DELTA_ZSCORE_EXTREME
- peak_conditions: DELTA_ZSCORE_EXTREME|PRICE_ZSCORE|DELTA_ZSCORE|GAUSSIAN_OUTER|GAUSSIAN_CONFIDENCE:MEDIUM_CONFIDENCE|PRICE_TAIL_PERSISTENCE|HIGH_VOLUME|VOLUME_STATE:HIGH_VOLUME|VOLUME_EXPANSION|VELOCITY_SHOCK|VELOCITY_ACCELERATION_STATE:VELOCITY_SHOCK|SINGLE_FACTOR_EXTREME|VELOCITY_EXTREME_EVENT
- peak_active_layers: multi_zscore|price_rarity|volume|velocity
- peak_observation_confidence: HIGH_CONFIDENCE
- start_price: 72710.17
- end_price: 72657.99
- peak_rvi: 12.39772100091554
- peak_velocity: 47.3575
- peak_delta_zscore: -2.641021772697188
- readable_start: 2026-05-28 14:05:34 UTC
- readable_end: 2026-05-28 14:05:38 UTC

## Row Alignment

- alignment_ok: True

### Observation start row
```json
{
  "row_id": "1345",
  "market_timestamp": "1779977134856",
  "close": 72710.17
}
```

### Observation end row
```json
{
  "row_id": "1347",
  "market_timestamp": "1779977138211",
  "close": 72657.99
}
```

## Raw Market Rows Around Compared Times

### 14:05_UTC

- historical_observation_rows: rows=11, min=72630.75, max=72899.5, dt_source=market_timestamp, file=outputs\historical_observation_rows.csv
  - {'row_id': 1341, 'market_timestamp': 1779977049555, 'close': 72852.4, 'parsed_time': '2026-05-28 14:04:09 UTC'}
  - {'row_id': 1342, 'market_timestamp': 1779977073567, 'close': 72899.5, 'parsed_time': '2026-05-28 14:04:33 UTC'}
  - {'row_id': 1343, 'market_timestamp': 1779977113621, 'close': 72826.72, 'parsed_time': '2026-05-28 14:05:13 UTC'}
  - {'row_id': 1344, 'market_timestamp': 1779977134519, 'close': 72760.3, 'parsed_time': '2026-05-28 14:05:34 UTC'}
  - {'row_id': 1345, 'market_timestamp': 1779977134856, 'close': 72710.17, 'parsed_time': '2026-05-28 14:05:34 UTC'}
  - {'row_id': 1346, 'market_timestamp': 1779977135817, 'close': 72688.0, 'parsed_time': '2026-05-28 14:05:35 UTC'}
  - {'row_id': 1347, 'market_timestamp': 1779977138211, 'close': 72657.99, 'parsed_time': '2026-05-28 14:05:38 UTC'}
  - {'row_id': 1348, 'market_timestamp': 1779977139699, 'close': 72630.75, 'parsed_time': '2026-05-28 14:05:39 UTC'}
- historical_market_rows: rows=11, min=72612.61, max=72901.13, dt_source=market_timestamp, file=outputs\historical_market_rows.csv
  - {'row_id': 1341, 'market_timestamp': 1779977049555, 'start_ts': 1779977029935, 'end_ts': 1779977049555, 'open': 72847.4, 'high': 72852.4, 'low': 72820.0, 'close': 72852.4, 'parsed_time': '2026-05-28 14:04:09 UTC'}
  - {'row_id': 1342, 'market_timestamp': 1779977073567, 'start_ts': 1779977049555, 'end_ts': 1779977073567, 'open': 72852.4, 'high': 72901.13, 'low': 72852.4, 'close': 72899.5, 'parsed_time': '2026-05-28 14:04:33 UTC'}
  - {'row_id': 1343, 'market_timestamp': 1779977113621, 'start_ts': 1779977073570, 'end_ts': 1779977113621, 'open': 72898.0, 'high': 72898.01, 'low': 72826.72, 'close': 72826.72, 'parsed_time': '2026-05-28 14:05:13 UTC'}
  - {'row_id': 1344, 'market_timestamp': 1779977134519, 'start_ts': 1779977113621, 'end_ts': 1779977134519, 'open': 72826.67, 'high': 72826.91, 'low': 72760.3, 'close': 72760.3, 'parsed_time': '2026-05-28 14:05:34 UTC'}
  - {'row_id': 1345, 'market_timestamp': 1779977134856, 'start_ts': 1779977134520, 'end_ts': 1779977134856, 'open': 72758.28, 'high': 72758.28, 'low': 72710.17, 'close': 72710.17, 'parsed_time': '2026-05-28 14:05:34 UTC'}
  - {'row_id': 1346, 'market_timestamp': 1779977135817, 'start_ts': 1779977134856, 'end_ts': 1779977135817, 'open': 72710.04, 'high': 72712.0, 'low': 72679.38, 'close': 72688.0, 'parsed_time': '2026-05-28 14:05:35 UTC'}
  - {'row_id': 1347, 'market_timestamp': 1779977138211, 'start_ts': 1779977135818, 'end_ts': 1779977138211, 'open': 72688.0, 'high': 72693.08, 'low': 72657.99, 'close': 72657.99, 'parsed_time': '2026-05-28 14:05:38 UTC'}
  - {'row_id': 1348, 'market_timestamp': 1779977139699, 'start_ts': 1779977138211, 'end_ts': 1779977139699, 'open': 72657.98, 'high': 72657.98, 'low': 72625.0, 'close': 72630.75, 'parsed_time': '2026-05-28 14:05:39 UTC'}
- live_market_rows: rows=136721, min=None, max=None, dt_source=NO_TIMESTAMP_PARSED, file=outputs\market_rows.csv

### 14:05_local_Africa_Lagos_as_13:05_UTC

- historical_observation_rows: rows=2, min=73490.19, max=73494.63, dt_source=market_timestamp, file=outputs\historical_observation_rows.csv
  - {'row_id': 1204, 'market_timestamp': 1779973487600, 'close': 73494.63, 'parsed_time': '2026-05-28 13:04:47 UTC'}
  - {'row_id': 1205, 'market_timestamp': 1779973557588, 'close': 73490.19, 'parsed_time': '2026-05-28 13:05:57 UTC'}
- historical_market_rows: rows=2, min=73456.63, max=73498.96, dt_source=market_timestamp, file=outputs\historical_market_rows.csv
  - {'row_id': 1204, 'market_timestamp': 1779973487600, 'start_ts': 1779973439419, 'end_ts': 1779973487600, 'open': 73464.84, 'high': 73494.63, 'low': 73456.63, 'close': 73494.63, 'parsed_time': '2026-05-28 13:04:47 UTC'}
  - {'row_id': 1205, 'market_timestamp': 1779973557588, 'start_ts': 1779973487662, 'end_ts': 1779973557588, 'open': 73494.63, 'high': 73498.96, 'low': 73475.44, 'close': 73490.19, 'parsed_time': '2026-05-28 13:05:57 UTC'}
- live_market_rows: rows=136721, min=None, max=None, dt_source=NO_TIMESTAMP_PARSED, file=outputs\market_rows.csv

### 13:05_UTC

- historical_observation_rows: rows=2, min=73490.19, max=73494.63, dt_source=market_timestamp, file=outputs\historical_observation_rows.csv
  - {'row_id': 1204, 'market_timestamp': 1779973487600, 'close': 73494.63, 'parsed_time': '2026-05-28 13:04:47 UTC'}
  - {'row_id': 1205, 'market_timestamp': 1779973557588, 'close': 73490.19, 'parsed_time': '2026-05-28 13:05:57 UTC'}
- historical_market_rows: rows=2, min=73456.63, max=73498.96, dt_source=market_timestamp, file=outputs\historical_market_rows.csv
  - {'row_id': 1204, 'market_timestamp': 1779973487600, 'start_ts': 1779973439419, 'end_ts': 1779973487600, 'open': 73464.84, 'high': 73494.63, 'low': 73456.63, 'close': 73494.63, 'parsed_time': '2026-05-28 13:04:47 UTC'}
  - {'row_id': 1205, 'market_timestamp': 1779973557588, 'start_ts': 1779973487662, 'end_ts': 1779973557588, 'open': 73494.63, 'high': 73498.96, 'low': 73475.44, 'close': 73490.19, 'parsed_time': '2026-05-28 13:05:57 UTC'}
- live_market_rows: rows=136721, min=None, max=None, dt_source=NO_TIMESTAMP_PARSED, file=outputs\market_rows.csv

### 15:05_UTC

- historical_observation_rows: rows=0, min=None, max=None, dt_source=market_timestamp, file=outputs\historical_observation_rows.csv
- historical_market_rows: rows=0, min=None, max=None, dt_source=market_timestamp, file=outputs\historical_market_rows.csv
- live_market_rows: rows=136721, min=None, max=None, dt_source=NO_TIMESTAMP_PARSED, file=outputs\market_rows.csv

## Dashboard / RDM Compare

- birth_time: 2026-05-28 14:05:34
- real_birth_price: 72710.17
- real_zone_upper_edge: 73131.38
- real_zone_lower_edge: 72760.3
- active_core_upper: 72959.165
- active_core_lower: 72866.395
- density_peak_price: 72954.32
- final_price: 73021.41
- live_latest_price: 72762.36
- source_csvs: {'rdm_results': 'research/zone_mechanics_cycle3_results.csv', 'real_geometry': 'research/zone_real_geometry_tracking.csv', 'interaction_core': 'research/zone_interaction_core_geometry.csv', 'density': 'research/zone_interaction_density_map.csv', 'live_evolution': 'research/zone_live_rdm_evolution.csv'}
- live_latest_timestamp: 1779977289492

## Stale / Mixed Artifact Check

- live_market_rows: old modified 2026-05-21 00:31:54
- dashboard_v2_episodes_expected: missing
- dashboard_v2_episode_research_expected: missing

## File Modified Times / Row Counts

- historical_v2_episodes: {'path': 'outputs\\historical_replay_dashboard_v2_episodes.csv', 'exists': True, 'size_bytes': 40176, 'modified': '2026-05-28 15:57:06', 'rows': 86}
- historical_v2_events: {'path': 'outputs\\historical_replay_observation_v2_events.csv', 'exists': True, 'size_bytes': 219638, 'modified': '2026-05-28 15:57:06', 'rows': 517}
- historical_observation_rows: {'path': 'outputs\\historical_observation_rows.csv', 'exists': True, 'size_bytes': 2065098, 'modified': '2026-05-28 15:56:59', 'rows': 1562}
- historical_market_rows: {'path': 'outputs\\historical_market_rows.csv', 'exists': True, 'size_bytes': 292515, 'modified': '2026-05-28 15:56:59', 'rows': 1562}
- live_market_rows: {'path': 'outputs\\market_rows.csv', 'exists': True, 'size_bytes': 19420720, 'modified': '2026-05-21 00:31:54', 'rows': 136721}
- dashboard_v2_episodes_expected: {'path': 'outputs\\dashboard_v2_episodes.csv', 'exists': False}
- dashboard_v2_episode_research_expected: {'path': 'outputs\\dashboard_v2_episode_research.csv', 'exists': False}
- research_log: {'path': 'research\\phase1b_episode_research_log.csv', 'exists': True, 'size_bytes': 45996, 'modified': '2026-05-28 15:58:22', 'rows': 27}
- rdm_results: {'path': 'research\\zone_mechanics_cycle3_results.csv', 'exists': True, 'size_bytes': 90838, 'modified': '2026-05-28 15:58:42', 'rows': 27}
- real_geometry: {'path': 'research\\zone_real_geometry_tracking.csv', 'exists': True, 'size_bytes': 20327, 'modified': '2026-05-28 15:58:42', 'rows': 27}
- live_evolution: {'path': 'research\\zone_live_rdm_evolution.csv', 'exists': True, 'size_bytes': 1527678, 'modified': '2026-05-28 15:58:44', 'rows': 2739}
- interaction_core: {'path': 'research\\zone_interaction_core_geometry.csv', 'exists': True, 'size_bytes': 11135, 'modified': '2026-05-28 15:58:44', 'rows': 27}
- density: {'path': 'research\\zone_interaction_density_map.csv', 'exists': True, 'size_bytes': 6143, 'modified': '2026-05-28 15:58:44', 'rows': 27}
- true_lifecycle: {'path': 'research\\zone_true_lifecycle_tracking.csv', 'exists': True, 'size_bytes': 9314, 'modified': '2026-05-28 15:58:44', 'rows': 27}
- birth: {'path': 'research\\zone_birth_registry.csv', 'exists': True, 'size_bytes': 12713, 'modified': '2026-05-28 15:58:44', 'rows': 27}
- death: {'path': 'research\\zone_death_registry.csv', 'exists': True, 'size_bytes': 6861, 'modified': '2026-05-28 15:58:44', 'rows': 27}

## Diagnostic Notes

- Binance chart external value was not fetched because diagnostics are local/read-only/no network.
- Dashboard historical mode loads historical_observation_rows.csv and historical_replay_dashboard_v2_episodes.csv.
- Default/live dashboard files such as outputs/market_rows.csv are older than current historical files and can cause visual confusion if mode is mixed.

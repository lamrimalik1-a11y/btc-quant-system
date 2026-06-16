# Raw-Trade Replay Parity PoC -- 2026-06-11 00:00:00-00:35:49 UTC

## Inputs

- Raw trades in window: 115197
- PoC rows built (500 raw trades/row, full rows only): 230
- LIVE rows in same market_timestamp window (observation_rows.csv): 221

## Row-count comparison

- PoC row count: 230
- LIVE row count: 221
- Difference: 9 (4.07% )
- Index-aligned rows compared (min): 221

## OHLCV / delta / velocity comparison (tolerance: <1e-6 relative)

- close: 2/221 rows within tolerance (max rel diff = 0.00209296, mean rel diff = 0.000415509)
- volume: 0/221 rows within tolerance (max rel diff = 21.4373, mean rel diff = 0.920158)
- delta: 0/221 rows within tolerance (max rel diff = 665.232, mean rel diff = 5.55001)
- velocity: 0/221 rows within tolerance (max rel diff = 395.388, mean rel diff = 4.85374)

## Z-score comparison (tolerance: <0.01 absolute)

- price_zscore: 4/221 rows within tolerance (max abs diff = 2.21252, mean abs diff = 0.662554)
- volume_zscore: 12/221 rows within tolerance (max abs diff = 4.82905, mean abs diff = 0.53465)
- velocity_zscore: 13/221 rows within tolerance (max abs diff = 4.65872, mean abs diff = 0.33118)
- spread_zscore: 0/0 rows within tolerance (max abs diff = nan, mean abs diff = nan)
- delta_zscore: 10/221 rows within tolerance (max abs diff = 4.61191, mean abs diff = 0.503843)

## Layer / state comparison (tolerance: exact match)

- dashboard_v2_state: 165/221 exact matches
- dashboard_v2_layer_count: 92/221 exact matches
- dashboard_v2_active_layers: 55/221 exact matches
- extreme_event_state: 178/221 exact matches

## First divergence (close price)

- First divergence at index 0 (PoC row_id=1, LIVE row_id=1896): PoC close=61524.0 vs LIVE close=61521.25
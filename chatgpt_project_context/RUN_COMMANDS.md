# Run Commands

## Generate Historical Replay

### Standard command (recommended — all three tiers active)

```powershell
python tools/generate_binance_historical_replay.py --start "YYYY-MM-DD 00:00:00" --end "YYYY-MM-DD 23:59:59" --symbol BTCUSDT --row-size 500
```

### Current research target (14-day window)

```powershell
python tools/generate_binance_historical_replay.py --start "2026-05-20 00:00:00" --end "2026-06-02 00:00:00" --symbol BTCUSDT --row-size 500
```

### Download behavior (3-tier architecture)

For each UTC day in the requested range, priority order:

1. **CACHE HIT** — `archives/BTCUSDT/raw-trades/{date}.csv` exists and passes verification → no download, <5 sec total for any range
2. **ZIP HIT** — downloads daily ZIP from `data.binance.vision` (only for dates >= 2 days old) → ~3-10 sec per day, then saves to local cache
3. **API fallback** — uses existing Binance aggTrades API with retry/backoff/checkpoint → only for recent dates or when ZIP unavailable

After any ZIP or API download, the data is saved to the local raw-trades cache so the next run uses CACHE HIT.

### Second run of the same date range

```powershell
python tools/generate_binance_historical_replay.py --start "2026-05-20 00:00:00" --end "2026-06-02 00:00:00" --symbol BTCUSDT --row-size 500
```

Output: `CACHE HIT` for all days, completes in ~5 seconds, zero network requests.

### Overwrite and re-download everything

```powershell
python tools/generate_binance_historical_replay.py --start "2026-05-20 00:00:00" --end "2026-06-02 00:00:00" --overwrite --no-local-cache --no-zip
```

### Skip ZIP, use API only (for testing or recent dates)

```powershell
python tools/generate_binance_historical_replay.py --start "2026-06-01 00:00:00" --end "2026-06-03 23:59:59" --no-zip
```

### Use --slow-mode (API fallback only, for unstable networks)

```powershell
python tools/generate_binance_historical_replay.py --start "YYYY-MM-DD 00:00:00" --end "YYYY-MM-DD 23:59:59" --no-zip --slow-mode
```

Important: `--slow-mode` is no longer needed for historical downloads because ZIP and local cache avoid thousands of API calls. Use `--slow-mode` only when the API fallback is needed for very recent dates and the network is unstable (WinError 10060 storms).

### Available CLI flags

| Flag | Default | Effect |
|---|---|---|
| `--no-local-cache` | OFF | Skip Tier 1 (local raw-trades cache) |
| `--no-zip` | OFF | Skip Tier 2 (Binance public ZIP) |
| `--slow-mode` | OFF | Sets request_sleep=2.0s, timeout=240s, max_retries=40 (for API fallback on unstable networks) |
| `--max-retries N` | 15 | Override max retry attempts per API batch |
| `--timeout N` | 150 | Override HTTP timeout in seconds |
| `--request-sleep N` | 0.5 | Override inter-batch sleep in seconds |
| `--overwrite` | OFF | Clear checkpoint and re-download everything |
| `--overwrite-archive` | OFF | Overwrite existing processed archive entries |
| `--save-raw` | OFF | Also archive raw aggTrades CSV |

### Local raw-trades cache location

```
archives/BTCUSDT/raw-trades/
  2026-05-20.csv
  2026-05-21.csv
  ...
```

One CSV file per UTC day. Verified before reuse. Corrupted files are skipped but preserved for inspection.

## Analyze Phase 1B Episodes

Default score >= 4 research mode:

```powershell
python tools/analyze_phase1b_episode_research.py --mode score4plus
```

All episodes mode:

```powershell
python tools/analyze_phase1b_episode_research.py --mode all
```

## Run RDM Market Mechanics Calculator

```powershell
python research/zone_mechanics_calculator.py
```

Research output CSVs:

- `research/zone_mechanics_cycle3_results.csv`
- `research/zone_strength_profile.csv`
- `research/zone_vs_attacker_profile.csv`
- `research/zone_anomaly_profile.csv`
- `research/zone_reinforcement_profile.csv`
- `research/attacker_conversion_profile.csv`
- `research/force_allocation_profile.csv`

## Run Dashboard

```powershell
streamlit run dashboard_app.py
```

## Live Observation Only

```powershell
python -m engines.stream_manager
```

Important: Live observation is not execution. No entries, exits, BUY / SELL, or live signals.

## Validation

```powershell
python -m py_compile tools/generate_binance_historical_replay.py research/zone_mechanics_calculator.py dashboard_app.py dashboard/research_mapping.py dashboard/overlay_renderer.py context_memory.py tools/analyze_phase1b_episode_research.py
```

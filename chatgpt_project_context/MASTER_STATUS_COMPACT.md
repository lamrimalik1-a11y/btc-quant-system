# Master Status Compact

## Current Stable Status

The project is stable at:

PHASE1B_HYBRID_DOWNLOADER_STABLE

Prior checkpoints:

- PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE
- PHASE1B_DOWNLOAD_STABILITY_FIX_STABLE
- PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK

Current system status:

- Dashboard V2 = stable
- Dashboard V2 replay = operational
- Research Agent V1 = stable
- RDM Market Mechanics V1.5 = validated
- RDM Market Mechanics V1.6-A through B7.7 = completed
- Exposure physics = validated (omega ~ sigma x penetration, r=0.9935)
- Downloader = 3-tier hybrid (local cache / ZIP / API)
- Local raw-trades cache = operational
- Binance public ZIP archive = operational

## Downloader Architecture

3-tier priority per UTC day:

Tier 1: Local raw trade cache
- archives/{SYMBOL}/raw-trades/{date}.csv
- If valid: CACHE HIT, zero network requests

Tier 2: Binance public ZIP archive
- data.binance.vision daily ZIP files
- If date >= 2 days old: ZIP HIT, saves to Tier 1 cache

Tier 3: Binance aggTrades API
- Only for recent dates or ZIP failures
- Existing retry/backoff/checkpoint logic

Key detail: Binance ZIP timestamps are in microseconds. Converted to milliseconds (divide by 1000) before use. Rest of pipeline unchanged.

Standard command:

```powershell
python tools/generate_binance_historical_replay.py --start "2026-05-20 00:00:00" --end "2026-06-02 00:00:00" --symbol BTCUSDT --row-size 500
```

## Completed Phases / Modules

Completed:

- Dashboard V2 statistical layer
- Dashboard V2 replay events / episodes
- Dashboard V2 Streamlit display
- Phase 1B Episode Research Assistant
- Research Dashboard
- RDM Market Mechanics V1.1 through V1.5
- RDM V1.6-A Numerical Foundation
- RDM V1.6-B1 through B7.7 (full attacker and exposure physics series)
- Downloader stability improvements (retries, backoff, jitter, WinError 10060)
- PHASE1B_RAW_TRADE_ARCHIVE_V1 (Tier 1 local cache)
- PHASE1B_BINANCE_ZIP_ARCHIVE_V1 (Tier 2 ZIP archive)

## Validated Physics (RDM V1.6)

sigma x penetration vs omega: r = 0.9935

Structural engagement chain:

Force -> sigma_barre filter -> Penetration -> Omega -> mechanical_family -> Growth or Damage

sigma_barre is driven by structural memory (reclaim_history r=0.69, mechanical_memory_score r=0.67), NOT by force.

Surface Damage hypothesis: REJECTED. Zero-omega damage is time-based temporal decay formula.

## Next Steps

Priority:

1. Run historical replay for research dataset (2026-05-20 to 2026-06-02)
2. Rebuild 634-row RDM research base (currently 50-row single-day dataset)
3. Continue RDM V1.6 development on full dataset

Do not:

- Enter Phase 2
- Add execution / entries / exits / BUY / SELL
- Change Dashboard V2 scoring
- Change replay scoring
- Change lifecycle logic

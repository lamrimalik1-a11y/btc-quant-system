# Current Checkpoint

## Active Checkpoint

Checkpoint:

PHASE1B_HYBRID_DOWNLOADER_STABLE

Status:

- Research only
- Observation only
- No Phase 2
- No execution
- No entries
- No live signals
- No scoring changes
- No Dashboard V2 scoring changes
- No RDM formula changes
- No lifecycle changes
- No replay formula changes

## Prior Checkpoints (preserved)

- `PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE`
- `PHASE1B_DOWNLOAD_STABILITY_FIX_STABLE`
- `PHASE1B_RDM_REPLAY_CONSISTENCY_LOCK`
- `PHASE1B_RDM_VISUALIZATION_STABLE`
- `PHASE1B_RDM_MARKET_MECHANICS_V1_5`

---

## PHASE1B_HYBRID_DOWNLOADER_STABLE

### PHASE1B_RAW_TRADE_ARCHIVE_V1 — Tier 1

Status: COMPLETED

Local raw trade archive. One CSV per UTC day stored in `archives/{SYMBOL}/raw-trades/{date}.csv`.

Implemented:

- `_raw_trade_cache_path(symbol, date_str)` — path helper
- `_day_ms_range(date_str)` — UTC day boundary in milliseconds
- `_iter_utc_days(start_ms, end_ms)` — list of UTC date strings for a time range
- `_trade_to_csv_row(trade)` — dict to 8-column CSV row
- `_csv_row_to_trade(row)` — 8-column CSV row to dict
- `_verify_raw_trades(trades, date_str)` — sanity check (count, timestamp bounds)
- `try_load_raw_trade_cache(symbol, date_str)` — load with verification, CACHE HIT log
- `save_raw_trade_cache(symbol, date_str, trades)` — atomic write (temp + rename + verify)

Cache file format (8 columns):

```
aggTradeId, price, qty, firstTradeId, lastTradeId, timestamp, isBuyerMaker, isBestMatch
```

Matches API dict keys `{a, p, q, f, l, T, m, M}` exactly.

Verification rules:

- len >= 1000 (sanity floor)
- first timestamp within expected UTC day
- last timestamp within expected UTC day
- corrupted files are skipped but preserved on disk

### PHASE1B_BINANCE_ZIP_ARCHIVE_V1 — Tier 2

Status: COMPLETED

Binance public data archive. Daily aggTrades ZIP files from `data.binance.vision`.

Implemented:

- `BINANCE_PUBLIC_DATA_URL = "https://data.binance.vision"`
- `BINANCE_ZIP_LAG_DAYS = 2`
- `is_binance_zip_available(date_str)` — gate: date <= today UTC - 2 days
- `download_day_from_binance_zip(symbol, date_str)` — HTTP GET, in-memory ZIP extract, CSV parse

URL pattern:

```
https://data.binance.vision/data/spot/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{YYYY-MM-DD}.zip
```

Important implementation detail:

Binance public ZIP timestamps are in **microseconds**. API timestamps are in **milliseconds**. Conversion applied inside `download_day_from_binance_zip`:

```python
t["T"] = t["T"] // 1000   # microseconds -> milliseconds
```

Failure handling:

- HTTP 404: date not yet available → fall through to Tier 3
- HTTP 5xx / network error → fall through to Tier 3
- Bad ZIP / parse error → fall through to Tier 3
- All failures are logged, never silently swallowed

After ZIP success: data is saved to Tier 1 cache (`save_raw_trade_cache`) so the next run gets CACHE HIT.

Validated test:

```
BTCUSDT 2026-05-25
ZIP downloaded: 542,386 trades | 7.7 MB | 2.7 seconds
Timestamps: within 2026-05-25 UTC (after microsecond conversion)
Cache save: OK
Second run: CACHE HIT (542,386 trades, 0 network requests)
```

### 3-Tier Priority Order (per UTC day)

```
TIER 1  archives/{SYMBOL}/raw-trades/{date}.csv
        Valid cache exists → CACHE HIT — zero network requests

TIER 2  data.binance.vision ZIP (gate: date <= today - 2 days)
        ZIP available → ZIP HIT — save to Tier 1 cache — done

TIER 3  api.binance.com/api/v3/aggTrades (existing API loop)
        Per-day checkpoint/resume — save to Tier 1 cache on success
```

### New CLI Flags

- `--no-local-cache` — skip Tier 1 (always download fresh)
- `--no-zip` — skip Tier 2 (API only for uncached dates)

Existing flags unchanged:

- `--slow-mode` — for API fallback on unstable networks (not needed for historical downloads using ZIP/cache)
- `--max-retries N`, `--timeout N`, `--request-sleep N`

### Why This Solves WinError 10060

Historical downloads previously required thousands of sequential API calls (200-500 per day, 1400-3500 for a 7-day window). Each API call is a separate TCP connection. WinError 10060 fires at the OS-level TCP stack under this load.

After this update:
- Old dates (>= 2 days old): one ZIP file per day, one TCP connection, ~3 sec → no WinError 10060
- Same range on second run: zero TCP connections → no WinError 10060
- Recent dates only: API fallback still available with existing retry/backoff

---

## RDM V1.6 Exposure Physics (prior checkpoint, preserved)

See `PHASE1B_RDM_EXPOSURE_PHYSICS_STABLE` checkpoint content in `RDM_MARKET_MECHANICS_STATUS.md`.

Core finding: `sigma × penetration ≈ omega` (r = 0.9935). Omega is the primary deep structural exposure variable.

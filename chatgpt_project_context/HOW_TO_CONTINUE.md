# How To Continue In A New ChatGPT Project

## What To Upload

Upload these files into ChatGPT Project knowledge:

- `chatgpt_project_context/PROJECT_OVERVIEW.md`
- `chatgpt_project_context/MASTER_STATUS_COMPACT.md`
- `chatgpt_project_context/RDM_MARKET_MECHANICS_STATUS.md`
- `chatgpt_project_context/HOW_TO_CONTINUE.md`
- `chatgpt_project_context/RUN_COMMANDS.md`
- `chatgpt_project_context/CURRENT_CHECKPOINT.md`
- `README_CHATGPT_PROJECT.md`

Recommended additional source files:

- `MASTER_STATUS.md`
- `research/zone_mechanics_calculator.py`
- `tools/generate_binance_historical_replay.py`
- `tools/analyze_phase1b_episode_research.py`
- `dashboard_app.py`
- `context_memory.py`

## First Message

```text
You are working on my BTC Quant repo in PHASE 1B+ Research Expansion.
Load the uploaded project context files first.
Current checkpoint: PHASE1B_HYBRID_DOWNLOADER_STABLE.
Rules: research only, no Phase 2, no execution, no entries, no live signals,
no scoring changes, no RDM formula changes, no lifecycle changes.
Completed: RDM V1.6-A through B7.7 (exposure physics) + 3-tier hybrid downloader.
Key finding: omega ~ sigma x penetration (r=0.9935).
Downloader now uses: Tier 1 local cache / Tier 2 Binance ZIP / Tier 3 API fallback.
Next: run historical replay to rebuild 634-row RDM research dataset.
```

## Priority Next Steps

1. Run historical replay for 2026-05-20 to 2026-06-02

```powershell
python tools/generate_binance_historical_replay.py --start "2026-05-20 00:00:00" --end "2026-06-02 00:00:00" --symbol BTCUSDT --row-size 500
```

Most days will be served by ZIP (Tier 2) or local cache (Tier 1). Recent days fall back to API. After the first run, all days are cached locally — re-runs complete in ~5 seconds.

2. Run RDM calculator to rebuild 634-row research base

```powershell
python research/zone_mechanics_calculator.py
```

3. Continue RDM V1.6 development (B8 or later) on the full 634-row dataset.

## Command Sequence (new session)

Validate everything compiles:

```powershell
python -m py_compile tools/generate_binance_historical_replay.py research/zone_mechanics_calculator.py dashboard_app.py dashboard/research_mapping.py dashboard/overlay_renderer.py context_memory.py tools/analyze_phase1b_episode_research.py
```

Run historical replay:

```powershell
python tools/generate_binance_historical_replay.py --start "2026-05-20 00:00:00" --end "2026-06-02 00:00:00" --symbol BTCUSDT --row-size 500
```

Run RDM calculator:

```powershell
python research/zone_mechanics_calculator.py
```

Run dashboard:

```powershell
streamlit run dashboard_app.py
```

## What Not To Do

Do not:

- Add Phase 2
- Add execution / entries / exits / BUY / SELL
- Change Dashboard V2 scoring
- Change replay scoring
- Change RDM formulas
- Change lifecycle logic
- Add live signals
- Treat RDM results as trade signals

## Downloader Notes

The new 3-tier downloader eliminates WinError 10060 for historical dates by using:
- Tier 2 ZIP: one HTTP request per day (~3-10 sec) instead of 200-500 API calls
- Tier 1 cache: zero requests on repeat runs

Use `--slow-mode` only when downloading very recent dates (< 2 days old) on an unstable network. For all historical dates, ZIP and cache handle it without slow-mode.

## Replay Source Rule

In HISTORICAL_REPLAY_MODE, Dashboard, overlays, RDM, lifecycle, density, cases, and summaries must read explicit historical replay sources only. Do not silently fallback to live/default files.

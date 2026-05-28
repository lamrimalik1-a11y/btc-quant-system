# Run Commands

## Generate Historical Replay

```powershell
python tools/generate_binance_historical_replay.py --start YYYY-MM-DD --end YYYY-MM-DD --overwrite
```

Notes:

- Downloader has robustness upgrades.
- Timeout = 120 seconds.
- Retry = 10.
- Exponential backoff is active.
- Checkpoint / resume is active.

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

## Run Dashboard

```powershell
streamlit run dashboard_app.py
```

## Live Observation Only

```powershell
python -m engines.stream_manager
```

Important:

Live observation is not execution. No entries, exits, BUY / SELL, or live signals.

## Validation

```powershell
python -m py_compile research/zone_mechanics_calculator.py dashboard_app.py dashboard/research_mapping.py dashboard/overlay_renderer.py context_memory.py tools/analyze_phase1b_episode_research.py
```

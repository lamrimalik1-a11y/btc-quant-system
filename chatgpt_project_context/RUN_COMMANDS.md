# Run Commands

## Generate Historical Replay

Basic (resume if interrupted):

```powershell
python tools/generate_binance_historical_replay.py --start "YYYY-MM-DD 00:00:00" --end "YYYY-MM-DD 23:59:59"
```

Overwrite from scratch:

```powershell
python tools/generate_binance_historical_replay.py --start "YYYY-MM-DD 00:00:00" --end "YYYY-MM-DD 23:59:59" --overwrite
```

With stability overrides (for persistent WinError 10060 networks):

```powershell
python tools/generate_binance_historical_replay.py --start "YYYY-MM-DD 00:00:00" --end "YYYY-MM-DD 23:59:59" --max-retries 25 --timeout 180
```

Notes:

- Timeout = 150 seconds (raised from 120).
- Max retries = 15 (raised from 10).
- Extended backoff: [10, 20, 40, 80, 120, 180, 240, 300]s.
- Retry jitter active (±30% random).
- WinError 10060 detection: uses 1.5× longer backoff.
- Checkpoint / resume: automatic — re-run same command to resume.
- Resume deduplication: partial file is deduplicated by aggTrade ID on resume.
- Progress checkpoint logged every 25 batches.
- Final verification printed on completion (row count, first/last timestamp, duplicate check).
- New CLI: `--max-retries N`, `--timeout N`

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

Output files:

- `research/zone_mechanics_cycle3_results.csv`
- `research/zone_strength_profile.csv`
- `research/zone_vs_attacker_profile.csv`
- `research/zone_anomaly_profile.csv`
- `research/zone_reinforcement_profile.csv`
- `research/attacker_conversion_profile.csv`
- `research/force_allocation_profile.csv`
- `research/attacker_conversion_profile.csv` (B7)

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
python -m py_compile research/zone_mechanics_calculator.py dashboard_app.py dashboard/research_mapping.py dashboard/overlay_renderer.py context_memory.py tools/analyze_phase1b_episode_research.py tools/generate_binance_historical_replay.py
```

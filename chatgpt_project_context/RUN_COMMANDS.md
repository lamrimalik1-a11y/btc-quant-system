# Run Commands

## Generate Historical Replay (3-tier hybrid downloader)

Standard (uses local cache -> Binance ZIP -> API fallback):

```powershell
python tools/generate_binance_historical_replay.py --start "YYYY-MM-DD 00:00:00" --end "YYYY-MM-DD 23:59:59" --symbol BTCUSDT --row-size 500
```

Extended data collection (45-60 day window):

```powershell
python tools/generate_binance_historical_replay.py --start "2026-05-01 00:00:00" --end "2026-07-01 00:00:00" --symbol BTCUSDT --row-size 500
```

Second run (all from local cache, ~5 seconds):

```powershell
python tools/generate_binance_historical_replay.py --start "2026-05-01 00:00:00" --end "2026-07-01 00:00:00" --symbol BTCUSDT --row-size 500
```

For unstable networks (API fallback only):

```powershell
python tools/generate_binance_historical_replay.py --start "YYYY-MM-DD 00:00:00" --end "YYYY-MM-DD 23:59:59" --no-zip --slow-mode
```

CLI flags:
    --no-local-cache    Skip Tier 1 (local raw-trades cache)
    --no-zip            Skip Tier 2 (Binance public ZIP)
    --slow-mode         Sets request_sleep=2.0s, timeout=240s, max_retries=40
    --max-retries N     Override max retry attempts per API batch
    --timeout N         Override HTTP timeout in seconds
    --stream            Bounded-memory streaming rebuild path (PHASE1B_STREAMING_REPLAY_STABLE,
                        EXPERIMENTAL until Stage 3 equivalence below is confirmed PASS).
                        Requires all needed days already in the Tier-1 raw-trade cache
                        (raises SystemExit on any missing day -- never downloads).

## Streaming Replay (--stream, bounded memory) -- EXPERIMENTAL

Same CLI as the standard command, with `--stream` added. Output files
and locations are identical (outputs/historical_*.csv). Use only after
pre-caching the window with a normal (non-stream) run.

```powershell
python tools/generate_binance_historical_replay.py --start "YYYY-MM-DD 00:00:00" --end "YYYY-MM-DD 23:59:59" --symbol BTCUSDT --row-size 500 --stream
```

### Stage 3 equivalence test (April 2026-04-01 -> 2026-05-01)

Proves the streaming path is byte-identical to the in-memory path.
Run sequentially (both write to outputs/, so copy results out between runs):

```powershell
New-Item -ItemType Directory -Force -Path "research\equivalence_april\inmemory" | Out-Null
New-Item -ItemType Directory -Force -Path "research\equivalence_april\stream"   | Out-Null

# 1. OLD in-memory run
python tools\generate_binance_historical_replay.py --start "2026-04-01 00:00:00" --end "2026-05-01 00:00:00" --row-size 500 --no-zip --overwrite --overwrite-archive

# 2. Preserve its outputs
Copy-Item outputs\historical_observation_rows.csv             research\equivalence_april\inmemory\
Copy-Item outputs\historical_market_rows.csv                   research\equivalence_april\inmemory\
Copy-Item outputs\historical_replay_dashboard_v2_episodes.csv  research\equivalence_april\inmemory\

# 3. NEW streaming run (same window, overwrites outputs/)
python tools\generate_binance_historical_replay.py --start "2026-04-01 00:00:00" --end "2026-05-01 00:00:00" --row-size 500 --overwrite --overwrite-archive --stream

# 4. Preserve its outputs
Copy-Item outputs\historical_observation_rows.csv             research\equivalence_april\stream\
Copy-Item outputs\historical_market_rows.csv                   research\equivalence_april\stream\
Copy-Item outputs\historical_replay_dashboard_v2_episodes.csv  research\equivalence_april\stream\

# 5. Compare
Get-FileHash research\equivalence_april\inmemory\historical_observation_rows.csv, research\equivalence_april\stream\historical_observation_rows.csv -Algorithm SHA256
Get-FileHash research\equivalence_april\inmemory\historical_market_rows.csv, research\equivalence_april\stream\historical_market_rows.csv -Algorithm SHA256
Get-FileHash research\equivalence_april\inmemory\historical_replay_dashboard_v2_episodes.csv, research\equivalence_april\stream\historical_replay_dashboard_v2_episodes.csv -Algorithm SHA256
```

PASS = all 3 hash pairs identical. If only the V2 episodes hash
differs, suspect the `pd.read_csv` read-back dtype issue (see
CURRENT_CHECKPOINT.md "Outstanding before --stream is trusted").

## Rebuild Research Dataset (Episode Research + RDM)

```powershell
python tools/analyze_phase1b_episode_research.py --mode score4plus
python research/zone_mechanics_calculator.py
```

Outputs produced by zone_mechanics_calculator.py:
    research/zone_mechanics_cycle3_results.csv     — zone cases
    research/zone_attacker_evolution.csv           — B1 attacker
    research/zone_strength_profile.csv             — B4-A ZSS
    research/zone_vs_attacker_profile.csv          — B4-B force ratio
    research/zone_anomaly_profile.csv              — B5 anomaly
    research/zone_reinforcement_profile.csv        — B6 reinforcement
    research/attacker_conversion_profile.csv       — B7 conversion
    research/force_allocation_profile.csv          — B7.5 allocation
    research/zone_visit_timeline.csv               — B8 visits
    research/zone_health_evolution.csv             — B9 health
    research/zone_structural_trajectory.csv        — B10 trajectory
    research/zone_structural_prediction.csv        — B11 prediction
    research/zone_synthesis.csv                    — Synthesis Engine output

## Run Dashboard

```powershell
streamlit run dashboard_app.py
```

## Live Observation Only

```powershell
python -m engines.stream_manager
```

## Validation

```powershell
python -m py_compile research/synthesis_engine.py research/zone_mechanics_calculator.py dashboard_app.py dashboard/research_mapping.py dashboard/overlay_renderer.py context_memory.py tools/analyze_phase1b_episode_research.py tools/generate_binance_historical_replay.py
```

## Expected Synthesis Output (zone_synthesis.csv)

After running zone_mechanics_calculator.py on the 12-day archive:

    Rows:               276
    Columns:            13
    Duplicate case_id:  0
    Null interpretation: 0

Fields: analysis_run_utc, case_id, episode_id, zone_id, zone_mechanical_state,
        context, structure, engagement, flow, prediction, coherence,
        interpretation, research_only

Example interpretation sentences:
    "TERMINAL zone under opposing flow — failure confirmed."
    "STRENGTHENING zone after 3 visits — hold confirmed."
    "STABLE zone with zone dominant — hold expected."
    "DEGRADING zone — trajectory developing, await further visits."
    "Single-visit zone — insufficient evidence for structural prediction."

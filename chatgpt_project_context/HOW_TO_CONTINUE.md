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

Recommended additional source/status files:

- `MASTER_STATUS.md`
- `research/MASTER_RESEARCH_STATUS.md`
- `research/RESEARCH_JOURNAL.md`
- `dashboard_app.py`
- `dashboard/research_mapping.py`
- `dashboard/overlay_renderer.py`
- `research/zone_mechanics_calculator.py`
- `tools/analyze_phase1b_episode_research.py`
- `tools/generate_binance_historical_replay.py`
- `context_memory.py`

## First Message To Ask ChatGPT

Use this at the start of a new conversation:

```text
You are working on my BTC Quant repo in PHASE 1B+ Research Expansion.
Load the uploaded project context files first.
Current checkpoint is PHASE1B_RDM_MARKET_MECHANICS_V1_5, commit b04a781, tag PHASE1B_RDM_MARKET_MECHANICS_V1_5.
Rules: research only, no Phase 2, no execution, no entries, no live signals, no scoring changes, no Dashboard V2 scoring changes.
Continue from the current RDM Market Mechanics V1.5 state.
```

## Command Sequence To Run

Basic validation:

```powershell
python -m py_compile research/zone_mechanics_calculator.py dashboard_app.py dashboard/research_mapping.py dashboard/overlay_renderer.py context_memory.py tools/analyze_phase1b_episode_research.py
python research/zone_mechanics_calculator.py
```

Run dashboard:

```powershell
streamlit run dashboard_app.py
```

Research assistant:

```powershell
python tools/analyze_phase1b_episode_research.py --mode score4plus
```

Historical replay example:

```powershell
python tools/generate_binance_historical_replay.py --start YYYY-MM-DD --end YYYY-MM-DD --overwrite
```

Live observation command:

```powershell
python -m engines.stream_manager
```

## What Not To Do

Do not:

- Add Phase 2
- Add execution
- Add entries
- Add exits
- Add BUY / SELL logic
- Add live signals
- Add decision engine
- Add risk engine
- Change Dashboard V2 scoring
- Change replay scoring
- Treat RDM research results as trade signals

## Recommended Next Work

Next safe research workflow:

1. Pull only today's data.
2. Run historical replay.
3. Run episode research assistant.
4. Run RDM mechanics calculator.
5. Open dashboard.
6. Observe Dashboard V2 episodes, Active RDM Zone, Interaction Density Band, and RDM lifecycle state.
7. Record false positives, recoveries, ruptures, dormant zones, and density behavior.
8. After today's observation is complete, pull a 10-day replay window.

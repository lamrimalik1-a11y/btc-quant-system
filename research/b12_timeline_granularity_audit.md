# B12 Timeline Granularity + Performance Audit

Audit only. No files modified except this report and its companion CSV.
Data state at audit time (current on-disk files):

| File | Rows | Size |
|---|---|---|
| outputs/historical_replay_dashboard_v2_episodes.csv | 15,925 | 7.8 MB |
| outputs/historical_observation_rows.csv | 295,822 (Feb 1 → Jun 5) | 398 MB |
| research/phase1b_episode_research_log.csv | 4,859 (Score4+) | 9.0 MB |
| research/zone_mechanics_cycle3_results.csv | 4,859 | 16.8 MB |
| research/zone_visit_timeline.csv | **14,083** | 4.5 MB |
| research/zone_live_rdm_evolution.csv | 1,809,010 | 996 MB |

---

## ⚠️ Premise correction

The request states `zone_visit_timeline.csv` "generated 4,859 rows … same as the number of
analyzed cases." **The current file on disk has 14,083 rows, not 4,859.** 4,859 is the number
of *cases* (and the row count of `zone_mechanics_cycle3_results.csv` and the per-case health
file). `zone_visit_timeline.csv` is **already visit-level**: 14,083 visit rows across 4,859
cases (avg 2.898 visits/case), with a real `visit_index` column running 1→9.

---

## TASK 1 — Timeline granularity

**Verdict: TRUE VISIT-LEVEL (within a bounded window — see Task 2).**

| Metric | Value |
|---|---|
| total_rows | 14,083 |
| unique_case_ids | 4,859 |
| cases_with_1_visit | 1,848 |
| cases_with_2plus_visits | 3,011 |
| max_visits_per_case | 9 |
| avg_visits_per_case | 2.898 |
| median_visits_per_case | 3 |

- Each `case_id` appears **1–9 times** (not once).
- `visit_index` column **present**, integer 1→9.
- Multiple rows per case genuinely represent visit 1, 2, 3, … (confirmed below).

**visit_index distribution:** 1→4859, 2→3011, 3→2504, 4→1877, 5→1122, 6→501, 7→167, 8→36, 9→6.

**Top 10 cases by visit count (all = 9 or 8):**
CASE_07038(9), CASE_06951(9), CASE_09450(9), CASE_07651(9), CASE_01119(9),
CASE_05437(9), CASE_12888(8), CASE_07397(8), CASE_02625(8), CASE_00258(8).

**Columns (34):** analysis_run_utc, case_id, episode_id, zone_id, zone_mechanical_state,
visit_index, visit_start_row, visit_end_row, visit_start_time, visit_end_time,
visit_duration_rows, rigidity_at_visit, capacity_at_visit, fatigue_at_visit,
recovery_at_visit, sigma_at_visit, health_at_visit, penetration_at_visit,
max_penetration_at_visit, omega_at_visit, attacker_force_at_visit,
rigidity_change_from_birth, capacity_change_from_birth, fatigue_change_from_birth,
recovery_change_from_birth, rigidity_change_from_previous, capacity_change_from_previous,
fatigue_change_from_previous, health_change_from_previous, inside_zone_rows,
evolution_state_at_visit, span_source, visit_result, research_only.

**All rows for the max-visit case (CASE_07038, 9 visits):** distinct increasing
`visit_start_row` (131232 → 131320), distinct `omega_at_visit` / `penetration_at_visit`
per visit, `health_at_visit` rising 58.3 → 79.0 across visits, all classed GROWTH.
This is unambiguously per-visit data, not a duplicated case summary.

`span_source` for all 14,083 rows = `force_lull_segments` (the primary B3.5-B segmentation;
the touch-flag fallback was not needed in this run).

`visit_result` distribution: GROWTH 6978, DAMAGE 3999, BREAKDOWN 2598, ABSORPTION 478,
RECLAIM 20, REFLECTION 10.

---

## TASK 2 — Are post-return visits stored?

**Verdict: NO. The timeline is visit-level but the window terminates at the return event.**

Empirical proof: of 2,980 cases that have a `return_row`, **0** have any `visit_end_row`
greater than `return_row`. The last visit ends exactly at `return_row`
(e.g. CASE_00011 return_row=266, max_visit_end_row=266).

1. **What defines a "visit"?** A force-lull-segmented attacker attempt span.
   `build_zone_visit_timeline` (zone_mechanics_calculator.py:3548) reads spans via
   `_parse_visit_spans` (:3427) from the attacker frame field
   `rdm_v16b_force_lull_attempt_row_spans` (primary, B3.5-B) →
   `rdm_v16b_attacker_attempt_row_spans` (fallback, B3.5-A). If both absent it falls back to
   `_compute_touch_spans` (:3453), which groups rows where `zone_touch_flag` /
   `inside_zone_flag` / non-dormant `evolution_state` are active, splitting on a 3-row lull
   gap. Each span = one visit row. Structural metrics are taken from the **last** evolution
   row in the span; peaks (penetration, sigma, load) from the max over the span.

2. **Does it stop at the first return?** Not at the *first* return specifically — it emits
   *all* force-lull segments found inside the case's live-evolution window, and there is even
   a RECLAIM class for return events. But the window itself ends at the return.

3. **Does it scan rows after the return event?** No. Visits are filtered to `evo_case`
   (this case's rows in `zone_live_rdm_evolution`), and that frame is bounded by
   `live_row_window` (zone_mechanics_calculator.py:~1855), whose end =
   `max(end_row_id, return_row, preparation_end_row)`. In practice `return_row` is the max,
   so the window stops at the return.

4. **Does it store N+1, N+2, N+3 post-return visits?** No — confirmed by the 0/2,980 result.
   Anything after `return_row` is outside the evolution window and is never segmented.

5. **Current granularity = (C) one row per true visit** — specifically one row per
   force-lull-segmented attacker attempt **within the pre-return → return window**. Two
   qualifications vs the B12.5 target:
   - It is **not Active-Core-specific**: `penetration_at_visit` is reconstructed as
     `fleche_live * real_zone_width` (the full real zone), not Active-Core bounds.
   - It is **return-bounded**: no post-return continuation.

6. **Functions to modify to capture post-return visits** (for reference, not now):
   - `live_row_window` (zone_mechanics_calculator.py ~1855) — the window end caps at
     `return_row`; the cap must be extended (e.g. to a post-return horizon) for any
     post-return data to exist downstream.
   - `build_live_rdm_evolution` (~1843) — consumes that window; needs the extended rows.
   - Upstream attacker span computation that fills `rdm_v16b_force_lull_attempt_row_spans` —
     spans are derived inside the same evolution window.
   - `build_zone_visit_timeline` / `_parse_visit_spans` / `_compute_touch_spans`
     (:3548 / :3427 / :3453) — to segment the extended window and add a `post_return_flag`.

---

## TASK 3 — Performance bottleneck audit

### research_analysis_time_after_cache = 16,572 s (~4.6 h) — dominant cost

This is the per-episode loop in `analyze_phase1b_episode_research.py:149-158`
(`for _, episode in selected_episodes.iterrows(): analyze_episode(...)`), 4,859 episodes
≈ 3.4 s/episode.

1. **Loops/functions that dominate:** `detect_preparation_return`
   (analyze_phase1b_episode_research.py:1548) and its helper `contiguous_row_groups` (:2092),
   called once per episode.

2. **Nested episodes × observation_rows?** Effectively yes. `detect_preparation_return` does
   `future_rows = rows.after_time(episode_end_dt)` → `ResearchRowIndex.after_time` (:323)
   returns `self.rows.iloc[position:].copy()` — it **copies the entire tail** of the
   295,822-row frame. For early episodes that is ~all rows, per episode. It then filters
   `future_rows[(close>=low)&(close<=high)].copy()` (a second full pass/copy) and runs
   `contiguous_row_groups` over the in-zone subset.

3. **Timestamps indexed efficiently?** Partially. `ResearchRowIndex` locates boundaries with
   `searchsorted` on a sorted datetime series (good). But `after_time` / `between` /
   `before_row_id` then `.copy()` the located slice, so the per-call cost is O(slice length),
   not O(log n). `after_time` copies the whole remaining tail.

4. **Repeated dataframe filters inside loops?** Yes — the in-zone boolean mask is recomputed
   per episode over a large slice, and `contiguous_row_groups` iterates that slice with
   `iterrows()` (per-row Python overhead) plus a `pd.DataFrame(current_rows)` build per group
   — the slowest pattern in the file.

5. **Can interval searches use prebuilt indexes / searchsorted?** Boundary location already
   does. The remaining wins are: (a) avoid the full-tail `.copy()` in `after_time` — return
   detection only needs the *first* re-entry group, so a bounded look-ahead or a view would
   suffice; (b) replace `contiguous_row_groups`' `iterrows` with vectorized gap detection
   (`numpy.diff` on `row_id` + `numpy.split`) — identical grouping, ~orders of magnitude
   faster.

### zone_mechanics_calculator stages

6. **Why csv_write_rdm_outputs = 514 s?** It serializes ~24 CSVs in one block
   (zone_mechanics_calculator.py:297-322). The cost is dominated by
   `zone_live_rdm_evolution.csv` = **1,809,010 rows × 61 cols ≈ 996 MB** via pandas
   `to_csv` (line 304). Note this same data is **written twice per run**: once as
   `zone_live_rdm_evolution.incremental.csv` (~950 MB, the streaming intermediate from the
   earlier memory fix) and again as the final `.csv` — ~1.9 GB of serialization for one
   dataset.

7. **Largest output file:** `zone_live_rdm_evolution.csv` (996 MB) — ~60× the next largest
   (`zone_mechanics_cycle3_results.csv`, 16.8 MB).

8. **Too many CSVs?** Yes — ~24 result CSVs + ~10 notes files every run. Most are <2 MB and
   harmless, but (a) the duplicate ~950 MB live-evolution write and (b) re-serializing the
   996 MB file from the read-back DataFrame are the real costs.

9. **Safe optimizations (no result change):**
   - Vectorize `contiguous_row_groups` (numpy diff/split) — identical groups, removes
     `iterrows`.
   - Bound the look-ahead in `detect_preparation_return` / `after_time` instead of copying
     the full tail (the first in-zone group is all that's consumed).
   - Avoid writing `zone_live_rdm_evolution` twice: the `.incremental.csv` already holds the
     data; rename it to final instead of re-serializing via `to_csv`.
   - Other 1.0–1.5 s per file is rdominated by the live-evolution file; the small CSVs need
     no change.
   - All of the above preserve byte-identical analytical results; they are I/O / iteration
     optimizations only.

---

## TASK 4 — B12.5 recommendation

**Required? PARTIALLY.** The current timeline already delivers most of what "B12.5 full visit
timeline" asks for (true per-visit rows, visit_index, per-visit structural state, omega,
penetration, deltas). A *new* engine is **not** required just to get visit-level granularity.

Two genuine gaps justify a B12.5 *extension* (not a rebuild):
1. **Post-return visits (N+1, N+2, …) are not captured** — the window stops at `return_row`.
   This is the real new capability and requires extending the evolution window (Task 2 #6).
2. **Active-Core-specific geometry** — current penetration is vs `real_zone_width`, not the
   Active Core bounds; the B12.5 column list wants `active_core_low/high` and
   Active-Core-relative penetration.

Missing columns relative to current 34-col timeline (would need adding):
`market_timestamp`, `active_core_low`, `active_core_high`, `price_at_visit`, `close`,
`derivative_class`, `time_since_previous_visit`, `post_return_flag`,
`cumulative_integral_seed`. (Current file already has equivalents for omega/health/rigidity/
fatigue/recovery/capacity/attacker_force/penetration/visit_index.)

Recommended shape if pursued: write `research/zone_visit_timeline_dynamic.csv` as a NEW file
(do not overwrite `zone_visit_timeline.csv`), produced by extending `live_row_window` past
the return horizon and re-segmenting, with `post_return_flag` and Active-Core columns added.
Validation metrics to emit: total_cases, total_dynamic_visit_rows, unique_case_ids,
cases_with_1_visit, cases_with_2plus_visits, avg_visits_per_case, max_visits_per_case.

---

## FINAL ANSWER

1. **Timeline granularity verdict:** TRUE VISIT-LEVEL (14,083 rows / 4,859 cases, visit_index
   1→9). The "4,859 rows" premise was a case-count/row-count mix-up.
2. **Evidence:** see Task 1 tables + CASE_07038 nine-row sample; 0/2,980 returning cases
   track past `return_row`.
3. **Code location:** `build_zone_visit_timeline` (zone_mechanics_calculator.py:3548), with
   `_parse_visit_spans` (:3427), `_compute_touch_spans` (:3453), `_classify_visit` (:3500);
   window bound by `live_row_window` (~:1855).
4. **Performance:** the 4.6 h research stage is `detect_preparation_return`'s full-tail
   `.copy()` + `iterrows`-based `contiguous_row_groups`, per episode. The 514 s write is the
   996 MB `zone_live_rdm_evolution.csv` (written twice).
5. **B12.5:** NOT required for visit-level granularity (already present); a focused EXTENSION
   is justified only to add post-return visits + Active-Core geometry.
6. **Next safe step:** AUDIT ONLY for now. If proceeding: (a) decide whether post-return
   tracking is actually wanted before any code; (b) the performance optimizations are safe and
   independent and could be done first; (c) B12.5 should be a new-file extension, never an
   overwrite of the existing timeline. Do NOT implement B13 until this is settled.

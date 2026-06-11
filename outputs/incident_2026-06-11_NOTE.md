# Incident Note — 2026-06-11 — B12 validation harness output contamination

## What happened

While building `tools/validate_live_b12.py` (the dry-run harness for B12 Live
Validation Instrumentation), the harness was modeled on
`tools/validate_live_rdm.py`'s `run_live_capture` monkeypatch/replay pattern.
That pattern *replaces* `core.live_rdm._persist_record` with a non-writing
capture function for the duration of the replay, then restores the original
afterward.

When adapting the pattern, the
`original_persist_record = lr._persist_record` /
`lr._persist_record = capture_persist_record` /
`lr._persist_record = original_persist_record` triple was mistakenly judged
to be a no-op self-reassignment and removed entirely. As a result, the
harness left the **real** `_persist_record` active during three replay runs
(one in an earlier turn, two more during a later "byte-identical proof"
check), which wrote real PENDING_FINALIZATION / FINALIZED_OUTCOME / evolution
records to:

- `outputs/live_rdm_results.csv`
- `outputs/live_rdm_state.csv`
- `outputs/live_rdm_evolution.csv`

`outputs/observation_rows.csv` (the harness's read-only input) was verified
unchanged across all runs (`git hash-object` identical before/after).

## Root cause

Harness bug only — not a defect in `core/live_return_detection.py`,
`core/live_rdm.py`, or `core/live_b12_validation.py` (the additive B12
production code). Fixed in `tools/validate_live_b12.py` by restoring the
save/replace/restore of `lr._persist_record` (mirroring
`tools/validate_live_rdm.py` exactly).

## Reference-count correction

The first "byte-identical" baseline (57 / 109 / 6073 lines) was itself
captured **after** the first contaminated run had already executed — it was
never a pristine baseline, just "pristine + run 1's contamination." This was
discovered and corrected during forensic analysis: `analysis_run_utc`
clustering across all three files showed a single, consistent, non-interleaved
cutoff at **`analysis_run_utc < 2026-06-11 09:54:00 UTC`** (genuine live rows)
vs `>= 09:54:00 UTC` (three harness-run contamination clusters). The true
pristine state was established forensically from this cutoff, not from the
57/109/6073 reference.

## Rows removed

| File | Total (contaminated) | Removed (`>= 09:54:00 UTC`) | Restored (pristine) |
|---|---|---|---|
| `outputs/live_rdm_results.csv` | 70 data rows (71 lines) | 56 | 14 data rows (15 lines incl. header) |
| `outputs/live_rdm_state.csv` | 135 data rows (136 lines) | 108 | 27 data rows (28 lines incl. header) |
| `outputs/live_rdm_evolution.csv` | 7590 data rows (7591 lines) | 6072 | 1518 data rows (1519 lines incl. header) |

Cross-file consistency verified after removal: all three files' restored
portions reference exactly the same 14 known case_ids
(`LIVE_PREP_ZONE_23/34/35/37/44/69/72/78/81/83/97/101/102/105`).
`live_rdm_state.csv` contains 14 `PENDING_FINALIZATION` + 13
`FINALIZED_OUTCOME` rows — `LIVE_PREP_ZONE_105` correctly has no
`FINALIZED_OUTCOME` row (its 4h post-return window extends ~4 minutes past
the end of `outputs/observation_rows.csv`, so it never reaches finalization
in this dataset — a pre-existing, independently-confirmed property, not
caused by this incident).

## Known limitation

This is a **row-exact reconstruction based on timestamp-cutoff forensics**,
not a provable byte-identical restoration to a pre-incident snapshot (no such
snapshot exists — `outputs/` is gitignored and no backup predates the
incident). The contaminated originals are preserved permanently in
`outputs/incident_2026-06-11_backup/` for any future re-examination.

## Permanent rule going forward

**Any tool that replays data through the live stack (anything that calls
`core.live_rdm`, `core.live_return_detection`,
`core.observation_logger`, or `core.live_lifecycle` write paths) must take a
pre-run snapshot/hash of every file in `outputs/` it could possibly touch,
and must verify those hashes are unchanged after the run.** Monkeypatch-based
harnesses must explicitly enumerate and restore every patched write function
— do not assume any `original_x = module.x` / `module.x = replacement` /
`module.x = original_x` triple is a no-op.

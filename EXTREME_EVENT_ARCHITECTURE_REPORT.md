# EXTREME EVENT DETECTION — ACTIVATION ARCHITECTURE REPORT

**Date:** 2026-06-09
**Type:** Architecture review only — no code, scoring, or dashboard changes
**Scope:** Dashboard V2 Extreme Event Layer (`core/statistics.py`)

---

## 1. CURRENT EXTREME EVENT LAYER DESIGN

The Extreme Event Layer is the **9th layer** in `DASHBOARD_V2_LAYERS`, alongside `distribution`, `multi_zscore`, `price_rarity`, `volatility`, `volume`, `velocity`, `delta`, `spread_execution`.

It is implemented as a **pure classifier over already-computed statistics** — `add_extreme_event_detection_features()` (`core/statistics.py:2314-2460`) does not compute any new rolling windows. It re-reads six zscore/flag values that the upstream layers (lines 2520-2594) already produced for that row:

| Dimension | Trigger | Source field |
|---|---|---|
| Price | `abs(price_zscore) >= 3.0` | price distribution (adaptive std) |
| Volume | `climactic_volume==True` OR `volume_zscore >= 2.5` | volume distribution |
| Delta | `abs(delta_zscore) >= 2.5` | cumulative delta distribution |
| Velocity | `velocity_shock==True` OR `abs(velocity_zscore) >= 2.5` | velocity distribution |
| Gaussian | `gaussian_extreme==True` (zone == GAUSSIAN_EXTREME) | Gaussian model |
| Spread | `abnormal_spread==True` OR `BAD_EXECUTION` | spread distribution |

It then aggregates `active_dimensions = count(active flags)` into a state:

```
active_dimensions == 0                          -> NO_EXTREME_EVENT
active_dimensions == 1                          -> SINGLE_FACTOR_EXTREME   (LOW)
active_dimensions == 2                          -> MULTI_FACTOR_EXTREME    (MEDIUM)
active_dimensions >= 3                          -> CRITICAL_EXTREME_EVENT  (HIGH)
distribution_shift==True AND dims >= 2          -> UNSTABLE_EXTREME_CONTEXT (EXTREME)
```

Important structural fact: **`extreme_event` is explicitly excluded from `peak_layer_count`** (only 7 of 9 layers count toward confluence). It cannot independently start an episode — it acts as a **severity modifier / escalation layer** on top of the 7 counted layers, and as the trigger condition for `UNSTABLE_STATISTICAL_CONTEXT` (which overrides the normal confluence-count state).

---

## 2. COMPUTATIONAL COST

**Current cost is effectively zero marginal cost.** All inputs (zscores, climactic/shock/abnormal flags, gaussian zone) are computed once per row by upstream layers regardless of whether the Extreme Event Layer runs. The Extreme Event Layer itself is six threshold comparisons + a count + a lookup table — O(1), no new memory, no new rolling buffers.

The only existing gate is the **`distribution_ready` warmup** (`len(price_distribution) >= 30`, line 2586): before warmup, all six flags are forced `False` and the layer reports `NO_EXTREME_EVENT`. This is a data-sufficiency gate, not an activation-policy gate — it exists so the engine doesn't fire on statistically meaningless early-window zscores.

**Conclusion:** Option A (continuous evaluation) and Option B (dormant-until-anomaly) have **identical compute cost** in the current design, because the expensive part (rolling distributions, zscores) runs unconditionally either way as the foundation for the other 8 layers. There is no "extra" computation to gate.

---

## 3. STATISTICAL VALIDITY

Continuous evaluation is the statistically correct mode for this layer, for three reasons:

1. **Zscore-based classifiers require a continuous baseline.** A zscore is only meaningful relative to a continuously-maintained rolling distribution. If the distribution stops updating while "dormant," the zscore on re-activation is computed against a stale window — this would silently corrupt the very thresholds (`>= 2.5`, `>= 3.0`) the layer relies on.

2. **`NO_EXTREME_EVENT` is itself information.** The episode/state machine (`UNSTABLE_STATISTICAL_CONTEXT` gate, `peak_max_severity` escalation) needs to know on every row whether extreme conditions are absent, not just when they're present. A "dormant" layer that produces no output for normal rows would break the confluence/severity logic that depends on a value existing every row.

3. **The 30-row warmup gate already serves the legitimate "should this be active" question.** Below 30 samples, zscores are not statistically meaningful — the engine correctly suppresses the layer. Above 30 samples, every additional row is equally valid input; there is no statistical basis for further suppression.

---

## 4. SIGNAL QUALITY & NOISE GENERATION RISK

The layer's noise profile is already controlled by **threshold severity, not activation frequency**:

- Single-dimension events (`SINGLE_FACTOR_EXTREME`, ~1 in ~80 rows at zscore>=2.5 for a normal distribution) are LOW severity and do not by themselves change `peak_state`.
- Multi-dimension confluence (`MULTI_FACTOR_EXTREME`, `CRITICAL_EXTREME_EVENT`) is rare by construction — it requires 2-3 independent zscore dimensions to cross threshold simultaneously, which for roughly-independent statistics has combinatorially low probability.
- `UNSTABLE_EXTREME_CONTEXT` additionally requires `distribution_shift==True`, a structural regime-change signal, not just a zscore spike.

A gated/dormant design (Option B) would not reduce this noise — it would instead introduce a **new noise source**: the trigger condition that wakes the engine up. Whatever heuristic decides "abnormal enough to activate" is itself a threshold subject to the same false-positive/negative tradeoffs, but now sitting *in front of* the zscore engine rather than *as* the zscore engine. This duplicates logic without improving precision.

---

## 5. RELATIONSHIP TO OTHER LAYERS

| Layer | Relationship to Extreme Event |
|---|---|
| **ZScore (multi_zscore)** | Direct input — price/volume/delta/velocity zscores ARE the extreme event triggers. Extreme Event is a thresholded view of multi_zscore, not an independent computation. |
| **Distribution Shift** | Used as the AND-condition for the highest severity tier (`UNSTABLE_EXTREME_CONTEXT`). Distribution shift answers "has the regime changed"; extreme event answers "is the current row an outlier within/across that regime." Together they distinguish a transient spike from a regime-changing spike. |
| **Tail Detection** | Not currently a separate layer — `gaussian_zone == GAUSSIAN_EXTREME` and `price_zscore >= 3` together serve this role today. If a dedicated tail-risk layer is added later, it should plug into the Extreme Event aggregator the same way (one more boolean dimension), not as a separate activation gate. |
| **Volatility Regime** | Independent context layer (not counted in extreme dimensions). Volatility regime tells you the *baseline* volatility state; Extreme Event tells you whether the *current row* is anomalous relative to that baseline. These are complementary, not redundant — extreme events can occur in both LOW_VOLATILITY and HIGH_VOLATILITY regimes (different meanings in each). |
| **Delta Extremes / Velocity Extremes** | These are two of the six input dimensions to Extreme Event — already fully integrated. |
| **Entropy (future)** | Should be added as a 7th input dimension to `add_extreme_event_detection_features()` exactly like the existing six (a boolean "entropy_extreme" flag derived from an entropy zscore/threshold), feeding the same `active_dimensions` counter. No separate activation pathway needed — it inherits the existing always-on, post-warmup evaluation for free. |

---

## 6. ACTIVATION QUESTIONS — ANSWERS

**Should Extreme Event Detection run permanently (post-warmup)?**
Yes. This is already the design, and it is correct. The layer is a zero-marginal-cost reclassification of statistics that must be computed continuously for the other 8 layers anyway.

**Should it activate only after anomaly triggers?**
No. There is no anomaly-detection problem to solve here that the zscore framework doesn't already solve. Gating on "anomaly" would require a pre-anomaly-detector to decide when to run the anomaly detector — circular, and adds a second threshold surface with its own false-negative risk (a missed activation trigger silently disables the entire layer for that period).

**What should the activation gates be?**
Keep exactly the one that exists: `distribution_ready` (rolling window >= 30 samples). This is a data-sufficiency gate, not a market-condition gate, and should remain the only gate. No additional gates are needed or recommended.

**What should the deactivation conditions be?**
None, by design. The layer should never "turn off" once warm. (If the underlying stream disconnects/resets, `distribution_ready` naturally goes back to `False` until 30 fresh rows accumulate — this is already handled as a side effect of the existing rolling-buffer mechanics, not a separate deactivation rule.)

**What is the institutional/research best practice?**
Continuous evaluation of statistical-outlier layers downstream of a continuously-maintained baseline distribution is standard practice in quantitative market surveillance and risk systems (e.g., real-time VaR breach monitoring, surveillance z-score alerting). The "alert" is the threshold crossing, not the act of computing the statistic — the statistic is always running. Gated/event-driven re-computation is reserved for *expensive, independent* computations (e.g., a full re-fit of a model), which is not the case here since Extreme Event reuses existing per-row statistics at O(1) cost.

---

## RECOMMENDED ARCHITECTURE

**Keep the current design: continuous, always-on (post-warmup) evaluation. No change required.**

### Activation Flow

```
Row arrives
   |
   v
Update rolling distributions (price/volume/delta/velocity/spread/gaussian)
   |
   v
distribution_ready? (len >= 30)
   |--- NO  --> all extreme flags = False, state = NO_EXTREME_EVENT
   |--- YES --> compute 6 zscore/flag dimensions (already computed for other layers)
                  |
                  v
                count active_dimensions
                  |
                  v
                classify state (NO_EXTREME_EVENT / SINGLE / MULTI / CRITICAL / UNSTABLE)
                  |
                  v
                feed into peak_max_severity escalation + UNSTABLE_STATISTICAL_CONTEXT gate
                (peak_layer_count unaffected — extreme_event stays uncounted)
```

### Trigger Hierarchy (severity escalation, low to high)

```
NO_EXTREME_EVENT          (0 dimensions active)
  -> SINGLE_FACTOR_EXTREME    (1 dimension,  severity LOW)
    -> MULTI_FACTOR_EXTREME   (2 dimensions, severity MEDIUM)
      -> CRITICAL_EXTREME_EVENT (>=3 dimensions, severity HIGH)
        -> UNSTABLE_EXTREME_CONTEXT (>=2 dimensions AND distribution_shift==True, severity EXTREME)
                                     -> overrides dashboard state to UNSTABLE_STATISTICAL_CONTEXT
```

### Computational Implications

- Zero additional cost vs. current implementation — confirmed no separate rolling windows exist for this layer.
- Adding Entropy as a 7th dimension later: +1 threshold compare, +1 boolean in the active_dimensions count. Negligible.
- No caching, no conditional skip logic needed — would add branching complexity for no measurable savings.

### Statistical Implications

- Preserves zscore baseline continuity — no stale-distribution risk on "reactivation" (because there is no deactivation).
- `NO_EXTREME_EVENT` remains a valid, continuously-available state for the confluence/severity state machine.
- Severity tiering (1/2/3+ dimensions, plus distribution-shift AND-gate) already provides the noise control that an activation gate would otherwise attempt to provide — redundant gating would not improve signal quality.

### Final Recommendation

**Option A (continuous evaluation) — confirmed as current and correct design. No architectural change recommended.** The only legitimate gate (`distribution_ready`, 30-row warmup) is already in place and should be preserved unchanged. Future additions (Entropy, Tail Detection) should integrate as additional input dimensions to the existing always-on aggregator, not as separate activation-gated subsystems.

---

**No code changes made. No scoring changes made. No Dashboard changes made. No execution changes made.**

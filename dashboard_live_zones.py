"""
dashboard_live_zones.py — Live Zone Monitor (last N hours)
Standalone, read-only Streamlit app.  Never touches dashboard_app.py.

Launch (avoids port conflict with existing dashboard on 8501):
    streamlit run dashboard_live_zones.py --server.port 8502
"""
from __future__ import annotations

import inspect
import math
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from research.zone_mechanics_calculator import (  # noqa: F401
    _classify_dynamic_state,
    STABLE_SLOPE_EPS,
)

# ─────────────────────────────────────────────────────────────────────────────
# Paths  (read-only — no writes anywhere)
# ─────────────────────────────────────────────────────────────────────────────
_ROOT     = Path(__file__).parent
_OUT      = _ROOT / "outputs"
_RES      = _ROOT / "research"

_RESULTS_PATH = _OUT  / "live_rdm_results.csv"
_EVOL_PATH    = _OUT  / "live_rdm_evolution.csv"
_DYN_PATH     = _RES  / "live_zone_visit_timeline_dynamic.csv"

ALGERIA_TZ = ZoneInfo("Africa/Algiers")

# ─────────────────────────────────────────────────────────────────────────────
# Dynamic state → (card-bg, badge-bg, badge-text)
# ─────────────────────────────────────────────────────────────────────────────
_STYLE: dict[str, tuple[str, str, str]] = {
    "STRONG_HOLD":       ("#0d2018", "#15803d", "#dcfce7"),
    "ATTACKER_DOMINANT": ("#1c0a0a", "#b91c1c", "#fee2e2"),
    "PEAK_WARNING":      ("#1c1208", "#c2410c", "#ffedd5"),
    "CRITICAL":          ("#130505", "#7f1d1d", "#fee2e2"),
    "RECOVERING":        ("#1c0a0a", "#dc2626", "#fee2e2"),
    "DEGRADING":         ("#1a1206", "#b45309", "#fef3c7"),
    "STABLE":            ("#0a1525", "#1d4ed8", "#dbeafe"),
    "PROBABLE_HOLD":     ("#1a1506", "#a16207", "#fefce8"),
    "UNCERTAIN":         ("#111827", "#4b5563", "#f3f4f6"),
    "NO_DATA":           ("#0f1117", "#1f2937", "#9ca3af"),
}
_DEFAULT_STYLE = ("#0f1117", "#1f2937", "#9ca3af")

_STATE_ORDER = [
    "STRONG_HOLD", "ATTACKER_DOMINANT", "PEAK_WARNING", "CRITICAL",
    "RECOVERING", "DEGRADING", "STABLE", "PROBABLE_HOLD", "UNCERTAIN", "NO_DATA",
]

# ─────────────────────────────────────────────────────────────────────────────
# CSS  (dark theme, injected once)
# ─────────────────────────────────────────────────────────────────────────────
_CSS = """
<style>
.stApp { background-color: #0f1117 !important; color: #e5e7eb !important; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Card ── */
.zcard {
  border: 1px solid #1f2937;
  border-radius: 12px;
  padding: 16px 18px;
  margin-bottom: 14px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.ztitle { font-size: 1.0rem; font-weight: 700; color: #f9fafb; margin-bottom: 2px; }
.zid    { font-size: 0.68rem; color: #6b7280; font-family: monospace; margin-bottom: 8px; }

/* ── Badge ── */
.badge {
  display: inline-block;
  padding: 3px 11px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.05em;
}

/* ── Labels & values ── */
.lbl  { font-size: 0.68rem; color: #6b7280; text-transform: uppercase;
        letter-spacing: 0.06em; margin-bottom: 1px; }
.mval { font-size: 0.92rem; font-weight: 600; color: #e5e7eb; margin-bottom: 3px; }

/* ── Mini progress bar ── */
.bar-bg { background: #374151; border-radius: 3px; height: 5px;
          margin-bottom: 8px; overflow: hidden; }
.bar-fg { height: 5px; border-radius: 3px; }

/* ── SDR two-tone track ── */
.sdr-track {
  position: relative; height: 7px; border-radius: 4px;
  background: linear-gradient(to right, #15803d 50%, #b91c1c 50%);
  margin: 5px 0 4px 0;
}
.sdr-pin {
  position: absolute; top: -3px; width: 3px; height: 13px;
  background: #ffffff; border-radius: 2px; transform: translateX(-50%);
}

/* ── Geometry panel ── */
.geo {
  background: #111827; border: 1px solid #1f2937;
  border-radius: 8px; padding: 10px 14px; margin-top: 12px;
}
.geo-hdr {
  font-size: 0.68rem; font-weight: 700; color: #6b7280;
  text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;
}
.geo-col-lbl {
  display: grid; grid-template-columns: 110px 1fr 1fr 1fr;
  gap: 6px; font-size: 0.63rem; color: #4b5563;
  text-transform: uppercase; letter-spacing: 0.05em;
  border-bottom: 1px solid #1f2937; padding-bottom: 4px; margin-bottom: 5px;
}
.geo-row {
  display: grid; grid-template-columns: 110px 1fr 1fr 1fr;
  gap: 6px; margin-bottom: 4px; font-size: 0.77rem; align-items: baseline;
}
.geo-row .comp { color: #9ca3af; font-weight: 600; }
.geo-row .num  { font-family: "Courier New", "Consolas", monospace; color: #d1d5db; }

/* ── Summary strip ── */
.summary {
  background: #111827; border: 1px solid #1f2937; border-radius: 8px;
  padding: 10px 16px; margin-bottom: 18px;
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
}
.chip {
  font-size: 0.75rem; font-weight: 700;
  padding: 2px 10px; border-radius: 999px;
}

/* ── Empty state ── */
.empty-msg {
  text-align: center; color: #6b7280; padding: 56px 0; font-size: 0.95rem;
}

/* ── WHY / reasoning block ── */
.why-block {
  font-size: 0.76rem; font-style: italic; color: #d1d5db;
  border-left: 3px solid #374151; padding-left: 10px;
  margin: 8px 0 10px 0; line-height: 1.55;
}

/* ── Geo primary row (Density Band — decision zone) ── */
.geo-row-primary {
  display: grid; grid-template-columns: 110px 1fr 1fr 1fr;
  gap: 6px; margin-bottom: 5px; font-size: 0.77rem; align-items: baseline;
  background: rgba(30, 58, 138, 0.30); border-radius: 4px;
  padding: 4px 5px; border-left: 2px solid #3b82f6;
}
.geo-row-primary .comp { color: #93c5fd; font-weight: 700; }
.geo-row-primary .num  { font-family: "Courier New", "Consolas", monospace; color: #e5e7eb; }

/* ── Geo secondary row (Active Core — context) ── */
.geo-row-secondary {
  display: grid; grid-template-columns: 110px 1fr 1fr 1fr;
  gap: 6px; margin-bottom: 4px; font-size: 0.72rem; align-items: baseline;
}
.geo-row-secondary .comp { color: #4b5563; font-weight: 600; }
.geo-row-secondary .num  { font-family: "Courier New", "Consolas", monospace; color: #6b7280; }
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Data helpers
# ─────────────────────────────────────────────────────────────────────────────

def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, low_memory=False)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=10)
def _load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return _read(_RESULTS_PATH), _read(_EVOL_PATH), _read(_DYN_PATH)


def _parse_utc(s: object) -> pd.Timestamp | None:
    """Parse any timestamp string to a UTC-aware Timestamp. Returns None on failure."""
    if s is None:
        return None
    try:
        if isinstance(s, float) and math.isnan(s):
            return None
    except Exception:
        pass
    try:
        dt = pd.to_datetime(s)
        if dt is pd.NaT:
            return None
        if dt.tzinfo is None:
            dt = dt.tz_localize("UTC")
        else:
            dt = dt.tz_convert("UTC")
        return dt
    except Exception:
        return None


def _alg(s: object) -> str:
    """Format any UTC timestamp string as Algeria local time."""
    dt = _parse_utc(s)
    if dt is None:
        return "—"
    return dt.astimezone(ALGERIA_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _ago(s: object, now: pd.Timestamp) -> str:
    """Human-readable elapsed time (e.g. '3h 12m ago')."""
    dt = _parse_utc(s)
    if dt is None:
        return ""
    secs = int((now - dt).total_seconds())
    if secs < 0:
        return "just now"
    h, rem = divmod(secs, 3600)
    m = rem // 60
    if h >= 24:
        d, rh = divmod(h, 24)
        return f"{d}d {rh}h ago"
    if h:
        return f"{h}h {m}m ago"
    return f"{m}m ago"


def _p(v: object) -> str:
    """Format a price with 2 decimal places and thousands separator."""
    try:
        return f"{float(v):,.2f}"
    except Exception:
        return "—"


def _f(v: object, d: int = 1) -> str:
    """Format a float to d decimal places."""
    try:
        return f"{float(v):.{d}f}"
    except Exception:
        return "—"


def _bar(pct: float, color: str) -> str:
    w = max(0.0, min(100.0, pct))
    return (
        f'<div class="bar-bg">'
        f'<div class="bar-fg" style="width:{w:.0f}%;background:{color};"></div>'
        f'</div>'
    )


def _sdr_gauge(sdr_val: object) -> str:
    try:
        sdr = float(sdr_val)
        if math.isnan(sdr):
            raise ValueError
        pct = max(0.0, min(100.0, sdr / 2.0 * 100.0))
        c   = "#22c55e" if sdr < 1.0 else "#f87171"
        dom = "zone dominant" if sdr < 1.0 else "attacker dominant"
        return (
            f'<div class="lbl">SDR</div>'
            f'<div class="mval">'
            f'<span style="color:{c};">{sdr:.3f}</span>'
            f'<span style="font-size:0.72rem;color:#6b7280;font-weight:400;"> · {dom}</span>'
            f'</div>'
            f'<div class="sdr-track">'
            f'<div class="sdr-pin" style="left:{pct:.1f}%;"></div>'
            f'</div>'
        )
    except Exception:
        return (
            '<div class="lbl">SDR</div>'
            '<div class="mval" style="color:#6b7280;">— (no post-return visits yet)</div>'
        )


# ─────────────────────────────────────────────────────────────────────────────
# Dynamic state reasoning
# ─────────────────────────────────────────────────────────────────────────────

# REPLAY-calibrated thresholds (same values as add_dynamic_layers_to_timeline_live).
# Hardcoded here to keep LIVE/REPLAY labels directly comparable.
_THRESHOLDS: dict = {
    "slope_pos":     3.894,
    "slope_neg":    -1.248,
    "integral_high": 410.68,
    "integral_low":   76.85,
    "sdr_high":        1.079,
}


def _build_reasoning(sdr_row: dict) -> str:
    """One-sentence explanation for the dynamic_state on this card.

    Mirrors the exact rule priority of _classify_dynamic_state() (imported above
    from research/zone_mechanics_calculator.py) using the same REPLAY-calibrated
    _THRESHOLDS and the imported STABLE_SLOPE_EPS constant.
    """
    if not sdr_row:
        return "No dynamic data — zone not yet tracked in visit timeline."
    ds = str(sdr_row.get("dynamic_state") or "NO_DATA")
    if ds == "NO_DATA":
        return (
            "Zone returned to the Density Band but has not re-engaged the Active Core "
            "— no post-return visits recorded yet."
        )

    def _g(k: str):
        try:
            v = float(sdr_row.get(k))  # type: ignore[arg-type]
            return None if math.isnan(v) else v
        except Exception:
            return None

    t    = _THRESHOLDS
    sdr  = _g("SDR")
    fd   = _g("first_derivative")
    sd   = _g("second_derivative")
    smed = _g("slope_medium")
    zint = _g("zone_integral")

    # Rules mirror _classify_dynamic_state() exactly (rule 1 → rule 9).
    if sdr is not None and sdr >= t["sdr_high"]:
        return (
            f"SDR={sdr:.3f} ≥ {t['sdr_high']} — attacker force exceeds zone strength; "
            "structural dominance shifted to attacker."
        )
    if zint is not None and sdr is not None and zint >= t["integral_high"] and sdr < 1.0:
        return (
            f"zone_integral={zint:.1f} (≥{t['integral_high']}) with SDR={sdr:.3f} (<1.0) "
            "— cumulative health confirmed strong, zone holds the attacker."
        )
    if sd is not None and fd is not None and sd < 0 and fd > 0:
        return (
            f"Health rising (Δ={fd:+.3f}) but decelerating (Δ²={sd:+.3f}) "
            "— peak forming, momentum reversal expected."
        )
    if zint is not None and smed is not None and zint < t["integral_low"] and smed < t["slope_neg"]:
        return (
            f"zone_integral={zint:.1f} (<{t['integral_low']}) and slope_medium={smed:+.3f} "
            f"(<{t['slope_neg']}) — severe structural degradation."
        )
    if sd is not None and fd is not None and sd > 0 and fd < 0:
        return (
            f"Health falling (Δ={fd:+.3f}) but decelerating (Δ²={sd:+.3f}) "
            "— attacker losing momentum; structural trough in progress."
        )
    if smed is not None and smed < t["slope_neg"]:
        return (
            f"slope_medium={smed:+.3f} (<{t['slope_neg']}) — persistent medium-term "
            "deterioration in zone structural integrity."
        )
    if smed is not None and abs(smed) < STABLE_SLOPE_EPS:
        return (
            f"slope_medium={smed:+.3f}, |slope| < {STABLE_SLOPE_EPS} — zone in "
            "equilibrium, no clear structural trend detected."
        )
    if sdr is not None and sdr < 1.0:
        return (
            f"SDR={sdr:.3f} (<1.0, zone dominant) with no strong structural signal "
            "— marginal hold confidence only."
        )
    if sdr is not None and sdr >= 1.0:
        return (
            f"SDR={sdr:.3f} (≥1.0, attacker dominant) — tiebreaker applied, "
            "no strong structural confirmation."
        )
    return "Insufficient data to determine structural direction."


# ─────────────────────────────────────────────────────────────────────────────
# Card HTML builder
# ─────────────────────────────────────────────────────────────────────────────

def _card(zone: pd.Series, sdr: dict, now: pd.Timestamp) -> str:
    cid = str(zone.get("case_id", "—"))
    zid = str(zone.get("zone_id",  "—"))

    ds              = str(sdr.get("dynamic_state") or "NO_DATA")
    bg, bbg, btx    = _STYLE.get(ds, _DEFAULT_STYLE)

    # Timestamps
    birth_s   = zone.get("formation_start_time")
    return_s  = zone.get("return_timestamp")
    birth_alg  = _alg(birth_s)
    return_alg = _alg(return_s)
    birth_ago  = _ago(birth_s,  now)
    return_ago = _ago(return_s, now)

    # Mechanical values from live_rdm_results
    rig   = zone.get("rigidity_live")
    fat   = zone.get("fatigue_live")
    hlt   = zone.get("health_live")
    rdm_h = zone.get("rdm_health_score")
    rdm_s = str(zone.get("rdm_live_status") or "—")
    rdm_r = str(zone.get("rdm_risk_level")  or "—")

    def _fval(v: object) -> float:
        try:
            x = float(v)
            return 0.0 if math.isnan(x) else x
        except Exception:
            return 0.0

    rig_f = _fval(rig)
    fat_f = _fval(fat)
    hlt_f = _fval(hlt)

    s_color = {"LIVE_SAFE": "#22c55e", "LIVE_WARNING": "#f97316",
               "LIVE_CRITICAL": "#ef4444"}.get(rdm_s, "#9ca3af")
    r_color = {"LOW": "#22c55e", "MEDIUM": "#f97316",
               "HIGH": "#ef4444"}.get(rdm_r, "#9ca3af")

    # Geometry — Density Band (primary decision zone) / Active Core (context only).
    # Preparation Zone is shown in the expander, not here.
    core_birth = _alg(zone.get("core_temporal_window_start"))
    core_hi    = _p(zone.get("interaction_core_upper_edge"))
    core_lo    = _p(zone.get("interaction_core_lower_edge"))

    dens_birth = _alg(zone.get("core_temporal_window_start"))
    dens_hi    = _p(zone.get("interaction_density_upper_band"))
    dens_lo    = _p(zone.get("interaction_density_lower_band"))

    why = _build_reasoning(sdr)

    return f"""
<div class="zcard" style="background:{bg};">

  <div class="ztitle">{cid}</div>
  <div class="zid">{zid}</div>
  <span class="badge" style="background:{bbg};color:{btx};">{ds}</span>

  <div class="why-block">{why}</div>

  <div style="margin:10px 0 12px 0;font-size:0.80rem;line-height:1.7;">
    <span class="lbl">Zone birth</span>&nbsp;
    <span style="color:#d1d5db;">{birth_alg}</span>
    <span style="color:#6b7280;font-size:0.70rem;"> · {birth_ago}</span><br/>
    <span class="lbl">Last return</span>&nbsp;
    <span style="color:#d1d5db;">{return_alg}</span>
    <span style="color:#6b7280;font-size:0.70rem;"> · {return_ago}</span>
  </div>

  {_sdr_gauge(sdr.get("SDR"))}

  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:10px;">
    <div>
      <div class="lbl">Rigidity</div>
      <div class="mval">{_f(rig)}</div>
      {_bar(rig_f, "#3b82f6")}
    </div>
    <div>
      <div class="lbl">Fatigue</div>
      <div class="mval">{_f(fat)}</div>
      {_bar(fat_f, "#f97316")}
    </div>
    <div>
      <div class="lbl">Health</div>
      <div class="mval">{_f(hlt)}</div>
      {_bar(hlt_f, "#22c55e")}
    </div>
  </div>

  <div style="font-size:0.74rem;margin-bottom:12px;color:#9ca3af;">
    Status:&nbsp;<span style="color:{s_color};font-weight:600;">{rdm_s}</span>
    &nbsp;·&nbsp;Risk:&nbsp;<span style="color:{r_color};font-weight:600;">{rdm_r}</span>
    &nbsp;·&nbsp;RDM&nbsp;score:&nbsp;<span style="color:#d1d5db;font-weight:600;">{_f(rdm_h)}</span>
  </div>

  <div class="geo">
    <div class="geo-hdr">Decision Zone Geometry · Algeria time (UTC+1)</div>
    <div class="geo-col-lbl">
      <span>Component</span>
      <span>Birth (Algeria)</span>
      <span>Upper bound</span>
      <span>Lower bound</span>
    </div>
    <div class="geo-row-primary">
      <span class="comp">Density Band</span>
      <span class="num">
        {dens_birth}
        <span style="color:#4b5563;font-size:0.60rem;display:block;">zone birth</span>
      </span>
      <span class="num">{dens_hi}</span>
      <span class="num">{dens_lo}</span>
    </div>
    <div class="geo-row-secondary">
      <span class="comp">Active Core <span style="font-size:0.60rem;">(Context)</span></span>
      <span class="num">{core_birth}</span>
      <span class="num">{core_hi}</span>
      <span class="num">{core_lo}</span>
    </div>
  </div>

</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# Expander: More Information
# ─────────────────────────────────────────────────────────────────────────────

def _render_expander(
    zone: pd.Series,
    sdr_row: dict,
    dyn_rows: pd.DataFrame,
) -> None:
    """Render the collapsible 'More Information' section beneath each zone card."""
    with st.expander("More Information ▾"):

        # (A) Preparation Zone bounds
        st.markdown("**Formation (Preparation Zone)**")
        st.markdown(
            f"Birth: `{_alg(zone.get('formation_start_time'))}` &nbsp;·&nbsp; "
            f"Upper: `{_p(zone.get('preparation_high_price'))}` &nbsp;·&nbsp; "
            f"Lower: `{_p(zone.get('preparation_low_price'))}`"
        )

        st.markdown("---")

        # (B) + (C) Full post-return visit history with outcome tracking
        actual_visits = pd.DataFrame()
        if not dyn_rows.empty:
            if "post_return_visit_count" in dyn_rows.columns:
                mask = pd.to_numeric(
                    dyn_rows["post_return_visit_count"], errors="coerce"
                ).fillna(0) > 0
                actual_visits = dyn_rows[mask].copy()
            else:
                actual_visits = dyn_rows.copy()

        if actual_visits.empty:
            st.caption("No post-return visit history yet for this zone.")
        else:
            st.markdown("**Post-Return Visit History**")

            display_cols = [
                "visit_index", "timestamp_start", "timestamp_end",
                "visit_result", "dynamic_state", "SDR",
                "zone_integral", "first_derivative", "second_derivative", "slope_medium",
            ]
            avail = [c for c in display_cols if c in actual_visits.columns]
            vdf = actual_visits[avail].copy()

            if "visit_index" in vdf.columns:
                vdf = vdf.sort_values("visit_index").reset_index(drop=True)

            if "timestamp_start" in vdf.columns:
                vdf["timestamp_start"] = vdf["timestamp_start"].apply(_alg)
            if "timestamp_end" in vdf.columns:
                vdf["timestamp_end"] = vdf["timestamp_end"].apply(_alg)

            # (C) what_happened_next — next visit's visit_result
            if "visit_result" in vdf.columns:
                next_results = vdf["visit_result"].shift(-1).tolist()
                if next_results:
                    next_results[-1] = "PENDING — most recent visit"
                vdf["what_happened_next"] = next_results

            st.dataframe(vdf, use_container_width=True, hide_index=True)

            # (D) Summary line
            n_visits = len(actual_visits)
            if "visit_result" in actual_visits.columns and n_visits > 1:
                if "visit_index" in actual_visits.columns:
                    resolved_ser = actual_visits.sort_values("visit_index").iloc[:-1]["visit_result"]
                else:
                    resolved_ser = actual_visits.iloc[:-1]["visit_result"]
                continued  = int(resolved_ser.isin(["GROWTH", "RECLAIM", "STABLE"]).sum())
                broke_down = int(resolved_ser.isin(["BREAKDOWN"]).sum())
                st.caption(
                    f"This zone has returned **{n_visits}** time(s).  "
                    f"Of **{n_visits - 1}** resolved visit(s): "
                    f"**{continued}** continued · **{broke_down}** broke down."
                )
            else:
                st.caption(f"This zone has returned **{n_visits}** time(s).")


# ─────────────────────────────────────────────────────────────────────────────
# Main render (called inside the auto-refresh fragment)
# ─────────────────────────────────────────────────────────────────────────────

def _render() -> None:
    window: str = str(st.session_state.get("date_window_ctrl", "Today"))

    results, evo, dynamic = _load()

    now     = pd.Timestamp.now(tz="UTC")
    now_alg = now.astimezone(ALGERIA_TZ)

    # Compute Algeria-midnight cutoffs for calendar-day filtering.
    today_midnight_alg = now_alg.replace(hour=0, minute=0, second=0, microsecond=0)
    today_midnight_utc = today_midnight_alg.tz_convert("UTC")
    if window == "Yesterday":
        cutoff      = today_midnight_utc - pd.Timedelta(days=1)
        cutoff_high = today_midnight_utc
    elif window == "Last 3 days":
        cutoff      = today_midnight_utc - pd.Timedelta(days=2)
        cutoff_high = None
    else:  # "Today" (default)
        cutoff      = today_midnight_utc
        cutoff_high = None

    # ── Page header ───────────────────────────────────────────────────────
    st.markdown(
        f'<h1 style="color:#f9fafb;font-size:1.7rem;margin-bottom:2px;">'
        f'⚡ Live Zones — {window}</h1>'
        f'<div style="font-size:0.82rem;color:#6b7280;font-family:monospace;margin-bottom:16px;">'
        f'Algeria time &nbsp;·&nbsp; {now_alg.strftime("%Y-%m-%d %H:%M:%S")} (UTC+1)'
        f' &nbsp;·&nbsp; auto-refresh every 15s</div>',
        unsafe_allow_html=True,
    )

    if results.empty:
        st.warning(
            f"No data at `{_RESULTS_PATH}`. "
            "Run the live RDM pipeline first, then reload."
        )
        return

    # ── Dedup live_rdm_results (same logic as run_zone_visit_timeline_dynamic_live) ──
    if "analysis_run_utc" in results.columns:
        results = (
            results.sort_values("analysis_run_utc")
            .drop_duplicates(subset=["case_id"], keep="last")
            .reset_index(drop=True)
        )

    # ── Latest-activity timestamp per zone (from evolution file) ──────────
    latest: pd.Series
    if not evo.empty and "timestamp" in evo.columns and "case_id" in evo.columns:
        e = evo[["case_id", "timestamp"]].copy()
        e["_ts"] = pd.to_datetime(e["timestamp"], unit="ms", utc=True, errors="coerce")
        latest = e.groupby("case_id")["_ts"].max()
    else:
        # Fallback: use return_timestamp from results
        pairs = {
            str(row["case_id"]): _parse_utc(row.get("return_timestamp"))
            for _, row in results.iterrows()
            if _parse_utc(row.get("return_timestamp")) is not None
        }
        latest = pd.Series(pairs)

    # ── Apply calendar-day window filter ──────────────────────────────────
    if not latest.empty:
        mask = latest >= cutoff
        if cutoff_high is not None:
            mask = mask & (latest < cutoff_high)
        active_ids = set(latest[mask].index)
        filtered   = results[results["case_id"].isin(active_ids)].reset_index(drop=True)
    else:
        filtered = results.copy()

    # ── SDR / dynamic_state per zone (last visit from dynamic file) ────────
    sdr_map: dict[str, dict] = {}
    if not dynamic.empty and "case_id" in dynamic.columns:
        sort_col = "visit_index" if "visit_index" in dynamic.columns else None
        dyn_work = dynamic.sort_values(sort_col) if sort_col else dynamic
        last_visits = dyn_work.groupby("case_id", as_index=False).last()
        for _, row in last_visits.iterrows():
            sdr_map[str(row["case_id"])] = row.to_dict()

    # ── Summary strip ─────────────────────────────────────────────────────
    state_counts: dict[str, int] = {}
    for _, z in filtered.iterrows():
        ds = str(sdr_map.get(str(z["case_id"]), {}).get("dynamic_state") or "NO_DATA")
        state_counts[ds] = state_counts.get(ds, 0) + 1

    total = len(filtered)
    chips = (
        f'<span style="color:#9ca3af;font-weight:600;font-size:0.83rem;">'
        f'{total} zone{"s" if total != 1 else ""}</span>'
    )
    for s in _STATE_ORDER:
        if s in state_counts:
            _, sbg, stx = _STYLE.get(s, _DEFAULT_STYLE)
            chips += (
                f'<span class="chip" style="background:{sbg};color:{stx};">'
                f'{state_counts[s]} {s}</span>'
            )

    st.markdown(f'<div class="summary">{chips}</div>', unsafe_allow_html=True)

    # ── Empty state ───────────────────────────────────────────────────────
    if filtered.empty:
        st.markdown(
            f'<div class="empty-msg">'
            f'No zones with activity for: {window}.<br/>'
            f'Select a wider window in the sidebar.'
            f'</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Sort by most recent activity ──────────────────────────────────────
    if not latest.empty:
        filtered = filtered.copy()
        filtered["_sort"] = filtered["case_id"].map(latest)
        filtered = (
            filtered.sort_values("_sort", ascending=False)
            .drop(columns=["_sort"])
            .reset_index(drop=True)
        )

    # ── Zone cards — 3 per row ─────────────────────────────────────────────
    n_cols = 3
    for row_i in range(math.ceil(len(filtered) / n_cols)):
        cols = st.columns(n_cols)
        for col_i, col in enumerate(cols):
            idx = row_i * n_cols + col_i
            if idx >= len(filtered):
                break
            z   = filtered.iloc[idx]
            cid = str(z.get("case_id", ""))
            sdr = sdr_map.get(cid, {})
            z_dyn = (
                dynamic[dynamic["case_id"] == cid].copy()
                if not dynamic.empty and "case_id" in dynamic.columns
                else pd.DataFrame()
            )
            with col:
                st.markdown(_card(z, sdr, now), unsafe_allow_html=True)
                _render_expander(z, sdr, z_dyn)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Live Zones",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(_CSS, unsafe_allow_html=True)

    # ── Sidebar ────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚡ Live Zone Monitor")
        st.selectbox(
            "Show zones from",
            options=["Today", "Yesterday", "Last 3 days"],
            index=0,
            key="date_window_ctrl",
            help="'Today' = since 00:00 Algeria time. 'Last 3 days' for catch-up when stream has gaps.",
        )
        if st.button("↻ Refresh Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.caption(
            "Auto-refreshes every 15 seconds via Streamlit fragment.  \n"
            "Filter by Algeria calendar day (UTC+1).  \n"
            "Use 'Last 3 days' if the live stream has gaps."
        )
        st.markdown("---")
        st.caption("Read-only · No data files are ever modified.")

    # ── Auto-refresh fragment (Streamlit ≥ 1.33, confirmed 1.57 here) ─────
    # run_every=15 re-runs _content() every 15s independently of the sidebar.
    # Sidebar changes still trigger a full rerun that resets the timer.
    _has_run_every = "run_every" in inspect.signature(st.fragment).parameters

    if _has_run_every:
        @st.fragment(run_every=15)
        def _content() -> None:
            _render()

        _content()
    else:
        # Fallback for older Streamlit builds (should not occur on 1.57)
        _render()
        st.info("Auto-refresh not available on this Streamlit version. Use ↻ Refresh Now.")


if __name__ == "__main__":
    main()

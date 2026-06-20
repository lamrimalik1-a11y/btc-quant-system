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


@st.cache_data(ttl=30)
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

    # Geometry
    prep_birth = birth_alg
    prep_hi    = _p(zone.get("preparation_high_price"))
    prep_lo    = _p(zone.get("preparation_low_price"))

    core_birth = _alg(zone.get("core_temporal_window_start"))
    core_hi    = _p(zone.get("interaction_core_upper_edge"))
    core_lo    = _p(zone.get("interaction_core_lower_edge"))

    dens_birth = _alg(zone.get("core_temporal_window_start"))
    dens_hi    = _p(zone.get("interaction_density_upper_band"))
    dens_lo    = _p(zone.get("interaction_density_lower_band"))

    return f"""
<div class="zcard" style="background:{bg};">

  <div class="ztitle">{cid}</div>
  <div class="zid">{zid}</div>
  <span class="badge" style="background:{bbg};color:{btx};">{ds}</span>

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
    <div class="geo-hdr">Zone Geometry · Algeria time (UTC+1)</div>
    <div class="geo-col-lbl">
      <span>Component</span>
      <span>Birth (Algeria)</span>
      <span>Upper bound</span>
      <span>Lower bound</span>
    </div>
    <div class="geo-row">
      <span class="comp">Preparation</span>
      <span class="num">{prep_birth}</span>
      <span class="num">{prep_hi}</span>
      <span class="num">{prep_lo}</span>
    </div>
    <div class="geo-row">
      <span class="comp">Active Core</span>
      <span class="num">{core_birth}</span>
      <span class="num">{core_hi}</span>
      <span class="num">{core_lo}</span>
    </div>
    <div class="geo-row">
      <span class="comp">Density Band</span>
      <span class="num">
        {dens_birth}
        <span style="color:#4b5563;font-size:0.60rem;display:block;">zone birth</span>
      </span>
      <span class="num">{dens_hi}</span>
      <span class="num">{dens_lo}</span>
    </div>
  </div>

</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# Main render (called inside the auto-refresh fragment)
# ─────────────────────────────────────────────────────────────────────────────

def _render() -> None:
    n_hours: int = int(st.session_state.get("n_hours_ctrl", 24))

    results, evo, dynamic = _load()

    now     = pd.Timestamp.now(tz="UTC")
    now_alg = now.astimezone(ALGERIA_TZ)
    cutoff  = now - pd.Timedelta(hours=n_hours)

    # ── Page header ───────────────────────────────────────────────────────
    st.markdown(
        f'<h1 style="color:#f9fafb;font-size:1.7rem;margin-bottom:2px;">'
        f'⚡ Live Zones — Last {n_hours}h</h1>'
        f'<div style="font-size:0.82rem;color:#6b7280;font-family:monospace;margin-bottom:16px;">'
        f'Algeria time &nbsp;·&nbsp; {now_alg.strftime("%Y-%m-%d %H:%M:%S")} (UTC+1)'
        f' &nbsp;·&nbsp; auto-refresh every 60s</div>',
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

    # ── Apply N-hour window filter ─────────────────────────────────────────
    if not latest.empty:
        active_ids = set(latest[latest >= cutoff].index)
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
            f'No zones with activity in the last {n_hours} hours.<br/>'
            f'Increase the window in the sidebar.'
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
            with col:
                st.markdown(_card(z, sdr, now), unsafe_allow_html=True)


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
        st.number_input(
            "Show zones active in the last N hours",
            min_value=1,
            max_value=168,
            value=24,
            step=1,
            key="n_hours_ctrl",
            help="Default 24h. Set to 72h+ if live data has gaps between sessions.",
        )
        if st.button("↻ Refresh Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.caption(
            "Auto-refreshes every 60 seconds via Streamlit fragment.  \n"
            "A zone exits the view when its last evolution activity  \n"
            "exceeds the N-hour window."
        )
        st.markdown("---")
        st.caption("Read-only · No data files are ever modified.")

    # ── Auto-refresh fragment (Streamlit ≥ 1.33, confirmed 1.57 here) ─────
    # run_every=60 re-runs _content() every 60s independently of the sidebar.
    # Sidebar changes still trigger a full rerun that resets the timer.
    _has_run_every = "run_every" in inspect.signature(st.fragment).parameters

    if _has_run_every:
        @st.fragment(run_every=60)
        def _content() -> None:
            _render()

        _content()
    else:
        # Fallback for older Streamlit builds (should not occur on 1.57)
        _render()
        st.info("Auto-refresh not available on this Streamlit version. Use ↻ Refresh Now.")


if __name__ == "__main__":
    main()

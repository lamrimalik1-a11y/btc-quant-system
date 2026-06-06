from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

import pandas as pd


def load_rdm_overlay_data(base_dir: Path, source_mode: str = "HISTORICAL_REPLAY_MODE") -> tuple[pd.DataFrame, pd.DataFrame]:
    output_dir = base_dir / "outputs"
    research_dir = base_dir / "research"
    if source_mode != "HISTORICAL_REPLAY_MODE":
        return pd.DataFrame(), pd.DataFrame()
    observation_rows = read_optional_csv(output_dir / "historical_observation_rows.csv")
    live_rows = read_optional_csv(research_dir / "zone_live_rdm_evolution.csv")
    return observation_rows, live_rows


def read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def render_rdm_visual_overlay(row: pd.Series, observation_rows: pd.DataFrame, live_rows: pd.DataFrame) -> None:
    import streamlit as st
    import streamlit.components.v1 as components

    st.subheader("RDM Visual Overlay - Research Only")
    st.caption(
        "Visual replay overlay for observation research only. It is not a signal, "
        "not execution, and does not affect Dashboard V2 scoring."
    )

    chart_data = overlay_chart_data(row, observation_rows, live_rows)
    if chart_data.empty:
        st.info("No replay rows available for visual overlay yet.")
        return

    html = build_overlay_svg(row, chart_data, live_rows_for_case(row, live_rows))
    components.html(html, height=620, scrolling=False)
    render_overlay_summary(row)
    render_rdm_price_overlay(row)


def overlay_chart_data(row: pd.Series, observation_rows: pd.DataFrame, live_rows: pd.DataFrame) -> pd.DataFrame:
    if not observation_rows.empty and {"row_id", "close"}.issubset(observation_rows.columns):
        source = observation_rows.copy()
        source["row_id_numeric"] = pd.to_numeric(source["row_id"], errors="coerce")
        source = source.dropna(subset=["row_id_numeric"])
        start = numeric(row.get("start_row_id")) or numeric(row.get("row_index")) or source["row_id_numeric"].min()
        end = numeric(row.get("end_row_id")) or start + 80
        case_live = live_rows_for_case(row, live_rows)
        if not case_live.empty and "row_index" in case_live.columns:
            live_row_ids = pd.to_numeric(case_live["row_index"], errors="coerce").dropna()
            if not live_row_ids.empty:
                start = min(start, live_row_ids.min())
                end = max(end, live_row_ids.max())
        padding = max((end - start) * 0.15, 20)
        selected = source[
            (source["row_id_numeric"] >= start - padding)
            & (source["row_id_numeric"] <= end + padding)
        ].copy()
        selected["chart_x"] = selected["row_id_numeric"]
        selected["chart_price"] = pd.to_numeric(selected["close"], errors="coerce")
        selected["chart_label"] = selected.get("market_timestamp", selected["row_id"]).astype(str)
        return selected.dropna(subset=["chart_price"])

    case_live = live_rows_for_case(row, live_rows)
    if case_live.empty:
        return pd.DataFrame()
    selected = case_live.copy()
    selected["chart_x"] = pd.to_numeric(selected.get("row_index"), errors="coerce")
    selected["chart_price"] = pd.to_numeric(selected.get("price"), errors="coerce")
    selected["chart_label"] = selected.get("timestamp", selected.get("row_index")).astype(str)
    return selected.dropna(subset=["chart_x", "chart_price"])


def live_rows_for_case(row: pd.Series, live_rows: pd.DataFrame) -> pd.DataFrame:
    if live_rows.empty or "case_id" not in live_rows.columns:
        return pd.DataFrame()
    case_id = str(row.get("case_id") or "")
    return live_rows[live_rows["case_id"].astype(str) == case_id].copy()


def build_overlay_svg(row: pd.Series, chart_data: pd.DataFrame, case_live: pd.DataFrame) -> str:
    width = 1120
    height = 500
    pad_left = 58
    pad_right = 28
    pad_top = 28
    pad_bottom = 72
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    x_values = pd.to_numeric(chart_data["chart_x"], errors="coerce")
    y_values = pd.to_numeric(chart_data["chart_price"], errors="coerce")
    y_levels = [
        numeric(row.get("formation_upper_edge")),
        numeric(row.get("formation_lower_edge")),
        numeric(row.get("interaction_core_upper_edge")),
        numeric(row.get("interaction_core_lower_edge")),
        numeric(row.get("real_birth_price")),
        numeric(row.get("last_mechanical_interaction_price")),
    ]
    y_min = min([y_values.min(), *[value for value in y_levels if value is not None]])
    y_max = max([y_values.max(), *[value for value in y_levels if value is not None]])
    if y_max == y_min:
        y_max += 1
        y_min -= 1
    y_margin = (y_max - y_min) * 0.08
    y_min -= y_margin
    y_max += y_margin
    x_min = x_values.min()
    x_max = x_values.max()
    if x_max == x_min:
        x_max += 1

    def sx(value: Any) -> float:
        number = numeric(value)
        if number is None:
            return pad_left
        return pad_left + ((number - x_min) / (x_max - x_min)) * plot_w

    def sy(value: Any) -> float:
        number = numeric(value)
        if number is None:
            return pad_top + plot_h
        return pad_top + ((y_max - number) / (y_max - y_min)) * plot_h

    line_points = " ".join(
        f"{sx(x)},{sy(y)}" for x, y in zip(x_values.tolist(), y_values.tolist())
    )
    shapes = []
    shapes.append(rect_band(row, sx, sy, x_min, x_max, "formation_lower_edge", "formation_upper_edge", "#94A3B8", 0.09, "CONTEXT / FORMATION RANGE"))
    core_color = core_overlay_color(str(row.get("interaction_core_width_state") or ""))
    shapes.append(rect_band(row, sx, sy, x_min, x_max, "interaction_core_lower_edge", "interaction_core_upper_edge", core_color, 0.44, "ACTIVE RDM ZONE"))
    shapes.append(rect_band(row, sx, sy, x_min, x_max, "interaction_density_lower_band", "interaction_density_upper_band", "#A855F7", 0.38, "INTERACTION DENSITY"))
    shapes.append(marker(sx(x_min), sy(row.get("real_birth_price")), "#22D3EE", "ZONE BIRTH"))
    if numeric(row.get("interaction_density_peak_price")) is not None:
        shapes.append(marker(sx(x_max), sy(row.get("interaction_density_peak_price")), "#7C3AED", "DENSITY PEAK"))
    shapes.extend(live_markers(case_live, sx, sy))
    if truthy(row.get("true_mechanical_death_flag")):
        death_x = x_from_live_time_or_last(case_live, x_max)
        death_y = numeric(row.get("last_mechanical_interaction_price")) or numeric(row.get("real_birth_price")) or y_values.iloc[-1]
        shapes.append(x_marker(sx(death_x), sy(death_y), "#7F1D1D", "MECHANICALLY DEAD"))

    fatigue_polyline = fatigue_line(case_live, sx, height - 48, height - 18)
    status = escape(format_label(row.get("rdm_final_status") or row.get("guarded_live_status") or "N/A"))
    lifecycle = escape(format_label(row.get("true_lifecycle_state") or "N/A"))
    guarded = escape(format_label(row.get("guarded_live_status") or "N/A"))

    return f"""
    <div style="font-family:Inter,Segoe UI,Arial,sans-serif;border:1px solid #E5E7EB;border-radius:8px;padding:10px;background:#fff;">
      <div style="display:flex;gap:12px;align-items:center;margin-bottom:8px;">
        <strong>RDM Overlay</strong>
        <span style="background:#DBEAFE;padding:2px 8px;border-radius:999px;">{status}</span>
        <span style="background:#E0F2FE;padding:2px 8px;border-radius:999px;">Lifecycle: {lifecycle}</span>
        <span style="background:#FEF3C7;padding:2px 8px;border-radius:999px;">Live: {guarded}</span>
      </div>
      <svg width="100%" viewBox="0 0 {width} {height}" role="img" aria-label="RDM visual overlay">
        <rect x="0" y="0" width="{width}" height="{height}" fill="#FFFFFF"/>
        <line x1="{pad_left}" y1="{pad_top + plot_h}" x2="{width - pad_right}" y2="{pad_top + plot_h}" stroke="#CBD5E1"/>
        <line x1="{pad_left}" y1="{pad_top}" x2="{pad_left}" y2="{pad_top + plot_h}" stroke="#CBD5E1"/>
        {''.join(shapes)}
        <polyline points="{line_points}" fill="none" stroke="#111827" stroke-width="2"/>
        <text x="{pad_left}" y="{pad_top - 8}" fill="#475569" font-size="12">Price replay with RDM research overlays</text>
        <text x="{pad_left}" y="{height - 54}" fill="#475569" font-size="12">Fatigue / health strip</text>
        {fatigue_polyline}
      </svg>
    </div>
    """


def rect_band(row: pd.Series, sx, sy, x_min: float, x_max: float, lower_field: str, upper_field: str, color: str, opacity: float, label: str) -> str:
    lower = numeric(row.get(lower_field))
    upper = numeric(row.get(upper_field))
    if lower is None or upper is None:
        return ""
    y_top = sy(max(lower, upper))
    y_bottom = sy(min(lower, upper))
    x = sx(x_min)
    width = sx(x_max) - x
    height = max(y_bottom - y_top, 2)
    stroke_width = 3 if "ACTIVE RDM" in label else 1
    stroke_opacity = 0.95 if "ACTIVE RDM" in label else 0.35
    return (
        f'<rect x="{x:.2f}" y="{y_top:.2f}" width="{width:.2f}" height="{height:.2f}" '
        f'fill="{color}" opacity="{opacity}" stroke="{color}" stroke-width="{stroke_width}" stroke-opacity="{stroke_opacity}"/>'
        f'<text x="{x + 8:.2f}" y="{y_top + 16:.2f}" fill="{color}" font-size="12" font-weight="700">{escape(label)}</text>'
    )


def marker(x: float, y: float, color: str, label: str) -> str:
    return (
        f'<circle cx="{x:.2f}" cy="{y:.2f}" r="6" fill="{color}" stroke="#0F172A" stroke-width="1"/>'
        f'<text x="{x + 8:.2f}" y="{y - 8:.2f}" fill="#0F172A" font-size="11">{escape(label)}</text>'
    )


def x_marker(x: float, y: float, color: str, label: str) -> str:
    return (
        f'<line x1="{x-7:.2f}" y1="{y-7:.2f}" x2="{x+7:.2f}" y2="{y+7:.2f}" stroke="{color}" stroke-width="3"/>'
        f'<line x1="{x+7:.2f}" y1="{y-7:.2f}" x2="{x-7:.2f}" y2="{y+7:.2f}" stroke="{color}" stroke-width="3"/>'
        f'<text x="{x + 10:.2f}" y="{y - 10:.2f}" fill="{color}" font-size="11" font-weight="700">{escape(label)}</text>'
    )


def live_markers(case_live: pd.DataFrame, sx, sy) -> list[str]:
    if case_live.empty:
        return []
    markers = []
    sampled = case_live[
        case_live.get("zone_touch_flag", pd.Series(False, index=case_live.index)).astype(str).str.upper().isin(["TRUE", "1"])
        | case_live.get("return_to_zone_flag", pd.Series(False, index=case_live.index)).astype(str).str.upper().isin(["TRUE", "1"])
        | case_live.get("guarded_live_status", pd.Series("", index=case_live.index)).astype(str).isin(["LIVE_BREACH", "LIVE_RUPTURE"])
    ].head(40)
    for _, live_row in sampled.iterrows():
        status = str(live_row.get("guarded_live_status") or "")
        color = "#16A34A"
        label = "TOUCH"
        if status == "LIVE_RUPTURE":
            color = "#DC2626"
            label = "RUPTURE"
        elif status == "LIVE_BREACH":
            color = "#F97316"
            label = "BREACH"
        elif truthy(live_row.get("return_to_zone_flag")):
            color = "#22C55E"
            label = "RETEST"
        x = sx(live_row.get("row_index"))
        y = sy(live_row.get("price"))
        markers.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}" opacity="0.85"><title>{escape(label)}</title></circle>')
        if label in {"BREACH", "RUPTURE"}:
            markers.append(f'<line x1="{x:.2f}" y1="28" x2="{x:.2f}" y2="428" stroke="{color}" stroke-dasharray="4 4" opacity="0.7"/>')
    return markers


def fatigue_line(case_live: pd.DataFrame, sx, y_top: float, y_bottom: float) -> str:
    if case_live.empty or "row_index" not in case_live.columns:
        return ""
    rows = case_live.copy()
    fatigue = pd.to_numeric(rows.get("fatigue_live", 0), errors="coerce").fillna(0).clip(0, 100)
    points = []
    for (_, live_row), fatigue_value in zip(rows.iterrows(), fatigue):
        x = sx(live_row.get("row_index"))
        y = y_bottom - (fatigue_value / 100.0) * (y_bottom - y_top)
        points.append(f"{x},{y}")
    return f'<polyline points="{" ".join(points)}" fill="none" stroke="#EF4444" stroke-width="2" opacity="0.75"/>'


def x_from_live_time_or_last(case_live: pd.DataFrame, fallback: float) -> float:
    if case_live.empty or "row_index" not in case_live.columns:
        return fallback
    return numeric(case_live.tail(1).iloc[0].get("row_index")) or fallback


def core_overlay_color(state: str) -> str:
    state = state.upper()
    if state == "CORE_TIGHT":
        return "#22C55E"
    if state == "CORE_NORMAL":
        return "#EAB308"
    if state == "CORE_FALLBACK":
        return "#94A3B8"
    if "INVALID" in state:
        return "#DC2626"
    return "#F59E0B"


def render_overlay_summary(row: pd.Series) -> None:
    import streamlit as st

    columns = st.columns(4)
    summary_items = [
        ("Active RDM Zone / Interaction Core Width", "interaction_core_width"),
        ("Density Band / Interaction Heart Width", "interaction_density_width"),
        ("Density State", "interaction_density_state"),
        ("Density Peak", "interaction_density_peak_price"),
        ("Efficiency Ratio", "interaction_core_efficiency_ratio"),
        ("Core State", "interaction_core_width_state"),
        ("Formation Range Width (broad context)", "formation_width"),
        ("Lifecycle", "true_lifecycle_state"),
        ("Guarded Status", "guarded_live_status"),
        ("Fatigue", "fatigue_live"),
        ("Health", "health_live"),
        ("Death Score", "mechanical_death_score"),
    ]
    for index, (label, field) in enumerate(summary_items):
        columns[index % 4].metric(label, display_value(row.get(field)))


def render_rdm_price_overlay(row: pd.Series) -> None:
    import streamlit as st
    import streamlit.components.v1 as components

    st.subheader("RDM Price Overlay - Research Only")
    st.caption(
        "Absolute BTC price view for comparing RDM zones directly with chart "
        "prices. Display only; it does not affect calculations, scoring, or signals."
    )

    required_fields = [
        "formation_lower_edge",
        "formation_upper_edge",
        "interaction_core_lower_edge",
        "interaction_core_upper_edge",
        "interaction_density_lower_band",
        "interaction_density_upper_band",
    ]
    if any(numeric(row.get(field)) is None for field in required_fields):
        st.info("No complete price overlay geometry is mapped for this case yet.")
        return

    components.html(build_price_overlay_html(row), height=560, scrolling=False)
    st.dataframe(
        build_price_overlay_table(row),
        use_container_width=True,
        hide_index=True,
    )


def build_price_overlay_html(row: pd.Series) -> str:
    width = 920
    height = 390
    pad_left = 150
    pad_right = 40
    pad_top = 36
    pad_bottom = 40
    plot_h = height - pad_top - pad_bottom
    band_x = pad_left + 170
    band_w = width - band_x - pad_right

    formation_lower = numeric(row.get("formation_lower_edge"))
    formation_upper = numeric(row.get("formation_upper_edge"))
    core_lower = numeric(row.get("interaction_core_lower_edge"))
    core_upper = numeric(row.get("interaction_core_upper_edge"))
    density_lower = numeric(row.get("interaction_density_lower_band"))
    density_upper = numeric(row.get("interaction_density_upper_band"))
    birth_price = numeric(row.get("real_birth_price")) or numeric(row.get("birth_price"))

    prices = [
        formation_lower,
        formation_upper,
        core_lower,
        core_upper,
        density_lower,
        density_upper,
        birth_price,
    ]
    valid_prices = [price for price in prices if price is not None]
    price_min = min(valid_prices)
    price_max = max(valid_prices)
    if price_max == price_min:
        price_max += 1
        price_min -= 1
    margin = max((price_max - price_min) * 0.10, 10)
    price_min -= margin
    price_max += margin

    def sy(price: Any) -> float:
        number = numeric(price)
        if number is None:
            return pad_top + plot_h
        return pad_top + ((price_max - number) / (price_max - price_min)) * plot_h

    axis_ticks = price_axis_ticks(price_min, price_max, 6)
    tick_shapes = []
    for tick in axis_ticks:
        y = sy(tick)
        tick_shapes.append(
            f'<line x1="{pad_left - 8}" y1="{y:.2f}" x2="{width - pad_right}" y2="{y:.2f}" '
            f'stroke="#E2E8F0" stroke-width="1"/>'
            f'<text x="{pad_left - 14}" y="{y + 4:.2f}" text-anchor="end" '
            f'fill="#475569" font-size="12">{format_price(tick)}</text>'
        )

    bands = [
        price_band(
            sy,
            band_x,
            band_w,
            formation_lower,
            formation_upper,
            "#94A3B8",
            0.22,
            "Formation Range (broad context)",
        ),
        price_band(
            sy,
            band_x + 34,
            band_w - 68,
            core_lower,
            core_upper,
            "#22C55E",
            0.52,
            "Active RDM Zone / Interaction Core",
        ),
        price_band(
            sy,
            band_x + 76,
            band_w - 152,
            density_lower,
            density_upper,
            "#A855F7",
            0.66,
            "Density Band / Interaction Heart",
        ),
    ]

    birth_line = ""
    if birth_price is not None:
        y = sy(birth_price)
        birth_line = (
            f'<line x1="{pad_left}" y1="{y:.2f}" x2="{width - pad_right}" y2="{y:.2f}" '
            f'stroke="#0891B2" stroke-width="3" stroke-dasharray="7 5"/>'
            f'<text x="{pad_left + 8}" y="{y - 8:.2f}" fill="#0E7490" '
            f'font-size="12" font-weight="700">Birth Price {format_price(birth_price)}</text>'
        )

    episode_id = escape(display_value(row.get("episode_id")))
    case_id = escape(display_value(row.get("case_id")))
    utc_time = display_value(row.get("episode_start_time_utc"))
    algeria_time = algeria_time_from_utc(row.get("episode_start_time_utc"))
    core_ratio = ratio_value(row.get("interaction_core_width"), row.get("formation_width"))
    density_ratio = ratio_value(row.get("interaction_density_width"), row.get("formation_width"))

    return f"""
    <div style="font-family:Inter,Segoe UI,Arial,sans-serif;border:1px solid #E5E7EB;border-radius:8px;padding:12px;background:#FFFFFF;">
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
        <strong>RDM Price Overlay</strong>
        <span style="background:#E0F2FE;padding:2px 8px;border-radius:999px;">Episode {episode_id}</span>
        <span style="background:#F1F5F9;padding:2px 8px;border-radius:999px;">{case_id}</span>
        <span style="background:#ECFDF5;padding:2px 8px;border-radius:999px;">Core / Formation: {format_ratio(core_ratio)}</span>
        <span style="background:#F3E8FF;padding:2px 8px;border-radius:999px;">Density / Formation: {format_ratio(density_ratio)}</span>
      </div>
      <div style="color:#475569;font-size:12px;margin-bottom:8px;">
        UTC: {escape(utc_time)} | Algeria: {escape(algeria_time)}
      </div>
      <svg width="100%" viewBox="0 0 {width} {height}" role="img" aria-label="Absolute price RDM overlay">
        <rect x="0" y="0" width="{width}" height="{height}" fill="#FFFFFF"/>
        <text x="{pad_left}" y="22" fill="#334155" font-size="13" font-weight="700">Absolute Price Axis</text>
        <line x1="{pad_left}" y1="{pad_top}" x2="{pad_left}" y2="{height - pad_bottom}" stroke="#64748B" stroke-width="2"/>
        {''.join(tick_shapes)}
        {''.join(bands)}
        {birth_line}
      </svg>
    </div>
    """


def price_band(sy, x: float, width: float, lower: Any, upper: Any, color: str, opacity: float, label: str) -> str:
    lower_value = numeric(lower)
    upper_value = numeric(upper)
    if lower_value is None or upper_value is None:
        return ""
    y_top = sy(max(lower_value, upper_value))
    y_bottom = sy(min(lower_value, upper_value))
    height = max(y_bottom - y_top, 3)
    return (
        f'<rect x="{x:.2f}" y="{y_top:.2f}" width="{width:.2f}" height="{height:.2f}" '
        f'fill="{color}" opacity="{opacity}" stroke="{color}" stroke-width="2"/>'
        f'<text x="{x + 10:.2f}" y="{max(y_top - 7, 18):.2f}" fill="{color}" '
        f'font-size="12" font-weight="700">{escape(label)} '
        f'{format_price(lower_value)} -> {format_price(upper_value)}</text>'
    )


def build_price_overlay_table(row: pd.Series) -> pd.DataFrame:
    formation_width = numeric(row.get("formation_width"))
    core_width = numeric(row.get("interaction_core_width"))
    density_width = numeric(row.get("interaction_density_width"))

    rows = [
        {
            "Layer": "Formation Range (broad context)",
            "Lower": format_price(row.get("formation_lower_edge")),
            "Upper": format_price(row.get("formation_upper_edge")),
            "Width": format_price(formation_width),
            "Compression Ratio": "1.0000",
        },
        {
            "Layer": "Active RDM Zone / Interaction Core",
            "Lower": format_price(row.get("interaction_core_lower_edge")),
            "Upper": format_price(row.get("interaction_core_upper_edge")),
            "Width": format_price(core_width),
            "Compression Ratio": format_ratio(ratio_value(core_width, formation_width)),
        },
        {
            "Layer": "Density Band / Interaction Heart",
            "Lower": format_price(row.get("interaction_density_lower_band")),
            "Upper": format_price(row.get("interaction_density_upper_band")),
            "Width": format_price(density_width),
            "Compression Ratio": format_ratio(ratio_value(density_width, formation_width)),
        },
        {
            "Layer": "Birth Price",
            "Lower": "",
            "Upper": "",
            "Width": format_price(numeric(row.get("real_birth_price")) or numeric(row.get("birth_price"))),
            "Compression Ratio": "",
        },
    ]
    return pd.DataFrame(rows)


def price_axis_ticks(price_min: float, price_max: float, count: int) -> list[float]:
    if count <= 1:
        return [price_min, price_max]
    step = (price_max - price_min) / (count - 1)
    return [price_min + step * index for index in range(count)]


def ratio_value(numerator: Any, denominator: Any) -> float | None:
    numerator_value = numeric(numerator)
    denominator_value = numeric(denominator)
    if numerator_value is None or denominator_value in [None, 0]:
        return None
    return numerator_value / denominator_value


def format_ratio(value: Any) -> str:
    number = numeric(value)
    if number is None:
        return "N/A"
    return f"{number:.4f}"


def format_price(value: Any) -> str:
    number = numeric(value)
    if number is None:
        return "N/A"
    return f"{number:.2f}"


def algeria_time_from_utc(value: Any) -> str:
    parsed = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(parsed):
        return display_value(value)
    return (parsed + pd.Timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")


def numeric(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def truthy(value: Any) -> bool:
    return str(value).upper() in {"TRUE", "1", "YES"}


def display_value(value: Any) -> str:
    if value is None:
        return "N/A"
    try:
        if pd.isna(value):
            return "N/A"
    except (TypeError, ValueError):
        pass
    text = str(value)
    if "_" in text:
        return text.replace("_", " ").title()
    return text


def format_label(value: Any) -> str:
    return display_value(value)

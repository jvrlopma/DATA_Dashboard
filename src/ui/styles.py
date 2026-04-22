"""Sistema de diseño DATA Dashboard — implementación del design bundle de Claude Design.

Paleta de colores (hex exactos del bundle, equivalentes oklch del diseño):
  ok    = #39b577  warn  = #d9a441  crit  = #d14a5b  none  = #8a8f96
  accent= #3b6bd9  text  = #1a2330  bg    = #f9fafb  surface=#ffffff

CSS scoped bajo .dd para evitar conflictos con estilos propios de Streamlit.
Todos los colores en hex puro (sin oklch) para máxima compatibilidad.
"""

import streamlit as st
import plotly.io as pio
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Paleta hex (extraída directamente del screen-specs.jsx del design bundle)
# ---------------------------------------------------------------------------
C = {
    "ok":           "#39b577",
    "warn":         "#d9a441",
    "crit":         "#d14a5b",
    "none":         "#8a8f96",
    "accent":       "#3b6bd9",
    "ok_bg":        "#edf7f1",
    "ok_border":    "#a8d9bf",
    "ok_text":      "#1d6b46",
    "warn_bg":      "#fdf6e3",
    "warn_border":  "#e8cc80",
    "warn_text":    "#8a6000",
    "crit_bg":      "#fdf0f1",
    "crit_border":  "#e8a0ab",
    "crit_text":    "#8a1f30",
    "none_bg":      "#f5f6f7",
    "none_border":  "#c8ccd0",
    "none_text":    "#555a60",
    "bg":           "#f9fafb",
    "bg_subtle":    "#f3f4f6",
    "bg_muted":     "#eff0f3",
    "surface":      "#ffffff",
    "surface_alt":  "#f7f8fa",
    "border":       "#e5e7eb",
    "border_strong":"#d1d5db",
    "divider":      "#eef0f3",
    "text":         "#1a2330",
    "text2":        "#5a6475",
    "text3":        "#8a909a",
    "text4":        "#b0b5bc",
    "grid":         "#eef0f3",
    "axis":         "#c5cad0",
}

# ---------------------------------------------------------------------------
# Plotly template global (del plotlyTemplate del screen-specs.jsx)
# ---------------------------------------------------------------------------
pio.templates["data_dashboard"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Space Grotesk, system-ui, sans-serif", size=12, color="#1a2330"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        colorway=["#3b6bd9", "#39b577", "#d9a441", "#d14a5b"],
        xaxis=dict(gridcolor="#eef0f3", zerolinecolor="#dfe2e6",
                   linecolor="#cfd3d9", ticks="outside", ticklen=4),
        yaxis=dict(gridcolor="#eef0f3", zerolinecolor="#dfe2e6",
                   linecolor="#cfd3d9", ticks="outside", ticklen=4),
        margin=dict(l=48, r=16, t=24, b=40),
        hoverlabel=dict(bgcolor="#1a2330", font_color="#ffffff",
                        font_family="JetBrains Mono, monospace"),
    )
)
pio.templates.default = "data_dashboard"

# ---------------------------------------------------------------------------
# Mapa de estado
# ---------------------------------------------------------------------------
_SM = {
    "OK":      ("ok",   "✓", "OK"),
    "REGULAR": ("warn", "!", "REGULAR"),
    "CRITICO": ("crit", "×", "CRÍTICO"),
    None:      ("none", "•", "SIN DATOS"),
}

def status_key(estado) -> str:
    return _SM.get(estado, _SM[None])[0]


# ---------------------------------------------------------------------------
# Helpers HTML — usan clases CSS scoped bajo .dd
# ---------------------------------------------------------------------------

def badge_html(estado, sin_datos: bool = False) -> str:
    key = None if sin_datos else estado
    sk, icon, label = _SM.get(key, _SM[None])
    return f'<span class="dd-badge {sk}"><span class="dd-badge-icon">{icon}</span>{label}</span>'


def kpi_strip_html(total: int, ok: int, warn: int, crit: int) -> str:
    none_count = total - ok - warn - crit
    return f"""<div class="dd"><div class="kpi-strip">
  <div class="kpi">
    <div class="kpi-label">TOTAL PROYECTOS</div>
    <div class="kpi-value">{total}</div>
    <div class="kpi-delta">pipelines activos</div>
  </div>
  <div class="kpi accent-ok">
    <div class="kpi-label"><span class="icon-ok">✓</span> OK</div>
    <div class="kpi-value">{ok}<span class="kpi-unit">/ {total}</span></div>
    <div class="kpi-delta">operativos</div>
  </div>
  <div class="kpi accent-warn">
    <div class="kpi-label"><span class="icon-warn">!</span> REGULAR</div>
    <div class="kpi-value">{warn}<span class="kpi-unit">/ {total}</span></div>
    <div class="kpi-delta">degradados</div>
  </div>
  <div class="kpi accent-crit">
    <div class="kpi-label"><span class="icon-crit">×</span> CRÍTICO</div>
    <div class="kpi-value">{crit}<span class="kpi-unit">/ {total}</span></div>
    <div class="kpi-delta kpi-delta-down">requieren atención</div>
  </div>
</div></div>"""


def day_kpi_strip_html(ejecuciones: int, proyectos: int, total_proy: int,
                       pct_ok: float, total_proc: int) -> str:
    return f"""<div class="dd"><div class="kpi-strip">
  <div class="kpi">
    <div class="kpi-label">EJECUCIONES HOY</div>
    <div class="kpi-value">{ejecuciones:,}</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">PROYECTOS ACTIVOS</div>
    <div class="kpi-value">{proyectos}<span class="kpi-unit">/ {total_proy}</span></div>
  </div>
  <div class="kpi accent-ok">
    <div class="kpi-label"><span class="icon-ok">✓</span> % OK MEDIO</div>
    <div class="kpi-value">{pct_ok:.1f}<span class="kpi-unit">%</span></div>
  </div>
  <div class="kpi">
    <div class="kpi-label">TOTAL PROCESOS</div>
    <div class="kpi-value">{total_proc:,}</div>
  </div>
</div></div>"""


def project_card_html(proyecto: str, grupo: str, estado, sin_datos: bool,
                      xok, dt_str: str) -> str:
    sk = status_key(None if sin_datos else estado)
    xok_str = f"{xok:.1f}" if xok is not None else "—"
    pct = min(float(xok or 0), 100)
    bdg = badge_html(estado, sin_datos)
    unit = "" if sin_datos or xok is None else '<span class="pcard-metric-unit">%</span>'
    return f"""<div class="dd"><div class="pcard pcard-a {sk}">
  <div class="pcard-a-rail"></div>
  <div class="pcard-a-body">
    <div class="pcard-a-head">
      <div>
        <div class="pcard-cat">Grupo {grupo}</div>
        <div class="pcard-name">{proyecto}</div>
      </div>
      {bdg}
    </div>
    <div class="pcard-a-metrics">
      <div class="pcard-metric">
        <div class="pcard-metric-label">% EJECUCIONES OK</div>
        <div class="pcard-metric-value mono">{xok_str}{unit}</div>
      </div>
      <div class="pcard-metric">
        <div class="pcard-metric-label">ÚLTIMA EJECUCIÓN</div>
        <div class="pcard-metric-value sm mono">{dt_str}</div>
      </div>
    </div>
    <div class="pcard-a-foot">
      <div class="progress {sk}"><span style="width:{pct:.1f}%"></span></div>
    </div>
  </div>
</div></div>"""


def attention_items_html(items: list) -> str:
    """items: lista de (badge_html, name, reason, time_str)"""
    rows = ""
    for bdg, name, reason, ts in items:
        rows += (
            f'<div class="attention-item">'
            f'{bdg}'
            f'<span class="name">{name}</span>'
            f'<span class="reason">{reason}</span>'
            f'<span class="time mono">{ts}</span>'
            f'</div>'
        )
    empty = f'<div style="padding:24px;text-align:center;color:{C["text3"]};font-size:12px">Todos los pipelines están OK</div>'
    return f'<div class="dd">{rows if rows else empty}</div>'


def panel_html(title: str, subtitle: str, body_html: str, no_pad: bool = False) -> str:
    pad_class = "panel-body no-pad" if no_pad else "panel-body"
    return (
        f'<div class="dd"><div class="panel">'
        f'<div class="panel-header">'
        f'<h3>{title}</h3>'
        f'<span class="subtitle">{subtitle}</span>'
        f'</div>'
        f'<div class="{pad_class}">{body_html}</div>'
        f'</div></div>'
    )


def section_title_html(text: str, sub: str = "") -> str:
    sub_html = f'<span class="mono" style="color:{C["text4"]};font-weight:500;text-transform:none;letter-spacing:0;margin-left:8px">{sub}</span>' if sub else ""
    return f'<div class="dd"><div class="section-title">{text}{sub_html}</div></div>'


def mini_grid_html(stats: list, cols: int = 3) -> str:
    """stats: lista de (label, value, status_key='')"""
    cells = ""
    for label, value, *rest in stats:
        sk = rest[0] if rest else ""
        cls = f"mini-stat {sk}" if sk else "mini-stat"
        cells += (
            f'<div class="{cls}">'
            f'<div class="mini-stat-label">{label}</div>'
            f'<div class="mini-stat-value mono">{value}</div>'
            f'</div>'
        )
    return (
        f'<div class="dd"><div class="mini-grid" '
        f'style="grid-template-columns:repeat({cols},1fr)">'
        f'{cells}</div></div>'
    )


# ---------------------------------------------------------------------------
# CSS — hex puro, scoped bajo .dd, refleja fielmente el design bundle
# ---------------------------------------------------------------------------
_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>
/* ===== Aplicar fuente a todo Streamlit ===== */
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stSidebar"],
.stMarkdown, .stMarkdown p, .stMarkdown div,
h1, h2, h3, h4, p, label, button, input, select {
  font-family: 'Space Grotesk', system-ui, sans-serif !important;
}
.stApp { background: #f9fafb !important; }
.block-container { padding-top: 1.5rem !important; max-width: 1600px !important; }
[data-testid="stSidebar"] > div:first-child { background: #ffffff !important; border-right: 1px solid #e5e7eb !important; }
#MainMenu, footer { visibility: hidden !important; }
.stMarkdown { margin-bottom: 0 !important; }
.element-container { margin-bottom: 6px !important; }

/* ===== Scope: .dd contiene todos los elementos del design ===== */

/* -- Badge -- */
.dd .dd-badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 2px 8px 2px 6px;
  font-size: 11px; font-weight: 600; letter-spacing: 0.02em; text-transform: uppercase;
  border-radius: 999px; border: 1px solid; white-space: nowrap; line-height: 1.4;
  font-family: 'JetBrains Mono', monospace;
}
.dd .dd-badge-icon { font-size: 10px; line-height: 1; }
.dd .dd-badge.ok   { background: #edf7f1; color: #1d6b46; border-color: #a8d9bf; }
.dd .dd-badge.warn { background: #fdf6e3; color: #8a6000; border-color: #e8cc80; }
.dd .dd-badge.crit { background: #fdf0f1; color: #8a1f30; border-color: #e8a0ab; }
.dd .dd-badge.none { background: #f5f6f7; color: #555a60; border-color: #c8ccd0; }

/* -- KPI strip -- */
.dd .kpi-strip {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 4px;
}
.dd .kpi {
  background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px;
  padding: 16px; display: flex; flex-direction: column; gap: 8px;
  position: relative; overflow: hidden;
}
.dd .kpi::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  border-radius: 2px 0 0 2px;
}
.dd .kpi.accent-ok::before   { background: #39b577; }
.dd .kpi.accent-warn::before { background: #d9a441; }
.dd .kpi.accent-crit::before { background: #d14a5b; }
.dd .kpi-label {
  font-size: 10px; font-weight: 600; color: #8a909a;
  text-transform: uppercase; letter-spacing: 0.08em;
  font-family: 'JetBrains Mono', monospace;
  display: flex; align-items: center; gap: 6px;
}
.dd .kpi-value {
  font-size: 32px; font-weight: 600; letter-spacing: -0.03em; line-height: 1;
  font-variant-numeric: tabular-nums; color: #1a2330;
  display: flex; align-items: baseline; gap: 6px;
}
.dd .kpi-unit { font-size: 14px; font-weight: 500; color: #8a909a; letter-spacing: 0; }
.dd .kpi-delta { font-size: 11px; color: #8a909a; font-family: 'JetBrains Mono', monospace; }
.dd .kpi-delta-down { color: #d14a5b; }
.dd .kpi-delta-up   { color: #39b577; }
.dd .icon-ok   { color: #39b577; }
.dd .icon-warn { color: #d9a441; }
.dd .icon-crit { color: #d14a5b; }

/* -- Project card Variant A -- */
.dd .pcard {
  background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px;
  overflow: hidden; box-shadow: 0 1px 2px rgba(26,35,48,0.05);
  transition: border-color 120ms, box-shadow 120ms; margin-bottom: 4px;
}
.dd .pcard:hover { border-color: #d1d5db; box-shadow: 0 2px 8px rgba(26,35,48,0.08); }
.dd .pcard.ok   { border-color: #a8d9bf; }
.dd .pcard.warn { border-color: #e8cc80; }
.dd .pcard.crit { border-color: #e8a0ab; }
.dd .pcard-a { display: grid; grid-template-columns: 3px 1fr; min-height: 150px; }
.dd .pcard-a-rail { }
.dd .pcard-a.ok   .pcard-a-rail { background: #39b577; }
.dd .pcard-a.warn .pcard-a-rail { background: #d9a441; }
.dd .pcard-a.crit .pcard-a-rail { background: #d14a5b; }
.dd .pcard-a.none .pcard-a-rail { background: #8a8f96; }
.dd .pcard-a-body { padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.dd .pcard-a-head {
  display: flex; justify-content: space-between; align-items: flex-start; gap: 10px;
}
.dd .pcard-cat {
  font-size: 10px; font-weight: 500; color: #8a909a;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 3px;
}
.dd .pcard-name { font-size: 13px; font-weight: 600; color: #1a2330; letter-spacing: -0.01em; line-height: 1.2; }
.dd .pcard-a-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.dd .pcard-metric { display: flex; flex-direction: column; gap: 3px; }
.dd .pcard-metric-label {
  font-size: 9px; font-weight: 600; color: #b0b5bc;
  font-family: 'JetBrains Mono', monospace; text-transform: uppercase; letter-spacing: 0.1em;
}
.dd .pcard-metric-value {
  font-size: 20px; font-weight: 600; letter-spacing: -0.02em;
  color: #1a2330; line-height: 1.1;
  display: flex; align-items: baseline; gap: 3px;
  font-variant-numeric: tabular-nums;
}
.dd .pcard-metric-value.sm { font-size: 13px !important; }
.dd .pcard-metric-unit { font-size: 11px; font-weight: 500; color: #8a909a; }
.dd .pcard-metric-sub { font-size: 10px; color: #b0b5bc; }
.dd .pcard-a-foot { margin-top: auto; padding-top: 8px; border-top: 1px dashed #eef0f3; }

/* -- Progress bar -- */
.dd .progress {
  height: 4px; background: #eff0f3; border-radius: 999px; overflow: hidden;
}
.dd .progress > span {
  display: block; height: 100%; border-radius: inherit; transition: width 300ms ease;
}
.dd .progress.ok   > span { background: #39b577; }
.dd .progress.warn > span { background: #d9a441; }
.dd .progress.crit > span { background: #d14a5b; }
.dd .progress.none > span { background: #8a8f96; }

/* -- Panel -- */
.dd .panel {
  background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden;
}
.dd .panel-header {
  padding: 12px 16px; border-bottom: 1px solid #eef0f3;
  display: flex; align-items: center; gap: 12px;
}
.dd .panel-header h3 {
  margin: 0; font-size: 13px; font-weight: 600; color: #1a2330; letter-spacing: -0.005em;
}
.dd .panel-header .subtitle {
  font-size: 11px; color: #8a909a; font-family: 'JetBrains Mono', monospace;
}
.dd .panel-body { padding: 16px; }
.dd .panel-body.no-pad { padding: 0; }

/* -- Section title -- */
.dd .section-title {
  font-size: 11px; font-weight: 600; color: #8a909a;
  text-transform: uppercase; letter-spacing: 0.1em;
  font-family: 'JetBrains Mono', monospace;
  margin: 8px 0; display: flex; align-items: center; gap: 8px;
}
.dd .section-title::after {
  content: ''; flex: 1; height: 1px; background: #eef0f3;
}

/* -- Attention list -- */
.dd .attention-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px; border-bottom: 1px solid #eef0f3; font-size: 12px;
}
.dd .attention-item:last-child { border-bottom: none; }
.dd .attention-item .name { font-weight: 600; color: #1a2330; }
.dd .attention-item .reason { color: #8a909a; flex: 1; }
.dd .attention-item .time {
  font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #8a909a;
}

/* -- Mini grid (9-stat breakdown) -- */
.dd .mini-grid {
  display: grid; gap: 1px; background: #eef0f3;
  border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;
}
.dd .mini-stat {
  background: #ffffff; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;
}
.dd .mini-stat-label {
  font-size: 9px; font-weight: 600; color: #8a909a;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase; letter-spacing: 0.07em;
}
.dd .mini-stat-value {
  font-size: 22px; font-weight: 600; letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums; color: #1a2330; line-height: 1.1;
}
.dd .mini-stat.ok   .mini-stat-value { color: #1d6b46; }
.dd .mini-stat.warn .mini-stat-value { color: #8a6000; }
.dd .mini-stat.crit .mini-stat-value { color: #8a1f30; }

/* -- Util -- */
.dd .mono { font-family: 'JetBrains Mono', monospace !important; }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

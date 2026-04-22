"""Sistema de diseño DATA Dashboard — paleta oklch → hex, temas claro/oscuro.

Colores de estado (del design bundle):
  ok=#39b577  warn=#d9a441  crit=#d14a5b  none=#8a8f96  accent=#3b6bd9

Uso:
    set_dark(True/False)   → activa tema antes de renderizar
    inject_css()           → inyecta fuentes + CSS completo (ambos temas)
    badge_html(...)        → genera HTML con clase .dd o .dd.dark según tema
"""

import math
import streamlit as st
import plotly.io as pio
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Estado de tema (módulo-level, se configura desde app.py)
# ---------------------------------------------------------------------------
_dark: bool = False

def set_dark(dark: bool) -> None:
    global _dark
    _dark = dark

def _dd() -> str:
    """Clase del wrapper raíz según el tema activo."""
    return "dd dark" if _dark else "dd"


# ---------------------------------------------------------------------------
# Paletas de color
# ---------------------------------------------------------------------------

# Tema claro (hex equivalentes del bundle, screen-specs.jsx)
C = {
    "ok": "#39b577", "warn": "#d9a441", "crit": "#d14a5b",
    "none": "#8a8f96", "accent": "#3b6bd9",
    "ok_bg": "#edf7f1", "ok_border": "#a8d9bf", "ok_text": "#1d6b46",
    "warn_bg": "#fdf6e3", "warn_border": "#e8cc80", "warn_text": "#8a6000",
    "crit_bg": "#fdf0f1", "crit_border": "#e8a0ab", "crit_text": "#8a1f30",
    "none_bg": "#f5f6f7", "none_border": "#c8ccd0", "none_text": "#555a60",
    "bg": "#f9fafb", "bg_subtle": "#f3f4f6", "bg_muted": "#eff0f3",
    "surface": "#ffffff", "surface_alt": "#f7f8fa",
    "border": "#e5e7eb", "border_strong": "#d1d5db", "divider": "#eef0f3",
    "text": "#1a2330", "text2": "#5a6475", "text3": "#8a909a", "text4": "#b0b5bc",
    "grid": "#eef0f3", "axis": "#c5cad0",
}

# Tema oscuro (equivalentes hex de [data-theme="dark"] de tokens.css)
D = {
    "ok": "#4ecf8c", "warn": "#f0c060", "crit": "#e8647a",
    "none": "#8890a0", "accent": "#6b96f0",
    "ok_bg": "#1a3028", "ok_border": "#1f4534", "ok_text": "#72e0a8",
    "warn_bg": "#2e2415", "warn_border": "#4c3c20", "warn_text": "#f5cd72",
    "crit_bg": "#2e181e", "crit_border": "#4c2830", "crit_text": "#f09aaa",
    "none_bg": "#222838", "none_border": "#303848", "none_text": "#a8b0c4",
    "bg": "#171c2a", "bg_subtle": "#1b2030", "bg_muted": "#202636",
    "surface": "#1d2235", "surface_alt": "#22283e",
    "border": "#2c3450", "border_strong": "#374058", "divider": "#252c42",
    "text": "#eef0f6", "text2": "#b8c0d2", "text3": "#8890a8", "text4": "#5e6680",
    "grid": "#252c42", "axis": "#374058",
}

def _p(key: str) -> str:
    """Color del tema activo para la clave dada."""
    return D[key] if _dark else C[key]


# ---------------------------------------------------------------------------
# Plotly template global
# ---------------------------------------------------------------------------
def _register_plotly() -> None:
    for name, palette in (("data_dashboard_light", C), ("data_dashboard_dark", D)):
        pio.templates[name] = go.layout.Template(
            layout=go.Layout(
                font=dict(family="Space Grotesk, system-ui, sans-serif",
                          size=12, color=palette["text"]),
                paper_bgcolor=palette["surface"],
                plot_bgcolor=palette["surface"],
                colorway=[palette["accent"], palette["ok"], palette["warn"], palette["crit"]],
                xaxis=dict(gridcolor=palette["grid"], zerolinecolor=palette["divider"],
                           linecolor=palette["border"], ticks="outside", ticklen=4),
                yaxis=dict(gridcolor=palette["grid"], zerolinecolor=palette["divider"],
                           linecolor=palette["border"], ticks="outside", ticklen=4),
                margin=dict(l=48, r=16, t=24, b=40),
                hoverlabel=dict(bgcolor=palette["text"], font_color=palette["surface"],
                                font_family="JetBrains Mono, monospace"),
            )
        )

_register_plotly()

def apply_plotly_theme() -> None:
    pio.templates.default = "data_dashboard_dark" if _dark else "data_dashboard_light"


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
# Helpers HTML — todos emiten <div class="dd [dark]"> para que el CSS
# gestione el tema sin condicionales en Python
# ---------------------------------------------------------------------------

def badge_html(estado, sin_datos: bool = False) -> str:
    key = None if sin_datos else estado
    sk, icon, label = _SM.get(key, _SM[None])
    return (
        f'<span class="dd-badge {sk}">'
        f'<span class="dd-bi">{icon}</span>{label}</span>'
    )


def _ring_svg(pct: float | None, sk: str) -> str:
    R = 28
    circ = 2 * math.pi * R  # ≈ 175.93
    offset = circ - (min(float(pct or 0), 100) / 100) * circ
    return (
        f'<svg width="72" height="72" viewBox="0 0 72 72" style="flex-shrink:0">'
        f'<circle class="ring-track" cx="36" cy="36" r="{R}" fill="none" stroke-width="4"/>'
        f'<circle class="ring-fill {sk}" cx="36" cy="36" r="{R}" fill="none" stroke-width="4"'
        f' stroke-dasharray="{circ:.2f}" stroke-dashoffset="{offset:.2f}"'
        f' transform="rotate(-90 36 36)" stroke-linecap="round"/>'
        f'</svg>'
    )


def kpi_strip_html(total: int, ok: int, warn: int, crit: int) -> str:
    return f"""<div class="{_dd()}"><div class="kpi-strip">
  <div class="kpi">
    <div class="kpi-label">TOTAL PROYECTOS</div>
    <div class="kpi-value">{total}</div>
    <div class="kpi-delta">pipelines activos</div>
  </div>
  <div class="kpi accent-ok">
    <div class="kpi-label"><span class="icon-ok">✓</span>&nbsp;OK</div>
    <div class="kpi-value">{ok}<span class="kpi-unit">/ {total}</span></div>
    <div class="kpi-delta kpi-delta-up">operativos</div>
  </div>
  <div class="kpi accent-warn">
    <div class="kpi-label"><span class="icon-warn">!</span>&nbsp;REGULAR</div>
    <div class="kpi-value">{warn}<span class="kpi-unit">/ {total}</span></div>
    <div class="kpi-delta">degradados</div>
  </div>
  <div class="kpi accent-crit">
    <div class="kpi-label"><span class="icon-crit">×</span>&nbsp;CRÍTICO</div>
    <div class="kpi-value">{crit}<span class="kpi-unit">/ {total}</span></div>
    <div class="kpi-delta kpi-delta-down">requieren atención</div>
  </div>
</div></div>"""


def day_kpi_strip_html(ejecuciones: int, proyectos: int, total_proy: int,
                       pct_ok: float, total_proc: int) -> str:
    return f"""<div class="{_dd()}"><div class="kpi-strip">
  <div class="kpi">
    <div class="kpi-label">EJECUCIONES HOY</div>
    <div class="kpi-value">{ejecuciones:,}</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">PROYECTOS ACTIVOS</div>
    <div class="kpi-value">{proyectos}<span class="kpi-unit">/ {total_proy}</span></div>
  </div>
  <div class="kpi accent-ok">
    <div class="kpi-label"><span class="icon-ok">✓</span>&nbsp;% OK MEDIO</div>
    <div class="kpi-value">{pct_ok:.1f}<span class="kpi-unit">%</span></div>
  </div>
  <div class="kpi">
    <div class="kpi-label">TOTAL PROCESOS</div>
    <div class="kpi-value">{total_proc:,}</div>
  </div>
</div></div>"""


def project_card_html(proyecto: str, grupo: str, estado, sin_datos: bool,
                      xok, dt_str: str) -> str:
    """Variant C: anillo prominente con % OK, fiel al diseño."""
    sk = status_key(None if sin_datos else estado)
    xok_str = f"{xok:.1f}%" if xok is not None and not sin_datos else "—"
    bdg = badge_html(estado, sin_datos)
    ring = _ring_svg(xok, sk)
    return f"""<div class="{_dd()}"><div class="pcard pcard-c {sk}">
  <div class="pcard-c-head">
    <div class="pcard-cat">Grupo {grupo}</div>
    {bdg}
  </div>
  <div class="pcard-c-body">
    {ring}
    <div class="pcard-c-text">
      <div class="pcard-name">{proyecto}</div>
      <div class="pcard-c-big mono">{xok_str}</div>
      <div class="pcard-c-sub mono">↻ {dt_str}</div>
    </div>
  </div>
</div></div>"""


def attention_items_html(items: list) -> str:
    rows = "".join(
        f'<div class="attention-item">{bdg}'
        f'<span class="name">{name}</span>'
        f'<span class="reason">{reason}</span>'
        f'<span class="time mono">{ts}</span></div>'
        for bdg, name, reason, ts in items
    )
    if not rows:
        rows = f'<div class="attn-empty">Todos los pipelines están OK</div>'
    return f'<div class="{_dd()}"><div class="panel"><div class="panel-header"><h3>Requieren atención</h3><span class="subtitle">{len(items)} proyectos</span></div><div class="panel-body no-pad">{rows}</div></div></div>'


def panel_html(title: str, subtitle: str, body_html: str, no_pad: bool = False) -> str:
    cls = "panel-body no-pad" if no_pad else "panel-body"
    return (
        f'<div class="{_dd()}"><div class="panel">'
        f'<div class="panel-header"><h3>{title}</h3>'
        f'<span class="subtitle">{subtitle}</span></div>'
        f'<div class="{cls}">{body_html}</div>'
        f'</div></div>'
    )


def section_title_html(text: str, sub: str = "") -> str:
    sub_html = f'<span class="section-sub">{sub}</span>' if sub else ""
    return f'<div class="{_dd()}"><div class="section-title">{text}{sub_html}</div></div>'


def mini_grid_html(stats: list, cols: int = 3) -> str:
    cells = "".join(
        f'<div class="mini-stat {rest[0] if rest else ""}">'
        f'<div class="mini-stat-label">{label}</div>'
        f'<div class="mini-stat-value mono">{value}</div></div>'
        for label, value, *rest in stats
    )
    return (
        f'<div class="{_dd()}"><div class="mini-grid" '
        f'style="grid-template-columns:repeat({cols},1fr)">{cells}</div></div>'
    )


# ---------------------------------------------------------------------------
# CSS — ambos temas en un bloque. El tema se activa añadiendo .dark a .dd
# ---------------------------------------------------------------------------
_CSS_BASE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stSidebar"],
.stMarkdown,.stMarkdown p,.stMarkdown div,h1,h2,h3,h4,p,label,button,input,select{
  font-family:'Space Grotesk',system-ui,sans-serif!important;
}
.block-container{padding-top:1.5rem!important;max-width:1600px!important;}
#MainMenu,footer{visibility:hidden!important;}
.stMarkdown{margin-bottom:0!important;}
.element-container{margin-bottom:6px!important;}

/* ===== Tema claro (Streamlit chrome) ===== */
.stApp-light{background:#f9fafb!important;}
[data-testid="stSidebar"].light > div:first-child{
  background:#ffffff!important;border-right:1px solid #e5e7eb!important;
}

/* ===== Tema oscuro (Streamlit chrome) ===== */
.stApp-dark{background:#171c2a!important;color:#eef0f6!important;}
[data-testid="stSidebar"].dark > div:first-child{
  background:#1d2235!important;border-right:1px solid #2c3450!important;
}
[data-testid="stSidebar"].dark label,
[data-testid="stSidebar"].dark .stRadio label{color:#eef0f6!important;}
[data-testid="stSidebar"].dark p,
[data-testid="stSidebar"].dark span{color:#8890a8!important;}

/* ===== Componentes .dd ===== */

/* -- Badge -- */
.dd .dd-badge{
  display:inline-flex;align-items:center;gap:5px;
  padding:2px 8px 2px 6px;font-size:11px;font-weight:600;
  letter-spacing:0.02em;text-transform:uppercase;
  border-radius:999px;border:1px solid;white-space:nowrap;line-height:1.4;
  font-family:'JetBrains Mono',monospace;
}
.dd .dd-bi{font-size:10px;line-height:1;}
/* light */
.dd .dd-badge.ok  {background:#edf7f1;color:#1d6b46;border-color:#a8d9bf;}
.dd .dd-badge.warn{background:#fdf6e3;color:#8a6000;border-color:#e8cc80;}
.dd .dd-badge.crit{background:#fdf0f1;color:#8a1f30;border-color:#e8a0ab;}
.dd .dd-badge.none{background:#f5f6f7;color:#555a60;border-color:#c8ccd0;}
/* dark */
.dd.dark .dd-badge.ok  {background:#1a3028;color:#72e0a8;border-color:#1f4534;}
.dd.dark .dd-badge.warn{background:#2e2415;color:#f5cd72;border-color:#4c3c20;}
.dd.dark .dd-badge.crit{background:#2e181e;color:#f09aaa;border-color:#4c2830;}
.dd.dark .dd-badge.none{background:#222838;color:#a8b0c4;border-color:#303848;}

/* -- KPI strip -- */
.dd .kpi-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:4px;}
.dd .kpi{
  background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;
  padding:16px;display:flex;flex-direction:column;gap:8px;
  position:relative;overflow:hidden;
}
.dd.dark .kpi{background:#1d2235;border-color:#2c3450;}
.dd .kpi::before{
  content:'';position:absolute;left:0;top:0;bottom:0;width:3px;border-radius:2px 0 0 2px;
}
.dd .kpi.accent-ok::before  {background:#39b577;}
.dd .kpi.accent-warn::before{background:#d9a441;}
.dd .kpi.accent-crit::before{background:#d14a5b;}
.dd.dark .kpi.accent-ok::before  {background:#4ecf8c;}
.dd.dark .kpi.accent-warn::before{background:#f0c060;}
.dd.dark .kpi.accent-crit::before{background:#e8647a;}
.dd .kpi-label{
  font-size:10px;font-weight:600;color:#8a909a;text-transform:uppercase;
  letter-spacing:0.08em;font-family:'JetBrains Mono',monospace;
  display:flex;align-items:center;gap:6px;
}
.dd.dark .kpi-label{color:#8890a8;}
.dd .kpi-value{
  font-size:32px;font-weight:600;letter-spacing:-0.03em;line-height:1;
  font-variant-numeric:tabular-nums;color:#1a2330;
  display:flex;align-items:baseline;gap:6px;
}
.dd.dark .kpi-value{color:#eef0f6;}
.dd .kpi-unit{font-size:14px;font-weight:500;color:#8a909a;letter-spacing:0;}
.dd.dark .kpi-unit{color:#8890a8;}
.dd .kpi-delta{font-size:11px;color:#8a909a;font-family:'JetBrains Mono',monospace;}
.dd.dark .kpi-delta{color:#8890a8;}
.dd .kpi-delta-down{color:#d14a5b!important;}
.dd .kpi-delta-up  {color:#39b577!important;}
.dd.dark .kpi-delta-down{color:#e8647a!important;}
.dd.dark .kpi-delta-up  {color:#4ecf8c!important;}
.dd .icon-ok {color:#39b577;}
.dd .icon-warn{color:#d9a441;}
.dd .icon-crit{color:#d14a5b;}
.dd.dark .icon-ok {color:#4ecf8c;}
.dd.dark .icon-warn{color:#f0c060;}
.dd.dark .icon-crit{color:#e8647a;}

/* -- Project card (Variant C — anillo) -- */
.dd .pcard{
  background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;
  overflow:hidden;box-shadow:0 1px 2px rgba(26,35,48,0.05);
  transition:border-color 120ms,box-shadow 120ms;margin-bottom:4px;
}
.dd.dark .pcard{background:#1d2235;border-color:#2c3450;box-shadow:none;}
.dd .pcard:hover{border-color:#d1d5db;box-shadow:0 2px 8px rgba(26,35,48,0.08);}
.dd.dark .pcard:hover{border-color:#374058;}
.dd .pcard.ok  {border-color:#a8d9bf;}
.dd .pcard.warn{border-color:#e8cc80;}
.dd .pcard.crit{border-color:#e8a0ab;}
.dd.dark .pcard.ok  {border-color:#1f4534;}
.dd.dark .pcard.warn{border-color:#4c3c20;}
.dd.dark .pcard.crit{border-color:#4c2830;}
.dd .pcard-c{padding:16px;display:flex;flex-direction:column;gap:14px;min-height:150px;}
.dd .pcard-c-head{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;}
.dd .pcard-c-body{display:flex;align-items:center;gap:14px;}
.dd .pcard-c-text{display:flex;flex-direction:column;gap:3px;min-width:0;}
.dd .pcard-cat{
  font-size:10px;font-weight:500;color:#8a909a;
  font-family:'JetBrains Mono',monospace;
  text-transform:uppercase;letter-spacing:0.08em;margin-bottom:3px;
}
.dd.dark .pcard-cat{color:#8890a8;}
.dd .pcard-name{font-size:13px;font-weight:600;color:#1a2330;letter-spacing:-0.01em;line-height:1.2;}
.dd.dark .pcard-name{color:#eef0f6;}
.dd .pcard-c-big{
  font-size:22px;font-weight:600;letter-spacing:-0.025em;color:#1a2330;line-height:1.1;
  font-variant-numeric:tabular-nums;
}
.dd.dark .pcard-c-big{color:#eef0f6;}
.dd .pcard-c-sub{font-size:10px;color:#8a909a;}
.dd.dark .pcard-c-sub{color:#8890a8;}

/* Ring SVG — colores via CSS */
.dd .ring-track{stroke:#eff0f3;}
.dd.dark .ring-track{stroke:#2c3450;}
.dd .ring-fill.ok  {stroke:#39b577;}
.dd .ring-fill.warn{stroke:#d9a441;}
.dd .ring-fill.crit{stroke:#d14a5b;}
.dd .ring-fill.none{stroke:#8a8f96;}
.dd.dark .ring-fill.ok  {stroke:#4ecf8c;}
.dd.dark .ring-fill.warn{stroke:#f0c060;}
.dd.dark .ring-fill.crit{stroke:#e8647a;}
.dd.dark .ring-fill.none{stroke:#8890a0;}

/* -- Panel -- */
.dd .panel{background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.dd.dark .panel{background:#1d2235;border-color:#2c3450;}
.dd .panel-header{
  padding:12px 16px;border-bottom:1px solid #eef0f3;
  display:flex;align-items:center;gap:12px;
}
.dd.dark .panel-header{border-bottom-color:#252c42;}
.dd .panel-header h3{margin:0;font-size:13px;font-weight:600;color:#1a2330;letter-spacing:-0.005em;}
.dd.dark .panel-header h3{color:#eef0f6;}
.dd .panel-header .subtitle{font-size:11px;color:#8a909a;font-family:'JetBrains Mono',monospace;}
.dd.dark .panel-header .subtitle{color:#8890a8;}
.dd .panel-body{padding:16px;}
.dd .panel-body.no-pad{padding:0;}

/* -- Section title -- */
.dd .section-title{
  font-size:11px;font-weight:600;color:#8a909a;text-transform:uppercase;
  letter-spacing:0.1em;font-family:'JetBrains Mono',monospace;
  margin:8px 0;display:flex;align-items:center;gap:8px;
}
.dd.dark .section-title{color:#8890a8;}
.dd .section-title::after{content:'';flex:1;height:1px;background:#eef0f3;}
.dd.dark .section-title::after{background:#252c42;}
.dd .section-sub{
  color:#b0b5bc;font-weight:500;text-transform:none;
  letter-spacing:0;font-size:11px;
}
.dd.dark .section-sub{color:#5e6680;}

/* -- Attention list -- */
.dd .attention-item{
  display:flex;align-items:center;gap:12px;
  padding:10px 16px;border-bottom:1px solid #eef0f3;font-size:12px;
}
.dd.dark .attention-item{border-bottom-color:#252c42;}
.dd .attention-item:last-child{border-bottom:none;}
.dd .attention-item .name{font-weight:600;color:#1a2330;}
.dd.dark .attention-item .name{color:#eef0f6;}
.dd .attention-item .reason{color:#8a909a;flex:1;}
.dd.dark .attention-item .reason{color:#8890a8;}
.dd .attention-item .time{font-family:'JetBrains Mono',monospace;font-size:11px;color:#8a909a;}
.dd.dark .attention-item .time{color:#8890a8;}
.dd .attn-empty{padding:24px;text-align:center;color:#8a909a;font-size:12px;}
.dd.dark .attn-empty{color:#8890a8;}

/* -- Mini grid -- */
.dd .mini-grid{
  display:grid;gap:1px;background:#eef0f3;
  border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;
}
.dd.dark .mini-grid{background:#252c42;border-color:#2c3450;}
.dd .mini-stat{background:#ffffff;padding:12px 14px;display:flex;flex-direction:column;gap:4px;}
.dd.dark .mini-stat{background:#1d2235;}
.dd .mini-stat-label{
  font-size:9px;font-weight:600;color:#8a909a;
  font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:0.07em;
}
.dd.dark .mini-stat-label{color:#8890a8;}
.dd .mini-stat-value{
  font-size:22px;font-weight:600;letter-spacing:-0.02em;
  font-variant-numeric:tabular-nums;color:#1a2330;line-height:1.1;
}
.dd.dark .mini-stat-value{color:#eef0f6;}
.dd .mini-stat.ok   .mini-stat-value{color:#1d6b46;}
.dd .mini-stat.warn .mini-stat-value{color:#8a6000;}
.dd .mini-stat.crit .mini-stat-value{color:#8a1f30;}
.dd.dark .mini-stat.ok   .mini-stat-value{color:#72e0a8;}
.dd.dark .mini-stat.warn .mini-stat-value{color:#f5cd72;}
.dd.dark .mini-stat.crit .mini-stat-value{color:#f09aaa;}

/* -- Util -- */
.dd .mono{font-family:'JetBrains Mono',monospace!important;}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS_BASE, unsafe_allow_html=True)

    # Clases dinámicas en el chrome de Streamlit según tema
    theme = "dark" if _dark else "light"
    bg    = D["bg"] if _dark else C["bg"]
    text  = D["text"] if _dark else C["text"]
    text3 = D["text3"] if _dark else C["text3"]
    st.markdown(
        f"""<style>
.stApp{{background:{bg}!important;}}
h1,h2,h3,h4,h5,h6,.stMarkdown h1,.stMarkdown h2,.stMarkdown h3{{color:{text}!important;}}
.stMarkdown p,.stMarkdown span{{color:{text3};}}
[data-testid="stSidebar"]>div:first-child{{
  background:{"#1d2235" if _dark else "#ffffff"}!important;
  border-right:1px solid {"#2c3450" if _dark else "#e5e7eb"}!important;
}}
[data-testid="stSidebar"] *{{color:{"#b8c0d2" if _dark else "inherit"}!important;}}
[data-testid="stSidebar"] .stImage img{{filter:{"brightness(0.9)" if _dark else "none"};}}
</style>""",
        unsafe_allow_html=True,
    )

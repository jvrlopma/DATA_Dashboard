"""Sistema de diseño DATA Dashboard — temas claro y oscuro, paleta Aqualia/Stitch."""

import math
import json as _json
import streamlit as st
import plotly.io as pio
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Paletas de color — extraídas del diseño Stitch / Aqualia spec
# ---------------------------------------------------------------------------
C_LIGHT: dict = {
    "ok":   "#22C55E", "warn": "#F59E0B", "crit": "#EF4444", "none": "#94A3B8",
    "ok_bg":    "#f0fdf4", "ok_border":    "#bbf7d0", "ok_text":    "#15803d",
    "warn_bg":  "#fffbeb", "warn_border":  "#fde68a", "warn_text":  "#b45309",
    "crit_bg":  "#fef2f2", "crit_border":  "#fecaca", "crit_text":  "#dc2626",
    "none_bg":  "#f8fafc", "none_border":  "#e2e8f0", "none_text":  "#64748b",
    "accent":   "#005791", "accent_bg":    "#e6f0ff",
    "bg":         "#f8f9ff",
    "bg_subtle":  "#f1f3fa",
    "bg_muted":   "#eceef4",
    "surface":    "#ffffff",
    "surface_alt":"#f1f3fa",
    "border":     "#e2e8f0",
    "border_strong": "#c0c7d2",
    "divider":    "#f1f3fa",
    "text":       "#1e293b",
    "text2":      "#64748b",
    "text3":      "#94a3b8",
    "text4":      "#cbd5e1",
    "grid":       "#f1f3fa",
    "axis":       "#e2e8f0",
}

C_DARK: dict = {
    "ok":   "#22C55E", "warn": "#F59E0B", "crit": "#EF4444", "none": "#94A3B8",
    "ok_bg":    "#052e16", "ok_border":    "#14532d", "ok_text":    "#86efac",
    "warn_bg":  "#451a03", "warn_border":  "#78350f", "warn_text":  "#fcd34d",
    "crit_bg":  "#450a0a", "crit_border":  "#7f1d1d", "crit_text":  "#fca5a5",
    "none_bg":  "#1e293b", "none_border":  "#334155", "none_text":  "#64748b",
    "accent":   "#9dcaff", "accent_bg":    "#001d35",
    "bg":         "#0f172a",
    "bg_subtle":  "#0f172a",
    "bg_muted":   "#162032",
    "surface":    "#1e293b",
    "surface_alt":"#162032",
    "border":     "#334155",
    "border_strong": "#475569",
    "divider":    "#1e293b",
    "text":       "#f1f5f9",
    "text2":      "#94a3b8",
    "text3":      "#64748b",
    "text4":      "#475569",
    "grid":       "#1e293b",
    "axis":       "#334155",
}

# C es el dict mutable activo — actualizado por inject_css()
C: dict = dict(C_LIGHT)

# ---------------------------------------------------------------------------
# Mapa de estado
# ---------------------------------------------------------------------------
_SM = {
    "OK":      ("ok",   "✓", "OK"),
    "REGULAR": ("warn", "!", "REGULAR"),
    "CRITICO": ("crit", "×", "CRÍTICO"),
    None:      ("none", "·", "SIN DATOS"),
}

def status_key(estado) -> str:
    return _SM.get(estado, _SM[None])[0]

# ---------------------------------------------------------------------------
# Plotly — dos templates: aqualia_light y aqualia_dark
# ---------------------------------------------------------------------------
def _register_plotly() -> None:
    for dark in (False, True):
        c = C_DARK if dark else C_LIGHT
        name = "aqualia_dark" if dark else "aqualia_light"
        pio.templates[name] = go.layout.Template(
            layout=go.Layout(
                font=dict(family="Inter, system-ui, sans-serif",
                          size=11, color=c["text"]),
                paper_bgcolor=c["surface"],
                plot_bgcolor=c["surface"],
                colorway=[c["accent"], c["ok"], c["warn"], c["crit"]],
                xaxis=dict(
                    gridcolor=c["grid"], zerolinecolor=c["grid"],
                    linecolor=c["border"], ticks="outside", ticklen=4,
                    tickfont=dict(family="JetBrains Mono, monospace",
                                  size=10, color=c["text3"]),
                ),
                yaxis=dict(
                    gridcolor=c["grid"], zerolinecolor=c["grid"],
                    linecolor=c["border"], ticks="outside", ticklen=4,
                    tickfont=dict(family="JetBrains Mono, monospace",
                                  size=10, color=c["text3"]),
                ),
                margin=dict(l=44, r=12, t=20, b=32),
                hoverlabel=dict(
                    bgcolor="#f2f4f7" if not dark else "#1e293b",
                    font_color="#1a1f26" if not dark else "#f1f5f9",
                    font_family="JetBrains Mono, monospace",
                ),
            )
        )

_register_plotly()

def apply_plotly_theme(dark: bool = False) -> None:
    pio.templates.default = "aqualia_dark" if dark else "aqualia_light"

# ---------------------------------------------------------------------------
# Helpers HTML
# ---------------------------------------------------------------------------

def badge_html(estado, sin_datos: bool = False) -> str:
    key = None if sin_datos else estado
    sk, icon, label = _SM.get(key, _SM[None])
    return (
        '<span class="dd-badge ' + sk + '">'
        '<span class="dd-bi">' + icon + '</span>' + label + '</span>'
    )


def _ring_svg(pct: float | None, sk: str) -> str:
    R = 28
    circ = 2 * math.pi * R
    offset = circ - (min(float(pct or 0), 100) / 100) * circ
    return (
        '<svg width="72" height="72" viewBox="0 0 72 72" style="flex-shrink:0">'
        '<circle class="ring-track" cx="36" cy="36" r="' + str(R) + '" fill="none" stroke-width="4"/>'
        '<circle class="ring-fill ' + sk + '" cx="36" cy="36" r="' + str(R) + '" fill="none" stroke-width="4"'
        ' stroke-dasharray="' + f'{circ:.2f}' + '" stroke-dashoffset="' + f'{offset:.2f}' + '"'
        ' transform="rotate(-90 36 36)" stroke-linecap="round"/>'
        '</svg>'
    )


def kpi_strip_html(total: int, ok: int, warn: int, crit: int) -> str:
    return (
        '<div class="dd"><div class="kpi-strip">'
        '<div class="kpi"><div class="kpi-label">TOTAL PROYECTOS</div>'
        '<div class="kpi-value">' + str(total) + '</div>'
        '<div class="kpi-delta">pipelines activos</div></div>'
        '<div class="kpi accent-ok"><div class="kpi-label"><span class="icon-ok">&#x2713;</span>&nbsp;OK</div>'
        '<div class="kpi-value">' + str(ok) + '<span class="kpi-unit">/ ' + str(total) + '</span></div>'
        '<div class="kpi-delta kpi-delta-up">operativos</div></div>'
        '<div class="kpi accent-warn"><div class="kpi-label"><span class="icon-warn">!</span>&nbsp;REGULAR</div>'
        '<div class="kpi-value">' + str(warn) + '<span class="kpi-unit">/ ' + str(total) + '</span></div>'
        '<div class="kpi-delta">degradados</div></div>'
        '<div class="kpi accent-crit"><div class="kpi-label"><span class="icon-crit">&#x00D7;</span>&nbsp;CR&#xCD;TICO</div>'
        '<div class="kpi-value">' + str(crit) + '<span class="kpi-unit">/ ' + str(total) + '</span></div>'
        '<div class="kpi-delta kpi-delta-down">requieren atenci&#xF3;n</div></div>'
        '</div></div>'
    )


def day_kpi_strip_html(ejecuciones: int, proyectos: int, total_proy: int,
                       pct_ok: float, total_proc: int) -> str:
    return (
        '<div class="dd"><div class="kpi-strip">'
        '<div class="kpi"><div class="kpi-label">EJECUCIONES HOY</div>'
        '<div class="kpi-value">' + f'{ejecuciones:,}' + '</div></div>'
        '<div class="kpi"><div class="kpi-label">PROYECTOS ACTIVOS</div>'
        '<div class="kpi-value">' + str(proyectos) + '<span class="kpi-unit">/ ' + str(total_proy) + '</span></div></div>'
        '<div class="kpi accent-ok"><div class="kpi-label"><span class="icon-ok">&#x2713;</span>&nbsp;% OK MEDIO</div>'
        '<div class="kpi-value">' + f'{pct_ok:.1f}' + '<span class="kpi-unit">%</span></div></div>'
        '<div class="kpi"><div class="kpi-label">TOTAL PROCESOS</div>'
        '<div class="kpi-value">' + f'{total_proc:,}' + '</div></div>'
        '</div></div>'
    )


def project_card_html(proyecto: str, grupo: str, estado, sin_datos: bool,
                      xok, dt_str: str) -> str:
    sk = status_key(None if sin_datos else estado)
    xok_str = f"{xok:.1f}%" if xok is not None and not sin_datos else "&#x2014;"
    bdg = badge_html(estado, sin_datos)
    ring = _ring_svg(xok, sk)
    return (
        '<div class="dd"><div class="pcard pcard-c ' + sk + '">'
        '<div class="pcard-c-head">'
        '<div class="pcard-cat">Grupo ' + str(grupo) + '</div>'
        + bdg +
        '</div>'
        '<div class="pcard-c-body">'
        + ring +
        '<div class="pcard-c-text">'
        '<div class="pcard-name">' + proyecto + '</div>'
        '<div class="pcard-c-big mono">' + xok_str + '</div>'
        '<div class="pcard-c-sub mono">&#x21BB; ' + dt_str + '</div>'
        '</div></div></div></div>'
    )


def attention_items_html(items: list) -> str:
    rows = "".join(
        '<div class="attention-item">' + bdg +
        '<span class="name">' + name + '</span>'
        '<span class="reason">' + reason + '</span>'
        '<span class="time mono">' + ts + '</span></div>'
        for bdg, name, reason, ts in items
    )
    if not rows:
        rows = '<div class="attn-empty">Todos los pipelines est&#xE1;n OK</div>'
    n = len(items)
    return (
        '<div class="dd"><div class="panel">'
        '<div class="panel-header"><h3>Requieren atenci&#xF3;n</h3>'
        '<span class="subtitle">' + str(n) + ' proyecto' + ('s' if n != 1 else '') + '</span></div>'
        '<div class="panel-body no-pad">' + rows + '</div>'
        '</div></div>'
    )


def panel_html(title: str, subtitle: str, body_html: str, no_pad: bool = False) -> str:
    cls = "panel-body no-pad" if no_pad else "panel-body"
    return (
        '<div class="dd"><div class="panel">'
        '<div class="panel-header"><h3>' + title + '</h3>'
        '<span class="subtitle">' + subtitle + '</span></div>'
        '<div class="' + cls + '">' + body_html + '</div>'
        '</div></div>'
    )


def section_title_html(text: str, sub: str = "") -> str:
    sub_html = '<span class="section-sub">' + sub + '</span>' if sub else ""
    return (
        '<div class="dd"><div class="section-title">'
        + text + sub_html +
        '</div></div>'
    )


def mini_grid_html(stats: list, cols: int = 3) -> str:
    cells = "".join(
        '<div class="mini-stat ' + (rest[0] if rest else "") + '">'
        '<div class="mini-stat-label">' + str(label) + '</div>'
        '<div class="mini-stat-value mono">' + str(value) + '</div></div>'
        for label, value, *rest in stats
    )
    return (
        '<div class="dd"><div class="mini-grid" '
        'style="grid-template-columns:repeat(' + str(cols) + ',1fr)">'
        + cells +
        '</div></div>'
    )

# ---------------------------------------------------------------------------
# CSS — usa CSS custom properties para soporte de temas
# ---------------------------------------------------------------------------
_CSS_RULES = """
/* ===== Tokens — Tema claro (defecto) ===== */
:root {
  --dd-bg:          #f8f9ff;
  --dd-surface:     #ffffff;
  --dd-surface-low: #f1f3fa;
  --dd-surface-med: #eceef4;
  --dd-border:      #e2e8f0;
  --dd-border-str:  #c0c7d2;
  --dd-divider:     #f1f3fa;
  --dd-text:        #1e293b;
  --dd-text2:       #64748b;
  --dd-text3:       #94a3b8;
  --dd-text4:       #cbd5e1;
  --dd-accent:      #005791;
  --dd-accent-bg:   #e6f0ff;

  --dd-ok:          #22C55E;
  --dd-ok-bg:       #f0fdf4;
  --dd-ok-brd:      #bbf7d0;
  --dd-ok-txt:      #15803d;

  --dd-warn:        #F59E0B;
  --dd-warn-bg:     #fffbeb;
  --dd-warn-brd:    #fde68a;
  --dd-warn-txt:    #b45309;

  --dd-crit:        #EF4444;
  --dd-crit-bg:     #fef2f2;
  --dd-crit-brd:    #fecaca;
  --dd-crit-txt:    #dc2626;

  --dd-none:        #94A3B8;
  --dd-none-bg:     #f8fafc;
  --dd-none-brd:    #e2e8f0;
  --dd-none-txt:    #64748b;

  --dd-shadow:     0 1px 3px rgba(0,0,0,0.08),0 1px 2px rgba(0,0,0,0.04);
  --dd-shadow-md:  0 4px 6px -1px rgba(0,0,0,0.08),0 2px 4px -1px rgba(0,0,0,0.04);
  --dd-radius:     8px;
  --dd-radius-sm:  6px;
  --dd-radius-pill:9999px;
}

/* ===== Tokens — Tema oscuro ===== */
body.dd-dark {
  --dd-bg:          #0f172a;
  --dd-surface:     #1e293b;
  --dd-surface-low: #0f172a;
  --dd-surface-med: #162032;
  --dd-border:      #334155;
  --dd-border-str:  #475569;
  --dd-divider:     #1e293b;
  --dd-text:        #f1f5f9;
  --dd-text2:       #94a3b8;
  --dd-text3:       #64748b;
  --dd-text4:       #475569;
  --dd-accent:      #9dcaff;
  --dd-accent-bg:   #001d35;

  --dd-ok:          #22C55E;
  --dd-ok-bg:       #052e16;
  --dd-ok-brd:      #14532d;
  --dd-ok-txt:      #86efac;

  --dd-warn:        #F59E0B;
  --dd-warn-bg:     #451a03;
  --dd-warn-brd:    #78350f;
  --dd-warn-txt:    #fcd34d;

  --dd-crit:        #EF4444;
  --dd-crit-bg:     #450a0a;
  --dd-crit-brd:    #7f1d1d;
  --dd-crit-txt:    #fca5a5;

  --dd-none:        #94A3B8;
  --dd-none-bg:     #1e293b;
  --dd-none-brd:    #334155;
  --dd-none-txt:    #64748b;

  --dd-shadow:     0 1px 3px rgba(0,0,0,0.3),0 1px 2px rgba(0,0,0,0.2);
  --dd-shadow-md:  0 4px 6px -1px rgba(0,0,0,0.35),0 2px 4px -1px rgba(0,0,0,0.25);
}

/* ===== Streamlit: app y sidebar ===== */
.stApp, [data-testid="stAppViewContainer"] {
  background: var(--dd-bg) !important;
}
[data-testid="stSidebar"] > div:first-child {
  background: var(--dd-surface) !important;
  border-right: 1px solid var(--dd-border) !important;
}
[data-testid="stSidebar"] * { color: var(--dd-text2) !important; }
[data-testid="stSidebar"] strong, [data-testid="stSidebar"] b { color: var(--dd-text) !important; }
[data-testid="stSidebar"] .stRadio label { color: var(--dd-text) !important; }

/* Dark: forzar overrides sobre base light de Streamlit */
body.dd-dark section.main,
body.dd-dark [data-testid="stMain"],
body.dd-dark [data-testid="stMainBlockContainer"] {
  background: var(--dd-bg) !important;
}
body.dd-dark .stMarkdown p,
body.dd-dark .stMarkdown span,
body.dd-dark .stMarkdown div { color: var(--dd-text) !important; }
body.dd-dark h1, body.dd-dark h2, body.dd-dark h3,
body.dd-dark h4, body.dd-dark h5, body.dd-dark h6 { color: var(--dd-text) !important; }
body.dd-dark label { color: var(--dd-text2) !important; }
body.dd-dark p { color: var(--dd-text) !important; }
body.dd-dark input {
  background: var(--dd-surface-low) !important;
  color: var(--dd-text) !important;
  border-color: var(--dd-border) !important;
}
body.dd-dark [data-baseweb="select"] > div { background: var(--dd-surface-low) !important; }
body.dd-dark [data-baseweb="select"] * { color: var(--dd-text) !important; }
body.dd-dark hr { border-color: var(--dd-border) !important; }
body.dd-dark [data-testid="stCaptionContainer"] * { color: var(--dd-text3) !important; }
body.dd-dark [data-testid="stToggle"] p { color: var(--dd-text2) !important; }
body.dd-dark [data-testid="stRadio"] label span { color: var(--dd-text2) !important; }

/* ===== Tipografía ===== */
html, body, .stApp, * { font-family: 'Inter', system-ui, sans-serif; }
.stMarkdown, .stMarkdown p, .stMarkdown div { color: var(--dd-text) !important; }
h1,h2,h3,h4,h5,h6 { color: var(--dd-text) !important; }

/* ===== Layout full-width ===== */
.block-container {
  padding-top: 1.2rem !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
  max-width: 100% !important;
  width: 100% !important;
}
[data-testid="stAppViewBlockContainer"] {
  max-width: 100% !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
}
#MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden !important; display: none !important; }
.stMarkdown { margin-bottom: 0 !important; }
.element-container { margin-bottom: 6px !important; }

/* ===== Widgets ===== */
[data-testid="stDateInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] {
  background: var(--dd-surface-low) !important;
  border-color: var(--dd-border) !important;
  color: var(--dd-text) !important;
}
.stButton button {
  background: var(--dd-surface-low) !important;
  border: 1px solid var(--dd-border) !important;
  color: var(--dd-text) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 12px !important;
  border-radius: var(--dd-radius-sm) !important;
}
.stButton button:hover { border-color: var(--dd-border-str) !important; }

/* ===== Tabs ===== */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid var(--dd-divider) !important;
  gap: 0 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--dd-text3) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
  padding: 6px 14px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
  color: var(--dd-text) !important;
  border-bottom: 2px solid var(--dd-accent) !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }

/* ===== Columnas igual altura ===== */
[data-testid="stHorizontalBlock"] { align-items: stretch !important; }
[data-testid="stHorizontalBlock"] > div {
  display: flex !important;
  flex-direction: column !important;
}
[data-testid="stHorizontalBlock"] > div > [data-testid="stVerticalBlock"] {
  flex: 1 !important;
  display: flex !important;
  flex-direction: column !important;
}
.dd .panel { height: 100%; display: flex; flex-direction: column; }
.dd .panel-body { flex: 1; overflow-y: auto; }

/* ===== Componentes .dd ===== */

/* Badge */
.dd .dd-badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px 3px 7px; font-size: 11px; font-weight: 700;
  letter-spacing: 0.04em; text-transform: uppercase;
  border-radius: var(--dd-radius-pill); border: 1px solid;
  white-space: nowrap; line-height: 1.4; font-family: 'Inter', sans-serif;
}
.dd .dd-bi { font-size: 10px; line-height: 1; }
.dd .dd-badge.ok   { background: var(--dd-ok-bg);   color: var(--dd-ok-txt);   border-color: var(--dd-ok-brd); }
.dd .dd-badge.warn { background: var(--dd-warn-bg); color: var(--dd-warn-txt); border-color: var(--dd-warn-brd); }
.dd .dd-badge.crit { background: var(--dd-crit-bg); color: var(--dd-crit-txt); border-color: var(--dd-crit-brd); }
.dd .dd-badge.none { background: var(--dd-none-bg); color: var(--dd-none-txt); border-color: var(--dd-none-brd); }

/* KPI strip */
.dd .kpi-strip {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 4px;
}
.dd .kpi {
  background: var(--dd-surface); border: 1px solid var(--dd-border);
  border-radius: var(--dd-radius); padding: 12px 14px;
  display: flex; flex-direction: column; gap: 6px;
  position: relative; overflow: hidden; box-shadow: var(--dd-shadow);
}
.dd .kpi::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0;
  width: 4px; border-radius: 2px 0 0 2px;
}
.dd .kpi.accent-ok::before   { background: #22C55E; }
.dd .kpi.accent-warn::before  { background: #F59E0B; }
.dd .kpi.accent-crit::before  { background: #EF4444; }
.dd .kpi-label {
  font-size: 11px; font-weight: 700; color: var(--dd-text3); text-transform: uppercase;
  letter-spacing: 0.06em; font-family: 'Inter', sans-serif;
  display: flex; align-items: center; gap: 5px;
}
.dd .kpi-value {
  font-size: 28px; font-weight: 700; letter-spacing: -0.03em; line-height: 1;
  font-variant-numeric: tabular-nums; color: var(--dd-text);
  display: flex; align-items: baseline; gap: 6px;
}
.dd .kpi-unit { font-size: 13px; font-weight: 500; color: var(--dd-text3); }
.dd .kpi-delta { font-size: 11px; color: var(--dd-text3); font-family: 'JetBrains Mono', monospace; }
.dd .kpi-delta-down { color: #EF4444 !important; }
.dd .kpi-delta-up   { color: #22C55E !important; }
.dd .icon-ok   { color: #22C55E; }
.dd .icon-warn { color: #F59E0B; }
.dd .icon-crit { color: #EF4444; }

/* Project card Variant C (ring) */
.dd .pcard {
  background: var(--dd-surface); border: 1px solid var(--dd-border);
  border-radius: var(--dd-radius); overflow: hidden;
  transition: border-color 150ms, box-shadow 150ms, transform 150ms;
  margin-bottom: 4px; box-shadow: var(--dd-shadow);
}
.dd .pcard:hover {
  border-color: var(--dd-border-str);
  box-shadow: var(--dd-shadow-md);
  transform: translateY(-1px);
}
.dd .pcard.ok   { border-left: 4px solid #22C55E; }
.dd .pcard.warn { border-left: 4px solid #F59E0B; }
.dd .pcard.crit { border-left: 4px solid #EF4444; }
.dd .pcard.none { border-left: 4px solid #94A3B8; }
.dd .pcard-c {
  padding: 10px 10px 10px 8px; display: flex; flex-direction: column;
  gap: 10px; min-height: 140px;
}
.dd .pcard-c-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.dd .pcard-c-body { display: flex; align-items: center; gap: 12px; }
.dd .pcard-c-text { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.dd .pcard-cat {
  font-size: 10px; font-weight: 600; color: var(--dd-text3);
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 2px;
}
.dd .pcard-name { font-size: 13px; font-weight: 600; color: var(--dd-text); letter-spacing: -0.01em; line-height: 1.2; }
.dd .pcard-c-big {
  font-size: 20px; font-weight: 700; letter-spacing: -0.025em; color: var(--dd-text);
  line-height: 1.1; font-variant-numeric: tabular-nums;
}
.dd .pcard-c-sub { font-size: 10px; color: var(--dd-text3); }

/* Ring SVG */
.dd .ring-track { stroke: var(--dd-border-str); }
.dd .ring-fill.ok   { stroke: #22C55E; }
.dd .ring-fill.warn { stroke: #F59E0B; }
.dd .ring-fill.crit { stroke: #EF4444; }
.dd .ring-fill.none { stroke: #94A3B8; }

/* Panel */
.dd .panel {
  background: var(--dd-surface); border: 1px solid var(--dd-border);
  border-radius: var(--dd-radius); overflow: hidden; box-shadow: var(--dd-shadow);
}
.dd .panel-header {
  padding: 10px 14px; border-bottom: 1px solid var(--dd-divider);
  display: flex; align-items: center; gap: 12px;
  background: var(--dd-surface);
}
.dd .panel-header h3 {
  margin: 0; font-size: 13px; font-weight: 600; color: var(--dd-text);
  letter-spacing: -0.005em;
}
.dd .panel-header .subtitle {
  font-size: 11px; color: var(--dd-text3); font-family: 'JetBrains Mono', monospace;
}
.dd .panel-body { padding: 10px 14px; background: var(--dd-surface); }
.dd .panel-body.no-pad { padding: 0; }

/* Section title */
.dd .section-title {
  font-size: 10px; font-weight: 700; color: var(--dd-text3); text-transform: uppercase;
  letter-spacing: 0.1em; font-family: 'Inter', sans-serif;
  margin: 6px 0; display: flex; align-items: center; gap: 8px;
}
.dd .section-title::after { content: ''; flex: 1; height: 1px; background: var(--dd-divider); }
.dd .section-sub {
  color: var(--dd-text4); font-weight: 500;
  text-transform: none; letter-spacing: 0; font-size: 11px;
}

/* Attention list */
.dd .attention-item {
  display: flex; align-items: center; gap: 12px;
  padding: 9px 14px; border-bottom: 1px solid var(--dd-divider); font-size: 12px;
  background: var(--dd-surface);
}
.dd .attention-item:last-child { border-bottom: none; }
.dd .attention-item .name { font-weight: 600; color: var(--dd-text); }
.dd .attention-item .reason { color: var(--dd-text3); flex: 1; }
.dd .attention-item .time { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--dd-text3); }
.dd .attn-empty { padding: 20px; text-align: center; color: var(--dd-text3); font-size: 12px; background: var(--dd-surface); }

/* Mini grid */
.dd .mini-grid {
  display: grid; gap: 1px; background: var(--dd-divider);
  border: 1px solid var(--dd-border); border-radius: var(--dd-radius); overflow: hidden;
}
.dd .mini-stat { background: var(--dd-surface); padding: 10px 12px; display: flex; flex-direction: column; gap: 3px; }
.dd .mini-stat-label {
  font-size: 9px; font-weight: 700; color: var(--dd-text3);
  font-family: 'Inter', sans-serif; text-transform: uppercase; letter-spacing: 0.07em;
}
.dd .mini-stat-value {
  font-size: 20px; font-weight: 700; letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums; color: var(--dd-text); line-height: 1.1;
}
.dd .mini-stat.ok   .mini-stat-value { color: var(--dd-ok-txt); }
.dd .mini-stat.warn .mini-stat-value { color: var(--dd-warn-txt); }
.dd .mini-stat.crit .mini-stat-value { color: var(--dd-crit-txt); }

/* Util */
.dd .mono { font-family: 'JetBrains Mono', monospace !important; }
"""

# ---------------------------------------------------------------------------
# Inyección CSS + clase de tema via JavaScript
# ---------------------------------------------------------------------------
def inject_css(dark: bool = False) -> None:
    C.clear()
    C.update(C_DARK if dark else C_LIGHT)

    css_escaped = _json.dumps(_CSS_RULES)
    font_url = (
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700"
        "&family=JetBrains+Mono:wght@400;500;600&display=swap"
    )
    theme_class = "dd-dark" if dark else "dd-light"
    script = (
        "<script>"
        "(function(){"
        "var l=document.getElementById('dd-fonts');"
        "if(!l){"
        "l=document.createElement('link');"
        "l.id='dd-fonts';"
        "l.rel='stylesheet';"
        "l.href='" + font_url + "';"
        "document.head.appendChild(l);}"
        "var old=document.getElementById('dd-styles');"
        "if(old){old.remove();}"
        "var s=document.createElement('style');"
        "s.id='dd-styles';"
        "s.textContent=" + css_escaped + ";"
        "document.head.appendChild(s);"
        "document.body.classList.remove('dd-dark','dd-light');"
        "document.body.classList.add('" + theme_class + "');"
        "})();"
        "</script>"
    )
    st.html(script, unsafe_allow_javascript=True)


# Compatibilidad hacia atrás
def set_dark(dark: bool) -> None:
    C.clear()
    C.update(C_DARK if dark else C_LIGHT)

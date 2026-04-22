"""Sistema de diseño DATA Dashboard — tokens CSS, helpers HTML y colores Plotly.

Basado en el prototipo de Claude Design (Space Grotesk + JetBrains Mono,
paleta oklch moderna con WCAG AA, tarjeta Variant A).
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Colores hex para Plotly (oklch no soportado por Plotly)
# ---------------------------------------------------------------------------
C = {
    "ok":          "#1a9870",
    "warn":        "#c08b12",
    "crit":        "#c82619",
    "none":        "#788390",
    "accent":      "#3558d4",
    "ok_bg":       "#edfaf4",
    "warn_bg":     "#fef8e8",
    "crit_bg":     "#fef0ef",
    "none_bg":     "#f4f5f6",
    "ok_border":   "#7dcdb0",
    "warn_border": "#e8c46a",
    "crit_border": "#e89a95",
    "ok_text":     "#0f6b4d",
    "warn_text":   "#7a5200",
    "crit_text":   "#8a1a12",
    "none_text":   "#5a6170",
    "grid":        "#eaecf0",
    "axis":        "#c5cad0",
}

# ---------------------------------------------------------------------------
# Mapas de estado → CSS / icono / etiqueta
# ---------------------------------------------------------------------------
_STATUS_MAP = {
    "OK":      ("ok",   "✓", "OK"),
    "REGULAR": ("warn", "!", "REGULAR"),
    "CRITICO": ("crit", "×", "CRÍTICO"),
    None:      ("none", "•", "SIN DATOS"),
}


def status_class(estado: str | None) -> str:
    return _STATUS_MAP.get(estado, _STATUS_MAP[None])[0]


def badge_html(estado: str | None, sin_datos: bool = False) -> str:
    key = None if sin_datos else estado
    css, icon, label = _STATUS_MAP.get(key, _STATUS_MAP[None])
    return (
        f'<span class="dd-badge dd-badge-{css}">'
        f'<span class="dd-badge-icon">{icon}</span>{label}</span>'
    )


def kpi_strip_html(total: int, ok: int, warn: int, crit: int) -> str:
    return f"""
<div class="dd-kpi-strip">
  <div class="dd-kpi">
    <div class="dd-kpi-label">TOTAL PROYECTOS</div>
    <div class="dd-kpi-value">{total}</div>
    <div class="dd-kpi-delta">pipelines activos</div>
  </div>
  <div class="dd-kpi dd-kpi-ok">
    <div class="dd-kpi-label"><span class="dd-icon-ok">✓</span>&nbsp;OK</div>
    <div class="dd-kpi-value">{ok}<span class="dd-kpi-unit">/ {total}</span></div>
    <div class="dd-kpi-delta dd-delta-up">operativos</div>
  </div>
  <div class="dd-kpi dd-kpi-warn">
    <div class="dd-kpi-label"><span class="dd-icon-warn">!</span>&nbsp;REGULAR</div>
    <div class="dd-kpi-value">{warn}<span class="dd-kpi-unit">/ {total}</span></div>
    <div class="dd-kpi-delta">degradados</div>
  </div>
  <div class="dd-kpi dd-kpi-crit">
    <div class="dd-kpi-label"><span class="dd-icon-crit">×</span>&nbsp;CRÍTICO</div>
    <div class="dd-kpi-value">{crit}<span class="dd-kpi-unit">/ {total}</span></div>
    <div class="dd-kpi-delta dd-delta-down">requieren atención</div>
  </div>
</div>"""


def project_card_html(proyecto: str, grupo: str, estado: str | None,
                      sin_datos: bool, xok, dt_str: str) -> str:
    css = status_class(None if sin_datos else estado)
    xok_num  = f"{xok:.1f}" if xok is not None else "—"
    xok_pct  = xok if xok is not None else 0
    progress = f'<div class="dd-progress dd-progress-{css}"><span style="width:{min(xok_pct,100):.1f}%"></span></div>'
    badge    = badge_html(estado, sin_datos)
    return f"""
<div class="dd-pcard dd-pcard-{css}">
  <div class="dd-pcard-rail"></div>
  <div class="dd-pcard-body">
    <div class="dd-pcard-head">
      <div>
        <div class="dd-pcard-cat">Grupo {grupo}</div>
        <div class="dd-pcard-name">{proyecto}</div>
      </div>
      {badge}
    </div>
    <div class="dd-pcard-metrics">
      <div class="dd-pcard-metric">
        <div class="dd-metric-label">% OK</div>
        <div class="dd-metric-value">{xok_num}<span class="dd-metric-unit">%</span></div>
      </div>
      <div class="dd-pcard-metric">
        <div class="dd-metric-label">Ult. ejec.</div>
        <div class="dd-metric-value dd-metric-sm dd-mono">{dt_str}</div>
      </div>
    </div>
    <div class="dd-pcard-foot">{progress}</div>
  </div>
</div>"""


def attention_item_html(badge: str, name: str, reason: str, time_str: str) -> str:
    return f"""
<div class="dd-attention">
  {badge}
  <span class="dd-attention-name">{name}</span>
  <span class="dd-attention-reason">{reason}</span>
  <span class="dd-attention-time dd-mono">{time_str}</span>
</div>"""


def mini_stat_html(label: str, value, css_mod: str = "") -> str:
    return f"""
<div class="dd-mini-stat{' ' + css_mod if css_mod else ''}">
  <div class="dd-mini-label">{label}</div>
  <div class="dd-mini-value">{value}</div>
</div>"""


# ---------------------------------------------------------------------------
# Inyección de CSS global
# ---------------------------------------------------------------------------
_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>
/* ===== Tokens ===== */
:root {
  --dd-font:    'Space Grotesk', ui-sans-serif, system-ui, sans-serif;
  --dd-mono:    'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, monospace;

  --dd-bg:       oklch(99% 0.003 240);
  --dd-surface:  oklch(100% 0 0);
  --dd-border:   oklch(92% 0.006 240);
  --dd-divider:  oklch(94% 0.005 240);
  --dd-text:     oklch(20% 0.01 240);
  --dd-text-2:   oklch(42% 0.01 240);
  --dd-text-3:   oklch(58% 0.01 240);
  --dd-text-4:   oklch(72% 0.008 240);

  --dd-ok:       oklch(58% 0.14 155);
  --dd-ok-bg:    oklch(96% 0.03 155);
  --dd-ok-brd:   oklch(85% 0.08 155);
  --dd-ok-txt:   oklch(38% 0.1 155);

  --dd-warn:     oklch(68% 0.14 70);
  --dd-warn-bg:  oklch(96% 0.04 75);
  --dd-warn-brd: oklch(85% 0.1 75);
  --dd-warn-txt: oklch(42% 0.1 60);

  --dd-crit:     oklch(58% 0.18 25);
  --dd-crit-bg:  oklch(96% 0.03 25);
  --dd-crit-brd: oklch(85% 0.08 25);
  --dd-crit-txt: oklch(40% 0.14 25);

  --dd-none:     oklch(58% 0.005 240);
  --dd-none-bg:  oklch(96% 0.003 240);
  --dd-none-brd: oklch(88% 0.005 240);
  --dd-none-txt: oklch(40% 0.005 240);

  --dd-r-sm: 4px; --dd-r-md: 6px; --dd-r-lg: 10px; --dd-r-pill: 999px;
  --dd-shadow: 0 1px 3px oklch(20% 0.01 240 / 0.07), 0 1px 1px oklch(20% 0.01 240 / 0.04);
}

/* ===== Base overrides ===== */
html, body, .stApp, [data-testid="stAppViewContainer"] {
  font-family: var(--dd-font) !important;
  background: var(--dd-bg) !important;
  -webkit-font-smoothing: antialiased;
}
.block-container {
  padding: 1.5rem 2rem 3rem !important;
  max-width: 1600px !important;
}
#MainMenu, footer { visibility: hidden !important; }
header[data-testid="stHeader"] { background: var(--dd-surface) !important; border-bottom: 1px solid var(--dd-border) !important; }

/* ===== Sidebar ===== */
[data-testid="stSidebar"] {
  background: var(--dd-surface) !important;
  border-right: 1px solid var(--dd-border) !important;
}
[data-testid="stSidebar"] > div { padding: 1rem 0.75rem !important; }
[data-testid="stSidebar"] .stRadio > label { display: none; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap: 2px !important; }
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] {
  padding: 7px 10px !important;
  border-radius: var(--dd-r-md) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  color: var(--dd-text-2) !important;
  transition: background 120ms !important;
}
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:hover {
  background: var(--dd-bg) !important;
  color: var(--dd-text) !important;
}

/* ===== DD Badge ===== */
.dd-badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 2px 8px 2px 6px;
  font-size: 11px; font-weight: 600;
  font-family: var(--dd-mono);
  letter-spacing: 0.03em; text-transform: uppercase;
  border-radius: var(--dd-r-pill);
  border: 1px solid; white-space: nowrap; line-height: 1.5;
}
.dd-badge-icon { font-size: 10px; line-height: 1; }
.dd-badge-ok   { background: var(--dd-ok-bg);   color: var(--dd-ok-txt);   border-color: var(--dd-ok-brd); }
.dd-badge-warn { background: var(--dd-warn-bg);  color: var(--dd-warn-txt); border-color: var(--dd-warn-brd); }
.dd-badge-crit { background: var(--dd-crit-bg);  color: var(--dd-crit-txt); border-color: var(--dd-crit-brd); }
.dd-badge-none { background: var(--dd-none-bg);  color: var(--dd-none-txt); border-color: var(--dd-none-brd); }

/* ===== KPI strip ===== */
.dd-kpi-strip {
  display: grid; grid-template-columns: repeat(4,1fr);
  gap: 16px; margin-bottom: 8px;
}
.dd-kpi {
  background: var(--dd-surface);
  border: 1px solid var(--dd-border);
  border-radius: var(--dd-r-lg);
  padding: 16px; position: relative; overflow: hidden;
  display: flex; flex-direction: column; gap: 6px;
}
.dd-kpi::before {
  content: ''; position: absolute;
  left: 0; top: 0; bottom: 0; width: 3px;
}
.dd-kpi-ok::before  { background: var(--dd-ok); }
.dd-kpi-warn::before { background: var(--dd-warn); }
.dd-kpi-crit::before { background: var(--dd-crit); }
.dd-kpi-label {
  font-size: 10px; font-weight: 600; font-family: var(--dd-mono);
  color: var(--dd-text-3); text-transform: uppercase; letter-spacing: 0.1em;
  display: flex; align-items: center; gap: 5px;
}
.dd-kpi-value {
  font-size: 32px; font-weight: 600; letter-spacing: -0.03em;
  line-height: 1; font-variant-numeric: tabular-nums;
  color: var(--dd-text);
  display: flex; align-items: baseline; gap: 6px;
}
.dd-kpi-unit { font-size: 14px; font-weight: 500; color: var(--dd-text-3); letter-spacing: 0; }
.dd-kpi-delta { font-size: 11px; color: var(--dd-text-3); font-family: var(--dd-mono); }
.dd-delta-up   { color: var(--dd-ok); }
.dd-delta-down { color: var(--dd-crit); }
.dd-icon-ok   { color: var(--dd-ok); }
.dd-icon-warn { color: var(--dd-warn); }
.dd-icon-crit { color: var(--dd-crit); }

/* ===== Project card (Variant A) ===== */
.dd-pcard {
  display: grid; grid-template-columns: 3px 1fr;
  background: var(--dd-surface);
  border: 1px solid var(--dd-border);
  border-radius: var(--dd-r-lg);
  overflow: hidden; min-height: 150px;
  box-shadow: var(--dd-shadow);
  transition: border-color 120ms, box-shadow 120ms;
}
.dd-pcard:hover { border-color: oklch(86% 0.008 240); box-shadow: 0 2px 8px oklch(20% 0.01 240 / 0.08); }
.dd-pcard-ok   { border-color: var(--dd-ok-brd); }
.dd-pcard-warn { border-color: var(--dd-warn-brd); }
.dd-pcard-crit { border-color: var(--dd-crit-brd); }
.dd-pcard-rail { }
.dd-pcard-ok   .dd-pcard-rail { background: var(--dd-ok); }
.dd-pcard-warn .dd-pcard-rail { background: var(--dd-warn); }
.dd-pcard-crit .dd-pcard-rail { background: var(--dd-crit); }
.dd-pcard-none .dd-pcard-rail { background: var(--dd-none); }
.dd-pcard-body {
  padding: 16px; display: flex; flex-direction: column; gap: 12px;
}
.dd-pcard-head {
  display: flex; justify-content: space-between; align-items: flex-start; gap: 10px;
}
.dd-pcard-cat {
  font-size: 10px; font-weight: 500; font-family: var(--dd-mono);
  color: var(--dd-text-3); text-transform: uppercase; letter-spacing: 0.08em;
  margin-bottom: 3px;
}
.dd-pcard-name {
  font-size: 13px; font-weight: 600; letter-spacing: -0.01em;
  color: var(--dd-text); line-height: 1.2;
}
.dd-pcard-metrics {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
}
.dd-pcard-metric { display: flex; flex-direction: column; gap: 3px; }
.dd-metric-label {
  font-size: 9px; font-weight: 600; font-family: var(--dd-mono);
  color: var(--dd-text-4); text-transform: uppercase; letter-spacing: 0.1em;
}
.dd-metric-value {
  font-size: 20px; font-weight: 600; letter-spacing: -0.02em;
  color: var(--dd-text); line-height: 1.1;
  display: flex; align-items: baseline; gap: 3px;
}
.dd-metric-unit { font-size: 11px; font-weight: 500; color: var(--dd-text-3); }
.dd-metric-sm   { font-size: 13px !important; }
.dd-pcard-foot  { margin-top: auto; padding-top: 8px; border-top: 1px dashed var(--dd-divider); }

/* ===== Progress bar ===== */
.dd-progress {
  height: 4px; background: oklch(93% 0.005 240);
  border-radius: var(--dd-r-pill); overflow: hidden;
}
.dd-progress > span {
  display: block; height: 100%;
  border-radius: inherit; transition: width 300ms ease;
}
.dd-progress-ok   > span { background: var(--dd-ok); }
.dd-progress-warn > span { background: var(--dd-warn); }
.dd-progress-crit > span { background: var(--dd-crit); }
.dd-progress-none > span { background: var(--dd-none); }

/* ===== Attention list ===== */
.dd-attention {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px; border-bottom: 1px solid var(--dd-divider);
  font-size: 12px;
}
.dd-attention:last-child { border-bottom: none; }
.dd-attention-name   { font-weight: 600; color: var(--dd-text); }
.dd-attention-reason { color: var(--dd-text-3); flex: 1; }
.dd-attention-time   { font-family: var(--dd-mono); font-size: 11px; color: var(--dd-text-3); }

/* ===== Mini stats grid ===== */
.dd-mini-grid {
  display: grid; gap: 1px;
  background: var(--dd-divider);
  border: 1px solid var(--dd-border);
  border-radius: var(--dd-r-md); overflow: hidden;
}
.dd-mini-stat {
  background: var(--dd-surface);
  padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;
}
.dd-mini-label {
  font-size: 10px; font-family: var(--dd-mono); font-weight: 600;
  color: var(--dd-text-3); text-transform: uppercase; letter-spacing: 0.07em;
}
.dd-mini-value {
  font-size: 22px; font-weight: 600; letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums; color: var(--dd-text); line-height: 1.1;
}
.dd-mini-stat-ok   .dd-mini-value { color: var(--dd-ok-txt); }
.dd-mini-stat-warn .dd-mini-value { color: var(--dd-warn-txt); }
.dd-mini-stat-crit .dd-mini-value { color: var(--dd-crit-txt); }

/* ===== Panel (section wrapper) ===== */
.dd-panel {
  background: var(--dd-surface);
  border: 1px solid var(--dd-border);
  border-radius: var(--dd-r-lg); overflow: hidden;
}
.dd-panel-header {
  padding: 12px 16px; border-bottom: 1px solid var(--dd-divider);
  display: flex; align-items: center; gap: 12px;
}
.dd-panel-title { margin: 0; font-size: 13px; font-weight: 600; letter-spacing: -0.005em; color: var(--dd-text); }
.dd-panel-sub   { font-size: 11px; font-family: var(--dd-mono); color: var(--dd-text-3); }
.dd-panel-body  { padding: 16px; }
.dd-panel-body-nopad { padding: 0; }

/* ===== Day KPI strip (Operativa) ===== */
.dd-day-kpis {
  display: grid; grid-template-columns: repeat(4,1fr);
  gap: 12px;
}
.dd-day-kpi {
  background: var(--dd-surface);
  border: 1px solid var(--dd-border);
  border-radius: var(--dd-r-lg);
  padding: 14px 16px;
  display: flex; flex-direction: column; gap: 4px;
}
.dd-day-kpi-label {
  font-size: 10px; font-weight: 600; font-family: var(--dd-mono);
  color: var(--dd-text-3); text-transform: uppercase; letter-spacing: 0.1em;
}
.dd-day-kpi-value {
  font-size: 26px; font-weight: 600; letter-spacing: -0.03em;
  color: var(--dd-text); line-height: 1; font-variant-numeric: tabular-nums;
}

/* ===== Misc ===== */
.dd-mono { font-family: var(--dd-mono) !important; }
.dd-section-title {
  font-size: 11px; font-weight: 600; font-family: var(--dd-mono);
  color: var(--dd-text-3); text-transform: uppercase; letter-spacing: 0.1em;
  margin: 0 0 8px; display: flex; align-items: center; gap: 8px;
}
.dd-section-title::after { content: ''; flex: 1; height: 1px; background: var(--dd-divider); }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

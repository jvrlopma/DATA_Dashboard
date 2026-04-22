"""Sistema de diseño DATA Dashboard.

Colores hex extraídos directamente del design bundle de Claude Design:
  ok=#39b577  warn=#d9a441  crit=#d14a5b  none=#8a8f96  accent=#3b6bd9
"""

import streamlit as st
import plotly.io as pio
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Paleta de colores — exactos del design bundle (screen-specs.jsx)
# ---------------------------------------------------------------------------
C = {
    # Colores de estado (para Plotly y estilos inline)
    "ok":          "#39b577",
    "warn":        "#d9a441",
    "crit":        "#d14a5b",
    "none":        "#8a8f96",
    "accent":      "#3b6bd9",
    # Fondos de estado
    "ok_bg":       "#edf7f1",
    "warn_bg":     "#fdf6e3",
    "crit_bg":     "#fdf0f1",
    "none_bg":     "#f5f6f7",
    # Bordes de estado
    "ok_border":   "#a8d9bf",
    "warn_border": "#e8cc80",
    "crit_border": "#e8a0ab",
    "none_border": "#c8ccd0",
    # Texto de estado
    "ok_text":     "#1d6b46",
    "warn_text":   "#8a6000",
    "crit_text":   "#8a1f30",
    "none_text":   "#555a60",
    # Estructura
    "bg":          "#f9fafb",
    "surface":     "#ffffff",
    "border":      "#e8eaed",
    "divider":     "#eef0f3",
    "text":        "#1a2330",
    "text2":       "#5a6475",
    "text3":       "#8a909a",
    "text4":       "#b0b5bc",
    "grid":        "#eef0f3",
    "axis":        "#c8ccd0",
    "shadow":      "rgba(26,35,48,0.07)",
}

# ---------------------------------------------------------------------------
# Template Plotly global — registrado una sola vez
# ---------------------------------------------------------------------------
_PLOTLY_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Space Grotesk, system-ui, sans-serif", size=12, color=C["text"]),
        paper_bgcolor=C["surface"],
        plot_bgcolor=C["surface"],
        colorway=[C["accent"], C["ok"], C["warn"], C["crit"]],
        xaxis=dict(
            gridcolor=C["grid"], zerolinecolor=C["divider"],
            linecolor=C["border"], ticks="outside", ticklen=4,
        ),
        yaxis=dict(
            gridcolor=C["grid"], zerolinecolor=C["divider"],
            linecolor=C["border"], ticks="outside", ticklen=4,
        ),
        margin=dict(l=48, r=16, t=24, b=40),
        hoverlabel=dict(
            bgcolor=C["text"], font_color="#ffffff",
            font_family="JetBrains Mono, monospace",
        ),
    )
)

pio.templates["data_dashboard"] = _PLOTLY_TEMPLATE
pio.templates.default = "data_dashboard"


# ---------------------------------------------------------------------------
# Mapa de estado → (key_color, icono, label)
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
# Helpers HTML — colores completamente inline (sin CSS custom properties)
# para garantizar visibilidad independientemente de Streamlit
# ---------------------------------------------------------------------------

def badge_html(estado, sin_datos: bool = False) -> str:
    key = None if sin_datos else estado
    sk, icon, label = _SM.get(key, _SM[None])
    bg  = C[f"{sk}_bg"]
    brd = C[f"{sk}_border"]
    txt = C[f"{sk}_text"]
    return (
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'padding:2px 8px 2px 6px;font-size:11px;font-weight:600;'
        f'font-family:\'JetBrains Mono\',monospace;letter-spacing:0.02em;'
        f'text-transform:uppercase;border-radius:999px;'
        f'border:1px solid {brd};background:{bg};color:{txt};white-space:nowrap;">'
        f'<span style="font-size:10px;line-height:1">{icon}</span>{label}</span>'
    )


def kpi_strip_html(total: int, ok: int, warn: int, crit: int) -> str:
    def _kpi(label, value, unit_of=None, accent_color=None):
        bar = ""
        if accent_color:
            bar = (
                f'<div style="position:absolute;left:0;top:0;bottom:0;width:3px;'
                f'background:{accent_color};border-radius:2px 0 0 2px"></div>'
            )
        unit_html = ""
        if unit_of is not None:
            unit_html = (
                f'<span style="font-size:14px;font-weight:500;'
                f'color:{C["text3"]};letter-spacing:0;margin-left:4px">/ {unit_of}</span>'
            )
        return (
            f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
            f'border-radius:10px;padding:16px;display:flex;flex-direction:column;'
            f'gap:8px;position:relative;overflow:hidden;">'
            f'{bar}'
            f'<div style="font-size:10px;font-weight:600;font-family:\'JetBrains Mono\',monospace;'
            f'color:{C["text3"]};text-transform:uppercase;letter-spacing:0.08em;">{label}</div>'
            f'<div style="font-size:32px;font-weight:600;letter-spacing:-0.03em;line-height:1;'
            f'color:{C["text"]};font-variant-numeric:tabular-nums;display:flex;align-items:baseline;">'
            f'{value}{unit_html}</div>'
            f'</div>'
        )

    return (
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:4px">'
        f'{_kpi("TOTAL PROYECTOS", total)}'
        f'{_kpi("OK", ok, total, C["ok"])}'
        f'{_kpi("REGULAR", warn, total, C["warn"])}'
        f'{_kpi("CRÍTICO", crit, total, C["crit"])}'
        f'</div>'
    )


def project_card_html(proyecto: str, grupo: str, estado, sin_datos: bool, xok, dt_str: str) -> str:
    sk  = status_key(None if sin_datos else estado)
    rail_color = C[sk]
    brd_color  = C[f"{sk}_border"] if sk != "ok" else C["border"]

    xok_str = f"{xok:.1f}" if xok is not None else "—"
    pct = min(float(xok or 0), 100)
    bdg = badge_html(estado, sin_datos)

    progress_track = C["divider"]
    progress_fill  = C[sk]

    return (
        f'<div style="display:grid;grid-template-columns:3px 1fr;'
        f'background:{C["surface"]};border:1px solid {brd_color};'
        f'border-radius:10px;overflow:hidden;min-height:150px;'
        f'box-shadow:0 1px 3px {C["shadow"]},0 1px 1px rgba(26,35,48,0.04);'
        f'margin-bottom:2px;">'

        f'<div style="background:{rail_color}"></div>'

        f'<div style="padding:16px;display:flex;flex-direction:column;gap:12px;">'

        # cabecera: nombre + badge
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">'
        f'<div>'
        f'<div style="font-size:10px;font-weight:500;font-family:\'JetBrains Mono\',monospace;'
        f'color:{C["text3"]};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:3px;">'
        f'Grupo {grupo}</div>'
        f'<div style="font-size:13px;font-weight:600;color:{C["text"]};line-height:1.2;">'
        f'{proyecto}</div>'
        f'</div>'
        f'{bdg}'
        f'</div>'

        # métricas
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">'
        f'<div style="display:flex;flex-direction:column;gap:3px;">'
        f'<div style="font-size:9px;font-weight:600;font-family:\'JetBrains Mono\',monospace;'
        f'color:{C["text4"]};text-transform:uppercase;letter-spacing:0.1em;">% OK</div>'
        f'<div style="font-size:20px;font-weight:600;letter-spacing:-0.02em;color:{C["text"]};'
        f'line-height:1.1;font-variant-numeric:tabular-nums;">'
        f'{xok_str}<span style="font-size:11px;font-weight:500;color:{C["text3"]};margin-left:2px">%</span></div>'
        f'</div>'
        f'<div style="display:flex;flex-direction:column;gap:3px;">'
        f'<div style="font-size:9px;font-weight:600;font-family:\'JetBrains Mono\',monospace;'
        f'color:{C["text4"]};text-transform:uppercase;letter-spacing:0.1em;">Últ. ejec.</div>'
        f'<div style="font-size:12px;font-weight:500;color:{C["text"]};font-family:\'JetBrains Mono\',monospace;">'
        f'{dt_str}</div>'
        f'</div>'
        f'</div>'

        # barra de progreso
        f'<div style="padding-top:8px;border-top:1px dashed {C["divider"]};">'
        f'<div style="height:4px;background:{progress_track};border-radius:999px;overflow:hidden;">'
        f'<div style="height:100%;width:{pct:.1f}%;background:{progress_fill};'
        f'border-radius:inherit;"></div>'
        f'</div>'
        f'</div>'

        f'</div>'  # body
        f'</div>'  # card
    )


def attention_item_html(badge: str, name: str, reason: str, time_str: str) -> str:
    return (
        f'<div style="display:flex;align-items:center;gap:12px;'
        f'padding:10px 16px;border-bottom:1px solid {C["divider"]};font-size:12px;">'
        f'{badge}'
        f'<span style="font-weight:600;color:{C["text"]}">{name}</span>'
        f'<span style="color:{C["text3"]};flex:1">{reason}</span>'
        f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:11px;'
        f'color:{C["text3"]}">{time_str}</span>'
        f'</div>'
    )


def mini_stat_html(label: str, value, color_key: str = "") -> str:
    val_color = C[f"{color_key}_text"] if color_key else C["text"]
    return (
        f'<div style="background:{C["surface"]};padding:12px 14px;'
        f'display:flex;flex-direction:column;gap:4px;">'
        f'<div style="font-size:10px;font-family:\'JetBrains Mono\',monospace;font-weight:600;'
        f'color:{C["text3"]};text-transform:uppercase;letter-spacing:0.06em;">{label}</div>'
        f'<div style="font-size:22px;font-weight:600;letter-spacing:-0.02em;'
        f'font-variant-numeric:tabular-nums;color:{val_color};line-height:1.1;">{value}</div>'
        f'</div>'
    )


def panel_html(title: str, subtitle: str, body_html: str, no_pad: bool = False) -> str:
    body_pad = "0" if no_pad else "16px"
    return (
        f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
        f'border-radius:10px;overflow:hidden;margin-bottom:8px;">'
        f'<div style="padding:12px 16px;border-bottom:1px solid {C["divider"]};'
        f'display:flex;align-items:center;gap:12px;">'
        f'<span style="font-size:13px;font-weight:600;color:{C["text"]}">{title}</span>'
        f'<span style="font-size:11px;font-family:\'JetBrains Mono\',monospace;'
        f'color:{C["text3"]}">{subtitle}</span>'
        f'</div>'
        f'<div style="padding:{body_pad}">{body_html}</div>'
        f'</div>'
    )


def section_title_html(text: str) -> str:
    return (
        f'<div style="display:flex;align-items:center;gap:8px;'
        f'font-size:11px;font-weight:600;font-family:\'JetBrains Mono\',monospace;'
        f'color:{C["text3"]};text-transform:uppercase;letter-spacing:0.1em;'
        f'margin:12px 0 8px;">'
        f'{text}'
        f'<div style="flex:1;height:1px;background:{C["divider"]}"></div>'
        f'</div>'
    )


def day_kpis_html(ejecuciones: int, proyectos: int, pct_ok: float, total_proc: int) -> str:
    def _k(label, value):
        return (
            f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
            f'border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:4px;">'
            f'<div style="font-size:10px;font-weight:600;font-family:\'JetBrains Mono\',monospace;'
            f'color:{C["text3"]};text-transform:uppercase;letter-spacing:0.1em;">{label}</div>'
            f'<div style="font-size:26px;font-weight:600;letter-spacing:-0.03em;'
            f'color:{C["text"]};line-height:1;font-variant-numeric:tabular-nums;">{value}</div>'
            f'</div>'
        )
    return (
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:12px;">'
        f'{_k("Ejecuciones", f"{ejecuciones:,}")}'
        f'{_k("Proyectos activos", proyectos)}'
        f'{_k("% OK medio", f"{pct_ok:.1f} %")}'
        f'{_k("Total procesos", f"{total_proc:,}")}'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# CSS inyectado — solo estructura y fuentes; colores inline en el HTML
# ---------------------------------------------------------------------------
_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>
/* Fuentes globales */
html, body, .stApp { font-family: 'Space Grotesk', system-ui, sans-serif !important; }
.stMarkdown, .stMarkdown p, .stMarkdown div { font-family: 'Space Grotesk', system-ui, sans-serif; }
[data-testid="stSidebar"] { font-family: 'Space Grotesk', system-ui, sans-serif; }

/* Quitar menú hamburguesa y footer de Streamlit */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* Fondo de la app */
.stApp { background: #f9fafb !important; }
.block-container { padding-top: 1.5rem !important; max-width: 1600px !important; }

/* Sidebar limpio */
[data-testid="stSidebar"] > div:first-child { background: #ffffff !important; }

/* Quitar separación extra de st.markdown cuando contiene HTML */
.stMarkdown { margin-bottom: 0 !important; }
.element-container { margin-bottom: 4px !important; }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

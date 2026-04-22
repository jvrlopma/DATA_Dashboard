"""Vista 1 — Resumen global del estado de los proyectos ETL."""

from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.core.data_access.base_repository import BaseRepository
from src.domain.models import ALL_PROJECTS, ProjectStatus
from src.domain.project_status import (
    execution_from_row,
    compute_project_health,
    get_all_project_health,
)

# TTL 5 min; el prefijo _ en _repo excluye el objeto del hash de cache
@st.cache_data(ttl=300, show_spinner=False)
def _load_last(_repo):
    return _repo.get_last_execution_per_project()


@st.cache_data(ttl=300, show_spinner=False)
def _load_all(_repo):
    return _repo.get_all_executions()

# ---------------------------------------------------------------------------
# Constantes visuales
# ---------------------------------------------------------------------------

_STATUS_CONFIG = {
    ProjectStatus.OK: {
        "icon": "✅",
        "label": "OK",
        "bg": "#d4edda",
        "border": "#28a745",
        "text": "#155724",
    },
    ProjectStatus.REGULAR: {
        "icon": "⚠️",
        "label": "REGULAR",
        "bg": "#fff3cd",
        "border": "#ffc107",
        "text": "#856404",
    },
    ProjectStatus.CRITICO: {
        "icon": "❌",
        "label": "CRITICO",
        "bg": "#f8d7da",
        "border": "#dc3545",
        "text": "#721c24",
    },
}

_SIN_DATOS_CONFIG = {
    "icon": "⚫",
    "label": "Sin datos",
    "bg": "#e2e3e5",
    "border": "#6c757d",
    "text": "#383d41",
}


def _status_cfg(health) -> dict:
    if health.sin_datos_recientes:
        return _SIN_DATOS_CONFIG
    return _STATUS_CONFIG[health.estado]


# ---------------------------------------------------------------------------
# Componente: tarjeta KPI
# ---------------------------------------------------------------------------

def _kpi_card(health) -> str:
    """Genera el HTML de una tarjeta KPI para un proyecto."""
    cfg = _status_cfg(health)
    xok_str = f"{health.xEjecutadosOK:.1f} %" if health.xEjecutadosOK is not None else "—"
    dt_str = (
        health.ultima_ejecucion.strftime("%d/%m/%Y %H:%M")
        if health.ultima_ejecucion
        else "Sin datos"
    )
    badge = (
        f'<span style="font-size:1.1rem">{cfg["icon"]}</span> '
        f'<strong style="color:{cfg["text"]}">{cfg["label"]}</strong>'
    )
    return f"""
<div style="
    background:{cfg['bg']};
    border-left: 5px solid {cfg['border']};
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
    min-height: 110px;
">
  <div style="font-size:0.85rem;color:#555;margin-bottom:4px;
              white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
    {health.proyecto}
  </div>
  <div style="margin-bottom:6px">{badge}</div>
  <div style="font-size:1.4rem;font-weight:bold;color:{cfg['text']}">{xok_str}</div>
  <div style="font-size:0.75rem;color:#666;margin-top:4px">
    Ult. ejec.: {dt_str}
  </div>
</div>
"""


# ---------------------------------------------------------------------------
# Grafico de evolucion temporal
# ---------------------------------------------------------------------------

def _trend_chart(df_all: pd.DataFrame, days: int) -> go.Figure:
    """Genera el grafico de linea del % OK agregado en los ultimos N dias."""
    max_date = df_all["nFecha_ejecucion"].max()
    cutoff = int((
        datetime.strptime(str(max_date), "%Y%m%d") - timedelta(days=days)
    ).strftime("%Y%m%d"))

    df = df_all[df_all["nFecha_ejecucion"] >= cutoff].copy()

    daily = (
        df.groupby("nFecha_ejecucion")["xEjecutadosOK"]
        .mean()
        .reset_index()
        .rename(columns={"nFecha_ejecucion": "fecha", "xEjecutadosOK": "xOK_medio"})
    )
    daily["fecha_dt"] = pd.to_datetime(daily["fecha"].astype(str), format="%Y%m%d")
    daily = daily.sort_values("fecha_dt")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["fecha_dt"],
        y=daily["xOK_medio"],
        mode="lines+markers",
        name="% OK medio",
        line=dict(color="#28a745", width=2),
        marker=dict(size=4),
        hovertemplate="%{x|%d/%m/%Y}<br>% OK: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=90, line_dash="dot", line_color="#ffc107",
                  annotation_text="90 %", annotation_position="right")
    fig.add_hline(y=80, line_dash="dot", line_color="#dc3545",
                  annotation_text="80 %", annotation_position="right")

    fig.update_layout(
        margin=dict(l=0, r=60, t=10, b=0),
        yaxis=dict(range=[0, 105], ticksuffix=" %", gridcolor="#eee"),
        xaxis=dict(gridcolor="#eee"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=280,
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Vista principal
# ---------------------------------------------------------------------------

def render(repo: BaseRepository) -> None:
    """Renderiza la Vista 1 — Resumen global."""
    st.title("Resumen global — Estado ETL")

    # --- Datos ---
    df_last = _load_last(repo)
    now = datetime.now()

    last_by_project = {}
    for _, row in df_last.iterrows():
        e = execution_from_row(row)
        last_by_project[e.proyecto] = e

    healths = get_all_project_health(df_last, now)

    # --- KPIs en cabecera ---
    col_ok = sum(1 for h in healths if h.estado == ProjectStatus.OK and not h.sin_datos_recientes)
    col_reg = sum(1 for h in healths if h.estado == ProjectStatus.REGULAR)
    col_crit = sum(1 for h in healths if h.estado == ProjectStatus.CRITICO)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total proyectos", len(ALL_PROJECTS))
    k2.metric("✅ OK", col_ok)
    k3.metric("⚠️ Regular", col_reg)
    k4.metric("❌ Critico / Sin datos", col_crit)

    st.divider()

    # --- Grid de tarjetas ---
    st.subheader("Estado por proyecto")
    cols = st.columns(4)
    for i, health in enumerate(sorted(healths, key=lambda h: h.proyecto)):
        with cols[i % 4]:
            st.markdown(_kpi_card(health), unsafe_allow_html=True)

    st.divider()

    # --- Proyectos que requieren atencion ---
    problemas = [h for h in healths if h.estado != ProjectStatus.OK or h.sin_datos_recientes]
    if problemas:
        st.subheader("⚠️ Proyectos que requieren atencion")
        for h in problemas:
            cfg = _status_cfg(h)
            xok_str = f"{h.xEjecutadosOK:.1f} %" if h.xEjecutadosOK is not None else "—"
            dt_str = (
                h.ultima_ejecucion.strftime("%d/%m/%Y %H:%M")
                if h.ultima_ejecucion else "Sin datos"
            )
            st.markdown(
                f"{cfg['icon']} **{h.proyecto}** — "
                f"{h.etiqueta_estado} | % OK: {xok_str} | "
                f"Ult. ejec.: {dt_str}"
            )
    else:
        st.success("Todos los proyectos están en estado OK.")

    st.divider()

    # --- Grafico de evolucion ---
    st.subheader("Evolucion del % OK")
    tab7, tab30, tab90 = st.tabs(["Ultimos 7 dias", "Ultimos 30 dias", "Ultimos 90 dias"])
    df_all = _load_all(repo)

    with tab7:
        st.plotly_chart(_trend_chart(df_all, 7), use_container_width=True)
    with tab30:
        st.plotly_chart(_trend_chart(df_all, 30), use_container_width=True)
    with tab90:
        st.plotly_chart(_trend_chart(df_all, 90), use_container_width=True)

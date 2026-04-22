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
from src.ui.styles import C, badge_html, kpi_strip_html, project_card_html, attention_item_html, section_title_html, panel_html


@st.cache_data(ttl=300, show_spinner=False)
def _load_last(_repo):
    return _repo.get_last_execution_per_project()


@st.cache_data(ttl=300, show_spinner=False)
def _load_all(_repo):
    return _repo.get_all_executions()


# ---------------------------------------------------------------------------
# Grafico de evolucion temporal
# ---------------------------------------------------------------------------

def _trend_chart(df_all: pd.DataFrame, days: int) -> go.Figure:
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
        line=dict(color=C["ok"], width=2),
        marker=dict(size=4, color=C["ok"]),
        hovertemplate="%{x|%d/%m/%Y}<br>% OK: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=90, line_dash="dot", line_color=C["warn"],
                  annotation_text="90 %", annotation_position="right")
    fig.add_hline(y=80, line_dash="dot", line_color=C["crit"],
                  annotation_text="80 %", annotation_position="right")

    fig.update_layout(
        margin=dict(l=0, r=60, t=10, b=0),
        yaxis=dict(range=[0, 105], ticksuffix=" %", gridcolor=C["grid"]),
        xaxis=dict(gridcolor=C["grid"]),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=280,
        showlegend=False,
        font=dict(family="Space Grotesk, sans-serif", size=12),
    )
    return fig


# ---------------------------------------------------------------------------
# Vista principal
# ---------------------------------------------------------------------------

def render(repo: BaseRepository) -> None:
    """Renderiza la Vista 1 — Resumen global."""
    st.markdown('<h2 style="margin-bottom:4px;font-size:20px;font-weight:600">Resumen global — Estado ETL</h2>', unsafe_allow_html=True)

    df_last = _load_last(repo)
    now = datetime.now()

    last_by_project = {}
    for _, row in df_last.iterrows():
        e = execution_from_row(row)
        last_by_project[e.proyecto] = e

    healths = get_all_project_health(df_last, now)

    col_ok   = sum(1 for h in healths if not h.sin_datos_recientes and h.estado == ProjectStatus.OK)
    col_warn = sum(1 for h in healths if not h.sin_datos_recientes and h.estado == ProjectStatus.REGULAR)
    col_crit = sum(1 for h in healths if not h.sin_datos_recientes and h.estado == ProjectStatus.CRITICO)

    # --- KPI strip ---
    st.markdown(kpi_strip_html(len(ALL_PROJECTS), col_ok, col_warn, col_crit), unsafe_allow_html=True)

    # --- Section: Estado por proyecto ---
    from src.domain.models import PROYECTOS_GRUPO_A
    st.markdown(section_title_html("Estado por pipeline"), unsafe_allow_html=True)

    sorted_healths = sorted(healths, key=lambda h: h.proyecto)
    cols = st.columns(4)
    for i, health in enumerate(sorted_healths):
        dt_str = (
            health.ultima_ejecucion.strftime("%d/%m %H:%M")
            if health.ultima_ejecucion else "Sin datos"
        )
        estado_val = health.estado.value if hasattr(health.estado, "value") else str(health.estado)
        with cols[i % 4]:
            st.markdown(
                project_card_html(
                    proyecto=health.proyecto,
                    grupo="A" if health.proyecto in PROYECTOS_GRUPO_A else "B",
                    estado=estado_val,
                    sin_datos=health.sin_datos_recientes,
                    xok=health.xEjecutadosOK,
                    dt_str=dt_str,
                ),
                unsafe_allow_html=True,
            )

    # --- Proyectos que requieren atencion ---
    problemas = [h for h in healths if h.sin_datos_recientes or h.estado != ProjectStatus.OK]
    if problemas:
        st.markdown(section_title_html("Requieren atención"), unsafe_allow_html=True)
        items_html = ""
        for h in problemas:
            estado_val = h.estado.value if hasattr(h.estado, "value") else str(h.estado)
            bdg = badge_html(None if h.sin_datos_recientes else estado_val, h.sin_datos_recientes)
            xok_str = f"{h.xEjecutadosOK:.1f} %" if h.xEjecutadosOK is not None else "—"
            dt_str = (
                h.ultima_ejecucion.strftime("%d/%m/%Y %H:%M")
                if h.ultima_ejecucion else "Sin datos"
            )
            items_html += attention_item_html(bdg, h.proyecto, f"% OK: {xok_str}", dt_str)
        st.markdown(
            panel_html("Proyectos que requieren atención",
                       f"{len(problemas)} proyectos", items_html, no_pad=True),
            unsafe_allow_html=True,
        )
    else:
        st.success("Todos los proyectos están en estado OK.")

    # --- Grafico de evolucion ---
    st.markdown(section_title_html("Evolución del % OK"), unsafe_allow_html=True)
    tab7, tab30, tab90 = st.tabs(["Últimos 7 días", "Últimos 30 días", "Últimos 90 días"])
    df_all = _load_all(repo)

    with tab7:
        st.plotly_chart(_trend_chart(df_all, 7), use_container_width=True)
    with tab30:
        st.plotly_chart(_trend_chart(df_all, 30), use_container_width=True)
    with tab90:
        st.plotly_chart(_trend_chart(df_all, 90), use_container_width=True)

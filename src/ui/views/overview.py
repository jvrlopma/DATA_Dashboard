"""Vista 1 — Resumen global del estado de los proyectos ETL."""

from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.core.data_access.base_repository import BaseRepository
from src.domain.models import ALL_PROJECTS, PROYECTOS_GRUPO_A, ProjectStatus
from src.domain.project_status import execution_from_row, get_all_project_health
from src.ui.styles import (
    C, badge_html, kpi_strip_html, project_card_html,
    attention_items_html, section_title_html,
)


@st.cache_data(ttl=60, show_spinner=False)
def _load_last(_repo):
    return _repo.get_last_execution_per_project()


@st.cache_data(ttl=60, show_spinner=False)
def _load_all(_repo):
    return _repo.get_all_executions()


@st.cache_data(ttl=60, show_spinner=False)
def _load_gis(_repo):
    return _repo.get_executions_by_project("Aqualia_GIS")


# ---------------------------------------------------------------------------
# Clasificador de estado (idéntico al de daily_ops/project_detail)
# ---------------------------------------------------------------------------
def _clasificar(xok: float, proyecto: str) -> str:
    if proyecto in PROYECTOS_GRUPO_A:
        return "CRITICO" if xok < 100.0 else "OK"
    if xok >= 90.0:
        return "OK"
    if xok >= 80.0:
        return "REGULAR"
    return "CRITICO"


# ---------------------------------------------------------------------------
# Gráfico: ejecuciones por estado por día (stacked bar)
# ---------------------------------------------------------------------------
def _status_bar_chart(df_all: pd.DataFrame, days: int) -> go.Figure:
    max_date = df_all["nFecha_ejecucion"].max()
    cutoff = int((
        datetime.strptime(str(max_date), "%Y%m%d") - timedelta(days=days)
    ).strftime("%Y%m%d"))

    df = df_all[df_all["nFecha_ejecucion"] >= cutoff].copy()
    df["Estado"] = df.apply(
        lambda r: _clasificar(r["xEjecutadosOK"], r["proyecto"]), axis=1
    )
    df["fecha_dt"] = pd.to_datetime(
        df["nFecha_ejecucion"].astype(str), format="%Y%m%d"
    )

    counts = (
        df.groupby(["fecha_dt", "Estado"])
        .size()
        .reset_index(name="n")
    )

    fig = go.Figure()
    palette = {"OK": C["ok"], "REGULAR": C["warn"], "CRITICO": C["crit"]}
    for estado in ["CRITICO", "REGULAR", "OK"]:
        sub = counts[counts["Estado"] == estado].sort_values("fecha_dt")
        fig.add_trace(go.Bar(
            x=sub["fecha_dt"], y=sub["n"],
            name=estado,
            marker_color=palette[estado],
            hovertemplate="%{x|%d/%m/%Y}<br>" + estado + ": %{y} ejec.<extra></extra>",
        ))

    fig.update_layout(
        barmode="stack",
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(tickformat="%d/%m"),
        yaxis=dict(title="Ejecuciones"),
        margin=dict(l=44, r=12, t=8, b=32),
    )
    return fig


# ---------------------------------------------------------------------------
# Vista principal
# ---------------------------------------------------------------------------

def render(repo: BaseRepository) -> None:
    df_last = _load_last(repo)
    df_gis = _load_gis(repo)
    now = datetime.now()

    healths = get_all_project_health(df_last, now, df_gis=df_gis)

    col_ok   = sum(1 for h in healths if not h.sin_datos_recientes and h.estado == ProjectStatus.OK)
    col_warn = sum(1 for h in healths if not h.sin_datos_recientes and h.estado == ProjectStatus.REGULAR)
    col_crit = sum(1 for h in healths if not h.sin_datos_recientes and h.estado == ProjectStatus.CRITICO)

    # Cabecera
    st.markdown(
        '<h2 style="font-family:Inter,sans-serif;font-size:22px;'
        'font-weight:600;color:var(--dd-text);letter-spacing:-0.02em;margin:0 0 4px">Resumen global</h2>'
        '<p style="font-family:\'JetBrains Mono\',monospace;font-size:12px;color:var(--dd-text3);margin:0 0 16px">'
        f'Vista de mando · {now.strftime("%d/%m/%Y")} · {now.strftime("%H:%M")}</p>',
        unsafe_allow_html=True,
    )

    # KPI strip
    st.markdown(kpi_strip_html(len(ALL_PROJECTS), col_ok, col_warn, col_crit), unsafe_allow_html=True)

    # Grid de tarjetas
    st.markdown(section_title_html("Estado por pipeline", f"{len(ALL_PROJECTS)} proyectos"), unsafe_allow_html=True)

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

    # Panel inferior: atención + gráfico de actividad
    problemas = [h for h in healths if h.sin_datos_recientes or h.estado != ProjectStatus.OK]

    col_att, col_chart = st.columns([1, 1.4])

    with col_att:
        attn_items = []
        for h in problemas:
            estado_val = h.estado.value if hasattr(h.estado, "value") else str(h.estado)
            bdg = badge_html(None if h.sin_datos_recientes else estado_val, h.sin_datos_recientes)
            xok_str = f"{h.xEjecutadosOK:.1f} %" if h.xEjecutadosOK is not None else "—"
            dt_str = h.ultima_ejecucion.strftime("%H:%M") if h.ultima_ejecucion else "—"
            reason = "Sin datos recientes" if h.sin_datos_recientes else f"% OK: {xok_str}"
            attn_items.append((bdg, h.proyecto, reason, dt_str))

        # attention_items_html ya genera el panel completo con cabecera
        st.markdown(attention_items_html(attn_items), unsafe_allow_html=True)

    with col_chart:
        df_all = _load_all(repo)
        tab7, tab30, tab90 = st.tabs(["7d", "30d", "90d"])
        with tab7:
            st.plotly_chart(_status_bar_chart(df_all, 7), use_container_width=True)
        with tab30:
            st.plotly_chart(_status_bar_chart(df_all, 30), use_container_width=True)
        with tab90:
            st.plotly_chart(_status_bar_chart(df_all, 90), use_container_width=True)

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
    attention_items_html, panel_html, section_title_html,
)


@st.cache_data(ttl=300, show_spinner=False)
def _load_last(_repo):
    return _repo.get_last_execution_per_project()


@st.cache_data(ttl=300, show_spinner=False)
def _load_all(_repo):
    return _repo.get_all_executions()


# ---------------------------------------------------------------------------
# Gráfico de evolución
# ---------------------------------------------------------------------------

def _trend_chart(df_all: pd.DataFrame, days: int) -> go.Figure:
    max_date = df_all["nFecha_ejecucion"].max()
    cutoff = int((
        datetime.strptime(str(max_date), "%Y%m%d") - timedelta(days=days)
    ).strftime("%Y%m%d"))

    df = df_all[df_all["nFecha_ejecucion"] >= cutoff].copy()
    daily = (
        df.groupby("nFecha_ejecucion")["xEjecutadosOK"]
        .mean().reset_index()
        .rename(columns={"nFecha_ejecucion": "fecha", "xEjecutadosOK": "pct_ok"})
    )
    daily["fecha_dt"] = pd.to_datetime(daily["fecha"].astype(str), format="%Y%m%d")
    daily = daily.sort_values("fecha_dt")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["fecha_dt"], y=daily["pct_ok"],
        mode="lines+markers", name="% OK medio",
        line=dict(color=C["accent"], width=2),
        marker=dict(size=4, color=C["accent"]),
        hovertemplate="%{x|%d/%m/%Y}<br>% OK: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=90, line_dash="dot", line_color=C["warn"],
                  annotation_text="OBJETIVO · 90%", annotation_position="right")
    fig.add_hline(y=80, line_dash="dot", line_color=C["crit"],
                  annotation_text="UMBRAL CRÍTICO · 80%", annotation_position="right")
    fig.update_layout(
        yaxis=dict(range=[0, 105], ticksuffix=" %"),
        height=240, showlegend=False,
        margin=dict(l=48, r=80, t=16, b=40),
    )
    return fig


# ---------------------------------------------------------------------------
# Vista principal
# ---------------------------------------------------------------------------

def render(repo: BaseRepository) -> None:
    df_last = _load_last(repo)
    now = datetime.now()

    healths = get_all_project_health(df_last, now)

    col_ok   = sum(1 for h in healths if not h.sin_datos_recientes and h.estado == ProjectStatus.OK)
    col_warn = sum(1 for h in healths if not h.sin_datos_recientes and h.estado == ProjectStatus.REGULAR)
    col_crit = sum(1 for h in healths if not h.sin_datos_recientes and h.estado == ProjectStatus.CRITICO)

    # Cabecera
    st.markdown(
        f'<h2 style="font-family:\'Space Grotesk\',sans-serif;font-size:22px;'
        f'font-weight:600;color:{C["text"]};letter-spacing:-0.02em;margin:0 0 4px">Resumen global</h2>'
        f'<p style="font-family:\'JetBrains Mono\',monospace;font-size:12px;color:{C["text3"]};margin:0 0 16px">'
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

    # Panel inferior: atención + evolución (dos columnas)
    problemas = [h for h in healths if h.sin_datos_recientes or h.estado != ProjectStatus.OK]

    col_att, col_chart = st.columns([1, 1.2])

    with col_att:
        attn_items = []
        for h in problemas:
            estado_val = h.estado.value if hasattr(h.estado, "value") else str(h.estado)
            bdg = badge_html(None if h.sin_datos_recientes else estado_val, h.sin_datos_recientes)
            xok_str = f"{h.xEjecutadosOK:.1f} %" if h.xEjecutadosOK is not None else "—"
            dt_str = h.ultima_ejecucion.strftime("%H:%M") if h.ultima_ejecucion else "—"
            reason = "Sin datos recientes" if h.sin_datos_recientes else f"% OK: {xok_str}"
            attn_items.append((bdg, h.proyecto, reason, dt_str))

        body = attention_items_html(attn_items)
        # Extraer el contenido interno (sin el wrapper .dd) para el panel
        inner = body.replace('<div class="dd">', "").rstrip("</div>").rstrip()
        st.markdown(panel_html(
            "Requieren atención",
            f"{len(problemas)} proyectos",
            inner,
            no_pad=True,
        ), unsafe_allow_html=True)

    with col_chart:
        df_all = _load_all(repo)
        tab7, tab30, tab90 = st.tabs(["7d", "30d", "90d"])
        with tab7:
            st.plotly_chart(_trend_chart(df_all, 7), use_container_width=True)
        with tab30:
            st.plotly_chart(_trend_chart(df_all, 30), use_container_width=True)
        with tab90:
            st.plotly_chart(_trend_chart(df_all, 90), use_container_width=True)

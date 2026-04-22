"""Vista 2 — Detalle por proyecto."""

from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.core.data_access.base_repository import BaseRepository
from src.domain.models import PROYECTOS_GRUPO_A, ProjectStatus
from src.domain.project_status import compute_project_health, execution_from_row
from src.utils.date_utils import int_to_date
from src.ui.styles import C, badge_html, mini_grid_html, panel_html, section_title_html


@st.cache_data(ttl=300, show_spinner=False)
def _load_projects(_repo):
    return _repo.get_available_projects()


@st.cache_data(ttl=300, show_spinner=False)
def _load_by_project(_repo, project: str):
    return _repo.get_executions_by_project(project)


_ESTADO_COLORS  = {"OK": C["ok"], "REGULAR": C["warn"], "CRITICO": C["crit"]}
_ESTADO_PATTERNS = {"OK": "", "REGULAR": "/", "CRITICO": "x"}


def _fecha_int_to_str(n: int) -> str:
    return int_to_date(n).strftime("%d/%m/%Y")


def _clasificar_estado(xok: float, proyecto: str) -> str:
    if proyecto in PROYECTOS_GRUPO_A:
        return "OK" if xok == 100.0 else "CRITICO"
    if xok >= 90.0:
        return "OK"
    if xok >= 80.0:
        return "REGULAR"
    return "CRITICO"


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------

def _chart_evolucion(df: pd.DataFrame, proyecto: str) -> go.Figure:
    daily = (
        df.groupby("nFecha_ejecucion")
        .agg(xOK=("xEjecutadosOK", "mean"), xErr=("xError", "mean"))
        .reset_index()
    )
    daily["fecha_dt"] = pd.to_datetime(daily["nFecha_ejecucion"].astype(str), format="%Y%m%d")
    daily = daily.sort_values("fecha_dt")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["fecha_dt"], y=daily["xOK"], name="% OK", mode="lines+markers",
        line=dict(color=C["ok"], width=2), marker=dict(size=4, color=C["ok"]),
        hovertemplate="%{x|%d/%m/%Y}<br>% OK: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=daily["fecha_dt"], y=daily["xErr"], name="% Error", mode="lines+markers",
        line=dict(color=C["crit"], width=2, dash="dash"), marker=dict(size=4, color=C["crit"]),
        hovertemplate="%{x|%d/%m/%Y}<br>% Error: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=90, line_dash="dot", line_color=C["warn"],
                  annotation_text="OBJETIVO · 90%", annotation_position="right")
    fig.add_hline(y=80, line_dash="dot", line_color=C["crit"],
                  annotation_text="UMBRAL · 80%", annotation_position="right")
    fig.update_layout(
        title=f"Evolución diaria — {proyecto}",
        yaxis=dict(range=[0, 105], ticksuffix=" %"),
        height=240, margin=dict(l=48, r=80, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def _chart_por_hora(df: pd.DataFrame, proyecto: str) -> go.Figure:
    hourly = (
        df.groupby("Hora_ejecucion")
        .agg(n=("Id", "count"), xOK=("xEjecutadosOK", "mean"))
        .reset_index()
    )
    estados  = hourly["xOK"].apply(lambda x: _clasificar_estado(x, proyecto))
    colors   = [_ESTADO_COLORS.get(e, C["none"]) for e in estados]
    patterns = [_ESTADO_PATTERNS.get(e, "") for e in estados]

    fig = go.Figure(go.Bar(
        x=hourly["Hora_ejecucion"], y=hourly["n"],
        marker=dict(color=colors, pattern=dict(shape=patterns, solidity=0.6)),
        hovertemplate="Hora %{x}h<br>Ejecuciones: %{y}<br>% OK medio: %{customdata:.1f}%<extra></extra>",
        customdata=hourly["xOK"],
    ))
    fig.update_layout(
        title=f"Distribución por hora — {proyecto}",
        xaxis=dict(title="Hora del día", dtick=1),
        yaxis=dict(title="N.º ejecuciones"),
        height=240, margin=dict(l=48, r=16, t=40, b=40),
    )
    return fig


def _chart_volumen(df: pd.DataFrame, proyecto: str) -> go.Figure:
    daily = (
        df.groupby("nFecha_ejecucion")["nTotalEjecuciones"].sum().reset_index()
    )
    daily["fecha_dt"] = pd.to_datetime(daily["nFecha_ejecucion"].astype(str), format="%Y%m%d")
    daily = daily.sort_values("fecha_dt")

    fig = go.Figure(go.Scatter(
        x=daily["fecha_dt"], y=daily["nTotalEjecuciones"],
        fill="tozeroy", mode="lines",
        line=dict(color=C["accent"], width=1.5),
        fillcolor=C["accent"] + "26",
        hovertemplate="%{x|%d/%m/%Y}<br>Total: %{y:,}<extra></extra>",
    ))
    fig.update_layout(
        title=f"Volumen de ejecuciones — {proyecto}",
        height=180, margin=dict(l=48, r=16, t=40, b=40),
    )
    return fig


# ---------------------------------------------------------------------------
# Panel de última ejecución (mini-grid 9 stats)
# ---------------------------------------------------------------------------

def _panel_ultima_ejecucion(row: pd.Series, proyecto: str) -> None:
    fecha_str = _fecha_int_to_str(int(row["nFecha_ejecucion"]))
    hora = int(row["Hora_ejecucion"])
    minuto = int(row["Minuto_ejecucion"])
    xok = row["xEjecutadosOK"]
    err_proc = int(row["nErrorProc"])
    err_inst = int(row["nErrorInst"])

    ck_xok  = "ok" if xok >= 90 else ("warn" if xok >= 80 else "crit")
    ck_errp = "crit" if err_proc > 0 else ""
    ck_erri = "warn" if err_inst > 0 else ""

    stats = [
        ("PROCESOS · EN ESPERA",    int(row["nEsperaProc"]),        ""),
        ("PROCESOS · EN EJECUCIÓN", int(row["nEnEjecucionProc"]),   ""),
        ("PROCESOS · CON ERROR",    err_proc,                        ck_errp),
        ("PROCESOS · OK",           int(row["nEjecutadosOkProc"]),  "ok"),
        ("INSTALACIONES · ESPERA",  int(row["nEsperaInst"]),        ""),
        ("INSTALACIONES · EJEC.",   int(row["nEnEjecucionInst"]),   ""),
        ("INSTALACIONES · ERROR",   err_inst,                        ck_erri),
        ("INSTALACIONES · OK",      int(row["nEjecutadosOkInst"]), "ok"),
        ("TOTAL OK %",              f"{xok:.1f}%",                  ck_xok),
    ]
    grid_html = mini_grid_html(stats, cols=3).replace('<div class="dd">', "").rstrip("</div>").rstrip()

    bdg = badge_html(
        None if xok < 80 else ("OK" if xok >= 90 else "REGULAR"),
        sin_datos=False,
    )
    st.markdown(
        panel_html(
            proyecto,
            f"{fecha_str} · {hora:02d}:{minuto:02d}",
            f'<div class="section-title" style="margin-bottom:12px">Última ejecución · 9 métricas</div>{grid_html}',
        ),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Vista principal
# ---------------------------------------------------------------------------

def render(repo: BaseRepository) -> None:
    st.markdown(
        f'<h2 style="font-family:\'Space Grotesk\',sans-serif;font-size:22px;'
        f'font-weight:600;color:{C["text"]};letter-spacing:-0.02em;margin:0 0 4px">Detalle por proyecto</h2>'
        f'<p style="font-family:\'JetBrains Mono\',monospace;font-size:12px;color:{C["text3"]};margin:0 0 16px">'
        f'Vista de análisis · última ejecución, evolución e histórico</p>',
        unsafe_allow_html=True,
    )

    proyectos = _load_projects(repo)
    if not proyectos:
        st.error("No hay proyectos disponibles en los datos.")
        return

    col_sel, col_empty = st.columns([2, 3])
    with col_sel:
        proyecto = st.selectbox("Proyecto", proyectos, label_visibility="collapsed")

    df_proyecto = _load_by_project(repo, proyecto)
    if df_proyecto.empty:
        st.warning(f"Sin datos para el proyecto '{proyecto}'.")
        return

    # Filtros
    with st.expander("Filtros", expanded=True):
        fc1, fc2, fc3 = st.columns(3)
        fecha_min = int_to_date(int(df_proyecto["nFecha_ejecucion"].min()))
        fecha_max = int_to_date(int(df_proyecto["nFecha_ejecucion"].max()))
        with fc1:
            desde = st.date_input("Desde", value=fecha_max - timedelta(days=90),
                                  min_value=fecha_min, max_value=fecha_max)
        with fc2:
            hasta = st.date_input("Hasta", value=fecha_max,
                                  min_value=fecha_min, max_value=fecha_max)
        with fc3:
            estados_sel = st.multiselect("Estado", ["OK", "REGULAR", "CRITICO"],
                                         default=["OK", "REGULAR", "CRITICO"])

    desde_int = int(desde.strftime("%Y%m%d"))
    hasta_int = int(hasta.strftime("%Y%m%d"))
    df_fil = df_proyecto[
        (df_proyecto["nFecha_ejecucion"] >= desde_int) &
        (df_proyecto["nFecha_ejecucion"] <= hasta_int)
    ].copy()

    if df_fil.empty:
        st.warning("No hay datos en el rango de fechas seleccionado.")
        return

    df_fil["Estado"] = df_fil["xEjecutadosOK"].apply(lambda x: _clasificar_estado(x, proyecto))
    if estados_sel:
        df_fil = df_fil[df_fil["Estado"].isin(estados_sel)]

    if df_fil.empty:
        st.warning("Ningún registro coincide con los filtros seleccionados.")
        return

    st.caption(f"{len(df_fil):,} ejecuciones en el rango seleccionado")

    # Panel de última ejecución
    ultima = df_fil.sort_values(
        ["nFecha_ejecucion", "Hora_ejecucion", "Minuto_ejecucion"], ascending=False
    ).iloc[0]
    _panel_ultima_ejecucion(ultima, proyecto)

    # Gráficos: evolución + distribución horaria
    gc1, gc2 = st.columns(2)
    with gc1:
        st.plotly_chart(_chart_evolucion(df_fil, proyecto), use_container_width=True)
    with gc2:
        st.plotly_chart(_chart_por_hora(df_fil, proyecto), use_container_width=True)

    # Volumen
    st.plotly_chart(_chart_volumen(df_fil, proyecto), use_container_width=True)

    # Tabla histórica
    st.markdown(section_title_html("Histórico de ejecuciones", f"{len(df_fil):,} registros"), unsafe_allow_html=True)
    tabla = df_fil[[
        "nFecha_ejecucion", "Hora_ejecucion", "Minuto_ejecucion",
        "nTotalEjecuciones", "nEjecutadosOkProc", "nErrorProc",
        "xEjecutadosOK", "xError", "Estado",
    ]].copy()
    tabla["Fecha"] = tabla["nFecha_ejecucion"].apply(lambda n: _fecha_int_to_str(int(n)))
    tabla["Hora"] = tabla.apply(
        lambda r: f"{int(r['Hora_ejecucion']):02d}:{int(r['Minuto_ejecucion']):02d}", axis=1
    )
    tabla = tabla.rename(columns={
        "nTotalEjecuciones": "Total", "nEjecutadosOkProc": "OK (proc)",
        "nErrorProc": "Error (proc)", "xEjecutadosOK": "% OK", "xError": "% Error",
    })[["Fecha", "Hora", "Total", "OK (proc)", "Error (proc)", "% OK", "% Error", "Estado"]]
    tabla = tabla.sort_values(
        ["nFecha_ejecucion", "Hora_ejecucion", "Minuto_ejecucion"], ascending=False
    ).drop(columns=["nFecha_ejecucion", "Hora_ejecucion", "Minuto_ejecucion"], errors="ignore")

    st.dataframe(
        tabla.reset_index(drop=True), use_container_width=True, height=320,
        column_config={
            "% OK": st.column_config.NumberColumn(format="%.1f %%"),
            "% Error": st.column_config.NumberColumn(format="%.1f %%"),
        },
    )

"""Vista 2 — Detalle por proyecto."""

from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.core.data_access.base_repository import BaseRepository
from src.domain.models import ProjectStatus
from src.domain.project_status import compute_project_health, execution_from_row
from src.utils.date_utils import int_to_date
from src.ui.styles import C, mini_stat_html, section_title_html


@st.cache_data(ttl=300, show_spinner=False)
def _load_projects(_repo):
    return _repo.get_available_projects()


@st.cache_data(ttl=300, show_spinner=False)
def _load_by_project(_repo, project: str):
    return _repo.get_executions_by_project(project)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ESTADO_COLORS = {
    "OK":      C["ok"],
    "REGULAR": C["warn"],
    "CRITICO": C["crit"],
}

# Patrones de relleno por estado (accesibilidad para daltonismo)
_ESTADO_PATTERNS = {
    "OK": "",
    "REGULAR": "/",
    "CRITICO": "x",
}


def _fecha_int_to_str(n: int) -> str:
    d = int_to_date(n)
    return d.strftime("%d/%m/%Y")


def _clasificar_estado(xok: float, proyecto: str) -> str:
    from src.domain.models import PROYECTOS_GRUPO_A
    if proyecto in PROYECTOS_GRUPO_A:
        return "OK" if xok == 100.0 else "CRITICO"
    if xok >= 90.0:
        return "OK"
    if xok >= 80.0:
        return "REGULAR"
    return "CRITICO"


# ---------------------------------------------------------------------------
# Graficos
# ---------------------------------------------------------------------------

def _chart_evolucion(df: pd.DataFrame, proyecto: str) -> go.Figure:
    """Grafico de linea: xEjecutadosOK y xError en el tiempo."""
    daily = (
        df.groupby("nFecha_ejecucion")
        .agg(xOK=("xEjecutadosOK", "mean"), xErr=("xError", "mean"))
        .reset_index()
    )
    daily["fecha_dt"] = pd.to_datetime(daily["nFecha_ejecucion"].astype(str), format="%Y%m%d")
    daily = daily.sort_values("fecha_dt")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["fecha_dt"], y=daily["xOK"],
        name="% OK", mode="lines+markers",
        line=dict(color=C["ok"], width=2), marker=dict(size=4, color=C["ok"]),
        hovertemplate="%{x|%d/%m/%Y}<br>% OK: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=daily["fecha_dt"], y=daily["xErr"],
        name="% Error", mode="lines+markers",
        line=dict(color=C["crit"], width=2, dash="dash"), marker=dict(size=4, color=C["crit"]),
        hovertemplate="%{x|%d/%m/%Y}<br>% Error: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=90, line_dash="dot", line_color=C["warn"],
                  annotation_text="90 %", annotation_position="right")
    fig.add_hline(y=80, line_dash="dot", line_color=C["crit"],
                  annotation_text="80 %", annotation_position="right")
    fig.update_layout(
        title=f"Evolución diaria — {proyecto}",
        yaxis=dict(range=[0, 105], ticksuffix=" %", gridcolor=C["grid"]),
        xaxis=dict(gridcolor=C["grid"]),
        plot_bgcolor="white", paper_bgcolor="white",
        height=300, margin=dict(l=0, r=60, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family="Space Grotesk, sans-serif", size=12),
    )
    return fig


def _chart_por_hora(df: pd.DataFrame, proyecto: str) -> go.Figure:
    """Grafico de barras: distribucion de ejecuciones por hora del dia."""
    hourly = (
        df.groupby("Hora_ejecucion")
        .agg(n=("Id", "count"), xOK=("xEjecutadosOK", "mean"))
        .reset_index()
    )
    estados = hourly["xOK"].apply(lambda x: _clasificar_estado(x, proyecto))
    colors   = [_ESTADO_COLORS.get(e, "#6c757d") for e in estados]
    patterns = [_ESTADO_PATTERNS.get(e, "") for e in estados]

    fig = go.Figure(go.Bar(
        x=hourly["Hora_ejecucion"],
        y=hourly["n"],
        marker=dict(
            color=colors,
            pattern=dict(shape=patterns, solidity=0.6),
        ),
        hovertemplate="Hora %{x}h<br>Ejecuciones: %{y}<br>% OK medio: %{customdata:.1f}%<extra></extra>",
        customdata=hourly["xOK"],
    ))
    fig.update_layout(
        title=f"Distribución por hora — {proyecto}",
        xaxis=dict(title="Hora del día", dtick=1, gridcolor=C["grid"]),
        yaxis=dict(title="N.º ejecuciones", gridcolor=C["grid"]),
        plot_bgcolor="white", paper_bgcolor="white",
        height=280, margin=dict(l=0, r=20, t=40, b=0),
        font=dict(family="Space Grotesk, sans-serif", size=12),
    )
    return fig


def _chart_volumen(df: pd.DataFrame, proyecto: str) -> go.Figure:
    """Grafico de area: volumen de nTotalEjecuciones en el tiempo."""
    daily = (
        df.groupby("nFecha_ejecucion")["nTotalEjecuciones"]
        .sum()
        .reset_index()
    )
    daily["fecha_dt"] = pd.to_datetime(daily["nFecha_ejecucion"].astype(str), format="%Y%m%d")
    daily = daily.sort_values("fecha_dt")

    fig = go.Figure(go.Scatter(
        x=daily["fecha_dt"], y=daily["nTotalEjecuciones"],
        fill="tozeroy", mode="lines",
        line=dict(color=C["accent"], width=1.5),
        fillcolor=C["accent"] + "26",
        hovertemplate="%{x|%d/%m/%Y}<br>Total ejecuciones: %{y:,}<extra></extra>",
    ))
    fig.update_layout(
        title=f"Volumen de ejecuciones — {proyecto}",
        yaxis=dict(gridcolor=C["grid"]),
        xaxis=dict(gridcolor=C["grid"]),
        plot_bgcolor="white", paper_bgcolor="white",
        height=260, margin=dict(l=0, r=20, t=40, b=0),
        font=dict(family="Space Grotesk, sans-serif", size=12),
    )
    return fig


# ---------------------------------------------------------------------------
# Panel de ultima ejecucion
# ---------------------------------------------------------------------------

def _panel_ultima_ejecucion(row: pd.Series) -> None:
    """Muestra el desglose detallado de la ultima ejecucion."""
    fecha_str = _fecha_int_to_str(int(row["nFecha_ejecucion"]))
    hora = int(row["Hora_ejecucion"])
    minuto = int(row["Minuto_ejecucion"])

    xok = row["xEjecutadosOK"]
    err_proc = int(row["nErrorProc"])
    ck_xok = "ok" if xok >= 90 else ("warn" if xok >= 80 else "crit")
    ck_err  = "crit" if err_proc > 0 else ""

    proc_html = (
        mini_stat_html("En espera", int(row["nEsperaProc"]))
        + mini_stat_html("En ejecución", int(row["nEnEjecucionProc"]))
        + mini_stat_html("Con error", err_proc, ck_err)
        + mini_stat_html("Ejec. OK", int(row["nEjecutadosOkProc"]))
        + mini_stat_html("% OK", f"{xok:.1f} %", ck_xok)
    )
    inst_html = (
        mini_stat_html("En espera", int(row["nEsperaInst"]))
        + mini_stat_html("En ejecución", int(row["nEnEjecucionInst"]))
        + mini_stat_html("Con error", int(row["nErrorInst"]),
                         "crit" if row["nErrorInst"] > 0 else "")
        + mini_stat_html("Ejec. OK", int(row["nEjecutadosOkInst"]))
    )

    from src.ui.styles import C, section_title_html
    body = (
        section_title_html("Procesos")
        + f'<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:1px;'
          f'background:{C["divider"]};border:1px solid {C["border"]};'
          f'border-radius:8px;overflow:hidden;margin-bottom:16px">'
        + proc_html + '</div>'
        + section_title_html("Instalaciones")
        + f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;'
          f'background:{C["divider"]};border:1px solid {C["border"]};'
          f'border-radius:8px;overflow:hidden">'
        + inst_html + '</div>'
    )
    st.markdown(
        f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
        f'border-radius:10px;overflow:hidden;margin-bottom:16px">'
        f'<div style="padding:12px 16px;border-bottom:1px solid {C["divider"]};'
        f'display:flex;align-items:center;gap:12px">'
        f'<span style="font-size:13px;font-weight:600;color:{C["text"]}">Última ejecución — desglose</span>'
        f'<span style="font-size:11px;font-family:\'JetBrains Mono\',monospace;'
        f'color:{C["text3"]}">{fecha_str} · {hora:02d}:{minuto:02d}</span>'
        f'</div>'
        f'<div style="padding:16px">{body}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Vista principal
# ---------------------------------------------------------------------------

def render(repo: BaseRepository) -> None:
    """Renderiza la Vista 2 — Detalle por proyecto."""
    st.markdown('<h2 style="margin-bottom:4px;font-size:20px;font-weight:600">Detalle por proyecto</h2>', unsafe_allow_html=True)

    proyectos = _load_projects(repo)
    if not proyectos:
        st.error("No hay proyectos disponibles en los datos.")
        return

    # --- Selector de proyecto ---
    col_sel, col_empty = st.columns([2, 3])
    with col_sel:
        proyecto = st.selectbox("Selecciona un proyecto", proyectos)

    df_proyecto = _load_by_project(repo, proyecto)
    if df_proyecto.empty:
        st.warning(f"Sin datos para el proyecto '{proyecto}'.")
        return

    # --- Filtros ---
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
            estados_sel = st.multiselect(
                "Estado",
                options=["OK", "REGULAR", "CRITICO"],
                default=["OK", "REGULAR", "CRITICO"],
            )

    # Aplicar filtros
    desde_int = int(desde.strftime("%Y%m%d"))
    hasta_int = int(hasta.strftime("%Y%m%d"))
    df_fil = df_proyecto[
        (df_proyecto["nFecha_ejecucion"] >= desde_int) &
        (df_proyecto["nFecha_ejecucion"] <= hasta_int)
    ].copy()

    if df_fil.empty:
        st.warning("No hay datos en el rango de fechas seleccionado.")
        return

    df_fil["Estado"] = df_fil["xEjecutadosOK"].apply(
        lambda x: _clasificar_estado(x, proyecto)
    )
    if estados_sel:
        df_fil = df_fil[df_fil["Estado"].isin(estados_sel)]

    if df_fil.empty:
        st.warning("Ningun registro coincide con los filtros seleccionados.")
        return

    st.caption(f"{len(df_fil):,} ejecuciones en el rango seleccionado")

    # --- Ultima ejecucion (del rango filtrado) ---
    ultima = df_fil.sort_values(
        ["nFecha_ejecucion", "Hora_ejecucion", "Minuto_ejecucion"], ascending=False
    ).iloc[0]
    _panel_ultima_ejecucion(ultima)

    st.divider()

    # --- Graficos ---
    st.plotly_chart(_chart_evolucion(df_fil, proyecto), use_container_width=True)

    gc1, gc2 = st.columns(2)
    with gc1:
        st.plotly_chart(_chart_por_hora(df_fil, proyecto), use_container_width=True)
    with gc2:
        st.plotly_chart(_chart_volumen(df_fil, proyecto), use_container_width=True)

    st.divider()

    # --- Tabla historica ---
    st.markdown("#### Historico de ejecuciones")
    tabla = df_fil[[
        "nFecha_ejecucion", "Hora_ejecucion", "Minuto_ejecucion",
        "nTotalEjecuciones", "nEjecutadosOkProc", "nErrorProc",
        "xEjecutadosOK", "xError", "Estado",
    ]].copy()
    tabla["Fecha"] = tabla["nFecha_ejecucion"].apply(_fecha_int_to_str)
    tabla["Hora"] = tabla.apply(
        lambda r: f"{int(r['Hora_ejecucion']):02d}:{int(r['Minuto_ejecucion']):02d}", axis=1
    )
    tabla = tabla.rename(columns={
        "nTotalEjecuciones": "Total",
        "nEjecutadosOkProc": "OK (proc)",
        "nErrorProc": "Error (proc)",
        "xEjecutadosOK": "% OK",
        "xError": "% Error",
    })
    tabla = tabla[["Fecha", "Hora", "Total", "OK (proc)", "Error (proc)", "% OK", "% Error", "Estado"]]
    tabla = tabla.sort_values(["nFecha_ejecucion", "Hora_ejecucion", "Minuto_ejecucion"],
                               ascending=False).drop(
        columns=["nFecha_ejecucion", "Hora_ejecucion", "Minuto_ejecucion"], errors="ignore"
    )

    st.dataframe(
        tabla.reset_index(drop=True),
        use_container_width=True,
        height=350,
        column_config={
            "% OK": st.column_config.NumberColumn(format="%.1f %%"),
            "% Error": st.column_config.NumberColumn(format="%.1f %%"),
        },
    )

"""Vista 3 — Operativa diaria: timeline del día y detección de inactividad."""

from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.core.data_access.base_repository import BaseRepository
from src.domain.models import ALL_PROJECTS, PROYECTOS_GRUPO_A
from src.utils.date_utils import int_to_date
from src.ui.styles import C, day_kpi_strip_html, section_title_html, badge_html


@st.cache_data(ttl=60, show_spinner=False)
def _load_all(_repo):
    return _repo.get_all_executions()


@st.cache_data(ttl=60, show_spinner=False)
def _load_range(_repo, start, end):
    return _repo.get_executions_in_range(start, end)


_STATUS_PATTERNS = {"OK": "", "REGULAR": "/", "CRITICO": "x"}


def _clasificar_estado(xok: float, proyecto: str) -> str:
    if proyecto in PROYECTOS_GRUPO_A:
        return "OK" if xok == 100.0 else "CRITICO"
    if xok >= 90.0:
        return "OK"
    if xok >= 80.0:
        return "REGULAR"
    return "CRITICO"


def _parse_dt(s) -> datetime | None:
    if pd.isna(s) or not s:
        return None
    try:
        return datetime.strptime(str(s)[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Estado"]   = df.apply(lambda r: _clasificar_estado(r["xEjecutadosOK"], r["proyecto"]), axis=1)
    df["Inicio"]   = df["dFech_Ini_Carga"].apply(_parse_dt)
    df["Fin"]      = df["dFech_Fin_Carga"].apply(_parse_dt)
    df["Hora_fmt"] = df.apply(
        lambda r: f"{int(r['Hora_ejecucion']):02d}:{int(r['Minuto_ejecucion']):02d}", axis=1
    )
    return df


# ---------------------------------------------------------------------------
# Gantt
# ---------------------------------------------------------------------------

def _gantt(df: pd.DataFrame, fecha_sel: date) -> go.Figure:
    df_gantt = df.dropna(subset=["Inicio", "Fin"]).copy()
    if df_gantt.empty:
        return _gantt_puntos(df, fecha_sel)

    df_gantt["Fin"] = df_gantt.apply(
        lambda r: r["Fin"] if r["Fin"] > r["Inicio"] else r["Inicio"] + timedelta(minutes=1),
        axis=1,
    )
    fig = px.timeline(
        df_gantt, x_start="Inicio", x_end="Fin", y="proyecto",
        color="Estado", color_discrete_map={"OK": C["ok"], "REGULAR": C["warn"], "CRITICO": C["crit"]},
        pattern_shape="Estado", pattern_shape_map=_STATUS_PATTERNS,
        hover_data={"xEjecutadosOK": ":.1f", "nTotalEjecuciones": True,
                    "Hora_fmt": True, "Estado": True, "Inicio": False, "Fin": False},
        labels={"proyecto": "Proyecto", "xEjecutadosOK": "% OK",
                "nTotalEjecuciones": "Total ejec.", "Hora_fmt": "Hora"},
        category_orders={"proyecto": sorted(ALL_PROJECTS)},
    )
    dia_ini = datetime(fecha_sel.year, fecha_sel.month, fecha_sel.day, 0, 0)
    dia_fin = datetime(fecha_sel.year, fecha_sel.month, fecha_sel.day, 23, 59)
    fig.update_xaxes(range=[dia_ini, dia_fin], tickformat="%H:%M")
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=360, margin=dict(l=0, r=10, t=8, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="Hora del día", yaxis_title="",
    )
    return fig


def _gantt_puntos(df: pd.DataFrame, fecha_sel: date) -> go.Figure:
    fig = go.Figure()
    for estado, color in {"OK": C["ok"], "REGULAR": C["warn"], "CRITICO": C["crit"]}.items():
        sub = df[df["Estado"] == estado]
        if sub.empty:
            continue
        x_vals = sub["Hora_ejecucion"] + sub["Minuto_ejecucion"] / 60
        fig.add_trace(go.Scatter(
            x=x_vals, y=sub["proyecto"], mode="markers", name=estado,
            marker=dict(color=color, size=12,
                        symbol="circle" if estado == "OK" else
                               "triangle-up" if estado == "REGULAR" else "x"),
            hovertemplate="%{y}<br>Hora: %{customdata[0]}<br>% OK: %{customdata[1]:.1f}%<extra></extra>",
            customdata=sub[["Hora_fmt", "xEjecutadosOK", "nTotalEjecuciones"]].values,
        ))
    fig.update_layout(
        xaxis=dict(range=[0, 24], dtick=2, title="Hora del día"),
        yaxis=dict(title="", categoryorder="category ascending"),
        height=360, margin=dict(l=0, r=10, t=8, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ---------------------------------------------------------------------------
# Tabla de inactividad
# ---------------------------------------------------------------------------

def _tabla_inactividad(df_all: pd.DataFrame, now: datetime, umbral_h: int) -> pd.DataFrame:
    limite = now - timedelta(hours=umbral_h)
    fecha_str = df_all["nFecha_ejecucion"].astype(int).astype(str)
    hora_str  = df_all["Hora_ejecucion"].astype(int).astype(str).str.zfill(2)
    min_str   = df_all["Minuto_ejecucion"].astype(int).astype(str).str.zfill(2)

    last = (
        df_all.assign(dt=pd.to_datetime(fecha_str + hora_str + min_str, format="%Y%m%d%H%M"))
        .sort_values("dt", ascending=False)
        .groupby("proyecto", as_index=False).first()
        [["proyecto", "dt", "xEjecutadosOK"]]
    )

    rows = []
    for proyecto in sorted(ALL_PROJECTS):
        fila = last[last["proyecto"] == proyecto]
        if fila.empty:
            rows.append({
                "Proyecto": proyecto, "Última ejecución": "Sin datos",
                "Horas transcurridas": None, "Estado": "SIN DATOS", "% OK (últ.)": None,
            })
        else:
            dt  = fila.iloc[0]["dt"]
            xok = fila.iloc[0]["xEjecutadosOK"]
            horas = (now - dt).total_seconds() / 3600
            activo = dt > limite
            rows.append({
                "Proyecto": proyecto,
                "Última ejecución": dt.strftime("%d/%m/%Y %H:%M"),
                "Horas transcurridas": round(horas, 1),
                "Estado": "ACTIVO" if activo else "INACTIVO",
                "% OK (últ.)": round(xok, 2),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Vista principal
# ---------------------------------------------------------------------------

def render(repo: BaseRepository) -> None:
    now = datetime.now()
    df_all = _load_all(repo)
    fecha_max = int_to_date(int(df_all["nFecha_ejecucion"].max()))

    st.markdown(
        '<h2 style="font-family:Inter,sans-serif;font-size:22px;'
        'font-weight:600;color:var(--dd-text);letter-spacing:-0.02em;margin:0 0 4px">Operativa diaria</h2>'
        '<p style="font-family:\'JetBrains Mono\',monospace;font-size:12px;color:var(--dd-text3);margin:0 0 16px">'
        'Vista operacional · ejecuciones del d&#237;a y an&#225;lisis de inactividad</p>',
        unsafe_allow_html=True,
    )

    # Controles
    ctrl1, ctrl2 = st.columns([2, 2])
    with ctrl1:
        fecha_sel = st.date_input(
            "Fecha", value=fecha_max,
            min_value=int_to_date(int(df_all["nFecha_ejecucion"].min())),
            max_value=fecha_max,
        )
    with ctrl2:
        umbral_h = st.slider("Umbral de inactividad (h)", 1, 72, 24, 1)

    # Datos del día
    df_dia = _load_range(repo, fecha_sel, fecha_sel)

    st.markdown(section_title_html(f"Ejecuciones del día · {fecha_sel.strftime('%d/%m/%Y')}"), unsafe_allow_html=True)

    if df_dia.empty:
        st.warning(f"No hay ejecuciones registradas el {fecha_sel.strftime('%d/%m/%Y')}.")
    else:
        df_dia = _enrich(df_dia)

        # KPI strip
        st.markdown(day_kpi_strip_html(
            ejecuciones=len(df_dia),
            proyectos=df_dia["proyecto"].nunique(),
            total_proy=len(ALL_PROJECTS),
            pct_ok=df_dia["xEjecutadosOK"].mean(),
            total_proc=int(df_dia["nTotalEjecuciones"].sum()),
        ), unsafe_allow_html=True)

        # Gantt
        st.plotly_chart(_gantt(df_dia, fecha_sel), use_container_width=True)

        with st.expander("Resumen de ejecuciones del día"):
            resumen = (
                df_dia.groupby("proyecto")
                .agg(
                    Ejecuciones=("Id", "count"),
                    xOK_medio=("xEjecutadosOK", "mean"),
                    Total_proc=("nTotalEjecuciones", "sum"),
                    Errores=("nErrorProc", "sum"),
                )
                .reset_index()
                .rename(columns={
                    "proyecto": "Proyecto", "xOK_medio": "% OK medio",
                    "Total_proc": "Total procesos", "Errores": "Procesos con error",
                })
            )
            resumen["% OK medio"] = resumen["% OK medio"].round(2)
            st.dataframe(resumen, use_container_width=True, hide_index=True,
                         column_config={"% OK medio": st.column_config.NumberColumn(format="%.1f %%")})

    # Inactividad
    st.markdown(section_title_html(f"Análisis de inactividad · umbral {umbral_h} h"), unsafe_allow_html=True)
    tabla_act = _tabla_inactividad(df_all, now, umbral_h)

    inactivos = tabla_act[tabla_act["Estado"] == "INACTIVO"]
    if not inactivos.empty:
        st.error(
            f"{len(inactivos)} proyecto(s) sin ejecución en las últimas {umbral_h} h: "
            + ", ".join(inactivos["Proyecto"].tolist())
        )
    else:
        st.success(f"Todos los proyectos han ejecutado en las últimas {umbral_h} h.")

    st.dataframe(
        tabla_act, use_container_width=True, hide_index=True,
        column_config={
            "% OK (últ.)": st.column_config.NumberColumn(format="%.2f %%"),
            "Horas transcurridas": st.column_config.NumberColumn(format="%.1f h"),
        },
    )

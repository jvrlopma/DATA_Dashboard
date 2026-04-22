"""Vista 3 — Operativa diaria: timeline del dia y deteccion de proyectos inactivos."""

from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.core.data_access.base_repository import BaseRepository
from src.domain.models import ALL_PROJECTS, PROYECTOS_GRUPO_A
from src.utils.date_utils import int_to_date

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STATUS_COLORS = {"OK": "#28a745", "REGULAR": "#ffc107", "CRITICO": "#dc3545"}
_STATUS_ICONS  = {"OK": "✅", "REGULAR": "⚠️", "CRITICO": "❌"}


def _clasificar_estado(xok: float, proyecto: str) -> str:
    if proyecto in PROYECTOS_GRUPO_A:
        return "OK" if xok == 100.0 else "CRITICO"
    if xok >= 90.0:
        return "OK"
    if xok >= 80.0:
        return "REGULAR"
    return "CRITICO"


def _parse_dt(s) -> datetime | None:
    """Parsea un string datetime del Excel; devuelve None si es nulo/invalido."""
    if pd.isna(s) or not s:
        return None
    try:
        return datetime.strptime(str(s)[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Anade columnas derivadas utiles para la vista."""
    df = df.copy()
    df["Estado"] = df.apply(lambda r: _clasificar_estado(r["xEjecutadosOK"], r["proyecto"]), axis=1)
    df["Inicio"] = df["dFech_Ini_Carga"].apply(_parse_dt)
    df["Fin"]    = df["dFech_Fin_Carga"].apply(_parse_dt)
    df["Hora_fmt"] = df.apply(
        lambda r: f"{int(r['Hora_ejecucion']):02d}:{int(r['Minuto_ejecucion']):02d}", axis=1
    )
    return df


# ---------------------------------------------------------------------------
# Grafico Gantt
# ---------------------------------------------------------------------------

def _gantt(df: pd.DataFrame, fecha_sel: date) -> go.Figure:
    """Gantt simplificado: cada ejecucion como barra de duracion real."""
    df_gantt = df.dropna(subset=["Inicio", "Fin"]).copy()

    if df_gantt.empty:
        # Fallback: puntos sin duracion
        return _gantt_puntos(df, fecha_sel)

    # Asegurar que Fin >= Inicio (minimo 1 minuto para visibilidad)
    df_gantt["Fin"] = df_gantt.apply(
        lambda r: r["Fin"] if r["Fin"] > r["Inicio"] else r["Inicio"] + timedelta(minutes=1),
        axis=1,
    )

    fig = px.timeline(
        df_gantt,
        x_start="Inicio",
        x_end="Fin",
        y="proyecto",
        color="Estado",
        color_discrete_map=_STATUS_COLORS,
        hover_data={"xEjecutadosOK": ":.1f", "nTotalEjecuciones": True,
                    "Hora_fmt": True, "Estado": True,
                    "Inicio": False, "Fin": False},
        labels={"proyecto": "Proyecto", "xEjecutadosOK": "% OK",
                "nTotalEjecuciones": "Total ejec.", "Hora_fmt": "Hora"},
        category_orders={"proyecto": sorted(ALL_PROJECTS)},
    )

    # Rango X = dia completo seleccionado
    dia_ini = datetime(fecha_sel.year, fecha_sel.month, fecha_sel.day, 0, 0)
    dia_fin = datetime(fecha_sel.year, fecha_sel.month, fecha_sel.day, 23, 59)
    fig.update_xaxes(range=[dia_ini, dia_fin], tickformat="%H:%M")
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=320,
        margin=dict(l=0, r=10, t=10, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="Hora del dia",
        yaxis_title="",
    )
    return fig


def _gantt_puntos(df: pd.DataFrame, fecha_sel: date) -> go.Figure:
    """Fallback: scatter de puntos por hora cuando no hay duraciones."""
    fig = go.Figure()
    for estado, color in _STATUS_COLORS.items():
        sub = df[df["Estado"] == estado]
        if sub.empty:
            continue
        x_vals = sub["Hora_ejecucion"] + sub["Minuto_ejecucion"] / 60
        fig.add_trace(go.Scatter(
            x=x_vals, y=sub["proyecto"], mode="markers",
            name=estado,
            marker=dict(color=color, size=12,
                        symbol="circle" if estado == "OK" else
                               "triangle-up" if estado == "REGULAR" else "x"),
            hovertemplate=(
                "%{y}<br>Hora: %{customdata[0]}<br>"
                "% OK: %{customdata[1]:.1f}%<br>"
                "Total ejec.: %{customdata[2]}<extra></extra>"
            ),
            customdata=sub[["Hora_fmt", "xEjecutadosOK", "nTotalEjecuciones"]].values,
        ))
    fig.update_layout(
        xaxis=dict(range=[0, 24], dtick=2, tickformat="%H:00",
                   title="Hora del dia", gridcolor="#eee"),
        yaxis=dict(title="", gridcolor="#eee", categoryorder="category ascending"),
        height=320, plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0, r=10, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ---------------------------------------------------------------------------
# Deteccion de inactividad
# ---------------------------------------------------------------------------

def _tabla_inactividad(df_all: pd.DataFrame, now: datetime, umbral_h: int) -> pd.DataFrame:
    """Construye una tabla con el estado de actividad de cada proyecto."""
    limite = now - timedelta(hours=umbral_h)

    last = (
        df_all.assign(
            dt=df_all.apply(
                lambda r: datetime(
                    *[int(x) for x in [
                        str(int(r["nFecha_ejecucion"]))[:4],
                        str(int(r["nFecha_ejecucion"]))[4:6],
                        str(int(r["nFecha_ejecucion"]))[6:8],
                        int(r["Hora_ejecucion"]),
                        int(r["Minuto_ejecucion"]),
                    ]]
                ),
                axis=1,
            )
        )
        .sort_values("dt", ascending=False)
        .groupby("proyecto", as_index=False)
        .first()[["proyecto", "dt", "xEjecutadosOK"]]
    )

    rows = []
    for proyecto in sorted(ALL_PROJECTS):
        fila = last[last["proyecto"] == proyecto]
        if fila.empty:
            rows.append({
                "Proyecto": proyecto,
                "Ultima ejecucion": "Sin datos",
                "Horas desde ult. ejec.": None,
                "Estado actividad": "⚫ Sin datos",
                "% OK (ult.)": None,
            })
        else:
            dt = fila.iloc[0]["dt"]
            xok = fila.iloc[0]["xEjecutadosOK"]
            horas = (now - dt).total_seconds() / 3600
            activo = dt > limite
            rows.append({
                "Proyecto": proyecto,
                "Ultima ejecucion": dt.strftime("%d/%m/%Y %H:%M"),
                "Horas desde ult. ejec.": round(horas, 1),
                "Estado actividad": "✅ Activo" if activo else "❌ Inactivo",
                "% OK (ult.)": round(xok, 2),
            })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Vista principal
# ---------------------------------------------------------------------------

def render(repo: BaseRepository) -> None:
    """Renderiza la Vista 3 — Operativa diaria."""
    st.title("Operativa diaria")

    df_all = repo.get_all_executions()
    fecha_max = int_to_date(int(df_all["nFecha_ejecucion"].max()))
    now = datetime.now()

    # --- Controles ---
    ctrl1, ctrl2 = st.columns([2, 2])
    with ctrl1:
        fecha_sel = st.date_input(
            "Fecha a visualizar",
            value=fecha_max,
            min_value=int_to_date(int(df_all["nFecha_ejecucion"].min())),
            max_value=fecha_max,
        )
    with ctrl2:
        umbral_h = st.slider(
            "Umbral de inactividad (horas)", min_value=1, max_value=72, value=24, step=1
        )

    st.divider()

    # --- Datos del dia seleccionado ---
    df_dia = repo.get_executions_in_range(fecha_sel, fecha_sel)

    st.subheader(f"Timeline — {fecha_sel.strftime('%d/%m/%Y')}")

    if df_dia.empty:
        st.warning(f"No hay ejecuciones registradas el {fecha_sel.strftime('%d/%m/%Y')}.")
    else:
        df_dia = _enrich(df_dia)

        # KPIs del dia
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Ejecuciones", len(df_dia))
        k2.metric("Proyectos activos", df_dia["proyecto"].nunique())
        k3.metric("% OK medio", f"{df_dia['xEjecutadosOK'].mean():.1f} %")
        k4.metric("Total procesos", f"{df_dia['nTotalEjecuciones'].sum():,}")

        # Gantt
        st.plotly_chart(_gantt(df_dia, fecha_sel), use_container_width=True)

        # Tabla resumen del dia
        with st.expander("Resumen de ejecuciones del dia"):
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
                    "proyecto": "Proyecto",
                    "xOK_medio": "% OK medio",
                    "Total_proc": "Total procesos",
                    "Errores": "Procesos con error",
                })
            )
            resumen["% OK medio"] = resumen["% OK medio"].round(2)
            st.dataframe(resumen, use_container_width=True, hide_index=True,
                         column_config={"% OK medio": st.column_config.NumberColumn(format="%.1f %%")})

    st.divider()

    # --- Deteccion de inactividad ---
    st.subheader(f"Deteccion de inactividad (umbral: {umbral_h} h)")
    tabla_act = _tabla_inactividad(df_all, now, umbral_h)

    inactivos = tabla_act[tabla_act["Estado actividad"].str.startswith("❌")]
    if not inactivos.empty:
        st.error(
            f"{len(inactivos)} proyecto(s) sin ejecucion en las ultimas {umbral_h} horas: "
            + ", ".join(inactivos["Proyecto"].tolist())
        )
    else:
        st.success(f"Todos los proyectos han ejecutado en las ultimas {umbral_h} horas.")

    st.dataframe(
        tabla_act,
        use_container_width=True,
        hide_index=True,
        column_config={
            "% OK (ult.)": st.column_config.NumberColumn(format="%.2f %%"),
            "Horas desde ult. ejec.": st.column_config.NumberColumn(format="%.1f h"),
        },
    )

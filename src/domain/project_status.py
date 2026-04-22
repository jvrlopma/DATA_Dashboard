"""Logica pura de calculo del estado de salud de proyectos ETL.

Reglas de negocio generales:

Grupo A — proyectos criticos (deben estar al 100 %):
    AqualiaApemsa, AqualiaDW, AqualiaSII2_FICO, Aqualia_Diario
    - xEjecutadosOK == 100  ->  OK
    - xEjecutadosOK  < 100  ->  CRITICO

Grupo B — proyectos con tolerancia:
    AqualiaODS, AqualiaSII2_Doc_AEF, AqualiaTPL, Aqualia_GIS
    - xEjecutadosOK >= 90            ->  OK
    - xEjecutadosOK >= 80 y < 90    ->  REGULAR
    - xEjecutadosOK  < 80            ->  CRITICO

Proyectos con cadencia especial:

AqualiaTPL — ejecucion diaria diferida:
    Procesa datos del dia anterior (D-1). La ejecucion llega a BD
    entre las 13:00 y 15:00 del dia D. Antes de esa hora, el registro
    mas reciente es del dia D-1. Se usa ventana de inactividad de 48h
    para no marcar como "sin datos" durante la manana del dia D.

Aqualia_GIS — ejecucion mensual (dias 6-10):
    - Si ejecuto en dias 6-10 del mes actual (o anterior si hoy < 6) -> OK
    - Si hoy esta en dias 6-10 y aun no ejecuto -> REGULAR (pendiente)
    - Si la ventana 6-10 ya paso sin ejecucion -> CRITICO
"""

from datetime import datetime, timedelta

import pandas as pd

from src.domain.models import (
    ALL_PROJECTS,
    PROYECTOS_GRUPO_A,
    PROYECTOS_GRUPO_B,
    Execution,
    ProjectHealth,
    ProjectStatus,
)
from src.utils.date_utils import build_datetime

_GIS_PROYECTO = "Aqualia_GIS"
_TPL_PROYECTO = "AqualiaTPL"

# ---------------------------------------------------------------------------
# Logica de estado (funciones puras)
# ---------------------------------------------------------------------------


def _status_grupo_a(xok: float) -> ProjectStatus:
    """Calcula el estado para proyectos del Grupo A (umbral 100 %)."""
    return ProjectStatus.OK if xok == 100.0 else ProjectStatus.CRITICO


def _status_grupo_b(xok: float) -> ProjectStatus:
    """Calcula el estado para proyectos del Grupo B (umbrales 90 % / 80 %)."""
    if xok >= 90.0:
        return ProjectStatus.OK
    if xok >= 80.0:
        return ProjectStatus.REGULAR
    return ProjectStatus.CRITICO


def _gis_window(year: int, month: int) -> tuple[int, int]:
    """Retorna (fecha_inicio, fecha_fin) YYYYMMDD de la ventana días 6-10 del mes."""
    return int(f"{year}{month:02d}06"), int(f"{year}{month:02d}10")


def _compute_gis_health(df_gis: pd.DataFrame, now: datetime) -> ProjectHealth:
    """Aqualia_GIS: OK si ejecutó en días 6-10 del mes relevante.

    Mes relevante:
    - Si hoy < día 6: mes anterior (la ventana de este mes aún no abre)
    - Si hoy >= día 6: mes actual
    """
    today = now.date()
    day, month, year = today.day, today.month, today.year

    if day < 6:
        check_year = year - 1 if month == 1 else year
        check_month = 12 if month == 1 else month - 1
        in_window = False
    else:
        check_year, check_month = year, month
        in_window = (day <= 10)

    w_start, w_end = _gis_window(check_year, check_month)
    df_w = df_gis[
        (df_gis["nFecha_ejecucion"] >= w_start) &
        (df_gis["nFecha_ejecucion"] <= w_end)
    ]

    if df_w.empty:
        if in_window:
            # Días 6-10, aún sin ejecución → pendiente (no crítico todavía)
            return ProjectHealth(
                proyecto=_GIS_PROYECTO,
                estado=ProjectStatus.REGULAR,
                xEjecutadosOK=None,
                ultima_ejecucion=None,
                sin_datos_recientes=False,
            )
        # Fuera de ventana sin ejecución → crítico
        return ProjectHealth(
            proyecto=_GIS_PROYECTO,
            estado=ProjectStatus.CRITICO,
            xEjecutadosOK=None,
            ultima_ejecucion=None,
            sin_datos_recientes=True,
        )

    best = df_w.loc[df_w["xEjecutadosOK"].idxmax()]
    exec_ = execution_from_row(best)
    return ProjectHealth(
        proyecto=_GIS_PROYECTO,
        estado=_status_grupo_b(exec_.xEjecutadosOK),
        xEjecutadosOK=exec_.xEjecutadosOK,
        ultima_ejecucion=exec_.datetime_ejecucion,
        sin_datos_recientes=False,
    )


def compute_status(proyecto: str, xEjecutadosOK: float) -> ProjectStatus:
    """Devuelve el estado de un proyecto dado su % de ejecuciones OK.

    Args:
        proyecto:       Nombre exacto del proyecto ETL.
        xEjecutadosOK: Porcentaje de procesos ejecutados OK (0-100).

    Returns:
        ProjectStatus correspondiente segun las reglas de negocio.

    Raises:
        ValueError: Si el nombre del proyecto no pertenece a ningun grupo conocido.
    """
    if proyecto in PROYECTOS_GRUPO_A:
        return _status_grupo_a(xEjecutadosOK)
    if proyecto in PROYECTOS_GRUPO_B:
        return _status_grupo_b(xEjecutadosOK)
    raise ValueError(
        f"Proyecto desconocido: '{proyecto}'. "
        f"Proyectos validos: {sorted(ALL_PROJECTS)}"
    )


def compute_project_health(
    proyecto: str,
    last_execution: Execution | None,
    now: datetime,
    inactivity_hours: int = 24,
) -> ProjectHealth:
    """Calcula el estado de salud completo de un proyecto.

    Args:
        proyecto:          Nombre del proyecto ETL.
        last_execution:    Ultima ejecucion conocida, o None si no hay datos.
        now:               Momento actual (inyectado para facilitar los tests).
        inactivity_hours:  Horas sin ejecucion para considerar el proyecto inactivo.

    Returns:
        ProjectHealth con el estado calculado.
    """
    limite = now - timedelta(hours=inactivity_hours)

    if last_execution is None or last_execution.datetime_ejecucion <= limite:
        return ProjectHealth(
            proyecto=proyecto,
            estado=ProjectStatus.CRITICO,
            xEjecutadosOK=None,
            ultima_ejecucion=last_execution.datetime_ejecucion if last_execution else None,
            sin_datos_recientes=True,
        )

    estado = compute_status(proyecto, last_execution.xEjecutadosOK)
    return ProjectHealth(
        proyecto=proyecto,
        estado=estado,
        xEjecutadosOK=last_execution.xEjecutadosOK,
        ultima_ejecucion=last_execution.datetime_ejecucion,
        sin_datos_recientes=False,
    )


# ---------------------------------------------------------------------------
# Adaptador DataFrame -> dominio
# ---------------------------------------------------------------------------


def execution_from_row(row: pd.Series) -> Execution:
    """Construye un Execution a partir de una fila de DataFrame del repositorio.

    Args:
        row: Fila del DataFrame devuelto por BaseRepository.

    Returns:
        Instancia de Execution.
    """
    return Execution(
        id=int(row["Id"]),
        proyecto=str(row["proyecto"]),
        nFecha_ejecucion=int(row["nFecha_ejecucion"]),
        hora_ejecucion=int(row["Hora_ejecucion"]),
        minuto_ejecucion=int(row["Minuto_ejecucion"]),
        nTotalEjecuciones=int(row["nTotalEjecuciones"]),
        nEjecutadosOkProc=int(row["nEjecutadosOkProc"]),
        nErrorProc=int(row["nErrorProc"]),
        nEsperaProc=int(row["nEsperaProc"]),
        nEnEjecucionProc=int(row["nEnEjecucionProc"]),
        nTotalInstalaciones=int(row["nTotalInstalaciones"]),
        nEjecutadosOkInst=int(row["nEjecutadosOkInst"]),
        nErrorInst=int(row["nErrorInst"]),
        nEsperaInst=int(row["nEsperaInst"]),
        nEnEjecucionInst=int(row["nEnEjecucionInst"]),
        xEjecutadosOK=float(row["xEjecutadosOK"]),
        xError=float(row["xError"]),
        xEspera=float(row["xEspera"]),
        xEnEjecucion=float(row["xEnEjecucion"]),
        datetime_ejecucion=build_datetime(
            int(row["nFecha_ejecucion"]),
            int(row["Hora_ejecucion"]),
            int(row["Minuto_ejecucion"]),
        ),
    )


def get_all_project_health(
    repo_df_last: pd.DataFrame,
    now: datetime,
    inactivity_hours: int = 24,
    df_gis: pd.DataFrame | None = None,
) -> list[ProjectHealth]:
    """Calcula el estado de salud de todos los proyectos conocidos.

    Args:
        repo_df_last:     DataFrame con la ultima ejecucion por proyecto
                          (resultado de BaseRepository.get_last_execution_per_project()).
        now:              Momento actual.
        inactivity_hours: Horas sin ejecucion para considerar inactivo (proyectos standard).
        df_gis:           Todas las ejecuciones de Aqualia_GIS (para lógica mensual).
                          Si None, Aqualia_GIS se evalúa con la lógica estándar.

    Returns:
        Lista de ProjectHealth, uno por cada proyecto en ALL_PROJECTS,
        ordenada por severidad (CRITICO primero) y luego alfabeticamente.

    Cadencias especiales:
        AqualiaTPL  — ventana de inactividad 48h (procesa datos D-1, ejecuta 13-15h).
        Aqualia_GIS — ejecución mensual días 6-10; requiere df_gis para lógica correcta.
    """
    last_by_project: dict[str, Execution] = {}
    for _, row in repo_df_last.iterrows():
        exec_ = execution_from_row(row)
        last_by_project[exec_.proyecto] = exec_

    healths: list[ProjectHealth] = []
    for p in ALL_PROJECTS:
        if p == _GIS_PROYECTO and df_gis is not None:
            healths.append(_compute_gis_health(df_gis, now))
        elif p == _TPL_PROYECTO:
            # Ventana 48h: el registro D-1 no debe marcarse como inactivo a primera hora de D
            healths.append(compute_project_health(p, last_by_project.get(p), now, inactivity_hours=48))
        else:
            healths.append(compute_project_health(p, last_by_project.get(p), now, inactivity_hours))

    severity_order = {ProjectStatus.CRITICO: 0, ProjectStatus.REGULAR: 1, ProjectStatus.OK: 2}
    return sorted(healths, key=lambda h: (severity_order[h.estado], h.proyecto))

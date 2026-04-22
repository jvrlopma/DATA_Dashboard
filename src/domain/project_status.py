"""Logica pura de calculo del estado de salud de proyectos ETL.

Reglas de negocio (definidas en PROJECT_SPEC.md, seccion 2.2):

Grupo A — proyectos criticos (deben estar al 100 %):
    AqualiaApemsa, AqualiaDW, AqualiaSII2_FICO, Aqualia_Diario
    - xEjecutadosOK == 100  ->  OK
    - xEjecutadosOK  < 100  ->  CRITICO

Grupo B — proyectos con tolerancia:
    AqualiaODS, AqualiaSII2_Doc_AEF, AqualiaTPL, Aqualia_GIS
    - xEjecutadosOK >= 90            ->  OK
    - xEjecutadosOK >= 80 y < 90    ->  REGULAR
    - xEjecutadosOK  < 80            ->  CRITICO

Estado transversal:
    Sin ejecucion en las ultimas N horas  ->  CRITICO + sin_datos_recientes=True
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
) -> list[ProjectHealth]:
    """Calcula el estado de salud de todos los proyectos conocidos.

    Args:
        repo_df_last:     DataFrame con la ultima ejecucion por proyecto
                          (resultado de BaseRepository.get_last_execution_per_project()).
        now:              Momento actual.
        inactivity_hours: Horas sin ejecucion para considerar inactivo.

    Returns:
        Lista de ProjectHealth, uno por cada proyecto en ALL_PROJECTS,
        ordenada por severidad (CRITICO primero) y luego alfabeticamente.
    """
    last_by_project: dict[str, Execution] = {}
    for _, row in repo_df_last.iterrows():
        exec_ = execution_from_row(row)
        last_by_project[exec_.proyecto] = exec_

    healths = [
        compute_project_health(
            proyecto=p,
            last_execution=last_by_project.get(p),
            now=now,
            inactivity_hours=inactivity_hours,
        )
        for p in ALL_PROJECTS
    ]

    severity_order = {ProjectStatus.CRITICO: 0, ProjectStatus.REGULAR: 1, ProjectStatus.OK: 2}
    return sorted(healths, key=lambda h: (severity_order[h.estado], h.proyecto))

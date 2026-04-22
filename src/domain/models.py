"""Modelos de dominio de DATA_Dashboard."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ProjectStatus(Enum):
    """Estado de salud de un proyecto ETL."""

    OK = "OK"
    REGULAR = "REGULAR"
    CRITICO = "CRITICO"


# Proyectos del Grupo A: deben ejecutar al 100 %
PROYECTOS_GRUPO_A: frozenset[str] = frozenset({
    "AqualiaApemsa",
    "AqualiaDW",
    "AqualiaSII2_FICO",
    "Aqualia_Diario",
})

# Proyectos del Grupo B: tolerancia hasta el 80 %
PROYECTOS_GRUPO_B: frozenset[str] = frozenset({
    "AqualiaODS",
    "AqualiaSII2_Doc_AEF",
    "AqualiaTPL",
    "Aqualia_GIS",
})

# Union de todos los proyectos conocidos
ALL_PROJECTS: frozenset[str] = PROYECTOS_GRUPO_A | PROYECTOS_GRUPO_B


@dataclass(frozen=True)
class Execution:
    """Representa una fila de ejecucion ETL tal como llega del repositorio."""

    id: int
    proyecto: str
    nFecha_ejecucion: int        # YYYYMMDD
    hora_ejecucion: int          # 0-23
    minuto_ejecucion: int        # 0-59
    nTotalEjecuciones: int
    nEjecutadosOkProc: int
    nErrorProc: int
    nEsperaProc: int
    nEnEjecucionProc: int
    nTotalInstalaciones: int
    nEjecutadosOkInst: int
    nErrorInst: int
    nEsperaInst: int
    nEnEjecucionInst: int
    xEjecutadosOK: float         # % ejecutado OK — clave para el estado
    xError: float                # % con error
    xEspera: float
    xEnEjecucion: float
    datetime_ejecucion: datetime  # campo derivado, construido por el repositorio


@dataclass(frozen=True)
class ProjectHealth:
    """Estado de salud calculado para un proyecto en un instante dado."""

    proyecto: str
    estado: ProjectStatus
    xEjecutadosOK: float | None          # None si sin_datos_recientes
    ultima_ejecucion: datetime | None    # None si sin_datos_recientes
    sin_datos_recientes: bool            # True cuando no hay datos en las ultimas N horas

    @property
    def etiqueta_estado(self) -> str:
        """Texto para mostrar en la UI, incluye aviso especial si sin datos."""
        if self.sin_datos_recientes:
            return "Sin datos recientes"
        return self.estado.value

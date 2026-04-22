"""Interfaz abstracta del repositorio de ejecuciones ETL."""

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class BaseRepository(ABC):
    """Contrato que deben cumplir todas las implementaciones de acceso a datos.

    La capa de dominio y la UI solo dependen de esta interfaz, nunca de la
    implementacion concreta (Excel o SQL Server).
    """

    @abstractmethod
    def get_all_executions(self) -> pd.DataFrame:
        """Devuelve todas las ejecuciones disponibles como DataFrame.

        Columnas garantizadas (mismas que la tabla origen):
            Id, nFecha_ejecucion, Hora_ejecucion, Minuto_ejecucion,
            nFecha_Info, proyecto, dFech_Ini_Info, dFech_Fin_Info,
            dFech_Ini_Carga, dFech_Fin_Carga, Estado_proyecto,
            nTotalInstalaciones, nTotalEjecuciones,
            nEsperaProc, nEnEjecucionProc, nErrorProc, nEjecutadosOkProc,
            nEsperaInst, nEnEjecucionInst, nErrorInst, nEjecutadosOkInst,
            xEspera, xEnEjecucion, xError, xEjecutadosOK,
            CREATE_DATE, UPDATE_DATE.
        """

    @abstractmethod
    def get_executions_by_project(self, project: str) -> pd.DataFrame:
        """Devuelve todas las ejecuciones de un proyecto concreto.

        Args:
            project: Nombre exacto del proyecto (ej.: 'AqualiaDW').

        Returns:
            DataFrame con las mismas columnas que get_all_executions(),
            filtrado por el proyecto indicado.
        """

    @abstractmethod
    def get_last_execution_per_project(self) -> pd.DataFrame:
        """Devuelve la ultima ejecucion de cada proyecto.

        La 'ultima' se determina por el mayor valor de nFecha_ejecucion
        y, dentro de la misma fecha, por la mayor Hora_ejecucion + Minuto_ejecucion.

        Returns:
            DataFrame con una fila por proyecto (8 filas como maximo).
        """

    @abstractmethod
    def get_executions_in_range(self, start: date, end: date) -> pd.DataFrame:
        """Devuelve las ejecuciones cuya nFecha_ejecucion esta en [start, end].

        Args:
            start: Fecha de inicio (inclusive), en formato date de Python.
            end:   Fecha de fin (inclusive), en formato date de Python.

        Returns:
            DataFrame filtrado con las mismas columnas que get_all_executions().
        """

    @abstractmethod
    def get_available_projects(self) -> list[str]:
        """Devuelve la lista de proyectos distintos presentes en los datos.

        Returns:
            Lista de strings ordenada alfabeticamente.
        """

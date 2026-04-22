"""Implementacion Excel del repositorio de ejecuciones ETL."""

from datetime import date
from pathlib import Path

import pandas as pd

from src.core.data_access.base_repository import BaseRepository

# Columnas que se deben leer del Excel (las 27 definidas en el spec)
_EXPECTED_COLUMNS: list[str] = [
    "Id", "nFecha_ejecucion", "Hora_ejecucion", "Minuto_ejecucion",
    "nFecha_Info", "proyecto", "dFech_Ini_Info", "dFech_Fin_Info",
    "dFech_Ini_Carga", "dFech_Fin_Carga", "Estado_proyecto",
    "nTotalInstalaciones", "nTotalEjecuciones",
    "nEsperaProc", "nEnEjecucionProc", "nErrorProc", "nEjecutadosOkProc",
    "nEsperaInst", "nEnEjecucionInst", "nErrorInst", "nEjecutadosOkInst",
    "xEspera", "xEnEjecucion", "xError", "xEjecutadosOK",
    "CREATE_DATE", "UPDATE_DATE",
]


class ExcelRepository(BaseRepository):
    """Repositorio que lee datos desde un fichero Excel (.xlsx).

    Carga el fichero una sola vez en memoria al instanciarse y sirve
    todas las consultas desde el DataFrame en RAM. Adecuado para el
    dataset de desarrollo (~10.200 filas).

    Args:
        excel_path: Ruta al fichero .xlsx.
        sheet_name: Nombre de la hoja a leer (por defecto 'Hoja1').
    """

    def __init__(self, excel_path: Path | str, sheet_name: str = "Hoja1") -> None:
        self._path = Path(excel_path)
        self._sheet = sheet_name
        self._df: pd.DataFrame = self._load()

    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------

    def _load(self) -> pd.DataFrame:
        """Lee el Excel y valida que las columnas esperadas existen."""
        if not self._path.exists():
            raise FileNotFoundError(f"Fichero Excel no encontrado: {self._path}")

        df = pd.read_excel(self._path, sheet_name=self._sheet, engine="openpyxl")

        missing = [c for c in _EXPECTED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Columnas faltantes en el Excel: {missing}")

        return df

    # ------------------------------------------------------------------
    # Interfaz publica
    # ------------------------------------------------------------------

    def get_all_executions(self) -> pd.DataFrame:
        """Devuelve todas las ejecuciones como DataFrame (copia)."""
        return self._df.copy()

    def get_executions_by_project(self, project: str) -> pd.DataFrame:
        """Devuelve las ejecuciones de un proyecto concreto.

        Args:
            project: Nombre exacto del proyecto.

        Returns:
            DataFrame filtrado (copia).
        """
        return self._df[self._df["proyecto"] == project].copy()

    def get_last_execution_per_project(self) -> pd.DataFrame:
        """Devuelve la ultima ejecucion de cada proyecto.

        Criterio: mayor nFecha_ejecucion y, en caso de empate,
        mayor Hora_ejecucion y Minuto_ejecucion.
        """
        df = self._df.sort_values(
            ["nFecha_ejecucion", "Hora_ejecucion", "Minuto_ejecucion"],
            ascending=False,
        )
        return df.groupby("proyecto", as_index=False).first()

    def get_executions_in_range(self, start: date, end: date) -> pd.DataFrame:
        """Devuelve las ejecuciones en el rango de fechas [start, end].

        Args:
            start: Fecha de inicio (inclusive).
            end:   Fecha de fin (inclusive).

        Returns:
            DataFrame filtrado (copia).
        """
        start_int = int(start.strftime("%Y%m%d"))
        end_int = int(end.strftime("%Y%m%d"))
        mask = (self._df["nFecha_ejecucion"] >= start_int) & (
            self._df["nFecha_ejecucion"] <= end_int
        )
        return self._df[mask].copy()

    def get_available_projects(self) -> list[str]:
        """Devuelve los proyectos distintos presentes en el Excel."""
        return sorted(self._df["proyecto"].unique().tolist())

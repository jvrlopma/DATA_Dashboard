"""Implementacion SQL Server del repositorio de ejecuciones ETL."""

from datetime import date
from functools import cached_property

import pandas as pd
import urllib.parse

from src.core.data_access.base_repository import BaseRepository

_TABLE = "AqALL_t_PWC_Monitorizacion_CdM"

_COLUMN_MAP = {
    "Id": "Id",
    "nFecha_ejecucion": "nFecha_ejecucion",
    "Hora_ejecucion": "Hora_ejecucion",
    "Minuto_ejecucion": "Minuto_ejecucion",
    "nFecha_Info": "nFecha_Info",
    "proyecto": "proyecto",
    "dFech_Ini_Info": "dFech_Ini_Info",
    "dFech_Fin_Info": "dFech_Fin_Info",
    "dFech_Ini_Carga": "dFech_Ini_Carga",
    "dFech_Fin_Carga": "dFech_Fin_Carga",
    "Estado_proyecto": "Estado_proyecto",
    "nTotalInstalaciones": "nTotalInstalaciones",
    "nTotalEjecuciones": "nTotalEjecuciones",
    "nEsperaProc": "nEsperaProc",
    "nEnEjecucionProc": "nEnEjecucionProc",
    "nErrorProc": "nErrorProc",
    "nEjecutadosOkProc": "nEjecutadosOkProc",
    "nEsperaInst": "nEsperaInst",
    "nEnEjecucionInst": "nEnEjecucionInst",
    "nErrorInst": "nErrorInst",
    "nEjecutadosOkInst": "nEjecutadosOkInst",
    "xEspera": "xEspera",
    "xEnEjecucion": "xEnEjecucion",
    "xError": "xError",
    "xEjecutadosOK": "xEjecutadosOK",
    "CREATE_DATE": "CREATE_DATE",
    "UPDATE_DATE": "UPDATE_DATE",
}


class SqlServerRepository(BaseRepository):
    """Repositorio que lee de SQL Server via pyodbc + SQLAlchemy.

    Requiere las variables de entorno SECRETS_KEY_PATH y CREDENTIALS_PATH
    apuntando a secrets.key y credentials.enc generados con los scripts
    de la Fase 6 (ver docs/SECURITY.md).

    La conexion se crea de forma perezosa al primer uso y se reutiliza.
    """

    def __init__(self) -> None:
        from src.core.security import load_credentials_from_env
        self._creds = load_credentials_from_env()

    @cached_property
    def _engine(self):
        """Crea el engine de SQLAlchemy (lazy, singleton por instancia)."""
        from sqlalchemy import create_engine
        params = urllib.parse.quote_plus(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self._creds.server};"
            f"DATABASE={self._creds.database};"
            f"UID={self._creds.user};"
            f"PWD={self._creds.password};"
            "TrustServerCertificate=yes;"
            "Encrypt=yes;"
        )
        return create_engine(
            f"mssql+pyodbc:///?odbc_connect={params}",
            fast_executemany=True,
        )

    def _query(self, where: str = "", params: dict | None = None) -> pd.DataFrame:
        """Ejecuta una SELECT sobre la tabla de monitorizacion.

        Args:
            where:  Clausula WHERE adicional (sin la palabra WHERE).
            params: Parametros para el WHERE (dict para SQLAlchemy).

        Returns:
            DataFrame con las columnas estandar del repositorio.
        """
        from sqlalchemy import text
        cols = ", ".join(f"[{c}]" for c in _COLUMN_MAP.keys())
        sql = f"SELECT {cols} FROM [{_TABLE}]"
        if where:
            sql += f" WHERE {where}"
        sql += " ORDER BY nFecha_ejecucion DESC, Hora_ejecucion DESC, Minuto_ejecucion DESC"

        with self._engine.connect() as conn:
            df = pd.read_sql(text(sql), conn, params=params or {})
        return df

    # ------------------------------------------------------------------
    # Interfaz publica
    # ------------------------------------------------------------------

    def get_all_executions(self) -> pd.DataFrame:
        """Devuelve todas las ejecuciones de la tabla de monitorizacion."""
        return self._query()

    def get_executions_by_project(self, project: str) -> pd.DataFrame:
        """Devuelve todas las ejecuciones de un proyecto concreto.

        Args:
            project: Nombre exacto del proyecto ETL.
        """
        return self._query("proyecto = :proyecto", {"proyecto": project})

    def get_last_execution_per_project(self) -> pd.DataFrame:
        """Devuelve la ultima ejecucion de cada proyecto via subconsulta SQL."""
        from sqlalchemy import text
        cols = ", ".join(f"t.[{c}]" for c in _COLUMN_MAP.keys())
        sql = f"""
            SELECT {cols}
            FROM [{_TABLE}] t
            INNER JOIN (
                SELECT proyecto,
                       MAX(nFecha_ejecucion * 10000 + Hora_ejecucion * 100 + Minuto_ejecucion)
                           AS max_ts
                FROM [{_TABLE}]
                GROUP BY proyecto
            ) sub
            ON  t.proyecto = sub.proyecto
            AND (t.nFecha_ejecucion * 10000 + t.Hora_ejecucion * 100 + t.Minuto_ejecucion)
                = sub.max_ts
        """
        with self._engine.connect() as conn:
            return pd.read_sql(text(sql), conn)

    def get_executions_in_range(self, start: date, end: date) -> pd.DataFrame:
        """Devuelve las ejecuciones cuya nFecha_ejecucion esta en [start, end].

        Args:
            start: Fecha de inicio (inclusive).
            end:   Fecha de fin (inclusive).
        """
        start_int = int(start.strftime("%Y%m%d"))
        end_int = int(end.strftime("%Y%m%d"))
        return self._query(
            "nFecha_ejecucion >= :start AND nFecha_ejecucion <= :end",
            {"start": start_int, "end": end_int},
        )

    def get_available_projects(self) -> list[str]:
        """Devuelve los proyectos distintos presentes en SQL Server."""
        from sqlalchemy import text
        sql = f"SELECT DISTINCT proyecto FROM [{_TABLE}] ORDER BY proyecto"
        with self._engine.connect() as conn:
            df = pd.read_sql(text(sql), conn)
        return df["proyecto"].tolist()

"""Implementacion SQL Server del repositorio (Fase 6)."""

from datetime import date

import pandas as pd

from src.core.data_access.base_repository import BaseRepository


class SqlServerRepository(BaseRepository):
    """Repositorio que lee de SQL Server via pyodbc + SQLAlchemy.

    Pendiente de implementacion en la Fase 6.
    Requiere SECRETS_KEY_PATH y CREDENTIALS_PATH configurados.
    """

    def get_all_executions(self) -> pd.DataFrame:
        raise NotImplementedError("SqlServerRepository se implementa en la Fase 6.")

    def get_executions_by_project(self, project: str) -> pd.DataFrame:
        raise NotImplementedError("SqlServerRepository se implementa en la Fase 6.")

    def get_last_execution_per_project(self) -> pd.DataFrame:
        raise NotImplementedError("SqlServerRepository se implementa en la Fase 6.")

    def get_executions_in_range(self, start: date, end: date) -> pd.DataFrame:
        raise NotImplementedError("SqlServerRepository se implementa en la Fase 6.")

    def get_available_projects(self) -> list[str]:
        raise NotImplementedError("SqlServerRepository se implementa en la Fase 6.")

"""Factoria de repositorios: devuelve la implementacion segun DATA_SOURCE."""

from src.core import config
from src.core.data_access.base_repository import BaseRepository


def get_repository() -> BaseRepository:
    """Devuelve el repositorio adecuado segun la variable DATA_SOURCE.

    - DATA_SOURCE=excel     -> ExcelRepository (por defecto, desarrollo)
    - DATA_SOURCE=sqlserver -> SqlServerRepository (produccion)

    Returns:
        Instancia de BaseRepository lista para usar.

    Raises:
        ValueError: Si DATA_SOURCE tiene un valor no reconocido.
    """
    source = config.DATA_SOURCE

    if source == "excel":
        from src.core.data_access.excel_repository import ExcelRepository
        return ExcelRepository(
            excel_path=config.EXCEL_PATH,
            sheet_name=config.EXCEL_SHEET,
        )

    if source == "sqlserver":
        from src.core.data_access.sqlserver_repository import SqlServerRepository
        return SqlServerRepository()

    raise ValueError(
        f"Valor de DATA_SOURCE no reconocido: '{source}'. "
        "Valores validos: 'excel', 'sqlserver'."
    )

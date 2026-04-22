"""Configuracion centralizada de DATA_Dashboard.

Lee variables de entorno y proporciona valores por defecto para desarrollo.
"""

import os
from pathlib import Path

# Directorio raiz del proyecto (dos niveles sobre este fichero: src/core/ -> raiz)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Fuente de datos: "excel" (desarrollo) | "sqlserver" (produccion)
DATA_SOURCE: str = os.environ.get("DATA_SOURCE", "excel").lower()

# Ruta al fichero Excel (relativa a la raiz del proyecto)
EXCEL_PATH: Path = Path(
    os.environ.get("EXCEL_PATH", str(_PROJECT_ROOT / "data" / "PWC_Monitorizacion_CdM.xlsx"))
)

# Hoja del Excel que contiene los datos
EXCEL_SHEET: str = os.environ.get("EXCEL_SHEET", "Hoja1")

# Credenciales SQL Server (solo relevante con DATA_SOURCE=sqlserver)
SECRETS_KEY_PATH: str = os.environ.get("SECRETS_KEY_PATH", "")
CREDENTIALS_PATH: str = os.environ.get("CREDENTIALS_PATH", "")

# Horas sin ejecucion antes de considerar un proyecto inactivo
INACTIVITY_HOURS: int = int(os.environ.get("INACTIVITY_HOURS", "24"))

# Puerto de Streamlit
STREAMLIT_PORT: int = int(os.environ.get("STREAMLIT_PORT", "8501"))

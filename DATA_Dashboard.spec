# DATA_Dashboard.spec — PyInstaller onedir
# Generado manualmente: no sobreescribir con pyinstaller --auto-spec.
#
# Para compilar:  build.bat
# Resultado:      dist\DATA_Dashboard\DATA_Dashboard.exe

import sys
from pathlib import Path
import streamlit

# ---------------------------------------------------------------------------
# Rutas base
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(SPECPATH)
STREAMLIT_PKG = Path(streamlit.__file__).parent

# ---------------------------------------------------------------------------
# Datos a empaquetar
# ---------------------------------------------------------------------------
SITE_PACKAGES = STREAMLIT_PKG.parent


def _dist_info(pkg_name: str) -> tuple | None:
    """Devuelve la tupla (src, dest) para el dist-info de un paquete, o None."""
    import glob
    matches = glob.glob(str(SITE_PACKAGES / f"{pkg_name}-*.dist-info"))
    if matches:
        p = Path(matches[0])
        return (str(p), p.name)
    return None


added_datas = [
    # Código fuente de la aplicación
    (str(PROJECT_ROOT / "app.py"), "."),
    (str(PROJECT_ROOT / "src"), "src"),
    (str(PROJECT_ROOT / "data"), "data"),

    # Assets estáticos de Streamlit (imprescindibles para que el servidor funcione)
    (str(STREAMLIT_PKG / "static"),     "streamlit/static"),
    (str(STREAMLIT_PKG / "runtime"),    "streamlit/runtime"),
    (str(STREAMLIT_PKG / "vendor"),     "streamlit/vendor"),
    (str(STREAMLIT_PKG / "components"), "streamlit/components"),

    # Metadata de paquetes que usan importlib.metadata en runtime
    *filter(None, [
        _dist_info("streamlit"),
        _dist_info("altair"),
        _dist_info("click"),
        _dist_info("tornado"),
        _dist_info("packaging"),
        _dist_info("toml"),
        _dist_info("validators"),
        _dist_info("watchdog"),
        _dist_info("pydeck"),
        _dist_info("gitpython"),
    ]),
]

# ---------------------------------------------------------------------------
# Imports ocultos (no detectados por análisis estático)
# ---------------------------------------------------------------------------
hidden = [
    # Streamlit internals
    "streamlit",
    "streamlit.web",
    "streamlit.web.cli",
    "streamlit.web.server",
    "streamlit.web.server.server",
    "streamlit.runtime",
    "streamlit.runtime.scriptrunner",
    "streamlit.runtime.scriptrunner.magic_funcs",
    "streamlit.runtime.state",
    "streamlit.runtime.caching",
    "streamlit.runtime.uploaded_file_manager",
    "streamlit.components.v1",
    "streamlit.components.v1.components",
    # Tornado (servidor HTTP interno de Streamlit)
    "tornado",
    "tornado.web",
    "tornado.ioloop",
    "tornado.httpserver",
    "tornado.websocket",
    # Click (CLI de Streamlit)
    "click",
    # Altair (visualizaciones Streamlit)
    "altair",
    "altair.vegalite.v5",
    # Plotly
    "plotly",
    "plotly.graph_objects",
    "plotly.express",
    # Pandas + backends
    "pandas",
    "pyarrow",
    "openpyxl",
    # Seguridad
    "cryptography",
    "cryptography.fernet",
    "cryptography.hazmat",
    "cryptography.hazmat.primitives",
    "cryptography.hazmat.backends",
    # SQL Server
    "sqlalchemy",
    "sqlalchemy.dialects.mssql",
    "pyodbc",
    # Otros módulos de Streamlit usados en runtime
    "validators",
    "toml",
    "packaging",
    "pympler",
    "watchdog",
    "gitpython",
    "rich",
    "pydeck",
]

# ---------------------------------------------------------------------------
# Análisis
# ---------------------------------------------------------------------------
a = Analysis(
    [str(PROJECT_ROOT / "launcher.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "ruff",
        "black",
        "tkinter",
        "matplotlib",
        "IPython",
        "notebook",
        "jupyter",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DATA_Dashboard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX desactivado: compatibilidad antivirus corporativo
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DATA_Dashboard",
)

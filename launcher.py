"""Entry point del ejecutable DATA_Dashboard.exe.

Arranca Streamlit de forma programática (sin invocar la CLI externa),
lo que es el único método compatible con PyInstaller onedir.

En modo .exe (sys.frozen=True), app.py y src/ viven en sys._MEIPASS
(_internal/ junto al ejecutable). En modo desarrollo, se usa la ruta
relativa al propio launcher.py.
"""

import os
import sys


def _base_path() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # _internal/ dentro de la carpeta onedir
    return os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    base = _base_path()
    app_py = os.path.join(base, "app.py")
    port = os.environ.get("STREAMLIT_PORT", "8501")

    sys.argv = [
        "streamlit",
        "run",
        app_py,
        "--global.developmentMode=false",
        "--server.headless=true",
        f"--server.port={port}",
        "--browser.gatherUsageStats=false",
        "--server.fileWatcherType=none",
    ]

    from streamlit.web import cli as stcli
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()

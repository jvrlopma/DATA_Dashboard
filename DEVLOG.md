# DEVLOG.md — DATA_Dashboard

Bitacora cronologica de desarrollo. Append-only.

---

## [2026-04-22 09:33] — Preflight: verificacion y preparacion del entorno

**Fase**: -1 — Preflight
**Commit**: b8ce633

**Que se ha hecho**:
- Creado `scripts/preflight.ps1` con 12 comprobaciones del entorno de desarrollo.
- Ejecutado el preflight: resultado OK (10/12; ODBC Driver y NSSM son no bloqueantes).
- Instalado via winget: Python 3.11.9, Visual Studio Build Tools 2022.
- Configurado git global: user.name="Javier Lopez", user.email="jvrlopezmartinez@gmail.com".
- Generado `preflight_report.md` (excluido del repo via .gitignore).
- Primer push al repo remoto `github.com/jvrlopma/DATA_Dashboard`.

**Decisiones tecnicas relevantes**:
- El script usa `$env:OS -eq "Windows_NT"` en lugar de `$IsWindows` para compatibilidad con Windows PowerShell 5.1 (la variable `$IsWindows` solo existe en PowerShell Core 6+).
- Python 3.11 instalado en `%LOCALAPPDATA%\Programs\Python\Python311`; el alias de Microsoft Store tenia prioridad en el PATH de maquina, por lo que se prefixa Python311 al PATH en la sesion antes de llamar al script.

**Problemas encontrados / a revisar**:
- El alias `python` de Microsoft Store interfiere con el PATH de maquina. No hay permisos de admin para modificar HKLM PATH. Solucion de trabajo: anteponer la ruta de Python311 en la sesion. Pendiente de evaluar si esto afecta al entorno CI/CD o a futuros scripts de build.

**Siguiente paso**:
- Fase 0: Bootstrap del repo (estructura, .gitignore, README, STATUS, DEVLOG, requirements.txt, venv).

---

## [2026-04-22 09:50] — Bootstrap del repo

**Fase**: 0 — Bootstrap del repo
**Commit**: (ver hash tras commit)

**Que se ha hecho**:
- Creada estructura completa de carpetas segun PROJECT_SPEC.md seccion 8.
- Creados todos los `__init__.py` vacios en `src/` y `tests/`.
- Creado `.gitignore` (excluye .venv, build/, dist/, secretos, preflight_report.md).
- Creados `README.md`, `STATUS.md`, `DEVLOG.md` iniciales.
- Creados `requirements.txt` (dependencias fijadas con ==) y `pyproject.toml` (ruff, black, pytest).
- Creado virtualenv `.venv` con Python 3.11 e instaladas todas las dependencias.

**Decisiones tecnicas relevantes**:
- `data/PWC_Monitorizacion_CdM.xlsx` se versiona (dataset de desarrollo; reevaluar si contiene datos sensibles).
- `preflight_report.md` excluido del repo (se genera localmente en cada ejecucion del preflight).
- El fichero `.spec` de PyInstaller autogenerado se excluye; solo se versiona `DATA_Dashboard.spec` (custom, Fase 7).

**Siguiente paso**:
- Fase 1: Implementar `BaseRepository` y `ExcelRepository`, tests unitarios, colocar Excel real en `data/`.

---

## [2026-04-22 10:30] — Fases 1-5: capa de datos, dominio y las 3 vistas UI

**Fase**: 1-5
**Commits**: 9fa6070 (F1), 3ceff0d (F2), 795da14 (F3), 6ceb796 (F4), (F5 en curso)

**Que se ha hecho**:
- Fase 1: `BaseRepository`, `ExcelRepository`, `factory.py`, `date_utils.py`. 26 tests.
- Fase 2: modelos `Execution`/`ProjectHealth`, logica pura `compute_status()` y `compute_project_health()`. 81 tests totales cubriendo todos los limites del spec.
- Fase 3: `app.py` con navegacion Streamlit, Vista 1 (tarjetas KPI accesibles, listado de atencion, grafico de evolucion con tabs 7/30/90 dias).
- Fase 4: Vista 2 con selector de proyecto, filtros de fecha y estado, panel de ultima ejecucion desglosada, 3 graficos Plotly, tabla historica.
- Fase 5: Vista 3 con Gantt real (dFech_Ini_Carga / dFech_Fin_Carga), KPIs del dia, tabla de inactividad con umbral configurable (slider).

**Decisiones tecnicas relevantes**:
- El Gantt usa `px.timeline` con duraciones reales de carga; fallback a scatter si faltan timestamps.
- La deteccion de inactividad compara `datetime.now()` con la ultima ejecucion de cada proyecto en todo el dataset (no solo en el dia seleccionado).
- Telemetria de Streamlit desactivada via variable de entorno y flag CLI.

**Problemas encontrados / a revisar**:
- El alias `python` de MS Store sigue teniendo prioridad sobre Python311 en nuevas sesiones de PowerShell. Workaround: se prefixa Python311 al PATH en cada sesion. Pendiente de resolver definitivamente (requiere admin para HKLM).

**Siguiente paso**:
- Fase 6: SqlServerRepository, scripts de cifrado de credenciales, SECURITY.md. Requiere instalar ODBC Driver 18.

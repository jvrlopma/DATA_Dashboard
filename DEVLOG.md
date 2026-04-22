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

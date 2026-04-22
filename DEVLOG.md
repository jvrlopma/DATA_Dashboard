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
- Fase 6: SqlServerRepository, scripts de cifrado de credenciales, SECURITY.md.

---

## [2026-04-22 11:30] — Fases 6-7: seguridad, SQL Server y empaquetado PyInstaller

**Fase**: 6-7
**Commits**: 736e660 (F6), 0ea38d5 (F7)

**Que se ha hecho**:
- Fase 6: `src/core/security.py` (CredentialStore, cifrado Fernet, load_credentials_from_env). `src/core/data_access/sqlserver_repository.py` (SQLAlchemy + pyodbc, cached_property engine, subconsulta MAX para last_execution). `scripts/generate_key.py` y `scripts/encrypt_credentials.py` (CLIs interactivos). `docs/SECURITY.md` (manual completo: generación, rotación, permisos NTFS, backup). `preflight.ps1` actualizado: check ODBC puramente informativo en dev.
- Fase 7: `launcher.py` (arranca Streamlit programáticamente con `--global.developmentMode=false`). `DATA_Dashboard.spec` (onedir, assets Streamlit, dist-info de dependencias). `build.bat` (compila con un solo comando). `scripts/package_release.ps1` (genera .zip versionado). `docs/BUILD.md`. `requirements.txt` actualizado con pyinstaller==6.11.1.

**Decisiones tecnicas relevantes**:
- ODBC Driver 18 no se instala en dev (ya estará en el servidor destino). El check de preflight es solo informativo.
- El exe requiere `--global.developmentMode=false` para que Streamlit no bloquee `--server.port` cuando detecta que se ejecuta desde un bundle PyInstaller.
- Los dist-info de las dependencias deben incluirse en los datas del spec porque Streamlit y otros paquetes leen su propia versión vía `importlib.metadata` en runtime.
- UPX desactivado en el spec (compatibilidad con antivirus corporativo).

**Problemas encontrados / resueltos**:
- `importlib.metadata.PackageNotFoundError: No package metadata was found for streamlit` → solución: incluir `streamlit-1.56.0.dist-info` y los dist-info de dependencias en los datas del spec.
- `RuntimeError: server.port does not work when global.developmentMode is true` → solución: pasar `--global.developmentMode=false` en sys.argv del launcher.

**Siguiente paso**:
- Fase 9: pulido y validación (accesibilidad, performance, conexiones salientes, ARCHITECTURE.md).
- Fase 8 diferida: despliegue en Windows Server (pendiente de INSTALL_PATH del PM).

---

## [2026-04-22 12:15] — Fase 9: pulido, accesibilidad y documentacion final

**Fase**: 9 — Pulido y validacion
**Commit**: (ver hash tras commit)

**Que se ha hecho**:
- **Accesibilidad (daltonismo)**: añadidos patrones de relleno Plotly (`marker.pattern.shape`) a `_chart_por_hora` (Vista 2) y `pattern_shape` a `px.timeline` (Vista 3 Gantt). OK=sólido, REGULAR=diagonal `/`, CRITICO=cruz `x`. Combinado con icono + color + texto ya existentes.
- **Performance**: vectorizado `_tabla_inactividad` en daily_ops.py — sustituido `apply()` fila a fila por `pd.to_datetime()` con concatenación de strings (O(n) vectorizado vs O(n·overhead) en apply). Crítico para 10k+ filas.
- **Caching UI**: añadidos `@st.cache_data(ttl=300)` en las tres vistas para consultas al repositorio. Evita re-fetches en cada interacción de Streamlit; especialmente útil en modo SQL Server.
- **STATUS.md y DEVLOG.md**: actualizados para reflejar el estado real (Fases 6, 7 y 9 completadas).
- **docs/ARCHITECTURE.md**: documento final con diagrama de capas, flujo de arranque, tabla de proyectos, stack, política de conexiones salientes y accesibilidad.

**Decisiones tecnicas relevantes**:
- El prefijo `_` en el argumento `_repo` de las funciones cacheadas le dice a Streamlit que NO hashee el objeto repo (que no es serializable). El cache queda keyed por nombre de función y demás args (proyecto, fechas…).
- `marker.pattern.shape` en Plotly admite lista de strings por barra — no hace falta dividir en trazas separadas.
- `pattern_shape` en `px.timeline` genera una leyenda combinada color+patrón sin código adicional.

**Verificacion**:
- 81 tests pasan sin cambios.
- Streamlit arranca sin errores en modo Excel.
- `.exe` (dist\DATA_Dashboard\DATA_Dashboard.exe) sigue funcional.

**Siguiente paso**:
- Fase 8 (despliegue): diferida. Requiere INSTALL_PATH del PM en el servidor.
- Pruebas funcionales con el usuario sobre el .exe generado.

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

---

## [2026-04-22 ~15:00] — Sesión UI: diseño Stitch, temas claro/oscuro y lógica especial de proyectos

**Commits**: (ver hash tras push)

### Cambios aplicados

#### 1. Sistema de diseño dual (claro / oscuro) — Stitch spec

- **`src/ui/styles.py`** — reescritura completa:
  - Dos paletas `C_LIGHT` / `C_DARK` con los tokens exactos del diseño Stitch/Aqualia.
  - Colores de estado: OK `#22C55E` · REGULAR `#F59E0B` · CRÍTICO `#EF4444` · SIN DATOS `#94A3B8`.
  - Accent corporativo Aqualia: `#005791` (claro) / `#9dcaff` (oscuro).
  - CSS custom properties (`:root` claro, `body.dd-dark` oscuro): todos los componentes usan `var(--dd-*)` — sin hex hardcoded en las reglas CSS.
  - Dos templates Plotly registrados: `aqualia_light` y `aqualia_dark`.
  - `inject_css(dark)` actualiza `C` en-lugar + inyecta CSS + añade clase `dd-dark`/`dd-light` al body via JS.
  - Fuente principal: **Inter** (antes Space Grotesk). Mono: JetBrains Mono sin cambios.
  - Tarjetas de proyecto: borde izquierdo de 4px con color de estado (además del anillo SVG).

- **`.streamlit/config.toml`**: base `"light"`, colores del tema claro, `primaryColor = "#005791"`.

- **`app.py`**: toggle "Tema oscuro" en sidebar. Al cambiar llama `st.rerun()`. `inject_css(dark)` y `apply_plotly_theme(dark)` reciben el estado.

- **Views**: headers usan `var(--dd-text)` / `var(--dd-text3)` en lugar de `C["text"]` interpolado.

- **`daily_ops.py` / `project_detail.py`**: eliminados `_STATUS_COLORS` y `_ESTADO_COLORS` a nivel de módulo (se capturaban en import-time, no reflejaban cambio de tema). Colores computados inline en cada función de chart, leyendo `C` en runtime.

#### 2. Lógica especial por proyecto — `src/domain/project_status.py`

- **AqualiaTPL** (ejecución diaria diferida):
  - Procesa datos D-1; el registro llega a BD entre las 13:00 y 15:00 del día D.
  - Solución: `inactivity_hours=48` en lugar de 24. Evita falsa alerta "sin datos" durante la mañana del día D mientras el registro de D-1 sigue siendo el más reciente.
  - El registro de D llega de forma natural (~15:00) y pasa a ser el evaluado automáticamente.

- **Aqualia_GIS** (ejecución mensual, días 6-10):
  - Nueva función `_compute_gis_health(df_gis, now)`.
  - Lógica: si ejecutó en la ventana 6-10 del mes relevante → OK; si estamos en días 6-10 y no ha ejecutado aún → REGULAR (pendiente, no crítico); si la ventana ya cerró sin ejecución → CRÍTICO.
  - Mes relevante: mes actual si `día >= 6`, mes anterior si `día < 6`.
  - `get_all_project_health` acepta nuevo parámetro `df_gis: pd.DataFrame | None`.
  - `overview.py` carga `_load_gis(repo)` via `get_executions_by_project("Aqualia_GIS")` y lo pasa.

#### 3. Mejoras UI previas (misma sesión, antes del push)

- **Gráfico resumen**: reemplazado trend de % OK por stacked bar por estado (OK/REGULAR/CRÍTICO) por día, con tabs 7d/30d/90d. Altura 400px.
- **Columnas igual altura**: CSS flex en `[data-testid="stHorizontalBlock"]` + `.dd .panel { height: 100% }`.
- **Full-width**: `.block-container { max-width: 100% !important }`.
- **Hot reload**: `fileWatcherType = "auto"` en config.toml. `run.bat` fijado a puerto 9000.
- **Doble cabecera corregida**: `attention_items_html()` ya genera panel completo; se eliminó el wrapper `panel_html()` que duplicaba el header.

### Decisiones técnicas relevantes

- **CSS variables vs hex hardcoded**: elegido CSS variables para que el mismo HTML generado sirva para ambos temas. Solo Plotly (que necesita hex reales) usa el dict `C` de Python.
- **`inject_css(dark)` actualiza `C` en-lugar**: las funciones de chart que leen `C["ok"]` en runtime (no en import-time) obtienen el color correcto del tema activo. El dict `C` es el dict mutable compartido (`dict(C_LIGHT)` por defecto).
- **base = "light"**: el tema Stitch es primariamente claro. Para oscuro, se añaden overrides `body.dd-dark *` sobre la base light de Streamlit.

### Pendiente / a revisar mañana

- [ ] Verificar visualmente que el toggle oscuro/claro funciona bien en todos los views (tarjetas, gráficos Plotly, widgets nativos de Streamlit).
- [ ] Comprobar que Aqualia_GIS muestra REGULAR cuando estamos en días 6-10 sin ejecución (simular con fecha de test).
- [ ] Revisar si `body.dd-dark` overrides cubren todos los widgets Streamlit (selectbox, date_input, slider) — puede haber widgets con estilos light residuales.
- [ ] Evaluar si añadir una barra de estado en el sidebar (última actualización, modo de datos: Excel/SQL).
- [ ] Fase 8 (despliegue) sigue diferida — requiere INSTALL_PATH del PM.

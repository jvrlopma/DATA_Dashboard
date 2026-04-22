# PROJECT_SPEC.md — DATA_Dashboard

> Especificación técnica para Claude Code.
> Este documento define **QUÉ** construir, **CÓMO** estructurarlo y **QUÉ reglas** son no negociables.
> Léelo entero antes de empezar y, si tienes dudas, pregunta antes de escribir código.

---

## 0. Contexto del proyecto

**Autor/PM**: Javier López — Project Manager de DATA, departamento de TI de Aqualia.
**Responsabilidad**: centralizar datos de todas las aplicaciones corporativas en SQL Server vía procesos ETL (PowerCenter 10.5.1 y SSIS) para explotación analítica.

**Problema que resuelve este proyecto**:
Actualmente existe una tabla de monitorización (`AqALL_t_PWC_Monitorizacion_CdM`) que registra las ejecuciones de los proyectos ETL, pero no hay una visualización consolidada. Se necesita un **dashboard web** que permita ver de un vistazo el estado del departamento de DATA y detectar anomalías sin navegar por el Excel.

**Usuarios finales**:
- El PM de DATA (visión agregada, detección de problemas).
- Posteriormente, otros miembros del equipo de TI con acceso a la red interna.

---

## 1. Rutas del proyecto

### 1.1. Ruta de desarrollo (fijada)

```
C:\Users\Javi\Documents\Proyectos\DATA_Dashboard
```

Esta es la ruta local en el equipo de desarrollo del PM. Todas las instrucciones, scripts y ejemplos de comandos deben asumir esta ruta como base durante el desarrollo.

### 1.2. Ruta de despliegue en el servidor (PENDIENTE de decisión)

**El PM aún no ha decidido** la ruta definitiva donde se instalará la aplicación en el Windows Server. Por tanto:

1. **Todos los scripts de despliegue deben parametrizar la ruta** mediante una variable configurable (`$InstallPath` en PowerShell, o equivalente).
2. **No se debe hardcodear ninguna ruta de servidor** en código, scripts ni documentación.
3. **Claude Code debe preguntar al PM** la ruta definitiva **antes de empezar la Fase 8** (despliegue).
4. Como placeholder temporal en la documentación, usar `<INSTALL_PATH>` (ej.: `<INSTALL_PATH>\DATA_Dashboard\`).

Posibles opciones que se evaluarán llegado el momento:
- `C:\DATA_Dashboard\`
- `C:\Program Files\DATA_Dashboard\`
- `D:\Aplicaciones\DATA_Dashboard\`
- `C:\ProgramData\DATA_Dashboard\`
- Otra ruta estándar corporativa de Aqualia.

---

## 2. Objetivo del dashboard

Proporcionar, en una única pantalla principal, una visión consolidada del estado de salud de **los 8 proyectos ETL** activos, con navegación a detalle por proyecto.

### 2.1. Vistas obligatorias

**Vista 1 — Resumen global (landing page)**
- Tarjeta KPI por cada proyecto con: nombre, estado actual (OK / REGULAR / CRÍTICO / CON ERRORES), última ejecución (fecha + hora), % OK última ejecución, % error última ejecución.
- Semáforo visual claro (verde / amarillo / rojo) por proyecto. **Accesible**: el estado debe ser reconocible también por forma/icono, no solo por color (daltonismo).
- Listado destacado de "Proyectos que requieren atención" ordenado por severidad.
- Gráfico de línea temporal: evolución del % OK agregado de los últimos 7/30/90 días.

**Vista 2 — Detalle por proyecto**
- Seleccionable desde la vista 1.
- Histórico de ejecuciones con tabla filtrable (fecha desde/hasta, estado).
- Gráficos: evolución de `xError` y `xEjecutadosOK` en el tiempo, distribución por hora del día, volumen de `nTotalEjecuciones`.
- Última ejecución desglosada: `nEsperaProc`, `nEnEjecucionProc`, `nErrorProc`, `nEjecutadosOkProc` y equivalentes de instalaciones.

**Vista 3 — Operativa diaria**
- Timeline del día actual con las ejecuciones de todos los proyectos en una vista tipo Gantt simplificada (eje X = horas del día, eje Y = proyecto).
- Detección de proyectos que no han ejecutado en las últimas N horas (configurable, por defecto 24h).

### 2.2. Criterios de estado por proyecto (REGLA DE NEGOCIO CRÍTICA)

El estado se calcula a partir de `xEjecutadosOK` (% de procesos OK) de la **última ejecución** de cada proyecto. **Los umbrales varían por proyecto**:

**Grupo A — Proyectos críticos (deben estar al 100%)**
- `AqualiaApemsa`
- `AqualiaDW`
- `AqualiaSII2_FICO`
- `Aqualia_Diario`

Reglas:
- `xEjecutadosOK == 100` → **OK** (verde)
- `xEjecutadosOK < 100` → **CRÍTICO** (rojo)

**Grupo B — Resto de proyectos (tolerancia)**
- `AqualiaODS`
- `AqualiaSII2_Doc_AEF`
- `AqualiaTPL`
- `Aqualia_GIS`

Reglas:
- `xEjecutadosOK >= 90` → **OK** (verde)
- `xEjecutadosOK >= 80 y < 90` → **REGULAR** (amarillo)
- `xEjecutadosOK < 80` → **CRÍTICO** (rojo)

**Estado adicional transversal — "SIN EJECUCIONES RECIENTES"**
Si el proyecto no tiene ninguna ejecución en las últimas 24h → estado **CRÍTICO** con etiqueta específica "Sin datos recientes".

Implementa esta lógica en un módulo `domain/project_status.py` con una función pura y **tests unitarios que cubran los 3 grupos de casos** (límites 100, 90, 80 incluidos). No quiero ver la lógica dispersa por la UI.

---

## 3. Fuente de datos

### 3.1. Fase actual (desarrollo)
La fuente es un **fichero Excel** `PWC_Monitorizacion_CdM.xlsx` ubicado en `data/` dentro del repo.

**Estructura de la tabla** (hoja `Hoja1`, ~10.200 filas, 27 columnas):

| Columna | Tipo | Descripción |
|---|---|---|
| `Id` | int | Identificador único de la ejecución |
| `nFecha_ejecucion` | int (YYYYMMDD) | Fecha de ejecución del proceso ETL |
| `Hora_ejecucion` | int (0-23) | Hora de ejecución |
| `Minuto_ejecucion` | int (0-59) | Minuto de ejecución |
| `nFecha_Info` | int (YYYYMMDD) | Fecha de la información procesada |
| `proyecto` | str | Nombre del proyecto ETL (uno de los 8) |
| `dFech_Ini_Info` | str (datetime) | Fecha/hora inicio del periodo de información |
| `dFech_Fin_Info` | str (datetime) | Fecha/hora fin del periodo de información |
| `dFech_Ini_Carga` | str (datetime) | Fecha/hora inicio de la carga ETL |
| `dFech_Fin_Carga` | str (datetime) | Fecha/hora fin de la carga ETL |
| `Estado_proyecto` | float | **IGNORAR** — está 100% nulo en los datos actuales |
| `nTotalInstalaciones` | int | Nº de instalaciones a procesar |
| `nTotalEjecuciones` | int | Nº total de ejecuciones del proceso |
| `nEsperaProc` | int | Procesos en espera |
| `nEnEjecucionProc` | int | Procesos en ejecución |
| `nErrorProc` | int | Procesos con error |
| `nEjecutadosOkProc` | int | Procesos ejecutados OK |
| `nEsperaInst` | int | Instalaciones en espera |
| `nEnEjecucionInst` | int | Instalaciones en ejecución |
| `nErrorInst` | int | Instalaciones con error |
| `nEjecutadosOkInst` | int | Instalaciones ejecutadas OK |
| `xEspera` | float (%) | % en espera |
| `xEnEjecucion` | float (%) | % en ejecución |
| `xError` | float (%) | **% con error (clave para estado)** |
| `xEjecutadosOK` | float (%) | **% ejecutado OK (clave para estado)** |
| `CREATE_DATE` | str (datetime) | Timestamp de creación del registro |
| `UPDATE_DATE` | str (datetime, nullable) | Timestamp de última actualización |

**Proyectos identificados en los datos**:
`AqualiaApemsa`, `AqualiaDW`, `AqualiaODS`, `AqualiaSII2_Doc_AEF`, `AqualiaSII2_FICO`, `AqualiaTPL`, `Aqualia_Diario`, `Aqualia_GIS`.

### 3.2. Fase de producción (despliegue en servidor interno)
La fuente pasará a ser **SQL Server**, tabla `PWC_Monitorizacion_CdM` con la misma estructura de columnas.

**Por tanto, el acceso a datos debe estar abstraído** mediante un patrón Repository / Data Access Layer:

```
core/
  data_access/
    __init__.py
    base_repository.py        # Interfaz abstracta
    excel_repository.py       # Implementación Excel (fase actual)
    sqlserver_repository.py   # Implementación SQL Server (fase producción)
    factory.py                # Devuelve la implementación según configuración
```

La capa de dominio y la UI **NUNCA** deben importar pandas de lectura directa ni `pyodbc` directamente. Solo consumen el repositorio.

La selección de implementación se hace vía variable de entorno `DATA_SOURCE` (valores: `excel` | `sqlserver`).

---

## 4. Stack tecnológico (DECIDIDO)

- **SO del servidor destino**: **Windows Server**.
- **Lenguaje**: Python 3.11.
- **Framework UI**: **Streamlit**.
- **Gráficas**: Plotly.
- **Manejo de datos**: pandas + openpyxl (fase Excel) / pyodbc + SQLAlchemy (fase SQL Server).
- **Cifrado de credenciales**: `cryptography` (Fernet).
- **Testing**: pytest.
- **Linter/formatter**: ruff + black.
- **Empaquetado**: **PyInstaller en modo `--onedir`** → se genera una **carpeta `DATA_Dashboard\`** con el `.exe` principal y un subdirectorio `_internal\` con todas las dependencias desplegadas.
- **Ejecución en servidor**: el `.exe` dentro de esa carpeta se lanzará como **Servicio de Windows** mediante **NSSM** (Non-Sucking Service Manager) para arranque automático y reinicio ante caídas.

**Justificación del modo `onedir`** (vs `onefile`):
1. **Compatibilidad con antivirus corporativo**: el modo onefile autoextraíble dispara heurísticas de muchos antivirus empresariales (CrowdStrike, Defender for Endpoint, etc.), que pueden bloquear o poner en cuarentena el `.exe`. El modo onedir no se autoextrae y es mucho más tolerado.
2. **Arranque rápido**: onedir arranca en 1-2 segundos (sin descompresión); onefile tardaría 10-20 segundos en arrancar por descomprimir dependencias en `%TEMP%`.
3. **Debugging en producción**: con onedir puedes inspeccionar directamente las DLLs, módulos y ficheros desplegados. Con onefile, habría que esperar a que se descomprima en `%TEMP%` para poder inspeccionar.
4. **Contraprestación asumida**: en redeploy se copia una carpeta en lugar de un único fichero. Coste trivial — el proceso se zipea, se transfiere, se descomprime. Queda documentado en `docs/DEPLOYMENT.md`.

### 4.1. Consideraciones específicas de PyInstaller + Streamlit

Empaquetar Streamlit con PyInstaller requiere configuración específica porque Streamlit arranca un servidor Tornado interno y carga assets dinámicamente:

1. **Launcher programático**: el `.exe` no puede invocar `streamlit run app.py` como si fuera CLI. Se necesita un `launcher.py` que arranque Streamlit desde código:
   ```python
   from streamlit.web import cli as stcli
   import sys, os
   if __name__ == "__main__":
       sys.argv = ["streamlit", "run", os.path.join(base_path, "app.py"),
                   "--server.headless=true", "--server.port=8501",
                   "--browser.gatherUsageStats=false"]
       sys.exit(stcli.main())
   ```
2. **Hooks de PyInstaller** para incluir los recursos estáticos de Streamlit (`.streamlit`, templates, static assets). Claude Code debe preparar un fichero `.spec` custom con los `datas` y `hiddenimports` necesarios.
3. **Deshabilitar telemetría**: `--browser.gatherUsageStats=false` + variable de entorno `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false`. **Requisito obligatorio** por política de no-conexión-exterior.
4. **El build debe hacerse en Windows** (PyInstaller no hace cross-compilation). La máquina donde corra Claude Code debe ser Windows.

### 4.2. Ciclo de modificaciones (confirmado con el PM)

El flujo para aplicar cambios en producción será siempre:

1. Se modifica el código fuente en el equipo de desarrollo (`C:\Users\Javi\Documents\Proyectos\DATA_Dashboard`).
2. Se ejecuta `build.bat` → se regenera la carpeta `dist\DATA_Dashboard\`.
3. Se prueba ejecutando `dist\DATA_Dashboard\DATA_Dashboard.exe` en local.
4. Se empaqueta la carpeta en un `.zip` y se copia al servidor.
5. Se para el servicio, se sustituye la carpeta (en la ruta `<INSTALL_PATH>` a decidir), se arranca el servicio.
6. El procedimiento queda documentado paso a paso en `docs/DEPLOYMENT.md`.

---

## 5. Reglas técnicas NO NEGOCIABLES

### 5.1. Seguridad y aislamiento
1. **Cero conexiones al exterior** en runtime. Nada de CDNs, APIs externas, telemetría, analytics, fonts de Google, etc. Revisa explícitamente las dependencias que uses y confirma que no hacen llamadas salientes.
2. **Telemetría de Streamlit desactivada** por defecto en el launcher.
3. **Credenciales NUNCA en el código ni en el repo**. Se gestionan con un fichero cifrado local (ver sección 7).
4. **`.gitignore`** debe excluir: `.env`, `secrets.key`, `credentials.enc`, carpeta `build/`, carpeta `dist/`, `__pycache__/`, `.venv/`, ficheros `.spec` autogenerados (solo se versiona el `.spec` custom final).
   - **El Excel `data/PWC_Monitorizacion_CdM.xlsx` SÍ se versiona** (dataset de desarrollo; si más adelante contiene datos sensibles habrá que reevaluar).
5. El `requirements.txt` debe tener **versiones fijadas** (`==`) para garantizar reproducibilidad del build.
6. **Ninguna ruta de servidor hardcodeada**. Toda ruta de despliegue se parametriza (ver sección 1.2).

### 5.2. Calidad de código
1. Tipado con `type hints` en todas las funciones públicas.
2. Separación estricta de capas: `ui/` no accede a datos crudos, solo a `domain/` y `core/`.
3. Tests unitarios mínimos para: cálculo de estado por proyecto, parseo de fechas del Excel, lógica del repositorio.
4. Docstrings en español en funciones públicas (el equipo es hispanohablante).

### 5.3. Reglas del repositorio Git
1. Repo: **https://github.com/jvrlopma/DATA_Dashboard**
2. Commits pequeños y frecuentes, en español, formato Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
3. Rama principal: `main`. Trabajar directo sobre `main` en esta fase (proyecto unipersonal); cuando entre más gente, se abrirán ramas `feature/*`.
4. **Cada commit debe dejar el proyecto en estado ejecutable**. No subir código roto.
5. **Push al remoto después de cada fase completada**.

---

## 6. Preflight — verificación de entorno (OBLIGATORIO antes de codificar)

**Antes de la Fase 0**, Claude Code debe ejecutar un *script de preflight* que verifique las herramientas necesarias en el equipo de desarrollo. Si algo falta, debe avisar al PM y proponer la instalación, **nunca instalar nada sin confirmación explícita**.

### 6.1. Entregable de preflight

Claude Code creará un fichero `scripts/preflight.ps1` (PowerShell, dado que el entorno es Windows) que realice las siguientes comprobaciones y muestre un resumen claro al final:

| # | Comprobación | Acción si falta |
|---|---|---|
| 1 | **Es Windows** (`$IsWindows` o `$env:OS`) | Si no es Windows → abortar: el `.exe` solo se compila en Windows. |
| 2 | **Ruta de desarrollo existe** (`C:\Users\Javi\Documents\Proyectos\`) y es escribible | Si no existe, crearla (con confirmación). |
| 3 | **Python 3.11** en PATH (`python --version`) | Indicar al PM el instalador oficial: https://www.python.org/downloads/release/python-3119/ . Marcar "Add Python to PATH" durante la instalación. |
| 4 | **pip** actualizado (`python -m pip --version`) | Ejecutar `python -m pip install --upgrade pip` tras confirmación. |
| 5 | **Git** en PATH (`git --version`) | Indicar instalador: https://git-scm.com/download/win |
| 6 | **Configuración de Git** (`git config --global user.name` y `user.email`) | Pedir al PM que los configure. |
| 7 | **Acceso al repo remoto** (`git ls-remote https://github.com/jvrlopma/DATA_Dashboard`) | Si falla, avisar de posible proxy corporativo o necesidad de credenciales/PAT de GitHub. |
| 8 | **Visual C++ Build Tools** (necesarios para compilar dependencias nativas como `pyodbc`) | Indicar: https://visualstudio.microsoft.com/visual-cpp-build-tools/ (seleccionar "Desktop development with C++"). |
| 9 | **Microsoft ODBC Driver 18 for SQL Server** | Indicar: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server . Necesario para la Fase 6 (conexión a SQL Server). |
| 10 | **Virtualenv creable** (`python -m venv .venv` en un tmp dir) | Si falla, diagnosticar. |
| 11 | **NSSM** (informativo; solo relevante para el servidor). URL: https://nssm.cc/download | Informativo. |
| 12 | **Puerto 8501 libre** (puerto por defecto de Streamlit en desarrollo) | Si está ocupado, proponer otro. |

### 6.2. Comportamiento del script

- **Modo por defecto**: solo verifica y reporta. Genera un `preflight_report.md` con el resultado.
- **Modo `-Install`**: tras confirmación interactiva (y/n por cada herramienta faltante), descarga e instala lo que sea instalable vía `winget` o `choco` (si están disponibles). Para lo que requiera instalador manual (Visual C++ Build Tools, ODBC Driver), abre la URL en el navegador y pausa hasta que el PM confirme que ha terminado.
- **Código de salida**: 0 si todo OK, 1 si falta algo bloqueante. Claude Code **no arranca la Fase 0 hasta que el preflight devuelva 0**.

### 6.3. Ejecución

Desde la ruta de desarrollo (`C:\Users\Javi\Documents\Proyectos\DATA_Dashboard`):

```powershell
# Solo verificar
.\scripts\preflight.ps1

# Verificar e instalar lo que falte (con confirmación)
.\scripts\preflight.ps1 -Install
```

---

## 7. Gestión de credenciales cifradas (fase SQL Server)

### 7.1. Generación inicial (una sola vez, el PM lo hace a mano)
1. Se ejecuta un script `scripts/generate_key.py` que crea un fichero `secrets.key` (clave Fernet).
2. Se ejecuta un script `scripts/encrypt_credentials.py` que pide por consola los datos de conexión a SQL Server (servidor, BBDD, usuario, contraseña) y genera `credentials.enc` cifrado con la `secrets.key`.
3. **Ambos ficheros se colocan FUERA del repo y FUERA de la carpeta del `.exe`**, en una ruta del servidor protegida por permisos NTFS. La ruta concreta se definirá junto con `<INSTALL_PATH>` (ver sección 1.2).
4. La ruta se pasa al `.exe` vía variables de entorno (`SECRETS_KEY_PATH`, `CREDENTIALS_PATH`) configuradas en el servicio de Windows.

### 7.2. Runtime
- Al arrancar, la aplicación lee `secrets.key`, descifra `credentials.enc` en memoria, construye la cadena de conexión y NUNCA la escribe en disco ni en logs.
- Si falta cualquiera de los dos ficheros → error explícito en el log del servicio y cierre controlado.

### 7.3. Entregable específico para este punto
Claude Code debe generar en `docs/SECURITY.md` un manual paso a paso, con comandos copiables, para que el PM pueda:
- Generar las claves desde cero.
- Cifrar un nuevo set de credenciales.
- Rotar las claves si hay sospecha de compromiso.
- Configurar las variables de entorno en el servicio de Windows (vía NSSM o `sc.exe`).
- Verificar los permisos NTFS de la carpeta de secretos.

---

## 8. Estructura del repositorio

Base: `C:\Users\Javi\Documents\Proyectos\DATA_Dashboard\`

```
DATA_Dashboard/
├── README.md                    # Visión rápida del proyecto
├── STATUS.md                    # Estado actual (ver sección 10)
├── DEVLOG.md                    # Bitácora de desarrollo (ver sección 11)
├── PROJECT_SPEC.md              # Este documento
├── .gitignore
├── requirements.txt
├── pyproject.toml               # Config de ruff/black/pytest
├── launcher.py                  # Entry point del .exe (arranca Streamlit programáticamente)
├── app.py                       # App Streamlit (punto de entrada de la UI)
├── DATA_Dashboard.spec          # Fichero .spec custom de PyInstaller (versionado)
├── build.bat                    # Script de build del .exe en Windows
├── data/
│   ├── PWC_Monitorizacion_CdM.xlsx
│   └── .gitkeep
├── src/
│   ├── __init__.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── views/
│   │   │   ├── overview.py
│   │   │   ├── project_detail.py
│   │   │   └── daily_ops.py
│   │   └── components/
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── project_status.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   └── data_access/
│   │       ├── __init__.py
│   │       ├── base_repository.py
│   │       ├── excel_repository.py
│   │       ├── sqlserver_repository.py
│   │       └── factory.py
│   └── utils/
│       ├── __init__.py
│       └── date_utils.py
├── scripts/
│   ├── preflight.ps1
│   ├── generate_key.py
│   ├── encrypt_credentials.py
│   ├── package_release.ps1       # Empaqueta dist\DATA_Dashboard\ en un .zip versionado
│   └── install_service.ps1       # Instala la carpeta como servicio de Windows (parámetro -InstallPath obligatorio)
├── tests/
│   ├── __init__.py
│   ├── test_project_status.py
│   ├── test_excel_repository.py
│   └── test_date_utils.py
└── docs/
    ├── SECURITY.md               # Manual de credenciales
    ├── DEPLOYMENT.md             # Guía de despliegue (build + copia + servicio)
    ├── BUILD.md                  # Cómo generar el .exe (ciclo desarrollo)
    └── ARCHITECTURE.md           # Diagrama y decisiones técnicas
```

### 8.1. Resultado del build (estructura de `dist/`)

Tras ejecutar `build.bat`, PyInstaller generará:

```
dist/
└── DATA_Dashboard/               ← esta carpeta completa es lo que se despliega
    ├── DATA_Dashboard.exe        ← el ejecutable principal (pequeño, ~10 MB)
    └── _internal/                ← todas las dependencias
        ├── python311.dll
        ├── base_library.zip
        ├── streamlit/
        ├── pandas/
        ├── plotly/
        └── (muchos más ficheros)
```

**Para desplegar**: se copia la carpeta `DATA_Dashboard\` completa al servidor, a la ruta `<INSTALL_PATH>` que el PM defina en la Fase 8. Para ejecutar: se lanza `DATA_Dashboard.exe` que está dentro.

---

## 9. Plan de fases (roadmap)

Ejecuta una fase, haz commit, haz push, actualiza `DEVLOG.md` y `STATUS.md`, y pasa a la siguiente. **No saltes fases**.

**Fase -1 — Preflight** *(obligatoria, primero de todo)*
- Crear la ruta de trabajo si no existe: `C:\Users\Javi\Documents\Proyectos\DATA_Dashboard`.
- Clonar el repo `https://github.com/jvrlopma/DATA_Dashboard` dentro de esa ruta (si está vacío, inicializarlo desde cero — ver Fase 0).
- Crear `scripts/preflight.ps1`.
- Ejecutarlo y resolver cualquier herramienta faltante con el PM.
- No avanzar hasta que el preflight reporte OK.
- Commit: `chore: add preflight script and verify environment`.

**Fase 0 — Bootstrap del repo**
- Inicializar git (si el repo remoto está vacío), crear estructura de carpetas, `.gitignore`, `README.md`, `STATUS.md`, `DEVLOG.md` iniciales.
- Crear el `requirements.txt` con dependencias mínimas fijadas.
- Crear el virtualenv `.venv` en local (no se versiona).
- Primer commit y push a `main`.

**Fase 1 — Capa de datos (Excel)**
- Definir `BaseRepository` e implementar `ExcelRepository`.
- Tests unitarios del repositorio con un Excel mínimo de fixture.
- Colocar el Excel real en `data/`.

**Fase 2 — Dominio**
- Modelos (`Execution`, `ProjectHealth`).
- Módulo `project_status.py` con la lógica de los dos grupos de proyectos.
- Tests exhaustivos de la lógica de estado (cubrir 100, 99.99, 90, 89.99, 80, 79.99 y el caso sin ejecuciones recientes).

**Fase 3 — UI base (Streamlit) y Vista 1 (Resumen global)**
- Layout principal con navegación.
- Tarjetas KPI por proyecto con semáforo.
- Listado de "Proyectos que requieren atención".
- Gráfico de evolución agregada.

**Fase 4 — Vista 2 (Detalle por proyecto)**
- Selector de proyecto.
- Tabla filtrable + gráficos.

**Fase 5 — Vista 3 (Operativa diaria)**
- Timeline del día.
- Detección de proyectos inactivos.

**Fase 6 — Seguridad y capa SQL Server**
- Implementar `SqlServerRepository`.
- Scripts `generate_key.py` y `encrypt_credentials.py`.
- `docs/SECURITY.md` con manual paso a paso.

**Fase 7 — Empaquetado con PyInstaller (onedir)**
- Crear `launcher.py` (arranque programático de Streamlit).
- Crear `DATA_Dashboard.spec` custom con:
  - `datas` y `hiddenimports` necesarios (incluir recursos de Streamlit: `static`, `runtime`, etc.).
  - Modo `onedir` (sin `--onefile`; usar `COLLECT` en el `.spec`).
- Crear `build.bat`:
  ```bat
  @echo off
  call .venv\Scripts\activate
  pyinstaller --clean --noconfirm DATA_Dashboard.spec
  echo.
  echo Build terminado. Carpeta lista en: dist\DATA_Dashboard\
  echo Ejecutable principal: dist\DATA_Dashboard\DATA_Dashboard.exe
  ```
- Crear `scripts/package_release.ps1` que empaquete `dist\DATA_Dashboard\` en un `.zip` con el nombre `DATA_Dashboard_vX.Y.Z_YYYYMMDD.zip` (versionado + fecha).
- Probar el `.exe` en local (`.\dist\DATA_Dashboard\DATA_Dashboard.exe`) antes de dar la fase por terminada.
- `docs/BUILD.md` con el ciclo completo: modificar código → `build.bat` → probar → `package_release.ps1` → desplegar.

**Fase 8 — Despliegue en Windows Server**

**ANTES de empezar esta fase, Claude Code debe preguntar al PM la ruta `<INSTALL_PATH>` definitiva en el servidor.**

- Crear `scripts/install_service.ps1` con parámetros:
  ```powershell
  param(
      [Parameter(Mandatory=$true)]
      [string]$InstallPath,        # ej.: "C:\DATA_Dashboard" o "D:\Aplicaciones\DATA_Dashboard"

      [Parameter(Mandatory=$true)]
      [string]$ZipPath,            # ruta al .zip generado por package_release.ps1

      [Parameter(Mandatory=$true)]
      [string]$SecretsPath,        # ruta donde están secrets.key y credentials.enc
      # ... otros parámetros
  )
  ```
- El script:
  - Descomprime el `.zip` en `$InstallPath`.
  - Instala NSSM como servicio de Windows apuntando a `$InstallPath\DATA_Dashboard.exe`.
  - Configura las variables de entorno del servicio (`DATA_SOURCE`, `SECRETS_KEY_PATH`, `CREDENTIALS_PATH`, etc.).
  - Configura el arranque automático y la política de reinicio ante fallos.
  - Configura permisos NTFS de la carpeta de secretos para que solo la cuenta de servicio pueda leerla.
- `docs/DEPLOYMENT.md` con el procedimiento completo, incluyendo ejemplos con varias rutas posibles, cómo hacer un redeploy tras modificar el código, y cómo revertir.

**Fase 9 — Pulido y validación**
- Revisión de accesibilidad de colores (daltonismo: semáforo reconocible por forma/icono, no solo color).
- Performance con los 10.200 registros reales.
- Verificación de que el `.exe` no hace NINGUNA conexión saliente (ej.: con `netstat -b` o monitorizando con el firewall de Windows).
- Documento final `docs/ARCHITECTURE.md`.

---

## 10. STATUS.md — qué tiene que contener

Este fichero es **la puerta de entrada** para cualquiera (incluido un futuro Claude Code que retome el proyecto sin contexto). Debe permitir, leyéndolo en 2 minutos, saber:

1. **Qué es el proyecto** (2 líneas).
2. **En qué fase está ahora mismo** (ej.: "Fase 3 — UI base en curso, falta gráfico de evolución").
3. **Ruta de desarrollo**: `C:\Users\Javi\Documents\Proyectos\DATA_Dashboard`.
4. **Ruta de despliegue en servidor**: pendiente de decisión (si ya se ha decidido en la Fase 8, indicarla aquí).
5. **Cómo arrancar el proyecto en local** (comandos exactos, copiables, incluyendo activación del venv).
6. **Cómo ejecutar los tests**.
7. **Cómo generar el `.exe`** (una vez se llegue a la fase 7).
8. **Dónde está el Excel de datos** y cómo cambiar a modo SQL Server.
9. **Qué falta por hacer** (checklist con referencia a las fases del roadmap).
10. **Bloqueos o decisiones pendientes** (si las hay).
11. **Enlace al `DEVLOG.md`** y al `PROJECT_SPEC.md`.

Se actualiza **al final de cada fase**, cuando cambie el "ahora mismo".

---

## 11. DEVLOG.md — qué tiene que contener

Bitácora cronológica, append-only, de todo lo que se va haciendo. Cada entrada tiene:

```markdown
## [YYYY-MM-DD HH:MM] — Título corto de lo hecho

**Fase**: X — Nombre de la fase
**Commit**: <hash corto>

**Qué se ha hecho**:
- Bullet 1
- Bullet 2

**Decisiones técnicas relevantes**:
- (Si ha habido alguna)

**Problemas encontrados / a revisar**:
- (Si los ha habido)

**Siguiente paso**:
- Qué toca ahora.
```

Se actualiza **en cada commit relevante** (no hace falta en commits triviales de formateo).

---

## 12. Flujo de trabajo esperado de Claude Code

En cada turno de trabajo:

1. **Lee** `STATUS.md` para saber dónde se dejó el proyecto.
2. **Ejecuta** la fase que toque según el roadmap.
3. **Escribe código + tests**. Corre los tests antes de considerar la fase terminada.
4. **Commit** con mensaje descriptivo en Conventional Commits.
5. **Push** a `github.com/jvrlopma/DATA_Dashboard`.
6. **Actualiza** `DEVLOG.md` (añadir entrada) y `STATUS.md` (reescribir el estado).
7. **Commit + push** de los docs actualizados (puede ir en el mismo commit si es coherente).
8. Al acabar el turno: un resumen al PM de **qué se ha hecho, qué viene ahora, y si hay algo que necesites que el PM decida**.

---

## 13. Preguntas que debes hacerme ANTES de codificar (si aplica)

- Si el preflight detecta que la máquina de desarrollo **no es Windows**, párate y avísame: el `.exe` solo se puede compilar en Windows.
- Si alguna regla de estado de proyecto te resulta ambigua en un caso límite concreto, pregúntame con el caso en la mano.
- Si propones una librería distinta a las del stack fijado, explícame por qué y espera confirmación.
- Antes de empezar la Fase 7 (PyInstaller), confírmame si la máquina donde vas a compilar tiene acceso a PyPI (para `pip install pyinstaller`) o si hay un mirror interno de Aqualia.
- **ANTES de empezar la Fase 8, preguntar al PM por la ruta `<INSTALL_PATH>` definitiva del servidor y por la ruta de `<SECRETS_PATH>` (ubicación de `secrets.key` y `credentials.enc`).**

---

## 14. Ciclo de redeploy (recordatorio para el PM)

Una vez en producción, el ciclo de cambios será:

**En el equipo de desarrollo Windows** (`C:\Users\Javi\Documents\Proyectos\DATA_Dashboard`):
1. `git pull`
2. Modificar el código necesario.
3. Ejecutar tests: `pytest`.
4. Ejecutar `build.bat` → se genera `dist\DATA_Dashboard\`.
5. Probar en local: `.\dist\DATA_Dashboard\DATA_Dashboard.exe` y abrir `http://localhost:8501`.
6. Ejecutar `scripts\package_release.ps1` → se genera `DATA_Dashboard_vX.Y.Z_YYYYMMDD.zip`.
7. Copiar el `.zip` al servidor (recurso compartido, SCP, etc.).

**En el servidor Windows** (sustituir `<INSTALL_PATH>` por la ruta definitiva):
```powershell
# Parar el servicio
nssm stop DATA_Dashboard

# Backup de la versión anterior (por si hay que revertir)
Rename-Item "<INSTALL_PATH>\DATA_Dashboard" "<INSTALL_PATH>\DATA_Dashboard_backup_$(Get-Date -Format yyyyMMdd_HHmm)"

# Descomprimir la nueva versión
Expand-Archive -Path .\DATA_Dashboard_v1.2.0_20260430.zip -DestinationPath "<INSTALL_PATH>\"

# Arrancar el servicio
nssm start DATA_Dashboard

# Verificar que responde
Start-Sleep -Seconds 5
Invoke-WebRequest -Uri http://localhost:8501 -UseBasicParsing
```

8. Verificar en el navegador que el dashboard responde.
9. Si todo OK tras 24h, eliminar la carpeta `DATA_Dashboard_backup_*`. Si algo falla, restaurar el backup.

Esto queda detallado, con variantes y troubleshooting, en `docs/DEPLOYMENT.md`.

---

## 15. Checklist de "proyecto terminado"

- [ ] Preflight devuelve OK.
- [ ] Dashboard corre en local contra el Excel sin errores.
- [ ] Dashboard corre como `.exe` (carpeta onedir) contra el Excel sin errores.
- [ ] Dashboard corre como `.exe` (carpeta onedir) contra SQL Server con credenciales cifradas.
- [ ] Cero llamadas de red salientes en runtime (verificado con herramienta de red).
- [ ] Tests pasan al 100%.
- [ ] Ruta `<INSTALL_PATH>` definida por el PM y documentada en `STATUS.md` y `DEPLOYMENT.md`.
- [ ] `STATUS.md`, `DEVLOG.md`, `README.md`, `SECURITY.md`, `DEPLOYMENT.md`, `BUILD.md`, `ARCHITECTURE.md` completos y actualizados.
- [ ] Todo pusheado a `github.com/jvrlopma/DATA_Dashboard`.
- [ ] Carpeta `DATA_Dashboard\` instalada como servicio de Windows en el servidor.
- [ ] PM ha validado las 3 vistas en el dashboard desplegado.

---

**Fin del documento. Adelante.**

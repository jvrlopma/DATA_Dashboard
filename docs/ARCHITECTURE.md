# Arquitectura — DATA_Dashboard

Visión general del sistema: capas, flujo de datos y decisiones de diseño clave.

---

## 1. Diagrama de capas

```
┌─────────────────────────────────────────────────┐
│               Presentación (Streamlit)           │
│  app.py → Vista 1 | Vista 2 | Vista 3           │
│  src/ui/views/overview.py                        │
│  src/ui/views/project_detail.py                  │
│  src/ui/views/daily_ops.py                       │
└────────────────────┬────────────────────────────┘
                     │ usa
┌────────────────────▼────────────────────────────┐
│               Dominio                            │
│  src/domain/models.py        (Execution, ProjectHealth, enums)  │
│  src/domain/project_status.py (compute_status, compute_health)  │
└────────────────────┬────────────────────────────┘
                     │ usa
┌────────────────────▼────────────────────────────┐
│            Acceso a datos                        │
│  BaseRepository (abstracta)                      │
│    ├── ExcelRepository   (DATA_SOURCE=excel)     │
│    └── SqlServerRepository (DATA_SOURCE=sqlserver)│
│  factory.py → get_repository() según env var    │
└────────────────────┬────────────────────────────┘
                     │ usa (solo SqlServerRepository)
┌────────────────────▼────────────────────────────┐
│            Seguridad                             │
│  src/core/security.py                           │
│  CredentialStore → descifra credentials.enc     │
│  Fernet (cryptography) + secrets.key            │
└─────────────────────────────────────────────────┘
```

---

## 2. Flujo de arranque

```
launcher.py (o streamlit run app.py)
  → st.set_page_config()
  → load_repository()  [st.cache_resource — singleton]
      → get_repository()  [factory.py]
          → ExcelRepository(data/PWC_Monitorizacion_CdM.xlsx)
          └─ o SqlServerRepository → CredentialStore → SQL Server
  → sidebar: radio "Resumen global | Detalle | Operativa"
  → render(repo)  [vista seleccionada]
      → _load_*()  [st.cache_data TTL 5 min]
      → lógica de dominio (compute_health, etc.)
      → gráficos Plotly / tablas Streamlit
```

---

## 3. Componentes clave

### 3.1. factory.py + repositorios

`get_repository()` lee la variable de entorno `DATA_SOURCE`:

| Valor | Clase | Fuente |
|---|---|---|
| `excel` (default) | `ExcelRepository` | `data/PWC_Monitorizacion_CdM.xlsx` |
| `sqlserver` | `SqlServerRepository` | SQL Server vía pyodbc + SQLAlchemy |

El cambio de fuente es transparente para la capa de dominio y UI.

### 3.2. Dominio puro

`src/domain/` no importa pandas, pyodbc, ni Streamlit. Contiene:

- **`Execution`**: dataclass frozen con los datos de una ejecucion ETL.
- **`ProjectHealth`**: dataclass frozen con el estado calculado de un proyecto.
- **`ProjectStatus`**: enum OK / REGULAR / CRITICO.
- **`compute_status()`**: aplica los umbrales según el grupo del proyecto.
- **`compute_project_health()`**: detecta inactividad y calcula estado.

### 3.3. Caching en UI

Las vistas usan `@st.cache_data(ttl=300)` con el argumento `_repo` (prefijo `_` → excluido del hash). Esto evita re-consultas al repositorio en cada re-render de Streamlit, especialmente relevante en modo SQL Server.

### 3.4. Seguridad de credenciales

```
Desarrollo:  DATA_SOURCE=excel  → sin credenciales
Producción:  DATA_SOURCE=sqlserver
                → SECRETS_KEY_PATH  → secrets.key  (Fernet key)
                → CREDENTIALS_PATH  → credentials.enc (JSON cifrado)
                → CredentialStore descifra en RAM, nunca escribe a disco
```

Ver [SECURITY.md](SECURITY.md) para el manual operativo.

---

## 4. Empaquetado (PyInstaller onedir)

```
dist/DATA_Dashboard/
  DATA_Dashboard.exe        ← bootloader PyInstaller
  _internal/
    app.py                  ← código fuente empaquetado
    src/                    ← paquetes de la aplicación
    data/                   ← Excel de desarrollo
    streamlit/              ← assets estáticos del servidor Tornado
    ...dependencias...
```

`launcher.py` arranca Streamlit programáticamente con:
- `--global.developmentMode=false` (necesario en bundle PyInstaller)
- `--server.headless=true`
- `--browser.gatherUsageStats=false` (telemetría desactivada)
- `--server.fileWatcherType=none` (file watching innecesario en producción)

---

## 5. Accesibilidad

Los semáforos de estado usan **icono + patrón + color + texto** para que sean legibles sin distinción de color:

| Estado | Icono | Color | Patrón de relleno |
|---|---|---|---|
| OK | ✅ | Verde | Sólido |
| REGULAR | ⚠️ | Amarillo | Diagonal `/` |
| CRITICO | ❌ | Rojo | Cruz `x` |
| Sin datos | ⚫ | Gris | Sólido |

---

## 6. Conexiones de red en producción

El `.exe` no hace **ninguna conexión saliente** en condiciones normales:

| Componente | Conexión | Estado |
|---|---|---|
| Streamlit telemetría | `analytics.streamlit.io` | Desactivada (`--browser.gatherUsageStats=false`) |
| Streamlit server | `localhost:8501` | Solo local |
| SQL Server | Red corporativa interna | Solo si `DATA_SOURCE=sqlserver` |
| Plotly | CDN externo | No: Plotly bundled, sin CDN |
| PyPI / actualizaciones | Ninguna | El exe no auto-actualiza |

Para verificar en el servidor: `netstat -b -n | findstr DATA_Dashboard`

---

## 7. Proyectos ETL monitorizados

| Proyecto | Grupo | Umbral OK |
|---|---|---|
| AqualiaApemsa | A | 100 % exacto |
| AqualiaDW | A | 100 % exacto |
| AqualiaSII2_FICO | A | 100 % exacto |
| Aqualia_Diario | A | 100 % exacto |
| AqualiaODS | B | ≥ 90 % OK, ≥ 80 % REGULAR |
| AqualiaSII2_Doc_AEF | B | ≥ 90 % OK, ≥ 80 % REGULAR |
| AqualiaTPL | B | ≥ 90 % OK, ≥ 80 % REGULAR |
| Aqualia_GIS | B | ≥ 90 % OK, ≥ 80 % REGULAR |

Inactividad: sin ejecución en las últimas N horas (default 24 h, configurable) → estado CRITICO + etiqueta "Sin datos recientes".

---

## 8. Stack tecnológico

| Capa | Tecnología | Versión |
|---|---|---|
| UI | Streamlit | 1.56.0 |
| Gráficos | Plotly | 6.7.0 |
| Datos | pandas | 3.0.2 |
| Excel | openpyxl | 3.1.5 |
| SQL Server | pyodbc + SQLAlchemy | 5.3.0 + 2.0.49 |
| Seguridad | cryptography (Fernet) | 46.0.7 |
| Empaquetado | PyInstaller (onedir) | 6.11.1 |
| Servicio Windows | NSSM | — |
| Runtime | Python | 3.11.9 |

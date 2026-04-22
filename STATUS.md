# STATUS.md — DATA_Dashboard

## Que es este proyecto

Dashboard web interno (Streamlit) para el departamento de DATA de Aqualia.
Visualiza el estado de los 8 proyectos ETL a partir de la tabla `PWC_Monitorizacion_CdM`.

## Fase actual

**Fase 5 — Vista 3 Operativa diaria** (completada 2026-04-22)

Siguiente: **Fase 6 — Seguridad + capa SQL Server**
- Implementar `SqlServerRepository` con pyodbc + SQLAlchemy.
- Scripts `generate_key.py` y `encrypt_credentials.py`.
- `docs/SECURITY.md` con manual paso a paso.
- Requiere instalar ODBC Driver 18 for SQL Server.

## Ruta de desarrollo

```
C:\Users\Javi\Documents\Proyectos\DATA_Dashboard
```

## Ruta de despliegue en servidor

**Pendiente de decision del PM** (se decide antes de la Fase 8).
Placeholder: `<INSTALL_PATH>\DATA_Dashboard\`

## Como arrancar en local

```powershell
# Activar el entorno virtual
.\.venv\Scripts\Activate.ps1

# Arrancar Streamlit
streamlit run app.py
# -> Abrir http://localhost:8501
```

## Como ejecutar los tests

```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

## Como generar el .exe

Disponible a partir de la **Fase 7**. Ver [docs/BUILD.md](docs/BUILD.md).

## Fuente de datos

- **Desarrollo**: Excel en `data/PWC_Monitorizacion_CdM.xlsx`
- **Produccion**: SQL Server (variable `DATA_SOURCE=sqlserver`)

Para cambiar de fuente: editar la variable de entorno `DATA_SOURCE` (`excel` | `sqlserver`).

## Checklist de fases

- [x] Fase -1 — Preflight (entorno verificado)
- [x] Fase 0  — Bootstrap del repo
- [x] Fase 1  — Capa de datos (Excel)
- [x] Fase 2  — Dominio (modelos + logica de estado)
- [x] Fase 3  — UI base + Vista 1 (Resumen global)
- [x] Fase 4  — Vista 2 (Detalle por proyecto)
- [x] Fase 5  — Vista 3 (Operativa diaria)
- [ ] Fase 6  — Seguridad + capa SQL Server
- [ ] Fase 7  — Empaquetado con PyInstaller (onedir)
- [ ] Fase 8  — Despliegue en Windows Server
- [ ] Fase 9  — Pulido y validacion final

## Bloqueos / decisiones pendientes

- Ruta `<INSTALL_PATH>` del servidor: pendiente de decision del PM (necesaria antes de la Fase 8).
- ODBC Driver 18 for SQL Server: pendiente de instalacion (necesario en la Fase 6).

## Referencias

- [DEVLOG.md](DEVLOG.md) — Bitacora cronologica
- [PROJECT_SPEC.md](PROJECT_SPEC.md) — Especificacion tecnica completa

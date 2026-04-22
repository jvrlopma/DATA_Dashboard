# STATUS.md — DATA_Dashboard

## Que es este proyecto

Dashboard web interno (Streamlit) para el departamento de DATA de Aqualia.
Visualiza el estado de los 8 proyectos ETL a partir de la tabla `PWC_Monitorizacion_CdM`.

## Fase actual

**Fase 9 — Pulido y validacion** (completada, 2026-04-22)

Todas las fases del roadmap completadas excepto la Fase 8 (despliegue), que queda diferida
hasta que el PM decida la ruta `<INSTALL_PATH>` en el servidor destino.

## Ruta de desarrollo

```
C:\Users\Javi\Documents\Proyectos\DATA_Dashboard
```

## Ruta de despliegue en servidor

**Pendiente de decision del PM** (se decide antes de la Fase 8, diferida).

## Como arrancar en local

```powershell
# Activar el entorno virtual
.\.venv\Scripts\Activate.ps1

# Arrancar Streamlit (modo Excel, desarrollo)
streamlit run app.py --browser.gatherUsageStats=false
# -> Abrir http://localhost:8501

# Arrancar el .exe compilado (modo produccion)
dist\DATA_Dashboard\DATA_Dashboard.exe
```

## Como ejecutar los tests

```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

## Como generar el .exe

```bat
build.bat
```

Genera `dist\DATA_Dashboard\DATA_Dashboard.exe`. Ver [docs/BUILD.md](docs/BUILD.md).

Para empaquetar en .zip:

```powershell
.\scripts\package_release.ps1 -Version 1.0.0
```

## Fuente de datos

- **Desarrollo**: Excel en `data/PWC_Monitorizacion_CdM.xlsx` (`DATA_SOURCE=excel`, por defecto)
- **Produccion**: SQL Server (`DATA_SOURCE=sqlserver` + `SECRETS_KEY_PATH` + `CREDENTIALS_PATH`)

Para cambiar de fuente: editar la variable de entorno `DATA_SOURCE` (`excel` | `sqlserver`).

Cifrar credenciales SQL Server (una sola vez en el servidor):

```powershell
python scripts\generate_key.py --out C:\DATA_secrets\secrets.key
python scripts\encrypt_credentials.py --key C:\DATA_secrets\secrets.key --out C:\DATA_secrets\credentials.enc
```

Ver [docs/SECURITY.md](docs/SECURITY.md).

## Checklist de fases

- [x] Fase -1 — Preflight (entorno verificado)
- [x] Fase 0  — Bootstrap del repo
- [x] Fase 1  — Capa de datos (Excel)
- [x] Fase 2  — Dominio (modelos + logica de estado)
- [x] Fase 3  — UI base + Vista 1 (Resumen global)
- [x] Fase 4  — Vista 2 (Detalle por proyecto)
- [x] Fase 5  — Vista 3 (Operativa diaria)
- [x] Fase 6  — Seguridad + capa SQL Server
- [x] Fase 7  — Empaquetado con PyInstaller (onedir)
- [ ] Fase 8  — Despliegue en Windows Server (diferida; requiere INSTALL_PATH del PM)
- [x] Fase 9  — Pulido y validacion final

## Bloqueos / decisiones pendientes

- Ruta `<INSTALL_PATH>` del servidor: pendiente de decision del PM (necesaria antes de la Fase 8).

## Referencias

- [DEVLOG.md](DEVLOG.md) — Bitacora cronologica
- [PROJECT_SPEC.md](PROJECT_SPEC.md) — Especificacion tecnica completa
- [docs/SECURITY.md](docs/SECURITY.md) — Manual de credenciales cifradas
- [docs/BUILD.md](docs/BUILD.md) — Ciclo completo de build y packaging

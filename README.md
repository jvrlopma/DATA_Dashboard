# DATA_Dashboard

Dashboard web interno para el departamento de DATA de Aqualia (TI).

Proporciona una vision consolidada del estado de los 8 proyectos ETL
(PowerCenter 10.5.1 / SSIS) monitorizados en la tabla `PWC_Monitorizacion_CdM`.

## Ficheros excluidos del repositorio

> **IMPORTANTE — leer antes de clonar o desplegar.**

Los siguientes ficheros contienen datos sensibles y **nunca deben subirse a GitHub**. Están excluidos via `.gitignore` y deben gestionarse manualmente en cada entorno:

| Fichero | Contenido | Dónde obtenerlo |
|---|---|---|
| `data/PWC_Monitorizacion_CdM.xlsx` | Datos de monitorización ETL | Exportar desde SQL Server o solicitar al equipo DATA |
| `secrets.key` | Clave Fernet de cifrado | Generar con `python scripts/generate_key.py` |
| `credentials.enc` | Credenciales SQL Server cifradas | Generar con `python scripts/encrypt_credentials.py` |

Para el procedimiento completo de generación y configuración ver [docs/SECURITY.md](docs/SECURITY.md).

---

## Inicio rapido (desarrollo)

```powershell
# 1. Activar el entorno virtual
.\.venv\Scripts\Activate.ps1

# 2. Arrancar el dashboard
streamlit run app.py
```

Abre el navegador en http://localhost:8501

## Tests

```powershell
pytest
```

## Documentacion

| Documento | Descripcion |
|---|---|
| [STATUS.md](STATUS.md) | Estado actual del proyecto |
| [DEVLOG.md](DEVLOG.md) | Bitacora de desarrollo |
| [PROJECT_SPEC.md](PROJECT_SPEC.md) | Especificacion tecnica completa |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitectura y decisiones tecnicas |
| [docs/BUILD.md](docs/BUILD.md) | Como generar el .exe |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Guia de despliegue en servidor |
| [docs/SECURITY.md](docs/SECURITY.md) | Gestion de credenciales cifradas |

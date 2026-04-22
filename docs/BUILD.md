# Guía de Build — DATA_Dashboard

Ciclo completo: modificar código → compilar → probar → empaquetar → desplegar.

---

## Requisitos previos

- Python 3.11 en PATH (o activar el venv manualmente).
- Entorno virtual `.venv` instalado:
  ```bat
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
  ```
- Visual C++ Build Tools instalado (necesario para compilar pyodbc).
- Ejecutar **en Windows** (PyInstaller no hace cross-compilation).

---

## 1. Modificar el código fuente

Edita los ficheros en:
- `app.py` — navegación y carga del repositorio
- `src/ui/views/` — vistas de Streamlit
- `src/domain/` — lógica de negocio
- `src/core/data_access/` — repositorios de datos

No es necesario recompilar para probar cambios en desarrollo: ejecuta directamente con Streamlit:

```bat
.venv\Scripts\streamlit run app.py --browser.gatherUsageStats=false
```

---

## 2. Compilar el ejecutable

```bat
build.bat
```

El script activa el venv, llama a PyInstaller con `DATA_Dashboard.spec` y genera:

```
dist\
  DATA_Dashboard\
    DATA_Dashboard.exe       ← ejecutable principal
    _internal\               ← dependencias (no mover ni borrar)
      app.py
      src\
      data\
      streamlit\
      ...
```

> **Modo onedir**: toda la carpeta `dist\DATA_Dashboard\` debe copiarse al servidor como una unidad. El `.exe` no funciona sin la carpeta `_internal\`.

---

## 3. Probar el ejecutable en local

```bat
dist\DATA_Dashboard\DATA_Dashboard.exe
```

Abre un navegador en `http://localhost:8501` y verifica:

- [ ] Vista 1 — Resumen global carga correctamente con el Excel de `data/`.
- [ ] Vista 2 — Detalle por proyecto funciona sin errores.
- [ ] Vista 3 — Operativa diaria muestra el Gantt.
- [ ] No aparecen errores de importación en la consola.
- [ ] Streamlit no intenta conectar con `analytics.streamlit.io` (telemetría desactivada).

Para probar contra SQL Server, establece las variables de entorno antes de lanzar:

```bat
set DATA_SOURCE=sqlserver
set SECRETS_KEY_PATH=C:\DATA_secrets\secrets.key
set CREDENTIALS_PATH=C:\DATA_secrets\credentials.enc
dist\DATA_Dashboard\DATA_Dashboard.exe
```

---

## 4. Empaquetar en .zip

```powershell
powershell -ExecutionPolicy Bypass -File scripts\package_release.ps1 -Version 1.0.0
```

Genera `dist\DATA_Dashboard_v1.0.0_YYYYMMDD.zip` comprimido con las mismas instrucciones de despliegue impresas en consola.

Para cambiar el directorio de salida del .zip:

```powershell
.\scripts\package_release.ps1 -Version 1.0.0 -OutDir C:\Releases
```

---

## 5. Desplegar en el servidor

Ver [docs/DEPLOYMENT.md](DEPLOYMENT.md) para el procedimiento completo.

Resumen rápido:

1. Copiar el `.zip` al servidor Windows.
2. Parar el servicio: `nssm stop DATA_Dashboard`
3. Descomprimir sobre la carpeta de instalación (sobreescribir todo).
4. Arrancar el servicio: `nssm start DATA_Dashboard`
5. Verificar en navegador: `http://localhost:8501`

---

## Referencia: ficheros del sistema de build

| Fichero | Propósito |
|---|---|
| `launcher.py` | Entry point del `.exe`; arranca Streamlit programáticamente |
| `DATA_Dashboard.spec` | Spec custom de PyInstaller (versionado en Git) |
| `build.bat` | Invoca PyInstaller; activa el venv automáticamente |
| `scripts/package_release.ps1` | Empaqueta `dist\DATA_Dashboard\` en un `.zip` versionado |
| `docs/BUILD.md` | Esta guía |
| `docs/DEPLOYMENT.md` | Procedimiento de despliegue en servidor |

---

## Solución de problemas frecuentes

### El `.exe` arranca pero la UI no carga (pantalla en blanco)

- Verifica que `_internal\streamlit\static\` existe y no está vacío.
- Abre la consola y busca errores de tipo `FileNotFoundError` o `ModuleNotFoundError`.

### Error `ModuleNotFoundError` al arrancar

- Añade el módulo a `hiddenimports` en `DATA_Dashboard.spec` y recompila con `build.bat`.

### El antivirus bloquea el `.exe`

- El modo onedir no se autoextrae, por lo que debería ser compatible con la mayoría de antivirus.
- Si Defender for Endpoint lo bloquea, añade la carpeta de instalación a las exclusiones del AV corporativo.
- **Nunca usar `--onefile`** (se autoextrae en `%TEMP%`, mucho más propenso a falsos positivos).

### `build.bat` falla con error de activación del venv

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### El `.exe` no encuentra `secrets.key` / `credentials.enc`

Las rutas se pasan como variables de entorno del servicio, no están embebidas en el `.exe`. Ver [docs/SECURITY.md](SECURITY.md).

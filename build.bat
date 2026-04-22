@echo off
REM build.bat — Compila DATA_Dashboard en modo onedir con PyInstaller
REM
REM Uso:
REM   build.bat
REM
REM Resultado:
REM   dist\DATA_Dashboard\DATA_Dashboard.exe

echo.
echo ============================================================
echo   DATA_Dashboard -- Build (PyInstaller onedir)
echo ============================================================
echo.

REM Activar el entorno virtual
call .venv\Scripts\activate
if errorlevel 1 (
    echo [ERROR] No se pudo activar el entorno virtual .venv
    echo         Ejecuta primero: python -m venv .venv ^&^& pip install -r requirements.txt
    exit /b 1
)

echo [1/2] Compilando con PyInstaller...
pyinstaller --clean --noconfirm DATA_Dashboard.spec
if errorlevel 1 (
    echo.
    echo [ERROR] La compilacion ha fallado. Revisa los mensajes anteriores.
    exit /b 1
)

echo.
echo [2/2] Build completado correctamente.
echo.
echo ============================================================
echo   Resultado:
echo     Carpeta:     dist\DATA_Dashboard\
echo     Ejecutable:  dist\DATA_Dashboard\DATA_Dashboard.exe
echo ============================================================
echo.
echo Para probar localmente:
echo   dist\DATA_Dashboard\DATA_Dashboard.exe
echo.
echo Para empaquetar en .zip:
echo   powershell -ExecutionPolicy Bypass -File scripts\package_release.ps1 -Version 1.0.0
echo.

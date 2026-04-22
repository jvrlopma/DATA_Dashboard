#Requires -Version 5.1
<#
.SYNOPSIS
    Empaqueta dist\DATA_Dashboard\ en un .zip versionado.

.DESCRIPTION
    Comprime la carpeta onedir generada por build.bat en un fichero .zip con
    nombre DATA_Dashboard_vX.Y.Z_YYYYMMDD.zip listo para copiar al servidor.

.PARAMETER Version
    Version semantica del release, p. ej. "1.0.0".

.PARAMETER DistPath
    Ruta a la carpeta onedir generada por PyInstaller.
    Default: dist\DATA_Dashboard (relativo al CWD).

.PARAMETER OutDir
    Directorio donde se guarda el .zip resultante.
    Default: dist\ (relativo al CWD).

.EXAMPLE
    .\scripts\package_release.ps1 -Version 1.0.0
    .\scripts\package_release.ps1 -Version 1.2.3 -OutDir C:\Releases
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Version,

    [string]$DistPath = "dist\DATA_Dashboard",

    [string]$OutDir   = "dist"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------
if (-not (Test-Path $DistPath -PathType Container)) {
    Write-Error "No se encuentra la carpeta de distribución: $DistPath`nEjecuta build.bat primero."
    exit 1
}

$exePath = Join-Path $DistPath "DATA_Dashboard.exe"
if (-not (Test-Path $exePath -PathType Leaf)) {
    Write-Error "No se encuentra el ejecutable: $exePath`nEjecuta build.bat primero."
    exit 1
}

if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Error "Formato de version incorrecto: '$Version'. Usa X.Y.Z (p. ej. 1.0.0)."
    exit 1
}

# ---------------------------------------------------------------------------
# Nombre del fichero de salida
# ---------------------------------------------------------------------------
$fecha   = Get-Date -Format "yyyyMMdd"
$zipName = "DATA_Dashboard_v${Version}_${fecha}.zip"
$zipPath = Join-Path $OutDir $zipName

if (-not (Test-Path $OutDir -PathType Container)) {
    New-Item -Path $OutDir -ItemType Directory -Force | Out-Null
}

# ---------------------------------------------------------------------------
# Comprimir
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  DATA_Dashboard -- Package Release" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Version:  v$Version" -ForegroundColor White
Write-Host "  Origen:   $((Resolve-Path $DistPath).Path)" -ForegroundColor White
Write-Host "  Destino:  $((Resolve-Path $OutDir).Path)\$zipName" -ForegroundColor White
Write-Host ""

if (Test-Path $zipPath) {
    $resp = Read-Host "Ya existe '$zipName'. Sobreescribir? [s/N]"
    if ($resp -notmatch "^[sS]$") {
        Write-Host "Operacion cancelada." -ForegroundColor Yellow
        exit 0
    }
    Remove-Item $zipPath -Force
}

Write-Host "Comprimiendo..." -ForegroundColor Cyan

try {
    Compress-Archive -Path "$DistPath\*" -DestinationPath $zipPath -CompressionLevel Optimal
} catch {
    Write-Error "Error al comprimir: $_"
    exit 1
}

$sizeMB = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)

Write-Host ""
Write-Host "  [OK] Paquete generado: $zipName ($sizeMB MB)" -ForegroundColor Green
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Proximos pasos:" -ForegroundColor Cyan
Write-Host "  1. Copia $zipName al servidor Windows." -ForegroundColor White
Write-Host "  2. Para el servicio DATA_Dashboard (nssm stop DATA_Dashboard)." -ForegroundColor White
Write-Host "  3. Descomprime sobre la carpeta de instalacion." -ForegroundColor White
Write-Host "  4. Arranca el servicio (nssm start DATA_Dashboard)." -ForegroundColor White
Write-Host "  5. Verifica en el navegador: http://localhost:8501" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

#Requires -Version 5.1
<#
.SYNOPSIS
    Preflight -- verifica el entorno de desarrollo para DATA_Dashboard.

.DESCRIPTION
    Comprueba todas las herramientas necesarias antes de empezar a codificar.
    Por defecto solo verifica y genera preflight_report.md.
    Con -Install intenta instalar lo que falte (previa confirmacion).

.PARAMETER Install
    Si se indica, intenta instalar las herramientas faltantes tras confirmacion.

.EXAMPLE
    .\scripts\preflight.ps1
    .\scripts\preflight.ps1 -Install
#>
param(
    [switch]$Install
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------
$DEV_PATH       = "C:\Users\Javi\Documents\Proyectos\DATA_Dashboard"
$REPO_URL       = "https://github.com/jvrlopma/DATA_Dashboard"
$REPORT         = Join-Path $DEV_PATH "preflight_report.md"
$STREAMLIT_PORT = 8501

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
$results = [System.Collections.Generic.List[hashtable]]::new()

function Add-Result {
    param(
        [int]    $Num,
        [string] $Name,
        [bool]   $OK,
        [string] $Detail,
        [bool]   $Blocking = $true
    )
    $results.Add(@{
        Num      = $Num
        Name     = $Name
        OK       = $OK
        Detail   = $Detail
        Blocking = $Blocking
    })
}

function Write-Check { param([string]$Msg) Write-Host "  > $Msg" -ForegroundColor Cyan }
function Write-OK    { param([string]$m)   Write-Host "  [OK] $m" -ForegroundColor Green }
function Write-WARN  { param([string]$m)   Write-Host "  [!!] $m" -ForegroundColor Yellow }
function Write-FAIL  { param([string]$m)   Write-Host "  [XX] $m" -ForegroundColor Red }

function Confirm-Action {
    param([string]$Question)
    $resp = Read-Host "$Question [s/N]"
    return ($resp -match "^[sS]$")
}

function Test-CommandExists {
    param([string]$cmd)
    return ($null -ne (Get-Command $cmd -ErrorAction SilentlyContinue))
}

# ---------------------------------------------------------------------------
# CABECERA
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  DATA_Dashboard -- Preflight Check" -ForegroundColor Magenta
Write-Host ("  Fecha: " + (Get-Date -Format 'yyyy-MM-dd HH:mm')) -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""

# ---------------------------------------------------------------------------
# CHECK 1 -- Es Windows
# ---------------------------------------------------------------------------
Write-Host "[1/12] Verificando sistema operativo..." -ForegroundColor White
Write-Check "Comprobando que el SO es Windows"

$isWin = ($env:OS -eq "Windows_NT")
if ($isWin) {
    $osDetail = (Get-CimInstance Win32_OperatingSystem).Caption
    Write-OK "Windows detectado: $osDetail"
    Add-Result 1 "Sistema operativo Windows" $true $osDetail
} else {
    Write-FAIL "No es Windows. El .exe SOLO se puede compilar en Windows. Abortando."
    Add-Result 1 "Sistema operativo Windows" $false "No es Windows -- build imposible" $true
    Write-Host ""
    Write-Host "PREFLIGHT ABORTADO: se requiere Windows." -ForegroundColor Red
    exit 1
}

# ---------------------------------------------------------------------------
# CHECK 2 -- Ruta de desarrollo existe y es escribible
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/12] Verificando ruta de desarrollo..." -ForegroundColor White
Write-Check "Comprobando existencia de: $DEV_PATH"

if (Test-Path $DEV_PATH -PathType Container) {
    $testFile = Join-Path $DEV_PATH ".preflight_write_test"
    try {
        [void](New-Item -Path $testFile -ItemType File -Force)
        Remove-Item $testFile -Force
        Write-OK "Ruta existe y es escribible: $DEV_PATH"
        Add-Result 2 "Ruta de desarrollo existe y es escribible" $true $DEV_PATH
    } catch {
        Write-FAIL "Ruta existe pero NO es escribible: $DEV_PATH"
        Add-Result 2 "Ruta de desarrollo existe y es escribible" $false "Sin permisos de escritura en $DEV_PATH"
    }
} else {
    Write-WARN "La ruta NO existe: $DEV_PATH"
    if ($Install) {
        if (Confirm-Action "Crear la ruta $DEV_PATH ?") {
            try {
                New-Item -Path $DEV_PATH -ItemType Directory -Force | Out-Null
                Write-OK "Ruta creada: $DEV_PATH"
                Add-Result 2 "Ruta de desarrollo existe y es escribible" $true "Creada durante preflight"
            } catch {
                Write-FAIL "No se pudo crear la ruta: $_"
                Add-Result 2 "Ruta de desarrollo existe y es escribible" $false "Error al crear: $_"
            }
        } else {
            Add-Result 2 "Ruta de desarrollo existe y es escribible" $false "No creada por el usuario"
        }
    } else {
        Add-Result 2 "Ruta de desarrollo existe y es escribible" $false "Ruta no existe. Ejecutar con -Install para crearla."
    }
}

# ---------------------------------------------------------------------------
# CHECK 3 -- Python 3.11
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/12] Verificando Python 3.11..." -ForegroundColor White
Write-Check "Ejecutando: python --version"

$pythonOK     = $false
$pythonDetail = "No encontrado"

if (Test-CommandExists "python") {
    try {
        $pyVer = (& python --version 2>&1).ToString().Trim()
        Write-Check "Version detectada: $pyVer"
        if ($pyVer -match "Python 3\.11") {
            Write-OK "Python 3.11 encontrado: $pyVer"
            $pythonOK     = $true
            $pythonDetail = $pyVer
        } else {
            Write-WARN "Python encontrado pero NO es 3.11: $pyVer"
            $pythonDetail = "Version incorrecta: $pyVer (se requiere 3.11)"
        }
    } catch {
        Write-FAIL "Error al ejecutar python: $_"
        $pythonDetail = "Error: $_"
    }
} else {
    Write-FAIL "python no encontrado en PATH"
    Write-Host "  -> Instalar desde: https://www.python.org/downloads/release/python-3119/" -ForegroundColor Yellow
    Write-Host "     IMPORTANTE: marcar 'Add Python to PATH' durante la instalacion." -ForegroundColor Yellow
    if ($Install -and (Test-CommandExists "winget")) {
        if (Confirm-Action "Intentar instalar Python 3.11 con winget?") {
            winget install Python.Python.3.11 --silent
            $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
            if (Test-CommandExists "python") {
                $pyVer2 = (& python --version 2>&1).ToString().Trim()
                if ($pyVer2 -match "Python 3\.11") {
                    $pythonOK     = $true
                    $pythonDetail = $pyVer2
                    Write-OK "Python 3.11 instalado: $pyVer2"
                }
            }
        }
    }
}
Add-Result 3 "Python 3.11 en PATH" $pythonOK $pythonDetail

# ---------------------------------------------------------------------------
# CHECK 4 -- pip actualizado
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/12] Verificando pip..." -ForegroundColor White
Write-Check "Ejecutando: python -m pip --version"

$pipOK     = $false
$pipDetail = "No disponible"

if ($pythonOK) {
    try {
        $pipVer    = ((& python -m pip --version 2>&1) | Out-String).Trim()
        Write-OK "pip encontrado: $pipVer"
        $pipOK     = $true
        $pipDetail = $pipVer
        if ($Install) {
            Write-Check "Actualizando pip..."
            & python -m pip install --upgrade pip --quiet 2>&1 | Out-Null
            $pipVer2   = (& python -m pip --version 2>&1).ToString().Trim()
            $pipDetail = $pipVer2
            Write-OK "pip actualizado: $pipVer2"
        }
    } catch {
        Write-FAIL "Error con pip: $_"
        $pipDetail = "Error: $_"
    }
} else {
    Write-WARN "Saltando (Python 3.11 no disponible)"
}
Add-Result 4 "pip disponible" $pipOK $pipDetail

# ---------------------------------------------------------------------------
# CHECK 5 -- Git en PATH
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[5/12] Verificando Git..." -ForegroundColor White
Write-Check "Ejecutando: git --version"

$gitOK     = $false
$gitDetail = "No encontrado"

if (Test-CommandExists "git") {
    try {
        $gitVer    = (& git --version 2>&1).ToString().Trim()
        Write-OK "Git encontrado: $gitVer"
        $gitOK     = $true
        $gitDetail = $gitVer
    } catch {
        Write-FAIL "Error al ejecutar git: $_"
        $gitDetail = "Error: $_"
    }
} else {
    Write-FAIL "git no encontrado en PATH"
    Write-Host "  -> Instalar desde: https://git-scm.com/download/win" -ForegroundColor Yellow
    if ($Install -and (Test-CommandExists "winget")) {
        if (Confirm-Action "Intentar instalar Git con winget?") {
            winget install Git.Git --silent
            $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
            if (Test-CommandExists "git") {
                $gitVer2   = (& git --version 2>&1).ToString().Trim()
                $gitOK     = $true
                $gitDetail = $gitVer2
                Write-OK "Git instalado: $gitVer2"
            }
        }
    }
}
Add-Result 5 "Git en PATH" $gitOK $gitDetail

# ---------------------------------------------------------------------------
# CHECK 6 -- Configuracion de Git (user.name y user.email)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[6/12] Verificando configuracion de Git..." -ForegroundColor White

$gitConfigOK     = $false
$gitConfigDetail = ""

if ($gitOK) {
    try {
        $gitNameRaw  = & git config --global user.name  2>&1
        $gitEmailRaw = & git config --global user.email 2>&1
        $gitName     = if ($gitNameRaw)  { $gitNameRaw.ToString().Trim()  } else { "" }
        $gitEmail    = if ($gitEmailRaw) { $gitEmailRaw.ToString().Trim() } else { "" }
        $hasName  = ($gitName  -ne "") -and ($gitName  -notmatch "error")
        $hasEmail = ($gitEmail -ne "") -and ($gitEmail -notmatch "error")

        if ($hasName -and $hasEmail) {
            Write-OK "Git configurado -- user.name: '$gitName' | user.email: '$gitEmail'"
            $gitConfigOK     = $true
            $gitConfigDetail = "user.name=$gitName | user.email=$gitEmail"
        } else {
            Write-WARN "Git no configurado correctamente."
            if (-not $hasName)  { Write-WARN "  Falta: git config --global user.name  'Tu Nombre'" }
            if (-not $hasEmail) { Write-WARN "  Falta: git config --global user.email 'tu@email.com'" }
            $gitConfigDetail = "Falta configurar user.name y/o user.email"
        }
    } catch {
        Write-FAIL "Error verificando git config: $_"
        $gitConfigDetail = "Error: $_"
    }
} else {
    Write-WARN "Saltando (Git no disponible)"
    $gitConfigDetail = "Git no disponible"
}
Add-Result 6 "Git configurado (user.name y user.email)" $gitConfigOK $gitConfigDetail

# ---------------------------------------------------------------------------
# CHECK 7 -- Acceso al repo remoto
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[7/12] Verificando acceso al repo remoto..." -ForegroundColor White
Write-Check "Ejecutando: git ls-remote $REPO_URL"

$repoOK     = $false
$repoDetail = "No comprobado"

if ($gitOK) {
    try {
        $lsRemote  = (& git ls-remote $REPO_URL 2>&1)
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Acceso al repo remoto OK: $REPO_URL"
            $repoOK     = $true
            $repoDetail = "Accesible"
        } else {
            Write-FAIL "No se puede acceder al repo: $lsRemote"
            $repoDetail = "Error: $lsRemote -- Posibles causas: proxy corporativo, PAT de GitHub necesario."
        }
    } catch {
        Write-FAIL "Error al verificar repo remoto: $_"
        $repoDetail = "Error: $_"
    }
} else {
    Write-WARN "Saltando (Git no disponible)"
    $repoDetail = "Git no disponible"
}
Add-Result 7 "Acceso al repo remoto GitHub" $repoOK $repoDetail

# ---------------------------------------------------------------------------
# CHECK 8 -- Visual C++ Build Tools
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[8/12] Verificando Visual C++ Build Tools..." -ForegroundColor White
Write-Check "Buscando vswhere o directorios MSVC..."

$vcOK     = $false
$vcDetail = "No detectado"

$vsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $vsWhere) {
    try {
        $vsJson = & "$vsWhere" -products * -requires Microsoft.VisualCpp.Tools.HostX64.TargetX64 -format json 2>&1
        $vsInstalls = $vsJson | ConvertFrom-Json
        if ($vsInstalls -and $vsInstalls.Count -gt 0) {
            $vsDetail = $vsInstalls[0].displayName
            Write-OK "Visual C++ Build Tools encontrado: $vsDetail"
            $vcOK     = $true
            $vcDetail = $vsDetail
        }
    } catch { }
}

if (-not $vcOK) {
    $clPaths = @(
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\BuildTools\VC\Tools\MSVC",
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC"
    )
    foreach ($p in $clPaths) {
        if (Test-Path $p) {
            Write-OK "MSVC encontrado en: $p"
            $vcOK     = $true
            $vcDetail = $p
            break
        }
    }
}

if (-not $vcOK) {
    Write-WARN "Visual C++ Build Tools NO detectado."
    Write-Host "  -> Instalar desde: https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor Yellow
    Write-Host "     Seleccionar: 'Desktop development with C++'" -ForegroundColor Yellow
    if ($Install) {
        if (Confirm-Action "Abrir la URL de descarga en el navegador?") {
            Start-Process "https://visualstudio.microsoft.com/visual-cpp-build-tools/"
            Read-Host "  Pulsa ENTER cuando hayas terminado la instalacion de Visual C++ Build Tools"
        }
    }
}
Add-Result 8 "Visual C++ Build Tools" $vcOK $vcDetail

# ---------------------------------------------------------------------------
# CHECK 9 -- Microsoft ODBC Driver 18 for SQL Server
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[9/12] Verificando Microsoft ODBC Driver 18 for SQL Server..." -ForegroundColor White
Write-Check "Buscando en drivers ODBC instalados..."

$odbcOK     = $false
$odbcDetail = "No detectado"

try {
    $odbcDrivers = Get-OdbcDriver -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "ODBC Driver 1[78] for SQL Server" }
    if ($odbcDrivers) {
        $driverNames = ($odbcDrivers | ForEach-Object { $_.Name }) -join ", "
        Write-OK "ODBC Driver encontrado: $driverNames"
        $odbcOK     = $true
        $odbcDetail = $driverNames
    } else {
        Write-WARN "ODBC Driver 18 for SQL Server NO detectado en esta maquina (informativo)."
        Write-Host "  -> Solo necesario en el servidor Windows destino del despliegue." -ForegroundColor Yellow
        Write-Host "     En desarrollo se usa DATA_SOURCE=excel (Excel local, sin ODBC)." -ForegroundColor Yellow
    }
} catch {
    Write-WARN "Error al verificar drivers ODBC: $_"
    $odbcDetail = "Error: $_"
}
Add-Result 9 "Microsoft ODBC Driver 18 for SQL Server" $odbcOK $odbcDetail $false

# ---------------------------------------------------------------------------
# CHECK 10 -- Virtualenv creable
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[10/12] Verificando que se puede crear un virtualenv..." -ForegroundColor White

$venvOK     = $false
$venvDetail = "No comprobado"

if ($pythonOK) {
    $tmpVenv = Join-Path $env:TEMP ("preflight_venv_" + (Get-Random).ToString())
    Write-Check "Intentando: python -m venv $tmpVenv"
    try {
        & python -m venv $tmpVenv 2>&1 | Out-Null
        if (Test-Path (Join-Path $tmpVenv "Scripts\python.exe")) {
            Write-OK "Virtualenv creado correctamente (y eliminado)"
            $venvOK     = $true
            $venvDetail = "OK"
        } else {
            Write-FAIL "El directorio de venv se creo pero falta Scripts\python.exe"
            $venvDetail = "Creacion incompleta"
        }
    } catch {
        Write-FAIL "Error al crear virtualenv: $_"
        $venvDetail = "Error: $_"
    } finally {
        if (Test-Path $tmpVenv) { Remove-Item $tmpVenv -Recurse -Force -ErrorAction SilentlyContinue }
    }
} else {
    Write-WARN "Saltando (Python 3.11 no disponible)"
    $venvDetail = "Python no disponible"
}
Add-Result 10 "Virtualenv creable (python -m venv)" $venvOK $venvDetail

# ---------------------------------------------------------------------------
# CHECK 11 -- NSSM (informativo)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[11/12] Verificando NSSM (informativo -- solo relevante en servidor)..." -ForegroundColor White
Write-Check "Buscando nssm en PATH..."

$nssmOK     = $false
$nssmDetail = "No en PATH (informativo -- instalar en el servidor destino)"

if (Test-CommandExists "nssm") {
    try {
        $nssmVer    = (& nssm version 2>&1 | Select-Object -First 1).ToString().Trim()
        Write-OK "NSSM encontrado: $nssmVer"
        $nssmOK     = $true
        $nssmDetail = $nssmVer
    } catch {
        $nssmDetail = "nssm en PATH pero error al ejecutar"
    }
} else {
    Write-WARN "NSSM no detectado en PATH (no bloqueante en desarrollo)."
    Write-Host "  -> Descargar desde: https://nssm.cc/download" -ForegroundColor Yellow
    Write-Host "     Solo necesario en el Windows Server destino del despliegue." -ForegroundColor Yellow
}
Add-Result 11 "NSSM (Non-Sucking Service Manager)" $nssmOK $nssmDetail $false

# ---------------------------------------------------------------------------
# CHECK 12 -- Puerto 8501 libre
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[12/12] Verificando que el puerto $STREAMLIT_PORT esta libre..." -ForegroundColor White
Write-Check "Comprobando puerto $STREAMLIT_PORT..."

$portOK     = $false
$portDetail = ""

try {
    $tcpConn = Get-NetTCPConnection -LocalPort $STREAMLIT_PORT -State Listen -ErrorAction SilentlyContinue
    if ($tcpConn) {
        $pidOwner = ($tcpConn | Select-Object -First 1).OwningProcess
        $procName = (Get-Process -Id $pidOwner -ErrorAction SilentlyContinue).ProcessName
        Write-WARN "Puerto $STREAMLIT_PORT ocupado por proceso '$procName' (PID $pidOwner)."
        Write-Host "  -> Puedes usar otro puerto con --server.port=XXXX en el launcher." -ForegroundColor Yellow
        $portDetail = "Ocupado por $procName (PID $pidOwner). Usar otro puerto."
    } else {
        Write-OK "Puerto $STREAMLIT_PORT libre."
        $portOK     = $true
        $portDetail = "Puerto $STREAMLIT_PORT libre"
    }
} catch {
    try {
        $test = Test-NetConnection -ComputerName localhost -Port $STREAMLIT_PORT -WarningAction SilentlyContinue
        if ($test.TcpTestSucceeded) {
            Write-WARN "Puerto $STREAMLIT_PORT parece ocupado (Test-NetConnection)."
            $portDetail = "Puerto ocupado (verificar manualmente)"
        } else {
            Write-OK "Puerto $STREAMLIT_PORT libre (Test-NetConnection)."
            $portOK     = $true
            $portDetail = "Puerto $STREAMLIT_PORT libre"
        }
    } catch {
        Write-WARN "No se pudo verificar el puerto $STREAMLIT_PORT"
        $portDetail = "No verificable -- asumir libre"
        $portOK     = $true
    }
}
Add-Result 12 "Puerto $STREAMLIT_PORT libre" $portOK $portDetail

# ---------------------------------------------------------------------------
# RESUMEN
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  RESUMEN DEL PREFLIGHT" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta

$blockFail = $false

foreach ($r in $results) {
    $icon     = if ($r.OK) { "[OK]" } else { "[XX]" }
    $color    = if ($r.OK) { "Green" } elseif ($r.Blocking) { "Red" } else { "Yellow" }
    $blocking = if (-not $r.OK -and $r.Blocking) { " [BLOQUEANTE]" } else { "" }
    Write-Host ("  {0} [{1,2}/12] {2}{3}" -f $icon, $r.Num, $r.Name, $blocking) -ForegroundColor $color
    if (-not $r.OK) {
        Write-Host ("           -> {0}" -f $r.Detail) -ForegroundColor DarkYellow
    }
    if (-not $r.OK -and $r.Blocking) { $blockFail = $true }
}

Write-Host ""
if ($blockFail) {
    Write-Host "  RESULTADO: PREFLIGHT FALLIDO -- hay comprobaciones bloqueantes." -ForegroundColor Red
    Write-Host "  Resuelve los puntos marcados [XX][BLOQUEANTE] y vuelve a ejecutar." -ForegroundColor Red
} else {
    Write-Host "  RESULTADO: PREFLIGHT OK -- entorno listo para continuar." -ForegroundColor Green
}
Write-Host ""

# ---------------------------------------------------------------------------
# GENERAR preflight_report.md
# ---------------------------------------------------------------------------
$reportLines = [System.Collections.Generic.List[string]]::new()
$reportLines.Add("# Preflight Report -- DATA_Dashboard")
$reportLines.Add("")
$reportLines.Add("**Fecha**: " + (Get-Date -Format 'yyyy-MM-dd HH:mm'))
$modoStr = if ($Install) { "Verificacion + Instalacion (-Install)" } else { "Solo verificacion" }
$reportLines.Add("**Modo**: " + $modoStr)
$reportLines.Add("")
$reportLines.Add("## Resultados")
$reportLines.Add("")
$reportLines.Add("| # | Comprobacion | Estado | Detalle |")
$reportLines.Add("|---|---|---|---|")

foreach ($r in $results) {
    $estado  = if ($r.OK) { "OK" } elseif ($r.Blocking) { "FALLA (bloqueante)" } else { "AVISO (no bloqueante)" }
    $detalle = $r.Detail -replace "\|", "\|"
    $reportLines.Add(("| {0} | {1} | {2} | {3} |" -f $r.Num, $r.Name, $estado, $detalle))
}

$reportLines.Add("")
if ($blockFail) {
    $reportLines.Add("## Conclusion: PREFLIGHT FALLIDO")
    $reportLines.Add("")
    $reportLines.Add("Hay comprobaciones bloqueantes sin resolver. No avanzar a la Fase 0.")
} else {
    $reportLines.Add("## Conclusion: PREFLIGHT OK")
    $reportLines.Add("")
    $reportLines.Add("Entorno verificado. Se puede avanzar a la Fase 0.")
}

$reportContent = $reportLines -join "`r`n"
[System.IO.File]::WriteAllText($REPORT, $reportContent, [System.Text.Encoding]::UTF8)

Write-Host "  Informe guardado en: $REPORT" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# CODIGO DE SALIDA
# ---------------------------------------------------------------------------
if ($blockFail) { exit 1 } else { exit 0 }

#Requires -Version 5.1
<#
.SYNOPSIS
    Setup shared_Environment for AILearning project - Python venv with all required packages.

.DESCRIPTION
    This script:
    1. Ensures Python 3.13.2 is installed (via winget)
    2. Creates shared_Environment virtual environment
    3. Installs all consolidated requirements
    4. Registers Jupyter kernel
    5. Prints next steps for optional software

.PARAMETER SkipPythonInstall
    Skip Python installation check (use if Python 3.13.2 is already installed).

.PARAMETER SkipPackages
    Only create venv, do not install packages.

.EXAMPLE
    .\setup_shared_Environment.ps1
    Full setup: Python, venv, packages, Jupyter kernel.

.EXAMPLE
    .\setup_shared_Environment.ps1 -SkipPythonInstall
    Create venv and install packages only (Python assumed installed).
#>

param(
    [switch]$SkipPythonInstall,
    [switch]$SkipPackages
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot "shared_Environment"
$RequirementsFile = Join-Path $ProjectRoot "shared_Environment_requirements.txt"

# ----- Helper Functions -----
function Write-Step { param([string]$Msg) Write-Host "`n==> $Msg" -ForegroundColor Cyan }
function Write-Ok { param([string]$Msg) Write-Host "  [OK] $Msg" -ForegroundColor Green }
function Write-Warn { param([string]$Msg) Write-Host "  [WARN] $Msg" -ForegroundColor Yellow }
function Write-Info { param([string]$Msg) Write-Host "  [INFO] $Msg" -ForegroundColor Gray }

# ----- 1. Python -----
if (-not $SkipPythonInstall) {
    Write-Step "Checking Python 3.13.2..."
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

    $pyVersion = $null
    try {
        $pyVersion = python --version 2>&1
    } catch { }

    if ($pyVersion -notmatch "3\.13") {
        Write-Info "Python 3.13.x not found. Installing via winget..."
        try {
            winget install Python.Python.3.13 --version 3.13.2 --accept-package-agreements --accept-source-agreements
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        } catch {
            Write-Warn "winget install failed. Please install Python 3.13.2 manually from https://www.python.org/downloads/"
            exit 1
        }
    }
    $pyVer = python --version 2>&1
    Write-Ok "Python: $pyVer"
} else {
    Write-Step "Skipping Python check (SkipPythonInstall)."
}

# ----- 2. Create venv -----
Write-Step "Creating shared_Environment virtual environment..."
if (Test-Path $VenvPath) {
    Write-Warn "shared_Environment already exists. Recreate? (y/n)"
    $r = Read-Host
    if ($r -eq 'y') {
        Remove-Item -Recurse -Force $VenvPath
    } else {
        Write-Info "Using existing shared_Environment."
    }
}

if (-not (Test-Path $VenvPath)) {
    python -m venv $VenvPath
    Write-Ok "Created $VenvPath"
} else {
    Write-Ok "Venv exists at $VenvPath"
}

$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
$PipExe = Join-Path $VenvPath "Scripts\pip.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: Python not found at $PythonExe" -ForegroundColor Red
    exit 1
}

# ----- 3. Upgrade pip -----
Write-Step "Upgrading pip..."
& $PythonExe -m pip install --upgrade pip --quiet
Write-Ok "pip upgraded"

# ----- 4. Install packages -----
if (-not $SkipPackages) {
    Write-Step "Installing packages from shared_Environment_requirements.txt..."
    if (-not (Test-Path $RequirementsFile)) {
        Write-Host "ERROR: Requirements file not found: $RequirementsFile" -ForegroundColor Red
        exit 1
    }
    & $PipExe install -r $RequirementsFile
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Some packages may have failed. Check output above."
    } else {
        Write-Ok "Packages installed"
    }
}

# ----- 5. Register Jupyter kernel -----
Write-Step "Registering Jupyter kernel..."
& $PythonExe -m ipykernel install --user --name=shared_Environment --display-name "shared_Environment"
Write-Ok "Jupyter kernel 'shared_Environment' registered"

# ----- 6. Summary -----
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  shared_Environment Setup Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Python:     $PythonExe" -ForegroundColor White
Write-Host "Activate:   $VenvPath\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Quick start:" -ForegroundColor Cyan
Write-Host "  cd $ProjectRoot" -ForegroundColor Gray
Write-Host "  .\shared_Environment\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host ""

# ----- 7. Optional software reminder -----
Write-Host "Optional software (install if needed):" -ForegroundColor Yellow
Write-Host "  - Ollama (local LLM): https://ollama.ai" -ForegroundColor Gray
Write-Host "  - Docker (MCP server): https://docs.docker.com/get-docker/" -ForegroundColor Gray
Write-Host "  - TA-Lib C library (for ta-lib Python):" -ForegroundColor Gray
Write-Host "    1. Download: https://github.com/ta-lib/ta-lib/releases (ta-lib-0.6.4-windows-x86_64.msi)" -ForegroundColor Gray
Write-Host "    2. Install, then: pip install TA-Lib" -ForegroundColor Gray
Write-Host "    (Note: 'ta' package is already installed as pure-Python alternative)" -ForegroundColor Gray
Write-Host ""

<#
.SYNOPSIS
    Run the Multi-Agent Dev Team locally (Orchestrator API + React UI).

.DESCRIPTION
    Restores packages, builds the solution, runs all tests, then starts:
      - Orchestrator API  on http://localhost:5000  (background process)
      - React UI          on http://localhost:3000  (foreground, Ctrl+C to stop both)

.PARAMETER SkipTests
    Skip running tests before starting the app.

.PARAMETER ApiKey
    Anthropic API key. Falls back to ANTHROPIC_API_KEY environment variable.

.EXAMPLE
    .\deploy-local.ps1
    .\deploy-local.ps1 -SkipTests
    .\deploy-local.ps1 -ApiKey "sk-ant-xxxx"
#>

param(
    [switch]$SkipTests,
    [string]$ApiKey = $env:ANTHROPIC_API_KEY
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root                = Split-Path -Parent $PSScriptRoot
$OrchestratorProject = Join-Path $Root "src\MultiAgentDevTeam.Orchestrator\MultiAgentDevTeam.Orchestrator.csproj"
$UIDir               = Join-Path $Root "src\MultiAgentDevTeam.UI"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Multi-Agent Dev Team - Local Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Validate API key
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    Write-Error "ANTHROPIC_API_KEY is required. Set the environment variable or pass -ApiKey."
    exit 1
}

$env:ANTHROPIC_API_KEY = $ApiKey

# Step 1: Restore
Write-Host "`n[1/5] Restoring NuGet packages..." -ForegroundColor Yellow
dotnet restore $Root
if ($LASTEXITCODE -ne 0) { Write-Error "Restore failed."; exit 1 }

# Step 2: Build
Write-Host "`n[2/5] Building solution..." -ForegroundColor Yellow
dotnet build $Root -c Release --no-restore
if ($LASTEXITCODE -ne 0) { Write-Error "Build failed."; exit 1 }

# Step 3: Test
if (-not $SkipTests) {
    Write-Host "`n[3/5] Running tests with coverage..." -ForegroundColor Yellow
    dotnet test $Root `
        --no-build -c Release `
        --collect:"XPlat Code Coverage" `
        --results-directory "$Root\TestResults" `
        --logger "console;verbosity=minimal"
    if ($LASTEXITCODE -ne 0) { Write-Error "Tests failed."; exit 1 }
    Write-Host "Tests passed." -ForegroundColor Green
} else {
    Write-Host "`n[3/5] Skipping tests (-SkipTests flag set)" -ForegroundColor DarkYellow
}

# Step 4: Start Orchestrator in background
Write-Host "`n[4/5] Starting Orchestrator API on http://localhost:5000 ..." -ForegroundColor Yellow
$orchestratorArgs = "run --project `"$OrchestratorProject`" -c Release --no-build --urls http://localhost:5000"
$orchestrator = Start-Process -FilePath "dotnet" -ArgumentList $orchestratorArgs -PassThru -NoNewWindow

# Wait for Orchestrator health check
$ready = $false
for ($i = 1; $i -le 20; $i++) {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Write-Host "  Waiting for Orchestrator... attempt $i/20" -ForegroundColor DarkGray
}
if (-not $ready) {
    Write-Warning "Orchestrator health check timed out. UI may not be able to reach the API."
} else {
    Write-Host "  Orchestrator is healthy!" -ForegroundColor Green
}

# Step 5: Start React UI (foreground - Ctrl+C stops both)
Write-Host "`n[5/5] Starting React UI on http://localhost:3000 ..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop both services.`n" -ForegroundColor Gray
Write-Host "  API : http://localhost:5000" -ForegroundColor Cyan
Write-Host "  UI  : http://localhost:3000" -ForegroundColor Cyan
Write-Host ""

try {
    Push-Location $UIDir
    npm run dev
} finally {
    Pop-Location
    if ($null -ne $orchestrator -and -not $orchestrator.HasExited) {
        Write-Host "`nStopping Orchestrator (PID $($orchestrator.Id))..." -ForegroundColor Yellow
        Stop-Process -Id $orchestrator.Id -Force -ErrorAction SilentlyContinue
        Write-Host "Orchestrator stopped." -ForegroundColor Green
    }
}

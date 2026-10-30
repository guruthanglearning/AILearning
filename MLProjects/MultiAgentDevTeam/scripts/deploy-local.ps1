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
    Anthropic API key. Optional: if omitted, the key comes from the ANTHROPIC_API_KEY
    environment variable, then src/MultiAgentDevTeam.Orchestrator/appsettings.secrets.json,
    then a masked prompt (see scripts/Resolve-AnthropicApiKey.ps1). Passing it here saves
    it in your shell history, so prefer the other sources.

.EXAMPLE
    .\deploy-local.ps1
    .\deploy-local.ps1 -SkipTests
#>

param(
    [switch]$SkipTests,
    [string]$ApiKey
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "Resolve-AnthropicApiKey.ps1")

$Root                = Split-Path -Parent $PSScriptRoot
$OrchestratorProject = Join-Path $Root "src\MultiAgentDevTeam.Orchestrator\MultiAgentDevTeam.Orchestrator.csproj"
$UIDir               = Join-Path $Root "src\MultiAgentDevTeam.UI"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Multi-Agent Dev Team - Local Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Resolve the API key; the Orchestrator reads it from this process's environment
$null = Resolve-AnthropicApiKey -ApiKey $ApiKey

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
    # node_modules isn't committed, so a fresh clone needs the packages installed first
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing UI packages (npm ci)..." -ForegroundColor Yellow
        npm ci
        if ($LASTEXITCODE -ne 0) { throw "npm ci failed." }
    }
    npm run dev
} finally {
    Pop-Location
    if ($null -ne $orchestrator -and -not $orchestrator.HasExited) {
        Write-Host "`nStopping Orchestrator (PID $($orchestrator.Id))..." -ForegroundColor Yellow
        Stop-Process -Id $orchestrator.Id -Force -ErrorAction SilentlyContinue
        Write-Host "Orchestrator stopped." -ForegroundColor Green
    }
}

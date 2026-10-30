<#
.SYNOPSIS
    Build and run the Multi-Agent Dev Team (API + UI) using Docker Compose.

.PARAMETER ApiKey
    Anthropic API key. Optional: if omitted, the key comes from the ANTHROPIC_API_KEY
    environment variable, then src/MultiAgentDevTeam.Orchestrator/appsettings.secrets.json,
    then a masked prompt (see scripts/Resolve-AnthropicApiKey.ps1). Passing it here saves
    it in your shell history, so prefer the other sources.

.PARAMETER Down
    Stop and remove running containers instead of starting them.

.EXAMPLE
    .\deploy-docker.ps1
    .\deploy-docker.ps1 -Down
#>

param(
    [string]$ApiKey,
    [switch]$Down
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "Resolve-AnthropicApiKey.ps1")

$Root      = Split-Path -Parent $PSScriptRoot
$DockerDir = Join-Path $Root "docker"
$Compose   = Join-Path $DockerDir "docker-compose.yml"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Multi-Agent Dev Team - Docker Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Tear down if requested
if ($Down) {
    Write-Host "`nStopping containers..." -ForegroundColor Yellow
    docker compose -f $Compose down
    Write-Host "Containers stopped." -ForegroundColor Green
    exit 0
}

# Resolve the API key; docker compose reads it from this process's environment
$null = Resolve-AnthropicApiKey -ApiKey $ApiKey

# Step 1: Build Orchestrator image
Write-Host "`n[1/4] Building Orchestrator image..." -ForegroundColor Yellow
docker build -f "$DockerDir\Dockerfile" -t multi-agent-dev-team:latest $Root
if ($LASTEXITCODE -ne 0) { Write-Error "Orchestrator Docker build failed."; exit 1 }
Write-Host "Orchestrator image built." -ForegroundColor Green

# Step 2: Build UI image
Write-Host "`n[2/4] Building UI image..." -ForegroundColor Yellow
docker build -f "$DockerDir\Dockerfile.ui" -t multi-agent-dev-team-ui:latest $Root
if ($LASTEXITCODE -ne 0) { Write-Error "UI Docker build failed."; exit 1 }
Write-Host "UI image built." -ForegroundColor Green

# Step 3: Start containers
Write-Host "`n[3/4] Starting containers..." -ForegroundColor Yellow
docker compose -f $Compose up -d
if ($LASTEXITCODE -ne 0) { Write-Error "Docker Compose up failed."; exit 1 }

# Step 4: Health check
Write-Host "`n[4/4] Waiting for services to be healthy..." -ForegroundColor Yellow
$maxAttempts = 10
for ($i = 1; $i -le $maxAttempts; $i++) {
    Start-Sleep -Seconds 3
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "  Orchestrator is healthy!" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "  Attempt $i/$maxAttempts - waiting for Orchestrator..." -ForegroundColor DarkYellow
    }
    if ($i -eq $maxAttempts) {
        Write-Warning "Health check timed out. Check logs: docker logs orchestrator"
    }
}

Write-Host "`nDeployment complete!" -ForegroundColor Green
Write-Host "  UI          : http://localhost:3000" -ForegroundColor Cyan
Write-Host "  API (Swagger): http://localhost:5000" -ForegroundColor Cyan
Write-Host "  Health      : http://localhost:5000/health" -ForegroundColor Cyan
Write-Host "`nTo stop: .\deploy-docker.ps1 -Down" -ForegroundColor Gray
Write-Host "Logs: docker logs -f orchestrator  |  docker logs -f ui" -ForegroundColor Gray

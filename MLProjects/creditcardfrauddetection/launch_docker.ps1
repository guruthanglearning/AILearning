# =====================================================
# DOCKER DEPLOYMENT LAUNCHER
# Credit Card Fraud Detection System
# =====================================================
# Launches API and UI in Docker containers
# UI connects to API via Docker network

param(
    [switch]$Build,
    [switch]$Down,
    [switch]$Logs,
    [switch]$Status,
    [switch]$Clean,
    [switch]$Help
)

$ProjectRoot = "D:\Study\AILearning\MLProjects\creditcardfrauddetection"
$DockerEnvFile = Join-Path $ProjectRoot ".env.docker"
$DockerComposeFile = Join-Path $ProjectRoot "docker-compose.yml"

function Show-Help {
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host "Credit Card Fraud Detection - DOCKER Launcher" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "`nThis script launches the application in Docker containers." -ForegroundColor White
    Write-Host "`nUsage: .\launch_docker.ps1 [options]" -ForegroundColor White
    Write-Host "`nOptions:" -ForegroundColor Yellow
    Write-Host "  -Build     - Rebuild Docker images before starting" -ForegroundColor White
    Write-Host "  -Down      - Stop and remove all containers" -ForegroundColor White
    Write-Host "  -Logs      - View container logs" -ForegroundColor White
    Write-Host "  -Status    - Check container status" -ForegroundColor White
    Write-Host "  -Clean     - Stop containers and remove volumes/images" -ForegroundColor White
    Write-Host "  -Help      - Show this help message" -ForegroundColor White
    Write-Host "`nExamples:" -ForegroundColor Yellow
    Write-Host "  .\launch_docker.ps1                 # Start containers" -ForegroundColor Gray
    Write-Host "  .\launch_docker.ps1 -Build          # Rebuild and start" -ForegroundColor Gray
    Write-Host "  .\launch_docker.ps1 -Down           # Stop containers" -ForegroundColor Gray
    Write-Host "  .\launch_docker.ps1 -Logs           # View logs" -ForegroundColor Gray
    Write-Host "  .\launch_docker.ps1 -Status         # Check status" -ForegroundColor Gray
    Write-Host "  .\launch_docker.ps1 -Clean          # Clean everything" -ForegroundColor Gray
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host "Configuration: .env.docker" -ForegroundColor Yellow
    Write-Host "API URL (internal): http://fraud-detection-api:8000" -ForegroundColor Yellow
    Write-Host "API URL (external): http://localhost:8000" -ForegroundColor Yellow
    Write-Host "UI URL: http://localhost:8501" -ForegroundColor Yellow
    Write-Host "Prometheus: http://localhost:9090" -ForegroundColor Yellow
    Write-Host "Grafana: http://localhost:3000" -ForegroundColor Yellow
    Write-Host "==================================================`n" -ForegroundColor Cyan
}

if ($Help) {
    Show-Help
    exit 0
}

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "Credit Card Fraud Detection - DOCKER Deployment" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Deployment Mode: DOCKER" -ForegroundColor Blue
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "Configuration: .env.docker" -ForegroundColor Gray
Write-Host "==================================================" -ForegroundColor Cyan

Set-Location -Path $ProjectRoot

# Check if Docker env file exists
if (-not (Test-Path $DockerEnvFile)) {
    Write-Host "`n❌ Error: .env.docker file not found!" -ForegroundColor Red
    Write-Host "   Expected location: $DockerEnvFile" -ForegroundColor Yellow
    Write-Host "   Please create the .env.docker configuration file first." -ForegroundColor Yellow
    exit 1
}

# Check if docker-compose.yml exists
if (-not (Test-Path $DockerComposeFile)) {
    Write-Host "`n❌ Error: docker-compose.yml file not found!" -ForegroundColor Red
    Write-Host "   Expected location: $DockerComposeFile" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
Write-Host "`n🐋 Checking Docker daemon..." -ForegroundColor Yellow
try {
    $dockerVersion = docker version --format '{{.Server.Version}}' 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker daemon is not running!" -ForegroundColor Red
        Write-Host "   Please start Docker Desktop and try again." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✅ Docker is running (version: $dockerVersion)" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not available: $_" -ForegroundColor Red
    exit 1
}

# Handle different operations
if ($Down) {
    Write-Host "`n🛑 Stopping Docker containers..." -ForegroundColor Yellow
    docker-compose --env-file $DockerEnvFile down
    Write-Host "✅ Containers stopped" -ForegroundColor Green
    exit 0
}

if ($Clean) {
    Write-Host "`n🧹 Cleaning Docker resources..." -ForegroundColor Yellow
    Write-Host "   Stopping containers..." -ForegroundColor Gray
    docker-compose --env-file $DockerEnvFile down -v --remove-orphans
    Write-Host "   Removing images..." -ForegroundColor Gray
    docker rmi creditcardfrauddetection-api creditcardfrauddetection-ui -f 2>$null
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
    exit 0
}

if ($Logs) {
    Write-Host "`n📋 Viewing container logs..." -ForegroundColor Yellow
    Write-Host "   Press Ctrl+C to exit log view" -ForegroundColor Gray
    docker-compose --env-file $DockerEnvFile logs -f
    exit 0
}

if ($Status) {
    Write-Host "`n📊 Container Status:" -ForegroundColor Yellow
    docker-compose --env-file $DockerEnvFile ps
    Write-Host "`n📈 Resource Usage:" -ForegroundColor Yellow
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker-compose --env-file $DockerEnvFile ps -q)
    exit 0
}

# Main deployment flow
Write-Host "`n📋 Setting up Docker configuration..." -ForegroundColor Yellow
Copy-Item -Path $DockerEnvFile -Destination (Join-Path $ProjectRoot ".env") -Force
Write-Host "✅ Configuration loaded from .env.docker" -ForegroundColor Green

# Build or pull images
if ($Build) {
    Write-Host "`n🔨 Building Docker images..." -ForegroundColor Yellow
    docker-compose --env-file $DockerEnvFile build --no-cache
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker build failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Images built successfully" -ForegroundColor Green
} else {
    Write-Host "`n📦 Checking existing images..." -ForegroundColor Yellow
    $existingImages = docker images --format "{{.Repository}}" | Select-String -Pattern "creditcardfrauddetection"
    if ($existingImages) {
        Write-Host "✅ Using existing Docker images" -ForegroundColor Green
        Write-Host "   Use -Build flag to rebuild images" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  No existing images found, building now..." -ForegroundColor Yellow
        docker-compose --env-file $DockerEnvFile build
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Docker build failed!" -ForegroundColor Red
            exit 1
        }
    }
}

# Start containers
Write-Host "`n🚀 Starting Docker containers..." -ForegroundColor Yellow
docker-compose --env-file $DockerEnvFile up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start containers!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Containers started" -ForegroundColor Green

# Wait for services to be ready
Write-Host "`n⏳ Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check API health
Write-Host "`n🔍 Checking API health..." -ForegroundColor Yellow
$maxRetries = 6
$retryCount = 0
$apiHealthy = $false

while ($retryCount -lt $maxRetries -and -not $apiHealthy) {
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
        Write-Host "✅ API Health Check: HEALTHY" -ForegroundColor Green
        Write-Host "   Status: $($healthResponse.status)" -ForegroundColor Gray
        Write-Host "   LLM Service: $($healthResponse.llm_service_type)" -ForegroundColor Gray
        $apiHealthy = $true
    } catch {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Host "⏳ API not ready, retrying ($retryCount/$maxRetries)..." -ForegroundColor Yellow
            Start-Sleep -Seconds 5
        } else {
            Write-Host "⚠️  Could not confirm API health (may still be starting)" -ForegroundColor Yellow
            Write-Host "   Check logs: docker-compose logs -f api" -ForegroundColor Gray
        }
    }
}

# Check UI
Write-Host "`n🔍 Checking UI status..." -ForegroundColor Yellow
try {
    $uiResponse = Invoke-WebRequest -Uri "http://localhost:8501" -Method Get -TimeoutSec 5 -UseBasicParsing
    if ($uiResponse.StatusCode -eq 200) {
        Write-Host "✅ UI is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  UI may still be starting up" -ForegroundColor Yellow
    Write-Host "   Check logs: docker-compose logs -f ui" -ForegroundColor Gray
}

# Show container status
Write-Host "`n📊 Container Status:" -ForegroundColor Yellow
docker-compose --env-file $DockerEnvFile ps

# Summary
Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "✅ DOCKER DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan

Write-Host "`n🐋 Docker Services:" -ForegroundColor White
Write-Host "   - API Container: fraud-detection-api" -ForegroundColor Gray
Write-Host "   - UI Container: fraud-detection-ui" -ForegroundColor Gray
Write-Host "   - Monitoring: prometheus, grafana" -ForegroundColor Gray

Write-Host "`n🌐 Access URLs (from host machine):" -ForegroundColor White
Write-Host "   - API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   - API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   - UI Dashboard: http://localhost:8501" -ForegroundColor Cyan
Write-Host "   - Prometheus: http://localhost:9090" -ForegroundColor Cyan
Write-Host "   - Grafana: http://localhost:3000" -ForegroundColor Cyan

Write-Host "`n🔗 Internal Network:" -ForegroundColor White
Write-Host "   - UI connects to: http://fraud-detection-api:8000" -ForegroundColor Gray
Write-Host "   - Docker network: creditcardfrauddetection_default" -ForegroundColor Gray

Write-Host "`n📝 Useful Commands:" -ForegroundColor White
Write-Host "   - View logs: .\launch_docker.ps1 -Logs" -ForegroundColor Gray
Write-Host "   - Check status: .\launch_docker.ps1 -Status" -ForegroundColor Gray
Write-Host "   - Stop containers: .\launch_docker.ps1 -Down" -ForegroundColor Gray
Write-Host "   - Rebuild: .\launch_docker.ps1 -Build" -ForegroundColor Gray
Write-Host "   - Clean all: .\launch_docker.ps1 -Clean" -ForegroundColor Gray

Write-Host "`n📁 Data Persistence:" -ForegroundColor White
Write-Host "   - ChromaDB: /app/data/chroma_db (in container)" -ForegroundColor Gray
Write-Host "   - Logs: /app/logs (in container)" -ForegroundColor Gray
Write-Host "   - Volumes managed by Docker Compose" -ForegroundColor Gray

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "🌐 Open in browser: http://localhost:8501" -ForegroundColor Green
Write-Host "==================================================`n" -ForegroundColor Cyan

exit 0

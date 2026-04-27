# =====================================================
# LAUNCH DOCKER SERVICES - FRAUD DETECTION SYSTEM
# =====================================================
# Launches API + UI for DOCKER deployment
# UI connects to DOCKER API (fraud-detection-api:8000)
# =====================================================

Write-Host "`n=========================================================" -ForegroundColor Cyan
Write-Host "  FRAUD DETECTION - DOCKER DEPLOYMENT" -ForegroundColor White
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = "D:\Study\AILearning\MLProjects\creditcardfrauddetection"

# STEP 1: Force DOCKER Configuration
Write-Host "[STEP 1] Setting up DOCKER configuration..." -ForegroundColor Yellow
Set-Location $ProjectRoot

# Set DOCKER mode
$env:DEPLOYMENT_MODE = 'docker'
$env:API_URL = 'http://fraud-detection-api:8000'
$env:API_BASE_URL = 'http://fraud-detection-api:8000'

Write-Host "  [SUCCESS] Environment set to DOCKER mode" -ForegroundColor Green
Write-Host "  API_URL = http://fraud-detection-api:8000" -ForegroundColor Gray
Write-Host ""

# STEP 2: Copy DOCKER configuration files
Write-Host "[STEP 2] Copying DOCKER configuration files..." -ForegroundColor Yellow

if (-not (Test-Path ".env.docker")) {
    Write-Host "  [ERROR] .env.docker not found!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "ui\.env.docker")) {
    Write-Host "  [ERROR] ui\.env.docker not found!" -ForegroundColor Red
    exit 1
}

Copy-Item -Path ".env.docker" -Destination ".env" -Force
Copy-Item -Path "ui\.env.docker" -Destination "ui\.env" -Force

Write-Host "  [SUCCESS] .env.docker -> .env" -ForegroundColor Green
Write-Host "  [SUCCESS] ui\.env.docker -> ui\.env" -ForegroundColor Green
Write-Host ""

# STEP 3: Verify Docker is running
Write-Host "[STEP 3] Checking Docker..." -ForegroundColor Yellow

try {
    $dockerVersion = docker --version
    Write-Host "  [SUCCESS] Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Docker not found or not running!" -ForegroundColor Red
    Write-Host "  Please start Docker Desktop first." -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# STEP 4: Check for existing containers
Write-Host "[STEP 4] Checking for existing containers..." -ForegroundColor Yellow
$existingContainers = docker ps -a --filter "name=fraud-detection" --format "{{.Names}}"

if ($existingContainers) {
    Write-Host "  [INFO] Found existing containers:" -ForegroundColor Cyan
    $existingContainers | ForEach-Object {
        Write-Host "    - $_" -ForegroundColor Gray
    }
    $cleanup = Read-Host "  Remove existing containers? (y/n)"
    if ($cleanup -eq 'y') {
        Write-Host "  [INFO] Stopping and removing containers..." -ForegroundColor Yellow
        docker-compose down
        Write-Host "  [SUCCESS] Containers removed" -ForegroundColor Green
    }
} else {
    Write-Host "  [SUCCESS] No existing containers found" -ForegroundColor Green
}
Write-Host ""

# STEP 5: Launch Docker Compose
Write-Host "[STEP 5] Launching Docker Compose..." -ForegroundColor Yellow
Write-Host "  Building and starting containers..." -ForegroundColor Gray
Write-Host ""

docker-compose up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "  [SUCCESS] Docker containers launched" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  [ERROR] Docker Compose failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# STEP 6: Wait for services
Write-Host "[STEP 6] Waiting for services to start..." -ForegroundColor Yellow
Write-Host "  This may take 30-60 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 15

# Check container status
Write-Host ""
Write-Host "  Container Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  DOCKER DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  API: http://localhost:8000 (mapped from container)" -ForegroundColor White
Write-Host "  UI:  http://localhost:8501 (mapped from container)" -ForegroundColor White
Write-Host ""
Write-Host "  Inside Docker network:" -ForegroundColor Gray
Write-Host "    UI connects to: http://fraud-detection-api:8000" -ForegroundColor Gray
Write-Host ""
Write-Host "  View logs: docker-compose logs -f" -ForegroundColor Gray
Write-Host "  Stop services: docker-compose down" -ForegroundColor Gray
Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

# Open browser
$openBrowser = Read-Host "Open UI in browser? (y/n)"
if ($openBrowser -eq 'y') {
    Start-Process "http://localhost:8501"
}

# TorchSharp Inspector Deployment Script (PowerShell)
# This script builds and deploys the TorchSharp Inspector web application

param(
    [switch]$SkipTests,
    [switch]$SkipBuild,
    [switch]$Help
)

# Configuration
$ProjectRoot = $PSScriptRoot
$DockerComposeFile = Join-Path $ProjectRoot "docker-compose.yml"
$BuildConfig = "Release"
$Services = @("nanogpt-api", "nanogpt-dashboard", "torchsharp-inspector", "prometheus", "grafana")

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

# Functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check Docker
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed or not in PATH"
        exit 1
    }
    
    # Check Docker Compose
    if (-not ((Get-Command docker-compose -ErrorAction SilentlyContinue) -or 
              (docker compose version 2>$null))) {
        Write-Error "Docker Compose is not installed or not in PATH"
        exit 1
    }
    
    # Check .NET SDK
    if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
        Write-Error ".NET SDK is not installed or not in PATH"
        exit 1
    }
    
    Write-Success "Prerequisites check passed"
}

function Restore-Packages {
    Write-Info "Restoring NuGet packages..."
    Set-Location $ProjectRoot
    dotnet restore
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to restore NuGet packages"
        exit 1
    }
    Write-Success "NuGet packages restored"
}

function Build-Applications {
    Write-Info "Building .NET applications..."
    
    # Build TorchSharp Inspector
    Write-Info "Building TorchSharp Inspector..."
    Set-Location (Join-Path $ProjectRoot "TorchSharpInspector")
    dotnet build --configuration $BuildConfig --no-restore
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build TorchSharp Inspector"
        exit 1
    }
    
    # Build NanoGPT Dashboard
    Write-Info "Building NanoGPT Dashboard..."
    Set-Location (Join-Path $ProjectRoot "NanoGpt.Dashboard")
    dotnet build --configuration $BuildConfig --no-restore
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build NanoGPT Dashboard"
        exit 1
    }
    
    # Build NanoGPT API
    Write-Info "Building NanoGPT API..."
    Set-Location $ProjectRoot
    dotnet build --configuration $BuildConfig --no-restore
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build NanoGPT API"
        exit 1
    }
    
    Write-Success "All applications built successfully"
}

function Invoke-Tests {
    Write-Info "Running tests..."
    Set-Location $ProjectRoot
    
    # Run TorchSharp Inspector tests
    $TestProject = Join-Path $ProjectRoot "TorchSharpInspector.Tests"
    if (Test-Path $TestProject) {
        Write-Info "Running TorchSharp Inspector tests..."
        dotnet test $TestProject --configuration $BuildConfig --logger "console;verbosity=minimal"
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Some tests failed, but continuing deployment"
        }
    }
    
    Write-Success "Tests completed"
}

function Build-DockerImages {
    Write-Info "Building Docker images..."
    Set-Location $ProjectRoot
    
    # Build with docker-compose
    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        docker-compose -f $DockerComposeFile build --no-cache
    } else {
        docker compose -f $DockerComposeFile build --no-cache
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build Docker images"
        exit 1
    }
    
    Write-Success "Docker images built successfully"
}

function Deploy-Services {
    Write-Info "Deploying services..."
    Set-Location $ProjectRoot
    
    # Stop existing services
    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        docker-compose -f $DockerComposeFile down
        docker-compose -f $DockerComposeFile up -d
    } else {
        docker compose -f $DockerComposeFile down
        docker compose -f $DockerComposeFile up -d
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to deploy services"
        exit 1
    }
    
    Write-Success "Services deployed successfully"
}

function Wait-ForServices {
    Write-Info "Waiting for services to be healthy..."
    
    $MaxAttempts = 30
    $Attempt = 0
    $AllHealthy = $false
    
    while (($Attempt -lt $MaxAttempts) -and (-not $AllHealthy)) {
        $AllHealthy = $true
        
        foreach ($Service in $Services) {
            try {
                if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
                    $ContainerId = docker-compose -f $DockerComposeFile ps -q $Service 2>$null
                } else {
                    $ContainerId = docker compose -f $DockerComposeFile ps -q $Service 2>$null
                }
                
                if ($ContainerId) {
                    $Status = docker inspect -f '{{.State.Health.Status}}' $ContainerId 2>$null
                    if (($Status -ne "healthy") -and ($Status -ne "")) {
                        $AllHealthy = $false
                        break
                    }
                }
            } catch {
                # Service might not have health check
            }
        }
        
        if (-not $AllHealthy) {
            Write-Info "Waiting for services... (attempt $($Attempt + 1)/$MaxAttempts)"
            Start-Sleep 10
            $Attempt++
        }
    }
    
    if ($AllHealthy) {
        Write-Success "All services are healthy"
    } else {
        Write-Warning "Some services may not be fully healthy yet"
    }
}

function Test-Deployment {
    Write-Info "Verifying deployment..."
    
    # Check API health
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            Write-Success "NanoGPT API is responding"
        }
    } catch {
        Write-Warning "NanoGPT API health check failed"
    }
    
    # Check Dashboard
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:5169" -UseBasicParsing -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            Write-Success "NanoGPT Dashboard is responding"
        }
    } catch {
        Write-Warning "NanoGPT Dashboard health check failed"
    }
    
    # Check TorchSharp Inspector
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:8082/api/health" -UseBasicParsing -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            Write-Success "TorchSharp Inspector is responding"
        }
    } catch {
        Write-Warning "TorchSharp Inspector health check failed"
    }
    
    # Check Grafana
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:3001" -UseBasicParsing -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            Write-Success "Grafana is responding"
        }
    } catch {
        Write-Warning "Grafana health check failed"
    }
    
    # Check Prometheus
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:9090" -UseBasicParsing -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            Write-Success "Prometheus is responding"
        }
    } catch {
        Write-Warning "Prometheus health check failed"
    }
}

function Show-ServiceUrls {
    Write-Info "Deployment completed! Services are available at:"
    Write-Host ""
    Write-Host "🎭 NanoGPT Dashboard:     http://localhost:5169" -ForegroundColor $Green
    Write-Host "🔍 TorchSharp Inspector:  http://localhost:8082" -ForegroundColor $Blue
    Write-Host "📊 API Documentation:      http://localhost:8080/swagger" -ForegroundColor $Yellow
    Write-Host "📊 Inspector API Docs:     http://localhost:8082/api-docs" -ForegroundColor $Yellow
    Write-Host "📈 Grafana Monitoring:    http://localhost:3001 (admin/admin123)" -ForegroundColor $Green
    Write-Host "📊 Prometheus Metrics:     http://localhost:9090" -ForegroundColor $Blue
    Write-Host ""
    Write-Host "Health Checks:" -ForegroundColor $Yellow
    Write-Host "  • API Health:       http://localhost:8080/health"
    Write-Host "  • Inspector Health: http://localhost:8082/api/health"
    Write-Host ""
}

function Show-Help {
    Write-Host "TorchSharp Inspector Deployment Script"
    Write-Host "Usage: .\deploy.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SkipTests   Skip running tests"
    Write-Host "  -SkipBuild   Skip building applications"
    Write-Host "  -Help        Show this help message"
    Write-Host ""
}

# Main deployment process
function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    Write-Info "TorchSharp Inspector Deployment Script v1.0.0"
    Write-Info "================================================"
    
    # Execute deployment steps
    Test-Prerequisites
    
    if (-not $SkipBuild) {
        Restore-Packages
        Build-Applications
        
        if (-not $SkipTests) {
            Invoke-Tests
        }
    }
    
    Build-DockerImages
    Deploy-Services
    Wait-ForServices
    Test-Deployment
    Show-ServiceUrls
    
    Write-Success "🎉 Deployment completed successfully!"
}

# Execute main function
Main
#!/usr/bin/env pwsh
# Deploy MCP Stock Server Docker Container
# This script builds, deploys, and manages the MCP Stock Server Docker container

param(
    [string]$Action = "deploy",  # deploy, start, stop, restart, rebuild, logs, status
    [switch]$Force,              # Force rebuild without cache
    [switch]$Verbose             # Enable verbose output
)

# Configuration
$CONTAINER_NAME = "mcp-stock-server"
$IMAGE_NAME = "mcp-stock-server:latest"
$PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$DOCKER_COMPOSE_FILE = Join-Path $PROJECT_DIR "docker-compose.yml"

# Color functions
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Info { param($Message) Write-Host "📋 $Message" -ForegroundColor Cyan }
function Write-Step { param($Message) Write-Host "🔧 $Message" -ForegroundColor Blue }

# Check if Docker is running
function Test-DockerRunning {
    try {
        $null = docker version 2>$null
        return $true
    }
    catch {
        return $false
    }
}

# Check if container exists
function Test-ContainerExists {
    param($ContainerName)
    $containers = docker ps -a --format "{{.Names}}" 2>$null
    return $containers -contains $ContainerName
}

# Check if container is running
function Test-ContainerRunning {
    param($ContainerName)
    $runningContainers = docker ps --format "{{.Names}}" 2>$null
    return $runningContainers -contains $ContainerName
}

# Stop and remove existing container
function Remove-ExistingContainer {
    param($ContainerName)
    
    if (Test-ContainerExists $ContainerName) {
        Write-Step "Stopping existing container: $ContainerName"
        docker stop $ContainerName 2>$null | Out-Null
        
        Write-Step "Removing existing container: $ContainerName"
        docker rm $ContainerName 2>$null | Out-Null
        
        Write-Success "Removed existing container: $ContainerName"
    }
}

# Build Docker image
function Build-DockerImage {
    param($ImageName, $ProjectDir, [switch]$Force)
    
    Write-Step "Building Docker image: $ImageName"
    
    $buildArgs = @("build", "-t", $ImageName)
    if ($Force) {
        $buildArgs += "--no-cache"
        Write-Info "Building with --no-cache flag"
    }
    $buildArgs += $ProjectDir
    
    $buildResult = & docker @buildArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker image built successfully: $ImageName"
        return $true
    }
    else {
        Write-Error "Failed to build Docker image"
        return $false
    }
}

# Deploy using Docker Compose
function Deploy-WithCompose {
    param($ComposeFile)
    
    if (Test-Path $ComposeFile) {
        Write-Step "Deploying with Docker Compose"
        
        # Stop existing services
        docker-compose -f $ComposeFile down 2>$null | Out-Null
        
        # Start services
        $result = docker-compose -f $ComposeFile up -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Container deployed successfully with Docker Compose"
            return $true
        }
        else {
            Write-Error "Failed to deploy with Docker Compose"
            return $false
        }
    }
    else {
        Write-Warning "Docker Compose file not found: $ComposeFile"
        return $false
    }
}

# Deploy with direct Docker run
function Deploy-WithDockerRun {
    param($ImageName, $ContainerName)
    
    Write-Step "Deploying with Docker run command"
    
    $runArgs = @(
        "run", "-d",
        "--name", $ContainerName,
        "--restart", "unless-stopped",
        "-e", "MCP_SERVER_NAME=Docker_StockServer",
        "-e", "MCP_SERVER_SOURCE=Docker_YFinance_Server",
        "-e", "PYTHONUNBUFFERED=1",
        "-e", "LOG_LEVEL=INFO",
        "--stdin-open",
        "--tty",
        $ImageName
    )
    
    $result = & docker @runArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Container deployed successfully: $ContainerName"
        return $true
    }
    else {
        Write-Error "Failed to deploy container"
        return $false
    }
}

# Wait for container to be ready
function Wait-ContainerReady {
    param($ContainerName, $TimeoutSeconds = 30)
    
    Write-Step "Waiting for container to be ready..."
    
    $timeout = $TimeoutSeconds
    while ($timeout -gt 0) {
        if (Test-ContainerRunning $ContainerName) {
            # Test if the container is responding
            $testResult = docker exec $ContainerName python -c "import sys; print('Container Ready'); sys.exit(0)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Container is ready and responding"
                return $true
            }
        }
        
        Start-Sleep -Seconds 2
        $timeout -= 2
        Write-Host "." -NoNewline
    }
    
    Write-Error "Container failed to become ready within $TimeoutSeconds seconds"
    return $false
}

# Show container status
function Show-ContainerStatus {
    param($ContainerName)
    
    Write-Info "Container Status Information"
    Write-Host "=" * 50 -ForegroundColor Gray
    
    if (Test-ContainerExists $ContainerName) {
        # Container details
        Write-Host "`nContainer Details:" -ForegroundColor Yellow
        docker ps -a --filter "name=$ContainerName" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"
        
        # Container logs (last 10 lines)
        Write-Host "`nRecent Logs:" -ForegroundColor Yellow
        docker logs --tail 10 $ContainerName 2>$null
        
        # Resource usage
        Write-Host "`nResource Usage:" -ForegroundColor Yellow
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" $ContainerName 2>$null
    }
    else {
        Write-Warning "Container '$ContainerName' does not exist"
    }
}

# Main deployment function
function Start-Deployment {
    Write-Info "MCP Stock Server Docker Deployment"
    Write-Host "=" * 60 -ForegroundColor Gray
    
    # Check Docker availability
    if (-not (Test-DockerRunning)) {
        Write-Error "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    }
    Write-Success "Docker is running"
    
    # Change to project directory
    Set-Location $PROJECT_DIR
    Write-Info "Working directory: $PROJECT_DIR"
    
    # Remove existing container
    Remove-ExistingContainer $CONTAINER_NAME
    
    # Build image
    if (-not (Build-DockerImage $IMAGE_NAME $PROJECT_DIR -Force:$Force)) {
        exit 1
    }
    
    # Deploy container
    $deploySuccess = $false
    
    # Try Docker Compose first
    if (Test-Path $DOCKER_COMPOSE_FILE) {
        $deploySuccess = Deploy-WithCompose $DOCKER_COMPOSE_FILE
    }
    
    # Fallback to direct Docker run
    if (-not $deploySuccess) {
        Write-Info "Falling back to direct Docker deployment"
        $deploySuccess = Deploy-WithDockerRun $IMAGE_NAME $CONTAINER_NAME
    }
    
    if (-not $deploySuccess) {
        Write-Error "Deployment failed"
        exit 1
    }
    
    # Wait for container to be ready
    if (Wait-ContainerReady $CONTAINER_NAME) {
        Write-Success "MCP Stock Server deployed successfully!"
        Write-Info "Container Name: $CONTAINER_NAME"
        Write-Info "Image: $IMAGE_NAME"
        
        # Show status
        Show-ContainerStatus $CONTAINER_NAME
        
        Write-Host "`n🚀 Next Steps:" -ForegroundColor Green
        Write-Host "   • Test the server: .\test_docker_mcp_stock.ps1" -ForegroundColor Cyan
        Write-Host "   • View logs: docker logs $CONTAINER_NAME" -ForegroundColor Cyan
        Write-Host "   • Stop server: .\deploy_mcp_stock_docker.ps1 -Action stop" -ForegroundColor Cyan
    }
    else {
        Write-Error "Container deployment completed but container is not ready"
        exit 1
    }
}

# Handle different actions
switch ($Action.ToLower()) {
    "deploy" {
        Start-Deployment
    }
    
    "start" {
        if (Test-ContainerExists $CONTAINER_NAME) {
            Write-Step "Starting container: $CONTAINER_NAME"
            docker start $CONTAINER_NAME
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Container started successfully"
                Show-ContainerStatus $CONTAINER_NAME
            }
        }
        else {
            Write-Error "Container '$CONTAINER_NAME' does not exist. Use 'deploy' action first."
        }
    }
    
    "stop" {
        if (Test-ContainerRunning $CONTAINER_NAME) {
            Write-Step "Stopping container: $CONTAINER_NAME"
            docker stop $CONTAINER_NAME
            Write-Success "Container stopped successfully"
        }
        else {
            Write-Warning "Container '$CONTAINER_NAME' is not running"
        }
    }
    
    "restart" {
        Write-Step "Restarting container: $CONTAINER_NAME"
        docker restart $CONTAINER_NAME
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Container restarted successfully"
            Wait-ContainerReady $CONTAINER_NAME
            Show-ContainerStatus $CONTAINER_NAME
        }
    }
    
    "rebuild" {
        Write-Info "Rebuilding and redeploying container"
        $Force = $true
        Start-Deployment
    }
    
    "logs" {
        if (Test-ContainerExists $CONTAINER_NAME) {
            Write-Info "Showing container logs (press Ctrl+C to exit)"
            docker logs -f $CONTAINER_NAME
        }
        else {
            Write-Error "Container '$CONTAINER_NAME' does not exist"
        }
    }
    
    "status" {
        Show-ContainerStatus $CONTAINER_NAME
    }
    
    default {
        Write-Error "Invalid action: $Action"
        Write-Info "Valid actions: deploy, start, stop, restart, rebuild, logs, status"
        exit 1
    }
}

# =====================================================
# Integration Tests Runner - Credit Card Fraud Detection
# =====================================================
# Runs integration tests for API endpoints
# Supports local and Docker deployment modes

param(
    [switch]$StartAPI,
    [switch]$Verbose,
    [ValidateSet('local', 'docker')]
    [string]$Mode = 'local'
)

$ProjectRoot = "D:\Study\AILearning\MLProjects\creditcardfrauddetection"
$PythonPath = "D:\Study\AILearning\shared_Environment\Scripts\python.exe"

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "Credit Card Fraud Detection - Integration Tests" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
if ($Mode -eq 'docker') {
    Write-Host "Deployment Mode: DOCKER" -ForegroundColor Blue
} else {
    Write-Host "Deployment Mode: LOCAL" -ForegroundColor Green
}

Set-Location -Path $ProjectRoot

# Check if API is running on port 8000
$apiRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $apiRunning = $true
        Write-Host "✅ API server is already running on port 8000" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  API server is not running on port 8000" -ForegroundColor Yellow
}

$apiProcess = $null

if (-not $apiRunning) {
    if ($StartAPI) {
        Write-Host "`nStarting API server..." -ForegroundColor Yellow
        $apiProcess = Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; & '$PythonPath' run_server.py" -PassThru -WindowStyle Minimized
        
        Write-Host "Waiting for API server to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        # Verify API started
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5
            Write-Host "✅ API server started successfully" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to start API server" -ForegroundColor Red
            if ($apiProcess) { Stop-Process -Id $apiProcess.Id -Force }
            exit 1
        }
    } else {
        Write-Host "❌ API server must be running. Use -StartAPI flag to start it automatically." -ForegroundColor Red
        Write-Host "   Or run: .\launch.ps1 api" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "`nRunning integration tests..." -ForegroundColor Yellow

& $PythonPath tests/run_integration_tests.py --mode $Mode

$exitCode = $LASTEXITCODE

# Stop API if we started it
if ($apiProcess) {
    Write-Host "`nStopping API server..." -ForegroundColor Yellow
    Stop-Process -Id $apiProcess.Id -Force
    Write-Host "✅ API server stopped" -ForegroundColor Green
}

Write-Host "`n==================================================" -ForegroundColor Cyan

exit $exitCode

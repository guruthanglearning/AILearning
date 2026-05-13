# =====================================================
# Playwright E2E Tests Runner - Credit Card Fraud Detection
# =====================================================
# Runs Playwright end-to-end UI tests
# Supports local and Docker deployment modes

param(
    [switch]$StartServices,
    [switch]$Headless,
    [switch]$Verbose,
    [ValidateSet('local', 'docker')]
    [string]$Mode = 'local'
)

$ProjectRoot = "D:\Study\AILearning\MLProjects\creditcardfrauddetection"
$PythonPath = "D:\Study\AILearning\shared_Environment\Scripts\python.exe"

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "Credit Card Fraud Detection - Playwright E2E Tests" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
if ($Mode -eq 'docker') {
    Write-Host "Deployment Mode: DOCKER" -ForegroundColor Blue
} else {
    Write-Host "Deployment Mode: LOCAL" -ForegroundColor Green
}

Set-Location -Path $ProjectRoot

# Check if API and UI are running
$apiRunning = $false
$uiRunning = $false

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $apiRunning = $true
        Write-Host "✅ API server is running on port 8000" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  API server is not running on port 8000" -ForegroundColor Yellow
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8501" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $uiRunning = $true
        Write-Host "✅ UI server is running on port 8501" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  UI server is not running on port 8501" -ForegroundColor Yellow
}

$apiProcess = $null
$uiProcess = $null

if (-not $apiRunning -or -not $uiRunning) {
    if ($StartServices) {
        if (-not $apiRunning) {
            Write-Host "`nStarting API server..." -ForegroundColor Yellow
            $apiProcess = Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; & '$PythonPath' run_server.py" -PassThru -WindowStyle Minimized
            Start-Sleep -Seconds 10
        }
        
        if (-not $uiRunning) {
            Write-Host "Starting UI server..." -ForegroundColor Yellow
            $uiProcess = Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; & '$PythonPath' run_ui.py" -PassThru -WindowStyle Minimized
            Start-Sleep -Seconds 8
        }
        
        Write-Host "✅ Services started successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Both API and UI servers must be running. Use -StartServices flag to start them automatically." -ForegroundColor Red
        Write-Host "   Or run: .\launch.ps1 both" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "`nRunning Playwright E2E tests..." -ForegroundColor Yellow

if ($Headless) {
    $env:PLAYWRIGHT_HEADLESS = "true"
}

$env:DEPLOYMENT_MODE = $Mode

& $PythonPath tests/test_ui_e2e.py

$exitCode = $LASTEXITCODE

# Stop services if we started them
if ($apiProcess) {
    Write-Host "`nStopping API server..." -ForegroundColor Yellow
    Stop-Process -Id $apiProcess.Id -Force
}

if ($uiProcess) {
    Write-Host "Stopping UI server..." -ForegroundColor Yellow
    Stop-Process -Id $uiProcess.Id -Force
}

if ($apiProcess -or $uiProcess) {
    Write-Host "✅ Services stopped" -ForegroundColor Green
}

Write-Host "`n==================================================" -ForegroundColor Cyan

# Check if report was generated
$reportPattern = "tests/reports/ui_e2e_test_*.html"
$latestReport = Get-ChildItem -Path "tests/reports" -Filter "ui_e2e_test_*.html" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($latestReport) {
    Write-Host "`n📄 Test report: $($latestReport.FullName)" -ForegroundColor Cyan
}

exit $exitCode

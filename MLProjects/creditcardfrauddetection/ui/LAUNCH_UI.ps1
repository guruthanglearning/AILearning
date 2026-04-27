# Quick UI Launcher - Verify API Endpoint Configuration
# This script launches the UI and shows which API endpoint it's using

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   FRAUD DETECTION UI - LAUNCH & VERIFY                    ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$UIDir = "D:\Study\AILearning\MLProjects\creditcardfrauddetection\ui"
$StreamlitExe = "D:\Study\AILearning\shared_Environment\Scripts\streamlit.exe"
$EnvFile = Join-Path $UIDir ".env.local"

# Display configuration
Write-Host "Configuration Check:" -ForegroundColor Yellow
Write-Host "  UI Directory: $UIDir" -ForegroundColor Gray
Write-Host ""

if (Test-Path $EnvFile) {
    Write-Host "  ✓ Found .env.local" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Current API Configuration:" -ForegroundColor White
    Get-Content $EnvFile | Select-String -Pattern "API_URL|API_BASE_URL" | ForEach-Object {
        $line = $_.Line
        if ($line -match "localhost") {
            Write-Host "    $line" -ForegroundColor Green
        } elseif ($line -match "fraud-detection-api") {
            Write-Host "    $line" -ForegroundColor Red
            Write-Host "    ⚠️  WARNING: Using Docker service name!" -ForegroundColor Red
        } else {
            Write-Host "    $line" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  ✗ .env.local NOT FOUND!" -ForegroundColor Red
    Write-Host "    Using default: http://localhost:8000" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""

# Check if API is running
Write-Host "Checking API Server..." -NoNewline
try {
    $apiHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host " ✅ ONLINE" -ForegroundColor Green
    Write-Host "  Status: $($apiHealth.status)" -ForegroundColor Gray
    Write-Host "  Environment: $($apiHealth.environment)" -ForegroundColor Gray
} catch {
    Write-Host " ❌ OFFLINE" -ForegroundColor Red
    Write-Host ""
    Write-Host "  ⚠️  API is not running!" -ForegroundColor Yellow
    Write-Host "  Start API first with: .\START_ALL_SERVICES.ps1" -ForegroundColor Gray
    Write-Host ""
    $continue = Read-Host "Continue launching UI anyway? (y/n)"
    if ($continue -ne 'y') {
        Write-Host "  Cancelled." -ForegroundColor Gray
        exit 0
    }
}

Write-Host ""

# Check if UI is already running
$uiRunning = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
if ($uiRunning) {
    Write-Host "  ⚠️  UI already running on port 8501" -ForegroundColor Yellow
    Write-Host ""
    $restart = Read-Host "  Restart UI? (y/n)"
    if ($restart -eq 'y') {
        Write-Host ""
        Write-Host "  Stopping existing UI..." -NoNewline
        Get-Process | Where-Object {$_.ProcessName -like "*streamlit*" -or $_.ProcessName -like "*python*"} | ForEach-Object {
            try {
                $connections = Get-NetTCPConnection -OwningProcess $_.Id -ErrorAction SilentlyContinue | Where-Object {$_.LocalPort -eq 8501}
                if ($connections) {
                    Stop-Process -Id $_.Id -Force
                }
            } catch {}
        }
        Start-Sleep -Seconds 2
        Write-Host " Done" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "  Opening existing UI in browser..." -ForegroundColor Cyan
        Start-Process "http://localhost:8501"
        Write-Host "  ✓ Browser launched" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Check the sidebar for API URL (should show localhost:8000)" -ForegroundColor Yellow
        Write-Host ""
        exit 0
    }
}

# Launch UI
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   LAUNCHING UI DASHBOARD                                  ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  URL: http://localhost:8501" -ForegroundColor Yellow
Write-Host "  API: http://localhost:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Starting Streamlit..." -ForegroundColor White
Write-Host ""

Set-Location $UIDir

# Start Streamlit and capture output to see config loading
& $StreamlitExe run app.py --server.port 8501

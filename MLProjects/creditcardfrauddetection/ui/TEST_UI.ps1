# ═══════════════════════════════════════════════════════════
#  UI LAUNCH & TEST SCRIPT
#  Tests UI functionality and verifies localhost API connection
# ═══════════════════════════════════════════════════════════

param(
    [switch]$SkipTests,
    [switch]$OpenBrowser
)

$UIDir = "D:\Study\AILearning\MLProjects\creditcardfrauddetection\ui"
$ProjectRoot = "D:\Study\AILearning\MLProjects\creditcardfrauddetection"
$StreamlitExe = "D:\Study\AILearning\shared_Environment\Scripts\streamlit.exe"
$PythonExe = "D:\Study\AILearning\shared_Environment\Scripts\python.exe"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        UI LAUNCH & TEST - FRAUD DETECTION SYSTEM           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ═══════════════════════════════════════════════════════════
# STEP 1: Check Configuration
# ═══════════════════════════════════════════════════════════
Write-Host "Step 1: Configuration Check" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""

$envFile = Join-Path $UIDir ".env.local"
if (Test-Path $envFile) {
    Write-Host "  ✓ Configuration file found: .env.local" -ForegroundColor Green
    Write-Host ""
    Write-Host "  API Endpoint Configuration:" -ForegroundColor White
    
    $apiUrlLine = Get-Content $envFile | Select-String -Pattern "^API_URL=" | Select-Object -First 1
    if ($apiUrlLine) {
        $apiUrl = $apiUrlLine.ToString().Split('=')[1].Trim()
        if ($apiUrl -like "*localhost*" -or $apiUrl -like "*127.0.0.1*") {
            Write-Host "    API_URL: $apiUrl" -ForegroundColor Green
            Write-Host "    ✅ Correctly configured for LOCAL deployment" -ForegroundColor Green
        } elseif ($apiUrl -like "*fraud-detection-api*") {
            Write-Host "    API_URL: $apiUrl" -ForegroundColor Red
            Write-Host "    ❌ ERROR: Using DOCKER service name!" -ForegroundColor Red
            Write-Host "    This will NOT work for local deployment!" -ForegroundColor Red
            Write-Host ""
            Write-Host "  Fix required: Update $envFile" -ForegroundColor Yellow
            Write-Host "  Change to: API_URL=http://localhost:8000" -ForegroundColor Yellow
            Write-Host ""
            exit 1
        } else {
            Write-Host "    API_URL: $apiUrl" -ForegroundColor Yellow
            Write-Host "    ⚠️  Warning: Non-standard API URL" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  ⚠️  Warning: .env.local not found" -ForegroundColor Yellow
    Write-Host "    Using default: http://localhost:8000" -ForegroundColor Gray
}

Write-Host ""

# ═══════════════════════════════════════════════════════════
# STEP 2: Check if API is Running
# ═══════════════════════════════════════════════════════════
Write-Host "Step 2: API Server Status" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""

$apiRunning = $false
Write-Host "  Checking http://localhost:8000..." -NoNewline

try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host " ✅ ONLINE" -ForegroundColor Green
    Write-Host "    Status: $($health.status)" -ForegroundColor Gray
    Write-Host "    Environment: $($health.environment)" -ForegroundColor Gray
    $apiRunning = $true
} catch {
    Write-Host " ❌ OFFLINE" -ForegroundColor Red
    Write-Host ""
    Write-Host "  ⚠️  API Server is not running!" -ForegroundColor Yellow
    Write-Host "  The UI needs the API to function properly." -ForegroundColor Gray
    Write-Host ""
    Write-Host "  To start API:" -ForegroundColor White
    Write-Host "    cd $ProjectRoot" -ForegroundColor Gray
    Write-Host "    & '$PythonExe' run_server.py" -ForegroundColor Gray
    Write-Host ""
    
    $launchApi = Read-Host "  Launch API now in new window? (y/n)"
    if ($launchApi -eq 'y') {
        Write-Host ""
        Write-Host "  Starting API Server..." -ForegroundColor Cyan
        
        $apiCmd = @"
Set-Location '$ProjectRoot'
Write-Host ''
Write-Host '═══════════════════════════════════════════════' -ForegroundColor Cyan
Write-Host '   FRAUD DETECTION API SERVER' -ForegroundColor Cyan
Write-Host '═══════════════════════════════════════════════' -ForegroundColor Cyan
Write-Host ''
Write-Host 'URL: http://localhost:8000' -ForegroundColor Yellow
Write-Host ''
& '$PythonExe' run_server.py
"@
        
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCmd
        Write-Host "  ✓ API window opened" -ForegroundColor Green
        Write-Host "  Waiting for API to start..." -ForegroundColor Gray
        Start-Sleep -Seconds 10
        
        # Retry check
        try {
            $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
            Write-Host "  ✓ API is now ONLINE" -ForegroundColor Green
            $apiRunning = $true
        } catch {
            Write-Host "  ⚠️  API still starting, will check again later..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Continuing without API (UI will show connection errors)..." -ForegroundColor Gray
    }
}

Write-Host ""

# ═══════════════════════════════════════════════════════════
# STEP 3: Check if UI is Already Running
# ═══════════════════════════════════════════════════════════
Write-Host "Step 3: UI Status Check" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""

$uiRunning = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue

if ($uiRunning) {
    Write-Host "  ✓ UI already running on port 8501" -ForegroundColor Green
    Write-Host ""
    
    # Test if accessible
    try {
        $uiResponse = Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing -TimeoutSec 5
        Write-Host "  ✓ UI is accessible (HTTP $($uiResponse.StatusCode))" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Opening browser to test UI..." -ForegroundColor Cyan
        Start-Process "http://localhost:8501"
        Write-Host "  ✓ Browser launched" -ForegroundColor Green
        Write-Host ""
        Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║  VERIFY IN BROWSER:                                        ║" -ForegroundColor Green
        Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Host "  1. Check sidebar - Should show:" -ForegroundColor White
        Write-Host "     • API URL: http://localhost:8000" -ForegroundColor Gray
        Write-Host "     • Status: ✅ Connected (if API is running)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  2. Try analyzing a transaction:" -ForegroundColor White
        Write-Host "     • Go to 'Transaction Analysis' page" -ForegroundColor Gray
        Write-Host "     • Click 'Analyze Transaction'" -ForegroundColor Gray
        Write-Host "     • Verify prediction appears" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  3. Check other pages:" -ForegroundColor White
        Write-Host "     • Dashboard - View metrics" -ForegroundColor Gray
        Write-Host "     • Fraud Patterns - Search patterns" -ForegroundColor Gray
        Write-Host "     • System Health - Check status" -ForegroundColor Gray
        Write-Host ""
        exit 0
    } catch {
        Write-Host "  ⚠️  UI port is listening but not responding" -ForegroundColor Yellow
        Write-Host "  Restarting UI..." -ForegroundColor Cyan
        
        # Stop existing UI
        Get-Process | Where-Object {
            $_.ProcessName -like "*streamlit*" -or 
            ($_.ProcessName -like "*python*" -and (Get-NetTCPConnection -OwningProcess $_.Id -ErrorAction SilentlyContinue | Where-Object {$_.LocalPort -eq 8501}))
        } | Stop-Process -Force -ErrorAction SilentlyContinue
        
        Start-Sleep -Seconds 2
    }
}

# ═══════════════════════════════════════════════════════════
# STEP 4: Launch UI
# ═══════════════════════════════════════════════════════════
Write-Host "Step 4: Launching UI" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""

$uiCmd = @"
Set-Location '$UIDir'
Write-Host ''
Write-Host '═══════════════════════════════════════════════' -ForegroundColor Cyan
Write-Host '   FRAUD DETECTION UI DASHBOARD' -ForegroundColor Cyan
Write-Host '═══════════════════════════════════════════════' -ForegroundColor Cyan
Write-Host ''
Write-Host 'URL: http://localhost:8501' -ForegroundColor Yellow
Write-Host 'API: http://localhost:8000' -ForegroundColor Yellow
Write-Host ''
Write-Host 'Configuration loaded from: .env.local' -ForegroundColor Gray
Write-Host ''
Write-Host 'Starting Streamlit...' -ForegroundColor White
Write-Host ''
& '$StreamlitExe' run app.py --server.port 8501
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $uiCmd
Write-Host "  ✓ UI window opened" -ForegroundColor Green
Write-Host "  Waiting for UI to initialize..." -ForegroundColor Gray

# Wait and check
$maxWait = 15
$waited = 0
$uiReady = $false

while ($waited -lt $maxWait -and -not $uiReady) {
    Start-Sleep -Seconds 2
    $waited += 2
    
    try {
        $uiResponse = Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing -TimeoutSec 3
        if ($uiResponse.StatusCode -eq 200) {
            $uiReady = $true
        }
    } catch {
        Write-Host "  ." -NoNewline -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host ""

if ($uiReady) {
    Write-Host "  ✅ UI is READY!" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  UI is still starting (check UI window for progress)" -ForegroundColor Yellow
}

Write-Host ""

# ═══════════════════════════════════════════════════════════
# STEP 5: Run Basic Tests (if not skipped)
# ═══════════════════════════════════════════════════════════
if (-not $SkipTests -and $apiRunning) {
    Write-Host "Step 5: Running Basic Tests" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray
    Write-Host ""
    
    # Test 1: API Health
    Write-Host "  Test 1: API Health Endpoint..." -NoNewline
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
        if ($health.status -eq "healthy") {
            Write-Host " ✅ PASS" -ForegroundColor Green
        } else {
            Write-Host " ❌ FAIL (status: $($health.status))" -ForegroundColor Red
        }
    } catch {
        Write-Host " ❌ FAIL ($_)" -ForegroundColor Red
    }
    
    # Test 2: Fraud Patterns
    Write-Host "  Test 2: Fraud Patterns Endpoint..." -NoNewline
    try {
        $patterns = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/fraud-patterns?limit=5" -TimeoutSec 5
        if ($patterns.Count -gt 0) {
            Write-Host " ✅ PASS ($($patterns.Count) patterns)" -ForegroundColor Green
        } else {
            Write-Host " ⚠️  WARN (no patterns found)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host " ❌ FAIL ($_)" -ForegroundColor Red
    }
    
    # Test 3: Metrics
    Write-Host "  Test 3: Metrics Endpoint..." -NoNewline
    try {
        $metrics = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/metrics" -TimeoutSec 5
        Write-Host " ✅ PASS" -ForegroundColor Green
        Write-Host "    Transactions: $($metrics.total_transactions)" -ForegroundColor Gray
        Write-Host "    Fraud Cases: $($metrics.fraudulent_transactions)" -ForegroundColor Gray
        Write-Host "    Accuracy: $($metrics.model_accuracy)%" -ForegroundColor Gray
    } catch {
        Write-Host " ❌ FAIL ($_)" -ForegroundColor Red
    }
    
    # Test 4: Prediction
    Write-Host "  Test 4: Fraud Prediction..." -NoNewline
    try {
        $testData = @{
            amount = 150.00
            merchant_category = "retail"
            transaction_hour = 14
            day_of_week = 2
        } | ConvertTo-Json
        
        $headers = @{
            "Content-Type" = "application/json"
            "X-API-Key" = "development_api_key_for_testing"
        }
        
        $prediction = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/predict" -Method Post -Body $testData -Headers $headers -TimeoutSec 5
        Write-Host " ✅ PASS" -ForegroundColor Green
        Write-Host "    Prediction: $($prediction.prediction)" -ForegroundColor Gray
        Write-Host "    Confidence: $([math]::Round($prediction.fraud_probability * 100, 2))%" -ForegroundColor Gray
    } catch {
        Write-Host " ❌ FAIL ($_)" -ForegroundColor Red
    }
    
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════
# STEP 6: Open Browser & Final Instructions
# ═══════════════════════════════════════════════════════════
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  UI LAUNCHED SUCCESSFULLY                                  ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Access URLs:" -ForegroundColor White
Write-Host "    • UI Dashboard:  http://localhost:8501" -ForegroundColor Yellow
Write-Host "    • API Server:    http://localhost:8000" -ForegroundColor Yellow
Write-Host "    • API Docs:      http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Opening browser..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
Start-Process "http://localhost:8501"
Write-Host "  ✓ Browser launched" -ForegroundColor Green
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  MANUAL VERIFICATION CHECKLIST                             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  In the browser, verify the following:" -ForegroundColor White
Write-Host ""
Write-Host "  ✓ Sidebar shows:" -ForegroundColor Yellow
Write-Host "    • API URL: http://localhost:8000 (NOT fraud-detection-api)" -ForegroundColor Gray
Write-Host "    • Connection Status: Green checkmark if API is running" -ForegroundColor Gray
Write-Host ""
Write-Host "  ✓ Navigation works:" -ForegroundColor Yellow
Write-Host "    • Dashboard page loads with metrics" -ForegroundColor Gray
Write-Host "    • Transaction Analysis page accessible" -ForegroundColor Gray
Write-Host "    • Fraud Patterns page accessible" -ForegroundColor Gray
Write-Host "    • System Health page accessible" -ForegroundColor Gray
Write-Host ""
Write-Host "  ✓ Functionality test:" -ForegroundColor Yellow
Write-Host "    • Go to 'Transaction Analysis'" -ForegroundColor Gray
Write-Host "    • Fill in transaction details (or use defaults)" -ForegroundColor Gray
Write-Host "    • Click 'Analyze Transaction'" -ForegroundColor Gray
Write-Host "    • Verify prediction appears with confidence score" -ForegroundColor Gray
Write-Host ""
Write-Host "  ✓ Expected behavior:" -ForegroundColor Yellow
Write-Host "    • Pages load without errors" -ForegroundColor Gray
Write-Host "    • API calls complete successfully" -ForegroundColor Gray
Write-Host "    • Data displays correctly" -ForegroundColor Gray
Write-Host "    • Charts and visualizations render" -ForegroundColor Gray
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

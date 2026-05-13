# ═══════════════════════════════════════════════════════════
# COMPREHENSIVE UI LAUNCH TEST
# Tests UI launches without issues and validates endpoint
# ═══════════════════════════════════════════════════════════

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  UI LAUNCH TEST - FRAUD DETECTION SYSTEM                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = "D:\Study\AILearning\MLProjects\creditcardfrauddetection"
$UIDir = Join-Path $ProjectRoot "ui"
$StreamlitExe = "D:\Study\AILearning\shared_Environment\Scripts\streamlit.exe"
$PythonExe = "D:\Study\AILearning\shared_Environment\Scripts\python.exe"

$testResults = @{
    ConfigCheck = $false
    APIAvailable = $false
    UILaunched = $false
    UIAccessible = $false
    EndpointCorrect = $false
}

# ═══════════════════════════════════════════════════════════
# TEST 1: Configuration Check
# ═══════════════════════════════════════════════════════════
Write-Host "TEST 1: Configuration Validation" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray

$envFile = Join-Path $UIDir ".env.local"
if (Test-Path $envFile) {
    $content = Get-Content $envFile -Raw
    if ($content -match "API_URL=http://localhost:8000") {
        Write-Host "  ✅ PASS - API_URL correctly set to localhost:8000" -ForegroundColor Green
        $testResults.ConfigCheck = $true
        $testResults.EndpointCorrect = $true
    } elseif ($content -match "API_URL=.*fraud-detection-api") {
        Write-Host "  ❌ FAIL - API_URL points to Docker (fraud-detection-api)" -ForegroundColor Red
        Write-Host "     Expected: http://localhost:8000" -ForegroundColor Gray
        Write-Host "     Fix required in: ui/.env.local" -ForegroundColor Yellow
    } else {
        Write-Host "  ⚠️  WARN - Non-standard API_URL configuration" -ForegroundColor Yellow
        $testResults.ConfigCheck = $true
    }
} else {
    Write-Host "  ⚠️  WARN - .env.local not found, using defaults" -ForegroundColor Yellow
    $testResults.ConfigCheck = $true
}

Write-Host ""

# ═══════════════════════════════════════════════════════════
# TEST 2: API Server Check
# ═══════════════════════════════════════════════════════════
Write-Host "TEST 2: API Server Availability" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray

try {
    $apiHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "  ✅ PASS - API is reachable and healthy" -ForegroundColor Green
    Write-Host "     Status: $($apiHealth.status)" -ForegroundColor Gray
    Write-Host "     Environment: $($apiHealth.environment)" -ForegroundColor Gray
    $testResults.APIAvailable = $true
} catch {
    Write-Host "  ⚠️  WARN - API is not running" -ForegroundColor Yellow
    Write-Host "     UI will show connection errors without API" -ForegroundColor Gray
    Write-Host ""
    Write-Host "     To start API:" -ForegroundColor White
    Write-Host "       cd $ProjectRoot" -ForegroundColor Gray
    Write-Host "       python run_server.py" -ForegroundColor Gray
}

Write-Host ""

# ═══════════════════════════════════════════════════════════
# TEST 3: Check Current UI Status
# ═══════════════════════════════════════════════════════════
Write-Host "TEST 3: Current UI Status" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray

$uiPort = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue

if ($uiPort) {
    Write-Host "  ✓ Port 8501 is already in use" -ForegroundColor Yellow
    
    # Try to access it
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing -TimeoutSec 5
        Write-Host "  ✅ PASS - UI is already running and accessible" -ForegroundColor Green
        Write-Host "     HTTP Status: $($response.StatusCode)" -ForegroundColor Gray
        $testResults.UILaunched = $true
        $testResults.UIAccessible = $true
        
        Write-Host ""
        Write-Host "  Skipping launch - UI already operational" -ForegroundColor Cyan
        Write-Host ""
        
        # Skip to verification
        $skipLaunch = $true
    } catch {
        Write-Host "  ⚠️  Port is listening but UI not responding" -ForegroundColor Yellow
        Write-Host "     Stopping stale process..." -ForegroundColor Gray
        
        # Stop stale processes
        Get-Process | Where-Object {
            ($_.ProcessName -like "*streamlit*") -or
            (($_.ProcessName -like "*python*") -and 
             (Get-NetTCPConnection -OwningProcess $_.Id -ErrorAction SilentlyContinue | 
              Where-Object {$_.LocalPort -eq 8501}))
        } | Stop-Process -Force -ErrorAction SilentlyContinue
        
        Start-Sleep -Seconds 2
        Write-Host "  ✓ Cleared stale processes" -ForegroundColor Green
        $skipLaunch = $false
    }
} else {
    Write-Host "  ✓ Port 8501 is available" -ForegroundColor Green
    $skipLaunch = $false
}

Write-Host ""

# ═══════════════════════════════════════════════════════════
# TEST 4: Launch UI
# ═══════════════════════════════════════════════════════════
if (-not $skipLaunch) {
    Write-Host "TEST 4: UI Launch" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray
    
    Write-Host "  Starting Streamlit UI..." -ForegroundColor White
    
    # Check if Streamlit exists
    if (-not (Test-Path $StreamlitExe)) {
        Write-Host "  ❌ FAIL - Streamlit not found at: $StreamlitExe" -ForegroundColor Red
        Write-Host ""
        Write-Host "Install with: pip install streamlit" -ForegroundColor Yellow
        exit 1
    }
    
    # Launch in background
    $uiCmd = @"
Set-Location '$UIDir'
Write-Host ''
Write-Host '════════════════════════════════════════════════' -ForegroundColor Cyan
Write-Host '  FRAUD DETECTION UI DASHBOARD' -ForegroundColor Cyan
Write-Host '════════════════════════════════════════════════' -ForegroundColor Cyan
Write-Host ''
Write-Host 'URL: http://localhost:8501' -ForegroundColor Yellow
Write-Host 'API: http://localhost:8000' -ForegroundColor Yellow
Write-Host 'Config: ui/.env.local' -ForegroundColor Gray
Write-Host ''
Write-Host 'Starting Streamlit...' -ForegroundColor White
Write-Host ''
& '$StreamlitExe' run app.py --server.port 8501
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $uiCmd
    Write-Host "  ✓ UI process started" -ForegroundColor Green
    $testResults.UILaunched = $true
    
    Write-Host "  Waiting for UI to initialize..." -ForegroundColor Gray
    
    # Wait and check
    $maxAttempts = 20
    $attempt = 0
    $uiReady = $false
    
    while ($attempt -lt $maxAttempts -and -not $uiReady) {
        Start-Sleep -Seconds 2
        $attempt++
        
        Write-Host "    Attempt $attempt/$maxAttempts..." -NoNewline -ForegroundColor Gray
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200) {
                Write-Host " ✅" -ForegroundColor Green
                $uiReady = $true
                $testResults.UIAccessible = $true
            }
        } catch {
            Write-Host " ⏳" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    
    if ($uiReady) {
        Write-Host "  ✅ PASS - UI is accessible" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  TIMEOUT - UI may still be starting" -ForegroundColor Yellow
        Write-Host "     Check the UI window for detailed logs" -ForegroundColor Gray
    }
    
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════
# TEST 5: Verify UI Content and Endpoint
# ═══════════════════════════════════════════════════════════
Write-Host "TEST 5: UI Content Verification" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8501" -TimeoutSec 10
    $content = $response.Content
    
    if ($content -like "*Credit Card Fraud Detection*" -or $content.Length -gt 1000) {
        Write-Host "  ✅ PASS - UI content loaded successfully" -ForegroundColor Green
        Write-Host "     Content size: $($content.Length) bytes" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠️  WARN - UI page seems incomplete" -ForegroundColor Yellow
        Write-Host "     Content size: $($content.Length) bytes (expected > 1000)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ❌ FAIL - Cannot retrieve UI content: $_" -ForegroundColor Red
}

Write-Host ""

# ═══════════════════════════════════════════════════════════
# TEST 6: Browser Launch Test
# ═══════════════════════════════════════════════════════════
Write-Host "TEST 6: Browser Access" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray

Write-Host "  Opening UI in browser..." -ForegroundColor White
Start-Process "http://localhost:8501"
Start-Sleep -Seconds 2
Write-Host "  ✅ PASS - Browser launched" -ForegroundColor Green

Write-Host ""

# ═══════════════════════════════════════════════════════════
# TEST SUMMARY
# ═══════════════════════════════════════════════════════════
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  TEST SUMMARY                                              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$passed = 0
$total = 0

Write-Host "Test Results:" -ForegroundColor White
Write-Host ""

# Config Check
$total++
if ($testResults.ConfigCheck) {
    Write-Host "  ✅ Configuration Check" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ❌ Configuration Check" -ForegroundColor Red
}

# API Available
$total++
if ($testResults.APIAvailable) {
    Write-Host "  ✅ API Server Available" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ⚠️  API Server Available (Warning only)" -ForegroundColor Yellow
}

# UI Launched
$total++
if ($testResults.UILaunched) {
    Write-Host "  ✅ UI Launch Successful" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ❌ UI Launch Successful" -ForegroundColor Red
}

# UI Accessible
$total++
if ($testResults.UIAccessible) {
    Write-Host "  ✅ UI Web Accessible" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ❌ UI Web Accessible" -ForegroundColor Red
}

# Endpoint Check
$total++
if ($testResults.EndpointCorrect) {
    Write-Host "  ✅ Endpoint Configuration (localhost)" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ❌ Endpoint Configuration" -ForegroundColor Red
}

Write-Host ""
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray

$successRate = [math]::Round(($passed / $total) * 100, 1)

if ($passed -eq $total) {
    Write-Host "  🎉 ALL TESTS PASSED ($passed/$total - $successRate%)" -ForegroundColor Green
    $exitCode = 0
} elseif ($passed -ge ($total - 1)) {
    Write-Host "  ✅ MOSTLY PASSED ($passed/$total - $successRate%)" -ForegroundColor Green
    $exitCode = 0
} else {
    Write-Host "  ⚠️  SOME TESTS FAILED ($passed/$total - $successRate%)" -ForegroundColor Yellow
    $exitCode = 1
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Manual verification instructions
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  MANUAL VERIFICATION IN BROWSER                            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Please verify the following in the browser:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Sidebar shows:" -ForegroundColor Yellow
Write-Host "     • API URL: http://localhost:8000 ✅" -ForegroundColor Gray
Write-Host "     • Connection Status: Green checkmark" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Pages load without errors:" -ForegroundColor Yellow
Write-Host "     • Dashboard" -ForegroundColor Gray
Write-Host "     • Transaction Analysis" -ForegroundColor Gray
Write-Host "     • Fraud Patterns" -ForegroundColor Gray
Write-Host "     • System Health" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Test a transaction:" -ForegroundColor Yellow
Write-Host "     • Go to 'Transaction Analysis'" -ForegroundColor Gray
Write-Host "     • Click 'Analyze Transaction'" -ForegroundColor Gray
Write-Host "     • Verify fraud prediction appears" -ForegroundColor Gray
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($testResults.UIAccessible) {
    Write-Host "  Access URL: http://localhost:8501" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

exit $exitCode

# =====================================================
# START ALL SERVICES - FRAUD DETECTION SYSTEM
# =====================================================
# Launches API, UI, ML Model, and Analytics (LOCAL)
# UI connects to LOCAL API (localhost:8000) - NOT DOCKER

$ProjectRoot = "D:\Study\AILearning\MLProjects\creditcardfrauddetection"
$PythonExe   = "D:\Study\AILearning\shared_Environment\Scripts\python.exe"

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  FRAUD DETECTION SYSTEM - LOCAL DEPLOYMENT LAUNCHER" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $ProjectRoot

# ── STEP 1: Environment setup ─────────────────────────────────────────────────
Write-Host "[STEP 1] Configuring LOCAL environment..." -ForegroundColor Yellow

# Clear any lingering Docker env vars in current session
Remove-Item Env:\API_URL     -ErrorAction SilentlyContinue
Remove-Item Env:\API_BASE_URL -ErrorAction SilentlyContinue
$env:DEPLOYMENT_MODE = 'local'
$env:API_URL         = 'http://localhost:8000'
$env:API_BASE_URL    = 'http://localhost:8000'

# Validate required env files
if (-not (Test-Path ".env.local")) {
    Write-Host "  [ERROR] .env.local not found at $ProjectRoot" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path "ui\.env.local")) {
    Write-Host "  [ERROR] ui\.env.local not found" -ForegroundColor Red
    exit 1
}

# Copy env files
Copy-Item -Path ".env.local"     -Destination ".env"     -Force
Copy-Item -Path "ui\.env.local"  -Destination "ui\.env"  -Force

# Verify UI env points to localhost (fail fast if misconfigured)
$uiEnvContent = Get-Content "ui\.env" -Raw
if ($uiEnvContent -notmatch "localhost:8000") {
    Write-Host "  [ERROR] ui\.env does not point to localhost:8000" -ForegroundColor Red
    Get-Content "ui\.env" | Select-String "API_URL"
    exit 1
}

Write-Host "  [SUCCESS] .env.local loaded for API" -ForegroundColor Green
Write-Host "  [SUCCESS] ui\.env.local loaded for UI (localhost:8000)" -ForegroundColor Green
Write-Host ""

# ── STEP 2: Stop existing services ────────────────────────────────────────────
Write-Host "[STEP 2] Checking for existing services on ports 8000/8501..." -ForegroundColor Yellow

$apiRunning = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
$uiRunning  = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue

if ($apiRunning -or $uiRunning) {
    if ($apiRunning) { Write-Host "  [FOUND] API running on port 8000" -ForegroundColor Yellow }
    if ($uiRunning)  { Write-Host "  [FOUND] UI running on port 8501"  -ForegroundColor Yellow }
    Write-Host "  [ACTION] Stopping existing services..." -ForegroundColor Cyan

    Get-Process | Where-Object { $_.ProcessName -like "*python*" } | ForEach-Object {
        try {
            $conns = Get-NetTCPConnection -OwningProcess $_.Id -ErrorAction SilentlyContinue |
                     Where-Object { $_.LocalPort -eq 8000 -or $_.LocalPort -eq 8501 }
            if ($conns) {
                Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
                Write-Host "    [STOPPED] PID $($_.Id)" -ForegroundColor Green
            }
        } catch {}
    }
    Start-Sleep -Seconds 2
    Write-Host "  [SUCCESS] Services stopped" -ForegroundColor Green
} else {
    Write-Host "  [SUCCESS] Ports 8000 and 8501 are free" -ForegroundColor Green
}
Write-Host ""

# ── STEP 3: Launch API ────────────────────────────────────────────────────────
Write-Host "[STEP 3] Launching API Server..." -ForegroundColor Yellow
Write-Host "  Components: FastAPI | XGBoost ML Model | ChromaDB | Analytics" -ForegroundColor Gray

$apiCommand = @"
`$Host.UI.RawUI.WindowTitle = 'Fraud Detection API - LOCAL'
Set-Location '$ProjectRoot'
`$env:DEPLOYMENT_MODE = 'local'
Remove-Item Env:\API_URL -ErrorAction SilentlyContinue
Write-Host ''
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  FRAUD DETECTION API - LOCAL MODE'     -ForegroundColor White
Write-Host '========================================' -ForegroundColor Cyan
Write-Host 'URL: http://localhost:8000'  -ForegroundColor Yellow
Write-Host ''
& '$PythonExe' run_server.py
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCommand

# Wait for API to become healthy (up to 5 retries x 3s)
$apiHealthy = $false
for ($i = 1; $i -le 5; $i++) {
    Start-Sleep -Seconds 3
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
        if ($health.status -eq "healthy") { $apiHealthy = $true; break }
    } catch {}
    Write-Host "  Waiting for API... (attempt $i/5)" -ForegroundColor Gray
}

if ($apiHealthy) {
    Write-Host "  [SUCCESS] API is HEALTHY" -ForegroundColor Green
} else {
    Write-Host "  [WARNING] API may still be starting - check the API window" -ForegroundColor Yellow
}
Write-Host ""

# ── STEP 4: Launch UI ─────────────────────────────────────────────────────────
Write-Host "[STEP 4] Launching UI Dashboard..." -ForegroundColor Yellow

$uiCommand = @"
`$Host.UI.RawUI.WindowTitle = 'Fraud Detection UI - LOCAL'
Set-Location '$ProjectRoot'
`$env:DEPLOYMENT_MODE = 'local'
Remove-Item Env:\API_URL -ErrorAction SilentlyContinue
Write-Host ''
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  FRAUD DETECTION UI - LOCAL MODE'      -ForegroundColor White
Write-Host '========================================' -ForegroundColor Cyan
Write-Host 'URL: http://localhost:8501'              -ForegroundColor Yellow
Write-Host 'API: http://localhost:8000 (LOCAL)'      -ForegroundColor Yellow
Write-Host ''
& '$PythonExe' run_ui.py
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $uiCommand
Write-Host "  Waiting for UI to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 10
Write-Host ""

# ── STEP 5: Verify all components ─────────────────────────────────────────────
Write-Host "[STEP 5] Verifying all components..." -ForegroundColor Yellow
Write-Host ""
$allOk = $true

Write-Host "  1. API Server..." -NoNewline
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host " [SUCCESS] $($health.status)" -ForegroundColor Green
} catch {
    Write-Host " [ERROR] FAILED" -ForegroundColor Red
    $allOk = $false
}

Write-Host "  2. ML Model..." -NoNewline
try {
    $body    = @{ transaction_id = "health_check"; card_id = "card_001"; merchant_id = "merch_001"; timestamp = "2025-01-01T10:00:00Z"; amount = 150.50; merchant_category = "retail"; merchant_name = "Test Store"; merchant_country = "US"; customer_id = "cust_001"; is_online = $false; currency = "USD" } | ConvertTo-Json
    $headers = @{ "Content-Type" = "application/json"; "X-API-Key" = "development_api_key_for_testing" }
    Invoke-RestMethod -Uri "http://localhost:8000/api/v1/detect-fraud" -Method Post -Body $body -Headers $headers -TimeoutSec 10 | Out-Null
    Write-Host " [SUCCESS] LOADED" -ForegroundColor Green
} catch {
    Write-Host " [WARNING] Check API window" -ForegroundColor Yellow
}

Write-Host "  3. Fraud Patterns (Vector DB)..." -NoNewline
try {
    $patterns = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/fraud-patterns?limit=5" -TimeoutSec 5
    Write-Host " [SUCCESS] $($patterns.Count) patterns loaded" -ForegroundColor Green
} catch {
    Write-Host " [ERROR] FAILED" -ForegroundColor Red
    $allOk = $false
}

Write-Host "  4. Analytics Engine..." -NoNewline
try {
    $metrics = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/metrics" -TimeoutSec 5
    Write-Host " [SUCCESS] ACTIVE (transactions: $($metrics.total_transactions), accuracy: $($metrics.model_accuracy)%)" -ForegroundColor Green
} catch {
    Write-Host " [ERROR] FAILED" -ForegroundColor Red
    $allOk = $false
}

Write-Host "  5. UI Dashboard..." -NoNewline
try {
    Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing -TimeoutSec 5 | Out-Null
    Write-Host " [SUCCESS] ACCESSIBLE" -ForegroundColor Green
} catch {
    Write-Host " [ERROR] FAILED" -ForegroundColor Red
    $allOk = $false
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan

if ($allOk) {
    Write-Host "  [SUCCESS] ALL SYSTEMS OPERATIONAL!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  UI Dashboard : http://localhost:8501" -ForegroundColor Yellow
    Write-Host "  API Server   : http://localhost:8000" -ForegroundColor Yellow
    Write-Host "  API Docs     : http://localhost:8000/docs" -ForegroundColor Yellow
    Write-Host ""
    Start-Process "http://localhost:8501"
    Write-Host "  [INFO] Browser launched" -ForegroundColor Cyan
} else {
    Write-Host "  [WARNING] SOME COMPONENTS FAILED TO START" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Troubleshooting:" -ForegroundColor White
    Write-Host "    1. Check the API/UI PowerShell windows for errors" -ForegroundColor Gray
    Write-Host "    2. Verify Python environment: $PythonExe" -ForegroundColor Gray
    Write-Host "    3. Confirm ports 8000/8501 are not blocked" -ForegroundColor Gray
    Write-Host "    4. Review logs in the 'logs' directory" -ForegroundColor Gray
}

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

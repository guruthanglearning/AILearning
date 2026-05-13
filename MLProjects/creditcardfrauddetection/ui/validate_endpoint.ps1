# Quick Endpoint Validator for UI
# Run this before launching UI to verify configuration

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  UI ENDPOINT VALIDATION                                    ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$UIDir = "D:\Study\AILearning\MLProjects\creditcardfrauddetection\ui"
$EnvFile = Join-Path $UIDir ".env.local"

Write-Host "Checking UI Configuration..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path $EnvFile) {
    Write-Host "✓ Configuration file: .env.local" -ForegroundColor Green
    Write-Host ""
    
    $content = Get-Content $EnvFile -Raw
    
    # Check API_URL
    if ($content -match "API_URL=([^\r\n]+)") {
        $apiUrl = $matches[1].Trim()
        Write-Host "API_URL Configuration:" -ForegroundColor White
        Write-Host "  Current: $apiUrl" -ForegroundColor Yellow
        
        if ($apiUrl -eq "http://localhost:8000") {
            Write-Host "  Status: ✅ CORRECT (localhost)" -ForegroundColor Green
        } elseif ($apiUrl -like "*fraud-detection-api*") {
            Write-Host "  Status: ❌ WRONG (Docker service name)" -ForegroundColor Red
            Write-Host "  Fix: Change to http://localhost:8000" -ForegroundColor Yellow
        } else {
            Write-Host "  Status: ⚠️  Non-standard URL" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ❌ API_URL not found in config" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # Check API_BASE_URL
    if ($content -match "API_BASE_URL=([^\r\n]+)") {
        $apiBaseUrl = $matches[1].Trim()
        Write-Host "API_BASE_URL Configuration:" -ForegroundColor White
        Write-Host "  Current: $apiBaseUrl" -ForegroundColor Yellow
        
        if ($apiBaseUrl -eq "http://localhost:8000") {
            Write-Host "  Status: ✅ CORRECT (localhost)" -ForegroundColor Green
        } else {
            Write-Host "  Status: ⚠️  Should be http://localhost:8000" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "❌ Configuration file not found!" -ForegroundColor Red
    Write-Host "  Expected: $EnvFile" -ForegroundColor Gray
}

Write-Host ""
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""

# Check API accessibility
Write-Host "Checking API Server Connectivity..." -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "✅ API is REACHABLE" -ForegroundColor Green
    Write-Host "  Status: $($response.status)" -ForegroundColor Gray
    Write-Host "  Environment: $($response.environment)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "✅ UI can connect to API at localhost:8000" -ForegroundColor Green
} catch {
    Write-Host "⚠️  API is NOT REACHABLE" -ForegroundColor Yellow
    Write-Host "  Error: $_" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Note: Start API server before launching UI" -ForegroundColor Yellow
    Write-Host "Run: python run_server.py" -ForegroundColor Gray
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

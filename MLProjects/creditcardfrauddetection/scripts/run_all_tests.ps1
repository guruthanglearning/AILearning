# =====================================================
# ALL TESTS RUNNER (UBER SCRIPT)
# Credit Card Fraud Detection System
# =====================================================
# Runs all test suites: Unit, Integration, and E2E
# with comprehensive reporting
# Supports local and Docker deployment modes

param(
    [switch]$SkipUnit,
    [switch]$SkipIntegration,
    [switch]$SkipE2E,
    [switch]$StopOnFailure,
    [switch]$Verbose,
    [string]$OutputReport = "test_results_$(Get-Date -Format 'yyyyMMdd_HHmmss').json",
    [ValidateSet('local', 'docker')]
    [string]$Mode = 'local'
)

$ProjectRoot = "D:\Study\AILearning\MLProjects\creditcardfrauddetection"
$PythonPath = "D:\Study\AILearning\shared_Environment\Scripts\python.exe"

$results = @{
    "test_suite" = "All Tests"
    "timestamp" = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    "environment" = @{
        "project_root" = $ProjectRoot
        "python_path" = $PythonPath
    }
    "summary" = @{
        "total_suites" = 0
        "passed_suites" = 0
        "failed_suites" = 0
        "skipped_suites" = 0
    }
    "suites" = @()
}

Write-Host "`n" -NoNewline
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  CREDIT CARD FRAUD DETECTION - ALL TESTS RUNNER" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Project: $ProjectRoot" -ForegroundColor Gray
Write-Host "  Timestamp: $($results.timestamp)" -ForegroundColor Gray
if ($Mode -eq 'docker') {
    Write-Host "  Deployment Mode: DOCKER" -ForegroundColor Blue
} else {
    Write-Host "  Deployment Mode: LOCAL" -ForegroundColor Green
}
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location -Path $ProjectRoot

# Function to run a test suite
function Run-TestSuite {
    param(
        [string]$Name,
        [string]$Description,
        [scriptblock]$Command,
        [switch]$Skip
    )
    
    $results.summary.total_suites++
    
    $suiteResult = @{
        "name" = $Name
        "description" = $Description
        "status" = "NOT_RUN"
        "start_time" = $null
        "end_time" = $null
        "duration_seconds" = 0
        "exit_code" = $null
        "error" = $null
    }
    
    if ($Skip) {
        Write-Host "`n[$Name] SKIPPED" -ForegroundColor Yellow
        Write-Host "  $Description" -ForegroundColor Gray
        $suiteResult.status = "SKIPPED"
        $results.summary.skipped_suites++
        $results.suites += $suiteResult
        return $true
    }
    
    Write-Host "`n" -NoNewline
    Write-Host "------------------------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "[$Name] STARTING" -ForegroundColor Yellow
    Write-Host "  $Description" -ForegroundColor Gray
    Write-Host "------------------------------------------------------------" -ForegroundColor DarkCyan
    
    $suiteResult.start_time = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    $startTime = Get-Date
    
    try {
        & $Command
        $exitCode = $LASTEXITCODE
        $suiteResult.exit_code = $exitCode
        
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        $suiteResult.end_time = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
        $suiteResult.duration_seconds = [math]::Round($duration, 2)
        
        if ($exitCode -eq 0) {
            Write-Host "`n[$Name] ✅ PASSED (${duration}s)" -ForegroundColor Green
            $suiteResult.status = "PASSED"
            $results.summary.passed_suites++
            return $true
        } else {
            Write-Host "`n[$Name] ❌ FAILED (exit code: $exitCode, ${duration}s)" -ForegroundColor Red
            $suiteResult.status = "FAILED"
            $suiteResult.error = "Exit code: $exitCode"
            $results.summary.failed_suites++
            return $false
        }
    } catch {
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        $suiteResult.end_time = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
        $suiteResult.duration_seconds = [math]::Round($duration, 2)
        $suiteResult.status = "ERROR"
        $suiteResult.error = $_.Exception.Message
        $results.summary.failed_suites++
        
        Write-Host "`n[$Name] ❌ ERROR (${duration}s)" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    } finally {
        $results.suites += $suiteResult
    }
}

# =====================================================
# RUN TEST SUITES
# =====================================================

$allPassed = $true

# 1. Unit Tests
$unitPassed = Run-TestSuite `
    -Name "Unit Tests" `
    -Description "Testing ML models, system components, and transaction endpoints with code coverage" `
    -Skip:$SkipUnit `
    -Command {
        if ($Verbose) {
            & $PythonPath -m pytest tests/test_ml_model.py tests/test_system.py tests/test_transaction_endpoints.py -v --cov=app --cov-report=term --cov-report=html
        } else {
            & $PythonPath -m pytest tests/test_ml_model.py tests/test_system.py tests/test_transaction_endpoints.py --cov=app --cov-report=term --cov-report=html
        }
    }

if (-not $unitPassed -and $StopOnFailure) {
    Write-Host "`n❌ Stopping due to unit test failure (StopOnFailure enabled)" -ForegroundColor Red
    $allPassed = $false
} else {
    $allPassed = $allPassed -and $unitPassed
}

# 2. Integration Tests
if ($allPassed -or -not $StopOnFailure) {
    $integrationPassed = Run-TestSuite `
        -Name "Integration Tests" `
        -Description "Testing API endpoints: fraud detection, feedback, and pattern ingestion" `
        -Skip:$SkipIntegration `
        -Command {
            & $PythonPath tests/run_integration_tests.py --mode $Mode
        }
    
    if (-not $integrationPassed -and $StopOnFailure) {
        Write-Host "`n❌ Stopping due to integration test failure (StopOnFailure enabled)" -ForegroundColor Red
        $allPassed = $false
    } else {
        $allPassed = $allPassed -and $integrationPassed
    }
}

# 3. Playwright E2E Tests
if ($allPassed -or -not $StopOnFailure) {
    # Check if services are running
    $apiRunning = $false
    $uiRunning = $false
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        $apiRunning = ($response.StatusCode -eq 200)
    } catch { }
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8501" -TimeoutSec 2 -ErrorAction SilentlyContinue
        $uiRunning = ($response.StatusCode -eq 200)
    } catch { }
    
    if (-not $apiRunning -or -not $uiRunning) {
        Write-Host "`n⚠️  Warning: API or UI not running. Playwright tests will be skipped." -ForegroundColor Yellow
        Write-Host "   Start services with: .\launch.ps1 both" -ForegroundColor Yellow
        $SkipE2E = $true
    }
    
    $e2ePassed = Run-TestSuite `
        -Name "Playwright E2E Tests" `
        -Description "Testing UI interactions, navigation, forms, and end-to-end workflows" `
        -Skip:$SkipE2E `
        -Command {
            & $PythonPath tests/test_ui_e2e.py
        }
    
    $allPassed = $allPassed -and $e2ePassed
}

# =====================================================
# GENERATE SUMMARY REPORT
# =====================================================

Write-Host "`n" -NoNewline
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TEST EXECUTION SUMMARY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$totalDuration = ($results.suites | Measure-Object -Property duration_seconds -Sum).Sum
Write-Host "  Total Suites:   $($results.summary.total_suites)" -ForegroundColor White
Write-Host "  Passed:         $($results.summary.passed_suites)" -ForegroundColor Green
Write-Host "  Failed:         $($results.summary.failed_suites)" -ForegroundColor $(if ($results.summary.failed_suites -gt 0) { "Red" } else { "Gray" })
Write-Host "  Skipped:        $($results.summary.skipped_suites)" -ForegroundColor Yellow
Write-Host "  Total Duration: $([math]::Round($totalDuration, 2))s" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan

# Individual suite results
Write-Host "`nSuite Details:" -ForegroundColor Cyan
foreach ($suite in $results.suites) {
    $statusColor = switch ($suite.status) {
        "PASSED" { "Green" }
        "FAILED" { "Red" }
        "ERROR" { "Red" }
        "SKIPPED" { "Yellow" }
        default { "Gray" }
    }
    
    $statusIcon = switch ($suite.status) {
        "PASSED" { "✅" }
        "FAILED" { "❌" }
        "ERROR" { "❌" }
        "SKIPPED" { "⏭️ " }
        default { "⚪" }
    }
    
    Write-Host "  $statusIcon $($suite.name): " -NoNewline
    Write-Host "$($suite.status)" -ForegroundColor $statusColor -NoNewline
    if ($suite.duration_seconds -gt 0) {
        Write-Host " ($($suite.duration_seconds)s)" -ForegroundColor Gray
    } else {
        Write-Host ""
    }
    
    if ($suite.error) {
        Write-Host "     Error: $($suite.error)" -ForegroundColor Red
    }
}

Write-Host "============================================================" -ForegroundColor Cyan

# Save results to JSON
$reportPath = Join-Path $ProjectRoot "tests/reports" $OutputReport
$reportDir = Split-Path -Parent $reportPath
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

$results | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportPath -Encoding UTF8
Write-Host "`n📄 Detailed report saved to: $reportPath" -ForegroundColor Cyan

# Generate HTML summary
$htmlReport = $reportPath -replace '\.json$', '.html'
$htmlContent = @"
<!DOCTYPE html>
<html>
<head>
    <title>Test Results - Credit Card Fraud Detection</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .stat-box { flex: 1; padding: 20px; border-radius: 5px; text-align: center; }
        .stat-box h3 { margin: 0; font-size: 36px; }
        .stat-box p { margin: 10px 0 0 0; color: #666; }
        .passed { background-color: #d4edda; color: #155724; }
        .failed { background-color: #f8d7da; color: #721c24; }
        .skipped { background-color: #fff3cd; color: #856404; }
        .total { background-color: #d1ecf1; color: #0c5460; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #007bff; color: white; }
        tr:hover { background-color: #f5f5f5; }
        .status-passed { color: #28a745; font-weight: bold; }
        .status-failed { color: #dc3545; font-weight: bold; }
        .status-error { color: #dc3545; font-weight: bold; }
        .status-skipped { color: #ffc107; font-weight: bold; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Test Execution Report</h1>
        <p><strong>Project:</strong> Credit Card Fraud Detection System</p>
        <p><strong>Timestamp:</strong> $($results.timestamp)</p>
        <p><strong>Total Duration:</strong> $([math]::Round($totalDuration, 2)) seconds</p>
        
        <h2>Summary</h2>
        <div class="summary">
            <div class="stat-box total">
                <h3>$($results.summary.total_suites)</h3>
                <p>Total Suites</p>
            </div>
            <div class="stat-box passed">
                <h3>$($results.summary.passed_suites)</h3>
                <p>Passed</p>
            </div>
            <div class="stat-box failed">
                <h3>$($results.summary.failed_suites)</h3>
                <p>Failed</p>
            </div>
            <div class="stat-box skipped">
                <h3>$($results.summary.skipped_suites)</h3>
                <p>Skipped</p>
            </div>
        </div>
        
        <h2>Test Suite Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Suite</th>
                    <th>Status</th>
                    <th>Duration (s)</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
"@

foreach ($suite in $results.suites) {
    $statusClass = "status-$($suite.status.ToLower())"
    $errorInfo = if ($suite.error) { "<br><small>Error: $($suite.error)</small>" } else { "" }
    $htmlContent += @"
                <tr>
                    <td><strong>$($suite.name)</strong><br><small>$($suite.description)</small></td>
                    <td class="$statusClass">$($suite.status)</td>
                    <td>$($suite.duration_seconds)</td>
                    <td>Exit Code: $($suite.exit_code)$errorInfo</td>
                </tr>
"@
}

$htmlContent += @"
            </tbody>
        </table>
        
        <div class="footer">
            <p>Generated by Credit Card Fraud Detection Test Suite</p>
            <p>For detailed logs, check individual test reports in the tests/reports directory</p>
        </div>
    </div>
</body>
</html>
"@

$htmlContent | Out-File -FilePath $htmlReport -Encoding UTF8
Write-Host "📄 HTML report saved to: $htmlReport" -ForegroundColor Cyan

Write-Host "`n============================================================`n" -ForegroundColor Cyan

# Exit with appropriate code
if ($allPassed) {
    Write-Host "✅ ALL TESTS PASSED!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ SOME TESTS FAILED!" -ForegroundColor Red
    exit 1
}

# Integration Test Script for Fraud Detection System
# This script tests all components: API, UI, Monitoring, and Telemetry

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  FRAUD DETECTION INTEGRATION TEST" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$testResults = @{
    Passed = 0
    Failed = 0
    Tests = @()
}

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200,
        [string]$Method = "GET",
        [hashtable]$Headers = @{},
        [string]$Body = $null
    )
    
    Write-Host "Testing: $Name..." -NoNewline
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            UseBasicParsing = $true
            Headers = $Headers
        }
        
        if ($Body) {
            $params.Body = $Body
        }
        
        $response = Invoke-WebRequest @params -ErrorAction Stop
        
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host " [PASSED]" -ForegroundColor Green
            $script:testResults.Passed++
            $script:testResults.Tests += @{
                Name = $Name
                Status = "PASSED"
                Details = "Status: $($response.StatusCode)"
            }
            return $true
        } else {
            Write-Host " [FAILED] (Status: $($response.StatusCode))" -ForegroundColor Red
            $script:testResults.Failed++
            $script:testResults.Tests += @{
                Name = $Name
                Status = "FAILED"
                Details = "Expected: $ExpectedStatus, Got: $($response.StatusCode)"
            }
            return $false
        }
    } catch {
        Write-Host " [FAILED]" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:testResults.Failed++
        $script:testResults.Tests += @{
            Name = $Name
            Status = "FAILED"
            Details = $_.Exception.Message
        }
        return $false
    }
}

# Test 1: Docker Container Status
Write-Host "`n--- Phase 1: Docker Deployment Validation ---`n" -ForegroundColor Yellow
$containers = docker ps --filter "name=fraud-detection" --format "{{.Names}}"
$expectedContainers = @("fraud-detection-api", "fraud-detection-ui", "fraud-detection-grafana")

foreach ($container in $expectedContainers) {
    if ($containers -contains $container) {
        Write-Host "Container $container..." -NoNewline
        $status = docker inspect $container --format "{{.State.Status}}"
        if ($status -eq "running") {
            Write-Host " [PASSED] (Running)" -ForegroundColor Green
            $testResults.Passed++
            $testResults.Tests += @{
                Name = "Container: $container"
                Status = "PASSED"
                Details = "Status: Running"
            }
        } else {
            Write-Host " [FAILED] (Status: $status)" -ForegroundColor Red
            $testResults.Failed++
            $testResults.Tests += @{
                Name = "Container: $container"
                Status = "FAILED"
                Details = "Status: $status"
            }
        }
    } else {
        Write-Host "Container $container... [FAILED] (Not Found)" -ForegroundColor Red
        $testResults.Failed++
        $testResults.Tests += @{
            Name = "Container: $container"
            Status = "FAILED"
            Details = "Container not found"
        }
    }
}

# Test 2: Service Health Endpoints
Write-Host "`n--- Phase 2: Service Health Validation ---`n" -ForegroundColor Yellow

Test-Endpoint -Name "API Health Check" -Url "http://localhost:8000/health"
Test-Endpoint -Name "Streamlit UI" -Url "http://localhost:8501"
Test-Endpoint -Name "Prometheus" -Url "http://localhost:9090/-/healthy"
Test-Endpoint -Name "Grafana Health" -Url "http://localhost:3000/api/health"

# Test 3: API Endpoints
Write-Host "`n--- Phase 3: API Functionality Tests ---`n" -ForegroundColor Yellow

$apiKey = "development_api_key_for_testing"
$headers = @{
    'Content-Type' = 'application/json'
    'X-API-Key' = $apiKey
}

# Test legitimate transaction
$legitimateTransaction = @{
    transaction_id = "TXN_TEST_001"
    amount = 150
    merchant_name = "Walmart"
    merchant_id = "MERCH_001"
    merchant_category = "retail"
    transaction_type = "purchase"
    card_present = $true
    card_id = "CARD_001"
    online_order = $false
    is_online = $false
    customer_id = "CUST_001"
    timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    merchant_country = "US"
    currency = "USD"
} | ConvertTo-Json

Test-Endpoint -Name "Fraud Detection - Legitimate Transaction" `
    -Url "http://localhost:8000/api/v1/detect-fraud" `
    -Method "POST" `
    -Headers $headers `
    -Body $legitimateTransaction

# Test suspicious transaction (high amount, online, no merchant name)
$suspiciousTransaction = @{
    transaction_id = "TXN_TEST_002"
    amount = 9500
    merchant_name = "No merchant name"
    merchant_id = "MERCH_UNKNOWN"
    merchant_category = "electronics"
    transaction_type = "purchase"
    card_present = $false
    card_id = "CARD_001"
    online_order = $true
    is_online = $true
    customer_id = "CUST_001"
    timestamp = "2026-01-30T02:00:00"
    merchant_country = "US"
    currency = "USD"
    latitude = 0
    longitude = 0
} | ConvertTo-Json

Test-Endpoint -Name "Fraud Detection - Suspicious Transaction" `
    -Url "http://localhost:8000/api/v1/detect-fraud" `
    -Method "POST" `
    -Headers $headers `
    -Body $suspiciousTransaction

# Test data quality validation (missing merchant)
$dataQualityTest = @{
    transaction_id = "TXN_TEST_003"
    amount = 79
    merchant_name = "No merchant name"
    merchant_id = "MERCH_UNKNOWN"
    merchant_category = "services"
    transaction_type = "purchase"
    card_present = $false
    card_id = "CARD_001"
    online_order = $true
    is_online = $true
    customer_id = "CUST_001"
    timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    merchant_country = "US"
    currency = "USD"
    latitude = 0
    longitude = 0
} | ConvertTo-Json

Test-Endpoint -Name "Data Quality Validation Test" `
    -Url "http://localhost:8000/api/v1/detect-fraud" `
    -Method "POST" `
    -Headers $headers `
    -Body $dataQualityTest

# Test other API endpoints
Test-Endpoint -Name "Health Endpoint" -Url "http://localhost:8000/health"
Test-Endpoint -Name "Metrics Endpoint" -Url "http://localhost:8000/metrics"

# Test 4: Monitoring and Telemetry
Write-Host "`n--- Phase 4: Monitoring and Telemetry ---`n" -ForegroundColor Yellow

Test-Endpoint -Name "Prometheus Targets" -Url "http://localhost:9090/api/v1/targets"
Test-Endpoint -Name "Grafana Datasources" -Url "http://localhost:3000/api/datasources"

# Generate Test Report
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "         TEST RESULTS SUMMARY" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$totalTests = $testResults.Passed + $testResults.Failed
$passRate = if ($totalTests -gt 0) { [math]::Round(($testResults.Passed / $totalTests) * 100, 2) } else { 0 }

Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $($testResults.Passed)" -ForegroundColor Green
Write-Host "Failed: $($testResults.Failed)" -ForegroundColor $(if ($testResults.Failed -eq 0) { "Green" } else { "Red" })
Write-Host "Pass Rate: $passRate%" -ForegroundColor $(if ($passRate -ge 90) { "Green" } elseif ($passRate -ge 70) { "Yellow" } else { "Red" })

Write-Host "`n--- Detailed Results ---`n" -ForegroundColor Yellow

foreach ($test in $testResults.Tests) {
    $statusColor = if ($test.Status -eq "PASSED") { "Green" } else { "Red" }
    Write-Host "$($test.Name): " -NoNewline
    Write-Host "$($test.Status)" -ForegroundColor $statusColor
    Write-Host "  $($test.Details)" -ForegroundColor Gray
}

# Save results to JSON file
$reportPath = ".\tests\integration_test_results_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss').json"
$testResults | ConvertTo-Json -Depth 10 | Out-File $reportPath

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test report saved to: $reportPath" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Exit with appropriate code
if ($testResults.Failed -eq 0) {
    Write-Host "[ALL TESTS PASSED!]" -ForegroundColor Green
    exit 0
} else {
    Write-Host "[SOME TESTS FAILED!]" -ForegroundColor Red
    exit 1
}

# =====================================================
# Unit Tests Runner - Credit Card Fraud Detection
# =====================================================
# Runs unit tests with code coverage

param(
    [switch]$NoCoverage,
    [switch]$Verbose
)

$ProjectRoot = "D:\Study\AILearning\MLProjects\creditcardfrauddetection"
$PythonPath = "D:\Study\AILearning\shared_Environment\Scripts\python.exe"

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "Credit Card Fraud Detection - Unit Tests" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

Set-Location -Path $ProjectRoot

if ($NoCoverage) {
    Write-Host "`nRunning unit tests without coverage..." -ForegroundColor Yellow
    
    if ($Verbose) {
        & $PythonPath -m pytest tests/test_ml_model.py tests/test_system.py tests/test_transaction_endpoints.py -v
    } else {
        & $PythonPath -m pytest tests/test_ml_model.py tests/test_system.py tests/test_transaction_endpoints.py
    }
} else {
    Write-Host "`nRunning unit tests with code coverage..." -ForegroundColor Yellow
    
    if ($Verbose) {
        & $PythonPath -m pytest tests/test_ml_model.py tests/test_system.py tests/test_transaction_endpoints.py -v --cov=app --cov-report=term --cov-report=html
    } else {
        & $PythonPath -m pytest tests/test_ml_model.py tests/test_system.py tests/test_transaction_endpoints.py --cov=app --cov-report=term --cov-report=html
    }
    
    if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq 1) {
        Write-Host "`n✅ Coverage report generated in 'htmlcov' directory" -ForegroundColor Green
        Write-Host "   Open htmlcov/index.html to view detailed coverage" -ForegroundColor Cyan
    }
}

Write-Host "`n==================================================" -ForegroundColor Cyan

exit $LASTEXITCODE

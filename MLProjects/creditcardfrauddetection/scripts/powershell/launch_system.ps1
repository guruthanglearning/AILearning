# Launch System for Credit Card Fraud Detection
# This script starts both the API server and UI in separate PowerShell instances
# Updated: July 8, 2025

$projectPath = "d:\Study\AILearning\MLProjects\creditcardfrauddetection"
$sharedEnvPath = "d:\Study\AILearning\shared_Environment"

Write-Host "Starting Credit Card Fraud Detection System..." -ForegroundColor Cyan
Write-Host "Project Path: $projectPath" -ForegroundColor Gray
Write-Host "Shared Environment: $sharedEnvPath" -ForegroundColor Gray

# Check if paths exist
if (-not (Test-Path $projectPath)) {
    Write-Host "ERROR: Project path not found: $projectPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $sharedEnvPath)) {
    Write-Host "ERROR: Shared environment not found: $sharedEnvPath" -ForegroundColor Red
    exit 1
}

# Start API server in a new PowerShell window
Write-Host "Starting API server..." -ForegroundColor Yellow
$apiCommand = "cd '$projectPath'; python '$projectPath\run_server.py'"
Start-Process PowerShell -ArgumentList "-NoExit", "-Command", $apiCommand

# Wait for API to start
Write-Host "Waiting 8 seconds for API to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Start UI in a new PowerShell window
Write-Host "Starting Streamlit UI..." -ForegroundColor Yellow
$uiCommand = "cd '$sharedEnvPath\Scripts'; .\Activate.ps1; cd '$projectPath\ui'; streamlit run app.py --server.port=8501"
Start-Process PowerShell -ArgumentList "-NoExit", "-Command", $uiCommand

Write-Host "`nSystem launched successfully!" -ForegroundColor Green
Write-Host "- API server: http://localhost:8000" -ForegroundColor Cyan
Write-Host "- UI interface: http://localhost:8501" -ForegroundColor Cyan
Write-Host "`nBoth components are running in separate PowerShell windows." -ForegroundColor Yellow
Write-Host "Close the PowerShell windows to stop the services." -ForegroundColor Yellow
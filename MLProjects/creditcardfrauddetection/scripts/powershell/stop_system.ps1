# Stop all Fraud Detection System components
# This script stops any running instances of the API server and UI
# Created: May 28, 2025

# Stop API server (typically on port 8000)
$apiProcesses = Get-Process | Where-Object { $_.CommandLine -like "*run_server.py*" -or $_.CommandLine -like "*uvicorn*" }
if ($apiProcesses) {
    Write-Host "Stopping API server processes..." -ForegroundColor Yellow
    foreach ($process in $apiProcesses) {
        try {
            Stop-Process -Id $process.Id -Force
            Write-Host "Stopped process ID: $($process.Id)" -ForegroundColor Green
        } catch {
            Write-Host "Failed to stop process ID: $($process.Id)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "No API server processes found." -ForegroundColor Cyan
}

# Stop Streamlit UI (typically on port 8501)
$uiProcesses = Get-Process | Where-Object { $_.CommandLine -like "*streamlit*" }
if ($uiProcesses) {
    Write-Host "Stopping Streamlit UI processes..." -ForegroundColor Yellow
    foreach ($process in $uiProcesses) {
        try {
            Stop-Process -Id $process.Id -Force
            Write-Host "Stopped process ID: $($process.Id)" -ForegroundColor Green
        } catch {
            Write-Host "Failed to stop process ID: $($process.Id)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "No Streamlit UI processes found." -ForegroundColor Cyan
}

# Check for any Python processes related to our project
$projectPath = "d:\Study\AILearning\MLProjects\creditcardfrauddetection"
$pythonProcesses = Get-Process python | Where-Object { $_.CommandLine -like "*$projectPath*" }
if ($pythonProcesses) {
    Write-Host "Stopping remaining Python processes related to the project..." -ForegroundColor Yellow
    foreach ($process in $pythonProcesses) {
        try {
            Stop-Process -Id $process.Id -Force
            Write-Host "Stopped process ID: $($process.Id)" -ForegroundColor Green
        } catch {
            Write-Host "Failed to stop process ID: $($process.Id)" -ForegroundColor Red
        }
    }
}

Write-Host "`nAll Fraud Detection System components have been stopped." -ForegroundColor Green

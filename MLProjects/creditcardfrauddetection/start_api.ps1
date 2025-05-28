# Start API server for Credit Card Fraud Detection System
Write-Host "Starting Credit Card Fraud Detection API Server..." -ForegroundColor Cyan

$pythonPath = "d:\Study\AILearning\shared_Environment\Scripts\python.exe"
$projectPath = "d:\Study\AILearning\MLProjects\creditcardfrauddetection"

# Set the current directory to the project path
Set-Location -Path $projectPath

# Start the API server
Write-Host "Running API server on http://localhost:8000" -ForegroundColor Green
& $pythonPath run_server.py

# Test API connection for Credit Card Fraud Detection System
Write-Host "Testing API Connection..." -ForegroundColor Cyan

$pythonPath = "d:\Study\AILearning\shared_Environment\Scripts\python.exe"
$projectPath = "d:\Study\AILearning\MLProjects\creditcardfrauddetection"

# Set the current directory to the project path
Set-Location -Path $projectPath

# Run the API test script
Write-Host "Running API test..." -ForegroundColor Yellow
& $pythonPath ui\api_test.py

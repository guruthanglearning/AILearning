# Test API connection for Credit Card Fraud Detection System including starting the server
Write-Host "Starting API and running tests..." -ForegroundColor Cyan

$pythonPath = "d:\Study\AILearning\shared_Environment\Scripts\python.exe"
$projectPath = "d:\Study\AILearning\MLProjects\creditcardfrauddetection"

# Set the current directory to the project path
Set-Location -Path $projectPath

# Run the test script that starts the API and runs tests
Write-Host "Running tests with server startup..." -ForegroundColor Yellow
& $pythonPath run_tests.py

# Start API server and run tests
$pythonPath = "d:\Study\AILearning\shared_Environment\Scripts\python.exe"
$projectPath = "d:\Study\AILearning\MLProjects\creditcardfrauddetection"

# Set the current directory to the project path
Set-Location -Path $projectPath

Write-Host "Starting API server and running tests..." -ForegroundColor Cyan

# Run the Python script that starts the server and runs tests
& $pythonPath start_and_test_api.py

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
} else {
    Write-Host "Some tests failed. Please check the logs." -ForegroundColor Red
}

# Start API server and run tests
Write-Host "Starting Credit Card Fraud Detection API and Tests..." -ForegroundColor Cyan
Write-Host

$pythonPath = "d:\Study\AILearning\shared_Environment\Scripts\python.exe"
$projectPath = "d:\Study\AILearning\MLProjects\creditcardfrauddetection"

# Set the current directory to the project path
Set-Location -Path $projectPath

# Start API server in a new process
Write-Host "Starting API server..." -ForegroundColor Yellow
$serverProcess = Start-Process -FilePath $pythonPath -ArgumentList "run_server.py" -PassThru -NoNewWindow

# Wait a few seconds for the server to initialize
Write-Host "Waiting for server to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Run API tests
Write-Host "Running API tests..." -ForegroundColor Yellow
& $pythonPath ui\api_test.py

# Stop the API server
Write-Host "Stopping API server..." -ForegroundColor Yellow
Stop-Process -Id $serverProcess.Id -Force

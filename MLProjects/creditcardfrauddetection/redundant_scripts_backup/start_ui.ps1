# Start UI application for Credit Card Fraud Detection System
Write-Host "Starting Credit Card Fraud Detection UI Application..." -ForegroundColor Cyan

$pythonPath = "d:\Study\AILearning\shared_Environment\Scripts\python.exe"
$uiPath = "d:\Study\AILearning\MLProjects\creditcardfrauddetection\ui"

# Set the current directory to the UI path
Set-Location -Path $uiPath

# First try to check if API is running
Write-Host "Testing API connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -ErrorAction Stop
    if ($response.status -eq "ok") {
        Write-Host "API server is running and ready!" -ForegroundColor Green
    }
} catch {
    Write-Host "Warning: Could not connect to API server at http://localhost:8000" -ForegroundColor Red
    Write-Host "The UI will still run, but will use mock data instead of real API data." -ForegroundColor Yellow
    Write-Host "Make sure to start the API server using start_api.ps1 in another terminal." -ForegroundColor Yellow
}

# Start the UI application
Write-Host "Running UI application on http://localhost:8501" -ForegroundColor Green
& $pythonPath -m streamlit run app.py

@echo off
:: Credit Card Fraud Detection System - Launch Script
:: This script starts both the API server and the UI

echo Starting Credit Card Fraud Detection System...

:: Set path to Python executable in the shared environment
set PYTHON_CMD=d:\Study\AILearning\shared_Environment\Scripts\python.exe
set BASE_DIR=d:\Study\AILearning\MLProjects\creditcardfrauddetection

:: Start API server in a new window
echo Starting API server...
start "Credit Card Fraud Detection API" cmd /c "cd /d %BASE_DIR% && %PYTHON_CMD% run_server.py"

:: Wait for API to initialize and check health
echo Waiting for API to initialize...
timeout /t 3 /nobreak

:: Use PowerShell to check API health with retry
powershell -Command "& {
    $maxRetries = 5;
    $retryCount = 0;
    $success = $false;
    while (-not $success -and $retryCount -lt $maxRetries) {
        try {
            $response = Invoke-RestMethod -Uri 'http://localhost:8000/health' -Method Get -ErrorAction Stop;
            if ($response.status -eq 'ok') {
                Write-Host 'API server is up and running!';
                $success = $true;
            }
        } catch {
            $retryCount++;
            Write-Host ('API server not ready yet. Retrying... Attempt ' + $retryCount + ' of ' + $maxRetries);
            Start-Sleep -Seconds 2;
        }
    }
    if (-not $success) {
        Write-Host 'Failed to connect to API server after multiple attempts.' -ForegroundColor Red;
        exit 1;
    }
}"

:: Start UI in a new window
echo Starting UI...
start "Credit Card Fraud Detection UI" cmd /c "cd /d %BASE_DIR%\ui && %PYTHON_CMD% -m streamlit run app.py"

echo.
echo =====================================================================
echo Credit Card Fraud Detection System started successfully!
echo.
echo API server: http://localhost:8000
echo UI:         http://localhost:8501
echo.
echo API Documentation: http://localhost:8000/docs
echo =====================================================================

@echo off
:: Credit Card Fraud Detection System - Stop Script
:: This script stops all Python processes related to the fraud detection system

echo Stopping Credit Card Fraud Detection System...

:: First try to gracefully stop streamlit
powershell -Command "& {
    $streamlitProcesses = Get-Process -Name python | Where-Object { $_.CommandLine -like '*streamlit*' };
    if ($streamlitProcesses) {
        foreach ($process in $streamlitProcesses) {
            Write-Host ('Stopping Streamlit process (PID: ' + $process.Id + ')');
            Stop-Process -Id $process.Id -Force;
        }
    } else {
        Write-Host 'No Streamlit processes found.';
    }
}"

:: Then stop any Python processes that might be running the API server
powershell -Command "& {
    $apiProcesses = Get-Process -Name python | Where-Object { $_.CommandLine -like '*run_server.py*' -or $_.CommandLine -like '*uvicorn*' };
    if ($apiProcesses) {
        foreach ($process in $apiProcesses) {
            Write-Host ('Stopping API server process (PID: ' + $process.Id + ')');
            Stop-Process -Id $process.Id -Force;
        }
    } else {
        Write-Host 'No API server processes found.';
    }
}"

echo Credit Card Fraud Detection System has been stopped.

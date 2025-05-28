@echo off
echo Starting Credit Card Fraud Detection API and Tests...
echo.

set PYTHON_PATH=d:\Study\AILearning\shared_Environment\Scripts\python.exe
set PROJECT_PATH=d:\Study\AILearning\MLProjects\creditcardfrauddetection

cd %PROJECT_PATH%

echo Starting API server...
start cmd /k "%PYTHON_PATH% run_server.py"

echo Waiting for server to initialize...
timeout /t 5

echo Running API tests...
%PYTHON_PATH% ui\api_test.py

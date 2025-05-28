# Start the Credit Card Fraud Detection System
# This script starts both the API server and the Streamlit UI

# First, start the API server in the background
Write-Host "Starting API server in the background..."
$apiProcess = Start-Process -FilePath "python" -ArgumentList "run_server.py" -PassThru -NoNewWindow

# Wait a moment for the API server to initialize
Write-Host "Waiting for API server to initialize..."
Start-Sleep -Seconds 5

# Then start the Streamlit UI
Write-Host "Starting Streamlit UI..."
Write-Host "You can access the UI at http://localhost:8501"
Write-Host "Press Ctrl+C to stop the UI (you'll need to manually kill the API server after)"
streamlit run ui\app.py

# Optional: If the UI is closed, also stop the API server
# Stop-Process -Id $apiProcess.Id -Force

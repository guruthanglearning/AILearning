# Running the Credit Card Fraud Detection System

This document provides instructions on how to run the Credit Card Fraud Detection system.

## Option 1: Running the Complete System (Recommended)

The easiest way to run the entire system is using the single startup script:

```powershell
# Navigate to project directory
cd d:\Study\AILearning\MLProjects\creditcardfrauddetection

# Start both API and UI with one command
.\start_system.ps1
```

This script will:
- Start the API server in the background
- Wait for the API to initialize
- Start the UI application
- Open the UI in your default browser

## Option 2: Running Components Separately

If you prefer to run and monitor the components separately:

### Step 1: Start the API Server

1. Open a new PowerShell window
2. Run these commands:
   ```powershell
   # Navigate to project directory
   cd d:\Study\AILearning\MLProjects\creditcardfrauddetection
   
   # Start the API server
   .\start_api.ps1
   ```
3. Wait until you see messages indicating the API server has started successfully
   - You should see something like "Application startup complete" in the output
   - The API will be running at http://localhost:8000

### Step 2: Start the UI Application

1. Open a second PowerShell window (keep the first one running with the API server)
2. Run these commands:
   ```powershell
   # Navigate to project directory
   cd d:\Study\AILearning\MLProjects\creditcardfrauddetection
   
   # Start the Streamlit UI
   .\run_ui_fixed.ps1
   ```
3. Wait for the UI to initialize
   - A browser tab should open automatically at http://localhost:8501 with the UI

## Testing the System

After starting the system, you can:

1. Navigate to "Fraud Patterns" from the sidebar menu
2. Add a new fraud pattern using the form
3. View and edit existing patterns
4. Process transactions in the Transaction Analysis section

### Verify API Connection

To verify the connection between UI and API:
```powershell
# Navigate to project directory
cd d:\Study\AILearning\MLProjects\creditcardfrauddetection

# Run the API test script
python ui\api_test.py
```

## Troubleshooting

- If the UI shows "Could not connect to API" warning:
  - Make sure the API server is running
  - Check that no firewall is blocking the connection
  - Verify the API is running on port 8000

- If you need to stop the system:
  - Press Ctrl+C in the PowerShell window
  - Close the browser tab with the UI

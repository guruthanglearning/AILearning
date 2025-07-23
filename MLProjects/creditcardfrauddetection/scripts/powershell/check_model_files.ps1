# Check ML Model Files for Fraud Detection System
# This script runs the model file checking utility in a user-friendly manner
# Created: June 11, 2025

# Get the script's directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)  # Go up two levels

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "       MODEL FILE VERIFICATION UTILITY            " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Set Python path to include the project
$env:PYTHONPATH = $projectRoot

# Run the model checker script
try {
    # Change to project root to ensure proper path resolution
    Set-Location -Path $projectRoot
    
    Write-Host "Checking model files for the fraud detection system..." -ForegroundColor Yellow
    python -m scripts.utility.check_model_files
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nSome model files are missing or invalid!" -ForegroundColor Red
        Write-Host "Would you like to download the model files? (y/n)" -ForegroundColor Yellow
        $response = Read-Host
        
        if ($response -eq "y") {
            Write-Host "`nDownloading model files..." -ForegroundColor Yellow
            python -m scripts.manage_models --action download --output-dir data/models
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "`nVerifying downloaded model files..." -ForegroundColor Yellow
                python -m scripts.utility.check_model_files
            }
        }
    }
} catch {
    Write-Host "Error running model verification: $_" -ForegroundColor Red
}

# Keep window open if run directly
if ($MyInvocation.Line -eq "") {
    Write-Host "`nPress any key to continue..." -ForegroundColor Cyan
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

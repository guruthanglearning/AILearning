# Clean up redundant files in the Credit Card Fraud Detection project
# Created on: May 27, 2025

Write-Host "Starting cleanup of redundant script files..." -ForegroundColor Cyan

# Define the project root directory
$projectRoot = "d:\Study\AILearning\MLProjects\creditcardfrauddetection"

# Create a backup directory
$backupDir = Join-Path $projectRoot "redundant_scripts_backup"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Write-Host "Created backup directory: $backupDir" -ForegroundColor Green
}

# Function to move a file to backup instead of deleting it
function Backup-File {
    param($filePath)
    
    if (Test-Path $filePath) {
        $fileName = Split-Path $filePath -Leaf
        $destPath = Join-Path $backupDir $fileName
        
        # If a file with the same name exists in backup, add a timestamp
        if (Test-Path $destPath) {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $destPath = Join-Path $backupDir "$($fileName).$timestamp"
        }
        
        Move-Item -Path $filePath -Destination $destPath -Force
        Write-Host "Moved to backup: $fileName" -ForegroundColor Yellow
    } else {
        Write-Host "File not found: $filePath" -ForegroundColor Red
    }
}

# List of redundant files to move to backup
$redundantFiles = @(
    # Redundant UI startup scripts
    "start_ui.bat",
    
    # Redundant API scripts
    "start_api_and_test.bat",
    
    # Redundant system scripts
    "start_system.bat",
    
    # Redundant test scripts
    "run_api_and_tests.ps1",
    "test_api.ps1",
    "start_and_test_api.ps1",
    "start_and_test_api.py",
    
    # Script used for fixing indentation (no longer needed)
    "fix_indentation.py"
)

# Process each redundant file
foreach ($file in $redundantFiles) {
    $filePath = Join-Path $projectRoot $file
    Backup-File $filePath
}

# Clean up redundant scripts in the scripts directory
$redundantScriptsDir = @(
    "scripts/verify_env.py",
    "scripts/check_environment.py",
    "scripts/run_with_shared_env.py",
    "scripts/run_verify.bat",
    "scripts/verify_simple.py"
)

foreach ($script in $redundantScriptsDir) {
    $scriptPath = Join-Path $projectRoot $script
    Backup-File $scriptPath
}

Write-Host "`nCleanup complete!" -ForegroundColor Green
Write-Host "All redundant files have been moved to: $backupDir" -ForegroundColor Green
Write-Host "The following scripts remain for operating the system:" -ForegroundColor Cyan
Write-Host "  - start_system.ps1     (Start both API and UI)" -ForegroundColor White
Write-Host "  - start_api.ps1        (Start API only)" -ForegroundColor White
Write-Host "  - run_ui_fixed.ps1     (Start UI only)" -ForegroundColor White
Write-Host "  - run_tests.py         (Run all tests)" -ForegroundColor White

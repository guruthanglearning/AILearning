# Comprehensive Project Cleanup Script
# Created: June 18, 2025
# Purpose: Execute comprehensive cleanup of the Credit Card Fraud Detection project

param(
    [switch]$Live,
    [switch]$DryRun = $true,
    [string]$ProjectRoot = $PSScriptRoot
)

# Set project root to the correct location
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "Credit Card Fraud Detection - Comprehensive Cleanup" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python not found. Please ensure Python is installed and in PATH." -ForegroundColor Red
    exit 1
}

# Determine execution mode
if ($Live) {
    $mode = "--live"
    $modeText = "LIVE MODE - Changes will be made"
    $color = "Yellow"
} else {
    $mode = ""
    $modeText = "DRY RUN MODE - No changes will be made"
    $color = "Green"
}

Write-Host $modeText -ForegroundColor $color
Write-Host "Project root: $ProjectRoot" -ForegroundColor Cyan
Write-Host ""

# Confirm execution
if ($Live) {
    $confirm = Read-Host "Are you sure you want to proceed with live cleanup? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "Cleanup cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Execute the cleanup script
Write-Host "Starting cleanup process..." -ForegroundColor Cyan

try {
    $cleanupScript = Join-Path $ProjectRoot "scripts\utility\comprehensive_cleanup.py"
    
    if ($Live) {
        python $cleanupScript --live --project-root $ProjectRoot
    } else {
        python $cleanupScript --project-root $ProjectRoot
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Cleanup completed successfully!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Cleanup completed with errors. Check the output above." -ForegroundColor Yellow
    }
    
} catch {
    Write-Host ""
    Write-Host "Error executing cleanup script: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Review the cleanup report generated in the project root" -ForegroundColor White
Write-Host "2. Check the backup directory for any files that were moved/removed" -ForegroundColor White
Write-Host "3. Test the application to ensure everything still works correctly" -ForegroundColor White

if (-not $Live) {
    Write-Host ""
    Write-Host "To execute the cleanup for real, run:" -ForegroundColor Yellow
    Write-Host "  .\scripts\powershell\comprehensive_cleanup.ps1 -Live" -ForegroundColor White
}

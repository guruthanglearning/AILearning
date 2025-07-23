# Simple launcher for the Credit Card Fraud Detection System
# This script forwards to the main launcher in the scripts/powershell directory

# Get the script's directory (project root)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Call the main launcher script
& "$scriptDir\scripts\powershell\launch_system.ps1"

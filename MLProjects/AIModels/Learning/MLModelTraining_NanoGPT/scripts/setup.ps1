# Build and Setup Script for NanoGPT Training
# This script builds the solution, downloads data, and sets up the environment

param(
    [switch]$SkipData,
    [switch]$Clean
)

Write-Host "NanoGPT Setup Script"
Write-Host "==================="

# Navigate to project root
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot

if ($Clean) {
    Write-Host "Cleaning solution..."
    dotnet clean
    if (Test-Path "bin") { Remove-Item -Recurse -Force "bin" }
    if (Test-Path "obj") { Remove-Item -Recurse -Force "obj" }
}

# Restore and build solution
Write-Host "Restoring packages..."
dotnet restore

Write-Host "Building solution..."
$buildResult = dotnet build --configuration Release
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed!"
    exit 1
}

Write-Host "Build completed successfully!"

# Download data if not skipped
if (-not $SkipData) {
    Write-Host "`nSetting up training data..."
    & "$PSScriptRoot/download_data.ps1"
}

# Create required directories
$directories = @("checkpoints", "logs")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created directory: $dir"
    }
}

Write-Host "`nSetup completed successfully!"
Write-Host "To start training, run:"
Write-Host "  dotnet run --project NanoGpt.Training --configuration Release"
Write-Host ""
Write-Host "To run with custom config:"
Write-Host "  dotnet run --project NanoGpt.Training --configuration Release -- custom_config.json"
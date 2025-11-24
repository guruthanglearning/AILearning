#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build and deployment script for NanoGPT project

.DESCRIPTION
    This script builds the entire NanoGPT solution, runs tests, and prepares for deployment

.PARAMETER Mode
    The build mode: Debug or Release (default: Release)

.PARAMETER SkipTests
    Skip running unit and integration tests

.PARAMETER Deploy
    Deploy to Docker after successful build

.EXAMPLE
    .\build.ps1 -Mode Release -Deploy
#>

param(
    [Parameter()]
    [ValidateSet("Debug", "Release")]
    [string]$Mode = "Release",
    
    [Parameter()]
    [switch]$SkipTests,
    
    [Parameter()]
    [switch]$Deploy
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

Write-Host "🚀 Starting NanoGPT Build Process" -ForegroundColor Green
Write-Host "Build Mode: $Mode" -ForegroundColor Yellow
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Yellow

try {
    # Step 1: Clean previous builds
    Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Cyan
    dotnet clean "$ProjectRoot\NanoGpt.sln" --configuration $Mode --verbosity minimal
    
    if (Test-Path "$ProjectRoot\bin") {
        Remove-Item "$ProjectRoot\bin" -Recurse -Force
    }
    
    if (Test-Path "$ProjectRoot\obj") {
        Remove-Item "$ProjectRoot\obj" -Recurse -Force
    }

    # Step 2: Restore dependencies
    Write-Host "📦 Restoring NuGet packages..." -ForegroundColor Cyan
    dotnet restore "$ProjectRoot\NanoGpt.sln" --verbosity minimal

    # Step 3: Build solution
    Write-Host "🔨 Building solution..." -ForegroundColor Cyan
    dotnet build "$ProjectRoot\NanoGpt.sln" --configuration $Mode --no-restore --verbosity minimal

    # Step 4: Run tests (unless skipped)
    if (-not $SkipTests) {
        Write-Host "🧪 Running unit tests..." -ForegroundColor Cyan
        dotnet test "$ProjectRoot\NanoGpt.Tests.Unit\NanoGpt.Tests.Unit.csproj" --configuration $Mode --no-build --verbosity minimal --logger "console;verbosity=normal"
        
        Write-Host "🧪 Running integration tests..." -ForegroundColor Cyan
        dotnet test "$ProjectRoot\NanoGpt.Tests.Integration\NanoGpt.Tests.Integration.csproj" --configuration $Mode --no-build --verbosity minimal --logger "console;verbosity=normal"
    }

    # Step 5: Publish API
    Write-Host "📋 Publishing API..." -ForegroundColor Cyan
    dotnet publish "$ProjectRoot\NanoGpt.Api\NanoGpt.Api.csproj" --configuration $Mode --no-build --output "$ProjectRoot\publish\api"

    # Step 6: Publish Training Console
    Write-Host "📋 Publishing Training Console..." -ForegroundColor Cyan
    dotnet publish "$ProjectRoot\NanoGpt.Training\NanoGpt.Training.csproj" --configuration $Mode --no-build --output "$ProjectRoot\publish\training"

    # Step 7: Copy configuration and data files
    Write-Host "📄 Copying configuration files..." -ForegroundColor Cyan
    Copy-Item "$ProjectRoot\config.json" "$ProjectRoot\publish\api\" -Force
    Copy-Item "$ProjectRoot\config.json" "$ProjectRoot\publish\training\" -Force
    
    if (Test-Path "$ProjectRoot\data") {
        Copy-Item "$ProjectRoot\data" "$ProjectRoot\publish\" -Recurse -Force
    }

    # Step 8: Generate version info
    $Version = "1.0.0"
    $BuildTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss UTC"
    $VersionInfo = @{
        Version = $Version
        BuildTime = $BuildTime
        BuildMode = $Mode
        GitCommit = if (Get-Command git -ErrorAction SilentlyContinue) { 
            try { git rev-parse --short HEAD } catch { "unknown" } 
        } else { "unknown" }
    }
    
    $VersionInfo | ConvertTo-Json | Out-File "$ProjectRoot\publish\version.json"

    Write-Host "✅ Build completed successfully!" -ForegroundColor Green
    
    # Step 9: Docker deployment (if requested)
    if ($Deploy) {
        Write-Host "🐳 Building Docker image..." -ForegroundColor Cyan
        docker build -t nanogpt:latest -t "nanogpt:$Version" .
        
        Write-Host "🐳 Starting Docker containers..." -ForegroundColor Cyan
        docker-compose up -d
        
        Write-Host "✅ Deployment completed!" -ForegroundColor Green
        Write-Host "🌐 API available at: http://localhost:8080/swagger" -ForegroundColor Yellow
        Write-Host "📊 Dashboard available at: http://localhost:3000" -ForegroundColor Yellow
        Write-Host "📈 Grafana available at: http://localhost:3001 (admin/admin123)" -ForegroundColor Yellow
    }
    
    Write-Host "🎉 All tasks completed successfully!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Build failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
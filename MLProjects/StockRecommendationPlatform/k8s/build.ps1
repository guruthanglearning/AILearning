# Build Docker images for Kubernetes deployment.
# Run from the StockRecommendationPlatform directory.
# Usage: .\k8s\build.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "==> Building backend image: stockresearch-backend:latest"
docker build -t stockresearch-backend:latest "$ProjectRoot"

Write-Host "==> Building frontend image: stockresearch-frontend:k8s (NEXT_PUBLIC_API_URL=http://api.stockresearch.local)"
docker build `
  --build-arg NEXT_PUBLIC_API_URL=http://api.stockresearch.local `
  -t stockresearch-frontend:k8s `
  "$ProjectRoot\frontend"

Write-Host ""
Write-Host "Images built:"
docker images --filter "reference=stockresearch-*" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

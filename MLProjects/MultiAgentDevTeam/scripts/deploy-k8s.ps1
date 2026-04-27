<#
.SYNOPSIS
    Deploy the Multi-Agent Dev Team (API + UI) to a local Kubernetes cluster (Docker Desktop).

.PARAMETER ApiKey
    Anthropic API key. Falls back to ANTHROPIC_API_KEY environment variable.

.PARAMETER Down
    Remove all Kubernetes resources (delete the namespace).

.PARAMETER SkipBuild
    Skip rebuilding Docker images (use existing images).

.EXAMPLE
    .\deploy-k8s.ps1 -ApiKey "sk-ant-xxxx"
    .\deploy-k8s.ps1 -SkipBuild
    .\deploy-k8s.ps1 -Down
#>

param(
    [string]$ApiKey = $env:ANTHROPIC_API_KEY,
    [switch]$Down,
    [switch]$SkipBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root      = Split-Path -Parent $PSScriptRoot
$K8sDir    = Join-Path $Root "k8s"
$DockerDir = Join-Path $Root "docker"
$Namespace = "multi-agent-dev-team"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Multi-Agent Dev Team - Kubernetes Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Tear down
if ($Down) {
    Write-Host "`nRemoving Kubernetes namespace '$Namespace'..." -ForegroundColor Yellow
    kubectl delete namespace $Namespace --ignore-not-found
    Write-Host "Namespace removed." -ForegroundColor Green
    exit 0
}

# Validate prerequisites
Write-Host "`n[0/8] Validating prerequisites..." -ForegroundColor Yellow

kubectl cluster-info 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "kubectl cannot reach a cluster. Ensure Docker Desktop Kubernetes is enabled."
    exit 1
}
Write-Host "Kubernetes cluster reachable." -ForegroundColor Green

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    Write-Error "ANTHROPIC_API_KEY is required. Set the environment variable or pass -ApiKey."
    exit 1
}

# Step 1: Build Orchestrator image
if (-not $SkipBuild) {
    Write-Host "`n[1/8] Building Orchestrator Docker image..." -ForegroundColor Yellow
    docker build -f "$DockerDir\Dockerfile" -t multi-agent-dev-team:latest $Root
    if ($LASTEXITCODE -ne 0) { Write-Error "Orchestrator Docker build failed."; exit 1 }
    Write-Host "Orchestrator image built." -ForegroundColor Green
} else {
    Write-Host "`n[1/8] Skipping Orchestrator image build (-SkipBuild)" -ForegroundColor DarkYellow
}

# Step 2: Build UI image
if (-not $SkipBuild) {
    Write-Host "`n[2/8] Building UI Docker image..." -ForegroundColor Yellow
    docker build -f "$DockerDir\Dockerfile.ui" -t multi-agent-dev-team-ui:latest $Root
    if ($LASTEXITCODE -ne 0) { Write-Error "UI Docker build failed."; exit 1 }
    Write-Host "UI image built." -ForegroundColor Green
} else {
    Write-Host "`n[2/8] Skipping UI image build (-SkipBuild)" -ForegroundColor DarkYellow
}

# Step 3: Namespace
Write-Host "`n[3/8] Creating namespace..." -ForegroundColor Yellow
kubectl apply -f "$K8sDir\namespace.yaml"

# Step 4: Secret
Write-Host "`n[4/8] Creating secret..." -ForegroundColor Yellow
kubectl create secret generic agent-secrets `
    --from-literal=ANTHROPIC_API_KEY=$ApiKey `
    -n $Namespace `
    --dry-run=client -o yaml | kubectl apply -f -
Write-Host "Secret applied." -ForegroundColor Green

# Step 5: ConfigMap
Write-Host "`n[5/8] Applying ConfigMap..." -ForegroundColor Yellow
kubectl apply -f "$K8sDir\configmap.yaml"

# Step 6: Orchestrator Deployment + Service
Write-Host "`n[6/8] Applying Orchestrator Deployment and Service..." -ForegroundColor Yellow
kubectl apply -f "$K8sDir\deployment.yaml"
kubectl apply -f "$K8sDir\service.yaml"

# Step 7: UI Deployment + Service
Write-Host "`n[7/8] Applying UI Deployment and Service..." -ForegroundColor Yellow
kubectl apply -f "$K8sDir\deployment-ui.yaml"
kubectl apply -f "$K8sDir\service-ui.yaml"

# Step 8: Wait for pod readiness
Write-Host "`n[8/8] Waiting for pods to be ready..." -ForegroundColor Yellow
kubectl rollout status deployment/orchestrator -n $Namespace --timeout=120s
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Orchestrator rollout timed out. Check: kubectl get pods -n $Namespace"
} else {
    Write-Host "  Orchestrator pod is ready!" -ForegroundColor Green
}

kubectl rollout status deployment/ui -n $Namespace --timeout=60s
if ($LASTEXITCODE -ne 0) {
    Write-Warning "UI rollout timed out. Check: kubectl get pods -n $Namespace"
} else {
    Write-Host "  UI pod is ready!" -ForegroundColor Green
}

# Summary
Write-Host "`n================================================" -ForegroundColor Green
Write-Host "  Deployment complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "  UI          : http://localhost:30000" -ForegroundColor Cyan
Write-Host "  API (Swagger): http://localhost:30080" -ForegroundColor Cyan
Write-Host "  Health      : http://localhost:30080/health" -ForegroundColor Cyan
Write-Host "`nUseful commands:" -ForegroundColor Gray
Write-Host "  kubectl get pods -n $Namespace" -ForegroundColor Gray
Write-Host "  kubectl logs -f deployment/orchestrator -n $Namespace" -ForegroundColor Gray
Write-Host "  kubectl logs -f deployment/ui -n $Namespace" -ForegroundColor Gray
Write-Host "  kubectl scale deployment/orchestrator --replicas=2 -n $Namespace" -ForegroundColor Gray
Write-Host "  .\deploy-k8s.ps1 -Down   # tear everything down" -ForegroundColor Gray

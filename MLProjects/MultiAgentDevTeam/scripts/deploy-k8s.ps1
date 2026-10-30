<#
.SYNOPSIS
    Deploy the Multi-Agent Dev Team (API + UI) to a local Kubernetes cluster (Docker Desktop).

.PARAMETER ApiKey
    Anthropic API key. Optional: if omitted, the key comes from the ANTHROPIC_API_KEY
    environment variable, then src/MultiAgentDevTeam.Orchestrator/appsettings.secrets.json,
    then a masked prompt (see scripts/Resolve-AnthropicApiKey.ps1). Passing it here saves
    it in your shell history, so prefer the other sources.
    If no key is found but the cluster already has the agent-secrets Secret, it is reused.

.PARAMETER Down
    Remove all Kubernetes resources (delete the namespace).

.PARAMETER SkipBuild
    Skip rebuilding Docker images (use existing images).

.EXAMPLE
    .\deploy-k8s.ps1
    .\deploy-k8s.ps1 -SkipBuild
    .\deploy-k8s.ps1 -Down
#>

param(
    [string]$ApiKey,
    [switch]$Down,
    [switch]$SkipBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "Resolve-AnthropicApiKey.ps1")

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

# Resolve the API key before building anything, so a missing key fails fast
$resolvedKey = Resolve-AnthropicApiKey -ApiKey $ApiKey -AllowMissing
if (-not $resolvedKey) {
    # Stderr from a native command is a terminating error under "Stop" in Windows PowerShell
    $secretExists = & { $ErrorActionPreference = 'Continue'; kubectl get secret agent-secrets -n $Namespace -o name 2>$null; $LASTEXITCODE -eq 0 }
    if (-not ($secretExists | Select-Object -Last 1)) {
        # Nothing to reuse either; let the resolver raise its full "how to provide a key" error
        $null = Resolve-AnthropicApiKey -NonInteractive
    }
    Write-Warning "No API key found; reusing the existing 'agent-secrets' Secret in the cluster."
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
if ($resolvedKey) {
    Write-Host "`n[4/8] Applying secret..." -ForegroundColor Yellow
    Set-KubernetesApiKeySecret -Key $resolvedKey -Namespace $Namespace
    Write-Host "Secret applied." -ForegroundColor Green
} else {
    Write-Host "`n[4/8] Keeping existing secret" -ForegroundColor DarkYellow
}

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

# Step 8: Restart pods and wait for readiness. Pods read the Secret and the :latest image
# only at startup, so without a restart a rotated key or rebuilt image is never picked up.
Write-Host "`n[8/8] Restarting pods and waiting for them to be ready..." -ForegroundColor Yellow
kubectl rollout restart deployment/orchestrator deployment/ui -n $Namespace
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

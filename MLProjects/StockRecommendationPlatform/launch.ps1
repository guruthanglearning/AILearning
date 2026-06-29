param(
    [int]$BackendPort  = 8024,
    [int]$FrontendPort = 3001
)

$Root     = $PSScriptRoot
$Python   = "D:\Study\AILearning\shared_Environment\Scripts\python.exe"
$Edge     = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$EnvLocal = "$Root\frontend\.env.local"

function Is-PortListening {
    param([int]$Port)
    $null -ne (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-ForPort {
    param([int]$Port, [int]$TimeoutSec = 30)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:$Port" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -lt 500) { return $true }
        } catch { }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

# Backend
if (Is-PortListening -Port $BackendPort) {
    Write-Host "[backend]  Already running on :$BackendPort" -ForegroundColor Green
} else {
    Write-Host "[backend]  Starting on :$BackendPort ..." -ForegroundColor Cyan
    $backendArgs = @{
        FilePath         = "cmd.exe"
        ArgumentList     = "/c `"$Python`" -m uvicorn app.main:app --host 0.0.0.0 --port $BackendPort"
        WorkingDirectory = $Root
        WindowStyle      = "Minimized"
    }
    Start-Process @backendArgs
    if (Wait-ForPort -Port $BackendPort -TimeoutSec 30) {
        Write-Host "[backend]  Ready on :$BackendPort" -ForegroundColor Green
    } else {
        Write-Warning "[backend]  Did not become ready within 30s."
    }
}

# Sync .env.local if port changed
$envContent = Get-Content $EnvLocal -Raw
$updated    = $envContent -replace "NEXT_PUBLIC_API_URL=http://localhost:\d+", "NEXT_PUBLIC_API_URL=http://localhost:$BackendPort"
if ($updated -ne $envContent) {
    Set-Content $EnvLocal $updated -NoNewline
    Write-Host "[env]      Updated .env.local NEXT_PUBLIC_API_URL -> :$BackendPort" -ForegroundColor Yellow
}

# Frontend
if (Is-PortListening -Port $FrontendPort) {
    Write-Host "[frontend] Already running on :$FrontendPort" -ForegroundColor Green
} else {
    Write-Host "[frontend] Starting on :$FrontendPort ..." -ForegroundColor Cyan
    $frontendArgs = @{
        FilePath         = "cmd.exe"
        ArgumentList     = "/c npm run dev -- --port $FrontendPort"
        WorkingDirectory = "$Root\frontend"
        WindowStyle      = "Minimized"
    }
    Start-Process @frontendArgs
    if (Wait-ForPort -Port $FrontendPort -TimeoutSec 60) {
        Write-Host "[frontend] Ready on :$FrontendPort" -ForegroundColor Green
    } else {
        Write-Warning "[frontend] Did not become ready within 60s."
    }
}

# Open Edge
Write-Host "[browser]  Opening http://localhost:$FrontendPort in Edge ..." -ForegroundColor Cyan
Start-Process -FilePath $Edge -ArgumentList "http://localhost:$FrontendPort"

Write-Host ""
Write-Host "StockResearch Platform is running." -ForegroundColor Green
Write-Host "  Backend  -> http://localhost:$BackendPort/docs"
Write-Host "  Frontend -> http://localhost:$FrontendPort"

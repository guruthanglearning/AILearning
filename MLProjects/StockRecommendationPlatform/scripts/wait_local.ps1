$timeout = 90
$elapsed = 0

Write-Host "Waiting for backend (http://localhost:8024)..."
while ($elapsed -lt $timeout) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8024/healthz" -UseBasicParsing -TimeoutSec 2
        Write-Host "Backend ready (HTTP $($r.StatusCode))"
        break
    } catch {
        Start-Sleep 2
        $elapsed += 2
    }
}
if ($elapsed -ge $timeout) { Write-Host "Backend timed out after ${timeout}s" }

$elapsed = 0
Write-Host "Waiting for frontend (http://localhost:3001)..."
while ($elapsed -lt $timeout) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:3001" -UseBasicParsing -TimeoutSec 2
        Write-Host "Frontend ready (HTTP $($r.StatusCode))"
        break
    } catch {
        Start-Sleep 2
        $elapsed += 2
    }
}
if ($elapsed -ge $timeout) {
    Write-Host "Frontend not on 3001, trying 3000..."
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2
        Write-Host "Frontend ready on port 3000 (HTTP $($r.StatusCode))"
    } catch { Write-Host "Frontend timed out" }
}

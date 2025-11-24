# Simple NanoGPT API Test
Write-Host "Testing NanoGPT Shakespeare API..." -ForegroundColor Green

# Test health
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8080/health" -Method GET
    Write-Host "API Health: $health" -ForegroundColor Green
}
catch {
    Write-Host "API Error: $($_.Exception.Message)" -ForegroundColor Red
    exit
}

# Test Shakespeare generation
Write-Host "Testing Hamlet prompt..." -ForegroundColor Yellow

$body = @{
    prompt = "HAMLET:"
    maxTokens = 100
    temperature = 0.7
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/api/generate" -Method POST -Body $body -ContentType "application/json"
    
    Write-Host "Generated Text:" -ForegroundColor Cyan
    Write-Host $response.generatedText -ForegroundColor White
    Write-Host "Token Count: $($response.tokenCount)" -ForegroundColor Gray
}
catch {
    Write-Host "Generation Error: $($_.Exception.Message)" -ForegroundColor Red
}
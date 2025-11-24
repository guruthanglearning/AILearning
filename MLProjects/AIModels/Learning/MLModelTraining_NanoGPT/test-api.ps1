# NanoGPT API Test Script
# Test your trained Shakespeare model with various prompts

Write-Host "🎭 NanoGPT Shakespeare Model API Tester" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# Function to test text generation
function Test-TextGeneration {
    param(
        [string]$Prompt,
        [int]$MaxTokens = 100,
        [double]$Temperature = 0.7,
        [string]$Description = ""
    )
    
    Write-Host "`n🎪 Testing: $Description" -ForegroundColor Yellow
    Write-Host "📝 Prompt: '$Prompt'" -ForegroundColor White
    
    try {
        $body = @{
            prompt = $Prompt
            maxTokens = $MaxTokens
            temperature = $Temperature
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "http://localhost:8080/api/generate" -Method POST -Body $body -ContentType "application/json"
        
        Write-Host "✅ Generated Text:" -ForegroundColor Green
        Write-Host $response.generatedText -ForegroundColor White
        Write-Host "📊 Tokens: $($response.tokenCount)" -ForegroundColor Gray
        Write-Host "⏱️ Time: $($response.completionTime)" -ForegroundColor Gray
    }
    catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test API health first
Write-Host "`n🔍 Checking API Health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8080/health" -Method GET
    Write-Host "✅ API Health: $health" -ForegroundColor Green
}
catch {
    Write-Host "❌ API not responding. Make sure Docker services are running." -ForegroundColor Red
    Write-Host "Run: docker-compose up -d" -ForegroundColor Yellow
    exit
}

# Test Shakespeare Character Dialogues
Test-TextGeneration -Prompt "HAMLET:" -MaxTokens 150 -Temperature 0.7 -Description "Hamlet's Soliloquy"
Test-TextGeneration -Prompt "ROMEO:" -MaxTokens 120 -Temperature 0.8 -Description "Romeo's Passion"
Test-TextGeneration -Prompt "JULIET:" -MaxTokens 100 -Temperature 0.6 -Description "Juliet's Words"
Test-TextGeneration -Prompt "MACBETH:" -MaxTokens 130 -Temperature 0.9 -Description "Macbeth's Ambition"

# Test Famous Shakespeare Lines
Test-TextGeneration -Prompt "To be or not to be" -MaxTokens 80 -Temperature 0.5 -Description "Famous Hamlet Quote"
Test-TextGeneration -Prompt "Romeo, Romeo" -MaxTokens 90 -Temperature 0.6 -Description "Juliet's Balcony Scene"

# Test Scene Directions
Test-TextGeneration -Prompt "Enter " -MaxTokens 50 -Temperature 0.7 -Description "Stage Direction"

# Test Different Temperature Settings
Write-Host "`n🌡️ Temperature Comparison for 'OTHELLO:'" -ForegroundColor Cyan
Test-TextGeneration -Prompt "OTHELLO:" -MaxTokens 80 -Temperature 0.3 -Description "Low Temperature (Conservative)"
Test-TextGeneration -Prompt "OTHELLO:" -MaxTokens 80 -Temperature 0.7 -Description "Medium Temperature (Balanced)"
Test-TextGeneration -Prompt "OTHELLO:" -MaxTokens 80 -Temperature 1.0 -Description "High Temperature (Creative)"

Write-Host "`n🎉 Testing Complete!" -ForegroundColor Green
Write-Host "💡 Tips:" -ForegroundColor Cyan
Write-Host "  - Lower temperature (0.3-0.5) = more predictable, coherent text" -ForegroundColor White
Write-Host "  - Higher temperature (0.8-1.0) = more creative, surprising text" -ForegroundColor White
Write-Host "  - Character names (HAMLET:, ROMEO:) should trigger dialogue responses" -ForegroundColor White
Write-Host "  - Famous quotes should continue naturally" -ForegroundColor White
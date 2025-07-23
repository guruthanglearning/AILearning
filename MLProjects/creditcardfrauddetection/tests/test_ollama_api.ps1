# Test Ollama API Connectivity (both local and online)
# This script runs the test_ollama_api.py script and summarizes the results
# Usage: .\test_ollama_api.ps1

Write-Host "`n==============================================" -ForegroundColor Cyan
Write-Host "    OLLAMA API CONNECTIVITY TEST SCRIPT" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "Testing connectivity to both local and online Ollama APIs..." -ForegroundColor White
Write-Host "This may take a minute depending on your network connection.`n" -ForegroundColor White

# Run the Python test script
try {
    python test_ollama_api.py
    
    Write-Host "`n==============================================" -ForegroundColor Cyan
    Write-Host "    NEXT STEPS" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "1. If local Ollama is not available, you can:" -ForegroundColor White
    Write-Host "   - Install Ollama from https://ollama.ai/download" -ForegroundColor White
    Write-Host "   - Or ensure online Ollama API is correctly configured" -ForegroundColor White
    Write-Host "`n2. If online Ollama API is not available, check:" -ForegroundColor White
    Write-Host "   - Your internet connection" -ForegroundColor White
    Write-Host "   - The API URL format in .env" -ForegroundColor White
    Write-Host "   - Your API key's validity" -ForegroundColor White
    Write-Host "   - The cloud provider's service status" -ForegroundColor White
    
    Write-Host "`n3. For additional Ollama cloud providers, see:" -ForegroundColor White
    Write-Host "   - Ollama Cloud (https://ollama.cloud)" -ForegroundColor White
    Write-Host "   - RunPod (https://www.runpod.io)" -ForegroundColor White
    Write-Host "   - Replicate (https://replicate.com)" -ForegroundColor White

    Write-Host "`nFor more information, check the README.md section on Online Ollama API Services." -ForegroundColor White
}
catch {
    Write-Host "Error running test script: $_" -ForegroundColor Red
}

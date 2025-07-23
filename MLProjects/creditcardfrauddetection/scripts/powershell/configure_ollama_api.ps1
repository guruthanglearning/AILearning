# Configure Online Ollama API Settings
# This script runs the interactive configuration wizard for setting up online Ollama API
# Usage: .\configure_ollama_api.ps1

Write-Host "`n==============================================" -ForegroundColor Green
Write-Host "    ONLINE OLLAMA API CONFIGURATION WIZARD" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host "This wizard will help you set up and test your online Ollama API connection.`n" -ForegroundColor White

# Run the Python configuration script
try {
    $projectRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
    python "$projectRoot\scripts\utility\configure_ollama_api.py"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n==============================================" -ForegroundColor Green
        Write-Host "    CONFIGURATION COMPLETE" -ForegroundColor Green
        Write-Host "==============================================" -ForegroundColor Green
        Write-Host "You can verify your configuration by running:" -ForegroundColor White
        Write-Host "    .\test_ollama_api.ps1" -ForegroundColor Cyan
        Write-Host "`nFor more information about online Ollama services," -ForegroundColor White
        Write-Host "check the README.md section on Online Ollama API Services." -ForegroundColor White
    }
}
catch {
    Write-Host "Error running configuration script: $_" -ForegroundColor Red
    Write-Host "Please make sure you have the required Python libraries installed:" -ForegroundColor Yellow
    Write-Host "    pip install python-dotenv requests" -ForegroundColor White
}

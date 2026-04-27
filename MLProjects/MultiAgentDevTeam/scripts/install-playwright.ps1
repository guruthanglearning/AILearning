# Run this once after building to install Playwright browsers
$testBin = "tests\MultiAgentDevTeam.BlazorUI.E2ETests\bin\Debug\net10.0"
$playwrightScript = Join-Path $testBin "playwright.ps1"

if (Test-Path $playwrightScript) {
    & pwsh $playwrightScript install
} else {
    Write-Error "Build the E2E tests first: dotnet build tests/MultiAgentDevTeam.BlazorUI.E2ETests/"
}

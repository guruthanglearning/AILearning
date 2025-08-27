# Interactive PowerShell script for testing MCP Stock Server
# Usage: .\run_stock_tests.ps1

function Show-Menu {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "MCP Stock Server Interactive Test" -ForegroundColor Cyan  
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available Options:" -ForegroundColor Yellow
    Write-Host "   1. Get Stock Price" -ForegroundColor White
    Write-Host "   2. Get Stock Info" -ForegroundColor White
    Write-Host "   3. Get Stock History" -ForegroundColor White
    Write-Host "   4. Run Example Tests" -ForegroundColor White
    Write-Host "   5. Exit" -ForegroundColor White
    Write-Host ""
}

function Get-UserChoice {
    do {
        $choice = Read-Host "Select an option (1-5)"
        if ($choice -match '^[1-5]$') {
            return $choice
        }
        Write-Host "ERROR: Invalid choice. Please enter 1, 2, 3, 4, or 5." -ForegroundColor Red
    } while ($true)
}

function Get-StockSymbol {
    do {
        $symbol = Read-Host "Enter stock symbol (e.g., AAPL, GOOGL, MSFT)"
        if ($symbol -match '^[A-Za-z]{1,5}$') {
            return $symbol.ToUpper()
        }
        Write-Host "ERROR: Invalid symbol. Please enter 1-5 letters only." -ForegroundColor Red
    } while ($true)
}

function Get-TimePeriod {
    Write-Host ""
    Write-Host "Available time periods:" -ForegroundColor Yellow
    Write-Host "   1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max" -ForegroundColor Gray
    
    do {
        $period = Read-Host "Enter time period (default: 1mo)"
        if ([string]::IsNullOrEmpty($period)) {
            return "1mo"
        }
        if ($period -match '^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$') {
            return $period
        }
        Write-Host "Invalid period. Please use one of the listed options." -ForegroundColor Red
    } while ($true)
}

function Execute-StockCommand {
    param(
        [string]$Option,
        [string]$Symbol,
        [string]$Period = ""
    )
    
    $pythonPath = "D:\Study\AILearning\shared_Environment\Scripts\python.exe"
    $scriptPath = "test_stock_client_args.py"
    
    Write-Host ""
    Write-Host "Executing command..." -ForegroundColor Yellow
    
    if ($Option -eq "3" -and $Period) {
        $command = "& `"$pythonPath`" `"$scriptPath`" --option $Option --symbol $Symbol --period $Period"
        Write-Host "Command: $scriptPath --option $Option --symbol $Symbol --period $Period" -ForegroundColor Gray
        & $pythonPath $scriptPath --option $Option --symbol $Symbol --period $Period
    } else {
        $command = "& `"$pythonPath`" `"$scriptPath`" --option $Option --symbol $Symbol"
        Write-Host "Command: $scriptPath --option $Option --symbol $Symbol" -ForegroundColor Gray
        & $pythonPath $scriptPath --option $Option --symbol $Symbol
    }
    
    Write-Host ""
    Write-Host "SUCCESS: Command completed!" -ForegroundColor Green
}

function Run-ExampleTests {
    Write-Host ""
    Write-Host "Running example tests..." -ForegroundColor Yellow
    Write-Host ""
    
    $pythonPath = "D:\Study\AILearning\shared_Environment\Scripts\python.exe"
    $scriptPath = "test_stock_client_args.py"

    # Test 1: Stock Price
    Write-Host "1. Testing AAPL Stock Price..." -ForegroundColor Yellow
    Write-Host "Command: $scriptPath --option 1 --symbol AAPL" -ForegroundColor Gray
    & $pythonPath $scriptPath --option 1 --symbol AAPL
    Write-Host ""

    # Test 2: Stock Info  
    Write-Host "2. Testing GOOGL Stock Info..." -ForegroundColor Yellow
    Write-Host "Command: $scriptPath --option 2 --symbol GOOGL" -ForegroundColor Gray
    & $pythonPath $scriptPath --option 2 --symbol GOOGL
    Write-Host ""

    # Test 3: Stock History
    Write-Host "3. Testing MSFT Stock History (1 year)..." -ForegroundColor Yellow
    Write-Host "Command: $scriptPath --option 3 --symbol MSFT --period 1y" -ForegroundColor Gray
    & $pythonPath $scriptPath --option 3 --symbol MSFT --period 1y
    Write-Host ""

    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS: All example tests completed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
}

# Main execution loop
do {
    Show-Menu
    $userChoice = Get-UserChoice
    
    switch ($userChoice) {
        "1" {
            Write-Host ""
            Write-Host "Get Stock Price" -ForegroundColor Cyan
            $symbol = Get-StockSymbol
            Execute-StockCommand -Option "1" -Symbol $symbol
        }
        "2" {
            Write-Host ""
            Write-Host "Get Stock Info" -ForegroundColor Cyan
            $symbol = Get-StockSymbol
            Execute-StockCommand -Option "2" -Symbol $symbol
        }
        "3" {
            Write-Host ""
            Write-Host "Get Stock History" -ForegroundColor Cyan
            $symbol = Get-StockSymbol
            $period = Get-TimePeriod
            Execute-StockCommand -Option "3" -Symbol $symbol -Period $period
        }
        "4" {
            Run-ExampleTests
        }
        "5" {
            Write-Host ""
            Write-Host "Goodbye! Thank you for using MCP Stock Server Test." -ForegroundColor Green
            Write-Host ""
            break
        }
    }
    
    if ($userChoice -ne "5") {
        Write-Host ""
        Write-Host "Press any key to continue..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    
} while ($userChoice -ne "5")

# Additional examples for reference
Write-Host ""
Write-Host "Additional Command Examples:" -ForegroundColor Magenta
Write-Host "   Get NVDA price:     test_stock_client_args.py -o 1 -s NVDA" -ForegroundColor White
Write-Host "   Get TSLA info:      test_stock_client_args.py -o 2 -s TSLA" -ForegroundColor White  
Write-Host "   Get AMZN history:   test_stock_client_args.py -o 3 -s AMZN -p 6mo" -ForegroundColor White
Write-Host ""

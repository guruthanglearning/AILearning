# Download Shakespeare Dataset
# This script downloads the Shakespeare dataset and prepares it for training

param(
    [string]$DataDir = "data"
)

Write-Host "Downloading Shakespeare dataset..."

# Create data directory if it doesn't exist
if (!(Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir -Force
}

# Download Shakespeare text
$url = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
$outputFile = Join-Path $DataDir "shakespeare.txt"

try {
    Invoke-WebRequest -Uri $url -OutFile $outputFile
    Write-Host "Downloaded Shakespeare text to $outputFile"
    
    # Get file info
    $fileInfo = Get-Item $outputFile
    Write-Host "File size: $([math]::Round($fileInfo.Length / 1KB, 2)) KB"
    
    # Read and split the data (90% train, 10% validation)
    $text = Get-Content $outputFile -Raw
    $totalLength = $text.Length
    $trainSize = [math]::Floor($totalLength * 0.9)
    
    $trainText = $text.Substring(0, $trainSize)
    $valText = $text.Substring($trainSize)
    
    # Save train and validation splits
    $trainFile = Join-Path $DataDir "shakespeare_train.txt"
    $valFile = Join-Path $DataDir "shakespeare_val.txt"
    
    Set-Content -Path $trainFile -Value $trainText -NoNewline
    Set-Content -Path $valFile -Value $valText -NoNewline
    
    Write-Host "Created training split: $trainFile ($([math]::Round((Get-Item $trainFile).Length / 1KB, 2)) KB)"
    Write-Host "Created validation split: $valFile ($([math]::Round((Get-Item $valFile).Length / 1KB, 2)) KB)"
    
    # Show some sample text
    Write-Host "`nSample from training data:"
    Write-Host "=========================="
    Write-Host $trainText.Substring(0, [math]::Min(500, $trainText.Length))
    Write-Host "..."
    
    Write-Host "`nDataset preparation completed successfully!"
    Write-Host "You can now run training with: dotnet run --project NanoGpt.Training"
    
} catch {
    Write-Error "Failed to download dataset: $_"
    exit 1
}
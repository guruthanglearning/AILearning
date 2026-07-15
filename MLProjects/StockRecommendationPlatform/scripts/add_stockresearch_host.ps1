$hostsFile = "C:\Windows\System32\drivers\etc\hosts"
$entry = "127.0.0.1   stockresearch.local"
$content = Get-Content $hostsFile -Raw
if ($content -match [regex]::Escape("stockresearch.local") -and $content -notmatch [regex]::Escape("app.stockresearch.local") -and $content -match "^127\.0\.0\.1\s+stockresearch\.local$") {
    Write-Host "Already present: stockresearch.local"
} elseif ($content -match "^\s*127\.0\.0\.1\s+stockresearch\.local\s*$") {
    Write-Host "Already present: stockresearch.local"
} else {
    Add-Content $hostsFile "`n$entry"
    Write-Host "Added: $entry"
}

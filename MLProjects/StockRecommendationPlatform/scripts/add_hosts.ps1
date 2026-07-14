$hostsFile = "C:\Windows\System32\drivers\etc\hosts"
$content = Get-Content $hostsFile -Raw

$entries = @(
    "127.0.0.1   stockresearch.local",
    "127.0.0.1   api.stockresearch.local"
)

foreach ($entry in $entries) {
    $domain = ($entry -split "\s+")[1]
    if ($content -match [regex]::Escape($domain)) {
        Write-Host "Already present: $domain"
    } else {
        Add-Content $hostsFile "`n$entry"
        Write-Host "Added: $entry"
    }
}

# Unblocks all compiled DLLs and EXEs in the project after a build.
# Required on machines where Windows Smart App Control (SAC) is active.
# Run this after dotnet build if tests fail with "Application Control policy has blocked this file".

param(
    [string]$ProjectRoot = $PSScriptRoot + "\.."
)

$paths = @(
    "$ProjectRoot\src",
    "$ProjectRoot\tests"
)

$count = 0
foreach ($path in $paths) {
    if (Test-Path $path) {
        $files = Get-ChildItem $path -Recurse -File -Include "*.dll","*.exe","*.pdb" -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            try {
                Unblock-File -Path $file.FullName -ErrorAction SilentlyContinue
                $count++
            } catch { }
        }
    }
}

Write-Host "✅ Unblocked $count files in $ProjectRoot" -ForegroundColor Green

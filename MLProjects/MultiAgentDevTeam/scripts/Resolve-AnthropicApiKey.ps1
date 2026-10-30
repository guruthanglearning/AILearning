<#
.SYNOPSIS
    Finds the Anthropic API key for the deploy scripts without ever printing it.

.DESCRIPTION
    Dot-source this file, then call Resolve-AnthropicApiKey. Sources are tried in order and
    the first one with a key wins:

      1. -ApiKey parameter            (works, but warns: the key is now in your shell history)
      2. ANTHROPIC_API_KEY env var    (the usual choice for CI)
      3. appsettings.secrets.json     (gitignored; copy appsettings.secrets.example.json to create it)
      4. A masked prompt              (interactive sessions only; offers to save to the secrets file)

    The key is placed in $env:ANTHROPIC_API_KEY for the current process only, so child
    processes such as docker compose can read it. It is never written to the user or
    machine environment.
#>

Set-StrictMode -Version Latest

$script:PlaceholderKeys = @('REPLACE_WITH_ACTUAL_KEY', 'REPLACE_WITH_YOUR_ANTHROPIC_API_KEY')
$script:DefaultSecretsPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'src\MultiAgentDevTeam.Orchestrator\appsettings.secrets.json'

function Test-AnthropicApiKeyFormat {
    param([string]$Key)
    return -not [string]::IsNullOrWhiteSpace($Key) -and
           $Key.Trim() -notin $script:PlaceholderKeys -and
           $Key.Trim().StartsWith('sk-ant-')
}

function Format-MaskedApiKey {
    param([string]$Key)
    return "$($Key.Substring(0, [Math]::Min(7, $Key.Length)))... ($($Key.Length) chars)"
}

function Read-SecretsFileApiKey {
    [CmdletBinding()]
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try {
        $json = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
        if ($json.PSObject.Properties.Name -contains 'AgentConfiguration' -and
            $json.AgentConfiguration.PSObject.Properties.Name -contains 'AnthropicApiKey') {
            return [string]$json.AgentConfiguration.AnthropicApiKey
        }
        Write-Warning "$Path has no AgentConfiguration.AnthropicApiKey entry."
    } catch {
        Write-Warning "Could not read ${Path}: $($_.Exception.Message)"
    }
    return $null
}

function Test-InteractiveSession {
    return [Environment]::UserInteractive -and -not [Console]::IsInputRedirected
}

function Save-ApiKeyToSecretsFile {
    [CmdletBinding()]
    param([string]$Key, [string]$Path)

    # Only save where git will ignore the file, so the key can't end up in a commit
    $dir = Split-Path -Parent $Path
    $ignored = $false
    if (Get-Command git -ErrorAction SilentlyContinue) {
        # Stderr from a native command is a terminating error under "Stop" in Windows PowerShell
        $ignored = & { $ErrorActionPreference = 'Continue'; git -C $dir check-ignore -q $Path 2>$null; $LASTEXITCODE -eq 0 }
    }
    if (-not $ignored) {
        Write-Warning "Not saving: $Path is not gitignored, so the key could be committed."
        return
    }

    $content = [ordered]@{ AgentConfiguration = [ordered]@{ AnthropicApiKey = $Key } }
    $content | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $Path -Encoding UTF8
    Write-Host "Saved to $Path (gitignored)." -ForegroundColor Green
}

function Resolve-AnthropicApiKey {
    <#
    .SYNOPSIS
        Returns the API key (and sets $env:ANTHROPIC_API_KEY), or throws if none is found.
    .PARAMETER AllowMissing
        Return $null instead of throwing when no source has a key.
    .PARAMETER NonInteractive
        Never prompt, even in an interactive session.
    #>
    [CmdletBinding()]
    param(
        [string]$ApiKey,
        [string]$SecretsPath = $script:DefaultSecretsPath,
        [switch]$AllowMissing,
        [switch]$NonInteractive
    )

    $key = $null
    $source = $null

    if (-not [string]::IsNullOrWhiteSpace($ApiKey)) {
        Write-Warning "-ApiKey puts the key in your shell history. Prefer `$env:ANTHROPIC_API_KEY or appsettings.secrets.json."
        $key, $source = $ApiKey, '-ApiKey parameter'
    }
    elseif (-not [string]::IsNullOrWhiteSpace($env:ANTHROPIC_API_KEY)) {
        $key, $source = $env:ANTHROPIC_API_KEY, 'ANTHROPIC_API_KEY environment variable'
    }
    else {
        $fileKey = Read-SecretsFileApiKey -Path $SecretsPath
        if (Test-AnthropicApiKeyFormat $fileKey) {
            $key, $source = $fileKey, (Split-Path -Leaf $SecretsPath)
        }
        elseif (-not [string]::IsNullOrWhiteSpace($fileKey)) {
            Write-Warning "$(Split-Path -Leaf $SecretsPath) still holds a placeholder or malformed key; ignoring it."
        }
    }

    if (-not $key -and -not $NonInteractive -and (Test-InteractiveSession)) {
        Write-Host "No Anthropic API key found. Get one at https://console.anthropic.com/settings/keys" -ForegroundColor Yellow
        $secure = Read-Host -Prompt 'Paste your Anthropic API key (input hidden)' -AsSecureString
        $entered = [System.Net.NetworkCredential]::new('', $secure).Password
        if (-not [string]::IsNullOrWhiteSpace($entered)) {
            $key, $source = $entered, 'prompt'
            if ((Test-AnthropicApiKeyFormat $key) -and
                (Read-Host "Save it to $(Split-Path -Leaf $SecretsPath) for next time? (y/N)") -match '^(y|yes)$') {
                Save-ApiKeyToSecretsFile -Key $key -Path $SecretsPath
            }
        }
    }

    if (-not $key) {
        if ($AllowMissing) { return $null }
        throw ("No Anthropic API key found. Provide one by either:`n" +
               "  - setting `$env:ANTHROPIC_API_KEY, or`n" +
               "  - copying src/MultiAgentDevTeam.Orchestrator/appsettings.secrets.example.json to appsettings.secrets.json and adding your key, or`n" +
               "  - running this script in an interactive terminal to be prompted.")
    }

    $key = $key.Trim()
    if (-not (Test-AnthropicApiKeyFormat $key)) {
        throw "The API key from $source doesn't look like an Anthropic key (expected it to start with 'sk-ant-')."
    }

    $env:ANTHROPIC_API_KEY = $key
    Write-Host "API key: from $source ($(Format-MaskedApiKey $key))" -ForegroundColor Green
    return $key
}

function Set-KubernetesApiKeySecret {
    <#
    .SYNOPSIS
        Creates or updates the Kubernetes Secret holding the key. The manifest is piped to
        kubectl on stdin, so the key never appears on a command line or in the process list.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Key,
        [Parameter(Mandatory)][string]$Namespace,
        [string]$Name = 'agent-secrets'
    )

    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Key))
    $manifest = @"
apiVersion: v1
kind: Secret
metadata:
  name: $Name
  namespace: $Namespace
type: Opaque
data:
  ANTHROPIC_API_KEY: $encoded
"@
    $manifest | kubectl apply -f - | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "kubectl failed to apply secret '$Name'." }
}

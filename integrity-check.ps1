param(
    [ValidateSet("Baseline", "Check")]
    [string]$Mode = "Check"
)

$ErrorActionPreference = "Stop"

# Keep all project files beside this script.
$configPath = Join-Path $PSScriptRoot "demo-config.json"
$baselinePath = Join-Path $PSScriptRoot "baseline.json"
$reportPath = Join-Path $PSScriptRoot "last-check.json"

function Save-CheckResult {
    param(
        [string]$Status,
        [string]$Message
    )

    $result = [PSCustomObject]@{
        checkedAt = (Get-Date).ToString("o")
        file = "demo-config.json"
        status = $Status
        message = $Message
    }

    $result |
        ConvertTo-Json |
        Set-Content -LiteralPath $reportPath -Encoding UTF8

    Write-Host "$Status : $Message"
    Write-Host "Report saved to: $reportPath"
}

if ($Mode -eq "Baseline") {
    if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
        throw "Cannot create a baseline: demo-config.json is missing."
    }

    if (Test-Path -LiteralPath $baselinePath) {
        throw "A baseline already exists. Keep it for these tests."
    }

    $fileHash = Get-FileHash -LiteralPath $configPath -Algorithm SHA256

    [PSCustomObject]@{
        createdAt = (Get-Date).ToString("o")
        file = "demo-config.json"
        algorithm = "SHA256"
        hash = $fileHash.Hash
    } |
        ConvertTo-Json |
        Set-Content -LiteralPath $baselinePath -Encoding UTF8

    Write-Host "BASELINE CREATED: Original configuration recorded."
    exit
}

if (-not (Test-Path -LiteralPath $baselinePath -PathType Leaf)) {
    throw "No baseline found. Run the script with -Mode Baseline first."
}

if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    Save-CheckResult -Status "MISSING" `
        -Message "The configuration file could not be found."
    exit
}

$baseline = Get-Content -LiteralPath $baselinePath -Raw |
    ConvertFrom-Json

if ($baseline.algorithm -ne "SHA256" -or
    $baseline.hash -notmatch "^[A-Fa-f0-9]{64}$") {
    throw "The baseline does not contain a valid SHA256 hash."
}

$currentHash = Get-FileHash -LiteralPath $configPath -Algorithm SHA256

if ($currentHash.Hash -eq $baseline.hash) {
    Save-CheckResult -Status "PASS" `
        -Message "Configuration matches the recorded baseline."
}
else {
    Save-CheckResult -Status "CHANGED" `
        -Message "Configuration differs from the recorded baseline."
}
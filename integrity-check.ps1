param(
    [ValidateSet("Baseline", "Check")]
    [string]$Mode = "Check"
)

$ErrorActionPreference = "Stop"

$configPath = Join-Path $PSScriptRoot "demo-config.json"
$baselinePath = Join-Path $PSScriptRoot "baseline-v2.json"
$reportPath = Join-Path $PSScriptRoot "last-check.json"

function Read-Config {
    param([string]$Path)

    $config = Get-Content -LiteralPath $Path -Raw |
        ConvertFrom-Json

    if ($config -isnot [System.Management.Automation.PSCustomObject]) {
        throw "The configuration must be a JSON object with named settings."
    }

    return $config
}

function Save-CheckResult {
    param(
        [string]$Status,
        [string]$Message,
        [object[]]$Changes = @()
    )

    [PSCustomObject]@{
        checkedAt = (Get-Date).ToString("o")
        file = "demo-config.json"
        status = $Status
        message = $Message
        changes = @($Changes)
    } |
        ConvertTo-Json -Depth 50 |
        Set-Content -LiteralPath $reportPath -Encoding UTF8

    Write-Host "$Status : $Message"

    foreach ($change in $Changes) {
        $oldText = ConvertTo-Json -InputObject $change.oldValue -Compress -Depth 40
        $newText = ConvertTo-Json -InputObject $change.newValue -Compress -Depth 40

        switch ($change.type) {
            "MODIFIED" {
                Write-Host "  $($change.field): $oldText -> $newText"
            }
            "ADDED" {
                Write-Host "  ADDED $($change.field): $newText"
            }
            "REMOVED" {
                Write-Host "  REMOVED $($change.field): $oldText"
            }
        }
    }

    Write-Host "Report saved to: $reportPath"
}

if ($Mode -eq "Baseline") {
    if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
        throw "Cannot create a baseline: demo-config.json is missing."
    }

    if (Test-Path -LiteralPath $baselinePath) {
        throw "A version 2 baseline already exists. Keep it for these tests."
    }

    $config = Read-Config -Path $configPath
    $fileHash = Get-FileHash -LiteralPath $configPath -Algorithm SHA256

    [PSCustomObject]@{
        schemaVersion = 2
        createdAt = (Get-Date).ToString("o")
        file = "demo-config.json"
        algorithm = "SHA256"
        hash = $fileHash.Hash
        configuration = $config
    } |
        ConvertTo-Json -Depth 50 |
        Set-Content -LiteralPath $baselinePath -Encoding UTF8

    Write-Host "BASELINE CREATED: Hash and original settings recorded."
    exit
}

if (-not (Test-Path -LiteralPath $baselinePath -PathType Leaf)) {
    throw "Run the script with -Mode Baseline to create baseline-v2.json."
}

$baseline = Get-Content -LiteralPath $baselinePath -Raw |
    ConvertFrom-Json

if ($baseline.schemaVersion -ne 2 -or
    $baseline.algorithm -ne "SHA256" -or
    $baseline.hash -notmatch "^[A-Fa-f0-9]{64}$" -or
    $baseline.configuration -isnot [System.Management.Automation.PSCustomObject]) {
    throw "The version 2 baseline is invalid."
}

if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    Save-CheckResult -Status "MISSING" -Message "The configuration file could not be found."
    exit
}

$currentHash = Get-FileHash -LiteralPath $configPath -Algorithm SHA256

if ($currentHash.Hash -eq $baseline.hash) {
    Save-CheckResult -Status "PASS" -Message "Configuration matches the recorded baseline."
    exit
}

try {
    $currentConfig = Read-Config -Path $configPath
}
catch {
    Save-CheckResult -Status "INVALID" -Message "The changed file is not a valid JSON configuration object."
    exit
}

$originalConfig = $baseline.configuration
$oldNames = @($originalConfig.PSObject.Properties.Name)
$newNames = @($currentConfig.PSObject.Properties.Name)
$allNames = @($oldNames + $newNames | Sort-Object -Unique -CaseSensitive)
$changes = @()

foreach ($name in $allNames) {
    $hadField = $oldNames -ccontains $name
    $hasField = $newNames -ccontains $name
    $oldValue = $null
    $newValue = $null
    $changeType = $null

    if ($hadField) {
        $oldValue = $originalConfig.PSObject.Properties[$name].Value
    }

    if ($hasField) {
        $newValue = $currentConfig.PSObject.Properties[$name].Value
    }

    if (-not $hadField) {
        $changeType = "ADDED"
    }
    elseif (-not $hasField) {
        $changeType = "REMOVED"
    }
    else {
        $oldJson = ConvertTo-Json -InputObject $oldValue -Compress -Depth 40
        $newJson = ConvertTo-Json -InputObject $newValue -Compress -Depth 40

        if ($oldJson -cne $newJson) {
            $changeType = "MODIFIED"
        }
    }

    if ($changeType) {
        $changes += [PSCustomObject]@{
            field = $name
            type = $changeType
            oldValue = $oldValue
            newValue = $newValue
        }
    }
}

if ($changes.Count -gt 0) {
    Save-CheckResult -Status "CHANGED" -Message "Configuration settings differ from the baseline." -Changes $changes
}
else {
    Save-CheckResult -Status "CHANGED" -Message "File contents changed, but top-level setting values match. Check formatting or property order."
}
[CmdletBinding()]
param([switch]$IncludeResearchAssets)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

function Invoke-GitChecked {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$GitArguments)
    & git @GitArguments
    if ($LASTEXITCODE -ne 0) { throw "Git command failed: git $($GitArguments -join ' ')" }
}

$branch = (& git branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or $branch -ne 'main') { throw 'Run upload preparation from main.' }
$origin = (& git remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $origin -notmatch 'github\.com[:/]NafisAnwar/CAP4103-Team-Classifiers(?:\.git)?$') {
    throw 'Origin does not match the expected project repository.'
}

if ($IncludeResearchAssets) {
    Write-Host 'Including biometric data, models and course/private references; source sharing terms still apply.'
    Invoke-GitChecked lfs version
    Invoke-GitChecked lfs install --local #install the upload hook for this repository
    $ignorePath = Join-Path $projectRoot '.gitignore'
    $remove = @('data/raw/', 'data/processed/', 'ppa3_legacy/plots/', 'docs/reference/*', '!docs/reference/source_inventory.json')
    $lines = @(Get-Content -LiteralPath $ignorePath | Where-Object { $_.Trim() -notin $remove })
    [System.IO.File]::WriteAllText($ignorePath, ($lines -join "`n") + "`n", [System.Text.UTF8Encoding]::new($false))
    Invoke-GitChecked lfs track 'data/raw/**' 'data/processed/**' 'docs/reference/*.pdf' #keep bulk assets out of ordinary git blobs
}

Invoke-GitChecked add -- README.md docs/nazmus_handoff.md docs/nazmus_handoff.txt docs/project_status.md docs/developer_roadmap.md docs/methodology.md docs/upload_guide.md scripts/prepare_full_upload.ps1
if ($IncludeResearchAssets) {
    Invoke-GitChecked add -- .gitignore .gitattributes data/raw data/processed docs/reference ppa3_legacy/plots
    foreach ($folder in @('data/raw', 'data/processed', 'docs/reference', 'ppa3_legacy/plots')) {
        $localCount = @(Get-ChildItem -LiteralPath $folder -File -Recurse -Force).Count
        $tracked = @(& git ls-files -- $folder)
        if ($LASTEXITCODE -ne 0 -or $tracked.Count -ne $localCount) { throw "File-count mismatch in $folder; inspect before committing." }
        Write-Host "${folder}: $localCount local files staged/tracked"
    }
}

$staged = @(& git diff --cached --name-only)
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect staged files.' }
$unexpected = @($staged | Where-Object { $_ -match '(^|/)(\.venv|__pycache__|\.git|work|tmp)(/|$)|(^|/)\.env($|\.)|\.(pem|key)$' })
if ($unexpected.Count -gt 0) { throw "Unexpected environment/credential paths are staged: $($unexpected -join ', ')" }
Invoke-GitChecked diff --cached --check
Invoke-GitChecked diff --cached --shortstat
Write-Host 'Prepared only. Review git diff --cached --name-status before committing and pushing.'

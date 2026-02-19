param(
    [string]$ConfigPath = "C:\Users\natha\dev\repos\agent-ops\clawdbot\clawdbot.json"
)

$repoRoot = "C:\Users\natha\dev\repos\agent-ops"
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path $repoRoot "agent_outputs\clawdbot_$ts"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

if (-not (Test-Path $ConfigPath)) {
    throw "Config not found: $ConfigPath"
}

$config = Get-Content -Raw -Path $ConfigPath | ConvertFrom-Json

Write-Output "Clawdbot v1 run: $($config.name) at $ts" | Out-File (Join-Path $outDir "run.log") -Encoding utf8

# 1) Run parallel lanes
if ($config.runs.lanes) {
    Write-Output "Running lanes..." | Tee-Object -FilePath (Join-Path $outDir "run.log") -Append
    & (Join-Path $repoRoot "scripts\run_lanes.ps1") | Out-File (Join-Path $outDir "lanes.log") -Encoding utf8
}

# 2) Update repo inventory
if ($config.runs.inventory) {
    Write-Output "Updating repo inventory..." | Tee-Object -FilePath (Join-Path $outDir "run.log") -Append
    $env:JCW_REPO_ROOT = $config.repoRoot
    $env:JCW_REPO_INCLUDE = ($config.includePatterns -join ",")
    $env:JCW_REPO_EXCLUDE = ($config.excludePatterns -join ",")
    python (Join-Path $repoRoot "scripts\update_repo_inventory.py") | Out-File (Join-Path $outDir "inventory.log") -Encoding utf8
}

# 3) Research digest (optional)
if ($config.runs.researchDigest) {
    Write-Output "Running research digest..." | Tee-Object -FilePath (Join-Path $outDir "run.log") -Append
    & (Join-Path $repoRoot "scripts\run_research_digest.ps1") | Out-File (Join-Path $outDir "research.log") -Encoding utf8
}

Write-Output "Clawdbot run complete: $outDir" | Tee-Object -FilePath (Join-Path $outDir "run.log") -Append

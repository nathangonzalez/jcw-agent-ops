param(
    [string]$RepoRoot = "C:\Users\natha\dev\repos\agent-ops"
)

$scriptPath = Join-Path $RepoRoot "scripts\run_slack_bot.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "Missing run_slack_bot.ps1 at $scriptPath"
}

& $scriptPath

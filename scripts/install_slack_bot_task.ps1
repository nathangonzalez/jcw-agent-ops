param(
    [string]$TaskName = "ClawdbotSlack",
    [string]$RepoRoot = "C:\Users\natha\dev\repos\agent-ops"
)

$scriptPath = Join-Path $RepoRoot "scripts\run_slack_bot_svc.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "Missing run_slack_bot_svc.ps1 at $scriptPath"
}

$taskAction = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
schtasks /Create /TN $TaskName /TR $taskAction /SC ONLOGON /F | Out-Null

Write-Output "Installed task '$TaskName'."
Write-Output "Start now: schtasks /Run /TN $TaskName"

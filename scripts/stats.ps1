# OpenClaw activity summary

$ErrorActionPreference = "SilentlyContinue"

$logDir = "C:\\tmp\\openclaw"
$today = Get-Date -Format "yyyy-MM-dd"
$logFile = Join-Path $logDir ("openclaw-" + $today + ".log")
$auditFile = Join-Path $env:USERPROFILE ".openclaw\\logs\\config-audit.jsonl"
$persistFile = "C:\\Users\\natha\\dev\\repos\\agent-ops\\agent.persist"

Write-Host ""
Write-Host "OpenClaw Activity Summary"
Write-Host "========================="
Write-Host ""

Write-Host "Gateway Status"
Write-Host "--------------"
if (Get-Command openclaw -ErrorAction SilentlyContinue) {
  openclaw gateway status
} else {
  Write-Host "openclaw CLI not found in PATH."
}

Write-Host ""
Write-Host "Recent Gateway Log (tail 80)"
Write-Host "----------------------------"
if (Test-Path $logFile) {
  Get-Content -Path $logFile -Tail 80
} else {
  Write-Host "No log file found at $logFile"
}

Write-Host ""
Write-Host "Recent Config Audit (tail 20)"
Write-Host "-----------------------------"
if (Test-Path $auditFile) {
  Get-Content -Path $auditFile -Tail 20
} else {
  Write-Host "No config audit found at $auditFile"
}

Write-Host ""
Write-Host "Recent Approvals (tail 20)"
Write-Host "--------------------------"
if (Test-Path $persistFile) {
  Get-Content -Path $persistFile -Tail 20
} else {
  Write-Host "No approval log found at $persistFile"
}

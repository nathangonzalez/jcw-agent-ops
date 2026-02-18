param(
    [string]$Summary = "",
    [string]$Next = "",
    [string]$Blockers = "",
    [string]$Path = ""
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptRoot "..")
if ([string]::IsNullOrWhiteSpace($Path)) {
    $Path = Join-Path $repoRoot "agent.persist"
}

if ([string]::IsNullOrWhiteSpace($Summary)) {
    $Summary = Read-Host "Summary (what we did)"
}
if ([string]::IsNullOrWhiteSpace($Next)) {
    $Next = Read-Host "Next (what to do next)"
}
if ([string]::IsNullOrWhiteSpace($Blockers)) {
    $Blockers = Read-Host "Blockers (if any)"
}

$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$lines = @(
    "$ts | SESSION",
    "- Summary: $Summary",
    "- Next: $Next",
    "- Blockers: $Blockers",
    ""
)
$lines | Add-Content -Path $Path

Write-Output "Appended session log to $Path"

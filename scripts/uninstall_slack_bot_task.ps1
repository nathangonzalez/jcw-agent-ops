param(
    [string]$TaskName = "ClawdbotSlack"
)

schtasks /End /TN $TaskName 2>$null | Out-Null
schtasks /Delete /TN $TaskName /F | Out-Null

Write-Output "Removed task '$TaskName'."

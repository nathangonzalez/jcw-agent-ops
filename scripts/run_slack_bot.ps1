param(
    [string]$BotToken = "",
    [string]$AppToken = "",
    [string]$SigningSecret = ""
)

if ($BotToken) { $env:SLACK_BOT_TOKEN = $BotToken }
if ($AppToken) { $env:SLACK_APP_TOKEN = $AppToken }
if ($SigningSecret) { $env:SLACK_SIGNING_SECRET = $SigningSecret }

$repoRoot = "C:\Users\natha\dev\repos\agent-ops"
$secretsPath = Join-Path $repoRoot "Slack\sc_manager.txt"
if ((-not $env:SLACK_BOT_TOKEN -or -not $env:SLACK_APP_TOKEN) -and (Test-Path $secretsPath)) {
    $content = Get-Content -Raw -Path $secretsPath
    Invoke-Expression $content
}

$defaultOpenclaw = "C:\Users\natha\AppData\Roaming\npm\openclaw.cmd"
if (-not $env:OPENCLAW_BIN -and (Test-Path $defaultOpenclaw)) {
    $env:OPENCLAW_BIN = $defaultOpenclaw
}

python (Join-Path $repoRoot "scripts\slack_bot.py")

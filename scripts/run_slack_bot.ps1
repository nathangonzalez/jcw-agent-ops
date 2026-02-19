param(
    [string]$BotToken = "",
    [string]$AppToken = "",
    [string]$SigningSecret = ""
)

if ($BotToken) { $env:SLACK_BOT_TOKEN = $BotToken }
if ($AppToken) { $env:SLACK_APP_TOKEN = $AppToken }
if ($SigningSecret) { $env:SLACK_SIGNING_SECRET = $SigningSecret }

python C:\Users\natha\dev\repos\agent-ops\scripts\slack_bot.py

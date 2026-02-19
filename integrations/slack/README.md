# Slack Bridge (Clawdbot v1)

## Overview
This uses **Slack Socket Mode** to connect Clawdbot to Slack without exposing a public webhook.

## Create the Slack App
1. Create a Slack app (from scratch) in your workspace.
2. Enable **Socket Mode** and generate an **App Token** (`xapp-`) with the `connections:write` scope.
3. Add **Bot Token Scopes**:
   - `chat:write`
   - `app_mentions:read`
   - `im:history` (required for `message.im` DMs)
4. Enable **Event Subscriptions** and subscribe to:
   - `app_mention`
   - `message.im` (direct messages)
5. Install the app to your workspace to get the **Bot Token** (`xoxb-`).

## Environment Variables
Set the following:
```powershell
$env:SLACK_BOT_TOKEN="xoxb-..."
$env:SLACK_APP_TOKEN="xapp-..."
$env:SLACK_SIGNING_SECRET="..."
$env:CLAWDBOT_AGENT="orchestrator"
```

## Run
```powershell
pip install slack-bolt slack-sdk
scripts\run_slack_bot.ps1
```

## Notes
- The bot responds to @mentions in channels and DMs.
- Responses are **guidance only** (no external actions).
- Use a dedicated Slack channel for Clawdbot testing.

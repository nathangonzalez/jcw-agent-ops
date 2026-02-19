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
$env:OPENCLAW_BIN="C:\Users\natha\AppData\Roaming\npm\openclaw.cmd"
$env:CLAWDBOT_ALLOW_USERS="U12345,U67890"
$env:CLAWDBOT_ALLOW_CHANNELS="C12345,C67890"
$env:CLAWDBOT_ALLOW_DMS="true"
$env:CLAWDBOT_LOG_DIR="C:\Users\natha\dev\repos\agent-ops\agent_outputs"
$env:CLAWDBOT_LOG_LEVEL="INFO"
```

## Run
```powershell
pip install slack-bolt slack-sdk
scripts\run_slack_bot.ps1
```

## Slash Command (Optional)
- Add a `/claw` slash command to your Slack app.
- The bot will respond in the channel where the command was run.

## Scheduled Task (Optional)
```powershell
scripts\install_slack_bot_task.ps1
schtasks /Run /TN ClawdbotSlack
```
To uninstall:
```powershell
scripts\uninstall_slack_bot_task.ps1
```

## Notes
- The bot responds to @mentions in channels and DMs.
- Responses are **guidance only** (no external actions).
- Use a dedicated Slack channel for Clawdbot testing.
- Logs:
  - `agent_outputs\clawdbot_slack.log` (events)
  - `agent_outputs\clawdbot_slack_runtime.log` (runtime)

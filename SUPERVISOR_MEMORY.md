# Supervisor Memory (JCW Agent Ops)

## Purpose
This file captures stable context and decisions so the Codex supervisor can
operate from Slack with continuity. Keep it concise and update when major
decisions change.

## System Topology
- Slack bot (Clawbot) runs on a GCP VM for 24/7 uptime.
- Repo: `jcw-agent-ops` (GitHub). VM clones to `/opt/agent-ops`.
- VM instance: `clawbot-ops` in `us-central1-a`.
- Service account: `clawbot-sa@jcw-2-android-estimator.iam.gserviceaccount.com`
  with Secret Manager + Logging.
- Secrets stored in GCP Secret Manager:
  - `slack_bot_token`, `slack_app_token`, `slack_signing_secret`
  - `anthropic_api_key`, `openai_api_key`
- Runtime env on VM: `/etc/clawbot.env`
- Services:
  - `clawbot.service` (Slack bot)
  - `clawbot-monitor.timer` (hourly health report)

## Operating Model
- Codex (supervisor) in this chat or via Slack using prefix `codex:`.
- Clawbot handles routine ops by default.
- Approval buttons required for major tasks:
  - `/claw approve <task>`
  - `@jcw_service approve: <task>`
- Slack interactivity must be enabled; `commands` and `conversations:join`
  scopes recommended; app must be installed in channel or auto-join.

## Slack Routing Rules
- `/claw ...` -> Clawbot (OpenClaw)
- `/claw codex ...` or `@jcw_service codex: ...` -> Codex route (OpenAI)
- Clawbot responds in-channel for mentions and via `response_url` for slash.

## Monitoring
- Hourly report to `#jcw_bot` via `scripts/monitor_bot.py`
- Report includes DMs, mentions, replies, errors.

## Current Guardrails
- No external actions without explicit approval.
- Always log and report errors; keep summaries short and actionable.


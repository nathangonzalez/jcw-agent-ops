# Agent Ops Runbook

## Purpose
Operational procedures for the Agent Ops system, focused on safe execution, approvals, and recovery.

## Quick Actions

**Kill switch (stop all agents)**:
```powershell
openclaw gateway stop
```

**Resume agents**:
```powershell
openclaw gateway start
```

**Disable web search**:
1. Edit `%USERPROFILE%\.openclaw\openclaw.json`
2. Set `tools.web.search.enabled` to `false`
3. Restart the gateway

**Run stress test (parallel agents)**:
```powershell
scripts\run_stress.ps1
```

**Run research digest (requires web search enabled)**:
```powershell
scripts\run_research_digest.ps1
```

**Kill switch (local)**:
```powershell
scripts\kill_switch.ps1
```

**Log session summary**:
```powershell
scripts\log_session.ps1
```

**Run Tasks Web UI**:
```powershell
scripts\run_webui.ps1
```

**UAT Demo Video (Playwright)**:
```powershell
npm install
npm run uat:install
npm run uat:demo
```
Video + trace will appear under `test-results/` for the demo run.

**Clawdbot v1 (continuous development)**:
```powershell
scripts\clawdbot_run.ps1
```
Config: `clawdbot/clawdbot.json`

**Slack Bridge (Socket Mode)**:
```powershell
pip install slack-bolt slack-sdk
$env:SLACK_BOT_TOKEN="xoxb-..."
$env:SLACK_APP_TOKEN="xapp-..."
$env:SLACK_SIGNING_SECRET="..."
scripts\run_slack_bot.ps1
```
Repo targeting (exec):
- Set `CLAWDBOT_REPO_MAP="agent-ops=C:\Users\natha\dev\repos\agent-ops;jcw_payroll=C:\Users\natha\dev\repos\jcw_payroll"`
- Use `codex: exec repo=jcw_payroll; git status`

**Slack Bridge (Cloud Run / Events API)**:
```powershell
# Build + deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/jcw-clawbot -f Dockerfile.slackbot .
gcloud run deploy jcw-clawbot `
  --image gcr.io/$PROJECT_ID/jcw-clawbot `
  --region us-central1 `
  --allow-unauthenticated `
  --set-env-vars `
SLACK_BOT_TOKEN=...,
SLACK_SIGNING_SECRET=...,
OPENAI_API_KEY=...,
CLAWDBOT_REPO_MAP=agent-ops=/opt/agent-ops,
CLAWDBOT_MODE=http,
CLAWDBOT_CODE_MODE=false,
CLAWDBOT_EXEC_MODE=false
```
Slack app settings:
- Request URL: `https://<cloud-run-url>/slack/events`
- Interactivity URL: `https://<cloud-run-url>/slack/events`
- Slash commands: point to the same `/slack/events` URL

**Sync Tasks back to Excel (All Tasks)**:
```powershell
scripts\actions_writeback.ps1 -InputPath "C:\Users\natha\Downloads\Actions.xlsx"
```

**Gmail Draft (dry-run)**:
```powershell
python scripts/google_gmail_draft.py --to "you@example.com" --subject "Draft" --body "Hello"
```

**Calendar Draft (dry-run)**:
```powershell
python scripts/google_calendar_draft.py --title "Site visit" --start "2026-02-20T09:00:00" --end "2026-02-20T10:00:00"
```

**Web UI Draft + Sync Controls**:
- Task cards include “Draft Email” and “Draft Event” buttons (drafts only).
- “Sync Excel” requires typing `APPROVE` and writes DB updates to `All Tasks`.

## Approval and Logging
- Follow the approval process in `WORKFLOW.md`.
- Use the checklist in `OPENCLAW_GUARDRAILS.md`.
- Log approvals to `agent.persist` with timestamp, action, and approver.

## Incident Response

**Unexpected external action**:
1. Stop the gateway (kill switch).
2. Record the event in `agent.persist`.
3. Review `OPENCLAW_GUARDRAILS.md` and recent approval entries.
4. Resume only after root cause is identified.

**Risk of data loss**:
1. Stop all agents.
2. Verify backups and last known good state.
3. Escalate to human review before any write operations.

## Safe Mode
Use a minimal tool profile for all agents and re-enable tools one at a time after approval.

## References
- `OPENCLAW_GUARDRAILS.md`
- `WORKFLOW.md`
- `openclaw.json`
- `agent.persist`
- `OPS_METRICS.md`

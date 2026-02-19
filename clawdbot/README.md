# Clawdbot v1 (Continuous Development)

## Purpose
Run scheduled multi-agent lanes, update repo inventory, and generate research digests for the JCW suite.

## Defaults (per user)
- Scope: all repos matching `jcw-*`, `jcw_*`, plus `jcw_payroll`, `jcw_financials`.
- Actions: draft changes + auto PRs allowed; **no merges**.
- Cadence: daily + midday check (local time).
- Tools: web search enabled; email/posting disabled.

## Config
- `clawdbot/clawdbot.json`

## Run Manually
```powershell
scripts\clawdbot_run.ps1
```

## Outputs
- `agent_outputs/clawdbot_*` for run logs
- `inventory/repo_inventory.md` updated by crawler

## Guardrails
- No external posting or email sending
- No merges without human approval
- Logs appended to `agent.persist`

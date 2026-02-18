# Ops Emergency Controls

## Kill Switch (Local)
```powershell
openclaw gateway stop
```

## Soft Lockdown (Recommended First)
1. Disable web search and fetch in `%USERPROFILE%\.openclaw\openclaw.json`.
2. Disable agent-to-agent routing if needed.
3. Restart the gateway.

## Hard Lockdown (If Behavior Persists)
1. Stop the gateway.
2. Revoke or rotate API keys (OpenAI, Anthropic, Google) in `.env`.
3. Disable or remove scheduled tasks for OpenClaw.
4. Block outbound network access for the agent process.

## Post-Incident Review
- Capture logs and approvals.
- Identify root cause, update guardrails, add tests.

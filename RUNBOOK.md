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

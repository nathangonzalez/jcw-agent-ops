# OpenClaw Guardrails (Fast Track)

## Objective
Enable multi-agent work while requiring explicit human approval for risky actions (messaging, external posting, web browsing, automation, host exec).

## Risky Actions (Require Approval)
- Sending messages via Slack/Discord/WhatsApp/Email or any outbound "message" tool.
- Web browsing or fetching (web_search, web_fetch).
- UI automation (browser, canvas).
- Automation tools (cron, gateway).
- Host execution (elevated exec) or system-level changes.

## Enforcement (Config)
- Default tool profile is `minimal`.
- Only the `release` agent is allowed to use `group:messaging`, `group:web`, and `group:ui`.
- `tools.elevated.enabled` remains `false`.
- Research agent runs with `workspaceAccess: "none"`.

## Approval Workflow
1. Agent proposes action + exact payload.
2. Human replies with `APPROVE: <short reason>` to authorize.
3. `release` agent executes; all other agents abstain.

## Human Approval Checklist (Risky Actions)
- Scope is limited and reversible.
- Exact payload/command is included and reviewed.
- Target environment is correct (dev/staging/prod).
- Data exposure is minimal and acceptable.
- Rollback or stop plan is clear.
- Logging destination is specified.

## Logging
- Append approvals to `agent.persist` (date, action, approver).

## Change Policy
- Any expansion of tool permissions must be reviewed and recorded here.

## External Actions Guardrails
- Always require explicit approval before emails, postings, or payments.
- Show the exact payload (message, recipient, amount) before approval.
- Hold and flag any action with sensitive data or unusual recipients.
- No bulk actions without renewed, specific approval each time.

## Rollback Plan
- Notify the user immediately on unintended actions.
- Attempt reversal: recall or delete messages, cancel or reverse payments.
- Escalate with manual recovery steps if rollback fails.
- Preserve action logs for troubleshooting and audit.

## Circuit Breakers
- Kill switch: `scripts/kill_switch.ps1`
- Soft lockdown: disable web search and agent-to-agent, then restart gateway.
- Hard lockdown: stop gateway and revoke API keys.

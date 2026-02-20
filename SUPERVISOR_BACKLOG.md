# Supervisor Backlog

## P0 - Must Fix
- Ensure Slack responses are context-rich (match this chat).
- Confirm sprint board parsing in Slack always works (CRLF-safe).

## P1 - High Priority
- Add `SUPERVISOR_BACKLOG` and `SUPERVISOR_MEMORY` readback in Slack:
  `/claw codex supervisor status`.
- Add optional "Codex default" toggle (no prefix) via env.
- Add daily summary job (sprint + digest) to `#jcw_bot`.
- Payroll: reconcile weekly exports vs SQLite DB.
- Suite: build modern dashboard with backlog cards + suite scaffold.
- Suite: wire full usage + cost dashboard (Codex + Anthropic + OpenClaw + GCP billing).
- Suite: add agent burndown panel (per-agent progress + last update).
- Suite: app store data feed (populate `data/suite_apps.json`).
- OpenClaw visibility: show gateway status + error rate in Suite Ops.
- 24/7 research crawler: daily digests + backlog refinement spikes.
- JCW main website upgrade (jcweltonconstruction.com) discovery + redesign plan.

## P2 - Enhancements
- Create a persistent memory file (`PERSIST.txt`) and a summary updater.
- Add explicit status commands:
<!-- patch click test -->
  - `/claw status` (sprint summary)
  - `/claw digest` (latest digest)
  - `/claw agent-status` (bot uptime + errors)
 - patch click test 2
- Firestore sync for tasks (Actions.xlsx -> Firestore) for cloud UI.

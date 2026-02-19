# Supervisor Backlog

## P0 - Must Fix
- Ensure OpenClaw binary exists on VM (`/usr/local/bin/openclaw`) and Slack
  commands that use OpenClaw do not fail with "No such file or directory".
- Confirm sprint board parsing in Slack always works (CRLF-safe).

## P1 - High Priority
- Add `SUPERVISOR_BACKLOG` and `SUPERVISOR_MEMORY` readback in Slack:
  `/claw codex supervisor status`.
- Add optional "Codex default" toggle (no prefix) via env.
- Add daily summary job (sprint + digest) to `#jcw_bot`.

## P2 - Enhancements
- Create a persistent memory file (`PERSIST.txt`) and a summary updater.
- Add explicit status commands:
  - `/claw status` (sprint summary)
  - `/claw digest` (latest digest)
  - `/claw agent-status` (bot uptime + errors)


#!/usr/bin/env python
"""
Slack Socket Mode bot bridge for Clawdbot.
Responds to app mentions and direct messages using OpenClaw.
"""

import os
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "").strip()
APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "").strip()
SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "").strip()

if not BOT_TOKEN or not APP_TOKEN:
    raise SystemExit("Missing SLACK_BOT_TOKEN or SLACK_APP_TOKEN. See integrations/slack/README.md")

OPENCLAW_AGENT = os.environ.get("CLAWDBOT_AGENT", "orchestrator")
OPENCLAW_BIN = os.environ.get("OPENCLAW_BIN", "").strip()
SAFE_PREFIX = os.environ.get(
    "CLAWDBOT_SAFE_PREFIX",
    "You are Clawdbot. Do not take external actions. Provide guidance only. Ask for approval before any external action.",
)

LOG_DIR = Path(os.environ.get("CLAWDBOT_LOG_DIR", r"C:\Users\natha\dev\repos\agent-ops\agent_outputs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_line(message: str):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}"
    log_path = LOG_DIR / "clawdbot_slack.log"
    log_path.write_text(log_path.read_text() + line + "\n" if log_path.exists() else line + "\n")
    print(line, flush=True)


def run_openclaw(user_text: str) -> str:
    openclaw_cmd = OPENCLAW_BIN or shutil.which("openclaw") or shutil.which("openclaw.cmd")
    if not openclaw_cmd:
        # Common Windows global npm location
        candidate = r"C:\Users\natha\AppData\Roaming\npm\openclaw.cmd"
        if os.path.exists(candidate):
            openclaw_cmd = candidate
    if not openclaw_cmd:
        return "Clawdbot error: openclaw command not found. Set OPENCLAW_BIN to full path."

    prompt = f"{SAFE_PREFIX}\n\nUser: {user_text}".strip()
    cmd = [
        openclaw_cmd,
        "agent",
        "--agent",
        OPENCLAW_AGENT,
        "--message",
        prompt,
        "--thinking",
        "low",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
    if proc.returncode != 0:
        return f"Clawdbot error: {proc.stderr.strip() or 'unknown error'}"
    return proc.stdout.strip()


def truncate(text: str, limit: int = 3000) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


if SIGNING_SECRET:
    app = App(token=BOT_TOKEN, signing_secret=SIGNING_SECRET)
else:
    app = App(token=BOT_TOKEN)


@app.event("app_mention")
def on_app_mention(event, say):
    if event.get("bot_id"):
        return
    text = event.get("text", "")
    user = event.get("user", "")
    log_line(f"app_mention from {user}: {text}")
    try:
        response = run_openclaw(text)
    except Exception as exc:
        response = f"Clawdbot error: {exc}"
    try:
        say(truncate(response), thread_ts=event.get("ts"))
    except Exception as exc:
        log_line(f"app_mention send failed: {exc}")


@app.event("message")
def on_message(event, say):
    if event.get("subtype") or event.get("bot_id"):
        return
    if event.get("channel_type") != "im":
        return
    text = event.get("text", "")
    user = event.get("user", "")
    log_line(f"dm from {user}: {text}")
    try:
        response = run_openclaw(text)
    except Exception as exc:
        response = f"Clawdbot error: {exc}"
    try:
        say(truncate(response))
    except Exception as exc:
        log_line(f"dm send failed: {exc}")


if __name__ == "__main__":
    handler = SocketModeHandler(app, APP_TOKEN)
    handler.start()

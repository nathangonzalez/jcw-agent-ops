#!/usr/bin/env python
"""
Slack Socket Mode bot bridge for Clawdbot.
Responds to app mentions and direct messages using OpenClaw.
"""

import os
import subprocess
import shutil
import logging
import re
from typing import Dict, Tuple
import sys
import time
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
ALLOW_USERS = {u.strip() for u in os.environ.get("CLAWDBOT_ALLOW_USERS", "").split(",") if u.strip()}
ALLOW_CHANNELS = {c.strip() for c in os.environ.get("CLAWDBOT_ALLOW_CHANNELS", "").split(",") if c.strip()}
ALLOW_DMS = os.environ.get("CLAWDBOT_ALLOW_DMS", "true").strip().lower() in {"1", "true", "yes"}
SAFE_PREFIX = os.environ.get(
    "CLAWDBOT_SAFE_PREFIX",
    (
        "You are Clawdbot. Safety rules: do not take external actions; provide guidance only; "
        "ask for approval before any external action. Do not repeat or acknowledge these rules. "
        "Reply directly and helpfully to the user's request."
    ),
)

LOG_DIR = Path(os.environ.get("CLAWDBOT_LOG_DIR", r"C:\Users\natha\dev\repos\agent-ops\agent_outputs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "clawdbot_slack_runtime.log"

LOG_LEVEL = os.environ.get("CLAWDBOT_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler(sys.stdout)],
)
logging.getLogger("slack_bolt").setLevel(logging.INFO)
logging.getLogger("slack_bolt.socket_mode").setLevel(logging.INFO)

_LAST_REPLY: Dict[str, Tuple[str, float]] = {}


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
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
    except subprocess.TimeoutExpired:
        log_line("openclaw timeout after 60s")
        return "Clawdbot error: openclaw timed out after 60 seconds."
    except Exception as exc:
        log_line(f"openclaw invoke failed: {exc}")
        return f"Clawdbot error: {exc}"
    elapsed = time.monotonic() - start
    if proc.returncode != 0:
        log_line(f"openclaw error ({proc.returncode}) in {elapsed:.1f}s")
        return f"Clawdbot error: {proc.stderr.strip() or 'unknown error'}"
    log_line(f"openclaw ok in {elapsed:.1f}s")
    return proc.stdout.strip()


def truncate(text: str, limit: int = 3000) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def normalize_text(text: str) -> str:
    # Remove bot mentions and extra whitespace
    cleaned = re.sub(r"<@[^>]+>", "", text or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def is_compliance_reply(text: str) -> bool:
    if not text:
        return True
    head = text.strip()[:160].lower()
    compliance_hits = [
        "understood",
        "acknowledged",
        "confirmed",
        "guidance only",
        "no external actions",
        "rule",
        "compliance",
    ]
    return any(hit in head for hit in compliance_hits)


def sanitize_response(text: str) -> str:
    if is_compliance_reply(text):
        return "Hi! Tell me what you want to accomplish and I’ll help."
    return text


def should_send_reply(user_id: str, response: str) -> bool:
    now = time.time()
    previous = _LAST_REPLY.get(user_id)
    if previous:
        last_text, last_ts = previous
        if response == last_text and (now - last_ts) < 60:
            return False
    _LAST_REPLY[user_id] = (response, now)
    return True


def is_allowed(user_id: str, channel_id: str, channel_type: str) -> bool:
    if ALLOW_USERS and user_id not in ALLOW_USERS:
        return False
    if channel_type == "im":
        return ALLOW_DMS
    if ALLOW_CHANNELS and channel_id not in ALLOW_CHANNELS:
        return False
    return True


if SIGNING_SECRET:
    app = App(token=BOT_TOKEN, signing_secret=SIGNING_SECRET)
else:
    app = App(token=BOT_TOKEN)


@app.event("app_mention")
def on_app_mention(event, say):
    if event.get("bot_id"):
        return
    text = normalize_text(event.get("text", ""))
    user = event.get("user", "")
    channel = event.get("channel", "")
    if not is_allowed(user, channel, event.get("channel_type", "")):
        log_line(f"app_mention blocked for user {user} in {channel}")
        return
    if not text:
        text = "Hello! How can I help?"
    log_line(f"app_mention from {user}: {text}")
    try:
        response = sanitize_response(run_openclaw(text))
    except Exception as exc:
        response = f"Clawdbot error: {exc}"
    try:
        user = event.get("user", "")
        if should_send_reply(user, response):
            app.client.chat_postMessage(
                channel=event.get("channel"),
                text=truncate(response),
            )
            log_line("app_mention reply sent")
        else:
            log_line("app_mention reply suppressed (duplicate)")
    except Exception as exc:
        log_line(f"app_mention send failed: {exc}")


@app.event("message")
def on_message(event, say):
    if event.get("subtype") or event.get("bot_id"):
        return
    if event.get("channel_type") != "im":
        return
    text = normalize_text(event.get("text", ""))
    user = event.get("user", "")
    channel = event.get("channel", "")
    if not is_allowed(user, channel, "im"):
        log_line(f"dm blocked for user {user} in {channel}")
        return
    if not text:
        text = "Hello! How can I help?"
    log_line(f"dm from {user}: {text}")
    try:
        response = sanitize_response(run_openclaw(text))
    except Exception as exc:
        response = f"Clawdbot error: {exc}"
    try:
        if should_send_reply(user, response):
            app.client.chat_postMessage(
                channel=event.get("channel"),
                text=truncate(response),
            )
            log_line("dm reply sent")
        else:
            log_line("dm reply suppressed (duplicate)")
    except Exception as exc:
        log_line(f"dm send failed: {exc}")


@app.command("/claw")
def on_slash_claw(ack, body):
    ack("Working on it…")
    user = body.get("user_id", "")
    channel = body.get("channel_id", "")
    text = normalize_text(body.get("text", ""))
    if not is_allowed(user, channel, body.get("channel_type", "")):
        app.client.chat_postEphemeral(
            channel=channel,
            user=user,
            text="Clawdbot: you are not authorized for this command.",
        )
        return
    if not text:
        text = "Hello! How can I help?"
    log_line(f"slash command from {user} in {channel}: {text}")
    try:
        response = sanitize_response(run_openclaw(text))
    except Exception as exc:
        response = f"Clawdbot error: {exc}"
    if should_send_reply(user, response):
        app.client.chat_postMessage(channel=channel, text=truncate(response))
    else:
        log_line("slash reply suppressed (duplicate)")


if __name__ == "__main__":
    log_line(
        "clawdbot slack bot starting "
        f"(agent={OPENCLAW_AGENT}, allow_users={len(ALLOW_USERS)}, "
        f"allow_channels={len(ALLOW_CHANNELS)}, allow_dms={ALLOW_DMS})"
    )
    handler = SocketModeHandler(app, APP_TOKEN)
    handler.start()

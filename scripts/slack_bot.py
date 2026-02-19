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
from typing import Dict, Tuple, Optional
import sys
import time
from datetime import datetime
from pathlib import Path

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError
try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None


BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "").strip()
APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "").strip()
SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "").strip()

if not BOT_TOKEN or not APP_TOKEN:
    raise SystemExit("Missing SLACK_BOT_TOKEN or SLACK_APP_TOKEN. See integrations/slack/README.md")

OPENCLAW_AGENT = os.environ.get("CLAWDBOT_AGENT", "orchestrator")
OPENCLAW_BIN = os.environ.get("OPENCLAW_BIN", "").strip()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
CODEX_MODEL = os.environ.get("CODEX_MODEL", "gpt-4o-mini").strip()
ALLOW_USERS = {u.strip() for u in os.environ.get("CLAWDBOT_ALLOW_USERS", "").split(",") if u.strip()}
ALLOW_CHANNELS = {c.strip() for c in os.environ.get("CLAWDBOT_ALLOW_CHANNELS", "").split(",") if c.strip()}
ALLOW_DMS = os.environ.get("CLAWDBOT_ALLOW_DMS", "true").strip().lower() in {"1", "true", "yes"}
DM_ONLY = os.environ.get("CLAWDBOT_DM_ONLY", "false").strip().lower() in {"1", "true", "yes"}
CODEX_DEFAULT = os.environ.get("CLAWDBOT_CODEX_DEFAULT", "false").strip().lower() in {"1", "true", "yes"}
DISABLE_OPENCLAW = os.environ.get("CLAWDBOT_DISABLE_OPENCLAW", "false").strip().lower() in {"1", "true", "yes"}
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
REPO_ROOT = Path(os.environ.get("CLAWDBOT_REPO_ROOT", r"C:\Users\natha\dev\repos\agent-ops"))

LOG_LEVEL = os.environ.get("CLAWDBOT_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler(sys.stdout)],
)
logging.getLogger("slack_bolt").setLevel(logging.INFO)
logging.getLogger("slack_bolt.socket_mode").setLevel(logging.INFO)

_LAST_REPLY: Dict[str, Tuple[str, float]] = {}
_PENDING_APPROVALS: Dict[str, Dict[str, str]] = {}


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


def run_codex(user_text: str) -> str:
    if not OPENAI_API_KEY:
        return "Clawdbot error: OPENAI_API_KEY is not set."
    if OpenAI is None:
        return "Clawdbot error: openai package not installed."
    context = build_codex_context()
    system = (
        "You are Codex, the supervisor for the jcw-agent-ops repo. "
        "Use the repo context below. Be specific and actionable. "
        "Avoid generic helpdesk language. If something is missing, ask a precise question."
    )
    prompt = f"{SAFE_PREFIX}\n\n{context}".strip()
    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = client.responses.create(
            model=CODEX_MODEL,
            input=[
                {"role": "system", "content": system},
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_text},
            ],
        )
    except Exception as exc:
        return f"Clawdbot error: {exc}"
    return getattr(response, "output_text", "").strip() or "No response."


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
        return "Hi! Tell me what you want to accomplish and I'll help."
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


def _extract_section(text: str, header: str) -> str:
    pattern = rf"\\*\\*{re.escape(header)}\\*\\*\\r?\\n(.*?)(\\r?\\n\\*\\*|\\Z)"
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        return ""
    section = match.group(1).strip()
    lines = [line for line in section.splitlines() if line.strip()]
    return "\n".join(lines[:8])


def render_sprint_summary() -> str:
    sprint_path = REPO_ROOT / "SPRINT_BOARD.md"
    if not sprint_path.exists():
        return "Sprint board not found."
    text = sprint_path.read_text(encoding="utf-8", errors="ignore")
    lane_match = re.search(r"\\*\\*Lane Summaries.*?\\*\\*\\r?\\n(.*?)\\r?\\n---", text, flags=re.DOTALL)
    lane_lines = ""
    if lane_match:
        lane_lines = "\n".join(
            [line for line in lane_match.group(1).splitlines() if line.strip()]
        ).strip()
    ready = _extract_section(text, "Ready")
    in_progress = _extract_section(text, "In Progress")
    blocked = _extract_section(text, "Blocked")
    done = _extract_section(text, "Done")
    parts = []
    if lane_lines:
        parts.append("Lane summaries:\n" + lane_lines)
    if ready:
        parts.append("Ready:\n" + ready)
    if in_progress:
        parts.append("In Progress:\n" + in_progress)
    if blocked:
        parts.append("Blocked:\n" + blocked)
    if done:
        parts.append("Done:\n" + done)
    if parts:
        return "\n\n".join(parts)
    # Debug hint for troubleshooting in Slack
    head = "\n".join([line for line in text.splitlines()[:6] if line.strip()])
    return f"Sprint board is empty. Path: {sprint_path}\nFirst lines:\n{head}"


def strip_ansi(text: str) -> str:
    # Remove ANSI escape sequences and control characters
    text = re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)
    # Remove common leftover terminal fragments (e.g. "[?25l", "[90m")
    text = re.sub(r"\[\?[0-9]+[a-zA-Z]", "", text)
    text = re.sub(r"\[[0-9;]{1,5}m", "", text)
    return text


def render_digest_summary() -> str:
    digest_root = REPO_ROOT / "research" / "digests" / "daily"
    if not digest_root.exists():
        return "No research digest folder found."
    digests = sorted(digest_root.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not digests:
        return "No research digests found."
    latest = digests[0]
    lines = latest.read_text(encoding="utf-8", errors="ignore").splitlines()
    cleaned = []
    for line in lines:
        line = strip_ansi(line).strip()
        if not line:
            continue
        if re.fullmatch(r"[\|\-_=*`]+", line):
            continue
        lower = line.lower()
        if "temporary outage" in lower or "web fetching" in lower or "api restored" in lower:
            continue
        cleaned.append(line)
    preview = "\n".join(cleaned[:12]).strip()
    return f"Latest digest: {latest.name}\n\n{preview}" if preview else f"Latest digest: {latest.name}"


def maybe_local_response(text: str) -> Optional[str]:
    t = (text or "").lower()
    if not t:
        return None
    if "digest" in t:
        return render_digest_summary()
    if any(key in t for key in ["summarize", "summary", "today", "sprint", "board", "backlog", "sumerize", "summerize"]):
        return render_sprint_summary()
    return None


def parse_route(text: str) -> Tuple[str, str]:
    cleaned = normalize_text(text)
    if not cleaned:
        return ("codex" if CODEX_DEFAULT else "claw", "Hello! How can I help?")
    match = re.match(r"^\s*(codex|claw)\s*[:\-]?\s*(.*)$", cleaned, flags=re.IGNORECASE)
    if match:
        route = match.group(1).lower()
        payload = match.group(2).strip() or "Hello! How can I help?"
        return route, payload
    return ("codex" if CODEX_DEFAULT else "claw", cleaned)


def _load_context_snippet(path: Path, max_chars: int = 1800) -> str:
    if not path.exists():
        return ""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    snippet = raw.strip()[:max_chars]
    return snippet


def build_codex_context() -> str:
    parts = [f"Repo root: {REPO_ROOT}"]
    for name in ["SUPERVISOR_MEMORY.md", "SUPERVISOR_BACKLOG.md", "SPRINT_BOARD.md", "RUNBOOK.md"]:
        path = REPO_ROOT / name
        snippet = _load_context_snippet(path)
        if snippet:
            parts.append(f"\n[{name}]\n{snippet}")
    return "\n".join(parts)


def build_approval_blocks(task: str, requester: str) -> list:
    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Approval requested*\nTask: {task}"},
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"Requested by <@{requester}>"}],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "style": "primary",
                    "action_id": "claw_approve",
                    "value": "approve",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject"},
                    "style": "danger",
                    "action_id": "claw_reject",
                    "value": "reject",
                },
            ],
        },
    ]


def request_approval(channel: str, requester: str, task: str) -> str:
    try:
        result = app.client.chat_postMessage(
            channel=channel,
            text=f"Approval requested: {task}",
            blocks=build_approval_blocks(task, requester),
        )
    except SlackApiError as exc:
        if exc.response.get("error") == "not_in_channel":
            try:
                app.client.conversations_join(channel=channel)
                result = app.client.chat_postMessage(
                    channel=channel,
                    text=f"Approval requested: {task}",
                    blocks=build_approval_blocks(task, requester),
                )
            except SlackApiError:
                return "I need to be added to this channel or granted `conversations:join` scope."
        else:
            return f"Approval error: {exc.response.get('error')}"
    message_ts = result.get("ts")
    if message_ts:
        _PENDING_APPROVALS[message_ts] = {"task": task, "requester": requester, "channel": channel}
    return "Approval requested. Click Approve or Reject."


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
    if DM_ONLY:
        log_line("app_mention ignored (DM-only mode)")
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
        if text.lower().startswith(("approve:", "request:")):
            task = text.split(":", 1)[1].strip() or "Unspecified task"
            response = request_approval(channel, user, task)
        else:
            route, payload = parse_route(text)
            if route == "codex":
                response = sanitize_response(run_codex(payload))
            else:
                local = maybe_local_response(payload)
                if local:
                    response = local
                elif DISABLE_OPENCLAW:
                    response = "OpenClaw is disabled. Use the `codex:` prefix."
                else:
                    response = sanitize_response(run_openclaw(payload))
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
        if text.lower().startswith(("approve:", "request:")):
            task = text.split(":", 1)[1].strip() or "Unspecified task"
            response = request_approval(channel, user, task)
        else:
            route, payload = parse_route(text)
            if route == "codex":
                response = sanitize_response(run_codex(payload))
            else:
                local = maybe_local_response(payload)
                if local:
                    response = local
                elif DISABLE_OPENCLAW:
                    response = "OpenClaw is disabled. Use the `codex:` prefix."
                else:
                    response = sanitize_response(run_openclaw(payload))
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
def on_slash_claw(ack, body, respond):
    ack("Working on it...")
    if DM_ONLY:
        respond(text="DM-only mode enabled. Please DM me instead.", response_type="ephemeral")
        return
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
        if text.lower().startswith("approve "):
            task = text.split(" ", 1)[1].strip() or "Unspecified task"
            response = request_approval(channel, user, task)
        else:
            route, payload = parse_route(text)
            if route == "codex":
                response = sanitize_response(run_codex(payload))
            else:
                local = maybe_local_response(payload)
                if local:
                    response = local
                elif DISABLE_OPENCLAW:
                    response = "OpenClaw is disabled. Use the `codex:` prefix."
                else:
                    response = sanitize_response(run_openclaw(payload))
    except Exception as exc:
        response = f"Clawdbot error: {exc}"
    if should_send_reply(user, response):
        try:
            respond(text=truncate(response), response_type="in_channel")
            log_line("slash reply sent via respond")
        except Exception as exc:
            log_line(f"slash respond failed: {exc}")
            try:
                app.client.chat_postMessage(channel=channel, text=truncate(response))
                log_line("slash reply sent via chat_postMessage")
            except Exception as exc2:
                log_line(f"slash reply failed: {exc2}")
    else:
        log_line("slash reply suppressed (duplicate)")


@app.action("claw_approve")
def on_claw_approve(ack, body):
    ack()
    message = body.get("message", {})
    message_ts = message.get("ts")
    if not message_ts or message_ts not in _PENDING_APPROVALS:
        return
    payload = _PENDING_APPROVALS.pop(message_ts)
    task = payload["task"]
    channel = payload["channel"]
    try:
        response = sanitize_response(run_openclaw(f"APPROVED TASK: {task}"))
    except Exception as exc:
        response = f"Clawdbot error: {exc}"
    app.client.chat_postMessage(channel=channel, text=truncate(response))


@app.action("claw_reject")
def on_claw_reject(ack, body):
    ack()
    message = body.get("message", {})
    message_ts = message.get("ts")
    if message_ts and message_ts in _PENDING_APPROVALS:
        _PENDING_APPROVALS.pop(message_ts, None)


if __name__ == "__main__":
    log_line(
        "clawdbot slack bot starting "
        f"(agent={OPENCLAW_AGENT}, allow_users={len(ALLOW_USERS)}, "
        f"allow_channels={len(ALLOW_CHANNELS)}, allow_dms={ALLOW_DMS})"
    )
    handler = SocketModeHandler(app, APP_TOKEN)
    handler.start()

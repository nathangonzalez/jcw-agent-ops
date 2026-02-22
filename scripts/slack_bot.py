#!/usr/bin/env python
"""
Slack Socket Mode bot bridge for Clawdbot.
Responds to app mentions and direct messages using OpenClaw.
"""

import json
import os
import subprocess
import shutil
import logging
import re
import threading
from typing import Dict, Tuple, Optional
import sys
import time
from datetime import datetime
from pathlib import Path

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError
from urllib.request import Request, urlopen
from urllib.error import URLError
try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None


BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "").strip()
APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "").strip()
SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "").strip()
BOT_MODE = os.environ.get("CLAWDBOT_MODE", "socket").strip().lower()

if not BOT_TOKEN:
    raise SystemExit("Missing SLACK_BOT_TOKEN. See integrations/slack/README.md")
if BOT_MODE == "socket" and not APP_TOKEN:
    raise SystemExit("Missing SLACK_APP_TOKEN (Socket Mode). See integrations/slack/README.md")
if BOT_MODE != "socket" and not SIGNING_SECRET:
    raise SystemExit("Missing SLACK_SIGNING_SECRET (HTTP mode). See integrations/slack/README.md")

OPENCLAW_AGENT = os.environ.get("CLAWDBOT_AGENT", "orchestrator")
OPENCLAW_BIN = os.environ.get("OPENCLAW_BIN", "").strip()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
CODEX_MODEL = os.environ.get("CODEX_MODEL", "gpt-4o-mini").strip()
CODE_MODE_ENABLED = os.environ.get("CLAWDBOT_CODE_MODE", "true").strip().lower() in {"1", "true", "yes"}
EXEC_MODE_ENABLED = os.environ.get("CLAWDBOT_EXEC_MODE", "true").strip().lower() in {"1", "true", "yes"}
ALLOW_USERS = {u.strip() for u in os.environ.get("CLAWDBOT_ALLOW_USERS", "").split(",") if u.strip()}
ALLOW_CHANNELS = {c.strip() for c in os.environ.get("CLAWDBOT_ALLOW_CHANNELS", "").split(",") if c.strip()}
ALLOW_DMS = os.environ.get("CLAWDBOT_ALLOW_DMS", "true").strip().lower() in {"1", "true", "yes"}
DM_ONLY = os.environ.get("CLAWDBOT_DM_ONLY", "false").strip().lower() in {"1", "true", "yes"}
CODEX_DEFAULT = os.environ.get("CLAWDBOT_CODEX_DEFAULT", "false").strip().lower() in {"1", "true", "yes"}
DISABLE_OPENCLAW = os.environ.get("CLAWDBOT_DISABLE_OPENCLAW", "false").strip().lower() in {"1", "true", "yes"}
OPEN_CHAT = os.environ.get("CLAWDBOT_OPEN_CHAT", "false").strip().lower() in {"1", "true", "yes"}
CHANNEL_PREFIX = os.environ.get("CLAWDBOT_CHANNEL_PREFIX", "").strip()
EXEC_TIMEOUT = int(os.environ.get("CLAWDBOT_EXEC_TIMEOUT", "45"))
EXEC_ALLOW_DESTRUCTIVE = os.environ.get("CLAWDBOT_EXEC_ALLOW_DESTRUCTIVE", "false").strip().lower() in {"1", "true", "yes"}
REPO_MAP_RAW = os.environ.get("CLAWDBOT_REPO_MAP", "").strip()
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
ANTHROPIC_USAGE_LOG = LOG_DIR / "anthropic_usage.log"
REPO_ROOT = Path(os.environ.get("CLAWDBOT_REPO_ROOT", r"C:\Users\natha\dev\repos\agent-ops"))
_EXEC_CWD_RAW = os.environ.get("CLAWDBOT_EXEC_CWD", "").strip()
EXEC_CWD = Path(_EXEC_CWD_RAW).expanduser() if _EXEC_CWD_RAW else REPO_ROOT
RELAY_DIR = Path(os.environ.get("CLAWDBOT_RELAY_DIR", str(LOG_DIR / "relay")))
RELAY_DIR.mkdir(parents=True, exist_ok=True)
RELAY_URL = os.environ.get("CLAWDBOT_RELAY_URL", "http://127.0.0.1:8092").strip()
QUEUE_PATH = Path(os.environ.get("CLAWDBOT_QUEUE_PATH", str(REPO_ROOT / "tasks" / "approval_queue.json")))
QUEUE_CHANNEL = os.environ.get("CLAWDBOT_QUEUE_CHANNEL", "").strip()
QUEUE_INTERVAL = int(os.environ.get("CLAWDBOT_QUEUE_INTERVAL", "3600"))
ANTHROPIC_USAGE_ENABLED = os.environ.get("CLAWDBOT_ANTHROPIC_USAGE", "true").strip().lower() in {"1", "true", "yes"}

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
_PENDING_CODE: Dict[str, Dict[str, str]] = {}
_PENDING_CODE_BY_JOB: Dict[str, Dict[str, str]] = {}
_CODE_STATUS: Dict[str, Dict[str, str]] = {}
_PENDING_EXEC: Dict[str, Dict[str, str]] = {}
_EXEC_STATUS: Dict[str, Dict[str, str]] = {}


def _parse_repo_map(raw: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for entry in (raw or "").split(";"):
        entry = entry.strip()
        if not entry or "=" not in entry:
            continue
        name, path = entry.split("=", 1)
        name = name.strip().lower()
        path = path.strip()
        if name and path:
            out[name] = path
    return out


REPO_MAP = _parse_repo_map(REPO_MAP_RAW)


def log_line(message: str):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}"
    log_path = LOG_DIR / "clawdbot_slack.log"
    log_path.write_text(log_path.read_text() + line + "\n" if log_path.exists() else line + "\n")
    print(line, flush=True)


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, int(len(text) / 4))


def log_anthropic_usage(prompt: str, output: str) -> None:
    if not ANTHROPIC_USAGE_ENABLED:
        return
    prompt_tokens = estimate_tokens(prompt)
    output_tokens = estimate_tokens(output)
    total_tokens = prompt_tokens + output_tokens
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = (
        f"[{ts}] model=openclaw/{OPENCLAW_AGENT} "
        f"prompt={prompt_tokens} output={output_tokens} total={total_tokens} estimated=1\n"
    )
    ANTHROPIC_USAGE_LOG.write_text(
        ANTHROPIC_USAGE_LOG.read_text() + line if ANTHROPIC_USAGE_LOG.exists() else line
    )


def _load_queue() -> list:
    if not QUEUE_PATH.exists():
        return []
    try:
        return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_queue(items: list) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps(items, indent=2))


def _extract_queue_id(task: str) -> str:
    match = re.search(r"\[(Q-[^\]]+)\]", task or "")
    if match:
        return match.group(1)
    match = re.search(r"\bQ-\d{8}-\d{6}\b", task or "")
    return match.group(0) if match else ""


def _strip_queue_prefix(task: str) -> str:
    if not task:
        return ""
    cleaned = re.sub(r"^\s*\[Q-[^\]]+\]\s*", "", task).strip()
    return cleaned


def mark_queue_status(task: str, status: str) -> None:
    qid = _extract_queue_id(task)
    if not qid:
        return
    items = _load_queue()
    changed = False
    for item in items:
        if item.get("id") == qid:
            item["status"] = status
            if status == "approved":
                item["approved_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            changed = True
            break
    if changed:
        _save_queue(items)


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
        return f"Clawdbot error: {(proc.stderr or '').strip() or 'unknown error'}"
    log_line(f"openclaw ok in {elapsed:.1f}s")
    output = (proc.stdout or "").strip()
    log_anthropic_usage(prompt, output)
    return output


def run_codex(user_text: str, relay_context: str = "") -> str:
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
    if relay_context:
        prompt = f"{prompt}\n\n[Relay Context]\n{relay_context}".strip()
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
    usage = getattr(response, "usage", None)
    if usage:
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)
        # Newer Responses API fields
        if prompt_tokens is None:
            prompt_tokens = getattr(usage, "input_tokens", None)
        if output_tokens is None:
            output_tokens = getattr(usage, "output_tokens", None) or getattr(usage, "output_tokens_total", None)
        if total_tokens is None and prompt_tokens is not None and output_tokens is not None:
            total_tokens = prompt_tokens + output_tokens
        if prompt_tokens is not None or output_tokens is not None or total_tokens is not None:
            usage_path = LOG_DIR / "codex_usage.log"
            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            line = f"[{ts}] model={CODEX_MODEL} prompt={prompt_tokens or 0} output={output_tokens or 0} total={total_tokens or 0}\n"
            usage_path.write_text(
                usage_path.read_text() + line if usage_path.exists() else line
            )
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


def render_queue_summary() -> str:
    items = _load_queue()
    if not items:
        return "Approval queue is empty."
    lines = ["Approval queue:"]
    for item in items:
        lines.append(f"- {item.get('id')} | {item.get('status')} | {item.get('task')}")
    return "\n".join(lines)


def queue_tick():
    if not QUEUE_INTERVAL:
        return
    while True:
        try:
            items = _load_queue()
            changed = False
            for item in items:
                if item.get("status") != "pending":
                    continue
                if item.get("posted_at"):
                    continue
                channel = item.get("channel") or QUEUE_CHANNEL
                if not channel:
                    continue
                task = item.get("task") or ""
                qid = item.get("id") or ""
                label = f"[{qid}] {task}".strip()
                message_ts = request_approval_job(channel, "queue", label)
                if message_ts:
                    item["posted_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                    item["status"] = "queued"
                    changed = True
            if changed:
                _save_queue(items)
        except Exception as exc:
            log_line(f"queue_tick error: {exc}")
        time.sleep(QUEUE_INTERVAL)

def maybe_local_response(text: str) -> Optional[str]:
    t = (text or "").lower()
    if not t:
        return None
    if t.startswith("queue"):
        return render_queue_summary()
    if "uat" in t and "checklist" in t:
        return "\n".join(
            [
                "UAT checklist:",
                "- Suite dashboard: open /suite and verify sprint/backlog/ops panels load.",
                "- Monitor: confirm 15-min report hits #jcw_bot (timer active).",
                "- Payroll reconcile: run payroll_reconcile.py against exports + app.db and review deltas.",
            ]
        )
    if t.startswith("/latest") or "latest" in t or "what's the latest" in t or "whats the latest" in t:
        summary = []
        summary.append("Latest summary:")
        summary.append(render_sprint_summary())
        return "\n".join(summary)
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


def is_code_request(text: str) -> bool:
    if not text:
        return False
    lower = text.lower().strip()
    return lower.startswith("code ") or lower.startswith("code:") or lower.startswith("implement ") or lower.startswith("implement:")


def is_exec_request(text: str) -> bool:
    if not text:
        return False
    lower = text.lower().strip()
    return lower.startswith(("exec ", "exec:", "shell ", "shell:", "cmd ", "cmd:"))


def extract_exec_command(text: str) -> str:
    cleaned = text.strip()
    parts = re.split(r"^(exec|shell|cmd)\s*[: ]\s*", cleaned, flags=re.IGNORECASE)
    if len(parts) >= 3:
        return parts[2].strip()
    return cleaned


def extract_exec_target(text: str) -> Tuple[Optional[str], str]:
    cmd = extract_exec_command(text)
    repo = None
    match = re.match(r"^repo\s*=\s*([^;]+);?\s*(.*)$", cmd, flags=re.IGNORECASE)
    if match:
        repo = match.group(1).strip().lower()
        cmd = match.group(2).strip()
    return repo, cmd


def is_destructive_command(cmd: str) -> bool:
    lowered = cmd.lower()
    danger = [
        "rm -rf",
        "rm -r",
        "shutdown",
        "reboot",
        "mkfs",
        "dd if=",
        "format ",
        "del /f",
    ]
    return any(token in lowered for token in danger)


def run_exec_command(command: str, cwd: Optional[Path] = None) -> Tuple[str, str]:
    if not EXEC_MODE_ENABLED:
        return ("error", "Exec mode is disabled.")
    if not command:
        return ("error", "Missing command to execute.")
    if is_destructive_command(command) and not EXEC_ALLOW_DESTRUCTIVE:
        return ("error", "Command blocked: destructive commands require CLAWDBOT_EXEC_ALLOW_DESTRUCTIVE=true.")
    cwd = cwd if cwd and cwd.exists() else (EXEC_CWD if EXEC_CWD and EXEC_CWD.exists() else REPO_ROOT)
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=EXEC_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return ("error", f"Command timed out after {EXEC_TIMEOUT}s.")
    output = "\n".join([proc.stdout or "", proc.stderr or ""]).strip()
    output = output if output else "(no output)"
    status = "ok" if proc.returncode == 0 else "error"
    return (status, output)


def run_code_mode(request_text: str) -> Tuple[str, str]:
    """
    Run code mode generator. Returns (status, payload)
    status: ok|error
    payload: summary or error
    """
    if not CODE_MODE_ENABLED:
        return ("error", "Code mode is disabled.")
    try:
        from subprocess import run
    except Exception as exc:
        return ("error", f"Code mode error: {exc}")
    out_dir = LOG_DIR / "code_mode"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    work_dir = out_dir / ts
    work_dir.mkdir(parents=True, exist_ok=True)
    req_path = work_dir / "request.txt"
    req_path.write_text(request_text, encoding="utf-8")
    cmd = [
        "python3",
        str(REPO_ROOT / "scripts" / "code_mode.py"),
        "--request",
        str(req_path),
        "--out",
        str(work_dir),
    ]
    proc = run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return ("error", proc.stderr.strip() or "Code mode failed.")
    return ("ok", work_dir.name)


def _load_context_snippet(path: Path, max_chars: int = 1800) -> str:
    if not path.exists():
        return ""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    snippet = raw.strip()[:max_chars]
    return snippet


def build_codex_context() -> str:
    parts = [f"Repo root: {REPO_ROOT}", f"Today: {datetime.utcnow().strftime('%Y-%m-%d')}"]
    for name in [
        "SUPERVISOR_MEMORY.md",
        "SUPERVISOR_BACKLOG.md",
        "SPRINT_BOARD.md",
        "RUNBOOK.md",
        "PERSIST.txt",
    ]:
        path = REPO_ROOT / name
        snippet = _load_context_snippet(path)
        if snippet:
            parts.append(f"\n[{name}]\n{snippet}")
    return "\n".join(parts)


def relay_post(path: str, payload: dict, timeout: int = 6) -> Optional[dict]:
    if not RELAY_URL:
        return None
    try:
        data = json.dumps(payload).encode("utf-8")
        req = Request(f"{RELAY_URL}{path}", data=data, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except URLError:
        return None
    except Exception:
        return None


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


def request_approval_job(channel: str, requester: str, task: str) -> Optional[str]:
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
                return None
        else:
            return None
    message_ts = result.get("ts")
    if message_ts:
        _PENDING_APPROVALS[message_ts] = {"task": task, "requester": requester, "channel": channel}
    return message_ts


def request_approval(channel: str, requester: str, task: str) -> str:
    message_ts = request_approval_job(channel, requester, task)
    if not message_ts:
        return "Approval error: unable to post approval card."
    return "Approval requested. Click Approve or Reject."


def request_code_approval(channel: str, requester: str, job_id: str, summary: str) -> str:
    try:
        result = app.client.chat_postMessage(
            channel=channel,
            text=f"Code mode approval requested: {summary}",
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Code mode approval*\n{summary}"},
                },
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"Requested by <@{requester}> | Job {job_id}"}],
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Apply Patch"},
                            "style": "primary",
                            "action_id": "code_apply",
                            "value": job_id,
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Reject"},
                            "style": "danger",
                            "action_id": "code_reject",
                            "value": job_id,
                        },
                    ],
                },
            ],
        )
    except SlackApiError as exc:
        return f"Code approval error: {exc.response.get('error')}"
    message_ts = result.get("ts")
    if message_ts:
        _PENDING_CODE[message_ts] = {"job": job_id, "channel": channel}
        _PENDING_CODE_BY_JOB[job_id] = {"channel": channel, "message_ts": message_ts, "requester": requester}
        _CODE_STATUS[job_id] = {"status": "pending", "updated": datetime.utcnow().isoformat()}
    return "Code mode proposal ready. Click Apply Patch to proceed."


def request_exec_approval(channel: str, requester: str, command: str, repo: Optional[str] = None) -> str:
    job_id = f"exec-{int(time.time())}"
    repo_label = f"repo={repo}" if repo else "repo=default"
    try:
        result = app.client.chat_postMessage(
            channel=channel,
            text=f"Exec approval requested: {command}",
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Exec approval*\n`{command}`\n{repo_label}"},
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Requested by <@{requester}> | Job {job_id}",
                        }
                    ],
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Run Command"},
                            "style": "primary",
                            "action_id": "exec_apply",
                            "value": job_id,
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Reject"},
                            "style": "danger",
                            "action_id": "exec_reject",
                            "value": job_id,
                        },
                    ],
                },
            ],
        )
    except SlackApiError as exc:
        return f"Exec approval error: {exc.response.get('error')}"
    _PENDING_EXEC[job_id] = {
        "command": command,
        "repo": repo or "",
        "channel": channel,
        "requester": requester,
        "message_ts": result.get("ts"),
    }
    _EXEC_STATUS[job_id] = {"status": "pending", "updated": datetime.utcnow().isoformat()}
    return "Exec request queued. Click Run Command to proceed."


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
                if is_exec_request(payload):
                    repo, command = extract_exec_target(payload)
                    response = request_exec_approval(channel, user, command, repo=repo)
                elif is_code_request(payload):
                    status, result = run_code_mode(payload)
                    if status == "ok":
                        summary = f"Generated patch for request: {payload}"
                        response = request_code_approval(channel, user, result, summary)
                    else:
                        response = result
                else:
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
    channel_type = event.get("channel_type", "")
    text = normalize_text(event.get("text", ""))
    user = event.get("user", "")
    channel = event.get("channel", "")

    # DM flow
    relay_key_payload = {"channel_type": channel_type, "channel_id": channel, "user_id": user}
    if channel_type == "im":
        if not is_allowed(user, channel, "im"):
            log_line(f"dm blocked for user {user} in {channel}")
            return
        if not text:
            text = "Hello! How can I help?"
        log_line(f"dm from {user}: {text}")
    else:
        # Channel flow
        if DM_ONLY:
            return
        if not is_allowed(user, channel, channel_type):
            log_line(f"channel blocked for user {user} in {channel}")
            return
        if not text:
            return
        if not OPEN_CHAT:
            if CHANNEL_PREFIX and not text.lower().startswith(CHANNEL_PREFIX.lower()):
                return
        log_line(f"channel msg from {user} in {channel}: {text}")
    # Persist relay input (relay service)
    relay_post("/relay/message", {**relay_key_payload, "role": "user", "text": text})
    try:
        if text.lower().startswith(("approve:", "request:")):
            task = text.split(":", 1)[1].strip() or "Unspecified task"
            response = request_approval(channel, user, task)
        else:
            route, payload = parse_route(text)
            if route == "codex":
                if is_exec_request(payload):
                    repo, command = extract_exec_target(payload)
                    response = request_exec_approval(channel, user, command, repo=repo)
                elif is_code_request(payload):
                    status, result = run_code_mode(payload)
                    if status == "ok":
                        summary = f"Generated patch for request: {payload}"
                        response = request_code_approval(channel, user, result, summary)
                    else:
                        response = result
                else:
                    relay_context = ""
                    relay_ctx = relay_post("/relay/context", {**relay_key_payload, "limit": 20})
                    if relay_ctx:
                        summary = (relay_ctx.get("summary") or "").strip()
                        tail = relay_ctx.get("tail") or []
                        tail_lines = []
                        for row in tail:
                            role = row.get("role", "")
                            msg = row.get("text", "")
                            if msg:
                                tail_lines.append(f"{role}: {msg}")
                        relay_context = "\n".join([line for line in ([summary] + tail_lines) if line])
                    response = sanitize_response(run_codex(payload, relay_context=relay_context))
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
            relay_post("/relay/message", {**relay_key_payload, "role": "assistant", "text": response})
            if channel_type == "im":
                log_line("dm reply sent")
            else:
                log_line("channel reply sent")
        else:
            log_line("reply suppressed (duplicate)")
    except Exception as exc:
        log_line(f"send failed: {exc}")


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
                if is_exec_request(payload):
                    repo, command = extract_exec_target(payload)
                    response = request_exec_approval(channel, user, command, repo=repo)
                elif is_code_request(payload):
                    status, result = run_code_mode(payload)
                    if status == "ok":
                        summary = f"Generated patch for request: {payload}"
                        response = request_code_approval(channel, user, result, summary)
                    else:
                        response = result
                else:
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


def _extract_task_from_blocks(blocks: list) -> str:
    """Extract task text from approval card blocks (for orphan cards)."""
    for block in (blocks or []):
        if block.get("type") == "section":
            text_obj = block.get("text", {})
            raw = text_obj.get("text", "")
            for line in raw.split("\n"):
                line = line.strip()
                if line.lower().startswith("task:"):
                    return line.split(":", 1)[1].strip()
            cleaned = re.sub(r"\*+", "", raw).strip()
            if cleaned:
                return cleaned
    return "Unknown task"


@app.action("claw_approve")
def on_claw_approve(ack, body):
    ack()
    user_id = (body.get("user") or {}).get("id", "unknown")
    message = body.get("message", {})
    message_ts = message.get("ts")
    channel_info = body.get("channel", {})
    channel = channel_info.get("id") if isinstance(channel_info, dict) else str(channel_info or "")
    log_line(f"claw_approve clicked by {user_id} ts={message_ts} channel={channel}")
    if message_ts and message_ts in _PENDING_APPROVALS:
        payload = _PENDING_APPROVALS.pop(message_ts)
        task = payload.get("task") or "Unknown task"
        channel = payload.get("channel") or channel
        requester = payload.get("requester", "unknown")
    else:
        task = _extract_task_from_blocks(message.get("blocks", []))
        requester = "external"
        log_line(f"claw_approve: orphan card, extracted task={task}")
    if not channel:
        log_line("claw_approve: no channel, aborting")
        return
    try:
        mark_queue_status(task, "approved")
        raw_task = _strip_queue_prefix(task)
        if message_ts:
            try:
                app.client.chat_update(
                    channel=channel,
                    ts=message_ts,
                    text=f"Approved: {task}",
                    blocks=[
                        {"type": "section", "text": {"type": "mrkdwn", "text": f"✅ *Approved*\n{task}"}},
                        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"Approved by <@{user_id}> | Requested by <@{requester}>"}]},
                    ],
                )
                log_line("claw_approve: card updated")
            except Exception as exc:
                log_line(f"claw_approve: card update failed: {exc}")
        if raw_task.lower().startswith("exec:"):
            command = raw_task.split(":", 1)[1].strip()
            repo, cmd = extract_exec_target(f"exec {command}")
            cwd = None
            if repo:
                cwd = Path(REPO_MAP.get(repo.lower(), "")).expanduser()
            status, output = run_exec_command(cmd, cwd=cwd)
            response = f"Exec {status}:\n{output}"
        elif DISABLE_OPENCLAW:
            response = f"✅ Approved: {raw_task}\n(OpenClaw disabled — approval logged.)"
        else:
            response = sanitize_response(run_openclaw(f"APPROVED TASK: {raw_task}"))
        app.client.chat_postMessage(channel=channel, text=truncate(response))
        log_line("claw_approve: response posted")
    except Exception as exc:
        log_line(f"claw_approve error: {exc}")
        try:
            app.client.chat_postMessage(channel=channel, text=f"Approval error: {exc}")
        except Exception:
            pass


@app.action("claw_reject")
def on_claw_reject(ack, body):
    ack()
    user_id = (body.get("user") or {}).get("id", "unknown")
    message = body.get("message", {})
    message_ts = message.get("ts")
    channel_info = body.get("channel", {})
    channel = channel_info.get("id") if isinstance(channel_info, dict) else str(channel_info or "")
    log_line(f"claw_reject clicked by {user_id} ts={message_ts} channel={channel}")
    if message_ts and message_ts in _PENDING_APPROVALS:
        payload = _PENDING_APPROVALS.pop(message_ts, None)
        task = (payload or {}).get("task", "Unknown task")
        channel = (payload or {}).get("channel") or channel
    else:
        task = _extract_task_from_blocks(message.get("blocks", []))
        log_line(f"claw_reject: orphan card, extracted task={task}")
    if not channel:
        log_line("claw_reject: no channel, aborting")
        return
    mark_queue_status(task, "rejected")
    if message_ts:
        try:
            app.client.chat_update(
                channel=channel,
                ts=message_ts,
                text=f"Rejected: {task}",
                blocks=[
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"❌ *Rejected*\n{task}"}},
                    {"type": "context", "elements": [{"type": "mrkdwn", "text": f"Rejected by <@{user_id}>"}]},
                ],
            )
            log_line("claw_reject: card updated")
        except Exception as exc:
            log_line(f"claw_reject: card update failed: {exc}")


@app.action("code_apply")
def on_code_apply(ack, body):
    ack()
    message = body.get("message", {})
    message_ts = message.get("ts")
    user_id = body.get("user", {}).get("id")
    actions = body.get("actions") or []
    job_id = actions[0].get("value") if actions else None
    log_line(f"code_apply action by {user_id or 'unknown'} job={job_id or 'unknown'}")
    payload = None
    if message_ts and message_ts in _PENDING_CODE:
        payload = _PENDING_CODE.pop(message_ts)
        job_id = job_id or payload.get("job")
    if not payload and job_id and job_id in _PENDING_CODE_BY_JOB:
        payload = _PENDING_CODE_BY_JOB[job_id]
    if not job_id or not payload:
        if user_id and message_ts:
            app.client.chat_postEphemeral(
                channel=payload["channel"] if payload else body.get("channel", {}).get("id"),
                user=user_id,
                text="That patch request is no longer pending.",
            )
        log_line("code_apply ignored (no pending job)")
        return
    channel = payload["channel"]
    status = _CODE_STATUS.get(job_id, {}).get("status")
    if status in {"applying", "applied"}:
        if user_id:
            app.client.chat_postEphemeral(
                channel=channel,
                user=user_id,
                text=f"Patch already {status}.",
            )
        log_line(f"code_apply ignored (status={status})")
        return
    _CODE_STATUS[job_id] = {"status": "applying", "updated": datetime.utcnow().isoformat()}
    try:
        if message_ts:
            app.client.chat_update(
                channel=channel,
                ts=message_ts,
                text="Applying patch...",
                blocks=[
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"*Applying patch*\nJob {job_id}"}},
                ],
            )
    except Exception:
        pass
    try:
        from subprocess import run
        cmd = [
            "python3",
            str(REPO_ROOT / "scripts" / "code_mode_apply.py"),
            "--job",
            str((LOG_DIR / "code_mode" / job_id)),
        ]
        proc = run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            _CODE_STATUS[job_id] = {"status": "failed", "updated": datetime.utcnow().isoformat()}
            _PENDING_CODE_BY_JOB.pop(job_id, None)
            app.client.chat_postMessage(channel=channel, text=f"Code apply failed: {proc.stderr.strip()}")
            log_line(f"code_apply failed (job={job_id}): {proc.stderr.strip()}")
            return
        _CODE_STATUS[job_id] = {"status": "applied", "updated": datetime.utcnow().isoformat()}
        _PENDING_CODE_BY_JOB.pop(job_id, None)
        app.client.chat_postMessage(channel=channel, text=proc.stdout.strip() or "Code patch applied.")
        log_line(f"code_apply ok (job={job_id})")
        if message_ts:
            try:
                app.client.chat_update(
                    channel=channel,
                    ts=message_ts,
                    text="Patch applied.",
                    blocks=[
                        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Patch applied*\nJob {job_id}"}},
                    ],
                )
            except Exception:
                pass
    except Exception as exc:
        _CODE_STATUS[job_id] = {"status": "failed", "updated": datetime.utcnow().isoformat()}
        _PENDING_CODE_BY_JOB.pop(job_id, None)
        app.client.chat_postMessage(channel=channel, text=f"Code apply error: {exc}")
        log_line(f"code_apply exception (job={job_id}): {exc}")


@app.action("code_reject")
def on_code_reject(ack, body):
    ack()
    message = body.get("message", {})
    message_ts = message.get("ts")
    job_id = None
    if message_ts and message_ts in _PENDING_CODE:
        job_id = _PENDING_CODE.get(message_ts, {}).get("job")
        _PENDING_CODE.pop(message_ts, None)
    actions = body.get("actions") or []
    if actions:
        job_id = job_id or actions[0].get("value")
    if job_id:
        _CODE_STATUS[job_id] = {"status": "rejected", "updated": datetime.utcnow().isoformat()}
        _PENDING_CODE_BY_JOB.pop(job_id, None)


@app.action("exec_apply")
def on_exec_apply(ack, body):
    ack()
    actions = body.get("actions") or []
    job_id = actions[0].get("value") if actions else None
    user_id = body.get("user", {}).get("id")
    if not job_id or job_id not in _PENDING_EXEC:
        if user_id:
            app.client.chat_postEphemeral(
                channel=body.get("channel", {}).get("id"),
                user=user_id,
                text="That exec request is no longer pending.",
            )
        log_line("exec_apply ignored (no pending job)")
        return
    payload = _PENDING_EXEC[job_id]
    channel = payload["channel"]
    status = _EXEC_STATUS.get(job_id, {}).get("status")
    if status in {"running", "done"}:
        if user_id:
            app.client.chat_postEphemeral(
                channel=channel,
                user=user_id,
                text=f"Exec already {status}.",
            )
        log_line(f"exec_apply ignored (status={status})")
        return
    _EXEC_STATUS[job_id] = {"status": "running", "updated": datetime.utcnow().isoformat()}
    message_ts = payload.get("message_ts")
    try:
        if message_ts:
            app.client.chat_update(
                channel=channel,
                ts=message_ts,
                text="Running command...",
                blocks=[
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"*Running command*\nJob {job_id}"}},
                ],
            )
    except Exception:
        pass
    command = payload.get("command", "")
    repo = (payload.get("repo") or "").strip().lower()
    cwd = None
    if repo:
        repo_path = REPO_MAP.get(repo)
        if not repo_path:
            app.client.chat_postMessage(channel=channel, text=f"Unknown repo '{repo}'. Update CLAWDBOT_REPO_MAP.")
            _EXEC_STATUS[job_id] = {"status": "failed", "updated": datetime.utcnow().isoformat()}
            _PENDING_EXEC.pop(job_id, None)
            log_line(f"exec_apply failed (unknown repo={repo})")
            return
        cwd = Path(repo_path)
    log_line(f"exec_apply action by {user_id or 'unknown'} job={job_id} cmd={command}")
    try:
        result_status, output = run_exec_command(command, cwd=cwd)
        _EXEC_STATUS[job_id] = {"status": "done", "updated": datetime.utcnow().isoformat()}
        _PENDING_EXEC.pop(job_id, None)
        body_text = "\n".join(
            [
                f"*Exec result* ({result_status})",
                f"`{command}`",
                "```",
                truncate(output, 2800),
                "```",
            ]
        )
        app.client.chat_postMessage(channel=channel, text=body_text)
        log_line(f"exec_apply ok (job={job_id})")
        if message_ts:
            try:
                app.client.chat_update(
                    channel=channel,
                    ts=message_ts,
                    text="Command completed.",
                    blocks=[
                        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Command completed*\nJob {job_id}"}},
                    ],
                )
            except Exception:
                pass
    except Exception as exc:
        _EXEC_STATUS[job_id] = {"status": "failed", "updated": datetime.utcnow().isoformat()}
        _PENDING_EXEC.pop(job_id, None)
        app.client.chat_postMessage(channel=channel, text=f"Exec error: {exc}")
        log_line(f"exec_apply exception (job={job_id}): {exc}")


@app.action("exec_reject")
def on_exec_reject(ack, body):
    ack()
    actions = body.get("actions") or []
    job_id = actions[0].get("value") if actions else None
    if job_id:
        _EXEC_STATUS[job_id] = {"status": "rejected", "updated": datetime.utcnow().isoformat()}
        _PENDING_EXEC.pop(job_id, None)


if __name__ == "__main__":
    log_line(
        "clawdbot slack bot starting "
        f"(agent={OPENCLAW_AGENT}, allow_users={len(ALLOW_USERS)}, "
        f"allow_channels={len(ALLOW_CHANNELS)}, allow_dms={ALLOW_DMS})"
    )
    if QUEUE_INTERVAL:
        thread = threading.Thread(target=queue_tick, daemon=True)
        thread.start()
    if BOT_MODE in {"http", "web", "cloudrun"}:
        try:
            from flask import Flask, request
            from slack_bolt.adapter.flask import SlackRequestHandler
        except Exception as exc:
            raise SystemExit(f"Missing Flask adapter dependencies: {exc}")
        flask_app = Flask(__name__)
        handler = SlackRequestHandler(app)

        @flask_app.route("/slack/events", methods=["POST"])
        def slack_events():
            return handler.handle(request)

        @flask_app.route("/health", methods=["GET"])
        def health():
            return ("ok", 200)

        port = int(os.environ.get("PORT", "8080"))
        flask_app.run(host="0.0.0.0", port=port)
    else:
        handler = SocketModeHandler(app, APP_TOKEN)
        handler.start()

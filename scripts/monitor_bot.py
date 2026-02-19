#!/usr/bin/env python
"""
Hourly monitoring report for Clawbot.
Posts a summary to Slack using the bot token.
"""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from slack_sdk import WebClient


LOG_DIR = Path(os.environ.get("CLAWDBOT_LOG_DIR", "/opt/agent-ops/agent_outputs"))
CHANNEL = os.environ.get("CLAWDBOT_MONITOR_CHANNEL", "#jcw_bot")
BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "").strip()


def read_recent_lines(path: Path, since: datetime):
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    recent = []
    for line in lines:
        if not line.startswith("[") or "]" not in line:
            continue
        ts_str = line[1:20]
        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if ts >= since:
            recent.append(line)
    return recent


def main():
    if not BOT_TOKEN:
        raise SystemExit("Missing SLACK_BOT_TOKEN")

    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=1)

    slack_log = LOG_DIR / "clawdbot_slack.log"
    runtime_log = LOG_DIR / "clawdbot_slack_runtime.log"

    recent = read_recent_lines(slack_log, since)
    errors = 0
    replies = 0
    mentions = 0
    dms = 0
    for line in recent:
        lower = line.lower()
        if "error" in lower:
            errors += 1
        if "reply sent" in lower:
            replies += 1
        if "app_mention" in lower:
            mentions += 1
        if "dm from" in lower:
            dms += 1

    runtime_recent = read_recent_lines(runtime_log, since)
    runtime_errors = sum(1 for line in runtime_recent if "error" in line.lower())

    usage_log = LOG_DIR / "codex_usage.log"
    usage_recent = read_recent_lines(usage_log, since)
    prompt_tokens = 0
    output_tokens = 0
    for line in usage_recent:
        parts = line.split()
        for part in parts:
            if part.startswith("prompt="):
                prompt_tokens += int(part.split("=", 1)[1])
            if part.startswith("output="):
                output_tokens += int(part.split("=", 1)[1])

    last_event = recent[-1] if recent else "No events in last hour."

    text = (
        "*Clawbot Hourly Report*\n"
        f"- Window: {since.strftime('%H:%M')}-{now.strftime('%H:%M')} UTC\n"
        f"- DMs: {dms}\n"
        f"- Mentions: {mentions}\n"
        f"- Replies sent: {replies}\n"
        f"- Errors (log/runtime): {errors}/{runtime_errors}\n"
        f"- Codex tokens (prompt/output): {prompt_tokens}/{output_tokens}\n"
        f"- Last event: {last_event}"
    )

    client = WebClient(token=BOT_TOKEN)
    client.chat_postMessage(channel=CHANNEL, text=text)


if __name__ == "__main__":
    main()

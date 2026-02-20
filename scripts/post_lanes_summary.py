#!/usr/bin/env python3
"""
Post lane summaries to Slack.
"""

import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen


def read_snippet(path: Path, max_lines: int = 6):
    lines = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        lines.append(line)
        if len(lines) >= max_lines:
            break
    return lines


def post_message(token: str, channel: str, text: str) -> None:
    payload = {"channel": channel, "text": text, "mrkdwn": True}
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        "https://slack.com/api/chat.postMessage",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        result = json.loads(body)
        if not result.get("ok"):
            raise RuntimeError(f"Slack API error: {result}")


def main():
    if len(sys.argv) < 2:
        print("Usage: post_lanes_summary.py <outdir>")
        return 2

    outdir = Path(sys.argv[1]).resolve()
    if not outdir.exists():
        print(f"Output directory not found: {outdir}")
        return 1

    token = os.environ.get("SLACK_BOT_TOKEN", "")
    channel = os.environ.get("CLAWDBOT_MONITOR_CHANNEL", "")
    if not token or not channel:
        print("Missing SLACK_BOT_TOKEN or CLAWDBOT_MONITOR_CHANNEL")
        return 0

    files = sorted(outdir.glob("lane_*.md"))
    if not files:
        print("No lane files found.")
        return 0

    lines = [f"*Lane Summary* ({outdir.name})", f"Output: `{outdir}`", ""]
    for path in files:
        lane_title = path.stem.replace("lane_", "").replace("_", " ").title()
        lines.append(f"*{lane_title}*")
        snippet = read_snippet(path)
        if snippet:
            lines.extend(snippet)
        else:
            lines.append("(no content)")
        lines.append("")

    text = "\n".join(lines).strip()
    post_message(token, channel, text)
    print("Posted lane summary to Slack.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
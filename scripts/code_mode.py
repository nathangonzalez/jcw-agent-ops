#!/usr/bin/env python3
"""
Generate a unified diff patch for jcw-agent-ops using OpenAI.
"""

import argparse
from pathlib import Path

from openai import OpenAI


def read_file(path: Path, max_chars: int = 6000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True, help="Path to request text")
    parser.add_argument("--out", required=True, help="Output directory for diff")
    args = parser.parse_args()

    req_path = Path(args.request)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    request = req_path.read_text(encoding="utf-8", errors="ignore").strip()

    repo_root = Path("/opt/agent-ops")
    context_files = [
        repo_root / "scripts" / "slack_bot.py",
        repo_root / "SUPERVISOR_MEMORY.md",
        repo_root / "SUPERVISOR_BACKLOG.md",
        repo_root / "SPRINT_BOARD.md",
    ]
    context = []
    for path in context_files:
        content = read_file(path)
        if content:
            context.append(f"File: {path}\n{content}")

    system = (
        "You are a coding assistant for the repo /opt/agent-ops. "
        "Return ONLY a unified diff patch. "
        "Make minimal, correct changes. If unsure, output an empty diff."
    )
    client = OpenAI()
    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": "REQUEST:\n" + request},
            {"role": "user", "content": "\n\nCONTEXT:\n" + "\n\n".join(context)},
        ],
    )
    diff = getattr(response, "output_text", "").strip()
    diff_path = out_dir / "change.diff"
    diff_path.write_text(diff, encoding="utf-8")
    (out_dir / "summary.txt").write_text(request, encoding="utf-8")


if __name__ == "__main__":
    main()

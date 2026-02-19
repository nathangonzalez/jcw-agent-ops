#!/usr/bin/env python
"""
Append a daily supervisor summary to PERSIST.txt.
"""

from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path("/opt/agent-ops")
PERSIST = REPO_ROOT / "PERSIST.txt"


def read_snippet(path: Path, max_lines: int = 20) -> str:
    if not path.exists():
        return ""
    lines = [line.rstrip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()]
    lines = [line for line in lines if line.strip()]
    return "\n".join(lines[:max_lines])


def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    memory = read_snippet(REPO_ROOT / "SUPERVISOR_MEMORY.md", max_lines=20)
    backlog = read_snippet(REPO_ROOT / "SUPERVISOR_BACKLOG.md", max_lines=20)
    sprint = read_snippet(REPO_ROOT / "SPRINT_BOARD.md", max_lines=30)

    block = [
        f"## {ts}",
        "",
        "### Supervisor Memory",
        memory or "(empty)",
        "",
        "### Supervisor Backlog",
        backlog or "(empty)",
        "",
        "### Sprint Board (top)",
        sprint or "(empty)",
        "",
        "---",
        "",
    ]
    PERSIST.write_text(
        (PERSIST.read_text(encoding="utf-8", errors="ignore") if PERSIST.exists() else "")
        + "\n".join(block),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

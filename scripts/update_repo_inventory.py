#!/usr/bin/env python
"""
Update inventory/repo_inventory.md by scanning local repos.
Heuristics only; safe defaults when unknown.
"""

import fnmatch
import os
from pathlib import Path


def detect_stack(repo: Path) -> str:
    if (repo / "package.json").exists():
        return "Node.js"
    if (repo / "requirements.txt").exists() or (repo / "pyproject.toml").exists():
        return "Python"
    if (repo / "Gemfile").exists():
        return "Ruby"
    if any(repo.glob("*.csproj")):
        return ".NET"
    if (repo / "go.mod").exists():
        return "Go"
    if (repo / "build.gradle").exists() or (repo / "gradlew").exists():
        return "Java/Gradle"
    return "Unknown"


def detect_deploy(repo: Path) -> str:
    if (repo / "app.yaml").exists():
        return "App Engine"
    if (repo / "Dockerfile").exists():
        return "Docker"
    if (repo / ".github" / "workflows").exists():
        return "GitHub Actions"
    return "Unknown"


def detect_datastore(repo: Path) -> str:
    if any(repo.rglob("*.sqlite")):
        return "SQLite"
    if any(repo.rglob("prisma/schema.prisma")):
        return "Prisma"
    if any(repo.rglob("*.sql")):
        return "SQL (unknown)"
    return "Unknown"


def in_scope(name: str, includes, excludes) -> bool:
    for ex in excludes:
        if fnmatch.fnmatch(name, ex):
            return False
    for inc in includes:
        if fnmatch.fnmatch(name, inc):
            return True
    return False


def main():
    repo_root = Path(os.environ.get("JCW_REPO_ROOT", r"C:\Users\natha\dev\repos"))
    includes = os.environ.get("JCW_REPO_INCLUDE", "jcw-*,jcw_*,jcw_payroll,jcw_financials").split(",")
    excludes = os.environ.get("JCW_REPO_EXCLUDE", "output").split(",")

    rows = []
    for entry in sorted(repo_root.iterdir()):
        if not entry.is_dir():
            continue
        if not in_scope(entry.name, includes, excludes):
            continue
        stack = detect_stack(entry)
        deploy = detect_deploy(entry)
        datastore = detect_datastore(entry)
        rows.append((entry.name, stack, deploy, datastore))

    out_override = os.environ.get("JCW_REPO_OUTPUT", "")
    out = Path(out_override) if out_override else repo_root / "agent-ops" / "inventory" / "repo_inventory.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Repo Inventory (JCW)",
        "",
        "| Repo | Stack | Deploy Method | Datastore | Owners | Risks/Notes |",
        "|---|---|---|---|---|---|",
    ]
    for name, stack, deploy, datastore in rows:
        lines.append(f"| {name} | {stack} | {deploy} | {datastore} | natha | Needs verification |")

    out.write_text("\n".join(lines))
    print(f"Updated inventory at {out}")


if __name__ == "__main__":
    main()

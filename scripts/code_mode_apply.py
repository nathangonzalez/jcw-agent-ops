#!/usr/bin/env python3
"""
Apply a unified diff patch and commit to git.
"""

import argparse
import subprocess
from pathlib import Path


def _normalize_diff(diff_text: str, repo_root: Path) -> str:
    """
    Ensure diff is in git-apply friendly format.
    Converts unified diffs without diff --git headers and with absolute paths.
    """
    # Strip markdown code fences if present
    filtered_lines = []
    for line in diff_text.splitlines():
        if line.strip().startswith("```"):
            continue
        filtered_lines.append(line)
    diff_text = "\n".join(filtered_lines)

    if diff_text.lstrip().startswith("diff --git"):
        return diff_text

    def _relpath(p: str) -> str:
        if p in ("/dev/null", "dev/null"):
            return ""
        p = p.strip().strip('"')
        if p.startswith("a/") or p.startswith("b/"):
            p = p[2:]
        try:
            pp = Path(p)
            if pp.is_absolute():
                try:
                    return pp.resolve().relative_to(repo_root.resolve()).as_posix()
                except Exception:
                    return pp.name
            return pp.as_posix()
        except Exception:
            return p

    lines = diff_text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            old_path = _relpath(line[4:].strip())
            new_path = _relpath(lines[i + 1][4:].strip())
            if not old_path:
                old_path = new_path
            if not new_path:
                new_path = old_path
            out.append(f"diff --git a/{old_path} b/{new_path}")
            out.append(f"--- a/{old_path}")
            out.append(f"+++ b/{new_path}")
            i += 2
            continue
        out.append(line)
        i += 1
    return "\n".join(out) + "\n"


def _apply_patch(diff_path: Path, repo_root: Path) -> str:
    apply_proc = subprocess.run(
        ["git", "apply", str(diff_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if apply_proc.returncode == 0:
        return "applied"

    # Retry with recount for bad hunk line counts
    apply_proc = subprocess.run(
        ["git", "apply", "--recount", str(diff_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if apply_proc.returncode == 0:
        return "applied"

    # Check if already applied
    check_proc = subprocess.run(
        ["git", "apply", "--reverse", "--check", str(diff_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if check_proc.returncode == 0:
        return "already_applied"

    raise SystemExit(f"git apply failed: {apply_proc.stderr.strip()}")


def _parse_unified_diff(diff_text: str) -> dict:
    """
    Parse a unified diff into file->hunks with context/add/delete lines.
    Returns {path: [hunk, ...]}
    hunk: {"context": [...], "adds": [...], "dels": [...]}
    """
    files = {}
    current = None
    hunks = []
    context = []
    adds = []
    dels = []

    def _flush_hunk():
        nonlocal context, adds, dels, hunks
        if context or adds or dels:
            hunks.append({"context": context, "adds": adds, "dels": dels})
            context, adds, dels = [], [], []

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            _flush_hunk()
            if current and hunks:
                files[current] = hunks
            hunks = []
            current = None
            continue
        if line.startswith("+++ "):
            path = line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            current = path
            continue
        if line.startswith("@@ "):
            _flush_hunk()
            continue
        if line.startswith("+") and not line.startswith("+++"):
            adds.append(line[1:])
            continue
        if line.startswith("-") and not line.startswith("---"):
            dels.append(line[1:])
            continue
        if line.startswith(" ") or line == "":
            # context line (leading space) or blank line
            context.append(line[1:] if line.startswith(" ") else "")
            continue

    _flush_hunk()
    if current and hunks:
        files[current] = hunks
    return files


def _manual_apply(diff_text: str, repo_root: Path) -> bool:
    """
    Best-effort apply for add-only hunks. Returns True if applied.
    """
    files = _parse_unified_diff(diff_text)
    if not files:
        return False

    applied_any = False
    for rel_path, hunks in files.items():
        path = repo_root / rel_path
        if not path.exists():
            raise SystemExit(f"Manual apply failed: file not found {rel_path}")
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for hunk in hunks:
            if hunk["dels"]:
                raise SystemExit("Manual apply failed: deletes present in diff.")
            if not hunk["adds"]:
                continue
            # Find insertion point: last matching context line
            insert_at = None
            for ctx in reversed(hunk["context"]):
                for idx in range(len(lines) - 1, -1, -1):
                    if lines[idx] == ctx:
                        insert_at = idx + 1
                        break
                if insert_at is not None:
                    break
            if insert_at is None:
                insert_at = len(lines)
            # Avoid duplicate insertion
            for add in hunk["adds"]:
                if add in lines:
                    continue
                lines.insert(insert_at, add)
                insert_at += 1
                applied_any = True
        if applied_any:
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return applied_any


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True, help="Job directory containing change.diff")
    args = parser.parse_args()

    job_dir = Path(args.job)
    diff_path = job_dir / "change.diff"
    if not diff_path.exists():
        raise SystemExit("Missing change.diff")

    repo_root = Path("/opt/agent-ops")
    diff_text = diff_path.read_text(encoding="utf-8", errors="ignore")
    if not diff_text.strip():
        raise SystemExit("Diff is empty or invalid; aborting.")

    normalized = _normalize_diff(diff_text, repo_root)
    normalized_path = job_dir / "change.normalized.diff"
    normalized_path.write_text(normalized, encoding="utf-8")

    try:
        result = _apply_patch(normalized_path, repo_root)
        if result == "already_applied":
            print("Patch already applied.")
            return
    except SystemExit as exc:
        # Fallback to manual apply for add-only diffs
        try:
            if _manual_apply(normalized, repo_root):
                print("Patch applied via manual fallback.")
            else:
                raise
        except SystemExit:
            raise exc

    subprocess.run(["git", "add", "."], cwd=repo_root, check=False)
    commit_msg = f"Code mode apply: {job_dir.name}"
    commit_proc = subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_root, capture_output=True, text=True)
    if commit_proc.returncode != 0:
        raise SystemExit(f"git commit failed: {commit_proc.stderr.strip()}")

    push_proc = subprocess.run(["git", "push"], cwd=repo_root, capture_output=True, text=True)
    if push_proc.returncode != 0:
        print("Patch applied and committed, but push failed:")
        print(push_proc.stderr.strip())
        return

    print("Patch applied, committed, and pushed.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Apply a unified diff patch and commit to git.
"""

import argparse
import subprocess
from pathlib import Path


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
    if not diff_text.strip().startswith("diff --git"):
        raise SystemExit("Diff is empty or invalid; aborting.")

    apply_proc = subprocess.run(["git", "apply", str(diff_path)], cwd=repo_root, capture_output=True, text=True)
    if apply_proc.returncode != 0:
        raise SystemExit(f"git apply failed: {apply_proc.stderr.strip()}")

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

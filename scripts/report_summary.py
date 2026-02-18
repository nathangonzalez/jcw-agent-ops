#!/usr/bin/env python
"""
Generate a summary report from the unified repo index DB.
"""

import argparse
import sqlite3
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="Unified SQLite DB path")
    parser.add_argument("--out", required=True, help="Output report path (md)")
    args = parser.parse_args()

    db_path = Path(args.db)
    out_path = Path(args.out)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Totals
    total_files = cur.execute("SELECT COUNT(*) FROM repo_files").fetchone()[0]
    total_chunks = cur.execute("SELECT COUNT(*) FROM repo_chunks").fetchone()[0]

    # By repo
    by_repo = cur.execute(
        "SELECT repo_name, COUNT(*) as cnt FROM repo_files GROUP BY repo_name ORDER BY cnt DESC"
    ).fetchall()

    # By extension
    by_ext = cur.execute(
        "SELECT ext, COUNT(*) as cnt FROM repo_files GROUP BY ext ORDER BY cnt DESC LIMIT 20"
    ).fetchall()

    # Largest files
    largest = cur.execute(
        """
        SELECT repo_name, rel_path, size
        FROM repo_files
        ORDER BY size DESC
        LIMIT 20
        """
    ).fetchall()

    conn.close()

    lines = []
    lines.append("# Repo Index Summary")
    lines.append("")
    lines.append("## Totals")
    lines.append(f"- Files indexed: {total_files}")
    lines.append(f"- Chunks indexed: {total_chunks}")
    lines.append("")
    lines.append("## Files by Repo")
    for repo, cnt in by_repo:
        lines.append(f"- {repo}: {cnt}")
    lines.append("")
    lines.append("## Top Extensions (by file count)")
    for ext, cnt in by_ext:
        ext_display = ext if ext else "(no ext)"
        lines.append(f"- {ext_display}: {cnt}")
    lines.append("")
    lines.append("## Largest Files (by size)")
    for repo, path, size in largest:
        lines.append(f"- {repo}: {path} ({size} bytes)")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote report: {out_path}")


if __name__ == "__main__":
    main()

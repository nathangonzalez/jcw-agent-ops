#!/usr/bin/env python
"""
Export tasks from SQLite to CSV for Excel write-back.
"""

import argparse
import csv
import sqlite3
from pathlib import Path


HEADERS = [
    ("Title", "title"),
    ("Tags", "tags"),
    ("Status", "status"),
    ("Due Date", "due_date"),
    ("Priority", "priority"),
    ("Next Action", "next_action"),
    ("Notes", "notes"),
    ("Source", "source"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="SQLite db path")
    parser.add_argument("--out", required=True, help="CSV output path")
    args = parser.parse_args()

    db_path = Path(args.db)
    out_path = Path(args.out)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            title,
            tags,
            status,
            due_date,
            priority,
            next_action,
            notes,
            COALESCE(source, source_sheet) AS source
        FROM tasks
        ORDER BY id
        """
    )
    rows = cur.fetchall()
    conn.close()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([h for h, _ in HEADERS])
        for row in rows:
            writer.writerow(["" if v is None else v for v in row])

    print(f"Wrote {len(rows)} tasks to {out_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Summarize payroll DB contents (counts, hours, date range).
"""

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="Path to payroll SQLite DB")
    return parser.parse_args()


def fmt_date(value):
    if not value:
        return "unknown"
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        return str(value)


def main():
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"DB not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM time_entries")
    total_entries = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(hours),0) FROM time_entries")
    total_hours = cur.fetchone()[0] or 0
    cur.execute("SELECT MIN(work_date), MAX(work_date) FROM time_entries")
    min_date, max_date = cur.fetchone()
    cur.execute("SELECT COUNT(DISTINCT employee_id) FROM time_entries")
    employees_in_entries = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM employees")
    total_employees = cur.fetchone()[0]
    conn.close()

    print("Payroll DB Summary")
    print(f"- DB: {db_path}")
    print(f"- Entries: {total_entries}")
    print(f"- Total hours: {float(total_hours):.2f}")
    print(f"- Employees (in entries): {employees_in_entries}")
    print(f"- Employees (total): {total_employees}")
    print(f"- Date range: {fmt_date(min_date)} to {fmt_date(max_date)}")


if __name__ == "__main__":
    main()

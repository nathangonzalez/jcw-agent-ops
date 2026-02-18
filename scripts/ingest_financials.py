#!/usr/bin/env python
"""
Ingest CSV financial data into a structured SQLite database.

- Scans a list of CSV files and/or directories
  (recursively finds *.csv/*.CSV).
- Stores raw row JSON plus best-effort extracted fields.
"""

import argparse
import csv
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


MAX_BYTES_DEFAULT = 20 * 1024 * 1024  # 20 MB


def iter_csv_files(paths: List[Path]) -> List[Path]:
    files = []
    for p in paths:
        if p.is_file() and p.suffix.lower() == ".csv":
            files.append(p)
        elif p.is_dir():
            for f in p.rglob("*.csv"):
                files.append(f)
            for f in p.rglob("*.CSV"):
                files.append(f)
    # Deduplicate
    unique = []
    seen = set()
    for f in files:
        fp = str(f.resolve())
        if fp not in seen:
            seen.add(fp)
            unique.append(f)
    return unique


def init_db(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS file_meta (
            id INTEGER PRIMARY KEY,
            file_path TEXT UNIQUE,
            file_name TEXT,
            file_size INTEGER,
            row_count INTEGER,
            headers_json TEXT,
            ingested_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS raw_transactions (
            id INTEGER PRIMARY KEY,
            file_id INTEGER,
            row_num INTEGER,
            data_json TEXT,
            date TEXT,
            amount REAL,
            description TEXT,
            vendor TEXT,
            vendor_norm TEXT,
            account TEXT,
            category TEXT,
            category_norm TEXT,
            FOREIGN KEY(file_id) REFERENCES file_meta(id)
        );
        CREATE INDEX IF NOT EXISTS idx_raw_file ON raw_transactions(file_id);
        """
    )
    ensure_columns(
        conn,
        "raw_transactions",
        [
            ("vendor_norm", "TEXT"),
            ("category_norm", "TEXT"),
        ],
    )
    return conn


def sniff_dialect(sample: str) -> csv.Dialect:
    try:
        dialect = csv.Sniffer().sniff(sample)
        return dialect
    except Exception:
        return csv.excel


def normalize_header(h: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in h).strip("_")


def parse_amount(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    raw = str(value).strip()
    if raw == "":
        return None
    negative = False
    if raw.startswith("(") and raw.endswith(")"):
        negative = True
        raw = raw[1:-1].strip()
    raw = raw.replace("$", "").replace(",", "").strip()
    if raw == "":
        return None
    try:
        amt = float(raw)
    except Exception:
        return None
    return -amt if negative else amt


def normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    raw = str(value).strip()
    if raw == "":
        return None
    # Keep alphanumerics; collapse whitespace.
    cleaned = []
    for ch in raw:
        if ch.isalnum():
            cleaned.append(ch.lower())
        else:
            cleaned.append(" ")
    norm = " ".join("".join(cleaned).split())
    return norm if norm else None


def ensure_columns(conn: sqlite3.Connection, table: str, columns: List[Tuple[str, str]]):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cur.fetchall()}
    for name, col_type in columns:
        if name not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {col_type}")
    conn.commit()


def extract_fields(row: Dict[str, str]) -> Tuple[Optional[str], Optional[float], Optional[str], Optional[str], Optional[str], Optional[str]]:
    # Heuristic column mapping
    key_map = {normalize_header(k): k for k in row.keys()}

    def first(*candidates):
        for c in candidates:
            if c in key_map:
                return row.get(key_map[c])
        return None

    date = first("date", "transaction_date", "posted_date", "post_date", "value_date")
    amount_raw = first(
        "amount",
        "amt",
        "transaction_amount",
        "net_amount",
        "value",
        "total",
        "original_amount",
        "adjusted_amount",
    )
    debit_raw = first("debit", "withdrawal", "withdrawals", "money_out", "outflow", "paid_out")
    credit_raw = first("credit", "deposit", "deposits", "money_in", "inflow", "paid_in")
    description = first(
        "description",
        "memo",
        "details",
        "transaction_description",
        "transaction_details",
        "reference",
        "note",
        "narration",
        "payee_description",
    )
    vendor = first(
        "vendor",
        "merchant",
        "payee",
        "vendor_name",
        "merchant_name",
        "payee_name",
        "name",
        "counterparty",
        "counterparty_name",
        "supplier",
        "company",
        "entity",
        "beneficiary",
    )
    account = first("account", "account_name", "bank_account", "account_number", "account_id")
    category = first("category", "category_name", "type", "subcategory")

    amount = parse_amount(amount_raw)
    if amount is None:
        debit = parse_amount(debit_raw)
        credit = parse_amount(credit_raw)
        if debit is not None or credit is not None:
            amount = (credit or 0.0) - (debit or 0.0)

    return date, amount, description, vendor, account, category


def ingest_file(conn, file_path: Path, max_bytes: int):
    size = file_path.stat().st_size
    if size > max_bytes:
        return 0

    text = file_path.read_text(encoding="utf-8", errors="replace")
    sample = text[:4096]
    dialect = sniff_dialect(sample)

    rows = []
    reader = csv.DictReader(text.splitlines(), dialect=dialect)
    headers = reader.fieldnames or []
    for i, row in enumerate(reader, start=1):
        rows.append((i, row))

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO file_meta (file_path, file_name, file_size, row_count, headers_json, ingested_at)
        VALUES (?, ?, ?, ?, ?, strftime('%s','now'))
        ON CONFLICT(file_path) DO UPDATE SET
            file_size=excluded.file_size,
            row_count=excluded.row_count,
            headers_json=excluded.headers_json,
            ingested_at=excluded.ingested_at
        """,
        (str(file_path), file_path.name, size, len(rows), json.dumps(headers)),
    )
    conn.commit()

    cur.execute("SELECT id FROM file_meta WHERE file_path = ?", (str(file_path),))
    file_id = cur.fetchone()[0]

    # Replace rows for this file
    cur.execute("DELETE FROM raw_transactions WHERE file_id = ?", (file_id,))
    for row_num, row in rows:
        date, amount, desc, vendor, account, category = extract_fields(row)
        vendor_norm = normalize_text(vendor)
        category_norm = normalize_text(category)
        cur.execute(
            """
            INSERT INTO raw_transactions
            (file_id, row_num, data_json, date, amount, description, vendor, vendor_norm, account, category, category_norm)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file_id,
                row_num,
                json.dumps(row),
                date,
                amount,
                desc,
                vendor,
                vendor_norm,
                account,
                category,
                category_norm,
            ),
        )
    conn.commit()
    return len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="SQLite output path")
    parser.add_argument("--max-bytes", type=int, default=MAX_BYTES_DEFAULT)
    parser.add_argument("paths", nargs="+", help="Files or directories to ingest")
    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    paths = [Path(p).resolve() for p in args.paths]

    conn = init_db(db_path)
    files = iter_csv_files(paths)

    total_files = 0
    total_rows = 0
    for f in files:
        total_files += 1
        total_rows += ingest_file(conn, f, args.max_bytes)

    conn.close()
    print(f"Files ingested: {total_files}")
    print(f"Rows ingested: {total_rows}")


if __name__ == "__main__":
    sys.exit(main())

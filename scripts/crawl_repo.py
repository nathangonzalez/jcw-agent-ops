#!/usr/bin/env python
"""
Repository crawler and indexer.

Outputs:
- SQLite DB with file metadata and content chunks.
- JSONL with raw chunks (optional).
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path


DEFAULT_EXCLUDES = [
    ".git",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".venv",
    "venv",
    "__pycache__",
    "data",
    "exports",
    ".husky",
    ".devcontainer",
]

DEFAULT_EXT_EXCLUDES = {
    ".zip",
    ".xlsx",
    ".xls",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".mp4",
    ".mp3",
    ".wav",
    ".db",
    ".sqlite",
    ".log",
}

DEFAULT_NAME_EXCLUDES = {
    ".env",
    "gcloud-auth.json",
    "gcloud-info.json",
    "gcloud-configs.json",
    "sa-keys.json",
    "sa-candidates.txt",
}


def is_binary_bytes(sample: bytes) -> bool:
    if b"\x00" in sample:
        return True
    # Heuristic: a lot of non-text bytes
    text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
    nontext = sample.translate(None, text_chars)
    return float(len(nontext)) / max(len(sample), 1) > 0.30


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def chunk_text(text: str, max_chars: int = 4000, overlap: int = 200):
    if max_chars <= 0:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        chunk = text[start:end]
        chunks.append((start, end, chunk))
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


def should_exclude(path: Path, root: Path, excludes, ext_excludes, name_excludes):
    rel = path.relative_to(root)
    parts = set(rel.parts)
    if parts & set(excludes):
        return True
    if path.suffix.lower() in ext_excludes:
        return True
    if path.name in name_excludes:
        return True
    return False


def init_db(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS repo_files (
            id INTEGER PRIMARY KEY,
            rel_path TEXT UNIQUE,
            abs_path TEXT,
            ext TEXT,
            size INTEGER,
            mtime INTEGER,
            sha256 TEXT,
            is_binary INTEGER,
            indexed_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS repo_chunks (
            id INTEGER PRIMARY KEY,
            file_id INTEGER,
            chunk_index INTEGER,
            start_char INTEGER,
            end_char INTEGER,
            content TEXT,
            FOREIGN KEY(file_id) REFERENCES repo_files(id)
        );
        CREATE INDEX IF NOT EXISTS idx_chunks_file ON repo_chunks(file_id);
        """
    )
    return conn


def upsert_file(conn, rel_path, abs_path, ext, size, mtime, sha256, is_binary):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO repo_files (rel_path, abs_path, ext, size, mtime, sha256, is_binary, indexed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(rel_path) DO UPDATE SET
            abs_path=excluded.abs_path,
            ext=excluded.ext,
            size=excluded.size,
            mtime=excluded.mtime,
            sha256=excluded.sha256,
            is_binary=excluded.is_binary,
            indexed_at=excluded.indexed_at
        """,
        (rel_path, abs_path, ext, size, mtime, sha256, is_binary, int(time.time())),
    )
    conn.commit()
    cur.execute("SELECT id FROM repo_files WHERE rel_path = ?", (rel_path,))
    return cur.fetchone()[0]


def replace_chunks(conn, file_id, chunks):
    cur = conn.cursor()
    cur.execute("DELETE FROM repo_chunks WHERE file_id = ?", (file_id,))
    for idx, (start, end, content) in enumerate(chunks):
        cur.execute(
            """
            INSERT INTO repo_chunks (file_id, chunk_index, start_char, end_char, content)
            VALUES (?, ?, ?, ?, ?)
            """,
            (file_id, idx, start, end, content),
        )
    conn.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Root repo path")
    parser.add_argument("--db", required=True, help="SQLite output path")
    parser.add_argument("--jsonl", default="", help="Optional JSONL output path")
    parser.add_argument("--max-bytes", type=int, default=2 * 1024 * 1024, help="Max file size to index")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    db_path = Path(args.db).resolve()
    jsonl_path = Path(args.jsonl).resolve() if args.jsonl else None

    conn = init_db(db_path)
    jsonl_fp = jsonl_path.open("w", encoding="utf-8") if jsonl_path else None

    total = 0
    indexed = 0
    skipped = 0

    for path in root.rglob("*"):
        if path.is_dir():
            continue

        total += 1
        if should_exclude(path, root, DEFAULT_EXCLUDES, DEFAULT_EXT_EXCLUDES, DEFAULT_NAME_EXCLUDES):
            skipped += 1
            continue

        try:
            size = path.stat().st_size
            if size > args.max_bytes:
                skipped += 1
                continue

            rel_path = str(path.relative_to(root)).replace("\\", "/")
            ext = path.suffix.lower()
            mtime = int(path.stat().st_mtime)
            sha = sha256_file(path)

            with path.open("rb") as f:
                sample = f.read(4096)
                is_binary = 1 if is_binary_bytes(sample) else 0

            file_id = upsert_file(conn, rel_path, str(path), ext, size, mtime, sha, is_binary)

            if is_binary:
                skipped += 1
                continue

            text = path.read_text(encoding="utf-8", errors="replace")
            chunks = chunk_text(text)
            replace_chunks(conn, file_id, chunks)

            if jsonl_fp:
                for idx, (start, end, content) in enumerate(chunks):
                    jsonl_fp.write(
                        json.dumps(
                            {
                                "rel_path": rel_path,
                                "chunk_index": idx,
                                "start_char": start,
                                "end_char": end,
                                "content": content,
                            }
                        )
                        + "\n"
                    )

            indexed += 1
        except Exception:
            skipped += 1
            continue

    if jsonl_fp:
        jsonl_fp.close()
    conn.close()

    print(f"Total files: {total}")
    print(f"Indexed: {indexed}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    sys.exit(main())

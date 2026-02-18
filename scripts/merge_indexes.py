#!/usr/bin/env python
"""
Merge per-repo SQLite indexes into a single unified DB.
"""

import argparse
import sqlite3
from pathlib import Path


def init_db(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS repo_sources (
            id INTEGER PRIMARY KEY,
            repo_name TEXT UNIQUE,
            source_file TEXT,
            merged_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS repo_files (
            id INTEGER PRIMARY KEY,
            repo_name TEXT,
            rel_path TEXT,
            abs_path TEXT,
            ext TEXT,
            size INTEGER,
            mtime INTEGER,
            sha256 TEXT,
            is_binary INTEGER,
            indexed_at INTEGER,
            UNIQUE(repo_name, rel_path)
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
        CREATE INDEX IF NOT EXISTS idx_files_repo ON repo_files(repo_name);
        CREATE INDEX IF NOT EXISTS idx_files_repo_path ON repo_files(repo_name, rel_path);
        CREATE INDEX IF NOT EXISTS idx_chunks_file ON repo_chunks(file_id);
        """
    )
    return conn


def repo_name_from_file(path: Path):
    name = path.stem  # repo_xxx or repo_index
    if name == "repo_index":
        return "jcw_payroll"
    if name.startswith("repo_"):
        return name.replace("repo_", "", 1)
    return name


def merge_db(dest: sqlite3.Connection, source_path: Path):
    repo_name = repo_name_from_file(source_path)
    src = sqlite3.connect(source_path)
    src.row_factory = sqlite3.Row

    dest.execute(
        """
        INSERT INTO repo_sources (repo_name, source_file, merged_at)
        VALUES (?, ?, strftime('%s','now'))
        ON CONFLICT(repo_name) DO UPDATE SET
            source_file=excluded.source_file,
            merged_at=excluded.merged_at
        """,
        (repo_name, str(source_path)),
    )

    # Prepare statements
    insert_file = dest.cursor()
    insert_chunk = dest.cursor()

    file_id_map = {}

    for row in src.execute("SELECT * FROM repo_files"):
        dest.execute(
            """
            INSERT INTO repo_files (repo_name, rel_path, abs_path, ext, size, mtime, sha256, is_binary, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo_name, rel_path) DO UPDATE SET
                abs_path=excluded.abs_path,
                ext=excluded.ext,
                size=excluded.size,
                mtime=excluded.mtime,
                sha256=excluded.sha256,
                is_binary=excluded.is_binary,
                indexed_at=excluded.indexed_at
            """,
            (
                repo_name,
                row["rel_path"],
                row["abs_path"],
                row["ext"],
                row["size"],
                row["mtime"],
                row["sha256"],
                row["is_binary"],
                row["indexed_at"],
            ),
        )
        cur = dest.execute(
            "SELECT id FROM repo_files WHERE repo_name = ? AND rel_path = ?",
            (repo_name, row["rel_path"]),
        )
        new_id = cur.fetchone()[0]
        file_id_map[row["id"]] = new_id

    # Replace chunks for files in this repo
    dest.execute("DELETE FROM repo_chunks WHERE file_id IN (SELECT id FROM repo_files WHERE repo_name = ?)", (repo_name,))
    for row in src.execute("SELECT * FROM repo_chunks"):
        new_file_id = file_id_map.get(row["file_id"])
        if not new_file_id:
            continue
        insert_chunk.execute(
            """
            INSERT INTO repo_chunks (file_id, chunk_index, start_char, end_char, content)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                new_file_id,
                row["chunk_index"],
                row["start_char"],
                row["end_char"],
                row["content"],
            ),
        )

    dest.commit()
    src.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, help="Directory with repo_*.sqlite files")
    parser.add_argument("--output", required=True, help="Unified SQLite output path")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output = Path(args.output)

    dest = init_db(output)

    sources = sorted(input_dir.glob("repo_*.sqlite"))
    # Include repo_index.sqlite (jcw_payroll)
    index_path = input_dir / "repo_index.sqlite"
    if index_path.exists():
        sources = [index_path] + sources

    for src in sources:
        merge_db(dest, src)

    dest.close()
    print(f"Merged {len(sources)} sources into {output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Minimal local web UI for Actions tasks.
No external dependencies. Uses Python stdlib only.
"""

import json
import os
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "data" / "actions.sqlite"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


def row_to_dict(row, columns):
    return {col: row[i] for i, col in enumerate(columns)}


class TaskServer(BaseHTTPRequestHandler):
    server_version = "AgentOpsTasks/1.0"

    def _send_json(self, data, status=200):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_text(self, text, status=200, content_type="text/plain; charset=utf-8"):
        payload = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _serve_file(self, path: Path, content_type: str):
        if not path.exists() or not path.is_file():
            self._send_text("Not found", status=404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/" or path == "":
            self._serve_file(TEMPLATES_DIR / "index.html", "text/html; charset=utf-8")
            return
        if path.startswith("/static/"):
            rel = path.replace("/static/", "")
            file_path = STATIC_DIR / rel
            if file_path.suffix == ".css":
                self._serve_file(file_path, "text/css; charset=utf-8")
                return
            if file_path.suffix == ".js":
                self._serve_file(file_path, "application/javascript; charset=utf-8")
                return
            self._serve_file(file_path, "application/octet-stream")
            return
        if path == "/api/health":
            self._send_json({"ok": True, "db": str(DB_PATH), "time": datetime.utcnow().isoformat()})
            return
        if path == "/api/tags":
            self.handle_list_tags()
            return
        if path == "/api/tasks":
            self.handle_list_tasks(parsed.query)
            return
        self._send_text("Not found", status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/tasks":
            payload = self._read_json() or {}
            self.handle_create_task(payload)
            return
        self._send_text("Not found", status=404)

    def do_PATCH(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/tasks/"):
            task_id = parsed.path.split("/")[-1]
            payload = self._read_json() or {}
            self.handle_update_task(task_id, payload)
            return
        self._send_text("Not found", status=404)

    def handle_list_tasks(self, query_string):
        if not DB_PATH.exists():
            self._send_json({"error": "DB not found", "db": str(DB_PATH)}, status=404)
            return
        params = parse_qs(query_string)
        status = params.get("status", [""])[0].strip()
        tag = params.get("tag", [""])[0].strip().lower()
        search = params.get("q", [""])[0].strip().lower()
        limit = int(params.get("limit", ["200"])[0])
        offset = int(params.get("offset", ["0"])[0])

        clauses = []
        values = []
        if status:
            clauses.append("status = ?")
            values.append(status)
        if tag:
            clauses.append("lower(coalesce(tags, '')) like ?")
            values.append(f"%{tag}%")
        if search:
            clauses.append("lower(title) like ?")
            values.append(f"%{search}%")

        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"""
            SELECT id, title, tags, status, due_date, priority, next_action, notes, source, updated_at
            FROM tasks
            {where}
            ORDER BY
                CASE status
                    WHEN 'Not Started' THEN 1
                    WHEN 'In-Progress' THEN 2
                    WHEN 'Completed' THEN 3
                    ELSE 4
                END,
                COALESCE(due_date, '')
            LIMIT ? OFFSET ?
        """
        values.extend([limit, offset])

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(sql, values)
        rows = cur.fetchall()
        conn.close()

        columns = [
            "id",
            "title",
            "tags",
            "status",
            "due_date",
            "priority",
            "next_action",
            "notes",
            "source",
            "updated_at",
        ]
        data = [row_to_dict(r, columns) for r in rows]
        self._send_json({"items": data, "count": len(data)})

    def handle_list_tags(self):
        if not DB_PATH.exists():
            self._send_json({"error": "DB not found", "db": str(DB_PATH)}, status=404)
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT tags FROM tasks WHERE tags IS NOT NULL AND tags <> ''")
        rows = cur.fetchall()
        conn.close()

        tags = set()
        for (tag_str,) in rows:
            for t in str(tag_str).split(","):
                t = t.strip()
                if t:
                    tags.add(t)

        self._send_json({"items": sorted(tags)})

    def handle_create_task(self, payload):
        if not DB_PATH.exists():
            self._send_json({"error": "DB not found", "db": str(DB_PATH)}, status=404)
            return
        title = (payload.get("title") or "").strip()
        if not title:
            self._send_json({"error": "title required"}, status=400)
            return

        fields = {
            "title": title,
            "tags": (payload.get("tags") or "").strip(),
            "status": (payload.get("status") or "Not Started").strip(),
            "due_date": (payload.get("due_date") or "").strip(),
            "priority": (payload.get("priority") or "").strip(),
            "next_action": (payload.get("next_action") or "").strip(),
            "notes": (payload.get("notes") or "").strip(),
            "source": (payload.get("source") or "All Tasks").strip(),
        }

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO tasks
            (raw_id, source_sheet, title, tags, due_date, status, status_color, category, priority, next_action, notes, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%s','now'), strftime('%s','now'))
            """,
            (
                None,
                "All_Tasks",
                fields["title"],
                fields["tags"],
                fields["due_date"],
                fields["status"],
                None,
                "All_Tasks",
                fields["priority"],
                fields["next_action"],
                fields["notes"],
                fields["source"],
            ),
        )
        task_id = cur.lastrowid
        conn.commit()
        conn.close()

        fields["id"] = task_id
        self._send_json(fields, status=201)

    def handle_update_task(self, task_id, payload):
        if not DB_PATH.exists():
            self._send_json({"error": "DB not found", "db": str(DB_PATH)}, status=404)
            return
        try:
            task_id = int(task_id)
        except Exception:
            self._send_json({"error": "invalid id"}, status=400)
            return

        allowed = {"title", "tags", "status", "due_date", "priority", "next_action", "notes", "source"}
        updates = []
        values = []
        for key, value in payload.items():
            if key in allowed:
                updates.append(f"{key} = ?")
                values.append(value)
        if not updates:
            self._send_json({"error": "no updatable fields"}, status=400)
            return

        values.append(task_id)
        sql = f"UPDATE tasks SET {', '.join(updates)}, updated_at=strftime('%s','now') WHERE id = ?"

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(sql, values)
        conn.commit()
        conn.close()

        self._send_json({"ok": True, "id": task_id})


def main():
    host = os.environ.get("AGENT_OPS_HOST", "127.0.0.1")
    port = int(os.environ.get("AGENT_OPS_PORT", "8090"))
    server = HTTPServer((host, port), TaskServer)
    print(f"Task UI running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

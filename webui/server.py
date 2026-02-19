#!/usr/bin/env python
"""
Minimal local web UI for Actions tasks.
No external dependencies. Uses Python stdlib only.
"""

import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
DB_PATH = REPO_ROOT / "data" / "actions.sqlite"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DRAFTS_DIR = REPO_ROOT / "data" / "drafts"
SPRINT_PATH = REPO_ROOT / "SPRINT_BOARD.md"
BACKLOG_PATH = REPO_ROOT / "SUPERVISOR_BACKLOG.md"
OPS_LOG = REPO_ROOT / "agent_outputs" / "clawdbot_slack.log"
RUNTIME_LOG = REPO_ROOT / "agent_outputs" / "clawdbot_slack_runtime.log"


def row_to_dict(row, columns):
    return {col: row[i] for i, col in enumerate(columns)}


def read_text_safe(path: Path, limit: int = 12000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    if len(text) <= limit:
        return text
    return text[-limit:]


def tail_lines(path: Path, limit: int = 120) -> list:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return lines[-limit:]


def compute_ops_summary():
    slack_lines = tail_lines(OPS_LOG, 200)
    runtime_lines = tail_lines(RUNTIME_LOG, 200)
    errors = sum(1 for line in slack_lines if "error" in line.lower())
    runtime_errors = sum(1 for line in runtime_lines if "error" in line.lower())
    dms = sum(1 for line in slack_lines if "dm from" in line.lower())
    mentions = sum(1 for line in slack_lines if "app_mention" in line.lower())
    replies = sum(1 for line in slack_lines if "reply sent" in line.lower())
    last_event = slack_lines[-1] if slack_lines else "No events yet."
    return {
        "dms": dms,
        "mentions": mentions,
        "replies": replies,
        "errors": errors,
        "runtime_errors": runtime_errors,
        "last_event": last_event,
        "log_path": str(OPS_LOG),
    }


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
        if path == "/suite":
            self._serve_file(TEMPLATES_DIR / "suite.html", "text/html; charset=utf-8")
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
        if path == "/api/sprint":
            text = read_text_safe(SPRINT_PATH)
            self._send_json(
                {"content": text, "updated_at": SPRINT_PATH.stat().st_mtime if SPRINT_PATH.exists() else None}
            )
            return
        if path == "/api/backlog":
            text = read_text_safe(BACKLOG_PATH)
            self._send_json(
                {"content": text, "updated_at": BACKLOG_PATH.stat().st_mtime if BACKLOG_PATH.exists() else None}
            )
            return
        if path == "/api/ops":
            self._send_json(compute_ops_summary())
            return
        self._send_text("Not found", status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/tasks":
            payload = self._read_json() or {}
            self.handle_create_task(payload)
            return
        if parsed.path == "/api/drafts/email":
            payload = self._read_json() or {}
            self.handle_draft_email(payload)
            return
        if parsed.path == "/api/drafts/event":
            payload = self._read_json() or {}
            self.handle_draft_event(payload)
            return
        if parsed.path == "/api/writeback":
            payload = self._read_json() or {}
            self.handle_writeback(payload)
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
            "status": (payload.get("status") or "In-Progress").strip(),
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

    def handle_draft_email(self, payload):
        title = (payload.get("subject") or "").strip()
        to = (payload.get("to") or "").strip()
        body = (payload.get("body") or "").strip()
        commit = bool(payload.get("commit"))
        approve = (payload.get("approve") or "").strip()

        if not to or not title or not body:
            self._send_json({"error": "to, subject, and body are required"}, status=400)
            return

        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        out_path = DRAFTS_DIR / f"email-draft-{stamp}.eml"

        if commit and approve != "APPROVE":
            self._send_json({"error": "approval required", "hint": "Type APPROVE to commit."}, status=400)
            return

        result = {"to": to, "subject": title, "body": body, "draft_file": str(out_path)}

        if not commit:
            out_path.write_text(f"To: {to}\nSubject: {title}\n\n{body}")
            self._send_json({"ok": True, "mode": "dry-run", "draft": result})
            return

        script = BASE_DIR.parent / "scripts" / "google_gmail_draft.py"
        cmd = [
            sys.executable,
            str(script),
            "--to",
            to,
            "--subject",
            title,
            "--body",
            body,
            "--out",
            str(out_path),
            "--commit",
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)
            return

        if proc.returncode != 0:
            self._send_json({"error": "draft failed", "stderr": proc.stderr}, status=500)
            return

        self._send_json({"ok": True, "mode": "commit", "draft": result, "stdout": proc.stdout})

    def handle_draft_event(self, payload):
        title = (payload.get("title") or "").strip()
        start = (payload.get("start") or "").strip()
        end = (payload.get("end") or "").strip()
        timezone = (payload.get("timezone") or "America/Denver").strip()
        description = (payload.get("description") or "").strip()
        location = (payload.get("location") or "").strip()
        attendees = (payload.get("attendees") or "").strip()
        calendar_name = (payload.get("calendar_name") or "JCW Drafts").strip()
        commit = bool(payload.get("commit"))
        approve = (payload.get("approve") or "").strip()

        if not title or not start or not end:
            self._send_json({"error": "title, start, and end are required"}, status=400)
            return

        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        out_path = DRAFTS_DIR / f"event-draft-{stamp}.json"

        if commit and approve != "APPROVE":
            self._send_json({"error": "approval required", "hint": "Type APPROVE to commit."}, status=400)
            return

        event = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {"dateTime": start, "timeZone": timezone},
            "end": {"dateTime": end, "timeZone": timezone},
        }
        if attendees:
            event["attendees"] = [{"email": e.strip()} for e in attendees.split(",") if e.strip()]

        if not commit:
            out_path.write_text(json.dumps(event, indent=2))
            self._send_json({"ok": True, "mode": "dry-run", "event": event, "draft_file": str(out_path)})
            return

        script = BASE_DIR.parent / "scripts" / "google_calendar_draft.py"
        cmd = [
            sys.executable,
            str(script),
            "--title",
            title,
            "--start",
            start,
            "--end",
            end,
            "--timezone",
            timezone,
            "--description",
            description,
            "--location",
            location,
            "--attendees",
            attendees,
            "--calendar-name",
            calendar_name,
            "--out",
            str(out_path),
            "--commit",
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)
            return

        if proc.returncode != 0:
            self._send_json({"error": "event draft failed", "stderr": proc.stderr}, status=500)
            return

        self._send_json({"ok": True, "mode": "commit", "event": event, "draft_file": str(out_path), "stdout": proc.stdout})

    def handle_writeback(self, payload):
        approve = (payload.get("approve") or "").strip()
        if approve != "APPROVE":
            self._send_json({"error": "approval required", "hint": "Type APPROVE to sync back to Excel."}, status=400)
            return

        input_path = (payload.get("input_path") or os.environ.get("AGENT_OPS_ACTIONS_XLSX") or r"C:\Users\natha\Downloads\Actions.xlsx").strip()
        db_path = (payload.get("db_path") or str(DB_PATH)).strip()
        sheet_name = (payload.get("sheet_name") or "All Tasks").strip()

        script = BASE_DIR.parent / "scripts" / "actions_writeback.ps1"
        if not script.exists():
            self._send_json({"error": "writeback script missing", "script": str(script)}, status=500)
            return

        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-InputPath",
            input_path,
            "-DbPath",
            db_path,
            "-SheetName",
            sheet_name,
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)
            return

        if proc.returncode != 0:
            self._send_json({"error": "writeback failed", "stderr": proc.stderr}, status=500)
            return

        self._send_json({"ok": True, "stdout": proc.stdout.strip()})


def main():
    host = os.environ.get("AGENT_OPS_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT") or os.environ.get("AGENT_OPS_PORT") or "8090")
    server = HTTPServer((host, port), TaskServer)
    print(f"Task UI running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

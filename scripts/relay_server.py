#!/usr/bin/env python3
"""
Relay server for Slack chat context.
Stores per-channel message logs and optional summaries.
"""

import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


RELAY_DIR = Path(os.environ.get("RELAY_DATA_DIR", "/opt/agent-ops/agent_outputs/relay"))
RELAY_DIR.mkdir(parents=True, exist_ok=True)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
RELAY_MODEL = os.environ.get("RELAY_MODEL", "gpt-4o-mini").strip()


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


def _key(channel_type: str, channel_id: str, user_id: str) -> str:
    if channel_type == "im":
        return f"dm_{user_id}"
    return f"channel_{channel_id}"


def _log_path(key: str) -> Path:
    return RELAY_DIR / f"{key}.jsonl"


def _summary_path(key: str) -> Path:
    return RELAY_DIR / f"{key}.summary.md"


def _append_message(key: str, role: str, text: str, user_id: str | None):
    record = {
        "ts": _now(),
        "role": role,
        "user_id": user_id,
        "text": text,
    }
    path = _log_path(key)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_tail(key: str, limit: int = 40) -> list:
    path = _log_path(key)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    tail = lines[-limit:]
    out = []
    for line in tail:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def _read_summary(key: str) -> str:
    path = _summary_path(key)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore").strip()


def _write_summary(key: str, text: str):
    path = _summary_path(key)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _summarize(key: str, tail: list) -> str:
    if not OPENAI_API_KEY or OpenAI is None:
        return ""
    if not tail:
        return ""
    client = OpenAI(api_key=OPENAI_API_KEY)
    content = "\n".join([f"{row.get('role')}: {row.get('text')}" for row in tail])
    prompt = (
        "Summarize the conversation briefly for context. "
        "Keep to 8 bullet points max. Focus on decisions, tasks, and pending questions."
    )
    response = client.responses.create(
        model=RELAY_MODEL,
        input=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ],
    )
    return (getattr(response, "output_text", "") or "").strip()


class RelayServer(BaseHTTPRequestHandler):
    server_version = "AgentOpsRelay/1.0"

    def _send_json(self, data, status=200):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

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
        if parsed.path == "/relay/health":
            self._send_json({"ok": True, "time": _now(), "dir": str(RELAY_DIR)})
            return
        self._send_json({"error": "not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        payload = self._read_json() or {}
        channel_type = (payload.get("channel_type") or "im").strip()
        channel_id = (payload.get("channel_id") or "").strip()
        user_id = (payload.get("user_id") or "").strip()
        key = _key(channel_type, channel_id, user_id)

        if parsed.path == "/relay/message":
            role = (payload.get("role") or "user").strip()
            text = (payload.get("text") or "").strip()
            if not text:
                self._send_json({"ok": False, "error": "text required"}, status=400)
                return
            _append_message(key, role, text, user_id)
            self._send_json({"ok": True, "key": key})
            return

        if parsed.path == "/relay/context":
            limit = int(payload.get("limit") or 40)
            summarize = bool(payload.get("summarize"))
            tail = _read_tail(key, limit=limit)
            summary = _read_summary(key)
            if summarize:
                summary = _summarize(key, tail)
                if summary:
                    _write_summary(key, summary)
            self._send_json({"ok": True, "key": key, "summary": summary, "tail": tail})
            return

        if parsed.path == "/relay/summary":
            tail = _read_tail(key, limit=120)
            summary = _summarize(key, tail)
            if summary:
                _write_summary(key, summary)
            self._send_json({"ok": True, "summary": summary})
            return

        self._send_json({"error": "not found"}, status=404)


def main():
    host = os.environ.get("RELAY_HOST", "127.0.0.1")
    port = int(os.environ.get("RELAY_PORT", "8092"))
    server = HTTPServer((host, port), RelayServer)
    print(f"Relay server running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
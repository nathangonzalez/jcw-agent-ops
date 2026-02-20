#!/usr/bin/env python3
"""
Collect ops metrics (tokens, calls, VM health) and publish to Firestore.
"""

import argparse
import json
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from google.cloud import firestore  # type: ignore
except Exception:
    firestore = None

LOG_DIR = Path(os.environ.get("CLAWDBOT_LOG_DIR", "/opt/agent-ops/agent_outputs"))
USAGE_LOG = LOG_DIR / "codex_usage.log"
SLACK_LOG = LOG_DIR / "clawdbot_slack.log"


def parse_usage_line(line: str):
    match = re.search(r"\[(?P<ts>[^\]]+)\].*prompt=(?P<prompt>\d+) output=(?P<output>\d+)", line)
    if not match:
        return None
    ts_str = match.group("ts")
    try:
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return None
    return {
        "ts": ts,
        "prompt": int(match.group("prompt")),
        "output": int(match.group("output")),
    }


def parse_slack_lines(lines):
    stats = {"openclaw_calls": 0, "replies": 0, "errors": 0}
    for line in lines:
        lower = line.lower()
        if "openclaw ok" in lower:
            stats["openclaw_calls"] += 1
        if "reply sent" in lower:
            stats["replies"] += 1
        if "error" in lower:
            stats["errors"] += 1
    return stats


def read_recent_lines(path: Path, limit: int = 2000):
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]


def sum_usage(window_seconds: int):
    now = datetime.now(timezone.utc)
    prompt = 0
    output = 0
    lines = read_recent_lines(USAGE_LOG, 5000)
    for line in lines:
        parsed = parse_usage_line(line)
        if not parsed:
            continue
        age = (now - parsed["ts"]).total_seconds()
        if age <= window_seconds:
            prompt += parsed["prompt"]
            output += parsed["output"]
    return prompt, output


def read_meminfo():
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return None
    total = free = None
    for line in meminfo.read_text().splitlines():
        if line.startswith("MemTotal"):
            total = int(line.split()[1])
        if line.startswith("MemAvailable"):
            free = int(line.split()[1])
    if total is None or free is None:
        return None
    return {"mem_total_gb": round(total / 1024 / 1024, 2), "mem_free_gb": round(free / 1024 / 1024, 2)}


def collect_metrics():
    prompt_1h, output_1h = sum_usage(3600)
    prompt_24h, output_24h = sum_usage(86400)

    slack_lines_1h = read_recent_lines(SLACK_LOG, 2000)
    slack_stats = parse_slack_lines(slack_lines_1h)

    load_1m = os.getloadavg()[0] if hasattr(os, "getloadavg") else 0
    disk = shutil.disk_usage("/")
    mem = read_meminfo() or {}

    return {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "codex_prompt_tokens_1h": prompt_1h,
        "codex_output_tokens_1h": output_1h,
        "codex_prompt_tokens_24h": prompt_24h,
        "codex_output_tokens_24h": output_24h,
        "openclaw_calls_24h": slack_stats["openclaw_calls"],
        "slack_replies_1h": slack_stats["replies"],
        "slack_errors_1h": slack_stats["errors"],
        "vm_load_1m": round(load_1m, 2),
        "vm_disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
        "vm_mem_free_gb": mem.get("mem_free_gb"),
    }


def publish_firestore(doc_path: str, payload: dict):
    if firestore is None:
        raise RuntimeError("google-cloud-firestore not installed")
    if "/" in doc_path:
        collection, doc_id = doc_path.split("/", 1)
    else:
        collection, doc_id = "ops_metrics", doc_path
    client = firestore.Client()
    client.collection(collection).document(doc_id).set(payload, merge=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", default=os.environ.get("OPS_METRICS_DOC", "ops_metrics/current"))
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    payload = collect_metrics()

    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2))

    publish_firestore(args.doc, payload)
    print("Published metrics")


if __name__ == "__main__":
    main()
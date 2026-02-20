#!/usr/bin/env python3
"""
Approval queue helper.
"""

import argparse
import json
import time
from pathlib import Path


def load_queue(path: Path) -> list:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_queue(path: Path, items: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, indent=2))


def cmd_list(path: Path) -> int:
    items = load_queue(path)
    if not items:
        print("Queue is empty.")
        return 0
    for item in items:
        print(f"{item.get('id')} | {item.get('status')} | {item.get('task')}")
    return 0


def cmd_add(path: Path, task: str) -> int:
    items = load_queue(path)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    qid = f"Q-{stamp}"
    items.append(
        {
            "id": qid,
            "task": task,
            "status": "pending",
            "posted_at": None,
            "approved_at": None,
            "notes": "",
        }
    )
    save_queue(path, items)
    print(f"Added {qid}")
    return 0


def cmd_mark(path: Path, qid: str, status: str) -> int:
    items = load_queue(path)
    found = False
    for item in items:
        if item.get("id") == qid:
            item["status"] = status
            if status == "approved":
                item["approved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            found = True
            break
    if not found:
        print(f"Queue id not found: {qid}")
        return 1
    save_queue(path, items)
    print(f"Updated {qid} -> {status}")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", default="tasks/approval_queue.json", help="Queue JSON path")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")
    add_p = sub.add_parser("add")
    add_p.add_argument("task", help="Task text")
    mark_p = sub.add_parser("mark")
    mark_p.add_argument("id", help="Queue id")
    mark_p.add_argument("status", help="New status (approved|rejected|done)")

    args = parser.parse_args()
    path = Path(args.queue)

    if args.cmd == "list":
        return cmd_list(path)
    if args.cmd == "add":
        return cmd_add(path, args.task)
    if args.cmd == "mark":
        return cmd_mark(path, args.id, args.status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
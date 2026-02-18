#!/usr/bin/env python
"""Create Calendar event drafts (dry-run by default)."""

import argparse
import json
from pathlib import Path

from googleapiclient.discovery import build

from google_common import get_credentials

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def find_calendar_id(service, name):
    page_token = None
    while True:
        resp = service.calendarList().list(pageToken=page_token).execute()
        for item in resp.get("items", []):
            if item.get("summary") == name:
                return item.get("id")
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--start", required=True, help="ISO date-time, e.g., 2026-02-20T09:00:00")
    parser.add_argument("--end", required=True, help="ISO date-time, e.g., 2026-02-20T10:00:00")
    parser.add_argument("--timezone", default="America/Denver")
    parser.add_argument("--description", default="")
    parser.add_argument("--location", default="")
    parser.add_argument("--attendees", default="", help="Comma-separated emails")
    parser.add_argument("--calendar-name", default="JCW Drafts")
    parser.add_argument("--calendar-id", default="")
    parser.add_argument("--commit", action="store_true", help="Actually create the event")
    parser.add_argument("--out", default="", help="Optional path to write JSON")
    args = parser.parse_args()

    event = {
        "summary": args.title,
        "description": args.description,
        "location": args.location,
        "start": {"dateTime": args.start, "timeZone": args.timezone},
        "end": {"dateTime": args.end, "timeZone": args.timezone},
    }

    if args.attendees:
        event["attendees"] = [{"email": e.strip()} for e in args.attendees.split(",") if e.strip()]

    if args.out:
        Path(args.out).write_text(json.dumps(event, indent=2))

    if not args.commit:
        print("DRY RUN: Event not created. Use --commit to create in Calendar.")
        return

    creds = get_credentials(SCOPES)
    service = build("calendar", "v3", credentials=creds)

    calendar_id = args.calendar_id
    if not calendar_id:
        calendar_id = find_calendar_id(service, args.calendar_name)

    if not calendar_id:
        raise SystemExit(f"Calendar not found: {args.calendar_name}. Create it manually or pass --calendar-id.")

    created = service.events().insert(calendarId=calendar_id, body=event, sendUpdates="none").execute()
    print("Created event:", created.get("id"))


if __name__ == "__main__":
    main()

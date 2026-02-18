#!/usr/bin/env python
"""Create Gmail drafts (dry-run by default)."""

import argparse
import base64
from email.message import EmailMessage
from pathlib import Path

from googleapiclient.discovery import build

from google_common import get_credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def build_message(to, subject, body, cc=None, bcc=None):
    msg = EmailMessage()
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    msg["Subject"] = subject
    msg.set_content(body)
    return msg


def encode_message(msg: EmailMessage) -> str:
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--cc", default="")
    parser.add_argument("--bcc", default="")
    parser.add_argument("--commit", action="store_true", help="Actually create the draft in Gmail")
    parser.add_argument("--out", default="", help="Optional path to write .eml")
    args = parser.parse_args()

    msg = build_message(args.to, args.subject, args.body, cc=args.cc or None, bcc=args.bcc or None)
    raw = encode_message(msg)

    if args.out:
        Path(args.out).write_bytes(msg.as_bytes())

    if not args.commit:
        print("DRY RUN: Draft not created. Use --commit to create in Gmail.")
        return

    creds = get_credentials(SCOPES)
    service = build("gmail", "v1", credentials=creds)
    draft = {"message": {"raw": raw}}
    result = service.users().drafts().create(userId="me", body=draft).execute()
    print("Created draft:", result.get("id"))


if __name__ == "__main__":
    main()

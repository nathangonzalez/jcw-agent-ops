#!/usr/bin/env python
"""Shared helpers for Google API scripts."""

from pathlib import Path
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

DEFAULT_CREDS = Path(__file__).resolve().parent.parent / "data" / "google" / "credentials.json"
DEFAULT_TOKEN = Path(__file__).resolve().parent.parent / "data" / "google" / "token.json"


def get_credentials(scopes: List[str], creds_path: Path = DEFAULT_CREDS, token_path: Path = DEFAULT_TOKEN) -> Credentials:
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError(f"Missing credentials: {creds_path}")
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), scopes)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())

    return creds

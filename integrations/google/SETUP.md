# Google Integration Setup (Draft-Only)

This setup enables draft creation for Gmail and Calendar. All scripts default to dry-run and require --commit to perform external actions.

## 1) Create OAuth credentials
1. Open Google Cloud Console and select a project.
2. Enable Gmail API and Google Calendar API.
3. Configure OAuth consent screen.
4. Create OAuth Client ID of type Desktop App.
5. Download the JSON and save it as:
   data/google/credentials.json

OAuth for installed apps is documented here.

## 2) Install Python dependencies

pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

## 3) Create a drafts calendar (recommended)
Create a calendar named "JCW Drafts" in Google Calendar so events are never added to your primary calendar by accident.

## 4) Run the draft scripts

Gmail draft (dry-run):
python scripts/google_gmail_draft.py --to "someone@example.com" --subject "Draft" --body "Hello"

Gmail draft (commit):
python scripts/google_gmail_draft.py --to "someone@example.com" --subject "Draft" --body "Hello" --commit

Calendar event draft (dry-run):
python scripts/google_calendar_draft.py --title "Site visit" --start "2026-02-20T09:00:00" --end "2026-02-20T10:00:00" --timezone "America/Denver"

Calendar event draft (commit):
python scripts/google_calendar_draft.py --title "Site visit" --start "2026-02-20T09:00:00" --end "2026-02-20T10:00:00" --timezone "America/Denver" --commit

Use --calendar-name "JCW Drafts" (default) or --calendar-id if you want a specific calendar.

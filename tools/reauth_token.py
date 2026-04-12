"""
Re-authenticate OAuth token with all required scopes.

Usage:
    python tools/reauth_token.py

Opens a browser for Google OAuth consent. Saves token.json with all scopes.
"""

import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/youtube",
]

CREDENTIALS_FILE = Path(__file__).parent.parent / "credentials.json"
TOKEN_FILE = Path(__file__).parent.parent / "token.json"


def main():
    print(f"Requesting {len(SCOPES)} scopes:")
    for s in SCOPES:
        print(f"  - {s}")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    # Verify
    token = json.loads(TOKEN_FILE.read_text())
    granted = token.get("scopes", [])
    print(f"\nToken saved with {len(granted)} scopes:")
    for s in granted:
        print(f"  - {s}")

    missing = set(SCOPES) - set(granted)
    if missing:
        print(f"\nWARNING: Missing scopes: {missing}")
    else:
        print("\nAll scopes granted.")


if __name__ == "__main__":
    main()

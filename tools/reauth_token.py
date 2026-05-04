"""
Re-authenticate OAuth token with all required scopes.

Usage:
    python tools/reauth_token.py

Opens a browser for Google OAuth consent. Saves token.json with all scopes.
"""

import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auth import SCOPES, CREDENTIALS_FILE, TOKEN_FILE


def main():
    print(f"Force reauth -- requesting {len(SCOPES)} scopes:")
    for s in SCOPES:
        print(f"  - {s}")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json())

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

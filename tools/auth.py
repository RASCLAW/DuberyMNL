"""
Shared Google OAuth helper.

Always uses the full scope set so no individual tool can accidentally strip
scopes from token.json during a reauth flow.

Import pattern (from any tools/subdir/script.py):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from auth import get_credentials
"""
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

_TOOLS_DIR = Path(__file__).parent
PROJECT_ROOT = _TOOLS_DIR.parent
TOKEN_FILE = PROJECT_ROOT / "token.json"
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/youtube",
]


def _run_flow() -> Credentials:
    """Run the interactive browser consent for the current SCOPES."""
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    return flow.run_local_server(port=0)


def get_credentials() -> Credentials:
    """Load, refresh, or first-time-auth with the full scope set. Saves token.json on change.

    Gentle by design: a valid cached token is returned as-is, so this never surprises
    a headless caller (cron job, server) with a browser prompt. Adding a NEW scope to
    SCOPES does NOT force a reauth here -- run reauth() once to grant it (a token
    refresh cannot widen scopes).
    """
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = _run_flow()
        TOKEN_FILE.write_text(creds.to_json())

    return creds


def reauth() -> Credentials:
    """Force a fresh browser consent for the CURRENT SCOPES, then overwrite token.json.

    Run once after editing SCOPES (e.g. adding the tasks scope):
        python -c "import sys;sys.path.insert(0,'tools');from auth import reauth;reauth()"
    Re-grants the full set, so existing scopes keep working too.
    """
    creds = _run_flow()
    TOKEN_FILE.write_text(creds.to_json())
    return creds


def service(name: str, version: str):
    """Build an authorized Google API client, e.g. service('gmail', 'v1')."""
    return build(name, version, credentials=get_credentials(), cache_discovery=False)

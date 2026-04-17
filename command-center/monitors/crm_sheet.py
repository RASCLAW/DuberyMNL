"""CRM sheet monitor -- verifies the DuberyMNL Google Sheet is readable.

Reads the header row (row 1) of the first tab via the existing
`tools/sheets/read_sheet.py` module. IPv4-only patch is applied before any
google-api-python-client import (see feedback_google_api_client_broken.md).
"""
from __future__ import annotations

# --- IPv4-only patch (MUST come before any googleapiclient imports) ----
# Google APIs return IPv6 first; RA's ISP can't route IPv6 -> 60s hangs.
import socket as _socket
_orig_getaddrinfo = _socket.getaddrinfo
def _ipv4_only_getaddrinfo(*args, **kwargs):
    return [r for r in _orig_getaddrinfo(*args, **kwargs) if r[0] == _socket.AF_INET]
_socket.getaddrinfo = _ipv4_only_getaddrinfo
# -----------------------------------------------------------------------

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from monitors import ServiceStatus  # noqa: E402

SHEET_ID_ENV = "GOOGLE_SHEETS_SPREADSHEET_ID"
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"


def check() -> ServiceStatus:
    log_src = str(TOKEN_FILE) if TOKEN_FILE.exists() else None
    try:
        spreadsheet_id = os.environ.get(SHEET_ID_ENV)
        if not spreadsheet_id:
            return ServiceStatus.now(
                "crm_sheet", "not_wired", f"{SHEET_ID_ENV} missing from .env", log_src
            )
        if not CREDENTIALS_FILE.exists() or not TOKEN_FILE.exists():
            return ServiceStatus.now(
                "crm_sheet", "not_wired", "credentials missing", log_src
            )

        from sheets.read_sheet import get_sheets_service  # noqa: E402

        service = get_sheets_service()
        meta = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id, includeGridData=False
        ).execute()
        first_tab = meta["sheets"][0]["properties"]["title"]
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=f"{first_tab}!1:1"
        ).execute()
        headers = result.get("values", [[]])[0]
        msg = f"sheet reachable -- tab '{first_tab}', {len(headers)} headers"
        return ServiceStatus.now("crm_sheet", "active", msg, log_src)
    except Exception as exc:
        return ServiceStatus.now(
            "crm_sheet", "offline", f"{type(exc).__name__}: {exc}", log_src
        )


if __name__ == "__main__":
    print(check())

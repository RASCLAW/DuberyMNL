"""
Delete a folder (and all its contents recursively) from Google Drive.

Permanent delete -- does NOT move to trash. Use with care.

Includes the same IPv4 monkey-patch as sync_folder.py because RA's home ISP
doesn't route IPv6 and Python waits ~60s per call waiting for IPv6 fallback.
See feedback_google_api_client_broken.md for the full story.

Usage:
    python tools/drive/delete_folder.py --remote "DuberyMNL/backup/contents/failed"
    python tools/drive/delete_folder.py --remote "..." --dry-run
"""

# ==== IPv4 MONKEY-PATCH -- MUST BE BEFORE HTTP IMPORTS ====
import socket as _socket
_orig_getaddrinfo = _socket.getaddrinfo
def _ipv4_only_getaddrinfo(*args, **kwargs):
    return [r for r in _orig_getaddrinfo(*args, **kwargs) if r[0] == _socket.AF_INET]
_socket.getaddrinfo = _ipv4_only_getaddrinfo
# ==========================================================

import argparse
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

SCOPES = ["https://www.googleapis.com/auth/drive"]
TOKEN_FILE = PROJECT_DIR / "token.json"
API_BASE = "https://www.googleapis.com/drive/v3"
TIMEOUT = 60


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def get_credentials() -> Credentials:
    if not TOKEN_FILE.exists():
        print(f"Error: token.json not found at {TOKEN_FILE}", file=sys.stderr)
        sys.exit(1)
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())
        else:
            print("Error: token.json is invalid and cannot be refreshed", file=sys.stderr)
            sys.exit(1)
    return creds


class DriveClient:
    def __init__(self, creds: Credentials):
        self.creds = creds
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {creds.token}"

    def find_folder(self, name: str, parent_id: str) -> str | None:
        q = (
            f"name='{_escape(name)}' and "
            f"mimeType='application/vnd.google-apps.folder' and "
            f"'{parent_id}' in parents and trashed=false"
        )
        r = self.session.get(
            f"{API_BASE}/files",
            params={"q": q, "fields": "files(id)", "pageSize": 10},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        files = r.json().get("files", [])
        return files[0]["id"] if files else None

    def count_descendants(self, folder_id: str) -> tuple[int, int]:
        """Return (file_count, folder_count) under folder_id recursively."""
        files = 0
        folders = 0
        stack = [folder_id]
        while stack:
            cur = stack.pop()
            page_token = None
            while True:
                params = {
                    "q": f"'{cur}' in parents and trashed=false",
                    "fields": "nextPageToken,files(id,mimeType)",
                    "pageSize": 100,
                }
                if page_token:
                    params["pageToken"] = page_token
                r = self.session.get(f"{API_BASE}/files", params=params, timeout=TIMEOUT)
                r.raise_for_status()
                data = r.json()
                for f in data.get("files", []):
                    if f["mimeType"] == "application/vnd.google-apps.folder":
                        folders += 1
                        stack.append(f["id"])
                    else:
                        files += 1
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
        return files, folders

    def delete(self, file_id: str):
        r = self.session.delete(f"{API_BASE}/files/{file_id}", timeout=TIMEOUT)
        if r.status_code not in (204, 200):
            r.raise_for_status()


def resolve_path(client: DriveClient, remote_path: str) -> str:
    parts = [p for p in remote_path.replace("\\", "/").split("/") if p]
    parent_id = "root"
    traversed = ""
    for part in parts:
        traversed = f"{traversed}/{part}" if traversed else part
        fid = client.find_folder(part, parent_id)
        if not fid:
            print(f"Error: path does not exist in Drive: {remote_path}", file=sys.stderr)
            print(f"       (missing folder: {traversed})", file=sys.stderr)
            sys.exit(1)
        parent_id = fid
    return parent_id


def main():
    parser = argparse.ArgumentParser(description="Delete a folder and its contents from Google Drive")
    parser.add_argument("--remote", required=True, help='Drive folder path e.g. "DuberyMNL/backup/contents/failed"')
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    args = parser.parse_args()

    creds = get_credentials()
    client = DriveClient(creds)

    print(f"Resolving path: {args.remote}")
    folder_id = resolve_path(client, args.remote)
    print(f"  -> folder id: {folder_id}")

    print("Counting contents (recursive)...")
    file_count, folder_count = client.count_descendants(folder_id)
    print(f"  -> {file_count} files in {folder_count} subfolders (plus the root folder)")

    if args.dry_run:
        print()
        print(f"[dry-run] would delete: {args.remote}")
        print(f"[dry-run] would remove: {file_count} files + {folder_count + 1} folders")
        return

    print()
    print(f"Deleting {args.remote}...")
    client.delete(folder_id)
    print(f"Deleted: {args.remote} ({file_count} files + {folder_count + 1} folders removed)")


if __name__ == "__main__":
    main()

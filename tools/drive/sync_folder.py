"""
Sync a local folder to Google Drive. Mirrors directory structure.

Idempotent -- files matching name + parent folder are skipped. Safe to re-run.
Backup mode: uploaded files are NOT made public (unlike upload_image.py).

IPv4-only: Patches socket.getaddrinfo to filter out IPv6 addresses because RA's
home ISP doesn't route IPv6. Python waits ~60s for OS TCP timeout on IPv6
attempts before falling back to IPv4, which made every API call molasses-slow.
See feedback_google_api_client_broken.md for the full diagnosis. The patch is
process-wide but harmless in cloud environments where IPv6 works.

Usage:
    python tools/drive/sync_folder.py --local contents/failed --remote "DuberyMNL/backup/content/failed"
    python tools/drive/sync_folder.py --local archives --remote "DuberyMNL/backup/archives" --dry-run
"""

# ==== IPv4 MONKEY-PATCH -- MUST BE BEFORE HTTP IMPORTS ====
import socket as _socket
_orig_getaddrinfo = _socket.getaddrinfo
def _ipv4_only_getaddrinfo(*args, **kwargs):
    return [r for r in _orig_getaddrinfo(*args, **kwargs) if r[0] == _socket.AF_INET]
_socket.getaddrinfo = _ipv4_only_getaddrinfo
# ==========================================================

import argparse
import json
import mimetypes
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
TOKEN_FILE = PROJECT_DIR / "token.json"

API_BASE = "https://www.googleapis.com/drive/v3"
UPLOAD_BASE = "https://www.googleapis.com/upload/drive/v3"
TIMEOUT = 60  # seconds -- large uploads need room


class DriveClient:
    def __init__(self, creds: Credentials):
        self.creds = creds
        self.session = requests.Session()
        self._update_auth_header()

    def _update_auth_header(self):
        self.session.headers["Authorization"] = f"Bearer {self.creds.token}"

    def _ensure_token(self):
        if not self.creds.valid:
            self.creds.refresh(Request())
            self._update_auth_header()
            TOKEN_FILE.write_text(self.creds.to_json())

    def find_folder(self, name: str, parent_id: str) -> str | None:
        self._ensure_token()
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

    def create_folder(self, name: str, parent_id: str) -> str:
        self._ensure_token()
        body = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        r = self.session.post(
            f"{API_BASE}/files",
            params={"fields": "id"},
            json=body,
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["id"]

    def file_exists(self, name: str, parent_id: str) -> bool:
        self._ensure_token()
        q = f"name='{_escape(name)}' and '{parent_id}' in parents and trashed=false"
        r = self.session.get(
            f"{API_BASE}/files",
            params={"q": q, "fields": "files(id)", "pageSize": 1},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return bool(r.json().get("files"))

    def upload_file(self, local_path: Path, parent_id: str) -> dict:
        """Resumable upload. Works for any file size, tolerates interruptions."""
        self._ensure_token()
        mime_type, _ = mimetypes.guess_type(str(local_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        size = local_path.stat().st_size
        metadata = {"name": local_path.name, "parents": [parent_id]}

        # Step 1: initiate resumable upload session
        init = self.session.post(
            f"{UPLOAD_BASE}/files",
            params={"uploadType": "resumable"},
            headers={
                "X-Upload-Content-Type": mime_type,
                "X-Upload-Content-Length": str(size),
            },
            json=metadata,
            timeout=TIMEOUT,
        )
        init.raise_for_status()
        upload_url = init.headers["Location"]

        # Step 2: upload file bytes in one PUT (simpler than chunking)
        with open(local_path, "rb") as f:
            body = f.read()
        put = requests.put(
            upload_url,
            data=body,
            headers={"Content-Type": mime_type, "Content-Length": str(size)},
            timeout=TIMEOUT * 5,  # big files need more headroom
        )
        put.raise_for_status()
        return put.json()


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


def get_or_create_folder(client: DriveClient, folder_path: str, cache: dict, dry_run: bool) -> str:
    if folder_path in cache:
        return cache[folder_path]

    parts = [p for p in folder_path.replace("\\", "/").split("/") if p]
    parent_id = "root"
    traversed = ""
    in_dryrun_chain = False  # once a parent is faked, don't hit API for children

    for part in parts:
        traversed = f"{traversed}/{part}" if traversed else part
        if traversed in cache:
            parent_id = cache[traversed]
            if parent_id.startswith("DRYRUN_"):
                in_dryrun_chain = True
            continue

        if in_dryrun_chain:
            parent_id = f"DRYRUN_{traversed}"
            print(f"  [dry-run] would create folder: {traversed}")
        else:
            found = client.find_folder(part, parent_id)
            if found:
                parent_id = found
            elif dry_run:
                print(f"  [dry-run] would create folder: {traversed}")
                parent_id = f"DRYRUN_{traversed}"
                in_dryrun_chain = True
            else:
                parent_id = client.create_folder(part, parent_id)
                print(f"  created folder: {traversed}")

        cache[traversed] = parent_id

    return parent_id


def sync(client: DriveClient, local_root: Path, remote_root: str, dry_run: bool) -> dict:
    stats = {"files_total": 0, "uploaded": 0, "skipped": 0, "errors": 0, "bytes": 0}
    folder_cache = {}

    all_files = [p for p in local_root.rglob("*") if p.is_file()]
    stats["files_total"] = len(all_files)

    print(f"Syncing {len(all_files)} files from {local_root} -> {remote_root}")
    if dry_run:
        print("DRY RUN -- no changes will be made")
    print()

    for idx, local_file in enumerate(all_files, start=1):
        rel = local_file.relative_to(local_root).as_posix()
        rel_dir = str(Path(rel).parent).replace("\\", "/")
        drive_folder_path = remote_root if rel_dir == "." else f"{remote_root}/{rel_dir}"

        try:
            folder_id = get_or_create_folder(client, drive_folder_path, folder_cache, dry_run)

            if not folder_id.startswith("DRYRUN_") and client.file_exists(local_file.name, folder_id):
                stats["skipped"] += 1
                print(f"  [{idx}/{len(all_files)}] SKIP (exists): {rel}")
                continue

            size_kb = local_file.stat().st_size // 1024
            if dry_run:
                print(f"  [{idx}/{len(all_files)}] [dry-run] {rel} ({size_kb}KB)")
            else:
                client.upload_file(local_file, folder_id)
                print(f"  [{idx}/{len(all_files)}] [uploaded] {rel} ({size_kb}KB)")
                stats["uploaded"] += 1
                stats["bytes"] += local_file.stat().st_size

            if not dry_run and idx % 20 == 0:
                time.sleep(0.5)

        except requests.HTTPError as e:
            stats["errors"] += 1
            print(f"  [{idx}/{len(all_files)}] HTTP ERROR: {rel} -- {e.response.status_code} {e.response.text[:200]}", file=sys.stderr)
            if stats["errors"] >= 5:
                print("Too many errors, aborting", file=sys.stderr)
                break
        except Exception as e:
            stats["errors"] += 1
            print(f"  [{idx}/{len(all_files)}] ERROR: {rel} -- {type(e).__name__}: {e}", file=sys.stderr)
            if stats["errors"] >= 5:
                print("Too many errors, aborting", file=sys.stderr)
                break

    return stats


def main():
    parser = argparse.ArgumentParser(description="Sync local folder to Google Drive")
    parser.add_argument("--local", required=True, help="Local folder to sync")
    parser.add_argument("--remote", required=True, help='Drive destination path e.g. "DuberyMNL/backup/content"')
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    args = parser.parse_args()

    local_root = Path(args.local).resolve()
    if not local_root.exists() or not local_root.is_dir():
        print(f"Error: not a directory: {local_root}", file=sys.stderr)
        sys.exit(1)

    creds = get_credentials()
    client = DriveClient(creds)
    stats = sync(client, local_root, args.remote, args.dry_run)

    print()
    print("=== SUMMARY ===")
    print(f"Files found:  {stats['files_total']}")
    print(f"Uploaded:     {stats['uploaded']}")
    print(f"Skipped:      {stats['skipped']}")
    print(f"Errors:       {stats['errors']}")
    print(f"Bytes sent:   {stats['bytes'] // 1024 // 1024}MB")

    # Append summary to drive-sync.log for /sendit workflow
    from datetime import datetime
    log_path = Path(__file__).resolve().parent.parent.parent / ".tmp" / "drive-sync.log"
    log_path.parent.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{ts}] {args.remote} | {stats['uploaded']} uploaded, {stats['skipped']} skipped, {stats['errors']} errors, {stats['bytes'] // 1024 // 1024}MB\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_line)

    if stats["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

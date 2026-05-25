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
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth import get_credentials as _auth_get_credentials

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

    def list_folder_files(self, parent_id: str) -> set[str]:
        """Return set of all non-trashed file names directly under parent_id.

        Replaces N individual file_exists() calls with one paginated list.
        Massive speedup for many-small-files syncs.
        """
        self._ensure_token()
        names: set[str] = set()
        page_token: str | None = None
        q = f"'{parent_id}' in parents and trashed=false"
        while True:
            params = {
                "q": q,
                "fields": "files(name),nextPageToken",
                "pageSize": 1000,
            }
            if page_token:
                params["pageToken"] = page_token
            r = self.session.get(f"{API_BASE}/files", params=params, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            for f in data.get("files", []):
                if f.get("name"):
                    names.add(f["name"])
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return names

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
    return _auth_get_credentials()


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


def sync(client: DriveClient, local_root: Path, remote_root: str, dry_run: bool,
         workers: int = 4) -> dict:
    """Two-phase sync:
      Phase 1 (sequential): walk locals, resolve all destination folders,
        bulk-list existing names per folder (1 API call per folder vs N per file).
      Phase 2 (parallel): upload missing files with a small worker pool.
    """
    stats = {"files_total": 0, "uploaded": 0, "skipped": 0, "errors": 0, "bytes": 0}
    stats_lock = threading.Lock()
    folder_cache: dict = {}

    all_files = [p for p in local_root.rglob("*") if p.is_file()]
    stats["files_total"] = len(all_files)

    print(f"Syncing {len(all_files)} files from {local_root} -> {remote_root}")
    if dry_run:
        print("DRY RUN -- no changes will be made")
    print()

    # ---- Phase 1: group by destination folder + bulk-check existence ----
    # Group local files by the Drive folder they'll land in.
    by_folder: dict[str, list[Path]] = {}
    for local_file in all_files:
        rel = local_file.relative_to(local_root).as_posix()
        rel_dir = str(Path(rel).parent).replace("\\", "/")
        drive_folder_path = remote_root if rel_dir == "." else f"{remote_root}/{rel_dir}"
        by_folder.setdefault(drive_folder_path, []).append(local_file)

    print(f"Phase 1: resolving {len(by_folder)} destination folder(s) + bulk-checking existence...")

    # upload_queue[i] = (local_file, folder_id, rel_path)
    upload_queue: list[tuple[Path, str, str]] = []
    for drive_folder_path, files in by_folder.items():
        try:
            folder_id = get_or_create_folder(client, drive_folder_path, folder_cache, dry_run)
        except Exception as e:
            print(f"  ERROR resolving {drive_folder_path}: {e}", file=sys.stderr)
            stats["errors"] += len(files)
            continue

        if folder_id.startswith("DRYRUN_"):
            existing_names: set[str] = set()
        else:
            try:
                existing_names = client.list_folder_files(folder_id)
            except Exception as e:
                print(f"  ERROR listing {drive_folder_path}: {e}", file=sys.stderr)
                existing_names = set()

        for local_file in files:
            rel = local_file.relative_to(local_root).as_posix()
            if local_file.name in existing_names:
                stats["skipped"] += 1
                continue
            upload_queue.append((local_file, folder_id, rel))

    print(f"  resolved. {stats['skipped']} already on Drive, {len(upload_queue)} to upload.")

    if not upload_queue:
        print("Nothing to upload.")
        return stats

    # ---- Phase 2: parallel uploads ----
    if dry_run:
        print(f"\nPhase 2 (DRY-RUN): would upload {len(upload_queue)} files")
        for local_file, _folder_id, rel in upload_queue:
            size_kb = local_file.stat().st_size // 1024
            print(f"  [dry-run] {rel} ({size_kb}KB)")
        return stats

    print(f"\nPhase 2: uploading {len(upload_queue)} files with {workers} parallel workers...")

    def upload_one(item: tuple[Path, str, str]) -> tuple[str, str, int, str | None]:
        local_file, folder_id, rel = item
        try:
            client.upload_file(local_file, folder_id)
            size = local_file.stat().st_size
            return ("ok", rel, size, None)
        except requests.HTTPError as e:
            return ("err", rel, 0, f"HTTP {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            return ("err", rel, 0, f"{type(e).__name__}: {e}")

    completed = 0
    total = len(upload_queue)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(upload_one, item) for item in upload_queue]
        for fut in as_completed(futures):
            status, rel, size, err = fut.result()
            completed += 1
            with stats_lock:
                if status == "ok":
                    stats["uploaded"] += 1
                    stats["bytes"] += size
                else:
                    stats["errors"] += 1
            if status == "ok":
                print(f"  [{completed}/{total}] uploaded: {rel} ({size // 1024}KB)")
            else:
                print(f"  [{completed}/{total}] ERROR: {rel} -- {err}", file=sys.stderr)
                if stats["errors"] >= 5:
                    # Cancel any not-yet-started futures and bail.
                    for f in futures:
                        f.cancel()
                    print("Too many errors, aborting", file=sys.stderr)
                    break

    return stats


def main():
    parser = argparse.ArgumentParser(description="Sync local folder to Google Drive")
    parser.add_argument("--local", required=True, help="Local folder to sync")
    parser.add_argument("--remote", required=True, help='Drive destination path e.g. "DuberyMNL/backup/content"')
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    parser.add_argument("--workers", type=int, default=4,
                        help="Parallel upload workers (default 4; raise cautiously, Drive API rate-limits ~10 QPS)")
    args = parser.parse_args()

    local_root = Path(args.local).resolve()
    if not local_root.exists() or not local_root.is_dir():
        print(f"Error: not a directory: {local_root}", file=sys.stderr)
        sys.exit(1)

    creds = get_credentials()
    client = DriveClient(creds)
    stats = sync(client, local_root, args.remote, args.dry_run, workers=args.workers)

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

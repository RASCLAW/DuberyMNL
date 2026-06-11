"""
Report what's eating your Google Drive storage.

Read-only. Prints:
  1. Storage quota breakdown (limit, total usage, Drive, Drive trash, Gmail+Photos+other).
  2. Top-N largest files you OWN (only owned files count toward your quota),
     newest-size-first, with immediate parent folder, modified date, and a [TRASHED] flag.
  3. Trash total (trashed files still count toward storage until trash is emptied).

Only files you own consume your quota; shared files owned by others don't, so the
listing filters to "'me' in owners". The Drive API can't split Gmail vs Photos, so
those are reported together as (total usage - Drive usage).

IPv4-only socket patch (same rationale as sync_folder.py): RA's home ISP doesn't
route IPv6, so without this every Google API call hangs ~60s before falling back.

Usage:
    python tools/drive/storage_report.py
    python tools/drive/storage_report.py --top 60
    python tools/drive/storage_report.py --top 40 --min-mb 50
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
from google.auth.transport.requests import Request

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth import get_credentials

TOKEN_FILE = PROJECT_DIR / "token.json"
API_BASE = "https://www.googleapis.com/drive/v3"
TIMEOUT = 60


def _human(n: int | float | None) -> str:
    if n is None:
        return "?"
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024.0:
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024.0
    return f"{n:.1f} PB"


class Drive:
    def __init__(self, creds):
        self.creds = creds
        self.s = requests.Session()
        self._auth()

    def _auth(self):
        if not self.creds.valid:
            self.creds.refresh(Request())
            TOKEN_FILE.write_text(self.creds.to_json())
        self.s.headers["Authorization"] = f"Bearer {self.creds.token}"

    def get(self, path, **params):
        self._auth()
        r = self.s.get(f"{API_BASE}/{path}", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()


def main():
    ap = argparse.ArgumentParser(description="Report Google Drive storage usage")
    ap.add_argument("--top", type=int, default=40, help="How many largest files to list (default 40)")
    ap.add_argument("--min-mb", type=float, default=0, help="Only list files at least this many MB")
    args = ap.parse_args()

    d = Drive(get_credentials())

    # ---- 1. Quota ----
    about = d.get("about", fields="user,storageQuota")
    q = about.get("storageQuota", {})
    user = about.get("user", {})
    limit = int(q["limit"]) if q.get("limit") else None
    usage = int(q.get("usage", 0))
    in_drive = int(q.get("usageInDrive", 0))
    in_trash = int(q.get("usageInDriveTrash", 0))
    other = usage - in_drive  # Gmail + Photos + anything non-Drive

    print("=== Google Drive Storage ===")
    print(f"Account:           {user.get('emailAddress', '?')}")
    if limit:
        pct = usage / limit * 100
        print(f"Limit:             {_human(limit)}")
        print(f"Used (total):      {_human(usage)}  ({pct:.0f}%)")
    else:
        print(f"Used (total):      {_human(usage)}  (unlimited / pooled plan)")
    print(f"  Drive files:     {_human(in_drive)}")
    print(f"  Drive trash:     {_human(in_trash)}   <- still counts; empty trash to reclaim")
    print(f"  Gmail + Photos:  {_human(other)}   (Drive API can't split these)")
    print()

    # ---- 2. Largest owned files (ordered server-side by storage used) ----
    print(f"=== Top {args.top} largest files you own ===")
    files = []
    page_token = None
    while len(files) < args.top:
        params = {
            "q": "'me' in owners",
            "orderBy": "quotaBytesUsed desc",
            "fields": "files(id,name,quotaBytesUsed,size,mimeType,modifiedTime,parents,trashed),nextPageToken",
            "pageSize": min(200, args.top - len(files) + 50),
            "spaces": "drive",
        }
        if page_token:
            params["pageToken"] = page_token
        data = d.get("files", **params)
        files.extend(data.get("files", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break

    min_bytes = args.min_mb * 1024 * 1024
    parent_cache: dict[str, str] = {}

    def parent_name(file: dict) -> str:
        parents = file.get("parents") or []
        if not parents:
            return "(root or shared)"
        pid = parents[0]
        if pid not in parent_cache:
            try:
                pinfo = d.get(f"files/{pid}", fields="name")
                parent_cache[pid] = pinfo.get("name", "?")
            except Exception:
                parent_cache[pid] = "?"
        return parent_cache[pid]

    shown = 0
    for f in files:
        used = int(f.get("quotaBytesUsed", 0))
        if used < min_bytes:
            continue
        if shown >= args.top:
            break
        shown += 1
        flag = "  [TRASHED]" if f.get("trashed") else ""
        modified = (f.get("modifiedTime") or "")[:10]
        folder = parent_name(f)
        name = f.get("name", "?")
        if len(name) > 50:
            name = name[:47] + "..."
        print(f"  {shown:>2}. {_human(used):>9}  {name:<50}  [{folder}]  {modified}{flag}")

    if shown == 0:
        print("  (no owned files matched)")
    print()
    print("Tip: empty Drive trash to reclaim the trash total above; large .mp4/.zip/.psd")
    print("     files and old backups are usually the quickest wins.")


if __name__ == "__main__":
    main()

"""
Move specific Google Drive items to Trash (recoverable ~30 days). NOT permanent.

Safer companion to delete_folder.py (which hard-deletes). Resolves targets by
exact name (owned-by-me, not already trashed) or by file id, shows a verification
table with size + parent + type, and only acts with --execute. A name that
matches 0 or >1 files is reported and SKIPPED (never guesses which to trash).

Trashing a folder trashes its whole subtree. Trashed items still count toward
quota until trash is emptied -- run empty_trash (or Drive UI) to reclaim space.

IPv4-only socket patch: RA's home ISP doesn't route IPv6 (see sync_folder.py).

Usage:
    python tools/drive/trash_items.py --name "portfolio.html" --name "Skate Pilipinas"   # dry-run
    python tools/drive/trash_items.py --name "portfolio.html" --execute
    python tools/drive/trash_items.py --id 1AbC... --execute
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
FOLDER_MIME = "application/vnd.google-apps.folder"


def _human(n):
    if n is None:
        return "?"
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024.0:
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024.0
    return f"{n:.1f} PB"


def _escape(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")


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

    def find_by_name(self, name):
        self._auth()
        q = f"name = '{_escape(name)}' and 'me' in owners and trashed = false"
        r = self.s.get(f"{API_BASE}/files", params={
            "q": q,
            "fields": "files(id,name,mimeType,size,quotaBytesUsed,parents,trashed)",
            "pageSize": 50,
        }, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json().get("files", [])

    def get(self, file_id):
        self._auth()
        r = self.s.get(f"{API_BASE}/files/{file_id}", params={
            "fields": "id,name,mimeType,size,quotaBytesUsed,parents,trashed",
        }, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()

    def parent_name(self, file, cache):
        parents = file.get("parents") or []
        if not parents:
            return "(root/shared)"
        pid = parents[0]
        if pid not in cache:
            try:
                cache[pid] = self.get(pid).get("name", "?")
            except Exception:
                cache[pid] = "?"
        return cache[pid]

    def folder_size(self, folder_id):
        """Sum quotaBytesUsed of everything under a folder (one level of listing,
        recursing into subfolders). Best-effort -- for reporting only."""
        self._auth()
        total = 0
        stack = [folder_id]
        seen = set()
        while stack:
            fid = stack.pop()
            if fid in seen:
                continue
            seen.add(fid)
            page_token = None
            while True:
                params = {
                    "q": f"'{fid}' in parents and trashed = false",
                    "fields": "files(id,mimeType,quotaBytesUsed),nextPageToken",
                    "pageSize": 1000,
                }
                if page_token:
                    params["pageToken"] = page_token
                r = self.s.get(f"{API_BASE}/files", params=params, timeout=TIMEOUT)
                r.raise_for_status()
                data = r.json()
                for c in data.get("files", []):
                    total += int(c.get("quotaBytesUsed", 0))
                    if c.get("mimeType") == FOLDER_MIME:
                        stack.append(c["id"])
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
        return total

    def trash(self, file_id):
        self._auth()
        r = self.s.patch(f"{API_BASE}/files/{file_id}", params={"fields": "id,name,trashed"},
                         json={"trashed": True}, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()


def main():
    ap = argparse.ArgumentParser(description="Trash specific Drive items (recoverable)")
    ap.add_argument("--name", action="append", default=[], help="Exact file/folder name (repeatable)")
    ap.add_argument("--id", action="append", default=[], dest="ids", help="Drive file id (repeatable)")
    ap.add_argument("--execute", action="store_true", help="Actually trash (default: dry-run)")
    args = ap.parse_args()

    if not args.name and not args.ids:
        ap.error("give at least one --name or --id")

    d = Drive(get_credentials())
    cache = {}
    resolved = []   # (file_dict, effective_bytes)
    skipped = []    # (label, reason)

    for name in args.name:
        matches = d.find_by_name(name)
        if len(matches) == 0:
            skipped.append((name, "no owned, non-trashed match"))
        elif len(matches) > 1:
            detail = "; ".join(f"{m['id']} in [{d.parent_name(m, cache)}] ({_human(int(m.get('quotaBytesUsed',0)))})" for m in matches)
            skipped.append((name, f"{len(matches)} matches -- pass the exact --id: {detail}"))
        else:
            resolved.append(matches[0])

    for fid in args.ids:
        try:
            resolved.append(d.get(fid))
        except Exception as e:
            skipped.append((fid, f"lookup failed: {e}"))

    print("=== Targets ===")
    total_bytes = 0
    rows = []
    for f in resolved:
        is_folder = f.get("mimeType") == FOLDER_MIME
        if is_folder:
            size = d.folder_size(f["id"])
            kind = "FOLDER (subtree)"
        else:
            size = int(f.get("quotaBytesUsed", 0))
            kind = "file"
        total_bytes += size
        rows.append((f, size, kind, d.parent_name(f, cache)))

    for f, size, kind, parent in rows:
        print(f"  {_human(size):>9}  {kind:<16}  {f.get('name'):<45}  [{parent}]  id={f['id']}")
    if not rows:
        print("  (nothing resolved)")
    print(f"\n  Reclaimable after emptying trash: ~{_human(total_bytes)}")

    if skipped:
        print("\n=== Skipped (NOT trashed) ===")
        for label, reason in skipped:
            print(f"  {label!r}: {reason}")

    if not args.execute:
        print("\nDRY RUN -- nothing trashed. Re-run with --execute to move these to Trash.")
        return

    if not rows:
        print("\nNothing to trash.")
        return

    print("\n=== Trashing ===")
    errors = 0
    for f, size, kind, parent in rows:
        try:
            res = d.trash(f["id"])
            print(f"  trashed: {res.get('name')}  ({_human(size)})")
        except Exception as e:
            errors += 1
            print(f"  ERROR trashing {f.get('name')}: {e}", file=sys.stderr)
    print(f"\nDone. {len(rows) - errors} trashed, {errors} errors.")
    print("Space is reclaimed when Drive trash is emptied (or auto ~30 days).")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()

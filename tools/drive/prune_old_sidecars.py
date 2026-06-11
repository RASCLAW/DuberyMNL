"""
Prune stale sidecar copies left behind after a --split-sidecars migration.

When sync_folder.py --split-sidecars first runs on a folder that was previously
backed up the old way, the sidecar JSONs get a NEW copy in <root>/_meta/ but the
OLD copies still sit next to their images (sync only adds, never deletes). This
tool removes those redundant old copies -- but ONLY after confirming each one's
encoded twin actually exists in _meta/, so it can never delete a sole copy.

SAFE BY DEFAULT:
  - Dry-run unless --execute is passed.
  - Trashes (recoverable from Drive trash ~30 days), not permanent-delete.
    Pass --purge for permanent deletion.
  - Any old sidecar whose _meta/ twin is MISSING is skipped + reported, never trashed.

Images and any file already inside _meta/ are never touched.

Includes the same IPv4 monkey-patch as sync_folder.py (RA's home ISP has no IPv6).
See feedback_google_api_client_broken.md.

Usage:
    python tools/drive/prune_old_sidecars.py --remote "DuberyMNL/backup/contents/ready"            # dry-run
    python tools/drive/prune_old_sidecars.py --remote "DuberyMNL/backup/contents/ready" --execute   # trash
    python tools/drive/prune_old_sidecars.py --remote "..." --execute --purge                       # permanent
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
import threading
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
FOLDER_MIME = "application/vnd.google-apps.folder"
TIMEOUT = 60


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def _encode_sidecar_name(rel: str) -> str:
    """Mirror sync_folder._encode_sidecar_name: 'a/b/c.json' -> 'a__b__c.json'."""
    return rel.replace("\\", "/").replace("/", "__")


def get_credentials() -> Credentials:
    return _auth_get_credentials()


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
            f"mimeType='{FOLDER_MIME}' and "
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

    def list_children(self, parent_id: str) -> list[dict]:
        """All non-trashed children (id, name, mimeType) directly under parent_id."""
        self._ensure_token()
        out: list[dict] = []
        page_token = None
        while True:
            params = {
                "q": f"'{parent_id}' in parents and trashed=false",
                "fields": "nextPageToken,files(id,name,mimeType)",
                "pageSize": 1000,
            }
            if page_token:
                params["pageToken"] = page_token
            r = self.session.get(f"{API_BASE}/files", params=params, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            out.extend(data.get("files", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return out

    def trash(self, file_id: str):
        self._ensure_token()
        r = self.session.patch(
            f"{API_BASE}/files/{file_id}",
            json={"trashed": True},
            timeout=TIMEOUT,
        )
        r.raise_for_status()

    def purge(self, file_id: str):
        self._ensure_token()
        r = self.session.delete(f"{API_BASE}/files/{file_id}", timeout=TIMEOUT)
        if r.status_code not in (200, 204):
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


def collect_old_sidecars(client: DriveClient, root_id: str, sidecar_subdir: str,
                         exts: set[str]) -> list[tuple[str, str]]:
    """Walk root recursively, skipping the top-level <sidecar_subdir> subtree.

    Return [(file_id, rel_path)] for every file whose extension is in exts and
    that lives OUTSIDE the sidecar folder -- i.e. the stale mirrored copies.
    """
    out: list[tuple[str, str]] = []
    # stack of (folder_id, prefix_rel_path, is_root)
    stack = [(root_id, "", True)]
    while stack:
        cur_id, prefix, is_root = stack.pop()
        for f in client.list_children(cur_id):
            name = f["name"]
            rel = f"{prefix}/{name}" if prefix else name
            if f["mimeType"] == FOLDER_MIME:
                if is_root and name == sidecar_subdir:
                    continue  # the keepers live here -- never descend for deletion
                stack.append((f["id"], rel, False))
            elif Path(name).suffix.lower() in exts:
                out.append((f["id"], rel))
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Trash stale sidecar copies left outside _meta/ after a --split-sidecars migration")
    parser.add_argument("--remote", required=True,
                        help='Drive backup root e.g. "DuberyMNL/backup/contents/ready"')
    parser.add_argument("--sidecar-subdir", default="_meta",
                        help="Subfolder holding the kept (encoded) sidecars (default: _meta)")
    parser.add_argument("--sidecar-ext", default=".json",
                        help="Comma-separated extensions to treat as sidecars (default: .json)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually remove files. Without this, dry-run only.")
    parser.add_argument("--purge", action="store_true",
                        help="Permanently delete instead of trashing (default: trash, recoverable ~30 days)")
    parser.add_argument("--workers", type=int, default=4,
                        help="Parallel workers for removal (default 4)")
    args = parser.parse_args()

    exts = {
        e if e.startswith(".") else f".{e}"
        for e in (x.strip().lower() for x in args.sidecar_ext.split(",")) if e
    }

    creds = get_credentials()
    client = DriveClient(creds)

    print(f"Resolving: {args.remote}")
    root_id = resolve_path(client, args.remote)

    meta_id = client.find_folder(args.sidecar_subdir, root_id)
    if not meta_id:
        print(f"Error: no '{args.sidecar_subdir}/' folder under {args.remote}.", file=sys.stderr)
        print("       Run sync_folder.py --split-sidecars first; nothing to prune.", file=sys.stderr)
        sys.exit(1)
    twins = {f["name"] for f in client.list_children(meta_id) if f["mimeType"] != FOLDER_MIME}
    print(f"  {args.sidecar_subdir}/ holds {len(twins)} encoded sidecars (the keepers)")

    print("Walking backup tree for stale sidecars outside _meta/ ...")
    candidates = collect_old_sidecars(client, root_id, args.sidecar_subdir, exts)
    print(f"  found {len(candidates)} sidecar files outside {args.sidecar_subdir}/")

    safe: list[tuple[str, str]] = []   # (file_id, rel) -- twin confirmed in _meta/
    unsafe: list[str] = []             # rel paths whose twin is missing -> keep
    for file_id, rel in candidates:
        if _encode_sidecar_name(rel) in twins:
            safe.append((file_id, rel))
        else:
            unsafe.append(rel)

    print()
    print(f"Safe to remove (twin verified in {args.sidecar_subdir}/): {len(safe)}")
    print(f"SKIPPED -- twin MISSING, kept for safety:               {len(unsafe)}")
    for rel in unsafe:
        print(f"  [keep] {rel}  (no {_encode_sidecar_name(rel)} in {args.sidecar_subdir}/)", file=sys.stderr)

    if not args.execute:
        print()
        print("DRY RUN -- nothing removed. Re-run with --execute to remove the safe set.")
        for _fid, rel in safe[:50]:
            print(f"  [dry-run] would {'purge' if args.purge else 'trash'}: {rel}")
        if len(safe) > 50:
            print(f"  ... and {len(safe) - 50} more")
        return

    if not safe:
        print("Nothing to remove.")
        return

    action = "purge" if args.purge else "trash"
    print()
    print(f"{action.upper()}ING {len(safe)} stale sidecars with {args.workers} workers...")
    stats = {"ok": 0, "err": 0}
    stats_lock = threading.Lock()

    def remove_one(item: tuple[str, str]):
        file_id, rel = item
        try:
            if args.purge:
                client.purge(file_id)
            else:
                client.trash(file_id)
            return ("ok", rel, None)
        except Exception as e:
            return ("err", rel, f"{type(e).__name__}: {e}")

    done = 0
    total = len(safe)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(remove_one, item) for item in safe]
        for fut in as_completed(futures):
            status, rel, err = fut.result()
            done += 1
            with stats_lock:
                stats["ok" if status == "ok" else "err"] += 1
            if status == "err":
                print(f"  [{done}/{total}] ERROR {rel} -- {err}", file=sys.stderr)
                if stats["err"] >= 5:
                    for f in futures:
                        f.cancel()
                    print("Too many errors, aborting", file=sys.stderr)
                    break

    print()
    print("=== SUMMARY ===")
    print(f"Removed ({action}): {stats['ok']}")
    print(f"Errors:            {stats['err']}")
    print(f"Kept (twin missing): {len(unsafe)}")
    if stats["err"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

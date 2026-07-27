"""
Create a YouTube playlist on RA's account (and optionally seed it with videos).

Uses the shared Google OAuth token (token.json) which already carries the
`youtube` write scope -- no separate auth needed.

Usage:
    # Empty private playlist
    python tools/youtube/create_playlist.py "My Playlist"

    # With description + privacy + seed videos (URLs or bare IDs, space-separated)
    python tools/youtube/create_playlist.py "Landcover Training" \
        --desc "Annotation reference clips" \
        --privacy unlisted \
        --add https://youtu.be/dQw4w9WgXcQ VIDEO_ID2

    # Seed from a file (one URL/ID per line, blank lines + # comments ignored)
    python tools/youtube/create_playlist.py "Batch" --add-file videos.txt

    # See what it WOULD do, no account write, no quota spend:
    python tools/youtube/create_playlist.py "Test" --add URL --dry-run

Privacy: private (default) | unlisted | public
Quota: playlists.insert = 50 units, each video add = 50 units. Budget 10k/day.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth import service  # noqa: E402

# Matches a YouTube URL (watch?v=, youtu.be/, /shorts/, /embed/) or a bare 11-char ID.
_ID_RE = re.compile(
    r"(?:v=|/shorts/|/embed/|youtu\.be/)([A-Za-z0-9_-]{11})|^([A-Za-z0-9_-]{11})$"
)


def parse_video_id(token: str) -> str:
    """Extract an 11-char video ID from a URL or bare ID. Raises on garbage."""
    token = token.strip()
    m = _ID_RE.search(token)
    if not m:
        raise ValueError(f"Could not parse a video ID from: {token!r}")
    return m.group(1) or m.group(2)


def load_seed_ids(add, add_file):
    """Merge --add args and --add-file lines into a de-duped, order-preserved ID list."""
    raw = list(add or [])
    if add_file:
        for line in Path(add_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                raw.append(line)
    ids, seen = [], set()
    for tok in raw:
        vid = parse_video_id(tok)
        if vid not in seen:
            seen.add(vid)
            ids.append(vid)
    return ids


def main():
    ap = argparse.ArgumentParser(description="Create a YouTube playlist.")
    ap.add_argument("title", help="Playlist title")
    ap.add_argument("--desc", default="", help="Playlist description")
    ap.add_argument(
        "--privacy",
        default="private",
        choices=["private", "unlisted", "public"],
        help="Playlist visibility (default: private)",
    )
    ap.add_argument("--add", nargs="+", default=[], help="Video URLs or IDs to seed")
    ap.add_argument("--add-file", help="File with one video URL/ID per line")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the intended actions without writing or spending quota",
    )
    args = ap.parse_args()

    try:
        seed_ids = load_seed_ids(args.add, args.add_file)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Playlist : {args.title}")
    print(f"Privacy  : {args.privacy}")
    if args.desc:
        print(f"Desc     : {args.desc}")
    print(f"Videos   : {len(seed_ids)}" + (f" -> {seed_ids}" if seed_ids else ""))

    if args.dry_run:
        quota = 50 + 50 * len(seed_ids)
        print(f"\n[DRY-RUN] Would create the playlist + add {len(seed_ids)} "
              f"video(s). Est. quota: {quota} units. No account write made.")
        return

    yt = service("youtube", "v3")

    resp = yt.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {"title": args.title, "description": args.desc},
            "status": {"privacyStatus": args.privacy},
        },
    ).execute()
    playlist_id = resp["id"]
    print(f"\nCreated: https://www.youtube.com/playlist?list={playlist_id}")

    added, failed = 0, []
    for vid in seed_ids:
        try:
            yt.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": vid},
                    }
                },
            ).execute()
            added += 1
            print(f"  + {vid}")
        except Exception as e:  # noqa: BLE001 - report per-video, keep going
            failed.append(vid)
            print(f"  ! {vid} FAILED: {e}", file=sys.stderr)

    print(f"\nDone. {added} added, {len(failed)} failed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

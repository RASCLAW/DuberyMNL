"""
Insert or update a single moment in the content_calendar Sheet, keyed by `id`.

Append a new moment (or update if the id already exists):
    python tools/moments/upsert_moment.py --data '{"id":"2026-12-25-christmas","title":"Christmas gifting","type":"holiday","window_start":"2026-11-15","window_end":"2026-12-25","relevance":"9","angle":"Giftable shades","format":"ugc-story","source":"manual","status":"suggested"}'

Update just the status of an existing moment:
    python tools/moments/upsert_moment.py --data '{"id":"2026-12-25-christmas","status":"approved"}'

Preview without writing:
    python tools/moments/upsert_moment.py --data '{...}' --dry-run

Output: JSON result to stdout.
"""

import argparse
import json
import sys

from moment_store import upsert_moment


def main():
    parser = argparse.ArgumentParser(description="Upsert a moment into the content calendar")
    parser.add_argument("--data", required=True, help="JSON object; must include 'id'")
    parser.add_argument("--dry-run", action="store_true", help="Preview, do not write")
    args = parser.parse_args()

    try:
        data = json.loads(args.data)
    except json.JSONDecodeError as e:
        print(f"Error: --data is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = upsert_moment(data, dry_run=args.dry_run)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

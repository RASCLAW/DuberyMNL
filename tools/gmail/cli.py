"""
Gmail CLI -- read, search, send, label, draft, trash.

Reuses the shared OAuth token via tools/auth.py (scope: gmail.modify, which
covers read/search/label/draft/trash/send; permanent-delete is NOT included).

Usage (direct, or via `gog gmail <cmd>`):
    python tools/gmail/cli.py list --max 5
    python tools/gmail/cli.py list --query "is:unread from:meta"
    python tools/gmail/cli.py read <message_id>
    python tools/gmail/cli.py send --to a@b.com --subject "Hi" --body "..." [--dry-run]
    python tools/gmail/cli.py label <message_id> --add Work --remove UNREAD [--dry-run]
    python tools/gmail/cli.py draft --to a@b.com --subject "Hi" --body "..." [--dry-run]
    python tools/gmail/cli.py trash <message_id> [--dry-run]

All mutating commands support --dry-run (prints intended action, no API write).
Output: JSON to stdout. Errors to stderr, exit 1.
"""

import argparse
import base64
import json
import sys
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth import service  # noqa: E402


def _headers(payload):
    return {h["name"]: h["value"] for h in payload.get("headers", [])}


def cmd_list(svc, args):
    resp = (
        svc.users()
        .messages()
        .list(userId="me", q=args.query or "", maxResults=args.max)
        .execute()
    )
    out = []
    for m in resp.get("messages", []):
        full = (
            svc.users()
            .messages()
            .get(
                userId="me",
                id=m["id"],
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"],
            )
            .execute()
        )
        h = _headers(full.get("payload", {}))
        out.append(
            {
                "id": m["id"],
                "from": h.get("From", ""),
                "subject": h.get("Subject", ""),
                "date": h.get("Date", ""),
                "snippet": full.get("snippet", ""),
            }
        )
    return out


def _decode_body(payload):
    """Walk MIME parts, prefer text/plain; fall back to first part with data."""

    def walk(p, want_plain):
        if p.get("body", {}).get("data"):
            if not want_plain or p.get("mimeType") == "text/plain":
                raw = base64.urlsafe_b64decode(p["body"]["data"] + "===")
                return raw.decode("utf-8", "replace")
        for sub in p.get("parts", []) or []:
            r = walk(sub, want_plain)
            if r:
                return r
        return None

    return walk(payload, True) or walk(payload, False) or ""


def cmd_read(svc, args):
    full = svc.users().messages().get(userId="me", id=args.message_id, format="full").execute()
    h = _headers(full.get("payload", {}))
    return {
        "id": args.message_id,
        "from": h.get("From", ""),
        "to": h.get("To", ""),
        "subject": h.get("Subject", ""),
        "date": h.get("Date", ""),
        "body": _decode_body(full.get("payload", {})),
    }


def _mime_raw(to, subject, body):
    msg = MIMEText(body, _charset="utf-8")
    msg["to"] = to
    msg["subject"] = subject
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def cmd_send(svc, args):
    if args.dry_run:
        return {
            "dry_run": True,
            "action": "send",
            "to": args.to,
            "subject": args.subject,
            "body_preview": args.body[:200],
        }
    sent = svc.users().messages().send(userId="me", body={"raw": _mime_raw(args.to, args.subject, args.body)}).execute()
    return {"sent": True, "id": sent.get("id")}


def _resolve_label_ids(svc, names):
    if not names:
        return []
    labels = svc.users().labels().list(userId="me").execute().get("labels", [])
    by_name = {label["name"].lower(): label["id"] for label in labels}
    ids_set = {label["id"] for label in labels}
    out = []
    for n in names:
        if n.lower() in by_name:
            out.append(by_name[n.lower()])
        elif n.upper() in ids_set:  # system labels e.g. INBOX, UNREAD, STARRED
            out.append(n.upper())
        else:
            out.append(n)  # pass through; API will error if invalid
    return out


def cmd_label(svc, args):
    add_ids = _resolve_label_ids(svc, args.add)
    rm_ids = _resolve_label_ids(svc, args.remove)
    if args.dry_run:
        return {
            "dry_run": True,
            "action": "label",
            "message_id": args.message_id,
            "add": add_ids,
            "remove": rm_ids,
        }
    res = (
        svc.users()
        .messages()
        .modify(
            userId="me",
            id=args.message_id,
            body={"addLabelIds": add_ids, "removeLabelIds": rm_ids},
        )
        .execute()
    )
    return {"modified": True, "id": res.get("id"), "labelIds": res.get("labelIds", [])}


def cmd_draft(svc, args):
    if args.dry_run:
        return {"dry_run": True, "action": "draft", "to": args.to, "subject": args.subject}
    d = (
        svc.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": _mime_raw(args.to, args.subject, args.body)}})
        .execute()
    )
    return {"draft_created": True, "id": d.get("id")}


def cmd_trash(svc, args):
    if args.dry_run:
        return {"dry_run": True, "action": "trash", "message_id": args.message_id}
    t = svc.users().messages().trash(userId="me", id=args.message_id).execute()
    return {"trashed": True, "id": t.get("id")}


def _all_ids(svc, query, cap):
    """Paginate every message id matching query, up to cap."""
    ids, tok = [], None
    while True:
        r = svc.users().messages().list(userId="me", q=query, maxResults=500, pageToken=tok).execute()
        ids += [m["id"] for m in r.get("messages", [])]
        tok = r.get("nextPageToken")
        if not tok or len(ids) >= cap:
            break
    return ids[:cap]


def cmd_sort(svc, args):
    """Bulk add/remove labels on every message matching --query, via batchModify (<=1000/call)."""
    if not args.add and not args.remove:
        raise ValueError("sort needs at least one --add or --remove")
    ids = _all_ids(svc, args.query, args.cap)
    add_ids = _resolve_label_ids(svc, args.add)
    rm_ids = _resolve_label_ids(svc, args.remove)
    if args.dry_run:
        sample = []
        for mid in ids[:8]:
            h = _headers(
                svc.users().messages()
                .get(userId="me", id=mid, format="metadata", metadataHeaders=["Subject", "From"])
                .execute().get("payload", {})
            )
            sample.append({"from": h.get("From", ""), "subject": h.get("Subject", "")})
        return {"dry_run": True, "query": args.query, "match_count": len(ids),
                "capped": len(ids) >= args.cap, "add": add_ids, "remove": rm_ids, "sample": sample}
    modified = 0
    for i in range(0, len(ids), 1000):
        chunk = ids[i:i + 1000]
        svc.users().messages().batchModify(
            userId="me", body={"ids": chunk, "addLabelIds": add_ids, "removeLabelIds": rm_ids}
        ).execute()
        modified += len(chunk)
    return {"sorted": True, "query": args.query, "modified": modified, "add": add_ids, "remove": rm_ids}


def build_parser():
    p = argparse.ArgumentParser(prog="gog gmail", description="Gmail CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("list", help="list/search messages")
    s.add_argument("--query", help='Gmail search, e.g. "is:unread from:meta"')
    s.add_argument("--max", type=int, default=10)
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("read", help="read one message")
    s.add_argument("message_id")
    s.set_defaults(func=cmd_read)

    s = sub.add_parser("send", help="send a message")
    s.add_argument("--to", required=True)
    s.add_argument("--subject", required=True)
    s.add_argument("--body", required=True)
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_send)

    s = sub.add_parser("label", help="add/remove labels on a message")
    s.add_argument("message_id")
    s.add_argument("--add", action="append", default=[], help="label name or system id; repeatable")
    s.add_argument("--remove", action="append", default=[], help="label name or system id; repeatable")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_label)

    s = sub.add_parser("draft", help="create a draft")
    s.add_argument("--to", required=True)
    s.add_argument("--subject", required=True)
    s.add_argument("--body", required=True)
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_draft)

    s = sub.add_parser("sort", help="bulk label/archive all messages matching a query (batchModify)")
    s.add_argument("--query", required=True, help="Gmail search, e.g. 'in:inbox from:linkedin.com'")
    s.add_argument("--add", action="append", default=[], help="label to add; repeatable")
    s.add_argument("--remove", action="append", default=[], help="label to remove (INBOX = archive); repeatable")
    s.add_argument("--cap", type=int, default=5000, help="safety cap on messages touched per run (default 5000)")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_sort)

    s = sub.add_parser("trash", help="move a message to trash")
    s.add_argument("message_id")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_trash)

    return p


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = build_parser().parse_args(argv)
    try:
        result = args.func(service("gmail", "v1"), args)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

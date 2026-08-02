"""
Sync BPI transaction notifications from Gmail into the finance ledger.

BPI emails a confirmation for every deposit-account movement within seconds of
it happening, which makes Gmail a near-real-time transaction feed -- no bank
scraping, no stored credentials. This pulls those emails, parses them into
structured transactions, and merges them into EA-brain/finance/.

Covers (both directions):
  inflow   Incoming InstaPay          "You have an incoming interbank funds transfer"
  outflow  Outgoing InstaPay          "Interbank Funds Transfer Confirmation"
  outflow  Pay via QR                 "Pay <merchant> via QR"
  outflow  Internal transfer          "Transfer Money" / "Funds Transfer Confirmation"
  outflow  Prepaid load               "Load Prepaid Phone Confirmation"

Does NOT cover (structural gaps -- see the README):
  - Credit card purchases      -> monthly eSOA only
  - Payroll / salary credits   -> posted internally, BPI sends no email
  - Cash deposits, ATM, OTC    -> no email
Anything not captured here shows up only on the monthly deposit eStatement.

Merges on Gmail message id, so re-running is safe and idempotent.

Usage:
    python tools/finance/sync_bpi_email.py                  # last 90 days
    python tools/finance/sync_bpi_email.py --days 365
    python tools/finance/sync_bpi_email.py --summary        # monthly in/out rollup
    python tools/finance/sync_bpi_email.py --dry-run        # parse + print, no write
"""

import argparse
import base64
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_DIR / "tools"))

from auth import service  # noqa: E402

OUT_DIR = Path.home() / "projects" / "EA-brain" / "finance"
OUT_FILE = OUT_DIR / "bpi-transactions.json"

QUERY = "from:bpi.com.ph"

# Moving money between RA's own accounts is not spending, but BPI emails it the
# same way it emails a real payment. Without this, shuffling PHP 40k from Floater
# to Savings inflates "outflow" by PHP 40k and the burn number becomes fiction.
# Match is a substring test against the counterparty field. Add to this list as
# accounts are confirmed -- an unlisted own-account silently double-counts.
OWN_ACCOUNTS = [
    "(PAYROLL ACCOUNT)",
    "(Floater)",
    "(SAVINGS)",
    "01XXXXX48927",  # GoTyme -- appears on both sides of the ledger
]

# Marketing blasts share the sender domain -- a mail only counts as a
# transaction if it carries a confirmation/reference number AND an amount.
DATE_RE = re.compile(r"([A-Za-z]+, [A-Za-z]+ \d{1,2} \d{4})(?:; (\d{1,2}:\d{2}:\d{2} [AP]M))?")
AMOUNT_RE = re.compile(r"PHP\s*([\d,]+\.\d{2})")


def flatten(payload, acc):
    """Collect every text/html part of a Gmail message."""
    data = payload.get("body", {}).get("data")
    if data:
        acc.append(base64.urlsafe_b64decode(data).decode("utf-8", "ignore"))
    for part in payload.get("parts") or []:
        flatten(part, acc)


def tokenize(raw_html: str) -> list[str]:
    """BPI lays these emails out as label/value table cells. Strip tags and
    keep the cell boundaries so a label can be paired with the value after it."""
    text = re.sub(r"<[^>]+>", "\x00", raw_html)
    text = html.unescape(text)
    return [t.strip() for t in text.split("\x00") if t.strip()]


def field(tokens: list[str], *labels: str) -> str:
    """Value of the first matching label, taken as the next non-empty cell."""
    for label in labels:
        for i, tok in enumerate(tokens):
            if tok.rstrip(":").lower() == label.lower() and i + 1 < len(tokens):
                return tokens[i + 1]
    return ""


def money(value: str) -> float | None:
    m = AMOUNT_RE.search(value) or re.search(r"([\d,]+\.\d{2})", value)
    return float(m.group(1).replace(",", "")) if m else None


def parse_date(value: str) -> str:
    m = DATE_RE.search(value)
    if not m:
        return ""
    try:
        return datetime.strptime(m.group(1), "%A, %b %d %Y").strftime("%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(m.group(1), "%A, %B %d %Y").strftime("%Y-%m-%d")
        except ValueError:
            return ""


def classify(subject: str, tokens: list[str]) -> tuple[str, str]:
    """(direction, kind). Direction cannot be read from the subject alone --
    at least one incoming transfer arrives titled 'Funds transfer confirmation',
    identical to an outgoing one. The body sentence is the reliable signal."""
    blob = " ".join(tokens[:40]).lower()
    if "you have an incoming" in blob:
        return "in", "instapay_in"
    if "via qr" in subject.lower():
        return "out", "qr_payment"
    if "load prepaid" in subject.lower() or "Load From" in tokens:
        return "out", "prepaid_load"
    if "interbank" in subject.lower() or "instapay" in blob:
        return "out", "instapay_out"
    return "out", "transfer"


def parse(msg: dict) -> dict | None:
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    subject = headers.get("Subject", "")

    parts: list[str] = []
    flatten(msg["payload"], parts)
    tokens = tokenize(" ".join(parts))

    ref = field(tokens, "Confirmation Number", "Reference Number")
    if not ref:
        return None  # marketing mail

    amount = money(field(tokens, "Total Amount", "Transfer Amount", "Amount"))
    if amount is None:
        return None

    direction, kind = classify(subject, tokens)
    payee = field(tokens, "Pay To", "Mobile Number")
    if not payee and kind == "qr_payment":
        m = re.match(r"Pay (.+?) via QR", subject)
        payee = m.group(1) if m else ""
    if not payee:
        payee = field(tokens, "Transfer To")

    if any(hint.lower() in payee.lower() for hint in OWN_ACCOUNTS if payee):
        direction = "internal"

    return {
        "id": msg["id"],
        "date": parse_date(field(tokens, "Transaction Date and Time", "Date and Time")),
        "direction": direction,
        "kind": kind,
        "amount": amount,
        "fee": money(field(tokens, "Service Fee")) or 0.0,
        "counterparty": payee,
        "counterparty_bank": field(tokens, "Bank Name"),
        "account": field(tokens, "Transfer From", "Pay From", "Load From"),
        "reference": ref,
        "subject": subject,
    }


def fetch(days: int) -> list[dict]:
    svc = service("gmail", "v1")
    out, token = [], None
    while True:
        res = (
            svc.users()
            .messages()
            .list(userId="me", q=f"newer_than:{days}d {QUERY}", maxResults=200, pageToken=token)
            .execute()
        )
        for stub in res.get("messages", []):
            msg = svc.users().messages().get(userId="me", id=stub["id"]).execute()
            txn = parse(msg)
            if txn:
                out.append(txn)
        token = res.get("nextPageToken")
        if not token:
            break
    return out


def merge(new: list[dict]) -> tuple[list[dict], int]:
    existing = []
    if OUT_FILE.exists():
        existing = json.loads(OUT_FILE.read_text(encoding="utf-8")).get("transactions", [])
    by_id = {t["id"]: t for t in existing}
    added = sum(1 for t in new if t["id"] not in by_id)
    by_id.update({t["id"]: t for t in new})
    return sorted(by_id.values(), key=lambda t: (t["date"], t["amount"]), reverse=True), added


def summarize(txns: list[dict]) -> None:
    months: dict[str, dict] = {}
    for t in txns:
        if not t["date"]:
            continue
        m = months.setdefault(t["date"][:7], {"in": 0.0, "out": 0.0, "internal": 0.0, "n": 0})
        m[t["direction"]] += t["amount"] + t["fee"]
        m["n"] += 1

    print("\nReal money in/out. 'shuffle' = transfers between RA's own accounts, excluded from both.")
    print(f"\n{'month':9} {'in':>13} {'out':>13} {'net':>13} {'shuffle':>12}  txns")
    print("-" * 72)
    for month in sorted(months, reverse=True):
        m = months[month]
        print(
            f"{month:9} {m['in']:13,.2f} {m['out']:13,.2f} "
            f"{m['in'] - m['out']:13,.2f} {m['internal']:12,.2f}  {m['n']:4}"
        )

    unlisted = {
        t["counterparty"]
        for t in txns
        if t["direction"] == "out" and t["counterparty"]
    } & {t["counterparty"] for t in txns if t["direction"] == "in" and t["counterparty"]}
    if unlisted:
        print("\nSeen on BOTH sides -- likely RA's own accounts, add to OWN_ACCOUNTS if so:")
        for acct in sorted(unlisted):
            print(f"  {acct}")

    print("\nOutflow by kind:")
    kinds: dict[str, list[float]] = {}
    for t in txns:
        if t["direction"] == "out":
            kinds.setdefault(t["kind"], []).append(t["amount"] + t["fee"])
    for kind, amounts in sorted(kinds.items(), key=lambda kv: -sum(kv[1])):
        print(f"  {kind:15} {sum(amounts):12,.2f}  ({len(amounts)} txns)")

    print("\nTop counterparties (outflow):")
    payees: dict[str, list[float]] = {}
    for t in txns:
        if t["direction"] == "out" and t["counterparty"]:
            payees.setdefault(t["counterparty"], []).append(t["amount"])
    top = sorted(payees.items(), key=lambda kv: -sum(kv[1]))[:15]
    for payee, amounts in top:
        print(f"  {payee[:34]:34} {sum(amounts):11,.2f}  ({len(amounts)}x)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Sync BPI transaction emails into the finance ledger")
    ap.add_argument("--days", type=int, default=90, help="lookback window (default 90)")
    ap.add_argument("--summary", action="store_true", help="print monthly rollup after syncing")
    ap.add_argument("--dry-run", action="store_true", help="parse and report, write nothing")
    args = ap.parse_args()

    print(f"Fetching BPI emails from the last {args.days} days...")
    parsed = fetch(args.days)
    print(f"Parsed {len(parsed)} transactions.")

    txns, added = merge(parsed)

    if args.dry_run:
        print("[dry-run] nothing written")
    else:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        OUT_FILE.write_text(
            json.dumps(
                {
                    "source": "BPI email notifications via Gmail",
                    "synced_at": datetime.now().isoformat(timespec="seconds"),
                    "covers": "deposit account only -- excludes credit card purchases, payroll credits, cash/ATM deposits",
                    "transactions": txns,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"{added} new, {len(txns)} total -> {OUT_FILE}")

    if args.summary:
        summarize(txns)


if __name__ == "__main__":
    main()

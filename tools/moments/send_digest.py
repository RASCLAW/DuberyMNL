"""
Send the daily "Content Radar" Telegram digest: which calendar moments are live
now or opening soon, so RA can approve angles before the window passes.

    python tools/moments/send_digest.py             # send to Telegram
    python tools/moments/send_digest.py --dry-run   # print only, no send
    python tools/moments/send_digest.py --soon-days 60

Reuses the project TG channel (TELEGRAM_BOT_TOKEN + TG_CHAT_ID), same as
meta_ads/daily_digest.py. Called by the /moment-research skill at the end of a run.
"""

import argparse
import os
import sys
from datetime import date, datetime, timedelta

import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from moment_store import read_moments  # noqa: E402

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")

TYPE_EMOJI = {"holiday": "🎉", "event": "🏀", "trend": "🔥", "weather": "🌦️"}


def _d(s):
    try:
        return date.fromisoformat((s or "").strip())
    except ValueError:
        return None


def build_digest(soon_days: int) -> str:
    today = date.today()
    horizon = today + timedelta(days=soon_days)
    rows = [r for r in read_moments() if (r.get("status") or "") not in ("dismissed", "posted")]

    live, soon = [], []
    for r in rows:
        start, end = _d(r.get("window_start")), _d(r.get("window_end"))
        if not start:
            continue
        if (end or start) >= today and start <= today:
            live.append(r)
        elif today < start <= horizon:
            soon.append(r)

    def relkey(r):
        try:
            return -int(r.get("relevance") or 0)
        except ValueError:
            return 0

    live.sort(key=relkey)
    soon.sort(key=lambda r: (_d(r.get("window_start")) or horizon))

    def fmt(r, with_lead=False):
        em = TYPE_EMOJI.get((r.get("type") or "").lower(), "•")
        rel = r.get("relevance", "")
        title = r.get("title", "")
        angle = (r.get("angle", "") or "").strip()
        lead = ""
        if with_lead:
            start = _d(r.get("window_start"))
            if start:
                lead = f"  _(in {(start - today).days}d)_"
        line = f"{em} *{title}*  `rel {rel}`{lead}\n   {angle}"
        if (r.get("status") or "") == "approved":
            line = "✅ " + line
        return line

    lines = [f"🗓️ *DuberyMNL Content Radar* — {today.isoformat()}", ""]

    if live:
        lines.append(f"*LIVE NOW ({len(live)})* — windows open, shoot/post these:")
        lines += [fmt(r) for r in live]
        lines.append("")
    if soon:
        lines.append(f"*OPENING SOON (next {soon_days}d, {len(soon)})*:")
        lines += [fmt(r, with_lead=True) for r in soon]
        lines.append("")

    if not live and not soon:
        lines.append("_No moments live or opening soon. Quiet window._")
        lines.append("")

    pending = sum(1 for r in (live + soon) if (r.get("status") or "") == "suggested")
    if pending:
        lines.append(f"⏳ {pending} suggested — approve angles in the Command Center Calendar tab.")

    return "\n".join(lines)


def send_telegram(text: str) -> bool:
    if not TG_TOKEN or not TG_CHAT_ID:
        print("TG not configured (TELEGRAM_BOT_TOKEN / TG_CHAT_ID) — skipping send", file=sys.stderr)
        return False
    r = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown",
              "disable_web_page_preview": True},
        timeout=15,
    )
    if r.status_code == 200:
        print(f"TG sent OK ({len(text)} chars)")
        return True
    print(f"TG send failed {r.status_code}: {r.text[:200]}", file=sys.stderr)
    return False


def main():
    ap = argparse.ArgumentParser(description="Send the Content Radar TG digest")
    ap.add_argument("--dry-run", action="store_true", help="print only, no TG send")
    ap.add_argument("--soon-days", type=int, default=45, help="how far ahead 'opening soon' looks")
    args = ap.parse_args()

    text = build_digest(args.soon_days)
    print(text)
    print("-" * 40)
    if args.dry_run:
        print("(dry-run — not sent)")
    else:
        send_telegram(text)


if __name__ == "__main__":
    main()

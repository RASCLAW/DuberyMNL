"""
Daily ad-monitoring digest.

Runs daily at 9 AM PHT via Windows Task Scheduler. Pulls:
  - Yesterday's Meta ad insights (per-ad)
  - 7-day rolling Meta insights (per-ad, for ROAS smoothing)
  - Yesterday's Pixel events (for Pixel-attributed ROAS)
  - Yesterday's orders from the DuberyMNL Orders sheet (cash-basis ROAS)

Composes a markdown digest and sends it to RA's TG DM
(the same channel used by chatbot order_intent pings).

Archives every digest to .tmp/daily_digest/YYYY-MM-DD.md for trend lookback.

Run modes:
  python daily_digest.py            # send to TG (production)
  python daily_digest.py --dry      # print to console only, no TG send
  python daily_digest.py --date 2026-05-26   # backdate (PHT yyyy-mm-dd)
"""
import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env")

META_TOKEN = os.environ["META_ADS_ACCESS_TOKEN"]
META_ACCT = os.environ["META_AD_ACCOUNT_ID"].replace("act_", "")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")
PIXEL_ID = os.environ.get("META_PIXEL_ID", "1513349880261420")
CAMPAIGN_ID = "6968215093276"  # DuberyMNL Traffic

PHT = timezone(timedelta(hours=8))
API = "https://graph.facebook.com/v23.0"
ARCHIVE_DIR = REPO_ROOT / ".tmp" / "daily_digest"
LOG_PATH = REPO_ROOT / ".tmp" / "daily_digest.log"


def log(msg):
    ts = datetime.now(PHT).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.open("a", encoding="utf-8").write(line)
    print(line, end="")


def meta_get(endpoint, **params):
    params["access_token"] = META_TOKEN
    r = requests.get(f"{API}/{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def pull_ad_insights(date_from, date_to):
    """Per-ad insights, summed within the date range."""
    data = []
    after = None
    while True:
        params = {
            "level": "ad",
            "time_range": json.dumps({"since": date_from, "until": date_to}),
            "fields": "ad_id,ad_name,spend,impressions,clicks,ctr,actions",
            "limit": 100,
        }
        if after:
            params["after"] = after
        r = meta_get(f"act_{META_ACCT}/insights", **params)
        data.extend(r.get("data", []))
        nxt = r.get("paging", {}).get("cursors", {}).get("after")
        if not nxt or nxt == after:
            break
        after = nxt
    return data


def lpv_from_actions(row):
    for a in row.get("actions", []) or []:
        if a.get("action_type") == "landing_page_view":
            return int(a.get("value", 0))
    return 0


def pull_pixel_events(date_from, date_to):
    """Aggregate pixel events for the window."""
    try:
        r = meta_get(f"{PIXEL_ID}/stats",
                     start_time=date_from, end_time=date_to,
                     aggregation="event")
        out = {}
        for row in r.get("data", []):
            for e in row.get("data", []):
                k = e.get("event")
                if k:
                    out[k] = out.get(k, 0) + int(e.get("count", 0))
        return out
    except Exception as e:
        log(f"pixel pull failed: {e}")
        return {}


def pull_orders_for_date(date_str):
    """Hit local CC if running; otherwise return empty (degrade gracefully)."""
    try:
        r = requests.get("http://127.0.0.1:8090/api/crm/orders", params={"fresh": "1"}, timeout=10)
        if r.status_code != 200:
            return []
        return [o for o in r.json() if o.get("order_date") == date_str]
    except Exception as e:
        log(f"orders pull failed: {e}")
        return []


def pull_orders_window(date_from, date_to):
    try:
        r = requests.get("http://127.0.0.1:8090/api/crm/orders", params={"fresh": "1"}, timeout=10)
        if r.status_code != 200:
            return []
        return [o for o in r.json() if date_from <= o.get("order_date", "") <= date_to]
    except Exception:
        return []


def revenue_excl_cancelled(orders):
    return sum(
        o.get("total", 0) or 0
        for o in orders
        if (o.get("status") or "").strip().upper() != "CANCELED"
    )


def format_digest(date_str, y_insights, w_insights, y_pixel, y_orders, w_orders):
    """Compose the markdown digest body."""
    y_spend = sum(float(r.get("spend", 0) or 0) for r in y_insights)
    y_impr = sum(int(r.get("impressions", 0) or 0) for r in y_insights)
    y_clicks = sum(int(r.get("clicks", 0) or 0) for r in y_insights)
    y_lpv = sum(lpv_from_actions(r) for r in y_insights)
    y_ctr = (y_clicks / y_impr * 100) if y_impr else 0

    y_pixel_purchase = y_pixel.get("Purchase", 0)
    y_pixel_atc = y_pixel.get("AddToCart", 0)

    y_cash_revenue = revenue_excl_cancelled(y_orders)
    y_cash_orders = sum(
        1 for o in y_orders
        if (o.get("status") or "").strip().upper() != "CANCELED"
    )
    y_roas_cash = (y_cash_revenue / y_spend) if y_spend else 0
    y_roas_pixel = (y_pixel_purchase * 998 / y_spend) if y_spend else 0  # estimate at AOV ₱998

    w_spend = sum(float(r.get("spend", 0) or 0) for r in w_insights)
    w_lpv = sum(lpv_from_actions(r) for r in w_insights)
    w_cash_revenue = revenue_excl_cancelled(w_orders)
    w_cash_orders = sum(
        1 for o in w_orders
        if (o.get("status") or "").strip().upper() != "CANCELED"
    )
    w_roas_cash = (w_cash_revenue / w_spend) if w_spend else 0

    # top + lowest performer by cost/LPV (only ads with >0 LPV for top; >₱20 spent for lowest)
    ads_with_lpv = []
    for r in y_insights:
        lpv = lpv_from_actions(r)
        spend = float(r.get("spend", 0) or 0)
        if spend > 0:
            cost_per_lpv = (spend / lpv) if lpv else None
            ads_with_lpv.append({
                "name": (r.get("ad_name") or "?").replace("DuberyMNL - ", ""),
                "spend": spend,
                "lpv": lpv,
                "cpl": cost_per_lpv,
            })

    # top = lowest cost/LPV among ads with meaningful spend
    top = min(
        (a for a in ads_with_lpv if a["lpv"] > 0 and a["spend"] >= 10),
        key=lambda a: a["cpl"],
        default=None,
    )
    # biggest spender (informational, not necessarily bad)
    biggest = max(ads_with_lpv, key=lambda a: a["spend"], default=None)

    lines = []
    lines.append(f"*Dubery Ads — {date_str} (PHT)*")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"Spend:   ₱{y_spend:,.2f}   ·   LPV {y_lpv}   ·   CTR {y_ctr:.2f}%")
    lines.append(f"Orders:  {y_cash_orders}   ·   Revenue ₱{y_cash_revenue:,.0f}")
    lines.append("")
    lines.append("*ROAS (yesterday)*")
    lines.append(f"  Cash basis (Orders):  {y_roas_cash:.2f}x")
    lines.append(f"  Pixel-attributed:     {y_roas_pixel:.2f}x  ({y_pixel_purchase} Purchase, {y_pixel_atc} ATC)")
    lines.append("")
    if top:
        lines.append(f"🏆 Best CPL: {top['name']}   ₱{top['spend']:.0f} / {top['lpv']} LPV = ₱{top['cpl']:.2f}/LPV")
    else:
        lines.append(f"🏆 Best CPL: n/a (no ads with ≥₱10 spend + ≥1 LPV)")
    if biggest and biggest["spend"] >= 5:
        if biggest["lpv"] == 0:
            lines.append(f"💰 Biggest spend: {biggest['name']}   ₱{biggest['spend']:.0f}, 0 LPV")
        else:
            lines.append(f"💰 Biggest spend: {biggest['name']}   ₱{biggest['spend']:.0f} / {biggest['lpv']} LPV = ₱{biggest['cpl']:.2f}/LPV")
    lines.append("")
    lines.append(f"*7-day rolling*")
    lines.append(f"  Spend ₱{w_spend:,.0f}   ·   Orders {w_cash_orders}   ·   Revenue ₱{w_cash_revenue:,.0f}")
    lines.append(f"  ROAS (cash): {w_roas_cash:.2f}x")

    return "\n".join(lines)


def send_telegram(text):
    if not TG_TOKEN or not TG_CHAT_ID:
        log("TG not configured — skipping send")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={
                "chat_id": TG_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        if r.status_code == 200:
            log(f"TG sent OK ({len(text)} chars)")
            return True
        log(f"TG send failed {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        log(f"TG send exception: {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="print only, no TG send")
    ap.add_argument("--date", help="override yesterday's date (YYYY-MM-DD, PHT)")
    args = ap.parse_args()

    now_pht = datetime.now(PHT)
    if args.date:
        y_date = args.date
    else:
        y_date = (now_pht - timedelta(days=1)).strftime("%Y-%m-%d")
    y_dt = datetime.strptime(y_date, "%Y-%m-%d")
    w_from = (y_dt - timedelta(days=6)).strftime("%Y-%m-%d")
    w_to = y_date

    log(f"Building digest for {y_date} (window {w_from} to {w_to})")

    y_insights = pull_ad_insights(y_date, y_date)
    w_insights = pull_ad_insights(w_from, w_to)
    y_pixel = pull_pixel_events(y_date, y_date)
    y_orders = pull_orders_for_date(y_date)
    w_orders = pull_orders_window(w_from, w_to)

    digest = format_digest(y_date, y_insights, w_insights, y_pixel, y_orders, w_orders)

    # archive
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    (ARCHIVE_DIR / f"{y_date}.md").write_text(digest, encoding="utf-8")
    log(f"archived {ARCHIVE_DIR}/{y_date}.md")

    print()
    print(digest)
    print()

    if not args.dry:
        send_telegram(digest)


if __name__ == "__main__":
    main()

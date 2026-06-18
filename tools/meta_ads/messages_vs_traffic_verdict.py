"""
Messages-vs-Traffic verdict for the Father's Day click-to-Messenger test.

One-shot read (scheduled via Task Scheduler for 2026-06-23, after the Messages
FD test auto-stops). Pulls campaign-level Meta insights for BOTH campaigns over
the test window, splits CRM orders into Messenger vs Web buckets, computes
cost-per-order for each channel, and Telegrams RA a keep-or-kill verdict.

Attribution is best-effort:
  - Messages channel  = orders sourced 'chatbot_mark_sale' / 'messenger', or a
    numeric source matching one of the Messages campaign's ad ids.
  - Web/Traffic channel = everything else (order_form + other ad ids).
Meta-native metrics (cost per messaging conversation, cost per LPV) are exact.

Run:
  python tools/meta_ads/messages_vs_traffic_verdict.py            # send to TG
  python tools/meta_ads/messages_vs_traffic_verdict.py --dry      # console only
  python tools/meta_ads/messages_vs_traffic_verdict.py --from 2026-06-18 --to 2026-06-23
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
import os

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env")

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

META_TOKEN = os.environ["META_ADS_ACCESS_TOKEN"]
META_ACCT = os.environ["META_AD_ACCOUNT_ID"].replace("act_", "")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")
API = "https://graph.facebook.com/v23.0"
PHT = timezone(timedelta(hours=8))

MESSAGES_CAMP = "52528754160080"   # DuberyMNL - Messages - Father's Day Test
TRAFFIC_CAMP = "6968215093276"     # DuberyMNL Traffic (proven converter)
MESSAGES_AD_IDS = {"52528755732480", "52528755759480", "52528755778280", "52528755796880"}
DEFAULT_FROM = "2026-06-18"
DEFAULT_TO = "2026-06-23"

LOG = REPO_ROOT / ".tmp" / "messages_verdict.log"


def log(msg):
    ts = datetime.now(PHT).strftime("%Y-%m-%d %H:%M:%S")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.open("a", encoding="utf-8").write(f"[{ts}] {msg}\n")
    print(msg)


def meta_get(endpoint, **params):
    params["access_token"] = META_TOKEN
    r = requests.get(f"{API}/{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def campaign_insights(camp_id, date_from, date_to):
    r = meta_get(f"{camp_id}/insights",
                 level="campaign",
                 time_range=json.dumps({"since": date_from, "until": date_to}),
                 fields="spend,impressions,clicks,actions,cost_per_action_type")
    data = r.get("data", [])
    return data[0] if data else {}


def action_val(row, *types):
    out = 0
    for a in row.get("actions", []) or []:
        if a.get("action_type") in types:
            out += int(float(a.get("value", 0)))
    return out


def pull_orders_window(date_from, date_to):
    try:
        r = requests.get("http://127.0.0.1:8090/api/crm/orders",
                         params={"fresh": "1"}, timeout=15)
        if r.status_code != 200:
            log(f"CC orders HTTP {r.status_code}")
            return None
        return [o for o in r.json()
                if date_from <= (o.get("order_date") or "") <= date_to]
    except Exception as e:
        log(f"orders pull failed: {e}")
        return None


def is_messages_order(o):
    src = (o.get("source") or "").strip().lower()
    if src in MESSAGES_AD_IDS:
        return True
    return any(tok in src for tok in ("chatbot", "messenger", "mark_sale", "m.me"))


def not_cancelled(o):
    return (o.get("status") or "").strip().upper() not in ("CANCELED", "CANCELLED")


def bucket_orders(orders):
    msg = [o for o in orders if not_cancelled(o) and is_messages_order(o)]
    web = [o for o in orders if not_cancelled(o) and not is_messages_order(o)]
    return msg, web


def rev(orders):
    return sum(float(o.get("total", 0) or 0) for o in orders)


def peso(n):
    return f"₱{n:,.0f}"


def cpo(spend, n):
    return f"₱{spend / n:,.0f}/order" if n else "— (0 orders)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--from", dest="dfrom", default=DEFAULT_FROM)
    ap.add_argument("--to", dest="dto", default=DEFAULT_TO)
    args = ap.parse_args()
    dfrom, dto = args.dfrom, args.dto

    log(f"Verdict window {dfrom}..{dto}")

    m = campaign_insights(MESSAGES_CAMP, dfrom, dto)
    t = campaign_insights(TRAFFIC_CAMP, dfrom, dto)
    m_spend = float(m.get("spend", 0) or 0)
    t_spend = float(t.get("spend", 0) or 0)
    m_convos = action_val(m, "onsite_conversion.messaging_conversation_started_7d",
                          "onsite_conversion.total_messaging_connection")
    t_lpv = action_val(t, "landing_page_view")

    orders = pull_orders_window(dfrom, dto)
    if orders is None:
        cc_note = "⚠ Command Center unreachable — order figures unavailable (Meta metrics only)."
        m_orders = w_orders = []
    else:
        m_orders, w_orders = bucket_orders(orders)
        cc_note = ""

    m_n, w_n = len(m_orders), len(w_orders)
    m_rev, w_rev = rev(m_orders), rev(w_orders)

    # verdict logic
    if orders is None:
        verdict = "INCONCLUSIVE — no order data. Pull orders manually before deciding."
    elif m_n == 0:
        verdict = (f"KILL — Messages booked 0 orders on {peso(m_spend)}. "
                   f"The website remains the converter; keep the proof you have.")
    else:
        m_cpo = m_spend / m_n
        w_cpo = (t_spend / w_n) if w_n else float("inf")
        if m_cpo <= w_cpo:
            verdict = (f"KEEP / EXTEND — Messages closed at {peso(m_cpo)}/order vs "
                       f"Traffic {cpo(t_spend, w_n)}. Cheaper channel — worth a longer run.")
        else:
            verdict = (f"KILL — Messages {peso(m_cpo)}/order vs Traffic {cpo(t_spend, w_n)}. "
                       f"Traffic is cheaper; the website is still the converter.")

    lines = [
        f"*Messages vs Traffic — FD Test Verdict*",
        f"_Window {dfrom} → {dto} (PHT)_",
        "━━━━━━━━━━━━━━━━━━━━",
        "*📩 Messages (click-to-Messenger)*",
        f"  Spend {peso(m_spend)} · {m_convos} convos · "
        + (f"{peso(m_spend / m_convos)}/convo" if m_convos else "—/convo"),
        f"  Orders {m_n} · Rev {peso(m_rev)} · {cpo(m_spend, m_n)}",
        "",
        "*🌐 Traffic (website)*",
        f"  Spend {peso(t_spend)} · {t_lpv} LPV · "
        + (f"{peso(t_spend / t_lpv)}/LPV" if t_lpv else "—/LPV"),
        f"  Orders {w_n} · Rev {peso(w_rev)} · {cpo(t_spend, w_n)}",
        "",
        f"*Verdict:* {verdict}",
    ]
    if cc_note:
        lines += ["", cc_note]
    lines += ["", "_Attribution best-effort (order source split). Cross-check before acting._"]
    text = "\n".join(lines)

    print("\n" + text + "\n")

    if args.dry:
        log("dry run — not sent")
        return
    if not TG_TOKEN or not TG_CHAT_ID:
        log("TG not configured — skipping send")
        return
    r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      json={"chat_id": TG_CHAT_ID, "text": text,
                            "parse_mode": "Markdown", "disable_web_page_preview": True},
                      timeout=15)
    log(f"TG send {r.status_code}: {r.text[:160]}")


if __name__ == "__main__":
    main()

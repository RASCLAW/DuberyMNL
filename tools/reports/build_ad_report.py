"""Build HTML ad-performance report with creative thumbnails."""
import os
import sys
import json
import requests
from datetime import datetime, date
from dotenv import load_dotenv
from pathlib import Path

# Promoted from .tmp 2026-06-05. Paths anchor to the repo root (tools/reports/ -> repo).
REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / '.env')

TOK = os.getenv('META_ADS_ACCESS_TOKEN')
# Input: Meta ad-insights snapshot (regenerable scratch in .tmp). Override with argv[1].
INSIGHTS_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / '.tmp' / 'ad_insights.json'
INSIGHTS = json.load(open(INSIGHTS_PATH, encoding='utf-8'))

CAMPAIGN_START = date(2026, 5, 6)
PIXEL_INSTALL = date(2026, 5, 20)
ORDERS_SHEET_ID = '1vS-yuFWovqHYWrFte4QXJLtH3Q2-BRDi6i9P4-vXbkA'


def fetch_orders():
    """Pull orders since campaign start, classify by status."""
    sys.path.insert(0, str(REPO_ROOT / 'tools'))
    from auth import get_credentials
    from googleapiclient.discovery import build
    svc = build('sheets', 'v4', credentials=get_credentials())
    rng = 'Orders!A:L'
    res = svc.spreadsheets().values().get(spreadsheetId=ORDERS_SHEET_ID, range=rng).execute()
    values = res.get('values', [])
    if not values:
        return []
    headers = values[0]
    rows = [dict(zip(headers, r + [''] * (len(headers) - len(r)))) for r in values[1:]]
    # add manual status (col K) - sheet has 10 headers + col K unheadered
    for i, r in enumerate(rows, start=2):
        full_row = values[i - 1] + [''] * 12
        r['_status'] = (full_row[10] if len(full_row) > 10 else '').strip().upper()
    return rows


def parse_order_date(ts):
    """Order Timestamp formats: '5/25/2026 14:30:22' (sheet's native) or ISO."""
    if not ts:
        return None
    for fmt in ('%m/%d/%Y %H:%M:%S', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(ts.strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_qty(qty_str, items_str):
    """Qty field is newline-separated per item: '1\\n1' = 2 units. Falls back to item count."""
    if qty_str:
        total = 0
        for line in qty_str.split('\n'):
            try:
                total += int(line.strip())
            except (ValueError, TypeError):
                continue
        if total > 0:
            return total
    # fallback: count en-dash-separated colorway lines
    if items_str:
        return len([l for l in items_str.split('\n') if '–' in l])
    return 1


orders = fetch_orders()
campaign_orders = []
for o in orders:
    d = parse_order_date(o.get('Timestamp', ''))
    if not d or d < CAMPAIGN_START:
        continue
    status = o.get('_status', '')
    qty = parse_qty(o.get('Qty', ''), o.get('Items', ''))
    total_str = (o.get('Total Amount', '') or '0').replace(',', '').replace('P', '').replace('₱', '').strip()
    try:
        total = float(total_str)
    except ValueError:
        total = 0
    campaign_orders.append({
        'date': d,
        'name': o.get('Name', ''),
        'items': o.get('Items', ''),
        'qty': qty,
        'total': total,
        'status': status,
        'source': o.get('Ad ID', '') or 'order_form',
    })

delivered = [o for o in campaign_orders if o['status'] == 'DELIVERED']
cancelled = [o for o in campaign_orders if o['status'] == 'CANCELED' or o['status'] == 'CANCELLED']
pending = [o for o in campaign_orders if o['status'] not in ('DELIVERED', 'CANCELED', 'CANCELLED')]

real_sales = {
    'delivered_orders': len(delivered),
    'delivered_units': sum(o['qty'] for o in delivered),
    'delivered_gross': sum(o['total'] for o in delivered),
    'pending_orders': len(pending),
    'pending_units': sum(o['qty'] for o in pending),
    'pending_gross': sum(o['total'] for o in pending),
    'cancelled_orders': len(cancelled),
    'total_orders': len(delivered) + len(pending),  # exclude cancelled from "real"
    'total_units': sum(o['qty'] for o in delivered) + sum(o['qty'] for o in pending),
    'total_gross': sum(o['total'] for o in delivered) + sum(o['total'] for o in pending),
    'post_pixel_orders': sum(1 for o in campaign_orders if o['date'] >= PIXEL_INSTALL and o['status'] != 'CANCELED'),
}

print(f"Orders since {CAMPAIGN_START}: {len(campaign_orders)} total, {real_sales['delivered_orders']} delivered ({real_sales['delivered_units']}u), {real_sales['pending_orders']} pending ({real_sales['pending_units']}u), {real_sales['cancelled_orders']} cancelled")


def get_action(actions, name):
    return next((int(x['value']) for x in actions or [] if x['action_type'] == name), 0)


def fetch_creative(ad_id):
    r = requests.get(
        f'https://graph.facebook.com/v21.0/{ad_id}',
        params={'fields': 'creative{image_url,thumbnail_url,object_story_spec}', 'access_token': TOK},
        timeout=30,
    )
    return r.json().get('creative', {})


# Build per-ad rows
rows = []
for ad in INSIGHTS['ads']:
    spend = float(ad.get('spend', 0) or 0)
    if spend < 5:  # skip near-zero
        continue
    creative = fetch_creative(ad['ad_id'])
    img = creative.get('image_url') or creative.get('thumbnail_url') or ''
    story = creative.get('object_story_spec', {}).get('link_data', {})
    rows.append({
        'name': ad['ad_name'].replace('DuberyMNL - ', ''),
        'adset': ad['adset_name'],
        'img': img,
        'message': story.get('message', ''),
        'spend': spend,
        'impr': int(ad.get('impressions', 0) or 0),
        'clicks': int(ad.get('clicks', 0) or 0),
        'ctr': float(ad.get('ctr', 0) or 0),
        'cpc': float(ad.get('cpc', 0) or 0),
        'lpv': get_action(ad.get('actions'), 'landing_page_view'),
        'msg': get_action(ad.get('actions'), 'onsite_conversion.total_messaging_connection'),
        'purch': get_action(ad.get('actions'), 'omni_purchase'),
    })
    print(f"  {ad['ad_name'][:60]} -> img={'YES' if img else 'NO'}")

rows.sort(key=lambda r: r['spend'], reverse=True)

# Adset totals
adsets = {}
for a in INSIGHTS['adsets']:
    adsets[a['adset_name']] = {
        'spend': float(a.get('spend', 0)),
        'clicks': int(a.get('clicks', 0)),
        'impr': int(a.get('impressions', 0)),
        'ctr': float(a.get('ctr', 0)),
        'cpc': float(a.get('cpc', 0)),
        'lpv': get_action(a.get('actions'), 'landing_page_view'),
        'msg': get_action(a.get('actions'), 'onsite_conversion.total_messaging_connection'),
        'purch': get_action(a.get('actions'), 'omni_purchase'),
    }


def badge(row):
    """Traffic-objective tier: hits the full funnel from impression to LPV."""
    lpv_rate = (row['lpv'] / row['clicks'] * 100) if row['clicks'] else 0
    if row['ctr'] >= 2.3 and row['cpc'] <= 1.20 and lpv_rate >= 40:
        return ('WINNER', '#2d8a4e')   # --ok
    if row['ctr'] >= 2.0 and row['cpc'] <= 1.30:
        return ('KEEP', '#e07a3a')     # --accent
    if row['ctr'] < 1.5 or row['cpc'] > 2.0:
        return ('CUT', '#d93025')      # --bad
    return ('OK', '#9e9890')           # --gray


def ctr_tone(v):
    if v >= 2.5: return 'good'
    if v >= 2.0: return 'mid'
    return 'bad'

def cpc_tone(v):
    if v <= 1.20: return 'good'
    if v <= 1.60: return 'mid'
    return 'bad'

def msg_tone(v):
    if v >= 2: return 'good'
    if v >= 1: return 'mid'
    return 'bad'


# ============ KPI targets (Traffic objective) ============
# Campaign objective is Traffic -- Meta optimizes for clicks -> LPVs.
# Msg metrics tracked as secondary signals, not primary, until/unless
# we switch to a Messages-objective campaign.
KPI_TARGETS = {
    'ctr': 2.0,             # >= 2.0%
    'cpc': 1.30,            # <= P1.30
    'lpv_rate': 40.0,       # LPV / clicks >= 40%
    'cost_per_lpv': 3.20,   # spend / LPV <= P3.20 (CPC P1.30 / 40% LPV-rate)
    'cost_per_order': 320,  # spend / orders <= P320 (30% of AOV)
    # Secondary (Messages-objective territory; tracked, not gated)
    'msg_rate': 0.8,
    'cost_per_msg': 150,
}


def kpi_status(actual, target, lower_is_better=False):
    if actual is None:
        return 'na'
    if lower_is_better:
        if actual <= target: return 'good'
        if actual <= target * 1.3: return 'mid'
        return 'bad'
    else:
        if actual >= target: return 'good'
        if actual >= target * 0.8: return 'mid'
        return 'bad'


def analyze_ad(r, campaign_avg):
    """Rule-based reasoning -- no AI in scripts. Returns (verdict, why, opportunity)."""
    ctr = r['ctr']; cpc = r['cpc']; msg = r['msg']; lpv = r['lpv']
    clicks = r['clicks']; spend = r['spend']; purch = r['purch']
    lpv_rate = (lpv / clicks * 100) if clicks else 0
    msg_rate = (msg / clicks * 100) if clicks else 0
    avg_ctr = campaign_avg['ctr']
    avg_cpc = campaign_avg['cpc']

    # Full-funnel winner (Traffic objective)
    if ctr >= 2.3 and cpc <= 1.20 and lpv_rate >= 40:
        msg_note = f" {msg} Msg connections on top." if msg > 0 else ""
        return (
            "Full-funnel winner",
            f"Strong hook ({ctr:.2f}% CTR, {(ctr/avg_ctr-1)*100:+.0f}% vs campaign avg), efficient bid (P{cpc:.2f} CPC, {(1-cpc/avg_cpc)*100:+.0f}% cheaper than avg), and clickers land cleanly ({lpv_rate:.0f}% LPV-rate).{msg_note}",
            "Duplicate the creative format into 2-3 variants. Use as control when testing new hooks. Safe to bump budget on its adset."
        )
    # Hook works but LP doesn't
    if ctr >= 2.5 and lpv_rate < 35:
        return (
            "Thumb-stopper, weak landing",
            f"Excellent CTR ({ctr:.2f}%) but only {lpv_rate:.0f}% of clicks become landing-page views (target {KPI_TARGETS['lpv_rate']:.0f}%). The image is doing its job; the landing experience isn't.",
            "Check the link UTM destination -- creative promise (lifestyle / spec / price) needs to match what shows on the PDP. Also check LP load time on 3G."
        )
    # Quiet quality - underfunded but decent
    if spend < 35 and ctr >= 2.5 and cpc <= 1.30:
        return (
            "Quiet quality (under-tested)",
            f"Strong CTR ({ctr:.2f}%) and clean CPC (P{cpc:.2f}) but Meta has only spent P{spend:.0f} on it -- algo hasn't found its audience yet.",
            "Move into a new adset with budget headroom so it can earn impressions. Pair with the top performer in an A/B."
        )
    # Bid loser
    if ctr < 1.5 and cpc > 1.80:
        return (
            "Auction loser",
            f"Weak CTR ({ctr:.2f}%, {(ctr/avg_ctr-1)*100:+.0f}% vs avg) combined with expensive bid (P{cpc:.2f}, {(cpc/avg_cpc-1)*100:+.0f}% above avg). Meta's relevance score is punishing this ad in the auction.",
            "Pause. The audience-creative match is off. If you want to save it: retag as different product or rebuild hook."
        )
    # Cheap but unconverting
    if cpc <= 1.30 and msg == 0 and purch == 0 and clicks >= 30:
        return (
            "Cheap clicks, no conversion",
            f"CPC is fine (P{cpc:.2f}) and you've gotten {clicks} clicks -- but zero Messenger leads and zero purchases. Audience clicks out of curiosity, not buying intent.",
            "Test a higher-intent placement (Reels-only, in-stream). Or treat as awareness ad and stop expecting bottom-funnel conversion from it."
        )
    # Msg magnet
    if msg >= 2 and msg_rate >= 1.5:
        return (
            "Messenger magnet",
            f"{msg} Msg leads from {clicks} clicks ({msg_rate:.1f}% conversion rate, vs target {KPI_TARGETS['msg_rate']:.1f}%). Above-average pull into 1:1 conversation.",
            "Duplicate into a Messages-objective campaign where Meta optimizes specifically for the Msg action -- should drop cost per Msg by 30-50%."
        )
    # Volume leader
    if spend >= 150 and ctr >= 2.0 and cpc <= 1.30:
        return (
            "Scale-tested winner",
            f"Meta has spent P{spend:.0f} on this -- highest confidence vote in the account. Maintains CTR {ctr:.2f}% / CPC P{cpc:.2f} even at scale, meaning audience hasn't fatigued.",
            "Use as the control creative for the next test cycle. Don't change it; build variants around it."
        )
    # Bouncy clicks
    if clicks >= 30 and lpv_rate < 30:
        return (
            "Bouncy clicks",
            f"{clicks} clicks but only {lpv_rate:.0f}% become LPVs (target {KPI_TARGETS['lpv_rate']:.0f}%). Likely accidental scrolls or LP load failure rather than rejection.",
            "Verify mobile LP load time. If it's slow, fix that first -- creative is fine."
        )
    # Middle of the pack with no glaring weakness
    if ctr >= 1.8 and cpc <= 1.60:
        return (
            "Middle of the pack",
            f"CTR {ctr:.2f}% and CPC P{cpc:.2f} are acceptable but no standout signal. Meta's spreading budget here without strong reward.",
            "Iterate the hook (caption first line, image lead element). Or rotate out to make budget room for the quiet-quality ads."
        )
    # Default weak
    return (
        "Underperforming",
        f"CTR {ctr:.2f}% and CPC P{cpc:.2f} both below comfortable thresholds. {msg} Msg, {purch} purch.",
        "Cut or rework. Use the spend savings to fund a new variant of the top winner."
    )


# ============ Visual tag extraction (rule-based, from naming convention) ============
def extract_visual_tags(ad_name):
    n = ad_name.lower()
    tags = {'format': None, 'product': None, 'color': None, 'style': None}

    # Format taxonomy
    if 'bespoke' in n:
        tags['format'] = 'UGC Bespoke'
    elif 'bold-' in n:
        tags['format'] = 'Bold Statement'
    elif 'callout' in n:
        tags['format'] = 'Feature Callout'
    elif 'coll-' in n or 'collection' in n.lower():
        tags['format'] = 'Collection Showcase'
    elif 'brand-v3-split' in n:
        tags['format'] = 'Brand Split-screen'
    elif 'brand-v3-topbottom' in n:
        tags['format'] = 'Brand Top-Bottom'
    elif 'sample-coll' in n:
        tags['format'] = 'Collection Showcase'
    else:
        tags['format'] = 'Other'

    # Product
    if 'bandits' in n:
        tags['product'] = 'Bandits'
    elif 'outback' in n:
        tags['product'] = 'Outback'
    elif 'rasta' in n:
        tags['product'] = 'Rasta'
    else:
        tags['product'] = 'Brand Graphic'

    # Colorway (order matters — longer match first)
    for color in ['glossy-black', 'tortoise', 'brown', 'green', 'black', 'blue', 'red']:
        if color in n:
            tags['color'] = color.replace('-', ' ').title()
            break
    if not tags['color']:
        tags['color'] = 'No single colorway'

    # Style cue
    if 'graphic' in n:
        tags['style'] = 'Text-overlay graphic'
    elif 'edit' in n:
        tags['style'] = 'Manual edit'
    elif 'concept' in n:
        tags['style'] = 'Concept image'
    elif 'eyes-on-the-view' in n:
        tags['style'] = 'Tagline-led'
    else:
        tags['style'] = 'Clean'

    return tags


def group_by_tag(rows, tag_key):
    """Group rows by a tag category, return aggregated metrics."""
    groups = {}
    for r in rows:
        tags = extract_visual_tags(r['name'])
        t = tags.get(tag_key) or 'Unknown'
        if t not in groups:
            groups[t] = {'tag': t, 'count': 0, 'spend': 0, 'impr': 0, 'clicks': 0, 'msg': 0, 'lpv': 0, 'purch': 0}
        g = groups[t]
        g['count'] += 1
        g['spend'] += r['spend']
        g['impr'] += r['impr']
        g['clicks'] += r['clicks']
        g['msg'] += r['msg']
        g['lpv'] += r['lpv']
        g['purch'] += r['purch']
    out = []
    for g in groups.values():
        g['ctr'] = (g['clicks'] / g['impr'] * 100) if g['impr'] else 0
        g['cpc'] = (g['spend'] / g['clicks']) if g['clicks'] else 0
        g['lpv_rate'] = (g['lpv'] / g['clicks'] * 100) if g['clicks'] else 0
        g['msg_rate'] = (g['msg'] / g['clicks'] * 100) if g['clicks'] else 0
        out.append(g)
    return sorted(out, key=lambda g: -g['ctr'])


PATTERN_GROUPS = {
    'format': group_by_tag(rows, 'format'),
    'product': group_by_tag(rows, 'product'),
    'color': group_by_tag(rows, 'color'),
    'style': group_by_tag(rows, 'style'),
}


def pattern_takeaway(groups, category):
    """Plain-English interpretation that respects sample size."""
    if len(groups) < 2:
        return 'Not enough variety to compare.'

    # Filter to groups with N >= 3 for trustworthy comparison
    reliable = [g for g in groups if g['count'] >= 3]

    if len(reliable) >= 2:
        best = reliable[0]
        worst = reliable[-1]
        if worst['ctr'] == 0:
            return f"<strong>{best['tag']}</strong> ({best['count']} ads) leads at {best['ctr']:.2f}% CTR / P{best['cpc']:.2f} CPC. Reliable comparison -- sample size on top of {worst['tag']} is too thin to judge."
        delta_ctr = (best['ctr'] - worst['ctr']) / worst['ctr'] * 100
        cpc_dir = "cheaper" if best['cpc'] < worst['cpc'] else "more expensive"
        cpc_pct = abs((best['cpc'] - worst['cpc']) / worst['cpc'] * 100)
        return (f"<strong>{best['tag']}</strong> ({best['count']} ads) beats <strong>{worst['tag']}</strong> "
                f"({worst['count']} ads) by {delta_ctr:+.0f}% on CTR -- {best['ctr']:.2f}% vs {worst['ctr']:.2f}%. "
                f"And {cpc_pct:.0f}% {cpc_dir} per click (P{best['cpc']:.2f} vs P{worst['cpc']:.2f}).")

    # Only 1 reliable group -- compare against the single-ad leaders carefully
    if len(reliable) == 1:
        r = reliable[0]
        single_best = max((g for g in groups if g['count'] < 3 and g['count'] > 0), key=lambda g: g['ctr'], default=None)
        if single_best and single_best['ctr'] > r['ctr']:
            return (f"<strong>{r['tag']}</strong> is the only category with a reliable sample ({r['count']} ads, "
                    f"{r['ctr']:.2f}% CTR / P{r['cpc']:.2f} CPC). <strong>{single_best['tag']}</strong> looks better "
                    f"on paper ({single_best['ctr']:.2f}% CTR) but with only {single_best['count']} ad -- "
                    f"early signal, not a proven pattern. Build more variants to test.")
        return f"<strong>{r['tag']}</strong> ({r['count']} ads) is the only category with a meaningful sample. {r['ctr']:.2f}% CTR / P{r['cpc']:.2f} CPC."

    # No reliable samples at all -- everything is small-N
    best = groups[0]
    return (f"Every category here is small-sample (1-2 ads each). Don't trust the rankings; "
            f"these are early signals. Top so far: <strong>{best['tag']}</strong> at {best['ctr']:.2f}% CTR.")


def pattern_interpretation(groups, category):
    """Auto-generate 2-3 sentence plain-English reading of the table."""
    if not groups:
        return 'No data.'

    total_ads = sum(g['count'] for g in groups)
    small_n = [g for g in groups if g['count'] < 3]
    big_n = [g for g in groups if g['count'] >= 3]

    parts = []

    # Sample-size warning if dominant
    if len(small_n) > len(big_n):
        parts.append(f"{len(small_n)} of {len(groups)} {category}s have only 1-2 ads -- treat their numbers as early signals, not proven patterns.")

    # Identify the highest-volume / most-tested category
    most_tested = max(groups, key=lambda g: g['count'])
    if most_tested['count'] >= 5:
        ctr_word = "well above" if most_tested['ctr'] >= 2.5 else ("around" if most_tested['ctr'] >= 1.8 else "below")
        parts.append(f"<strong>{most_tested['tag']}</strong> has the largest sample ({most_tested['count']} ads); its {most_tested['ctr']:.2f}% CTR is {ctr_word} the campaign average.")

    # Identify any obvious laggards (N >= 3, CTR < 2.0%)
    laggers = [g for g in big_n if g['ctr'] < 2.0]
    if laggers:
        worst = min(laggers, key=lambda g: g['ctr'])
        parts.append(f"<strong>{worst['tag']}</strong> is underperforming at {worst['ctr']:.2f}% CTR across {worst['count']} ads -- a real signal, not a one-ad fluke.")

    if not parts:
        parts.append(f"Sample sizes here are mostly small. Need more ads per category to draw conclusions.")

    return ' '.join(parts)


# ============ Executive summary + KPIs (must be defined before cards loop) ============
campaign_total = INSIGHTS.get('campaign', [{}])[0] if INSIGHTS.get('campaign') else {}
total_spend = float(campaign_total.get('spend', 0) or 0)
total_clicks = int(campaign_total.get('clicks', 0) or 0)
total_impr = int(campaign_total.get('impressions', 0) or 0)
total_msg = get_action(campaign_total.get('actions'), 'onsite_conversion.total_messaging_connection')
total_purch = get_action(campaign_total.get('actions'), 'omni_purchase')
total_lpv = get_action(campaign_total.get('actions'), 'landing_page_view')
overall_ctr = float(campaign_total.get('ctr', 0) or 0)
overall_cpc = float(campaign_total.get('cpc', 0) or 0)

adset_sorted = sorted(adsets.items(), key=lambda kv: (-kv[1]['ctr'], kv[1]['cpc']))
winning_adset = adset_sorted[0][0]
losing_adset = adset_sorted[-1][0]
win = adset_sorted[0][1]
lose = adset_sorted[-1][1]


def score(r):
    return r['ctr'] * 10 - r['cpc'] * 3 + r['msg'] * 2


ad_scored = sorted(rows, key=score, reverse=True)
top3 = ad_scored[:3]
bottom3 = ad_scored[-3:][::-1]

campaign_avg = {
    'ctr': overall_ctr,
    'cpc': overall_cpc,
    'lpv_rate': (total_lpv / total_clicks * 100) if total_clicks else 0,
    'cost_per_lpv': (total_spend / total_lpv) if total_lpv else None,
    'msg_rate': (total_msg / total_clicks * 100) if total_clicks else 0,
    'cost_per_msg': (total_spend / total_msg) if total_msg else None,
    'cost_per_order': (total_spend / real_sales['total_orders']) if real_sales['total_orders'] else None,
}

# Primary KPIs -- Traffic-objective funnel
KPI_PANEL_PRIMARY = [
    {'key': 'ctr', 'label': 'Hook rate (CTR)', 'value': f"{campaign_avg['ctr']:.2f}%", 'target': f">= {KPI_TARGETS['ctr']:.1f}%", 'status': kpi_status(campaign_avg['ctr'], KPI_TARGETS['ctr']), 'desc': 'attention per impression'},
    {'key': 'cpc', 'label': 'Click efficiency (CPC)', 'value': f"P{campaign_avg['cpc']:.2f}", 'target': f"<= P{KPI_TARGETS['cpc']:.2f}", 'status': kpi_status(campaign_avg['cpc'], KPI_TARGETS['cpc'], lower_is_better=True), 'desc': 'cost per click'},
    {'key': 'lpv_rate', 'label': 'Landing engagement', 'value': f"{campaign_avg['lpv_rate']:.0f}%", 'target': f">= {KPI_TARGETS['lpv_rate']:.0f}%", 'status': kpi_status(campaign_avg['lpv_rate'], KPI_TARGETS['lpv_rate']), 'desc': 'LPV / click'},
    {'key': 'cost_per_lpv', 'label': 'Cost per LPV', 'value': f"P{campaign_avg['cost_per_lpv']:.2f}" if campaign_avg['cost_per_lpv'] else 'n/a', 'target': f"<= P{KPI_TARGETS['cost_per_lpv']:.2f}", 'status': kpi_status(campaign_avg['cost_per_lpv'], KPI_TARGETS['cost_per_lpv'], lower_is_better=True), 'desc': 'spend / LPV -- the cost metric Traffic optimizes for'},
    {'key': 'cost_per_order', 'label': 'Cost per order', 'value': f"P{campaign_avg['cost_per_order']:.0f}" if campaign_avg['cost_per_order'] else 'n/a', 'target': f"<= P{KPI_TARGETS['cost_per_order']}", 'status': kpi_status(campaign_avg['cost_per_order'], KPI_TARGETS['cost_per_order'], lower_is_better=True), 'desc': 'spend / Orders-sheet count'},
]

# Secondary KPIs -- Msg signals, only primary for Messages-objective campaigns
KPI_PANEL_SECONDARY = [
    {'key': 'msg_rate', 'label': 'Msg conversion', 'value': f"{campaign_avg['msg_rate']:.2f}%", 'target': f">= {KPI_TARGETS['msg_rate']:.1f}%", 'status': kpi_status(campaign_avg['msg_rate'], KPI_TARGETS['msg_rate']), 'desc': 'msg / click (secondary on Traffic)'},
    {'key': 'cost_per_msg', 'label': 'Cost per Msg', 'value': f"P{campaign_avg['cost_per_msg']:.0f}" if campaign_avg['cost_per_msg'] else 'n/a', 'target': f"<= P{KPI_TARGETS['cost_per_msg']}", 'status': kpi_status(campaign_avg['cost_per_msg'], KPI_TARGETS['cost_per_msg'], lower_is_better=True), 'desc': 'spend / Msg lead'},
]


cards_html = []
for i, r in enumerate(rows):
    label, color = badge(r)
    img_tag = f'<img src="{r["img"]}" loading="lazy">' if r['img'] else '<div class="noimg">no image</div>'
    adset_short = r['adset'].replace('Traffic - ', '').replace(' - May2026', '')
    verdict, why, opportunity = analyze_ad(r, campaign_avg)
    visual_tags = extract_visual_tags(r['name'])
    tag_chips = ''.join(
        f'<span class="tag-chip tag-{k}" data-tagtype="{k}" data-tagval="{v}" '
        f'onclick="filterByTag(event, this)" title="Click to filter to {k}: {v}">{v}</span>'
        for k, v in visual_tags.items() if v
    )
    cards_html.append(f"""
    <div class="card" data-idx="{i}" data-adset="{adset_short}" data-tier="{label}" data-name="{r['name'].lower()}" data-spend="{r['spend']}" data-ctr="{r['ctr']}" data-cpc="{r['cpc']}" data-msg="{r['msg']}" data-lpv="{r['lpv']}" data-clicks="{r['clicks']}" data-format="{visual_tags.get('format', '')}" data-product="{visual_tags.get('product', '')}" data-color="{visual_tags.get('color', '')}" data-style="{visual_tags.get('style', '')}">
      <div class="imgwrap">
        {img_tag}
        <span class="badge" style="background:{color}">{label}</span>
        <button class="mark-btn" type="button" onclick="toggleMark(event, this)" aria-label="Mark as keep">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
        </button>
      </div>
      <div class="info">
        <div class="adset">{adset_short}</div>
        <div class="name">{r['name']}</div>
        <div class="msg">{r['message'][:120]}</div>

        <div class="key-stats">
          <div class="key tone-{ctr_tone(r['ctr'])}">
            <div class="key-num">{r['ctr']:.2f}%</div>
            <div class="key-lbl">CTR</div>
            <div class="key-desc">click-through rate</div>
          </div>
          <div class="key tone-{cpc_tone(r['cpc'])}">
            <div class="key-num">P{r['cpc']:.2f}</div>
            <div class="key-lbl">CPC</div>
            <div class="key-desc">cost per click</div>
          </div>
          <div class="key tone-{msg_tone(r['msg'])}">
            <div class="key-num">{r['msg']}</div>
            <div class="key-lbl">MSG</div>
            <div class="key-desc">messenger leads</div>
          </div>
        </div>

        <div class="context-stats">
          <div><span class="lbl">Spend</span><span class="val">P{r['spend']:.0f}</span></div>
          <div><span class="lbl">Impr</span><span class="val">{r['impr']:,}</span></div>
          <div><span class="lbl">Clicks</span><span class="val">{r['clicks']}</span></div>
          <div><span class="lbl">LPV</span><span class="val">{r['lpv']}</span></div>
          <div><span class="lbl">Purch</span><span class="val">{r['purch']}</span></div>
        </div>

        <div class="tag-chips">{tag_chips}</div>

        <div class="analysis">
          <div class="analysis-verdict">{verdict}</div>
          <div class="analysis-why"><strong>Why:</strong> {why}</div>
          <div class="analysis-opp"><strong>Opportunity:</strong> {opportunity}</div>
        </div>
      </div>
    </div>
    """)

# ============ Executive summary uses values defined above ============


def summary_brief():
    items = []
    cpa = real_sales['total_gross'] / real_sales['total_orders'] if real_sales['total_orders'] else 0
    cost_per_real_order = total_spend / real_sales['total_orders'] if real_sales['total_orders'] else 0
    items.append(f"<strong>{real_sales['total_orders']} real orders ({real_sales['total_units']} units, P{real_sales['total_gross']:,.0f} gross)</strong> from <strong>P{total_spend:,.0f}</strong> ad spend over 20 days -- {real_sales['delivered_orders']} delivered ({real_sales['delivered_units']}u) + {real_sales['pending_orders']} pending ({real_sales['pending_units']}u). Cost per closed order: <strong>P{cost_per_real_order:,.0f}</strong>.")
    items.append(f"Meta's pixel only sees <strong>{total_purch} purchase{'s' if total_purch != 1 else ''}</strong> because the Pixel went live 2026-05-20 -- 4 of the 7 orders predate it, and Meta's 7d-click attribution misses the rest.")
    items.append(f"<strong>{winning_adset}</strong> is the clear winner -- CTR {win['ctr']:.2f}% / CPC P{win['cpc']:.2f} / {win['msg']} msg vs {losing_adset} at CTR {lose['ctr']:.2f}% / CPC P{lose['cpc']:.2f} / {lose['msg']} msg.")
    items.append(f"Top creative: <strong>{top3[0]['name']}</strong> -- CTR {top3[0]['ctr']:.2f}%, CPC P{top3[0]['cpc']:.2f}, {top3[0]['msg']} msg.")
    items.append(f"Suggested action: build one consolidated adset with the top 3-4 creatives, pause both current adsets, bump daily budget P140 -> P200-250.")
    return '<ul class="brief-list">' + ''.join(f'<li>{x}</li>' for x in items) + '</ul>'


def summary_detailed():
    parts = []
    cost_per_real_order = total_spend / real_sales['total_orders'] if real_sales['total_orders'] else 0
    roas = real_sales['total_gross'] / total_spend if total_spend else 0
    parts.append(f"""
    <p>Over the past <strong>20 days</strong> (campaign live since 2026-05-06), the DuberyMNL Traffic campaign has spent <strong>P{total_spend:,.0f}</strong> across two adsets running at P140/day combined. The campaign produced <strong>{total_impr:,} impressions</strong>, <strong>{total_clicks:,} clicks</strong> at CTR {overall_ctr:.2f}% / CPC P{overall_cpc:.2f}, <strong>{total_lpv} landing-page views</strong>, and <strong>{total_msg} Messenger leads</strong>.</p>
    """)
    parts.append(f"""
    <p><strong>Real sales (from Orders sheet, not Meta Pixel):</strong> <strong>{real_sales['total_orders']} orders / {real_sales['total_units']} units / P{real_sales['total_gross']:,.0f} gross</strong> since campaign launch. {real_sales['delivered_orders']} delivered ({real_sales['delivered_units']} units, P{real_sales['delivered_gross']:,.0f}) + {real_sales['pending_orders']} pending ({real_sales['pending_units']} units, P{real_sales['pending_gross']:,.0f}). Cost per closed order: <strong>P{cost_per_real_order:,.0f}</strong>. Gross ROAS: <strong>{roas:.2f}x</strong>.</p>
    <p><strong>Why Meta only sees {total_purch}:</strong> Pixel went live 2026-05-20 -- 4 of the 7 orders predate it (Mark 5/14, Sean 5/15, Jeff 5/16, plus 1 cancelled). Of the 4 post-Pixel orders, Meta credits only {total_purch} because the rest lacked a recent ad-click cookie within the 7-day attribution window. Trust the Orders sheet for real revenue; trust Meta's number only for the directional "is the Pixel firing" check.</p>
    """)
    parts.append(f"""
    <p><strong>Winning adset:</strong> {winning_adset} is meaningfully ahead -- CTR {win['ctr']:.2f}% vs {lose['ctr']:.2f}%, CPC P{win['cpc']:.2f} vs P{lose['cpc']:.2f}, and {win['msg']} Messenger leads vs {lose['msg']}. {losing_adset} has the top UGC creative however, so don't kill the whole adset blindly.</p>
    """)
    top_lines = ''.join(f'<li><strong>{r["name"]}</strong> -- CTR {r["ctr"]:.2f}%, CPC P{r["cpc"]:.2f}, {r["msg"]} msg, {r["purch"]} purch ({r["adset"].replace("Traffic - ","").replace(" - May2026","")})</li>' for r in top3)
    bot_lines = ''.join(f'<li><strong>{r["name"]}</strong> -- CTR {r["ctr"]:.2f}%, CPC P{r["cpc"]:.2f}, {r["msg"]} msg ({r["adset"].replace("Traffic - ","").replace(" - May2026","")})</li>' for r in bottom3)
    parts.append(f"""
    <p><strong>Top 3 creatives to keep:</strong></p>
    <ul class="detail-list">{top_lines}</ul>
    """)
    parts.append(f"""
    <p><strong>Bottom 3 to cut or rework:</strong></p>
    <ul class="detail-list">{bot_lines}</ul>
    """)
    parts.append(f"""
    <p><strong>Recommended action:</strong> Build a new "Traffic - Winners" adset containing the top 3-4 creatives above. Pause both current adsets the same day to avoid double-paying. Bump daily budget from P140 to P200-250 -- modest enough that the new adset can exit learning phase cleanly (Meta needs ~50 conversion events to stabilize). Reassess after 5-7 days.</p>
    """)
    return ''.join(parts)


adset_html = []
for name, a in adsets.items():
    adset_html.append(f"""
    <div class="adset-card">
      <h3>{name}</h3>
      <div class="key-stats">
        <div class="key tone-{ctr_tone(a['ctr'])}">
          <div class="key-num">{a['ctr']:.2f}%</div>
          <div class="key-lbl">CTR</div>
        </div>
        <div class="key tone-{cpc_tone(a['cpc'])}">
          <div class="key-num">P{a['cpc']:.2f}</div>
          <div class="key-lbl">CPC</div>
        </div>
        <div class="key tone-{msg_tone(a['msg'])}">
          <div class="key-num">{a['msg']}</div>
          <div class="key-lbl">MSG</div>
        </div>
      </div>
      <div class="context-stats">
        <div><span class="lbl">Spend</span><span class="val">P{a['spend']:.0f}</span></div>
        <div><span class="lbl">Clicks</span><span class="val">{a['clicks']}</span></div>
        <div><span class="lbl">LPV</span><span class="val">{a['lpv']}</span></div>
        <div><span class="lbl">Purch</span><span class="val">{a['purch']}</span></div>
      </div>
    </div>
    """)

html = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>Dubery Ads - 30d Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #f7f5f0;
    --surface: #ffffff;
    --surface-2: #f0ede6;
    --border: #e5ddd3;
    --text: #1a1613;
    --muted: #6b6560;
    --accent: #e07a3a;
    --accent-dim: rgba(224, 122, 58, 0.10);
    --ok: #2d8a4e;
    --warn: #b8860b;
    --bad: #d93025;
    --gray: #9e9890;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
  }}
  * {{ box-sizing: border-box; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
    margin: 0; padding: 0;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
  }}
  .container {{ max-width: 1280px; margin: 0 auto; padding: 56px 48px 80px; }}

  /* Header */
  h1 {{ margin:0 0 8px; font-size: 28px; font-weight: 700; letter-spacing:-0.01em; }}
  .meta {{ color: var(--muted); margin-bottom: 32px; font-size: 13px; }}

  /* Executive summary */
  .summary {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 10px;
    padding: 28px 32px;
    margin-bottom: 40px;
    box-shadow: var(--shadow-sm);
  }}
  .summary-head {{
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 18px;
  }}
  .summary-title {{ font-size: 13px; font-weight: 700; color: var(--accent); letter-spacing: 0.08em; text-transform: uppercase; }}
  .toggle-group {{ display: flex; gap: 0; background: var(--surface-2); border-radius: 6px; padding: 3px; }}
  .toggle-btn {{
    border: none; background: transparent; color: var(--muted);
    padding: 5px 14px; border-radius: 4px; cursor: pointer;
    font-size: 12px; font-weight: 600; font-family: inherit;
    transition: all 0.15s;
  }}
  .toggle-btn.active {{ background: var(--surface); color: var(--text); box-shadow: var(--shadow-sm); }}
  .summary-body {{ font-size: 14px; color: var(--text); }}
  .summary-body p {{ margin: 0 0 12px; }}
  .summary-body p:last-child {{ margin-bottom: 0; }}
  .summary-body strong {{ color: var(--text); font-weight: 600; }}
  .brief-list, .detail-list {{ list-style: none; padding: 0; margin: 0; }}
  .brief-list li {{ position: relative; padding: 10px 0 10px 24px; border-bottom: 1px solid var(--border); }}
  .brief-list li:last-child {{ border-bottom: none; }}
  .brief-list li::before {{
    content: ''; position: absolute; left: 4px; top: 18px;
    width: 6px; height: 6px; border-radius: 50%; background: var(--accent);
  }}
  .detail-list {{ margin: 8px 0 16px; }}
  .detail-list li {{
    padding: 8px 14px; margin-bottom: 6px;
    background: var(--surface-2); border-radius: 6px; font-size: 13px;
  }}

  /* Real sales row */
  .sales-row {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-bottom: 40px;
  }}
  .sales-tile {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent);
    border-radius: 10px;
    padding: 16px 18px;
    box-shadow: var(--shadow-sm);
  }}
  .sales-tile.sales-meta-tile {{ border-top-color: var(--gray); background: var(--surface-2); }}
  .sales-lbl {{ font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; margin-bottom: 6px; }}
  .sales-num {{ font-size: 26px; font-weight: 700; color: var(--text); line-height: 1.1; margin-bottom: 4px; }}
  .sales-num-dim {{ color: var(--gray); }}
  .sales-sub {{ font-size: 11px; color: var(--muted); line-height: 1.4; }}

  /* KPI panel */
  .kpi-row {{
    display: grid;
    gap: 10px;
  }}
  .kpi-row.kpi-primary {{
    grid-template-columns: repeat(5, 1fr);
    margin-bottom: 16px;
  }}
  .kpi-row.kpi-secondary {{
    grid-template-columns: repeat(2, 1fr);
    margin-bottom: 32px;
    max-width: 520px;
  }}
  .kpi-secondary-header {{
    font-size: 10px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
    margin-bottom: 8px;
  }}
  .kpi-secondary-header span {{
    font-weight: 400;
    text-transform: none;
    letter-spacing: 0;
    font-style: italic;
    color: var(--gray);
  }}
  .kpi-tile-dim {{ opacity: 0.78; }}
  .kpi-tile {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--gray);
    border-radius: 8px;
    padding: 14px 16px;
    box-shadow: var(--shadow-sm);
  }}
  .kpi-tile.tone-good {{ border-left-color: var(--ok); }}
  .kpi-tile.tone-mid {{ border-left-color: var(--warn); }}
  .kpi-tile.tone-bad {{ border-left-color: var(--bad); }}
  .kpi-tile.tone-na {{ border-left-color: var(--gray); opacity: 0.7; }}
  .kpi-lbl {{ font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; margin-bottom: 6px; }}
  .kpi-value {{ font-size: 22px; font-weight: 700; color: var(--text); line-height: 1.1; margin-bottom: 4px; }}
  .kpi-tile.tone-good .kpi-value {{ color: var(--ok); }}
  .kpi-tile.tone-mid .kpi-value {{ color: var(--warn); }}
  .kpi-tile.tone-bad .kpi-value {{ color: var(--bad); }}
  .kpi-target {{ font-size: 10px; color: var(--muted); font-weight: 600; margin-bottom: 2px; }}
  .kpi-desc {{ font-size: 10px; color: var(--gray); font-style: italic; }}

  /* Pattern breakdown */
  .pattern-howto {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 18px;
    font-size: 12.5px;
    line-height: 1.6;
    color: var(--text);
  }}
  .pattern-howto strong {{ color: var(--text); }}
  .pattern-howto ul {{ margin: 8px 0 0 0; padding-left: 18px; }}
  .pattern-howto li {{ margin-bottom: 4px; color: var(--muted); }}
  .pattern-howto li strong {{ color: var(--text); font-weight: 600; }}

  .pattern-interp {{
    font-size: 12px;
    color: var(--text);
    line-height: 1.55;
    margin-bottom: 14px;
    padding-bottom: 12px;
    border-bottom: 1px dashed var(--border);
  }}
  .pattern-interp strong {{ color: var(--accent); }}

  tr.small-sample td {{ color: var(--muted); }}
  tr.small-sample .star {{ color: var(--warn); font-weight: 700; margin-left: 3px; }}

  tr.clickable-row {{ cursor: pointer; transition: background 0.1s; }}
  tr.clickable-row:hover td {{ background: var(--accent-dim); color: var(--text); }}
  tr.clickable-row:hover td:first-child {{ color: var(--accent); font-weight: 600; }}

  /* Tag filter bar (above toolbar) */
  .tag-filter-bar {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    padding: 12px 16px;
    background: var(--accent-dim);
    border: 1px solid var(--accent);
    border-radius: 8px;
  }}
  .tfb-label {{
    font-size: 11px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
  }}
  .tfb-chip {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--accent);
    color: white;
    padding: 6px 8px 6px 12px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
  }}
  .tfb-type {{
    font-size: 10px;
    text-transform: uppercase;
    opacity: 0.85;
    letter-spacing: 0.05em;
  }}
  .tfb-type::after {{ content: ':'; margin-left: 1px; }}
  .tfb-value {{ font-weight: 700; }}
  .tfb-clear {{
    background: rgba(255,255,255,0.2);
    border: none;
    color: white;
    width: 20px; height: 20px;
    border-radius: 50%;
    font-size: 14px;
    line-height: 1;
    cursor: pointer;
    padding: 0;
    display: flex; align-items: center; justify-content: center;
  }}
  .tfb-clear:hover {{ background: rgba(255,255,255,0.35); }}

  /* Tag chip on cards becomes interactive */
  .tag-chip {{ cursor: pointer; transition: opacity 0.1s; }}
  .tag-chip:hover {{ opacity: 0.75; outline: 2px solid var(--accent); outline-offset: 1px; }}

  .patterns-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-bottom: 32px;
  }}
  .pattern-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: var(--shadow-sm);
  }}
  .pattern-card h3 {{
    margin: 0 0 12px;
    font-size: 13px;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
  }}
  .pattern-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }}
  .pattern-table th {{
    text-align: left;
    color: var(--muted);
    font-weight: 600;
    text-transform: uppercase;
    font-size: 10px;
    letter-spacing: 0.06em;
    padding: 6px 8px;
    border-bottom: 1px solid var(--border);
  }}
  .pattern-table td {{
    padding: 7px 8px;
    border-bottom: 1px solid var(--surface-2);
    color: var(--text);
  }}
  .pattern-table tr:last-child td {{ border-bottom: none; }}
  .pattern-table tr:first-child td {{ font-weight: 600; }}
  .pattern-table td.num {{ font-variant-numeric: tabular-nums; }}
  .pattern-takeaway {{
    margin-top: 12px;
    padding: 10px 12px;
    background: var(--surface-2);
    border-left: 3px solid var(--accent);
    border-radius: 4px;
    font-size: 12px;
    color: var(--text);
    line-height: 1.5;
  }}
  .pattern-takeaway strong {{ color: var(--accent); }}

  /* Visual tag chips on cards */
  .tag-chips {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 4px;
  }}
  .tag-chip {{
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 10px;
    background: var(--surface-2);
    color: var(--muted);
    font-weight: 600;
    letter-spacing: 0.02em;
    border: 1px solid var(--border);
  }}
  .tag-chip.tag-format {{ background: var(--accent-dim); color: var(--accent); border-color: transparent; }}
  .tag-chip.tag-product {{ background: #e8f4ec; color: var(--ok); border-color: transparent; }}

  /* Per-card analysis */
  .analysis {{
    margin-top: 14px;
    padding: 12px 14px;
    background: var(--surface-2);
    border-radius: 8px;
    border-left: 3px solid var(--accent);
    font-size: 11.5px;
    line-height: 1.55;
  }}
  .analysis-verdict {{
    font-weight: 700;
    color: var(--text);
    font-size: 12px;
    margin-bottom: 6px;
    letter-spacing: 0.01em;
  }}
  .analysis-why {{ color: var(--muted); margin-bottom: 6px; }}
  .analysis-why strong {{ color: var(--text); }}
  .analysis-opp {{ color: var(--text); }}
  .analysis-opp strong {{ color: var(--accent); }}

  /* Section headings */
  .section-head {{ margin: 48px 0 18px; }}
  .section-head h2 {{ margin: 0 0 4px; font-size: 16px; font-weight: 700; color: var(--text); letter-spacing: 0.02em; }}
  .section-head p {{ margin: 0; color: var(--muted); font-size: 12px; }}

  /* Metric guide */
  .metric-guide {{
    display:grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 22px 26px;
    margin-bottom: 32px;
    box-shadow: var(--shadow-sm);
  }}
  .metric-guide-item .mg-lbl {{ font-size: 10px; color: var(--accent); text-transform:uppercase; letter-spacing:0.1em; font-weight:700; margin-bottom: 4px; }}
  .metric-guide-item .mg-name {{ font-size: 14px; color: var(--text); font-weight: 600; margin-bottom: 4px; }}
  .metric-guide-item .mg-desc {{ font-size: 12px; color: var(--muted); }}

  /* Legend */
  .legend {{ display:flex; flex-wrap:wrap; gap:20px; margin-bottom: 24px; font-size:12px; color: var(--muted); }}
  .legend-item {{ display:flex; align-items:center; gap:8px; }}
  .legend-chip {{ width:10px; height:10px; border-radius:2px; }}
  .legend-rule {{ color: var(--gray); }}
  .legend-item strong {{ color: var(--text); }}

  /* Adset summary cards */
  .adset-row {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  .adset-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 24px; box-shadow: var(--shadow-sm); }}
  .adset-card h3 {{ margin:0 0 18px; font-size:14px; color: var(--text); font-weight:600; }}

  /* Card grid */
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:24px; }}
  .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; overflow:hidden; display:flex; flex-direction:column; box-shadow: var(--shadow-sm); transition: transform 0.15s, box-shadow 0.15s; }}
  .card:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-md); }}
  .imgwrap {{ position:relative; aspect-ratio:1; background: var(--surface-2); }}
  .imgwrap img {{ width:100%; height:100%; object-fit:contain; }}
  .noimg {{ display:flex; align-items:center; justify-content:center; height:100%; color: var(--gray); font-size:12px; }}
  .badge {{ position:absolute; top:10px; left:10px; padding:5px 12px; font-size:10px; font-weight:700; color:white; border-radius:4px; letter-spacing:0.08em; }}

  .info {{ padding:18px; flex:1; display:flex; flex-direction:column; gap:14px; }}
  .adset {{ font-size:10px; color: var(--accent); text-transform:uppercase; letter-spacing:0.08em; font-weight:600; }}
  .name {{ font-size:12px; color: var(--text); word-break:break-word; font-family: ui-monospace, 'SF Mono', monospace; }}
  .msg {{ font-size:12px; color: var(--muted); font-style:italic; line-height:1.5; min-height:34px; }}

  /* Key stats */
  .key-stats {{
    display:grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin: 4px 0;
  }}
  .key {{
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-top: 3px solid var(--gray);
    border-radius: 6px;
    padding: 10px 8px;
    text-align: center;
  }}
  .key-num {{ font-size: 18px; font-weight: 700; color: var(--text); line-height: 1.1; margin-bottom: 4px; }}
  .key-lbl {{ font-size: 10px; color: var(--text); font-weight: 700; letter-spacing: 0.08em; }}
  .key-desc {{ font-size: 9px; color: var(--muted); margin-top: 2px; }}

  .key.tone-good {{ border-top-color: var(--ok); }}
  .key.tone-good .key-num {{ color: var(--ok); }}
  .key.tone-mid {{ border-top-color: var(--warn); }}
  .key.tone-mid .key-num {{ color: var(--warn); }}
  .key.tone-bad {{ border-top-color: var(--bad); }}
  .key.tone-bad .key-num {{ color: var(--bad); }}

  /* Context stats */
  .context-stats {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 6px;
    padding-top: 14px;
    border-top: 1px solid var(--border);
    margin-top: auto;
  }}
  .context-stats > div {{ display:flex; flex-direction:column; gap:2px; }}
  .lbl {{ font-size:9px; color: var(--muted); text-transform:uppercase; letter-spacing:0.05em; font-weight:600; }}
  .val {{ font-size:12px; color: var(--text); font-weight:600; }}

  .adset-card .context-stats {{ grid-template-columns: repeat(4, 1fr); padding-top:18px; margin-top:18px; }}
  .adset-card .context-stats .val {{ font-size:14px; }}

  /* Toolbar */
  .toolbar {{
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 24px;
    box-shadow: var(--shadow-sm);
    align-items: flex-end;
  }}
  .tool-group {{ display: flex; flex-direction: column; gap: 4px; min-width: 140px; }}
  .tool-group.tool-marked {{ margin-left: auto; }}
  .tool-group label {{ font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; }}
  .tool-group select, .tool-group input, .tool-group button {{
    font-family: inherit;
    font-size: 13px;
    color: var(--text);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 7px 10px;
    outline: none;
    cursor: pointer;
  }}
  .tool-group input {{ cursor: text; }}
  .tool-group select:focus, .tool-group input:focus {{ border-color: var(--accent); }}
  .tool-group button {{ font-weight: 600; }}
  .tool-group button:hover {{ background: var(--surface-2); }}
  .tool-group button.active {{ background: var(--accent); color: white; border-color: var(--accent); }}

  /* Mark button on card */
  .mark-btn {{
    position: absolute; top: 10px; right: 10px;
    width: 28px; height: 28px;
    background: rgba(255,255,255,0.94);
    border: 1px solid var(--border);
    border-radius: 50%;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    color: var(--gray);
    transition: all 0.15s;
  }}
  .mark-btn:hover {{ color: var(--accent); border-color: var(--accent); }}
  .card.marked {{
    border-color: var(--accent);
    box-shadow: 0 0 0 2px var(--accent-dim), var(--shadow-sm);
  }}
  .card.marked .mark-btn {{ background: var(--accent); color: white; border-color: var(--accent); }}

  /* Empty state */
  .empty-state {{
    text-align: center;
    padding: 60px 20px;
    color: var(--muted);
    background: var(--surface);
    border: 1px dashed var(--border);
    border-radius: 10px;
  }}

  /* Picks tray */
  .picks-tray {{
    position: fixed;
    bottom: 24px;
    right: 24px;
    width: 360px;
    max-height: 60vh;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: var(--shadow-lg, 0 8px 30px rgba(0,0,0,0.15));
    z-index: 50;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  .tray-head {{
    padding: 14px 16px;
    background: var(--accent);
    color: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }}
  .tray-head strong {{ font-size: 18px; }}
  .tray-actions {{ display: flex; gap: 6px; }}
  .tray-actions button {{
    font-family: inherit;
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.3);
    color: white;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
  }}
  .tray-actions button:hover {{ background: rgba(255,255,255,0.28); }}
  .tray-actions .tray-clear {{ background: rgba(0,0,0,0.18); }}
  .tray-list {{
    padding: 8px 12px 12px;
    overflow-y: auto;
    max-height: 320px;
  }}
  .tray-item {{
    font-size: 12px;
    padding: 6px 10px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    font-family: ui-monospace, monospace;
    word-break: break-all;
  }}
  .tray-item:last-child {{ border-bottom: none; }}
  .tray-item .tray-tier {{ color: var(--muted); font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em; margin-left: 6px; }}

  /* Responsive */
  @media (max-width: 768px) {{
    .toolbar {{ flex-direction: column; align-items: stretch; }}
    .tool-group {{ min-width: 0; }}
    .tool-group.tool-marked {{ margin-left: 0; }}
    .picks-tray {{ width: calc(100vw - 32px); right: 16px; bottom: 16px; }}
    .container {{ padding: 32px 20px 56px; }}
    .summary {{ padding: 20px; }}
    .summary-head {{ flex-direction: column; align-items: flex-start; gap: 12px; }}
    .sales-row {{ grid-template-columns: repeat(2, 1fr); }}
    .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
    .patterns-grid {{ grid-template-columns: 1fr; }}
    .adset-row {{ grid-template-columns: 1fr; }}
    .metric-guide {{ grid-template-columns: 1fr; gap: 16px; padding: 18px; }}
    .grid {{ grid-template-columns: 1fr; }}
  }}
</style></head><body>
<div class="container">
  <h1>Dubery Ads -- 30d Report</h1>
  <div class="meta">Apr 26 - May 26 &nbsp;&middot;&nbsp; campaign live since May 6 (20 days) &nbsp;&middot;&nbsp; P140/day combined &nbsp;&middot;&nbsp; sorted by spend</div>

  <div class="summary">
    <div class="summary-head">
      <div class="summary-title">Executive Summary</div>
      <div class="toggle-group">
        <button class="toggle-btn active" data-mode="brief" onclick="setMode('brief')">Brief</button>
        <button class="toggle-btn" data-mode="detailed" onclick="setMode('detailed')">Detailed</button>
      </div>
    </div>
    <div class="summary-body" id="summary-brief">{summary_brief()}</div>
    <div class="summary-body" id="summary-detailed" style="display:none">{summary_detailed()}</div>
  </div>

  <div class="sales-row">
    <div class="sales-tile">
      <div class="sales-lbl">Real orders</div>
      <div class="sales-num">{real_sales['total_orders']}</div>
      <div class="sales-sub">{real_sales['delivered_orders']} delivered &middot; {real_sales['pending_orders']} pending</div>
    </div>
    <div class="sales-tile">
      <div class="sales-lbl">Units sold</div>
      <div class="sales-num">{real_sales['total_units']}</div>
      <div class="sales-sub">{real_sales['delivered_units']} shipped &middot; {real_sales['pending_units']} to ship</div>
    </div>
    <div class="sales-tile">
      <div class="sales-lbl">Gross revenue</div>
      <div class="sales-num">P{real_sales['total_gross']:,.0f}</div>
      <div class="sales-sub">P{real_sales['delivered_gross']:,.0f} collected &middot; P{real_sales['pending_gross']:,.0f} pending</div>
    </div>
    <div class="sales-tile">
      <div class="sales-lbl">Cost per order</div>
      <div class="sales-num">P{(total_spend / real_sales['total_orders'] if real_sales['total_orders'] else 0):,.0f}</div>
      <div class="sales-sub">vs P{total_spend:,.0f} ad spend &middot; {(real_sales['total_gross']/total_spend if total_spend else 0):.2f}x ROAS</div>
    </div>
    <div class="sales-tile sales-meta-tile">
      <div class="sales-lbl">Meta says</div>
      <div class="sales-num sales-num-dim">{total_purch}</div>
      <div class="sales-sub">Pixel-attributed only (live since 5/20)</div>
    </div>
  </div>

  <div class="section-head" style="margin-top: 8px;">
    <h2>Campaign KPIs</h2>
    <p>Campaign objective: <strong>Traffic</strong> -- Meta optimizes for clicks &rarr; LPVs. Status colors: green = hitting target, amber = within ~25-30% of target, red = below target.</p>
  </div>
  <div class="kpi-row kpi-primary">
    {''.join(f'''
    <div class="kpi-tile tone-{k['status']}">
      <div class="kpi-lbl">{k['label']}</div>
      <div class="kpi-value">{k['value']}</div>
      <div class="kpi-target">target {k['target']}</div>
      <div class="kpi-desc">{k['desc']}</div>
    </div>
    ''' for k in KPI_PANEL_PRIMARY)}
  </div>

  <div class="kpi-secondary-header">Secondary signals &middot; <span>Msg metrics for reference -- only primary for Messages-objective campaigns</span></div>
  <div class="kpi-row kpi-secondary">
    {''.join(f'''
    <div class="kpi-tile kpi-tile-dim tone-{k['status']}">
      <div class="kpi-lbl">{k['label']}</div>
      <div class="kpi-value">{k['value']}</div>
      <div class="kpi-target">target {k['target']}</div>
      <div class="kpi-desc">{k['desc']}</div>
    </div>
    ''' for k in KPI_PANEL_SECONDARY)}
  </div>

  <div class="metric-guide">
    <div class="metric-guide-item">
      <div class="mg-lbl">CTR</div>
      <div class="mg-name">Click-through rate</div>
      <div class="mg-desc">% of people who saw the ad and clicked. Headline performance signal. Target: &gt; 2.0%</div>
    </div>
    <div class="metric-guide-item">
      <div class="mg-lbl">CPC</div>
      <div class="mg-name">Cost per click</div>
      <div class="mg-desc">What you pay for each click. Lower = more efficient. Target: &lt; P1.30</div>
    </div>
    <div class="metric-guide-item">
      <div class="mg-lbl">MSG</div>
      <div class="mg-name">Messenger leads</div>
      <div class="mg-desc">Conversations started from the ad. The real conversion signal beyond clicks.</div>
    </div>
  </div>

  <div class="legend">
    <div class="legend-item"><span class="legend-chip" style="background:var(--ok)"></span><strong>WINNER</strong><span class="legend-rule">CTR&ge;2.3% + CPC&le;P1.20 + LPV-rate&ge;40%</span></div>
    <div class="legend-item"><span class="legend-chip" style="background:var(--accent)"></span><strong>KEEP</strong><span class="legend-rule">CTR&ge;2.0%, CPC&le;P1.30</span></div>
    <div class="legend-item"><span class="legend-chip" style="background:var(--gray)"></span><strong>OK</strong><span class="legend-rule">middle pack</span></div>
    <div class="legend-item"><span class="legend-chip" style="background:var(--bad)"></span><strong>CUT</strong><span class="legend-rule">CTR&lt;1.5% or CPC&gt;P2.00</span></div>
  </div>

  <div class="section-head">
    <h2>Adset Summary</h2>
    <p>Headline numbers per adset over the last 30 days.</p>
  </div>
  <div class="adset-row">
{''.join(adset_html)}
  </div>

  <div class="section-head">
    <h2>Creative Pattern Breakdown</h2>
    <p>Performance aggregated by visual tag, derived from ad naming conventions. Reveals which formats / products / colorways are doing the work.</p>
  </div>

  <div class="pattern-howto">
    <strong>How to read these tables.</strong> Each row groups your ads by a visual attribute (Format / Product / etc.) and averages the metrics across that group. Columns mean:
    <ul>
      <li><strong>#</strong> -- how many ads are in that group. <strong>Rows with fewer than 3 ads are marked with *</strong> -- those are small samples, not proven patterns.</li>
      <li><strong>CTR</strong> -- click-through rate (clicks / impressions). Higher is better. Target &ge; 2.0%.</li>
      <li><strong>CPC</strong> -- cost per click. Lower is better. Target &le; P1.30.</li>
      <li><strong>LPV-rate</strong> -- of the people who clicked, what % actually landed on the site. Higher is better. Target &ge; 40%. (This replaces Msg in the table view since the campaign objective is Traffic; Msg is still per ad card.)</li>
    </ul>
    The orange callout below each table is the plain-English reading -- what's actually winning and what's just small-sample noise.
  </div>

  <div class="patterns-grid">
    {''.join(f'''
    <div class="pattern-card">
      <h3>By {cat_label}</h3>
      <div class="pattern-interp">{pattern_interpretation(PATTERN_GROUPS[cat_key], cat_label.lower())}</div>
      <table class="pattern-table">
        <thead>
          <tr><th>Tag</th><th>#</th><th>CTR</th><th>CPC</th><th>LPV-rate</th></tr>
        </thead>
        <tbody>
          {''.join(f"<tr class='clickable-row {'small-sample' if g['count'] < 3 else ''}' data-tagtype='{cat_key}' data-tagval='{g['tag']}' onclick='filterByTag(event, this)' title='Click to filter the ad grid to this tag'><td>{g['tag']}{'<span class=star>*</span>' if g['count'] < 3 else ''}</td><td>{g['count']}</td><td class='num'>{g['ctr']:.2f}%</td><td class='num'>P{g['cpc']:.2f}</td><td class='num'>{g['lpv_rate']:.0f}%</td></tr>" for g in PATTERN_GROUPS[cat_key])}
        </tbody>
      </table>
      <div class="pattern-takeaway">{pattern_takeaway(PATTERN_GROUPS[cat_key], cat_label.lower())}</div>
    </div>
    ''' for cat_key, cat_label in [('format', 'Format'), ('product', 'Product'), ('color', 'Colorway'), ('style', 'Style')])}
  </div>

  <div class="section-head" id="individual-ads">
    <h2>Individual Ads</h2>
    <p>{len(rows)} ads with spend &gt; P5. Click <strong>Mark</strong> on a card to add it to your keep-list. Click any tag chip on a card -- or any row in the Creative Pattern tables above -- to filter this grid by that tag.</p>
  </div>

  <div class="tag-filter-bar" id="tag-filter-bar" style="display:none">
    <span class="tfb-label">Filtered by</span>
    <span class="tfb-chip" id="tag-filter-chip">
      <span class="tfb-type" id="tfb-type"></span>
      <span class="tfb-value" id="tfb-value"></span>
      <button type="button" class="tfb-clear" onclick="clearTagFilter()" aria-label="Clear filter">&times;</button>
    </span>
  </div>

  <div class="toolbar">
    <div class="tool-group">
      <label>Sort</label>
      <select id="sort-by" onchange="applyFilters()">
        <option value="spend-desc">Spend (high to low)</option>
        <option value="spend-asc">Spend (low to high)</option>
        <option value="ctr-desc">CTR (high to low)</option>
        <option value="cpc-asc">CPC (low to high)</option>
        <option value="msg-desc">Messenger leads (most first)</option>
        <option value="lpv-desc">Landing-page views (most first)</option>
        <option value="name-asc">Name (A-Z)</option>
      </select>
    </div>
    <div class="tool-group">
      <label>Adset</label>
      <select id="filter-adset" onchange="applyFilters()">
        <option value="">All adsets</option>
        <option value="Brand Graphics">Brand Graphics</option>
        <option value="Bespoke UGC">Bespoke UGC</option>
      </select>
    </div>
    <div class="tool-group">
      <label>Tier</label>
      <select id="filter-tier" onchange="applyFilters()">
        <option value="">All tiers</option>
        <option value="WINNER">WINNER only</option>
        <option value="KEEP">KEEP only</option>
        <option value="WINNER+KEEP">WINNER + KEEP</option>
        <option value="OK">OK</option>
        <option value="CUT">CUT</option>
      </select>
    </div>
    <div class="tool-group">
      <label>Search</label>
      <input id="search-box" type="text" placeholder="Filter by name..." oninput="applyFilters()">
    </div>
    <div class="tool-group tool-marked">
      <label>Marked</label>
      <button id="show-marked-btn" type="button" onclick="toggleMarkedOnly()">Show marked only</button>
    </div>
  </div>

  <div class="grid" id="grid">
{''.join(cards_html)}
  </div>

  <div class="empty-state" id="empty-state" style="display:none">
    No ads match the current filters.
  </div>
</div>

<div class="picks-tray" id="picks-tray" style="display:none">
  <div class="tray-head">
    <div>
      <strong id="tray-count">0</strong> ads marked for keep-list
    </div>
    <div class="tray-actions">
      <button type="button" onclick="copyPicks()">Copy names</button>
      <button type="button" onclick="exportPicks()">Export JSON</button>
      <button type="button" onclick="clearPicks()" class="tray-clear">Clear</button>
    </div>
  </div>
  <div class="tray-list" id="tray-list"></div>
</div>
<script>
  function setMode(m) {{
    document.getElementById('summary-brief').style.display = m === 'brief' ? '' : 'none';
    document.getElementById('summary-detailed').style.display = m === 'detailed' ? '' : 'none';
    document.querySelectorAll('.toggle-btn').forEach(b => {{
      b.classList.toggle('active', b.dataset.mode === m);
    }});
  }}

  // ===== Marks (localStorage) =====
  const MARKS_KEY = 'dubery_ad_marks_v1';
  let marks = new Set(JSON.parse(localStorage.getItem(MARKS_KEY) || '[]'));
  let showMarkedOnly = false;

  function saveMarks() {{ localStorage.setItem(MARKS_KEY, JSON.stringify([...marks])); }}

  function toggleMark(ev, btn) {{
    ev.stopPropagation();
    const card = btn.closest('.card');
    const name = card.querySelector('.name').textContent;
    if (marks.has(name)) {{ marks.delete(name); card.classList.remove('marked'); }}
    else {{ marks.add(name); card.classList.add('marked'); }}
    saveMarks();
    renderTray();
    if (showMarkedOnly) applyFilters();
  }}

  function clearPicks() {{
    if (!confirm('Clear all marks?')) return;
    marks.clear(); saveMarks();
    document.querySelectorAll('.card.marked').forEach(c => c.classList.remove('marked'));
    renderTray();
    if (showMarkedOnly) applyFilters();
  }}

  function copyPicks() {{
    const names = [...document.querySelectorAll('.card.marked')].map(c => c.querySelector('.name').textContent);
    if (!names.length) return alert('Nothing marked yet.');
    navigator.clipboard.writeText(names.join('\\n')).then(() => {{
      const btn = event.target; const orig = btn.textContent;
      btn.textContent = 'Copied!'; setTimeout(() => btn.textContent = orig, 1200);
    }});
  }}

  function exportPicks() {{
    const data = [...document.querySelectorAll('.card.marked')].map(c => ({{
      name: c.querySelector('.name').textContent,
      adset: c.dataset.adset,
      tier: c.dataset.tier,
      ctr: +c.dataset.ctr,
      cpc: +c.dataset.cpc,
      msg: +c.dataset.msg,
      lpv: +c.dataset.lpv,
      spend: +c.dataset.spend,
    }}));
    if (!data.length) return alert('Nothing marked yet.');
    const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'ad-picks.json'; a.click();
    URL.revokeObjectURL(url);
  }}

  function renderTray() {{
    const tray = document.getElementById('picks-tray');
    const list = document.getElementById('tray-list');
    const count = document.getElementById('tray-count');
    count.textContent = marks.size;
    tray.style.display = marks.size ? 'flex' : 'none';
    list.innerHTML = [...marks].map(n => {{
      const card = [...document.querySelectorAll('.card')].find(c => c.querySelector('.name').textContent === n);
      const tier = card ? card.dataset.tier : '';
      return `<div class="tray-item">${{n}}<span class="tray-tier">${{tier}}</span></div>`;
    }}).join('');
  }}

  function toggleMarkedOnly() {{
    showMarkedOnly = !showMarkedOnly;
    document.getElementById('show-marked-btn').classList.toggle('active', showMarkedOnly);
    document.getElementById('show-marked-btn').textContent = showMarkedOnly ? 'Show all' : 'Show marked only';
    applyFilters();
  }}

  // ===== Tag filter (from pattern tables + tag chips) =====
  // activeTagFilter shape: {{type: 'format'|'product'|'color'|'style', value: 'X'}} or null
  let activeTagFilter = null;

  function filterByTag(ev, el) {{
    ev.stopPropagation();
    const type = el.dataset.tagtype;
    const val = el.dataset.tagval;
    if (activeTagFilter && activeTagFilter.type === type && activeTagFilter.value === val) {{
      activeTagFilter = null;  // toggle off
    }} else {{
      activeTagFilter = {{ type, value: val }};
    }}
    renderTagFilterChip();
    applyFilters();
    if (activeTagFilter) {{
      document.getElementById('individual-ads').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }}
  }}

  function clearTagFilter() {{
    activeTagFilter = null;
    renderTagFilterChip();
    applyFilters();
  }}

  function renderTagFilterChip() {{
    const bar = document.getElementById('tag-filter-bar');
    if (activeTagFilter) {{
      bar.style.display = 'flex';
      document.getElementById('tfb-type').textContent = activeTagFilter.type;
      document.getElementById('tfb-value').textContent = activeTagFilter.value;
    }} else {{
      bar.style.display = 'none';
    }}
  }}

  // ===== Filter + Sort =====
  function applyFilters() {{
    const adset = document.getElementById('filter-adset').value;
    const tier = document.getElementById('filter-tier').value;
    const search = document.getElementById('search-box').value.toLowerCase().trim();
    const sortBy = document.getElementById('sort-by').value;

    const grid = document.getElementById('grid');
    const cards = [...grid.querySelectorAll('.card')];

    cards.forEach(c => {{
      const matchAdset = !adset || c.dataset.adset === adset;
      let matchTier = true;
      if (tier === 'WINNER+KEEP') matchTier = c.dataset.tier === 'WINNER' || c.dataset.tier === 'KEEP';
      else if (tier) matchTier = c.dataset.tier === tier;
      const matchSearch = !search || c.dataset.name.includes(search);
      const matchMarked = !showMarkedOnly || c.classList.contains('marked');
      const matchTag = !activeTagFilter || c.dataset[activeTagFilter.type] === activeTagFilter.value;
      c.style.display = (matchAdset && matchTier && matchSearch && matchMarked && matchTag) ? '' : 'none';
    }});

    // Sort visible cards
    const visible = cards.filter(c => c.style.display !== 'none');
    const [key, dir] = sortBy.split('-');
    visible.sort((a, b) => {{
      let va = key === 'name' ? a.dataset.name : +a.dataset[key];
      let vb = key === 'name' ? b.dataset.name : +b.dataset[key];
      if (key === 'name') return dir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
      return dir === 'asc' ? va - vb : vb - va;
    }});
    visible.forEach(c => grid.appendChild(c));

    document.getElementById('empty-state').style.display = visible.length ? 'none' : 'block';
  }}

  // Restore marks on load
  document.querySelectorAll('.card').forEach(c => {{
    const name = c.querySelector('.name').textContent;
    if (marks.has(name)) c.classList.add('marked');
  }});
  renderTray();
</script>
</body></html>"""

out = REPO_ROOT / '.tmp' / 'ads_report.html'
out.write_text(html, encoding='utf-8')
print(f'\nWrote {out}')
print(f'Cards: {len(rows)}')

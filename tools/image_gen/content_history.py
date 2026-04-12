"""
Content History -- tracks used headlines and layout combos across sessions.

Prevents the feed from looking repetitive by ensuring the randomizer and skills
don't reuse headlines or skill+layout+product combos that have already been posted.

Usage:
    python tools/image_gen/content_history.py record --batch .tmp/batch_001.json
    python tools/image_gen/content_history.py record --headline "BLOCK THE NOISE." --skill brand-bold --product "Outback Black" --layout SPLIT_TEXT
    python tools/image_gen/content_history.py list
    python tools/image_gen/content_history.py list --headlines
    python tools/image_gen/content_history.py list --layouts
    python tools/image_gen/content_history.py check --headline "BLOCK THE NOISE."
    python tools/image_gen/content_history.py check --layout RADIAL --skill brand-callout --product "Outback Green"

Files:
    contents/headline_history.json
    contents/layout_history.json
"""

import json
import sys
from datetime import date
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
HEADLINE_FILE = PROJECT_DIR / "contents" / "headline_history.json"
LAYOUT_FILE = PROJECT_DIR / "contents" / "layout_history.json"


def load_json(path: Path) -> list:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def save_json(path: Path, data: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_used_headlines() -> set:
    return {e["headline"].upper().strip() for e in load_json(HEADLINE_FILE)}


def get_used_layouts() -> set:
    """Return set of 'skill|layout|product' keys."""
    return {f"{e['skill']}|{e['layout']}|{e['product']}" for e in load_json(LAYOUT_FILE)}


def record_headline(headline: str, skill: str, product: str, layout: str = "", session: int = 0):
    data = load_json(HEADLINE_FILE)
    entry = {
        "headline": headline,
        "skill": skill,
        "product": product,
        "layout": layout,
        "session": session,
        "date": date.today().isoformat(),
    }
    # Skip if already exists
    if headline.upper().strip() in get_used_headlines():
        print(f"SKIP (already recorded): {headline}", file=sys.stderr)
        return
    data.append(entry)
    save_json(HEADLINE_FILE, data)
    print(f"Recorded headline: {headline}", file=sys.stderr)


def record_layout(skill: str, layout: str, product: str, scenario: str = "", session: int = 0):
    data = load_json(LAYOUT_FILE)
    key = f"{skill}|{layout}|{product}"
    if key in get_used_layouts():
        print(f"SKIP (already recorded): {key}", file=sys.stderr)
        return
    entry = {
        "skill": skill,
        "layout": layout,
        "product": product,
        "scenario": scenario,
        "session": session,
        "date": date.today().isoformat(),
    }
    data.append(entry)
    save_json(LAYOUT_FILE, data)
    print(f"Recorded layout: {skill} / {layout} / {product}", file=sys.stderr)


def record_batch(batch_file: str, session: int = 0):
    """Record all entries from a batch JSON file."""
    batch = json.loads(Path(batch_file).read_text(encoding="utf-8"))
    for a in batch:
        inp = a.get("input", {})
        skill_short = a["skill"].replace("dubery-", "")

        # Record layout combo
        layout = inp.get("layout") or inp.get("scenario_type", "")
        product = inp.get("product_ref", "")
        products = inp.get("product_refs", [])

        if product:
            record_layout(skill_short, layout, product, session=session)
        for p in products:
            record_layout(skill_short, layout, p, session=session)

        # Record headline if present
        headline = inp.get("headline")
        if headline:
            record_headline(headline, skill_short, product or products[0] if products else "", layout, session)


def check_headline(headline: str) -> bool:
    used = get_used_headlines()
    is_used = headline.upper().strip() in used
    status = "USED" if is_used else "AVAILABLE"
    print(f"{status}: {headline}")
    return not is_used


def check_layout(skill: str, layout: str, product: str) -> bool:
    used = get_used_layouts()
    key = f"{skill}|{layout}|{product}"
    is_used = key in used
    status = "USED" if is_used else "AVAILABLE"
    print(f"{status}: {skill} / {layout} / {product}")
    return not is_used


def list_history(show_headlines=True, show_layouts=True):
    if show_headlines:
        headlines = load_json(HEADLINE_FILE)
        print(f"=== Headlines ({len(headlines)}) ===")
        for h in headlines:
            print(f"  {h['headline']:35s} | {h['skill']:15s} | {h['product']:20s} | s{h.get('session',0)}")

    if show_layouts:
        layouts = load_json(LAYOUT_FILE)
        print(f"\n=== Layouts ({len(layouts)}) ===")
        for l in layouts:
            print(f"  {l['skill']:20s} | {l['layout']:15s} | {l['product']:25s} | s{l.get('session',0)}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Content History Tracker")
    sub = parser.add_subparsers(dest="cmd")

    rec = sub.add_parser("record")
    rec.add_argument("--batch", help="Batch JSON file to record all entries from")
    rec.add_argument("--headline", help="Single headline to record")
    rec.add_argument("--skill", default="")
    rec.add_argument("--product", default="")
    rec.add_argument("--layout", default="")
    rec.add_argument("--session", type=int, default=0)

    chk = sub.add_parser("check")
    chk.add_argument("--headline", help="Check if headline is used")
    chk.add_argument("--layout", help="Layout name to check")
    chk.add_argument("--skill", default="")
    chk.add_argument("--product", default="")

    lst = sub.add_parser("list")
    lst.add_argument("--headlines", action="store_true")
    lst.add_argument("--layouts", action="store_true")

    args = parser.parse_args()

    if args.cmd == "record":
        if args.batch:
            record_batch(args.batch, session=args.session)
        elif args.headline:
            record_headline(args.headline, args.skill, args.product, args.layout, args.session)
        elif args.layout:
            record_layout(args.skill, args.layout, args.product, session=args.session)
    elif args.cmd == "check":
        if args.headline:
            check_headline(args.headline)
        elif args.layout:
            check_layout(args.skill, args.layout, args.product)
    elif args.cmd == "list":
        show_h = args.headlines or (not args.headlines and not args.layouts)
        show_l = args.layouts or (not args.headlines and not args.layouts)
        list_history(show_h, show_l)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

"""Human-paced browser session.

Launches a headed Chromium with a PERSISTENT profile (cookies/logins survive
restarts) and a CDP port, so later commands attach to the same live window
instead of starting a fresh, logged-out browser.

Design rules:
  - Never handles passwords. RA logs in by hand in the visible window once;
    the profile keeps the session.
  - Every action is paced with randomized human-ish delays, incremental
    scrolling and jittered typing. No rapid-fire request bursts.

Usage:
    python tools/browser/session.py start [--profile NAME] [--url URL]
    python tools/browser/session.py goto <url>
    python tools/browser/session.py text [--max-chars N]
    python tools/browser/session.py shot [--out PATH]
    python tools/browser/session.py scroll [--screens N]
    python tools/browser/session.py click "<selector or text>"
    python tools/browser/session.py links [--contains SUBSTR]
    python tools/browser/session.py stop

`start` runs in the foreground and keeps the browser alive -- launch it with
run_in_background, then use the other verbs from separate calls.
"""

import argparse
import os
import random
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

CDP_PORT = int(os.environ.get("BROWSER_CDP_PORT", "9333"))
PROFILE_ROOT = Path(os.path.expanduser("~")) / ".config" / "browser-profiles"


def pause(lo=1.2, hi=3.0):
    """Human beat between actions."""
    time.sleep(random.uniform(lo, hi))


def _page(ctx):
    """Newest non-blank page in the live browser."""
    pages = [p for p in ctx.pages if not p.url.startswith("about:")]
    return (pages or ctx.pages)[-1]


def _attach(pw):
    browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
    if not browser.contexts:
        raise SystemExit("No browser context. Run `session.py start` first.")
    return browser, browser.contexts[0]


def human_scroll(page, screens=1.0):
    """Scroll down in small nudges with pauses, like reading."""
    steps = max(1, int(screens * 5))
    for _ in range(steps):
        page.mouse.wheel(0, random.randint(180, 340))
        time.sleep(random.uniform(0.35, 0.9))
    pause(0.8, 1.6)


def human_move(page):
    """A couple of idle mouse drifts."""
    for _ in range(random.randint(1, 3)):
        page.mouse.move(random.randint(120, 1100), random.randint(120, 700),
                        steps=random.randint(12, 30))
        time.sleep(random.uniform(0.15, 0.5))


def human_type(page, selector, value):
    page.click(selector)
    pause(0.4, 1.0)
    for ch in value:
        page.keyboard.type(ch)
        time.sleep(random.uniform(0.06, 0.19))
    pause(0.5, 1.2)


# --------------------------------------------------------------------------- #

def cmd_start(args):
    profile = PROFILE_ROOT / args.profile
    profile.mkdir(parents=True, exist_ok=True)
    print(f"profile: {profile}")
    print(f"cdp    : http://127.0.0.1:{CDP_PORT}")

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            headless=False,
            channel="chrome" if args.chrome else None,
            args=[
                f"--remote-debugging-port={CDP_PORT}",
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ],
            no_viewport=True,
            locale="en-PH",
            timezone_id="Asia/Manila",
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        if args.url:
            page.goto(args.url, wait_until="domcontentloaded")
        print("READY -- browser is live. Log in by hand if needed.")
        sys.stdout.flush()
        # Hold the process open until the window is closed or `stop` is called.
        try:
            while True:
                time.sleep(2)
                if not ctx.pages:
                    break
        except KeyboardInterrupt:
            pass
        print("browser closed")


def cmd_goto(args):
    with sync_playwright() as pw:
        _, ctx = _attach(pw)
        page = _page(ctx)
        pause()
        page.goto(args.url, wait_until="domcontentloaded")
        pause(1.5, 3.5)
        human_move(page)
        print(f"{page.url}\n{page.title()}")


def cmd_text(args):
    with sync_playwright() as pw:
        _, ctx = _attach(pw)
        page = _page(ctx)
        body = page.inner_text("body")
        print(f"URL: {page.url}\nTITLE: {page.title()}\n{'-' * 60}")
        print(body[: args.max_chars])


def cmd_shot(args):
    with sync_playwright() as pw:
        _, ctx = _attach(pw)
        page = _page(ctx)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out), full_page=args.full)
        print(out)


def cmd_scroll(args):
    with sync_playwright() as pw:
        _, ctx = _attach(pw)
        human_scroll(_page(ctx), args.screens)
        print("scrolled")


def cmd_click(args):
    with sync_playwright() as pw:
        _, ctx = _attach(pw)
        page = _page(ctx)
        human_move(page)
        pause()
        target = args.target
        loc = page.get_by_text(target, exact=False).first if args.by_text \
            else page.locator(target).first
        loc.scroll_into_view_if_needed()
        pause(0.6, 1.4)
        loc.click()
        pause(1.5, 3.0)
        print(f"{page.url}\n{page.title()}")


def cmd_links(args):
    with sync_playwright() as pw:
        _, ctx = _attach(pw)
        page = _page(ctx)
        rows = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => [e.innerText.trim().slice(0,90), e.href])",
        )
        seen = set()
        for label, href in rows:
            if args.contains and args.contains.lower() not in (label + href).lower():
                continue
            if href in seen or not label:
                continue
            seen.add(href)
            print(f"{label}  ->  {href}")


def cmd_stop(args):
    with sync_playwright() as pw:
        browser, ctx = _attach(pw)
        ctx.close()
        print("closed")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("start")
    s.add_argument("--profile", default="onlinejobs")
    s.add_argument("--url", default=None)
    s.add_argument("--chrome", action="store_true", help="use installed Chrome")
    s.set_defaults(func=cmd_start)

    s = sub.add_parser("goto")
    s.add_argument("url")
    s.set_defaults(func=cmd_goto)

    s = sub.add_parser("text")
    s.add_argument("--max-chars", type=int, default=6000)
    s.set_defaults(func=cmd_text)

    s = sub.add_parser("shot")
    s.add_argument("--out", default=".tmp/browser-shot.png")
    s.add_argument("--full", action="store_true")
    s.set_defaults(func=cmd_shot)

    s = sub.add_parser("scroll")
    s.add_argument("--screens", type=float, default=1.0)
    s.set_defaults(func=cmd_scroll)

    s = sub.add_parser("click")
    s.add_argument("target")
    s.add_argument("--by-text", action="store_true")
    s.set_defaults(func=cmd_click)

    s = sub.add_parser("links")
    s.add_argument("--contains", default=None)
    s.set_defaults(func=cmd_links)

    s = sub.add_parser("stop")
    s.set_defaults(func=cmd_stop)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

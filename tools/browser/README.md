# tools/browser

Human-paced browser automation for **logged-in sites that have no API** — job
boards, dashboards, account settings. Built for the OnlineJobs.ph profile work
(session 249) and reusable for anything else that needs a real, signed-in browser.

## Why it exists

Some sites can only be reached through a session you cannot script from scratch:
no public API, bot detection on the login flow, and a session that must look like
a person. This tool solves that by never touching the login at all.

- A **headed Chromium** runs with a **persistent profile**, so a login done by
  hand once survives every later run.
- **RA's password is never handled by any script.** He logs in manually in the
  visible window; the profile keeps the cookie.
- A **CDP port** is exposed, so later commands attach to the same live window
  instead of launching a fresh, logged-out browser.
- Every action is **paced like a human**: randomized 1-3s beats between steps,
  incremental wheel-scrolls, idle mouse drift, jittered per-character typing.

## Usage

```bash
# 1. Start the session (run in background -- it holds the browser open).
python tools/browser/session.py start --profile onlinejobs \
    --url https://www.onlinejobs.ph/jobseekers/login

# 2. Log in by hand in the window that opens. Once only, per profile.

# 3. Drive it from separate calls.
python tools/browser/session.py goto <url>
python tools/browser/session.py text [--max-chars N]
python tools/browser/session.py shot [--out PATH] [--full]
python tools/browser/session.py scroll [--screens N]
python tools/browser/session.py click "<selector>" [--by-text]
python tools/browser/session.py links [--contains SUBSTR]
python tools/browser/session.py stop
```

Profiles live in `~/.config/browser-profiles/<name>/`. CDP port defaults to
9333, override with `BROWSER_CDP_PORT`.

## Writing a task script

For anything beyond the built-in verbs, connect over CDP directly. The pattern
used for the OnlineJobs.ph work:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    b = pw.chromium.connect_over_cdp("http://127.0.0.1:9333")
    page = [p for p in b.contexts[0].pages if not p.url.startswith("about:")][-1]
    ...
```

Pace it: `time.sleep(random.uniform(...))` between actions, and prefer
`keyboard.insert_text()` for long blocks over per-character typing.

## Gotchas learned the hard way

- **Escape JS carefully.** Regex and newlines inside a bash heredoc get mangled.
  Put non-trivial `page.evaluate()` bodies in a `.js` file and read them in.
- **React inline editors are not `<input>`s.** OnlineJobs.ph uses
  `contenteditable` spans (salary) and `contenteditable="plaintext-only"`
  (profile description). Type into them; do not `fill()`.
- **Debounced search dropdowns need a poll, not a fixed sleep.** A 1.5s wait
  silently returned zero options maybe a third of the time. Poll until the
  expected option appears.
- **Duplicate `data-cy` nodes** exist for mobile and desktop layouts. Use
  `:visible` or the element actually in the viewport.
- **Radix dialogs intercept pointer events.** A click that "times out" while the
  element is visible and enabled usually means an overlay is open. Handle the
  confirm dialog first.
- **Reload before believing a save.** Several fields render optimistically
  (avatar showed a `data:` URI locally). Always reload and re-read.

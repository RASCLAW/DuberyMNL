# DuberyMNL Messenger Chatbot

Production Messenger assistant for [DuberyMNL](https://duberymnl.com), a Philippines-based polarized-sunglasses brand. Handles customer inquiries, qualifies leads, writes to a Google Sheets CRM, and hands off to a human when a conversation is more than the bot should be handling.

This is a hybrid architecture running on RA's home laptop (primary) with a Cloudflare Worker fallback when the origin is down. First real order closed through this bot on 2026-04-15.

---

## Why this exists

Out-of-the-box chat assistants try to close every deal. That works for toy demos. It breaks for real customers, who have trust issues, repeat objections, ask about things you don't sell, or simply aren't your target segment.

The hard problem isn't making a bot talk. It's teaching it **when to stop**.

This codebase is a running attempt at that: a chatbot that behaves less like a retry loop and more like a disciplined customer service employee. Seven layered guardrails decide when the bot should reply, when it should shut up, and when it should hand off to a human.

---

## Architecture

```
                              Messenger user
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   Meta Webhook        │
                        │  (graph.facebook.com) │
                        └──────────┬────────────┘
                                   │
                                   ▼
            ┌──────────────────────────────────────┐
            │  Cloudflare Worker (fallback)        │
            │  chatbot.duberymnl.com               │
            │  - Tries to proxy to origin          │
            │  - On origin-down: intent classifier │
            │    (pricing / polarized / shipping / │
            │     how_to_order / order_intent)     │
            │    answers from KV + pings TG        │
            └──────────┬───────────────────────────┘
                       │
                       ▼ (Cloudflare Tunnel)
            ┌──────────────────────────────────────┐
            │  Flask webhook (this code)           │
            │  127.0.0.1:8080 on RA's laptop       │
            │                                      │
            │  ┌────────────────────────────────┐  │
            │  │  run_generate()                │  │
            │  │  ├─ Handoff silent gate        │  │
            │  │  │  (with 24h time-decay)      │  │
            │  │  ├─ Injection gate             │  │
            │  │  ├─ Bot-sender gate            │  │
            │  │  ├─ Complaint gate             │  │
            │  │  ├─ Policy-pushback gate       │  │
            │  │  └─ Gemini generate_reply()    │  │
            │  └────────────┬───────────────────┘  │
            │               │                      │
            │  ┌────────────▼───────────────────┐  │
            │  │  process_message() post-pipe   │  │
            │  │  ├─ Phantom-QR guard           │  │
            │  │  ├─ Turn-cap override          │  │
            │  │  ├─ Loop guard                 │  │
            │  │  ├─ first_name persist         │  │
            │  │  ├─ Policy stamping            │  │
            │  │  └─ Handoff flag + TG ping     │  │
            │  └────────────────────────────────┘  │
            │                                      │
            │  Background: Nurture scanner        │
            │  (every 30 min, 18-23h window)       │
            └───────┬─────────────┬────────────────┘
                    │             │
                    ▼             ▼
            ┌────────────┐  ┌────────────────┐
            │ Vertex AI  │  │ Google Sheets  │
            │ Gemini 2.5 │  │ (CRM)          │
            │ Flash      │  └────────────────┘
            └────────────┘
```

### Layers

- **Meta Webhook** — incoming messages from the DuberyMNL Facebook Page.
- **Cloudflare Worker** — edge fallback with a tiny 5-intent classifier backed by KV. Responds if the origin is unreachable and pings Telegram so RA knows to check.
- **Cloudflare Tunnel** — exposes `127.0.0.1:8080` to the public internet as `chatbot.duberymnl.com` without opening router ports.
- **Flask webhook** — primary handler. Runs Gemini 2.5 Flash via Vertex AI REST API, stacked with deterministic guardrails.
- **Background nurture scanner** — daemon thread wakes every 30 min and sends a single follow-up to customers who showed interest but went silent between 18 and 23 hours ago.

---

## The seven guardrails

Ordered by execution. Each one is a small, testable unit with a single responsibility. Most are pre-Gemini (so they save tokens) or post-Gemini overrides (so they catch Gemini hallucinations and loops the model can't detect).

| # | Guardrail | Stage | Triggers when | Behavior |
|---|-----------|-------|---------------|----------|
| 1 | **Human takeover** | webhook | Meta echo arrives with `app_id != META_APP_ID` (RA typed in Page Inbox) | Flags handoff, logs RA's reply to store + CRM, bot goes silent |
| 2 | **Complaint detector** | pre-Gemini | ~30 PH trust/scam/deflection phrases (`naloko`, `2beses`, `try ko na lang sa tiktok`, etc.) | Short-circuits Gemini, sends bridge line, flags handoff, TG pings RA |
| 3 | **Policy pushback** | pre-Gemini | Customer pushes back on a policy already delivered in the convo (e.g. asking for COD after being told it's Metro Manila only) | Short-circuits Gemini, sends bridge line, flags handoff, TG pings RA |
| 4 | **Phantom QR injector** | post-Gemini | Reply text references a QR code (`"here's our QR"`, `"QR code"`, etc.) but no QR image key was set | Auto-injects `support-instapay-qr` so the image actually sends |
| 5 | **Turn cap** | post-Gemini | Assistant reply count ≥ `TURN_CAP` (default 10) without `order_complete=true` | Overrides reply with bridge, flags handoff, TG pings RA |
| 6 | **Loop guard** | post-Gemini | This reply's theme signature matches the last two stored signatures (3 near-identical replies in a row) | Overrides reply with bridge, flags handoff, TG pings RA |
| 7 | **first_name persist** | post-Gemini | Gemini extracts a customer name and none is cached | Stamps `conv.metadata.first_name` for future-reply personalization |

### Related behaviors

- **Time-decay release** — if a conversation has been handoff-flagged for ≥ `HANDOFF_DECAY_HOURS` (default 24) when a new customer message arrives, the flag auto-clears. Stale handoffs don't permanently silence the bot.
- **Proactive nurture** — background scanner sends ONE follow-up per customer between `NURTURE_MIN_HOURS` and `NURTURE_MAX_HOURS` (default 18–23) after their last message. Only fires if they showed interest (`inquiry` or `order` intent) and weren't already handed off or sold.
- **Ad-referral capture (Phase 1)** — if Meta fires a `referral` event (from a Click-to-Messenger ad or `m.me?ref=...` link), the `ad_id`/`ref`/`source` get stamped on the conversation for first-touch attribution and logged to `.tmp/referral_log.jsonl`.
- **Ad-aware openers (Phase 2)** — on first contact, the webhook looks up the `source_ref`/`source_ad_id` in `chatbot/ad_registry.json` (15 entries: 9 per-variant, 3 per-series, 3 generic) and injects an `AD_CONTEXT` + `AD_PRODUCT_FOCUS` block into Gemini's system-prompt so the opener references the specific product the customer clicked on (e.g. *"Saw you checking out the Bandits Tortoise..."*) instead of firing the generic SALES TEMPLATE. Ongoing turns skip the hint. Unknown refs fall back safely to the SALES TEMPLATE.
- **Manual-close CRM capture** — `/mark-sale/<sender_id>` lets the owner record a sale closed manually from the Page Inbox. Writes a structured Orders row via `create_order`, stamps `order_recorded=True`, flags handoff, and appends a transcript note. Closes the invisibility gap on sales that didn't go through the bot's order flow.

---

## Tech stack

- **Python 3.12 + Flask** — webhook server, stateful conversation store, orchestration
- **Vertex AI Gemini 2.5 Flash** — reply generation via REST (no SDK to avoid init hangs)
- **Google Sheets API** — CRM persistence (leads, orders, messages, status changes)
- **Cloudflare Workers + KV** — edge fallback classifier
- **Cloudflare Tunnel (`cloudflared`)** — laptop-to-internet exposure
- **Meta Graph API v21.0** — Messenger Send API, user profile lookups, attachment upload
- **Windows Task Scheduler** — keeps the Flask server + tunnel running at login

---

## Project structure

```
chatbot/
├── messenger_webhook.py       # Flask server + orchestration + scanner threads
├── conversation_engine.py     # Vertex AI Gemini call + system prompt
├── conversation_store.py      # Thread-safe persistent conversation dict
├── knowledge_base.py          # Product specs, FAQs, image keys
├── handoff.py                 # Handoff reason labels
├── security.py                # Injection + complaint + policy detectors
├── crm_sync.py                # Google Sheets reads/writes
├── ad_registry.json           # Maps Meta Click-to-Messenger ref tags to per-ad opener hints
├── cloudflare-worker/
│   ├── worker.js              # Edge fallback classifier
│   └── test-classifier.mjs    # Local test harness
├── .tmp/
│   ├── conversation_store.json  # Persisted conversations (30-day TTL)
│   └── referral_log.jsonl       # Ad referral audit trail
└── README.md                  # this file
```

---

## Configuration

All secrets in the project-level `.env`:

| Variable | Required | Purpose |
|----------|----------|---------|
| `META_PAGE_ACCESS_TOKEN` | ✓ | Messenger Send API calls |
| `META_PAGE_ID` | ✓ | Own-page detection on incoming events |
| `META_APP_SECRET` | ✓ | Webhook HMAC verification |
| `META_APP_ID` | ✓ | Distinguishes bot echoes from human takeover |
| `MESSENGER_VERIFY_TOKEN` | ✓ | Webhook verification challenge |
| `TELEGRAM_BOT_TOKEN` | optional | TG handoff pings |
| `TG_CHAT_ID` | optional | TG handoff pings |
| `CHATBOT_TURN_CAP` | default 10 | Assistant reply cap before forced handoff |
| `CHATBOT_HANDOFF_DECAY_HOURS` | default 24 | Stale-flag auto-release threshold |
| `CHATBOT_NURTURE_MIN_HOURS` | default 18 | Earliest nurture send |
| `CHATBOT_NURTURE_MAX_HOURS` | default 23 | Latest nurture send (stay under Meta 24h window) |
| `CHATBOT_NURTURE_SCAN_SECONDS` | default 1800 | Nurture scanner wake interval |

Ad-aware openers are configured in [chatbot/ad_registry.json](ad_registry.json), not env vars. Each entry is keyed by the Meta Click-to-Messenger `ref` tag (or `ad_id` as fallback) and carries a `product_focus` label plus an `opener_hint` injected into Gemini's system prompt on first contact.

Vertex AI auth uses Application Default Credentials (`gcloud auth application-default login` on the dev machine).

---

## Admin endpoints

All local-only at `http://127.0.0.1:8080`. The Cloudflare tunnel forwards `/webhook` externally; admin routes stay on LAN.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/flag/<sender_id>?reason=<label>` | GET / POST | Flag a conversation for handoff (bot goes silent) |
| `/release/<sender_id>` | GET / POST | Clear a handoff flag (bot resumes) |
| `/mark-sale/<sender_id>` | GET / POST | Record a manually-closed sale → CRM Orders row, stamps `order_recorded`, flags handoff. Required: `items`, `total`. Many optional fields (see in-code docstring). |
| `/status` | GET | JSON with stats + readiness |
| `/readiness` | GET | Cloud Run–style probe; 503 during warmup, 200 after |
| `/conversations` | GET | HTML admin view (rich badges: handoff reason, order id+total, policies delivered, ad source, nurture, intents) with AJAX action buttons: RELEASE / FLAG / MARK SALE (with inline form). |
| `/chat-test` | GET / POST | Local browser chat UI (bypasses Meta + CRM) |
| `/webhook` | GET / POST | Meta Messenger verification + events |

### Stats tracked (visible at `/status`)

```json
{
  "messages_received": 0,
  "messages_sent": 0,
  "messages_deduped": 0,
  "handoffs_triggered": 0,
  "loop_handoffs": 0,
  "turn_cap_handoffs": 0,
  "human_takeovers": 0,
  "manual_replies_logged": 0,
  "manual_sales_marked": 0,
  "handoff_auto_released": 0,
  "nurtures_sent": 0,
  "nurture_failed": 0,
  "referrals_captured": 0,
  "errors": 0
}
```

Every guardrail fires a structured `log_event(...)` JSON line to stdout; Cloud Run / any log collector can filter by `jsonPayload.event` (e.g. `event="policy_pushback_detected"`).

---

## Local testing

```bash
# Install deps
pip install -r requirements.txt

# Point at your .env, start the Flask dev server
python messenger_webhook.py

# Open the local chat UI
open http://127.0.0.1:8080/chat-test
```

`/chat-test` auto-prefixes session IDs with `TEST_` so nothing pollutes the CRM. Bypasses Meta entirely. Useful for iterating on the system prompt or new guardrails without burning a single Meta call.

**Unit-testable components** (in `security.py` and `conversation_store.py`):

- `detect_injection(text)`
- `detect_bot_sender(text)`
- `detect_complaint(text)`
- `extract_policies_from_reply(text)` → list of policy_ids
- `detect_policy_pushback(customer_text, policies_delivered)` → policy_id or None
- `categorize_reply(text)` → theme signature for loop guard
- `store.push_reply_signature(sender_id, sig)` → bool (loop detected)

---

## Observability

- Structured JSON logs on stdout (`event`, `sender_id`, plus context fields)
- `/status` counters updated on every guardrail trigger
- `.tmp/referral_log.jsonl` append-only audit trail of ad-driven entries
- `.tmp/conversation_store.json` — human-readable snapshot of every conversation with all metadata (handoff state, policies delivered, reply signatures, nurture state, source ad, first name)
- Telegram pings on every handoff reason except `human_takeover` (RA doesn't need to ping himself)

---

## Known limitations & roadmap

**Known limitations**

- **Single-instance / single-tenant deployment.** The nurture scanner runs in-process; if the server crashes mid-scan, that scan is lost. One codebase instance serves one brand — multi-tenancy is pending.
- **Policies are hand-coded.** Adding a new policy (e.g. "free shipping cutoff is 4pm") requires editing `security.POLICY_DEFINITIONS`. No admin UI.
- **Ad registry is file-based.** Adding new ad tags means editing `ad_registry.json` + restarting (or waiting for lazy cache to reload on first new lookup).
- **Manual sale marking is transactional, not retroactive.** If owner forgets to call `/mark-sale`, nurture scanner may fire on a converted customer. Mitigation: takeover flag (auto-set on owner's Page Inbox reply) is sufficient for most skip-scenarios.

**Roadmap**

- [ ] Multi-tenancy isolation — rework config loading so one codebase runs N clients on one server
- [ ] `/reload-registry` endpoint to hot-swap ad registry without restart
- [ ] System prompt: add `insistence detection` guardrail (same customer objection topic 2x → handoff, more general than current policy-pushback)
- [ ] Ad-aware Phase 3: A/B variants per ad tag for opener-template testing
- [ ] Cross-instance lock on nurture scanner if we ever run multiple replicas
- [ ] Client-pitch package — 2-min demo video + Upwork listing + README scrub for public repo

---

## Why this matters

This bot serves a real business running live Meta ads. It has closed real orders. It routes real customers to a real owner when the conversation outgrows it.

The design constraint isn't "make the bot talk." It's "make the bot behave like a customer service employee who knows when to stop pitching." Every guardrail in this codebase exists because a specific failure mode was observed in production and needed a deterministic fix — not because an LLM review suggested it.

Portfolio framing: the interesting engineering isn't in the LLM call. It's in the seven layers around it that make the LLM's output deployable.

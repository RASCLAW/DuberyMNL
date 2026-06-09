# RESUME — Chatbot Pricing Patch (single-pair delivery fee + 2-pair upsell)

**Invoke:** in a fresh session after the laptop reboot, say *"read resume-chatbotpatch.md and continue."*
**Created:** 2026-06-10 (paused mid-deploy — waiting on a laptop restart to load the patch).

---

## Why this patch exists (the bug)
A recent sale closed at **₱549** because the bot quoted only the **₱50 COD fee** and **forgot the ₱99 delivery fee**, and it **didn't offer the 2-pair promo** (free delivery + free COD). RA had to message the customer to correct it to **₱648**.

Correct pricing (matches the website `dubery-landing-v3/order/order.js`: `DELIVERY_FEE=99`, `COD_FEE=50`):
- **1 pair (Metro Manila COD): 499 + 99 delivery + 50 COD = 648 total.**
- **2+ pairs: delivery fee AND COD fee BOTH waived → 2 pairs = 998 total.**
- Provincial = prepaid (GCash/bank/InstaPay), no COD; provincial shipping varies by area.

## The fix (DONE on disk, verified, NOT yet committed)
Two files edited (price must live in both — see memory `feedback_price_two_files`):

**`chatbot/knowledge_base.py`**
- `PRICING` dict: replaced vague `shipping_min_single:100` with concrete `delivery_fee_single:99`, `single_pair_total:648`, `two_pair_total:998`; rewrote `promo_note`.
- FAQ "Delivery - Metro Manila": now states the 648 breakdown + 998 for 2.
- `get_pricing_text()`: emits "ALWAYS quote all three (499 + 99 + 50 = 648)" + "2+ waives both fees".

**`chatbot/conversation_engine.py`**
- SALES TEMPLATE single-pair line: now `499 + 99 delivery + 50 COD = 648 total`.
- New **SINGLE-PAIR PRICING (CRITICAL — never under-quote)** rule block.
- PROMO UPSELL: added **ORDER-POINT EXCEPTION (always fire)** — surface the 2-pair offer once when a customer commits to a single pair (overrides the once-per-convo anti-spam rule at the decision moment).
- ORDER FLOW summary rule: single-pair total MUST include delivery + COD (648), never 499/549.
- Few-shot price example rewritten to model the full 648 quote + upsell.
- Peso-example numbers + discount-fallback line updated for consistency.

See the exact diff with: `git -C c:/Users/RAS/projects/DuberyMNL diff chatbot/knowledge_base.py chatbot/conversation_engine.py`

## Why a reboot was needed
The running webhook (was PID 10064) is a **Session-0 S4U** task; the sandboxed/console session got "Access denied" trying to kill it, and the canonical task had already been `/End`-ed (left an orphan still serving old code on :8085). A laptop restart kills the orphan and Task Scheduler relaunches `DuberyMNL-Chatbot` (Boot + Logon triggers, Enabled) → fresh `monitor.py` → fresh `messenger_webhook.py` that imports the edited code. Confirmed the task is Enabled before reboot, so the bot WILL come back on its own.

---

## AFTER REBOOT — do these (in order)

### 1. Confirm the bot came back fresh
```bash
curl -s --max-time 5 http://127.0.0.1:8085/status | python -m json.tool
```
Expect `"status":"running"`, `"warmup_complete":true`, and **`started_at` = today/just now** (NOT 2026-06-05 — that was the orphan). Also confirm exactly one listener:
```bash
netstat -ano | grep ":8085" | grep LISTENING   # should be ONE PID, new
```

### 2. Verify the new prompt is live (RA pre-approved ONE paid Gemini test call ~ $0.001 on project 'dubery')
```bash
cd c:/Users/RAS/projects/DuberyMNL/chatbot
python -c "from conversation_engine import generate_reply; r=generate_reply('Magkano po isang pair?', history=[]); print(r['reply_text'])"
```
PASS if the reply quotes **648** (or shows 499 + 99 + 50) **and** mentions the 2-pair promo (free delivery + COD waived / 998). If it still says 549 or omits delivery → the new code didn't load; re-check step 1.
- Free alternative (no Gemini call): `python -c "import knowledge_base as kb; print(kb.get_pricing_text())"` — confirms source, but only the live call proves Gemini behavior.

### 3. Commit + push the chatbot code (crash-proof) — ASK RA first
```bash
git -C c:/Users/RAS/projects/DuberyMNL add chatbot/knowledge_base.py chatbot/conversation_engine.py
git -C c:/Users/RAS/projects/DuberyMNL commit -m "fix(chatbot): single-pair quote = 499+99 delivery+50 COD=648; fire 2-pair upsell at order point"
git -C c:/Users/RAS/projects/DuberyMNL push origin main
```

### 4. Cleanup (optional)
- `.tmp/restart-chatbot.ps1` — leftover one-shot restarter, safe to delete (it's gitignored).
- Transient task `DuberyMNL-ChatbotRestart` was **never created** (registration was denied) — nothing to remove.

### 5. Update memory
- `reference_delivery_pricing_policy.md` — mark **"Chatbot KB pending" → DONE** (chatbot now quotes 648 single / 998 for 2, order-point upsell). Bump the index line in MEMORY.md.

---

## Rollback (if the patch reads wrong)
```bash
git -C c:/Users/RAS/projects/DuberyMNL checkout chatbot/knowledge_base.py chatbot/conversation_engine.py
```
then restart the bot (reboot, or `schtasks /End` + `/Run /tn DuberyMNL-Chatbot` from an admin shell).

## Unrelated, already shipped this session (don't redo)
- Inventory update committed + pushed: `a57274c` (+8 outback-black, -1 bandits-blue, -1 bandits-green, bandits-matte-black 1 pending delivery; as_of 2026-06-10). `inventory.json` tracked, `orders/reorder.json` gitignored/local.

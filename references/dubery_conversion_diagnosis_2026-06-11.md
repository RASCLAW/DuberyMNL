# DuberyMNL Conversion & Engagement Drop — Root-Cause Diagnosis
*2026-06-11 · read-only audit · sources cited per figure · no ads touched, no paid spend*

---

## 1. VERDICT

The drop is **two stacked regressions, not one**. First, around **May 25–27** the homepage→product-page path broke (site-wide image optimization 5/25 + hero refresh 5/27-28; the "Pick-your-style" section needed a fix commit on 6/1): pixel ViewContent collapsed from ~35/day to **0–2/day for May 27–31**, and website orders stopped after **May 24** — the last `order_form` row in the Orders sheet. Second, on **June 4–5** the proven "DuberyMNL Traffic" campaign (Metro Manila, broad 24–45 — the audience that produced every delivered order) was **paused** and replaced with an Outback Carousel targeting a *different* audience (LuzVis-wide, 18–65, 1% Lookalike-of-Chatters) plus post-engagement boosts that buy zero site visits — account cost-per-landing-page-view went from **₱2.59 to ₱6.89 (2.7x worse)**. On top of that, organic posting **stopped entirely after May 31** (feed queue ran dry; PAGE_ACCESS_TOKEN now returns an error), which is the engagement drop. The site itself is up (all pages 200) and the pixel is firing — but **zero Purchase events since May 31** despite 40+ AddToCarts since June 1 means the post-ATC step (order form) is either high-friction (₱499 ad price becomes ₱648 at checkout) or silently broken — one unverified gap.

---

## 2. METRICS TIMELINE (before vs now)

### Orders (source: `orders/orders.json` via `tools/orders/sync_orders.py`, synced 2026-06-11 20:00)
| Window | Web orders (order_form) | Chatbot orders | Delivered revenue |
|---|---|---|---|
| May 14–24 (11d) | **7** (4 delivered ₱3,741, 3 canceled) | 0 | ₱3,741 |
| May 25–Jun 11 (18d) | **0** | 2 (5/30 ₱998, 6/9 ₱648) | ₱1,646 |
**Inflection: May 24–25.** Web order rate 0.64/day → 0.00/day (−100%). With ~700 LPVs delivered after 5/25 at the prior ~1 order/60 LPV rate, 0 orders is statistically impossible as noise — conversion genuinely broke.

### Website funnel (source: Meta Pixel `/stats`, read-only Graph API, pixel 1513349880261420; pixel live since 5/20)
| Metric | 5/20–5/24 | 5/27–5/31 | 6/1–6/3 | 6/5–6/11 |
|---|---|---|---|---|
| PageView/day | 145–381 | 59–441 | 474–711 | 96–271 |
| ViewContent/day | 11–37 | **0–8 (collapse)** | 82–221 (recovered) | 14–64 |
| AddToCart/day | 0–4 | 0–2 | 5–17 | 0–4 |
| Purchase/day | 2 on 5/24 | 2 on 5/31* | **0** | **0** |
**Zero pixel Purchases since May 31** despite ~40 ATCs since 6/1 (vs ~50% ATC→Purchase on 5/24). *The 2 Purchases on 5/31 have **no matching Orders-sheet row** — either tests or a lost order (see Gaps).

### Ads (source: read-only Graph API account/campaign daily insights, saved `.tmp/diag_account_daily.json`)
| Metric | May 20–Jun 1 ("good", old Traffic campaign) | Jun 5–11 ("now", carousel + boosts) | Δ |
|---|---|---|---|
| Spend/day | ~₱139 | ~₱173 | +24% |
| LPV/day | 53.7 (range 25–113) | **25.1** (range 16–42) | **−53%** |
| Cost/LPV | **₱2.59** | **₱6.89** | **+166%** |
| CTR | 1.8–2.4% (stable) | 1.0–4.6% (boost-inflated) | noisy |
| Msg conversations/day | 0–4 | 0 | −100% |
Of Jun 6–11 spend, **~₱319 went to two post-engagement boosts that produced 0 LPVs** (Graph API per-campaign daily: "Post: This is the colorway…" 6/6–6/8; "Post: Saw the beach…" 6/10–6/11, 331–397 post-engagements, 0 LPV). Carousel frequency Jun 5–11 = **1.55** (no fatigue).

### Organic / engagement (source: `tools/facebook/feed_queue.json`; page-post API pull FAILED — token invalid)
| Window | Organic posts | Notes |
|---|---|---|
| May 20–31 | ~every 1–2 days (last POSTED 5/31 09:00) | normal cadence |
| Jun 1–11 | **0** | queue has 0 QUEUED items; PAGE_ACCESS_TOKEN now errors `(#200) Provide valid app ID` |
Per-post engagement numbers: **DATA UNAVAILABLE — page token invalid.** But 11 days of zero posting + a dead page token (also used by the comment auto-responder) fully explains "engagement dropped."

### Chatbot (source: `.tmp/conversation_store.json`, `chatbot/` git history)
- 31 total conversations ever; ~15 active during the pricing-bug window.
- **Pricing bug live 5/19 → 6/10** (commit `2004d10` rephrased pricing; fixed session 219 `d731115`): quoted ₱549 single-pair (dropped ₱99 delivery; real total ₱648) and skipped the 2-pair promo.
- Despite the bug, the chatbot closed the **only 2 sales since May 25** (5/30, 6/9 — `chatbot_mark_sale`).

### Website availability (live check, read-only GETs, 2026-06-11)
`/`, `/products/`, PDP, `/order/`, `data.json`, `cart.js`, `order.js` — **all 200 OK**.

---

## 3. RANKED SUSPECTS

**S1 — Campaign swap on Jun 4–5: proven campaign paused, unproven audience activated. Correlation: TIGHT. Confidence: HIGH.**
- What changed: "DuberyMNL Traffic" (created 4/19, Metro Manila regions-only, age 24–45, broad — the config behind every delivered order) paused 6/4 (campaign `updated_time` 2026-06-04). Replaced by "Outback Carousel" (ACTIVE since 6/5): **LuzVis-wide, age 18–65, 1% Lookalike of Chatters**, Outback-only creative, PDP/series links. Plus 2 engagement boosts (6/5, 6/10) at ~₱66–88/day buying post-engagement, not visits.
- Effect: cost/LPV 2.7x worse; site traffic from ads halved; Metro Manila COD buyers (the only segment that ever completed delivery) no longer specifically targeted.
- Confirm: compare carousel adset insights split by region vs old campaign; un-pause test (see Fix Plan).

**S2 — Homepage→PDP path broke ~May 25–27 (image-opt + hero refresh era). Correlation: TIGHT. Confidence: HIGH.**
- What changed: 5/25 `e03833d` site-wide image swap (305MB→39MB); 5/27–28 hero refresh (session 183); homepage still 4.3MB (s204 diagnosis). 6/1 `81f2acd` **"fix Pick-your-style section"** — something on the homepage was broken and got fixed only on 6/1. (Also 6/9 `309f14d` "replace corrupt inline base64 imgs" — image corruption confirmed elsewhere later.)
- Effect: pixel ViewContent fell to **0–2/day May 27–31** while homepage LPVs ran 39–80/day — visitors landed and never reached a product page. Orders stopped 5/24-25. RA detected the symptom on 6/2 ("no orders = site leak") and routed ads to /products as a workaround.
- Confirm: it's already fixed (VC recovered 6/1–6/3); this explains the May leg of the drop historically.

**S3 — Post-ATC checkout drop-off / possible silent order-intake failure. Correlation: TIGHT (starts when VC recovered). Confidence: MEDIUM.**
- Evidence: since 6/1, ~40 AddToCarts and **0 Purchases / 0 sheet rows** (vs ~50% ATC→Purchase 5/24). Purchase pixel fires only on submit (`order/order.js:268`), so users aren't completing submit — friction or breakage.
- Friction candidates: ad/catalog price ₱499 becomes **₱648** at the order page for a single pair (+₱99 delivery +₱50 COD = +30% sticker shock); 6/1–6/5 bundles ALSO charged the ₱50 COD fee (s196 rule, reversed 6/5 `a57421b`). The 2 Purchase events on 5/31 with **no Orders-sheet row** hint the Apps Script intake may have dropped an order.
- Confirm: place one TEST order end-to-end on the live site + check Apps Script execution logs (script.google.com) for errors since 5/24.

**S4 — Organic posting stopped Jun 1 + dead Page token. Correlation: TIGHT (for engagement). Confidence: HIGH (for the engagement drop, not orders).**
- Feed queue: last POSTED 5/31, zero queued since; PAGE_ACCESS_TOKEN now invalid → scheduler, story rotation, and comment auto-responder are all dead in the water. Engagement now only exists when a boost runs.

**S5 — Chatbot pricing bug (5/19→6/10). Correlation: LOOSE. Confidence: LOW as a drop cause.**
- ~15 conversations touched. It quoted too LOW (₱549), so it wasn't scaring buyers off with price; the bot still closed the only 2 recent sales. Real cost: wrong expectations + missed 2-pair upsells. Already fixed (verify with 1 Gemini test per memory note).

**S6 — Attribution artifact (?ref= → utm_content). Correlation: N/A. Confidence: CLEARED as the cause — but it's real as a measurement gap.**
- Every Orders-sheet row ever says `Ad ID: order_form` — the old `?ref=` tags were never captured, and since utm capture shipped (cart.js reads `utm_content`, verified in code; active carousel links carry `utm_source/campaign/content`, verified via Graph API) there have been **zero web orders to test it on**. The drop is NOT phantom: the Orders sheet is source-of-truth and it is genuinely empty since 5/24. Measurement isn't hiding sales; there are none to hide.

**S7 — Creative fatigue. CLEARED.** CTR drifted 2.6%→1.9% across late May (mild), carousel frequency 1.55, CTR on 6/11 was 3.78%. Not the driver.

---

## 4. WHAT IS *NOT* BROKEN

- **The site is up** — all key pages + JS return 200 (live GET check, 6/11).
- **The Meta Pixel is firing** — the empty `.tmp/pixel_stats.json` was a tool bug (raw `/stats` endpoint returns full data); PageView/VC/ATC all flowing.
- **Clarity shows no UX meltdown** (`.tmp/clarity_metrics.json`, Jun 1–4): 0 rage clicks, 1.8% script errors, dead clicks 7.6% — normal.
- **Creative is not fatigued** (freq 1.55; CTR healthy).
- **The chatbot is not the problem** — it produced the only 2 sales since May 25, even while misquoting price.
- **The COD-waiver on 2+ (6/5)** is offer-positive, not a regression.
- **Attribution plumbing** (cart.js capture + utm-tagged carousel links) is correctly wired in code — just unproven for lack of orders.

---

## 5. FIX PLAN (prioritized)

**Reversible now:**
1. **[S×H] Restore the proven audience.** Un-pause the "DuberyMNL Traffic" campaign's `[products]` ads (Metro Manila 24–45 broad → /products with `utm_content={{ad.id}}` — already built on 6/2, ran only ~2 days before being paused with the campaign), or clone the carousel adset with MM-broad targeting. *First action: in Ads Manager, set campaign 6968215093276 ACTIVE and confirm only the `[products]` ad variants are on.* (Live ads — get RA's go first.)
2. **[S×H] Verify the order intake end-to-end.** Place one TEST order on duberymnl.com/order (name "TEST — ignore"), confirm: sheet row appears, Ad ID carries utm when visiting via a tagged link, Purchase pixel fires. Then check Apps Script execution logs for failures since 5/24 (the 5/31 orphan Purchases). *First action: open the site with `?utm_content=TEST123`, order, check the sheet.*
3. **[S×H] Stop paying for engagement that can't convert.** The boosts (₱85–88/day, 0 LPVs) should be paused or capped while order volume is zero. (Live ads — RA's call.)
4. **[S×M] Restart organic.** Renew PAGE_ACCESS_TOKEN (it errors now), refill the feed queue, confirm the hourly scheduler task fires. *First action: regenerate the page token in Meta Business settings, update `.env`, run `post_from_queue.py --dry-run`.*

**Test carefully:**
5. **[M×M] Attack the ₱499→₱648 checkout jump.** Show the all-in single-pair total earlier (PDP/cart), or A/B waiving the ₱50 COD fee on singles. Don't change price sitewide in one move — orders are the only signal you have left; change one variable.
6. **[S×M] Measurement hygiene.** Fix `pull_pixel_stats.py` (returns `{}` — wrong call shape vs the raw `/stats` endpoint that works) and `build_ad_report.py` hard-coded window + single-campaign input (today's report rendered 1 ad and stale Apr 26–May 26 dates). These produced the confusing "Meta says 0" picture.
7. **[S×L] Chatbot regression test** — 1 Gemini test of the new 648/998 quoting (flagged in memory as still pending).

---

## 6. CONFIDENCE + GAPS

**Confidence: HIGH** on the two-stage mechanism (May 25–27 site path breakage; Jun 4–5 campaign/audience swap + boost spend) and on organic stoppage as the engagement cause. **MEDIUM** on why ATCs stopped converting after 6/1 (friction vs silent intake failure) — that's the one live unknown on the website leg.

Gaps to close:
- **Order submit verification** — needs one live TEST order + Apps Script execution log review (only RA's Google account can view). Highest-value 10 minutes available.
- **Organic per-post engagement numbers** — DATA UNAVAILABLE: PAGE_ACCESS_TOKEN invalid (`(#200) Provide valid app ID`). Renew token, then pull `published_posts` engagement to quantify the organic decline.
- **Clarity after Jun 4** — cache is stale (pulled 6/4, 3-day window). Re-run `tools/clarity/` pull (free, rate-limited) to get funnel behavior for the carousel era, esp. /order page drop-off.
- **5/31 orphan Purchase events (2)** with no Orders-sheet row — test-or-lost-order ambiguity; Apps Script logs will settle it.
- **Region split of carousel LPVs** (how much of the new spend even reaches Metro Manila) — one more read-only insights call with `breakdowns=region` if wanted.

*Data files used: `orders/orders.json` · `.tmp/diag_account_daily.json` (saved this session) · Meta Graph API read-only pulls (campaigns, adsets, ads/creatives, pixel /stats, insights) · `.tmp/clarity_metrics.json` · `.tmp/conversation_store.json` · `tools/facebook/feed_queue.json` · git history + `decisions/log.md`.*

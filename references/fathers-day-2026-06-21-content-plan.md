# Father's Day 2026 (Jun 21) — Content Plan & Execution

**Author:** RA + Claude EA
**Date written:** 2026-06-16
**Father's Day PH:** Sun Jun 21, 2026 (3rd Sunday of June)

## Strategy (Hormozi avatar-angle, applied)

Stop product flatlays, build avatar-angle creatives. One creative per specific buyer-in-context — the creative IS the targeting. At ~₱100/day Meta budget, don't fragment; use 3-5 avatar-angle creatives in one ad set + organic rotation for awareness.

## Asset inventory (7 pieces total)

| ID | File | Avatar / Angle | Date gen |
|----|------|----------------|----------|
| FD V1 | `2026-06-15_BESPOKE-OUTBACK-BLACK-FD-05-GIFT.png` | Two hands giving, orange FATHER'S DAY headline | 2026-06-15 |
| FD V2 | `2026-06-15_BESPOKE-OUTBACK-BLACK-FD-V2-02-GIFT.png` | Single giver + receiver sleeve | 2026-06-15 |
| FD V3 | `2026-06-15_BESPOKE-OUTBACK-BLACK-FD-V3-02-GIFT.png` | Still life, no hands, greeting-card edge | 2026-06-15 |
| A1 | `2026-06-16_2026-06-16_BESPOKE-OUTBACK-BLACK-FD-A1-DRIVE.png` | Pang-Sunday-drive tatay (commuter/driving avatar) | 2026-06-16 |
| B1 | `2026-06-16_2026-06-16_BESPOKE-OUTBACK-BLACK-FD-B1-DESK.png` | Tito desk flat-lay (gift-buyer/"has everything" avatar) | 2026-06-16 |
| C1 | `2026-06-16_2026-06-16_BESPOKE-OUTBACK-BLACK-FD-C1-BOLD.png` | PARA SA TATAY bold typographic (scroll-stopper) | 2026-06-16 |
| D1 | `2026-06-16_2026-06-16_BESPOKE-FD-D1-DUO-GIFT.png` | Outback-Black + Bandits-Tortoise gift duo (bundle-buyer) | 2026-06-16 |

## Paid (already staged)

- **Existing FD Carousel** (campaign `52524866266480`, ad `52524866335480`) — 6-card arc using yesterday's V4/V6/V3/V9 gens, ₱100/day, OUTCOME_TRAFFIC, PAUSED. Targets PH ex-Mindanao/Cagayan, LAL (PH 1%) — Chatters. UTM: `utm_campaign=fathers-day-2-pair`. RA's call to unpause when ready.
- **No new paid set staged today** — adding a second paid FD set would fragment the small budget (Hormozi).

## Organic feed (queued via tools/facebook/queue_add.py, handed off to Meta-native scheduler)

| Slot (PHT) | Asset | Queue ID |
|-----------|-------|----------|
| Wed Jun 17, 19:00 | **C1** PARA SA TATAY bold (drumbeat opener) | `feed-20260617-1900-001` |
| Thu Jun 18, 19:00 | **A1** Driving tatay (lifestyle aspirational) | `feed-20260618-1900-001` |
| Fri Jun 19, 19:00 | **D1** Gift duo (bundle hook — 2-pair ₱998) | `feed-20260619-1900-001` |
| Sat Jun 20, 12:00 | **B1** Tito desk flat-lay (Father's-Day-eve gift idea) | `feed-20260620-1200-001` |

All `handed_off=true` — scheduled at Meta directly, no local cron dependency.

## Captions (locked, English-led natural Taglish, leads with 2-pair bundle ₱998 + free delivery + free COD per s224)

### C1 — Wed Jun 17, 19:00

```
PARA SA TATAY.

The man who taught you how to drive, fix things, and stay calm — give him shades that actually cut the glare.

Polarized lenses. Built for outdoor light. Pang-Sunday-drive, pang-fishing, pang-everything.

Get the 2-pair bundle for ₱998 — one for him, one for you. Walang delivery fee, walang COD fee, kahit saan sa PH.

Father's Day is 06.21. Order by Friday to ship in time.

→ duberymnl.com/products/?series=outback
```

### A1 — Thu Jun 18, 19:00

```
This is the kind of pair you don't notice until the glare's gone.

Polarized. Lightweight. Matte black, walang arte.

If your tatay drives — or just loves a quiet Sunday — this is the gift.

2-pair bundle ₱998. Free delivery, free COD, kahit saan sa Pilipinas.

Father's Day 06.21. Order by Friday.

→ duberymnl.com/products/?series=outback
```

### D1 — Fri Jun 19, 19:00

```
One for tatay. One for you. Both pairs, ₱998.

This is how we move sa Dubery: 2-pair bundle, free delivery, free COD — kahit saan ka sa Pilipinas.

Outback Black for him (clean, classic, won't go out of style).
Bandits Tortoise for you (slim square, OOTD-ready).

Mix-and-match any two pairs in the shop. Father's Day 06.21 — last day to order with time to spare is today.

→ duberymnl.com/products
```

### B1 — Sat Jun 20, 12:00

```
Para sa tito who already has everything.

Wallet, keys, watch — all sorted. Pero polarized shades na actually fits his face? That's the gap.

D918 Outback Black. Square frame, matte finish, polarized lenses na talagang humaharang sa windshield glare. Quiet drip, hindi try-hard.

Get the 2-pair bundle (₱998) — keep one, give one. Walang delivery fee, walang COD fee.

Father's Day 06.21 — last call. Order today.

→ duberymnl.com/products/?series=outback
```

## Bench / not used

- **FD V2** — redundant with V1 (same giving-moment family).
- **Stories rotation** — skipped today. Pool has 70 picks; adding 1 = ~6%/day odds it shows. If you want a guaranteed FD-day story, manually post FD V3 still life on Sun Jun 21 morning via `python tools/facebook/post_story.py --image contents/new/2026-06-15_BESPOKE-OUTBACK-BLACK-FD-V3-02-GIFT.png`.

## RA decisions still open

1. **Unpause the existing FD carousel?** Or keep it dark and let organic carry it? My recommendation: unpause Tue Jun 17 morning so it runs the full 5-day window into Father's Day.
2. **FD-morning story?** Manual post FD V3 on Sun Jun 21 ~9am PHT? (One-line command above.)

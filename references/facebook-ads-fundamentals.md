# Facebook Ads Fundamentals — DuberyMNL

*Documented 2026-03-18. Reference for future ad campaign planning.*

---

## Structure

```
Campaign (goal)
    └── Ad Set (who sees it + budget)
            └── Ad (image + caption + CTA)
```

One Campaign → multiple Ad Sets → multiple Ads. Facebook tests them and puts budget behind winners.

---

## Objective

For DuberyMNL: **Traffic** or **Leads** -- both point people to duberymnl.vercel.app.

Never use:
- Engagement (optimizes for likes/comments, not orders)
- Awareness (shows to as many as possible regardless of intent)

---

## The Only Metric That Matters Right Now

**Cost per order** -- how much ad spend to get one form submission.

Likes and follows are side effects of real buyers. Never run ads to chase them.

---

## Budget

- Start: ₱100-200/day
- Type: Daily budget (not lifetime) for always-on ads
- Learning phase: first 7 days -- do NOT touch budget or targeting while Facebook learns
- Facebook may spend up to 25% over daily budget on good days, compensates on slow days -- normal behavior

---

## Targeting

- Location: Metro Manila
- Age: 18-40
- Gender: All (let Facebook find who actually buys)
- Interests: broad, or 2-3 max -- don't stack filters
- **Advantage+ Audience** (Facebook AI targeting) is a valid starting point for small budgets

**Key principle: the creative does the targeting, not the interest checkboxes.**
A moto camping caption attracts moto people without needing an "motorcycles" interest filter.

### Audience types (for later)
- **Core Audiences** -- manual interest/demo targeting (where we start)
- **Lookalike Audiences** -- Facebook finds people similar to past buyers (needs buyer data first)
- **Advantage+** -- AI handles targeting with minimal input

---

## The Creative

Priority order:
1. **Image** -- stops the scroll. 1.5 seconds.
2. **First caption line** -- holds attention. Only line visible before "See more."
3. **CTA button** -- converts. Use **Shop Now** or **Order Now**.

### What stops scrolls in PH market
- Faces with real expressions (not posing)
- High contrast -- bright product, dramatic background
- Unexpected text overlay in first 3 words
- Scenes that feel real, not stock

### What kills scroll-stop
- White background product shots (looks like Lazada)
- Generic lifestyle imagery
- Too much text in the image

### CTA button
- Use: Shop Now, Order Now
- Never: Learn More (that's for considered purchases, not ₱699 impulse buys)

---

## DuberyMNL Ad Flow

```
Caption (WF1) → Image (WF2) → Ad creative
                                    ↓
                          duberymnl.vercel.app
                                    ↓
                            Order form → Google Sheet
                                    ↓
                              SMS confirmation (Semaphore)
```

---

## Launch Readiness

- 24 ads on duberymnl.vercel.app: **ready to run now**
- New 15-caption batch (20260318): needs WF2 images first
- WF2 pipeline: tools exist, end-to-end automation not yet wired

**Recommended:** Launch ads on existing 24 first. Build WF2 in parallel.

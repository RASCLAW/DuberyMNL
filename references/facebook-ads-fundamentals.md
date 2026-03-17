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

---

## Part 5 -- Launching Inside Meta Ads Manager

*Step-by-step. Click-by-click.*

### Step 1: Get to Ads Manager

Go to: **business.facebook.com → Meta Ads Manager**

Top-left: click the green **+ Create** button.

### Step 2: Pick Campaign Objective

Select **Traffic** → Click **Continue**.

### Step 3: Name the Campaign

```
DuberyMNL | Traffic | Mar 2026
```

Leave everything else at default. Click **Next**.

### Step 4: Configure the Ad Set

**A. Destination:** Website → `https://duberymnl.vercel.app`

**B. Budget:**
- Daily budget: ₱150
- Start date: today or tomorrow
- No end date

**C. Audience:**
- Location: Metro Manila
- Age: 18-40
- Gender: All
- Interests: broad, or 1-2 max (e.g. "sunglasses", "outdoor activities")
- Do not stack multiple interest filters -- small budget needs wide net

**D. Placements:** Advantage+ Placements (let Facebook decide -- Feed, Reels, Stories)

Click **Next**.

### Step 5: Build Each Ad (repeat for each of 3-5 ads)

**Naming convention:**
```
Ad 01 | Product | Outdoor Trail
Ad 02 | Person | Moto Camping
Ad 03 | Bundle | Crew Ride
```

**Per ad:**
- Facebook Page: Dubery MNL
- Format: Single Image
- Image: upload (1:1 square or 4:5 portrait)
- Primary text: paste caption
- Headline: 5-7 words (e.g. "Polarized. Built for the Road.")
- CTA button: **Shop Now**
- URL: `https://duberymnl.vercel.app`

Add all 3-5 ads under the same ad set before publishing.

### Step 6: Review and Publish

Check:
- Budget correct?
- URL correct? (click to verify)
- All ads present?

Click **Publish**. Meta reviews within 1-24 hours. Once approved: **Active**.

### After Launch -- What to Watch (Day 3+)

| Metric | What it tells you |
|---|---|
| CTR | Are people clicking? (>1% is decent) |
| CPC | Cost per click (lower = better) |
| Reach | Unique people who saw the ad |
| Spend | How budget is distributed across ads |

After 7 days: kill underperformers. Scale the winner. Do NOT touch anything during the learning phase.

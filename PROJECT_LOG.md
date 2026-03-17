# DuberyMNL Project Log

Running log of progress across all workflows. Updated at each session closeout.

---

## Pipeline Overview
```
WF1 Caption Gen → Review → WF2 Image Gen → WF3a Organic FB Post
                                          → WF3b Meta Ads (parallel)
```

---

## WF1 — Caption Generation
**Status: COMPLETE**
- 15 captions/batch, 7-8 vibes, 1-2 per vibe
- Bundle quota: 3, elevated tone: 2-3
- Output: Google Sheet (captions tab)

## Caption Review Server
**Status: COMPLETE — CAPTION REVIEW DONE. UPGRADES PLANNED.**
- Flask app, runs locally via ngrok tunnel
- Star ratings, notes, product recommendations (cascading dropdowns)
- Rejected rows auto-move to rejected_captions tab
- Relaunch: `bash tools/captions/start_review.sh`
- Caption review complete (batch reviewed and processed)
- Planned upgrades (not yet built):
  - Sheet tabs: WF1 writes to `pending`, review moves approved to `captions`, feedback saved to `feedback`
  - Two input boxes: comment (→ WF2 image brief) + feedback (→ next WF1 batch)
  - Overlay tick boxes: Header, Header 2, Price, Accessories (PRODUCT only), Bubble
  - Feedback is batch-level (shapes next WF1 run, not per-caption regeneration)

## WF2 — Image Generation
**Status: SKILL REBUILT + ARCHITECTURE LOCKED**

### Session 2026-03-15 — Skill rebuild + data architecture
- dubery-prompt-writer rebuilt from git original (d836b34) as clean base
- SKILL_maybe.md = parked over-engineered version (kept for reference)
- Improvements grafted onto original:
  - Step 1 rewritten: 5 steps, angle inherited from WF1 (not re-derived), AIDA map preserved
  - Product primacy rule, 4:5 format rule, bottom-right clear zone added
  - Angle inheritance table: maps 6 angles to visual energy
  - 60/40 batch target, PERSON rule tightened (TYPE A only when human experience is undeniable hook)
  - COD + CTA as auto-always overlays
  - Auto-conditional: deal badge (2+ products), series label (same family)
  - Checkbox-driven overlays: headline, price, bubble, accessories — read from overlays field in captions.json
  - Language rule + headline rule added
- dubery-prompt-parser skill created — converts NB2 prompts to structured JSON
- Data architecture locked: captions.json = primary store for full pipeline; Sheets written only at WF3
- WF1→WF2 handoff fixed: angle, hook_type, creative_hypothesis now survive to WF2 (were previously dropped)
- Workflow docs updated: caption_generation.md + image_generation.md now reference captions.json
- Overlays: review_server.py already has checkbox UI (headline, price, bubble, accessories) — confirmed working

**Previous status:**
- Architecture confirmed: WF2a picks caption (5-star pool → random) → composes NB2 prompt → saves to col K → Status=PROMPT_READY
- WF2b reads PROMPT_READY rows → generates image → writes Image_URL col L + Image_Status=DONE col M
- workflows/image_generation.md updated to reflect final architecture
- Prompt generation tested on captions: 20260309-001, 20260309-015, 20260309-016, 20260309-006
- Opus confirmed as WF2a model (richer scene detail, better lighting, more cinematic vs Sonnet)
- Skill rules updated (cumulative):
  - Portrait format: 4:5 verbatim at end of SCENE
  - Product bubble: 3/4+ body shot → freshly rendered close-up beside ₱699/POLARIZED; no white bg, no reference photo paste; Dubery logo must be legible inside bubble
  - Language: English overlays primary, Taglish ok, pure Tagalog rarely
  - Headline: independent billboard copy, max 5 words, NOT a caption restatement
  - Model tag: [MODEL: SONNET] or [MODEL: OPUS] prepended to every prompt
  - Safe zone: bottom 5% clear of all overlays (kie.ai watermark mitigation)
  - Product primacy: scene exists to serve product; sparse scene = NB2 focuses on product
  - Batch composition: 60% PRODUCT / 40% PERSON
- Dual-model workflow confirmed: both Sonnet + Opus run per caption; RA picks winner in Gemini
- Sheet structure updated: K=Prompt_Sonnet, N=Prompt_Opus (both saved per caption)
- Model scores: Opus 3 — Sonnet 1 — Tie 1. Opus consistently wins on scene richness and prop storytelling.
- Skill rule added: Bottom bar (replaces safe zone rule). Full-width dark strip flush at bottom, all overlays sit above it. Resolves kie.ai watermark overlap.
- Skill rule added: Explicit approval required before editing any skill file.
- Captions with PROMPT_READY: 006 (Sonnet), 008 (Opus), 010 (Opus), 014 (Tie), 017 (Opus)
- Next: continue batch prompts for remaining APPROVED captions, then sheet restructure (remove Generated_At + Hashtags cols)

## Landing Page — dubery-landing/
**Status: BUILT — READY FOR REAL TRAFFIC TESTING**

### Session 2026-03-15 — Initial build
- Mobile-first direct-response landing page for Facebook ads
- Vanilla HTML/CSS/JS, no frameworks — `dubery-landing/` folder in project root
- 7 sections: Hero → Benefits → Product Showcase → Offer Cards → Delivery → Final CTA → Order Modal
- Dark theme: `#111111` bg, `#ff6a00` accent, Poppins + Inter typography
- Order modal: slides up on mobile, centered on desktop
- Dynamic product picker: variant dropdown + thumbnail preview + qty stepper
- Live order summary + form validation + confirmation message on submit
- All 10 product variants mapped with real PNG images from Downloads
- Hero: dubery_5.jpg ("Stop Squinting" lifestyle shot)
- Showcase: dubery_14.jpg (multi-variant bundle flat lay)
- Assets: `dubery-landing/assets/` — all PNGs + hero.jpg + bundle.jpg

**Next steps:**
- Add Dubery logo to hero or nav area
- Connect form to Google Sheets or email via a backend/n8n trigger
- A/B test hero headline variants

---

## WF3a — Organic Facebook Post
**Status: NOT STARTED**
- Tool: tools/meta/post_to_page.py (to be built)
- Inputs: approved caption + generated image
- Requires: pages_manage_posts permission (pending Meta app approval)

## WF3b — Meta Ads
**Status: NOT STARTED**
- Parallel to WF3a
- Uses same caption + image assets
- Requires: confirmed ad account + campaign setup

---

## Session Log

### 2026-03-17 (Session 25) — Landing Page: Ad Mapping, Vercel Deploy, Variant Fixes

**What was done:**
- Audited all 28 ads in `captions.json` against product refs and hero shots
- Removed 6 Classic series ads from `captions.json` (out of stock) → parked in `captions-classic.json`
- Moved `id: 31` (Purple variant) to `captions-classic.json`
- Fixed `id: 24` product_ref: Rasta Red → Outback Red
- Fixed `id: 32` product_ref: Rasta Red (Gold/Amber) → Rasta Red
- Fixed `id: 23` product_ref: Mixed (bundle display) → Rasta Brown, Rasta Red, Outback Green, Bandits Camo (carousel)
- **Deployed landing page to Vercel** → [duberymnl.vercel.app](https://duberymnl.vercel.app)
- Split `Bandits – Green Blue` (single variant) into two: `Bandits – Green` (idx 8) and `Bandits – Blue` (idx 9); Tortoise shifted to idx 10
- Updated VARIANTS array + PRODUCT_IMAGE_MAP variantIdx accordingly
- Built + removed hero swipe navigation (RA decided against it)
- Emailed full Ad ID → Product Ref mapping to sarinasmedia+claude@gmail.com

**Active ads: 22** (captions.json)
**Parked ads: 7** (captions-classic.json — restore when Classic series restocks)

**Pending (deferred to tonight):**
- Add missing picker thumbnails: Outback Red, Outback Blue, Bandits Green, Bandits Blue, Bandits Tortoise (single-angle shots saved in Screenshots + Downloads)
- Restrict Google Maps API key to `duberymnl.vercel.app` domain
- Connect order form to Google Apps Script (RA manual step) → fill `FORM_ENDPOINT` in script.js

### 2026-03-16 (Session 21) — Landing Page UX Polish (Floating FB Button + Card Preview)

**What was built:**
- Floating Facebook widget button (top-left, fixed position, scrolls with page)
  - Facebook blue pill, 70% opacity, restores to full on hover
  - Links to `facebook.com/duberymnl`
  - Label: "Visit our profile"
- Product card image now tappable — opens full image preview overlay (same behavior as variant thumbnails)
  - `cursor: zoom-in` hint on hover
  - Wired to existing `openImgPreview()` — no new overlay code needed

**Files changed:**
- `dubery-landing/index.html` — floating FB button HTML
- `dubery-landing/styles.css` — `.fb-float-btn` styles
- `dubery-landing/script.js` — product card click handler

**Pending (unchanged from last session):**
- Vercel deploy → live URL → restrict Google Maps API key to domain
- Google Apps Script setup (RA manual) → fill `FORM_ENDPOINT` in script.js
- Update stage_ad.py CTA to landing page URL (after Vercel deploy)
- Hero background image fit on mobile
- Update status.py — add "Has ad staged" line

---

### 2026-03-16 (Session 20) — Google Maps Autocomplete on Address Field

**What was built:**
- Google Maps Places Autocomplete on delivery address field
- API: Maps JavaScript API + Places API enabled in Google Cloud Console
- Restricted to Philippines only (`componentRestrictions: { country: 'ph' }`)
- All place types included (streets + establishments like Venice Grand Canal, Wells Fargo, etc.)
- Solid white dropdown (was semi-transparent — `--surface` is `rgba(255,255,255,0.55)`)
- Browser autofill disabled (`autocomplete="nope"` — browsers ignore `"off"`)
- Favicon added: dubery-logo.png shown in browser tab
- Fixed `hero.jpg` 404 → renamed to `hero.png` across all references
- Fixed `initMaps` not found in strict mode → `window.initMaps = function()`
- Stayed on old `google.maps.places.Autocomplete` (new `PlaceAutocompleteElement` triggers popup/redirect — not ready for use)

**Google Cloud setup (RA did manually):**
- API key: AIzaSyBWM01ElyeTUTBoTrlR2TxY7Pu8Po_f-MA
- Enabled: Maps JavaScript API, Places API, Places API (New)
- TODO: Restrict key to Vercel domain after deploy

**Pending:**
- Vercel deploy → live URL → restrict API key to domain
- Google Apps Script setup (RA manual)
- Update stage_ad.py CTA to landing page URL

---

### 2026-03-15 (Session 18) — Landing Page UI Polish (dubery-landing/)

**Hero image:**
- Swapped hero to dubery_32.jpg (portrait 4:5, warm golden sunset)
- Fixed background-position to center 30% for portrait fit
- hero.jpg is default fallback; ?id=N loads assets/ads/dubery_N.jpg dynamically

**Layout change:**
- Moved headline + subheadline out of hero overlay → below hero in .hero-below div
- Logo removed from hero
- Hero is now clean full-bleed image only

**Dynamic accent system (script.js):**
- extractAndApplyAccent(): uses Canvas API to scan hero image pixels, finds most saturated color
- applyTheme(): sets --accent, --accent-hover, --accent-active, --accent-glow CSS variables
- Also sets --surface, --surface-raised, --surface-border with accent hue tints
- Confirmed working: hue=41 sat=88% → accent=#e6a20f for golden sunset image

**Dynamic background system:**
- Added #page-bg fixed div behind all sections
- Background = blurred hero image (blur 32px, brightness 1.1, saturate 0.5) + white overlay
- Switches automatically when ad changes via ?id=
- Creates visual continuity between hero and content sections

**Light theme:**
- Switched from dark (#111) to light (transparent bg, white frosted surfaces)
- Text colors: --text: #111111, --text-muted: #444444
- Feature items now have card treatment: surface bg + border + border-radius + backdrop-filter blur
- .btn-outline updated: accent color border + text (was white/transparent)

**Mobile preview tool:**
- preview.html updated with "Simulate Ad" dropdown — all 20 available ad IDs
- Tests ?id=N URL parameter locally without needing Vercel deploy

**Pending:**
- Vercel deploy → live URL
- Google Apps Script setup (RA manual)
- Update stage_ad.py CTA to landing page URL

---

### 2026-03-15 (Session 15) — Drive consolidation + pipeline housekeeping

**What was built:**
- `tools/status.py` — CLI pipeline snapshot (`python tools/status.py`), shows all status counts, has_image, has_prompt, unmapped files
- `tools/image_gen/image_review_server.py` — reject now physically moves image to `output/images/rejected/`
- `dubery-caption-gen/SKILL.md` — WF1 feedback loop added (step 0: reads rejected_captions.json before generating, avoids repeated vibe/angle combos, uses notes as negative creative direction)
- `.claude/skills/dubery-prompt-writer/overlay-formula.md` — 8 design rules reverse-engineered from 8 approved ads (badge color = lens accent, shape = concept energy, 6 POLARIZED treatments, delivery zone styles, headline typography, logo placement)
- `dubery-prompt-writer/SKILL.md` — overlay section rebuilt to reference overlay-formula.md; pills are the correct default for lifestyle shots (old rule said "never pills" — wrong)

**Pipeline changes:**
- Gemini batch (#23-#32) catalogued and added to pipeline.json with full metadata
- 6 legacy images (#33-#38) reverse-engineered from visual content and added
- Caption #26 deleted (duplicate of #12 — same image, same vibe)
- All 35 entries synced to Notion + Sheet

**Drive cleanup:**
- All 35 images consolidated into single folder: `My Drive → DuberyMNL → Generated Images`
- All image URLs normalized to thumbnail format (`drive.google.com/thumbnail?id=...&sz=w1000`)
- 24 orphan/duplicate files deleted from Drive (2 duplicates + 12 unmapped PNGs + 10 legacy dated JPGs)
- 6 Sample Content files moved to `My Drive → DuberyMNL → Sample Content`
- OAuth token re-authorized with Drive + Sheets scopes (was Sheets-only, caused upload failures)

**Milestones:**
- Pipeline fully in sync across all 4 locations: local files + Drive + Notion + Google Sheet
- 34 IMAGE_APPROVED, 1 IMAGE_REJECTED (#2), 35 total tracked
- Drive folder is clean and organized for the first time

**Struggles:**
- token.json only had Sheets scope — Drive uploads failed with 403 until re-auth
- Re-auth requires browser interaction from WSL (can't auto-open browser) — had to manually copy URL
- Accidentally deleted 6 images RA wanted to keep — restored from Drive trash manually
- "The user" vs "RA" — noted and saved to memory

**Next:**
- WF3a: post_to_page.py — blocked on Meta `pages_manage_posts` permission
- IMAGE_REJECTED #2 — needs WF2a retry with rejection feedback
- 7 entries still missing local image files (dubery_1, 8, 9, 10, 11, 12 stored as Gemini PNGs on Drive, not renamed locally)

---

### 2026-03-15 (Session 18) — Comic Strip Format + Kiko Character Bible

**What was built:**

**2 new skills added:**
- `.claude/skills/dubery-infographic-ad/` — DuberyMNL hand-drawn callout bubble infographic format. Design DNA extracted from original Dubery Bandits ad (beach backdrop, granite surface, 3 oval callouts, Rule of Three, sparkle accent). Includes SKILL.md + README.md.
- `.claude/skills/ad-reverse-engineer/` — General-purpose skill for reverse-engineering any ad image into a structured NB2 prompt. 4-layer method: Backdrop / Hero / Graphics / Text. Includes SKILL.md + README.md.

**Ad reverse-engineering:**
- Reverse-engineered SAMPLE CONTENT 1 (Dubery Bandit Camo, comic strip style) — extracted full layer breakdown and design rules
- Identified new content type: Filipino street culture comic strip (wide horizontal, 3-character contrast panel, hand-drawn callouts, speech bubble)

**Comic strip format tested:**
- Concept: Beach barkada, Rasta Red, dreadlock protagonist
- First output: good structure, wrong orientation (16:9), no dreadlocks, too many bubbles
- Refined: 4:5 portrait, one speech bubble only, relaxed tone, Kiko character introduced
- `.tmp/comic_strip_rasta_red.json` — current working prompt for the beach strip

**Kiko character bible created:**
- Protagonist: Kiko, 24, Filipino, short thin dreadlocks (chin length, loose, natural), Dubery Rasta Red, calm half-smile, "hindi nagpapanic" archetype
- Barkada: Dodong (foil, over-reactor) + Ces (practical one)
- Universe: "KIKO" / "Si Kiko at ang Mundo" — Manila is chaotic, Kiko moves through it calm
- Strip formula locked: Setup (everyone suffers) → Contrast (Kiko is fine) → Punchline (one understated line)
- `.tmp/kiko_character_bible.json` — full character specs + prompt rules
- `characters/kiko_reference.png` — approved character portrait from Gemini
- `characters/kiko_description.json` — locked visual description for consistent generation

**Day 0 arc planned:**
- 8-panel origin story: night before swimming trip → discovers DuberyMNL on FB → landing page → order → COD → unboxing → ready
- Doubles as a live customer journey map (discovery, landing page, COD, delivery, unboxing)
- Panel generation priority: Panel 1 first (establishes Kiko's look), then Panel 7 (unboxing), then Panel 2 (scroll — direct FB ad)

**Milestones:**
- Comic strip format proven viable — first test output was strong
- Kiko locked as DuberyMNL's recurring comic protagonist
- 2 new reusable skills in the toolkit

**Next:**
- Generate Day 0 panels starting with Panel 1
- Lock `dubery-comic-strip` as a formal skill once format is fully proven
- Add Kiko reference image as `image_input` in all future comic strip prompts for consistency

---

### 2026-03-17 (Session 24) — Landing Page Major Upgrade + Facebook Page First Post

**What was built:**

**Facebook page (done by RA + assisted by Claude):**
- Cover photo updated (Gemini-generated Dubery MNL image)
- Bio rewritten: "Polarized sunglasses built for Manila. Starting at ₱699 -- same-day delivery, COD."
- Website field: `https://duberymnl.vercel.app`
- Action button: Shop Now → landing page
- First organic post in years: infographic (beach scene, 3 callouts), Taglish quick-facts caption
  - Caption: "Regular vs. polarized. Here's the difference: Glare? Wala na. Eye strain? Finish na. UV rays? Blocked."

**Landing page -- major upgrades:**

Product card:
- All product hero shots added (Outback Black/Blue/Red, Rasta Red/Brown, Bandits Camo/Black/Blue/Green/Tortoise)
- `PRODUCT_IMAGE_MAP` fully updated with all new filenames + `desc` + `variantIdx` fields
- `resolveProductImage` updated to return full entry (was stripping `desc` + `variantIdx`)
- Default hero background: `OUTBACK - BLACK - HERO SHOT.png`
- Default footer logo: `dubery-logo.png` (transparent, blends with black footer)

Multi-product carousel:
- `resolveMultiProducts()` -- detects comma-separated product refs, dedupes by image
- `renderProductCarousel()` -- builds swipeable carousel with dots + tap-to-preview per slide
- `initCarousel()` -- touch swipe + dot nav, updates description on slide change
- `prePopulatePicker()` -- auto-selects featured variants in order modal with qty 1 each
- Description updates per slide (swipe left/right to see each product's desc)
- Carousel triggers only for multi-product captions; single product stays as-is
- Tested on `?id=17` (DALAWANG PAIRS. ISANG DEAL. -- Rasta Red + Rasta Brown)

Proof of purchase strip:
- 6 proof photos added: proof1-6.jpg (COD packages, boxes, LBC counter)
- Rotated proof3, proof4 (then proof4 rotated back), proof5 rotated right
- Order: proof5 → proof3 → proof2 → proof1 → proof4 → proof6
- Section background set to solid `var(--bg)` to fix washed-out opacity issue

Order picker:
- Default thumbnail: `logo new.png` (shown before variant selected)
- `variant-selected` CSS class: switches from `contain` (logo) to `cover` (product) on selection
- Pre-populated from `prePopulatePicker` when ad caption loads

Pricing section:
- Bundle card moved first (was second)
- FREE DELIVERY green stamp added to bundle card
- `pricing-card` gets `align-items: flex-start` so stamp doesn't stretch full width
- `.pricing-card .btn { width: 100% }` keeps ORDER NOW button full width

Footer:
- Background: `#000` (full black)
- Logo: `dubery-logo.png` (transparent bg, 120px, no padding)
- Border removed

Spacing cleanup:
- `.lens-proof` padding: 60px → 24px (leaner)
- `.proof-strip` padding-top: 48px → 16px
- `.pricing.section` padding-top: 16px (override)
- `.final-cta.section` padding-top: 16px (override)

Missing assets fixed:
- `hero.png` (was 404) -- copied from OUTBACK - BLACK - HERO SHOT.png
- `dubery-logo.png` (was 404) -- downloaded from Drive (ID: 1kJiHQd81IofqDcDcATfN62nzQDUSC89D)
- `dubery_17.jpg` -- downloaded from Drive (ID: 1GNw5UVgDz0X_QS0MO7Nb7QwniR9pJEkc)
- Caption #17 added to `data/captions.json`

**Deployed:**
- Git pushed: `ea740ab`
- Vercel: `https://duberymnl.vercel.app` (live, updated)

**Milestones:**
- Facebook page is now active and presentable for the first time in years
- Landing page now has full product hero shots, social proof, working carousel
- All product descriptions written (10 variants)
- Multi-product ads now show carousel + auto-populate order modal

**Next:**
- 3-5 more FB posts before running paid traffic (feed is thin with 1 post)
- Google Apps Script setup (RA manual) → fill `FORM_ENDPOINT` in script.js
- stage_ad.py CTA swap: Messenger → `https://duberymnl.vercel.app?id=[id]`
- Outback Green hero shot missing (using old `outback-green.png` fallback)
- Carousel content direction for homepage: variants / social proof / lifestyle (TBD)

---

### 2026-03-16 (Session 23) — Facebook Page Update + Landing Page Carousel Planning

**What was done:**
- Updated Dubery MNL Facebook page for the first time in years:
  - New cover photo: Dubery MNL logo on black bg (clean, brand-forward)
  - Bio rewritten: from broken auto-translated copy to "Polarized sunglasses built for Manila. Starting at ₱699 -- same-day delivery, COD."
  - Website field: `https://duberymnl.vercel.app` (live landing page)
  - Action button: "Shop Now" → landing page
- First organic Facebook post published in years:
  - Used the infographic image (beach scene, 3 callout bubbles: Polarized Lenses, UV400 Protection, Lightweight Frame)
  - Caption: Option C (quick facts, Taglish punchlines) -- "Regular vs. polarized. Here's the difference: Glare? Wala na. Eye strain? Finish na. UV rays? Blocked. That's what you're getting."
  - Educational/brand-building angle, not sales-focused

**Carousel planning started:**
- RA asked about adding a carousel to the landing page
- Content direction not yet decided -- candidates: product variants, social proof, lifestyle shots
- Pending: RA to confirm content direction before build starts

**Milestones:**
- Facebook page now active and presentable -- cover, bio, website, and first post all live
- Page is ready to receive traffic from ads and landing page

**Next:**
- Decide carousel content direction (variants / social proof / lifestyle)
- 3-5 more FB posts before running paid ads (feed looks thin with 1 post)
- Google Apps Script setup (RA manual) → fill FORM_ENDPOINT in script.js
- stage_ad.py CTA swap: Messenger → `https://duberymnl.vercel.app`

---

### 2026-03-16 (Session 19) — Day 0 Arc: Cover + Panels 1 & 2

**What was built:**

**Storyboard locked:**
- `.tmp/kiko_day0_storyboard.json` — full 8-panel Day 0 arc documented with scene, dialogue, tone, and visual notes
- Arc premise: night before swimming trip → FB ad → landing page → COD order → delivery → unboxing → ready

**Panel 1 (v1 → v2):**
- v1 generated and approved — Kiko's look confirmed solid, scene reads correctly
- Feedback: room too bare, needs identity elements to tell who Kiko is
- v2 prompt updated: added tsinelas, electric fan, reggae poster, calendar (date circled), Bluetooth speaker, paperback, charging cable
- v2 generated — room now tells Kiko's story before the plot does. Strong improvement.

**Cover — "KIKO: Issue 01":**
- Concept: split composition — dark bedroom (left) / bright beach (right), Kiko centered with Rasta Red
- Typography: "KIKO" title + "Day 0: Bago pa ang Bukas" subtitle + DUBERY MNL / ISSUE 01 bottom strip
- Generated and approved — looks like a real komiks cover
- Files: `.tmp/kiko_day0_cover_prompt.txt` + `.tmp/kiko_day0_cover.json`

**Panel 2 prompt built:**
- Scene: Kiko in bed scrolling Facebook, DuberyMNL ad appears in feed, thumb stops
- Key visual: phone screen showing Rasta Red ad + "Same-day delivery. Metro Manila. COD."
- Caption: "Sinabi mo?" — quiet discovery, not excitement
- Files: `.tmp/kiko_day0_panel2_prompt.txt` + `.tmp/kiko_day0_panel2.json`

**Workflow rule added:**
- Memory: always run parser after generating prompt.txt — both outputs required (plain text + structured JSON)

**Notes on Kiko's look (carry forward):**
- Dreadlocks are rendering slightly long (shoulder-length) vs. spec (chin-length) — consistent across cover + Panel 1
- If this becomes the locked look, update the spec. If not, add: "Dreadlocks end exactly at chin level, thin and sparse."

**Next:**
- Panel 2 to be generated in Gemini
- Continue arc: Panel 3 (landing page), Panel 4 (order), Panel 5 (confirmation), Panel 6 (rider), Panel 7 (unboxing), Panel 8 (ready)
- Panel 7 is the most emotional beat and highest-priority standalone ad unit

---

### Session 17 — Landing Page Template Build

**tools/landing/export_captions.py** — built and run:
- Exports 28 IMAGE_APPROVED entries to `dubery-landing/data/captions.json`
- Copies `output/images/dubery_[id].jpg` → `dubery-landing/assets/ads/`
- 6 skipped (IDs 16-21, no local image)
- Run: `python3 tools/landing/export_captions.py`

**Landing page template built (3 files rewritten):**
- `index.html` — reference design layout: full-bleed hero, 2-col features, lens proof, delivery strip, pricing, modal
- `styles.css` — Barlow Condensed headlines, orange accent (#E8500A), dark editorial
- `script.js` — dynamic `?id=` loading + real form submit to `FORM_ENDPOINT` constant

Assets downloaded from Drive Misc folder → `assets/dubery-logo.png`, `assets/dubery-mnl-logo.png`

Dynamic JS: `?id=5` → swaps hero bg to `assets/ads/dubery_5.jpg` + loads headline/vibe from `data/captions.json`

`FORM_ENDPOINT` = empty string (template mode) — fill after Google Apps Script deploy

Preview: `cd dubery-landing && python3 -m http.server 8080`

**Pending fixes (next session):**
- Hero background image fit on mobile (sizing/positioning)
- Review in Chrome DevTools device mode
- Google Apps Script setup (RA manual) → fill FORM_ENDPOINT
- Vercel deploy → live URL → update stage_ad.py CTA

---

### 2026-03-15 (Session 16) — WF3b Meta Ads + Dynamic Landing Page

**What was built / decided:**
- Researched full Meta Graph API + Instagram Graph API + TikTok Content Posting API capabilities
- Confirmed: organic posting, Reels, Stories require separate tokens/permissions; reacting/commenting on external posts not possible in any API
- `tools/meta_ads/create_campaign.py` — CTA fixed: SHOP_NOW → SEND_MESSAGE (Messenger), destination_type FACEBOOK → MESSENGER, optimization_goal LINK_CLICKS → CONVERSATIONS
- `tools/meta_ads/stage_ad.py` — new orchestrator: reads pipeline.json → uploads image → creates PAUSED campaign → writes campaign IDs back to pipeline.json → syncs Notion
- `tools/landing/` — new directory created for landing page tools
- `dubery-landing/data/` + `dubery-landing/assets/ads/` — new directories for dynamic landing page data
- Plan finalized for dynamic landing page redesign (matches premium reference design)

**Key decisions:**
- Notion is the primary database; Google Sheet is backup mirror only
- Landing page: single HTML, dynamic via `?id=5` URL param, JS swaps hero image + headline per caption
- Order form backend: Google Sheet via Google Apps Script webhook (RA sets up manually)
- Hosting: Vercel (free static deploy)
- CTA: both "Order via Form" + "Chat on Messenger"
- Meta Ads CTA will swap from Messenger → landing page URL once deployed

**Landing page plan (pending execution):**
- Full redesign of `dubery-landing/` — bold lifestyle hero, features, polarized lens section, delivery, pricing
- `tools/landing/export_captions.py` — generates captions.json + copies ad images to assets/ads/
- Deploy via `npx vercel --prod` from dubery-landing/
- After URL is live: update stage_ad.py to point to `?id=[caption_id]`

**Milestones:**
- WF3b architecture fully designed and partially built
- Landing page strategy locked: dynamic per-ad personalization
- Explored full social media API landscape (FB, IG, TikTok)

**Struggles:**
- Realized mid-build that Meta Ads need a destination URL → needed landing page first
- stage_ad.py built but Meta Ads CTA still points to Messenger (interim until landing page live)

**Next:**
- Execute landing page redesign + export_captions.py
- Deploy to Vercel → get live URL
- Update stage_ad.py CTA to landing page
- Complete status.py update (Has ad staged line)
- WF3a organic posting (deprioritized — Meta Ads first)
- IMAGE_REJECTED #2 — needs WF2a retry

---

### 2026-03-10 (Session 1 -- from work via VSCode tunnel)
- EA second brain initialized at /home/ra/
- facts.md created, auto-loads via CLAUDE.md
- FIGGY backlog cleaned, principles + self-improvement loop adapted
- Journal system created at journal/2026/03.md
- Decision log upgraded to two-tier format (one-liner + ADR)
- PROJECT_LOG.md created (this file)
- Session closeout + trigger words added to EA CLAUDE.md
- Resume pulled from Drive -- needs AI-focused rewrite (parked until DuberyMNL done)
- Brand guidelines: none exist yet -- to be defined before WF2 scales up
- No public web presence for RA yet -- LinkedIn + GitHub needed post-DuberyMNL

### 2026-03-13 (Session 4)
- Caption review confirmed complete (was pending last session)
- Locked sheet tab architecture: pending / captions / rejected_captions / feedback
- Locked WF2a/WF2b split logic:
  - WF2a picks caption (5-star pool random, fallback 4-star) → composes prompt → Status=PROMPT_READY
  - WF2b processes PROMPT_READY → generates image → Image_Status=DONE
- Added Image_Status column (col M) to captions sheet structure
- Updated workflows/image_generation.md to reflect final architecture
- Tested WF2a prompt generation on 3 captions with Opus model -- all strong output
- Skill updates to dubery-prompt-writer:
  - Portrait format rule added (4:5, verbatim in SCENE)
  - Product bubble rule: full/3/4 body shot → floating bubble beside ₱699 or POLARIZED label
  - Language rule: English overlays primary, Taglish allowed, Tagalog rarely
  - Headline rule: independent billboard copy, NOT caption restatement, max 5 words
- Next: regenerate 20260309-015 with updated rules → save prompts to sheet → proceed to WF2b

### 2026-03-12 (Session 3 -- from work, day shift)
- Read both n8n workflows (Caption Generator + Image Generator) for full context
- Confirmed prompt format: labeled sections plain text (not NB2 JSON schema)
- Confirmed reference image mechanism: `image_input` Drive URLs passed to kie.ai API directly
- No Pillow overlay needed -- NB2 handles scene + all text + product via reference image
- Created dubery-caption-gen skill (WF1 CCO brain, 182 lines)
- Created dubery-prompt-writer skill (WF2 prompt composer, 233 lines)
- Both skills audited with skill-builder: frontmatter fixed, disable-model-invocation set
- DuberyMNL Content sheet (n8n) ID: 1OwWHwlhHfFgMMokMS3GGtH1fHptahbg2OscB07c8bkk (reference only)
- n8n workflows scrapped -- going full agentic (Claude Code as orchestrator)

### 2026-03-11 (Session 2 -- from work, night shift ~midnight)
- No DuberyMNL build work -- side session focused on EA personal tooling
- Discovered Google Workspace CLI (gws) v0.9.1 -- official Google tool, just released
- Installed gws CLI on home PC (`npm install -g @googleworkspace/cli`)
- Configured credentials.json (~/.config/gws/client_secret.json)
- Auth attempted -- blocked by OAuth localhost redirect not working via VSCode tunnel
- Parked: run `gws auth login` locally when home tonight
- Once authed: gws can access Gmail + Drive + Calendar + Docs from terminal (I operate it as EA)

### 2026-03-15 (Session 14) — File consolidation + Google Sheet

Local file consolidation:
- captions.json + pending_post.json merged into single pipeline.json (20 active captions)
- rejected_captions.json retained as discard pile
- All 6 tools updated: generate_kie.py, review_server.py, image_review_server.py, start_review.sh, start_image_review.sh, sync_pipeline.py
- image_review_server.py: approve now updates status in pipeline.json (no more move to pending_post); reject moves to rejected_captions.json

Google Sheet:
- New sheet created: "DuberyMNL Pipeline" (ID: 1LVshSQP5Ob9RNqt35PoSjbUuAiu9dneyHHhUiUZKYrg)
- 16 columns mirroring Notion: Caption ID, Status, Headline, Caption Text, Vibe, Angle, Visual Anchor, Rating, Image URL, Image Status, Has Image, Has Prompt, Image Feedback, Notes, Prompt, Source
- sync_pipeline.py now writes to both Notion + Sheet on every run
- Sheet is overwritten fresh each sync (full refresh)

### 2026-03-15 (Session 13) — Pipeline cleanup + Notion finalized

Pipeline cleanup:
- #21 (Class Dismissed / Classic Blue) added to pending_post.json — sourced from n8n image_log tab (dubery-2026-03-08-114349.jpg), uploaded to Drive
- #22 (Pure Value Truepa / Rasta Red + Brown) added to pending_post.json — sourced from n8n image_log row 5
- #13 and #15 (REJECTED, no images) deleted from Notion and removed from rejected_captions.json — will not re-sync
- #2 set to IMAGE_REJECTED (product fidelity failure, confirmed by RA)
- All remaining 20 active captions set to IMAGE_APPROVED
- sync_pipeline.py updated: inline `headline` field used as fallback when no prompt file exists

Headlines filled for pending_post.json entries (#16-22):
- #16 MAY PLANO KA SA BUHAY. | #17 DALAWANG PAIRS. ISANG DEAL. | #18 CONTENT KA NA, IDOL.
- #19 BAHALA NA SILA SA AKIN. | #20 SHADES LANG ANG TIYAK. | #21 CLASS DISMISSED. TIME TO FLEX. | #22 PURE VALUE, TRUEPA!

Notion state (22 total, 13 + 15 archived):
- 20 IMAGE_APPROVED (ready for WF3)
- 1 IMAGE_REJECTED (#2)
- 2 archived (#13, #15 — no image, deleted from view)

Creative insight saved to memory:
- Overlay accent color follows product lens/frame color
- Price (₱699/₱1,200) is a visual design element, not just a label
- Favorites analysis: RA prefers captions with specific Metro Manila moments, felt pain points, natural Filipino voice

Next: WF3a — post_to_page.py (blocked on Meta pages_manage_posts permission)

### 2026-03-15 (Session 12) — Notion dashboard upgrades + image mapping

Notion improvements:
- Image URL property changed from url → Files & Media type (enables thumbnails)
- Page cover set per caption row via sync_pipeline.py (enables Gallery view card previews)
- Headline property added — extracted from overlays.headline.text in _prompt_structured.json
- Gallery view now shows image thumbnails as card covers (Drive thumbnail URL format)
- Sheets batch (20260309) imported: 5 image-approved captions added as #16-20 to pending_post.json
- All 20 captions synced to Notion (0 errors)

Image mapping — matched orphaned output/images files to captions by headline:
- Gemini_Generated_Image_rlomi4rlomi4rlom.png → #1 (Cut the Glare)
- image_342ca09.png → #8 (DM. Order. Delivered.)
- image_dd7344d1.png → #9 (Delivered Before Lunch)
- Gemini_Generated_Image_z5l723z5l723z5l7.png → #12 (The Fit Just Hit)
- Gemini_Generated_Image_ujds2nujds2nujds.png → #11 (Stay Classy)
- Gemini_Generated_Image_4v6tki4v6tki4v6t.png → #10 (Delivered Today)
- All uploaded to Drive, image_url + status=DONE set in captions.json

Still unmapped (5 files, dated 2026-03-07/08):
- dubery-2026-03-07-071410.jpg
- dubery-2026-03-07-071958.jpg
- dubery-2026-03-07-073303.jpg
- dubery-2026-03-07-085050.jpg
- dubery-2026-03-08-114349.jpg

Captions still at PROMPT_READY with images (need status fix + image review):
- #4 Palenke / Market Day
- #5 Walking the Dog
- #7 Lifestyle / Pinoy Culture
- #14 Content Creator Setup

Next: finish image mapping → fix #4 #5 #7 #14 status → run image review on all DONE captions

---

### 2026-03-15 (Session 11) — Pipeline hardening + Notion dashboard

**Pipeline audit completed — 12 gaps identified across 3 sprints**

Sprint 1 (pipeline-critical fixes):
- generate_kie.py: now auto-updates captions.json on success (DONE + image_url) and failure (IMAGE_FAILED)
- run_batch.sh: per-job logs (.tmp/generate_[id].log), exit codes tracked, summary at end
- captions.json: backup written to .json.bak before every write (all 3 servers)
- Cron deactivated (was a test, hardcoded to dead IDs)

Sprint 2 (close the loops):
- run_batch.sh: auto-launches start_image_review.sh when all jobs succeed
- review_server.py: REJECTED captions move to rejected_captions.json on submit
- image_review_server.py: IMAGE_REJECTED → rejected_captions.json, IMAGE_APPROVED → pending_post.json
- generate_kie.py: Drive upload after save, URL saved back to captions.json
- 7 existing images (#2-7, #14) uploaded to Drive, URLs patched in captions.json

Notion dashboard:
- Notion MCP connected (@notionhq/notion-mcp-server in ~/.claude.json)
- NOTION_TOKEN + NOTION_DATABASE_ID added to .env
- tools/notion/sync_pipeline.py: reads all 3 JSON files, upserts to Notion with 14 properties
- All 15 captions synced with prompt text + Drive image URLs

Data architecture finalized:
- captions.json = active pipeline (PENDING → APPROVED → PROMPT_READY → DONE)
- rejected_captions.json = all rejects (caption + image level) with feedback
- pending_post.json = IMAGE_APPROVED queue for WF3 FB post

### 2026-03-15 (Session 10)
- Built WF3 image review server: tools/image_gen/image_review_server.py (Flask, port 5001)
- Built tools/image_gen/start_image_review.sh — same pattern as caption review (ngrok + email)
- Image review UI: card per image, 4:5 display, caption/vibe/angle/anchor/stars, feedback textarea
- Actions: Approve (IMAGE_APPROVED) + Reject (IMAGE_REJECTED + image_feedback) + Skip (stays DONE)
- Fixed cron: added `cd /home/ra/projects/DuberyMNL &&` prefix (was failing due to wrong working dir)
- Generated images #2, #3, #6 (run_batch.sh) — all saved to output/images/
- Updated statuses manually: #2/#3/#6 → DONE after generation
- Image review results: #3 APPROVED, #6 APPROVED, #2 REJECTED (product fidelity 0%)
- Moved all Mar 15 images from Windows Downloads/approved/ → output/images/
- output/images/ established as single destination for all generated images (run_batch.sh updated)
- Next: update captions #4 #5 #7 #14 to DONE → run image review on them

### 2026-03-15 (Session 9)
- WF2b pipeline unblocked: generate_kie.py fixed (.env path + KIE_AI_API_KEY key name)
- run_batch.sh created: tools/image_gen/run_batch.sh — runs multiple captions in parallel
- Cron scheduled: 9:40am daily, runs #2 #3 #6 — log at /tmp/dubery_batch.log
- Confirmed parallel WF2a+WF2b flow: #5 (Walking the Dog), #14 (Content Creator), #4 (Palengke), #7 (Sala table) — all generated and saved to Downloads
- SKILL.md updated: overlay shape rule — shapes must be named explicitly and earned by concept (no pill default)
- Badge shape feedback saved to memory (confirmed across multiple images)
- All 13 approved captions now PROMPT_READY
- WF2b images generated: #5, #14, #4, #7 (4 new) + #1, #9, #12 confirmed from Session 8
- Scheduled for 9:40am: #2 (Outback Series / outdoor ridge), #3 (Bandits Camo / motorbike helmet), #6 (Rasta Series / commuter bundle)
- Pipeline architecture confirmed: cron runs scripts directly, no Claude approval prompts needed at execution layer
- Next: image review UI (approve to post) + WF3 organic FB post

### 2026-03-15 (Session 8)
- Generated and passed prompts for captions #12, #9, #1 — all tested in NB2, all passed
  - #12: Mirror Selfie / Glow Up / Outback Blue — bedroom, pills, blue-grey badge treatment
  - #9: Gen Z Hangout / Antipolo inihaw / Outback Black — stamped/block badge treatment, grill smoke tones
  - #1: Commuter / EDSA footbridge / Outback Red — sharp rectangular badges, red lens reflection in bubble
- Saved 4 passed prompts as reference (incl. #8 from Session 7)
- Key learning: overlay badge shapes are per-concept, not locked to pills — derive shape from scene energy
- skill_original.md locked as main SKILL.md — SKILL_overengineered.md archived
- Feedback saved to memory:
  - Overlay shapes not hardcoded (derive from concept)
  - No [MODEL: SONNET] tag in prompts
  - Always show caption text before generating prompt
- Captions PROMPT_READY: #1, #8, #9, #10, #11, #12 (6 of 13 approved)
- Remaining APPROVED: #2, #3, #4, #5, #6, #7, #14 (7 to go)
- Next: continue batch prompt generation for remaining 7 APPROVED captions

### 2026-03-15 (Session 7)
- Tested caption #11 (barbershop/Status/PERSON) and caption #8 (Lalamove delivery/Convenience/PERSON)
- Discovered root cause of overlay quality regression: over-prescribed rules (compact row, left-half, never-white) were fighting NB2's natural creative output
- Found original skill file (AGENT 1) — the version that produced the reference-quality ads last week
- skill_original.md saved to .claude/skills/dubery-prompt-writer/ as the clean base
- Added to skill_original.md:
  - Bubble rule: circular crop lifted from main ad image, zoom circle effect
  - DUBERY logo note: D icon + wordmark description (red D swoosh, bold italic black wordmark, red outline)
  - Logo Drive URLs: Logo2 (DUBERY) + Logo4 (DUBERY MNL) added for image_input reference
- Caption #8 regenerated using skill_original — cleaner overlay intent, NB2 gets creative freedom
- Next: rebuild SKILL.md using skill_original as base + graft back only confirmed-valuable fixes
  (bottom-right clear zone, overlay zone split, product primacy, lens darkness rule, angle inheritance, COD auto-always)

### 2026-03-15 (Session 6)
- 6 skill fixes applied from caption #10 v2 test (product distortion, scene brevity, headline clarity, COD clustering, no random icons, delivery prominence)
- Brand rule update: same-day/next-day delivery now FREE; ₱1,200 bundle is free shipping — both skills updated
- Overlay zone rule added: revised Product primacy rule + overlay description instruction — overlays now constrained to top and bottom zones only, center = product space
- Caption #10 regenerated (v3) with all fixes — tested in Gemini — CONFIRMED WORKING
- Result: clean professional ad, product fills center unobstructed, overlay hierarchy correct
- Skill approach confirmed: surgical edits to existing rules, never stack new rules on top of old ones
- Next: generate prompts for remaining 11 APPROVED captions using final skill

### 2026-03-14 (Session 5)
- Major architecture shift: dropped Google Sheets as working store → .tmp/captions.json as primary working data
- Google Sheets retained as final archive only (written once after image generated)
- review_server.py fully rewritten: removed all Sheets API code, reads/writes .tmp/captions.json directly
- start_review.sh updated: count + angles now pulled from .tmp/captions.json
- WF1 skill replaced with new angle-based architecture:
  - 15 captions per batch (3 angles x 5)
  - Angle Library: Pain Relief, Identity, Lifestyle, Status/Glow Up, Value/Deal, Convenience/Fast Delivery
  - Hook Type Library with max-3-per-type rule
  - Visual anchor distribution: 60% PRODUCT / 40% PERSON
  - Voice reference file: research/filipino_caption_voice.md (RA-authored, cached)
  - Output: valid JSON only, no markdown
- WF1 first real run: 15 captions generated, 13 approved, 2 rejected (#13, #15 Status/Glow Up)
  - 10 captions rated 5-star
  - 6 captions have detailed image direction notes from RA
- WF2 comparison test started:
  - Two skill versions under evaluation: current (detailed) vs new (simplified, from promptest.txt)
  - Caption #9 selected randomly from 5-star pool for test
  - Both prompts generated and saved to .tmp/captions.json as prompt_current + prompt_new
  - Caption #9: POV/Convenience/Gen Z Hangout/Outback-Black | Scene: inihaw grilling at Antipolo resort
  - Headline chosen: "Delivered Before Lunch."
  - Pending: test both prompts in kie.ai, pick winner → set as prompt field → PROMPT_READY
- Known issue: Bandits - Glossy Black (#11) not in reference image map — nearest match is banditsblack
- banditstortoise still has placeholder Drive ID in new skill

---

### 2026-03-16 (Session 19) — Landing Page Order Form Polish

**What was built:**

**card_image system:**
- New `card_image` field added to pipeline.json, export_captions.py, captions.json, sync_pipeline.py, script.js
- Product card now uses a direct asset filename per caption instead of keyword-matching on product_ref
- Card Image column added to Google Sheet + Notion DB
- rasta-red-card.png added as the first new-format product card asset

**Asset cleanup:**
- Removed all duplicate .jpg product images (kept .png + bundle.jpg)
- Renamed Rasta - red - asset.png → rasta-red-card.png, Inclusions.png → inclusions.png

**Hero / CTA section:**
- Product card moved above CTA buttons (product first, then buy)
- "BUY NOW" → "ORDER NOW — SAME-DAY DELIVERY"
- Chat on Messenger → Facebook blue (#0084FF), 70% opacity, smaller than primary CTA
- Lens badge + headline color → `--accent-active` (darker dynamic accent)

**Order form — variant picker:**
- Dropdown options: white background + dark text (was dark-on-dark — unreadable)
- Stepper overflow fix: `min-width: 0` on .picker-select so stepper doesn't bleed off screen
- Tap-to-preview overlay: tap any thumbnail to see full image, tap to dismiss or press Escape

**Order summary redesign:**
- "Order Summary" header moved outside the card (above it, not inside)
- Each summary line shows product thumbnail (tappable), product name, quantity
- Freebies row added: inclusions.png + "Freebies" auto-populates, qty matches total pairs
- Delivery nudge: "Add 1 more pair to avail FREE delivery!" — shows at exactly 1 pair
- Tiered pricing: ₱699 / ₱1,200 / ₱1,800 / ₱2,300 / +₱500 per extra pair
- Amount row + Est. Delivery Fee (₱99) + COD Fee (₱0) + separator line + Total row
- At 2+ pairs: delivery fee → FREE (green), Total = exact product price

**Discoveries / Learnings:**
- `display: flex` in CSS overrides the HTML `hidden` attribute — must add explicit `[hidden] { display: none }` rule
- `min-width: auto` on flex items prevents proper shrinking — `min-width: 0` is the fix for overflow in constrained containers
- Google Places Autocomplete identified as next UX upgrade for address field — needs Google Maps API key with Places API enabled, free up to 28k requests/month

**Pending:**
- Google Maps Places Autocomplete (RA to get API key)
- Vercel deploy → live URL
- Google Apps Script setup (manual, RA)
- stage_ad.py CTA swap to landing page URL

---

### Session 22 — Vercel Deploy + Modal Fix + FB Button

**Deployed to Vercel:** https://duberymnl.vercel.app
- CLI deploy via `vercel --prod` from dubery-landing/
- Google Maps API key restricted to duberymnl.vercel.app in Google Cloud Console
- LANDING_PAGE_URL saved to .env

**Modal pointer-events fix:**
- Hidden modal (translateY off-screen) was still intercepting all pointer events on desktop
- Symptom: ORDER NOW button and tap-to-view did nothing on desktop, browser autofill popup appeared over product card
- Fix: added `pointer-events: none; visibility: hidden` to `.modal`, restored on `.modal.active`
- Desktop modal CSS override also updated for opacity transition

**Facebook button:**
- Swapped Messenger button href from `m.me/111349974035733` → `facebook.com/duberymnl`
- m.me blocked by NET::ERR_CERT_AUTHORITY_INVALID on RA's machine (SSL interception)
- Both hero and final CTA Messenger buttons updated

**Tunnel watchdog:**
- tools/tunnel-watchdog.sh — checks every 5 min, auto-restarts code-tunnel if dead

**Pending:**
- Google Apps Script setup (manual, RA) — paste Web App URL into FORM_ENDPOINT in script.js
- stage_ad.py CTA swap to https://duberymnl.vercel.app
- Landing page content backlog: proof of purchases, correct product assets, polarized benefits explainer

---

### Session 28 — Facebook Ads Education + WF2 Gap Identified (2026-03-18)

**Facebook ads fundamentals covered:**
- Campaign → Ad Set → Ad structure
- Objective: Traffic or Leads (not Engagement, not Awareness)
- Only metric that matters right now: cost per order
- Budget: ₱100-200/day to start, daily budget, don't touch during 7-day learning phase
- Targeting: broad (Metro Manila, 18-40, all genders) -- the creative does the targeting
- Advantage+ audience valid option for small budgets
- Creative priority order: image stops scroll → first caption line holds attention → CTA button converts
- CTA button: Shop Now or Order Now (not Learn More)

**Key decision:**
- 24 ads on duberymnl.vercel.app are ready to run ads on RIGHT NOW
- New 15-caption batch needs WF2 images first
- Launch ads on existing 24 while WF2 gets built

**WF2 gap identified:**
- Tools exist (generate_kie.py, image_review_server.py)
- End-to-end pipeline not wired: caption approved → prompt built → image generated → reviewed → ad-ready
- Next major build: complete WF2 as a clean single workflow

---

### Session 27 — WF1 Run + Workflow Upgrades (2026-03-18)

**WF1 caption generation run:**
- 15 new captions generated (IDs 20260318-001 to 20260318-015)
- Vibes: Outdoor/Trail+Adventure, Moto Camping, Church/Sunday Vibes, Cat Parent Vibes, Toddler/Young Parent, New Haircut/Barbershop, Motovlogger, Lifestyle/Pinoy Culture
- Bundle captions: IDs 004 (Moto crew), 008 (Cat parent barkada), 013 (Riding buddy)
- PRODUCT: 7 / PERSON: 8 (50/50 -- last time before bias change takes effect)
- Output appended to .tmp/captions.json (28 total entries)
- Review server live, email sent to sarinasmedia+claude@gmail.com

**WF1 workflow upgrades (caption_generation.md):**
- Research caching: Step 3 now checks .tmp/wf1_research_cache.json before web search (skip if < 7 days old)
- PRODUCT anchor bias: raised to 65-70% PRODUCT / 30-35% PERSON (was 50/50)
- Angkas voice rule hardened: energy reference only, no copying

**Scheduling:**
- WF1 cron job added to system crontab: every Monday 8pm PHT
- Command: `claude "run wf1 caption gen"` in DuberyMNL working dir
- Logs to .tmp/wf1_cron.log

---

### Session 26 — Lead Capture + Pipeline Sync (2026-03-18)

**Lead capture live:**
- Google Apps Script deployed as web app, linked to DuberyMNL Orders sheet
- Form POSTs via FormData to Apps Script endpoint
- Sheet columns: Timestamp, Name, Phone, Address, Items, Qty, Delivery Fee, Total Amount, Notes, Ad ID
- Items and Qty on separate lines per product (newline separator)
- Pricing logic from frontend: single pair ₱699 + ₱99 delivery = ₱798 total; 2+ pairs = bundle price (₱1,200+) FREE delivery
- FORM_ENDPOINT set in script.js, live on duberymnl.vercel.app
- SMS via Semaphore: script ready, pending Semaphore account + Sender ID registration (DUBERYMNL)

**Semaphore setup (pending):**
- Register at semaphore.co, submit Sender ID "DUBERYMNL" (1-3 day approval)
- Add API key to Apps Script line 2, redeploy as new version

**Pipeline audit:**
- Cross-checked captions.json vs Notion pipeline vs Google Sheet
- Removed all Classic series from active ads (IDs 18, 20, 21, 25, 27, 29, 30, 31, 36, 38 parked in captions-classic.json)
- Added IDs 16 (Bandits Black) and 19 (Bandits Blue) to captions.json -- were IMAGE_APPROVED but missing
- Fixed product refs in Notion: ID 23 → "Rasta Brown, Rasta Red, Outback Green, Bandits Camo"; ID 24 → "Outback Red"; ID 32 → "Rasta Red"
- Active ad count: 24

**Pending:**
- ID 2 (Outback Series) -- IMAGE_REJECTED in Notion for product fidelity, IMAGE_APPROVED in sheet -- RA to decide if it goes back in
- Add missing picker thumbnails: Outback Red, Outback Blue, Bandits Green, Bandits Blue, Bandits Tortoise
- Fix Google Maps Places Autocomplete (broken, debug via browser console at home)
- Restrict Google Maps API key confirmed set to duberymnl.vercel.app
- stage_ad.py CTA swap to https://duberymnl.vercel.app

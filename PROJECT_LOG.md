# DuberyMNL Project Log

Previous sessions (1-72) archived in `archives/pre-ea-rebuild/PROJECT_LOG.md`.
Sessions 73-97 archived in `archives/PROJECT_LOG-sessions-73-97.md`.

---

## Session 150 -- 2026-05-02 (v3-order-fixes) [IN PROGRESS]

### Savepoint 01:00 UTC+8

**Done:**
- Testimonials section on PDP converted to horizontal scroll rail — mobile: 1 card (85% width, snap), tablet: 2 cards, desktop: 4 cards; CSS-only change
- README updated: cache bust version → v3-011, PowerShell regex updated for 3-digit versions, added Product Card Navigation + PDP Interactions sections, expanded Shared Scripts table

**Learnings:**
- `item.html` is 13.7MB due to embedded base64 images — Python required for string replacement; PowerShell and normal Edit tool choke on file size. Long-term fix: extract base64 images to external files.

**In flight:**
- None

**Memories saved:**
- None new

---

### Savepoint 09:30 UTC+8

**Done:**
- PDP section order fixed: The Look → Testimonials → People Also Bought (Series)
  - HTML order restored to testimonials → series
  - `item.js` insertion changed from `insertAdjacentElement('afterend')` to `'beforebegin'` on testimonials
  - Version bumped v3-011 → v3-012; stale `?v=v3-010` script tags on item.html were the root cause of look section not moving
- Shop-social overhaul:
  - Removed Load More pagination — all 54 tiles render at once
  - Grid columns 4 → 6 (smaller thumbnails); responsive: 4 at 1080px, 3 at 720px, 2 at 480px
  - `?edit` mode: X remove button per tile, right-drawer edit panel (author/location/caption/products chips), Download data.json button
  - Fixed nested-button HTML bug: `<button>` inside `<button>` is invalid — browser ejects inner button from DOM, causing wrong tile removal; fixed by using `<span role="button">`
- Shop-social data.json updated 3× (user curated via edit mode: 60 → 54 tiles, retagged products)
- Final data.json: gender-corrected usernames (male images → male handles, female → female), captions rewritten with `#duberymnl` + product + `#polarized` hashtags

**Decisions:**
- Edit mode uses download-JSON pattern (no backend write) — consistent with gallery editor on PDPs

**Learnings:**
- `<button>` nested inside `<button>` is invalid HTML; browser ejects the inner button from the DOM during parsing, breaking `data-remove` ID matching
- Version tags on scripts must ALL be bumped together — item.html was loading item.js at `?v=v3-010` while CSS was already v3-012, serving cached JS that didn't have the fix

**In flight:**
- None

**Memories saved:**
- `feedback_nested_button_html.md` — nested button in button = invalid HTML, browser ejects inner element
- `project_shop_social_edit_mode.md` — shop social ?edit mode pattern + data.json workflow

---

## Bespoke Gen -- 2026-05-03 (chess-outback-red-002)

**Done:**
- Built v3 product-as-locked-asset prompt for outback-red chess editorial concept (chess board forced-perspective, low-angle upshot, navy jacket, blue sky + cumulus clouds, DUBERY MNL typography overlay)
- V3 validation: all 8 checks PASS (patched V6 color-word before generation -- stripped "red-orange iridescent" from required_details, Gemini reads lens color from prodref)
- First run returned NoneType error on candidate.content iteration -- transient; second run succeeded
- Generated: `contents/new/2026-05-03_bespoke-chess-outback-red-002.png` (1494KB, 4:5)
- Prompt archived: `contents/new/2026-05-03_bespoke-chess-outback-red-002_prompt.json`

**Visual result:**
- Filipino male model, navy bomber jacket, Outback Red sunglasses worn on face, low-angle forced perspective, chess board + pieces in foreground, "DUBERY MNL" white block type centered mid-frame, blue sky + cumulus clouds backdrop
- Lenses rendered as dark mirror reflecting sky -- red-orange iridescent tint present but subtle in output

**Issues:**
- Initial `generate_vertex.py` run failed with JSONDecodeError -- prompt file had plain-text prefix before JSON block; required restructuring to valid `{prompt: "...", image_input: [...]}` schema
- First API call returned candidate with no content (NoneType) -- transient, resolved on second call without changes

---

### Savepoint 14:00 UTC+8

**Done:**
- Mobile hero image crop fixed — iterated `object-position` from 35% → 10% → 22%, tried bottom-overlay / stacked / split layouts, landed on left-gradient overlay with `max-width: 58%` copy (matches desktop pattern)
- Created `hero-edit.js` — `?edit` panel with X/Y/Zoom sliders (0.5x–2.5x) + Copy CSS button; activates at any `?edit` URL
- Applied user-dialed mobile hero values: `object-position: 57% 28%; transform: scale(1.25); transform-origin: 57% 28%`
- Applied desktop hero position: `object-position: 49% 44%` (was `center`, user found via editor)
- Reduced desktop h1 font size: `clamp(2rem, 3.75vw, 3.25rem)` — was `clamp(2.5rem, 6vw, 4.5rem)`, too large on laptop
- Fixed CTA buttons stacking on mobile — `flex-wrap: nowrap; flex: 1` scoped to `.hero-primary-copy .cta-row` only
- Reduced mobile vignette gradient from `0.75/0.55` → `0.55/0.35`
- Fixed cart persistence bug — added `saveCart()` in `order.js`; called on every `+`, `−`, and `×` mutation; removes `dubery-cart` key when cart is empty
- Fixed order page JS cache miss — `order/index.html` had `order.js?v=v3-010` while fix was in v3-027; bumped all script tags
- Created `/savepointplus` skill — savepoint + README update in one shot

**Decisions:**
- Left-to-right gradient (90deg) on mobile matches desktop pattern; discarded bottom-overlay, stacked, split approaches
- `flex-wrap: nowrap` scoped to hero copy only — other `.cta-row` instances on the page keep wrapping behavior

**Learnings:**
- JS version tags need bumping alongside CSS — easy to miss; stale JS served cached fix even after CSS was current
- `hero-edit.js` slider pattern works well: user dials exact values visually, pastes output directly into CSS

**In flight:**
- None

**Memories saved:**
- `feedback_js_version_bump.md` — JS cache tags must be bumped with CSS; all script src tags need version bump
- `reference_hero_edit_js.md` — hero-edit.js visual editor, activates on ?edit

---

### Savepoint 23:30 UTC+8

**Done:**
- Diagnosed v3.duberymnl.com not reflecting changes — CF tunnel healthy, CF cache DYNAMIC; root cause was browser caching old `?v=v3-002` assets for live domain; fixed by bumping all version tags to v3-004
- Added Cache Busting section to `dubery-landing-v3/README.md` — documents `?v=v3-NNN` pattern, current version, PowerShell one-liner to bump
- Fixed Best Sellers card titles in `index.html` — updated 4 hardcoded cards from old format (OUTBACK | Black / Polarized) to correct format (Outback Black | Matte Black / Smoked Polarized Lenses) using `seriesLabel + colorLabel | colorway` from data.json
- Product card image navigation — full implementation:
  - Removed CSS `:hover` image swap entirely
  - Added `.is-swiped` CSS class + JS swipe gesture (40px threshold) to `script.js` (best sellers) and `catalog.js` (catalog page)
  - Added arrow buttons (`.bs-nav-bar`) overlaid at bottom-center of card image + 2-dot indicator (`.bs-dots`) below image
  - Arrows toggle `.is-swiped`, sync dots; swipe left = hover image, swipe right = primary; tap = link follows normally
  - Version tags bumped through v3-010
- PDP Add to Cart: after "Added ✓" animation (1.5s), button transitions to "Shop All" → navigates to `/products/`
- "People Also Bought" labels: changed from `colorway.split('/')[0]` ("Matte Black") to `seriesLabel + colorLabel` ("Outback Black")
- Hard refresh lesson: browser caches HTML itself; Shift+reload needed on live domain for HTML changes

**Decisions:**
- Removed hover image swap on desktop entirely — swipe-only pattern with visible arrows replaces it; no hover behavior on any breakpoint

**Learnings:**
- Browser caches HTML pages too, not just JS/CSS assets — bumping version tags isn't enough if the HTML itself is cached; Shift+reload (hard refresh) needed on live domain
- Always bump version tags after ANY CSS/JS change, even CSS-only; if the previous version was already fetched, the browser won't re-fetch without a new query string
- Buttons inside `<a>` tags: `e.stopPropagation()` + `e.preventDefault()` on click prevents link navigation while still intercepting the tap

**In flight:**
- None

**Memories saved:**
- feedback_version_bump_always.md -- bump tags after every CSS/JS change, hard refresh for HTML

---

### Savepoint 15:45 UTC+8

**Done:**
- Shop-social modal: `p.colorway` → `p.colorLabel || p.colorway` in `productCard()` — modal now shows short label (e.g. "Black") instead of truncated full colorway
- shop-social/data.json tile 18 (lifestyle-trio-surf): products corrected from `[outback-black, bandits-matte-black, rasta-red]` → `[outback-green, rasta-brown, outback-black]` to match actual photo
- shop-social/index.html: cache-bust bumped v3-003 → v3-004
- Ran `vercel --prod` from `dubery-landing-v3/` (unnecessary for live — CF tunnel is the live host)
- Confirmed v3.duberymnl.com is CF tunnel → localhost:8300; all file checksums match between local and live

**Decisions:**
- Vercel deploy was irrelevant for v3.duberymnl.com live updates — CF tunnel to :8300 is the live host (per EDITING.md)

**Learnings:**
- v3.duberymnl.com = CF tunnel → localhost:8300, not Vercel; deploying to Vercel doesn't update it
- Cloudflared config at `~/.cloudflared/*.yml` is the source of truth for subdomain → port mappings
- All 6 subdomains: chatbot/:8085, cc/:8090, review/:8123, tag/:8124, v3/:8300, cq/:8400

**In flight:**
- v3.duberymnl.com still showing stale in RA's browser — checksums confirmed identical; RA checking later

**Memories saved:**
- (see savepoint 2 below)

---

### Savepoint 20:00 UTC+8

**Done:**
- Fixed mobile X overlay on homepage — root cause: second `.lightbox` CSS block set `display: flex` (same 0-1-0 specificity), silently overriding first block's `display: none`. Fix: removed `display: flex` from second block, added `.lightbox:not([hidden]) { display: flex }` (0-2-0 wins cleanly). Updated `index.html` lightbox div to start with `hidden` attribute; JS now toggles via `removeAttribute/setAttribute('hidden')` instead of `is-open` class.
- Removed floating ✎ Edit button from `products/item.html` (deleted inline `<script>` block, lines 239–254)
- Catalog cards: product name format changed from `BANDITS | colorway` → `Bandits Matte Black | colorway` via `${p.seriesLabel} ${p.colorLabel}` in catalog.js
- Added `colorLabel` to 4 Bandits products that were missing it: glossy-black ("Glossy Black"), green ("Green"), blue ("Blue"), tortoise ("Tortoise")
- Updated colorway strings for 3 Bandits: green/blue/tortoise now correctly start with "Translucent / ..." (was "Green / Green..." etc.)
- PDP h1 (item.js): shows `${p.name} ${p.colorLabel}` → "Bandits Green", "Outback Black", etc. (series prefix kept per RA preference)
- Tried side-by-side series+color layout on PDP — reverted per RA

**Decisions:**
- Keep series name in PDP h1 even though eyebrow also shows series — RA prefers clarity over avoiding redundancy

**Learnings:**
- Two CSS blocks for the same `.lightbox` selector: later block's `display: flex` wins over earlier `display: none` (equal specificity, cascade order). Unified to `[hidden]` attribute + `.lightbox:not([hidden])` rule with higher specificity.
- 4 of 5 Bandits were missing `colorLabel`; fallback `colorway.split('/')[0]` gave "Glossy" instead of "Glossy Black"

**In flight:**
- None

**Memories saved:**
- feedback_css_hidden_display_override.md updated — added duplicate-selector display cascade variant

---

### Savepoint 18:30 UTC+8

**Done:**
- Free shipping banner on order page → green bg/border/text
- "Free delivery on 2 pairs." → dynamic: "Add one more pair for FREE DELIVERY PROMO." (0-1 pairs) / "Free delivery applied." green (2+) via cart.js `updateCartBadge()`
- "Message us instead" button replaced with "Checkout" → links to `/order/`
- Cart icon bumped 22px → 30px
- Order sidebar product names fixed: now shows `p.name + colorLabel` (e.g. "Outback Blue") instead of full colorway string
- Order product cards: same fix — `p.name + colorLabel`
- All 3 series accordions default to collapsed on `/order/`
- Art drop images: lightbox injected into index.html — click to open full view, ESC/click-outside closes
- Removed broken `data-field="messenger"` JS line from item.js — was null-crashing and killing Add to Cart + People Also Bought
- `localStorage['dubery-orders-log']` backup on every order submit in order.js
- `tools/orders/sync_orders.py` — pulls Orders sheet → `orders/orders.json`
- `dubery-landing-v3/README.md` written — full site reference for owner + agent
- Identified floating ✎ Edit button on PDPs (item.html inline script) — needs removal
- Identified X overlay on mobile homepage — under investigation (lightbox CSS or editor.js)

**Decisions:**
- Replaced "Message us instead" with "Checkout" — direct path to order form is higher value than Messenger fallback on PDP

**Learnings:**
- Removing `data-field="messenger"` from HTML without removing the JS line `document.querySelector('[data-field="messenger"]').href = ...` causes a null crash that kills all subsequent JS on the page (Add to Cart, SKU strip)
- Always check for JS field references before removing HTML elements with `data-field` attributes

**In flight:**
- Mobile X overlay bug — root cause not yet confirmed (lightbox vs editor.js)
- Floating edit button removal from item.html — pending

**Memories saved:**
- project_v3_order_enhancements.md -- order page UX improvements session 150
- feedback_data_field_removal_crash.md -- removing data-field HTML without cleaning JS causes null crash
- reference_v3_tunnel.md — CF tunnel arch, all 6 subdomains, Vercel not used for live

### Savepoint 14:30 UTC+8

**Done:**
- Order thumbnails in "Your order" sidebar: 48px → 72px (grid column + image dimensions)
- "The look." section system: single (`feature_image`) or dual-panel (`feature_images` array) injected below testimonials; padding 0.5rem; dual panels seamless (gap:0, outer-only border-radius)
- Added feature images: Bandits Green (eyesonfashion), Bandits Glossy Black (BESPOKE-002), Bandits Tortoise (hatbanner), Outback Black (laughwall), Rasta Red + Rasta Brown (dual panel BRAND-V2-004c)
- `colorLabel` field added to data.json + item.js: decouples PDP h1 title from colorway subtitle; used on Outback Black/Blue/Red/Green, Rasta Red/Brown
- All 11 products updated: colorway subtitles standardized to "X / Y Polarized Lenses" format, lens specs cleaned (no "Polarized" suffix), descriptions rewritten to match
- Catalog filter pills fixed: `.catalog-card[hidden] { display:none !important }` — same CSS display override bug as order page
- "You might also like" → "People also bought", moved below Add to Cart CTAs
- Dual-panel split layout: `feature_images` renders two columns, seamless join, rounded on outer edges only

**Decisions:**
- `colorLabel` over changing colorway first-segment — keeps subtitle format flexible without breaking the title
- "People also bought" over "Best paired with" — more trust-building, familiar to PH shoppers

**Learnings:**
- CSS display override bug hit again on catalog cards — `.catalog-card[hidden]` needed same fix as order page dropdowns
- Split panel images need `gap:0` + outer-only border-radius to read as one seamless image

**In flight:**
- Rasta Red description still using old copy (just updated this savepoint)

**Memories saved:**
- project_v3_pdp_descriptions.md — colorLabel pattern + 11-product spec update

### Savepoint 05:30 UTC+8 — v3 GO-LIVE

**Done:**
- Audited all image paths in v3 (127 product paths + 54 social + 27 HTML) — all clean, no broken refs
- Removed 15 unused assets from `dubery-landing-v3/assets/` (old hero variants, unused social tiles, outback-black orphans)
- Tightened section spacing: `--section-y` from `clamp(4rem,8vw,7rem)` → `clamp(2rem,4vw,3.5rem)` (option C too tight, landed on B)
- Section head margin-bottom: `2.5rem` → `1.5rem`
- Shop-our-feed "Shop this look" pill opacity: `rgba(255,255,255,0.96)` → `0.67`
- CSS version bumped: v3-027 → v3-030 across all 5 pages
- **Vercel domain swap:** removed `duberymnl.com` + `www.duberymnl.com` from `dubery-landing` project; added to `dubery-landing-v3`
- Connected `dubery-landing-v3` Vercel project to `RASCLAW/DuberyMNL` GitHub repo
- Set Vercel root directory to `dubery-landing-v3` (was `./`, causing 403)
- Triggered fresh deploy via empty commit push — `duberymnl.com` now live on v3

**Decisions:**
- Settled on spacing option B (mid-range) — C was too compressed, A was the old value
- Self-contained asset copies in `dubery-landing-v3/assets/` is correct for static Vercel deploy; `contents/` moves don't break site

**Learnings:**
- Vercel "Redeploy" reuses old source snapshot, not latest git — must push a new commit or trigger from connected git to get updated code
- Vercel root directory defaults to `./` — must set to subdirectory when repo has multiple sites

**In flight:**
- None — duberymnl.com is live on v3

**Memories saved:**
- None new

---

### Savepoint 01:30 UTC+8

**Done:**
- All `m.me/duberymnl` → `facebook.com/duberymnl` across 5 HTML files + order.js (success state link)
- Removed "Nationwide COD" from trust strip on all 5 pages (not offered yet)
- Removed color swatch dots (`bs-swatches`) from catalog product cards
- PDP "Added ✓" state now permanent — removed 1500ms setTimeout revert; button stays disabled
- Order page thumbnails: removed forced `aspect-ratio:1/1` + `object-fit:cover` → `height:auto` (no cropping)
- Order page dropdowns fixed: `display:grid` was overriding `[hidden]` attribute; added `.order-series-grid[hidden] { display:none !important }`
- Order page pricing fixed: `&#8369;` was rendering as raw text via `textContent`; switched to `₱` character directly
- Order page hidden rows (bundle note, discount, totals): added explicit `[data-*][hidden] { display:none !important }` rules
- Cache-bust version bumps: affected pages bumped to v3-002/v3-003
- Accidentally removed PDP thumbnail strip → restored

**Learnings:**
- CSS `display:grid/flex` on an element overrides UA `display:none` from `[hidden]` — must add `[selector][hidden] { display:none !important }` for every element with an explicit display rule
- `textContent` treats HTML entities as literal text — use actual Unicode characters, not `&#NNNN;`
- Cache-bust must bump BOTH the HTML file and every JS/CSS version tag it references — partial bump = old cached script loads

**In flight:**
- Cart flow browser verification still pending (carry-over from s148)

**Memories saved:**
- feedback_css_hidden_display_override.md — CSS display:grid/flex overrides [hidden] attribute

---

### Savepoint 19:00 UTC+8

**Done:**
- Reviewed v3 go-live checklist — confirmed only 3 items remain: chatbot image bank update, Vercel domain swap, smoke test
- Discovered chatbot image bank already uses `lh3.googleusercontent.com/d/` CDN URLs — not duberymnl.com paths — so domain swap has zero impact on chatbot images
- Built `.tmp/chatbot-bank-editor.html` — standalone HTML tool: shows all 44 bank images grouped by model, hover-to-replace via file picker, Save JSON exports diff with replacement filenames
- Processed `chatbot-bank-updates-2026-05-02.json` (18 replacements from RA)
- Found all 18 replacement files in `contents/ready/{type}/{model}/`
- Built `.tmp/batch_upload_bank.py` — batch uploads replacements to Drive (`DuberyMNL/ChatbotImageBank` folder), patches bank JSON in place
- Ran batch upload: 18/18 succeeded, all new Drive file IDs written to `chatbot-image-bank-2026-04.json`
- Updated `chatbot-bank-editor.html` BANK constant to reflect current state (44 picks, 18 updated)

**Decisions:**
- No chatbot code changes needed for domain swap — CDN URLs are Drive-hosted, independent of duberymnl.com

**Learnings:**
- Chatbot image bank was already decoupled from the landing page domain from day one — go-live checklist item was a precautionary hold that turned out to be a no-op

**In flight:**
- None

**Memories saved:**
- `reference_chatbot_bank_editor.md` — editor HTML + batch upload script location and workflow

---

## Session 149 -- 2026-05-02 (shop-social-expansion)

### What
- Added 48 images to `dubery-landing-v3/assets/social/` (social-07 to social-54) sourced from `contents/ready/person/` and `contents/ready/product/`
- Built 60-entry `shop-social/data.json` — mix of UGC person shots, flatlays, lifestyle, product shots; PH-authentic handles, locations, captions
- `shop-social` page: Load More pagination (24 on load → +12 per click → cap 60); centered button; scroll-anchor fix prevents masonry column reflow jump
- Homepage "Shop our feed": `script.js` now fetches `shop-social/data.json`, Fisher-Yates shuffles, renders random 12 on every page load; cleared all hardcoded base64 tiles from `index.html`

### Decisions
- None this session

### Deployed
- Nothing deployed (changes local, CF tunnel live at v3.duberymnl.com)

### Blockers
- v3 cart flow (PDP → Add to Cart → /order/) still needs browser verification (carry-over from session 148)

---

## Session 148 -- 2026-05-02 (v3-gallery-editor)

### What
- Built `item-editor.js` PDP gallery editor: add/remove/reorder photos, Save data.json, Save HTML
- Fixed base64 bloat → blob URLs + `data-uploadedFilename`; data.json stays small and clean
- Added floating `✎ Edit` button to `item.html` — all PDPs now have edit mode without manual `?edit`
- Built auto-process drop workflow: data.json drop → detect changed slug → search `contents/ready` → copy missing → merge
- Populated galleries for all 11 SKUs: Bandits (5), Outback (4), Rasta (2)
- Fixed outback-black catalog card hero/thumb → `hero-outback-black.png`
- Committed + pushed 86 files to GitHub (commit 07bd257)

### Decisions
- Blob URLs not base64 for browser file uploads in editors — base64 produces 5-6MB JSON per 3 images
- `contents/ready` is authoritative source for auto-copy on every data.json drop

### Deployed
- 86 files committed + pushed to GitHub (gallery images + editor JS + item.html)

### Blockers
- Catalog card hero/thumb for other products may still show stale shots (only outback-black fixed)
- bandits-blue has generic gallery-1 through gallery-6 filenames (no real names captured)
- v3 not yet deployed to production (Vercel)

### Savepoint ~17:00 UTC+8

**Done:**
- Fixed best sellers hover images (homepage) — were pointing to `assets/social/social-XX.png`, now use `gallery[1]` from data.json for each product
- Replaced outback-blue best seller card with outback-green
- Applied gallery reorder from RA's data (12).json — bandits-tortoise gallery[1]/[2] swapped; synced hover in index.html
- Applied gallery update from data (13).json — rasta-red gallery[1] → `-sq` version; copied missing file from `contents/ready/person/rasta-red/`
- Redesigned /order/ page: replaced abstract text dropdown picker rows with visual product grid grouped by Bandits/Outback/Rasta series accordions; each card shows hero image + colorway + stepper; Bandits open by default; qty > 0 = accent border highlight

**Decisions:**
- Best sellers hover = gallery[1] (not the `hover` field in data.json, not hero) — keeps hover consistent with what PDP gallery shows first
- Order page: series accordion (collapsible) over flat grid — better UX for 11 products

**Learnings:**
- When RA drops a new data.json (from Downloads), gallery[1] may change — must update both `products/data.json` AND `index.html` hover src for affected best sellers
- rasta-red-card-shot.jpg is PNG data with .jpg extension — doesn't cause load issues (browser sniffs header), but worth noting

**Memories saved:**
- project_v3_best_sellers_hover.md -- gallery[1] = hover source, must sync on gallery reorder
- project_v3_order_redesign.md -- order page now visual product grid + series accordion

### Savepoint ~23:30 UTC+8

**Done:**
- PDP cart redesign: removed PII order form from item page entirely
- Created `dubery-landing-v3/cart.js` — shared badge updater, loaded on all 4 pages
- Added cart icon + badge to nav on all 4 pages (index, products/index, products/item, order/index)
- `order.js` now reads `dubery-cart` localStorage on init, syncs stepper UI, clears cart on successful submit
- Added "You might also like" inline SKU strip (4 random thumbnails, 4-col grid) above product name in right column
- Added gallery prev/next arrow buttons overlaid on main PDP image + touch swipe support
- Replaced bottom "More styles" section with "Pick your style" series cards (same layout as homepage)
- Extracted homepage base64-embedded series images via Python → saved as `series-bandits-new.png`, `series-outback-new.png`, `series-rasta-new.png`

**Decisions:**
- Cart persists to localStorage (`dubery-cart` key, `{slug: qty}` map) — RA chose badge approach over redirect
- SKU strip: 4 random others, grid-fit `repeat(4,1fr)` not fixed px, positioned above product name
- Bottom section: reuse existing "Pick your style" series grid instead of all-SKUs thumbnail strip

**Learnings:**
- `index.html` is 6.9MB — base64-embedded images make it unreadable via Read tool; use Python + regex to extract
- Series images in `assets/hero/` were stale; homepage has newer versions embedded as base64
- Saved extracted images with `-new` suffix to avoid overwriting originals

**Memories saved:**
- project_v3_pdp_cart_redesign.md -- cart flow, localStorage schema, key files changed
- feedback_homepage_base64_images.md -- index.html too large to read; Python extraction pattern

---

## Session 147 -- 2026-04-29 (resume-bpo)

### What
- Reviewed existing resumes: `resume.html` (AI-focused) and `RAS-CV-2026.pdf` / `Resume June 2025.pdf` (traditional BPO CV)
- Built `resume-bpo-2026.html` in `ras-portfolio/` — two-column dark sidebar layout, BPO-first framing
- Work history trimmed to 4 roles: Informdata, Disney+/Hulu, Airbnb, Google/Teledirect
- Title: "Data Operations & Customer Experience Specialist"
- AI/automation downplayed to one-line "Personal Interest" blurb (small Facebook business framing)
- Removed LinkedIn URL and "Remote" label from job subtitles per RA request
- Old `resume.html` left untouched

### Decisions
- AI work framed as personal side project, not career focus — avoids misrepresenting current role in interviews
- Title derived from BPO arc (data + customer ops) not AI specialty

### Deployed
- Nothing deployed

### Blockers
- Export `resume-bpo-2026.html` to PDF when ready to apply
- LinkedIn profile (ras4hire) may need realignment with BPO-first framing

---

## Session 146 -- 2026-04-29 (cq-assistant)

### What
- Created `/cq-va` skill in `Knowledgebase-informdata/.claude/skills/cq-va.md` -- extraction + template filler for VA DOB verification emails
- Tested against live screenshot, worked correctly; added "Virginia Beach City Circuit Court | Mail" alias to lookup dictionary
- Built Flask webapp: `cq_app.py` (port 8400) + `templates/cq_index.html` -- drag/drop screenshot → Vertex AI Gemini → filled template → copy button
- Added `cq.duberymnl.com → port 8400` to CF tunnel config + DNS CNAME

### Decisions
- Used Vertex AI (ADC) instead of Google AI Studio key -- reuses existing DuberyMNL chatbot auth, no new credentials
- Port 8400 to avoid conflicts with existing ports (8090, 8300, 8085, 8123, 8124)

### Deployed
- Nothing deployed (cloudflared restart pending)

### Blockers
- Restart cloudflared process to activate cq.duberymnl.com tunnel -- paused this session, do at start of next

---

## Session 145 -- 2026-04-27 (music-discovery) [IN PROGRESS]

### Savepoint 00:00 UTC+8

**Done:**
- Used YouTube API skill to search PH music for RA during work hours (YouTube blocked on work network)
- Found Wish 107.5 performances: Yuridope (4 videos), Al James (4 videos), Waiian (3 videos)
- Found End Street x Reg Rubio collab: "Amarilyo" (MV + lyric video, March 2026)
- Pulled full End Street discography (48 videos) across TOWERofDOOM + Tower of Doom Music + official channel
- Pulled full Forgetting 69 discography (11 videos) via their official channel
- Researched 10 similar PH pop punk/alt bands: Not Informed, Story Unfold PH, There's Era!, 123 Pikit!, Pedicab, December Avenue, Cup of Joe, Lostthreads, Typecast, Chicosci
- Saved all findings to `.tmp/ph-music-youtube.md`

**Learnings:**
- YouTube watch history is NOT available via the Data API even with full OAuth — only liked videos and playlists
- Generic YouTube search is noisy for band names; better to find official channel ID first, then search within channel
- Tower of Doom Records is the hub label for PH alt/punk scene: End Street, Typecast, Chicosci, December Avenue, Lostthreads, Pedicab all under their umbrella

**Memories saved:**
- reference_ph_music_playlist.md -- RA's PH music YouTube links saved at .tmp/ph-music-youtube.md

---

## Session 143 -- 2026-04-25 (pricing-499-order-picker) [IN PROGRESS]

### Savepoint 15:30 UTC+8

**Done:**
- Committed carry-over from prev sessions: generate_vertex.py aspect_ratio fix (reads from `api_parameters.aspect_ratio` fallback) + rasta-brown image cleanup (3 deleted, 1 updated)
- Pricing drop: 499/pair (was 599), free shipping on 2+ (removed 99 bundle discount)
  - Updated: `chatbot/knowledge_base.py`, `chatbot/cloudflare-worker/worker.js` (redeployed, ID da28c30d), `dubery-landing-v3/products/data.json`, `order/order.js`, `order/index.html`
  - Provincial: pre-pay only (unchanged), nationwide coverage (unchanged)
- Fixed all remaining 599 refs across v3 landing: `index.html` (title, meta, hero, best-sellers, story, CTA), `order/index.html`, `products/index.html`, `products/item.html` (price, subtotal, testimonial), `shop-social/index.html`
- Removed qty pills (1 pair / 2 pairs buttons) from PDP `item.html` + dead qty pill JS in `item.js`
- Decided: replace v3 /order/ card grid with v1-style picker (option A)
- Pushed 3 commits to GitHub: session 143 pending cleanup, pricing changes, v3 sitewide 599→499

**Decisions:**
- 499/pair flat (was 599); free shipping on 2+ replaces the "99 bundle discount + free shipping" mechanism
- Option A for order UX: port v1 picker (thumbnail + dropdown + stepper, auto-add row) into v3 /order/ page

**In flight:**
- /plan skill interrupted mid-launch for v3 order form picker port — research phase was done, plan not yet written

### Savepoint 01:41 UTC+8

**Done:**
- Pivoted from Marketing Tab plan to v3 order picker (user chose option 2)
- Replaced card grid + filter pills in `dubery-landing-v3/order/index.html` with `<div class="picker-rows" data-picker-rows></div>`
- Rewrote `dubery-landing-v3/order/order.js` — picker rows (native select + thumb img + stepper), auto-add row on last selection, remove row on qty=0, pre-fill from ?model=&qty=, sidebar render + submit all intact
- Added `.picker-rows`, `.picker-row`, `.picker-select`, `.stepper`, `.stepper-btn` CSS to `dubery-landing-v3/styles.css`
- Started cloudflared tunnel (was down) + HTTP server on 8300 for v3.duberymnl.com

**Decisions:**
- Used native `<select>` for the picker dropdown (not v1's custom thumbnail dropdown) — RA flagged result as visually "far from v1", needs closer match

**Learnings:**
- Cloudflared tunnel does not autostart — must manually run on each session: `powershell Start-Process cloudflared -ArgumentList 'tunnel run f2e8c4e2-7911-4fdf-bf05-af6dc9d9a6b2' -WindowStyle Hidden`

**In flight:**
- v3 order picker coded but visually not matching v1 — next: diagnose gap (likely need custom thumbnail dropdown like v1, not native select)

### Savepoint 03:55 UTC+8

**Done:**
- Restarted Command Center (was down, killed port 8090, relaunched via PowerShell hidden process)
- Diagnosed GH Actions story rotation failure (run 24905669104): `story_rotation.py` exiting 1 at slot 41/74 — `contents/ready/person/outback-green/test-green-67.png` not in git
- Found 4 total missing files in `fb-stories-pool-2026-04.json` (outback-green/test-green-67.png + 3 rasta-brown images)
- Removed 4 missing entries from pool JSON (74 → 70), updated `count` field
- Verified dry-run passes (slot 43/70 clean)
- Committed + pushed: `5da8268` — story rotation unblocked

**Learnings:**
- Story pool JSON had stale refs to files deleted/never committed — rotation silently dies mid-index rather than skipping missing files; no graceful fallback in story_rotation.py

**In flight:**
- v3 order picker visual fix still pending (native select → custom thumbnail dropdown)
- Next GH Actions cron run should confirm rotation is clean

**Memories saved:**
- feedback_story_pool_stale_refs.md -- story pool JSON can silently contain paths not in git; rotation dies hard, no skip fallback

**Memories saved:**
- project_dubery_pricing_499.md -- pricing locked at 499/pair + free shipping on 2+

---

## Session 142 -- 2026-04-25 (website-cc-fixes)

### What
- Set up `v3.duberymnl.com` via Cloudflare tunnel: port 8300, ingress rule added to `~/.cloudflared/config.yml`, DNS CNAME created, cloudflared restarted
- Confirmed v3 editor accessible at `v3.duberymnl.com?edit` -- no button needed, `?edit` param activates editor.js
- CC fix: images not showing in output -- regex in `content_gen.js` expanded to match `contents/runs/` in addition to `contents/new/`
- CC fix: Clear button not resetting session -- added `POST /api/agent/reset` endpoint in `app.py`, wired Clear button in `bot.js` to call it; CC server restarted
- Saved feedback: CC agent settings read bug (mode/type not re-read on subsequent gen runs)
- Drafted recruiter reply email with portfolio URLs (ai: ras-portfolio.pages.dev/portfolio, main: rasclaw.github.io/ras-portfolio/)

### Decisions
- `v3.duberymnl.com` via CF tunnel over subfolder -- cleaner URL, no relative path breakage

### Deployed
- v3.duberymnl.com live via CF tunnel (local port 8300)

### Blockers
- CC agent settings bug (mode/type only read on first gen) -- logged in memory, not yet fixed
- v3 landing: needs real hover/gallery shots, testimonials, UGC, domain swap

---

## Session 141 -- 2026-04-23 (editorial-ytthumbs) [IN PROGRESS]

### Savepoint 00:47 UTC+8

**Done:**
- Built new `EDITORIAL_CUTOUT` brand variant (selective color -- B&W scene + colored product)
  - 2 Bandits Green thumbs generated (female + male), both PASS prompt-reviewer after V1/V6 patches
  - Files: `contents/new/2026-04-22_EDITORIAL-bandits-green-01.png` + `-02.png`
- Reviewed Upwork "AI Thumbnail Designer (Realistic YouTube Thumbnails)" gig ($1k fixed, 8 connects)
  - EA pushback: positioning drift + portfolio gap + economics risk
  - RA chose to build portfolio anyway
- v1 YT thumb spec set (3 thumbs, PH-flavored, MrBeast cringe style) -- RA rejected as wrong direction
- Researched the actual winning aesthetic: clean premium cinematic, photoreal AI hero, 2-5 word text + heavy outline, international/generic settings, no PH tells
- v2 spec set generated (4 thumbs): wealth, AI/tech, history/mystery, sigma/self-help
- Luxury spec set generated (4 thumbs): mansion, supercar, watch, jet -- gold accent text, no visible brand logos
- 3 Gmail send scripts in `.tmp/` (v1, v2, luxury) -- all sent to sarinasmedia@gmail.com

**Decisions:**
- New EDITORIAL_CUTOUT variant deviates from brand-bold S4 (caps text at 2 elements); deliberately 4 text elements to match concept -- candidate for codifying as `/dubery-brand-editorial` skill after second validated batch
- Use gold accent for luxury thumbs instead of red; red for "clickbait premium" niches -- rule: luxury aesthetic rejects loud red
- No branded products in AI-generated thumbs (no real Ray-Ban, Bugatti, Rolex) -- legally clean baseline

**Learnings:**
- Gemini 3.1 Flash renders YT thumb text reliably on first pass with: heavy black outline + phone-thumbnail-legibility callout + explicit line-break specification ("line one reads X, line two reads Y")
- Selective-color treatment works in Gemini when phrased as "grayscale EXCEPT [subject]" + "single most important rule of the image"
- PH context (jeepney, sari-sari, provincial road, Filipino models) is a dead giveaway for local market -- immediate mismatch for international Upwork clients
- Empty `image_input: []` works fine for text-only thumb generation (no ref needed)
- 10-sentence ceiling holds for prompt reviewer V6; got 15-sentence fail on first editorial pass, trimmed to 10

**In flight:**
- Nothing running in background
- 14 new images in `contents/new/` pending sort: 2 editorial-bandits-green + 3 v1 PH-thumbs (archive-only) + 4 v2-niche + 4 luxury + 1 already-moved duplicate

**Memories saved:**
- feedback_international_no_ph_context.md -- rule: strip PH markers from any portfolio/spec work targeting international clients
- project_ytthumb_spec_portfolio.md -- 8-thumb Upwork portfolio state + workflow proven (Vertex + Gmail send)
- project_brand_editorial_cutout.md -- new DuberyMNL brand variant, selective color, Bandits Green validated

---

## Session 139 -- 2026-04-22 (v3-hover-images-cc-autostart) [IN PROGRESS]

### Savepoint 23:30 UTC+8

**Done:**
- Built `portfolio.html` -- standalone AI image portfolio page for Upwork job application
- Deployed to https://ras-portfolio-one.vercel.app/portfolio.html via ras-portfolio Vercel project
- Built reusable deploy pipeline script at `DuberyMNL/.tmp/portfolio_deploy.py`:
  - Extracts base64 images → `assets/portfolio-images/`
  - Copies all DuberyMNL-relative image paths to ras-portfolio
  - Compresses all PNGs → JPEG at q82 (~5x size reduction)
  - Updates all HTML src references automatically
- Removed Edit button from live portfolio (`<!-- EDIT TOGGLE -->` comment + button element)
- Drafted Upwork proposal for "AI Image Creator for Lifestyle Product Images" ($35-60/hr, <5 proposals)

**Decisions:**
- Vercel over GitHub Pages: GitHub has 100MB file limit, portfolio was 193MB raw
- Extract + compress over CDN: self-contained deploy, no external dependencies
- portfolio.html lives in DuberyMNL (source of truth), ras-portfolio is deploy target only

**Learnings:**
- 193MB single-file HTML (base64 images) exceeds both GitHub Pages and Vercel 100MB limits
- Solution: extract base64 → files + compress PNG→JPEG brings 193MB → 33MB
- Vercel 100MB limit applies per-file AND total deploy -- both must be under limit
- `errors='replace'` needed when writing HTML with Unicode arrows (→) on Windows cp1252

**In flight:**
- Upwork proposal drafted, not yet submitted -- RA to review and submit

**Memories saved:**
- reference_portfolio_deploy_pipeline.md -- portfolio.html deploy pipeline: extract base64 + compress + Vercel

### Savepoint 18:15 UTC+8

**Done:**
- Revised Upwork proposal for "AI Image Creator for Lifestyle Product Images" ($35-60/hr, <5 proposals) — addressed all 6 job post bullet points with DuberyMNL pipeline proof
- Decided to update main profile instead of specialized profile (specialized not available without job history/account standing)
- Rewrote main Upwork bio to lead with image pipeline; recommended rate increase $20 → $35/hr
- Generated portfolio PDF using screenshot-stitch approach (Playwright fullPage → Pillow resize+slice → A4 pages): 1.9MB, 6 pages, pixel-perfect layout
- Fixed ras-portfolio root: updated vercel.json to redirect `/` → `/portfolio.html`, deployed to prod
- Drafted Upwork portfolio project entry (title, role, description, skills)

**Decisions:**
- Rate $20 → $35: current rate undersells and anchors all future proposals in the wrong bracket
- Screenshot-stitch over Playwright print-to-PDF: preserves exact visual layout, avoids text reflow artifacts

**Learnings:**
- Playwright print-to-PDF reflows and distorts layout — not faithful to screen rendering
- Screenshot-stitch pattern: `fullPage: true` screenshot → resize to A4 width (1240px) → slice into 1754px tall pages → `Pillow.save(..., save_all=True, append_images=pages[1:])` → 1.9MB result
- Canvas taint from `file://` URLs blocks JS image compression — must serve from localhost to bypass
- Upwork specialized profiles require job history / account standing — unavailable on new accounts

**In flight:**
- Upwork proposal drafted and ready — RA to submit
- Upwork portfolio project entry drafted — RA to submit

**Memories saved:**
- reference_portfolio_pdf_screenshot_stitch.md -- fullPage screenshot → Pillow A4 slice → PDF, pixel-perfect
- project_upwork_ai_image_application.md -- proposal copy + profile update state for AI Image Creator job

### Savepoint 05:55 UTC+8

**Done:**
- Hosted dubery-landing-v3 on port 7070 via `python -m http.server 7070 --bind 0.0.0.0`
- Set up Command Center autostart via Windows Startup folder — copied `boot.bat` to `C:\Users\RAS\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\`
- Updated `command-center/README.md` to reflect Startup folder approach (removed stale Task Scheduler reference)
- Started Command Center on port 8090
- Replaced all 11 catalog hover images using the catalog-edit HTML export workflow:
  - catalog-edit (1): replaced 9 of 11 (4 Bandits failed to register first pass)
  - catalog-edit (2)–(4): iterated until all 4 remaining Bandits hovers captured
  - Python script extracts base64 data URLs from saved HTML → writes to `assets/catalog/`
- Generated Rasta Red caption (2 versions: editorial + direct-response)

**Decisions:**
- Startup folder over Task Scheduler for CC autostart — no admin rights needed, terminal window confirms it's running

**Learnings:**
- Catalog editor drag-and-drop sometimes silently fails — verify by checking MD5 hash of base64 between saves
- Deleting asset files + Ctrl+Shift+R hard refresh clears browser cache so missing images become visible
- Identical file sizes between saves = reliable signal that drop didn't register

**In flight:**
- RA verifying hover images look correct on http://localhost:7070/products/

**Memories saved:**
- reference_catalog_hover_workflow.md -- how to extract hover images from catalog-edit HTML saves

---

## Session 138 -- 2026-04-20 (cc-online-mobile) [IN PROGRESS]

### Savepoint 11:45 UTC+8

**Done:**
- Loadout: killed orphan Claude session PID 7556
- Fixed chatbot port ref in Command Center monitor (8080 → 8085)
- Added `chatbot_monitor` service — checks `monitor.py` watchdog process is running via Windows process list
- Added secret URL auth to Command Center: `/auth/<token>` sets session cookie, all non-localhost routes gated
- Changed Flask binding `127.0.0.1` → `0.0.0.0` so Cloudflare tunnel can reach it
- Added `cc.duberymnl.com` ingress to `~/.cloudflared/config.yml` + DNS CNAME created via `cloudflared tunnel route dns`
- Added `CC_SECRET_TOKEN` + `FLASK_SECRET_KEY` to `.env`
- Created desktop shortcut: `C:\Users\RAS\Desktop\DuberyMNL Command Center.url` → `http://localhost:8090`
- Added plain-language service descriptions to monitoring tab (under each row name)
- Updated display names: "Chatbot Flask" → "Messenger Bot", "chatbot_monitor" → "Chatbot Watchdog", etc.
- Sent auth URL to RA via Telegram

**Decisions:**
- Secret URL auth (not password page) for cc.duberymnl.com — simpler for phone use, cookie persists after first visit
- Localhost access bypasses auth entirely — only external requests gated

**In flight:**
- Mobile-friendly pass in progress — interrupted before writing HTML/CSS

---

### Savepoint 14:30 UTC+8

**Done:**
- Mobile nav bar: added `<nav class="mobile-nav">` to shell.html with all 8 tabs (condensed labels), `@media (max-width: 640px)` CSS block — sidebar hides, bottom nav appears, content full-width, bot FAB repositioned above nav, grids collapse to 1-col
- Image Bank tab: replaced "Coming in Phase 3" with full working gallery
  - `/api/image-bank` endpoint scans `contents/ready/` + `contents/new/`, returns 291 images with type/model metadata sorted newest-first by mtime
  - Filter chips: All / Person / Product / Brand / New (purple)
  - Per-type model chips (Bandits Blue, Outback Black, etc.)
  - Filename search, live count badge
  - Masonry grid with lazy-loaded thumbnails + colored type badges
  - Lightbox: full-size view, prev/next arrows, keyboard ←/→/Esc, Copy URL, Download button (triggers phone save)
  - Image bank reloads on every tab visit (picks up newly generated images automatically)
- Regen history fix: `streamFeedback` now calls `/api/log-generation` for any new images it generates and appends a history batch row immediately
- Concept upload `+` button: added file input trigger to direction composer so phone users can upload screenshots without paste/drag-drop
- Stop button: Generate button turns red and says "Stop" during generation; uses AbortController to cancel fetch; any already-found images saved to history on stop

**Decisions:**
- Image bank sorted by mtime descending (newest first) — no manual tagging needed
- Stop = abort fetch stream (client-side cancel); server-side agent may still run briefly but images already found are preserved

**Learnings:**
- Flask with `debug=False` caches templates — server restart required for HTML changes to reflect
- Error 524 on CF tunnel = origin gave no response (server was mid-restart, not a persistent issue)
- Two CC instances (PC browser + background process) can conflict on port 8090 — use cc.duberymnl.com on both

**In flight:**
- CC running on :8090 (background process PID 12888)
- Cloudflare tunnel running (cc.duberymnl.com live)

**Memories saved:**
- feedback_cc_dual_instance.md -- two CC processes on port 8090 cause 524s; use cc.duberymnl.com on both devices
- feedback_flask_template_cache.md -- Flask debug=False caches templates; restart needed for HTML changes

**Memories saved:**
- reference_cc_command_center.md -- cc.duberymnl.com auth URL, port, env vars, desktop shortcut
- feedback_flask_tunnel_host.md -- Flask must bind 0.0.0.0 for CF tunnel to reach it

---

### Savepoint 17:00 UTC+8

**Done:**
- Diagnosed CC agent not responding on mobile: root cause was `asyncio.Lock()` in `AgentSession.__init__()` — gets bound to first event loop, fails on all subsequent per-request event loops
- Fixed: changed `asyncio.Lock()` → `threading.Lock()`, `async with` → `with` in `agent_session.py`
- Killed dual-instance conflict (3 stray PIDs on :8090), restarted clean (PID 17308)
- Added mobile streaming fallback in `bot.js`: detects mobile user agent, uses `await res.text()` instead of ReadableStream (SSE streaming unreliable on mobile Safari/Chrome)
- Deployed DuberyMNL v3 to Vercel for mobile phone access
- Replaced base64-embedded hero image (28MB → 26MB index.html) with file reference `assets/hero/outback-blue-hero.png` (new image: `2026-04-20_HERO-OUTBACK-BLUE-BESPOKE-v2.png`)
- Iteratively tuned hero `object-position` for mobile: 50% (default, face cut) → 25% (too far left) → 38% → 60% → 75% (RA still evaluating)

**Decisions:**
- `threading.Lock()` instead of `asyncio.Lock()` in AgentSession — Flask spawns a new thread+event loop per request; asyncio locks are per-loop

**Learnings:**
- `asyncio.Lock()` at module init binds to first event loop that uses it; all subsequent requests on different loops get "bound to a different event loop" RuntimeError
- CC agent was silently failing on ALL requests (not just mobile) — the 524 masked the real error
- editor.js bakes hero image as base64 into index.html — always extract to file after editor saves

**In flight:**
- CC running on :8090 (PID 17308)
- CF tunnel running (cc.duberymnl.com live)
- v3 hero object-position at 75% — RA evaluating on phone

**Memories saved:**
- feedback_asyncio_lock_threading.md -- asyncio.Lock at module level breaks per-request event loops; use threading.Lock
- project_dubery_v3_landing.md -- updated: new hero image + Vercel URL + object-position 75%

---

## Session 137 -- 2026-04-20 (chatbot-monitor)

### What
- Built `chatbot/monitor.py` — watchdog that owns chatbot subprocess; 30s health-check loop; auto-restart + TG crash notification; TG long-poll for `/restart` + `/status` commands
- Built `chatbot/start-monitor.bat` — Task Scheduler entry point for monitor
- Updated Task Scheduler `DuberyMNL-Chatbot` task to run `start-monitor.bat` instead of `start-chatbot.bat`
- Added "Running in production" section to `chatbot/README.md` (startup flow diagram, TG commands table, manual override)
- Changed chatbot port `8080` → `8085`: `PORT=8085` in `.env`, updated `monitor.py` + `~/.cloudflared/config.yml`
- Updated all port refs in README + added `PORT` to config table
- Fixed TG poll 409 spin: 60s backoff on conflict instead of 10s retry loop
- Diagnosed 409 root cause: Claude Code Telegram plugin (`bun server.ts`) holds long-poll on same bot token; `/restart` + `/status` commands only work when Claude Code is closed

### Decisions
- Port 8085 dedicated to chatbot — nothing else should bind it
- Task Scheduler runs monitor; monitor owns chatbot subprocess (no NSSM)
- TG command poll backs off 60s on 409 (Claude Code plugin conflict is expected, not a bug)

### Deployed
- Monitor live on :8085, Cloudflare tunnel routing updated, Task Scheduler updated

### Blockers
- Test bot via Meta developer test account (in progress)
- Provincial handoff E2E still unconfirmed

---

## Session 136 -- 2026-04-19 (dubery-v3-landing-editors)

### What
- Completed `/order/` multi-variant picker + wired PDP "2 pairs" pill to `/order/?model=<slug>&qty=1`
- Fixed order submit payload: FormData `payload` field (raw JSON silently dropped by Apps Script)
- Added `order_name` per variant in `data.json` (EN-DASH format, matches v1 sheet convention)
- Delivery fee: ₱99 single, FREE on 2+ pairs; PDP grand total includes delivery (₱698)
- Swapped hero to `bandits-tortoise-hatclean-wide-v2.png` (1376×768); tuned mobile `object-position`
- E2E order flow validated: 2 test rows in "DuberyMNL Orders" sheet (rows 9 + 10, ₱1698 3-pair)
- Explored Claude Design (research preview); set up DuberyMNL Design System; PLDT/Cloudflare loop fix = ProtonVPN/WARP
- Chatbot fixes: `handoff_flagged` disk-persist bug, Sheets `.execute()` no-timeout, Vertex prewarm, ADC scope (K_SERVICE gate), Gemini token limit 800→1500, `cache_discovery=False` hang
- Built `editor.js` for `dubery-landing-v3/index.html` — `?edit` visual editor (images + text); committed v3 to GitHub first time (59 files)
- Trimmed best sellers to 4; removed filter pills + swatch dots via Python regex
- Plan approved for `chatbot/monitor.py` (Task Scheduler → monitor.py → chatbot subprocess + TG /restart); implementation deferred (5hr limit hit)
- Built `chatbot/monitor-chatbot.bat`; fixed ADC/CRM, Gemini tokens, cache_discovery; provincial handoff rule added to system prompt
- Command Center Marketing tab MVP (tasks 4–12): backend routes, 3-column UI, dry-run gate, `contents/new/` filter pill, cp1252 fix in pull_insights.py
- Thumbnail grid bug fixed: `grid-auto-rows: 110px` (not `aspect-ratio`); verified via Node Playwright
- Ingested Behance Glowwave carousel design spec: 4 unity constants + 6 layout formats + mood-wash pattern
- Content Gen direction presets trimmed to 1 chip; CSS grid `min-width: 0` fix on Content Gen right column
- Built `products/item-editor.js` — PDP visual editor (`?slug=X&edit`): image replace/add, editable fields, Save HTML
- Built `products/catalog-editor.js` — catalog hover editor (`/products/?edit`): body-class toggle, per-card overlays, Save HTML
- Applied outback-black PDP edits (5 gallery images) + all 11 catalog hover images via Python extract scripts

### Decisions
- PDP = single-variant; multi-variant → `/order/` (simpler UX, no variant picker inside PDP)
- Keep v1 sheet convention (EN-DASH + FormData+payload) — zero migration, Apps Script works unchanged
- Editor UX = Exit + Save HTML only (matches `editor.js` pattern; Copy JSON + Download Images rejected)
- Extract workflow: Save HTML → Python regex → `assets/catalog/` + `data.json` (inline script, not a saved tool)
- ADC gated to Cloud Run only (`K_SERVICE`) — local always uses `token.json`
- CRM service pre-warmed at startup (not lazy) to prevent first-message blocking
- Glowwave structure adopted, not tone — DuberyMNL stays quiet-confidence per brand identity
- Model/lifestyle shots preferred for hover swaps (not social graphics)

### Deployed
- `dubery-landing-v3/` first push to GitHub (59 files)
- `item-editor.js` + `catalog-editor.js` wired into products pages
- outback-black: 5 gallery images in `assets/catalog/`
- All 11 products: hover images in `assets/catalog/{slug}-hover.png` + `data.json` updated
- chatbot: crm_sync.py, conversation_engine.py, messenger_webhook.py fixes live
- Command Center Marketing tab live on :8090
- `chatbot/monitor-chatbot.bat` created

### Blockers
- `monitor.py` not yet written (plan at `~/.claude/plans/i-want-a-windows-frolicking-dolphin.md`)
- Real model shots for hover swaps pending (RA to supply)
- Other 10 products still use original gallery images on PDP

---

## Session 135 -- 2026-04-18 (dubery-v2-homepage-polish) [IN PROGRESS]

### Savepoint 00:15 UTC+8 (2026-04-19)

**Done:**
- Fixed flickering near/below scratch-proof section (005→006 transition): removed fade-OUT from bidirectional fade — sections now only fade IN from below, stay at opacity 1 as they leave
- Attempted `background: var(--bg-dark)` on `.flow-section` to kill flicker — killed the peacock entirely, reverted
- Added peacock dim: `#dark-overlay` (fixed, z-index 2) driven by JS — ramps to `OVERLAY_MAX` (0.62) as sections come into view
- Tried `.flow-section::before` flat overlay (rgba 0,0,0,0.62) for per-section dim — caused new flicker (::before inherits parent opacity, two competing systems clashing), removed
- Settled on `#dark-overlay` JS-only for all dimming — no ::before on sections
- Cloudflare quick tunnel died multiple times → switched to Vercel CLI preview deploy for stable phone testing URL
- Phone test revealed multiple issues: hero not centered, flickering everywhere, slow peacock image load, misaligned text/images
- User plans fresh Opus session for mobile audit + fix

**Decisions:**
- `::before` pseudo-elements banned on `.flow-section` for dimming — they inherit section opacity and fight the JS fade system
- Vercel `vercel --yes` is the reliable preview URL method; CF quick tunnels unreliable when named tunnel credentials exist

**Learnings:**
- CSS `::before` pseudo-elements inherit parent `opacity` — when section fades in (0→1), `::before` also animates, creating double-dim flicker
- `background` is NOT an inherited CSS property — flow-sections were always transparent to the peacock (by design)
- Cloudflare quick tunnel returns edge 404 when named tunnel credentials exist in `.cloudflared/` — tunnels conflict
- `vercel --yes` from inside `dubery-landing-v2/` deploys a stable preview URL in ~10s

**In flight:**
- Vercel preview: https://dubery-landing-v2-ha35hrej4-rasclaws-projects.vercel.app
- Mobile issues outstanding — Opus session planned for full audit + fix

**Memories saved:**
- feedback_pseudo_element_opacity_inherit.md -- ::before inherits parent opacity, breaks section fade dimming
- feedback_vercel_preview_over_cf_tunnel.md -- Vercel CLI > CF quick tunnel for stable phone preview

### Savepoint ~01:30 UTC+8 (2026-04-19)

**Done:**
- Ingested Fix.com "Choosing the Right Fishing Sunglasses" article (Tyler Brinks, 2018)
- Created raw + summary + updated INDEX.md + ingest-log.md
- Attempted automated access via WebFetch + Playwright headless — fix.com uses Akamai WAF, 403 all approaches, not indexed by Google
- RA saved 4 article images manually to `C:\Users\RAS\Documents\Polarization\`
- Read all 4 images; lens colors infographic revealed 2 extra lens types not in article text (Green Mirror, Silver Mirror)
- Updated summary with full 7-lens color matrix + DuberyMNL fit notes
- Updated raw file with image paths

**Learnings:**
- fix.com (Akamai CDN) blocks WebFetch, Playwright headless, and has no Google-indexed blog pages — manual paste is the only viable ingest path
- Lens infographic > article text: infographic adds Green Mirror (copper+amber base + mirror) and Silver Mirror (copper base + mirror) with specific use cases
- Blue Mirror = clear water + extreme bright sun = strong PH year-round fit; Amber = max brightness field of view = everyday outdoor

**Memories saved:**
- reference_fishing_lens_colors.md -- 7-lens outdoor sunglass guide + DuberyMNL content hooks (polarization test video)

### Savepoint ~23:30 UTC+8

**Done:**
- Established DuberyMNL v2 brand identity through iterative copy discussion: "Made for the view" — outdoor life, polarization as revelation not just protection
- Rewrote all homepage copy: Hero / Clarity (001) / Collections (002) / Value (005) / CTA (006)
- Collections: series names only — Bandits / Outback / Rasta — no descriptions, product speaks for itself
- Replaced stats section with Facebook Community section ("Shop our Facebook.")
- Applied all copy to index.html + added hero-sub CSS style
- Auto-hide header on scroll down (JS scroll direction detection)
- Removed opacity change on collection card hover (CSS)
- Fixed centering on large screens: flow-section → flex column + align-items center; content containers → max-width + margin: auto
- Scaled site to 80% (html font-size: 80%)
- Removed backdrop-filter from mobile media query (flicker fix)
- Fixed section min-height: 60vh → 90vh (prevents peacock bg gaps between sections)
- Implemented bidirectional section fade (rAF-throttled scroll listener, fade in on enter / fade out on leave)
- Used Playwright to inspect Knockaround.com scroll-reveal pattern (standard IntersectionObserver, no heavy GSAP)

**Decisions:**
- Stats section → Facebook Community section (more social proof value)
- Series cards: names only, no copy (product identity speaks for itself)
- Bidirectional scroll fade over one-shot IntersectionObserver reveal (RA wants sections to fade both in AND out)
- min-height: 90vh not 60vh — sections must cover viewport to prevent peacock gap flicker

**Learnings:**
- min-height < viewport + moving peacock bg = gap flicker between sections as you scroll
- backdrop-filter on any element over the peacock grid = GPU re-raster flicker (confirmed again)
- RA copy feedback: "generic" = explaining technology, not the experience. Product-first beats poetic abstraction.
- Knockaround uses no heavy GSAP — simple Shopify/Tailwind with standard scroll behavior
- rAF throttling on scroll listener is cleaner than raw events for real-time opacity updates

**In flight:**
- Preview server at http://127.0.0.1:8123 (may need restart)
- RA reviewing latest flicker + bidirectional fade changes

**Memories saved:**
- feedback_section_coverage_flicker.md -- section min-height must cover viewport or peacock gaps flicker
- project_dubery_v2_brand_identity.md -- brand identity locked: Made for the view, outdoor life
- feedback_dubery_copy_direction.md -- product-first copy beats poetic tech abstractions

---

## Session 134 -- 2026-04-18 (sonnet-migration-prep) [IN PROGRESS]

### Savepoint ~22:30 UTC+8

**Done:**
- Verified `autoCompactWindow` semantics via docs: it's a trigger threshold, not post-compact target size
- Default threshold = model_context_window - 45k = ~155k on Sonnet 200k; our 185k pushes it 30k later
- Established savepoint sweet spot: call at 75% context (~150k used) → lands ~158k after savepoint → 27k margin to 185k autocompact

**Decisions:**
- 75% context = savepoint trigger point for Sonnet 200k + 185k autoCompactWindow (RA confirmed)

**Learnings:**
- `autoCompactWindow` is the trigger threshold -- fires compaction when usage hits that token count
- At 37% context now (73k/200k), well within safe territory

**In flight:**
- None

**Memories saved:**
- feedback_savepoint_sweetspot.md -- 75% context (~150k) is the optimal savepoint trigger

### Savepoint 22:xx UTC+8

**Done:**
- Resumed via RESUME.md flow -- confirmed the workflow works end-to-end
- `/model sonnet` switched per-session; `settings.json:115` updated from `opus[1m]` → `sonnet` (persistent, authorized by RA)
- Confirmed Sonnet = 200k context only; `[1m]` suffix is Opus 4.7-exclusive
- Discovered `autoCompactThreshold` doesn't exist in settings schema -- rejected on write
- Correct field is `autoCompactWindow` (integer, 100k–1M tokens); set to 185000

**Decisions:**
- Permanent model: `sonnet` (200k) -- faster, cheaper; jump to `opus[1m]` per-session when 1M needed
- `autoCompactWindow: 185000` -- pushes autocompact fire point later in conversation

**Learnings:**
- settings.json self-modification triggers permission gate -- requires explicit RA authorization each session
- `autoCompactWindow` is a token count (not percentage); exact semantics (trigger threshold vs post-compact target size) unverified
- The 33k "autocompact buffer" in `/context` output may be hardcoded headroom, not configurable

**In flight:**
- None

**Memories saved:**
- feedback_settings_self_modification.md -- settings.json edits need explicit auth each session
- reference_autocompact_window.md -- autoCompactWindow field, 185k token setting

### Savepoint 21:41 UTC+8

**Done:**
- Loadout check (tunnel healthy, power plugged, 3 local sessions no orphans)
- Discussed Pro-plan migration: per-session `/model sonnet[1m]` vs permanent settings.json line 115
- Confirmed Sonnet 4.6 supports 1M context via `[1m]` suffix (tier-gated on Pro)
- Designed context-continuance workflow: `/savepoint` + `/clear` + resume from RESUME.md (beats `/compact` on 200K window)
- Wired RESUME.md overwrite into `/savepoint` skill (~/.claude/commands/savepoint.md)
- Added pinned-first-line RESUME pointer spec for MEMORY.md index
- Testing the new flow via this savepoint

**Decisions:**
- Default to `sonnet[1m]` when migrating, fall back to plain `sonnet` if 1M beta not granted on tier
- RESUME.md = single source of truth for "where was I," overwritten every savepoint
- `/clear` + resume from RESUME > `/compact` on Sonnet -- cleaner, smaller reload footprint

**Learnings:**
- `/compact` at 160K retains ~20-40K of compressed buffer; `/savepoint` + `/clear` reloads ~5-8K of structured state on resume
- Auto-loaded context (CLAUDE.md + current-priorities + goals + MEMORY.md) already primes sessions — RESUME.md is the only missing piece for precise cursor-position

**In flight:**
- Testing savepoint flow end-to-end (this is the test)
- Model switch to `sonnet[1m]` still pending RA go-ahead

**Memories saved:**
- reference_resume_pointer.md -- RESUME.md pattern + how /savepoint wires it

---

## Session 133 -- 2026-04-18 (command-center-phase-2)

### What
- Built Command Center Phase 2 Content Gen tab end-to-end
- Added `--type person|product` flag to `v3_randomizer.py`
- Two-column layout (30/70): form controls left, output workspace right
- Mode pills: UGC / Brand / Bespoke (concept recreation workflow)
- Product picker (multi-select up to 4), inventory stats card (per-product person/product/UGC counts)
- Direction mini-chat: paste concept images + conversational confirm before generating
- Image paste/drag-drop upload → agent reads and interprets concept
- SSE streaming output with collapsible progress log + typing dots animation
- Image result cards with V1-V8 validation checklist (pass/fail grid)
- Lightbox on click for all images, "Reference used" section (concept + prodref side by side)
- Feedback composer appends to output without clearing
- Server-side generation history (`.tmp/content-gen-history.json`) with full metadata
- Toast notification system (slide-in, color-coded)
- Theme overhaul: dark GitHub → light Claude AI (warm cream, white cards, subtle shadows)
- Monitor tab: Fix buttons for offline services (chatbot, tunnel)
- 6 new API endpoints: products, content-stats, upload-concept, log-generation, generation-history, images
- Agent `max_turns` 10 → 30
- 4 successful image generations: 1 UGC outfit match, 2 brand/PRADA-concept, 1 bespoke underwater coral reef
- Bespoke mode validated: RA pasted random web images → agent produced high-fidelity brand recreations

### Decisions
- Simplified form from session 131 spec (6 pill rows) to Mode/Type/Count + chat direction (RA preferred simplicity)
- Direction is conversational mini-chat, not static textarea -- agent confirms understanding before generating
- Bespoke mode skips randomizer, goes straight to fidelity-prompt from concept image
- Light theme for Command Center (dark theme stays for duberymnl.com)
- Server-side history persistence over localStorage

### Deployed
- Nothing deployed -- deferred commit, no push.

### Blockers
- Server crashes under long agent sessions (needs error recovery)
- Clean up insider language in progress output (batch_randomizer → generic terms)
- Save concept images + full prompt data per generation
- Marketing tab + proactive bot bubbles (Phase 2 remaining)

---

## Session 132 -- 2026-04-18 (dubery-v2-website-build)

### What
- Major dubery-landing-v2 build session with RA -- extensive visual iteration via live preview + custom editor
- Converted Dubery TTF → WOFF2 (regular + italic) via fonttools, wired `@font-face`
- Hero: two-tone DUBERY (off-white) + MNL (red), centered, red glow text-shadow, logo-header.png above
- Removed promo/util bars from top of page
- Built lightning electricity canvas effect (rare 8-45s bursts), later removed to simplify
- Swapped collection series cards from product box shots to model wearing shots (3 models)
- Built Protection section: text-left + 3 product images grid-right (bandits-tortoise, outback-blue, rasta-brown)
- Built Value section: text-left + 2 product flatlays side-by-side right (bandits-glossy-black, outback-black)
- Peacock tile floor: 62deg lean (up from 58), opacity 0.55, brightness 0.72, vignette softened
- Section fade-on-scroll effect via IntersectionObserver-style scroll listener
- All section labels (002-005) removed, 001/Protection kept
- Sections set to 100vh, tightened padding (10vh top)
- Snap scroll added then removed per RA preference -- smooth Lenis only
- Built visual editor tool (`editor.js`) activated via `?edit` URL param:
  - v1→v3 evolution: floating panel → undo+multi-select → direct manipulation
  - 8 resize handles (4 corner free/proportional + 4 edge single-axis)
  - Click=select, drag=move, corner=resize, Ctrl+Click=multi-select
  - Text resize changes width (wrapping) not font-size
  - Double-click=inline text editing (green outline, Enter/Escape to exit)
  - Sketch/pen tool with canvas undo
  - +Text/+Image buttons insert into DOM flow (not floating)
  - Export captures per-element state: file path, position, size, visible/deleted status
  - Container elements (section, div) excluded from selection
  - Link navigation blocked in edit mode
- Light theme attempted (cream backgrounds), reverted -- too bright/overpowering per RA

### Decisions
- **Dark theme stays.** Light theme tested across 3 brightness levels (#f5f3ef → #e8e5e0 → #d4d0ca), all overpowered the peacock tiles. Reverted to original #0a0a0a.
- **Smooth scroll over snap.** Snap scroll felt too rigid for RA's taste.
- **Transforms → layout.** Editor exports CSS transforms but transforms break click targets. Convert large offsets to padding/margin/grid for production CSS.
- **Visual editor as dev tool.** `?edit` param loads editor.js; zero impact on production site. Speeds up visual iteration significantly.

### Deployed
- Nothing deployed -- deferred commit, no push.

### Blockers
- Server keeps dying between file edits (python http.server process terminates) -- consider file-watching auto-restart
- Mobile responsiveness not tested
- More sections to polish (Best Sellers cards, CTA button)
- Editor quirks: generic selectors on some elements, server restarts needed
- Not committed to git or deployed yet

---

## Session 131 -- 2026-04-18 (command-center-phase-2-scoping)

### What
- Discussion-only session. No code written. Scoped Phase 2 Content Gen tab with RA.
- Form shape locked: flat form (not stepper, not chat-first chip builder), all fields visible at once, blank field = randomize.
- Input controls locked: pill chips (not dropdowns), multi-select per row, +/- stepper for count.
- Field set locked: Mode / Product / Category / Count / Location / Scene. Mode pill reshapes the visible rows — UGC shows Location+Scene pills, Brand shows Skill+Layout pills instead.
- Read `tools/image_gen/batch_randomizer.py` + `tools/image_gen/v3_randomizer.py` + `.claude/skills/ugc-pipeline/SKILL.md`. Surfaced the two-randomizer wrinkle: UGC mode routes through `v3_randomizer.py` (has `--product`, `--category`, `--count`; missing `--location`, `--pose`); Brand mode routes through `batch_randomizer.py` (has `--type`, `--count`; different dimensions: layouts not locations).
- Sketched a three-part plan (extend `v3_randomizer.py` with location+pose flags → build pill form → mode-aware pill rows) but did NOT write it to `.tmp/plan.md` — RA paused to savesession before approval.
- Parked Marketing "agent thinking" window as Phase 2 polish (portfolio prop, not MVP).

### Decisions
- **Flat pill form, not stepper or chat-first.** Optional fields + sequential stepper clicks fight each other; chat-first muddles the tab-vs-FAB distinction set in Phase 1.
- **Multi-select pills over single-select.** Lock 1-N values per row, randomizer picks among the locked set. Matches how RA thinks about batches.
- **+/- stepper for count, not pill row.** Pill row caps the values; stepper is flexible.
- **Mode pill reshapes the field set.** UGC and Brand have genuinely different dimensions — don't flatten them into one row.
- **All locks flow through randomizer CLI flags, never through agent prompt hints.** Saved as `feedback_form_always_randomizes.md`. Reasons stack: `/ugc-pipeline` Step 3 already mandates it, dedup logic can't be bypassed by accident, CLI flags are deterministic where prompt hints are soft.

### Deployed
- Nothing pushed to remotes this session (closeout run in deferred mode). Also nothing deployed — discussion only, no code changes.

### Blockers
- `.tmp/plan.md` not yet written. Next session: draft it from the Phase 2 scoping memory, covering the three-part build (randomizer CLI extension → pill form → mode-aware rows).
- `v3_randomizer.py` needs `--location` and `--pose` CLI flags added before the Location/Scene pills can be wired. Prerequisite for Phase 2 MVP.
- Meta Ads 5-ACTIVE-vs-paused discrepancy carried from session 130 — still waiting on RA eyeball.
- Session 129 `dubery-landing-v2/` tree still uncommitted (intentional, waiting on polish signoff) — this closeout does not touch it.

---

## Session 130 -- 2026-04-18 (command-center-phase-1-shell)

### What
- Built DuberyMNL Command Center Phase 1 MVP end-to-end: local web dashboard with a persistent Claude Agent SDK session as the backend. 27 new files under [command-center/](command-center/). 46/46 Phase 1 tasks complete.
- Backend: Flask on port 8090, UTF-8 + CORS + request logging, SSE `/api/agent/chat` streaming through a module-level `AgentSession` that reuses session_id across requests (cheap resume after first-call cache-create).
- 9 monitor modules (chatbot, tunnel, worker_fallback, meta_ads, story_rotation, rasclaw_tg, chatbot_tg, crm_sheet, inventory) wired via a registry with cheap/expensive flag. `/api/monitor/status` runs 9 checks in parallel (cheap batch <2s, expensive batch ~6s). `/api/monitor/logs/<service>` tails last 50 lines when `log_source` set.
- `/api/home/summary` aggregates revenue (Phase 3), active convos (chatbot `/status`), pending approvals (`pipeline.json`), and system health pill (worst state across cheap monitors).
- Frontend: dark theme (`#0d1117` bg, `#ff9e4b` warm accent, Inter font), sidebar nav with 8 tabs, hash-based routing with `tab:activated` custom event. Home and Monitor tabs fully wired; Content Gen, Marketing, CRM, Chatbot, Image Bank, Inventory show "Coming in Phase 2/3" placeholders.
- Floating Claude chat FAB bottom-right: click-to-open overlay, SSE streaming, `localStorage` history (last 20 messages), clear button, typing indicator.
- Monitor tab renders Option B layout (9 dense rows with glowing status dot + relative timestamp + logs button). Auto-polls cheap checks every 30s while tab is active, stops on nav-away. "Refresh expensive" button runs the full batch. Modal log viewer with ESC + overlay-click dismiss.
- Research phase produced [.tmp/command-center-research.md](.tmp/command-center-research.md) (~1500 words + YouTube transcripts from Cleroux's Claude Code dashboard + Kulkarni's Next.js Agent SDK SaaS tutorial) and [.tmp/plan.md](.tmp/plan.md) (46 tasks, dependencies, acceptance criteria, risks, verification checklist).
- Layout pick validated via `/brainstorm` visual companion (Cloudflare quick tunnel so RA could vote from work laptop). Shell preview validated the same way before wiring the backend.
- Phase 1B dispatched 9 monitor subagents in parallel (all passed their individual acceptance checks).
- Bug found + fixed mid-build: `monitors.register()` rebinding `SERVICES = [...]` in a new list — broke the registry for any caller who'd already done `from monitors import SERVICES`. Swapped to in-place mutation.
- Agent SDK subscription auth verified via 10-line smoke test. Works through VSCode tunnel from work laptop — no need to be at home to install/configure.

### Decisions
- **Path A+ (local agentic dashboard) over production SaaS** — fastest ship for portfolio screenshots + personal ops, matches Rasclaw architecture RA already knows. Production SaaS path (Kulkarni's Next.js + Clerk + Drizzle + Fly) deferred to whenever RAS Creative needs a client demo.
- **Lives inside DuberyMNL repo under `command-center/`** rather than a separate repo — reuses existing `.env`, `tools/`, and `.claude/skills/` imports with zero plumbing. Can graduate to its own repo in Phase 3 if that's cleaner.
- **Monitor layout: Option B (dense vertical rows)** — picked via `/brainstorm` preview vs A (grid cards) vs C (wall-mount status board). B wins on info density above the fold.
- **Shell: left sidebar nav, not tabbed top bar or single long scroll page** — closest to SaaS dashboards buyers recognize, scales with more tabs later.
- **Proactive bot trigger: hybrid (event-driven + periodic safety net)** — matches how a good EA behaves. Deferred implementation to Phase 2.
- **Claude Agent SDK, not `claude --print` subprocess or custom channel plugin** — SDK is Anthropic's sanctioned programmatic wrapper around the same subprocess pattern Rasclaw uses, with clean streaming + session resume. Uses RA's Claude Code subscription, no API-key burn.

### Deployed
- Nothing pushed to remotes this session (closeout run in deferred mode). Cloudflare quick tunnel used for in-session previews only.

### Blockers
- Meta Ads monitor reports 5 ACTIVE adsets, but `current-priorities.md` item 1h says ads are still paused — needs RA eyeball to reconcile (either adset-level ACTIVE ≠ campaign-level, or ads got unpaused and priorities file is stale).
- Phase 2 plan not written yet (Content Gen form wiring + Marketing action buttons + proactive bubbles).
- `.env` additions still pending: `WORKER_URL`, `GITHUB_TOKEN`, `RASCLAW_BOT_TOKEN`. Monitor modules degrade gracefully when absent (state=not_wired) so nothing is broken, just under-reporting.
- Session 129 (dubery-landing-v2) still `[IN PROGRESS]` — leaving as-is, this closeout covers only the command-center work.

---

## Session 129 -- 2026-04-17/18 (dubery-v2-peacock-scroll)

### What
- Built `dubery-landing-v2/` from zero to working cinematic website. Five visual pivots landed on: simple flow sections + fixed peacock UGC tile-floor as scroll-linked background. Dark palette, Space Grotesk + Inter fonts, no card chrome.
- Preview wired via existing named Cloudflare tunnel: `review.duberymnl.com → localhost:8123` serves `dubery-landing-v2/` via `python -m http.server`. Zero Vercel auth friction. Prod `dubery-landing/` untouched.
- Added `/products/` catalog page: 11 variant cards mapped to `contents/assets/product-specs.json` (5 Bandits / 4 Outback / 2 Rasta), series filter tabs (URL-synced via `?series=`), deep-link anchors from home best-sellers row.
- Tile pool refiltered to UGC-heavy (131 tiles: 97 person + 34 brand, no kraft). Thumbnailed to 380×520 JPG ~23KB each, ~3MB total.
- Diagnosed + fixed Cloudflare edge-cache staleness: per-geography CDN meant dev laptop saw fresh CSS while RA's work network got old. Per-file `?v=<tag>` cache-bust is now mandatory on every asset URL.
- Adopted `read code, don't screenshot` discipline (feedback saved). Playwright DOM inspection (getBoundingClientRect, computed styles) replaces self-orientation screenshots; screenshots reserved for proving results TO RA.
- **Best-sellers flicker fixed.** Root cause: stale duplicate `.featured-card` + `.series-media` rule blocks had `backdrop-filter: blur(8px)` not overridden by the later "no chrome" declarations. Blur over the 262-img tilted peacock grid forced GPU re-raster on every scroll frame. Deleted duplicate blocks + added `transform: translateZ(0)` + `will-change: transform` on `.featured-card` / `.featured-media` for GPU compositor promotion (hover transitions during scroll no longer trigger layer rebuilds).
- **Section left-edge alignment fixed.** `.section-series` / `.section-featured` / `.section-brand-story` swapped from `justify-content: center` → `flex-start` with `padding-left: 6vw; padding-right: 6vw`. Collections / Best Sellers / Value now line up with the DUBERY nav logo + Protection section.
- **Built a real web font from the DUBERY-FONTS.png sample** end-to-end, no hand tracing:
  - De-skewed the italic source (PIL shear inverse) so column-gap segmentation could work.
  - Segmented 26 letters (row-by-row; auto-split merged F/G via widest-run column-minimum finder).
  - Extracted Calligraphr template via `pypdfium2` (pymupdf DLL load failed on Windows → fallback). Detected grid lines (9 vertical + horizontal) to find each A-Z cell coordinate.
  - Filled template with baseline-aligned letters. Q descender handled as 13% of bbox below baseline. Row 4 (U-Z) shifted up 56px (~2 guide lines) so all four rows share a consistent visual position inside their cells.
  - Built two template variants: upright + forward-italic (+13° right shear; PIL affine matrix `(1, s, -s*H, 0, 1, 0)`).
  - RA uploaded both to Calligraphr, built `Dubery-Regular` + `DuberyItalic-Regular`, downloaded TTF + OTF of each (4 files, ~6-8KB).
  - Converted TTF → WOFF2 with `fontTools` (3.4KB / 4.4KB).
  - Wired `@font-face` block + `--font-dubery` var in `styles.css`. Hero `.hero-heading` + `.nav-logo` now render in Dubery italic (size bumped to `clamp(3rem, 7.5vw, 7rem)` on hero for impact).

### Decisions
- **Simple flow > timed visibility system.** Normal `<section>` flow with `min-height: 80vh`, opacity always 1, single `gsap.to` on peacock grid = reliable. Three attempts with the rasta-scroll `data-enter`/`data-leave` dispatcher all had glitchy mid-scroll disappearing. Saved `feedback_simple_flow_beats_scroll_scrub.md`.
- **No card chrome rule.** Product / series / featured cards all have no bg / no border / no backdrop-filter. Peacock peeks between elements.
- **Kraft product shots for catalog only.** Removed from ambient tile-floor pool; kept in `assets/products/` hero + featured rows. Saved `feedback_kraft_not_in_ambient_bg.md`.
- **Preview hosted on tunnel, not Vercel.** `review.duberymnl.com` via existing named tunnel avoids Vercel auth. Saved `reference_cloudflare_tunnel_preview.md`.
- **Delete stale CSS rule blocks, don't override them.** The "no chrome" rewrite kept the old `.featured-card` rule intact so backdrop-filter survived unnoticed. Consolidation is cheaper than override-patching.
- **GPU layer promotion on hover cards in scroll-linked backgrounds.** `transform: translateZ(0)` + `will-change: transform` prevents layer rebuilds when a hover transition fires mid-scroll.
- **Ship two font variants (regular + italic), not italic-only.** CSS `font-style` toggles per use case — wordmark italic, other headlines upright when wanted. Italic letters in Calligraphr cells need forward lean (+13°, top shifts right); getting the shear sign right took one iteration.

### Deployed
- Nothing pushed to remotes. Closeout run in deferred mode. Preview lives on `review.duberymnl.com` via the existing chatbot tunnel. `dubery-landing-v2/` tree still untracked in git — intentional, waiting on RA polish signoff before committing.

### Blockers
- Best-sellers flicker fix not yet user-verified (moved on to fonts before RA confirmed the scroll was smooth). Worth a quick check next session.
- Font sizes may need tuning after RA views live (hero at `7.5vw`, nav logo at `1.5rem`).
- `dubery-landing-v2/` tree still not committed to git — waiting on polish signoff.
- Parked: Seedance/Veo hero loop, Three.js accents, /about + /how-it-works + /faq pages, DNS prod swap, founder story final copy, frontend-design plugin A/B.
- Chatbot tunnel was briefly killed mid-session while freeing a quick tunnel; restored via `schtasks /run /tn DuberyMNL-Tunnel`, confirmed 200. Watch for similar collisions if doing quick-tunnel tests near the chatbot.

---

## Session 128 -- 2026-04-16/17 (rasclaw bypass + brand-coll-B3 + story-rotation-fix)

### What

**Rasclaw bypass mode (5-file architecture):**
- [CLAUDE.md](CLAUDE.md) — added `contents/ready/` + `contents/assets/` directory map (chatbot/fb-stories banks, hero, prodref-kraft, product-refs, specs). Auto-loads when Rasclaw launches from DuberyMNL repo.
- `~/.claude/scripts/rasclaw-guard.py` (NEW) — PreToolUse hook. Reads tool JSON from stdin, exits 2 with stderr (= deny) when `RASCLAW_MODE=1` env var is set AND command matches deny patterns (rm -rf, git push, reset --hard, rebase, mv, gh destructive, vercel rm, shutdown, destructive SQL, writes to .env/credentials/secrets/token). Exits 0 immediately when env var unset → local sessions untouched.
- `~/.claude/scripts/rasclaw-system-prompt.md` — rewrite. Operating Mode block (bypass-permissions + guard aware) + Responsiveness rules (ack immediately, narrate plans for 3+ tool calls, progress pings for >15s ops, short replies) + Image-requests section with bank paths inline.
- `~/.claude/scripts/start-rasclaw.bat` — added `set RASCLAW_MODE=1`, `cd ~/projects/DuberyMNL`, `--permission-mode bypassPermissions`, duplicate `RASCLAW_MODE=1` inside bash invocation.
- `~/.claude/settings.json` — added PreToolUse hook matching `Bash|Write|Edit|NotebookEdit`, command runs `python ~/.claude/scripts/rasclaw-guard.py`.
- Smoke-tested: safe cmd exit 0, `rm -rf` with RASCLAW_MODE=1 exit 2 with reason, same cmd without flag exit 0 (local untouched).

**Brand Collection Batch B3 (15 generated, 12 passed):**
- Passed: COLL-B3-001-edit (Bandits triangle, bouclé, warm spot), 001-v2 (typography-only), 002-edit (Bandits DUO, terrazzo, cool side), 003-edit (Bandits Heritage, gunmetal, rim+key), 004-edit (Rasta DUO fanned, tadelakt, moody rim), 005-edit (Outback diagonal, charcoal felt, warm golden), 006 (Outback triangle, basalt, dramatic spot), 007-edit (OUTBACK SERIES lineup, dark linen), 008 (cross triangle arms folded, navy ceramic), 008-v2 (cross triangle arms open 3/4), 010 (cross HERO_CAST moody, dark cork), HC4 (cross HERO_CAST stripped, dark cork, MADE POLARIZED).
- Failed: 009 (5-up cross row, lenses drifted), 011 (UNBOX exploded flat-lay, fidelity load too heavy), HC1–HC3 (Rasta Brown rendered as Bandits Tortoise shape — rounded → slim square when mixed).
- Moved 12 PNGs + 12 prompt.json sidecars to `contents/ready/brand/`. Added 12 manifest entries (tags: LANDING, POST, AD) + 12 metadata entries.
- Validated formula (saved to memory `project_brand_collection_formula.md`): 5-input attachment (N prodrefs + font + logo) + fidelity triad (PHOTOREALISTIC_INTEGRATION + relight_instruction + per-product fidelity line) + 3 scene levers (surface + lighting + arrangement) = 100% fidelity on 3-product images. Drift at 5+ products when typography stacking (gradient, accent, identity line, branding-hide, no-bg logo) bloats the prompt.
- Font accent-color rule: match typography tone to the dominant lens/arm color (warm golden for Outback Line's lighting; gradient for subsequent tasks). Branding-hide directive clarified as flatlay-only (arms folded, top-down view); angled layouts keep branding natural.
- Two-pass identity text pattern: if base gen lands composition but omits identity line, run lightweight image-to-image edit ("add DUBERY [SERIES] text below sunglasses") instead of full regen. Used on 001, 002, 003, 004 retrofit.

**Story rotation fix:**
- Diagnosed 3 consecutive cron failures (2026-04-16 09:08, 13:04, 17:02 UTC). Root cause: session 126 curated `fb-stories-pool-2026-04.json` pointing to `contents/ready/product/{model}/...` paths, but `contents/ready/` is gitignored → GH runner had 14 old-path tracked files + 74 new-path untracked pool entries → failed on pick #1.
- Force-committed 74 pool PNGs (~113MB) to `contents/ready/product/` + `contents/ready/person/` despite gitignore (commit `bad5473`). Excluded sidecars + non-pool content (437→74 files, 378MB→113MB).
- Bumped cadence 4h→3h: `tools/facebook/story_rotation.py:50` (`hours // 4` → `hours // 3`) + `.github/workflows/story-rotation.yml:7` (`0 */4 * * *` → `0 */3 * * *`). Commit `6058970`.
- 2 manual smoketests passed: run `24530047161` (pick 1/74 bandits-matte-black), run `24530254227` (pick 51/74 bandits-green). FB Post IDs captured. Next scheduled cron: 21:00 UTC.
- Backlog entry added to `~/projects/EA-brain/context/current-priorities.md`: "Story rotation content delivery (proper fix)" — runtime fetch from Drive or Cloudflare R2 to stop bloating git with content.

### Decisions

- **Rasclaw bypass gated by `RASCLAW_MODE=1` env var, not global settings change.** Local Claude Code preserves normal permission flow. Guard enforces safety via hook-level deny list. Context: previous curated allowlist (~90 Bash patterns) hit 20+ prompts for "fetch 3 images from bank" — bypass + guard is the right model for a personal phone channel.
- **`git push` blocked entirely in Rasclaw.** Pushes stay on PC sessions. Prevents accidental phone-triggered deploys.
- **Launcher `cd`s to DuberyMNL** so project CLAUDE.md loads automatically. Single source of truth for directory awareness — rasclaw-system-prompt.md only adds responsiveness rules, not duplicate paths.
- **Brand collection formula (locked):** 3 scene levers + fidelity triad + 5-input attachment. `DUBERY [SERIES]` identity line for single-series only; skip for cross-series. Polarized tagline rotation: STAY / ALWAYS / DUBERY POLARIZED. Branding-hide flatlay-only.
- **Content repo bloat (temp fix):** force-commit 74 pool PNGs despite gitignore. Violates `feedback_content_storage_rule` (git=code, Drive=content). Proper fix (Drive/R2 runtime fetch) on backlog. Accepting the bloat is cheaper than the alternative — script fix is ~1-2 hrs, commit + push was 2 min.
- **Story cadence 3h (8/day) over 4h (6/day).** Still under Meta's ~10/day soft ceiling. No-repeat guarantee preserved via modulo sequence (cycle 9.25 days).
- **Stopped brand-coll batch at task 11** when prompt drift broke fidelity. Pivoted to 4 stripped-template HERO_CAST variants to isolate cause. Validated: minimalism on scene levers is load-bearing.

### Deployed

- DuberyMNL: `bad5473` (74 pool PNGs force-committed) + `6058970` (3h story rotation cadence) pushed to origin/main earlier in session.
- Story rotation: LIVE + 3h cadence. 2 manual smoketest posts went live on FB page (bandits-matte-black, bandits-green).
- 12 brand collection images staged in `contents/ready/brand/` with manifest + metadata tags for POST / LANDING / AD distribution.
- Current session files (Rasclaw scripts + memories + PROJECT_LOG + manifest/metadata) committed locally per `/savesession` deferred mode — awaiting `/sendit` for final push + backup + Drive sync.

### Blockers

- **Rasclaw new bypass config needs relaunch** — RA must kill current Rasclaw process + run `start-rasclaw.bat` on next use for the new behavior to activate.
- **Orphan session PID 11032** still idle from earlier loadout check. Kill when convenient: `Stop-Process -Id 11032 -Force`.
- **Rasta Red kraft prodref unreliable** — renders gold/amber lenses instead of red mirror in mixed batches. Backlog: regenerate with stronger red accent, or isolate Rasta Red to own scenes only.
- **009 (5-up cross row) + 011 (UNBOX exploded)** failed fidelity — candidates for stripped-template regen in a future session.
- **Brand-collection-pipeline skill** not yet built; formula is validated and ready to codify. Backlog.

---

## Session 127 -- 2026-04-16/17 (chatbot employee discipline + admin surface)

### What

**Rasclaw bypass mode (first half of session):**
- Designed + applied Rasclaw bypass mode across 5 files: [CLAUDE.md](CLAUDE.md) (banks+hero+prodref-kraft directory map), `~/.claude/scripts/rasclaw-guard.py` (NEW PreToolUse hook blocking rm -rf / git push / reset --hard / rebase / mv / .env writes when `RASCLAW_MODE=1`), `~/.claude/scripts/rasclaw-system-prompt.md` (full rewrite with Operating Mode + Responsiveness + Image-requests sections), `~/.claude/scripts/start-rasclaw.bat` (env var propagation + bypassPermissions + cd to DuberyMNL), `~/.claude/settings.json` (PreToolUse hook matcher).
- Smoke-tested guard: safe commands exit 0, `rm -rf` with RASCLAW_MODE=1 exits 2 with reason, same command without flag exits 0 (local PC sessions unaffected).

**Chatbot employee-discipline upgrade (second half, Alkabir-triggered):**
- Audited last 8h of DMs, diagnosed 5 failure modes in the Alkabir 27-msg spiral (phantom QR claimed 5x, no loop detection, no complaint catch, first_name not persisted, 9x identical policy repeats).
- Shipped 7 stacked guardrails in `chatbot/` (formerly `cloud-run/`):
  1. **Human takeover** — echo `app_id != META_APP_ID` → flag handoff, bot silent.
  2. **Complaint detector** (pre-Gemini) — ~30 PH trust/scam/deflection phrases, short-circuits with bridge line + TG ping.
  3. **Policy pushback** (pre-Gemini) — `prepay_provincial` + `no_discount` stamped once; customer pushback on delivered policy short-circuits Gemini, bridge + handoff.
  4. **Phantom QR injector** (post-Gemini) — regex catches "here's our QR" claims, auto-adds `support-instapay-qr` image.
  5. **Turn cap** (post-Gemini) — `TURN_CAP=10` assistant replies without `order_complete` → override reply + handoff.
  6. **Loop guard** (post-Gemini) — 3 consecutive identical theme-sig replies → override + handoff.
  7. **first_name persist** — Gemini-extracted name stamped to `conv.metadata.first_name`.
- Added Phase 1 **ad-referral capture**: `source_ad_id` / `source_ref` / `source_type` stamped on conv metadata + logged to `.tmp/referral_log.jsonl`.
- Added `/flag/<sender_id>` and `/release/<sender_id>` admin endpoints.
- **Echo logging**: every manual reply from Page Inbox captured to `conversation_store` + CRM (`intent=manual`) — closes invisibility gap on manually-closed sales.
- **24h time-decay handoff release**: stale flags auto-clear on next customer msg.
- **18h proactive nurture scanner**: daemon thread fires ONE follow-up per customer when 18-23h silent + showed `inquiry`/`order` interest + not handed-off/sold/nurtured. 3 rotating templates inside Meta's 24h window.
- Flagged Alkabir (PSID `...0248768733`) for manual takeover.

**Rename + portfolio doc:**
- `git mv cloud-run chatbot` (preserves history). 8 file path refs updated, Task Scheduler re-registered, log renamed `.tmp/chatbot-server.log`, CLAUDE.md marks `tools/chatbot/` as stale + adds "Chatbot (active)" pointer section.
- Wrote [chatbot/README.md](chatbot/README.md) — 14 sections: architecture diagram, 7-guardrail table, env vars, admin endpoints, roadmap. Portfolio-shippable as-is.

**Admin surface (owner-facing endpoints + dashboard):**
- `/mark-sale/<sender_id>` — structured CRM capture for Page-Inbox manual closes. Accepts JSON/form/query. Required: items + total. Optional: quantity, payment_method (default COD), delivery_preference/time, discount_code, name/phone/address/landmarks (triggers `upsert_lead`), note, force (override dup-guard), flag_handoff=false. Writes CRM Orders row via `create_order`, stamps `order_recorded` + `last_order_id/total/at`, flags handoff, resets reply-signature FIFO. 409 on double-sale without force.
- `/conversations` v2 admin dashboard — rich per-convo badges (handoff+reason, order+id+total, policy chips, source ref/ad_id, nurture, last 3 intents), 11-counter stat bar, per-row AJAX RELEASE/FLAG/MARK-SALE buttons, inline MARK-SALE form, toast notifications.

**Ad-aware openers Phase 2:**
- `chatbot/ad_registry.json` — 15 entries: 9 per-variant (each Bandits/Outback/Rasta color), 3 per-series (BANDITS_SERIES, OUTBACK_SERIES, RASTA_SERIES for single-image lineup ads), 3 generic (PRICING_SALE, COLLECTION_HERO, FULL_CATALOG).
- `conversation_engine.get_ad_context()` lookup (ref-first, ad_id-fallback, lazy-cached).
- `generate_reply(..., ad_context=...)` kwarg injects `AD_CONTEXT:` + `AD_PRODUCT_FOCUS:` into Gemini's system prompt on first contact ONLY; turn 2+ skips hint.
- Fallback safe: unknown refs → None → generic SALES TEMPLATE.

**System prompt softening (disciplined-employee voice):**
- New REPLY CLOSES section: default neutral closes, probe only on undecided-new OR mid-order-collection. Forbids `policy + promo + "which model?"` stacking (Alkabir pattern).
- PROMO UPSELL now "ONCE per conversation" — stops `(FREE shipping 2+!)` tail-spam.
- `ok/sige/noted` softened: reply briefly + stop, no "Anything else po?" reflex.
- 2 new JSON examples show neutral-close behavior. Live Gemini validation (3 turns on /chat-test): provincial Batangas policy → no which-model pile-on + QR attached; decline "mahal pala" → "Sige po, take your time..."; sizing question → complete answer + no probing follow-up.

**Three savepoints written mid-session** (00:30, 01:30, 02:00 UTC+8) — full savepoint history preserved here before consolidation.

### Decisions

- **TURN_CAP=10, not 6.** Simple buyer closes in 5 turns, browsing buyer 7-8, chatty buyer 10+. The cap is a last-line backstop; misfired handoff on an in-progress sale is worse than a missed handoff (the other 6 guardrails catch specific failures earlier). Erring loose.
- **Directory named `chatbot/`, not `flaskbot/`.** Role-based, not framework-based. `cloud-run/` rotted when we abandoned Cloud Run; naming after Flask would rot the same way if we ever migrate off.
- **Policy one-shot rule.** Policies are stated ONCE per customer (stamped in `policies_delivered`), pushback is NOT a re-negotiation. Encoded via `security.POLICY_DEFINITIONS`. Foundational principle for any disciplined-employee bot.
- **Nurture window 18-23h strict.** Inside Meta's 24h standard-messaging window with 1h safety buffer. One nudge per customer ever (tracked via `nurture_sent`).
- **Echo-logging fires on EVERY manual reply**, not just first takeover. Multi-message manual closes captured fully.
- **`deploy.sh` kept as DEPRECATED reference.** Cloud Run migration was decided against 2026-04-16; keeping the script for potential future reversibility, clearly marked. Rename doesn't change that decision.
- **`/mark-sale` accepts JSON + form + query (first-wins).** Maximum flexibility: browser URL, curl, dashboard AJAX — one endpoint serves all.
- **Ad registry is a flat JSON file** (not a DB). Lazy in-process cache. Good enough for current scale; hot-reload deferred.
- **Rasclaw bypass isolated via `RASCLAW_MODE` env var.** Not a global settings change. Preserves local Claude Code's normal permission flow.
- **Rasclaw blocks git push entirely.** Pushes stay on PC sessions (safer for phone-driven agent).
- **Multi-tenancy isolation deferred** to a clean-head session. Shipping too many things in one night sacrifices quality review time.
- **README kept portfolio-standard** (env var names + laptop refs stay). Public-repo scrub is a parked item for when DuberyMNL gets open-sourced or attached to Upwork.

### Deployed

- **Chatbot restarted multiple times** this session. Final live process confirmed at `started_at 2026-04-16T17:19:20+00:00` (local ~01:19 on 2026-04-17). `/status` 200, `warmup_complete: true`, nurture scanner thread active. All admin endpoints live: `/mark-sale`, `/flag`, `/release`, `/conversations` v2, `/chat-test`, `/status`, `/readiness`, `/webhook`.
- **Rasclaw bypass mode NOT yet relaunched** — activates on next `start-rasclaw.bat` boot (kill current Rasclaw process or reboot phone). First half of session only staged the config; Rasclaw itself can keep running with old behavior until next restart.
- **Task Scheduler tasks re-registered** via `install-autostart.ps1` to point at new `chatbot/` paths. Arguments now reference `C:\Users\RAS\projects\DuberyMNL\chatbot\start-chatbot.bat`.
- **Alkabir manually flagged** — `handoff_flagged=True, reason=human_takeover`. Bot silent on him, RA to follow up whenever.

### Blockers

- **Multi-tenancy isolation** — biggest deferred item (45-60 min focused work). Pending next session.
- **Ad-registry won't fire until ads are tagged** — RA needs to add `{"ref": "<TAG>"}` to each live Click-to-Messenger ad's Messenger-destination JSON payload in Ads Manager. Without tags, Phase 2 behavior falls back to generic SALES TEMPLATE (which is fine, just doesn't showcase the ad-aware feature).
- **18 memory files still reference `cloud-run/` path** — sweep on next `/lint-memory` run.
- **/mark-sale CRM write returned 502 on cold start** during smoke test — Sheets API + Google auth take a moment to warm after restart. Real sales will work fine once bot is fully warmed.
- **README scrub decision** deferred — portfolio-standard as-is; public-facing cleanup pending.
- **Client-pitch push** (README polish + 2-min demo video + Upwork listing) is the shortest path to first RAS Creative customer, estimated 4-6 hrs.
- **Rasclaw: orphan PID 11032 from earlier in session** — kill command was staged but not executed; may or may not still be running (unverified at closeout).

---


## Session 126 -- 2026-04-16 (image review reorg + bank curation)

### What
- Reorganized `contents/ready/` from flat + legacy folders to `person/{model}/` + `product/{model}/` + `brand/` + root-level `metadata.json` (197 images; visual inspection of ~60 ambiguous files, pHash-16 matching for disambiguation)
- `image_review_recent.py`: added `--review-failed` mode (scans `contents/failed/`, no time cutoff, approve = recover to ready/), added sidecar move alongside image (handles both `{stem}_prompt.json` and `{stem_minus_output}_prompt.json`), backfilled 163 historical sidecars + relocated 18 batch001/002 stragglers, then deleted empty folders
- Hid 140 sidecar JSON files via Windows Hidden attribute (Explorer shows only images, manifest.json + metadata.json left visible)
- Built `tools/image_gen/model_gallery.py` — model-grouped picker at :8125 with preload-from-saved-picks feature, click-select + lightbox + export-to-JSON
- Built `tools/facebook/upload_album.py` — parameterized Meta album uploader (not usable for album create, see decisions)
- Image gen batches (30 total): bandits-glossy-black 10-image UGC batch (9/10 pass) + 17-image chatbot image bank gap-filler across 9 models + 2 tortoise retries + 5 rasta-red concert shots + 3 rasta-brown products + 4 outback-red/green products. All tagged POST/STORY/AD/LANDING in manifest.
- Trimmed `product-specs.json`: removed "Slim straight glossy black temple arms..." from bandits-glossy-black, removed "Temple arms feature..." from bandits-tortoise. Reindexed all 6 sidecar `visible_details` to [0,1,2].
- Curated 2 permanent image banks (contents/assets/):
  - [chatbot-image-bank-2026-04.json](contents/assets/chatbot-image-bank-2026-04.json) — 44 picks (2P+2Pr × 11 models) for messenger chatbot
  - [fb-stories-pool-2026-04.json](contents/assets/fb-stories-pool-2026-04.json) — 74 picks for FB story rotation (6/day × ~12 day cycle)
  - Each pick enriched with metadata + manifest + full prompt sidecar

### Decisions
- Remove temple-arm lines from face-worn product specs (glossy-black + tortoise) — Gemini over-renders when the sidecar says visible_details=[0,1,2,3] but the final scene is a face portrait where arms go behind ears. See `feedback_spec_trim_face_worn.md`.
- UNBOXING/GIFTED/DELIVERY max 1 per batch (all anchor on same hero prodref). See `feedback_package_categories_sparingly.md`.
- Visual inspection is required for ambiguous filenames (`multiref_*`, `image_*`, `test-*`, `V3-*`, etc). Filename keywords alone misclassify. See `feedback_visual_image_inspection.md`.
- Meta album CREATE API is dead — `POST /page/albums` returns `(#3) Application does not have the capability` regardless of scope. Workaround: create album in FB UI once, then `POST /{album_id}/photos` for additions. See `reference_meta_album_api_limits.md`.
- Vertex AI Gemini 3.1 Flash image effective concurrency ~2 parallel; 429 RESOURCE_EXHAUSTED on higher. Batch pattern: 2 parallel + 25-30s stagger between waves. See `reference_vertex_rate_limits.md`.
- Bank files versioned permanently in `contents/assets/` (not `.tmp/`). On mutation, rename with `-v2` suffix before save to prevent overwrite loss. See `feedback_image_bank_backup.md`.
- Maintain both manifest-based (for distribution routing) AND folder-based (for human browsing) organization — different purposes, both kept.

### Deployed
- Nothing pushed (deferred mode)
- 3 local Flask servers up: review.duberymnl.com (8123), tag.duberymnl.com (8124), model gallery (8125 local-only)

### Blockers
- None new. (Wire-up of story_rotation.py + chatbot to the new bank files is being handled in parallel session 127.)

---

## Session 125 -- 2026-04-16 (chatbot hardening: Worker FAQ + behavior alignment)

### What
- Deployed Worker FAQ layer with intent classifier (pricing/polarized/shipping/how-to-order/order-intent), Workers KV dedup (10-min per-sender per-intent TTL, order-intent bypasses), suppress-polite-hold logic. Classifier unit-tested (34/34 pass) before deploy.
- Worker TG ping rule: only 🚨 on order_intent. Stripped 🔔 (customer waiting) and 🔁 (follow-up) pings — FAQ-answered customers often ghost, pinging RA was noise. Shipped as v2, re-tested origin-down.
- SYSTEM_PROMPT formatting fix: added MULTI-POINT REPLIES section with concrete WRONG/RIGHT example (Kingpin Batangas wall-of-text as the bad example). Forces Gemini to break multi-topic replies into blocks.
- Handoff dedup + 🔥 urgent-followup detection: first handoff fires standard 🚨 ping, subsequent should_handoff on already-flagged convos no longer spam. New `is_urgent_followup()` regex (phone+address, ASAP, urgent, rush, ngayon na, etc.) fires 🔥 TG ping for urgent follow-ups in handed-off conversations.
- Conversation store persistence: `conversation_store.py` now writes to `.tmp/conversation_store.json` on every mutation, loads on startup. Fixes returning-customer re-greeting (Kingpin was treated as new contact after Flask restart). Atomic writes, 30-day pruning.
- SALES TEMPLATE wired into Gemini first-contact: fires on pricing/greeting triggers ("hm", "magkano", "hi"), emits RA's manual 599 pitch verbatim with album URL. Preserves image-aware path (no template on screenshots/product asks).
- Album URL (`/share/p/1SuARZpPUz/`) wired across Worker FAQ pricing template + Flask SYSTEM_PROMPT + Meta comment auto-DM.
- Found + fixed Meta comment auto-DM 699 source: "Comment to message - PM SENT" in Meta Business Suite Automations. Template updated to nurture message ("What caught your eye?") + 10 keywords (hm, how much, magkano, price, order, avail, interested, mine, cod, free shipping) + album URL.
- Model shots removed from image bank (RA providing new versions). Image strategy aligned: 2-image combo planned (product-only kraft + packaging), pending CDN upload.
- Created `tools/facebook/upload_album.py` (parameterized, reusable). Silent album upload attempted — Meta auto-posted feed story despite no_story=true (known quirk). Album named "Catalog" by Meta auto-categorization.
- Diagnosed Christopher Zulueta convo (699 auto-DM vs Gemini 599 correction) and Kingpin Batangas followup (wall-of-text + re-greeting). Both fixed via tonight's changes.

### Decisions
- Worker pings only on order_intent (noise reduction). See `feedback_worker_ping_rule.md`.
- Handoff state: option B — bot keeps replying + urgent TG ping for follow-ups. No "silent mode" or "bot stops".
- SALES TEMPLATE preserves Kingpin image-aware pattern: no template on screenshots or product-specific asks.
- Comment auto-DM = short nurture + album link, not brochure dump. Conversion funnel: comment → nurture DM → customer replies → Gemini handles.
- Model shots pulled from image bank pending RA's new versions.
- Album feed story accepted (not worth cleanup effort).

### Deployed
- Worker v1 `845f06e6` (FAQ + KV + 3 TG flavors) → v2 `a29b0757` (ping strip) → v3 `3dbd73a4` (album URL) → v4 `5f8f3ea6` (corrected album URL)
- Flask restarted 4x with cumulative changes (formatting, handoff, persistence, SALES TEMPLATE, model shot removal)
- KV namespace `FAQ_DEDUP` created (id `3ff16e193cd2431eb770cd3bab232f58`)
- Meta comment auto-DM updated via Meta Business Suite UI

### Blockers
- Kraft hero product-only shots need CDN upload (Google Drive or duberymnl.com) before 2-image combo works in chatbot
- New model shots from RA (pending)
- Ad-aware chatbot (recognize which ad customer commented on): parked, ~30-45 min
- Auto-responder code rebuild (our own comment_responder.py): parked, future session
- Unpause boosted ads (RA manual, post Meta auto-reply cleanup)
- 1-week clean production data still needed

---

## Session 124 -- 2026-04-15/16 (chatbot architecture pivot + first closed order)

### Milestone: First real customer order closed through Gemini chatbot
- **Kingpin Dela Cruz** (profile name in Arabic script: ديلا كروز مسيحي) ordered 1x Outback Blue, same-day delivery 2pm, Taguig, 599 + shipping, COD.
- **Phase 1 (Gemini, 16:51-17:15 UTC)**: bot recognized stale 699 price in customer's uploaded screenshot and corrected to 599 with explanation, identified Bandits Glossy Black + Outback Black from 2 customer photos, presented 7-field order form, parsed filled form correctly, handed off gracefully with "The owner will message you shortly..."
- **Phase 2 (RA manual, 17:39-18:01 UTC)**: customer changed mind mid-convo (Bandits -> Outback Blue), RA negotiated 2pm delivery and closed. RA stumbled upon the convo without TG notification (FAQ+TG upgrade still being built).
- Memory saved at `project_first_closed_order.md`.

### Pivot: Cloud Run migration abandoned, laptop + CF Worker hardened
- Originally began the 16-task Cloud Run migration (`.tmp/plan.md`) after session 123 incidents.
- Deployed 23-task hardened plan (HMAC verify, Send API retry, structured logging, /readiness gate, multi-image in/out, PYTHONIOENCODING=utf-8, startup probe on /readiness).
- Deploy #1 failed: warmup only ran under `if __name__ == '__main__'`, never fired under gunicorn. Fix committed (`669291f`).
- Deploy #2 failed: warmup DID run (48/48 cached in 90s), but /readiness never flipped to 200 within the 5-min probe budget. Root cause not fully diagnosed.
- Audit of laptop log revealed laptop stack was NOT structurally broken: 2.6% error rate, single recurring cp1252 print-encoding bug, zero process crashes. Session 123 post-mortem was overstated.
- **Decided to pivot back** to laptop-primary + CF Worker fallback + TG notification. Hybrid architecture fits SMB scale and gives stronger RAS Creative portfolio story than managed-cloud story.
- Cloud Run service deleted (`duberymnl-chatbot` in asia-southeast1).
- Applied tonight's valuable commits to laptop: added `PYTHONIOENCODING=utf-8` to `start-chatbot.bat`, restarted Task Scheduler, laptop Flask now runs the full hardened code.

### CF Worker upgraded (polite hold + TG notification + event filtering)
- Replaced "we're offline" with polite hold: `"Hi! Got your message 🙏 give me a few minutes and I'll check and reply po."`
- TG notification to RA via Rasclaw bot — customer first_name (best-effort Graph API lookup), message preview, Messenger reply link.
- Skip fallback on Meta-generated events (`is_echo`, `quick_reply`, `postback`, `delivery`, `read`). Fixes the triple-reply pattern seen in today's inbox audit.
- Forwards `X-Hub-Signature-256` to origin so HMAC works end-to-end.
- Deployed to Cloudflare account `sarinasmedia+rasclaw@gmail.com`. Secrets set: `PAGE_ACCESS_TOKEN`, `TELEGRAM_BOT_TOKEN`.
- Commit `7b5ed02`.

### Inbox audit findings (informed design)
- **Triple-reply confirmed**: Meta Icebreakers + Meta Instant Replies (still showing ₱499!) + old CF Worker offline, all firing on ad-click quick-reply buttons within 3-5 seconds. RA himself typed `"Sorry, wait ung chatbot q tinotopak"` to a customer (Carlo 11:11). Pending: RA manually disable Meta auto-replies in Page Inbox settings.
- **RA manually sent the 599 sales template 5 times today** (Arjie, LJ, Jay Ar, Jermie, Lando) — strong signal this deserves automation.
- **Customer rapid-fire pattern is common** (Nandy 04:19 sent "How much? 🏷️" twice in same second) — justifies per-sender TG dedup.

### Flask bot TG handoff ping (CLOSES the Kingpin gap)
- Root cause: Gemini correctly returned `should_handoff: true`, `check_and_handle_handoff()` flagged conversation, bot said "owner will message you shortly" -- but nothing actually notified RA. The flag was a data field in `conversation_store`, not an external signal. Kingpin waited 24 min.
- New `notify_tg_handoff()` helper in `messenger_webhook.py`: fire-and-forget daemon thread, 5s timeout, sends Rasclaw TG ping with customer first_name (cached in `conv["metadata"]`), handoff reason label from `REASON_LABELS`, last customer message preview, direct Messenger reply link.
- Wired at the Gemini-flagged handoff path (NOT on security-flagged injection/bot_sender/output_leak -- those would be noise).
- TG creds added to `.env` (`TELEGRAM_BOT_TOKEN`, `TG_CHAT_ID=1762124488`). End-to-end TG path validated with a test ping.
- Emits `log_event("handoff_notified", ...)` structured log for grep/observability.
- Commit `59e22e8`.

### FAQ templates drafted for Worker (pending deploy)
- **Pricing**: existing 599 sales pitch (FB post URL swap pending RA's album work in another session)
- **Polarized**: "Yes po, all Dubery Sunglasses are Polarized."
- **Shipping combined** (with COD line): MM starts 100 / outside 150 / free at 2+ pairs / COD MM only
- **How to order**: aligned with Gemini's proven 7-field form
- **Order intent**: detect phone pattern + address keywords (covers both 3 and 7-field fills), fires urgent TG ping regardless of origin state
- **Disclaimer footer**: pending RA's pick between A/B/C wording
- **Cooldown**: 10-min per-sender dedup via Workers KV, order-intent bypasses gate

### Pending before next deploy
- Disclaimer wording choice (A/B/C)
- Workers KV namespace creation for dedup
- Worker redeploy with FAQ layer + dedup
- Disable Meta Auto-Replies in Page Inbox settings (manual RA step)
- Swap FB post URL in pricing template once RA's album is ready
- Live-test handoff TG ping with real customer handoff
- Screenshot + redact Kingpin Dela Cruz order for portfolio case study

### Commits tonight
- `e39a324` — Phase 2 code hardening (HMAC, retry, logging, multi-image, deploy.sh config)
- `6bcc41f` — CRM sync ADC fallback
- `669291f` — warmup at module-import fix (superseded by pivot)
- `7b5ed02` — laptop pivot + CF Worker upgrade
- `59e22e8` — Flask bot TG handoff notification

---

## Session 123 -- 2026-04-15 (10-video ingest batch: CRO + Routines + Cowork + Seedance) [IN PROGRESS]

### Savepoint 11:24 UTC+8

**Done:**
- Loadout check: tunnel healthy (dubery-dev), plugged in, 3 local VSCode + 1 telegram plugin sessions active, no orphans
- Ingested 10 liked YouTube videos total this session: 1 solo (Shiver Microsoft Clarity) + 9 batched via parallel Sonnet subagents (Nate Herk Seedance websites, Jay E Seedance video, Nate Herk Routines, Isenberg workflow, AI Edge make money, Chase AI top 10 skills, Sandy Lee content, Dan Martell all-in AI, Brock Cowork concepts)
- Reauthed YouTube OAuth token (all 6 scopes restored including youtube) — token had been narrowed by another Google tool
- Created 5 new reference memories: `reference_microsoft_clarity_cro.md`, `reference_claude_routines.md`, `reference_awesome_md.md`, `reference_skill_creator_skill.md`, `reference_cowork_client_framing.md`
- Added 7 backlog items to `current-priorities.md` (Microsoft Clarity install, Seedance hero workflow, Skill Creator Skill, awesome.md design reference, trend researcher spec, RAS Creative Cowork onboarding, dashboard moderator via Routines)
- Bidirectional cross-refs added by subagents and reconciled in main thread across shiver/aaron-young/jack-roberts/nate-superpowers/brad summaries

**Decisions:**
- Skipped installing most of Chase AI's top 10 (context bloat per Brad's guidance); only `awesome.md` + Skill Creator Skill cleared the INSTALL bar
- Kept Veo 3.1 as default video stack (Jay E Seedance confirmed Seedance 2.0 is 4-5x more expensive and Jay himself recommends Veo/Kling for general use)
- Claude Routines does NOT supersede existing cron/Task Scheduler; first genuine candidate = dashboard moderator only
- Low-signal ingests (AI Edge, Martell, Isenberg) still got summaries but flagged as rehash/motivation inside the summaries themselves — trusting `/lint-memory` to prune later if warranted

**Learnings:**
- Batch ingest pattern (9 videos in ~8 min wall time via parallel Sonnet subagents) validated. Previous ingests were 1-at-a-time.
- Subagents must NOT touch INDEX.md / ingest-log.md / MEMORY.md — concurrent writes conflict and formats drift. Main thread consolidates.
- Subagent briefing quality directly shapes summary quality. Adding RA's positioning + existing knowledge cross-refs + quality rules (opinionated, concrete actions) produced notably better summaries than generic "summarize this video."

**Memories saved:**
- `feedback_batch_ingest_pattern.md` — when 3+ sources, parallel Sonnet subagents; main thread consolidates
- (5 reference memories from the ingest batch noted above)

### Savepoint 12:10 UTC+8

**Done:**
- Live chatbot pricing + behavior patch (RA feedback during /savesession):
  - Pricing flattened: 599 per pair, no bundle discount. Promo = FREE shipping when ordering 2+ pairs. COD Metro Manila only.
  - `cloud-run/knowledge_base.py`: PRICING dict refactored (per_pair + promo_note, bundle_2/bundle_upsell removed); get_pricing_text() rewritten; get_catalog_text() no longer outputs model codes; FAQ Delivery Metro/Provincial + What's Included rewritten with plain numbers + new shipping rule.
  - `cloud-run/conversation_engine.py`: SECURITY RULES gained no-model-codes + no-peso-prefix rules; dedicated NAME USAGE block added above FIRST MESSAGE BEHAVIOR; all pricing examples + BUNDLE UPSELL / DISCOUNT CODES / Price-question JSON example updated to new structure.
- Smoke-tested knowledge base output: get_pricing_text + get_catalog_text + FAQ Delivery entries all render cleanly with plain numbers and no model codes.

**Decisions:**
- Flat 599/pair + free-shipping-at-2+ promo replaces the P599/P1,099 bundle (session 122). Simpler to explain, removes invented-total risk, preserves 2+ incentive. Logged in `decisions/log.md`.
- Chatbot never outputs internal model codes (D518/D918/D008) or peso-prefix prices. Logged in `decisions/log.md`.

**Learnings:**
- The `code` field in CATALOG stays in the Python dict but is deliberately omitted from get_catalog_text() output. Keeps internal data intact while the system prompt stays clean.
- Rule added in TWO places (SECURITY block + get_catalog_text docstring) so the omission is self-documenting — future edits won't accidentally reintroduce codes into the prompt.

**Memories saved:**
- `feedback_chatbot_no_model_codes.md`
- `feedback_chatbot_no_peso_prefix.md`
- `feedback_chatbot_address_by_name.md`

**Flagged to RA:**
- Landing page (`dubery-landing/`) still renders old P599 single / P1,099 bundle pricing + bundle math in script.js. Needs a separate patch to match the chatbot. Not done yet pending RA confirmation on scope.

---

## Session 122 -- 2026-04-15 (ugc-pipeline polish + pricing shift + chatbot recovery)

### What

**UGC pipeline + randomizer:**
- Generated 4 v3 UGC batches, 17/18 passed (bandits-tortoise 3/3, bandits-blue 3/3, bandits-green 3/3, rasta-red 5/6, rasta-brown 5/6; one skateboard flatlay failed "looks forced")
- Cleaned `contents/assets/product-specs.json`: stripped "Temple branding badge spells DUBERY exactly..." clause from all 9 products; updated bandits-blue + bandits-green specs
- Stripped DUBERY spelling clause from `/dubery-fidelity-prompt` + `/dubery-v3-validator` prefixes (single-variant)
- Randomizer: no-repeat category + product dedup, multi-product random mode, +12 activity locations (#35-46), -6 gritty locations (#7 jeepney, #15/#16 jungle, #26 rice paddy, #29 market, #33 sari-sari)
- Randomizer: rewrote `POSES_HOLDING` + `CAMERAS["UGC_PERSON_HOLDING"]` for product-forward framing
- Skills: created `/ugc-pipeline` as primary (replaces archived `/dubery-v3-pipeline`)
- `.gitignore`: added `.claude/scheduled_tasks.lock` + `.wrangler/`

**Pricing shift (LIVE):**
- Locked P599 single / P1,099 bundle (was P699 / P1,200), free shipping on bundle, single-pair shipping min P100 varying by address, DUBERY50 retired
- Decision logged in [decisions/log.md](decisions/log.md)
- Landing page: [dubery-landing/index.html](dubery-landing/index.html) (meta + pricing card), [dubery-landing/script.js](dubery-landing/script.js) (calcPrice bundle math for 3+), [dubery-landing/products/index.html](dubery-landing/products/index.html) (11 product cards + detail + price-tag + meta)
- `tools/chatbot/` KB: KNOWLEDGE_BASE.md + knowledge_base.py + conversation_engine.py + voice_server.py + conversation_store.py docstring
- Fixed RA-flagged `tools/chatbot/` FAQs: Payment (GCash/bank/InstaPay/COD Metro, was "COD only"), What's included (box+cloth+pouch, hard case +P100 add-on, was "zippered hard case standard"), How to order (full 6-step flow w/ landmarks + delivery prefs), Sizing (146mm, was 14cm)

**Chatbot recovery + auto-start:**
- Discovered **live chatbot path is `cloud-run/` not `tools/chatbot/`** -- first round of edits missed production
- Updated live `cloud-run/knowledge_base.py` (PRICING, DISCOUNT_CODES={}, delivery FAQs metro+provincial, get_pricing_text, empty-dict guards)
- Updated live `cloud-run/conversation_engine.py` (security rule, first-message pricing examples, DUBERY50 → retired section + bundle-upsell section, JSON example reply_text)
- Restarted chatbot: Flask on :8080 + cloudflared tunnel → chatbot.duberymnl.com
- Smoke tested: "hm?" returns new pricing reply, "DUBERY50 code?" returns retirement + bundle pitch
- Auto-start wired via PowerShell Register-ScheduledTask (no admin): `DuberyMNL-Chatbot` + `DuberyMNL-Tunnel` at-logon, hidden, auto-restart
- Added: [cloud-run/start-chatbot.bat](cloud-run/start-chatbot.bat), [cloud-run/start-tunnel.bat](cloud-run/start-tunnel.bat), [cloud-run/install-autostart.ps1](cloud-run/install-autostart.ps1), [cloud-run/verify-autostart.ps1](cloud-run/verify-autostart.ps1)

### Decisions
- Pricing shift reasoning (sticker drops but delivered single stays flat; bundle is the real 21%/pair lever) -- logged in decisions/log.md
- Bundle math for 3+ pairs = `floor(pairs/2)*1099 + (pairs%2)*599` (simplest honest extension)
- Auto-start via user-scope Task Scheduler at-logon (no admin), not `cloudflared service install` (needs admin + fails from Git Bash)
- DISCOUNT_CODES kept as empty `{}` not deleted (preserves import surface + JSON schema compatibility)
- Kept "brown-red mottled" / "red-black streaks" color words in bandits-tortoise spec despite V6 flag (pre-approved, multi-color pattern)
- Dropped tropical-pattern line from non-canonical bandits-blue hero angles (one-off for batch 2+3 only)
- Multi-product random mode is the default for count-only invocations (e.g. `ugc-pipeline 10`)

### Deployed
- Chatbot LIVE at chatbot.duberymnl.com with new pricing (via Cloudflare tunnel → local Flask :8080)
- Auto-start Task Scheduler tasks registered (survive reboots when RAS logs in)
- Nothing pushed to GitHub this session -- deferred, ship via `/sendit`

### Blockers
- Auto-start reliability: processes died silently between 09:45-10:02 UTC+8, Task Scheduler auto-restart didn't fire. Worth investigating what killed them before trusting the setup.
- Ad copy rewrite needed before unpause: lead with "2 for P1,099 + free shipping", not "P599 each"
- Session topic drift -- started as ugc-pipeline polish, became pricing + chatbot recovery. Too late to rename this session.
- `tools/chatbot/test_web.py` still has DUBERY50 preset + stale pricing (test harness, low priority)
- 1-week production data clock doesn't start until RA unpauses boosted ads ("clock starts when i post ads")

### Learnings
- Chatbot live path is `cloud-run/` not `tools/chatbot/` -- they have near-identical file trees, but only cloud-run/ is served. tools/chatbot/ is stale/historical.
- `project_chatbot_recovery_complete.md` memory claimed auto-start was wired in session 117, but Task Scheduler entries were missing today (root cause unknown). Re-registered.
- `cloudflared service install` needs admin + `schtasks /Create` denies access from Git Bash. PowerShell `Register-ScheduledTask` with `-RunLevel Limited -LogonType Interactive` is the no-admin path.
- Git Bash mangles PowerShell `$_` pipeline variable inline -- use `.ps1` script files, not `powershell -Command "..."`.
- Python `open()` default encoding on Windows is cp1252, chokes on UTF-8 source files -- always pass `encoding='utf-8'`.
- Delivered single-pair price stays flat at P699 (599 + 100 shipping) -- pricing shift is a bundle push disguised as a price drop, not a single-pair discount. Messaging must reflect that.
- Landing page modal already had bundle-free-shipping logic wired; only needed price number updates.
- Kraft-paper location + neutral-palette scenes bleed DUBERY box tan. Explicit "dark DUBERY box with red branding" in subject_placement locks it.
- Non-hero prodref angles (06-front) render frame more accurately than 3/4 angles (01-hero). Frame-shape fidelity stronger front-on.
- Small text + logos re-rendered (not pixel-copied) each generation -- DUBERY wordmark preservation is Gemini's interpretive rerender.

---

## Session 121 -- 2026-04-14 (randomizer-v2 + fidelity-prompt + batch-validation)

### What
- **Randomizer v2:** Rewrote `tools/image_gen/v3_randomizer.py` with numbered ID banks, per-kraft sidecar loading, daytime-only locations (34 person + 28 product), 15 lighting presets, per-category camera presets, aspect ratio pools
- **10 UGC categories total:** PRODUCT, PERSON_WEARING, PERSON_HOLDING, SELFIE, FLATLAY, UNBOXING, GIFTED, WHAT_YOU_GET, DELIVERY, OUTFIT_MATCH. Added LOCATIONS_INDOOR/GIFTED/DELIVERY banks + POSES_OUTFIT bank
- **Hero prodref branching:** UNBOXING/GIFTED/WHAT_YOU_GET/DELIVERY now use hero shot (full packaging) as prodref. All 11 hero sidecars created, `frame_direction` stripped (hero is overhead layout, not product angle). Randomizer uses `sidecar.get()` with None default.
- **Kraft prodref reorg:** `contents/new/*-kraft/` -> `contents/assets/prodref-kraft/{product}/` (11 folders moved, randomizer + SKILL.md updated)
- **Kraft prodrefs generated:** outback-red, outback-green, outback-black, all 5 bandits (01-hero + 06-front + sidecars). 07-flat for non-mirrored only (mirrored fails overhead). Rasta-brown + rasta-red still pending.
- **Multi-image color transfer:** bandits-blue 06-front used sibling's kraft as structure + supplier shot as color (first-class pattern, validator V5 allows 1-2 images)
- **Auto-versioning:** `generate_vertex.py` bumps to `-v2`, `-v3` when output exists (no overwrites)
- **Full rewrite of `/dubery-v3-validator`:** UGC-only scope, V1 filters by sidecar visible_details, V4 skips direction check for hero, V5 allows 1-2 images, V6 color-adjective ban, V7 category-prodref routing, V8 stripped schema (no lighting_logic/contact_points), accepts CRITICAL prefix variant
- **Full rewrite of `/dubery-fidelity-prompt`:** path table, stripped schema, filtered required_details, clock-direction ban, CRITICAL spelling guard, category routing, hero state templates, banks declared "Defined in randomizer" only
- **Wired Step 4 of `/dubery-v3-pipeline`:** now invokes fidelity-prompt skill instead of freelance Python (root cause of kraft-paper bleed bug on outback-black #1/#3 and #4/#5 deformations)
- **`product-specs.json` unified + cleaned:**
  - bandits-matte-black: "Gold-amber mirrored" -> "Vibrant mirrored"; removed "Inner temple arms feature a colorful..." line; 06-front sidecar shifted [0,1,4] -> [0,1,3]
  - bandits-tortoise: stripped "brown" adjectives
  - bandits-glossy-black: stripped "dark grey" adjectives
  - outback-black: "slightly translucent" -> "Polarized non-mirrored"
  - **All 5 bandits now have `Temple branding badge spells DUBERY exactly...` line** at a consistent index
- **HOLDING camera bank tightened:** dropped 35mm wide, now 85mm tight / 50mm close / 135mm macro only
- **POSES_OUTFIT cleaned:** removed both headband-style poses (perched / pushed up on head). OUTFIT_MATCH state template now "worn on face or held in hand" only
- **Live pipeline validation (batch of 40+ images):**
  - outback-black: 10/10 categories PASS after skill rewrites (PRODUCT, DELIVERY, FLATLAY, SELFIE, UNBOXING, GIFTED, OUTFIT_MATCH, WHAT_YOU_GET, PERSON_WEARING v2 with spec strip, PERSON_HOLDING v2 with 50mm close)
  - outback-red: 10+ gens PASS (all UGC categories, Manila locations incl. Venice Grand Canal, Wells Fargo McKinley, San Joaquin Pasig)
  - outback-green: 11+ gens PASS (135mm preset locked)
  - rasta-brown: 1 FLATLAY PASS (first rasta live test)
  - bandits-matte-black: 5/5 PASS (flatlay, gifted, delivery, wearing, selfie -- first pass through ALL new specs)
  - bandits-green: 3/3 generated
  - bandits-blue: 3/3 generated
  - bandits-tortoise: 3/3 generated
  - bandits-glossy-black: 3/3 generated
- **Tooling:** Built `~/.claude/scripts/tg-send.py` helper (allowlisted); built `.tmp/v3-pipeline-flow.html` visualization (5 sections: stats/flow/layout/routing/legend); built generalized `.tmp/build_batch.py` (product-agnostic prompt builder) + `randomize_one.py` (extracts JSON from randomizer)

### Decisions
- **Pipeline skill chain is single source of truth:** `/dubery-v3-pipeline` -> `v3_randomizer.py` -> `/dubery-fidelity-prompt` -> `/dubery-v3-validator` -> `generate_vertex.py`. No freelancing from the orchestrator.
- **Scene banks live ONLY in `v3_randomizer.py`.** Skill no longer duplicates banks (prevented semantically biased manual picks).
- **Hero sidecars have NO `frame_direction`.** Validator V4 skips direction check for hero; clock directions banned universally.
- **`subject_placement` must describe LOCATION scene, never prodref background** (kraft-paper-in-output bug root cause).
- **Validator is UGC-only.** Kraft prodref generation uses a lighter supplier-image review loop.
- **Multi-image color transfer is first-class** (up to 2 images; V5 allows).
- **Only 2 kraft prodrefs per product needed:** 01-hero + 06-front. 07-flat optional for non-mirrored only.
- **All 4 Outbacks share D918 identity.** Color lives in prodref photo, not spec.
- **OUTFIT_MATCH never uses headband pose** (RA rejected sunglasses-on-head as off-brand).
- **DUBERY branding line is mandatory in every product spec** (consistent across all 10 products).
- **135mm f/2.0** is PERSON_WEARING close-portrait preset; HOLDING uses 85/50/135mm close range.
- **UGC_UNBOXING regression resolved** by hero prodref (hero anchors box/pouch/cloth/card; kraft + verbose descriptions caused text-painting).
- **Numbered IDs in randomizer banks** let layout_history.json store integers for exact-match dedup.
- **Brand categories (CALLOUT, BOLD, COLLECTION, MODEL) stay in their own skills** -- different prompt shape (graphic + text overlays).

### Deployed
- Nothing deployed (pipeline iteration + content generation session). All work local.

### Blockers
- 16 bandits + rasta images pending final RA pass/fail in `contents/new/` (scores deferred by RA)
- Rasta-red kraft prodrefs + full rasta sweep still pending
- Brand categories (CALLOUT, BOLD, COLLECTION, MODEL) still untested under new flow
- Outback-blue/green/red not yet tested across all 10 categories under new flow

---

## Session 120 -- 2026-04-14 (outback-red-green-kraft + unboxing-regression)

### What
- Unified all 4 Outback product specs under `Dubery D918 Vintage Polarized Sunglasses` identity (same SKU, color carried by prodref photo). Cleaned outback-black, green, red specs to match outback-blue (3 generic required_details).
- Generated kraft prodrefs for outback-red (01-hero, 06-front) + sidecars. 01-hero took 4 iterations to get orange-red gradient + forward-facing.
- Generated kraft prodrefs for outback-green (01-hero, 06-front) + sidecars. 01-hero flipped orientation vs supplier (Gemini random mirror).
- Tested outback-red: 10+ generations across UGC categories (wearing, holding, product, selfie) incl. Manila locations (Venice Grand Canal, Wells Fargo McKinley Hill, San Joaquin Pasig). All passing.
- Tested outback-green: 11+ generations across categories. 135mm camera preset locked in.
- Strengthened `product-specs.json` branding line to "Temple branding badge spells DUBERY exactly, matching reference image character-for-character"
- Updated mandatory prefix in skill with CRITICAL spelling guard
- Updated PERSON_WEARING camera preset: 85mm → 135mm (sweet spot between too-far and too-close-macro)
- Fixed outback-blue sidecar direction (was incorrectly "left", actual image faces right)
- Renamed `06-back.jpg` to `06-front.jpg` where supplier misnamed (red + green)
- Fixed stale visible_details in outback-blue sidecars (were [0,1,2,3] but spec now only has 3 indices)
- Built `~/.claude/scripts/tg-send.py` helper + allowed `Bash(python ~/.claude/scripts/tg-send.py:*)` in settings -- no more permission prompts for TG sends
- Discovered UGC_UNBOXING regression: the stronger branding guards (CRITICAL prefix + "character-for-character") combined with verbose accessory descriptions cause Gemini to paint DUBERY text on cloth/box surfaces and lose the metal temple badge

### Decisions
- All 4 Outbacks share identity -- D918 SKU. Color info lives in the prodref photo, not the spec.
- Kraft prodref generation MAY use specific color hints (orange-red, etc); downstream UGC specs stay generic
- Only 2 kraft prodrefs per product needed: 01-hero (3/4 for person shots) + 06-front (flat lay / front)
- Sidecars must match current spec index count
- Filenames describe actual content (06-back → 06-front)
- 135mm f/2.0 close portrait is the PERSON_WEARING camera preset (not macro)
- UGC_UNBOXING skipped from the pipeline for now
- No hardcoded example strings in skills (RA preference) -- keep skills declarative, push examples to memory/test logs
- Sidecar `frame_direction` must describe actual generated image, not the supplier input (Gemini flips randomly)

### Deployed
- Nothing deployed (testing session)

### Blockers
- UGC_UNBOXING regression -- revisit with a cleaner approach (maybe kraft hero shots, maybe per-category prefix overrides)
- Outback black kraft + sidecars (last Outback variant, not yet done)
- Brand categories (CALLOUT, BOLD, COLLECTION, MODEL) still untested under new flow
- `v3_randomizer.py` still uses old camera presets + clock directions
- Bandits and Rasta series (6 more products) not yet kraft-ready
- Hero shots lack sidecars (gap, low priority since pipeline no longer uses them)

---

## Session 119 -- 2026-04-13 (v3-fidelity-kraft-prodrefs)

### What
- Generated 6 kraft-bg prodrefs for Outback Blue from supplier white-bg images (all angles)
- Built sidecar metadata system: `.json` next to each `.png` with frame_direction, visible_details, shows
- Stripped prompt schema: removed lighting_logic, objects_in_scene, clock directions, color words from required_details
- Updated fidelity prefix: "ensure that product attached keeps its identity and design do not hallucinate"
- Switched to camera-relative directions (left/right/toward camera) -- eliminates POV ambiguity
- Added pre-generation checklist (10 checks) + post-prompt validator gate (V1-V4)
- Replaced UGC_HEADBAND with SELFIE + FLATLAY + UNBOXING (UGC research-backed)
- **Validated all 6 UGC categories for Outback Blue** (~48 generations, ~$3 Vertex):
  - UGC_PRODUCT: wooden table, skateboard, motorcycle seat, marble, concrete -- all pass
  - UGC_PERSON_WEARING: 12+ tests, male/female, all directions, editorial + casual -- all pass
  - UGC_PERSON_HOLDING: 4 tests, left/right/toward camera -- all pass
  - UGC_SELFIE: park, beach boardwalk, rooftop mirror -- all pass
  - UGC_FLATLAY: white linen, rattan tray under palms -- all pass
  - UGC_UNBOXING: desk, bedsheet, cafe COD, POV floor -- all pass (hero shot as reference)
- Updated `/dubery-v3-pipeline` skill with complete validated flow + all rules + variety banks
- Saved UGC_PERSON_WEARING template to `.tmp/templates/`

### Decisions
- Color-free required_details: Gemini reads color from photo, text colors can conflict
- Angle-aware filtering: sidecar visible_details controls which required_details go into prompt
- Camera-relative directions replace clock directions everywhere (sidecars, prompts, skills)
- Stripped prompt: only blending_mode + reflection_logic + relight_instruction in interaction_physics
- No night/evening scenes: sunglasses are daytime product
- No scale-reference objects next to product in surface shots (newspapers, vinyl, phones cause oversizing)
- Specify which hand (LEFT/RIGHT) when hands are in frame -- prevents two-left-hands issue
- Validator gate mandatory: prodref → sidecar → prompt must all agree before generation
- Prompt format: .txt + _config.json (readable, editable)
- Prodref per category: 01-hero for person, 06-front for overhead, hero shot for unboxing
- Multi-image attachment test dropped -- single prodref approach works consistently
- UGC_HEADBAND dropped, replaced by SELFIE + FLATLAY + UNBOXING

### Deployed
- Nothing deployed (testing session)

### Blockers
- Brand categories (CALLOUT, BOLD, COLLECTION, MODEL) untested under new flow
- Update v3_randomizer.py with new rules (camera-relative, stripped schema, new categories)
- Expand to other 10 products (kraft prodrefs + sidecars + spec validation needed)
- Fix generate_vertex.py rename quirk (.txt → .json after generation)

---

## Session 118 -- 2026-04-13 (v3-pipeline-batch)

### What
- Ran v3 fidelity-spec pipeline 6x on Outback Blue: 5 PASS, 1 FAIL
  - PASS: UGC_PERSON_WEARING (rooftop golden hour), UGC_PRODUCT (poolside morning), UGC_PERSON_HOLDING (boardwalk sunset), UGC_PERSON_WEARING (bikini beach), BRAND_MODEL (Siargao editorial)
  - FAIL: UGC_PERSON_WEARING (basketball court blue hour) -- product fidelity lost in cool lighting
- Removed inner temple arm zebra detail from outback-blue product spec (Gemini hallucinated wood-tone arms)
- Added "Clean branding visible on the temple" to outback-blue spec (fixed missing emblem on holding shots)
- Hardcoded -1.png angle in v3 pipeline skill (stopped repetitive front-view results)
- Built `tools/image_gen/v3_randomizer.py` -- true RNG scene randomizer with variety banks: 24 locations, 14 lighting setups, gendered subject banks, 15 surfaces, camera presets per category
- Killed 3 orphan sessions (1434MB freed)

### Decisions
- Always use -1.png prodref for all products -- 3/4 view shows branding + more visual interest
- "Clean branding visible on the temple" as explicit required_detail -- Gemini doesn't reliably read it from ref alone
- Remove interior-only details from specs -- Gemini can't distinguish inside/outside temple arms
- Built dedicated v3_randomizer.py to replace biased manual scene picking

### Deployed
- Nothing deployed

### Blockers
- Basketball court blue hour shot failed -- retry or investigate cool-lighting fidelity
- Expand v3_randomizer variety banks if combos feel limited
- Test remaining categories: UGC_HEADBAND, BRAND_CALLOUT, BRAND_BOLD, BRAND_COLLECTION
- Validate other product specs beyond Outback Blue

---

## Session 117 -- 2026-04-13 (chatbot-recovery-live)

### What
- SSL cert confirmed live on chatbot.duberymnl.com -- blocker from session 111 cleared
- Added dotenv loading to Flask messenger_webhook.py (was missing for local runs, worked on Cloud Run via injected env vars)
- Fixed verify token fallback (empty .env value overrode default)
- Wired Meta webhook to chatbot.duberymnl.com/webhook (recovery step d)
- Auto-start on boot via Task Scheduler: DuberyMNL-Chatbot + DuberyMNL-Tunnel (step e)
- UptimeRobot confirmed already configured by RA (step f)
- Built smart message flood debounce (3s normal, 8s when image keywords like "this"/"ito"/"check" detected)
- Built customer image vision -- downloads customer-sent images, base64 encodes, sends to Gemini 2.5 Flash as inlineData
- Single image processing cap (1 at a time) with polite multi-image acknowledgment message
- Fixed security gate false positive -- bot detection triggered on augmented context text (brackets matched JSON regex)
- Fixed JSON leak in Gemini fallback parser -- regex extracts reply_text from malformed JSON instead of dumping raw
- Rewrote all 10 FAQ answers from spec-sheet format to conversational Filipino shop assistant tone
- Fixed CRM Sheets auth -- switched from ADC (google.auth.default) to token.json (same as pipeline tools)
- Built Cloudflare Worker fallback (dubery-chatbot-fallback) -- intercepts webhook when origin down, sends away message via Meta Send API
- Added startup attachment warmup -- background thread pre-uploads all 48 images to Meta CDN on boot (48/48, zero failures)
- Stress tested chatbot: 16/16 scenarios passed (greetings, pricing, shipping, injection, skeptic, comparison, order flow, follow-ups)
- Fallback Worker tested end-to-end: stopped Flask, sent Messenger message, received away reply

### Decisions
- Smart debounce (3s/8s) over fixed window -- keyword detection for common Filipino image-follow patterns ("this", "ito", "check")
- Security gates check original customer text, not augmented context -- prevents false positives from system-injected brackets/context
- Cloudflare Worker fallback over Facebook away message -- auto-detects origin down without manual toggle, handles webhook verification too
- Startup warmup in background thread -- server starts immediately, warmup runs parallel, URL fallback during ~60s window
- CRM uses token.json not ADC -- ADC from gcloud auth doesn't include Sheets write scope

### Deployed
- chatbot.duberymnl.com -- LIVE, receiving real Messenger messages
- dubery-chatbot-fallback Worker on Cloudflare -- LIVE on chatbot.duberymnl.com/*
- Meta webhook wired to new URL
- Task Scheduler tasks registered (DuberyMNL-Chatbot + DuberyMNL-Tunnel)

### Blockers
- (h) Unpause boosted ads -- RA manual action in Ads Manager
- (i) 1-week clean production data capture -- starts after (h)
- Chatbot image bank refresh (stale hero shots + add worn shot per variant) -- backlogged
- Landing page asset update -- backlogged
- Pricing decision P699/P1200 vs P599/P999 -- discussed, not decided

---

## Session 116 -- 2026-04-13 (superpowers-cherry-pick)

### What
- Restored YouTube OAuth -- re-ran `tools/reauth_token.py`, all 6 scopes granted (drive, sheets, gmail, calendar, youtube). YouTube now has full API access (liked videos, subscriptions, playlists)
- Fetched 392 liked videos via YouTube Data API to verify OAuth works
- Ingested "Unlock the Next Evolution of Claude Code with One Plugin" (Nate Herk) -- Superpowers plugin analysis
- Built custom Superpowers-inspired build flow (path B: cherry-pick, not install):
  - `/brainstorm` -- visual companion, localhost dashboard with clickable option cards + server.py
  - `/plan` -- hyper-detailed plans to .tmp/plan.md (2-5 min tasks, exact file paths, acceptance criteria)
  - `/execute` -- task-by-task execution with safety stops, subagent dispatch, post-task review
  - `/debug` -- 4-phase systematic debugging (investigate > analyze > hypothesize > fix)
  - Verification gate wired into `/closeout` (step 4b) and `/pipeline` (step 7)
  - Orchestrator rule `~/.claude/rules/build-flow.md` -- chains full flow on non-trivial builds
- Updated YouTube skill SKILL.md with OAuth operations documentation
- Updated YouTube skill memory with OAuth scope-loss warning

### Decisions
- Cherry-pick Superpowers patterns (custom build) instead of installing plugin wholesale -- avoids 14 extra skill descriptions loading into context on top of RA's 34 existing skills

### Deployed
- Nothing deployed

### Blockers
- YouTube token scope will get overwritten when other tools re-auth with narrower scopes -- no permanent fix yet
- New skills untested in real production use -- first test will be chatbot recovery or portfolio build

---

## Session 115 -- 2026-04-13 (context-optimization)

### What
- Applied Brad's power-ups: `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=75` + `BASH_MAX_OUTPUT_LENGTH=150000` in settings.json env
- Removed `@decisions/log.md` from global CLAUDE.md (45KB/message savings)
- Moved me.md, work.md, facts.md from @-includes to on-demand pointers (~10KB/message)
- Archived 8 pre-April decisions to `decisions/archive/log-2026-q1.md`
- Archived 5 parked v1 skills to `.claude/skills-archive-v1/`
- Cleaned settings.local.json: 153 → 45 allow patterns (~14.7KB savings)
- Trimmed MEMORY.md: 120 → ~95 entries, organized by section (~6KB savings)
- Trimmed current-priorities.md: 11.2KB → 3.0KB (cut completed section)
- Added deny rules for node_modules, .git/objects, dist, lock files, archives
- Disconnected 4 unused MCPs (Gmail, Calendar, Drive auth, Telegram)
- Archived PROJECT_LOG sessions 73-97 (94KB → 53KB)
- Audited backlog: removed 1 done item, reworded 3 stale items
- Result: ~91% reduction in per-message preloaded context (~29K → ~2.5K tokens)

### Decisions
- Progressive disclosure for CLAUDE.md: only current-priorities + goals always loaded; everything else on-demand
- Parked v1 skills archived (not deleted) to .claude/skills-archive-v1/
- PROJECT_LOG archived at session 97 boundary

### Deployed
- Nothing deployed

### Blockers
- Env var changes take effect next session
- MCP disconnect is per-session habit (not persistent)
- Further global skill audit possible (skill-builder 29KB, video-to-website 28KB)

---

## Session 114 -- 2026-04-13 (content-engine-v3-fidelity) [IN PROGRESS]

### Savepoint 03:00 UTC+8
- Built fidelity scorecard + batch randomizer (v2), batches 001 (9/11) and 002 (~6/9)
- Built cross-session headline dedup + layout history tracking
- Headline dedup and layout history confirmed working (zero reuse in batch 002)

### Savepoint 07:30 UTC+8

**Done:**
- Discovered v2 narrative prompts fail product fidelity -- RA introduced D918 fidelity-spec JSON approach (product as locked asset, scene as variable)
- A/B tested narrative vs fidelity-spec on Outback Blue (hardest product) -- narrative failed, fidelity-spec passed consistently
- Built 3 new skills: `/dubery-fidelity-prompt` (prompt generator), `/dubery-v3-pipeline` (orchestrator), `/dubery-v3-validator` (6-check validator)
- Built `product-specs.json` (11 products) + `prodref-metadata.json` (all angles with clock directions, compatible_directions, strengths)
- Added `outback-blue-0.png` multi-view reference (covers most angles in one image)
- Updated `schema_parser.py` for formatted JSON (indent=2)
- Tested Outback Blue across ~15 scenes (gym, cafe, boat, dashboard, desk, park, barbershop, Cebu coast, Pampanga, Seoul, Subic pier, jeepney, Doha, Riyadh, Palawan, Hong Kong) -- consistent passes with D918 spec
- Removed KNOCKOUT from bold layouts, updated V5 validator to not penalize -1 angle

**Decisions:**
- v3 fidelity-spec replaces v2 narrative prompts for ALL image gen
- Product is "locked asset" with structural details, scene is "variable"
- Don't describe emblem -- let Gemini read from reference photo (unless spec file includes it)
- "oversized" in proportions inflates product -- use "standard"
- reflection_logic simplified to fixed string, contact_points removed
- Prodref angle drives prompt direction -- text and image must agree
- Front-facing refs (-2, -3) don't work for person-wearing -- arm detail missing
- outback-blue-0.png (multi-view) works as single ref for all categories
- Mandatory prompt prefix: "Generate an image based on the following JSON parameters and the attached reference image:"

**Learnings:**
- Gemini follows text descriptions too literally -- describing the emblem wrong produces wrong emblems, not describing it lets Gemini read from the photo correctly
- Same headline = same-looking image (not just text repetition, functional duplication)
- Camera lens choice matters: 85mm for brand premium, 50mm for candid, 24mm for selfie
- Formatted JSON (indent=2) works better than one-liner -- Gemini can parse the hierarchy

**In flight:**
- v3 pipeline validated on Outback Blue only -- 10 other products need D918-quality specs
- Brand categories (callout, bold, collection) untested with v3

**Memories saved:**
- [v3 Fidelity Approach](project_v3_fidelity_approach.md) -- product-as-locked-asset JSON schema, validated on Outback Blue
- [Prodref Drives Direction](feedback_prodref_drives_direction.md) -- ref angle determines prompt direction, never conflict
- [Oversized Inflates Product](feedback_oversized_inflates.md) -- don't use "oversized" in proportions
- [Sequential Prompt Planning](feedback_sequential_prompt_planning.md) -- already saved earlier

---

## Session 113 -- 2026-04-12 (content-engine-v2-polish)

### What
- A7.1: Added R6 person-anchor framing rule to UGC skill -- banned whole-body/wide shots, added 6-option Framing Bank
- A7.2: Replaced all 8 gritty TEXTURE surfaces in brand-bold with clean premium (marble, walnut, slate, leather, bamboo, acrylic, metal, concrete-smooth)
- Bank rebalancing across all 4 v2 skills -- swapped gritty locations/surfaces/atmospheres for clean premium, added AESTHETIC DEFAULT note
- Banned `-2` (multi-angle strip) and `-multi` (composite) product ref angles across all 7 content skills
- Updated `generate_vertex.py` to default output to `contents/new/YYYY-MM-DD_{name}.png`
- Added 4 loadout auto-allow patterns to settings.json
- Generated 8 test images: 4 passed (011, 013b, 014, BOLD-002), 2 failed fidelity (012, 012b ~50%), 1 failed missing ref (013), 1 layout repetitive (BOLD-003)
- Added backlog: trend researcher agent, content batch randomizer, OFW location sub-bank
- Killed orphan Claude process PID 17656

### Decisions
- Ban `-2`/`-multi` angles for all image generation (catalog/reference use only)
- Clean premium is the default aesthetic across all content skills
- TEXTURE layout refined with clean premium surfaces (not retired)
- Python `random.choice()` from banks produces better variety than LLM-picked combos

### Deployed
- Nothing deployed

### Blockers
- Product fidelity scorecard needed (Bandits Green ~50% fidelity)
- Narrow scenarios (CAFE_TABLE) produce repetitive outputs
- Cross-session prompt combo deduplication still open
- First real batch volume + cadence undecided

---

## Session 112 -- 2026-04-12 (youtube-account-integration)

### What
- Added YouTube OAuth scope to token.json (readonly -> full read/write). Created `tools/reauth_token.py` with all 6 scopes
- Fixed scope drift -- token was down to 2 scopes, restored all 6 (drive, sheets, gmail.modify, gmail.settings.basic, calendar, youtube)
- Pulled full YouTube account: 390 liked videos, 228 subscriptions, 13 playlists, channel info
- Analyzed YouTube profile -- identity layers: longboarder (core), drummer, PH punk music, Axie/Web3 past, sailing, AI learner
- Assessed 5 liked videos for ingest, ingested 3: Jack Roberts ($10k websites), Aaron Young (Claude+Google Ads), Brad (Claude Code usage limits)
- Extracted power-ups from Brad's video (autoCompact 75%, BASH_MAX_OUTPUT_LENGTH, MCP hygiene)

### Decisions
- Upgraded to full `youtube` scope (not just readonly) for playlist creation/management
- Ingest #1 (Jack Roberts), #2 (Aaron Young), #4 (Brad). Skip #3 (entertainment). #7 already ingested session 94.

### Deployed
- Nothing deployed

### Blockers
- Power-ups not yet applied: autoCompactPercentageOverride 75 + BASH_MAX_OUTPUT_LENGTH=150000
- A7 content engine tasks still queued (UGC R6 framing, brand-bold TEXTURE bank, batch volume)

---

## Session 111 -- 2026-04-12 (cloudflare-chatbot-tunnel)

### What
- Migrated duberymnl.com DNS from Namecheap to Cloudflare (free plan). Phases 1-3 complete.
- Set up Cloudflare Email Routing: ras@duberymnl.com -> sarinasmedia@gmail.com (replaced 5 Namecheap eforward MX records)
- Cut nameservers to Cloudflare (jerome.ns + ursula.ns). Propagation confirmed instantly via Google DNS.
- Created named Cloudflare Tunnel `dubery-chatbot` (UUID f2e8c4e2-7911-4fdf-bf05-af6dc9d9a6b2)
- Routed chatbot.duberymnl.com CNAME to tunnel, wrote config.yml, started Flask + tunnel successfully
- Killed orphan Claude process PID 13752
- Cloudflare account: sarinasmedia+rasclaw@gmail.com

### Decisions
- Cloudflare account uses plus-addressed gmail (sarinasmedia+rasclaw@gmail.com) for inbox filtering

### Deployed
- Nothing deployed (waiting on Cloudflare SSL cert provisioning)

### Blockers
- Cloudflare zone still "waiting for nameserver propagation" internally -- SSL cert not yet provisioned for chatbot.duberymnl.com
- Once SSL is live: verify tunnel, wire Meta webhook (Phase 6), auto-start (Phase 5), monitoring, unpause ads

---

## Session 110 -- 2026-04-12 (dashboard)

### What
- Researched Beyblade tournaments for today (Metro Manila) -- no confirmed event, pointed RA to FB groups + pabeybey.com calendar
- Found Ten-O BBX Ranked Tournament #10 at Guijo Suites Makati (6 PM reg, P400, 3G RANKED SWISS, 50 slots)
- Researched Star City vs X-Site Festival Mall for family outing -- Festival Mall won (P399 ride-all-you-can, indoor, cheaper, Toy Town Beyblade possible)
- Updated ra-dashboard: Baby Jah feed 11:30 AM, Iver's bday (Apr 11), Pyro Musical (Apr 11), Festival Mall outing (Apr 12). Deployed to Vercel.

### Decisions
- None this session

### Deployed
- ra-dashboard updated + deployed to Vercel (family timeline + baby tracker)

### Blockers
- None

---

## Session 109 -- 2026-04-12 (savesession-command)

### What
- Created `/savesession` command — standalone shortcut for `/closeout --defer`. Harness hot-reloaded.
- Added 9 auto-allow permission patterns to `settings.local.json` for closeout + sendit operations (git add/commit/push for 3 repos, backup_secrets.py, sync_folder.py both conditional forms).

### Decisions
- `/savesession` as standalone command instead of `/closeout --defer` flag | cleaner UX, no flag to remember | RA preference

### Deployed
- `/savesession` command live and hot-reloaded. First use = this session.

### Blockers
- `/sendit` still needs first real-world test

---

## Session 108 -- 2026-04-12 (session-workflow-redesign)

### What
- Diagnosed closeout slowness: session entry length NOT the bloat (25-45 lines consistent across 34 sessions). Real cost = ADR format creep + bidirectional cross-link overhead.
- Saved `feedback_closeout_format.md`: one-liner decisions default, full ADR only for architectural. Conservative back-linking (forward-only unless ≥2 related). Pushed `cb15cc8`.
- Saved `feedback_multi_session_workflow.md`: consolidated multi-window best practices.
- Explained `~/.claude` three-repo backup architecture + two-layer secret backup to RA.
- **Modified `backup_secrets.py`**: added `pin_latest_revision()` — keepForever=True on each upload. Verified 28 existing revisions per file, latest pinned. Pushed `01b3813`.
- **Designed + implemented `/closeout --defer` + `/sendit`:**
  - Modified `closeout.md`: `--defer` skips push + backup + Drive sync, commits locally only.
  - Created `sendit.md`: 6-task parallel ship (secret backup, Drive sync x2, git push x3 with pull-rebase fallback).
  - RA's key insight: secrets + Drive sync belong with push ("local vs ship" decomposition).
  - Harness hot-reloaded both commands immediately.
- **Saved `feedback_session_rename_drift.md`**: proactive mid-session rename when topic drifts. Trigger conditions + anti-nagging rules. Session 105 was the reference case (5 unrelated topic shifts, none caught).
- **Updated `feedback_loadout_remote_status.md`**: conditional rename prompt at loadout (hard ask for multi-session + unnamed, soft for single-session).
- Updated `feedback_multi_session_workflow.md` with defer+sendit pattern + mid-session rename pointer.
- **First ever `/closeout --defer` run** — this session is the inaugural use.

### Decisions
- One-liner decisions default, ADR for architectural only | entry length isn't the bloat, ADR creep is | closeout timing analysis
- Conservative back-linking: forward-only unless ≥2 related | below threshold = wasted overhead | same analysis
- Drive revision pinning via keepForever=True | 28 revisions exist, prevents 30-day auto-delete | RA backup audit
- `/closeout --defer` + `/sendit` for multi-window | decouple save from ship, eliminate push races | RA's "local vs ship" insight
- `/flush` renamed `/sendit` | RA's voice, action-oriented | RA preference
- Secrets + Drive sync defer with push | all cloud-ship ops should defer together | RA's decomposition
- Session drift detection as behavioral rule, not hook | Claude notices, no code needed | RA observed session drift pattern
- Conditional rename at loadout: hard ask for multi-session only | only nag when useful | multi-window design

### Deployed
- `backup_secrets.py` keepForever pinning: pushed `01b3813` to DuberyMNL
- `/closeout --defer` + `/sendit` commands: created + hot-reloaded, inaugural use this session
- 3 feedback memories created, 2 updated, MEMORY.md indexed

### Blockers
- Chatbot recovery still top priority (unchanged)
- `/sendit` needs first real-world test — RA runs it after this closeout
- PROJECT_LOG archive (Tier 1 audit): discussed, not decided. Backlog candidate.
- Rasclaw-as-channel-plugin struck from backlog (confirmed working session 105)

---

## Session 107 -- 2026-04-12 (content-engine-v2)

### What
- Loadout: tunnel healthy, Meta scheduled queue = 0 (content bottleneck surfaced)
- **Phase A -- v2 skill rewrites** (all 3 active content skills upgraded to variety-banks + WF2 fidelity pattern):
  - A1 reverted: attempted naturalism patch on `dubery-ad-creative`, `dubery-prompt-validator` PF-4 enforces the exact v1 coercive phrase — reverted. Wrote `project_content_skill_iterations.md` locking v1 skills (ad-creative / prompt-writer / validator / infographic-ad / ugc-fidelity-gatekeeper) as parked.
  - A2 `dubery-brand-callout`: 5 "Reference prompt" templates removed, 20 per-layout variety banks added (129 options), R2/R3/R4 fidelity ported, angle randomization rule
  - A3 `dubery-brand-collection`: same pattern (18 banks, 106 options), L2 angle consistency + render_notes "applies uniformly to all products"
  - A4 `dubery-ugc-prompt-writer`: 7 global variety banks added (Location PH-specific / Lighting / Surface / Subject Archetype / Outfit / Atmosphere / Photographic Treatment) + batch diversity check in execution order
  - A6 structural smoke test passed across all 4 skills
- **Committed Phase A as `6080ada`** -- feat: v2 rewrite for brand-callout + brand-collection, UGC variety banks (+698 / -170)
- **Phase B -- posting audit + smoke test:**
  - B1: Story Rotation GH Actions cron HEALTHY (15/15 green, fires every 4h). UGC cadence is NOT a cron — uses Meta-native scheduled posts via `schedule_batch.py --ugc`. Meta token valid. **Scheduled post queue = 0** (drained during chatbot recovery — the actual "resume posting" bottleneck)
  - **36 IMAGE_APPROVED ads pipeline SCRAPPED** per RA — focus = brand + UGC only going forward
  - B2: Built new skill `/dubery-prompt-reviewer` — v2 quality gate, V1-V7 universal + per-skill checks, PASS/PATCH/FAIL verdicts, applies only to v2 skills
  - B3: Generated 4 sample prompts — bold TEXTURE/Outback Red, callout RADIAL/Bandits Green, collection HERO_CAST/Outback trio, UGC OOTD_STREET regen
  - B4: Reviewer returned 2 PASS + 2 PATCH. Applied UGC 1-word patch (`reflecting` → `catching`). Collection angle flagged as next-batch reminder only
  - B5: Generated 4 images via Vertex AI Gemini 3.1 Flash, ~$0.28 spend
  - B6: RA reviewed:
    - **CALLOUT-001 APPROVED**: "looks perfect". RA insight: the aged-leather + window-light scene bank could cross-pollinate to UGC if labels/arrows removed
    - **COLL-001 APPROVED + v2 VALIDATED**: "prompt was already used, this version is much better, reflection and product fidelity top notch, can be used as ads or UGC" — direct RA confirmation v2 > v1 on same input
    - **UGC-005 PARTIAL**: "whole-body, sunglasses barely recognizable" — framing rule missing from skill
    - **BOLD-001 REJECTED**: "looks AI, nail thru product doesn't make sense, don't like the dirty and gritty scene" — TEXTURE surface bank aesthetically biased wrong
  - RA also flagged: 3 of 4 prompts were "already used" across sessions — variety banks don't track cross-session history

### Decisions
- **v1 content skills parked permanently** — validator chain enforces v1 coercive phrase as required, can't patch piecemeal. Any v2 ad workflow = build new from scratch when paid ads resume. Locked in `project_content_skill_iterations.md`
- **v2 skill rewrite pattern VALIDATED** — RA confirmation on collection ("much better than prior") is direct A/B evidence. Pattern is the new template for all content skills. See `project_v2_skills_validated.md`
- **36 IMAGE_APPROVED ads pipeline scrapped** — brand + UGC only going forward
- **`/dubery-prompt-reviewer` is a required quality gate** before any batch image gen spend
- **DuberyMNL aesthetic = clean premium, NOT gritty/weathered** — session 107 smoke test BOLD-001 rejection. See `feedback_ra_aesthetic_preference.md`
- **UGC framing rule required** — product must be recognizable, no whole-body wides. See `feedback_ugc_framing.md`

### Deployed
- `6080ada` DuberyMNL main: Phase A skill rewrites (committed in session, pushed in closeout)
- `/dubery-prompt-reviewer` skill (committed in closeout)
- 4 sample images → `contents/new/SAMPLE-*.png` (Drive-synced in closeout, tier 2 per content storage rule)

### Blockers
- **A7.1** next session: apply UGC R6 framing rule + tight-crop photographic treatment bank
- **A7.2** next session: refine brand-bold TEXTURE surface bank (swap gritty for clean premium) OR retire TEXTURE layout entirely — RA to decide
- **A7.3** next session: regenerate BOLD-001 sample after A7.1/A7.2 fixes
- Backlog: cross-session prompt combo deduplication (variety banks don't track history)
- Backlog: cross-pollinate brand-callout scene bank into UGC as "product-hero" variant
- Decision pending: first real brand + UGC batch volume + cadence after A7 fixes

---

## Session 106 -- 2026-04-12 (chatbot-image-bank-v2)

### What
- Loadout: dubery-dev tunnel healthy, plugged in, killed 1 orphan + 1 rasclaw plugin per RA, kept this session only.
- **Recovery path (a) -- image bank restored 21 -> 48 with per-image captions.** Pulled session 98 manifest (d942c44), refactored schema so each image is `{url, caption}` dict, restored all 8 categories (11 hero + 6 model + 6 lifestyle + 4 collection + 5 brand + 8 customer-feedback + 6 proof + 2 support). Added `get_image_caption()` helper. Smoke test: 48 loaded, full knowledge 10819 chars.
- **Updated conversation_engine.py IMAGE RULES.** Removed "collection-/comparison- don't exist" ban (restored collection category). Replaced "never describe the scene" rule with "trust the caption, don't invent beyond" -- old rule was right when Gemini was blind, wrong now that captions exist. Added category-by-category picking guidance.
- **Visual verification of all 11 hero shots via local Read().** Discovered every hero shot is a **flat-lay on kraft background showing the full unboxing set** (Dubery box, drawstring pouch with microfiber cloth, warranty card) -- NOT a "clean product shot." Rewrote all 11 captions to lead with the flat-lay context.
- **CATALOG variant_notes errors fixed** (inherited from session 98 "visually verified" text that wasn't actually verified): Outback Red `gold/amber` -> `red/orange`, Outback Green `green-blue` -> `green/purple iridescent`, Bandits Green `black with green accents` -> `green + black bicolor`, Bandits Tortoise `dark tortoiseshell` -> `brown + dark brown tortoiseshell`.
- **Anchoring bias caught:** My first pass comparing Rasta and Outback hero shots concluded they were the same shape. RA pushed back. Second look: Rasta has curved top edge, visibly wider frame, taller lens -- the CATALOG "oversized aviator-style square" description is correct. Logged as feedback memory update.
- **Hero shots also double as inclusions shots.** Encoded into hero category hint: "don't also send support-inclusions after a hero" -- prevents redundant double-sends since every hero already shows the inclusions.
- **Recovery path (b-c) -- Cloudflare migration prep complete.** Discovered cloudflared 2026.3.0 already installed. Pulled full DNS state (A->Vercel, CNAME www->Vercel, 5 MX->Namecheap eforward email forwarding IS actively routing, SPF TXT, no DMARC/DKIM). Wrote comprehensive 6-phase runbook at `references/cloudflare-migration-runbook.md` with rollback plans + 3 open questions.
- **Recovery path (g) -- CRM test data cleanup done.** Wrote `tools/chatbot/cleanup_crm_test_data.py` (token.json OAuth2, --dry-run default, --confirm to delete). First attempt used ADC -> 403 insufficient scopes -> switched to token.json. Deleted 61 TEST_ rows: 8 leads, 7 log entries, 46 conversation messages. **Preserved 146 production rows** (25 real leads, 27 log entries, 94 conversation messages from session 97-98 live run) -- case-study material for RAS Creative SOLUTIONS.
- Did NOT execute Option 1 smoke test (Quick Tunnel + local Flask chat-test scenarios) -- RA chose closeout over it.

### Decisions
- **Image bank schema refactor: each image -> `{url, caption}` dict.** Gemini needs per-image captions to pick the right image for conversational context (proof for skeptical, feedback for social proof, collection for series asks). Bare URL strings worked at 21 in one category; 48 across 8 categories demands captions.
- **Restore 48-image bank (reverses session 101's 21-image shrink).** Session 101 called the shrink an "over-correction, expansion parked" -- this session unparks it.
- **Replace "never describe scenes" IMAGE RULE with "trust caption, don't invent beyond".** Old rule was right when Gemini was blind to photos, wrong now that captions describe scenes.
- **CATALOG variant_notes corrections for 4 variants.** Visual inspection revealed session 98 "visually verified" claim was partially wrong. Generalizable lesson: even memories that claim verification may need re-verification.
- **Hero shots double as inclusions shots -- encode into category hint.** Every card shot is a flat-lay with box/pouch/cloth/warranty card. Sending support-inclusions AFTER a hero is redundant.
- **Cloudflare migration: Path B (prep now, execute next session).** Lower risk of half-finished state if interrupted. Runbook at `references/cloudflare-migration-runbook.md`.
- **Cloudflare Email Routing over MX-mirroring.** Namecheap email forwarding is documented as tied to Namecheap NS. Email Routing survives the cutover cleanly.
- **CRM cleanup tool pattern: token.json OAuth2, --dry-run default, --confirm to delete.** ADC is missing the spreadsheets scope on this machine. Using token.json avoids touching global ADC state (which would affect Vertex AI + Veo tools).

### Deployed
- Nothing deployed. Chatbot still DOWN. All work was code/config/data changes for the recovery path.

### Blockers
- **Cloudflare migration execution** -- needs dedicated 45-60 min session. Gated on 3 open questions in runbook: (1) Cloudflare account fresh or existing? (2) Namecheap 2FA status? (3) ras@duberymnl.com verification dependencies?
- **Quick Tunnel smoke test of new image bank** -- deferred. Still valuable: proves Gemini picks sensible image_keys with new captions before committing to permanent URL migration. ~15-25 min, can attach to the migration session.
- **Recovery path remainder after migration:** (d) wire Meta webhook, (e) auto-start Flask + cloudflared, (f) uptimerobot, (h) unpause boosted ads, (i) 1 week clean production data capture.

---

## Session 105 -- 2026-04-12 (niche-strategy-lock)

### What
- Loadout: dubery-dev tunnel healthy, power plugged, 3 active local Claude sessions (no orphans).
- Cleaned up uncommitted pre-session-98 state across both repos.
  - DuberyMNL `04e458e`: settings.local.json carry-over — 54 permission entries accumulated across sessions 97-104 (WebFetch for supplier/Meta docs, gcloud, curl, mkdir for supplier-image scraping).
  - ~/.claude `60797a6`: 3655 files. Upstream plugin sync included **telegram 0.0.4 → 0.0.5 upgrade** with orphan-kill poller (fixes the 409 Conflict bug when a prior `bun run` grandchild survives as an orphan), SIGHUP handling, reparent watchdog, PID file lifecycle. Session-report plugin got per-session timeline + by-day view. Slack plugin removed. Session-report LICENSE added. Runtime state: 17 new telegram inbox captures + bot.pid + telegram 0.0.5 plugin cache (25MB incl. node_modules, matching existing 0.0.4 pattern).
  - Both pushed to their origins.
- **Rasclaw-as-channel-plugin backlog item confirmed WORKING** — the telegram 0.0.5 upgrade IS this. Two-way chat + permission relay is operational. Backlog item struck.
- Strategic discussion of RAS Creative SOLUTIONS launch prep:
  - Challenged the "after chatbot recovery, execute..." sequencing from current-priorities — only step (e) case study page is strictly blocked on chatbot data; (a) repricing, (c) portfolio hero, (d) cold outreach drafts have zero dependency on chatbot recovery.
  - Surfaced 6 strategic questions: parallel vs sequential with chatbot recovery, send-before-proof yes/no, first sub-niche, PH-first or international-first, portfolio hero proof without DuberyMNL screenshots, sender identity for v1 outreach.
  - RA's dental/spa "sellout" intuition: correct at pitch layer globally.
- Ranked 10+ niche candidates (original 4 + 7 sleeper picks: solar, tour operators, review centers, wedding photographers, interior designers, immigration, car detailing) against ticket × competition × chatbot fit × moat fit × PH market size.
- **Surfaced email-first businesses as a valid frame** (RA introduced this explicitly) — unlocks solar commercial, immigration, architects, IT managed services that Messenger-first had been filtering out.
- Reframed RA's "research → source → personalize → send" workflow as both the deliverable AND the sales engine (workflow = product flywheel). Build once, fork per niche.
- Locked the full 6-niche prioritized list. Dropped dental/spa + review centers + generic home services.
- Wrote `project_ras_creative_niches.md` memory with full strategic lock, workflow flywheel diagram, passive reading track, "how to apply" + "do not drift" enforcement sections.
- Cross-linked bidirectionally: `project_positioning_locked.md` `related:` extended + Niche section points to narrowed list; `MEMORY.md` indexed new entry directly below positioning lock line.

### Decisions
- **Solar panel installers = RAS Creative SOLUTIONS primary niche.** RA's passion + desire to learn solar + battery tech = compounding moat nobody else can build (Filipino AI agencies have zero domain knowledge). Highest ticket per deal (P200K-P2M, one install = 12-24 months retainer paid). Near-zero AI agency competition in PH. Growing market (Meralco rates climbing, grid reliability degrading, battery storage boom). Fallout leads moat maps 1:1 to tire-kicker filtering at high volume.
- **Battery storage paired with solar, not a separate niche.** Same customer (most PH solar installers sell both), same sales flow (quote-driven, email-first, technical, long consideration), same knowledge base, zero forking cost. Frame as "PH clean energy installers" = one market, two pitch angles.
- **Strict gate: DuberyMNL must be COMPLETE before any RAS Creative SOLUTIONS build begins.** "Complete" = all 9 recovery steps including step 9 (1 week clean production data capture). Not a soft preference. Steps 1-8 are 2-3 active sessions; step 9 is a full week of waiting, which is the window where the passive reading track runs.
- **Final 6-niche prioritized list:** solar (primary) → battery (paired) → tour operators → wedding photographers → real estate → immigration → car detailing.
- **Dropped from consideration:** dental/spa (pitch saturation globally), review centers (RA "out of my league"), generic home services (retainer math too tight for solo operators).
- **Solar scope: residential + commercial, PH + international, email-first primary.** Automation handles both drafting angles. If international cold email doesn't land, fallback to Upwork / LinkedIn / industry forums.
- **Email-first businesses are valid targets.** Frame broadened beyond Messenger-first.
- **Workflow = product.** "Research → source → personalize → send" is BOTH the deliverable RAS Creative SOLUTIONS sells AND the sales engine for landing the first clients. Build ONE template, fork per niche. Flywheel: outreach engine lands solar client → same engine becomes their lead qualification system → their live data becomes the case study → stronger outreach → more solar → fork template to niche #2.
- **Sequential niche fork > parallel niche build.** Pick ONE niche (solar), ship it, land a client or learn why not, then fork template. Parallel dilutes personalization.
- **Passive reading track during DuberyMNL recovery window:** ~30 min/day idle reading on PH installers (Solaric, Buskowitz, Freedom Solar, Ram Mendoza), solar/battery FB groups, slow-reply complaint screenshots (pitch ammunition), technical articles (string inverters, net metering, LFP vs NMC, grid-tied vs hybrid), installer brand research (Solis, Sungrow, Deye, Huawei, BYD, Pylontech, Dyness). Zero-cost prep that compounds — by DuberyMNL step 9, RA will know more than 90% of "AI agency" pitchers.

### Deployed
- Cleanup commits only, no production code changes:
  - DuberyMNL `04e458e` (settings.local.json) → pushed origin/main
  - ~/.claude `60797a6` (plugin sync + TG state) → pushed origin/master
- Session 105 closeout commits to follow.

### Blockers
- **Chatbot recovery remains top priority (unchanged).** No work on RAS Creative SOLUTIONS build until complete.
- **Image bank expansion is the next actionable step** (step 1 of recovery path) but requires coordination — 2 other active Claude sessions were editing `cloud-run/knowledge_base.py` during this session. Can't start this in the current window without collision risk.
- **Named Cloudflare tunnel migration (recovery steps 2-4) still deferred** — RA hasn't carved out the dedicated ~15-20 min window yet.
- **RAS Creative SOLUTIONS strategy locked but gated.** Niche decisions are durable; no build work authorized until step 9 of chatbot recovery completes.

---

## Session 104 -- 2026-04-11 (positioning-lock)

### What
- Ran in parallel with session 103 (sonnet-delegation-policy) in the other VSCode window. No file collisions — different topic.
- Analyzed GCP billing CSV (Apr 6-11): $31.61 total, Vertex AI dominated ($29.42, 93%). Traced Apr 7 spike to UGC pipeline + Vertex migration (session 87) and Apr 8 to Veo 3.1 video gen testing (session 90). No ongoing burn concern (Cloud Run already deleted in session 101).
- Ingested Jordan Platten YouTube "Top 3 AI Systems Clients Pay $4K+/Month For" (KqjWm2bexUc) via `/ingest` skill. Archived raw transcript, wrote full summary with 6 action items + 7 bidirectional cross-refs, updated INDEX + ingest-log.
- Deep strategic repositioning discussion: walked RA through Jordan's "closer to revenue" framework, identified that DuberyMNL is already the System 1 + System 3 bundle Jordan describes, surfaced the contradiction with current Make/Zapier/n8n portfolio positioning.
- **Unlocked the Google fallout leads moat.** RA realized mid-conversation that his years at TDCX/Google weren't generic "leads qualification" — he was on Google's worldwide fallout leads team, rescuing stalled Google Ads registrations, free trial dropouts, and high-intent signals that went cold. He was literally the human version of Jordan's AI qualification layer, at Google TOS quality standards, worldwide. This is the moat.
- Helped RA shape the services > products insight: higher margins justify higher CPAs, trust-building fits Messenger culture, services genuinely need funnels (unlike products that fall back on marketplaces), repeat customers built in.
- Drafted 17 one-liner variants (A-Q) across authority/outcome/pain/contrast framings. RA iterated on prose structure (pain-first → fix → who-we-are) and finalized covering top/middle/bottom funnel leaks explicitly.
- **Locked the positioning statement** verbatim. Brand renamed: RAS AI SOLUTIONS → RAS Creative SOLUTIONS (Creative frames outcome; AI is the how). Niche locked: service businesses only. Pricing locked: retainer, not project fees.
- Rewrote `EA-brain/context/work.md` RAS service offering section with full niche, offer stack, retainer pricing, proof stack, outbound strategy, ascension path, DuberyMNL role.
- Rewrote `EA-brain/context/me.md` background with Google fallout leads moat framing.
- Created `project_positioning_locked.md` with verbatim statement + explicit "do not drift" rules listing what future sessions must push back on.
- Updated `project_portfolio_rebuild.md` with POSITIONING CONTRADICTION block referencing Jordan summary + positioning_locked.
- Added bidirectional back-links from `project_valor_internal_pitch.md`, `project_messenger_strategy.md`, `project_brand_pipeline.md` to `project_positioning_locked.md`.
- Updated MEMORY.md index with Jordan Platten summary + positioning_locked entries.

### Decisions
- **Brand rename: RAS AI SOLUTIONS → RAS Creative SOLUTIONS.** Deliberate positioning move — "Creative" frames the outcome and escapes the crowded AI vendor bucket. AI is the how, not the what.
- **Niche locked: service businesses only** (dental, med spa, aesthetics, real estate, law, home services, gyms, coaches, photographers, tutoring). Not product e-commerce.
- **Pricing model locked: retainer, not project fees.** Starter $1.5K-$3K/mo, Bundled $3K-$7K/mo, Premium $7K-$15K/mo. Old "$1K-$2.5K end-to-end" pricing killed.
- **Outbound strategy: small-scale targeted (20-50/day), not volume.** Matches RA's bandwidth + leverages Google fallout leads muscle memory (qualification > scale).
- **Public portfolio framing shifts** from "automation builder" to the locked positioning statement. Tool learning (Make/Zapier/n8n) stays as internal skill-building, but public positioning sells outcomes, not tools.
- **Valor internal pitch demoted** from co-primary to fallback. External service-business retainers are the primary play now.
- **Chatbot recovery reframed** from "DuberyMNL task" to "critical path to first paid client." Every day unwired is a day the case study page can't launch.
- **AI qualification layer is the unique IP.** RA can build scoring logic that actually works because he has years of manual qualification muscle memory from Google. Future sessions should emphasize this as the moat.

### Deployed
- Nothing deployed. Session was strategy + context work only. No code changes, no cloud-run/, no contents/, no tools/.

### Blockers
- `me.md` one-liner still says "AI systems builder by day" — RA explicitly paused next actions (chose option d, come back fresh). Not updated this session.
- First paid-client path unlocked but not actionable until DuberyMNL case study data exists (1 week of clean production runs). Chatbot recovery remains the gating milestone.
- Session 103 (sonnet-delegation-policy) ran in parallel in the other VSCode window — already committed its own closeout. Orphan PID 12952 idle 88min. No file collisions in shared files (EA-brain decisions/log.md, current-priorities.md) because the two sessions edited different sections.

---

## Session 103 -- 2026-04-11 (sonnet-delegation-policy)

### What
- Loadout killed 1 orphan `claude.exe` (PID 4292, 407MB freed). Orphan was session `9d630c24` from 2 days ago — VSCode `/clear` spawned a new process without terminating the old one.
- Walked backlog from recent sessions (98-102). Top chatbot blocker confirmed: image bank expansion (21 → ~35-40 with per-image captions) before re-wiring Meta webhook.
- Evaluated backlog item "convert /closeout, /savepoint, /loadout to Sonnet" → **rejected**. The thinking part (session analysis, memory drafting) can't leave Opus because only Opus has conversation context. Mechanical parts (Write/Edit/Bash) are cheap regardless of model, so delegating buys nothing. Backlog item crossed off.
- Built a Sonnet delegation policy for daily coding: delegate when input spec is short + work is long + summary-only output needed + no mid-task decisions. Unilateral delegate list: test runs, log scans, scraping, doc lookups, bounded audits. Never delegate: conversation-dependent work, decisions, closeout-style tasks.
- Saved `feedback_sonnet_delegation.md` with bidirectional back-links to `feedback_diagnostic_depth.md` + `feedback_claude_code_layers.md`. Indexed in MEMORY.md.
- Chatbot go-live gate-check: Flask DOWN, cloudflared DOWN, ephemeral quick-tunnel URL dead. Named Cloudflare tunnel path (`chatbot.duberymnl.com`) surfaced as prerequisite because quick tunnels get a new URL on every restart → Meta webhook would break on every reboot. Named tunnel requires moving whole `duberymnl.com` zone from Namecheap → Cloudflare nameservers.
- Chatbot go-live **deferred** — RA can't do the nameserver migration tonight.

### Decisions
- Don't convert `/closeout`, `/savepoint`, `/loadout` to Sonnet. The thinking part needs Opus context; mechanical part is cheap either way. (Cross-project decision logged in EA-brain.)
- Sonnet delegation policy: unilateral delegate for bounded grunt work (tests, log scans, scraping, doc lookups, audits). Ask first for bulk edits + live service work. Never delegate conversation-dependent work. Saved as feedback memory.
- Chatbot go-live path = **named Cloudflare tunnel at `chatbot.duberymnl.com`** (Option B), not ephemeral quick tunnel. Quick tunnel URLs rotate on every cloudflared restart → Meta webhook would need re-wiring on every reboot. Named tunnel requires full zone migration from Namecheap → Cloudflare.
- Named tunnel work deferred to a dedicated session (not tonight). Adds ~15-20 min best case to chatbot recovery path.

### Deployed
- Nothing deployed. Chatbot still DOWN.

### Blockers
- **Chatbot still DOWN.** Flask + cloudflared not running. Meta webhook pointing at deleted Cloud Run URL. Boosted ads paused.
- **Top chatbot recovery path (in order):** (1) image bank expansion 21 → ~35-40 with per-image captions, (2) named Cloudflare tunnel migration (`duberymnl.com` nameservers → Cloudflare), (3) wire webhook to `chatbot.duberymnl.com`, (4) unpause ads
- **Named tunnel prerequisites before starting:** confirm `ras@duberymnl.com` email routing (break if Namecheap forwarding is active), inventory any other subdomains/MX records on duberymnl.com, verify Vercel CNAME stays intact through migration
- `.claude/settings.local.json` still unstaged (shared between active sessions, leave alone)
- Other IDE session has in-flight work on MEMORY.md + `project_portfolio_rebuild.md` + cloud-run/ files — not touched per multi-session safety rule

---

## Session 102 -- 2026-04-11 (refactor-recovery-drive-workflow)

### What
- Loadout caught 2 orphan claude.exe sessions (PIDs 7776, 10572 -- 756MB freed)
- Enhanced `pc-status.ps1` with orphan detection (`--SessionsOnly` mode). Cross-references claude.exe PIDs with JSONL mtimes; idle >30min = ORPHAN. Updated loadout memory so it runs `remote-status.sh` + `pc-status.ps1 --SessionsOnly` every session going forward.
- Audited + verified the crashed pre-session-98 Karpathy/Nate Herk work sitting uncommitted: 53 deleted files (51 in archives/, 2 landing assets intentionally deleted), 13 skill rewrites, 12 tool scripts rewired to new paths, brand-bold with full WF2 fidelity port (R2/R3/R4), brand-callout + brand-collection with path updates only (fidelity port parked).
- **Committed `fc3bddf`**: 144 files, 524+/284-, the full refactor recovery. Git auto-detected the `packaging.png` rename (delete + add staged together).
- Built `tools/drive/sync_folder.py` -- local → Drive mirror, direct REST (not googleapiclient), idempotent, dry-run, unbuffered progress.
- Initially misattributed Google API timeouts to httplib2. Other IDE session's parallel diagnosis corrected it: **IPv6 is the root cause**. Python's `socket.getaddrinfo` returns IPv6 first for some Google endpoints, RA's home ISP doesn't route IPv6, TCP waits ~60s for timeout before falling back. Added IPv4-only `getaddrinfo` monkey-patch at top of `sync_folder.py`. 30× speedup.
- **Drive backup populated** via sync_folder.py: 155 files, ~98MB at `My Drive/DuberyMNL/backup/`. Contents: `references/supplier-images/` (69 files, 11MB), `contents/new/` (43, 32MB), `contents/ready/` (43, 55MB).
- Accidentally synced `contents/failed/` (58MB rejected trash). RA caught it. Built `tools/drive/delete_folder.py` to clean up. Removed 98 files + 1 folder from Drive cleanly.
- Updated `.gitignore`: dropped stale `output/images/`, added `contents/{new,ready,failed}/`, `contents/assets/hero/`, `archives/`, `references/supplier-images/`.
- Updated `README.md` with fresh directory structure + Setup/bootstrap section.
- **Edited `~/.claude/commands/closeout.md`**: Step 5 now runs Drive content sync for `contents/new/` + `contents/ready/` in the parallel background batch. This closeout is the first run.

### Decisions
- Content storage is **3 tiers**, not 2: git for code + runtime-deps, Drive for valuable content (new/, ready/, supplier-refs), local-only for trash (`contents/failed/`) + redundant (`archives/` -- git history has the originals)
- IPv4 monkey-patch is canonical for all future Python tools hitting Google APIs on RA's Windows machine. Include at top of module before HTTP imports
- `/savepoint` stays memory-only (fast checkpoint), `/closeout` handles full git + Drive + secrets batch
- Archives/ stays local-only -- optional `rm -rf archives/` after push to reclaim 87MB disk
- "Session 99" naming in memory files kept as conversational shorthand (actual session number is 102). No retroactive rename.

### Deployed
- `fc3bddf` pushed to GitHub (via this closeout)
- `log: session 102 ...` follow-up commit pushed
- Drive backup populated at `My Drive/DuberyMNL/backup/{contents/new, contents/ready, references/supplier-images}`

### Blockers
- `brand-callout` + `brand-collection` WF2 fidelity port parked (needs QA testing bandwidth)
- `cloud-run/*` has 4 modified + 2 deleted files belonging to RA's other IDE session -- left untouched per multi-session safety rule
- `.claude/settings.local.json` unstaged (shared between active sessions)
- Drive at 8.5GB / 15GB (56%) -- watch growth
- `.git/` at 325MB on DuberyMNL -- worth auditing for old large blobs in a future session
- Subagent conversion for /closeout, /savepoint, /loadout to Sonnet (save cost) -- next session

---

## Session 101 -- 2026-04-11 (chatbot-refactor-local-hosting)

### What
- Diagnosed 4 live production bugs in session 98 chatbot code via customer screenshots: Tagalog "Pasensya" fallback silencing conversations, 15+ message flood on single customer question (Jonathan case), triple-fire "Sorry, I can only help..." injection defense on legit questions (Teddy case), "Hm" failing JSON parse and triggering fallback
- Root-caused each bug via 2 parallel Explore agents diffing session 97 → 98 commits; found `_fallback_response()` returns Tagalog + `should_handoff=True`, `reply_parts` array has no cap, `security.py` has 33 over-aggressive injection keywords, `warm_attachment_cache()` tries all 48 images at startup causing OOM
- **Rewrote `cloud-run/conversation_engine.py`**: English-only fallback with no auto-handoff, removed `reply_parts` schema (single message per turn), stricter image rules ("you cannot see the image, describe the product"), new FIRST MESSAGE BEHAVIOR section (greet warmly + use name + thank + answer), list formatting rules (newlines + numbered/bulleted, no inline `(1)(2)`), Filipino shorthand recognition ("Hm" = "how much"), customer_name kwarg injected into dynamic system prompt per call
- **Rewrote `cloud-run/messenger_webhook.py`**: removed `reply_parts` loop, removed `_human_delay` typing delay, removed `warm_attachment_cache()` startup call, deleted `/comment-webhook` routes, added `/chat-test` GET (Messenger-style web UI) + POST (process-without-Meta) + `/chat-test/reset`, added `get_customer_first_name()` Meta profile lookup, added customer name input field with localStorage persistence in /chat-test UI, added image_key to meta display line
- **Shrank `cloud-run/knowledge_base.py` image bank**: 48 → 21 images (11 hero + 8 lifestyle + 2 support). **This was over-correction** — real customer needs (feedback/proof/on-face shots) were lost. Expansion with per-image captions is parked for next session.
- **Relaxed `cloud-run/security.py`**: INJECTION_KEYWORDS 33 → 17 high-confidence only. LEAK_PATTERNS trimmed to structural JSON field names only (removed prose patterns that false-fired on legit "PROVINCIAL ORDERS:" replies)
- **Deleted `cloud-run/comment_responder.py` + `cloud-run/comment_templates.py`** — daemon-thread pattern was known broken on Cloud Run (session 97) and caused Jonathan flooding when triggered
- **Critical fix: IPv6 latency bug.** Python HTTP calls to `aiplatform.googleapis.com` were ~60s each (curl = 1.4s) because `socket.getaddrinfo` returned IPv6 first, home ISP couldn't route IPv6, TCP waited ~60s before IPv4 fallback. Fixed with an `socket.getaddrinfo` monkey-patch at top of `conversation_engine.py` (IPv4 filter). **60× speedup** — 5.00s avg regression test latency after fix vs. 61s before.
- Ran 10-test regression battery in `.tmp/chatbot_regression_test.py` — 10/10 passing covering first-contact greeting (with + without name), Hm shorthand, list formatting, image_key strict matching, injection defense, out-of-scope handling, Bandits vs Outback comparison
- **Infrastructure pivot:** Deleted Cloud Run `duberymnl-chatbot` service entirely (stopped ~$50/mo credit burn, clean slate). Installed `cloudflared.exe` directly from GitHub releases to `~/bin/cloudflared.exe` (winget install was stuck). Started Cloudflare Quick Tunnel → `https://compute-believe-distributors-rocky.trycloudflare.com`. Local Flask on `localhost:8080` is now publicly reachable via the tunnel.
- **Oracle Cloud signup rejected** ("error processing transaction", common for PH individual signups). Retry option parked. Hetzner CX11 (€3.29/mo) identified as backup option if Oracle keeps rejecting.
- **Commands rework:** Created new `/savepoint` command (mid-session save point — always writes memory + bidirectional cross-links + appends to in-progress PROJECT_LOG block). Renamed `/log` → `/closeout` (avoids `/login` tab-completion collision). Added bidirectional cross-linking rule + IN PROGRESS block consolidation logic to `/closeout`.
- Created plan file at `~/.claude/plans/melodic-whistling-book.md` (comprehensive chatbot recovery plan)
- **Meta boosted ads: PAUSED** on RA's side during the chatbot outage window

### Decisions
- **Delete Cloud Run service entirely** instead of scale-to-zero (max-instances=0 not allowed by Cloud Run). Reversible via `bash cloud-run/deploy.sh`. Cleanest complete shutdown.
- **Pivot to local hosting via Cloudflare Tunnel**. Free forever, fastest path after Oracle rejection. Home PC already runs 24/7 for Rasclaw + VSCode tunnel, so the uptime baseline is acceptable for a pre-revenue business (~15 msgs/day).
- **Keep agentic (Gemini) brain, not n8n/Make**. Agentic is the right tool for Taglish conversation + recommendations. The problem was infrastructure + code bugs, not the approach.
- **Session 98 introduced all 6 bugs in one commit (d942c44)**. Bugs were not caused by session 99's CPU throttle test or session 101's refactor-in-progress. Corrected earlier misattribution.
- **Strict "2 per model" image bank was over-correction** — RA flagged real customer needs for proofs/on-face/lifestyle shots during /chat-test testing. Expansion to ~35-40 with per-image captions is parked as the highest-priority next-session task.
- **First-message greeting is a behavior rule, not a hardcoded reply**. System prompt instructs Gemini to greet warmly + use name + thank for interest + THEN answer, all in one natural message. Dynamic context per call tells Gemini whether it's first contact and whether a name is known.
- **Filipino "hm" = "how much"**. PH customer shorthand that Gemini doesn't know natively — must be in the prompt. Saved as `reference_ph_customer_shorthand.md`.
- **"You cannot see the image" prompt rule**. Gemini was hallucinating scene descriptions ("here's Bandits on someone at a cafe") because it only knows image KEY names, not contents. Fixed by explicit rule to describe the PRODUCT (frame color, lens color, material) only.
- **Valor Global internal pitch strategy**: use DuberyMNL as proof-of-concept, ladder up from free Informdata KB chatbot demo → onboarding automation → Valor/client FB chatbots → HR automation → potential internal AI role. Low-risk internal career pivot attempt.

### Deployed
- **Cloud Run `duberymnl-chatbot` DELETED** (state change, not a deploy)
- **Local Flask + Cloudflare Tunnel LIVE** on home PC: `https://compute-believe-distributors-rocky.trycloudflare.com` → `localhost:8080`
- **Nothing pushed to remote prod** — refactored code is committed only to working copy so far (closeout commit pending)
- Meta webhook still points at deleted Cloud Run URL (returns 404) — intentional, will wire to tunnel URL after image bank expansion
- Boosted ads paused on RA's side

### Blockers
- **Image bank expansion** is the top next-session task. Bring back feedback/proof/on-face/lifestyle shots with short captions per image so Gemini knows what each one depicts. Target ~35-40 images. Without this, do NOT wire Meta webhook back to tunnel — real customers need proof/lifestyle shots we currently don't have.
- Meta webhook still points at deleted Cloud Run URL, returning 404 for any incoming message. OK for now because ads are paused.
- Cloudflare Worker fallback (for PC-offline resilience) not deployed. Needs a free Cloudflare account + Wrangler CLI.
- Auto-start of Flask + cloudflared on PC logon not wired (like Rasclaw's `start-rasclaw.bat` pattern).
- uptimerobot.com monitoring not set up.
- CRM Google Sheet has ~30 `TEST_BATTERY_*` and `TEST_SMOKE_*` rows from testing — needs cleanup script.
- Oracle Cloud signup rejected — decide tomorrow whether to retry, pivot to Hetzner €3.29/mo, or stay local indefinitely.
- Memory files saved this session reference "Session 99" in body text (pre-closeout naming). Low-priority cleanup for /lint-memory later.

---

## Session 100 -- 2026-04-11 (rasclaw-mobile-permissions)

### What
- Expanded `~/.claude/settings.json` allow list for mobile Telegram workflow: `Read(**/channels/telegram/inbox/**)`, `Bash(cp *)`, `WebFetch`, `Bash(gh *)`, `Bash(curl *)`, `Read/Write/Edit(**/Rasclaw/**)`, `mcp__plugin_telegram_telegram__reply` + `__react`
- Added `C:\Users\RAS\projects\Rasclaw` to `additionalDirectories` so Write/Edit tools can reach the Rasclaw inbox
- Diagnosed permission matching quirks through two screenshot iterations with RA on Telegram: scoped `cp "..."` pattern never matched because Claude Code strips quotes before matching
- Confirmed path format: Claude's internal Windows path form is `C:/Users/RAS/...` forward-slash, not git-bash `//c/Users/...`

### Decisions
- Scope mobile auto-approve to Rasclaw only (not all projects) -- RA explicit constraint, enforced by Write/Edit path globs
- Broad `Bash(cp *)` over scoped quoted pattern -- quote normalization kills scoped forms
- Voice ffmpeg not pre-approved -- images only per RA, defer until voice workflow breaks
- Trust existing deny list (rm -rf, force push, .env) as sandbox floor instead of stacking more deny rules

### Deployed
- Nothing deployed (config only)

### Blockers
- Telegram claude session still runs with old perms until manual restart via `~/.claude/scripts/start-rasclaw.bat` -- RA accepted staleness for now
- Voice ffmpeg transcode still prompts per-file if voice workflow comes up

---

## Session 98 -- 2026-04-10 (chatbot-kb-rebuild)

### What
- Added Rasclaw to main.code-workspace
- Rebuilt chatbot knowledge base from draft to production: accurate product descriptions (Bandits slim square, Outback blocky angular, Rasta oversized aviator), specs (TR90/PC frames, dimensions, weight), provincial-prepaid delivery flow, corrected inclusions (drawstring pouch not hard case), DUBERY50 on-mention-only, new tagline "Premium polarized shades at everyday prices", order flow with landmarks + delivery preference + urgent handling, warm+direct persona (not jolly)
- Scraped Dubery supplier site (duberysunglasses.com): 80+ product images + specs for Bandits x5 + Outback x4 + Rasta (D008), saved to references/supplier-images/
- Built chatbot image bank: 48 images in 8 categories (hero/model/lifestyle/collections/brand/feedback/proof/sales-support) uploaded to Google Drive, wired via lh3 CDN URLs + manifest
- Chatbot deployed 10+ times with incremental fixes: English-first rule tightened with Tagalog sentence ban, multi-part messages via reply_parts array, typing_off fix, time import bug fix, Meta attachment_id caching for fast image sends, startup warmup pre-uploading all 48 images, natural typing delay (1.5-4.5s based on reply length)
- Prompt injection defense (3 layers): input scanning for 40+ keywords, SECURITY RULES at top of system prompt, output leak scanning. Flagged senders silenced, no email to RA
- Created DuberyMNL CRM Google Sheet with 4 tabs (Leads, Orders, Lead Score Log, Conversations), shared with Cloud Run service account
- CRM sync wired into chatbot: Gemini extracts customer data per turn, webhook upserts Lead rows with Hot/Warm/Cold/Converted scoring, creates Order rows on completion
- Conversation history persistence: every message synced to Conversations tab, cold-start recovery loads last 20 messages from sheet for returning customers
- Chatbot went LIVE and handled real customer conversations (visible in /conversations dashboard)

### Decisions
- KNOWLEDGE_BASE.md as editable source of truth, sync to cloud-run/knowledge_base.py
- Image bank split: Vercel for hero shots (proven), Drive lh3 CDN for 7 other categories
- Startup warmup all 48 images (+30-60s boot time, eliminates first-send loading circle)
- Multi-part messages via reply_parts array (not \n line breaks) for cleaner Messenger UX
- Natural typing delay: 1.2s base + 25ms/char, capped 4.5s, with typing indicator between parts
- Handoff behavior: flag conversation + bot stops responding + no email (RA explicit feedback)
- DUBERY50 only mentioned when customer brings it up first
- Provincial orders = prepaid only (GCash/InstaPay) because no business docs for Shopee/J&T COD
- CRM v1 in Google Sheets, Supabase later for portfolio value
- Conversation history persisted to sheet for cold-start recovery across Cloud Run restarts

### Deployed
- Cloud Run chatbot (duberymnl-chatbot): 10+ revisions deployed today, currently live with knowledge base rebuild + image bank + prompt injection defense + CRM sync + conversation persistence
- DuberyMNL CRM Google Sheet created (ID: 1wVn9WGdY8pK7c68pZpnNSWoNkhhZvYUywcGqLCqcewA)
- 48 images uploaded to Google Drive (folder: 1TnnaSmd_IzRbus3mCwYw--FO0k4pOByZ)

### Blockers
- Debounce (5s wait + message combining) -- not built
- Flood protection + bot detection (v2 heuristics) -- not built
- Re-engagement script (20-hour follow-up) -- not built
- Facebook page tagline needs manual update (API blocked by pages_manage_metadata permission)
- Website updates pending: align tagline, add discount code field, add provincial/GCash info
- Old 3 conversations lost on pre-CRM redeploy

---

## Session 151 -- 2026-05-03 (bespoke-chess-outback-red)

### Bespoke image gen -- chess concept, outback-red

**Done:**
- Built v3 product-as-locked-asset prompt for outback-red chess editorial concept
- Concept ref: `.tmp/concept-1777748109301.jpeg` (male model + chess board, low dramatic angle, "DO&GO" overlay)
- Prodref used: `contents/assets/prodref-kraft/outback-red/01-hero.png`
- Prompt file: `contents/new/2026-05-03_bespoke-chess-outback-red-001_prompt.json`
- Output: `contents/new/2026-05-03_bespoke-chess-outback-red-001.png` (1490KB, 4:5)
- Manual v3 validation pass: V1-V6 all clean before gen

**Result:**
- Filipino male model in orange bomber jacket, leaning over chess board, low-angle dramatic shot
- Blue sky + clouds background, red-orange mirror Outback lens fidelity strong
- "DUBERY MNL" bold white wordmark centered mid-frame
- Overall: strong editorial campaign shot, product clearly recognizable

**Notes:**
- generate_vertex.py requires `prompt` key in JSON -- plain-text-preamble-only `.json` files parse-fail; wrapped in proper `{prompt, image_input, aspect_ratio}` structure
- Pending RA review before moving to contents/ready/
- Shopee/J&T couriers discussion parked for later

### Iteration 002 -- revision attempt (not logged separately)

- 002 output: lenses rendered dark/neutral instead of red mirror; "DUBERY MNL" text rendered by AI (no fidelity to actual font)

### Iteration 003 -- lens fix + real font composite (2026-05-03)

**Changes from 002:**
- Fix 1 (lens color): `reflection_logic` updated with explicit "vivid red mirror-coated, warm red-orange iridescent tint, reflects sky as deep red-gold -- NOT dark or neutral"; added lens color language to `relight_instruction` and `lighting_atmosphere`
- Fix 2 (font): removed `typography_overlay` from prompt entirely; post-processed with Pillow using `Dubery-Regular.ttf`
- Color-free spec rule correctly NOT applied to `reflection_logic` (applies only to `required_details`)

**Files:**
- Prompt: `contents/new/2026-05-03_bespoke-chess-outback-red-003_prompt.json`
- Raw gen (no text): `contents/new/2026-05-03_bespoke-chess-outback-red-003-raw.png`
- Final composited: `contents/new/2026-05-03_bespoke-chess-outback-red-003.png`

**Font composite details:**
- Font: `dubery-landing-v2/assets/fonts/Dubery-Regular.ttf` (TTF, no conversion needed)
- Font size: 150pt on 928x1152px image (~6.6% of height; font is wide, fills ~95% of frame width)
- Position: centered horizontally, visual top at 45% from image top (518px)
- Fill: solid white, no stroke, no shadow

**Pending:** RA review of -003.png before moving to ready/

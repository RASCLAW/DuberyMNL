# DuberyMNL v3 — Landing Site

Light-theme, mobile-first product site for DuberyMNL. Built to replace duberymnl.com.
Knockaround-inspired. No JS framework. Vanilla HTML/CSS/JS + Python order sync.

---

## Status

**Near production-ready.** All core pages and flows are working.

| Area | Status |
|------|--------|
| Homepage | Done |
| Product catalog (`/products/`) | Done |
| Product detail pages (11 variants) | Done |
| Order / checkout page | Done |
| Shop Social wall | Done |
| Order form → Google Sheets | Working |
| Cart (localStorage) | Working — saveCart() persists on every +/−/× |
| Free delivery logic | Working |
| Art drop lightbox | Working |
| Local order backup | Working |
| CF tunnel (v3.duberymnl.com) | Live |
| Vercel deploy (duberymnl.com) | **LIVE** |

---

## Pages

| URL | File | Purpose |
|-----|------|---------|
| `/` | `index.html` | Homepage — hero, best sellers, shop social, art drop, story, testimonials |
| `/products/` | `products/index.html` | Full catalog — all 11 variants, filter by series |
| `/products/item.html?slug=<slug>` | `products/item.html` | Product detail page (PDP) |
| `/order/` | `order/index.html` | Order / checkout — product picker + form |
| `/shop-social/` | `shop-social/index.html` | Shop-the-look UGC wall with product modals |

### Product Slugs

| Slug | Name |
|------|------|
| `bandits-matte-black` | Bandits – Matte Black |
| `bandits-glossy-black` | Bandits – Glossy Black |
| `bandits-green` | Bandits – Green |
| `bandits-blue` | Bandits – Blue |
| `bandits-tortoise` | Bandits – Tortoise |
| `outback-black` | Outback – Black |
| `outback-blue` | Outback – Blue |
| `outback-red` | Outback – Red |
| `outback-green` | Outback – Green |
| `rasta-red` | Rasta – Red |
| `rasta-brown` | Rasta – Brown |

---

## Running Locally

Start the server once per session (PowerShell):

```powershell
Start-Process python -ArgumentList '-m','http.server','8300' -WorkingDirectory 'C:\Users\RAS\projects\DuberyMNL\dubery-landing-v3' -WindowStyle Hidden
```

- **Local:** http://localhost:8300
- **Public (CF tunnel):** https://v3.duberymnl.com

The CF tunnel requires `cloudflared` running on the same machine. The tunnel maps `v3.duberymnl.com` → `localhost:8300`.

---

## Order Flow

1. Customer picks products on `/order/` or clicks "Add to Cart" on a PDP
2. Cart is stored in `localStorage['dubery-cart']`
3. Customer fills in name, phone, address on `/order/` and submits
4. On submit:
   - POST to Google Apps Script → **DuberyMNL Orders sheet** (source of truth)
   - Order also saved to `localStorage['dubery-orders-log']` as browser-side backup
5. Success screen shown. Cart cleared.

### Pricing

- ₱499 per pair
- Free delivery on 2+ pairs (bundle deal)
- ₱99 delivery fee for single pairs

### Delivery note on PDP

- 0–1 items in cart: "Add one more pair for FREE DELIVERY PROMO."
- 2+ items in cart: "Free delivery applied." (green)

---

## Order Backup

Orders land in **Google Sheets** (primary). To sync to a local JSON file:

```bash
python tools/orders/sync_orders.py
```

Saves to `orders/orders.json`. Run anytime to get a fresh snapshot.
Covers all orders — landing page, chatbot, PDP — since they all POST to the same sheet.

---

## Key Data Files

| File | Purpose |
|------|---------|
| `products/data.json` | All product data — galleries, prices, copy, specs, hero/thumb images |
| `shop-social/data.json` | Shop social wall tiles — UGC images + tagged products |
| `orders/orders.json` | Local order backup (run sync script to refresh) |

### Product data.json fields

Each product entry:

```json
{
  "slug": "outback-blue",
  "name": "Outback",
  "colorLabel": "Blue",
  "colorway": "Matte Black / Blue Mirror Polarized Lenses",
  "series": "outback",
  "seriesLabel": "Outback",
  "price": 499,
  "rating": 4.8,
  "count": 156,
  "frame": "Matte Black",
  "lens": "Blue Mirror",
  "copy": "...",
  "hero": "assets/catalog/outback-blue.png",
  "thumb": "assets/catalog/outback-blue-thumb.png",
  "gallery": ["assets/catalog/outback-blue.png", "..."],
  "order_name": "Outback – Blue"
}
```

`order_name` uses an en-dash (–) and must match the format in the Orders sheet.

---

## Editing Products

### Edit a gallery (add/remove/reorder photos)

1. Open: `http://localhost:8300/products/item.html?slug=<slug>`
2. Click the **Edit** button (bottom-right corner) or add `&edit` to the URL
3. Add, remove, or drag-reorder photos in the thumbnail strip
4. Click **Save data.json** — file downloads to your Downloads folder
5. Drop the `data.json` file in the Claude chat and say which product you edited
6. Claude will merge it, copy any new images to `assets/catalog/`, and report missing files

### Edit catalog card thumbnails

The catalog page (`/products/`) uses `hero` and `hover` fields — not `gallery[0]`.
To update a card's thumbnail, ask Claude to update `hero` and `thumb` in `data.json`.

---

## Cache Busting

All CSS and JS files use a `?v=v3-NNN` query string to bust browser cache.

**Current version:** `v3-030`

When CSS/JS changes are not showing on https://v3.duberymnl.com (even though localhost looks right):
1. The CF tunnel is pass-through (`cf-cache-status: DYNAMIC`) — not the culprit
2. The browser cached the old asset for the live domain

**Fix:** bump all version tags to the next number across all HTML files:

```powershell
$files = Get-ChildItem 'dubery-landing-v3' -Recurse -Filter '*.html'
foreach ($f in $files) {
    $c = Get-Content $f.FullName -Raw
    $u = $c -replace '\?v=v3-0[0-9]{2}', '?v=v3-014'  # change target/replacement as needed
    if ($u -ne $c) { Set-Content $f.FullName $u -NoNewline; Write-Host "Updated: $($f.Name)" }
}
```

Then reload the live URL — the browser fetches the fresh asset.

---

## Product Card Image Navigation

Cards (best sellers + catalog) support swipe and arrow navigation to reveal a second image.

- **Swipe left** → shows hover/alternate image (`.is-swiped` class toggled on card)
- **Swipe right** → back to primary image
- **Arrow buttons** (`.bs-nav-bar`) overlaid at bottom-center of the card image
- **Dot indicator** (`.bs-dots`) below the image — 2 pills, active one turns red
- Tapping the card (no swipe) navigates to PDP as normal
- CSS `:hover` swap removed — swipe/arrow is the only mechanism

CSS classes: `.is-swiped`, `.bs-nav-bar`, `.bs-nav--prev`, `.bs-nav--next`, `.bs-dots`, `.bs-dot`
JS: `attachCardSwipe()` in `script.js` (best sellers) and `catalog.js` (catalog page)

---

## Shop Social Wall (`/shop-social/`)

54 UGC tiles. Each tile has author, location, caption, and tagged product slugs.

### Edit mode

Go to `http://localhost:8300/shop-social/?edit` (or `v3.duberymnl.com/shop-social/?edit`):

- **X button** on each tile removes it
- **Click a tile** → opens right-drawer edit panel: author, location, caption, product chips
- **Download data.json** button (bottom bar) exports the current state
- **Exit Edit** returns to normal view

Workflow: edit in browser → Download → drop `data.json` into `shop-social/data.json`.

### data.json fields

```json
{
  "id": 1,
  "image": "../assets/social/social-01.png",
  "author": "@handle",
  "location": "City",
  "caption": "Caption text. #duberymnl #bandits #polarized",
  "products": ["bandits-matte-black"]
}
```

---

## PDP Section Order

On the product detail page, sections render in this order:

1. **The Look** — `section-feature-image` (injected by JS if product has `feature_image` / `feature_images`)
2. **What people are saying** — `section-testimonials`
3. **People also bought** — `section-series`

The Look is inserted via `insertAdjacentElement('beforebegin')` on `.section-testimonials` in `item.js`.

---

## PDP Interactions

### Add to Cart flow
1. "Add to Cart" → immediately shows "Added ✓" (green, disabled)
2. After 1.5s → transitions to "Shop All" (default style)
3. Tapping "Shop All" navigates to `/products/`

### Testimonials rail
Reviews on the PDP scroll horizontally. On mobile: 1 card at 85% width, snap-to-card. On tablet: 2 cards. On desktop: 4 cards.

---

## Shared Scripts

| File | Purpose |
|------|---------|
| `cart.js` | Shared cart badge updater — included on every page. Also updates delivery note. |
| `hero-edit.js` | Hero image crop editor — X/Y/Zoom sliders + Copy CSS. Activate at `?edit`. |
| `editor.js` | Visual editor (homepage `?edit` mode) |
| `script.js` | Homepage interactions (nav, scroll, best sellers, swipe) |
| `styles.css` | All styles — single stylesheet for the entire site |
| `products/item.js` | PDP logic — gallery, add to cart, people also bought, testimonials |
| `products/catalog.js` | Catalog card render + filter + swipe |

---

## Design System

See [DESIGN.md](DESIGN.md) for full token reference, typography scale, component specs, and DO NOTs.

Key rules:
- Accent color: `#D7392A` (coral-red) — CTAs and highlights only, never large fills
- No JS framework — vanilla only
- No scroll-scrub animations, no GSAP
- No dark scenes, no jeepneys/markets/sari-sari in photography

---

## Deployment

**Live at duberymnl.com.** Vercel project: `dubery-landing-v3` (rasclaws-projects).

- Connected to `RASCLAW/DuberyMNL` GitHub repo, root directory `dubery-landing-v3/`
- Auto-deploys on every push to `main`
- Cloudflare proxies the domain — "Proxy Detected" in Vercel is expected
- The old v1 site (`dubery-landing/`) stays in the repo as archive — do not delete

### Recent Changes (2026-05-03)
- Section spacing tightened: `--section-y` `clamp(2rem,4vw,3.5rem)` (was `4rem–7rem`)
- Shop-our-feed pill opacity reduced to 67% (was 96%)
- 15 unused assets removed from `assets/`
- CSS version: v3-030

---

## What's Next

- [ ] Smoke test: place a real order on duberymnl.com → confirm it lands in Orders sheet

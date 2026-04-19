# DuberyMNL v3 — Design System

Knockaround-inspired, light theme, product-first. Built for Filipino buyers on mobile, ordering through form OR Messenger.

## 1. Brand Essence

- **Tagline:** Made for the view.
- **Voice:** Authentic, relatable, labas-life Filipino. Not corporate. Not stiff.
- **Positioning:** Polarized sunglasses from ₱599. Same tech as 10x brands, without the markup.
- **Proof points:** Metro Manila same-day COD, nationwide shipping, 11 variants across 3 series.
- **Purchase paths:** (1) Order form → CRM Sheet; (2) Messenger `m.me/duberymnl`. No checkout.

## 2. Color Tokens

```
--bg              #ffffff   page background
--bg-soft         #f7f5f1   section alternation, warm off-white
--surface         #ffffff   cards, form inputs
--border          #e6e3dc   hairline dividers
--text            #1a1a1a   primary copy, headings
--text-muted      #5a5a5a   secondary copy, meta
--text-subtle     #8a8a8a   captions, disabled
--accent          #D7392A   coral-red (from BOLD creative), primary CTA
--accent-hover    #B82E20   CTA pressed
--accent-ink      #ffffff   text on accent
--success         #2E7D4F   order confirmation
```

Use accent sparingly — primary CTA, key badges, link hover. Never as a large fill.

## 3. Typography

```
--font-display    'Space Grotesk', sans-serif    // headings, navigation
--font-body       'Inter', sans-serif            // paragraphs, form fields
--font-dubery     'Dubery', 'Space Grotesk'      // brand italic accents only
```

**Scale (clamp for responsive):**
- `--fs-hero`:      clamp(2.5rem, 6vw, 4.5rem)    // H1 on hero
- `--fs-h2`:        clamp(2rem, 4vw, 3rem)        // section headings
- `--fs-h3`:        clamp(1.25rem, 2vw, 1.5rem)   // card titles
- `--fs-body`:      1rem                          // paragraph
- `--fs-small`:     0.875rem                      // meta, trust strip
- `--fs-micro`:     0.75rem                       // badges, tags

Weights: display uses 500/600/700. Body uses 400/500. No ultra-light, no black.

## 4. Layout Tokens

```
--container       1200px
--container-tight 960px
--gutter          clamp(1rem, 4vw, 2.5rem)
--section-y       clamp(4rem, 8vw, 7rem)
--radius-sm       6px
--radius-md       12px
--radius-lg       20px
--shadow-card     0 2px 8px rgba(0,0,0,0.06)
--shadow-hover    0 8px 24px rgba(0,0,0,0.12)
```

Grid: 12-col desktop, 6-col tablet, 2-4 col mobile. Mobile-first CSS.

## 5. Components

### Trust strip (top of page, above nav)
- Full-width bar, `--bg-soft`, `--text-muted` copy, 36px tall
- Copy: "Nationwide COD • Metro Manila Same-Day • 100% Polarized • From ₱599"
- Mobile: horizontal auto-scroll or single condensed line

### Sticky nav
- 72px tall desktop, 60px mobile, white bg with 1px bottom border on scroll
- Logo left (logo-header.png, 40px h), links center (Shop All, Series, About, Facebook), CTA right ("Message Us" — accent button)
- Mobile: hamburger collapses links; CTA persists inline

### Hero (primary)
- Full-bleed image, 70-80vh, darkening overlay on left 40% (not full image) so copy stays readable
- Copy stack: eyebrow (Dubery italic, accent) + H1 (display 600, white) + sub (body, white) + dual CTA (primary accent + secondary ghost)

### Product card (catalog + best sellers)
- White bg, 1px border, radius-md, hover lifts with shadow-hover
- Image pad: 12% padding, product-on-white shot
- Meta: series label (micro, muted), name (h3), price (h3, accent)
- Dual CTA at bottom: "Order" (primary filled) + "Message" (ghost, Messenger icon)

### CTA button
- Primary: accent bg, white text, 12px 24px padding, radius-sm, 600 weight
- Secondary/ghost: transparent bg, 1px border `--text`, `--text` text, same padding
- Hover: primary → accent-hover; ghost → bg `--text`, text white
- No drop shadow on buttons

### Form field
- 1px border `--border`, 12px 16px padding, radius-sm, full width on mobile
- Focus: border `--accent`, 2px ring `rgba(215,57,42,0.15)`
- Labels above, required mark (*) in `--accent`
- Error: border + helper text in `--accent`

### Section
- Vertical padding `--section-y`, alternating bg (`--bg` then `--bg-soft`)
- Container max-width, centered, `--gutter` horizontal padding
- Section eyebrow (Dubery italic, accent, micro) + H2 + optional body

### Tile with product tag (shop social)
- Square or portrait UGC photo, product-tag badge pinned bottom-left: small circle + label
- Hover (desktop): tag expands to show price + CTA
- Click: opens lightbox with full photo + tagged product card(s)

### Lightbox
- Full-screen dark overlay (rgba(0,0,0,0.85)), close X top-right
- Photo left 60%, product card right 40% on desktop; stacked on mobile
- ESC or click-outside closes

## 6. Photography Direction

- **Hero:** lifestyle-first. Real people wearing pairs, daytime, outdoor, Filipino context.
- **Catalog:** product-on-pure-white, 3/4 angle, soft studio light, consistent across all 11 variants.
- **UGC wall:** natural, mobile-shot-looking, varied scenes (skatepark, beach, market, festival, underwater).
- **Founder / story:** one bold portrait with brand-color bg (use `BOLD-1776484921.png` or similar).
- **Art drop:** graphic overlays on product shots (reused from v2).

## 7. DO NOT

- No dark overlays on product-on-white catalog shots
- No gradient abuse (hero darkening is the only allowed gradient)
- No scroll-scrub animations, no GSAP timelines, no Lenis (ref feedback_simple_flow_beats_scroll_scrub)
- No `backdrop-filter` over scroll-animated content (ref feedback_flicker_backdrop_filter)
- No CSS transforms for large layout shifts (ref feedback_transforms_break_clicks)
- No emoji in UI copy
- No Filipino-flavor scenes in photography: jeepneys, rice paddies, sari-sari stores, markets (ref feedback_no_sarisari_market)
- No night scenes (ref feedback_no_night_scenes)
- No baked-in product names inside hero images (keep logo/name as overlay text, not pixel-baked)

## 8. Accessibility

- Body copy minimum 16px, line-height 1.6
- Tap targets minimum 44x44 px
- Color contrast: text on bg ≥ 4.5:1; accent on white passes for buttons at 600 weight
- Alt text on all product + UGC images
- Form labels visible always, not placeholder-only

## 9. Performance

- Images: compressed WebP where supported, max 200KB per hero, max 80KB per catalog card
- Fonts: only regular + italic of Dubery (already WOFF2); Space Grotesk + Inter via `font-display: swap`
- No JS framework. Vanilla JS for interactions.
- Lighthouse target: perf ≥ 85 mobile, ≥ 95 desktop

## 10. File References

- Fonts: `assets/fonts/dubery-regular.woff2`, `assets/fonts/dubery-italic.woff2`
- Logo: `assets/logos/logo-header.png`
- Hero primary: `assets/hero/hero-primary.png` (source: `contents/new/BESPOKE-bandits-tortoise-hatbanner.png`)
- Hero polarized-proof: `assets/hero/hero-underwater.png` (source: `contents/new/EDIT-underwater-bandits-nobrand.png`)
- Series cards: `assets/hero/series-bandits.png` (HC1), `series-outback.png` (HC2), `series-classics.png` (HC3)
- Lifestyle wall: `assets/lifestyle/*.png` (4 tiles from BESPOKE-* set)
- Art drop: `assets/art/*.png` (reused from v2)
- Catalog: `assets/catalog/{slug}.png` (11 variants — Phase 5 generates missing)

---
name: v3 Order Page — Visual Product Grid
description: Order page redesigned from text-dropdown picker rows to visual product grid with Bandits/Outback/Rasta series accordions
type: project
related: [project_v3_best_sellers_hover.md, reference_v3_pdp_gallery_editor.md]
---

`dubery-landing-v3/order/` was redesigned in session 148. The old UI used text dropdown rows (`picker-rows` / `picker-select`). The new UI shows all 11 products as image cards grouped under collapsible series accordions.

**Architecture:**
- `qtys` map (slug → number) replaces the `rows` array — simpler, no dedup logic needed
- `cardEls` map (slug → {card, qtyDisplay}) for direct DOM updates from sidebar × remove
- Three accordions: Bandits (open by default), Outback, Rasta (both collapsed)
- Each card: hero img, colorway, price, stepper (−/qty/+)
- Card gets `.is-active` class (accent border) when qty > 0
- Sidebar render(), submission handler, and URL param pre-select (`?model=slug&qty=N`) all preserved

**Key files:**
- `order/order.js` — full rewrite (series accordion builder + qtys map)
- `order/index.html` — `data-picker-rows` → `data-product-grid`
- `styles.css` — `.order-series-group/toggle/grid` + `.order-product-card` (replaced old `.picker-rows/.picker-row`)

**Why:** Text dropdowns were abstract and not visually engaging. Product cards with images let users browse all colorways upfront and tap + to add — same mental model as a shopping page.

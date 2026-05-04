---
name: v3 Best Sellers Hover = gallery[1]
description: Homepage best sellers hover images use gallery[1] from data.json; must stay in sync when gallery order changes or best seller products are swapped
type: project
related: [project_v3_order_redesign.md, reference_v3_pdp_gallery_editor.md]
---

Best sellers hover images in `dubery-landing-v3/index.html` are hardcoded `<img class="bs-img hover">` tags. They must always match `gallery[1]` from `products/data.json` for the corresponding product slug.

**Why:** The `hover` field in data.json was originally used, but it pointed to stale social images (`assets/social/social-XX.png`). gallery[1] is the first lifestyle/studio shot shown in the PDP gallery — the most natural hover image.

**How to apply:**
- When RA drops a new data.json from Downloads with a reordered gallery, check if gallery[1] changed for any best seller product. If yes, update the hover src in `index.html` AND `products/data.json`.
- When swapping a best seller product (e.g. outback-blue → outback-green), update: `href` slug, primary img src, hover img src (= new product's gallery[1]), alt text, rating, count, colorway label.
- Current best sellers (2026-05-02): outback-black, rasta-red, outback-green, bandits-tortoise.
- Path in index.html uses `assets/catalog/` (no `../`). data.json uses `../assets/catalog/`.

---
name: dubery-brand-collection
description: Generate DuberyMNL collection showcase images -- multiple products in one frame. 5 layout variants plus wide carousel format. Use when showcasing product series, lineups, or unboxing experiences.
argument-hint: "layout products"
---

# DuberyMNL Collection Showcase Generator

Generates structured JSON prompts for Gemini 3.1 Flash that produce multi-product collection images.
Multiple products in one frame with clean studio presentation. Brand awareness -- no pricing.

---

## Rules (override everything below)

**L1 -- Real Surface Only**
Products must sit on a real surface: dark wood, leather, concrete, marble, stone.
Real surfaces provide reflections, shadows, and ambient color. Plain backgrounds = CG look.

**L2 -- Consistent Angle**
Every product at the EXACT same angle and scale (unless using HERO_CAST where hero is intentionally larger).
Inconsistent angles = amateur collage. This is non-negotiable.

**L3 -- Consistent Lighting & Shadows**
All products lit by the same light source. Shadows fall the same direction for every product.
Lens reflections should match the same environment for all products.

**L4 -- Odd Numbers**
3 or 5 products look more natural than 2 or 4. Use odd groupings when possible.
Exception: UNBOX_FLATLAY can use 2 (one series has only 2 models).

**L5 -- Breathing Room**
Products need space between them. Overcrowding kills the composition.
Each product must be clearly distinguishable.

**L6 -- Color Organization**
Arrange products by color gradient: light to dark, or warm to cool.
This creates visual flow instead of random placement.

**L7 -- One Reference Per Product**
Pass one reference image per product in the collection. Use `1.png` (3/4 front) for Bandits.

**L8 -- No Sales Language**
BANNED: pricing, "ORDER NOW", "BUY NOW", "MESSAGE US", discount codes.

**L9 -- Typography**
All text uses the bold italic sporty typeface from the font reference image.
Font reference must always be in `image_input`.

**L10 -- Text Under 15%**
Text occupies under 15% of image area. Series header + optional subtitle. Let the products speak.

---

## 5 Layout Variants

### FLAT_LAY

Top-down bird's-eye view. Products arranged in triangle formation on a flat surface, arms folded.

**Best for:** Showing all products at equal visual weight. "Here's the collection" overview.

**Scene:** Dark walnut wood table with natural overhead daylight.

**Feedback:** Pass at 90% fidelity. Use PRODUCT REF folder for Bandits when available.

**Reference prompt (3 Bandits, PASSED):**
"A top-down flat lay photograph of three [Series] sunglasses from DuberyMNL arranged in a triangle formation on a dark walnut wooden table. ONE pair each of [Product 1], [Product 2], and [Product 3] -- all real [finish] sunglasses matching the reference images, all at the same angle with arms folded, arranged light to dark left to right. Natural overhead daylight illuminates all three equally with consistent soft shadows beneath each pair. Breathing room between each pair. All text in the bold italic sporty typeface from the font reference. White headline '[SERIES] SERIES' at top. Small subtitle '[SUBTITLE]' below. DuberyMNL logo bottom-right. 4:5 aspect ratio."

### HERO_CAST

One product 30-40% larger in foreground as hero. Others flanking behind at left and right.

**Best for:** Featuring a hero product while showing the range. Premium catalog energy.

**Scene:** Dark leather surface with warm overhead studio lighting.

**Feedback:** Fire (96%). Needs environment reflections on front product for full pass.

**Reference prompt (3 Outbacks, FIRE):**
"A studio product photograph on a dark leather surface with warm overhead lighting. Three [Series] sunglasses from DuberyMNL -- [Hero Product] as hero in the foreground center, 30% larger than the others. [Product 2] and [Product 3] flanking behind at left and right. All real [finish] sunglasses matching the reference images, all at the same 3/4 angle, consistent shadows from the same overhead light. The hero [Hero Product] anchors the composition. All text in the bold italic sporty typeface from the font reference. White headline '[HEADLINE]' at top. Small subtitle '[SUBTITLE]' below. DuberyMNL logo bottom-right. 4:5 aspect ratio, premium catalog feel."

### DIAGONAL

Products arranged along a diagonal line from upper-left to lower-right. Slightly overlapping.
Color progression from warm to cool or light to dark.

**Best for:** Dynamic visual flow. Cross-series lineups. Dramatic side lighting.

**Scene:** Dark concrete surface with dramatic side lighting from the left.

**Feedback:** Concept is great, Bandits fidelity needs PRODUCT REF. Use single variant PNGs for Outback/Rasta.

**Reference prompt (mixed series, PASSED with notes):**
"A product photograph on a dark concrete surface with dramatic side lighting from the left. Three sunglasses from DuberyMNL arranged in a diagonal line from upper-left to lower-right: [Product 1], [Product 2], and [Product 3] -- each slightly overlapping the next, creating visual flow. All real sunglasses matching the reference images, all at the same 3/4 angle, each catching the same side light with consistent shadows. Color progression from [warm] to [cool]. All text in the bold italic sporty typeface from the font reference. White headline '[HEADLINE]' at top-left. DuberyMNL logo bottom-right. 4:5 aspect ratio."

### FAN_SPREAD

Products fanned out from a central point like a hand of cards. Arms overlap at the center, lenses fan outward.

**Best for:** Dynamic, eye-catching composition. 3 products max.

**Scene:** Dark marble surface with soft overhead studio lighting.

**Feedback:** Fire. Lens colors may drift but composition is legit.

**Reference prompt (3 Bandits, FIRE):**
"A product photograph on a dark marble surface with soft overhead studio lighting. Three [Series] sunglasses from DuberyMNL fanned out from a central point like a hand of cards: [Product 1] in the center, [Product 2] to the left, [Product 3] to the right. Arms overlap at the center pivot, lenses fan outward. All real sunglasses matching the reference images, same angle, consistent overhead lighting and matching shadows on the marble. All text in the bold italic sporty typeface from the font reference. White headline '[HEADLINE]' at top. DuberyMNL logo bottom-right. 4:5 aspect ratio."

### UNBOX_FLATLAY

Products + packaging accessories arranged together from above. Tells the "what's in the box" story.

**Best for:** Unboxing experience. Brand trust. Showing perceived value.

**Includes:** Sunglasses + Dubery box + black drawstring pouch + cleaning cloth. NO test card.

**Scene:** Dark wooden table with warm overhead natural light.

**Feedback:** Fire. Ensure sunglasses aren't dwarfed by packaging -- products should be prominent.

**Reference prompt (2 Rastas + packaging, FIRE):**
"A lifestyle flat lay photograph from above on a dark wooden table. The complete [Series] unboxing experience: ONE pair of [Product 1] and ONE pair of [Product 2] arranged side by side, with the Dubery branded packaging box, black drawstring pouch, and cleaning cloth arranged around them. All real products matching the reference images. The sunglasses are prominently sized -- not dwarfed by the packaging. Warm overhead natural light, consistent shadows. Everything arranged with breathing room -- not cramped. All text in the bold italic sporty typeface from the font reference. White headline '[HEADLINE]' at top. Small subtitle '[SUBTITLE]' below. DuberyMNL logo bottom-right. 4:5 aspect ratio."

---

## Wide Format (Carousel)

Any layout can be generated at 2:1 ratio for carousel slicing into two 1:1 panels.

**Rules for wide:**
- Keep text and key products away from the center cut line
- Each panel should work as a standalone image AND flow together
- Wide format works best for HERO_CAST and UNBOX_FLATLAY
- Use the standard slicer (Pillow crop at midpoint)

To generate wide, set `"aspect_ratio": "2:1"` in api_parameters.

---

## DROPPED: GRID

Grid layout (1x3 row, 2x2 arrangement) was tested and failed. Products look pasted, too sterile, no visual interest. Do not use.

---

## Input

```json
{
  "layout": "HERO_CAST",
  "product_refs": ["Outback Red", "Outback Blue", "Outback Green"],
  "hero": "Outback Red",
  "headline": "THE OUTBACK LINE",
  "subtitle": "Built for every adventure",
  "include_packaging": false,
  "wide": false,
  "notes": "Optional direction"
}
```

- `layout`: FLAT_LAY | HERO_CAST | DIAGONAL | FAN_SPREAD | UNBOX_FLATLAY
- `product_refs`: 2-4 products
- `hero`: which product is the hero (HERO_CAST only)
- `headline`: or null to auto-generate
- `subtitle`: optional
- `include_packaging`: true to add box/pouch/cloth (default for UNBOX_FLATLAY)
- `wide`: true for 2:1 carousel format
- `notes`: any direction

---

## JSON Output Schema

```json
{
  "task": "brand_collection",
  "layout": "HERO_CAST",

  "visual_mood": "1-2 sentence concept",

  "text_elements": [
    { "content": "TEXT", "role": "headline | subtitle", "position": "where", "size": "large | medium | small" }
  ],

  "product": {
    "models": ["Product 1", "Product 2", "Product 3"],
    "finish": "glossy | matte | mixed",
    "placement": "description of arrangement",
    "instruction": "All real sunglasses matching references, same angle, same lighting..."
  },

  "brand": {
    "logo_position": "bottom-right",
    "color_scheme": "description"
  },

  "prompt": "Adapt from reference prompt for chosen layout",

  "image_input": [
    "product 1 ref",
    "product 2 ref",
    "product 3 ref",
    "contents/assets/fonts/DUBERY-FONTS.png",
    "contents/assets/logos/dubery-logo.jpg"
  ],

  "api_parameters": { "aspect_ratio": "4:5", "resolution": "1K", "output_format": "jpg" }
}
```

For UNBOX_FLATLAY, add packaging reference:
`"contents/assets/logos/dubery-packaging.png"`

---

## Product Reference Table
**RANDOMIZE ANGLE:** Do NOT always use -1.png. Randomly pick from available angles (-1, -2, -3, -4, -multi) per product. Vary across a batch so the feed looks diverse. Match angle to composition when possible (e.g. -3 detail closeup for feature callouts, -multi for collections).

### Bandits (pick ONE angle from ref folder)

| product_ref | ref folder | default angle | finish |
|---|---|---|---|
| Bandits Glossy Black | `contents/assets/product-refs/bandits-glossy-black/` | bandits-glossy-black-1.png | glossy |
| Bandits Matte Black | `contents/assets/product-refs/bandits-matte-black/` | bandits-matte-black-1.png | matte |
| Bandits Blue | `contents/assets/product-refs/bandits-blue/` | bandits-blue-1.png | glossy |
| Bandits Green | `contents/assets/product-refs/bandits-green/` | bandits-green-1.png | glossy |
| Bandits Tortoise | `contents/assets/product-refs/bandits-tortoise/` | bandits-tortoise-1.png | matte |

### Outback + Rasta

| product_ref | ref folder | default angle | finish |
|---|---|---|---|
| Outback Black | `contents/assets/product-refs/outback-black/` | outback-black-1.png | matte |
| Outback Blue | `contents/assets/product-refs/outback-blue/` | outback-blue-1.png | matte |
| Outback Green | `contents/assets/product-refs/outback-green/` | outback-green-1.png | matte |
| Outback Red | `contents/assets/product-refs/outback-red/` | outback-red-1.png | matte |
| Rasta Brown | `contents/assets/product-refs/rasta-brown/` | rasta-brown-1.png | matte |
| Rasta Red | `contents/assets/product-refs/rasta-red/` | rasta-red-1.png | matte |

---

## Brand Assets

| Asset | Path |
|---|---|
| Font alphabet | `contents/assets/fonts/DUBERY-FONTS.png` |
| Logo (black bg) | `contents/assets/logos/dubery-logo.jpg` |
| Logo (white bg) | `contents/assets/logos/dubery-logo.png` |
| Packaging | `contents/assets/logos/dubery-packaging.png` |

---

## Self-Check

- [ ] Real surface (L1)
- [ ] All products at same angle (L2) -- unless HERO_CAST hero
- [ ] Consistent lighting and shadows (L3)
- [ ] Odd number of products preferred (L4)
- [ ] Breathing room between products (L5)
- [ ] Color-organized arrangement (L6)
- [ ] One ref per product (L7)
- [ ] No sales language (L8)
- [ ] Font ref in image_input (L9)
- [ ] Text under 15% of image (L10)
- [ ] No test card in UNBOX_FLATLAY
- [ ] Valid JSON, forward slashes, paths exist

---

## Execution

1. Read input
2. Select layout variant
3. Resolve product refs (one image per product)
4. Generate headline/subtitle if not provided
5. Adapt reference prompt for chosen layout
6. Build JSON, run self-check
7. Save to `.tmp/COLL-{id}_prompt.json`

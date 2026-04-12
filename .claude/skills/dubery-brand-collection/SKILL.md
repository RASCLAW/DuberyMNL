---
name: dubery-brand-collection
description: Generate DuberyMNL collection showcase images -- multiple products in one frame. 5 layout variants plus wide carousel format. Use when showcasing product series, lineups, or unboxing experiences.
argument-hint: "layout products"
---

# DuberyMNL Collection Showcase Generator

Generates structured JSON prompts for Gemini 3.1 Flash that produce multi-product collection images.
Multiple products in one frame with clean studio presentation. Brand awareness -- no pricing.

---

## Format Rules (fixed -- apply to every generation)

**L1 -- Real Surface Only**
Products must sit on a real surface: dark wood, leather, concrete, marble, stone.
Real surfaces provide reflections, shadows, and ambient color. Plain backgrounds = CG look.

**L2 -- Consistent Angle**
Every product at the EXACT same angle and scale (unless using HERO_CAST where hero is intentionally larger).
Inconsistent angles = amateur collage. Non-negotiable.

**L3 -- Consistent Lighting & Shadows**
All products lit by the same light source. Shadows fall the same direction for every product.
Lenses on every product catch the same environment light.

**L4 -- Odd Numbers**
3 or 5 products look more natural than 2 or 4. Use odd groupings when possible.
Exception: UNBOX_FLATLAY can use 2 (one series has only 2 models).

**L5 -- Breathing Room**
Products need space between them. Overcrowding kills the composition.
Each product must be clearly distinguishable.

**L6 -- Color Organization**
Arrange products by color gradient: light to dark, or warm to cool.
This creates visual flow instead of random placement.

**L7 -- One Reference Per Product, Varied Angles Across Batch**
Pass one reference image per product (multiple refs per single product causes duplicates).
Across a batch, rotate through available angles (`-1` 3/4 front, `-2` multi-angle, `-3` detail, `-4` technical, `-multi`). Never default to `-1.png` for every image. Within a single image, all products must be at the SAME angle (L2) -- so pick the angle once for that image, then apply it to every product in the set.

**L8 -- No Sales Language**
BANNED: pricing, "ORDER NOW", "BUY NOW", "MESSAGE US", discount codes.

**L9 -- Typography**
All text uses the bold italic sporty typeface from the font reference image.
Font reference must always be in `image_input`.

**L10 -- Text Under 15%**
Text occupies under 15% of image area. Series header + optional subtitle. Let the products speak.

---

## Product Fidelity Rules (ported from WF2 -- non-negotiable)

**R2 -- Product Fidelity**
The reference images are the ONLY authority on product appearance. Applies uniformly to every product in the collection.
BANNED in prompt text:
- Frame colors: black, blue, red, green, brown, amber, tortoise, camo, matte, glossy, dark, clear
- Lens descriptors: tinted, mirrored, warm, cool, gold, silver, smoke, amber, honey, sapphire
- Materials: metal, acetate, plastic, rubber, nylon
- Compound forms: "warm red/orange-tinted", "cool blue-tinted", "brown-amber", "earthy green"
- ANY description of what any frame or lens looks like

When tempted to describe a product, write "as shown in the reference image."
Model names (e.g., "Outback Red") may appear as identifiers only, never as color cues.

**Color-organization exception (L6):** You may say "arranged light to dark" or "warm to cool progression" as a composition cue -- these describe the arrangement order, not the products themselves. Do NOT say "from the warm Rasta Red to the cool Bandits Blue."

**R3 -- render_notes Template**
`product.render_notes` MUST use this exact 5-field template. Fill in ONLY the brackets. For collections, every field applies uniformly to ALL products in the image.

```
POSITION: [arrangement -- triangle formation / diagonal line / fan spread / hero-and-flank / flat lay with packaging].
ANGLE: [3/4 view / lens facing camera / profile / overhead -- same for every product].
LIGHTING: [how light hits the products -- single source, direction, quality, intensity].
LOGO: Dubery logo on temple arm must be sharp and legible on every product.
REFERENCE: Frame shape, color, material, and lens appearance for every product are dictated entirely by the reference images.
```

No text beyond these 5 fields. No color or material descriptions. Ever.

**R4 -- Lens Reflection Rule**
Do NOT describe specific lens reflections (no "palm trees reflected in lens", no "skyline visible in lens").
BUT the lenses should naturally interact with the scene lighting and environment -- Gemini should render reflections that make sense for where the products sit.
One allowed phrase: "lenses naturally catching the same light and environment of the scene across every pair."

---

## 5 Layout Variants

**VARIETY RULE:** For every generation, randomly pick ONE option from each variety bank. Never repeat the same combo in a batch. The layout RULES are fixed -- only the creative execution changes.

### FLAT_LAY

Top-down bird's-eye view. Products arranged in a formation (triangle for 3, row for 2-4, cross for 5) on a flat surface, arms folded.

**Best for:** Showing all products at equal visual weight. "Here's the collection" overview.

**Known good:** Pass at 90% fidelity. Use PRODUCT REF folder for Bandits when available.

**Surface bank (pick one):**
- Dark walnut wooden table with visible grain
- Clean oak boards
- Dark slate slab with subtle texture
- White marble with grey veining
- Grey linen fabric background
- Polished concrete surface
- Clean leather desk mat
- Dark walnut wood planks

**Lighting bank (pick one):**
- Natural overhead daylight, soft even fill
- Overhead soft studio light, consistent shadow direction
- Cool top-down morning light
- Warm overhead afternoon light
- Diffused overcast light from above
- Dramatic overhead spotlight, deep shadows

**Scatter detail bank (pick 0-2 optional, small, tasteful):**
- Single loose leaf beside the arrangement
- Small dried flower stem
- Travel passport at the edge
- Folded linen napkin corner
- Small brass compass
- Clean hardcover book corner

### HERO_CAST

One product 30-40% larger in foreground as hero. Others flanking behind at left and right. Hero anchors the composition.

**Best for:** Featuring a hero product while showing the range. Premium catalog energy.

**Known good:** Fire (96%). Needs environment reflections on front product for full pass.

**Surface bank (pick one):**
- Dark brown leather studio surface
- Dark walnut catalog table
- Slate slab with subtle texture
- Warm polished concrete
- Dark marble with veining
- Brushed metal studio surface

**Lighting bank (pick one):**
- Warm overhead studio light, even fill
- Cool rim light from behind, warm key from above
- Diagonal side light from the right
- Dramatic overhead spotlight on hero, soft fill on flank
- Soft top-down studio lighting
- Warm directional light, hero catches main highlight

**Mood bank (pick one):**
- Clean premium catalog
- Moody editorial
- Warm retail showroom
- Minimalist high-end
- Cinematic product hero

### DIAGONAL

Products arranged along a diagonal line from upper-left to lower-right. Slightly overlapping. Color progression follows the arrangement (light to dark or warm to cool).

**Best for:** Dynamic visual flow. Cross-series lineups. Dramatic side lighting.

**Known good:** Concept is strong. Bandits fidelity needs PRODUCT REF folder.

**Surface bank (pick one):**
- Dark polished concrete
- Dark slate slab
- Dark walnut wood planks
- Warm dark marble
- Brushed steel surface
- Charcoal textured concrete

**Lighting bank (pick one):**
- Dramatic side light from the left, long shadows
- Dramatic side light from the right, long shadows
- Cool rim light from behind, low-angle fill
- Warm golden side light, directional
- Overhead + side combo, catalog drama
- Single spotlight from upper-left

**Color flow bank (pick one):**
- Light to dark, left to right
- Dark to light, left to right
- Warm to cool, left to right
- Cool to warm, left to right
- Similar tones, arranged by size

### FAN_SPREAD

Products fanned out from a central point like a hand of cards. Arms overlap at the center, lenses fan outward.

**Best for:** Dynamic, eye-catching composition. 3 products max.

**Known good:** Fire. Lens colors may drift but composition is legit.

**Surface bank (pick one):**
- Dark marble with subtle veining
- Dark slate slab
- Polished concrete
- Dark walnut table
- Warm brown leather surface
- Black matte studio surface

**Lighting bank (pick one):**
- Soft overhead studio light
- Warm top-down light
- Cool even overhead
- Dramatic top spotlight, pivot catches highlight
- Diagonal overhead from the upper-right
- Natural overhead daylight

**Pivot detail bank (pick one):**
- Tight center pivot, clean arm overlap
- Slight center overlap, lenses clearly separated
- Anchored center pivot, radial symmetry
- Loose pivot, organic fan
- Precise pivot, catalog-tight

### UNBOX_FLATLAY

Products + packaging accessories arranged together from above. Tells the "what's in the box" story.

**Best for:** Unboxing experience. Brand trust. Showing perceived value.

**Includes:** Sunglasses + Dubery box + black drawstring pouch + cleaning cloth. NO test card.

**Known good:** Fire. Ensure sunglasses aren't dwarfed by packaging -- products should be prominent.

**Surface bank (pick one):**
- Dark walnut table with visible grain
- Warm walnut wood planks
- White marble with grey veining
- Grey linen fabric background
- Polished concrete countertop
- Dark slate slab
- Dark oak with clean finish

**Lighting bank (pick one):**
- Warm overhead natural daylight
- Soft window light from the side
- Cool overhead studio light
- Golden hour through a window
- Overcast diffused overhead
- Warm morning light from the left

**Arrangement bank (pick one):**
- Products center, packaging arranged radially around them
- Products upper half, packaging lower half
- Spiral arrangement flowing clockwise
- Asymmetric with products dominant
- Diagonal flow from packaging to products
- Clean grid with products prioritized

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

## Prompt Construction

Build every prompt fresh from the layout rules + variety banks + fidelity rules. Do NOT copy templates.

**Structure -- PRODUCTS FIRST:** The sunglasses are the anchor. Build the world around them.

1. **Open with the products** -- "ONE pair each of [Product 1], [Product 2], [Product 3] from DuberyMNL" photographed in this scene, all real pairs matching the reference images (R2).
2. **Surface + environment** -- the surface, mood, background detail. Keep it simple.
3. **Arrangement** -- the layout-specific formation (triangle / hero-flank / diagonal / fan / unboxing flat lay). State the color-organization flow (L6) as an arrangement cue, not a product description.
4. **Lighting** -- single light source, direction, quality; every product shares it with consistent shadows (L3). End with "lenses naturally catching the same light and environment of the scene across every pair" (R4).
5. **Typography + logo** -- headline + subtitle placement, font reference, logo position.

6-9 sentences max. Shorter = more natural.

**Mandatory in every prompt:**
- "ONE pair each of [Product Names] from DuberyMNL"
- "all real pairs photographed in this scene, matching the style shown in the reference images" (R2)
- "all at the same angle" (L2) -- unless HERO_CAST where hero is larger
- Single light source stated, products share it
- Consistent shadows on the surface (L3)
- "Lenses naturally catching the same light and environment of the scene across every pair" (R4)
- "Breathing room between each pair" (L5)
- "All text in the bold italic sporty typeface from the font reference" (L9)
- "DuberyMNL logo bottom-right" (or whatever position the layout specifies)

**NEVER include in prompt:**
- Any word from the R2 banned list describing any product
- Any specific lens reflection description (R4)
- Sales language (L8)
- Plain solid color background (L1)
- Inconsistent angles or lighting across products (L2 / L3)

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

- `layout`: FLAT_LAY | HERO_CAST | DIAGONAL | FAN_SPREAD | UNBOX_FLATLAY (default: HERO_CAST)
- `product_refs`: 2-4 products
- `hero`: which product is the hero (HERO_CAST only)
- `headline`: or null to auto-generate
- `subtitle`: optional
- `include_packaging`: true to add box/pouch/cloth (default true for UNBOX_FLATLAY)
- `wide`: true for 2:1 carousel format
- `notes`: any direction

---

## JSON Output Schema

```json
{
  "task": "brand_collection",
  "layout": "HERO_CAST",

  "visual_mood": "1-2 sentence concept -- describe scene and atmosphere, NOT the products",

  "text_elements": [
    { "content": "TEXT", "role": "headline | subtitle", "position": "where", "size": "large | medium | small" }
  ],

  "product": {
    "models": ["Product 1", "Product 2", "Product 3"],
    "render_notes": "POSITION: ... ANGLE: ... LIGHTING: ... LOGO: ... REFERENCE: ...",
    "instruction": "All real sunglasses as shown in the reference images. ONE pair each. Same angle, same lighting, consistent shadows."
  },

  "brand": {
    "logo_position": "bottom-right",
    "color_scheme": "description of scene colors, NOT product colors"
  },

  "prompt": "Built fresh from rules + banks. NOT copied from a template.",

  "image_input": [
    "contents/assets/product-refs/{model1}/{model1}-{N}.png",
    "contents/assets/product-refs/{model2}/{model2}-{N}.png",
    "contents/assets/product-refs/{model3}/{model3}-{N}.png",
    "contents/assets/fonts/DUBERY-FONTS.png",
    "contents/assets/logos/dubery-logo.jpg"
  ],

  "api_parameters": { "aspect_ratio": "4:5", "resolution": "1K", "output_format": "jpg" }
}
```

For UNBOX_FLATLAY, append packaging reference to `image_input`:
`"contents/assets/logos/dubery-packaging.png"`

All products in a single image share the SAME angle suffix (e.g. all `-2.png` or all `-3.png`). Pick the angle once per image from available angles, then apply it to every product.

---

## Product Reference Table

**RANDOMIZE ANGLE ACROSS BATCH:** Do NOT always use -1.png for every collection. Pick a different SINGLE-VIEW angle (-1, -3, -4) for each new collection image so the feed doesn't look like the same shot. Within a single image, all products use the SAME angle (L2 enforcement).
**BANNED for generation:** `-2.png` (multi-angle strip) and `-multi.png` (composite) -- these confuse Gemini into merging/distorting the product.

### Bandits

| product_ref | ref folder | finish |
|---|---|---|
| Bandits Glossy Black | `contents/assets/product-refs/bandits-glossy-black/` | glossy |
| Bandits Matte Black | `contents/assets/product-refs/bandits-matte-black/` | matte |
| Bandits Blue | `contents/assets/product-refs/bandits-blue/` | glossy |
| Bandits Green | `contents/assets/product-refs/bandits-green/` | glossy |
| Bandits Tortoise | `contents/assets/product-refs/bandits-tortoise/` | matte |

Angles: 1 = 3/4 front, 2 = multi-angle strip, 3 = detail closeups, 4 = technical diagram

### Outback + Rasta

| product_ref | ref folder | finish |
|---|---|---|
| Outback Black | `contents/assets/product-refs/outback-black/` | matte |
| Outback Blue | `contents/assets/product-refs/outback-blue/` | matte |
| Outback Green | `contents/assets/product-refs/outback-green/` | matte |
| Outback Red | `contents/assets/product-refs/outback-red/` | matte |
| Rasta Brown | `contents/assets/product-refs/rasta-brown/` | matte |
| Rasta Red | `contents/assets/product-refs/rasta-red/` | matte |

Filename pattern: `{model}-{N}.png` where N = 1, 2, 3, 4, or multi.

---

## Brand Assets

| Asset | Path |
|---|---|
| Font alphabet | `contents/assets/fonts/DUBERY-FONTS.png` |
| Logo (black bg) | `contents/assets/logos/dubery-logo.jpg` |
| Logo (white bg) | `contents/assets/logos/dubery-logo.png` |
| Packaging | `contents/assets/logos/dubery-packaging.png` |

Default logo: black bg. Use white bg when the image background is dark.

---

## Self-Check

- [ ] Real surface (L1) -- no plain backgrounds
- [ ] All products at same angle (L2) -- unless HERO_CAST hero
- [ ] Consistent lighting and shadows (L3)
- [ ] Odd number of products preferred (L4)
- [ ] Breathing room between products (L5)
- [ ] Color-organized arrangement (L6) -- expressed as arrangement order, not product descriptions
- [ ] One ref per product (L7), all products in same image share the same angle suffix
- [ ] No sales language (L8)
- [ ] Font ref in image_input (L9)
- [ ] Text under 15% of image (L10)
- [ ] No test card in UNBOX_FLATLAY
- [ ] render_notes uses exact 5-field template (R3), applied uniformly to all products
- [ ] No banned words from R2 in prompt or visual_mood
- [ ] No specific lens reflection descriptions (R4)
- [ ] "as shown in the reference images" for products (R2)
- [ ] Variety bank picks differ from other images in batch
- [ ] Prompt is original -- NOT copied from a template
- [ ] Valid JSON, forward slashes, paths exist

---

## Execution

1. Read input
2. Select layout variant
3. Resolve product refs (pick ONE angle for the image, apply to every product)
4. Generate headline/subtitle if not provided
5. Pick random options from variety banks for the chosen layout
6. Write a fresh prompt following Prompt Construction rules and R2/R3/R4 fidelity
7. Build JSON, run self-check
8. Save to `contents/new/COLL-{id}_prompt.json`

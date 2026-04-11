---
name: dubery-brand-callout
description: Generate DuberyMNL feature callout images -- product hero with labeled features. 5 layout variants. Use when creating product showcase posts with feature highlights.
argument-hint: "layout product"
---

# DuberyMNL Feature Callout Generator

Generates structured JSON prompts for Gemini 3.1 Flash that produce product feature callout images.
Product as hero with labeled features pointing to specific parts. Brand awareness content -- no pricing.

---

## Format Rules (fixed -- apply to every generation)

**C1 -- Real Environment Only**
Product must sit on a real surface with real lighting. NEVER use a plain solid color background.
Real surfaces give Gemini cues for reflections, shadows, and ambient color. Without them, products look CG.

**C2 -- Single Reference, Varied Angles**
Pass only ONE product reference image per generation (multiple refs cause duplicates).
BUT vary the angle across a batch -- rotate through `-1` (3/4 front), `-2` (multi-angle strip), `-3` (detail closeup), `-4` (technical diagram), `-multi` when available. Never default to `-1.png` for every image.

**C3 -- One Pair Only**
Every prompt must include: "only ONE pair of sunglasses" or "ONE pair of [product]".
Gemini will duplicate without this explicit instruction.

**C4 -- Callout Limits**
- 4-6 callouts max. More = manual, not marketing.
- Each label: 4-5 words max.
- Thin red arrows/lines. Never thick or colorful (they compete with product).
- Callouts radiate outward into clean space. NEVER overlap the product.
- Arrow placement is approximate -- Gemini places them compositionally, not anatomically. Accept ~80% accuracy.

**C5 -- No Sales Language**
BANNED: pricing, "ORDER NOW", "BUY NOW", "MESSAGE US", discount codes.
ALLOWED: "Follow @DuberyMNL", "duberymnl.com"

**C6 -- Typography**
All text uses the bold italic sporty typeface from the font reference image.
Font reference must always be in `image_input`.

---

## Product Fidelity Rules (ported from WF2 -- non-negotiable)

**R2 -- Product Fidelity**
The reference image is the ONLY authority on product appearance.
BANNED in prompt text:
- Frame colors: black, blue, red, green, brown, amber, tortoise, camo, matte, glossy, dark, clear
- Lens descriptors: tinted, mirrored, warm, cool, gold, silver, smoke, amber, honey, sapphire
- Materials: metal, acetate, plastic, rubber, nylon
- Compound forms: "warm red/orange-tinted", "cool blue-tinted", "brown-amber", "earthy green"
- ANY description of what the frame or lens looks like

When tempted to describe the product, write "as shown in the reference image."
Model names (e.g., "Outback Red") may appear as identifiers only, never as color cues.

**R3 -- render_notes Template**
`product.render_notes` MUST use this exact 5-field template. Fill in ONLY the brackets:

```
POSITION: [resting on surface / held / displayed / propped].
ANGLE: [3/4 view / lens facing camera / profile / overhead].
LIGHTING: [how light hits the product -- direction, quality, intensity].
LOGO: Dubery logo on temple arm must be sharp and legible.
REFERENCE: Frame shape, color, material, and lens appearance are dictated entirely by the reference image.
```

No text beyond these 5 fields. No color or material descriptions. Ever.

**R4 -- Lens Reflection Rule**
Do NOT describe specific lens reflections (no "palm trees reflected in lens", no "skyline visible in lens").
BUT the lenses should naturally interact with the scene lighting and environment -- Gemini should render reflections that make sense for where the product is, not copy the original photo's reflections.
One allowed phrase: "lenses naturally catching the light and environment of the scene."

---

## Feature Bank (pick 3-5 per image)

- Polarized lenses -- eliminates horizontal glare
- UV400 protection -- blocks 99.9% of harmful UV rays
- Lightweight frame -- all-day comfort
- Durable hinges -- built for daily use
- Dubery logo -- authentic branding on temple arm
- Anti-scratch coating -- lens longevity
- Flexible temples -- secure fit for active lifestyles
- TAC polarized construction -- premium lens tech
- Precision-molded frames -- clean lines, no distortion

---

## 5 Layout Variants

**VARIETY RULE:** For every generation, randomly pick ONE option from each variety bank. Never repeat the same combo in a batch. The layout RULES are fixed -- only the creative execution changes.

### RADIAL

Product centered at ~60% canvas width. 4 callout labels radiate outward in all directions with thin red arrows. Headline at top. Logo bottom-right.

**Best for:** Showing 4-6 features at once. The default layout.

**Surface bank (pick one):**
- Dark walnut wooden table
- Polished concrete ledge
- Aged brown leather surface
- Dark slate slab
- Brushed metal desk
- Reclaimed barn wood
- Matte black powder-coated surface
- Dark marble with subtle veining

**Lighting bank (pick one):**
- Warm window light from the left, afternoon
- Overhead soft studio light, even fill
- Cool morning light from the right
- Warm golden hour side light
- Dramatic single spotlight from above
- Diffused overcast daylight

**Background bank (pick one):**
- Soft warm bokeh of interior space
- Out-of-focus window with warm tones
- Neutral dark gradient fade
- Shallow depth of field, warm ambient
- Blurred warm industrial backdrop

### SPLIT

Product on the left side (~55% of frame). Feature labels stacked vertically on the right with thin horizontal connector lines. Editorial magazine feel.

**Best for:** Clean, readable layout. Text is easy to scan because it's aligned.

**Known issue:** Can leave vacant space below the product. Use `fill_objects` to populate.

**Surface bank (pick one):**
- Dark wooden editorial table
- Polished concrete with subtle texture
- Grey linen fabric background
- Aged leather desk mat
- Dark marble slab
- Warm walnut wood

**Lighting bank (pick one):**
- Warm window light from the left
- Overhead magazine studio light
- Soft diffused side lighting
- Dramatic editorial side light
- Even flat studio lighting

**Fill objects bank (pick 1-2 for vacant space):**
- Small brown leather keychain
- Vintage watch
- Brass compass
- Folded linen pocket square
- Weathered paperback book
- Coffee cup with steam
- Weathered notebook and pen
- Travel passport
- Brass lighter
- Leather wallet

### EXPLODED

Product fills 70% of the frame. One feature magnified in a circular inset with red outline. Single-feature deep dive.

**Best for:** Highlighting ONE hero feature in detail. "Look closer" energy.

**Known issue:** Zoomed-in texture is AI-generated, doesn't match actual polarized TAC lens tech. Use for visual impact, not technical accuracy.

**Surface bank (pick one):**
- Dark wooden surface, close grain
- Matte black textured surface
- Dark leather close-up texture
- Polished slate
- Charcoal concrete with fine texture
- Dark velvet fabric

**Lighting bank (pick one):**
- Warm side light from the right, deep shadows
- Cool rim light, high contrast
- Overhead product spotlight
- Warm directional light, dramatic fall-off
- Soft top-down studio light

**Inset placement bank (pick one):**
- Upper-right corner
- Upper-left corner
- Lower-right corner
- Mid-right floating
- Mid-left floating

### NUMBERED

Product on one side. Numbered features (1-4) listed on the other with large red numbers. "Reasons to buy" format.

**Best for:** Educational angle, scannable, shareable.

**Surface bank (pick one):**
- Outdoor concrete ledge
- Stone wall edge
- Reclaimed wood picnic bench
- Urban rooftop parapet
- Aged wooden dock plank
- Painted metal bench slat

**Background bank (pick one):**
- Blurred urban greenery and trees
- Out-of-focus city skyline
- Beach palms in soft focus
- Mountain landscape bokeh
- Blurred Manila street scene
- Tropical foliage background
- Industrial warehouse setting
- Shoreline with ocean bokeh

**Lighting bank (pick one):**
- Bright natural midday sunlight
- Warm golden hour from the side
- Overcast soft diffused daylight
- Early morning warm light
- Late afternoon side light

**Number style bank (pick one):**
- Large red outline numbers
- Solid red filled numbers
- Red numbers in white circles
- Red serif display numbers
- Red condensed bold numbers

### TOP_BOTTOM

Symmetrical balanced layout. 2 feature labels above the product, 2 below. Product centered in the middle.

**Best for:** Clean, balanced, premium catalog feel.

**Surface bank (pick one):**
- Brown leather cafe table
- Dark walnut catalog surface
- White marble slab
- Dark slate tile
- Polished concrete
- Warm wooden showroom surface
- Dark linen tablecloth

**Environment bank (pick one):**
- Cafe interior with warm bokeh
- Clean studio backdrop with shadow fall
- Retail showroom setting
- Home office desk setting
- Outdoor rooftop table at golden hour
- Hotel lounge side table

**Lighting bank (pick one):**
- Warm ambient overhead
- Cool even studio light
- Golden hour side light
- Overcast soft diffuse
- Dramatic rim light from behind

**Accent bank (pick one):**
- Red underlines on each label
- Red dot markers beside each label
- Red small square markers
- Thin red connector lines
- Red number-like ticks

---

## Prompt Construction

Build every prompt fresh from the layout rules + variety banks + fidelity rules. Do NOT copy templates.

**Structure -- PRODUCT FIRST:** The sunglasses are the anchor. Build the world around them.

1. **Open with the product** -- ONE pair of [Product Name] sunglasses from DuberyMNL, photographed in this scene, matching the style shown in the reference image (R2). Where it rests and how light hits it.
2. **Surface + environment** -- the surface the product sits on and the world behind it. Keep it simple -- let Gemini fill in natural details.
3. **Lighting** -- state the light source direction, quality, and how the product shares it (real shadows, natural lens/environment interaction -- R4).
4. **Callouts** -- describe where the 4-6 labels sit, the thin red arrows/connectors, and the layout pattern.
5. **Typography + logo** -- headline placement, font reference, logo position.

6-9 sentences max. Shorter = more natural.

**Mandatory in every prompt:**
- "ONE pair of [Product Name] sunglasses from DuberyMNL" (C3)
- "a real pair photographed in this scene, matching the style shown in the reference image" (R2 -- tells Gemini to RECREATE, not paste)
- Light source direction stated, product shares the same light
- Product casts real shadows onto the surface
- "Lenses naturally catching the light and environment of the scene" (R4 -- never describe specific reflections)
- "All text in the bold italic sporty typeface from the font reference" (C6)
- "DuberyMNL logo bottom-right" (or whatever position the layout specifies)
- Headline text and feature label text spelled out

**NEVER include in prompt:**
- Any word from the R2 banned list describing the product
- Any specific lens reflection description (R4)
- Sales language (C5)
- Multiple products or multiple pairs (C3)
- Plain solid color background (C1)

---

## Input

```json
{
  "layout": "RADIAL",
  "product_ref": "Bandits Green",
  "headline": "BUILT TO PERFORM",
  "features": ["POLARIZED LENSES", "UV400 PROTECTION", "FLEXIBLE TEMPLES", "DURABLE HINGES"],
  "notes": "Optional direction"
}
```

- `layout`: RADIAL | SPLIT | EXPLODED | NUMBERED | TOP_BOTTOM (default: RADIAL)
- `product_ref`: product name from reference table
- `headline`: 3-5 words, or null to auto-generate
- `features`: 3-5 from the feature bank, or custom
- `notes`: any specific direction

---

## JSON Output Schema

```json
{
  "task": "brand_callout",
  "layout": "RADIAL",

  "visual_mood": "1-2 sentence concept -- describe scene and atmosphere, NOT the product",

  "text_elements": [
    { "content": "TEXT", "role": "headline | label | caption", "position": "where", "size": "large | medium | small" }
  ],

  "product": {
    "models": ["Product Name"],
    "render_notes": "POSITION: ... ANGLE: ... LIGHTING: ... LOGO: ... REFERENCE: ...",
    "instruction": "Only ONE pair. As shown in the reference image."
  },

  "callouts": [
    { "label": "POLARIZED LENSES", "description": "Eliminates horizontal glare", "connector": "thin red arrow" }
  ],

  "brand": {
    "logo_position": "bottom-right",
    "color_scheme": "description of scene colors, NOT product colors"
  },

  "prompt": "Built fresh from rules + banks. NOT copied from a template.",

  "image_input": [
    "contents/assets/product-refs/{model}/{model}-{N}.png",
    "contents/assets/fonts/DUBERY-FONTS.png",
    "contents/assets/logos/dubery-logo.jpg"
  ],

  "api_parameters": { "aspect_ratio": "4:5", "resolution": "1K", "output_format": "jpg" }
}
```

---

## Product Reference Table

**RANDOMIZE ANGLE:** Do NOT always use -1.png. Randomly pick from available angles (-1, -2, -3, -4, -multi) per product. Vary across a batch so the feed looks diverse. For callout, `-3` (detail closeup) is often the best match when available.

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

Default logo: black bg (dubery-logo.jpg). Use white bg when the image background is dark.

---

## Self-Check

- [ ] Real surface environment (C1) -- no plain backgrounds
- [ ] Single reference image (C2)
- [ ] Angle is NOT -1.png if the product has other angles available (C2)
- [ ] "ONE pair" in prompt (C3)
- [ ] 4-6 callouts, 4-5 words each (C4)
- [ ] No sales language (C5)
- [ ] Font reference in image_input (C6)
- [ ] render_notes uses exact 5-field template (R3)
- [ ] No banned words from R2 in prompt or visual_mood
- [ ] No specific lens reflection descriptions (R4)
- [ ] "as shown in the reference image" for product (R2)
- [ ] Variety bank picks differ from other images in batch
- [ ] Prompt is original -- NOT copied from a template
- [ ] Valid JSON, forward slashes, paths exist

---

## Execution

1. Read input
2. Select layout variant (default RADIAL)
3. Resolve product ref to single image path (randomize angle from available)
4. Pick or generate features from bank
5. Generate headline if not provided (3-5 words, no repeats in batch)
6. Pick random options from variety banks for the chosen layout
7. Write a fresh prompt following Prompt Construction rules and R2/R3/R4 fidelity
8. Build JSON, run self-check
9. Save to `contents/new/CALLOUT-{id}_prompt.json`

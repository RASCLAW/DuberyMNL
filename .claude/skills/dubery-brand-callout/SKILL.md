---
name: dubery-brand-callout
description: Generate DuberyMNL feature callout images -- product hero with labeled features. 5 layout variants. Use when creating product showcase posts with feature highlights.
argument-hint: "layout product"
---

# DuberyMNL Feature Callout Generator

Generates structured JSON prompts for Gemini 3.1 Flash that produce product feature callout images.
Product as hero with labeled features pointing to specific parts. Brand awareness content -- no pricing.

---

## Rules (override everything below)

**C1 -- Real Environment Only**
Product must sit on a real surface with real lighting. NEVER use a plain solid color background.
Real surfaces: wooden table, concrete ledge, leather surface, stone, cafe table, outdoor surface.
Real surfaces give Gemini cues for reflections, shadows, and ambient color. Without them, products look CG.

**C2 -- Single Reference Angle**
Pass only ONE product reference image. Multiple angles cause Gemini to generate multiple sunglasses.
Default: `1.png` (3/4 front view) for Bandits. Single variant PNG for Outback/Rasta.

**C3 -- One Pair Only**
Every prompt must include: "only ONE pair of sunglasses" or "ONE pair of [product]".
Gemini will duplicate without this explicit instruction.

**C4 -- Lens Reflects Environment**
The lens should naturally reflect whatever environment the product sits in. Window light = window reflection.
Sunlight = sky reflection. This is what makes it look real vs CG.

**C5 -- Callout Limits**
- 4-6 callouts max. More = manual, not marketing.
- Each label: 4-5 words max.
- Thin red arrows/lines. Never thick or colorful (they compete with product).
- Callouts radiate outward into clean space. NEVER overlap the product.
- Arrow placement is approximate -- Gemini places them compositionally, not anatomically. Accept ~80% accuracy.

**C6 -- No Sales Language**
BANNED: pricing, "ORDER NOW", "BUY NOW", "MESSAGE US", discount codes.
ALLOWED: "Follow @DuberyMNL", "duberymnl.com"

**C7 -- Typography**
All text uses the bold italic sporty typeface from the font reference image.
Font reference must always be in `image_input`.

---

## Feature Bank (pick 3-5 per image)

- Polarized lenses -- eliminates horizontal glare
- UV400 protection -- blocks 99.9% of harmful UV rays
- Lightweight frame -- all-day comfort
- Durable hinges -- built for daily use
- Dubery logo -- authentic branding on temple arm
- Anti-scratch coating -- lens longevity
- Flexible temples -- secure fit for active lifestyles

---

## 5 Layout Variants

### RADIAL

Product centered at ~60% canvas width. 4 callout labels radiate outward in all directions with thin red arrows.
Headline at top. Logo bottom-right.

**Best for:** Showing 4-6 features at once. The default layout.

**Scene:** Dark wooden table with warm window light from the left. Soft warm bokeh behind.

**Reference prompt (Bandits Green, passed V3):**
"A product photograph of ONE pair of [Product] sunglasses from DuberyMNL resting on a dark wooden table with warm window light from the left. Real [finish] sunglasses matching the reference, with natural window reflections in the lens and a real contact shadow on the wood grain. Soft warm bokeh in the background. All text in the bold italic sporty typeface from the font reference. White headline '[HEADLINE]' at top. Four callout labels with thin red arrows: '[FEATURE 1]' and '[FEATURE 2]' above, '[FEATURE 3]' and '[FEATURE 4]' below, each with small description. DuberyMNL logo bottom-right. 4:5 aspect ratio."

### SPLIT

Product on the left side (~55% of frame). Feature labels stacked vertically on the right with thin horizontal connector lines. Editorial magazine feel.

**Best for:** Clean, readable layout. Text is easy to scan because it's aligned.

**Known issue:** Can leave vacant space below the product. Fill with packaging, accessories, or extend the surface detail.

**Scene:** Dark wooden table with warm window light. Or vary the surface.

**Reference prompt (Bandits Green, passed V3):**
"An editorial product photograph on a dark wooden table with warm window light from the left. Only ONE pair of [Product] sunglasses from DuberyMNL on the left side of the frame at 3/4 angle -- real [finish] sunglasses matching the reference image with natural lens reflections and real shadow on wood. On the right side, four feature labels stacked vertically with thin red horizontal lines connecting each to the product: '[FEATURE 1]', '[FEATURE 2]', '[FEATURE 3]', '[FEATURE 4]', each with a small description below. All text in the bold italic sporty typeface from the font reference. White headline '[HEADLINE]' at top. DuberyMNL logo bottom-right. 4:5 aspect ratio, magazine editorial feel."

### EXPLODED

Product fills 70% of the frame. One feature magnified in a circular inset with red outline. Single-feature deep dive.

**Best for:** Highlighting ONE hero feature in detail. "Look closer" energy.

**Known issue:** Zoomed-in texture is AI-generated, doesn't match actual polarized TAC lens tech. Use for visual impact, not technical accuracy.

**Scene:** Dark wooden surface with warm side lighting. Shallow depth of field.

**Reference prompt (Bandits Green, passed V3):**
"A close-up product photograph of ONE pair of [Product] sunglasses from DuberyMNL on a dark wooden surface with warm side lighting -- real [finish] sunglasses matching the reference image, filling 70% of the frame. A circular magnification inset with a thin red outline in the upper-right corner shows a zoomed detail of the polarized lens surface. White headline '[HEADLINE]' at top-left in the bold italic sporty typeface from the font reference. Label '[FEATURE]' near the inset with description '[DESCRIPTION]' below. DuberyMNL logo bottom-right. 4:5 aspect ratio, premium product photography."

### NUMBERED

Product on one side. Numbered features (1-4) listed on the other with large red numbers. "Reasons to buy" format.

**Best for:** Educational angle, scannable, shareable.

**Scene:** Outdoor concrete surface with bright natural sunlight. Urban greenery behind.

**Reference prompt (Bandits Matte Black, passed V3):**
"A product photograph of ONE pair of [Product] sunglasses from DuberyMNL resting on an outdoor concrete ledge in bright natural sunlight, blurred urban greenery in the background. Real [finish] sunglasses matching the reference image with natural sunlight on the lens and real shadow on the concrete. On the right side, a numbered feature list with large red numbers: '1 [FEATURE 1]', '2 [FEATURE 2]', '3 [FEATURE 3]', '4 [FEATURE 4]'. All text in the bold italic sporty typeface from the font reference. White headline '[HEADLINE]' at top. DuberyMNL logo bottom-right. 4:5 aspect ratio."

### TOP_BOTTOM

Symmetrical balanced layout. 2 feature labels above the product, 2 below. Product centered in the middle.

**Best for:** Clean, balanced, premium catalog feel.

**Scene:** Brown leather surface in a cafe with warm ambient lighting. Soft bokeh of cafe interior.

**Reference prompt (Outback Red, passed V3):**
"A product photograph of ONE pair of [Product] sunglasses from DuberyMNL centered on a brown leather surface inside a cafe with warm ambient overhead lighting and soft bokeh of the cafe interior behind. Real [finish] sunglasses matching the reference image with natural reflections and real shadow on the leather. Symmetrical layout: white headline '[HEADLINE]' at top, feature labels '[FEATURE 1]' and '[FEATURE 2]' in a row above the product, feature labels '[FEATURE 3]' and '[FEATURE 4]' in a row below the product. All text in the bold italic sporty typeface from the font reference. Red accent underlines on each label. DuberyMNL logo bottom-right. 4:5 aspect ratio, balanced composition."

---

## Input

```json
{
  "layout": "RADIAL",
  "product_ref": "Bandits Green",
  "headline": "BUILT TO PERFORM",
  "features": ["POLARIZED LENSES", "UV400 PROTECTION", "FLEXIBLE TEMPLES", "DURABLE HINGES"],
  "scene": null,
  "notes": "Optional direction"
}
```

- `layout`: RADIAL | SPLIT | EXPLODED | NUMBERED | TOP_BOTTOM (default: RADIAL)
- `product_ref`: product name from reference table
- `headline`: override or null to auto-generate
- `features`: 3-5 from the feature bank, or custom
- `scene`: override surface/environment, or null for layout default
- `notes`: any specific direction

---

## JSON Output Schema

```json
{
  "task": "brand_callout",
  "layout": "RADIAL",

  "visual_mood": "1-2 sentence concept",

  "text_elements": [
    { "content": "TEXT", "role": "headline | label | caption", "position": "where", "size": "large | medium | small" }
  ],

  "product": {
    "models": ["Product Name"],
    "finish": "glossy | matte",
    "placement": "description",
    "instruction": "Only ONE pair..."
  },

  "brand": {
    "logo_position": "bottom-right",
    "color_scheme": "description"
  },

  "prompt": "The full Gemini prompt -- adapt from the reference prompt for the chosen layout",

  "image_input": [
    "product ref path (single angle)",
    "C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/fonts/DUBERY-FONTS.png",
    "C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/dubery-logo.jpg"
  ],

  "api_parameters": { "aspect_ratio": "4:5", "resolution": "1K", "output_format": "jpg" }
}
```

---

## Product Reference Table

### Bandits (pick ONE angle from ref folder)

| product_ref | ref folder | default angle | finish |
|---|---|---|---|
| Bandits Glossy Black | `C:/Users/RAS/Documents/PRODUCT REF/bandits-glossy-black/` | 1.png | glossy |
| Bandits Matte Black | `C:/Users/RAS/Documents/PRODUCT REF/bandits-matte-black/` | 1.png | matte |
| Bandits Blue | `C:/Users/RAS/Documents/PRODUCT REF/bandits-blue/` | 1.png | glossy |
| Bandits Green | `C:/Users/RAS/Documents/PRODUCT REF/bandits-green/` | 1.png | glossy |
| Bandits Tortoise | `C:/Users/RAS/Documents/PRODUCT REF/bandits-tortoise/` | 1.png | matte |

Angles: 1=3/4 front, 2=multi-angle strip, 3=detail closeups, 4=technical diagram

### Outback + Rasta (single variant)

| product_ref | image_input path | finish |
|---|---|---|
| Outback Black | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/outback-black.png` | matte |
| Outback Blue | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/outback-blue.png` | matte |
| Outback Green | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/outback-green.png` | matte |
| Outback Red | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/outback-red.png` | matte |
| Rasta Brown | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/rasta-brown.png` | matte |
| Rasta Red | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/rasta-red.png` | matte |

---

## Brand Assets

| Asset | Path |
|---|---|
| Font alphabet | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/fonts/DUBERY-FONTS.png` |
| Logo (black bg) | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/dubery-logo.jpg` |
| Logo (white bg) | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/dubery-logo.png` |

Default logo: black bg (dubery-logo.jpg). Use white bg when image background is dark.

---

## Self-Check

- [ ] Real surface environment (C1) -- no plain backgrounds
- [ ] Single reference angle (C2) -- one product image only
- [ ] "ONE pair" instruction in prompt (C3)
- [ ] Lens reflects environment (C4)
- [ ] 4-6 callouts, 4-5 words each (C5)
- [ ] No sales language (C6)
- [ ] Font reference in image_input (C7)
- [ ] Valid JSON, forward slashes, paths exist
- [ ] Prompt adapted from the reference prompt for chosen layout

---

## Output Validation

- Valid JSON (no trailing commas, proper escaping)
- `prompt` field is a string
- `image_input` is an array of absolute paths that exist
- All paths use forward slashes

---

## Execution

1. Read input
2. Select layout variant (default RADIAL)
3. Resolve product ref to single image path
4. Pick features from bank or use provided
5. Generate headline if not provided
6. Adapt the reference prompt for the chosen layout, substituting product/features/scene
7. Build JSON, run self-check
8. Save to `.tmp/CALLOUT-{id}_prompt.json`

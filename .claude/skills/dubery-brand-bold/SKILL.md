---
name: dubery-brand-bold
description: Generate DuberyMNL bold statement images -- massive typography with product integration. 4 layout variants. Use when creating brand awareness posts with bold headlines, typographic designs, or statement pieces.
argument-hint: "layout product headline"
---

# DuberyMNL Bold Statement Generator

Generates structured JSON prompts for Gemini 3.1 Flash that produce bold typographic brand images.
Typography dominates. Product integrates INTO the text composition. Brand awareness -- no pricing.

---

## Rules (override everything below)

**S1 -- Typography Dominates**
Text occupies 40-60% of the canvas. This is the ONE format where text is bigger than the product.
The headline IS the design.

**S2 -- 3-5 Words Max**
Headlines must be 3-5 words. Not a sentence -- a statement.
"OWN THE SUN." not "Our sunglasses help you see the world better."

**S3 -- Product Integrates, Not Floats**
The product must be part of the same composition as the text -- never floating separately.
Each layout variant defines HOW the product integrates. Follow the variant's integration method.
A floating product on a plain background = instant fail.

**S4 -- Maximum 2 Text Elements**
The headline statement + one small tagline ("DUBERY POLARIZED"). Nothing else.
More text dilutes the impact.

**S5 -- Single Reference Angle**
Pass only ONE product reference image. Default: `1.png` for Bandits, single variant for Outback/Rasta.

**S6 -- One Pair Only**
Every prompt must include "ONE pair" to prevent duplicates.

**S7 -- No Sales Language**
BANNED: pricing, "ORDER NOW", "BUY NOW", "MESSAGE US", discount codes.

**S8 -- Typography**
All text uses the bold italic sporty typeface from the font reference image.
Font reference must always be in `image_input`.

**S9 -- High Contrast**
Text must be legible instantly on mobile. White text on dark bg, or dark text on light bg.
Minimum 4.5:1 contrast ratio.

---

## Headline Bank (use or adapt, always 3-5 words)

- "OWN THE SUN."
- "POLARIZED. ALWAYS."
- "SEE CLEAR."
- "STYLE THAT PROTECTS"
- "BUILT FOR PHILIPPINE SUN"
- "YOUR EYES DESERVE BETTER"
- "VISION WITHOUT COMPROMISE"
- "DON'T JUST BLOCK. OWN."

Auto-generate new headlines that match this energy. Bold, confident, aspirational.

---

## 4 Layout Variants

### TYPE_COLLAGE

Multiple font sizes and weights layered together. Text at slight angles, overlapping. Product sits within the text layers on a dark surface. Editorial magazine-cover energy.

**Integration:** Product rests on a surface within the layered text -- text is behind, around, and partially overlapping the product. Everything arranged on the same surface under the same dramatic side light.

**Scene:** Deep black background with dramatic side lighting.

**Reference prompt (Outback Red, PASSED):**
"An editorial type collage composition on a deep black background. Bold white italic text at multiple sizes and slight angles layered together: large '[WORD 1]' in the upper portion and massive '[WORD 2]' overlapping below, both in the typeface from the font reference. ONE pair of [Product] sunglasses from DuberyMNL rests on a dark surface within the text layers -- real [finish] sunglasses matching the reference image, naturally integrated into the collage as if product and text were arranged together on the same surface. Everything lit by the same dramatic side light. Small 'DUBERY MNL' tucked in the lower area. DuberyMNL logo bottom-right. 4:5 aspect ratio, magazine cover energy."

### TEXTURE

Text painted/stenciled directly onto a real surface. Product hangs or rests on the same surface. Text and product share the same physical plane -- they exist in the same world.

**Integration:** The text IS part of the surface (painted, stenciled, graffiti). The product physically attaches to or rests on that same surface (hanging from nail, resting on ledge). Real shadows connect both.

**Scene:** Weathered concrete wall, brick wall, wooden fence -- real textured outdoor surface with natural daylight.

**Reference prompt (Bandits Glossy Black, PASSED):**
"A product photograph on a weathered dark concrete wall outdoors. Bold white italic text '[HEADLINE]' in the typeface from the font reference is painted as street art graffiti directly onto the concrete wall. ONE pair of [Product] sunglasses from DuberyMNL hangs from a rusty nail on the wall below the text -- real [finish] sunglasses matching the reference image, catching natural daylight, casting a real shadow on the concrete. The text and product share the same weathered wall surface. Warm afternoon sunlight from the right. Small 'DUBERY POLARIZED' stenciled on the wall below the sunglasses. DuberyMNL logo bottom-right. 4:5 aspect ratio, urban street photography feel."

### SPLIT_TEXT

Headline split into two halves -- top word above, bottom word below. A person wearing the sunglasses fills the space between, creating a sandwich. The person IS the divider.

**Integration:** The person wearing sunglasses physically occupies the space between the split text halves. Text above the head, text below the chin. Product is worn naturally on face.

**Scene:** Solid color background (warm dark red, deep navy, or charcoal). Studio portrait lighting.

**Reference prompt (Rasta Brown, PASSED):**
"A portrait photograph of a Filipino male wearing ONE pair of [Product] sunglasses from DuberyMNL -- real [finish] sunglasses matching the reference image, naturally on face. Solid [background color] background. Massive white bold italic text split by the subject: '[WORD 1]' above the person's head and '[WORD 2]' below the chin, both in the typeface from the font reference. The person wearing the sunglasses fills the space between the two text halves, creating a sandwich effect. Everything lit by the same soft studio light. Small 'DUBERY POLARIZED' at bottom. DuberyMNL logo bottom-right. 4:5 aspect ratio, high contrast."

**Background color guide:** Match to product tones. Cool lenses = deep navy. Warm lenses = dark red. Neutral = charcoal.

### KNOCKOUT

Solid brand color fills the canvas. Headline text is cut out (transparent) revealing a scene through the letterforms. Product rests on a real surface below the text.

**Integration:** Product sits on a real surface (wood, concrete) at the bottom of the frame, grounded by shadows and reflections. The knockout text is above. The product is NOT inside the letters -- it's below them on a physical surface.

**Scene:** Solid Dubery red (#E31E24) fill. Beach/tropical scene visible through letter cutouts. Real wooden or concrete surface at bottom for the product.

**Reference prompt (Bandits Green, PASSED):**
"A minimal knockout typography design. Solid Dubery red fills the entire canvas. Large bold italic knockout text '[HEADLINE]' in the center in the typeface from the font reference -- the letters are cut out to reveal a vivid Philippine beach scene through the letterforms with palm trees and turquoise water. Below the text, ONE pair of [Product] sunglasses from DuberyMNL rests on a real wooden surface that sits at the bottom of the frame -- real [finish] sunglasses matching the reference image with warm natural light reflections in the lens and a real shadow on the wood. The wood surface grounds the product in reality. DuberyMNL logo in white bottom-right. 4:5 aspect ratio, ultra-clean modern design."

---

## Input

```json
{
  "layout": "TYPE_COLLAGE",
  "product_ref": "Outback Red",
  "headline": "POLARIZED. ALWAYS.",
  "notes": "Optional direction"
}
```

- `layout`: TYPE_COLLAGE | TEXTURE | SPLIT_TEXT | KNOCKOUT (default: TYPE_COLLAGE)
- `product_ref`: product name from reference table
- `headline`: 3-5 words, or null to pick from headline bank
- `notes`: any specific direction

---

## JSON Output Schema

```json
{
  "task": "brand_bold",
  "layout": "TYPE_COLLAGE",

  "visual_mood": "1-2 sentence concept",

  "text_elements": [
    { "content": "TEXT", "role": "headline | subtitle", "position": "where", "size": "large | small" }
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

  "prompt": "Adapt from the reference prompt for the chosen layout",

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

Default logo: black bg. Use white bg for KNOCKOUT variant (red fill needs white logo).

---

## Self-Check

- [ ] Headline is 3-5 words (S2)
- [ ] Product integrates into composition, not floating (S3)
- [ ] Maximum 2 text elements (S4)
- [ ] Single reference angle (S5)
- [ ] "ONE pair" in prompt (S6)
- [ ] No sales language (S7)
- [ ] Font reference in image_input (S8)
- [ ] High contrast text (S9)
- [ ] Valid JSON, forward slashes, paths exist
- [ ] Prompt adapted from reference prompt for chosen layout

---

## Output Validation

- Valid JSON (no trailing commas, proper escaping)
- `prompt` field is a string
- `image_input` is an array of absolute paths that exist
- All paths use forward slashes

---

## Execution

1. Read input
2. Select layout variant (default TYPE_COLLAGE)
3. Resolve product ref to single image path
4. Pick or validate headline (must be 3-5 words)
5. Adapt the reference prompt for the chosen layout
6. Build JSON, run self-check
7. Save to `.tmp/BOLD-{id}_prompt.json`

---
name: dubery-brand-bold
description: Generate DuberyMNL bold statement images -- massive typography with product integration. 4 layout variants. Use when creating brand awareness posts with bold headlines, typographic designs, or statement pieces.
argument-hint: "layout product headline"
---

# DuberyMNL Bold Statement Generator

Generates structured JSON prompts for Gemini 3.1 Flash that produce bold typographic brand images.
Typography dominates. Product integrates INTO the text composition. Brand awareness -- no pricing.

---

## Layout Rules (fixed -- apply to every generation)

**S1 -- Typography Dominates**
Text occupies 40-60% of the canvas. This is the ONE format where text is bigger than the product.
The headline IS the design.

**S2 -- 3-5 Words Max**
Headlines must be 3-5 words. Not a sentence -- a statement.

**S3 -- Product Integrates, Not Floats**
The product must be part of the same composition as the text -- never floating separately.
Each layout variant defines HOW the product integrates. Follow the variant's integration method.

**S4 -- Maximum 2 Text Elements**
The headline statement + one small tagline ("DUBERY POLARIZED"). Nothing else.

**S5 -- One Pair Only**
Every prompt must include "ONE pair" to prevent duplicates.

**S6 -- No Sales Language**
BANNED: pricing, "ORDER NOW", "BUY NOW", "MESSAGE US", discount codes.

**S7 -- Typography Style**
All text uses the bold italic sporty typeface from the font reference image.
Font reference must always be in `image_input`.

**S8 -- High Contrast**
Text must be legible instantly on mobile. White text on dark bg, or dark text on light bg.

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
POSITION: [resting on surface / worn on face / held / displayed / hanging from].
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

## Headline Bank (use, adapt, or generate new -- always 3-5 words)

- "OWN THE SUN."
- "POLARIZED. ALWAYS."
- "SEE CLEAR."
- "STYLE THAT PROTECTS"
- "BUILT FOR PHILIPPINE SUN"
- "YOUR EYES DESERVE BETTER"
- "VISION WITHOUT COMPROMISE"
- "DON'T JUST BLOCK. OWN."
- "GLARE DOESN'T STAND A CHANCE."
- "BLOCK THE NOISE."
- "SHARPER THAN YESTERDAY."
- "MADE FOR THE GRIND."
- "EYES ON THE PRIZE."
- "NEVER SETTLE FOR LESS."
- "THE SUN MET ITS MATCH."
- "CLARITY IS CONFIDENCE."

Auto-generate new headlines that match this energy. Bold, confident, aspirational. Never reuse a headline within the same batch.

---

## 4 Layout Variants

**VARIETY RULE:** For every generation, randomly pick ONE option from each variety bank. Never repeat the same combo in a batch. The layout RULES are fixed -- only the creative execution changes.

### TYPE_COLLAGE

Multiple font sizes and weights layered together. Text at slight angles, overlapping. Product sits within the text layers on a surface. Editorial magazine-cover energy.

**Integration:** Product rests on a surface within the layered text -- text is behind, around, and partially overlapping the product. Everything arranged on the same surface under the same light source.

**Scene bank (pick one):**
- Deep black background with dramatic side lighting
- Dark navy background with cool blue rim light
- Dark emerald green background with warm gold accent light
- Charcoal textured background with overhead spotlight
- Deep burgundy background with warm tungsten side light

**Text color bank:** White (default), cream/off-white, pale gold

### TEXTURE

Text applied directly onto a real surface. Product hangs or rests on the same surface. Text and product share the same physical plane -- they exist in the same world.

**Integration:** The text IS part of the surface. The product physically attaches to or rests on that same surface. Real shadows connect both.

**Surface + treatment bank (pick one combo):**
- Weathered concrete wall + white spray-painted graffiti text
- Sun-bleached wooden fence + hand-painted brush stroke text
- Dark brick wall + white chalk text
- Wet asphalt after rain + reflective stenciled text
- Corrugated steel wall + bold white industrial stencil text
- Aged leather surface + embossed/debossed text
- Rusted metal door + white wheat-paste poster text
- Mossy stone wall + carved/etched text

**Product placement bank (pick one):**
- Hanging from a rusty nail
- Resting on a narrow ledge/shelf
- Propped against the surface at an angle
- Sitting on a small wooden bracket
- Balanced on a pipe or metal bar

**Lighting bank (pick one):**
- Warm afternoon sunlight from the right
- Harsh midday sun from above, deep shadows
- Overcast soft diffused daylight
- Golden hour light from the left, long shadows
- Cool morning light, slight blue tone

### SPLIT_TEXT

Headline split into two halves -- top word above, bottom word below. A person wearing the sunglasses fills the space between, creating a sandwich. The person IS the divider.

**Integration:** The person wearing sunglasses physically occupies the space between the split text halves. Text above the head, text below the chin. Product is worn naturally on face.

**Subject bank (pick one, alternate male/female across batch):**
- Filipino male, confident expression, clean-shaven, mid-20s
- Filipino female, bold expression, hair pulled back, mid-20s
- Filipino male, slight smirk, stubble, early 30s
- Filipino female, relaxed cool expression, loose hair, late 20s
- Filipino male, serious stare, sharp jawline, late 20s
- Filipino female, head slightly tilted, earrings visible, mid-20s

**Background color bank (pick one, match to product tones):**
- Warm dark red (#8B1A1A) -- for warm/amber lenses
- Deep navy (#1A1A3E) -- for blue/green cool lenses
- Charcoal (#2D2D2D) -- for neutral/black lenses
- Forest green (#1A3E1A) -- for green lenses
- Warm brown (#3E2A1A) -- for tortoise/brown lenses
- Muted gold (#3E3A1A) -- for amber/orange lenses

**Lighting bank (pick one):**
- Soft studio light from front-left
- Dramatic side light from the right, shadow on opposite cheek
- Ring light, even illumination, catch light in lenses
- Split lighting, half face lit, half in shadow
- Warm overhead light, slight shadow under brow

### KNOCKOUT

Solid color fills the canvas. Headline text is cut out (transparent) revealing a scene through the letterforms. Product rests on a real surface below the text.

**Integration:** Product sits on a real surface at the bottom of the frame, grounded by shadows and reflections. The knockout text is above. The product is NOT inside the letters -- it's below them on a physical surface.

**Fill color bank (pick one):**
- Dubery red (#E31E24)
- Deep black (#111111)
- Navy blue (#1A1A3E)
- Warm charcoal (#333333)
- Forest green (#1A3E1A)

**Scene through letters bank (pick one):**
- Philippine beach with palm trees and turquoise water
- Manila golden hour skyline
- Tropical jungle canopy with light rays
- Ocean waves crashing on rocks
- Mountain road with lush greenery
- Sunset clouds in orange and purple

**Product surface bank (pick one):**
- Real wooden surface (walnut, driftwood, bamboo)
- Concrete ledge
- Dark marble slab
- Leather surface
- Wet stone

---

## Prompt Construction

Build every prompt fresh from the layout rules + variety banks + fidelity rules. Do NOT copy templates.

**Structure -- PRODUCT FIRST:** The sunglasses are the anchor. Build the world around them, not the other way around.

1. **Open with the product** -- ONE pair of sunglasses, photographed in this scene, matching the reference. State where it sits and how light hits it.
2. **Build the surface/environment around it** -- the surface the product is on, the world behind it. Keep it simple -- let Gemini fill in natural details.
3. **Add typography** -- text that's part of the same world.
4. **Close with logo.**

5-8 sentences max. Shorter = more natural.

**Mandatory in every prompt:**
- "ONE pair of [Product Name] sunglasses from DuberyMNL" (S5)
- "a real pair photographed in this scene, matching the style shown in the reference image" (R2 -- this tells Gemini to RECREATE, not paste)
- Light source direction stated, product shares the same light
- Product casts real shadows onto the surface
- "All text uses the bold italic sporty typeface shown in the font reference image" (S7)
- "DuberyMNL logo matching the logo reference image" + position

**NEVER include in prompt:**
- Any word from the R2 banned list describing the product
- Any lens reflection description (R4)
- Sales language (S6)
- Over-described scenes (don't tell Gemini every crack and stain -- let it be natural)

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

  "visual_mood": "1-2 sentence concept -- describe scene and atmosphere, NOT the product",

  "text_elements": [
    { "content": "TEXT", "role": "headline | subtitle", "position": "where", "size": "large | small" }
  ],

  "product": {
    "models": ["Product Name"],
    "render_notes": "POSITION: ... ANGLE: ... LIGHTING: ... LOGO: ... REFERENCE: ...",
    "instruction": "Only ONE pair. As shown in the reference image."
  },

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

**RANDOMIZE ANGLE:** Do NOT always use -1.png. Randomly pick from available angles (-1, -2, -3, -4, -multi) per product. Vary across a batch so the feed looks diverse.

### Bandits

| product_ref | ref folder | finish |
|---|---|---|
| Bandits Glossy Black | `contents/assets/product-refs/bandits-glossy-black/` | glossy |
| Bandits Matte Black | `contents/assets/product-refs/bandits-matte-black/` | matte |
| Bandits Blue | `contents/assets/product-refs/bandits-blue/` | glossy |
| Bandits Green | `contents/assets/product-refs/bandits-green/` | glossy |
| Bandits Tortoise | `contents/assets/product-refs/bandits-tortoise/` | matte |

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

Default logo: black bg. Use white bg for KNOCKOUT variant (red fill needs white logo).

---

## Self-Check

- [ ] Headline is 3-5 words (S2)
- [ ] Product integrates into composition, not floating (S3)
- [ ] Maximum 2 text elements (S4)
- [ ] "ONE pair" in prompt (S5)
- [ ] No sales language (S6)
- [ ] Font reference in image_input (S7)
- [ ] High contrast text (S8)
- [ ] render_notes uses exact 5-field template (R3)
- [ ] No banned words from R2 in prompt or visual_mood
- [ ] No lens reflection descriptions (R4)
- [ ] "as shown in the reference image" for product (R2)
- [ ] Variety bank picks differ from other images in batch
- [ ] Prompt is original -- NOT copied from a template
- [ ] Valid JSON, forward slashes, paths exist

---

## Execution

1. Read input
2. Select layout variant (default TYPE_COLLAGE)
3. Resolve product ref to single image path (randomize angle)
4. Pick or generate headline (must be 3-5 words, no repeats in batch)
5. Pick random options from variety banks for the chosen layout
6. Write a fresh prompt following Prompt Construction rules and R2/R3/R4 fidelity
7. Build JSON, run self-check
8. Save to `contents/new/BOLD-{id}_prompt.json`

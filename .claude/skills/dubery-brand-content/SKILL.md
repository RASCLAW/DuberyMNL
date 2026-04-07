---
name: dubery-brand-content
description: Generate branded visual content for DuberyMNL -- infographics, feature callouts, bold statements, collection showcases, comparisons, lifestyle cards. Use when creating brand awareness posts, educational content about polarization, or product showcase graphics.
argument-hint: "scenario_type product topic"
---

# DuberyMNL Brand Content Generator

Generates structured JSON prompts for Gemini 3.1 Flash that produce branded visual content
for organic Facebook feed posts. This is brand awareness content -- no pricing, no sales CTAs.

---

## Non-Negotiable Rules

**B1 -- Dubery Branding**
Every image includes the DuberyMNL logo. Position varies by scenario but defaults to bottom-right.
The brand font reference image must always be passed as `image_input` so Gemini matches the typography.

**B2 -- No Sales Language**
This is awareness content, not ad creative.
BANNED: pricing (P699, P1200, any peso amount), "ORDER NOW", "MESSAGE US", "BUY NOW", "SHOP NOW", "DM us", discount codes.
ALLOWED CTAs: "Follow @DuberyMNL", "duberymnl.com", "Learn more"

**B3 -- Product Naturalism & Scene Integration**
Products must look like real photographed objects that belong in the scene -- not composited on top.
- Reference image guides appearance -- recreate, don't paste
- State material finish explicitly (glossy/matte)
- Products obey physics: real shadows, surface contact, natural positioning
- **Lighting match is mandatory:** prompt must state light direction, shadow angle, and color temperature -- and these MUST match between product and background/text
- Product and scene share the same ambient color cast (warm scene = warm highlights on product)
- Background color palette should complement the product's tones (cool bg for cool lenses, warm for warm)

**B4 -- Typography**
All text in the image should match the Dubery brand font style -- bold, italic, sporty.
Pass the font alphabet reference image and instruct Gemini: "All text uses the bold italic sporty
typeface shown in the font reference image."

**B5 -- Language**
English primary. Minimal Tagalog only when it adds authentic flavor.
Keep text short and punchy -- this is visual content, not an article.

**B6 -- Color Palette**
Primary: Red (#E31E24), Black (#1A1A1A), White (#FFFFFF).
Accent colors allowed for backgrounds and decorative elements, but brand colors dominate text and key elements.

---

## Input

```json
{
  "scenario_type": "FEATURE_CALLOUT",
  "product_refs": ["Outback Red"],
  "topic": "UV400 protection",
  "headline": null,
  "notes": "Optional direction from RA"
}
```

- `scenario_type`: one of the 6 types below
- `product_refs`: 1-4 products (use multiple for COLLECTION)
- `topic`: the educational or thematic angle
- `headline`: override headline text, or null to auto-generate
- `notes`: any specific direction

---

## Scenario Types

### FEATURE_CALLOUT

Product as hero with labeled feature callouts.

**Rules:**
- Product at ~60% canvas width, 3/4 angle, large enough to show detail at callout points
- 4-6 callouts max. Each label: 4-5 words max. One-line description underneath
- Thin arrows/lines connect labels to product -- never thick or colorful (they compete with product)
- Callouts radiate outward into clean space -- NEVER overlap the product
- **Product must sit on a real surface with real lighting** -- wooden table, concrete, leather, stone. Never a plain solid color background. Real surfaces give Gemini environment cues for reflections, shadows, and ambient color
- The lens should naturally reflect the environment it's in

**DO NOT:**
- Use more than 6 callouts (looks like a manual, not marketing)
- Use decorative fonts on labels (clean sans-serif / brand font only)
- Place callouts on top of the product
- Use a plain solid color background (products look CG without real environment lighting)
- Use a busy/cluttered background (callouts need clean space to read -- use simple surfaces)

**Feature bank** (pick 3-5 per image):
- Polarized lenses -- eliminates horizontal glare
- UV400 protection -- blocks 99.9% of harmful UV rays
- Lightweight frame -- all-day comfort
- Durable hinges -- built for daily use
- Dubery logo -- authentic branding on temple arm
- Anti-scratch coating -- lens longevity
- Flexible temples -- secure fit for active lifestyles

**Prompt pattern:** Describe a product photograph on a real surface (wood, concrete, leather) with real lighting (window light, natural sun). Product centered. State "only ONE pair of sunglasses" to prevent duplicates. Name each callout label and describe thin red arrows. Use `1.png` (3/4 front view) as the default reference angle for Bandits.

### EDUCATIONAL

Teaches something about sunglasses, eye health, or polarization. The product lens IS the teaching tool.

**Rules:**
- The Dubery lens should be the visual centerpiece of the diagram -- not a small product shot in the corner
- Split-view through the lens (glary scene on one side, clear on the other) is the proven format
- One big hook question as headline, visual demonstration in the middle, brand small at bottom
- Let the visual do 70% of the teaching. Text does 30%
- 3-4 short text lines total. If you need more text, the visual isn't doing its job
- Always connect the science to a benefit ("less eye strain on long drives")

**DO NOT:**
- Use jargon without visual support ("400nm wavelength" means nothing without a diagram)
- Put the product as a tiny afterthought in the corner
- Write paragraph-length explanations
- Forget the "so what" -- always end with why this matters to the viewer

**Topic bank:**
- How polarization works -- horizontal light waves vs vertical filter (lens as the filter in the diagram)
- UV400 explained -- the invisible danger, shown through the lens
- Why cheap sunglasses hurt your eyes -- pupil dilation behind dark non-UV lenses
- How to test if your sunglasses are polarized -- LCD screen trick
- Lens care basics -- cleaning, storage, what damages coatings

**Prompt pattern:** Describe an educational infographic where the Dubery sunglasses lens is the central visual element of the diagram. Light/glare flows toward the lens, the lens filters it, clean vision comes out the other side. Hook question headline at top. Short benefit statement at bottom.

### BOLD_STATEMENT

Typography dominates. Product integrated INTO the text composition -- not layered on top.

**Rules:**
- Headline: 3-5 WORDS MAXIMUM. Not a sentence -- a statement. "SEE DIFFERENT." not "Our sunglasses help you see better."
- Text occupies 40-60% of the canvas
- **Text-behind-product technique:** Large bold text extends behind the sunglasses, creating 3D depth. The product partially obscures some letters, proving product and text coexist in the same space
- Solid single-color background. The fewer elements competing, the stronger the impact
- High contrast mandatory: white text on dark bg, or dark text on light bg
- Maximum 2 text elements: the statement + one small tagline. Nothing else

**DO NOT:**
- Write a headline longer than 5 words
- Place the product floating separately from the text (this is the "pasted" look)
- Use more than one background color/gradient
- Add more than 2 text elements
- Use low contrast (text must be legible instantly on mobile)

**Headline bank** (use or adapt, always 3-5 words):
- "BUILT FOR PHILIPPINE SUN"
- "SEE CLEAR. LOOK SHARP."
- "YOUR EYES DESERVE BETTER"
- "POLARIZED. ALWAYS."
- "OWN THE SUN."
- "STYLE THAT PROTECTS"
- "VISION WITHOUT COMPROMISE"

**Prompt pattern:** Describe a studio composition where massive bold text and sunglasses are photographed together. The text is physically behind/around the product. Product partially obscures some letters. State that they share the same lighting setup. Solid background color that complements the product's lens tones.

### COLLECTION

Multiple products from a series showcased together. Clean studio catalog feel.

**Rules:**
- Maximum 3 products per row, 4-6 total in a 4:5 frame
- **Every product at the exact same angle and scale** -- inconsistent angles = amateur collage
- Equal spacing (gutters) between all products -- grid alignment is non-negotiable
- Arrange by color gradient: light to dark, or warm to cool for visual flow
- **"Hero + supporting cast"**: one product 30-40% larger in center/foreground, others arranged around it
- All products cast consistent shadows (same direction, same softness)

**DO NOT:**
- Mix product angles (some flat, some 3/4, some from above)
- Use unequal spacing between products
- Try to fit more than 4 products in a single 4:5 image
- Give all products equal visual weight (one must anchor the eye)

**Text:** Series name as header ("BANDITS SERIES", "THE OUTBACK LINE"). Optional one-line subtitle. Text occupies under 15% of image. Let the products speak.

**Prompt pattern:** Describe a studio flat lay or 3/4 product arrangement. State that ALL products are at the same angle. Name one as the hero (slightly larger or in foreground). Describe consistent overhead studio lighting with matching shadows. Dark background for premium feel.

### LIFESTYLE_CARD

Magazine-ad quality lifestyle photo with branded text overlay. The photo sells the emotion -- text is secondary.

**Rules:**
- The lifestyle photo does 80% of the work. It must sell aspiration BEFORE the text adds anything
- Product is WORN or IN-USE in the scene -- never floating beside the person
- Text anchored to natural negative space in the photo (sky, blurred background, water)
- Text in one corner or one third of the image -- never spanning the full width
- Apply consistent warm color grading across all lifestyle cards for brand recognition
- Semi-transparent gradient overlay allowed to create text-safe zone without killing the photo

**DO NOT:**
- Let text overlay obscure the person's face or the product (reduces engagement by 30%)
- Make text too large relative to the lifestyle image (looks like a flyer, not a magazine ad)
- Use a generic stock-photo feeling -- the scene must feel specific to the Philippines
- Place text without a legibility zone (dark overlay, sky, blurred area)

**Text:** 1 headline + brand tagline only. Headlines at 36-48pt equivalent. Total text covers under 20% of image.

**Prompt pattern:** Describe a golden-hour or vibrant Philippine outdoor scene first -- the photo is the foundation. Person wearing sunglasses naturally. Then describe text placement in the natural negative space area (sky, upper portion). State the warm/vibrant color grading. The text should feel like it was typeset into the photo, not dropped on top.

### COMPARISON

Split-view showing a clear visual difference. The sunglasses ARE the divider between before and after.

**Rules:**
- **The product IS the dividing element** -- sunglasses sit at the center split, the lens becomes the literal window to the "after" state
- The difference must be obvious at THUMBNAIL SIZE. If you need to explain it, it's too subtle
- The "before" side must clearly look worse: washed out, glary, uncomfortable squinting
- Both sides use the SAME scene -- only the one variable (polarization) changes
- Labels at TOP of each panel ("WITHOUT" / "WITH DUBERY"), not bottom
- Use a slight diagonal split instead of a straight vertical line (feels less clinical)

**DO NOT:**
- Make the difference too subtle (mobile users scroll fast)
- Use different scenes on each side (the comparison loses credibility)
- Add a decorative/busy divider element (distracts from the actual comparison)
- Put labels at the bottom (eye reads top-down)
- Separate the product from the split (product must BE the divider)

**Comparison topics:**
- Polarized vs non-polarized (beach/water glare is most dramatic)
- With Dubery vs squinting in sun
- Cheap sunglasses vs proper UV protection
- Naked eye vs polarized (road glare, water glare)

**Prompt pattern:** Describe a Philippine beach or water scene split diagonally. The Dubery sunglasses sit at the center of the split. Left side through naked eye: washed out, harsh glare, person squinting. Right side through the lens: vivid colors, clear water, relaxed expression. Labels at top of each half. The sunglasses physically bridge both halves.

---

## JSON Output Schema

```json
{
  "task": "brand_content",
  "scenario_type": "FEATURE_CALLOUT",

  "visual_mood": "1-2 sentence concept summary",

  "layout": {
    "composition": "Describe spatial arrangement -- where product sits, where text goes, background treatment",
    "text_hierarchy": "What's biggest, what's secondary, what's smallest",
    "background": "Solid color, gradient, lifestyle photo, or studio backdrop"
  },

  "text_elements": [
    {
      "content": "THE ACTUAL TEXT",
      "role": "headline | subtitle | label | cta | caption",
      "position": "top-center | bottom-right | etc.",
      "size": "large | medium | small"
    }
  ],

  "product": {
    "models": ["Model Name"],
    "finish": "glossy | matte",
    "placement": "Where and how the product appears in the composition",
    "instruction": "The sunglasses should look like a real pair photographed in this scene -- matching the style shown in the reference image. Not a digital composite or 3D render."
  },

  "brand": {
    "logo_position": "bottom-right | top-left | etc.",
    "color_scheme": "Describe the color treatment for this specific image"
  },

  "prompt": "The full text prompt for Gemini. See prompt construction rules below.",

  "image_input": [
    "C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/[product].png",
    "C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/fonts/DUBERY-FONTS.png",
    "C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/dubery-logo.jpg"
  ],

  "api_parameters": {
    "aspect_ratio": "4:5",
    "resolution": "2K",
    "output_format": "jpg"
  }
}
```

**Schema notes:**
- `text_elements`: list every piece of text that should appear in the image
- `image_input`: always include product ref + font alphabet + logo. For COLLECTION, include multiple product refs
- `api_parameters.aspect_ratio`: default 4:5 for feed posts. Use 9:16 for Stories if specified
- For COLLECTION with 2-4 products, include all product variant images in `image_input`

---

## Prompt Construction

The `prompt` field is what Gemini actually receives. Each scenario type has a **prompt pattern**
described in its section above -- follow that pattern, not a generic template.

**Universal rules for all prompts:**

1. **Scene-first** -- Open by describing the overall scene/composition as a single photographed setup
2. **Typography** -- "All text uses the bold italic sporty typeface shown in the font reference image"
3. **Exact text content** -- State every word that appears and its position
4. **Product integration** -- Describe how the product exists IN the scene with matching lighting: "lit by the same [direction] light as the background, casting [shadow description]"
5. **Logo** -- "DuberyMNL logo (matching the logo reference image) in the [position]"

**Anti-paste rules (include in every prompt):**
- "Everything in this image is part of one cohesive studio/scene photograph"
- State the light source direction and confirm product shares it
- Describe product shadows falling onto nearby elements (surface, text, background)
- Never say "overlapping" or "on top of" -- say "in front of" or "positioned within"

**Keep it to 5-8 sentences.** Concise spatial instructions > long descriptions.

**Aspect ratio:** Default 4:5 (Facebook feed, 1080x1350). Use 9:16 only for Stories.

---

## Cross-Format Rules

These apply to ALL scenario types:

- **Real environments only:** Products must exist in real environments with real surfaces and real lighting. Plain solid color backgrounds make products look like CG renders. Even "studio" shots need a real surface (wood, concrete, leather, stone) so the product has something to interact with -- reflections in the lens, ambient color cast, contact shadows
- **20% text rule:** Facebook penalizes heavy text overlay in organic reach. Keep text under 20% of image area for all formats EXCEPT Bold Statement
- **Mobile-first sizing:** All text must be legible at phone-screen size. Minimum 24pt equivalent for body, 36pt for headlines, 48pt+ for hero statements
- **Brand consistency:** Same font style, same logo position (default bottom-right), same red accent color across all formats. When users scroll the feed, they recognize Dubery before reading a word
- **4:5 is king:** 1080x1350px takes maximum screen real estate on mobile Facebook feed

---

## Product Reference Table

**Bandits series** have multi-angle reference photos (4 angles each). Pass only ONE -- the angle that matches the composition.
**Outback + Rasta** only have single variant PNGs for now.

### Bandits (pick ONE angle per image)

| product_ref | ref folder | finish |
|---|---|---|
| Bandits Glossy Black | `C:/Users/RAS/Documents/PRODUCT REF/bandits-glossy-black/` | glossy |
| Bandits Matte Black | `C:/Users/RAS/Documents/PRODUCT REF/bandits-matte-black/` | matte |
| Bandits Blue | `C:/Users/RAS/Documents/PRODUCT REF/bandits-blue/` | glossy |
| Bandits Green | `C:/Users/RAS/Documents/PRODUCT REF/bandits-green/` | glossy |
| Bandits Tortoise | `C:/Users/RAS/Documents/PRODUCT REF/bandits-tortoise/` | matte |

**Angle guide -- pick the one that fits:**
- `1.png` -- 3/4 front view (best for: feature callout, bold statement, lifestyle)
- `2.png` -- multi-angle strip (best for: collection, technical)
- `3.png` -- detail closeups: lens, hinge, temple art (best for: feature callout needing arm detail)
- `4.png` -- technical diagram with dimensions (best for: educational)

**Never pass multiple angles** -- Gemini interprets them as multiple sunglasses in the scene.

### Outback + Rasta (single variant -- use as-is until better refs available)

| product_ref | image_input path | finish |
|---|---|---|
| Outback Black | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/outback-black.png` | matte |
| Outback Blue | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/outback-blue.png` | matte |
| Outback Green | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/outback-green.png` | matte |
| Outback Red | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/outback-red.png` | matte |
| Rasta Brown | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/rasta-brown.png` | matte |
| Rasta Red | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/rasta-red.png` | matte |

---

## Brand Asset Paths

| Asset | Path |
|---|---|
| Font alphabet | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/fonts/DUBERY-FONTS.png` |
| Logo (black bg) | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/dubery-logo.jpg` |
| Logo (white bg) | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/dubery-logo.png` |
| Logo (MNL variant) | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/logo-new-2.png` |
| Packaging | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/dubery-packaging.png` |

Use the black bg logo (dubery-logo.jpg) as default `image_input`. Use white bg version when the
image background is dark.

---

## Self-Check (Before Saving)

- [ ] No banned sales language (B2) -- no pricing, no "ORDER NOW", no "BUY NOW"
- [ ] Product naturalism (B3) -- real photographed object language, finish stated
- [ ] Font reference in image_input (B4)
- [ ] English primary, minimal Tagalog (B5)
- [ ] Brand colors dominant (B6)
- [ ] DuberyMNL logo included (B1)
- [ ] Prompt is 4-7 sentences, spatially specific
- [ ] text_elements lists every piece of text in the image
- [ ] Layout clearly describes composition
- [ ] Appropriate scenario type for the topic

---

## Output Validation

The saved JSON file must be parseable by `generate_vertex.py`. This means:
- Valid JSON (no trailing commas, no comments, proper escaping)
- `prompt` field is a string (the text Gemini receives)
- `image_input` field is an array of absolute file paths that exist on disk
- All paths use forward slashes: `C:/Users/RAS/projects/...`
- Verify the JSON parses cleanly before saving: mentally validate brackets, quotes, commas

**The JSON is the deliverable.** If it's malformed, the pipeline breaks.

---

## Execution

1. Read input (from arguments or conversation)
2. Select scenario type and resolve product refs
3. Generate headline if not provided
4. Build the structured JSON
5. Write the prompt following the construction order
6. Run self-check + validate JSON structure
7. Save to `.tmp/BRAND-{id}_prompt.json`

Process one at a time. Save immediately after each.

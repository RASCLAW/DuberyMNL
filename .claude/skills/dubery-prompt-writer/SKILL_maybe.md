---
name: dubery-prompt-writer
description: Use when writing a DuberyMNL image prompt, composing a Nano Banana 2 prompt for an approved caption, or running WF2 image generation.
disable-model-invocation: true
---

# DuberyMNL Image Prompt Writer (WF2)

## Trigger
Used internally during WF2 image generation. For each APPROVED caption, Claude Code applies this skill to compose the NB2 prompt before calling generate_kie.py.

## Role

World-class Facebook ad creative director specializing in mobile-first visual storytelling for Filipino consumer brands. Job: take one approved marketing caption and transform it into a complete, highly detailed image generation prompt for Nano Banana 2 (kie.ai).

The prompt will be sent to Nano Banana 2 to generate a photo-realistic ad image. Brand overlays (price, logo, tagline) are rendered directly in the generated image — NB2 handles all of it.

---

## Reference Image Map

When composing prompts, pass the matching Drive URL as `image_input` to the kie.ai API. The model uses this as product reference.

```
classicblack:  https://drive.google.com/uc?export=view&id=1K3KbbiPDY4puYY66XKa4gUzILlZzfTtT
classicblue:   https://drive.google.com/uc?export=view&id=1i1Zt5ufXkmikG0_xal5aNOQVdWVf8OpF
classicred:    https://drive.google.com/uc?export=view&id=1VQ5RSAF5NWNncwbaTHbFT65p-Fo9V2us
classicpurple: https://drive.google.com/uc?export=view&id=1rdZQymdtr-5C9Bi__s9m9nKvDPqiIWQR
outbackblack:  https://drive.google.com/uc?export=view&id=1Oo8a--aJW59XuJg6JmeHIzyReFPFYuMr
outbackblue:   https://drive.google.com/uc?export=view&id=1FW14Bo2NKpI49TcNEwbfd6FlCXwNzyTZ
outbackgreen:  https://drive.google.com/uc?export=view&id=1FLwh2S3M2g5DWjw0d0ox8Nwu0YFjD9mg
outbackred:    https://drive.google.com/uc?export=view&id=1lP0SBZYq3VUkZ26Tvl0v1zSU0ww_XIlJ
banditsblack:  https://drive.google.com/uc?export=view&id=1bZo8Wa_urThqSceTsO76FyGaEgiKCIRz
banditsblue:   https://drive.google.com/uc?export=view&id=1z1xi59K6YeHVzM6Qfr_7VS2plVg2bgth
banditscamo:   https://drive.google.com/uc?export=view&id=1wHsYsspQJlwEk0mBN3C0mWE3OmPYaw_F
banditsgreen:  https://drive.google.com/uc?export=view&id=11AmEBk_4SSh_wL9fQaC_FiTjnVCdgj3L
rastared:      https://drive.google.com/uc?export=view&id=1zFdvD2l82rqFPb2Ia9kh3nqqPyqj97eK
rastabrown:    https://drive.google.com/uc?export=view&id=18hihO0qIECpVYUutLVtpj8wfZJSIbTmK
```

Key lookup: normalize `Recommended_Products` field → lowercase, remove spaces/dashes/underscores.
Example: `"CLASSIC - Blue"` → `classicblue`

Multiple products = multiple URLs in `image_input` array.

---

## Step 1 — Caption Analysis (Internal Reasoning)

Run all five steps silently. Use the output to drive every visual decision in Step 2.

**1. Pain Point (The Hook)**
What physical or emotional discomfort does this caption agitate?
→ Becomes: the visual hook — expression, lighting, scene tension.

**2. Relevance & Urgency (The Context)**
What modern or localized context does the caption set? What cultural tone does it strike?
→ Becomes: scene tone, composition style, cultural grounding.

**3. Product Proof (The Desire)**
What technical or lifestyle claim needs to be SHOWN, not told?
→ Becomes: a specific visual proof element (e.g., sharp skyline reflected in polarized lens).

**4. Friction Removal (The Close)**
What facts convert a scroller into a buyer?
→ Becomes: graphic overlays — price, delivery, CTA energy.

Map to AIDA:
- Attention → Pain point / visual hook
- Interest → Local vibe, cultural tone, composition
- Desire → Visual proof of product benefit
- Action → ₱699, same-day delivery, DUBERY as overlays

**Angle inheritance rule:** The `Angle` field from WF1 is authoritative for persuasion strategy. Do not re-derive it from the caption. Use it to set scene energy and overlay tone:
- Pain Relief → tense scene, harsh or glaring light, product as the visual relief
- Identity → confident subject, aspirational setting, elevated composition
- Lifestyle → loose, natural, scene-forward, product integrated organically
- Status / Glow Up → elevated location, polished composition, premium feel
- Value / Deal → price badge is the hero, urgent overlay energy
- Convenience / Fast Delivery → motion or commute context, delivery info prominent

**5. Content Type Selection**
Based on analysis + `Visual_Anchor` field, select ONE content type.

**Batch composition target: 60% PRODUCT / 40% PERSON**
Across the full ad set, lean toward PRODUCT-anchored content types. When Visual_Anchor=PERSON and the caption can reasonably support a product-led execution, consider TYPE B/D over TYPE A. Person-led shots are reserved for captions where the human experience IS the hook and cannot be separated from it.

**Visual_Anchor enforcement (hard rule):**
- `PRODUCT` → must select TYPE B, C, D, or E. TYPE A is forbidden.
- `PRODUCT` + ambiguous caption → default to TYPE D.
- `PERSON` → all types available; TYPE A only when the human experience is the undeniable hook.

| Type | When to use |
|---|---|
| TYPE A — PERSON + PRODUCT | Caption agitates human pain/experience. Person is visual anchor. Product worn or held. Full overlay treatment. |
| TYPE B — PRODUCT IN ENVIRONMENT | Caption is context-setting or lifestyle-driven. Product placed in real-world setting. Minimal overlays. |
| TYPE C — PRODUCT LIFESTYLE MINIMAL | Caption is aspirational/vibe-based. Product in scenic backdrop. Brand name + one tagline. |
| TYPE D — PRODUCT HERO AD | Caption focuses on specific benefit/feature. Product in environment with visual proof (e.g., lens reflection). Full overlays. |
| TYPE E — INFOGRAPHIC | Caption lists/describes multiple product features. Callout arrows point to specific parts. DUBERY logo + price badge. |

---

## Step 2 — Write the Prompt

Write in plain text, labeled sections. **Not JSON. Not a template.** Every word must trace back to the caption analysis — nothing is arbitrary.

**Product primacy rule (applies to all types):**
The product is always the visual hero. The scene exists to serve the product — not the other way around. When in doubt, ask: "Is the product the first thing the eye lands on?" If no, the scene is too dominant. Keep environment detail sparse enough that NB2 allocates most of its rendering attention to the product. A detailed scene with a small product is a failure. A simple scene with a sharp, accurate product is a win.

### Required Sections

**SCENE:**
Full detail. Where, what time of day, atmosphere, light quality. Ground the scene in a specific Metro Manila or Philippine environment — no generic stock-photo locations. No stock-photo feel.

- TYPE A: environment frames the human subject
- TYPE B/C: environment IS the visual story
- TYPE D: environment is reflected in the lens
- TYPE E: clean, uncluttered backdrop

Setting rule: sunglasses are outdoor products.
- Default: outdoors — streets, markets, roads, parks, beaches, mountains. Use specific PH locations when relevant (España, Quezon Ave, SM North, Baguio, Mayon, Ilocos, etc.)
- Indoor allowed only for PRODUCT-anchored shots (TYPE B, C, D, E): retail store, optical shop, studio, gym, café.
- NEVER place a person wearing sunglasses in a casual indoor home setting (living room, bedroom, kitchen). That's not where sunglasses are worn.

Format rule (always include verbatim at the end of the SCENE section):
> "Vertical portrait format, 4:5 aspect ratio, optimized for mobile feed. Compose the scene top-to-bottom, not left-to-right. Subject and key elements fill the vertical frame."

---

**PRODUCT INSTRUCTION:**
Always include verbatim:

> "This ad MUST feature the exact style, frame shape, material, and lens color of the sunglasses shown in the [User-Provided Reference Image]. The Dubery logo must match the logo style and placement shown in the reference image. The reference image is the ground truth — render the product as a photographic exact match. The scene is background context. It must never distort, abstract, or stylize the product. A perfect product in an average scene is correct. A beautiful scene with an inaccurate product is not. Do not alter the product in any way."

For multiple products (Recommended_Products has 2+):
- Check if all share the same base family (all "classic*" → CLASSIC SERIES)
  - Same family: frame as Series shot — all color variants arranged together, named "DUBERY [FAMILY] SERIES"
  - Mixed families: describe each product individually, arrange as curated flat-lay or group display
- PERSON anchor + multiple products: describe N subjects, each wearing their respective model
- PRODUCT anchor + multiple products: apply Series or mixed display logic above

---

**SUBJECTS:** *(TYPE A only — omit for product-only types)*
Describe: subject(s), expression, emotion, body language, action, how the product is worn, lighting per area, composition, visual proof element.

**Product Visibility Rule:** If the shot is 3/4 body or full body (roughly 60% or more of the body visible), include a floating product bubble beside the ₱699/POLARIZED cluster. The bubble must be a freshly rendered close-up of the sunglasses — NOT a copy or paste of the reference photo. NB2 must render it as a clean, well-lit product shot: slight 3/4 angle or front-facing, frame shape fully visible, Dubery logo on the temple arm clearly legible. No white background, no colored background — the bubble blends seamlessly into the ad with a subtle dark shadow or soft glow border only. The reference image is the style guide for accuracy, not the image to reproduce inside the bubble.

For multi-subject (2+ products, PERSON anchor):
- Subject 1 → wears Reference Image 1 model, Subject 2 → wears Reference Image 2 model, etc.
- Describe group composition, interactions, each person's expression, each sunglass model distinctly visible.

---

**BRANDING:**
- DUBERY logo placement, style, color (red, top right corner or bottom left)
- Match vibe energy — bold and urgent for Sale, clean and minimal for Lifestyle

---

**TEXT OVERLAYS:**

Accuracy rule: Fixed strings must be spelled exactly, verbatim, every time:
```
₱699  |  POLARIZED  |  DUBERY  |  SAME-DAY DELIVERY  |  METRO MANILA
```

**Language rule:**
- Overlay text is primarily English -- professional, clean, broadly readable
- Taglish is allowed when it adds cultural punch (e.g. "Para sa mga bold enough.")
- Pure Tagalog headlines are rarely used -- only when the caption energy demands it and nothing else fits
- NEVER default to Tagalog just because the caption is in Tagalog -- the overlay and caption are separate layers

**Headline rule:**
- Headlines must NOT restate the caption -- they are a separate layer with their own voice
- Think billboard copy: short, punchy, provocative, benefit-driven, or curiosity-driven
- The headline stops the scroll. The caption closes the sale. They work together, not in parallel.
- Bad: "Walang Plano." (just repeating the caption)
- Good: "Built for the Unbothered." / "Shade That Hits Different." / "The Only Thing That's Sure."
- Max 5 words. No period needed unless it adds punch.

Dynamic rule: visual style, placement, font, color, shape — all creative and unique per concept. No two ads look the same.

**Color rule:**
Do NOT default all overlays to white. Overlay colors must be drawn from the scene, product palette, and vibe energy of the caption. White is one option — not the default. Each ad should have its own color logic: a warm scene may use amber or gold accents; a dark urban scene may use electric blue or red; a lifestyle shot may use muted earthy tones. The goal is visual variety across the ad set and internal coherence within each ad.

**Bottom-right clear zone rule (required on every ad, all types):**
The bottom-right corner of the frame must always be kept completely clear. No text, badges, logos, or overlays of any kind in the bottom-right quadrant. This ensures the kie.ai platform watermark lands in clean background space and never conflicts with ad content.

Instruct NB2: "Render all text with sharp, clean, fully legible letterforms. Blurred or distorted text is not acceptable."

**Auto-always overlays (every ad, every type — no exceptions):**
- DUBERY logo
- POLARIZED badge
- COD badge
- SAME-DAY DELIVERY + METRO MANILA
- CTA (e.g. "Message Us", "Order Now", "DM for Orders" — match the caption energy)
- One courier logo, randomly selected per ad: Lalamove / GrabExpress / Move It

**Auto-conditional overlays (included when applicable):**
- Deal badge (₱1,200 / 2 pairs or equivalent) — auto-include when Recommended_Products has 2+ items
- Series label (e.g. "OUTBACK SERIES", "BANDITS SERIES") — auto-include when all Recommended_Products share the same base family

**Checkbox-driven overlays (from Overlays field in sheet):**
- `headline` → include a headline (English or Taglish, scroll-stopping, NOT a restatement of the caption. Max 5 words.)
- `price` → include ₱699 price display (prominent)
- `bubble` → PERSON anchor only — floating product close-up beside ₱699/POLARIZED cluster
- `accessories` → PRODUCT anchor only — add Dubery_Packaging.png to image_input
- `other:...` → include as described

No body copy on any ad type.

**Required overlays by type:**

TYPE A — Full treatment:
- All auto-always overlays
- Price display (prominent) — if `price` checked
- Product bubble — if `bubble` checked (3/4 or full body shots)
- Headline — if `headline` checked

TYPE B — Minimal:
- All auto-always overlays
- Headline — if `headline` checked

TYPE C — Minimal:
- All auto-always overlays
- Headline — if `headline` checked

TYPE D — Full treatment:
- All auto-always overlays
- Price display (prominent) — if `price` checked
- Headline — if `headline` checked

TYPE E — Feature callouts:
- All auto-always overlays
- Each product feature from the caption as a callout label with arrow pointing to relevant part
- Price display (prominent) — if `price` checked

For each overlay: describe visual treatment, position in frame, how it connects to the concept.

---

**OBJECTS IN SCENE:** *(optional but recommended)*
List specific physical objects present — props, environment details, background elements. Makes NB2 output more grounded.

---

## Reflection Rule (TYPE A and TYPE D)

The lens reflection must mirror the ACTUAL environment described in the scene:
- Market scene → reflect market stalls, vendors, crowd
- Park → reflect trees, sky, open field
- Beach → reflect waves, horizon, sand
- Road/commute → reflect traffic, sky, road
- NEVER default to BGC towers or Makati skyline unless the scene is explicitly set there

The reflection is visual proof that the lenses are polarized — it must be scene-specific and immersive.

---

## Inputs from captions sheet (per row)

WF2 reads these fields from `.tmp/captions.json` for each entry with `status=APPROVED`:
- `Caption` — the approved caption text
- `Angle` — the persuasion strategy selected by WF1 (Pain Relief, Identity, Lifestyle, Status/Glow Up, Value/Deal, Convenience/Fast Delivery) — use this to anchor scene energy and overlay tone
- `Vibe` — scene/lifestyle context
- `Visual_Anchor` — PERSON or PRODUCT (drives content type selection)
- `Notes` — RA's image direction brief (scene concept, setting, mood) — use this to shape the scene
- `Recommended_Products` — determines which reference image URLs to pass as `image_input`
- `Overlays` — comma-separated list of checked overlays from review: `headline`, `price`, `bubble` (PERSON only), `accessories` (PRODUCT only), `other:...`

**Fixed overlays always included (regardless of overlays field):** DUBERY logo, POLARIZED, SAME-DAY DELIVERY, COD, CTA, one courier (random: Lalamove / GrabExpress / Move It)

**Auto-conditional:** Deal badge when recommended_products has 2+ items. Series label when all products share the same base family.

**Accessories overlay:** if `accessories` is checked, add `Dubery_Packaging.png` to `image_input`:
`https://drive.google.com/uc?export=view&id=1QYLxQSJzZ4v3Uf518Y_qPpADD4J1WXAm`

---

## Output

Plain text prompt only. No preamble, no explanation, no meta-commentary. Begin directly with `SCENE:`.

**WF2 Phase 1 — Prompt generation (stops here):**
1. Write the plain text prompt to `.tmp/captions.json` → `prompt` field for the caption's row.
2. Run `dubery-prompt-parser` on the prompt to produce structured JSON.
3. Save the structured JSON output to `.tmp/[id]_prompt_structured.json`.
4. Update Status → `PROMPT_READY` only after both files are written.
Do NOT run `generate_kie.py`. RA reads prompts and tests in Gemini first.

**WF2 Phase 2 — Image generation (separate trigger: "generate images"):**
Read all `PROMPT_READY` rows from captions sheet.
For each: run `generate_kie.py` → `upload_image.py` → write Drive URL to column L (Image_URL) → Status → `DONE`.

The prompt JSON (for Phase 2) is structured as:
```json
{
  "prompt": "[the full plain text prompt here]",
  "image_input": ["[reference image URL(s)]"],
  "api_parameters": {
    "aspect_ratio": "4:5",
    "resolution": "1K",
    "output_format": "jpg"
  }
}
```

---

## Quality Benchmark

A strong output leaves zero ambiguity. Every element described: what it looks like, where it is, how the light behaves, what the person is feeling (if applicable), and how every overlay is styled and positioned. The entire prompt traces directly back to the caption analysis — nothing is arbitrary.

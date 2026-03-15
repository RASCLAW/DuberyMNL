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

**1. Angle**
Read the `angle` field from WF1. Do not re-derive it. Map it directly to visual energy:
- Pain Relief → tense scene, harsh or glaring light, product as the visual relief
- Identity → confident subject, aspirational setting, elevated composition
- Lifestyle → loose, natural, scene-forward, product integrated organically
- Status / Glow Up → elevated location, polished composition, premium feel
- Value / Deal → price badge is the hero, urgent overlay energy
- Convenience / Fast Delivery → motion or commute context, delivery info prominent
→ Becomes: the visual mood, scene tension, and overlay energy for the entire ad. (AIDA: Attention)

**2. Context**
What specific PH cultural or local grounding fits this vibe and angle?
→ Becomes: scene tone, composition style, exact location, cultural grounding. (AIDA: Interest)

**3. Proof**
What product benefit needs to be SHOWN visually, not told?
→ Becomes: a specific visual proof element (e.g., traffic reflected in polarized lens, product sharp against a blurred crowd). (AIDA: Desire)

**4. Friction**
What overlay elements will convert this specific scroller?
→ Becomes: which badges, price display, CTA, and delivery info to emphasize and how urgently. (AIDA: Action)

Map to AIDA:
- Attention → Angle / visual mood and scene energy
- Interest → Local vibe, cultural tone, composition
- Desire → Visual proof of product benefit
- Action → ₱699, same-day delivery, DUBERY as overlays

**5. Content Type Selection**
Based on the four answers above + `visual_anchor` field, select ONE content type.

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

Scene description: 3 sentences maximum. Every extra sentence about the background is rendering budget taken from the product.

Overlay zone rule: Overlays live at the top and bottom of the frame only — never mid-frame. The center is the product's space. Top zone: headline and DUBERY logo. Bottom zone: all conversion info (price, delivery, POLARIZED, COD, CTA) consolidated into one compact cluster. Compact means small pills and thin strips — not full-width panels spanning the center.

### Required Sections

**CONTENT TYPE:** `[TYPE — NAME. Brief visual mood and scene concept — 1 sentence.]`

---

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

> "This ad MUST feature the exact style, frame shape, material, and lens color of the sunglasses shown in the [User-Provided Reference Image]. The Dubery logo must match the logo style and placement shown in the reference image. The reference image is the ground truth — render the product as a photographic exact match. The scene is background context. It must never distort, abstract, or stylize the product. A perfect product in an average scene is correct. A beautiful scene with an inaccurate product is not. Do not alter the product in any way. Do NOT distort, warp, bend, or tilt the product to expose the logo. Natural product position takes priority. If the logo is partially obscured by the product's resting angle, that is acceptable."

For multiple products (Recommended_Products has 2+):
- Check if all share the same base family (all "classic*" → CLASSIC SERIES)
  - Same family: frame as Series shot — all color variants arranged together, named "DUBERY [FAMILY] SERIES"
  - Mixed families: describe each product individually, arrange as curated flat-lay or group display
- PERSON anchor + multiple products: describe N subjects, each wearing their respective model
- PRODUCT anchor + multiple products: apply Series or mixed display logic above

---

**SUBJECTS:** *(TYPE A only — omit for product-only types)*
Describe: subject(s), expression, emotion, body language, action, how the product is worn, lighting per area, composition, visual proof element.

For multi-subject (2+ products, PERSON anchor):
- Subject 1 → wears Reference Image 1 model, Subject 2 → wears Reference Image 2 model, etc.
- Describe group composition, interactions, each person's expression, each sunglass model distinctly visible.

---

**BRANDING:**
- DUBERY logo placement, style, color (typically white, top right corner or bottom left)
- Match vibe energy — bold and urgent for Sale, clean and minimal for Lifestyle

---

**TEXT OVERLAYS:**

Accuracy rule: Fixed strings must be spelled exactly, verbatim, every time:
```
₱699  |  POLARIZED  |  DUBERY  |  FREE SAME-DAY DELIVERY  |  METRO MANILA
```

Dynamic text (headlines, body copy, taglines): spelling must be accurate and directly from the caption. No filler.

Dynamic rule: visual style, placement, font, color, shape — all creative and unique per concept. No two ads look the same.

**Language rule:**
- Overlay text is primarily English — professional, clean, broadly readable
- Taglish is allowed when it adds cultural punch (e.g. "Para sa mga bold enough.")
- Pure Tagalog headlines are rarely used — only when the caption energy demands it and nothing else fits
- NEVER default to Tagalog just because the caption is in Tagalog — the overlay and caption are separate layers

**Headline rule:**
- Headlines must NOT restate the caption — they are a separate layer with their own voice
- Think billboard copy: short, punchy, provocative, benefit-driven, or curiosity-driven
- The headline stops the scroll. The caption closes the sale. They work together, not in parallel.
- Max 5 words. No period needed unless it adds punch.
- Test: would a stranger immediately understand what's being offered? Punchy AND clear beats clever AND confusing.

**Bottom-right clear zone (required on every ad, all types):**
The bottom-right corner of the frame must always be kept completely clear. No text, badges, logos, or overlays of any kind in the bottom-right quadrant. The entire bottom overlay row (bubble, price, POLARIZED, COD, CTA) must stay within the LEFT HALF of the bottom zone — nothing crosses the vertical center line of the frame. This ensures the kie.ai platform watermark lands in clean background space and never conflicts with ad content.

Instruct NB2: "Render all text with sharp, clean, fully legible letterforms. Blurred or distorted text is not acceptable."

**No unspecified elements:** Do NOT render any decorative icons, symbols, graphic embellishments, or UI elements not explicitly named in this prompt. Every visual element must be specified.

**Required overlays by type:**

TYPE A — Full treatment:
- ₱699 price display (prominent)
- POLARIZED label
- Same-Day Delivery + Metro Manila
- DUBERY logo
- Headline derived from caption hook
- Body copy derived from caption voice

TYPE B — Minimal:
- DUBERY logo
- One short tagline relevant to the caption

TYPE C — Minimal:
- DUBERY brand name (prominent)
- One strong tagline relevant to the caption

TYPE D — Full treatment:
- ₱699 price display (prominent)
- POLARIZED label
- Same-Day Delivery + Metro Manila
- DUBERY logo
- Bold headline derived from caption
- Supporting line derived from caption

TYPE E — Feature callouts:
- Each product feature from the caption as a callout label with arrow pointing to relevant part
- DUBERY logo
- ₱699 price badge

**Auto-always overlays (every ad, every type — no exceptions):**
- COD badge — always group with the price badge or delivery strip. Never isolated. It belongs in the transaction information cluster.
- CTA (e.g. "Message Us", "Order Now", "DM for Orders" — match the caption energy)

**Auto-conditional overlays (included when applicable):**
- Deal badge (₱1,200 / 2 pairs) — when `recommended_products` has 2+ items
- Series label (e.g. "OUTBACK SERIES", "BANDITS SERIES") — when all `recommended_products` share the same base family

**Checkbox-driven overlays (from `overlays` field in captions.json):**
- `headline` → include a scroll-stopping headline (English or Taglish, NOT a restatement of the caption, max 5 words)
- `price` → include ₱699 price display (prominent)
- `bubble` → a circular crop lifted directly from the main ad image — a magnified section of the product as it appears in the scene, showing the frame shape, lens detail, finish, and Dubery logo up close. Looks like a zoom circle punched out of the photo itself. Thin white border, subtle drop shadow. Roughly fist-sized. Bottom zone, leftmost element in the compact row, left half of the frame only. (PERSON anchor only — RA sets this at review)
- `accessories` → add `Dubery_Packaging.png` to `image_input` so NB2 renders the full accessory set (pouch, cloth, box) alongside the sunglasses
  URL: `https://drive.google.com/uc?export=view&id=1QYLxQSJzZ4v3Uf518Y_qPpADD4J1WXAm`
- `other:...` → include as described

For each overlay, describe all of the following: shape (pill, capsule, tag, strip, panel), background color MUST be derived from the scene's dominant tones — dark environment colors, product tones, or ambient light. Never plain white. White is reserved for text only, not backgrounds., text color and weight, position within the overlay zone (top zone: headline/logo; bottom zone: conversion cluster — never mid-frame), and how it connects to the concept. Visual style, placement, font, color, shape — all creative and unique per concept. No two ads look the same.

When the caption angle is Convenience / Fast Delivery, SAME-DAY DELIVERY is the primary conversion message — give it the largest overlay after the headline. It is not a supporting detail.

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
Lens darkness governs reflection intensity: light or amber lenses → visible scene reflection; dark or smoky lenses (e.g. Bandits Glossy Black) → subtle, muted reflection only. Never show a vivid mirror reflection on dark lenses — it looks unnatural.

---

## Inputs (per entry from .tmp/captions.json)

WF2 reads these fields for each entry with `status=APPROVED`:
- `caption_text` — the approved caption text
- `angle` — persuasion strategy from WF1 (Pain Relief, Identity, Lifestyle, Status/Glow Up, Value/Deal, Convenience/Fast Delivery)
- `vibe` — scene/lifestyle context
- `visual_anchor` — PERSON or PRODUCT
- `notes` — RA's image direction brief (scene concept, setting, mood) — use this to shape the scene
- `recommended_products` — determines which reference image URLs to pass as `image_input`
- `overlays` — comma-separated list set by RA at review: `headline`, `price`, `bubble`, `accessories`, `other:...`

---

## Output

Plain text prompt only. No preamble, no explanation, no meta-commentary. Begin directly with `CONTENT TYPE:` followed by `SCENE:`.

**WF2 Phase 1 — Prompt generation (stops here):**
1. Write the plain text prompt to `.tmp/captions.json` → `prompt` field for the caption's entry.
2. Run `dubery-prompt-parser` on the prompt to produce structured JSON.
3. Save the structured JSON output to `.tmp/[id]_prompt_structured.json`.
4. Update `status` → `PROMPT_READY` only after both files are written.
Do NOT run `generate_kie.py`. RA reads prompts and tests in Gemini first.

**WF2 Phase 2 — Image generation (separate trigger: "generate images"):**
Read all `PROMPT_READY` entries from `.tmp/captions.json`.
For each: run `generate_kie.py` → `upload_image.py` → write Drive URL to `image_url` field → `status` → `DONE`.

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

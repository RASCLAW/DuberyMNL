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

**5. Content Type Selection**
Based on analysis + `Visual_Anchor` field, select ONE content type.

**Visual_Anchor enforcement (hard rule):**
- `PRODUCT` → must select TYPE B, C, D, or E. TYPE A is forbidden.
- `PRODUCT` + ambiguous caption → default to TYPE D.
- `PERSON` → TYPE A preferred, all types available.

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

### Required Sections

**CONTENT TYPE:** `[STATE THE TYPE AND VISUAL MOOD]`

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

For multi-subject (2+ products, PERSON anchor):
- Subject 1 → wears Reference Image 1 model, Subject 2 → wears Reference Image 2 model, etc.
- Describe group composition, interactions, each person's expression, each sunglass model distinctly visible.

---

**BRANDING:**
- DUBERY logo placement, style, color (typically white, top right corner or bottom right)
- Match vibe energy — bold and urgent for Sale, clean and minimal for Lifestyle

---

**TEXT OVERLAYS:**

Accuracy rule: Fixed strings must be spelled exactly, verbatim, every time:
```
₱699  |  POLARIZED  |  DUBERY  |  SAME-DAY DELIVERY  |  METRO MANILA
```

Dynamic text (headlines, body copy, taglines): spelling must be accurate and directly from the caption. No filler.

Dynamic rule: visual style, placement, font, color, shape — all creative and unique per concept. No two ads look the same.

Instruct NB2: "Render all text with sharp, clean, fully legible letterforms. Blurred or distorted text is not acceptable."

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

## Output

Plain text prompt only. No preamble, no explanation, no meta-commentary. Start directly with `CONTENT TYPE:`.

The prompt is saved to `.tmp/[ID]_prompt.json` as:
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

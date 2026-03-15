---
name: dubery-infographic-ad
description: Generate a DuberyMNL product infographic ad using the hand-drawn callout bubble format. Use when the caption highlights multiple product features. Outputs a production-ready NB2 JSON prompt.
---

# DuberyMNL Infographic Ad Generator

## Role
You are a DuberyMNL ad creative. Your job is to take a product model and 3 key features and output a complete NB2 JSON prompt that produces a hand-drawn callout infographic ad — the signature DuberyMNL format.

## Input
Provide any of the following:
- `product_model` — the Dubery model name and colorway (e.g., "Dubery Bandits - Green")
- `headline` — brand name + slogan (e.g., "DUBERY MNL: SEE EVERYTHING CLEARLY")
- `feature_1`, `feature_2`, `feature_3` — each as: PRIMARY BENEFIT + technical detail
  - e.g., Feature 1: "POLARIZED" / "100% UV400 protection"
  - e.g., Feature 2: "LIGHTWEIGHT" / "Featherlight TR90 frame"
  - e.g., Feature 3: "IMPACT-PROOF" / "Polycarbonate lens"

If inputs are not provided, derive them from the active caption in pipeline.json.

---

## Design DNA (Never Change These)

These are the fixed visual rules extracted from the original DuberyMNL infographic ad.

### Layer 1 — Backdrop
Sun-drenched tropical beach. Blurred palm trees in background. Turquoise water on the horizon. Bright natural daylight. Sky is clear, light is warm and direct.

### Layer 2 — Hero Product
Product centered in frame. Angled 3/4 view (left side slightly forward). Resting on a polished granite or marble surface. Soft shadow beneath product to ground it. Product takes up 50-60% of frame height.

### Layer 3 — Graphics (Hand-Drawn Elements)
- 3 callout ovals: thin-line, black, imperfect/sketchy stroke (not perfectly geometric)
- 3 arrows: hand-drawn, black, pointing from each oval to a specific part of the product
- Sparkle/action lines (3 short radiating strokes) above the top-left oval
- Placement: Callout 1 top-left, Callout 2 top-center, Callout 3 bottom-right

### Layer 4 — Typography
- Header: bold black sans-serif, all-caps, centered at top — "[BRAND NAME]: [PRODUCT SLOGAN]"
- Inside each oval: bold sans-serif, all-caps — the PRIMARY BENEFIT
- Below each oval: smaller regular-weight sans-serif — the TECHNICAL DETAIL
- All text must be sharply rendered, fully legible

### Design Logic
- Rule of Three: exactly 3 callouts, no more, no less
- Hierarchy contrast: bold benefit (big) vs. spec (small) — scannability
- Hand-drawn vs. clean product: the sketchy graphics make the product pop by contrast
- Sparkle accent signals the most important feature (callout 1)

---

## Step 1: Confirm Inputs

If product_model, headline, and 3 features are not provided:
1. Check `.tmp/pipeline.json` for the active APPROVED or PROMPT_READY caption
2. Extract `headline`, `vibe`, and caption text
3. Derive 3 features from the caption or standard Dubery product specs:
   - Default features: POLARIZED (UV400 protection) / LIGHTWEIGHT (TR90 frame) / IMPACT-PROOF (polycarbonate lens)

---

## Step 2: Build the NB2 Prompt

Output the following JSON. Replace all `[VARIABLE]` fields with actual values.

```json
{
  "prompt": "Generate a photo-realistic product infographic advertisement for a Facebook feed in 4:5 vertical format. This is a DuberyMNL sunglasses ad in the hand-drawn callout bubble style.\n\nSCENE: The product is centered on a polished granite surface. The background is a high-resolution sun-drenched tropical beach — blurred palm trees, turquoise water on the horizon, warm bright natural daylight with soft product shadow to ground it.\n\nPRODUCT: This ad MUST feature the exact style, frame shape, material, and lens color of the sunglasses shown in the [User-Provided Reference Image]. The Dubery logo must match the logo style and placement shown in the reference image. Do not alter the product in any way. Product is angled at a 3/4 view, left side slightly forward, occupying 50-60% of frame height.\n\nGRAPHICS LAYER: Render exactly three hand-drawn callout elements. Each callout consists of: (1) a thin-line black imperfect oval with slightly sketchy/organic stroke — not perfectly geometric; (2) a hand-drawn black arrow pointing FROM the oval TO a specific part of the product. Placement: Callout 1 is top-left, Callout 2 is top-center, Callout 3 is bottom-right. Above Callout 1, add three small hand-drawn sparkle action lines radiating outward.\n\nTYPOGRAPHY: Header at top-center: bold black sans-serif all-caps '[HEADLINE]'. Inside Callout 1 oval: bold sans-serif all-caps '[FEATURE_1_BENEFIT]'. Directly below Callout 1 oval: smaller regular-weight sans-serif '[FEATURE_1_SPEC]'. Inside Callout 2 oval: bold sans-serif all-caps '[FEATURE_2_BENEFIT]'. Directly below Callout 2 oval: smaller regular-weight sans-serif '[FEATURE_2_SPEC]'. Inside Callout 3 oval: bold sans-serif all-caps '[FEATURE_3_BENEFIT]'. Directly below Callout 3 oval: smaller regular-weight sans-serif '[FEATURE_3_SPEC]'.\n\nBRANDING: Render the Dubery logo bottom-left — the red D athlete/swoosh icon beside the bold italic condensed DUBERY wordmark (black fill, red outline). Render a price badge: ₱699, bold, prominent, positioned bottom-right.\n\nTEXT RENDER QUALITY: All text must be sharp, clean, and fully legible. No blurred, distorted, or broken letterforms. Render every letter exactly as specified — no substitutions, no placeholder text.",
  "negative_prompt": "blurry text, distorted letters, illegible text, broken typography, placeholder text, speech bubbles, rounded rectangle callouts, digital vector graphics, clean perfect oval strokes, studio backdrop, white background, indoor setting, generic stock photo, overexposed sky, no beach, no granite, plastic-looking product, altered frame shape, altered lens color, wrong logo, logo missing, price missing",
  "image_input": ["[REFERENCE_IMAGE_URL]"],
  "api_parameters": {
    "aspect_ratio": "4:5",
    "resolution": "1K",
    "output_format": "jpg"
  }
}
```

---

## Step 3: Fill Variables and Output

Replace all bracketed variables with real values:

| Variable            | Source                                        |
|---------------------|-----------------------------------------------|
| `[HEADLINE]`        | Input or derived from caption headline field  |
| `[FEATURE_1_BENEFIT]` | e.g., POLARIZED                             |
| `[FEATURE_1_SPEC]`  | e.g., 100% UV400 protection                   |
| `[FEATURE_2_BENEFIT]` | e.g., LIGHTWEIGHT                           |
| `[FEATURE_2_SPEC]`  | e.g., Featherlight TR90 frame                 |
| `[FEATURE_3_BENEFIT]` | e.g., IMPACT-PROOF                          |
| `[FEATURE_3_SPEC]`  | e.g., Polycarbonate lens                      |
| `[REFERENCE_IMAGE_URL]` | Product reference image URL               |

After substitution, output the full completed JSON so RA can copy-paste it directly to generate_kie.py.

---

## Hard Rules
1. Never change the 4-layer design DNA — these are the fixed brand rules for this format
2. Exactly 3 callouts — not 2, not 4
3. Hand-drawn oval style only — no digital vector bubbles or rectangles
4. All text must be spelled exactly as specified — no AI-generated filler
5. Product fidelity is non-negotiable — exact frame, lens, logo as in reference image
6. Always output the full completed JSON after building the prompt

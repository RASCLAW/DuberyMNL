---
name: dubery-v3-validator
description: Validate v3 UGC prompt files before image generation. Checks product spec match (filtered), naturalism, proportions, camera-relative direction, image input, color-word ban, category-prodref routing, and JSON schema. Use on UGC content prompts before generate_vertex.py. NOT for kraft prodref generation prompts.
argument-hint: "prompt_file"
---

# DuberyMNL v3 UGC Prompt Validator

Pre-spend gate for **UGC content prompts only** — the pipeline outputs that generate social/ad content (person wearing, flatlay, unboxing, outfit match, etc.). Matches post-session-121 pipeline: sidecar-driven fidelity, camera-relative directions, hero prodref for package categories, stripped schema (no `lighting_logic`, no `contact_points`).

## Scope

**Validate:**
- UGC prompts built from the v3 pipeline (`UGC_PRODUCT`, `UGC_PERSON_WEARING`, `UGC_UNBOXING`, `UGC_GIFTED`, `UGC_OUTFIT_MATCH`, etc.)
- Prompts whose `image_input` points to a prodref in `contents/assets/prodref-kraft/` or `contents/assets/hero/`

**Do NOT validate:**
- Kraft prodref generation prompts (the ones that created `prodref-kraft/{product}/01-hero.png` etc.) — these are a one-time setup step using supplier images as source, not UGC output
- Brand category prompts (CALLOUT, BOLD, COLLECTION) — those have their own skill
- Legacy v2 prompts — use `dubery-prompt-reviewer` instead

**Input:** path to a `.txt` prompt file (plain text prompt). Validator reads the sibling `_config.json` for `image_input`, and parses the JSON block embedded in the `.txt` for the v3 schema.

---

## Checks

### V1 — Product Spec Match (filtered)

1. Extract product key from `product_fidelity.identity` (e.g. "Dubery D918 Vintage Polarized Sunglasses" → `outback-blue` via lookup, or inferred from naming).
2. Load `contents/assets/product-specs.json`.
3. Identify the prodref file in `image_input[0]`:
   - If path matches `contents/assets/prodref-kraft/{product}/{angle}.png` → load `{angle}.json` sidecar
   - If path matches `contents/assets/hero/hero-{product}.png` → load `hero-{product}.json` sidecar
4. Read `sidecar.visible_details` (list of integer indices).
5. Build EXPECTED = `[spec.required_details[i] for i in visible_details]`.
6. Compare EXPECTED against prompt's `product_fidelity.required_details`.

PASS — every expected detail present, no fabricated extras, `proportions` + `finish` match spec.
FAIL — missing spec details, extra fabricated ones, or proportions/finish drift.

### V2 — Naturalism (unchanged)

**Banned anywhere in prompt text:** `paste`, `composite`, `overlay`, `superimpose`, `photoshop`, `insert`, `cut out`, `placed on top`

**Required phrases:**
- `interaction_physics.relight_instruction` contains: "Use the product in INPUT_IMAGE_0 but digitally relight it"
- `interaction_physics.reflection_logic` contains: "Do NOT preserve reflections from the original product photo" (required for mirrored-lens products; optional but recommended for non-mirrored)

PASS — no banned words, required phrases present.
FAIL — banned word found OR required phrase missing.

### V3 — Proportion Check (unchanged)

**Banned in `proportions`, `state`, `subject_placement`:**
`oversized`, `large`, `huge`, `massive`, `giant`, `extra-large`, `enlarged`, `big`

**OK:** `standard`, `retro`, `wide`, `compact`, `slim`, `rounded`, `square`

PASS — no size-inflating words.
FAIL — size-inflating word found.

### V4 — Direction (camera-relative, kraft-only)

1. Load the sidecar for `image_input[0]` (same lookup as V1).
2. If the sidecar has NO `frame_direction` field → this is a hero prodref (package category). **SKIP the direction check** and move on.
3. Otherwise (kraft prodref), read `sidecar.frame_direction` — must be camera-relative phrasing like "toward the right side of the frame", "facing directly toward camera", "toward the left side of the frame".
4. `product_fidelity.state` must reference the SAME camera-relative direction (or the canonical phrase "matching the reference photo orientation").
5. `scene_variables.subject_placement` must agree with `state`.

**Banned everywhere (even for hero prompts):** clock directions ("3 o'clock", "4 o'clock", "6 o'clock", "7 o'clock", "8 o'clock", "12 o'clock", etc.) — these are deprecated.

PASS — (kraft) sidecar direction aligns with state + placement OR (hero) no frame_direction in sidecar, no clock directions anywhere.
FAIL — direction drift OR clock direction present.

### V5 — Image Input (multi-image aware)

Read `image_input` from sibling `_config.json` (or inline if in legacy JSON prompt).

- Must be an array
- 1 OR 2 file paths allowed (2 = multi-image color transfer pattern)
- Every path must exist on disk
- NO logo overlay files (`dubery-logo.png`, `dubery-logo.jpg`, `DUBERY-FONTS.png`)

PASS — 1 or 2 valid paths, all exist, no logo overlays.
FAIL — missing file, logo overlay present, or more than 2 images.

### V6 — Color Words in required_details (NEW)

Scan `product_fidelity.required_details` for banned color adjectives:
`blue`, `black`, `green`, `red`, `gold`, `amber`, `grey`, `gray`, `brown`, `orange`, `purple`, `pink`, `yellow`

Exception: structural/pattern names are allowed (e.g. "tortoise shell pattern", "rasta stripe" — these are visual identifiers, not color-word descriptors).

**Why:** Gemini reads color from the prodref photo. Color adjectives in `required_details` can conflict with the reference image and cause compromise artifacts.

PASS — no color adjectives in required_details (structural names OK).
FAIL — color adjective found.

### V7 — Category / Prodref Routing (NEW)

Infer the category from the prompt (explicit field if present, otherwise from state/location/pose cues). Expected prodref types by category:

| Category | Expected prodref |
|----------|------------------|
| UGC_PRODUCT | `01-hero` kraft |
| UGC_PERSON_WEARING | `01-hero` kraft |
| UGC_PERSON_HOLDING | `01-hero` kraft |
| UGC_SELFIE | `01-hero` kraft |
| UGC_FLATLAY | `06-front` kraft |
| UGC_OUTFIT_MATCH | `01-hero` kraft |
| UGC_UNBOXING | `hero` (full package) |
| UGC_GIFTED | `hero` (full package) |
| UGC_WHAT_YOU_GET | `hero` (full package) |
| UGC_DELIVERY | `hero` (full package) |

Check that the path in `image_input[0]` matches the expected prodref type.

PASS — prodref matches category.
FAIL — prodref type mismatch (e.g. kraft used for UNBOXING).

### V8 — JSON Schema (updated)

- Valid JSON (the block inside the `.txt` prompt must parse)
- `product_fidelity` with: `identity`, `required_details`, `proportions`, `state`
- `interaction_physics` with: `blending_mode`, `reflection_logic`, `relight_instruction` (NOT `lighting_logic`, NOT `contact_points` — these are removed)
- `scene_variables` with: `location`, `subject_placement`, `lighting_atmosphere`, `camera_settings`
- `render_quality` present
- `api_parameters` present with `aspect_ratio` and `output_format`

**Prefix check:** Prompt text must begin with either:
- `"Generate an image based on the following JSON parameters and the attached reference image - ensure that product attached keeps its identity and design do not hallucinate"` (base)
- OR the same line followed by `"CRITICAL: Any text on the product (DUBERY branding) MUST preserve the exact spelling..."` (spelling guard variant)

PASS — schema valid, all sections present, prefix matches one of the two variants.
FAIL — missing section, invalid JSON, or wrong prefix.

---

## Report Format

```
═══════════════════════════════════════════
V3 VALIDATION: {filename}
Product: {identity}
Category: {inferred}
Prodref:  {image_input[0]}
Images:   {N}

V1 Product spec (filtered):   PASS | FAIL
V2 Naturalism:                PASS | FAIL
V3 Proportion check:          PASS | FAIL
V4 Direction (camera-rel):    PASS | FAIL
V5 Image input (multi-aware): PASS | FAIL
V6 Color-free required:       PASS | FAIL
V7 Category routing:          PASS | FAIL
V8 JSON schema:               PASS | FAIL

Issues:
  - {issue 1}
  - {issue 2}

Verdict: PASS | FAIL
═══════════════════════════════════════════
```

---

## Decision Rules

- **All PASS** → ready for `generate_vertex.py`
- **Any FAIL** → patch the specific issue, re-validate (no paid call yet)
- **3 consecutive fails on the same prompt** → stop, escalate to RA with summary

---

## What This Does NOT Check

- Aesthetic quality — only the generated image reveals that
- Scene creativity — human call
- Whether the prodref PNG is good — assume it passed earlier RA review
- Caption alignment — not applicable to v3 prompts
- Whether Gemini will actually obey every instruction — that's post-generation review

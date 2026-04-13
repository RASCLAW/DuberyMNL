---
name: dubery-v3-validator
description: Validate v3 fidelity-spec prompt JSONs before image generation. Checks product spec match, naturalism, proportions, direction alignment, image input, and JSON format. Use after dubery-fidelity-prompt, before generate_vertex.py.
argument-hint: "prompt_file"
---

# DuberyMNL v3 Prompt Validator

Validates a v3 fidelity-spec prompt JSON before spending Vertex AI credits. Catches product spec mismatches, naturalism violations, proportion inflation, direction conflicts, and structural issues.

**Input:** path to a v3 prompt JSON file (or multiple comma-separated)

---

## Checks

### V1 -- Product Spec Match

Load the product spec from `contents/assets/product-specs.json` using the product name from `product_fidelity.identity`.

- Every entry in the spec's `required_details` must appear in the prompt's `product_fidelity.required_details` -- verbatim or semantically equivalent
- No EXTRA product descriptions that aren't in the spec (fabricated details)
- `proportions` must match the spec
- `finish` must match the spec

Verdict:
- PASS -- all spec details present, no extras
- FAIL -- details missing, altered, or fabricated

### V2 -- Naturalism

Scan the full JSON text for anti-naturalism language.

**BANNED words anywhere in the prompt:**
`paste`, `composite`, `overlay`, `superimpose`, `photoshop`, `insert`, `cut out`, `placed on top`

**REQUIRED phrases -- must be present:**
- `relight_instruction` field must contain: "Use the product in INPUT_IMAGE_0 but digitally relight it to match the new location"
- `reflection_logic` field must contain: "Do NOT preserve reflections from the original product photo"

Verdict:
- PASS -- no banned words, both required phrases present
- FAIL -- banned word found OR required phrase missing

### V3 -- Proportion Check

Scan `product_fidelity.proportions`, `product_fidelity.state`, and `scene_variables.subject_placement` for size-inflating language.

**BANNED:** `oversized`, `large`, `huge`, `massive`, `giant`, `extra-large`, `enlarged`, `big`

**OK:** `standard`, `retro`, `wide`, `compact`, `slim`

Verdict:
- PASS -- no size-inflating words
- FAIL -- size-inflating word found

### V4 -- Direction Alignment

Load prodref metadata from `contents/assets/prodref-metadata.json`.

- Identify which prodref file is in `image_input[0]`
- Look up its `direction` and `compatible_directions`
- Check that `product_fidelity.state` references a direction from `compatible_directions`
- Check that `scene_variables.subject_placement` references the same direction
- Both must agree

Verdict:
- PASS -- directions align with prodref metadata
- FAIL -- direction conflict or missing

### V5 -- Image Input

- `image_input` must be an array
- Must contain ONLY the product reference photo (one file)
- NO logo overlay files (dubery-logo.png, dubery-logo.jpg)
- NO font reference files (DUBERY-FONTS.png)
- The referenced file must exist on disk

Verdict:
- PASS -- single prodref file, exists on disk
- FAIL -- extra files, or file doesn't exist

### V6 -- JSON Format

- Valid JSON (parses without error)
- `product_fidelity` section present with `identity`, `required_details`, `proportions`, `state`
- `interaction_physics` section present with `blending_mode`, `lighting_logic`, `reflection_logic`, `contact_points`, `relight_instruction`
- `scene_variables` section present with `location`, `subject_placement`, `lighting_atmosphere`, `camera_settings`
- `render_quality` section present
- `image_input` and `api_parameters` present
- When converted to prompt text, must start with: "Generate an image based on the following JSON parameters and the attached reference image:"

Verdict:
- PASS -- all sections present, valid structure
- FAIL -- missing sections or invalid JSON

---

## Report Format

```
═══════════════════════════════════════════
V3 REVIEW: {filename}
Product: {identity}
Prodref: {image_input[0]}

V1 Product spec match:    PASS | FAIL
V2 Naturalism:            PASS | FAIL
V3 Proportion check:      PASS | FAIL
V4 Direction alignment:   PASS | FAIL
V5 Image input:           PASS | FAIL
V6 JSON format:           PASS | FAIL

Issues:
  - {issue 1}
  - {issue 2}

Verdict: PASS | FAIL
═══════════════════════════════════════════
```

---

## Decision Rules

- **All PASS** → ready for image generation
- **Any FAIL** → patch the specific issue, re-validate
- **3 consecutive fails** on the same prompt → skip it, move to next

---

## What This Does NOT Check

- Aesthetic quality -- only the generated image reveals that
- Scene creativity -- whether the scene is interesting is a human call
- Caption alignment -- not applicable to v3 prompts
- Whether the generated image actually matches -- that's RA's review after generation

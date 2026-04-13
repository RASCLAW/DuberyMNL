---
name: dubery-v3-pipeline
description: Full v3 content pipeline -- randomize category/angle/scene, generate fidelity-spec prompt, validate, generate image. Product-fidelity-first approach.
argument-hint: "product [count]"
---

# DuberyMNL v3 Content Pipeline

End-to-end pipeline: randomize → prompt → validate → generate. One image at a time, meticulous.

---

## Step 1: RANDOMIZE

Pick one from each dimension. Never repeat a combo from earlier in the batch.

### 1a. Product
Load from `contents/assets/product-specs.json`. For now: **Outback Blue only** until all product specs are validated.

### 1b. Angle
Load from `contents/assets/prodref-metadata.json`. Pick a random usable angle file for the product. Note its `direction` and `compatible_directions`.

### 1c. Category
Pick one:

| Category | Description | Person? | Text overlay? |
|----------|-------------|---------|---------------|
| `UGC_PRODUCT` | Product resting on a surface, no person | No | No |
| `UGC_PERSON_WEARING` | Person wearing the sunglasses on their face | Yes | No |
| `UGC_PERSON_HOLDING` | Person holding the sunglasses up to camera | Yes | No |
| `UGC_HEADBAND` | Sunglasses pushed up on head as headband | Yes | No |
| `BRAND_MODEL` | Person wearing sunglasses, premium photo, no text | Yes | No |
| `BRAND_CALLOUT` | Product on surface with feature callout labels | No | Yes |
| `BRAND_BOLD` | Typography-dominated with product integration | Varies | Yes |
| `BRAND_COLLECTION` | Multiple products in one frame | No | Yes |

### 1d. Direction
Pick from `compatible_directions` for the chosen angle. The prompt's product placement must match this direction.

### 1e. Scene
Pick location, lighting, surface (if product-anchor), subject (if person), camera preset, objects. Ensure no repeat from previous images in this batch.

**Camera presets:**
- `UGC_PRODUCT`: 50mm, blur 0.4
- `UGC_PERSON_WEARING` / `BRAND_MODEL`: 50mm candid or 24mm selfie, blur 0.3-0.5
- `UGC_PERSON_HOLDING`: 50mm, blur 0.5
- `UGC_HEADBAND`: 50mm, blur 0.5
- `BRAND_CALLOUT` / `BRAND_BOLD`: 85mm, blur 0.7
- `BRAND_COLLECTION`: 85mm, blur 0.7

### 1f. Headline (brand categories only)
Check `contents/headline_history.json` for used headlines. Pick or generate an unused one.

---

## Step 2: GENERATE PROMPT

Build the JSON following the fidelity spec schema:

```json
{
  "product_fidelity": {
    "identity": "FROM product-specs.json",
    "required_details": "FROM product-specs.json",
    "proportions": "FROM product-specs.json",
    "state": "BUILT -- match prodref direction + how product appears for this category"
  },
  "interaction_physics": {
    "blending_mode": "PHOTOREALISTIC_INTEGRATION",
    "lighting_logic": "BUILT -- how scene light casts shadows from product",
    "reflection_logic": "Lenses naturally reflect the environment. Do NOT preserve reflections from the original product photo.",
    "relight_instruction": "Use the product in INPUT_IMAGE_0 but digitally relight it to match the new location. The product must look like it was physically present when the photo was taken."
  },
  "scene_variables": {
    "location": "FROM randomizer",
    "subject_placement": "FROM randomizer -- must reference the chosen direction",
    "lighting_atmosphere": "FROM randomizer",
    "camera_settings": "FROM preset",
    "objects_in_scene": "FROM randomizer"
  },
  "render_quality": {
    "resolution": "high",
    "color_space": "true-to-life",
    "background_blur_strength": "FROM preset"
  },
  "image_input": ["ONLY the prodref file -- no logo overlays"],
  "api_parameters": "FROM category defaults"
}
```

Add `subject` inside `scene_variables` for person categories.

**Product state by category:**
- `UGC_PRODUCT`: "Pristine condition, arms open, product facing [direction]"
- `UGC_PERSON_WEARING` / `BRAND_MODEL`: "Worn naturally on face, sitting on bridge of nose and ears"
- `UGC_PERSON_HOLDING`: "Held in hand, facing camera"
- `UGC_HEADBAND`: "Pushed up on top of the head like a headband, arms resting behind the ears, lenses facing upward"
- `BRAND_CALLOUT` / `BRAND_BOLD` / `BRAND_COLLECTION`: "Pristine condition, arms open, product facing [direction]"

---

## Step 3: VALIDATE

Check the prompt BEFORE generating. This catches issues that waste credits.

### V1 -- Product Fidelity Match
Compare `product_fidelity.required_details` in the prompt against `product-specs.json`.
- Every detail from the spec must appear verbatim or semantically equivalent
- No EXTRA product descriptions that aren't in the spec (hallucinated details)
- No emblem/logo descriptions (Gemini reads from the photo)
- FAIL if details are missing, altered, or fabricated

### V2 -- Naturalism Check
Scan the full JSON for anti-naturalism language:
- BANNED: "paste", "composite", "overlay", "superimpose", "photoshop", "insert"
- REQUIRED: `relight_instruction` must be present verbatim
- REQUIRED: `reflection_logic` must end with "Do NOT preserve reflections from the original product photo"
- FAIL if banned words found or required phrases missing

### V3 -- Proportion Check
Scan for size-inflating language:
- BANNED in proportions or anywhere: "oversized", "large", "huge", "massive", "giant", "extra-large"
- OK: "standard", "retro", "wide"
- FAIL if size-inflating words found

### V4 -- Direction Alignment
- `product_fidelity.state` must reference the chosen direction
- `scene_variables.subject_placement` must reference the same direction
- These must match the `compatible_directions` from the prodref metadata
- FAIL if directions conflict or are missing

### V5 -- Image Input
- `image_input` must contain ONLY the product reference photo
- NO logo overlays, NO font references, NO secondary images
- FAIL if extra files are included

### V6 -- JSON Format
- Must be valid JSON
- Must use indent=2 when converted to prompt text
- Prompt text must start with "Generate an image based on the following JSON parameters and the attached reference image:"

### Verdict
- All pass → proceed to Step 4
- Any fail → go to Step 3b (patch)

### Step 3b: PATCH
Fix the specific failing check. Do NOT rewrite the entire prompt -- only fix what failed. Then re-run Step 3.

If a prompt fails validation 3 times, skip it and move to the next assignment.

---

## Step 4: GENERATE IMAGE

Convert the validated JSON to prompt text.

**MANDATORY PREFIX (never change this):** Every prompt MUST start with exactly:
`Generate an image based on the following JSON parameters and the attached reference image:`
followed by two newlines, then the JSON with indent=2. This prefix is locked -- it tells Gemini to treat the JSON as structured parameters.

Save as `.txt` with sidecar `_config.json` for image_input.

Run: `python tools/image_gen/generate_vertex.py {prompt.txt} {output.png}`

---

## Step 5: RECORD

After RA scores the image:
- If PASS: record to `contents/headline_history.json` (if headline used) and `contents/layout_history.json`
- If FAIL: note the failure reason, do NOT record to history

---

## Execution Order

For each image in the batch:
1. Announce: "Randomizing -- [product], [category], [angle], [direction], [scene summary]"
2. Write the prompt JSON
3. Run validator, show results
4. If pass: generate image, show to RA
5. If fail: patch and re-validate
6. Wait for RA's score before moving to next

Process ONE image at a time. Do not batch-generate.

---
name: dubery-v3-pipeline
description: Full v3 content pipeline -- pick category, load prodref + sidecar, filter spec, randomize scene, validate, generate. Product-fidelity-first approach.
argument-hint: "product [category] [count]"
---

# DuberyMNL v3 Content Pipeline

End-to-end pipeline: pick category → load prodref → filter spec → randomize scene → validate → generate. One image at a time, meticulous.

---

## Categories

| Category | Description | Prodref | Aspect |
|----------|-------------|---------|--------|
| `UGC_PRODUCT` | Product resting on a surface | 06-front OR 01-hero | 1:1 |
| `UGC_PERSON_WEARING` | Person wearing sunglasses on face | 01-hero | 9:14 or 14:9 |
| `UGC_PERSON_HOLDING` | Person holding sunglasses up | 01-hero | 9:14 |
| `UGC_SELFIE` | Arm-length selfie, fit check | 01-hero | 9:14 |
| `UGC_FLATLAY` | Overhead flat lay with lifestyle items | 06-front | 1:1 |
| `UGC_UNBOXING` | Hands unboxing product from Dubery package | hero shot | 9:14 |

**Prodref selection rules:**
- Person categories (WEARING, HOLDING, SELFIE): use `01-hero` (3/4 angle, branding visible)
- Overhead/front categories (PRODUCT front, FLATLAY): use `06-front` (front view)
- Product angled on surface: use `01-hero`
- Unboxing: use `contents/assets/hero/hero-{product}.png` (full unboxing set)

---

## Step 1: LOAD PRODREF + SIDECAR

1. Pick the prodref `.png` based on category (see table above)
2. Load the sidecar `.json` from the same folder
3. Read: `frame_direction`, `visible_details`

**Kraft prodref location:** `contents/new/outback-blue-kraft/`
**Hero shot location:** `contents/assets/hero/`

**Sidecar format:**
```json
{
  "product": "outback-blue",
  "angle": "3/4 view",
  "frame_direction": "Product angled toward the left side of the frame",
  "shows": ["left temple arm", "branding badge", "both lenses", "frame shape", "inner arm pattern"],
  "visible_details": [0, 1, 2, 3]
}
```

---

## Step 2: FILTER SPEC

Load product spec from `contents/assets/product-specs.json`.

Filter `required_details` by `visible_details` indices from sidecar:
- If sidecar says `[0, 1, 3]` → only include indices 0, 1, 3
- If sidecar says `[0, 1, 2, 3]` → include all 4

**Outback Blue required_details:**
```
[0] "Square-style matte polycarbonate frame with angular flat-top edge"
[1] "Vibrant mirrored polarized lenses"
[2] "Ensure Branding visible on the temple and spelling stays same as prod ref"
[3] "Keyhole bridge design"
```

**Rules:**
- NO color words in required_details (no blue, black, green, red, gold). Gemini reads color from the photo.
- NO describing features not visible in the chosen angle. This causes Gemini to distort the product.

---

## Step 3: RANDOMIZE SCENE

Pick one from each dimension. Never repeat a combo from earlier in the batch.

### Frame direction options (camera-relative, NO clock directions):
- "Product angled toward the left side of the frame"
- "Product angled toward the right side of the frame"
- "Product facing directly toward camera"
- "Subject looking slightly downward toward the camera" (low angle)

### Location bank (daytime only -- NO night/neon/evening):
- Tropical beach with clean sky
- Resort infinity pool with turquoise water
- Rocky coastline with crashing waves
- Mountain trail viewpoint with green hills
- Coconut palm grove with dappled sunlight
- University campus lawn with old stone buildings
- Open sky with warm sunlight, minimal background
- Outdoor park with green trees
- Beach boardwalk with ocean behind
- Rooftop with city skyline
- Outdoor patio under palm trees

### Location bank for UGC_PRODUCT (scale-safe surfaces):
- Weathered wooden table with visible grain
- Smooth polished concrete ledge
- White marble surface
- Woven rattan tray
- Worn skateboard deck with grip tape
- Leather motorcycle seat on coastal overlook
- Clean wooden desk
- Dark slate stone surface

**AVOID for product shots:** Objects with recognizable real-world size next to the product (newspapers, phones, books, vinyl records, wallets). Product renders oversized.

### Subject bank (person categories only):
- Alternate male/female across batch
- Always Filipino/Filipina
- Age range: early 20s to early 30s
- Specify which hand when hands are in frame (LEFT hand / RIGHT hand)

### Lighting bank (daytime only):
- Bright warm afternoon sun, clean shadows
- Golden hour sunlight from the side, warm tones
- Bright tropical midday sun from above
- Morning light through scattered clouds, gentle and directional
- Warm natural window light (indoor)
- Dappled shade under tropical trees

### Camera presets:
- UGC_PRODUCT: "50mm, f/2.8, slightly elevated angle looking down at product, sharp focus on product"
- UGC_PERSON_WEARING: "85mm, f/1.4, tight beauty shot, face fills frame, extreme shallow DOF"
- UGC_PERSON_HOLDING: "50mm, f/2.0, focus on sunglasses in hand, face soft behind"
- UGC_SELFIE: "24mm wide angle, f/2.0, arm-length selfie distance, slight wide-angle distortion, sharp focus on face"
- UGC_FLATLAY: "50mm, f/4, shot directly from above looking straight down, everything in focus"
- UGC_UNBOXING: "24mm wide angle, f/2.0, POV looking down OR 50mm overhead"

---

## Step 4: BUILD PROMPT

### Mandatory prefix (NEVER change):
```
Generate an image based on the following JSON parameters and the attached reference image - ensure that product attached keeps its identity and design do not hallucinate:
```

### Prompt structure:
```json
{
  "product_fidelity": {
    "identity": "FROM product-specs.json",
    "required_details": "FILTERED by visible_details",
    "proportions": "FROM product-specs.json",
    "state": "BUILT from category + frame_direction"
  },
  "interaction_physics": {
    "blending_mode": "PHOTOREALISTIC_INTEGRATION",
    "reflection_logic": "Lenses naturally reflect the environment. Do NOT preserve reflections from the original product photo.",
    "relight_instruction": "Use the product in INPUT_IMAGE_0 but digitally relight it to match the new location. The product must look like it was physically present when the photo was taken."
  },
  "scene_variables": {
    "location": "FROM randomizer",
    "subject": "FOR person categories only",
    "subject_placement": "FROM category + frame_direction",
    "lighting_atmosphere": "FROM randomizer",
    "camera_settings": "FROM preset"
  },
  "render_quality": {
    "resolution": "high",
    "color_space": "true-to-life",
    "background_blur_strength": "0.4-0.6"
  },
  "image_input": ["prodref path"],
  "api_parameters": {
    "aspect_ratio": "FROM category table",
    "output_format": "png"
  }
}
```

### Product state by category:
- `UGC_PRODUCT`: "Pristine condition, arms open, {frame_direction}, resting on surface"
- `UGC_PERSON_WEARING`: "Worn naturally on face, sitting on bridge of nose and ears, {frame_direction} matching the reference photo orientation"
- `UGC_PERSON_HOLDING`: "Held in one hand, arms open, {frame_direction} matching the reference photo orientation"
- `UGC_SELFIE`: Same as PERSON_WEARING
- `UGC_FLATLAY`: "Pristine condition, arms open, product facing directly toward camera, laid flat on surface viewed from above"
- `UGC_UNBOXING`: "Product and accessories laid out as if just unboxed, matching the arrangement shown in the reference photo"

### Fields NOT needed (removed -- Gemini handles naturally):
- `lighting_logic` -- covered by `lighting_atmosphere`
- `objects_in_scene` -- Gemini fills from `location`

### Prompt format:
- Save as `.txt` + sidecar `_config.json` (readable, editable)
- NOT JSON-in-JSON (unreadable escaped strings)

---

## Step 5: VALIDATE (before generating)

### Pre-Generation Checklist:
- [ ] Prodref selected -- correct .png for this category?
- [ ] Sidecar loaded -- frame_direction + visible_details?
- [ ] Spec filtered -- required_details match visible_details indices?
- [ ] Frame direction -- camera-relative language, NO clock directions?
- [ ] Locked phrases -- all 3 verbatim?
- [ ] Fidelity prefix -- identity preservation line present?
- [ ] Scene makes sense -- daytime only, no night/neon?
- [ ] No color words in required_details?
- [ ] Aspect ratio correct for category?
- [ ] image_input path correct?

### Post-Prompt Validator Gate:
- [ ] **V1** image_input matches the chosen prodref
- [ ] **V2** state + subject_placement use frame_direction from THAT prodref's sidecar
- [ ] **V3** required_details filtered by THAT prodref's visible_details
- [ ] **V4** _config.json matches image_input in prompt

**If any check fails: STOP. Fix before generating.**

---

## Step 6: GENERATE

```bash
python tools/image_gen/generate_vertex.py .tmp/{name}_prompt.txt contents/new/{name}.png
```

---

## Step 7: RECORD

After RA scores the image:
- If PASS: record to `contents/layout_history.json`
- If FAIL: note the failure reason, do NOT record

---

## Execution Order

For each image:
1. Announce: "Generating -- [product], [category], [prodref], [frame_direction], [scene summary]"
2. Show the checklist (filled in)
3. Show the validator gate (all checks)
4. Write prompt + config
5. Generate
6. Show result to RA
7. Wait for score before moving to next

Process ONE image at a time. Do not batch-generate.

---

## Validated (Session 119)

All 6 UGC categories tested and passing for Outback Blue:
- UGC_PRODUCT: ~8 tests (wooden table, skateboard, motorcycle, marble, concrete)
- UGC_PERSON_WEARING: ~12 tests (left/right/down, male/female, editorial, casual)
- UGC_PERSON_HOLDING: ~4 tests (left/right, near face, toward camera)
- UGC_SELFIE: ~3 tests (park, beach boardwalk, rooftop mirror)
- UGC_FLATLAY: ~2 tests (white linen, rattan tray under palms)
- UGC_UNBOXING: ~5 tests (desk, bedsheet, cafe COD, POV floor)

Total: ~48 generations, ~$3 Vertex spend, all passing product fidelity.

---
name: ugc-pipeline
description: Full v3 UGC content pipeline -- pick category, load prodref + sidecar, filter spec, randomize scene, validate, generate. Product-fidelity-first approach.
argument-hint: "[product] [category] [count]  OR  just [count] for mixed-product batch"
---

## Invocation

- `ugc-pipeline bandits-blue 3` — lock batch to one product
- `ugc-pipeline 10` — mixed batch, randomizer picks different product per image (no-repeat until catalog exhausts)
- `ugc-pipeline bandits-tortoise UGC_SELFIE 3` — lock product + category


# DuberyMNL UGC Pipeline (v3)

End-to-end pipeline: pick category → load prodref → filter spec → randomize scene → validate → generate. One image at a time, meticulous.

---

## Categories

| Category | Description | Prodref | Aspect |
|----------|-------------|---------|--------|
| `UGC_PRODUCT` | Product resting on a surface | 01-hero kraft | 1:1 / 4:5 |
| `UGC_PERSON_WEARING` | Person wearing sunglasses on face | 01-hero kraft | 9:14 |
| `UGC_PERSON_HOLDING` | Person holding sunglasses up | 01-hero kraft | 9:14 |
| `UGC_SELFIE` | Arm-length selfie, fit check | 01-hero kraft | 9:14 |
| `UGC_FLATLAY` | Overhead flat lay with lifestyle items | 06-front kraft | 1:1 / 4:5 |
| `UGC_UNBOXING` | Hands unboxing product from Dubery package | hero (full packaging) | 9:14 / 1:1 |
| `UGC_GIFTED` | Gift reveal -- ribbon, greeting card, personal framing | hero (full packaging) | 1:1 / 4:5 |
| `UGC_WHAT_YOU_GET` | Clean contents showcase (Shopee-listing style) | hero (full packaging) | 1:1 / 4:5 |
| `UGC_DELIVERY` | Just-received moment, package on surface | hero (full packaging) | 1:1 / 4:5 / 9:14 |
| `UGC_OUTFIT_MATCH` | Full OOTD body shot, sunglasses as accent | 01-hero kraft | 9:14 |

**Prodref selection rules:**
- Person categories that show the product worn/held (WEARING, HOLDING, SELFIE, OUTFIT_MATCH): `01-hero` kraft
- Product-only surface shots (PRODUCT): `01-hero` kraft
- Overhead flat lay (FLATLAY): `06-front` kraft
- Package-centric categories (UNBOXING, GIFTED, WHAT_YOU_GET, DELIVERY): `hero` -- the full packaging shot at `contents/assets/hero/hero-{product}.png`. Hero anchors all accessory details (box, pouch, cloth, warranty card) so Gemini does not hallucinate them.

---

## Step 1: LOAD PRODREF + SIDECAR

1. Pick the prodref `.png` based on category (see table above)
2. Load the sidecar `.json` from the same folder
3. Read: `frame_direction`, `visible_details`

**Kraft prodref location:** `contents/assets/prodref-kraft/{product_key}/` (01-hero, 06-front, 07-flat)
**Hero shot location:** `contents/assets/hero/hero-{product_key}.png` (complete packaging for hero-based categories)

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

**Rules:**
- NO color words in required_details (no blue, black, green, red, gold). Gemini reads color from the photo.
- NO describing features not visible in the chosen angle. This causes Gemini to distort the product.

---

## Step 3: RANDOMIZE SCENE

**Run the randomizer -- it is the single source of truth for all scene banks.**

```bash
python tools/image_gen/v3_randomizer.py --product {product_key}           # single-product, 1 image
python tools/image_gen/v3_randomizer.py --product {product_key} --count 3 # single-product batch
python tools/image_gen/v3_randomizer.py --count 10                        # mixed-product batch (omit --product)
python tools/image_gen/v3_randomizer.py --category UGC_PERSON_WEARING     # force category
```

The randomizer outputs a complete scene assignment: category, prodref path, frame_direction (from sidecar), filtered required_details, location, lighting, camera, aspect_ratio, and (for person categories) a subject + pose + hand. Each bank item carries a numeric ID for layout_history dedup.

**Rules the randomizer enforces:**
- Frame direction is camera-relative (left side / right side / toward camera) -- NO clock directions
- Daytime-only locations and lighting (no night, neon, or blue-hour)
- Daytime-appropriate camera presets per category (closer presets allowed for PERSON categories: 50/85/135mm)
- LEFT or RIGHT hand is specified explicitly for HOLDING / SELFIE / UNBOXING poses
- Aspect ratios: 9:14 for person categories, 1:1 or 4:5 for product/flatlay, 9:14 or 1:1 for unboxing
- No repeat categories within a single batch until catalog is exhausted

**Do NOT pick scene dimensions manually.** If a value looks wrong in the randomizer output, edit `tools/image_gen/v3_randomizer.py` -- never override in the prompt.

---

## Step 4: BUILD PROMPT

**Invoke `/dubery-fidelity-prompt` with the randomizer assignment from Step 3.** That skill owns the schema, state templates (kraft + hero), category routing, mandatory prefix, and output format. Do NOT freelance the prompt structure here -- all of it lives in `/dubery-fidelity-prompt` so updates propagate to a single source of truth.

**What the fidelity-prompt skill handles (so you don't have to):**
- Mandatory prefix with identity preservation instruction
- `product_fidelity` block (identity + filtered required_details + proportions + state)
- `interaction_physics` locked template (blending_mode, reflection_logic, relight_instruction -- no lighting_logic, no contact_points, no objects_in_scene)
- Category-specific state templates (kraft categories use `{frame_direction}` from sidecar; hero categories use package-layout templates)
- `scene_variables` assembly from randomizer output (location, subject, subject_placement, lighting_atmosphere, camera_settings)
- Output written as `.tmp/{name}_prompt.txt` + sibling `.tmp/{name}_config.json` (with `image_input`)

**What Step 4 here is responsible for:**
- Passing the full randomizer assignment (category, prodref path, frame_direction, visible_details, location, subject, etc.) to the fidelity-prompt skill
- Picking a readable name for the output files (e.g. `{product}-{batch_index:02d}-{category_short}`)
- Confirming the fidelity-prompt skill wrote both `.txt` + `_config.json`
- For hero categories (GIFTED / UNBOXING / WHAT_YOU_GET / DELIVERY): include the literal phrase "dark DUBERY box with red branding" in subject_placement to prevent box-color drift

If the fidelity-prompt skill fails to produce a valid prompt, STOP -- do not freelance a replacement.

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
2. Invoke `/dubery-fidelity-prompt` with the randomizer assignment -- it writes `.tmp/{name}_prompt.txt` + `_config.json`
3. Invoke `/dubery-v3-validator` on the prompt -- must PASS all 8 checks before spending
4. Run `generate_vertex.py` on the prompt (paid)
5. Show result to RA
6. Wait for score before moving to next image
7. If PASS: append assignment to `layout_history.json` for dedup. If FAIL: do NOT record.

Process ONE image at a time. Do not batch-generate.

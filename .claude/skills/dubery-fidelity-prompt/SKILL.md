---
name: dubery-fidelity-prompt
description: Generate product-fidelity-first image prompts using the v3 JSON schema. Product is a locked asset, scene is the variable. Outputs formatted JSON for Vertex AI.
argument-hint: "product scene_description"
---

# DuberyMNL v3 Fidelity Prompt Generator

Generates structured JSON prompts where the **product is a locked asset** and the **scene is the variable**.

---

## Flow

1. **PICK** prodref file based on category (kraft vs hero -- see Category Routing below)
2. **LOAD** the sibling sidecar `.json` -- read camera-relative `frame_direction` (kraft only; hero has none) and `visible_details`
3. **LOAD** product spec from `contents/assets/product-specs.json`, then FILTER `required_details` by `visible_details`
4. **RECEIVE** scene parameters (from randomizer, from input, or from variety banks)
5. **BUILD** JSON following the schema template below -- use camera-relative direction in `state`, never clock directions
6. **FORMAT** with `indent=2`
7. **OUTPUT** as prompt text for `generate_vertex.py`, written to `.tmp/{name}_prompt.txt` + sibling `.tmp/{name}_config.json` with `image_input`

For kraft categories: the prodref's camera-relative direction DRIVES the prompt. Text and image must agree -- never conflict.
For hero categories: the hero shot IS the anchor for package layout (box, pouch, cloth, card). `state` describes what the scene does WITH the package, not a product angle.

---

## External References

| Data | Source |
|------|--------|
| Product specs | `contents/assets/product-specs.json` |
| Scene variety banks | Defined in randomizer |
| Camera presets | Defined in randomizer |
| Kraft prodref photos | `contents/assets/prodref-kraft/{product}/{01-hero,06-front,07-flat}.png` |
| Hero (packaging) prodref photos | `contents/assets/hero/hero-{product}.png` |
| Per-prodref sidecar metadata | Sibling `.json` next to each prodref (camera-relative `frame_direction`, `visible_details`) |

**Always load from these files.** Never write product specs, scene banks, or camera settings from memory.

---

## JSON Schema Template

```json
{
  "product_fidelity": {
    "identity": "FROM product-specs.json",
    "required_details": "FROM product-specs.json",
    "proportions": "FROM product-specs.json",
    "state": "BUILT from prodref direction + how the product appears in the scene"
  },

  "interaction_physics": {
    "blending_mode": "PHOTOREALISTIC_INTEGRATION",
    "reflection_logic": "Lenses naturally reflect the environment. Do NOT preserve reflections from the original product photo.",
    "relight_instruction": "Use the product in INPUT_IMAGE_0 but digitally relight it to match the new location. The product must look like it was physically present when the photo was taken."
  },

  "scene_variables": {
    "location": "FROM input or banks",
    "subject_placement": "FROM input -- must reference prodref direction (kraft) or match package layout (hero)",
    "lighting_atmosphere": "FROM input or banks",
    "camera_settings": "FROM input or presets"
  },

  "render_quality": {
    "resolution": "high",
    "color_space": "true-to-life",
    "background_blur_strength": "FROM input or camera preset"
  },

  "image_input": ["ONLY the product reference photo path"],

  "api_parameters": "FROM input"
}
```

Add `subject` inside `scene_variables` when a person is in the scene:
```json
"subject": {
  "description": "FROM input",
  "action": "FROM input",
  "emotion": "FROM input"
}
```

---

## Rules

### Product Fidelity (locked)
- `required_details` comes from `product-specs.json`, then FILTERED by the chosen prodref's sidecar `visible_details` -- only include indices the prodref angle actually shows. Never write from memory. Never include indices not in `visible_details`.
- Emblem/logo descriptions are allowed IF they are in the product-specs.json file -- use exactly what the spec says, don't improvise
- `state` must reference the prodref's camera-relative direction (from sidecar `frame_direction`): e.g. "angled toward the right side of the frame matching the reference photo orientation". Clock directions ("8 o'clock" etc.) are BANNED.
- For hero (packaging) prodrefs, the sidecar has NO `frame_direction`. Use a package-centric state template that describes accessories/layout, not a product angle (see Hero Categories below).

### Interaction Physics (locked template)
- `blending_mode` is always `PHOTOREALISTIC_INTEGRATION`
- `relight_instruction` is always the verbatim sentence above -- this prevents the "pasted on" look
- `reflection_logic` is always: "Lenses naturally reflect the environment. Do NOT preserve reflections from the original product photo."
- No `lighting_logic` field (Gemini handles lighting from `lighting_atmosphere` alone)
- No `objects_in_scene` field (Gemini fills these from `location`)
- No `contact_points` field -- removed, Gemini handles this naturally

### Category Routing
- Kraft categories (use `contents/assets/prodref-kraft/{product}/{angle}.png`):
  - `UGC_PRODUCT`, `UGC_PERSON_WEARING`, `UGC_PERSON_HOLDING`, `UGC_SELFIE`, `UGC_OUTFIT_MATCH` -> `01-hero`
  - `UGC_FLATLAY` -> `06-front`
- Hero categories (use `contents/assets/hero/hero-{product}.png` -- full packaging shot, anchors box/pouch/cloth/warranty card):
  - `UGC_UNBOXING`, `UGC_GIFTED`, `UGC_WHAT_YOU_GET`, `UGC_DELIVERY`

### Hero Category State Templates (no `frame_direction`)
- `UGC_UNBOXING`: "Dubery package and accessories matching the reference photo arrangement, with hands mid-unboxing the box or pouch"
- `UGC_GIFTED`: "Dubery package matching the reference photo, framed as a gift with wrapping, ribbon, or greeting card context"
- `UGC_WHAT_YOU_GET`: "Dubery package and all accessories laid out clearly as a contents showcase, matching the reference photo arrangement, no hands"
- `UGC_DELIVERY`: "Dubery package as just received, unopened or partially opened, on the delivery location surface, matching the product and accessories shown in the reference photo"

### Scene Variables (the creative freedom zone)
- All values come from input or external banks -- skill does not hardcode locations, lighting, or props
- `subject_placement` must reference the prodref direction to ensure alignment

### Image Input
- ONLY the product reference photo -- no logo overlays, no font references, no secondary images
- Logo overlay files cause Gemini to stamp branding in wrong places

### Output Format
- JSON formatted with `indent=2` -- never a one-liner
- **MANDATORY PREFIX (never change this):** Every prompt MUST start with exactly this text:
  `Generate an image based on the following JSON parameters and the attached reference image - ensure that product attached keeps its identity and design do not hallucinate:`
  followed by two newlines, then the JSON with indent=2. This prefix is what tells Gemini to treat the JSON as structured parameters, not free text.
- Save as `.txt` with sidecar `_config.json` containing `{"image_input": [...]}`

---

## Self-Check

- [ ] `product_fidelity.required_details` loaded from product-specs.json
- [ ] Emblem/logo description matches product-specs.json exactly (no improvising)
- [ ] `product_fidelity.state` matches the prodref direction
- [ ] `interaction_physics.relight_instruction` present verbatim
- [ ] `reflection_logic` ends with "Do NOT preserve reflections from the original product photo"
- [ ] `image_input` has ONLY the product reference photo
- [ ] JSON formatted with indent=2
- [ ] Scene values came from input/banks, not hardcoded

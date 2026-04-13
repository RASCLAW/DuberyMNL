---
name: dubery-fidelity-prompt
description: Generate product-fidelity-first image prompts using the v3 JSON schema. Product is a locked asset, scene is the variable. Outputs formatted JSON for Vertex AI.
argument-hint: "product scene_description"
---

# DuberyMNL v3 Fidelity Prompt Generator

Generates structured JSON prompts where the **product is a locked asset** and the **scene is the variable**.

---

## Flow

1. **PICK** prodref file
2. **READ** the prodref photo -- determine its clock direction (which way the product faces)
3. **LOAD** product spec from `contents/assets/product-specs.json`
4. **RECEIVE** scene parameters (from randomizer, from input, or from variety banks)
5. **BUILD** JSON following the schema template below
6. **FORMAT** with `indent=2`
7. **OUTPUT** as prompt text for `generate_vertex.py`

The prodref direction DRIVES the prompt. Text and image must agree -- never conflict.

---

## External References

| Data | Source |
|------|--------|
| Product specs | `contents/assets/product-specs.json` |
| Scene variety banks | Defined in randomizer or passed as input |
| Camera presets | Defined in randomizer or passed as input |
| Product ref photos | `contents/assets/product-refs/{product}/` |
| Prodref metadata | `contents/assets/prodref-metadata.json` (planned) |

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
    "lighting_logic": "BUILT -- how the scene light casts shadows from the product onto the surface/skin",
    "reflection_logic": "Lenses naturally reflect the environment. Do NOT preserve reflections from the original product photo.",
    "relight_instruction": "Use the product in INPUT_IMAGE_0 but digitally relight it to match the new location. The product must look like it was physically present when the photo was taken."
  },

  "scene_variables": {
    "location": "FROM input or banks",
    "subject_placement": "FROM input -- must reference prodref direction",
    "lighting_atmosphere": "FROM input or banks",
    "camera_settings": "FROM input or presets",
    "objects_in_scene": "FROM input or banks"
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
- `required_details` comes from `product-specs.json` -- never write from memory
- Emblem/logo descriptions are allowed IF they are in the product-specs.json file -- use exactly what the spec says, don't improvise
- `state` must include the prodref clock direction: "angled facing [direction] matching the reference photo orientation"

### Interaction Physics (locked template)
- `blending_mode` is always `PHOTOREALISTIC_INTEGRATION`
- `relight_instruction` is always the verbatim sentence above -- this prevents the "pasted on" look
- `lighting_logic` must reference the specific scene surface (e.g., "onto the marble table", "onto the cheeks")
- `reflection_logic` is always: "Lenses naturally reflect the environment. Do NOT preserve reflections from the original product photo."
- No `contact_points` field -- removed, Gemini handles this naturally

### Scene Variables (the creative freedom zone)
- All values come from input or external banks -- skill does not hardcode locations, lighting, or props
- `subject_placement` must reference the prodref direction to ensure alignment

### Image Input
- ONLY the product reference photo -- no logo overlays, no font references, no secondary images
- Logo overlay files cause Gemini to stamp branding in wrong places

### Output Format
- JSON formatted with `indent=2` -- never a one-liner
- **MANDATORY PREFIX (never change this):** Every prompt MUST start with exactly this text:
  `Generate an image based on the following JSON parameters and the attached reference image:`
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

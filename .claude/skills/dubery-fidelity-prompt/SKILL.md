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

  "image_input": ["primary product reference photo path (INPUT_IMAGE_0, drives state/orientation)", "+ optional companion images: other Dubery kraft prodrefs for multi-product scenes (DUO/LINEUP/comparison) OR contents/assets/logos/inclusions.png for contents-showing hero scenes"],

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
- **ALWAYS append this verbatim as the final item in `required_details`:** `"Match product proportions, frame shape, temple pattern, emblem placement, lens color, and branding 100% against the attached reference photo -- no drift"`

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

**Outback Red & Blue -- use the `-plain` prodref for person-wearing / worn / multi-product shots.** `outback-red` and `outback-blue` share a frame whose inner temple arm has a zebra/marble pattern that BLEEDS across the whole arm when worn or in dense shots. For `UGC_PERSON_WEARING` (and any worn or multi-product composition), use `01-hero-plain.png` (plain matte black arms, zebra removed) instead of `01-hero.png`. Use the real `01-hero.png` only for solo product / side / detail shots where the arm pattern renders cleanly and accuracy matters. (Outback only -- do NOT apply to bandits; its tropical arm graphic is a signature both-sides feature, leave it intact.)

### Hero Category State Templates (no `frame_direction`)
- `UGC_UNBOXING`: "Dubery package and accessories matching the reference photo arrangement, with hands mid-unboxing the box or pouch"
- `UGC_GIFTED`: "Dubery package matching the reference photo, framed as a gift with wrapping, ribbon, or greeting card context"
- `UGC_WHAT_YOU_GET`: "Dubery package and all accessories laid out clearly as a contents showcase, matching the reference photo arrangement, no hands"
- `UGC_DELIVERY`: "Dubery package as just received, unopened or partially opened, on the delivery location surface, matching the product and accessories shown in the reference photo"

### Scene Variables (the creative freedom zone)
- All values come from input or external banks -- skill does not hardcode locations, lighting, or props
- `subject_placement` must reference the prodref direction to ensure alignment

### Image Input
**Principle:** every reference image must be a real Dubery asset that the scene needs to render faithfully. Anything else (logos, fonts, generic stock) is banned because it makes Gemini stamp brand marks in the wrong places.

- **INPUT_IMAGE_0 (always):** the primary product kraft prodref. Drives `state`, `frame_direction`, and overall orientation. The mandatory fidelity anchor in `required_details` refers to this image.
- **INPUT_IMAGE_1+ (optional, allowed companions):**
  - Other Dubery kraft prodrefs when the scene must show multiple real products (DUO, LINEUP, comparison, family shots). Each companion gets a MINIMAL `companion_fidelity` block (template below): **source index + a reproduce-exactly rule, nothing else.** Do NOT give the companion an identity, product name, required_details, or any color/finish words -- the attached image alone defines it.
  - Inclusions accessories for contents-showing hero scenes (`UGC_WHAT_YOU_GET`, `UGC_UNBOXING`, `UGC_GIFTED`, `UGC_DELIVERY`). Two ways to attach -- pick the subset the scene needs, don't force all three into every shot:
    - `contents/assets/logos/inclusions.png` -- all three together (box + cloth + pouch). Use for a clean "everything you get" shot with few/no product pairs.
    - Single-item files (attach only what the scene calls for): `inclusions-box.png` (vertical black DUBERY product box with feature pictogram grid), `inclusions-cloth.png` (gray microfiber cloth), `inclusions-pouch.png` (black soft pouch w/ red drawstring). Prefer these for dense multi-product scenes so accessories don't crowd the frame -- e.g. attach just the box + pouch alongside a duo.
    - Each attached accessory file gets an `inclusions_fidelity` item describing it + the "these are accessories, NOT extra sunglasses" guard. This stops the agent inventing things like a nonexistent warranty card.
- **Banned everywhere:** logo overlay files, font reference sheets, generic stock photography, screenshots, anything not under `contents/assets/`.

#### `companion_fidelity` block template (multi-product scenes)
```json
"companion_fidelity": {
  "source": "INPUT_IMAGE_1 (or _2, _3, ...)",
  "rule": "Reproduce this pair EXACTLY as shown in INPUT_IMAGE_N. Do not alter its frame color, lens color, or finish. Do not copy INPUT_IMAGE_0's colors onto it. It is a separate, distinct pair."
}
```
**Why image-only:** describing the companion verbally (e.g. "Rasta Red, ruby mirror lenses") next to the primary's own description bleeds color words across the two products -- Gemini recolors one pair to match the other, or merges them. Validated 2026-05-28: stripping all identity/color words from the companion (and from `subject_placement` for that pair) and letting the attached image define it fixed a persistent Rasta DUO drift that the verbose block could not.

When using multiple kraft prodrefs in one prompt, `subject_placement` must call out each pair by its `INPUT_IMAGE` index for POSITION ONLY (e.g. "the pair from INPUT_IMAGE_1, right and behind") -- never describe the companion's color or finish there either.

### Multi-Product Hero Shots + Inclusions (validated 2026-05-28)

For "what you get" / collection / lifestyle hero shots that show products AND packaging:

- **Hierarchy is the whole game.** Sunglasses are the HERO: foreground, large, tack-sharp. Inclusions (box/cloth/pouch) are SUPPORTING: set BEHIND the sunglasses, smaller, softened by shallow depth of field so they recede. They must never match the visual weight of the sunglasses. Give each inclusion a `"role": "SUPPORTING background prop"` line.
- **Use all three inclusions together** (box + cloth + pouch) for the complete-package read -- a single accessory feels incomplete. Attach them as the three split single-item files, each its own `inclusions_fidelity` entry. (Subset is allowed but the full set is the default for hero shots.)
- **Slight elevated three-quarter tabletop angle** (NOT flat top-down) to create real foreground/background depth, with `background_blur_strength: strong`.

**Scene palette -- THIS IS REFERENCE, NOT A TEMPLATE TO COPY.** The validated premium moods are *dark slate + cool studio light* and *pale concrete + soft overcast* (clean white plaster is the safe baseline; warm wood tested poorly -- avoid). **Do NOT reuse the same surface/lighting every run.** Treat these as a starting palette: rotate between them across a batch AND invent fresh variations in the same spirit (other neutral/moody premium surfaces + lighting). Anchoring on one sampled scene every time is the failure mode -- vary deliberately. Surface, lighting, and exact arrangement are the variables; the hierarchy + fidelity rules above are the constants.

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
- [ ] `image_input` has the primary kraft prodref as INPUT_IMAGE_0; optional companions only if (a) other Dubery kraft prodrefs for multi-product scenes, or (b) inclusions.png for contents-showing hero scenes
- [ ] Multi-product scenes have a `companion_fidelity` block per extra prodref, and `subject_placement` calls out each by INPUT_IMAGE index
- [ ] JSON formatted with indent=2
- [ ] Scene values came from input/banks, not hardcoded

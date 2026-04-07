# AGENT -- DuberyMNL UGC Image Prompt Writer

Built from dubery-ad-creative. Same image quality, same scene construction,
same subject approach. No overlays, no price, no headlines. Dubery branding
stays as physical logo on the product.

---

## Non-Negotiable Rules

These rules override everything below.

**R1 -- Dubery Logo**
Include the Dubery logo (red D icon + DUBERY wordmark) in the upper corner of the image.

**R2 -- Product Fidelity**
The reference image is the ONLY authority on product appearance.
BANNED in `render_notes`, `scene.product_placement`, `visual_mood`, and `objects_in_scene`:
- Frame colors: black, blue, red, green, brown, amber, tortoise, camo, matte, glossy, dark, clear
- Lens descriptors: tinted, mirrored, warm, cool, gold, silver, smoke, amber, honey, sapphire
- Materials: metal, acetate, plastic, rubber, nylon
- Compound forms: "warm red/orange-tinted", "cool blue-tinted", "brown-amber", "earthy green"
- ANY description of what the frame or lens looks like

When tempted to describe the product, write "as shown in the reference image."
Model names (e.g., "Outback Red") may appear as identifiers only, never as color cues.

**R3 -- Lens Reflection Rule**
Do NOT describe lens reflections at all. No reflection instructions in any field.
BANNED phrases: "reflects the surrounding environment", "reflection of", "lens reflects",
"scene reflected in", "mirrored reflection", any description of what appears in the lens.

**R5 -- Setting Rule**
- Default: outdoors. Use specific Philippine locations (Espana, Quezon Ave, SM North, Baguio, Ilocos, etc.).
- Indoor only allowed for PRODUCT-anchored shots. Acceptable: retail store, optical shop, gym, cafe.
- NEVER place a person wearing sunglasses indoors (living room, bedroom, kitchen).

---

## Input

A JSON object from `ugc_pipeline.json`:

```json
{
  "scenario_type": "SELFIE_OUTDOOR",
  "subject_gender": "male",
  "product_ref": "Outback Red",
  "aspect_ratio": "9:16",
  "caption_text": null,
  "mood": null,
  "notes": "Optional direction from RA"
}
```

### Caption-Driven Mode

When `caption_text` and `mood` are provided, derive the visual scene FROM the caption:

1. Read the caption's story, theme, and emotional energy
2. Use `scenario_type` as the base scenario, but shape the specific setting and composition
   to match the caption's narrative
3. Use `mood` to determine lighting, color temperature, and subject expression:
   - `chill` -- soft natural light, relaxed posture, easy smile
   - `hype` -- bright daylight, energetic pose, wide grin
   - `flexing` -- confident stance, product prominent, aspirational backdrop
   - `grateful` -- warm light, genuine smile, intimate composition
   - `adventurous` -- dramatic landscape, action energy, wide scene
   - `confident` -- direct gaze, clean composition, effortless cool
   - `competitive` -- dynamic angle, post-activity energy, movement
4. The image and caption must tell the same story

When `caption_text` is null, select scene details from the scenario library based on `scenario_type` alone.

`product_image_url` is resolved automatically from the product reference table below.

---

## JSON Schema

Output must match this structure exactly.

```json
{
  "task": "ugc_simulation",

  "ugc_authenticity": {
    "scenario_type": "SELFIE_OUTDOOR",
    "dubery_logo_overlay": true,
    "product_logo_only_as_worn": true
  },

  "visual_mood": "1-2 sentence concept summary (no product color/material -- R2)",

  "scene": {
    "location": "Specific Philippine location",
    "time_of_day": "Time + light quality description",
    "atmosphere": "Environmental mood and texture",
    "lighting": "Direction, quality, intensity of light in the scene",
    "product_placement": "WHERE and HOW product sits (no color/material -- R2)",
    "format": "Vertical portrait format, 9:16 aspect ratio, optimized for mobile."
  },

  "product": {
    "models": ["Model Name"],
    "instruction": "This image MUST feature the exact style, frame shape, material, and lens color of the sunglasses shown in the reference image. Do not alter the product in any way."
  },

  "subject": {
    "description": "Age range, build, clothing style",
    "action": "What the person is doing",
    "emotion": "What they are feeling"
  },

  "prompt": "FIDELITY FIRST -- open with the product instruction, then scene, subject, logo. Keep it short. 3-5 sentences total.",

  "objects_in_scene": ["item 1 (no product color/material -- R2)", "item 2"],

  "image_input": [
    "C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/[variant].png",
    "C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/dubery-logo.png"
  ],
  "api_parameters": { "aspect_ratio": "9:16", "resolution": "2K", "output_format": "jpg" }
}
```

**Schema notes:**
- `subject`: only include for person-anchor scenarios
- `prompt`: FIDELITY FIRST. Open with "The subject wears [Product] from DuberyMNL exactly as shown in the reference image -- do not alter the frame shape, lens color, or logo placement." Then scene + subject in 2-3 short sentences. End with logo placement. Total: 3-5 sentences. Do NOT over-describe the scene.
- NO overlay fields. NO headline. NO price. NO delivery. NO badge.

---

## Scene Construction

### Be specific about:
- **Environment**: location, surfaces, objects, weather, air quality, cultural markers
- **Lighting**: direction, color temperature, shadow quality, highlight behavior, time of day
- **Composition**: framing, depth of field, camera angle, foreground/background balance
- **Atmosphere**: mood, energy, cultural grounding, what makes this feel like the Philippines
- **Human subject**: expression, emotion, body language, clothing, action, age range
- **Product position**: where it sits, angle, what direction light hits from (goes in render_notes -- R3)

### Leave to the reference image (never describe):
- Frame color, material, texture, finish
- Lens color, tint, mirror quality
- Logo appearance beyond "sharp and legible"
- Any compound color phrase applied to the product

---

## Scenario Library

Choose the scenario from `scenario_type`. Use the setting details as the visual anchor.
Settings listed are examples -- use any real, specific, nameable location that fits.

**Anchor bias: 70% PRODUCT / 30% PERSON.**

### PRODUCT-ANCHOR SCENARIOS (default)

**PRODUCT_HOLD** -- Customer holding sunglasses up, showing them off against a backdrop.
**COD_DELIVERY** -- Just-opened DuberyMNL package. Home setting, genuine excitement.
**REVIEW_UNBOX** -- Product appreciated after unboxing. Home surface, natural light.
**DASHBOARD_FLEX** -- Sunglasses on car dashboard, windshield view tells the story.
**CAFE_TABLE** -- Sunglasses on a cafe table. Casual "just sat down" energy.
**BEACH_SURFACE** -- Sunglasses on sand, towel, or lounger. Beach backdrop.
**GYM_BAG** -- Sunglasses on gym bag or bench. Post-workout energy.
**DESK_SHOT** -- Sunglasses on work desk or laptop. "About to head out" moment.
**SUNSET_PRODUCT** -- Golden hour product shot. Light and product do the work.
**TRAVEL_FLATLAY** -- Flat lay of travel essentials with sunglasses as centerpiece.
**OUTDOOR_SURFACE** -- Sunglasses on a natural or urban surface.

### PERSON-ANCHOR SCENARIOS (30%)

**SELFIE_OUTDOOR** -- Front-cam selfie outdoors. Harsh sun, candid expression.
**BEACH_CANDID** -- Shot by a friend at the beach. Natural, unposed.
**CAR_SELFIE** -- Driver or passenger. Window down, Filipino driving culture.
**OOTD_STREET** -- Outfit of the day. Sunglasses complete the look.
**COMMUTE_FLEX** -- Showing off shades mid-commute. Cool vs chaotic backdrop.
**WEEKEND_GROUP** -- Friends outing, 2-3 people. One wearing Dubery prominently.
**FESTIVAL** -- Filipino attending a regional festival. Colorful, energetic.
**FUN_RUN** -- Post-race or mid-event. Athletic energy.
**BIKING** -- Road cycling or leisure biking.
**BADMINTON** -- Post-game selfie or mid-play outdoor court.
**SUNSET_VIBE** -- Golden hour flex. Most aspirational UGC type.

---

## Product Reference Table

Look up `product_ref` and set as `image_input[0]`.
If `product_ref` is missing or unrecognized, default to Outback Red.

| product_ref | image_input path |
|---|---|
| Outback Red | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/outback-red.png` |
| Outback Black | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/outback-black.png` |
| Outback Blue | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/outback-blue.png` |
| Outback Green | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/outback-green.png` |
| Bandits Glossy Black | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/bandits-glossy-black.png` |
| Bandits Matte Black | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/bandits-matte-black.png` |
| Bandits Blue | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/bandits-blue.png` |
| Bandits Green | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/bandits-green.png` |
| Bandits Tortoise | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/bandits-tortoise.png` |
| Rasta Brown | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/rasta-brown.png` |
| Rasta Red | `C:/Users/RAS/projects/DuberyMNL/dubery-landing/assets/variants/rasta-red.png` |

---

## Self-Check (Before Saving)

- [ ] No banned words (R2) in `product_placement`, `visual_mood`, `objects_in_scene`
- [ ] No lens reflection descriptions (R3)
- [ ] Prompt opens with fidelity instruction (fidelity first)
- [ ] Prompt is 3-5 sentences total (not a wall of text)
- [ ] Dubery logo included in prompt (R1)
- [ ] `image_input` has local file path from the reference table
- [ ] `prompt` is a single dense narrative paragraph, not bullet points
- [ ] Setting is a specific, nameable Philippine location (R5)

---

## Execution Order

Process entries one at a time. Save immediately after each.

1. Read entry from `ugc_pipeline.json` where `status == "PENDING"` or `status == "CAPTION_APPROVED"`
2. Run internal scene analysis (silent)
3. Write the structured JSON prompt
4. Run Self-Check -- fix any violations
5. Save to `.tmp/{id}_ugc_prompt.json`
6. Update `ugc_pipeline.json`: `status = PROMPT_READY`, `prompt_file = ".tmp/{id}_ugc_prompt.json"`
7. Move to the next entry

Do NOT batch. Save each prompt immediately, then proceed.

---
name: dubery-prompt-reviewer
description: Review v2-generation prompt JSONs (brand-bold, brand-callout, brand-collection, UGC) against the v2 quality bar before image generation. Catches variety-bank fallbacks, fidelity violations, scene vagueness, angle repetition, and structural issues. Use after generating a batch to gate image gen spending.
argument-hint: "path to prompt JSON file, or folder of prompt JSONs"
---

# DuberyMNL v2 Prompt Reviewer

Reviews generated prompt JSONs from the v2 content skills and returns a graded report. Purpose: catch quality issues BEFORE burning Vertex AI credits on image generation.

Applies to v2 skills only:
- `dubery-brand-bold`
- `dubery-brand-callout`
- `dubery-brand-collection`
- `dubery-ugc-prompt-writer`

Does NOT apply to v1 skills (ad-creative, prompt-writer, infographic-ad) — those have their own validator chain (see `project_content_skill_iterations.md`).

---

## Input

One of:
- **Single file**: `contents/new/BOLD-001_output_prompt.json`
- **Folder**: `contents/new/` (reviews every `*_prompt.json` inside)
- **Comma-separated list**: `.tmp/UGC-20260407-005_ugc_prompt.json, contents/new/BOLD-001_output_prompt.json`

---

## Execution

1. Identify skill type from filename + JSON `task` field:
   - `task: "brand_bold"` → brand-bold rules
   - `task: "brand_callout"` → brand-callout rules
   - `task: "brand_collection"` → brand-collection rules
   - `task: "ugc_simulation"` → UGC rules
2. Read the full JSON
3. Run all checks V1-V7 (universal) + skill-specific checks
4. For each check: mark as ✅ PASS / ⚠️ PATCH / ❌ FAIL
5. Compute verdict:
   - Any FAIL → overall FAIL
   - No FAIL but any PATCH → overall PATCH
   - All PASS → overall PASS
6. Write report (format below)
7. Move to next file if batch

---

## Universal Checks (all skills)

### V1 — Product Fidelity (R2 banned words)

Scan these fields for any banned word:
- `visual_mood`, `prompt`
- `objects_in_scene` (if present)
- `scene.product_placement` (if present)
- `scene.atmosphere`, `scene.location`

**Banned tokens (case-insensitive, whole word match):**
- Frame colors: `black`, `blue`, `red`, `green`, `brown`, `amber`, `tortoise`, `camo`, `matte`, `glossy`, `dark`, `clear`
- Lens descriptors: `tinted`, `mirrored`, `warm-tinted`, `cool-tinted`, `gold`, `silver`, `smoke`, `honey`, `sapphire`
- Materials (as product descriptor): `metal frame`, `acetate`, `plastic`, `rubber`, `nylon`

**EXCEPTIONS (allowed):**
- Product model names used as IDENTIFIERS (e.g. "Outback Red" as a label is OK; "the red sunglasses" is NOT)
- Banned words describing NON-product elements (e.g. "dark wooden table", "golden hour light", "blue sky") — these describe the scene, not the product
- Material finish on product: `glossy | matte` — required, not banned
- Background colors for KNOCKOUT layout
- "dark" / "warm" / "cool" describing lighting or surfaces

**Judgment rule:** if the banned word is describing the PRODUCT (its appearance, frame, lens), it's a violation. If it's describing the SCENE (surface, lighting, backdrop), it's fine. Read context.

Verdict:
- ✅ PASS — no product-descriptive banned words
- ⚠️ PATCH — 1-2 borderline uses, suggest rewrite
- ❌ FAIL — explicit product color/material/lens description

### V2 — render_notes Template (R3)

Only applies to skills that have a `product.render_notes` field (brand-bold, brand-callout, brand-collection).

Check that `render_notes` contains all 5 fields IN ORDER:
1. `POSITION:`
2. `ANGLE:`
3. `LIGHTING:`
4. `LOGO:`
5. `REFERENCE:`

And that the final `REFERENCE:` line says "dictated entirely by the reference image(s)" or equivalent.

Verdict:
- ✅ PASS — all 5 fields present in order
- ⚠️ PATCH — fields out of order or 1 missing
- ❌ FAIL — template abandoned / free-form notes

### V3 — Lens Reflection Rule (R4)

Scan `prompt` and `visual_mood` for banned reflection phrases:
- "reflects the [specific]"
- "reflection of"
- "lens reflects"
- "scene reflected in"
- "mirrored reflection of"
- Any specific described reflection ("palm trees in the lens", "skyline visible")

Allowed:
- "lenses naturally catching the light and environment of the scene"
- "lenses naturally reflect the surrounding environment" (generic, not specific)

Verdict:
- ✅ PASS — no specific reflections described
- ❌ FAIL — specific reflection content described

### V4 — Variety Bank Usage

The prompt should show EVIDENCE that the agent picked specific options from the layout's variety banks, not defaulted to generic wording.

For brand-bold / brand-callout / brand-collection:
- Look for specific surface names (e.g. "dark walnut wooden table", "polished slate", "clean leather desk mat")
- Look for specific lighting descriptors (e.g. "warm window light from the left, afternoon", "dramatic overhead spotlight")
- Generic fallbacks = violation: "a wooden table", "soft light", "natural lighting", "a surface"

For UGC:
- Look for a specific nameable Philippine location (e.g. "Baler surf break", "España Boulevard", not "outdoors")
- Look for a specific lighting pick from the bank
- Look for a specific subject archetype (person-anchor) or specific surface (product-anchor)

Verdict:
- ✅ PASS — surface/lighting/location all specific, from banks
- ⚠️ PATCH — 1-2 generic fallbacks
- ❌ FAIL — mostly generic, bank picks not evident

### V5 — Angle Validity

Check `image_input[0]` — the primary product reference.

The batch randomizer handles angle variety across batches. The reviewer only checks for BANNED angles and collection consistency — it does NOT penalize `-1.png`.

- If path ends with `-2.png` or `-multi.png`: ❌ FAIL — "banned angle used (multi-view strip or composite confuses Gemini)"
- If path ends with `-1.png`, `-3.png`, `-4.png`: ✅ PASS
- Collection: all products must share the SAME angle suffix (L2 enforcement) — if mixed, ❌ FAIL

Verdict:
- ✅ PASS — valid single-view angle, consistent across collection
- ❌ FAIL — banned angle (-2 or -multi) used, or collection has mixed angles

### V6 — Prompt Length

Count sentences in the `prompt` field (split on `.`, ignore decimals).

- 3-10 sentences → ✅ PASS
- 11-14 sentences → ⚠️ PATCH — "over-described, trim to essentials"
- 15+ sentences → ❌ FAIL — "wall of text, the skill's Prompt Construction section said 5-9 max"
- Under 3 sentences → ⚠️ PATCH — "under-specified"

### V7 — Structural Integrity

- Valid JSON (parses without error)
- `task` field present and matches expected skill
- `image_input` is an array of existing file paths (verify each path exists on disk)
- `api_parameters` has `aspect_ratio`, `resolution`, `output_format`
- All forward slashes (no backslashes in paths)

Verdict:
- ✅ PASS — all fields present, all paths exist
- ⚠️ PATCH — field missing but recoverable
- ❌ FAIL — invalid JSON or paths don't exist

---

## Skill-Specific Checks

### brand-bold

- Headline is 3-5 words (count `text_elements[0].content` words, S2)
- "ONE pair" appears in the prompt (S5)
- Font reference present in `image_input` (S7)
- Maximum 2 text elements (S4)
- No sales language: BANNED tokens `price`, `order now`, `buy now`, `message us`, `p699`, `p1200`, `discount`, `cod`

### brand-callout

- 4-6 callouts in `callouts` array or text_elements of role "label" (C4)
- Each callout label is 4-5 words max (C4)
- Font reference in `image_input` (C6)
- No sales language
- "ONE pair" in prompt (C3)

### brand-collection

- `product.models` has 2-4 products (L4 — odd preferred, 2 only for UNBOX_FLATLAY)
- All products at same angle (L2) — verify `image_input` paths share the same angle suffix
- "ONE pair each" appears in prompt (arrangement rule)
- "All text in the bold italic sporty typeface" (L9)
- No sales language
- Text elements under ~15% estimate (L10 is best-effort, just check there are only 1-2 text elements)

### UGC (ugc_simulation)

- Prompt opens with naturalism instruction (contains "matching the style" OR "real pair photographed" OR "physical object, not a digital paste")
- `product.finish` is `glossy` or `matte` (explicitly stated)
- Prompt mentions finish in text
- `scene.location` is specific Philippine place (R5)
- If person-anchor: `subject` object present with description/action/emotion
- If product-anchor: no `subject` or subject describes scene only
- No lens reflection descriptions (R3 — already covered by V3)
- Physical realism: no floating, no arm bending mentions — scan for "floating", "hovering", "twisted"
- Dubery logo mentioned (R1)

---

## Report Format

For each reviewed file, output:

```
═══════════════════════════════════════════
REVIEW: {filename}
Skill: {skill_type}
Layout: {layout or scenario}

V1 Fidelity (R2 banned):     ✅ PASS | ⚠️ PATCH | ❌ FAIL
V2 render_notes (R3):        ✅ PASS | ⚠️ PATCH | ❌ FAIL | (N/A for UGC)
V3 Lens reflection (R4):     ✅ PASS | ❌ FAIL
V4 Variety bank usage:       ✅ PASS | ⚠️ PATCH | ❌ FAIL
V5 Angle randomization:      ✅ PASS | ⚠️ PATCH | ❌ FAIL
V6 Prompt length:            ✅ PASS | ⚠️ PATCH | ❌ FAIL  ({N} sentences)
V7 Structural integrity:     ✅ PASS | ⚠️ PATCH | ❌ FAIL
Skill-specific:              ✅ PASS | ⚠️ PATCH | ❌ FAIL

Issues found:
  - {specific issue 1}
  - {specific issue 2}

Verdict: ✅ PASS (ready for image gen)
       | ⚠️ PATCH (regenerate prompt, keep concept)
       | ❌ FAIL (skill-level bug — fix skill before regen)
═══════════════════════════════════════════
```

If batch review, end with a summary:
```
═══ BATCH SUMMARY ═══
Reviewed: 4 files
PASS:  2
PATCH: 1
FAIL:  1

Ready for image gen: {list of PASS filenames}
Needs patching:      {list of PATCH filenames + reasons}
Needs skill fix:     {list of FAIL filenames + root cause}
```

---

## Decision Rules

- **PASS verdict**: the prompt is clean enough to generate. RA can approve image gen.
- **PATCH verdict**: the concept is sound but execution has minor issues. Re-invoke the source skill on the same input to regenerate. The skill's variety banks should produce a better roll of the dice on the second run.
- **FAIL verdict**: something structural is wrong. Do NOT regenerate blindly — this usually means the skill has a bug (missing bank option, broken schema, bad banned-word rule). Fix the skill first, then regenerate.

---

## What NOT to check

- **Aesthetic quality** — reviewer only checks structural compliance. Only the generated image reveals aesthetic quality.
- **Caption alignment** (UGC) — the prompt is derived from caption intent, judging fit is a human call.
- **Product model accuracy** — can't verify product identity from text, only from the generated image.
- **Brand voice** — this is a quality bar for STRUCTURE, not TONE.

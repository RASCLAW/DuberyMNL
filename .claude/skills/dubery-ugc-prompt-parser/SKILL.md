---
name: dubery-ugc-prompt-parser
description: Parse a UGC image prompt into structured metadata for storage and traceability. Use after fidelity gatekeeper passes, before image generation.
disable-model-invocation: true
---

# DuberyMNL UGC Prompt Parser

Same format as dubery-prompt-parser but for UGC prompts. UGC has no overlays, no pricing, no CTAs -- those fields are omitted. Adds UGC-specific fields (subject, ugc_authenticity).

Reference: `.claude/skills/dubery-prompt-parser/SKILL.md`

## Role

Extract structured metadata from a completed UGC prompt JSON. No new information -- only what is explicitly present in the prompt narrative.

This runs after the fidelity gatekeeper passes. The output is saved alongside the prompt for traceability, search, and pipeline tracking.

## Input

A UGC prompt JSON file path (e.g., `.tmp/UGC-20260407-001_ugc_prompt.json`).

Read the `prompt` field (dense narrative paragraph) and all other JSON fields, then extract into the schema below.

## Output Schema

```json
{
  "content_type": "UGC",
  "visual_mood": "string",
  "scene": {
    "location": "string",
    "time_of_day": "string",
    "atmosphere": "string",
    "lighting": "string",
    "product_placement": "on face | held in hand | on surface | in bag | in flat lay",
    "format": "9:16 | 4:5"
  },
  "subject": {
    "type": "person | product_only",
    "gender": "male | female",
    "age_range": "string",
    "ethnicity": "Filipino",
    "expression": "string",
    "pose": "string",
    "clothing": "string"
  },
  "product": {
    "models": ["Outback Red"],
    "render_notes": "string",
    "instruction": "full verbatim product fidelity instruction block"
  },
  "ugc_authenticity": {
    "scenario_type": "string",
    "no_brand_overlays": true,
    "product_logo_only_as_worn": true,
    "no_overlays_instruction": "full verbatim no-overlays block"
  },
  "color_logic": "string",
  "objects_in_scene": ["string"],
  "negative_prompt": "full verbatim negative prompt",
  "image_input": ["string"],
  "api_parameters": {
    "aspect_ratio": "string",
    "resolution": "string",
    "output_format": "string"
  }
}
```

## Steps

1. Read the prompt JSON file
2. Parse the `prompt` narrative and extract each field
3. Copy `ugc_authenticity`, `negative_prompt`, `image_input`, `api_parameters` directly from the source JSON
4. Extract `product.instruction` as the full verbatim fidelity block from the prompt text
5. Extract `ugc_authenticity.no_overlays_instruction` as the full verbatim no-overlays block from the prompt text
6. Extract only what is explicitly stated -- do not infer or embellish
7. If a field is not present in the prompt, omit it entirely
8. Save output to `.tmp/{id}_ugc_parsed.json`
9. Update `ugc_pipeline.json`: add `parsed_file` field to the entry
10. Output ONLY valid JSON -- no markdown, no explanations

## Rules

- **Extraction only** -- no creative additions
- **Return ONLY valid JSON**
- **Omit missing fields** -- if something isn't in the prompt, leave it out
- `product.instruction` must be the full verbatim text of the fidelity block -- do not summarize
- `ugc_authenticity.no_overlays_instruction` must be the full verbatim no-overlays text
- `negative_prompt`, `image_input`, `api_parameters` are copied directly from the source JSON
- `color_logic` should describe the dominant color relationships in the scene
- `objects_in_scene` should list all notable objects mentioned in the prompt narrative

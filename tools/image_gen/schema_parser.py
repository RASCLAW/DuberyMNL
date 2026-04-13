"""
Schema Parser -- converts v2 skill output JSON into the Master Schema format.

The Master Schema uses IDENTITY_LOCK mode to preserve product fidelity
while allowing scene variables to change. Adds interaction_physics for
photorealistic blending (shadows, reflections, contact points).

Usage:
    python tools/image_gen/schema_parser.py <input_prompt.json> [output_schema.json]

If output is omitted, writes to same path with _schema.json suffix.
"""

import json
import sys
from pathlib import Path

# Camera lens presets by content type
CAMERA_PRESETS = {
    # Brand content -- premium product photography
    "brand_bold": "85mm prime lens, cinematic depth of field, sharp focus on subject",
    "brand_callout": "85mm prime lens, cinematic depth of field, sharp focus on subject",
    "brand_collection": "85mm prime lens, cinematic depth of field, sharp focus on all products equally",
    # UGC product-anchor -- natural product shot
    "ugc_product": "50mm lens, natural depth of field, sharp focus on subject",
    # UGC person-anchor selfie -- phone camera realism
    "ugc_person_selfie": "24mm wide-angle lens, front-camera perspective, natural phone camera look",
    # UGC person-anchor candid -- friend's phone
    "ugc_person_candid": "50mm lens, natural depth of field, candid back-camera feel",
}

SELFIE_SCENARIOS = {"SELFIE_OUTDOOR"}


def detect_content_type(data: dict) -> str:
    """Detect content type from the v2 skill JSON."""
    task = data.get("task", "")

    if task in ("brand_bold", "brand_callout", "brand_collection"):
        return task

    if task == "ugc_simulation":
        auth = data.get("ugc_authenticity", {})
        anchor = auth.get("anchor_type") or ("person" if data.get("subject") else "product")
        scenario = auth.get("scenario_type", "")

        if anchor == "person":
            if scenario in SELFIE_SCENARIOS:
                return "ugc_person_selfie"
            return "ugc_person_candid"
        return "ugc_product"

    return "brand_callout"  # fallback


def extract_location(data: dict) -> str:
    """Extract location from v2 JSON."""
    scene = data.get("scene", {})
    if scene.get("location"):
        return scene["location"]

    mood = data.get("visual_mood", "")
    if mood:
        return mood
    return "a clean surface in natural light"


def extract_placement(data: dict) -> str:
    """Extract product placement from v2 JSON."""
    scene = data.get("scene", {})
    if scene.get("product_placement"):
        return scene["product_placement"]

    product = data.get("product", {})
    render = product.get("render_notes", "")
    if "POSITION:" in render:
        pos = render.split("POSITION:")[1].split(".")[0].strip()
        return pos
    return "resting naturally on the surface"


def extract_lighting(data: dict) -> str:
    """Extract lighting from v2 JSON."""
    scene = data.get("scene", {})
    if scene.get("lighting"):
        return scene["lighting"]
    if scene.get("time_of_day"):
        return scene["time_of_day"]
    return "warm natural directional light"


def extract_text_elements(data: dict) -> dict | None:
    """Extract headline/text overlay info for brand content."""
    text_elements = data.get("text_elements", [])
    callouts = data.get("callouts", [])

    if not text_elements and not callouts:
        return None

    result = {}
    for te in text_elements:
        role = te.get("role", "")
        if role == "headline":
            result["headline"] = te.get("content", "")
            result["headline_position"] = te.get("position", "")
        elif role == "subtitle":
            result["subtitle"] = te.get("content", "")

    if callouts:
        result["callouts"] = [
            {"label": c.get("label", ""), "connector": c.get("connector", "")}
            for c in callouts
        ]

    return result if result else None


def parse_to_schema(data: dict) -> dict:
    """Convert v2 skill output to Master Schema format."""
    content_type = detect_content_type(data)
    location = extract_location(data)
    placement = extract_placement(data)
    lighting = extract_lighting(data)
    camera = CAMERA_PRESETS.get(content_type, CAMERA_PRESETS["ugc_product"])

    # Build master schema
    schema = {
        "control_protocol": {
            "version": "1.0",
            "mode": "IDENTITY_LOCK",
            "logic": "The pixels and geometry in INPUT_IMAGE_0 are the ground truth. Do not hallucinate or modify the product."
        },

        "subject_integrity": {
            "reference_source": "INPUT_IMAGE_0",
            "fidelity_requirements": [
                "Exact 1:1 geometric ratio and silhouette preservation",
                "Branding, logos, and text must be rendered exactly as positioned on source",
                "Material properties (reflectivity, matte finish, transparency) must match source",
                "Zero-tolerance for structural hallucination or design changes"
            ],
            "priority_weight": 1.0
        },

        "interaction_physics": {
            "blending_mode": "PHOTOREALISTIC_INTEGRATION",
            "lighting_logic": f"Cast realistic shadows from the product onto the {location} surface. Relight the product to match the scene lighting.",
            "reflection_logic": f"Render accurate environment reflections from {location} on the product's lens surfaces. Do NOT preserve reflections from the original reference photo.",
            "contact_points": "Ensure natural transition and grounding where the product touches surfaces -- slight shadow, surface contact, no floating.",
            "relight_instruction": "Use the product in INPUT_IMAGE_0 but digitally relight it to match the new location. The product must look like it was physically present when the photo was taken."
        },

        "scene_variables": {
            "location": location,
            "subject_placement": placement,
            "lighting_atmosphere": lighting,
            "camera_settings": camera,
        },

        "render_quality": {
            "resolution": "high",
            "color_space": "true-to-life",
            "background_blur_strength": 0.7 if "85mm" in camera else 0.4
        },

        # Pass through from v2 JSON
        "image_input": data.get("image_input", []),
        "api_parameters": data.get("api_parameters", {
            "aspect_ratio": "4:5",
            "resolution": "1K",
            "output_format": "jpg"
        }),
    }

    # Add text elements for brand content
    text_info = extract_text_elements(data)
    if text_info:
        schema["text_overlay"] = text_info
        # Include font and logo refs
        schema["text_overlay"]["font_instruction"] = "All text in the bold italic sporty typeface from the font reference image"
        schema["text_overlay"]["logo_instruction"] = "DuberyMNL logo matching the logo reference image"

    # Add subject info for UGC person-anchor
    subject = data.get("subject")
    if subject:
        schema["scene_variables"]["subject"] = {
            "description": subject.get("description", ""),
            "action": subject.get("action", ""),
            "emotion": subject.get("emotion", ""),
        }

    # Add atmosphere/objects
    scene = data.get("scene", {})
    if scene.get("atmosphere"):
        schema["scene_variables"]["atmosphere"] = scene["atmosphere"]

    objects = data.get("objects_in_scene", [])
    if objects:
        schema["scene_variables"]["objects_in_scene"] = objects

    return schema


def schema_to_prompt_text(schema: dict) -> str:
    """Convert the master schema to the prompt string sent to Gemini."""
    return "Generate an image based on the following JSON parameters and the attached reference image:\n\n" + json.dumps(schema, indent=2)


def main():
    if len(sys.argv) < 2:
        print("Usage: python schema_parser.py <input_prompt.json> [output_schema.json]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    data = json.loads(input_path.read_text(encoding="utf-8"))

    schema = parse_to_schema(data)

    # Determine output path
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.with_name(input_path.stem.replace("_prompt", "") + "_schema.json")

    # Write schema JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"Schema: {output_path}", file=sys.stderr)

    # Also write the prompt-ready version (what gets sent to Gemini)
    prompt_text = schema_to_prompt_text(schema)
    prompt_path = output_path.with_name(output_path.stem + "_prompt.txt")
    prompt_path.write_text(prompt_text, encoding="utf-8")
    print(f"Prompt: {prompt_path}", file=sys.stderr)
    print(f"Prompt length: {len(prompt_text)} chars", file=sys.stderr)

    # JSON output for pipeline
    print(json.dumps({
        "schema_path": str(output_path),
        "prompt_path": str(prompt_path),
        "content_type": schema.get("scene_variables", {}).get("camera_settings", ""),
        "image_input": schema.get("image_input", []),
    }))


if __name__ == "__main__":
    main()

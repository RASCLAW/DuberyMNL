---
name: ad-reverse-engineer
description: Reverse-engineer any ad image into a structured layer breakdown and production-ready NB2 prompt. Use when you have a reference ad and want to extract its design DNA to replicate the format.
---

# Ad Reverse Engineer

## Role
You are a creative director and prompt engineer. Given a reference ad image, you deconstruct it layer by layer, extract the design rules the creator followed, and output a reusable NB2 prompt template with clear variable placeholders.

## Input
- A reference ad image (file path or URL)
- Optional: target product or brand to adapt the template for

---

## Step 1: Visual Deconstruction

Analyze the image across 4 layers. Write down observations for each.

### Layer 1 — Backdrop
- What is the environment? (beach, street, studio, market, etc.)
- What is the surface the product rests on or the subject stands on?
- What is the light quality? (natural, directional, soft, harsh, warm, cool)
- What is in the background? (blurred, sharp, architectural, natural)

### Layer 2 — Hero
- What is the main subject? (person, product, flat-lay, etc.)
- How is it positioned in the frame? (centered, rule of thirds, diagonal)
- What angle is it shot from? (eye-level, top-down, 3/4, close-up)
- How does light interact with it? (reflections, shadows, highlights)
- What percentage of the frame does it occupy?

### Layer 3 — Graphics
- What design elements overlay the photo? (badges, arrows, bubbles, lines, shapes)
- What is the visual style? (hand-drawn, geometric, digital, photographic)
- How many elements? Are they grouped or scattered?
- What do they point to or frame?
- What accent elements exist? (sparkle lines, glow effects, corner treatments)

### Layer 4 — Text
- What text is present and in what order? (header, subhead, callouts, labels, CTA)
- What are the font weights and styles? (bold, regular, italic, all-caps, mixed case)
- Where is each text element positioned?
- What is the hierarchy? (what reads first, second, third)

---

## Step 2: Extract Design Rules

After completing the layer breakdown, identify the rules the designer was following:

- **Layout rule** — How are elements arranged? (e.g., Rule of Three, Z-pattern, symmetry)
- **Hierarchy rule** — How does the eye move through the ad? What creates visual priority?
- **Contrast technique** — What makes the hero stand out? (e.g., sharp photo vs. sketchy graphics)
- **Color rule** — What color logic is at work? (monochrome, complementary, brand-derived)
- **Accent rule** — What draws attention to specific areas? (sparkles, arrows, bold strokes)
- **Genre** — What type of ad is this? (product infographic, lifestyle shot, feature callout, catalog)

---

## Step 3: Build the NB2 Template

Using the layer breakdown and design rules, write a production-ready NB2 JSON prompt. Mark all variable fields with `[VARIABLE_NAME]` so they can be swapped per campaign.

Structure:

```json
{
  "prompt": "[Full descriptive prompt derived from layers 1-4 and design rules. Include scene, product, graphics layer, typography, and branding. Use [VARIABLE] placeholders for any element that will change per ad: product name, headline, feature text, price, etc.]",
  "negative_prompt": "[Comma-separated list of elements to exclude — derived from the design. e.g., digital vector bubbles, wrong callout style, altered product, blurry text]",
  "image_input": ["[REFERENCE_IMAGE_URL]"],
  "api_parameters": {
    "aspect_ratio": "[Derived from image — e.g., 4:5, 1:1, 16:9]",
    "resolution": "1K",
    "output_format": "jpg"
  }
}
```

### Variable Placeholder Table

List every `[VARIABLE]` in the prompt and describe what it represents:

| Variable        | Description                      | Example Value              |
|-----------------|----------------------------------|----------------------------|
| `[VARIABLE_NAME]` | What this field controls       | Example of a real value    |

---

## Step 4: Output

Return three things in order:

1. **Layer Breakdown** — structured observations from Step 1
2. **Design Rules** — extracted rules from Step 2
3. **NB2 Template** — completed JSON with variable placeholders from Step 3

---

## Hard Rules
1. Extract only what is actually in the image — do not invent elements that aren't there
2. Every design rule must trace back to a specific observation in the layer breakdown
3. Variable placeholders must be clearly marked — no ambiguity about what is fixed vs. swappable
4. The output template must be immediately usable — pass it to `generate_kie.py` after filling variables
5. If the image is a DuberyMNL ad, check `dubery-infographic-ad` skill first — the template may already be formalized

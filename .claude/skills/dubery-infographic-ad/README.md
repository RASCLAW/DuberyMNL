# dubery-infographic-ad

## What it is
A DuberyMNL-specific skill for generating product infographic ads in the hand-drawn callout bubble format. Design DNA extracted from RA's original Dubery Bandits ad via Gemini reverse-engineering.

## When to use
- Caption describes multiple product features (UV400, polarized, lightweight, etc.)
- You want a feature-focused ad instead of a lifestyle or person-anchored shot
- Equivalent to TYPE E in dubery-prompt-writer, but with a locked visual template

## Design DNA (Fixed Elements)
- Backdrop: sun-drenched tropical beach, blurred palm trees, turquoise water
- Surface: granite or marble, product resting on it
- Product: centered, angled 3/4 view
- Callouts: 3 hand-drawn oval bubbles (thin black imperfect stroke)
- Arrows: hand-drawn black arrows from each bubble pointing to a product feature
- Accents: sparkle/action lines above the leftmost bubble
- Layout: Callout 1 top-left, Callout 2 top-center, Callout 3 bottom-right
- Header: bold all-caps sans-serif at top center
- Hierarchy: bold all-caps benefit text inside bubble + smaller spec sub-text below bubble

## Variable Inputs
| Variable         | Description                                      |
|------------------|--------------------------------------------------|
| `product_model`  | e.g., "Dubery Bandits - Green"                   |
| `headline`       | Brand name + product slogan (e.g., "DUBERY MNL: POLARIZED CLEAR")  |
| `feature_1`      | Primary benefit (e.g., "POLARIZED") + spec (e.g., "100% UV400 Protection") |
| `feature_2`      | Second benefit + spec                            |
| `feature_3`      | Third benefit + spec                             |

## Output
A complete NB2 JSON prompt ready to pass to `tools/image_gen/generate_kie.py`.

## Related
- `dubery-prompt-writer` — full WF2 prompt writer (all content types)
- `ad-reverse-engineer` — the methodology used to extract this template
- `nano-banana-2` — NB2 schema reference

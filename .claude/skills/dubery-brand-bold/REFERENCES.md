# References -- dubery-brand-bold

## Reads
- contents/assets/product-refs/{model}/ (product reference photos)
- contents/assets/fonts/DUBERY-FONTS.png (brand font alphabet)
- contents/assets/logos/dubery-logo.jpg (logo, black bg default)
- contents/assets/logos/dubery-logo.png (logo, white bg for KNOCKOUT variant)

## Writes
- contents/new/{id}_prompt.json (structured prompt)
- contents/new/{id}_output.png (generated image via Vertex AI)

## Depends On
- generate_vertex.py (Gemini 3.1 Flash image generation)

## Referenced By
- dubery-brand-content (orchestrator routes to this skill)

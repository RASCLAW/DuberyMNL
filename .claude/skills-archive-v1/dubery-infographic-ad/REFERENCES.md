# References -- dubery-infographic-ad

## Reads
- Product model + colorway (input or from .tmp/pipeline.json)
- Feature descriptions (input or standard Dubery specs)
- Reference image URL (product photo)

## Writes
- NB2 JSON prompt (completed with variables substituted)

## Depends On
- ad-reverse-engineer (if reverse-engineering similar format first)
- generate_kie.py (receives completed JSON)

## Referenced By
- dubery-prompt-writer (when caption mentions infographic/callout style)

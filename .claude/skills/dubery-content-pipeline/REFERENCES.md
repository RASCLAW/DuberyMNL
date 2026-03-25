# References -- dubery-content-pipeline

## Reads
- .tmp/pipeline.json (last 20 entries for context)
- dubery-caption-gen SKILL.md (caption rules)
- dubery-prompt-writer SKILL.md (prompt rules)

## Writes
- .tmp/pipeline.json (captions: APPROVED)
- .tmp/{id}_prompt_structured.json (one per caption)

## Depends On
- dubery-caption-gen (caption generation rules)
- dubery-prompt-writer (prompt generation, parallel agents)
- dubery-prompt-validator (validates output)

## Referenced By
- CLAUDE.md (trigger: "content pipeline")
- Stops at PROMPT_READY (no image gen, no API cost)

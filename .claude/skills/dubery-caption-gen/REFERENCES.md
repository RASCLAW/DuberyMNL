# References -- dubery-caption-gen

## Reads
- .tmp/rejected_captions.json (calibration -- avoid rejected combos)
- .tmp/pipeline.json (last 10+ APPROVED captions to avoid repeats)
- .tmp/feedback.json (batch-level creative direction from RA)
- research/filipino_caption_voice.md (voice reference)

## Writes
- .tmp/pipeline.json (appends 15 captions, status: APPROVED)

## Depends On
- python tools/pipeline/validate_wf1.py (batch validator)
- Email system (sends review email after validation)

## Referenced By
- dubery-content-pipeline (invokes caption rules)
- dubery-content-pipeline-full (invokes caption rules)
- feedback_duberymnl_patterns.md (WF1 rules)

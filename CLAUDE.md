# DuberyMNL -- Project Instructions

DuberyMNL-specific context. Global EA identity and rules live in `~/.claude/CLAUDE.md` and `~/.claude/rules/`.

## Tools Directory

Production Python scripts in `tools/`. Always check here before building new ones.

| Directory | Purpose |
|-----------|---------|
| `pipeline/` | Content pipeline orchestration (WF2, UGC, regenerate, validate) |
| `image_gen/` | kie.ai / NB2 image generation + review server |
| `captions/` | Caption review server + email |
| `facebook/` | Post scheduling (single + batch) |
| `meta_ads/` | Ad insights, creative upload, ad staging |
| `sheets/` | Google Sheets read/write/setup |
| `drive/` | Google Drive uploads |
| `chatbot/` | Messenger webhook bot (ON HOLD) |
| `landing/` | Landing page data export |
| `upwork/` | Job scout + market intel |
| `notion/` | Pipeline sync to Notion |

## Pipeline Data Flow

```
Google Sheet (source of truth)
  -> WF1: Caption gen + approval
  -> WF2: Image gen (kie.ai / NB2)
  -> WF3a: Auto-post to Facebook (blocked on Meta verification)
  -> WF3b: Meta Ads staging (manual)
```

- Pipeline Sheet = source of truth. pipeline.json = local cache. Sync before/after.
- Use fcntl file locking on pipeline.json.
- No manual DB injection -- all data flows through the pipeline.

## Skills (DuberyMNL-specific)

| Skill | Purpose |
|-------|---------|
| `/dubery-content-pipeline` | Captions to image prompts (no review) |
| `/dubery-content-pipeline-full` | Full pipeline with image gen + review |
| `/dubery-prompt-writer` | Structured JSON prompt generation |
| `/dubery-ugc-prompt-writer` | UGC-style prompt generation (agent) |
| `/dubery-infographic-ad` | Product infographic ad generation |
| `/dubery-chatbot` | Messenger bot persona + guidelines |
| `/dubery-caption-gen` | Caption generation |
| `/dubery-prompt-parser` | Parse image prompts |
| `/dubery-prompt-validator` | Validate prompts |
| `/ad-reverse-engineer` | Reverse-engineer reference ads |

## Commands

- `/pipeline` -- Run content pipeline end to end

## Agents (subagent_type)

- `dubery-content` -- Content pipeline specialist (Sonnet)
- `dubery-ads` -- Meta ads analysis and staging (Sonnet)
- `dashboard` -- ra-dashboard UI and data (Sonnet)

## kie.ai Quirks

- Google Drive URLs don't work for reference images. Need CDN pre-upload.
- lh3.googleusercontent.com/d/{ID} works as CDN URL.
- Logo URL breaks the API -- don't include it.
- Default resolution is 2K.

## File Rules

- `.tmp/` -- Temporary files (regenerated as needed, gitignored)
- `output/` -- Generated pipeline images
- `dubery-landing/` -- Live landing page on Vercel (duberymnl.com)
- `.env` -- All secrets (gitignored)
- `decisions/log.md` -- DuberyMNL-specific decision log
- `references/` -- DuberyMNL-specific reference docs
- `archives/` -- Old organizational material (pre-EA-rebuild)

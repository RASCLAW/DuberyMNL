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
| `/dubery-ugc-prompt-writer` | UGC-style prompt generation (agent) |
| `/dubery-chatbot` | Messenger bot persona + guidelines |
| `/dubery-caption-gen` | Caption generation |
| `/dubery-ugc-caption-gen` | UGC caption generation |
| `/dubery-prompt-parser` | Parse image prompts |
| `/dubery-ugc-prompt-parser` | Parse UGC prompts |
| `/dubery-prompt-reviewer` | v2 quality gate -- run before image gen spend |
| `/dubery-brand-content` | Brand content orchestrator -- routes to sub-skills |
| `/dubery-brand-callout` | Feature callout images (5 layouts) |
| `/dubery-brand-bold` | Bold statement images (4 layouts) |
| `/dubery-brand-collection` | Collection showcase images (5 layouts + carousel) |
| `/dubery-ugc-pipeline` | End-to-end UGC pipeline |
| `/ad-reverse-engineer` | Reverse-engineer reference ads |

Archived v1 skills (in `.claude/skills-archive-v1/`): dubery-ad-creative, dubery-prompt-writer, dubery-prompt-validator, dubery-infographic-ad, dubery-ugc-fidelity-gatekeeper

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

## Verification

After making changes, verify your work:

- **Pipeline tools:** `python tools/status.py` -- confirms pipeline.json loads and prints status counts
- **Sheet access:** `python tools/sheets/read_sheet.py` -- confirms Google Sheets auth works
- **Image gen:** `python tools/image_gen/generate_image.py --dry-run` -- validates prompt without spending credits
- **Landing page:** Open `dubery-landing/index.html` in browser or check with Playwright
- **Env health:** Confirm `.env` exists and has required keys: `python -c "from dotenv import load_dotenv; load_dotenv(); import os; [print(f'{k}: {'SET' if os.getenv(k) else 'MISSING'}') for k in ['ANTHROPIC_API_KEY','KIE_AI_API_KEY','PAGE_ACCESS_TOKEN']]"`
- **After any tool edit:** Run the tool standalone to confirm it exits cleanly

No test suite exists yet. When writing new tools, add basic smoke tests inline (`if __name__ == '__main__'` block).

## File Rules

- `.tmp/` -- Temporary files (regenerated as needed, gitignored)
- `contents/` -- All generated content (ads, ugc, brand, carousel, product)
- `contents/new/` -- Staging area for newly generated images (pre-review)
- `contents/failed/` -- Rejected images
- `dubery-landing/` -- Live landing page on Vercel (duberymnl.com)
- `.env` -- All secrets (gitignored)
- `decisions/log.md` -- DuberyMNL-specific decision log
- `references/` -- DuberyMNL-specific reference docs
- `archives/` -- Old organizational material (pre-EA-rebuild)

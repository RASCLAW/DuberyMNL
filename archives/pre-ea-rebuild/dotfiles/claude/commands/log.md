---
name: log
description: Session closeout -- summarize the session, append to PROJECT_LOG.md, commit and push.
---

Close out the current session:

1. Ask RA: "What did we accomplish this session?" if not already stated.
2. Append a new entry to `PROJECT_LOG.md` in the relevant project using this format:
   ```
   ## Session [N] -- [YYYY-MM-DD] ([short title])

   ### What
   - Bullet points of what was built, fixed, or decided

   ### Decisions
   - Any non-obvious choices made and why (only if applicable)

   ### Deployed
   - What's live and where (only if applicable)
   ```
3. Stage and commit: `git add -A && git commit -m "log: session [N] -- [short title]"`
4. Push: `git push`
5. Confirm: "Session [N] logged and pushed."

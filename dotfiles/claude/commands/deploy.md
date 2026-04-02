---
name: deploy
description: Deploy the current project to its hosting target. Works for ra-dashboard (Vercel) and any other configured deploy targets.
---

Deploy the current project:

1. Check which project is active (read `package.json` or `deploy.sh` if present).
2. Run the deploy command:
   - **ra-dashboard**: `bash deploy.sh` or `vercel --prod`
   - **ras-portfolio**: `vercel --prod`
   - **DuberyMNL tools**: not deployed -- confirm with RA before proceeding
3. Confirm the deploy URL and report it.
4. If deploy fails, read the full error before retrying.

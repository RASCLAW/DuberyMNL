---
name: vscode-tunnel
description: Start the VSCode remote tunnel (dubery-dev) so you can connect from vscode.dev or any browser.
argument-hint: [optional: force-restart]
allowed-tools: Bash
---

# VSCode Remote Tunnel

## What This Skill Does

Starts the VSCode tunnel named `dubery-dev` so RA can connect remotely via `vscode.dev`.

---

## Steps

1. Check if tunnel is already running:

```bash
pgrep -fa code-tunnel
```

2. If a stale lock exists or you need to force-restart, clear it first:

```bash
rm -f ~/.vscode/cli/tunnel-stable.lock && pkill -f code-tunnel 2>/dev/null; sleep 1
```

3. Start the tunnel in the background:

```bash
code-tunnel tunnel --name dubery-dev --accept-server-license-terms &
```

4. Wait 3 seconds, then confirm it started:

```bash
sleep 3 && pgrep -fa code-tunnel
```

5. Tell RA:
   - Tunnel name: `dubery-dev`
   - How to connect: go to `vscode.dev` → Remote Explorer → Connect to Tunnel → `dubery-dev`
   - If it fails: run the force-restart step above and try again

---

## Notes

- Tunnel runs as a background process in WSL2
- It will stay alive as long as the WSL session is open
- If the tunnel stops responding, do the force-restart (step 2) and re-run step 3

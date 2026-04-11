# Cloudflare Migration Runbook

**Goal:** Move `duberymnl.com` DNS from Namecheap → Cloudflare, then create a named Cloudflare Tunnel `chatbot.duberymnl.com` → `localhost:8080` for the chatbot.

**Status:** Prep complete (session 105). Ready to execute in a dedicated session.

**Estimated time:** 45-60 min focused work, most of it waiting on DNS propagation and Email Routing verification.

---

## Current State (captured 2026-04-11)

### DNS records to mirror on Cloudflare

| Type | Name | Value | TTL | Purpose | Migration action |
|---|---|---|---|---|---|
| NS | @ | `dns1.registrar-servers.com` | — | Namecheap auth | **REPLACE** at registrar with Cloudflare NS |
| NS | @ | `dns2.registrar-servers.com` | — | Namecheap auth | **REPLACE** at registrar with Cloudflare NS |
| A | @ | `76.76.21.21` | auto | Vercel landing page | **MIRROR** on Cloudflare |
| CNAME | www | `cname.vercel-dns.com` | auto | Vercel landing page | **MIRROR** on Cloudflare |
| MX (×5) | @ | `eforward{1-5}.registrar-servers.com` | — | Namecheap email forwarding | **REPLACE** with Cloudflare Email Routing MX |
| TXT | @ | `v=spf1 include:spf.efwd.registrar-servers.com ~all` | — | Namecheap SPF | **REPLACE** with Cloudflare Email Routing SPF |

### Records to add

| Type | Name | Value | Purpose |
|---|---|---|---|
| CNAME | chatbot | `<tunnel-uuid>.cfargotunnel.com` | Named tunnel → local Flask on port 8080 |

### What's already done

- `cloudflared 2026.3.0` installed at `C:\Users\RAS\bin\cloudflared.exe`
- Local Flask chatbot code in `cloud-run/` refactored and tested (session 101)
- IPv4 socket monkey-patch in place (no IPv6 latency issues on Python requests)
- `~/.cloudflared/` does NOT exist yet — `cloudflared tunnel login` will create it

### What's NOT done (blockers to resume)

- Chatbot not currently running (local Flask + cloudflared Quick Tunnel both DOWN after session 102)
- No Cloudflare account yet (or unverified if signed up earlier)
- Namecheap email forwarding tied to Namecheap NS — must migrate email BEFORE cutting nameservers

---

## Pre-flight checks (do BEFORE the session)

1. **Confirm Vercel domain setup** still points at `duberymnl.com` — log in to Vercel, check the project's Domains tab. Record the exact A/CNAME Vercel expects.
2. **Confirm email destination** `sarinasmedia@gmail.com` is accessible (you'll need to click a Cloudflare verification link).
3. **Check if `ras@duberymnl.com` is currently verified on any service** (Vercel, Meta, Anthropic, etc.). These services send verification emails rarely, so a brief email outage probably doesn't break them — but be aware.
4. **Namecheap dashboard access** — make sure you can log in. If 2FA, have the OTP device ready.

---

## Step-by-step execution

### PHASE 1: Cloudflare account + zone setup (15 min, zero-risk)

1. Sign in / sign up at `dash.cloudflare.com` (free plan).
2. Click **Add a Site** → enter `duberymnl.com` → select **Free** plan.
3. Cloudflare auto-scans existing DNS and shows detected records. **Review:**
   - A @ → 76.76.21.21 should be there. If not, add manually.
   - CNAME www → cname.vercel-dns.com should be there. If not, add manually.
   - The 5 MX eforward records and the SPF TXT will be imported. **LEAVE THEM for now** — don't delete until Phase 2.
4. Cloudflare shows the two nameservers you'll need to paste into Namecheap. **Copy them** — example format: `abc.ns.cloudflare.com` + `xyz.ns.cloudflare.com`.
5. **DO NOT click "Continue" / "Check Nameservers" yet.** That triggers the activation flow. We need Email Routing set up first.

### PHASE 2: Cloudflare Email Routing setup (10 min, zero-risk, doesn't touch live DNS yet)

1. In Cloudflare for `duberymnl.com`, go to **Email → Email Routing**.
2. Click **Enable Email Routing**.
3. Under **Destination addresses**, add `sarinasmedia@gmail.com`. Cloudflare sends a verification email — click the link from your gmail.
4. Under **Routing rules**, create:
   - **Custom address:** `ras@duberymnl.com` → forward to `sarinasmedia@gmail.com`
   - (Optional) **Catch-all:** `*@duberymnl.com` → forward to `sarinasmedia@gmail.com` — catches anything addressed to the domain. Recommended for verification-only use.
5. Cloudflare will show you the MX records and SPF TXT it wants on the zone. It may offer an **automatic add** button. Click it — this **REPLACES the eforward MX + old SPF** with Cloudflare's. Because nameservers are still Namecheap, this change only lives on Cloudflare for now — won't take effect until step 3.
6. Verify the Cloudflare DNS panel now shows:
   - 3 MX records pointing to `route{1-3}.mx.cloudflare.net` (or similar)
   - 1 TXT SPF: `v=spf1 include:_spf.mx.cloudflare.net ~all`
   - A @ → 76.76.21.21 (Vercel) still intact
   - CNAME www → cname.vercel-dns.com still intact
7. **Do NOT proceed until all 4 record types above are confirmed on Cloudflare.**

### PHASE 3: Nameserver cut-over (5 min + wait, REVERSIBLE within 24h)

**This is the flip. Before proceeding, the Cloudflare zone must have: A @, CNAME www, MX (Cloudflare routes), TXT SPF (Cloudflare).**

1. Log in to Namecheap → **Domain List** → `duberymnl.com` → **Manage** → **Nameservers**.
2. Change from **Namecheap BasicDNS** → **Custom DNS**.
3. Paste the two Cloudflare nameservers from Phase 1 step 4.
4. Save.
5. Back on Cloudflare, click **Check Nameservers**. Propagation can be 5 min to 24 hrs. Don't panic if it says "not detected yet" — refresh every few minutes.
6. In parallel, test:
   - `nslookup duberymnl.com 8.8.8.8` should eventually show A record 76.76.21.21 (unchanged)
   - `nslookup -type=NS duberymnl.com 8.8.8.8` should eventually show Cloudflare nameservers
   - `https://duberymnl.com` in a browser should still load (Vercel landing page)
   - Send a test email from your phone to `ras@duberymnl.com`. It should land in `sarinasmedia@gmail.com` within a minute once propagation finishes.

**Rollback plan if something breaks within propagation window:**
Change Namecheap nameservers back to `dns1.registrar-servers.com` + `dns2.registrar-servers.com`. DNS will revert (another propagation delay). No data loss — Namecheap records are unchanged.

### PHASE 4: Named Cloudflare Tunnel setup (10 min, zero-risk, only after Phase 3 shows Cloudflare NS active)

1. In terminal:
   ```bash
   cloudflared tunnel login
   ```
   This opens a browser. Authorize for `duberymnl.com`. Drops `~/.cloudflared/cert.pem`.

2. Create the tunnel:
   ```bash
   cloudflared tunnel create dubery-chatbot
   ```
   Outputs a tunnel UUID. Copy it. Also drops `~/.cloudflared/<uuid>.json` (tunnel credentials).

3. Route DNS (Cloudflare auto-creates the CNAME for you):
   ```bash
   cloudflared tunnel route dns dubery-chatbot chatbot.duberymnl.com
   ```

4. Create `~/.cloudflared/config.yml`:
   ```yaml
   tunnel: <uuid-from-step-2>
   credentials-file: C:\Users\RAS\.cloudflared\<uuid>.json

   ingress:
     - hostname: chatbot.duberymnl.com
       service: http://localhost:8080
     - service: http_status:404
   ```

5. Start the local Flask chatbot in one terminal:
   ```bash
   cd c:/Users/RAS/projects/DuberyMNL/cloud-run
   python messenger_webhook.py
   ```
   (or however session 101 started it — double-check `PROJECT_LOG.md` session 101 entry for the exact command)

6. Start the tunnel in another terminal:
   ```bash
   cloudflared tunnel run dubery-chatbot
   ```

7. Test:
   - `https://chatbot.duberymnl.com/` should return the Flask root (404 is fine, just not a cloudflared error page)
   - `https://chatbot.duberymnl.com/webhook` should return Meta's expected challenge response
   - `https://chatbot.duberymnl.com/chat-test` should load the test webapp

### PHASE 5: Auto-start on PC logon (5 min, optional but strongly recommended)

Two services need to auto-start:
1. The Flask chatbot (`python messenger_webhook.py`)
2. The cloudflared tunnel (`cloudflared tunnel run dubery-chatbot`)

Options (pick one):
- **Windows Task Scheduler** with "At log on of RAS" trigger — run each as a batch file
- **NSSM** (Non-Sucking Service Manager) to wrap each as a Windows service — same pattern as the existing `dubery-dev` VSCode tunnel (see `~/.claude/projects/c--Users-RAS-projects-DuberyMNL/memory/reference_vscode_tunnel.md`)
- **cloudflared has built-in service mode:** `cloudflared service install` — installs as Windows service automatically

Recommended: `cloudflared service install` for the tunnel + Task Scheduler for Flask.

### PHASE 6: Meta webhook re-wire (5 min)

1. Facebook Developer Console → DuberyMNL app → Messenger → Webhooks
2. Change callback URL from the old quick-tunnel URL to:
   ```
   https://chatbot.duberymnl.com/webhook
   ```
3. Click **Verify and Save**. Meta hits the URL with a challenge — Flask must be running.
4. Subscribe to `messages`, `messaging_postbacks` (already configured from before — just confirm).
5. Send a test message to the DuberyMNL Facebook page. Check `cloud-run/` logs for inbound webhook hit.

---

## Post-cutover checks

- [ ] `https://duberymnl.com` loads (Vercel landing)
- [ ] `https://www.duberymnl.com` loads
- [ ] `https://chatbot.duberymnl.com/` returns Flask response
- [ ] Test email to `ras@duberymnl.com` lands in `sarinasmedia@gmail.com`
- [ ] Test Messenger DM to DuberyMNL Facebook page gets a real bot reply
- [ ] Reboot PC → confirm Flask + cloudflared both auto-start
- [ ] (Optional) Set up UptimeRobot free monitor on `https://chatbot.duberymnl.com/` → alerts your email if the tunnel goes down

## What comes after (not part of this runbook)

Per `current-priorities.md` recovery path, once the tunnel is live:
- (f) UptimeRobot monitoring
- (g) CRM test-data cleanup (wipe TEST_ rows from the 4 CRM tabs before capturing real data)
- (h) Unpause boosted ads
- (i) 1 week of clean production data capture for the RAS Creative SOLUTIONS case study

---

## Open questions to resolve before executing

1. **Does the `cloudflared tunnel login` browser auth work on this PC?** It needs a browser that can reach the Cloudflare dashboard AND write back to a localhost callback. Usually fine, but flag if behind a proxy.
2. **Is there a Cloudflare account already?** If so, which email. If not, sign up with what — `sarinasmedia@gmail.com`?
3. **Namecheap 2FA?** If yes, have the OTP device ready.
4. **`ras@duberymnl.com` currently verified on any service we should not break?** (Vercel, Meta, Anthropic Console, etc.) — acceptable if yes, because Cloudflare Email Routing catches up within minutes of propagation.

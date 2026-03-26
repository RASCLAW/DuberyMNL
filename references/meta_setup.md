# Meta Business Setup

## Objective
Configure Meta Business Manager, Ad Account, and API tokens needed for WF3 (Ad Publishing).

## Do This Once Before Running WF3

### Step 1 — Meta Business Manager
1. Go to [business.facebook.com](https://business.facebook.com)
2. Create a Business Manager (or confirm DuberyMNL's Page is already linked)
3. Add the DuberyMNL Facebook Page to Business Manager if not already done

### Step 2 — Ad Account
1. In Business Manager → Accounts → Ad Accounts
2. Create a new Ad Account (or add existing one)
3. Note the **Ad Account ID** — it looks like `act_1234567890`
4. Add to `.env`: `META_AD_ACCOUNT_ID=act_1234567890`

### Step 3 — Facebook Page ID
1. Go to your Facebook Page → About (or Page Settings)
2. Scroll down to find the **Page ID** (numeric)
3. Add to `.env`: `META_PAGE_ID=123456789`

### Step 4 — Create a Meta App
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create a new App → Business type
3. Add the **Marketing API** product to the app
4. Go to App → Settings → Basic → note `App ID` and `App Secret`

### Step 5 — Generate Access Token
Option A — System User Token (recommended for automation):
1. Business Manager → Settings → System Users
2. Create a System User with ADMIN role
3. Assign the System User to:
   - The DuberyMNL Page (with Advertiser role)
   - The Ad Account (with Advertiser role)
4. Generate Token → select your App → check permissions:
   - `ads_management`
   - `ads_read`
   - `pages_read_engagement`
   - `pages_manage_posts` (for organic posting)
5. Copy the token → add to `.env`: `META_ADS_ACCESS_TOKEN=...`

### Step 5b — Page Access Token (for organic posting / WF3a)
1. With a User Token that has `pages_manage_posts`, call:
   `GET /{PAGE_ID}?fields=access_token&access_token={USER_TOKEN}`
2. Exchange for long-lived:
   `GET /oauth/access_token?grant_type=fb_exchange_token&client_id={APP_ID}&client_secret={APP_SECRET}&fb_exchange_token={TOKEN}`
3. Add to `.env`: `META_PAGE_ACCESS_TOKEN=...`
4. This token is non-expiring when derived from a long-lived User Token.

Option B — Page Access Token (simpler but expires):
1. Go to [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer)
2. Select your App → Generate User Token
3. Request permissions: `ads_management`, `ads_read`, `pages_manage_ads`
4. Exchange for a long-lived token (valid 60 days):
   ```
   GET https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token
     &client_id={APP_ID}&client_secret={APP_SECRET}&fb_exchange_token={SHORT_TOKEN}
   ```
5. Add to `.env`: `META_ADS_ACCESS_TOKEN=...`

### Step 6 — Verify Setup
Test with a quick API call:
```bash
curl "https://graph.facebook.com/v21.0/me/adaccounts?access_token=YOUR_TOKEN"
```
You should see your ad account listed.

---

## Token Refresh

System User tokens don't expire — use Option A above for set-and-forget automation.

If you used Option B (Page Access Token):
- Token expires after ~60 days
- Repeat Step 5 to generate a new one
- Update `.env`: `META_ADS_ACCESS_TOKEN=NEW_TOKEN`

Signs that your token has expired:
- WF3 fails with `Error validating access token` or HTTP 400
- Meta API returns `OAuthException`

---

## Troubleshooting

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `Invalid OAuth access token` | Token expired or wrong | Regenerate token (Step 5) |
| `Ad account does not exist` | Wrong account ID | Double-check `META_AD_ACCOUNT_ID` in .env |
| `Pages must have at least one admin` | Page not linked to Business Manager | Complete Step 1 |
| `Unsupported post request` | Endpoint or API version mismatch | Check `GRAPH_API_VERSION` in create_campaign.py |

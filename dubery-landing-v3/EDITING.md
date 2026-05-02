# v3 Landing — Editing Guide

How to edit product galleries and content on the v3 landing page.

---

## Local server

Start it once per session:

```powershell
Start-Process python -ArgumentList '-m','http.server','8300' -WorkingDirectory 'C:\Users\RAS\projects\DuberyMNL\dubery-landing-v3' -WindowStyle Hidden
```

- **Local:** http://localhost:8300
- **Public (CF tunnel):** https://v3.duberymnl.com (requires cloudflared running)

---

## Editing a product gallery

### 1. Open the product page

Go to:
```
http://localhost:8300/products/item.html?slug=<slug>
```

Slugs: `bandits-matte-black`, `bandits-glossy-black`, `bandits-green`, `bandits-blue`, `bandits-tortoise`, `outback-black`, `outback-blue`, `outback-red`, `outback-green`, `rasta-red`, `rasta-brown`

### 2. Enter edit mode

Click the **✎ Edit** button in the bottom-right corner of any product page.

Or add `&edit` to the URL manually.

### 3. Edit the gallery

| Action | How |
|--------|-----|
| **Add photos** | Click **+** button in the thumb strip. Multi-select supported. |
| **Remove a photo** | Hover over a thumb → click **×** |
| **Reorder photos** | Drag thumbs left/right |
| **Replace a photo** | Click any image (main or thumb) → pick file |

### 4. Save

Click **Save data.json** (green button). A `data.json` file downloads to your Downloads folder.

> ⚠️ The saved file uses your uploaded filenames as paths (e.g. `../assets/catalog/my-photo.jpg`). The images are NOT embedded — you need to copy them to `assets/catalog/` (see below).

### 5. Hand off to Claude

Drop the `data.json` file in the chat and tell Claude which product you edited. Claude will:
- Detect which product changed
- Search `contents/ready/` for any missing files and copy them to `assets/catalog/`
- Merge the updated gallery into the project `data.json`
- Report any files it couldn't find

If a file is missing from `contents/ready/`, tell Claude the full path.

### 6. Copy any newly uploaded files

If you uploaded brand-new images (not from `contents/ready/`), copy them manually:

```
C:\Users\RAS\projects\DuberyMNL\dubery-landing-v3\assets\catalog\
```

---

## File locations

| What | Where |
|------|-------|
| Product data (galleries, prices, copy) | `products/data.json` |
| All catalog images | `assets/catalog/` |
| Approved image bank | `contents/ready/` (searched automatically) |
| Gallery editor script | `products/item-editor.js` |

---

## Catalog card thumbnail vs gallery

The **shop page** (`/products/`) uses `hero` and `hover` fields from `data.json` — **not** `gallery[0]`.

If you update a product's gallery and want the shop card to reflect the new primary image, ask Claude to update the `hero` and `thumb` fields in `data.json` to match.

---

## Committing changes

After Claude processes your data.json drop:

```bash
git add dubery-landing-v3/products/data.json dubery-landing-v3/assets/catalog/
git commit -m "v3: update <product> gallery"
git push
```

Or just say "commit and push" and Claude will handle it.

"""
Stage 2 — Tag approved images with use-case tags.

Scans contents/ready/ (approved images from Stage 1) and lets RA attach
multi-select tags: POST, STORY, AD, LANDING, ARCHIVE.

Non-destructive: files stay in place. Tags stored in contents/ready/manifest.json.
Downstream tools (story cron, ad uploader) query the manifest by tag.

Usage:
    python tools/image_gen/image_tag_approved.py                       # port 8124
    python tools/image_gen/image_tag_approved.py --port 8125
    python tools/image_gen/image_tag_approved.py --tunnel              # + ngrok URL
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, render_template_string, send_from_directory, abort

PROJECT_DIR = Path(__file__).parent.parent.parent
READY_DIR = PROJECT_DIR / "contents" / "ready"
MANIFEST_PATH = READY_DIR / "manifest.json"
IMG_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
TAGS = ["POST", "STORY", "AD", "LANDING", "ARCHIVE"]

app = Flask(__name__)


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    try:
        with MANIFEST_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"manifest read failed: {e}", file=sys.stderr)
        return {}


def save_manifest(manifest: dict) -> None:
    READY_DIR.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST_PATH.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    tmp.replace(MANIFEST_PATH)


def scan_ready_images() -> list[dict]:
    """List all images directly in contents/ready/ (not subfolders)."""
    manifest = load_manifest()
    if not READY_DIR.exists():
        return []
    out = []
    for path in sorted(READY_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMG_EXTENSIONS:
            continue
        entry = manifest.get(path.name, {})
        out.append({
            "name": path.name,
            "size_kb": path.stat().st_size // 1024,
            "modified": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            "tags": entry.get("tags", []),
        })
    return out


GALLERY_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DuberyMNL Image Tagging — Stage 2</title>
<style>
  :root {
    --bg: #0f0f10;
    --panel: #1a1a1c;
    --ink: #ecebe6;
    --ink-dim: #9a978f;
    --accent: #ff7a2f;
    --green: #4dd59b;
    --line: #2a2a2e;
    --tag-post: #4dd59b;
    --tag-story: #d09cff;
    --tag-ad: #ff7a2f;
    --tag-landing: #5ac8fa;
    --tag-archive: #9a978f;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: var(--bg); color: var(--ink);
    font: 14px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  header { position: sticky; top: 0; background: var(--panel); border-bottom: 1px solid var(--line);
    padding: 12px 20px; z-index: 20; display: flex; align-items: center; gap: 16px; }
  header h1 { font-size: 16px; margin: 0; flex: 1; }
  .meta-text { color: var(--ink-dim); font-size: 13px; }
  .filter-chips { display: flex; gap: 6px; }
  .filter-chip { background: transparent; color: var(--ink-dim); border: 1px solid var(--line);
    padding: 4px 10px; border-radius: 999px; cursor: pointer; font: inherit; font-size: 11px;
    transition: all 0.15s; user-select: none; }
  .filter-chip:hover { border-color: var(--accent); color: var(--ink); }
  .filter-chip.active { background: var(--accent); color: #0a0a0a; border-color: var(--accent); font-weight: 700; }
  main { padding: 20px; padding-bottom: 120px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
  .card { background: var(--panel); border: 2px solid var(--line); border-radius: 8px;
    overflow: hidden; transition: border-color 0.15s; }
  .card.has-changes { border-color: var(--accent); }
  .card img { width: 100%; aspect-ratio: 1/1; object-fit: cover; display: block; background: #000; }
  .meta { padding: 8px 10px; font-size: 11px; color: var(--ink-dim); line-height: 1.35; }
  .meta .name { color: var(--ink); font-weight: 600; word-break: break-all; margin-bottom: 3px; font-size: 12px; }
  .tags { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; padding: 8px 10px; border-top: 1px solid var(--line); }
  .tags .tag-btn {
    font: inherit; border: 1px solid var(--line); background: transparent; color: var(--ink-dim);
    padding: 7px 4px; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: 700;
    letter-spacing: 0.05em; transition: all 0.12s; user-select: none;
  }
  .tags .tag-btn:hover { color: var(--ink); }
  .tags .tag-btn.active { color: #0a0a0a; font-weight: 800; border-color: transparent; }
  .tags .tag-btn[data-tag="POST"].active { background: var(--tag-post); }
  .tags .tag-btn[data-tag="STORY"].active { background: var(--tag-story); }
  .tags .tag-btn[data-tag="AD"].active { background: var(--tag-ad); }
  .tags .tag-btn[data-tag="LANDING"].active { background: var(--tag-landing); }
  .tags .tag-btn[data-tag="ARCHIVE"].active { background: var(--tag-archive); }
  .tag-archive-slot { grid-column: 1 / -1; }
  .empty { text-align: center; color: var(--ink-dim); padding: 60px 20px; }
  .hidden { display: none !important; }
  footer { position: fixed; bottom: 0; left: 0; right: 0; background: var(--panel);
    border-top: 1px solid var(--line); padding: 14px 20px; display: flex; align-items: center;
    gap: 20px; z-index: 30; }
  footer .counts { display: flex; gap: 20px; font-size: 13px; flex: 1; flex-wrap: wrap; }
  footer .count { color: var(--ink-dim); }
  footer .count strong { color: var(--ink); }
  footer .count-changed { color: var(--accent); font-weight: 700; }
  footer button { font: inherit; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;
    font-weight: 700; transition: opacity 0.15s; }
  .btn-clear { background: transparent; color: var(--ink-dim); border: 1px solid var(--line); }
  .btn-clear:hover { color: var(--ink); border-color: var(--ink-dim); }
  .btn-submit { background: var(--accent); color: #0a0a0a; }
  .btn-submit:hover { opacity: 0.9; }
  .btn-submit:disabled { opacity: 0.3; cursor: not-allowed; }
  #toast { position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%);
    background: var(--green); color: #0a0a0a; padding: 12px 24px; border-radius: 6px; font-weight: 700;
    opacity: 0; pointer-events: none; transition: opacity 0.3s; z-index: 40; }
  #toast.show { opacity: 1; }
  #toast.error { background: #ff5a5a; }
  .card img { cursor: zoom-in; }
  #lightbox { position: fixed; inset: 0; background: rgba(0,0,0,0.92); z-index: 100;
    display: none; align-items: center; justify-content: center; padding: 20px;
    cursor: zoom-out; overflow: auto; }
  #lightbox.open { display: flex; }
  #lightbox img { max-width: 95vw; max-height: 95vh; display: block; box-shadow: 0 0 40px rgba(0,0,0,0.8);
    transition: transform 0.2s ease; cursor: zoom-in; }
  #lightbox img.zoomed { max-width: none; max-height: none; cursor: zoom-out; }
  #lightbox .lb-close { position: fixed; top: 18px; right: 24px; background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.25); color: var(--ink); width: 42px; height: 42px;
    border-radius: 50%; font-size: 22px; cursor: pointer; display: flex; align-items: center;
    justify-content: center; font-weight: 700; z-index: 101; }
  #lightbox .lb-close:hover { background: rgba(255,255,255,0.2); }
  #lightbox .lb-nav { position: fixed; top: 50%; transform: translateY(-50%);
    background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.25); color: var(--ink);
    width: 48px; height: 64px; border-radius: 6px; font-size: 28px; cursor: pointer; z-index: 101;
    display: flex; align-items: center; justify-content: center; }
  #lightbox .lb-nav:hover { background: rgba(255,255,255,0.2); }
  #lightbox .lb-prev { left: 20px; }
  #lightbox .lb-next { right: 20px; }
  #lightbox .lb-caption { position: fixed; bottom: 18px; left: 50%; transform: translateX(-50%);
    background: rgba(0,0,0,0.6); color: var(--ink); padding: 6px 14px; border-radius: 4px;
    font-size: 12px; z-index: 101; max-width: 80vw; white-space: nowrap; overflow: hidden;
    text-overflow: ellipsis; }
</style>
</head>
<body>

<header>
  <h1>Image Tagging — Stage 2</h1>
  <span class="meta-text">{{ total }} approved images</span>
  <div class="filter-chips" id="filter-chips">
    <button type="button" class="filter-chip active" data-filter="ALL">ALL</button>
    <button type="button" class="filter-chip" data-filter="UNTAGGED">UNTAGGED</button>
    {% for tag in tags %}
    <button type="button" class="filter-chip" data-filter="{{ tag }}">{{ tag }}</button>
    {% endfor %}
  </div>
</header>

<main>
  {% if images %}
  <div class="grid" id="grid">
    {% for img in images %}
    <div class="card" data-name="{{ img.name }}" data-initial-tags="{{ img.tags|join(',') }}">
      <img src="/image/{{ img.name }}" alt="{{ img.name }}" loading="lazy" onclick="openLightbox(this)">
      <div class="meta">
        <div class="name">{{ img.name }}</div>
        <div>{{ img.size_kb }} KB · {{ img.modified }}</div>
      </div>
      <div class="tags">
        {% for tag in tags %}
        <button
          type="button"
          class="tag-btn {% if tag == 'ARCHIVE' %}tag-archive-slot{% endif %} {% if tag in img.tags %}active{% endif %}"
          data-tag="{{ tag }}"
          onclick="toggleTag(this)"
        >{{ tag }}</button>
        {% endfor %}
      </div>
    </div>
    {% endfor %}
  </div>
  {% else %}
  <div class="empty">No images in <code>contents/ready/</code>. Run Stage 1 first to approve some.</div>
  {% endif %}
</main>

<footer>
  <div class="counts">
    <span class="count">Total: <strong>{{ total }}</strong></span>
    <span class="count">Tagged: <strong id="ct-tagged">{{ tagged }}</strong></span>
    <span class="count">Untagged: <strong id="ct-untagged">{{ untagged }}</strong></span>
    <span class="count-changed">Changed: <span id="ct-changed">0</span></span>
  </div>
  <button type="button" class="btn-clear" onclick="revertAll()">Revert</button>
  <button type="button" class="btn-submit" id="submit-btn" onclick="submitTags()" disabled>Save 0 changes</button>
</footer>

<div id="toast"></div>

<div id="lightbox" onclick="handleLightboxClick(event)">
  <button type="button" class="lb-close" onclick="closeLightbox()" aria-label="Close">&times;</button>
  <button type="button" class="lb-nav lb-prev" onclick="lightboxNav(-1); event.stopPropagation();" aria-label="Previous">&#8249;</button>
  <button type="button" class="lb-nav lb-next" onclick="lightboxNav(1); event.stopPropagation();" aria-label="Next">&#8250;</button>
  <img id="lightbox-img" src="" alt="" onclick="toggleZoom(event)">
  <div class="lb-caption" id="lightbox-caption"></div>
</div>

<script>
  let lightboxImages = [];
  let lightboxIndex = -1;

  function collectVisibleImages() {
    lightboxImages = Array.from(document.querySelectorAll('.card img'))
      .filter(img => !img.closest('.card.hidden'))
      .map(img => ({ src: img.src, name: img.alt }));
  }

  function openLightbox(imgEl) {
    collectVisibleImages();
    lightboxIndex = lightboxImages.findIndex(x => x.src === imgEl.src);
    if (lightboxIndex < 0) lightboxIndex = 0;
    showLightboxAt(lightboxIndex);
    document.getElementById('lightbox').classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function showLightboxAt(i) {
    const item = lightboxImages[i];
    if (!item) return;
    const lbImg = document.getElementById('lightbox-img');
    lbImg.classList.remove('zoomed');
    lbImg.src = item.src;
    document.getElementById('lightbox-caption').textContent =
      `${item.name}  ·  ${i + 1} / ${lightboxImages.length}`;
  }

  function closeLightbox() {
    document.getElementById('lightbox').classList.remove('open');
    document.body.style.overflow = '';
  }

  function lightboxNav(delta) {
    if (lightboxImages.length === 0) return;
    lightboxIndex = (lightboxIndex + delta + lightboxImages.length) % lightboxImages.length;
    showLightboxAt(lightboxIndex);
  }

  function toggleZoom(e) {
    e.stopPropagation();
    document.getElementById('lightbox-img').classList.toggle('zoomed');
  }

  function handleLightboxClick(e) {
    if (e.target.id === 'lightbox') closeLightbox();
  }

  document.addEventListener('keydown', e => {
    if (!document.getElementById('lightbox').classList.contains('open')) return;
    if (e.key === 'Escape') closeLightbox();
    else if (e.key === 'ArrowLeft') lightboxNav(-1);
    else if (e.key === 'ArrowRight') lightboxNav(1);
  });

  // Track changed cards (those whose tag set differs from initial)
  const changed = new Set();

  function getCurrentTags(card) {
    return Array.from(card.querySelectorAll('.tag-btn.active'))
      .map(b => b.dataset.tag)
      .sort();
  }

  function getInitialTags(card) {
    const s = card.dataset.initialTags;
    return s ? s.split(',').filter(Boolean).sort() : [];
  }

  function cardIsChanged(card) {
    const cur = getCurrentTags(card).join(',');
    const init = getInitialTags(card).join(',');
    return cur !== init;
  }

  function updateCardState(card) {
    const isChanged = cardIsChanged(card);
    card.classList.toggle('has-changes', isChanged);
    if (isChanged) changed.add(card.dataset.name);
    else changed.delete(card.dataset.name);
  }

  function recountTagged() {
    let tagged = 0, untagged = 0;
    document.querySelectorAll('.card').forEach(card => {
      if (getCurrentTags(card).length > 0) tagged++;
      else untagged++;
    });
    document.getElementById('ct-tagged').textContent = tagged;
    document.getElementById('ct-untagged').textContent = untagged;
  }

  function updateFooter() {
    document.getElementById('ct-changed').textContent = changed.size;
    const btn = document.getElementById('submit-btn');
    btn.disabled = changed.size === 0;
    btn.textContent = `Save ${changed.size} change${changed.size === 1 ? '' : 's'}`;
    recountTagged();
  }

  function toggleTag(btn) {
    btn.classList.toggle('active');
    const card = btn.closest('.card');
    updateCardState(card);
    updateFooter();
  }

  function revertAll() {
    if (changed.size === 0) return;
    if (!confirm(`Revert ${changed.size} unsaved change(s)?`)) return;
    document.querySelectorAll('.card.has-changes').forEach(card => {
      const initial = new Set(getInitialTags(card));
      card.querySelectorAll('.tag-btn').forEach(btn => {
        btn.classList.toggle('active', initial.has(btn.dataset.tag));
      });
      card.classList.remove('has-changes');
    });
    changed.clear();
    updateFooter();
  }

  function toast(msg, isError = false, duration = 2800) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.toggle('error', isError);
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), duration);
  }

  async function submitTags() {
    if (changed.size === 0) return;
    const btn = document.getElementById('submit-btn');
    btn.disabled = true;
    const original = btn.textContent;
    btn.textContent = 'Saving...';
    const payload = [];
    document.querySelectorAll('.card.has-changes').forEach(card => {
      payload.push({ name: card.dataset.name, tags: getCurrentTags(card) });
    });
    try {
      const res = await fetch('/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ changes: payload })
      });
      const data = await res.json();
      if (data.success) {
        toast(`Saved ${data.saved} change${data.saved === 1 ? '' : 's'}`);
        // Reset initial state for saved cards
        document.querySelectorAll('.card.has-changes').forEach(card => {
          const current = getCurrentTags(card);
          card.dataset.initialTags = current.join(',');
          card.classList.remove('has-changes');
        });
        changed.clear();
        updateFooter();
      } else {
        toast(`Error: ${data.error || 'unknown'}`, true, 4000);
        btn.disabled = false;
        btn.textContent = original;
      }
    } catch (e) {
      toast(`Error: ${e.message}`, true, 4000);
      btn.disabled = false;
      btn.textContent = original;
    }
  }

  // Filter chips
  document.getElementById('filter-chips').addEventListener('click', e => {
    const chip = e.target.closest('.filter-chip');
    if (!chip) return;
    document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    const f = chip.dataset.filter;
    document.querySelectorAll('.card').forEach(card => {
      const tags = getCurrentTags(card);
      let show;
      if (f === 'ALL') show = true;
      else if (f === 'UNTAGGED') show = tags.length === 0;
      else show = tags.includes(f);
      card.classList.toggle('hidden', !show);
    });
  });
</script>

</body>
</html>
"""


@app.route("/")
def index():
    images = scan_ready_images()
    total = len(images)
    tagged = sum(1 for i in images if i["tags"])
    untagged = total - tagged
    return render_template_string(
        GALLERY_HTML,
        images=images,
        total=total,
        tagged=tagged,
        untagged=untagged,
        tags=TAGS,
    )


@app.route("/image/<path:name>")
def serve_image(name):
    if "/" in name or "\\" in name or name.startswith(".."):
        abort(400)
    target = (READY_DIR / name).resolve()
    if not str(target).startswith(str(READY_DIR.resolve())):
        abort(403)
    if not target.exists():
        abort(404)
    return send_from_directory(READY_DIR, target.name)


@app.route("/save", methods=["POST"])
def save():
    data = request.get_json(silent=True) or {}
    changes = data.get("changes", [])
    if not changes:
        return jsonify({"success": False, "error": "no changes provided"})

    manifest = load_manifest()
    saved = 0
    now = datetime.now().isoformat(timespec="seconds")

    for c in changes:
        name = c.get("name")
        tags = c.get("tags", [])
        if not name:
            continue
        # Validate tags against allowed set
        valid = [t for t in tags if t in TAGS]
        if not valid:
            # Empty tag set — remove entry from manifest
            if name in manifest:
                del manifest[name]
        else:
            manifest[name] = {
                "tags": valid,
                "tagged_at": now,
            }
        saved += 1

    save_manifest(manifest)
    return jsonify({"success": True, "saved": saved})


def main():
    parser = argparse.ArgumentParser(description="Stage 2 — tag approved images for downstream use.")
    parser.add_argument("--port", type=int, default=8124, help="Local server port (default 8124)")
    args = parser.parse_args()

    images = scan_ready_images()
    print(f"Found {len(images)} images in contents/ready/.", file=sys.stderr)
    print(f"LOCAL_URL: http://127.0.0.1:{args.port}", flush=True)
    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()

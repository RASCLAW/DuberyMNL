"""
Model Gallery — browse all ready images grouped by model, pick anchors for chatbot image bank.

Shows person + product sections per model. Click images to select,
then export selections as JSON.

Usage:
    python tools/image_gen/model_gallery.py
    python tools/image_gen/model_gallery.py --port 8125
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from flask import Flask, request, jsonify, render_template_string, send_from_directory, abort

PROJECT_DIR = Path(__file__).parent.parent.parent
READY_DIR = PROJECT_DIR / "contents" / "ready"
IMG_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

app = Flask(__name__)

MODEL_ORDER = [
    "bandits-glossy-black", "bandits-matte-black", "bandits-blue",
    "bandits-green", "bandits-tortoise",
    "outback-black", "outback-blue", "outback-red", "outback-green",
    "rasta-brown", "rasta-red",
]

DISPLAY_NAMES = {
    "bandits-glossy-black": "Bandits Glossy Black",
    "bandits-matte-black": "Bandits Matte Black",
    "bandits-blue": "Bandits Blue",
    "bandits-green": "Bandits Green",
    "bandits-tortoise": "Bandits Tortoise",
    "outback-black": "Outback Black",
    "outback-blue": "Outback Blue",
    "outback-red": "Outback Red",
    "outback-green": "Outback Green",
    "rasta-brown": "Rasta Brown",
    "rasta-red": "Rasta Red",
}


def scan_models():
    data = {}
    for model in MODEL_ORDER:
        entry = {"person": [], "product": []}
        for img_type in ("person", "product"):
            folder = READY_DIR / img_type / model
            if not folder.exists():
                continue
            for img in sorted(folder.iterdir()):
                if img.suffix.lower() not in IMG_EXTENSIONS:
                    continue
                uid = f"{img_type}/{model}/{img.name}"
                entry[img_type].append({
                    "uid": uid,
                    "name": img.name,
                    "size_kb": img.stat().st_size // 1024,
                })
        if entry["person"] or entry["product"]:
            data[model] = entry
    return data


def resolve_uid(uid):
    parts = uid.split("/", 2)
    if len(parts) != 3:
        return None
    img_type, model, name = parts
    target = (READY_DIR / img_type / model / name).resolve()
    if not str(target).startswith(str(READY_DIR.resolve())):
        return None
    if not target.exists():
        return None
    return target


GALLERY_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DuberyMNL — Model Gallery</title>
<style>
  :root {
    --bg: #0f0f10; --panel: #1a1a1c; --ink: #ecebe6; --ink-dim: #9a978f;
    --accent: #ff7a2f; --green: #4dd59b; --blue: #5b9ef5; --line: #2a2a2e;
    --selected: #ff7a2f;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: var(--bg); color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace; }

  header { position: sticky; top: 0; z-index: 100; background: var(--panel);
    border-bottom: 1px solid var(--line); padding: 12px 20px; }
  header h1 { margin: 0; font-size: 16px; letter-spacing: 0.05em; }
  .header-meta { color: var(--ink-dim); font-size: 12px; margin-top: 4px; }
  .header-row { display: flex; justify-content: space-between; align-items: center; }

  .nav { display: flex; gap: 6px; flex-wrap: wrap; padding: 10px 20px;
    position: sticky; top: 58px; z-index: 99; background: var(--bg);
    border-bottom: 1px solid var(--line); }
  .nav a { color: var(--ink-dim); text-decoration: none; font-size: 12px;
    padding: 4px 10px; border: 1px solid var(--line); border-radius: 14px;
    transition: all 0.15s; white-space: nowrap; }
  .nav a:hover { border-color: var(--accent); color: var(--ink); }

  .model-section { padding: 20px; border-bottom: 1px solid var(--line); }
  .model-title { font-size: 20px; font-weight: 700; margin: 0 0 4px 0; color: var(--accent); }
  .model-count { font-size: 12px; color: var(--ink-dim); margin-bottom: 16px; }

  .type-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em;
    color: var(--ink-dim); margin: 12px 0 8px 0; padding-bottom: 4px;
    border-bottom: 1px solid var(--line); }
  .type-label.person { color: var(--blue); border-color: var(--blue); }
  .type-label.product { color: var(--green); border-color: var(--green); }

  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 10px; margin-bottom: 16px; }

  .card { position: relative; border-radius: 6px; overflow: hidden;
    border: 2px solid var(--line); cursor: pointer; transition: border-color 0.15s; }
  .card:hover { border-color: var(--ink-dim); }
  .card.selected { border-color: var(--selected); box-shadow: 0 0 12px rgba(255,122,47,0.3); }
  .card img { width: 100%; display: block; aspect-ratio: 4/5; object-fit: cover; }
  .card .badge { display: none; position: absolute; top: 6px; right: 6px;
    background: var(--selected); color: #0a0a0a; font-size: 10px; font-weight: 700;
    padding: 2px 8px; border-radius: 10px; }
  .card.selected .badge { display: inline-block; }
  .card .name { padding: 6px 8px; font-size: 10px; color: var(--ink-dim);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; background: var(--panel); }

  /* Selection bar */
  .sel-bar { position: fixed; bottom: 0; left: 0; right: 0; z-index: 200;
    background: var(--panel); border-top: 2px solid var(--accent);
    padding: 12px 20px; display: none; justify-content: space-between; align-items: center; }
  .sel-bar.show { display: flex; }
  .sel-bar .info { font-size: 13px; }
  .sel-bar button { background: var(--accent); color: #0a0a0a; border: none;
    padding: 8px 20px; border-radius: 6px; font-weight: 700; cursor: pointer;
    font-size: 13px; }
  .sel-bar button:hover { opacity: 0.9; }
  .sel-bar button.clear { background: transparent; color: var(--ink-dim);
    border: 1px solid var(--line); margin-right: 8px; }

  /* Lightbox */
  .lightbox { display: none; position: fixed; inset: 0; z-index: 300;
    background: rgba(0,0,0,0.92); justify-content: center; align-items: center; }
  .lightbox.open { display: flex; }
  .lightbox img { max-width: 90vw; max-height: 90vh; object-fit: contain; cursor: zoom-in; }
  .lightbox img.zoomed { max-width: none; max-height: none; cursor: zoom-out; }
  .lb-close { position: absolute; top: 16px; right: 20px; color: #fff;
    font-size: 28px; cursor: pointer; z-index: 301; }
  .lb-nav { position: absolute; top: 50%; font-size: 32px; color: #fff;
    cursor: pointer; user-select: none; z-index: 301; }
  .lb-prev { left: 16px; }
  .lb-next { right: 16px; }
  .lb-caption { position: absolute; bottom: 16px; left: 50%;
    transform: translateX(-50%); color: var(--ink-dim); font-size: 13px; }

  /* Toast */
  .toast { position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%);
    background: var(--green); color: #0a0a0a; padding: 10px 24px; border-radius: 8px;
    font-weight: 600; font-size: 13px; opacity: 0; transition: opacity 0.3s; z-index: 400; }
  .toast.show { opacity: 1; }
</style>
</head>
<body>

<header>
  <div class="header-row">
    <div>
      <h1>DUBERYMNL — MODEL GALLERY</h1>
      <div class="header-meta">{{ total }} images across {{ model_count }} models · click to select anchors</div>
    </div>
  </div>
</header>

<div class="nav">
  {% for model in models %}
  <a href="#{{ model }}">{{ display_names[model] }} ({{ counts[model] }})</a>
  {% endfor %}
</div>

{% for model in models %}
<div class="model-section" id="{{ model }}">
  <div class="model-title">{{ display_names[model] }}</div>
  <div class="model-count">{{ counts[model] }} images</div>

  {% if data[model].person %}
  <div class="type-label person">Person · {{ data[model].person | length }}</div>
  <div class="grid">
    {% for img in data[model].person %}
    <div class="card" data-uid="{{ img.uid }}" onclick="toggleSelect(this)" ondblclick="openLightbox(this)">
      <img src="/image/{{ img.uid }}" loading="lazy" alt="{{ img.name }}">
      <div class="badge">PICK</div>
      <div class="name">{{ img.name }}</div>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if data[model].product %}
  <div class="type-label product">Product · {{ data[model].product | length }}</div>
  <div class="grid">
    {% for img in data[model].product %}
    <div class="card" data-uid="{{ img.uid }}" onclick="toggleSelect(this)" ondblclick="openLightbox(this)">
      <img src="/image/{{ img.uid }}" loading="lazy" alt="{{ img.name }}">
      <div class="badge">PICK</div>
      <div class="name">{{ img.name }}</div>
    </div>
    {% endfor %}
  </div>
  {% endif %}
</div>
{% endfor %}

<div class="sel-bar" id="sel-bar">
  <div class="info" id="sel-info">0 selected</div>
  <div>
    <button class="clear" onclick="clearAll()">Clear</button>
    <button onclick="exportPicks()">Export Picks</button>
  </div>
</div>

<div class="lightbox" id="lightbox" onclick="handleLbClick(event)">
  <span class="lb-close" onclick="closeLb()">&times;</span>
  <span class="lb-nav lb-prev" onclick="lbNav(-1)">&larr;</span>
  <span class="lb-nav lb-next" onclick="lbNav(1)">&rarr;</span>
  <img id="lb-img" onclick="toggleZoom(event)">
  <div class="lb-caption" id="lb-caption"></div>
</div>

<div class="toast" id="toast"></div>

<script>
  const selected = new Set();
  const allCards = Array.from(document.querySelectorAll('.card'));
  const allImages = allCards.map(c => ({
    src: c.querySelector('img').src,
    name: c.querySelector('.name').textContent,
    uid: c.dataset.uid
  }));
  let lbIdx = 0;

  // Preload previously-saved picks
  const PRELOAD = {{ preload_uids | tojson }};
  PRELOAD.forEach(uid => {
    const card = document.querySelector('.card[data-uid="' + uid + '"]');
    if (card) {
      selected.add(uid);
      card.classList.add('selected');
    }
  });
  updateBar();

  function toggleSelect(card) {
    const uid = card.dataset.uid;
    if (selected.has(uid)) {
      selected.delete(uid);
      card.classList.remove('selected');
    } else {
      selected.add(uid);
      card.classList.add('selected');
    }
    updateBar();
  }

  function updateBar() {
    const bar = document.getElementById('sel-bar');
    const info = document.getElementById('sel-info');
    if (selected.size > 0) {
      bar.classList.add('show');
      info.textContent = selected.size + ' selected';
    } else {
      bar.classList.remove('show');
    }
  }

  function clearAll() {
    selected.clear();
    allCards.forEach(c => c.classList.remove('selected'));
    updateBar();
  }

  function toast(msg, dur) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), dur || 2500);
  }

  async function exportPicks() {
    if (selected.size === 0) return;
    const picks = Array.from(selected).map(uid => {
      const [type, model, name] = uid.split('/');
      return { uid, type, model, name };
    });
    try {
      const res = await fetch('/export', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({picks})
      });
      const data = await res.json();
      if (data.success) {
        toast('Exported ' + picks.length + ' picks to ' + data.path);
      }
    } catch(e) {
      toast('Export error: ' + e.message);
    }
  }

  function openLightbox(card) {
    const imgEl = card.querySelector('img');
    lbIdx = allImages.findIndex(x => x.src === imgEl.src);
    if (lbIdx < 0) lbIdx = 0;
    showLbAt(lbIdx);
    document.getElementById('lightbox').classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function showLbAt(i) {
    const item = allImages[i];
    if (!item) return;
    const img = document.getElementById('lb-img');
    img.classList.remove('zoomed');
    img.src = item.src;
    document.getElementById('lb-caption').textContent =
      item.name + '  ·  ' + (i+1) + ' / ' + allImages.length;
  }

  function closeLb() {
    document.getElementById('lightbox').classList.remove('open');
    document.body.style.overflow = '';
  }

  function lbNav(d) {
    lbIdx = (lbIdx + d + allImages.length) % allImages.length;
    showLbAt(lbIdx);
  }

  function toggleZoom(e) { e.stopPropagation(); document.getElementById('lb-img').classList.toggle('zoomed'); }
  function handleLbClick(e) { if (e.target.id === 'lightbox') closeLb(); }

  document.addEventListener('keydown', e => {
    if (!document.getElementById('lightbox').classList.contains('open')) return;
    if (e.key === 'Escape') closeLb();
    else if (e.key === 'ArrowLeft') lbNav(-1);
    else if (e.key === 'ArrowRight') lbNav(1);
  });
</script>
</body>
</html>
"""


@app.route("/")
def index():
    data = scan_models()
    models = [m for m in MODEL_ORDER if m in data]
    total = sum(len(v["person"]) + len(v["product"]) for v in data.values())
    counts = {m: len(data[m]["person"]) + len(data[m]["product"]) for m in models}

    # Load previously-saved picks if any
    picks_path = PROJECT_DIR / ".tmp" / "chatbot_image_bank_picks.json"
    preload_uids = []
    if picks_path.exists():
        try:
            import json as _json
            preload_uids = [p["uid"] for p in _json.loads(picks_path.read_text(encoding="utf-8"))]
        except Exception:
            pass

    return render_template_string(
        GALLERY_HTML,
        data=data,
        models=models,
        model_count=len(models),
        total=total,
        counts=counts,
        display_names=DISPLAY_NAMES,
        preload_uids=preload_uids,
    )


@app.route("/image/<path:uid>")
def serve_image(uid):
    target = resolve_uid(uid)
    if target is None:
        abort(404)
    return send_from_directory(target.parent, target.name)


@app.route("/export", methods=["POST"])
def export_picks():
    data = request.get_json(silent=True) or {}
    picks = data.get("picks", [])
    if not picks:
        return jsonify({"success": False, "error": "no picks"})

    out_path = PROJECT_DIR / ".tmp" / "chatbot_image_bank_picks.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(picks, indent=2, ensure_ascii=False), encoding="utf-8")
    return jsonify({"success": True, "count": len(picks), "path": str(out_path.relative_to(PROJECT_DIR))})


def main():
    parser = argparse.ArgumentParser(description="Model gallery for chatbot image bank picks.")
    parser.add_argument("--port", type=int, default=8125, help="Port (default 8125)")
    args = parser.parse_args()

    data = scan_models()
    total = sum(len(v["person"]) + len(v["product"]) for v in data.values())
    print(f"Found {total} images across {len(data)} models.", file=sys.stderr)
    print(f"LOCAL_URL: http://127.0.0.1:{args.port}", flush=True)
    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()

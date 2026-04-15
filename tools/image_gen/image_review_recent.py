"""
Recent-Image Review Server — Stage 1 quality gate.

Scans contents/ (and .tmp/) for images modified within the lookback window,
groups them by category, and lets RA approve or reject each one.

Approve  -> contents/ready/      (flat; Stage 2 tool sorts into use-case folders)
Reject   -> contents/failed/

Usage:
    python tools/image_gen/image_review_recent.py                       # last 4 days, port 8123
    python tools/image_gen/image_review_recent.py --days 7 --port 8124
    python tools/image_gen/image_review_recent.py --tunnel              # + ngrok public URL
    python tools/image_gen/image_review_recent.py --no-tmp              # skip .tmp/ images
"""

import argparse
import shutil
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, render_template_string, send_from_directory, abort

PROJECT_DIR = Path(__file__).parent.parent.parent
CONTENTS_DIR = PROJECT_DIR / "contents"
TMP_DIR = PROJECT_DIR / ".tmp"
READY_DIR = CONTENTS_DIR / "ready"
FAILED_DIR = CONTENTS_DIR / "failed"
IMG_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
EXCLUDE_CATEGORIES = {"archives", "assets", "failed", "ready"}
CATEGORY_ORDER = ["ugc", "brand", "ads", "carousel", "product", "new", "tmp", "other"]

app = Flask(__name__)
app.config["LOOKBACK_DAYS"] = 4
app.config["INCLUDE_TMP"] = True


def categorize(path: Path) -> str:
    """Return category for an image path."""
    try:
        rel = path.resolve().relative_to(CONTENTS_DIR.resolve())
        top = rel.parts[0] if len(rel.parts) > 1 else "other"
        return top
    except ValueError:
        # Not under contents/ — likely .tmp/
        try:
            path.resolve().relative_to(TMP_DIR.resolve())
            return "tmp"
        except ValueError:
            return "other"


def scan_recent_images(days: int, include_tmp: bool) -> dict:
    """Return dict of category -> list of image dicts, newest first."""
    cutoff = time.time() - (days * 86400)
    by_cat: dict[str, list[dict]] = defaultdict(list)

    scan_roots = [CONTENTS_DIR]
    if include_tmp and TMP_DIR.exists():
        scan_roots.append(TMP_DIR)

    for root in scan_roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in IMG_EXTENSIONS:
                continue

            cat = categorize(path)
            if cat in EXCLUDE_CATEGORIES:
                continue

            mtime = path.stat().st_mtime
            if mtime < cutoff:
                continue

            # Build uid that encodes root (so /image/<uid> can resolve it back)
            if root == CONTENTS_DIR:
                rel = path.relative_to(CONTENTS_DIR)
                uid = "contents/" + str(rel).replace("\\", "/")
            else:
                rel = path.relative_to(TMP_DIR)
                uid = "tmp/" + str(rel).replace("\\", "/")

            by_cat[cat].append({
                "uid": uid,
                "name": path.name,
                "size_kb": path.stat().st_size // 1024,
                "modified": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
                "mtime": mtime,
            })

    for cat in by_cat:
        by_cat[cat].sort(key=lambda x: x["mtime"], reverse=True)
    return dict(by_cat)


def resolve_uid(uid: str) -> Path | None:
    """Resolve a uid ('contents/foo.png' or 'tmp/bar.png') back to a Path, with path-escape guard."""
    if uid.startswith("contents/"):
        root, rel = CONTENTS_DIR, uid[len("contents/"):]
    elif uid.startswith("tmp/"):
        root, rel = TMP_DIR, uid[len("tmp/"):]
    else:
        return None
    target = (root / rel).resolve()
    root_resolved = root.resolve()
    if not str(target).startswith(str(root_resolved)):
        return None
    if not target.exists():
        return None
    return target


GALLERY_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DuberyMNL Image Review — Last {{ days }} days</title>
<style>
  :root {
    --bg: #0f0f10;
    --panel: #1a1a1c;
    --ink: #ecebe6;
    --ink-dim: #9a978f;
    --accent: #ff7a2f;
    --green: #4dd59b;
    --red: #ff5a5a;
    --line: #2a2a2e;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: var(--bg); color: var(--ink);
    font: 14px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  header { position: sticky; top: 0; background: var(--panel); border-bottom: 1px solid var(--line);
    padding: 12px 20px; z-index: 20; }
  .hdr-row1 { display: flex; align-items: center; gap: 16px; margin-bottom: 10px; }
  header h1 { font-size: 16px; margin: 0; flex: 1; }
  .meta-text { color: var(--ink-dim); font-size: 13px; }
  .chips { display: flex; flex-wrap: wrap; gap: 8px; }
  .chip { background: transparent; color: var(--ink-dim); border: 1px solid var(--line);
    padding: 5px 12px; border-radius: 999px; cursor: pointer; font: inherit; font-size: 12px;
    transition: all 0.15s; user-select: none; }
  .chip:hover { border-color: var(--accent); color: var(--ink); }
  .chip.active { background: var(--accent); color: #0a0a0a; border-color: var(--accent); font-weight: 700; }
  main { padding: 20px; padding-bottom: 120px; }
  .section { margin-bottom: 32px; }
  .section h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent);
    margin: 0 0 12px 0; padding-bottom: 6px; border-bottom: 1px solid var(--line); }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }
  .card { position: relative; background: var(--panel); border: 2px solid var(--line); border-radius: 8px;
    overflow: hidden; transition: border-color 0.15s; }
  .card.approved { border-color: var(--green); }
  .card.rejected { border-color: var(--red); opacity: 0.6; }
  .card img { width: 100%; aspect-ratio: 1/1; object-fit: cover; display: block; background: #000; }
  .card-badge { position: absolute; top: 8px; right: 8px; padding: 3px 8px; border-radius: 4px;
    font-size: 10px; font-weight: 800; letter-spacing: 0.08em; display: none; }
  .card.approved .card-badge.approved-badge { display: inline-block; background: var(--green); color: #0a0a0a; }
  .card.rejected .card-badge.rejected-badge { display: inline-block; background: var(--red); color: #0a0a0a; }
  .meta { padding: 8px 10px; font-size: 11px; color: var(--ink-dim); line-height: 1.35; }
  .meta .name { color: var(--ink); font-weight: 600; word-break: break-all; margin-bottom: 3px; font-size: 12px; }
  .btn-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; border-top: 1px solid var(--line); }
  .btn-row button { font: inherit; border: none; padding: 10px 0; cursor: pointer; font-weight: 700;
    font-size: 12px; letter-spacing: 0.05em; transition: opacity 0.15s; }
  .btn-reject { background: #2a1414; color: var(--red); }
  .btn-reject:hover { background: var(--red); color: #0a0a0a; }
  .btn-approve { background: #14251c; color: var(--green); }
  .btn-approve:hover { background: var(--green); color: #0a0a0a; }
  .btn-undo { grid-column: 1 / -1; background: var(--line); color: var(--ink-dim); }
  .btn-undo:hover { background: var(--accent); color: #0a0a0a; }
  .empty { text-align: center; color: var(--ink-dim); padding: 60px 20px; }
  footer { position: fixed; bottom: 0; left: 0; right: 0; background: var(--panel);
    border-top: 1px solid var(--line); padding: 14px 20px; display: flex; align-items: center;
    gap: 20px; z-index: 30; }
  footer .counts { display: flex; gap: 20px; font-size: 13px; flex: 1; }
  footer .count-pending { color: var(--ink-dim); }
  footer .count-approved { color: var(--green); font-weight: 700; }
  footer .count-rejected { color: var(--red); font-weight: 700; }
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
  #toast.error { background: var(--red); }
  .hidden-cat { display: none !important; }
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
  <div class="hdr-row1">
    <h1>Image Review — Stage 1 (quality gate)</h1>
    <span class="meta-text">{{ total }} images · last {{ days }} days</span>
  </div>
  <div class="chips" id="chips">
    <button type="button" class="chip active" data-cat="ALL">ALL {{ total }}</button>
    {% for cat, imgs in sections %}
    <button type="button" class="chip" data-cat="{{ cat }}">{{ cat|upper }} {{ imgs|length }}</button>
    {% endfor %}
  </div>
</header>

<main>
  {% if sections %}
    {% for cat, imgs in sections %}
    <section class="section" data-cat="{{ cat }}">
      <h2>{{ cat|upper }} · {{ imgs|length }} image{% if imgs|length != 1 %}s{% endif %}</h2>
      <div class="grid">
        {% for img in imgs %}
        <div class="card" data-uid="{{ img.uid }}">
          <img src="/image/{{ img.uid }}" alt="{{ img.name }}" loading="lazy" onclick="openLightbox(this, '{{ img.name }}')">
          <span class="card-badge approved-badge">APPROVED</span>
          <span class="card-badge rejected-badge">REJECTED</span>
          <div class="meta">
            <div class="name">{{ img.name }}</div>
            <div>{{ img.size_kb }} KB · {{ img.modified }}</div>
          </div>
          <div class="btn-row btn-row-default">
            <button type="button" class="btn-reject" onclick="decide(this, 'reject')">REJECT</button>
            <button type="button" class="btn-approve" onclick="decide(this, 'approve')">APPROVE</button>
          </div>
          <div class="btn-row btn-row-undo" style="display:none">
            <button type="button" class="btn-undo" onclick="undo(this)">UNDO</button>
          </div>
        </div>
        {% endfor %}
      </div>
    </section>
    {% endfor %}
  {% else %}
    <div class="empty">No images modified in the last {{ days }} days.</div>
  {% endif %}
</main>

<footer>
  <div class="counts">
    <span class="count-pending">Pending: <span id="ct-pending">{{ total }}</span></span>
    <span class="count-approved">Approved: <span id="ct-approved">0</span></span>
    <span class="count-rejected">Rejected: <span id="ct-rejected">0</span></span>
  </div>
  <button type="button" class="btn-clear" onclick="clearAll()">Clear all</button>
  <button type="button" class="btn-submit" id="submit-btn" onclick="submitDecisions()" disabled>Submit 0 decisions</button>
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
      .filter(img => img.closest('.section:not(.hidden-cat)'))
      .map(img => ({ src: img.src, name: img.alt }));
  }

  function openLightbox(imgEl, name) {
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
    // Click on the backdrop (not the image or controls) closes
    if (e.target.id === 'lightbox') closeLightbox();
  }

  document.addEventListener('keydown', e => {
    if (!document.getElementById('lightbox').classList.contains('open')) return;
    if (e.key === 'Escape') closeLightbox();
    else if (e.key === 'ArrowLeft') lightboxNav(-1);
    else if (e.key === 'ArrowRight') lightboxNav(1);
  });

  const decisions = new Map();  // uid -> "approve" | "reject"
  const TOTAL = {{ total }};

  function updateCounts() {
    let approved = 0, rejected = 0;
    decisions.forEach(v => v === 'approve' ? approved++ : rejected++);
    const total = approved + rejected;
    document.getElementById('ct-pending').textContent = TOTAL - total;
    document.getElementById('ct-approved').textContent = approved;
    document.getElementById('ct-rejected').textContent = rejected;
    const btn = document.getElementById('submit-btn');
    btn.disabled = total === 0;
    btn.textContent = `Submit ${total} decision${total === 1 ? '' : 's'}`;
  }

  function decide(btn, verdict) {
    const card = btn.closest('.card');
    const uid = card.dataset.uid;
    decisions.set(uid, verdict);
    card.classList.remove('approved', 'rejected');
    card.classList.add(verdict === 'approve' ? 'approved' : 'rejected');
    card.querySelector('.btn-row-default').style.display = 'none';
    card.querySelector('.btn-row-undo').style.display = 'grid';
    updateCounts();
  }

  function undo(btn) {
    const card = btn.closest('.card');
    const uid = card.dataset.uid;
    decisions.delete(uid);
    card.classList.remove('approved', 'rejected');
    card.querySelector('.btn-row-default').style.display = 'grid';
    card.querySelector('.btn-row-undo').style.display = 'none';
    updateCounts();
  }

  function clearAll() {
    if (decisions.size === 0) return;
    if (!confirm(`Clear ${decisions.size} decision(s)?`)) return;
    decisions.clear();
    document.querySelectorAll('.card').forEach(card => {
      card.classList.remove('approved', 'rejected');
      card.querySelector('.btn-row-default').style.display = 'grid';
      card.querySelector('.btn-row-undo').style.display = 'none';
    });
    updateCounts();
  }

  function toast(msg, isError = false, duration = 2800) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.toggle('error', isError);
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), duration);
  }

  async function submitDecisions() {
    if (decisions.size === 0) return;
    const btn = document.getElementById('submit-btn');
    btn.disabled = true;
    const original = btn.textContent;
    btn.textContent = 'Submitting...';
    try {
      const payload = Array.from(decisions.entries()).map(([uid, verdict]) => ({ uid, verdict }));
      const res = await fetch('/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decisions: payload })
      });
      const data = await res.json();
      if (data.success) {
        toast(`Approved ${data.approved} · Rejected ${data.rejected}${data.errors.length ? ' · ' + data.errors.length + ' errors' : ''}`);
        setTimeout(() => location.reload(), 1500);
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

  // Category filter chips
  document.getElementById('chips').addEventListener('click', e => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    const cat = chip.dataset.cat;
    document.querySelectorAll('.section').forEach(sec => {
      sec.classList.toggle('hidden-cat', cat !== 'ALL' && sec.dataset.cat !== cat);
    });
  });
</script>

</body>
</html>
"""


@app.route("/")
def index():
    by_cat = scan_recent_images(app.config["LOOKBACK_DAYS"], app.config["INCLUDE_TMP"])
    total = sum(len(v) for v in by_cat.values())
    # Ordered sections per CATEGORY_ORDER
    ordered = []
    for cat in CATEGORY_ORDER:
        if cat in by_cat:
            ordered.append((cat, by_cat[cat]))
    # Any categories not in the predefined order
    for cat in sorted(by_cat.keys()):
        if cat not in CATEGORY_ORDER:
            ordered.append((cat, by_cat[cat]))
    return render_template_string(
        GALLERY_HTML,
        sections=ordered,
        total=total,
        days=app.config["LOOKBACK_DAYS"],
    )


@app.route("/image/<path:uid>")
def serve_image(uid):
    target = resolve_uid(uid)
    if target is None:
        abort(404)
    return send_from_directory(target.parent, target.name)


@app.route("/submit", methods=["POST"])
def submit_decisions():
    data = request.get_json(silent=True) or {}
    decisions = data.get("decisions", [])
    if not decisions:
        return jsonify({"success": False, "error": "no decisions provided"})

    READY_DIR.mkdir(parents=True, exist_ok=True)
    FAILED_DIR.mkdir(parents=True, exist_ok=True)

    approved = 0
    rejected = 0
    errors = []

    for d in decisions:
        uid = d.get("uid")
        verdict = d.get("verdict")
        if verdict not in ("approve", "reject"):
            errors.append(f"{uid}: bad verdict {verdict!r}")
            continue

        src = resolve_uid(uid)
        if src is None:
            errors.append(f"{uid}: resolve failed")
            continue

        dst_dir = READY_DIR if verdict == "approve" else FAILED_DIR
        dst = dst_dir / src.name
        if dst.exists():
            stem, suffix = src.stem, src.suffix
            n = 2
            while (dst_dir / f"{stem}-v{n}{suffix}").exists():
                n += 1
            dst = dst_dir / f"{stem}-v{n}{suffix}"

        try:
            shutil.move(str(src), str(dst))
            if verdict == "approve":
                approved += 1
            else:
                rejected += 1
        except Exception as e:
            errors.append(f"{uid}: {e}")

    return jsonify({
        "success": True,
        "approved": approved,
        "rejected": rejected,
        "errors": errors,
    })


def start_ngrok_tunnel(port: int) -> str | None:
    try:
        from pyngrok import ngrok
        return ngrok.connect(port, "http").public_url
    except Exception as e:
        print(f"ngrok tunnel failed: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description="Stage 1 image review — approve/reject recent generations.")
    parser.add_argument("--days", type=int, default=4, help="Lookback window in days (default 4)")
    parser.add_argument("--port", type=int, default=8123, help="Local server port (default 8123)")
    parser.add_argument("--tunnel", action="store_true", help="Start ngrok tunnel and print public URL")
    parser.add_argument("--no-tmp", action="store_true", help="Skip .tmp/ images")
    args = parser.parse_args()

    app.config["LOOKBACK_DAYS"] = args.days
    app.config["INCLUDE_TMP"] = not args.no_tmp

    by_cat = scan_recent_images(args.days, app.config["INCLUDE_TMP"])
    total = sum(len(v) for v in by_cat.values())
    breakdown = ", ".join(f"{c}={len(v)}" for c, v in sorted(by_cat.items()))
    print(f"Found {total} images ({breakdown}) in last {args.days} days.", file=sys.stderr)

    if args.tunnel:
        public_url = start_ngrok_tunnel(args.port)
        if public_url:
            print(f"PUBLIC_URL: {public_url}", flush=True)
        else:
            print("PUBLIC_URL: (ngrok failed — local only)", flush=True)

    print(f"LOCAL_URL: http://127.0.0.1:{args.port}", flush=True)
    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()

"""
WF3 Image Review Server — Flask UI for reviewing generated ad images.

Reads DONE captions from .tmp/captions.json.
Approve sets status=IMAGE_APPROVED.
Reject sets status=IMAGE_REJECTED and saves feedback to image_feedback field.
Skip leaves status as DONE (reappears next session).

Run:
    python tools/image_gen/image_review_server.py
"""

import os
import sys
import json
from pathlib import Path

from flask import Flask, request, jsonify, render_template_string, send_from_directory

PROJECT_DIR = Path(__file__).parent.parent.parent
TMP_DIR = PROJECT_DIR / ".tmp"
CAPTIONS_FILE = TMP_DIR / "captions.json"
REJECTED_FILE = TMP_DIR / "rejected_captions.json"
PENDING_POST_FILE = TMP_DIR / "pending_post.json"
IMAGES_DIR = PROJECT_DIR / "output" / "images"

app = Flask(__name__)


def load_done_captions():
    if not CAPTIONS_FILE.exists():
        return []
    captions = json.loads(CAPTIONS_FILE.read_text())
    return [c for c in captions if c.get("status") == "DONE"]


def _read_json_list(path: Path) -> list:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _write_json_list(path: Path, data: list):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def move_caption(caption_id: str, fields: dict, destination: Path):
    """Remove caption from captions.json, update fields, append to destination file."""
    if not CAPTIONS_FILE.exists():
        return
    captions = json.loads(CAPTIONS_FILE.read_text())
    CAPTIONS_FILE.with_suffix(".json.bak").write_text(
        json.dumps(captions, indent=2, ensure_ascii=False)
    )
    target = None
    remaining = []
    for caption in captions:
        if str(caption.get("id")) == caption_id:
            caption.update(fields)
            target = caption
        else:
            remaining.append(caption)
    if target:
        dest_list = _read_json_list(destination)
        dest_list.append(target)
        _write_json_list(destination, dest_list)
    CAPTIONS_FILE.write_text(json.dumps(remaining, indent=2, ensure_ascii=False))


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DuberyMNL — Image Review</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #f0f2f5;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    padding: 16px;
  }
  h1 { text-align: center; color: #1c1e21; margin-bottom: 8px; font-size: 20px; }
  .subtitle { text-align: center; color: #65676b; margin-bottom: 24px; font-size: 14px; }
  .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(340px, 100%), 1fr));
    gap: 20px;
    max-width: 1400px;
    margin: 0 auto;
  }
  .card {
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.15);
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  .card-image {
    width: 100%;
    aspect-ratio: 4 / 5;
    object-fit: cover;
    display: block;
    background: #e4e6eb;
  }
  .card-image-placeholder {
    width: 100%;
    aspect-ratio: 4 / 5;
    background: #e4e6eb;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #aaa;
    font-size: 13px;
  }
  .card-body { padding: 12px 14px; flex: 1; }
  .meta-row {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 10px;
  }
  .badge {
    font-size: 11px;
    border-radius: 12px;
    padding: 3px 9px;
    font-weight: 600;
    white-space: nowrap;
  }
  .badge-vibe   { background: #e7f3ff; color: #1877f2; }
  .badge-angle  { background: #f0fff4; color: #2d7a3a; }
  .badge-anchor { background: #fff3e0; color: #b05a00; }
  .badge-id     { background: #f3f0ff; color: #5a3db5; }
  .stars {
    font-size: 14px;
    color: #f7b928;
    letter-spacing: 1px;
    margin-bottom: 8px;
  }
  .stars .empty { color: #ddd; }
  .caption-text {
    font-size: 13px;
    color: #1c1e21;
    line-height: 1.55;
    margin-bottom: 8px;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .notes-text {
    font-size: 12px;
    color: #65676b;
    font-style: italic;
    line-height: 1.4;
    border-top: 1px solid #e4e6eb;
    padding-top: 8px;
    margin-top: 4px;
  }
  .card-actions {
    display: flex;
    gap: 8px;
    padding: 10px 14px 14px;
  }
  .btn {
    flex: 1;
    padding: 10px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    transition: opacity 0.15s;
  }
  .btn:hover { opacity: 0.85; }
  .btn-approve { background: #42b72a; color: white; }
  .btn-reject  { background: #e02020; color: white; }
  .btn-skip    { background: #e4e6eb; color: #606770; }
  .feedback-section {
    padding: 0 14px 12px;
    border-top: 1px solid #e4e6eb;
  }
  .feedback-label {
    font-size: 11px;
    color: #65676b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
    margin-top: 10px;
    display: block;
  }
  .feedback-input {
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: 13px;
    font-family: inherit;
    outline: none;
    resize: none;
    line-height: 1.5;
    color: #1c1e21;
  }
  .feedback-input:focus { border-color: #1877f2; }
  .empty-state {
    text-align: center;
    padding: 80px 20px;
    color: #65676b;
    font-size: 15px;
    max-width: 400px;
    margin: 0 auto;
  }
  .empty-state p + p { margin-top: 8px; font-size: 13px; }
  .all-done {
    display: none;
    text-align: center;
    padding: 60px 20px;
    color: #42b72a;
    font-size: 18px;
    font-weight: 700;
  }
</style>
</head>
<body>

<h1>DuberyMNL — Image Review</h1>
<p class="subtitle" id="subtitle">{{ captions|length }} image{% if captions|length != 1 %}s{% endif %} ready for review</p>

{% if captions %}
<div class="cards-grid" id="cards-grid">
{% for cap in captions %}
<div class="card" data-id="{{ cap.id }}" id="card-{{ cap.id }}">

  {% set img_path = '/image/' ~ cap.id %}
  <img class="card-image" src="{{ img_path }}"
       alt="Caption #{{ cap.id }}"
       onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
  <div class="card-image-placeholder" style="display:none">Image not found</div>

  <div class="card-body">
    <div class="meta-row">
      <span class="badge badge-id">#{{ cap.id }}</span>
      <span class="badge badge-vibe">{{ cap.vibe }}</span>
      <span class="badge badge-angle">{{ cap.angle }}</span>
      <span class="badge badge-anchor">{{ cap.visual_anchor }}</span>
    </div>

    <div class="stars">
      {% set r = cap.rating | int %}
      {% for i in range(1, 6) %}
        {% if i <= r %}<span>★</span>{% else %}<span class="empty">★</span>{% endif %}
      {% endfor %}
    </div>

    <div class="caption-text">{{ cap.caption_text }}</div>

    {% if cap.notes %}
    <div class="notes-text">{{ cap.notes }}</div>
    {% endif %}
  </div>

  <div class="feedback-section">
    <span class="feedback-label">Feedback / Reason</span>
    <textarea class="feedback-input" id="feedback-{{ cap.id }}" rows="2"
      placeholder="e.g. Product fidelity 0%, wrong frame shape, overlays too large..."></textarea>
  </div>

  <div class="card-actions">
    <button class="btn btn-approve" onclick="approve('{{ cap.id }}')">Approve</button>
    <button class="btn btn-reject"  onclick="reject('{{ cap.id }}')">Reject</button>
    <button class="btn btn-skip"    onclick="skip('{{ cap.id }}')">Skip</button>
  </div>

</div>
{% endfor %}
</div>
<div class="all-done" id="all-done">All images reviewed. You can close this window.</div>

{% else %}
<div class="empty-state">
  <p>No images ready for review.</p>
  <p>Run WF2b to generate images first, then come back here.</p>
</div>
{% endif %}

<script>
let remaining = {{ captions|length }};

function removeCard(id) {
  const card = document.getElementById('card-' + id);
  if (card) {
    card.style.transition = 'opacity 0.25s';
    card.style.opacity = '0';
    setTimeout(() => {
      card.remove();
      remaining--;
      document.getElementById('subtitle').textContent =
        remaining + ' image' + (remaining !== 1 ? 's' : '') + ' ready for review';
      if (remaining === 0) {
        document.getElementById('all-done').style.display = 'block';
      }
    }, 250);
  }
}

function getFeedback(id) {
  const el = document.getElementById('feedback-' + id);
  return el ? el.value.trim() : '';
}

function approve(id) {
  fetch('/approve', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: String(id), feedback: getFeedback(id) })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) removeCard(id);
    else alert('Error approving image. Check terminal.');
  })
  .catch(() => alert('Network error. Check terminal.'));
}

function reject(id) {
  fetch('/reject', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: String(id), feedback: getFeedback(id) })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) removeCard(id);
    else alert('Error rejecting image. Check terminal.');
  })
  .catch(() => alert('Network error. Check terminal.'));
}

function skip(id) {
  removeCard(id);
}
</script>
</body>
</html>
"""


@app.route("/")
def index():
    captions = load_done_captions()
    return render_template_string(HTML_TEMPLATE, captions=captions)


@app.route("/image/<int:caption_id>")
def serve_image(caption_id):
    filename = f"dubery_{caption_id}.jpg"
    return send_from_directory(str(IMAGES_DIR), filename)


@app.route("/approve", methods=["POST"])
def approve():
    data = request.get_json()
    caption_id = str(data.get("id", "")).strip()
    if not caption_id:
        return jsonify({"success": False, "error": "Missing id"}), 400
    fields = {"status": "IMAGE_APPROVED"}
    if data.get("feedback"):
        fields["image_feedback"] = data["feedback"]
    move_caption(caption_id, fields, PENDING_POST_FILE)
    print(f"Caption #{caption_id} approved → pending_post.json")
    return jsonify({"success": True})


@app.route("/reject", methods=["POST"])
def reject():
    data = request.get_json()
    caption_id = str(data.get("id", "")).strip()
    if not caption_id:
        return jsonify({"success": False, "error": "Missing id"}), 400
    fields = {"status": "IMAGE_REJECTED"}
    if data.get("feedback"):
        fields["image_feedback"] = data["feedback"]
    move_caption(caption_id, fields, REJECTED_FILE)
    print(f"Caption #{caption_id} rejected → rejected_captions.json. Feedback: {data.get('feedback', '')}")
    return jsonify({"success": True})


@app.route("/status")
def status():
    captions = load_done_captions()
    return jsonify({"pending": len(captions)})


if __name__ == "__main__":
    TMP_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    if not CAPTIONS_FILE.exists():
        print("No .tmp/captions.json found.", file=sys.stderr)
        sys.exit(1)

    done_count = len(load_done_captions())
    print(f"Image review server starting at http://localhost:5001")
    print(f"{done_count} image(s) ready for review.")
    app.run(host="0.0.0.0", port=5001, debug=False)

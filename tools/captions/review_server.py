"""
WF1 Review Server — Local Flask UI for reviewing generated captions.

Reads from .tmp/captions.json (PENDING captions only).
Approve / reject writes status back to .tmp/captions.json.
Batch feedback saved to .tmp/feedback.json.

Run:
    python tools/captions/review_server.py
"""

import os
import sys
import json
import threading
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template_string

load_dotenv(Path(__file__).parent.parent.parent / ".env")

TMP_DIR = Path(__file__).parent.parent.parent / ".tmp"
CAPTIONS_FILE = TMP_DIR / "captions.json"
REJECTED_FILE = TMP_DIR / "rejected_captions.json"
FEEDBACK_FILE = TMP_DIR / "feedback.json"

app = Flask(__name__)


def load_pending_captions():
    if not CAPTIONS_FILE.exists():
        return []
    captions = json.loads(CAPTIONS_FILE.read_text())
    return [c for c in captions if c.get("status") == "PENDING"]


def update_captions_file(updates: dict):
    """Update captions in .tmp/captions.json by ID. updates = {id: {field: value}}"""
    if not CAPTIONS_FILE.exists():
        return
    captions = json.loads(CAPTIONS_FILE.read_text())
    # Backup before write
    CAPTIONS_FILE.with_suffix(".json.bak").write_text(
        json.dumps(captions, indent=2, ensure_ascii=False)
    )
    for caption in captions:
        cap_id = str(caption.get("id"))
        if cap_id in updates:
            caption.update(updates[cap_id])
    CAPTIONS_FILE.write_text(json.dumps(captions, indent=2, ensure_ascii=False))


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DuberyMNL — Caption Review</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #f0f2f5;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    padding: 16px;
  }
  @media (max-width: 480px) {
    body { padding: 10px; }
    .submit-section { padding: 0 10px; }
  }
  h1 { text-align: center; color: #1c1e21; margin-bottom: 8px; font-size: 20px; }
  .subtitle { text-align: center; color: #65676b; margin-bottom: 24px; font-size: 14px; }
  .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(420px, 100%), 1fr));
    gap: 16px;
    max-width: 1400px;
    margin: 0 auto 30px;
  }
  .card { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.15); overflow: hidden; }
  .card-header { display: flex; align-items: center; padding: 12px 16px; gap: 10px; }
  .avatar {
    width: 40px; height: 40px; border-radius: 50%;
    background: linear-gradient(135deg, #1877f2, #42b72a);
    display: flex; align-items: center; justify-content: center;
    color: white; font-weight: bold; font-size: 16px; flex-shrink: 0;
  }
  .page-meta { flex: 1; }
  .page-name { font-weight: 600; font-size: 14px; color: #1c1e21; }
  .post-meta { font-size: 12px; color: #65676b; }
  .meta-badges { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
  .vibe-badge { font-size: 11px; background: #e7f3ff; color: #1877f2; border-radius: 12px; padding: 3px 10px; font-weight: 600; white-space: nowrap; }
  .angle-badge { font-size: 11px; background: #f0fff4; color: #2d7a3a; border-radius: 12px; padding: 3px 10px; font-weight: 600; white-space: nowrap; }
  .hook-badge { font-size: 11px; background: #fff8e7; color: #b07d00; border-radius: 12px; padding: 3px 10px; font-weight: 600; white-space: nowrap; }
  .anchor-toggle {
    background: #e7f3ff; color: #1877f2; border: none;
    border-radius: 20px; padding: 5px 12px; font-size: 13px;
    cursor: pointer; font-weight: 600; transition: background 0.2s; flex-shrink: 0;
  }
  .anchor-toggle:hover { background: #cde4ff; }
  .card-body { padding: 12px 16px; }
  .caption-text {
    font-size: 14px; color: #1c1e21; line-height: 1.5;
    border: 1px dashed transparent; border-radius: 4px; padding: 4px 6px;
    min-height: 40px; outline: none; transition: border-color 0.2s, background 0.2s;
    white-space: pre-wrap; word-break: break-word;
  }
  .caption-text:focus { border-color: #1877f2; background: #f0f7ff; }
  .caption-text:hover:not(:focus) { border-color: #ccc; }
  .hashtags-text {
    font-size: 13px; color: #1877f2; margin-top: 8px;
    border: 1px dashed transparent; border-radius: 4px; padding: 3px 6px;
    outline: none; transition: border-color 0.2s, background 0.2s; word-break: break-word;
  }
  .hashtags-text:focus { border-color: #1877f2; background: #f0f7ff; }
  .hashtags-text:hover:not(:focus) { border-color: #ccc; }
  .hypothesis-text {
    font-size: 12px; color: #888; margin-top: 8px; font-style: italic;
    padding: 4px 6px;
  }
  .edit-hint { font-size: 11px; color: #aaa; margin-top: 4px; font-style: italic; }
  .product-section, .overlay-section {
    margin-top: 10px; padding-top: 10px; border-top: 1px solid #e4e6eb;
  }
  .product-label, .overlay-label {
    font-size: 11px; color: #65676b; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;
  }
  .product-select {
    display: block; width: 100%; padding: 7px 10px; margin-bottom: 6px;
    border: 1px solid #ccc; border-radius: 6px; font-size: 13px;
    font-family: inherit; color: #1c1e21; background: #fff;
    cursor: pointer; outline: none; appearance: auto;
  }
  .product-select:focus { border-color: #1877f2; }
  .product-select.hidden { display: none; }
  .overlay-grid {
    display: flex; flex-wrap: wrap; gap: 8px 16px;
  }
  .overlay-grid label {
    display: flex; align-items: center; gap: 5px;
    font-size: 13px; color: #1c1e21; cursor: pointer;
    white-space: nowrap;
  }
  .overlay-grid input[type="checkbox"] { cursor: pointer; accent-color: #1877f2; }
  .overlay-other-wrap {
    display: flex; align-items: center; gap: 5px; width: 100%; margin-top: 2px;
  }
  .overlay-other-input {
    flex: 1; padding: 4px 8px; border: 1px solid #ccc; border-radius: 6px;
    font-size: 13px; font-family: inherit; outline: none;
  }
  .overlay-other-input:focus { border-color: #1877f2; }
  .card-divider { height: 1px; background: #e4e6eb; margin: 10px 16px; }
  .card-actions { display: flex; padding: 2px 8px 10px; gap: 4px; position: relative; }
  .action-btn {
    flex: 1; display: flex; align-items: center; justify-content: center;
    gap: 6px; padding: 8px; border: none; background: none;
    border-radius: 6px; cursor: pointer; font-size: 14px;
    color: #65676b; font-weight: 600; transition: background 0.15s; position: relative;
  }
  .action-btn:hover { background: #f2f2f2; }
  .like-btn.rated { color: #f7b928; }
  .star-popup {
    display: none; position: absolute; bottom: calc(100% + 8px); left: 50%;
    transform: translateX(-50%); background: #fff; border-radius: 30px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.2); padding: 8px 14px;
    gap: 6px; white-space: nowrap; z-index: 100; flex-direction: row;
  }
  .like-wrapper { flex: 1; position: relative; display: flex; justify-content: center; }
  .like-wrapper .star-popup.open { display: flex; }
  .star { font-size: 24px; cursor: pointer; color: #ccc; transition: color 0.1s, transform 0.1s; line-height: 1; }
  .star:hover, .star.selected { color: #f7b928; transform: scale(1.2); }
  .comment-wrapper { flex: 1; position: relative; display: flex; justify-content: center; }
  .notes-input {
    display: none; position: absolute; bottom: calc(100% + 8px); left: 50%;
    transform: translateX(-50%); width: min(320px, 90vw); padding: 10px 12px;
    border: 1px solid #ccc; border-radius: 12px; font-size: 13px;
    font-family: inherit; outline: none; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    z-index: 100; resize: none; line-height: 1.5;
  }
  .notes-input:focus { border-color: #1877f2; }
  .comment-wrapper .notes-input.open { display: block; }
  .notes-saved { font-size: 11px; color: #42b72a; text-align: center; margin-top: 2px; height: 14px; }
  .share-btn { color: #bbb; cursor: default; flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px; padding: 8px; font-size: 14px; font-weight: 600; }
  .rating-label { text-align: center; font-size: 12px; color: #aaa; padding-bottom: 6px; }
  .rating-label.approved { color: #42b72a; font-weight: 600; }
  .rating-label.rejected { color: #e02020; font-weight: 600; }
  .submit-section { max-width: 500px; margin: 0 auto 60px; }
  .batch-feedback-label {
    display: block; font-size: 13px; font-weight: 600; color: #1c1e21;
    margin-bottom: 8px;
  }
  .batch-feedback-hint { font-size: 12px; color: #65676b; margin-bottom: 8px; }
  #batch-feedback {
    width: 100%; padding: 10px 12px; border: 1px solid #ccc; border-radius: 8px;
    font-size: 13px; font-family: inherit; outline: none; resize: vertical;
    line-height: 1.5; margin-bottom: 14px;
  }
  #batch-feedback:focus { border-color: #1877f2; }
  .submit-btn {
    display: block; width: 100%; background: #1877f2; color: white; border: none;
    border-radius: 8px; padding: 14px 40px; font-size: 16px;
    font-weight: 700; cursor: pointer; transition: background 0.2s;
  }
  .submit-btn:hover { background: #1558b0; }
  .submit-btn:disabled { background: #b0c4de; cursor: not-allowed; }
  .submit-warning { color: #e02020; font-size: 13px; margin-top: 10px; display: none; text-align: center; }
  #result-overlay {
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,0.6); z-index: 999;
    align-items: center; justify-content: center;
  }
  #result-overlay.visible { display: flex; }
  .result-card {
    background: white; border-radius: 12px; padding: 40px 50px;
    text-align: center; box-shadow: 0 4px 30px rgba(0,0,0,0.3);
  }
  .result-card h2 { font-size: 22px; color: #1c1e21; margin-bottom: 10px; }
  .result-card p { font-size: 15px; color: #65676b; white-space: pre-wrap; }
  .empty-state { text-align: center; padding: 60px 20px; color: #65676b; font-size: 15px; }
</style>
</head>
<body>

<h1>DuberyMNL — Caption Review</h1>
<p class="subtitle">{{ captions|length }} captions pending review &nbsp;·&nbsp; Rate all before submitting</p>

{% if captions %}
<div class="cards-grid" id="cards-grid">
{% for cap in captions %}
<div class="card" data-id="{{ cap.id }}">
  <div class="card-header">
    <div class="avatar">D</div>
    <div class="page-meta">
      <div class="page-name">DuberyMNL</div>
      <div class="post-meta">Just now &nbsp;·&nbsp; 🌐</div>
    </div>
    <div class="meta-badges">
      <div class="vibe-badge">{{ cap.vibe }}</div>
      <div class="angle-badge">{{ cap.angle }}</div>
      <div class="hook-badge">{{ cap.hook_type }}</div>
    </div>
    <button class="anchor-toggle" onclick="toggleAnchor(this)"
            data-value="{{ cap.visual_anchor }}">
      {% if cap.visual_anchor == 'PERSON' %}👤 PERSON{% else %}📦 PRODUCT{% endif %}
    </button>
  </div>

  <div class="card-body">
    <div class="caption-text" contenteditable="true"
         data-field="caption">{{ cap.caption_text }}</div>
    <div class="hashtags-text" contenteditable="true"
         data-field="hashtags">{{ cap.hashtags }}</div>
    <div class="hypothesis-text">{{ cap.creative_hypothesis }}</div>
    <div class="edit-hint">Click caption or hashtags to edit</div>

    <div class="product-section">
      <div class="product-label">Recommended Products</div>
      {% for slot in range(5) %}
      <select class="product-select{% if slot > 0 %} hidden{% endif %}"
              data-slot="{{ slot }}" onchange="handleProductSelect(this, {{ slot }})">
        <option value="">{% if slot == 0 %}-- pick a product --{% else %}-- add another --{% endif %}</option>
        <optgroup label="Classic">
          <option>Classic - Black</option>
          <option>Classic - Blue</option>
          <option>Classic - Red</option>
          <option>Classic - Purple</option>
        </optgroup>
        <optgroup label="Outback">
          <option>Outback - Black</option>
          <option>Outback - Blue</option>
          <option>Outback - Red</option>
          <option>Outback - Green</option>
        </optgroup>
        <optgroup label="Bandits">
          <option>Bandits - Glossy Black</option>
          <option>Bandits - Camo</option>
          <option>Bandits - Green</option>
          <option>Bandits - Blue</option>
        </optgroup>
        <optgroup label="Rasta">
          <option>Rasta - Red</option>
          <option>Rasta - Brown</option>
        </optgroup>
      </select>
      {% endfor %}
    </div>

    <div class="overlay-section">
      <div class="overlay-label">Ad Overlays</div>
      <div class="overlay-grid">
        <label><input type="checkbox" value="headline"> Headline</label>
        <label><input type="checkbox" value="price"> Price (₱699)</label>
        <label class="overlay-person"{% if cap.visual_anchor == 'PRODUCT' %} style="display:none"{% endif %}>
          <input type="checkbox" value="bubble"> Bubble
        </label>
        <label class="overlay-product"{% if cap.visual_anchor == 'PERSON' %} style="display:none"{% endif %}>
          <input type="checkbox" value="accessories"> Accessories
        </label>
        <div class="overlay-other-wrap">
          <label style="white-space:nowrap"><input type="checkbox" value="other" onchange="toggleOtherInput(this)"> Other:</label>
          <input type="text" class="overlay-other-input" placeholder="describe..." style="display:none">
        </div>
      </div>
    </div>
  </div>

  <div class="card-divider"></div>

  <div class="rating-label" data-label="{{ cap.id }}">Not rated yet</div>

  <div class="card-actions">
    <div class="like-wrapper">
      <button class="action-btn like-btn" title="Rate this caption" onclick="toggleStars(this)">
        👍 Like
      </button>
      <div class="star-popup">
        <span class="star" data-val="1" onclick="setRating(this, 1)">★</span>
        <span class="star" data-val="2" onclick="setRating(this, 2)">★</span>
        <span class="star" data-val="3" onclick="setRating(this, 3)">★</span>
        <span class="star" data-val="4" onclick="setRating(this, 4)">★</span>
        <span class="star" data-val="5" onclick="setRating(this, 5)">★</span>
      </div>
    </div>

    <div class="comment-wrapper">
      <button class="action-btn" title="Add image direction notes" onclick="toggleNotes(this)">
        💬 Comment
      </button>
      <textarea class="notes-input" rows="4"
        placeholder="Image direction for WF2...&#10;e.g. Female on a packed bus in front of Megamall, looking outside, side emblem visible."></textarea>
    </div>

    <div class="share-btn" title="Placeholder">↗ Share</div>
  </div>
  <div class="notes-saved" id="notes-saved-{{ cap.id }}"></div>
</div>
{% endfor %}
</div>

<div class="submit-section">
  <label class="batch-feedback-label">Batch Feedback for Next Run</label>
  <p class="batch-feedback-hint">Overall thoughts on this batch — what worked, what felt off, what you want more or less of. WF1 reads this when generating the next batch.</p>
  <textarea id="batch-feedback" rows="5"
    placeholder="e.g. Too many serious vibes, want more humor. The Tagalog felt forced on IDs 5 and 9. More chaos energy next batch."></textarea>
  <button class="submit-btn" onclick="submitAll()">Submit All</button>
  <div class="submit-warning" id="submit-warning">Please rate all captions before submitting.</div>
</div>

{% else %}
<div class="empty-state">
  <p>No pending captions to review.</p>
  <p style="margin-top:8px;font-size:13px;">Run WF1 to generate a new batch.</p>
</div>
{% endif %}

<div id="result-overlay">
  <div class="result-card">
    <h2 id="result-title">Review submitted!</h2>
    <p id="result-body">Saving...</p>
  </div>
</div>

<script>
function toggleStars(btn) {
  const popup = btn.closest('.like-wrapper').querySelector('.star-popup');
  const isOpen = popup.classList.contains('open');
  document.querySelectorAll('.star-popup.open, .notes-input.open').forEach(el => el.classList.remove('open'));
  if (!isOpen) popup.classList.add('open');
}

function toggleNotes(btn) {
  const input = btn.closest('.comment-wrapper').querySelector('.notes-input');
  const isOpen = input.classList.contains('open');
  document.querySelectorAll('.star-popup.open, .notes-input.open').forEach(el => el.classList.remove('open'));
  if (!isOpen) {
    input.classList.add('open');
    input.focus();
    const cardId = btn.closest('.card').dataset.id;
    const savedEl = document.getElementById('notes-saved-' + cardId);
    input.oninput = () => {
      if (savedEl) savedEl.textContent = input.value.trim() ? 'Note saved' : '';
    };
  }
}

document.addEventListener('click', function(e) {
  if (!e.target.closest('.like-wrapper') && !e.target.closest('.comment-wrapper')) {
    document.querySelectorAll('.star-popup.open, .notes-input.open').forEach(el => el.classList.remove('open'));
  }
});

function handleProductSelect(select, slotIndex) {
  const card = select.closest('.card');
  const selects = card.querySelectorAll('.product-select');
  if (select.value) {
    if (selects[slotIndex + 1]) selects[slotIndex + 1].classList.remove('hidden');
  } else {
    for (let i = slotIndex + 1; i < selects.length; i++) {
      selects[i].classList.add('hidden');
      selects[i].value = '';
    }
  }
}

function toggleAnchor(btn) {
  const card = btn.closest('.card');
  const personLabels = card.querySelectorAll('.overlay-person');
  const productLabels = card.querySelectorAll('.overlay-product');

  if (btn.dataset.value === 'PERSON') {
    btn.dataset.value = 'PRODUCT';
    btn.textContent = '📦 PRODUCT';
    personLabels.forEach(el => {
      el.style.display = 'none';
      el.querySelector('input[type="checkbox"]').checked = false;
    });
    productLabels.forEach(el => el.style.display = '');
  } else {
    btn.dataset.value = 'PERSON';
    btn.textContent = '👤 PERSON';
    productLabels.forEach(el => {
      el.style.display = 'none';
      el.querySelector('input[type="checkbox"]').checked = false;
    });
    personLabels.forEach(el => el.style.display = '');
  }
}

function toggleOtherInput(checkbox) {
  const wrap = checkbox.closest('.overlay-other-wrap');
  const input = wrap.querySelector('.overlay-other-input');
  input.style.display = checkbox.checked ? 'block' : 'none';
  if (checkbox.checked) input.focus();
}

function setRating(star, val) {
  const popup = star.closest('.star-popup');
  const card = star.closest('.card');
  const likeBtn = card.querySelector('.like-btn');
  const label = document.querySelector(`.rating-label[data-label="${card.dataset.id}"]`);

  popup.querySelectorAll('.star').forEach((s, i) => {
    s.classList.toggle('selected', i < val);
  });

  card.dataset.rating = val;
  likeBtn.classList.add('rated');
  likeBtn.textContent = '👍 Like';

  const status = val >= 3 ? 'APPROVED' : 'REJECTED';
  label.textContent = `★${val} — ${status}`;
  label.className = `rating-label ${status.toLowerCase()}`;

  popup.classList.remove('open');
}

function submitAll() {
  const cards = document.querySelectorAll('.card');
  const unrated = [...cards].filter(c => !c.dataset.rating);
  const warning = document.getElementById('submit-warning');

  if (unrated.length > 0) {
    warning.style.display = 'block';
    warning.textContent = `Please rate all captions before submitting. (${unrated.length} unrated)`;
    unrated[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }
  warning.style.display = 'none';

  const captions = [...cards].map(card => {
    const checkedBoxes = [...card.querySelectorAll('.overlay-grid input[type="checkbox"]:checked')]
      .map(cb => cb.value);
    const otherInput = card.querySelector('.overlay-other-input').value.trim();
    const overlays = checkedBoxes.map(v => v === 'other' && otherInput ? `other:${otherInput}` : v).join(',');

    return {
      id: card.dataset.id,
      caption_text: card.querySelector('[data-field="caption"]').innerText,
      hashtags: card.querySelector('[data-field="hashtags"]').innerText,
      visual_anchor: card.querySelector('.anchor-toggle').dataset.value,
      rating: parseInt(card.dataset.rating),
      notes: card.querySelector('.notes-input').value,
      recommended_products: [...card.querySelectorAll('.product-select')].map(s => s.value).filter(v => v).join(', '),
      overlays: overlays
    };
  });

  const payload = {
    captions: captions,
    batch_feedback: document.getElementById('batch-feedback').value.trim()
  };

  document.getElementById('result-overlay').classList.add('visible');

  fetch('/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .then(data => {
    document.getElementById('result-title').textContent = 'Review saved!';
    document.getElementById('result-body').textContent =
      `${data.approved} approved · ${data.rejected} rejected\n\nYou can close this window.`;
  })
  .catch(() => {
    document.getElementById('result-title').textContent = 'Error saving review';
    document.getElementById('result-body').textContent = 'Check the terminal for details.';
  });
}
</script>
</body>
</html>
"""


@app.route("/")
def index():
    captions = load_pending_captions()
    return render_template_string(HTML_TEMPLATE, captions=captions)


@app.route("/submit", methods=["POST"])
def submit():
    payload = request.get_json()
    items = payload.get("captions", [])
    batch_feedback = payload.get("batch_feedback", "").strip()

    updates = {}
    approved = 0
    rejected = 0

    for item in items:
        cap_id = str(item["id"])
        rating = int(item["rating"])
        status = "APPROVED" if rating >= 3 else "REJECTED"

        updates[cap_id] = {
            "caption_text": item["caption_text"],
            "hashtags": item["hashtags"],
            "visual_anchor": item["visual_anchor"],
            "rating": rating,
            "status": status,
            "notes": item.get("notes", ""),
            "recommended_products": item.get("recommended_products", ""),
            "overlays": item.get("overlays", ""),
        }

        if status == "APPROVED":
            approved += 1
        else:
            rejected += 1

    update_captions_file(updates)

    # Move rejected captions out of captions.json into rejected_captions.json
    rejected_ids = {cap_id for cap_id, u in updates.items() if u["status"] == "REJECTED"}
    if rejected_ids:
        captions = json.loads(CAPTIONS_FILE.read_text())
        remaining = []
        rejected_list = json.loads(REJECTED_FILE.read_text()) if REJECTED_FILE.exists() else []
        for caption in captions:
            if str(caption.get("id")) in rejected_ids:
                rejected_list.append(caption)
            else:
                remaining.append(caption)
        CAPTIONS_FILE.write_text(json.dumps(remaining, indent=2, ensure_ascii=False))
        REJECTED_FILE.write_text(json.dumps(rejected_list, indent=2, ensure_ascii=False))

    if batch_feedback:
        existing = []
        if FEEDBACK_FILE.exists():
            existing = json.loads(FEEDBACK_FILE.read_text())
        existing.append({
            "submitted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "feedback": batch_feedback
        })
        FEEDBACK_FILE.write_text(json.dumps(existing, indent=2, ensure_ascii=False))

    def shutdown():
        import time
        time.sleep(1.5)
        os._exit(0)

    threading.Thread(target=shutdown, daemon=True).start()
    return jsonify({"approved": approved, "rejected": rejected})


if __name__ == "__main__":
    TMP_DIR.mkdir(exist_ok=True)
    if not CAPTIONS_FILE.exists():
        print("No .tmp/captions.json found. Run WF1 first to generate captions.", file=sys.stderr)
        sys.exit(1)
    print("Review server starting at http://localhost:5000")
    print("Keep this terminal open until you submit the review.")
    app.run(host="0.0.0.0", port=5000, debug=False)

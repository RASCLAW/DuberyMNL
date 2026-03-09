"""
WF1 Review Server — Local Flask UI for reviewing generated captions.

Serves a Facebook-style review page at http://localhost:5000
Reads PENDING captions from Google Sheets, displays them as mockup cards.
RA edits captions, toggles visual anchor, rates with stars, adds notes.
Submit All writes results back to Sheets and shuts down the server.

Run:
    python tools/captions/review_server.py
"""

import os
import sys
import json
import threading
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template_string
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv(Path(__file__).parent.parent.parent / ".env")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_FILE = Path(__file__).parent.parent.parent / "credentials.json"
TOKEN_FILE = Path(__file__).parent.parent.parent / "token.json"
SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")

app = Flask(__name__)


def get_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("sheets", "v4", credentials=creds)


def load_pending_captions():
    service = get_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="captions!A1:Z"
    ).execute()
    rows = result.get("values", [])
    if not rows:
        return []
    headers = rows[0]
    captions = []
    for i, row in enumerate(rows[1:], start=2):
        data = dict(zip(headers, row + [""] * (len(headers) - len(row))))
        if data.get("Status", "").upper() == "PENDING":
            data["_row"] = i
            captions.append(data)
    return captions


def update_caption_row(row_index, caption_text, hashtags, visual_anchor, rating, notes):
    service = get_service()
    status = "APPROVED" if int(rating) >= 3 else "REJECTED"
    # Read headers to find column positions
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="captions!A1:Z1"
    ).execute()
    headers = result.get("values", [[]])[0]

    col_map = {h: i for i, h in enumerate(headers)}

    def col_letter(idx):
        return chr(ord("A") + idx)

    updates = []
    for field, value in [
        ("Caption", caption_text),
        ("Hashtags", hashtags),
        ("Visual_Anchor", visual_anchor),
        ("Rating", rating),
        ("Status", status),
        ("Notes", notes),
    ]:
        if field in col_map:
            col = col_letter(col_map[field])
            updates.append({
                "range": f"captions!{col}{row_index}",
                "values": [[value]]
            })

    if updates:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()

    return status


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
    padding: 20px;
  }
  h1 {
    text-align: center;
    color: #1c1e21;
    margin-bottom: 8px;
    font-size: 20px;
  }
  .subtitle {
    text-align: center;
    color: #65676b;
    margin-bottom: 24px;
    font-size: 14px;
  }
  .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
    gap: 20px;
    max-width: 1400px;
    margin: 0 auto 30px;
  }
  .card {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    overflow: hidden;
  }
  .card-header {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    gap: 10px;
  }
  .avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, #1877f2, #42b72a);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    font-size: 16px;
    flex-shrink: 0;
  }
  .page-meta { flex: 1; }
  .page-name { font-weight: 600; font-size: 14px; color: #1c1e21; }
  .post-meta { font-size: 12px; color: #65676b; }
  .vibe-badge {
    font-size: 11px;
    background: #e7f3ff;
    color: #1877f2;
    border-radius: 12px;
    padding: 3px 10px;
    font-weight: 600;
    white-space: nowrap;
  }
  .card-image {
    width: 100%;
    height: 220px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
  }
  .anchor-toggle {
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(0,0,0,0.55);
    color: white;
    border: none;
    border-radius: 20px;
    padding: 5px 12px;
    font-size: 13px;
    cursor: pointer;
    font-weight: 600;
    transition: background 0.2s;
  }
  .anchor-toggle:hover { background: rgba(0,0,0,0.75); }
  .image-placeholder {
    color: rgba(255,255,255,0.7);
    font-size: 13px;
    text-align: center;
  }
  .card-body { padding: 12px 16px; }
  .caption-text {
    font-size: 14px;
    color: #1c1e21;
    line-height: 1.5;
    border: 1px dashed transparent;
    border-radius: 4px;
    padding: 4px 6px;
    min-height: 40px;
    outline: none;
    transition: border-color 0.2s, background 0.2s;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .caption-text:focus {
    border-color: #1877f2;
    background: #f0f7ff;
  }
  .caption-text:hover:not(:focus) { border-color: #ccc; }
  .hashtags-text {
    font-size: 13px;
    color: #1877f2;
    margin-top: 8px;
    border: 1px dashed transparent;
    border-radius: 4px;
    padding: 3px 6px;
    outline: none;
    transition: border-color 0.2s, background 0.2s;
    word-break: break-word;
  }
  .hashtags-text:focus {
    border-color: #1877f2;
    background: #f0f7ff;
  }
  .hashtags-text:hover:not(:focus) { border-color: #ccc; }
  .edit-hint {
    font-size: 11px;
    color: #aaa;
    margin-top: 4px;
    font-style: italic;
  }
  .card-divider {
    height: 1px;
    background: #e4e6eb;
    margin: 10px 16px;
  }
  .card-actions {
    display: flex;
    padding: 2px 8px 10px;
    gap: 4px;
    position: relative;
  }
  .action-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 8px;
    border: none;
    background: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    color: #65676b;
    font-weight: 600;
    transition: background 0.15s;
    position: relative;
  }
  .action-btn:hover { background: #f2f2f2; }
  .like-btn.rated { color: #f7b928; }
  .star-popup {
    display: none;
    position: absolute;
    bottom: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    background: #fff;
    border-radius: 30px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.2);
    padding: 8px 14px;
    gap: 6px;
    white-space: nowrap;
    z-index: 100;
    flex-direction: row;
  }
  .like-wrapper {
    flex: 1;
    position: relative;
    display: flex;
    justify-content: center;
  }
  .like-wrapper:hover .star-popup { display: flex; }
  .star {
    font-size: 24px;
    cursor: pointer;
    color: #ccc;
    transition: color 0.1s, transform 0.1s;
    line-height: 1;
  }
  .star:hover, .star.selected { color: #f7b928; transform: scale(1.2); }
  .comment-wrapper { flex: 1; position: relative; display: flex; justify-content: center; }
  .notes-input {
    display: none;
    position: absolute;
    bottom: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    width: 280px;
    padding: 8px 10px;
    border: 1px solid #ccc;
    border-radius: 20px;
    font-size: 13px;
    outline: none;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    z-index: 100;
  }
  .notes-input:focus { border-color: #1877f2; }
  .comment-wrapper:hover .notes-input { display: block; }
  .share-btn { color: #bbb; cursor: default; flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px; padding: 8px; font-size: 14px; font-weight: 600; }
  .rating-label {
    text-align: center;
    font-size: 12px;
    color: #aaa;
    padding-bottom: 6px;
  }
  .rating-label.approved { color: #42b72a; font-weight: 600; }
  .rating-label.rejected { color: #e02020; font-weight: 600; }

  .submit-section {
    text-align: center;
    max-width: 400px;
    margin: 0 auto 60px;
  }
  .submit-btn {
    background: #1877f2;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 14px 40px;
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s;
  }
  .submit-btn:hover { background: #1558b0; }
  .submit-btn:disabled { background: #b0c4de; cursor: not-allowed; }
  .submit-warning {
    color: #e02020;
    font-size: 13px;
    margin-top: 10px;
    display: none;
  }

  #result-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.6);
    z-index: 999;
    align-items: center;
    justify-content: center;
  }
  #result-overlay.visible { display: flex; }
  .result-card {
    background: white;
    border-radius: 12px;
    padding: 40px 50px;
    text-align: center;
    box-shadow: 0 4px 30px rgba(0,0,0,0.3);
  }
  .result-card h2 { font-size: 22px; color: #1c1e21; margin-bottom: 10px; }
  .result-card p { font-size: 15px; color: #65676b; }
</style>
</head>
<body>

<h1>DuberyMNL — Caption Review</h1>
<p class="subtitle">{{ captions|length }} captions pending review &nbsp;·&nbsp; Rate all before submitting</p>

<div class="cards-grid" id="cards-grid">
{% for cap in captions %}
<div class="card" data-id="{{ cap.ID }}" data-row="{{ cap._row }}">
  <div class="card-header">
    <div class="avatar">D</div>
    <div class="page-meta">
      <div class="page-name">DuberyMNL</div>
      <div class="post-meta">Just now &nbsp;·&nbsp; 🌐</div>
    </div>
    <div class="vibe-badge">{{ cap.Vibe }}</div>
  </div>

  <div class="card-image">
    <button class="anchor-toggle" onclick="toggleAnchor(this)"
            data-value="{{ cap.Visual_Anchor }}">
      {% if cap.Visual_Anchor == 'PERSON' %}👤 PERSON{% else %}📦 PRODUCT{% endif %}
    </button>
    <div class="image-placeholder">
      📷 Image placeholder<br>
      <small>{{ cap.Visual_Anchor }}</small>
    </div>
  </div>

  <div class="card-body">
    <div class="caption-text" contenteditable="true"
         data-field="caption">{{ cap.Caption }}</div>
    <div class="hashtags-text" contenteditable="true"
         data-field="hashtags">{{ cap.Hashtags }}</div>
    <div class="edit-hint">Click caption or hashtags to edit</div>
  </div>

  <div class="card-divider"></div>

  <div class="rating-label" data-label="{{ cap.ID }}">Not rated yet</div>

  <div class="card-actions">
    <div class="like-wrapper">
      <button class="action-btn like-btn" title="Rate this caption">
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
      <button class="action-btn" title="Add feedback notes">
        💬 Comment
      </button>
      <input class="notes-input" type="text" placeholder="Add feedback for calibration..." />
    </div>

    <div class="share-btn" title="Placeholder">↗ Share</div>
  </div>
</div>
{% endfor %}
</div>

<div class="submit-section">
  <button class="submit-btn" onclick="submitAll()">Submit All</button>
  <div class="submit-warning" id="submit-warning">Please rate all captions before submitting.</div>
</div>

<div id="result-overlay">
  <div class="result-card">
    <h2 id="result-title">Review submitted!</h2>
    <p id="result-body">Saving to Google Sheets...</p>
  </div>
</div>

<script>
function toggleAnchor(btn) {
  const card = btn.closest('.card');
  const img = card.querySelector('.image-placeholder small');
  if (btn.dataset.value === 'PERSON') {
    btn.dataset.value = 'PRODUCT';
    btn.textContent = '📦 PRODUCT';
    if (img) img.textContent = 'PRODUCT';
  } else {
    btn.dataset.value = 'PERSON';
    btn.textContent = '👤 PERSON';
    if (img) img.textContent = 'PERSON';
  }
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

  const payload = [...cards].map(card => ({
    id: card.dataset.id,
    row: parseInt(card.dataset.row),
    caption: card.querySelector('[data-field="caption"]').innerText,
    hashtags: card.querySelector('[data-field="hashtags"]').innerText,
    visual_anchor: card.querySelector('.anchor-toggle').dataset.value,
    rating: parseInt(card.dataset.rating),
    notes: card.querySelector('.notes-input').value
  }));

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
    data = request.get_json()
    approved = 0
    rejected = 0

    for item in data:
        status = update_caption_row(
            row_index=item["row"],
            caption_text=item["caption"],
            hashtags=item["hashtags"],
            visual_anchor=item["visual_anchor"],
            rating=str(item["rating"]),
            notes=item["notes"],
        )
        if status == "APPROVED":
            approved += 1
        else:
            rejected += 1

    result = {"approved": approved, "rejected": rejected}

    # Shut down after a short delay so the response can be sent first
    def shutdown():
        import time
        time.sleep(1.5)
        os._exit(0)

    threading.Thread(target=shutdown, daemon=True).start()
    return jsonify(result)


if __name__ == "__main__":
    if not SPREADSHEET_ID:
        print("Error: GOOGLE_SHEETS_SPREADSHEET_ID not set in .env", file=sys.stderr)
        sys.exit(1)
    print("Review server starting at http://localhost:5000")
    print("Keep this terminal open until you submit the review.")
    app.run(host="0.0.0.0", port=5000, debug=False)

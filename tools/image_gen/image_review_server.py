"""
WF3 Image Review Server — Flask UI for reviewing generated ad images.

Reads DONE captions from .tmp/pipeline.json.
Approve sets status=IMAGE_APPROVED, syncs to Approved sheet.
Reject sets status=IMAGE_REJECTED, moves to rejected_captions.json, syncs to Rejected sheet.
Regenerate sets status=REGENERATE, syncs to Regenerate sheet.
Skip leaves status as DONE (reappears next session).

Run:
    python tools/image_gen/image_review_server.py          # ad images
    python tools/image_gen/image_review_server.py --ugc    # UGC images
"""

import argparse
try:
    import fcntl
except ImportError:
    fcntl = None
    import msvcrt
import os
import sys
import json
from pathlib import Path

import subprocess
from flask import Flask, request, jsonify, render_template_string, send_from_directory

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False

PROJECT_DIR = Path(__file__).parent.parent.parent
TMP_DIR = PROJECT_DIR / ".tmp"
PIPELINE_LOCK = TMP_DIR / "pipeline.json.lock"

# Defaults (ad mode) — overridden by --ugc flag at startup
CAPTIONS_FILE = TMP_DIR / "pipeline.json"
REJECTED_FILE = TMP_DIR / "rejected_captions.json"
IMAGES_DIR = PROJECT_DIR / "contents" / "ads"
IMAGE_PREFIX = "dubery"

PIPELINE_SHEET_ID = "1LVshSQP5Ob9RNqt35PoSjbUuAiu9dneyHHhUiUZKYrg"

app = Flask(__name__)


def _get_sheets_service():
    """Build Google Sheets service from local OAuth tokens."""
    if not SHEETS_AVAILABLE:
        return None
    try:
        token_path = PROJECT_DIR / "token.json"
        creds_path = PROJECT_DIR / "credentials.json"
        if not token_path.exists() or not creds_path.exists():
            return None
        with open(token_path) as f:
            token_data = json.load(f)
        with open(creds_path) as f:
            creds_data = json.load(f)
        creds = Credentials(
            token=token_data["token"],
            refresh_token=token_data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=creds_data["installed"]["client_id"],
            client_secret=creds_data["installed"]["client_secret"],
        )
        return build("sheets", "v4", credentials=creds)
    except Exception as e:
        print(f"Sheet sync unavailable: {e}")
        return None


def _build_sheet_row(caption: dict, sheet_name: str = "") -> list:
    """Build a row for the Google Sheet from a caption dict.
    Approved sheet uses: Caption ID, Status, Headline, Caption Text, Vibe, Angle, Visual Anchor, Rating
    Rejected/Regenerate use: Caption ID, Status, Caption Text, Product Ref, Thumbnail, Image URL, Feedback, Date
    """
    cid = str(caption.get("id", ""))
    if sheet_name == "Approved":
        url = caption.get("image_url", "") or caption.get("drive_url", "")
        file_id = None
        if "/d/" in url:
            file_id = url.split("/d/")[1].split("/")[0]
        elif "id=" in url:
            file_id = url.split("id=")[1].split("&")[0]
        thumb = f'=IMAGE("https://lh3.googleusercontent.com/d/{file_id}=w400", 1)' if file_id else ""
        has_image = "YES" if url else "NO"
        has_prompt = "YES"
        feedback = caption.get("image_feedback", "")
        return [cid, caption.get("status", ""), caption.get("headline", ""),
                caption.get("caption_text", "")[:150], caption.get("vibe", ""),
                caption.get("angle", ""), caption.get("visual_anchor", ""),
                str(caption.get("rating", "")),
                caption.get("recommended_products", ""), thumb, url,
                "", has_image, has_prompt, feedback, ""]
    else:
        url = caption.get("image_url", "") or caption.get("drive_url", "")
        file_id = None
        if "/d/" in url:
            file_id = url.split("/d/")[1].split("/")[0]
        elif "id=" in url:
            file_id = url.split("id=")[1].split("&")[0]
        thumb = f'=IMAGE("https://lh3.googleusercontent.com/d/{file_id}=w400", 1)' if file_id else ""
        feedback = caption.get("image_feedback", "") or caption.get("regeneration_instructions", "")
        return [cid, caption.get("status", ""), caption.get("caption_text", "")[:150],
                caption.get("recommended_products", ""), thumb, url, feedback, ""]


def _sync_to_sheet(caption: dict, sheet_name: str):
    """Append a caption row to the named sheet tab. Skips if caption ID already exists."""
    svc = _get_sheets_service()
    if not svc:
        return
    try:
        caption_id = str(caption.get("id", ""))
        # Check if already exists
        existing = svc.spreadsheets().values().get(
            spreadsheetId=PIPELINE_SHEET_ID,
            range=f"{sheet_name}!A:A",
        ).execute()
        for row in existing.get("values", []):
            if row and str(row[0]) == caption_id:
                print(f"  #{caption_id} already in {sheet_name} sheet, skipping")
                return
        row = _build_sheet_row(caption, sheet_name)
        svc.spreadsheets().values().append(
            spreadsheetId=PIPELINE_SHEET_ID,
            range=f"{sheet_name}!A2",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()
        print(f"  Synced #{caption.get('id')} to {sheet_name} sheet")
    except Exception as e:
        print(f"  Sheet sync failed ({sheet_name}): {e}")


def _remove_from_sheet(caption_id: str, sheet_name: str):
    """Remove a row from a sheet tab by caption ID (for moves between sheets)."""
    svc = _get_sheets_service()
    if not svc:
        return
    try:
        result = svc.spreadsheets().values().get(
            spreadsheetId=PIPELINE_SHEET_ID,
            range=f"{sheet_name}!A:A",
        ).execute()
        rows = result.get("values", [])
        row_idx = None
        for i, row in enumerate(rows):
            if row and str(row[0]) == caption_id:
                row_idx = i
                break
        if row_idx is not None:
            # Get sheet ID for delete request
            meta = svc.spreadsheets().get(spreadsheetId=PIPELINE_SHEET_ID).execute()
            sheet_id = None
            for s in meta["sheets"]:
                if s["properties"]["title"] == sheet_name:
                    sheet_id = s["properties"]["sheetId"]
                    break
            if sheet_id is not None:
                svc.spreadsheets().batchUpdate(
                    spreadsheetId=PIPELINE_SHEET_ID,
                    body={"requests": [{"deleteDimension": {
                        "range": {"sheetId": sheet_id, "dimension": "ROWS",
                                  "startIndex": row_idx, "endIndex": row_idx + 1}
                    }}]},
                ).execute()
                print(f"  Removed #{caption_id} from {sheet_name} sheet")
    except Exception as e:
        print(f"  Sheet remove failed ({sheet_name}): {e}")


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


def update_caption(caption_id: str, fields: dict):
    """Update fields on a caption in pipeline.json by ID (file-locked)."""
    if not CAPTIONS_FILE.exists():
        return
    with open(PIPELINE_LOCK, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX) if fcntl else msvcrt.locking(lf.fileno(), msvcrt.LK_LOCK, 1)
        try:
            captions = json.loads(CAPTIONS_FILE.read_text())
            CAPTIONS_FILE.with_suffix(".json.bak").write_text(
                json.dumps(captions, indent=2, ensure_ascii=False)
            )
            for caption in captions:
                if str(caption.get("id")) == caption_id:
                    caption.update(fields)
                    break
            CAPTIONS_FILE.write_text(json.dumps(captions, indent=2, ensure_ascii=False))
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN) if fcntl else msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)


def reject_caption(caption_id: str, fields: dict):
    """Update fields, move caption from pipeline.json to rejected_captions.json (file-locked)."""
    if not CAPTIONS_FILE.exists():
        return
    with open(PIPELINE_LOCK, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX) if fcntl else msvcrt.locking(lf.fileno(), msvcrt.LK_LOCK, 1)
        try:
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
                rejected = _read_json_list(REJECTED_FILE)
                rejected.append(target)
                _write_json_list(REJECTED_FILE, rejected)
            CAPTIONS_FILE.write_text(json.dumps(remaining, indent=2, ensure_ascii=False))
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN) if fcntl else msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)
    # Move image file to rejected folder
    src = IMAGES_DIR / f"{IMAGE_PREFIX}_{caption_id}.jpg"
    dst = IMAGES_DIR / "rejected" / f"{IMAGE_PREFIX}_{caption_id}.jpg"
    if src.exists():
        dst.parent.mkdir(exist_ok=True)
        src.rename(dst)


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
  .btn-approve    { background: #42b72a; color: white; }
  .btn-reject     { background: #e02020; color: white; }
  .btn-regenerate { background: #f5a623; color: white; }
  .btn-skip       { background: #e4e6eb; color: #606770; }
  .regen-mode-toggle {
    display: flex;
    gap: 0;
    margin-bottom: 8px;
  }
  .regen-mode-btn {
    flex: 1;
    padding: 7px 10px;
    border: 2px solid #f5a623;
    background: #fff;
    color: #f5a623;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.15s;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .regen-mode-btn:first-child { border-radius: 6px 0 0 6px; }
  .regen-mode-btn:last-child { border-radius: 0 6px 6px 0; }
  .regen-mode-btn.active {
    background: #f5a623;
    color: white;
  }
  .regen-mode-label {
    font-size: 11px;
    color: #65676b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }
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

  <div class="card-actions" style="flex-wrap: wrap;">
    <div style="width: 100%; padding: 0 0 6px;">
      <div class="regen-mode-label">Regen mode</div>
      <div class="regen-mode-toggle" id="regen-toggle-{{ cap.id }}">
        <button type="button" class="regen-mode-btn active" onclick="setRegenMode('{{ cap.id }}', 'edit', this)">Edit</button>
        <button type="button" class="regen-mode-btn" onclick="setRegenMode('{{ cap.id }}', 'regen', this)">Full Regen</button>
      </div>
    </div>
    <button class="btn btn-approve"    onclick="approve('{{ cap.id }}')">Approve</button>
    <button class="btn btn-reject"     onclick="reject('{{ cap.id }}')">Reject</button>
    <button class="btn btn-regenerate" onclick="regenerate('{{ cap.id }}')">Regenerate</button>
    <button class="btn btn-skip"       onclick="skip('{{ cap.id }}')">Skip</button>
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
        syncPipeline();
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

let regenModes = {};

function setRegenMode(id, mode, btn) {
  regenModes[id] = mode;
  const toggle = document.getElementById('regen-toggle-' + id);
  toggle.querySelectorAll('.regen-mode-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

function regenerate(id) {
  const fb = getFeedback(id);
  if (!fb) {
    alert('Please add feedback/instructions before regenerating.');
    document.getElementById('feedback-' + id).focus();
    return;
  }
  const mode = regenModes[id] || 'edit';
  fetch('/regenerate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: String(id), feedback: fb, mode: mode })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) removeCard(id);
    else alert('Error requesting regeneration. Check terminal.');
  })
  .catch(() => alert('Network error. Check terminal.'));
}

function skip(id) {
  removeCard(id);
}

function syncPipeline() {
  document.getElementById('all-done').textContent = 'All images reviewed. Syncing pipeline...';
  fetch('/sync', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      document.getElementById('all-done').textContent = 'All images reviewed. Pipeline synced.';
    } else {
      document.getElementById('all-done').textContent = 'All images reviewed. Sync failed -- check terminal.';
    }
  })
  .catch(() => {
    document.getElementById('all-done').textContent = 'All images reviewed. Sync failed -- check terminal.';
  });
}
</script>
</body>
</html>
"""


@app.route("/")
def index():
    captions = load_done_captions()
    return render_template_string(HTML_TEMPLATE, captions=captions)


@app.route("/image/<path:caption_id>")
def serve_image(caption_id):
    for ext in [".jpg", ".jpeg", ".png"]:
        filepath = IMAGES_DIR / f"{IMAGE_PREFIX}_{caption_id}{ext}"
        if filepath.exists():
            return send_from_directory(str(IMAGES_DIR), filepath.name)
    return send_from_directory(str(IMAGES_DIR), f"{IMAGE_PREFIX}_{caption_id}.jpg")


@app.route("/approve", methods=["POST"])
def approve():
    data = request.get_json()
    caption_id = str(data.get("id", "")).strip()
    if not caption_id:
        return jsonify({"success": False, "error": "Missing id"}), 400
    fields = {"status": "IMAGE_APPROVED"}
    if data.get("feedback"):
        fields["image_feedback"] = data["feedback"]
    update_caption(caption_id, fields)
    print(f"Caption #{caption_id} approved → IMAGE_APPROVED in pipeline.json")
    # Sync to Approved sheet
    captions = json.loads(CAPTIONS_FILE.read_text())
    cap = next((c for c in captions if str(c.get("id")) == caption_id), None)
    if cap:
        _sync_to_sheet(cap, "Approved")
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
    # Read caption before rejecting (it gets moved out of pipeline.json)
    captions = json.loads(CAPTIONS_FILE.read_text())
    cap = next((c for c in captions if str(c.get("id")) == caption_id), None)
    reject_caption(caption_id, fields)
    print(f"Caption #{caption_id} rejected → rejected_captions.json. Feedback: {data.get('feedback', '')}")
    # Sync to Rejected sheet
    if cap:
        cap.update(fields)
        _sync_to_sheet(cap, "Rejected")
    return jsonify({"success": True})


@app.route("/regenerate", methods=["POST"])
def regenerate():
    data = request.get_json()
    caption_id = str(data.get("id", "")).strip()
    if not caption_id:
        return jsonify({"success": False, "error": "Missing id"}), 400
    feedback = data.get("feedback", "").strip()
    if not feedback:
        return jsonify({"success": False, "error": "Feedback required for regeneration"}), 400
    mode = data.get("mode", "edit")
    fields = {
        "status": "REGENERATE",
        "regeneration_instructions": feedback,
        "regeneration_mode": mode,
    }
    update_caption(caption_id, fields)
    print(f"Caption #{caption_id} marked for REGENERATION [{mode.upper()}]. Instructions: {feedback}")
    # Sync to Regenerate sheet
    captions = json.loads(CAPTIONS_FILE.read_text())
    cap = next((c for c in captions if str(c.get("id")) == caption_id), None)
    if cap:
        _sync_to_sheet(cap, "Regenerate")
    return jsonify({"success": True})


@app.route("/sync", methods=["POST"])
def sync_pipeline():
    """Run sync_pipeline.py to sync pipeline.json to Google Sheet + Notion."""
    try:
        venv_python = PROJECT_DIR / ".venv" / "bin" / "python"
        sync_script = PROJECT_DIR / "tools" / "notion" / "sync_pipeline.py"
        result = subprocess.run(
            [str(venv_python), str(sync_script)],
            cwd=PROJECT_DIR, capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print("Pipeline sync completed successfully")
            return jsonify({"success": True, "output": result.stdout[-500:]})
        else:
            print(f"Pipeline sync failed: {result.stderr[:300]}")
            return jsonify({"success": False, "error": result.stderr[:300]}), 500
    except Exception as e:
        print(f"Pipeline sync error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/status")
def status():
    captions = load_done_captions()
    return jsonify({"pending": len(captions)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image review server")
    parser.add_argument("--ugc", action="store_true", help="Review UGC images instead of ad images")
    args = parser.parse_args()

    if args.ugc:
        CAPTIONS_FILE = TMP_DIR / "ugc_pipeline.json"
        REJECTED_FILE = TMP_DIR / "ugc_rejected.json"
        IMAGES_DIR = PROJECT_DIR / "contents" / "ugc"
        IMAGE_PREFIX = "ugc_UGC"
        mode_label = "UGC"
    else:
        mode_label = "Ad"

    TMP_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    if not CAPTIONS_FILE.exists():
        print(f"No pipeline file found at {CAPTIONS_FILE}", file=sys.stderr)
        sys.exit(1)

    done_count = len(load_done_captions())
    print(f"{mode_label} image review server starting at http://localhost:5001")
    print(f"{done_count} image(s) ready for review.")
    app.run(host="0.0.0.0", port=5001, debug=False)

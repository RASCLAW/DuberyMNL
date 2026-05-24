"""DuberyMNL Command Center -- Flask server.

Local web dashboard for ops + Claude Agent SDK-backed chat. Runs on
localhost:8090 by default. Uses Claude Code subscription auth via the SDK.

Run:
    cd c:/Users/RAS/projects/DuberyMNL/command-center
    python app.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Windows console is cp1252; force UTF-8 so print/log never crashes on
# non-Latin-1 characters (Filipino text, emoji, ellipses from Claude output).
if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Windows: suppress the cmd window flash on every child process this app spawns.
# The Claude Agent SDK shells out to the `claude` CLI; without this each chat
# call pops a console for ~1s. Patches subprocess.Popen globally for this process.
if sys.platform == "win32":
    import subprocess as _sp
    _CREATE_NO_WINDOW = 0x08000000
    _orig_popen_init = _sp.Popen.__init__
    def _silent_popen_init(self, *args, **kwargs):
        kwargs["creationflags"] = (kwargs.get("creationflags") or 0) | _CREATE_NO_WINDOW
        _orig_popen_init(self, *args, **kwargs)
    _sp.Popen.__init__ = _silent_popen_init

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Ensure project root is importable (chatbot.crm_sync, etc.)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import json
import threading

from flask import Flask, Response, jsonify, redirect, render_template, request, send_from_directory, session

from concurrent.futures import ThreadPoolExecutor, as_completed

from agent_session import AgentSession
from monitors import SERVICES, ServiceStatus, service_names_in_order
from monitors.registry import register_all

register_all()

# Fix commands for services that can be auto-started.
# Each value is a shell command run via subprocess on the server.
FIX_COMMANDS: dict[str, dict] = {
    "chatbot": {
        "label": "Start chatbot",
        "cmd": ["python", str(PROJECT_ROOT / "chatbot" / "messenger_webhook.py")],
        "bg": True,  # run in background, don't wait for exit
    },
    "tunnel": {
        "label": "Start tunnel",
        "cmd": ["cloudflared", "tunnel", "run", "dubery-tunnel"],
        "bg": True,
    },
}

HERE = Path(__file__).resolve().parent
STATIC_DIR = HERE / "static"
TEMPLATE_DIR = HERE / "templates"
PORT = int(os.environ.get("COMMAND_CENTER_PORT", "8090"))
CC_SECRET_TOKEN = os.environ.get("CC_SECRET_TOKEN", "")
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "")

app = Flask(
    __name__,
    static_folder=str(STATIC_DIR),
    template_folder=str(TEMPLATE_DIR),
)
app.secret_key = FLASK_SECRET_KEY or "local-dev-only"

# Paths that don't require auth (local health + the unlock endpoint itself)
_AUTH_EXEMPT = {"/health", "/favicon.ico"}


@app.before_request
def _require_auth():
    if request.path in _AUTH_EXEMPT or request.path.startswith("/auth/"):
        return
    # Allow unrestricted local access (Task Scheduler / localhost browser)
    host = request.host.split(":")[0]
    if host in ("localhost", "127.0.0.1"):
        return
    if not session.get("authed"):
        return ("Unauthorized", 403)


@app.route("/auth/<token>")
def auth_unlock(token: str):
    """Secret URL: visiting this once sets a session cookie granting full access."""
    if not CC_SECRET_TOKEN or token != CC_SECRET_TOKEN:
        return ("Forbidden", 403)
    session["authed"] = True
    session.permanent = True
    return redirect("/")


@app.before_request
def _req_start():
    from flask import g
    g._t0 = time.perf_counter()


@app.after_request
def _req_log(resp):
    from flask import g
    origin = request.headers.get("Origin", "")
    if origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1"):
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    try:
        dur_ms = (time.perf_counter() - g._t0) * 1000
    except Exception:
        dur_ms = 0
    print(f"{request.method} {request.path} {resp.status_code} {dur_ms:.0f}ms", flush=True)
    return resp


@app.route("/<path:any>", methods=["OPTIONS"])
def _cors_preflight(any):
    return ("", 204)


@app.route("/")
def index():
    # shell.html is the single-page app container. Created in Task 21.
    # Return a placeholder for now so /health works during Phase 1A.
    if (TEMPLATE_DIR / "shell.html").exists():
        return render_template("shell.html")
    return (
        "<html><body style='background:#0d1117;color:#f0f6fc;"
        "font-family:sans-serif;padding:40px;'>"
        "<h1>DuberyMNL Command Center</h1>"
        "<p>Backend is live. Shell template not yet built (Phase 1C).</p>"
        "<p><a href='/health' style='color:#ff9e4b;'>/health</a></p>"
        "</body></html>"
    )


@app.route("/health")
def health():
    return jsonify({"ok": True, "port": PORT})


@app.route("/api/products", methods=["GET"])
def list_products():
    """Return available product keys from product-specs.json."""
    specs_path = PROJECT_ROOT / "contents" / "assets" / "product-specs.json"
    try:
        products = list(json.load(open(specs_path)).keys())
    except Exception:
        products = []
    return jsonify(products)


@app.route("/api/log-generation", methods=["POST"])
def log_generation():
    """Log a content generation event with full details."""
    payload = request.get_json(silent=True) or {}
    log_dir = PROJECT_ROOT / ".tmp"
    log_dir.mkdir(exist_ok=True)
    history_file = log_dir / "content-gen-history.json"

    from datetime import datetime
    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "images": payload.get("images", []),
        "prompt_paths": payload.get("prompt_paths", []),
        "aspect_ratio": payload.get("aspect_ratio", "1:1"),
        "mode": payload.get("mode", ""),
        "type": payload.get("type", ""),
        "count": payload.get("count", 0),
        "products": payload.get("products", []),
        "direction": payload.get("direction", ""),
        "concept_paths": payload.get("concept_paths", []),
    }

    # Append to JSON array file
    history = []
    if history_file.exists():
        try:
            history = json.load(open(history_file, encoding="utf-8"))
        except Exception:
            history = []
    history.append(entry)
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    # Also write human-readable log
    log_file = log_dir / "content-gen.log"
    ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{ts_str}] {entry['count']} {entry['mode']}/{entry['type']} | products: {', '.join(entry['products']) or 'random'} | images: {', '.join(entry['images'])}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_line)

    return jsonify({"ok": True})


@app.route("/api/generation-history", methods=["GET"])
def generation_history():
    """Return generation history for the Content Gen tab."""
    history_file = PROJECT_ROOT / ".tmp" / "content-gen-history.json"
    if not history_file.exists():
        return jsonify([])
    try:
        history = json.load(open(history_file, encoding="utf-8"))
        return jsonify(history)
    except Exception:
        return jsonify([])


@app.route("/api/upload-concept", methods=["POST"])
def upload_concept():
    """Accept an image upload (multipart or base64) and save to .tmp/."""
    import base64
    tmp_dir = PROJECT_ROOT / ".tmp"
    tmp_dir.mkdir(exist_ok=True)

    ts = int(time.time() * 1000)

    # Handle multipart FormData (from video.js file picker)
    if "file" in request.files:
        f = request.files["file"]
        ext = Path(f.filename).suffix.lstrip(".") or "png"
        filename = f"concept-{ts}.{ext}"
        filepath = tmp_dir / filename
        f.save(str(filepath))
        return jsonify({"ok": True, "path": str(filepath), "filename": filename})

    # Handle base64 JSON payload (from clipboard paste)
    payload = request.get_json(silent=True)
    if payload and payload.get("image_data"):
        data = payload["image_data"]
        # Strip data URL prefix if present
        if "," in data:
            data = data.split(",", 1)[1]
        img_bytes = base64.b64decode(data)
        ext = payload.get("ext", "png")
        filename = f"concept-{ts}.{ext}"
        filepath = tmp_dir / filename
        filepath.write_bytes(img_bytes)
        rel_path = f".tmp/{filename}"
        return jsonify({"ok": True, "path": rel_path, "filename": filename})

    return jsonify({"ok": False, "error": "no image data"}), 400


@app.route("/api/content-stats", methods=["GET"])
def content_stats():
    """Count images in contents/ready/ by product and type."""
    ready = PROJECT_ROOT / "contents" / "ready"
    exts = {".png", ".jpg", ".jpeg", ".webp"}

    def count_dir(d):
        if not d.exists():
            return 0
        return sum(1 for f in d.iterdir() if f.is_file() and f.suffix.lower() in exts)

    stats = {}
    # Person shots per product
    person_dir = ready / "person"
    product_dir = ready / "product"
    brand_dir = ready / "brand"

    all_models = set()
    if person_dir.exists():
        all_models.update(d.name for d in person_dir.iterdir() if d.is_dir())
    if product_dir.exists():
        all_models.update(d.name for d in product_dir.iterdir() if d.is_dir())

    products = {}
    for model in sorted(all_models):
        products[model] = {
            "person": count_dir(person_dir / model),
            "product": count_dir(product_dir / model),
        }

    brand_count = count_dir(brand_dir) if brand_dir.exists() else 0

    total_person = sum(p["person"] for p in products.values())
    total_product = sum(p["product"] for p in products.values())

    return jsonify({
        "products": products,
        "brand": brand_count,
        "totals": {
            "person": total_person,
            "product": total_product,
            "brand": brand_count,
            "all": total_person + total_product + brand_count,
        },
    })


@app.route("/api/images/<path:filepath>")
def serve_image(filepath):
    """Serve generated images from the project directory."""
    full = PROJECT_ROOT / filepath
    if not full.exists() or not full.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm"}:
        return ("not found", 404)
    return send_from_directory(str(full.parent), full.name)


_THUMB_CACHE_DIR = PROJECT_ROOT / ".tmp" / "thumb_cache"
_THUMB_ALLOWED_WIDTHS = {120, 180, 240, 320, 480, 640}


@app.route("/api/thumb/<path:filepath>")
def serve_thumb(filepath):
    """Serve a cached, downscaled JPEG of an image. Query: ?w=240 (default).

    First request generates + caches to .tmp/thumb_cache/. Subsequent requests
    are zero-Pillow file serves. Cache is keyed by source mtime so edits regen.
    """
    try:
        w_raw = request.args.get("w", "240")
        w = int(w_raw)
    except Exception:
        w = 240
    if w not in _THUMB_ALLOWED_WIDTHS:
        # Snap to nearest allowed width to bound cache cardinality
        w = min(_THUMB_ALLOWED_WIDTHS, key=lambda x: abs(x - w))

    src = _safe_project_path(filepath)
    if src is None or not src.exists() or src.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        return ("not found", 404)

    # Cache key: <safe-name>.<mtime>.<width>.jpg
    import hashlib
    key = hashlib.sha1((filepath + "|" + str(src.stat().st_mtime_ns) + "|" + str(w)).encode("utf-8")).hexdigest()
    _THUMB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out = _THUMB_CACHE_DIR / f"{key}.jpg"

    if not out.exists():
        try:
            from PIL import Image
            with Image.open(src) as im:
                if im.mode in ("RGBA", "LA", "P"):
                    bg = Image.new("RGB", im.size, (255, 255, 255))
                    bg.paste(im, mask=im.convert("RGBA").split()[-1] if im.mode != "P" else None)
                    im = bg
                elif im.mode != "RGB":
                    im = im.convert("RGB")
                im.thumbnail((w, w * 4), Image.LANCZOS)
                im.save(out, "JPEG", quality=82, optimize=True, progressive=True)
        except Exception as exc:
            print(f"[thumb] generate failed for {filepath}: {exc}", flush=True)
            return ("thumb generation failed", 500)

    resp = send_from_directory(str(out.parent), out.name)
    resp.headers["Cache-Control"] = "public, max-age=2592000"  # 30 days; cache key includes mtime so fresh edits bypass
    return resp


def _safe_project_path(rel: str) -> Path | None:
    """Resolve a relative path under PROJECT_ROOT, rejecting traversal."""
    try:
        p = (PROJECT_ROOT / rel).resolve()
    except Exception:
        return None
    try:
        p.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return None
    return p


@app.route("/api/file-content/<path:filepath>")
def file_content(filepath):
    """Return text content of a file (prompt JSONs, sidecars). Scoped to project root."""
    p = _safe_project_path(filepath)
    if p is None or not p.exists() or not p.is_file():
        return ("not found", 404)
    if p.suffix.lower() not in {".json", ".txt", ".md"}:
        return ("unsupported type", 400)
    try:
        text = p.read_text(encoding="utf-8")
    except Exception as e:
        return (f"read failed: {e}", 500)
    return Response(text, mimetype="text/plain; charset=utf-8")


@app.route("/api/save-run", methods=["POST"])
def save_run():
    """Archive a generation run: copy images + prompt JSONs + concepts into contents/runs/<ts>_<mode>/.

    Request JSON: {
      images: [<rel paths under contents/new/>],
      prompt_paths: [<rel paths>],
      concept_paths: [<rel paths in .tmp/>],
      mode, type, count, products[], direction, aspect_ratio
    }

    Writes a run.json manifest alongside the copied files.
    """
    import shutil
    from datetime import datetime

    payload = request.get_json(silent=True) or {}
    images = payload.get("images") or []
    prompt_paths = payload.get("prompt_paths") or []
    concept_paths = payload.get("concept_paths") or []

    if not images:
        return jsonify({"ok": False, "error": "no images to save"}), 400

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    mode = (payload.get("mode") or "run").lower()
    run_dir = PROJECT_ROOT / "contents" / "runs" / f"{ts}_{mode}"
    run_dir.mkdir(parents=True, exist_ok=True)

    copied_images: list[str] = []
    copied_prompts: list[str] = []
    copied_concepts: list[str] = []

    for rel in images:
        src = _safe_project_path(rel)
        if not src or not src.exists():
            continue
        dest = run_dir / src.name
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)
        copied_images.append(f"contents/runs/{run_dir.name}/{dest.name}")

    # Prompt JSONs -- derive from image path if not provided
    if not prompt_paths:
        for rel in images:
            src = _safe_project_path(rel)
            if not src:
                continue
            pj = src.with_name(src.stem + "_prompt.json")
            if pj.exists():
                prompt_paths.append(str(pj.relative_to(PROJECT_ROOT)).replace("\\", "/"))

    for rel in prompt_paths:
        src = _safe_project_path(rel)
        if not src or not src.exists():
            continue
        dest = run_dir / src.name
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)
        copied_prompts.append(f"contents/runs/{run_dir.name}/{dest.name}")

    for rel in concept_paths:
        src = _safe_project_path(rel)
        if not src or not src.exists():
            continue
        dest = run_dir / ("concept_" + src.name)
        shutil.copy2(src, dest)
        copied_concepts.append(f"contents/runs/{run_dir.name}/{dest.name}")

    manifest = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "mode": payload.get("mode", ""),
        "type": payload.get("type", ""),
        "count": payload.get("count", 0),
        "products": payload.get("products", []),
        "direction": payload.get("direction", ""),
        "aspect_ratio": payload.get("aspect_ratio", "1:1"),
        "images": copied_images,
        "prompts": copied_prompts,
        "concepts": copied_concepts,
    }
    (run_dir / "run.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return jsonify({
        "ok": True,
        "run_dir": f"contents/runs/{run_dir.name}",
        "images": copied_images,
        "prompts": copied_prompts,
        "concepts": copied_concepts,
    })


@app.route("/api/marketing/presets", methods=["GET"])
def marketing_presets():
    """Return audience + budget presets from command-center/presets/marketing.json."""
    presets_file = HERE / "presets" / "marketing.json"
    if not presets_file.exists():
        return jsonify({"audiences": {}, "budgets": {}})
    try:
        return jsonify(json.loads(presets_file.read_text(encoding="utf-8")))
    except Exception as e:
        return jsonify({"error": f"read failed: {e}"}), 500


@app.route("/api/marketing/content", methods=["GET"])
def marketing_content():
    """List images in contents/ready/ for the Marketing picker.

    Returns [{path, filename, type, model, tags, mtime}]. Reads
    contents/ready/manifest.json for tags when available.
    """
    ready = PROJECT_ROOT / "contents" / "ready"
    if not ready.exists():
        return jsonify([])

    manifest_file = ready / "manifest.json"
    manifest = {}
    if manifest_file.exists():
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}

    exts = {".png", ".jpg", ".jpeg", ".webp"}
    items = []

    # person/* and product/* have a model subdir; brand/ is flat
    def _scan_tree(root: Path, kind: str, has_model: bool):
        if not root.exists():
            return
        if has_model:
            for model_dir in root.iterdir():
                if not model_dir.is_dir():
                    continue
                for f in model_dir.iterdir():
                    if not f.is_file() or f.suffix.lower() not in exts:
                        continue
                    if f.name.endswith("_prompt.json") or f.name.endswith(".bak"):
                        continue
                    rel = f.relative_to(PROJECT_ROOT).as_posix()
                    m = manifest.get(f.name, {})
                    items.append({
                        "path": rel,
                        "filename": f.name,
                        "type": kind,
                        "model": model_dir.name,
                        "tags": m.get("tags", []),
                        "mtime": f.stat().st_mtime,
                    })
        else:
            for f in root.iterdir():
                if not f.is_file() or f.suffix.lower() not in exts:
                    continue
                if f.name.endswith("_prompt.json") or f.name.endswith(".bak"):
                    continue
                rel = f.relative_to(PROJECT_ROOT).as_posix()
                m = manifest.get(f.name, {})
                items.append({
                    "path": rel,
                    "filename": f.name,
                    "type": kind,
                    "model": m.get("model", ""),
                    "tags": m.get("tags", []),
                    "mtime": f.stat().st_mtime,
                })

    _scan_tree(ready / "person", "person", has_model=True)
    _scan_tree(ready / "product", "product", has_model=True)
    _scan_tree(ready / "brand", "brand", has_model=False)
    _scan_tree(PROJECT_ROOT / "contents" / "new", "new", has_model=False)

    items.sort(key=lambda x: x["mtime"], reverse=True)
    return jsonify(items[:200])


@app.route("/api/marketing/insights", methods=["GET"])
def marketing_insights():
    """Pull last-7-day insights via pull_insights.py and return the JSON."""
    import subprocess as sp
    tmp = PROJECT_ROOT / ".tmp"
    tmp.mkdir(exist_ok=True)
    insights_file = tmp / "ad_insights.json"

    try:
        result = sp.run(
            [sys.executable, str(PROJECT_ROOT / "tools" / "meta_ads" / "pull_insights.py"),
             "--quiet", "--days", "7"],
            capture_output=True, text=True, timeout=20,
        )
    except sp.TimeoutExpired:
        return jsonify({"error": "insights fetch timed out"}), 504
    except Exception as e:
        return jsonify({"error": f"subprocess failed: {e}"}), 500

    if result.returncode != 0:
        return jsonify({"error": (result.stderr or result.stdout or "unknown").strip()[:500]}), 502

    if not insights_file.exists():
        return jsonify({"error": "insights file not written"}), 500

    try:
        return jsonify(json.loads(insights_file.read_text(encoding="utf-8")))
    except Exception as e:
        return jsonify({"error": f"parse failed: {e}"}), 500


@app.route("/api/marketing/stage", methods=["POST"])
def marketing_stage():
    """Write a creative plan to .tmp/marketing-plan.json, run stage_creatives.py."""
    import subprocess as sp
    payload = request.get_json(silent=True) or {}
    dry_run = bool(payload.get("dry_run", True))
    ad_set = payload.get("ad_set")
    if not ad_set:
        return jsonify({"ok": False, "error": "ad_set required"}), 400

    tmp = PROJECT_ROOT / ".tmp"
    tmp.mkdir(exist_ok=True)
    plan_file = tmp / "marketing-plan.json"
    plan_file.write_text(
        json.dumps({"ad_set": ad_set}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    cmd = [sys.executable,
           str(PROJECT_ROOT / "tools" / "meta_ads" / "stage_creatives.py"),
           "--plan", str(plan_file)]
    if dry_run:
        cmd.append("--dry-run")

    try:
        result = sp.run(cmd, capture_output=True, text=True, timeout=180)
    except sp.TimeoutExpired:
        return jsonify({"ok": False, "error": "stage timed out (>180s)"}), 504
    except Exception as e:
        return jsonify({"ok": False, "error": f"subprocess failed: {e}"}), 500

    return jsonify({
        "ok": result.returncode == 0,
        "exit": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    })


# ============= MARKETING ANALYTICS (new) =============

def _mkt_extract_actions(actions_list):
    """Flatten Meta actions array to a dict of action_type -> int."""
    out: dict[str, int] = {}
    for a in (actions_list or []):
        try:
            out[a.get("action_type", "")] = int(float(a.get("value", 0)))
        except (TypeError, ValueError):
            continue
    return out


def _mkt_extract_costs(cost_list):
    out: dict[str, float] = {}
    for a in (cost_list or []):
        try:
            out[a.get("action_type", "")] = float(a.get("value", 0))
        except (TypeError, ValueError):
            continue
    return out


def _mkt_load_cache(name: str):
    """Read a .tmp/<name>.json cache file; return (data, mtime_iso) or (None, None)."""
    import json as _json
    from datetime import datetime as _dt2, timezone as _tz2, timedelta as _td2
    path = PROJECT_ROOT / ".tmp" / name
    if not path.exists():
        return None, None
    try:
        data = _json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None, None
    mtime = _dt2.fromtimestamp(path.stat().st_mtime, _tz2(_td2(hours=8))).isoformat()
    return data, mtime


@app.route("/api/marketing/summary", methods=["GET"])
def marketing_summary():
    """Single consolidated read for the Marketing tab.

    Reads cached files written by pull_insights.py, pull_live_meta.py, and
    pull_pixel_stats.py. Doesn't hit Meta API directly -- the /refresh
    endpoint does that. Each section is best-effort; missing sources
    return null instead of failing the whole payload.
    """
    from datetime import datetime as _dt2, timedelta as _td2

    insights, insights_mtime = _mkt_load_cache("ad_insights.json")
    live_meta, live_mtime = _mkt_load_cache("marketing_live_meta.json")
    pixel, pixel_mtime = _mkt_load_cache("pixel_stats.json")
    daily, daily_mtime = _mkt_load_cache("ad_insights_daily.json")

    out: dict = {
        "cache": {
            "insights_mtime": insights_mtime,
            "live_meta_mtime": live_mtime,
            "pixel_mtime": pixel_mtime,
            "daily_mtime": daily_mtime,
        },
        "window": None,
        "snapshot": None,
        "adsets": [],
        "ads": [],
        "pixel": None,
        "gap": None,
        "daily": None,
        "needs_attention": [],
    }

    # ---- Account snapshot + ads list (insights) ----
    pixel_purchase_count = None
    if insights:
        meta = insights.get("meta") or {}
        out["window"] = {
            "from": meta.get("date_from"),
            "to": meta.get("date_to"),
            "campaign_id": meta.get("campaign_id"),
        }
        campaigns = insights.get("campaign") or []
        if campaigns:
            c0 = campaigns[0]
            actions = _mkt_extract_actions(c0.get("actions"))
            costs = _mkt_extract_costs(c0.get("cost_per_action_type"))
            lpv = actions.get("landing_page_view", 0)
            spend = float(c0.get("spend") or 0)
            impr = int(c0.get("impressions") or 0)
            clicks = int(c0.get("clicks") or 0)
            link_clicks = actions.get("link_click", 0)
            msgs = actions.get("onsite_conversion.total_messaging_connection", 0)
            purchases = actions.get("omni_purchase", 0) or actions.get("purchase", 0)
            try:
                df = _dt2.fromisoformat(meta.get("date_from", ""))
                dt = _dt2.fromisoformat(meta.get("date_to", ""))
                days = max(1, (dt - df).days + 1)
            except Exception:
                days = 7
            out["snapshot"] = {
                "spend": round(spend, 2),
                "spend_per_day": round(spend / days, 2),
                "days": days,
                "impressions": impr,
                "cpm": round(spend / impr * 1000, 2) if impr else None,
                "clicks": link_clicks or clicks,
                "cpc": round(spend / link_clicks, 2) if link_clicks else None,
                "lpv": lpv,
                "cost_per_lpv": round(costs.get("landing_page_view", 0), 2) if lpv else None,
                "messages": msgs,
                "purchases_pixel": purchases,
            }
            pixel_purchase_count = purchases

    # ---- Build adset + ad lookup maps from live_meta ----
    adset_meta: dict[str, dict] = {}
    ad_meta: dict[str, dict] = {}
    if live_meta:
        for a in (live_meta.get("adsets") or []):
            adset_meta[a.get("adset_id", "")] = a
        for a in (live_meta.get("ads") or []):
            ad_meta[a.get("ad_id", "")] = a

    # ---- Adsets (insights joined with live meta) ----
    if insights:
        for a in (insights.get("adsets") or []):
            adset_id = a.get("adset_id", "")
            actions = _mkt_extract_actions(a.get("actions"))
            costs = _mkt_extract_costs(a.get("cost_per_action_type"))
            lpv = actions.get("landing_page_view", 0)
            spend = float(a.get("spend") or 0)
            lm = adset_meta.get(adset_id, {})
            out["adsets"].append({
                "adset_id": adset_id,
                "name": a.get("adset_name", "(unknown)"),
                "status": lm.get("effective_status") or lm.get("status") or "UNKNOWN",
                "daily_budget_php": lm.get("daily_budget_php"),
                "spend": round(spend, 2),
                "impressions": int(a.get("impressions") or 0),
                "ctr": float(a.get("ctr") or 0),
                "cpc": float(a.get("cpc") or 0),
                "lpv": lpv,
                "cost_per_lpv": round(costs.get("landing_page_view", 0), 2) if lpv else None,
                "messages": actions.get("onsite_conversion.total_messaging_connection", 0),
                "purchases": actions.get("omni_purchase", 0) or actions.get("purchase", 0),
            })

    # ---- Ads (insights joined with live meta, including thumbnails) ----
    if insights:
        for a in (insights.get("ads") or []):
            ad_id = a.get("ad_id", "")
            actions = _mkt_extract_actions(a.get("actions"))
            costs = _mkt_extract_costs(a.get("cost_per_action_type"))
            lpv = actions.get("landing_page_view", 0)
            spend = float(a.get("spend") or 0)
            lm = ad_meta.get(ad_id, {})
            display_name = (a.get("ad_name") or "").replace("DuberyMNL - ", "").replace("2026-05-04_", "").replace("2026-04-22_", "")
            out["ads"].append({
                "ad_id": ad_id,
                "name": display_name,
                "adset_name": (a.get("adset_name") or "").replace("Traffic - ", "").replace(" - May2026", ""),
                "status": lm.get("effective_status") or lm.get("status") or "UNKNOWN",
                "thumbnail_url": lm.get("thumbnail_url"),
                "spend": round(spend, 2),
                "impressions": int(a.get("impressions") or 0),
                "ctr": float(a.get("ctr") or 0),
                "lpv": lpv,
                "cost_per_lpv": round(costs.get("landing_page_view", 0), 2) if lpv else None,
                "messages": actions.get("onsite_conversion.total_messaging_connection", 0),
                "purchases": actions.get("omni_purchase", 0) or actions.get("purchase", 0),
            })

    # ---- Pixel events ----
    pixel_total_purchases = None
    if pixel:
        events = pixel.get("events") or {}
        pv = events.get("PageView", 0)
        vc = events.get("ViewContent", 0)
        ac = events.get("AddToCart", 0)
        pu = events.get("Purchase", 0)
        out["pixel"] = {
            "pixel_id": (pixel.get("meta") or {}).get("pixel_id"),
            "days": (pixel.get("meta") or {}).get("days", 7),
            "events": [
                {"name": "PageView", "count": pv, "pct": 100.0},
                {"name": "ViewContent", "count": vc,
                 "pct": round(vc / pv * 100, 2) if pv else 0},
                {"name": "AddToCart", "count": ac,
                 "pct": round(ac / pv * 100, 2) if pv else 0},
                {"name": "Purchase", "count": pu,
                 "pct": round(pu / pv * 100, 2) if pv else 0},
            ],
        }
        pixel_total_purchases = pu

    # ---- Pixel <-> sheet purchase gap ----
    if pixel_total_purchases is not None:
        sheet_orders_7d = None
        try:
            from chatbot.crm_sync import ORDERS_SHEET_ID
            from datetime import datetime as _dt3, timedelta as _td3
            rows = _sheets_values(ORDERS_SHEET_ID, "A:L")[1:]
            cutoff = _dt3.now(_PHT) - _td3(days=7)
            count = 0
            for row in rows:
                if not row:
                    continue
                row_dt = _v3_row_datetime(row[0])
                if not row_dt:
                    continue
                cancelled = (len(row) >= 11 and (row[10] or "").strip().upper() == "CANCELED")
                if row_dt >= cutoff and not cancelled:
                    count += 1
            sheet_orders_7d = count
        except Exception:
            pass
        if sheet_orders_7d is not None:
            out["gap"] = {
                "sheet_orders": sheet_orders_7d,
                "pixel_purchases": pixel_total_purchases,
                "unattributed": max(0, sheet_orders_7d - pixel_total_purchases),
            }

    # ---- Daily trend (last 14 days from ad_insights_daily.json) ----
    if daily:
        series_days: list[dict] = []
        for c in (daily.get("campaign") or []):
            d = c.get("date_start")
            if not d:
                continue
            actions = _mkt_extract_actions(c.get("actions"))
            series_days.append({
                "date": d,
                "spend": round(float(c.get("spend") or 0), 2),
                "lpv": actions.get("landing_page_view", 0),
                "ctr": float(c.get("ctr") or 0),
                "clicks": int(c.get("clicks") or 0),
            })
        series_days.sort(key=lambda x: x["date"])
        if series_days:
            out["daily"] = series_days

    # ---- Needs attention (derived from ads list) ----
    attention: list[dict] = []
    active_ads = [a for a in out["ads"] if a["status"] == "ACTIVE" and a["spend"] > 0]
    if active_ads:
        # Pause candidate: high spend, low CTR
        ranked_bad = sorted(active_ads, key=lambda x: (x["ctr"], -x["spend"]))
        if ranked_bad and ranked_bad[0]["ctr"] < 1.0 and ranked_bad[0]["spend"] > 20:
            a = ranked_bad[0]
            attention.append({
                "kind": "pause",
                "label": "Pause candidate",
                "ad_name": a["name"],
                "detail": f"CTR {a['ctr']:.2f}% · Cost/LPV ₱{a['cost_per_lpv'] or 0:.2f} · spent ₱{a['spend']:.0f}",
                "value": "High spend, low click",
                "tone": "bad",
            })
        # Top spender (best Cost/LPV among spenders with >=3 LPV)
        money = [a for a in active_ads if a["lpv"] >= 3 and a["cost_per_lpv"]]
        if money:
            top = sorted(money, key=lambda x: x["cost_per_lpv"])[0]
            attention.append({
                "kind": "top",
                "label": "Top spender",
                "ad_name": top["name"],
                "detail": f"₱{top['spend']:.0f} spent · Cost/LPV ₱{top['cost_per_lpv']:.2f} · {top['lpv']} LPV",
                "value": "Best Cost/LPV",
                "tone": "ok",
            })
        # Watching: middle of pack, below avg CTR
        if len(active_ads) >= 3:
            avg_ctr = sum(a["ctr"] for a in active_ads) / len(active_ads)
            watching = [a for a in active_ads if 0 < a["ctr"] < avg_ctr and a["lpv"] >= 3]
            watching.sort(key=lambda x: x["spend"], reverse=True)
            if watching:
                w = watching[0]
                attention.append({
                    "kind": "watch",
                    "label": "Watching",
                    "ad_name": w["name"],
                    "detail": f"{w['lpv']} LPV · CTR {w['ctr']:.2f}% (avg {avg_ctr:.2f}%)",
                    "value": "Below-avg CTR",
                    "tone": "warn",
                })
    if out["gap"] and out["gap"]["unattributed"] > 0:
        attention.append({
            "kind": "gap",
            "label": "Pixel gap",
            "ad_name": None,
            "detail": f"{out['gap']['unattributed']} of {out['gap']['sheet_orders']} sheet orders unattributed",
            "value": "Post-2026-05-25 fix · watch",
            "tone": "warn",
        })
    out["needs_attention"] = attention

    return jsonify(out)


@app.route("/api/marketing/refresh", methods=["POST"])
def marketing_refresh():
    """Manual repull: insights (7d) + insights daily (14d) + live meta + pixel.

    Runs four subprocess calls sequentially (each < 5s). Returns per-step
    status so the UI can surface partial failures. Does NOT touch Meta API
    from this Flask process directly -- all calls go through the standalone
    Python tools so they remain runnable from CLI too.
    """
    import subprocess as sp

    PY = sys.executable
    ROOT = str(PROJECT_ROOT)
    TOOLS = PROJECT_ROOT / "tools" / "meta_ads"

    steps = [
        ("insights_7d", [PY, str(TOOLS / "pull_insights.py"), "--quiet", "--days", "7"]),
        ("insights_daily_14d", [PY, str(TOOLS / "pull_insights.py"),
                                "--quiet", "--days", "14", "--daily",
                                "--output", str(PROJECT_ROOT / ".tmp" / "ad_insights_daily.json")]),
        ("live_meta", [PY, str(TOOLS / "pull_live_meta.py"), "--quiet"]),
        ("pixel_stats", [PY, str(TOOLS / "pull_pixel_stats.py"), "--quiet", "--days", "7"]),
    ]

    results: dict[str, dict] = {}
    overall_ok = True
    for name, cmd in steps:
        try:
            r = sp.run(cmd, capture_output=True, text=True, timeout=30, cwd=ROOT)
            ok = (r.returncode == 0)
            if not ok:
                overall_ok = False
            results[name] = {
                "ok": ok,
                "exit": r.returncode,
                "stderr": (r.stderr or "").strip()[:300] if not ok else "",
            }
        except sp.TimeoutExpired:
            overall_ok = False
            results[name] = {"ok": False, "exit": -1, "stderr": "timeout (>30s)"}
        except Exception as e:
            overall_ok = False
            results[name] = {"ok": False, "exit": -1, "stderr": str(e)[:300]}

    return jsonify({"ok": overall_ok, "steps": results})


@app.route("/api/home/summary", methods=["GET"])
def home_summary():
    """Daily-briefing aggregation for the Home tab.

    One endpoint, many sources. Reuses sheet-cache + cached JSON files so a
    Home refresh doesn't hammer external APIs. Each section is best-effort --
    a missing data source returns null rather than failing the whole payload.
    """
    import requests as _req
    import json as _json
    from datetime import datetime as _dt2, timedelta as _td2

    out: dict = {}
    now_pht = _dt2.now(_PHT)

    # ---- Orders / revenue (Manila-time windows) ----
    revenue_today = revenue_7d = revenue_14d = None
    orders_today_count = 0
    recent_orders: list[dict] = []
    try:
        from chatbot.crm_sync import ORDERS_SHEET_ID
        rows = _sheets_values(ORDERS_SHEET_ID, "A:L")[1:]
        cutoff_today = now_pht.replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_7d = now_pht - _td2(days=7)
        cutoff_14d = now_pht - _td2(days=14)
        revenue_today = revenue_7d = revenue_14d = 0.0
        for row in rows:
            if not row:
                continue
            row_dt = _v3_row_datetime(row[0])
            if not row_dt:
                continue
            cancelled = (len(row) >= 11 and (row[10] or "").strip().upper() == "CANCELED")
            total = _parse_v3_total(row[7]) if len(row) >= 8 else 0.0
            if row_dt >= cutoff_today:
                orders_today_count += 1
                if not cancelled:
                    revenue_today += total
            if row_dt >= cutoff_7d and not cancelled:
                revenue_7d += total
            if row_dt >= cutoff_14d and not cancelled:
                revenue_14d += total
        # newest-first list, top 5 for recent activity
        scored = []
        for row in rows:
            row_dt = _v3_row_datetime(row[0]) if row else None
            if not row_dt:
                continue
            scored.append((row_dt, row))
        scored.sort(key=lambda x: x[0], reverse=True)
        for _dt_obj, row in scored[:5]:
            padded = row + [""] * (12 - len(row))
            ts, name, _phone, _addr, items, _qty, _dfee, total, _notes, _ad, status, _courier = padded[:12]
            recent_orders.append({
                "name": name or "Unknown",
                "items": (items or "").replace("\n", " · "),
                "total": _parse_v3_total(total),
                "status": (status or "Pending").strip() or "Pending",
                "date": _v3_row_date(ts),
            })
    except Exception as e:
        out["_orders_error"] = str(e)

    # ---- Recent leads (top 5) ----
    # Leads sheet schema: lead_id, name, phone, address, landmarks, source,
    # first_contact, last_contact, model_interest, status, notes
    recent_leads: list[dict] = []
    try:
        from chatbot.crm_sync import SHEET_ID as LEADS_SHEET_ID
        lrows = _sheets_values(LEADS_SHEET_ID, "'Leads'!A:K")[1:]
        for row in reversed(lrows[-10:]):
            padded = row + [""] * (11 - len(row))
            _lid, name, _phone, _addr, _lm, source, _first, last, model, status, _notes = padded[:11]
            recent_leads.append({
                "name": name or "Unknown",
                "status": (status or "Cold").strip() or "Cold",
                "model_interest": model or "",
                "source": source or "",
                "last_contact": (last or "")[:10],
            })
            if len(recent_leads) >= 5:
                break
    except Exception as e:
        out["_leads_error"] = str(e)

    # ---- Ads insights (from cached pull) ----
    ads_spend_total = ads_spend_today = None
    top_ad = None
    try:
        ads_path = PROJECT_ROOT / ".tmp" / "ad_insights.json"
        if ads_path.exists():
            ads = _json.loads(ads_path.read_text(encoding="utf-8"))
            campaigns = ads.get("campaign") or []
            if campaigns:
                spend_total = sum(float(c.get("spend") or 0) for c in campaigns)
                ads_spend_total = spend_total
                meta = ads.get("meta") or {}
                days = 0
                try:
                    df = _dt2.fromisoformat(meta.get("date_from", ""))
                    dt = _dt2.fromisoformat(meta.get("date_to", ""))
                    days = max(1, (dt - df).days + 1)
                except Exception:
                    days = 14
                ads_spend_today = spend_total / days  # rough average per day
            # Top ad by ratio of LPV to spend (cheapest LPV) among ads with >=3 LPV
            ads_list = ads.get("ads") or []
            ranked = []
            for ad in ads_list:
                actions = {a["action_type"]: float(a["value"]) for a in (ad.get("actions") or [])}
                lpv = actions.get("landing_page_view", 0)
                spend = float(ad.get("spend") or 0)
                if lpv >= 3 and spend > 0:
                    ranked.append((spend / lpv, ad, lpv, spend, actions))
            ranked.sort(key=lambda x: x[0])
            if ranked:
                cost_per_lpv, ad, lpv, spend, actions = ranked[0]
                top_ad = {
                    "name": (ad.get("ad_name") or "").replace("DuberyMNL - ", ""),
                    "ad_id": ad.get("ad_id"),
                    "spend": round(spend, 2),
                    "lpv": int(lpv),
                    "cost_per_lpv": round(cost_per_lpv, 2),
                    "ctr": ad.get("ctr"),
                    "messages": int(actions.get("onsite_conversion.total_messaging_connection", 0)),
                    "purchases": int(actions.get("omni_purchase", 0) or actions.get("purchase", 0)),
                }
    except Exception as e:
        out["_ads_error"] = str(e)

    # ROAS: revenue_14d / spend_total (cached ads window assumed 14d)
    roas_14d = None
    try:
        if ads_spend_total and revenue_14d is not None and ads_spend_total > 0:
            roas_14d = revenue_14d / ads_spend_total
    except Exception:
        pass

    # ---- Clarity (from cached pull) ----
    clarity = {"sessions": None, "users": None, "quickback_pct": None,
               "deadclick_pct": None, "active_seconds": None}
    try:
        cpath = PROJECT_ROOT / ".tmp" / "clarity_metrics.json"
        if cpath.exists():
            cdat = _json.loads(cpath.read_text(encoding="utf-8"))
            totals_rows = (cdat.get("calls") or {}).get("totals") or []
            for row in totals_rows:
                name = row.get("metricName")
                info = (row.get("information") or [{}])[0]
                if name == "Traffic":
                    clarity["sessions"] = int(info.get("totalSessionCount", 0) or 0) or None
                    clarity["users"] = int(info.get("distinctUserCount", 0) or 0) or None
                elif name == "QuickbackClick":
                    clarity["quickback_pct"] = info.get("sessionsWithMetricPercentage")
                elif name == "DeadClickCount":
                    clarity["deadclick_pct"] = info.get("sessionsWithMetricPercentage")
                elif name == "EngagementTime":
                    clarity["active_seconds"] = int(info.get("activeTime", 0) or 0) or None
    except Exception as e:
        out["_clarity_error"] = str(e)

    # ---- Active chatbot conversations ----
    active_convos = None
    try:
        r = _req.get("http://localhost:8080/status", timeout=2)
        if r.ok:
            data = r.json()
            for k in ("active_conversations", "conversations_active", "active_sessions"):
                if k in data:
                    active_convos = int(data[k])
                    break
    except Exception:
        pass

    # ---- Pending content approvals (pipeline.json) ----
    pending_approvals = None
    try:
        pipeline_path = PROJECT_ROOT / ".tmp" / "pipeline.json"
        if pipeline_path.exists():
            items = _json.loads(pipeline_path.read_text(encoding="utf-8"))
            pending_approvals = sum(
                1 for c in items
                if c.get("status") in ("PENDING", "PROMPT_READY", "DONE")
            )
    except Exception:
        pass

    # ---- Scheduled posts in next 24h ----
    scheduled_24h = None
    try:
        feed_queue_path = PROJECT_ROOT / "tools" / "facebook" / "feed_queue.json"
        if feed_queue_path.exists():
            q = _json.loads(feed_queue_path.read_text(encoding="utf-8"))
            items = q.get("items") if isinstance(q, dict) else q
            cutoff = now_pht + _td2(hours=24)
            count = 0
            for item in (items or []):
                if (item.get("status") or "").lower() not in ("queued", "scheduled", "pending"):
                    continue
                sched = item.get("scheduled_at") or item.get("publish_at")
                if not sched:
                    continue
                try:
                    sched_dt = _dt2.fromisoformat(sched.replace("Z", "+00:00"))
                    if sched_dt.tzinfo is None:
                        sched_dt = sched_dt.replace(tzinfo=_PHT)
                    if now_pht <= sched_dt <= cutoff:
                        count += 1
                except Exception:
                    continue
            scheduled_24h = count
    except Exception:
        pass

    # ---- System health (cheap monitors) ----
    health = "green"
    health_msg = "all good"
    try:
        cheap = [(n, fn) for (n, fn, exp) in SERVICES if not exp]
        def _safe(fn):
            try: return fn().state
            except Exception: return "offline"
        with ThreadPoolExecutor(max_workers=len(cheap) or 1) as pool:
            states = list(pool.map(_safe, (fn for _n, fn in cheap)))
        offline_n = sum(1 for s in states if s == "offline")
        degraded_n = sum(1 for s in states if s == "degraded")
        if offline_n:
            health = "red"
            health_msg = f"{offline_n} service(s) offline"
        elif degraded_n:
            health = "yellow"
            health_msg = f"{degraded_n} degraded"
        else:
            health = "green"
            health_msg = f"{len(states)} services up"
    except Exception:
        health = "yellow"
        health_msg = "health check failed"

    out.update({
        "now": now_pht.isoformat(),
        "revenue_today": revenue_today,
        "revenue_7d": revenue_7d,
        "revenue_14d": revenue_14d,
        "orders_today": orders_today_count,
        "ads_spend_today": ads_spend_today,
        "ads_spend_total": ads_spend_total,
        "roas_14d": roas_14d,
        "top_ad": top_ad,
        "clarity": clarity,
        "active_convos": active_convos,
        "pending_approvals": pending_approvals,
        "scheduled_24h": scheduled_24h,
        "recent_orders": recent_orders,
        "recent_leads": recent_leads,
        "system_health": health,
        "system_health_msg": health_msg,
    })
    return jsonify(out)


@app.route("/api/monitor/status", methods=["GET"])
def monitor_status():
    """Return current state of all registered services.

    Query params:
        include_expensive=1 -- also run monitors flagged EXPENSIVE
            (meta_ads, story_rotation). Otherwise those are skipped and
            returned with state="degraded", message="skipped (expensive)".
    """
    include_exp = request.args.get("include_expensive") == "1"
    ordered_names = service_names_in_order()
    by_name = {n: (fn, exp) for (n, fn, exp) in SERVICES}

    def run_one(name: str) -> ServiceStatus:
        fn, exp = by_name[name]
        if exp and not include_exp:
            return ServiceStatus.now(
                name=name, state="degraded", message="skipped (expensive)"
            )
        try:
            return fn()
        except Exception as e:
            return ServiceStatus.now(
                name=name,
                state="offline",
                message=f"monitor crashed: {type(e).__name__}: {e}",
            )

    results: list[ServiceStatus] = [None] * len(ordered_names)
    with ThreadPoolExecutor(max_workers=9) as pool:
        futures = {pool.submit(run_one, n): i for i, n in enumerate(ordered_names)}
        for fut in as_completed(futures, timeout=12):
            i = futures[fut]
            results[i] = fut.result()

    out = []
    for r in results:
        if r is None:
            continue
        d = r.to_dict()
        if r.name in FIX_COMMANDS and r.state in ("offline", "degraded"):
            d["has_fix"] = True
            d["fix_label"] = FIX_COMMANDS[r.name]["label"]
        out.append(d)
    return jsonify(out)


@app.route("/api/monitor/logs/<service>", methods=["GET"])
def monitor_logs(service: str):
    """Return the last 50 lines from a service's log_source, if available."""
    by_name = {n: fn for (n, fn, _exp) in SERVICES}
    if service not in by_name:
        return jsonify({"error": "unknown service"}), 404

    try:
        status = by_name[service]()
    except Exception as e:
        return jsonify({"error": f"monitor crashed: {e}"}), 500

    log_source = status.log_source
    if not log_source:
        return jsonify({
            "lines": [f"[no log_source configured for {service}]", status.message or ""],
            "source": None,
        })

    p = Path(log_source)
    if not p.exists():
        return jsonify({
            "lines": [f"[log file not found: {log_source}]"],
            "source": log_source,
        })

    try:
        with p.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        tail = [ln.rstrip() for ln in lines[-50:]]
        return jsonify({"lines": tail, "source": log_source})
    except Exception as e:
        return jsonify({"error": f"read failed: {e}"}), 500


@app.route("/api/monitor/fix/<service>", methods=["POST"])
def monitor_fix(service: str):
    """Attempt to fix a service by running its fix command."""
    if service not in FIX_COMMANDS:
        return jsonify({"ok": False, "error": "no fix available"}), 404

    fix = FIX_COMMANDS[service]
    try:
        if fix.get("bg"):
            import subprocess as sp
            sp.Popen(
                fix["cmd"],
                stdout=sp.DEVNULL,
                stderr=sp.DEVNULL,
                creationflags=sp.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            return jsonify({"ok": True, "message": f"{fix['label']} started in background"})
        else:
            import subprocess as sp
            result = sp.run(fix["cmd"], capture_output=True, text=True, timeout=15)
            return jsonify({
                "ok": result.returncode == 0,
                "message": result.stdout[:500] if result.returncode == 0 else result.stderr[:500],
            })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/agent/status", methods=["GET"])
def agent_status():
    """Lightweight agent health for the nav-item dot.

    Returns state: alive | warming | stale | dead. Based on cached
    `last_ok_ts` / `last_error` from AgentSession -- no live ping,
    so this is cheap to poll.
    """
    return jsonify(AgentSession.get().status())


@app.route("/api/agent/reset", methods=["POST"])
def agent_reset():
    """Reset the AgentSession so the next chat starts a fresh Claude context."""
    session = AgentSession.get()
    session.session_id = None
    session.last_ok_ts = None
    session.last_error = None
    return jsonify({"ok": True})


@app.route("/api/agent/chat", methods=["POST"])
def agent_chat():
    """Stream Claude replies to the caller via Server-Sent Events.

    Request JSON: {"prompt": str}
    Response: SSE stream of `data: {"text": "..."}\n\n` events, terminated
    with `data: {"done": true}\n\n`.
    """
    payload = request.get_json(silent=True) or {}
    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "prompt required"}), 400

    session = AgentSession.get()

    def sse_event(obj: dict) -> str:
        return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

    def generator():
        """Bridge async `session.ask` to a sync generator for Flask.

        Flask's streaming response needs a sync iterator, but the SDK is
        async. We run the coroutine on a dedicated thread's event loop and
        hand chunks across a thread-safe queue.
        """
        import queue as queue_mod

        q: "queue_mod.Queue[tuple[str, str]]" = queue_mod.Queue()
        SENTINEL = ("__done__", "")

        def runner() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def drain() -> None:
                try:
                    async for chunk in session.ask(prompt):
                        q.put(("text", chunk))
                except Exception as e:
                    q.put(("error", f"{type(e).__name__}: {e}"))
                finally:
                    q.put(SENTINEL)

            try:
                loop.run_until_complete(drain())
            finally:
                loop.close()

        threading.Thread(target=runner, daemon=True).start()

        while True:
            try:
                kind, value = q.get(timeout=15)
            except queue_mod.Empty:
                yield ": keepalive\n\n"
                continue
            if (kind, value) == SENTINEL:
                yield sse_event({"done": True})
                break
            if kind == "text":
                yield sse_event({"text": value})
            elif kind == "error":
                yield sse_event({"error": value})
                yield sse_event({"done": True})
                break

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }
    return Response(generator(), mimetype="text/event-stream", headers=headers)


@app.route("/api/video-bank")
def video_bank():
    """Scan contents/new/ for mp4 files, return metadata sorted newest-first."""
    items = []
    root = PROJECT_ROOT / "contents" / "new"
    if root.exists():
        for p in root.rglob("*.mp4"):
            rel = p.relative_to(PROJECT_ROOT)
            sidecar = p.with_suffix(".prompt.json")
            prompt_data = {}
            if sidecar.exists():
                try:
                    prompt_data = json.loads(sidecar.read_text(encoding="utf-8"))
                except Exception:
                    pass
            items.append({
                "url": "/api/images/" + "/".join(rel.parts),
                "filename": p.name,
                "size_kb": p.stat().st_size // 1024,
                "mtime": p.stat().st_mtime,
                "prompt": prompt_data.get("prompt", ""),
                "model": prompt_data.get("model", ""),
                "aspect_ratio": prompt_data.get("aspect_ratio", ""),
            })
    items.sort(key=lambda x: x["mtime"], reverse=True)
    for item in items:
        del item["mtime"]
    return jsonify(items)


@app.route("/api/image-bank")
def image_bank():
    """Scan contents/ready/ and contents/new/, return image metadata sorted newest-first."""
    IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
    items = []

    def collect(root, img_type_override=None):
        for p in root.rglob("*"):
            if p.suffix.lower() not in IMAGE_EXTS:
                continue
            rel = p.relative_to(PROJECT_ROOT)
            parts = rel.parts
            if img_type_override:
                img_type, model = img_type_override, None
            else:
                img_type = parts[2] if len(parts) > 2 else "other"
                if img_type == "brand":
                    model = None
                elif len(parts) == 5:
                    model = parts[3]
                else:
                    model = None
            items.append({
                "url": "/api/images/" + "/".join(rel.parts),
                "filename": p.name,
                "type": img_type,
                "model": model,
                "mtime": p.stat().st_mtime,
            })

    collect(PROJECT_ROOT / "contents" / "ready")
    collect(PROJECT_ROOT / "contents" / "new", img_type_override="new")
    # contents/runs/{timestamp}_bespoke/ -- bespoke-pipeline outputs that the
    # bank used to miss entirely. Treat them as type=new so RA's existing
    # filters surface them without adding a new chip.
    runs_root = PROJECT_ROOT / "contents" / "runs"
    if runs_root.exists():
        collect(runs_root, img_type_override="new")

    items.sort(key=lambda x: x["mtime"], reverse=True)
    for item in items:
        del item["mtime"]

    return jsonify(items)


# --- Sheets read helpers (bearer-token + TTL cache) ------------------------
# googleapiclient's httplib2 transport intermittently flakes on SSL handshakes
# from RA's home network (see memory `reference_googleapi_httplib2_fallback`).
# Hitting the REST endpoint with `requests` is faster + dodges the bug. The
# TTL cache layered on top makes repeat dashboard loads near-instant since
# CRM data is barely volatile (~1 write per closed sale).

import requests as _requests
from urllib.parse import quote as _urlquote

_SHEETS_CACHE: dict[tuple[str, str], tuple[float, list]] = {}
_SHEETS_CACHE_TTL = 30  # seconds


def _sheets_values(sheet_id: str, range_name: str, ttl: int = _SHEETS_CACHE_TTL, bypass_cache: bool = False) -> list:
    """Return rows from a Sheets range, cached for `ttl` seconds.

    Reads via direct REST (`requests` + bearer token) to skip googleapiclient's
    httplib2 SSL stack. Returns [] on auth failure or HTTP error.
    `bypass_cache=True` forces a fresh read and replaces the cache entry.
    """
    now = time.time()
    key = (sheet_id, range_name)
    cached = _SHEETS_CACHE.get(key)
    if cached and cached[0] > now and not bypass_cache:
        return cached[1]
    try:
        from chatbot.crm_sync import _get_creds
    except ImportError:
        return []
    creds = _get_creds()
    if not creds:
        return []
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request as _Req
        try:
            creds.refresh(_Req())
        except Exception as e:
            print(f"_sheets_values refresh failed: {e}", file=sys.stderr, flush=True)
            return cached[1] if cached else []
    encoded_range = _urlquote(range_name, safe="")
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
        f"/values/{encoded_range}"
    )
    try:
        r = _requests.get(
            url,
            headers={"Authorization": f"Bearer {creds.token}"},
            timeout=10,
        )
        r.raise_for_status()
        values = r.json().get("values", [])
    except Exception as e:
        print(f"_sheets_values {range_name} failed: {e}", file=sys.stderr, flush=True)
        return cached[1] if cached else []
    _SHEETS_CACHE[key] = (now + ttl, values)
    return values


def _invalidate_sheets_cache() -> None:
    """Clear the sheets read cache. Call after writes so the next read is fresh."""
    _SHEETS_CACHE.clear()


def _parse_v3_total(cell: str) -> float:
    """Parse 'Total Amount' cell -- strip peso prefix + commas, return 0 on junk."""
    if not cell:
        return 0.0
    cleaned = str(cell).replace("₱", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


def _v3_row_date(timestamp_cell: str) -> str:
    """Convert v3 M/D/YYYY ... timestamp to ISO YYYY-MM-DD; '' on parse fail."""
    if not timestamp_cell:
        return ""
    head = str(timestamp_cell).split(" ", 1)[0]
    try:
        from datetime import datetime as _dt
        return _dt.strptime(head, "%m/%d/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def _v3_row_datetime(timestamp_cell: str):
    """Parse v3 timestamp 'M/D/YYYY H:MM:SS' as Manila local time. Returns
    a tz-aware datetime in PHT, or None on parse failure. Used for rolling
    time windows (e.g. last 24h) rather than calendar-day comparison."""
    if not timestamp_cell:
        return None
    s = str(timestamp_cell).strip()
    from datetime import datetime as _dt
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M"):
        try:
            return _dt.strptime(s, fmt).replace(tzinfo=_PHT)
        except ValueError:
            continue
    return None


@app.route("/api/crm/summary", methods=["GET"])
def crm_summary():
    """Aggregate CRM stats: lead counts by status, order totals.

    Leads come from the CRM sheet (Leads tab). Orders come from the
    DuberyMNL Orders sheet -- canonical sales history that includes both
    v3 PDP form submissions and chatbot /mark-sale entries.
    """
    try:
        from chatbot.crm_sync import SHEET_ID, ORDERS_SHEET_ID
    except ImportError as e:
        return jsonify({"error": f"import failed: {e}"}), 500

    bypass = request.args.get("fresh") == "1"
    try:
        lead_rows = _sheets_values(SHEET_ID, "'Leads'!A:K", bypass_cache=bypass)[1:]

        status_counts = {"Cold": 0, "Warm": 0, "Hot": 0, "Converted": 0}
        for row in lead_rows:
            if len(row) >= 10:
                s = row[9].strip() or "Cold"
                status_counts[s] = status_counts.get(s, 0) + 1

        # v3 Orders schema (cols A-L): Timestamp | Name | Phone | Address |
        # Items | Qty | Delivery Fee | Total Amount | Notes | Ad ID |
        # (K: manual status) | (L: courier timestamp)
        order_rows = _sheets_values(ORDERS_SHEET_ID, "A:L", bypass_cache=bypass)[1:]

        # Revenue excludes cancelled rows (col K = CANCELED). Pending +
        # DELIVERED both count -- pending sales are still booked revenue
        # we expect to collect; cancelled is money we'll never see.
        def _is_cancelled(row):
            if len(row) < 11:
                return False
            return (row[10] or "").strip().upper() == "CANCELED"

        total_revenue = sum(
            _parse_v3_total(row[7]) for row in order_rows
            if len(row) >= 8 and not _is_cancelled(row)
        )

        # Rolling 24-hour window (Manila time) -- captures late-night orders
        # from "yesterday" that wouldn't show under a calendar-day check.
        from datetime import datetime as _dt2, timedelta as _td2
        now_pht = _dt2.now(_PHT)
        cutoff_24h = now_pht - _td2(hours=24)
        cutoff_30d = now_pht - _td2(days=30)
        orders_today = 0
        units_sold_30d = 0  # individual sunglasses (Qty column summed), excl. cancelled
        for row in order_rows:
            if not row:
                continue
            row_dt = _v3_row_datetime(row[0])
            if not row_dt:
                continue
            if row_dt >= cutoff_24h:
                orders_today += 1
            if row_dt >= cutoff_30d and not _is_cancelled(row) and len(row) >= 6:
                # Qty cell is newline-joined per-item counts ("1\n1\n2" etc).
                for line in str(row[5] or "").split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        units_sold_30d += int(line)
                    except ValueError:
                        continue

        return jsonify({
            "total_leads": len(lead_rows),
            "status_counts": status_counts,
            "total_orders": len(order_rows),
            "orders_today": orders_today,
            "total_revenue": total_revenue,
            "units_sold_30d": units_sold_30d,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/crm/leads", methods=["GET"])
def crm_leads():
    """Return leads from the CRM sheet, newest first (up to 100)."""
    try:
        from chatbot.crm_sync import SHEET_ID
    except ImportError as e:
        return jsonify({"error": f"import failed: {e}"}), 500

    bypass = request.args.get("fresh") == "1"
    try:
        rows = _sheets_values(SHEET_ID, "'Leads'!A:K", bypass_cache=bypass)[1:]
        keys = ["lead_id", "name", "phone", "address", "landmarks", "source",
                "first_contact", "last_contact", "model_interest", "status", "notes"]
        leads = []
        for row in reversed(rows):
            padded = row + [""] * (11 - len(row))
            leads.append(dict(zip(keys, padded[:11])))
        return jsonify(leads[:100])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/crm/orders", methods=["GET"])
def crm_orders():
    """Return orders from the DuberyMNL Orders sheet, newest first (up to 100).

    Maps v3 schema -> CC frontend keys. Payment method is extracted from the
    Notes cell when chatbot /mark-sale wrote a 'Payment: X' line; v3 PDP form
    rows don't capture payment explicitly so they show '-'.
    """
    try:
        from chatbot.crm_sync import ORDERS_SHEET_ID
    except ImportError as e:
        return jsonify({"error": f"import failed: {e}"}), 500

    bypass = request.args.get("fresh") == "1"
    try:
        rows = _sheets_values(ORDERS_SHEET_ID, "A:L", bypass_cache=bypass)[1:]
        orders = []
        for row in reversed(rows):
            padded = row + [""] * (12 - len(row))
            ts, name, phone, address, items, qty, dfee, total, notes, ad_id, status_k, courier_l = padded[:12]
            payment = "—"
            for line in (notes or "").splitlines():
                if line.lower().startswith("payment:"):
                    payment = line.split(":", 1)[1].strip()
                    break
            order_id = f"V3-{ts}" if ad_id != "chatbot_mark_sale" else f"MS-{ts}"
            orders.append({
                "order_id": order_id,
                "lead_id": phone or name,
                "items": items,
                "quantity": qty,
                "total": _parse_v3_total(total),
                "discount_code": "",
                "payment_method": payment,
                "delivery_preference": "",
                "delivery_time": "",
                "order_date": _v3_row_date(ts),
                "status": (status_k or "Pending").strip() or "Pending",
                "source": ad_id or "—",
                "name": name,
                "phone": phone,
                "address": address,
                "delivery_fee": dfee,
                "notes": notes,
            })
        return jsonify(orders[:100])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/inventory/summary", methods=["GET"])
def inventory_summary():
    """Return per-SKU inventory merged with reorder targets:
    {sku: {sold_history, pending, on_hand, target_stock, to_order}}.
    """
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "tools" / "orders"))
        from inventory_report import compute_report  # noqa: E402

        report = compute_report()
        unmatched = report.pop("_unmatched", [])

        # Merge target_stock from reorder.json
        reorder_path = PROJECT_ROOT / "orders" / "reorder.json"
        targets = {}
        if reorder_path.exists():
            import json as _json
            reorder = _json.loads(reorder_path.read_text(encoding="utf-8"))
            targets = {sku: meta.get("target_stock", 0) for sku, meta in reorder.get("skus", {}).items()}

        merged = {}
        for sku, data in report.items():
            target = targets.get(sku, 0)
            merged[sku] = {
                "sold_history": data["sold_history"],
                "pending": data["pending"],
                "on_hand": data["on_hand"],
                "target_stock": target,
                "to_order": max(0, target - data["on_hand"]),
            }
        if unmatched:
            merged["_unmatched"] = unmatched
        return jsonify(merged)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/page", methods=["GET"])
def page_analytics():
    """Pull page analytics from Meta Graph API.

    Combines two calls:
    - /me fields for real-time counts (fan_count, talking_about_count)
    - /insights for time-series metrics that have data
    """
    import requests as _req
    import time as _time

    token = os.environ.get("META_PAGE_ACCESS_TOKEN")
    page_id = os.environ.get("META_PAGE_ID", "111349974035733")
    if not token:
        return jsonify({"error": "META_PAGE_ACCESS_TOKEN not set"}), 503

    base = "https://graph.facebook.com/v21.0"
    out = {}

    # 1. Page summary -- always has data
    try:
        r = _req.get(
            f"{base}/me",
            params={"fields": "fan_count,followers_count,talking_about_count",
                    "access_token": token},
            timeout=8,
        )
        s = r.json()
        if "error" not in s:
            out["fans"] = {"total": s.get("fan_count", 0)}
            out["talking_about"] = {"total": s.get("talking_about_count", 0)}
    except Exception:
        pass

    # 2. Time-series insights (period=week; only metrics confirmed working for this page)
    metrics = [
        "page_impressions_unique",
        "page_post_engagements",
        "page_views_total",
    ]
    now = int(_time.time())
    try:
        # Build URL manually: requests encodes commas as %2C which Meta rejects
        from urllib.parse import urlencode
        qs = urlencode({
            "metric": ",".join(metrics),
            "period": "week",
            "since": now - 28 * 86400,
            "until": now,
            "access_token": token,
        }, safe=",")
        r = _req.get(f"{base}/{page_id}/insights?{qs}", timeout=10)
        data = r.json()
        if "error" not in data:
            for item in data.get("data", []):
                name = item.get("name")
                values = item.get("values", [])
                total = sum(v.get("value", 0) for v in values)
                daily = [{"date": v.get("end_time", "")[:10], "value": v.get("value", 0)}
                         for v in values]
                out[name] = {"total": total, "daily": daily}
    except Exception:
        pass

    return jsonify(out)


# ============= SCHEDULE TAB ROUTES =============

from datetime import datetime as _dt, timedelta as _td, timezone as _tz, date as _date
_PHT = _tz(_td(hours=8))

LAYOUT_IMAGE_COUNT = {"2h": 2, "2v": 2, "1p2": 3, "2x2": 4, "3h": 3, "hero3": 4, "ba": 2}


def _sched_load_queue():
    from tools.facebook.queue_helpers import load_queue
    return load_queue()


def _sched_save_item(item):
    from tools.facebook.queue_helpers import add_item
    return add_item(item)


def _sched_update_item(item_id, fields):
    from tools.facebook.queue_helpers import update_item
    return update_item(item_id, fields)


def _sched_parse_iso(text):
    dt = _dt.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_PHT)
    return dt


@app.route("/api/schedule/queue")
def sched_queue():
    items = _sched_load_queue()
    upcoming = [it for it in items if it.get("status") == "APPROVED"]
    upcoming.sort(key=lambda x: x.get("scheduled_for", ""))
    posted = [it for it in items if it.get("status") == "POSTED"]
    posted.sort(key=lambda x: x.get("posted_at") or "", reverse=True)
    failed = [it for it in items if it.get("status") == "FAILED"]
    failed.sort(key=lambda x: x.get("posted_at") or "", reverse=True)
    cancelled = [it for it in items if it.get("status") == "CANCELLED"]
    cancelled.sort(key=lambda x: x.get("posted_at") or x.get("added_at") or "", reverse=True)
    return jsonify({
        "upcoming": upcoming,
        "posted": posted[:20],
        "failed": failed[:20],
        "cancelled": cancelled[:20],
    })


@app.route("/api/schedule/add", methods=["POST"])
def sched_add():
    data = request.get_json(force=True, silent=True) or {}
    image_paths = data.get("image_paths") or []
    caption = (data.get("caption") or "").strip()
    scheduled_for = data.get("scheduled_for") or ""
    mode = data.get("mode") or "multi"
    layout = data.get("layout")
    source = data.get("source") or "manual"

    if not caption:
        return jsonify({"ok": False, "error": "caption is empty"}), 400
    if not isinstance(image_paths, list) or not (1 <= len(image_paths) <= 10):
        return jsonify({"ok": False, "error": "must supply 1-10 image paths"}), 400
    if mode not in ("multi", "collage"):
        return jsonify({"ok": False, "error": f"bad mode: {mode}"}), 400

    # Validate all images exist
    for p in image_paths:
        safe = _safe_project_path(p)
        if not safe or not safe.exists():
            return jsonify({"ok": False, "error": f"image not found: {p}"}), 400

    # Parse time
    try:
        sched_dt = _sched_parse_iso(scheduled_for)
    except Exception as exc:
        return jsonify({"ok": False, "error": f"bad scheduled_for: {exc}"}), 400
    if sched_dt <= _dt.now(_PHT):
        return jsonify({"ok": False, "error": "scheduled_for must be in the future PHT"}), 400

    # Layout validation
    if mode == "collage":
        if not layout or layout not in LAYOUT_IMAGE_COUNT:
            return jsonify({"ok": False, "error": "layout required for collage mode"}), 400
        expected = LAYOUT_IMAGE_COUNT[layout]
        if len(image_paths) != expected:
            return jsonify({"ok": False, "error": f"layout {layout} needs {expected} images"}), 400
    else:
        layout = None

    # ID
    stem = sched_dt.strftime("feed-%Y%m%d-%H%M")
    existing = [it.get("id", "") for it in _sched_load_queue() if it.get("id", "").startswith(stem)]
    item_id = f"{stem}-{len(existing) + 1:03d}"

    item = {
        "id": item_id,
        "image_paths": image_paths,
        "caption": caption,
        "scheduled_for": sched_dt.isoformat(),
        "mode": mode,
        "layout": layout,
        "composed_path": None,
        "status": "APPROVED",
        "fb_post_id": None,
        "added_at": _dt.now(_PHT).isoformat(),
        "posted_at": None,
        "error": None,
        "source": source,
    }
    _sched_save_item(item)
    return jsonify({"ok": True, "id": item_id})


@app.route("/api/schedule/cancel", methods=["POST"])
def sched_cancel():
    data = request.get_json(force=True, silent=True) or {}
    item_id = data.get("id", "")
    if not item_id:
        return jsonify({"ok": False, "error": "missing id"}), 400
    items = _sched_load_queue()
    target = next((it for it in items if it.get("id") == item_id), None)
    if not target:
        return jsonify({"ok": False, "error": "not found"}), 404
    if target.get("status") != "APPROVED":
        return jsonify({"ok": False, "error": f"cannot cancel from status {target.get('status')}"}), 409
    _sched_update_item(item_id, {"status": "CANCELLED", "posted_at": _dt.now(_PHT).isoformat()})
    return jsonify({"ok": True})


@app.route("/api/schedule/edit", methods=["POST"])
def sched_edit():
    """Patch caption and/or scheduled_for on an APPROVED queue item.

    Only APPROVED items can be edited (in-flight or completed posts are
    immutable). scheduled_for must be future-PHT and ISO-8601. Caption is
    free text -- no length cap server-side; client should warn on > 500 chars.
    """
    data = request.get_json(force=True, silent=True) or {}
    item_id = (data.get("id") or "").strip()
    if not item_id:
        return jsonify({"ok": False, "error": "missing id"}), 400

    items = _sched_load_queue()
    target = next((it for it in items if it.get("id") == item_id), None)
    if not target:
        return jsonify({"ok": False, "error": "not found"}), 404
    if target.get("status") != "APPROVED":
        return jsonify({"ok": False, "error": f"cannot edit from status {target.get('status')}"}), 409

    patch: dict = {}

    if "caption" in data:
        new_cap = (data.get("caption") or "")
        if not isinstance(new_cap, str):
            return jsonify({"ok": False, "error": "caption must be string"}), 400
        patch["caption"] = new_cap

    if "scheduled_for" in data:
        new_ts = (data.get("scheduled_for") or "").strip()
        if not new_ts:
            return jsonify({"ok": False, "error": "scheduled_for cannot be empty"}), 400
        try:
            dt = _dt.fromisoformat(new_ts)
        except Exception:
            return jsonify({"ok": False, "error": "scheduled_for must be ISO-8601 with timezone"}), 400
        if dt.tzinfo is None:
            return jsonify({"ok": False, "error": "scheduled_for must include timezone offset"}), 400
        if dt <= _dt.now(_PHT):
            return jsonify({"ok": False, "error": "scheduled_for must be in the future"}), 400
        patch["scheduled_for"] = new_ts

    if not patch:
        return jsonify({"ok": False, "error": "no editable fields supplied"}), 400

    _sched_update_item(item_id, patch)
    return jsonify({"ok": True, "id": item_id, "patched": list(patch.keys())})


@app.route("/api/schedule/last-run")
def sched_last_run():
    p = PROJECT_ROOT / ".tmp" / "feed_worker_last_run.json"
    if not p.exists():
        return jsonify({"last_run_at": None, "posted": 0, "failed": 0})
    try:
        return jsonify(json.loads(p.read_text(encoding="utf-8")))
    except Exception:
        return jsonify({"last_run_at": None, "posted": 0, "failed": 0})


# ---------- Image bank favorites + archive + delete ----------

_FAVORITES_PATH = PROJECT_ROOT / "contents" / "ready" / "favorites.json"
_ARCHIVE_PATH = PROJECT_ROOT / "contents" / "ready" / "archived.json"
_BANK_TRASH_DIR = PROJECT_ROOT / ".tmp" / "bank_trash"
_FAVORITES_LOCK = threading.Lock()
_ARCHIVE_LOCK = threading.Lock()


def _load_path_set(path: Path, key: str) -> set:
    if not path.exists():
        return set()
    try:
        return set(json.loads(path.read_text(encoding="utf-8")).get(key) or [])
    except Exception:
        return set()


def _save_path_set(path: Path, key: str, value: set) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({key: sorted(value)}, f, indent=2, ensure_ascii=False)


def _load_favorites() -> set:
    return _load_path_set(_FAVORITES_PATH, "favorites")


def _save_favorites(favs: set) -> None:
    _save_path_set(_FAVORITES_PATH, "favorites", favs)


def _load_archived() -> set:
    return _load_path_set(_ARCHIVE_PATH, "archived")


def _save_archived(archived: set) -> None:
    _save_path_set(_ARCHIVE_PATH, "archived", archived)


@app.route("/api/schedule/favorites", methods=["GET"])
def sched_favorites_list():
    return jsonify({"favorites": sorted(_load_favorites())})


@app.route("/api/schedule/favorites", methods=["POST"])
def sched_favorites_toggle():
    data = request.get_json(silent=True) or {}
    path = (data.get("path") or "").strip()
    action = (data.get("action") or "toggle").strip().lower()
    if not path:
        return jsonify({"ok": False, "error": "path required"}), 400
    # Validate path is project-safe (don't trust arbitrary input as favorite key)
    if not _safe_project_path(path):
        return jsonify({"ok": False, "error": "invalid path"}), 400
    with _FAVORITES_LOCK:
        favs = _load_favorites()
        if action == "add":
            favs.add(path)
            favorited = True
        elif action == "remove":
            favs.discard(path)
            favorited = False
        else:  # toggle
            if path in favs:
                favs.discard(path)
                favorited = False
            else:
                favs.add(path)
                favorited = True
        _save_favorites(favs)
    return jsonify({"ok": True, "path": path, "favorited": favorited, "count": len(favs)})


@app.route("/api/schedule/image-bank")
def sched_image_bank():
    """All images under contents/ready/ + contents/new/, enriched with manifest data.

    Query:
      ?include_archived=1   include archived images (default: hidden)
    """
    IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
    ready_dir = PROJECT_ROOT / "contents" / "ready"
    new_dir = PROJECT_ROOT / "contents" / "new"
    include_archived = request.args.get("include_archived") in {"1", "true", "yes"}

    # Manifest lookup: filename -> meta.
    manifest_path = ready_dir / "manifest.json"
    manifest: dict = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8")) or {}
        except Exception:
            manifest = {}

    favs = _load_favorites()
    archived = _load_archived()
    items = []

    def _walk(root: Path, source_tag: str):
        if not root.exists():
            return
        for p in root.rglob("*"):
            if p.suffix.lower() not in IMAGE_EXTS:
                continue
            rel = p.relative_to(PROJECT_ROOT)
            path_str = str(rel).replace("\\", "/")
            if not include_archived and path_str in archived:
                continue
            meta = manifest.get(p.name) or {}
            if source_tag == "new":
                img_type, model = "new", None
            elif meta:
                img_type = meta.get("type") or "other"
                model = meta.get("model")
            else:
                parts = rel.parts  # contents/ready/<group>/...
                img_type = parts[2] if len(parts) > 2 else "other"
                model = parts[3] if len(parts) == 5 else None
            tags = meta.get("tags") or []
            url_path = "/".join(rel.parts)
            try:
                mtime_iso = _dt.fromtimestamp(p.stat().st_mtime, tz=_PHT).isoformat()
            except Exception:
                mtime_iso = ""
            items.append({
                "filename": p.name,
                "path": path_str,
                "src_url": "/api/images/" + url_path,
                "thumb_url": "/api/thumb/" + url_path + "?w=240",
                "tags": tags,
                "type": img_type,
                "model": model,
                "tagged_at": meta.get("tagged_at") or mtime_iso,
                "favorite": path_str in favs,
                "archived": path_str in archived,
                "untagged": not bool(meta),
                "source": source_tag,
            })

    _walk(ready_dir, "ready")
    _walk(new_dir, "new")
    # contents/runs/{timestamp}_bespoke/ -- bespoke pipeline outputs that
    # used to be invisible to the schedule picker (same gap the image bank
    # had). Treat them as drafts (source=new) so they sort to the top.
    runs_dir = PROJECT_ROOT / "contents" / "runs"
    if runs_dir.exists():
        _walk(runs_dir, "new")
    items.sort(key=lambda x: (x.get("tagged_at") or "", x["filename"]), reverse=True)
    return jsonify(items)


@app.route("/api/schedule/image-bank/archive", methods=["POST"])
def sched_bank_archive():
    """Toggle archived state for an image path."""
    data = request.get_json(silent=True) or {}
    path = (data.get("path") or "").strip()
    action = (data.get("action") or "toggle").strip().lower()
    if not path or not _safe_project_path(path):
        return jsonify({"ok": False, "error": "invalid path"}), 400
    with _ARCHIVE_LOCK:
        archived = _load_archived()
        if action == "add":
            archived.add(path); is_archived = True
        elif action == "remove":
            archived.discard(path); is_archived = False
        else:
            if path in archived:
                archived.discard(path); is_archived = False
            else:
                archived.add(path); is_archived = True
        _save_archived(archived)
    return jsonify({"ok": True, "path": path, "archived": is_archived, "count": len(archived)})


@app.route("/api/schedule/image-bank/delete", methods=["POST"])
def sched_bank_delete():
    """Move an image to .tmp/bank_trash/<YYYY-MM-DD>/ (soft-delete, recoverable)."""
    data = request.get_json(silent=True) or {}
    rel_path = (data.get("path") or "").strip()
    safe = _safe_project_path(rel_path)
    if not rel_path or not safe or not safe.exists() or not safe.is_file():
        return jsonify({"ok": False, "error": "invalid or missing path"}), 400
    if safe.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        return jsonify({"ok": False, "error": "not an image"}), 400

    today = _dt.now(_PHT).strftime("%Y-%m-%d")
    trash_subdir = _BANK_TRASH_DIR / today
    trash_subdir.mkdir(parents=True, exist_ok=True)

    dest = trash_subdir / safe.name
    # If a same-named file already exists in today's trash, suffix _1, _2, ...
    if dest.exists():
        i = 1
        stem, ext = safe.stem, safe.suffix
        while (trash_subdir / f"{stem}_{i}{ext}").exists():
            i += 1
        dest = trash_subdir / f"{stem}_{i}{ext}"

    import shutil
    try:
        shutil.move(str(safe), str(dest))
    except Exception as exc:
        return jsonify({"ok": False, "error": f"move failed: {exc}"}), 500

    # Clean up favorites + archive lists (the path now refers to a moved file)
    with _FAVORITES_LOCK:
        favs = _load_favorites()
        if rel_path in favs:
            favs.discard(rel_path); _save_favorites(favs)
    with _ARCHIVE_LOCK:
        archived = _load_archived()
        if rel_path in archived:
            archived.discard(rel_path); _save_archived(archived)

    # Clean up manifest entry if present (filename-keyed, only safe to remove if no other file with same name exists)
    manifest_path = PROJECT_ROOT / "contents" / "ready" / "manifest.json"
    if manifest_path.exists():
        try:
            m = json.loads(manifest_path.read_text(encoding="utf-8")) or {}
            if safe.name in m:
                # Confirm no other ready-tree file shares this filename
                ready_dir = PROJECT_ROOT / "contents" / "ready"
                still_exists = any(p for p in ready_dir.rglob(safe.name) if p.is_file())
                if not still_exists:
                    del m[safe.name]
                    with open(manifest_path, "w", encoding="utf-8") as f:
                        json.dump(m, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    return jsonify({"ok": True, "path": rel_path, "moved_to": str(dest.relative_to(PROJECT_ROOT)).replace("\\", "/")})


# ---------- Schedule v2: Calendar + AI Suggest helpers ----------

_REFERENCES_DIR = PROJECT_ROOT / "references"


def _load_holidays(year: int) -> list:
    """Return [{date, name}] from references/ph_holidays_<year>.json. Empty list if missing/bad."""
    p = _REFERENCES_DIR / f"ph_holidays_{year}.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("holidays") or []
    except Exception:
        return []


def _load_manual_events() -> list:
    """Return [{id, date, title, notes}] from references/ph_events_manual.json. Empty if missing/bad."""
    p = _REFERENCES_DIR / "ph_events_manual.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("events") or []
    except Exception:
        return []


def _post_summary_for_calendar(item: dict) -> dict:
    sched_iso = item.get("scheduled_for") or ""
    try:
        dt = _sched_parse_iso(sched_iso) if sched_iso else None
    except Exception:
        dt = None
    return {
        "id": item.get("id"),
        "time": dt.strftime("%H:%M") if dt else "",
        "caption": (item.get("caption") or "")[:200],
        "image_count": len(item.get("image_paths") or []),
        "status": item.get("status"),
        "mode": item.get("mode"),
        "layout": item.get("layout"),
        "fb_post_id": item.get("fb_post_id"),
    }


@app.route("/api/schedule/calendar")
def sched_calendar():
    """Combined month view: posts + holidays + manual events, grouped by date.

    Query: ?month=YYYY-MM (default = current PHT month).
    """
    month = request.args.get("month", "").strip()
    today = _dt.now(_PHT).date()
    if not month:
        month = today.strftime("%Y-%m")
    try:
        year, mo = map(int, month.split("-"))
        if not (1 <= mo <= 12) or not (2024 <= year <= 2032):
            raise ValueError("out of range")
    except Exception:
        return jsonify({"ok": False, "error": "month must be YYYY-MM"}), 400

    days: dict[str, dict] = {}

    def _slot(date_str: str) -> dict:
        if date_str not in days:
            days[date_str] = {"posts": [], "events": [], "holidays": []}
        return days[date_str]

    # 1. Posts whose scheduled_for falls in this month
    for it in _sched_load_queue():
        sched_iso = it.get("scheduled_for") or ""
        if not sched_iso:
            continue
        try:
            dt = _sched_parse_iso(sched_iso)
        except Exception:
            continue
        if dt.year != year or dt.month != mo:
            continue
        date_str = dt.strftime("%Y-%m-%d")
        _slot(date_str)["posts"].append(_post_summary_for_calendar(it))

    # Sort posts in each day by time
    for d in days.values():
        d["posts"].sort(key=lambda p: p.get("time") or "")

    # 2. Holidays from references/ph_holidays_<year>.json (in this month)
    for h in _load_holidays(year):
        date_str = (h.get("date") or "").strip()
        if not date_str.startswith(f"{year:04d}-{mo:02d}"):
            continue
        _slot(date_str)["holidays"].append({"name": h.get("name", "")})

    # 3. Manual events from references/ph_events_manual.json (in this month)
    for e in _load_manual_events():
        date_str = (e.get("date") or "").strip()
        if not date_str.startswith(f"{year:04d}-{mo:02d}"):
            continue
        _slot(date_str)["events"].append({
            "title": e.get("title", ""),
            "notes": e.get("notes", ""),
            "id": e.get("id", ""),
        })

    return jsonify({
        "month": month,
        "today": today.isoformat(),
        "days": days,
    })


# ---------- Schedule v2: AI Suggest chat (per-session, persisted to disk) ----

_SCHED_CHAT_LOCK = threading.Lock()
_SCHED_CHAT_SESSIONS: dict[str, dict] = {}
# entry: { messages: [{role, content, ts}], claude_resume_id: str|None, images_hash: str, token_estimate: int, created_at: str }

SCHED_CHAT_MODEL = os.environ.get("SCHED_CHAT_MODEL", "claude-sonnet-4-6")

# Conversations are persisted to disk so RA can review how a caption decision
# evolved across iterations -- in-memory state survives only until CC restart,
# but the audit trail survives forever.
_SCHED_CHAT_DIR = PROJECT_ROOT / ".tmp" / "sched_chat_history"


def _sched_chat_persist(sid: str, sess: dict) -> None:
    """Atomically write the session to disk. Best-effort; never raises."""
    try:
        _SCHED_CHAT_DIR.mkdir(parents=True, exist_ok=True)
        path = _SCHED_CHAT_DIR / f"{sid}.json"
        data = {
            "session_id": sid,
            "created_at": sess.get("created_at") or _dt.now(_PHT).isoformat(),
            "last_updated": _dt.now(_PHT).isoformat(),
            "images_hash": sess.get("images_hash", ""),
            "claude_resume_id": sess.get("claude_resume_id"),
            "message_count": len(sess.get("messages", [])),
            "messages": sess.get("messages", []),
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    except Exception as e:
        print(f"sched_chat_persist failed for {sid}: {e}", file=sys.stderr, flush=True)


def _sched_chat_load(sid: str) -> dict | None:
    """Read a persisted session from disk -- None if missing/corrupt."""
    try:
        path = _SCHED_CHAT_DIR / f"{sid}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        msgs = data.get("messages", []) or []
        return {
            "messages": msgs,
            "claude_resume_id": data.get("claude_resume_id"),
            "images_hash": data.get("images_hash", ""),
            "token_estimate": sum(len(m.get("content", "")) for m in msgs) // 4,
            "created_at": data.get("created_at"),
        }
    except Exception as e:
        print(f"sched_chat_load failed for {sid}: {e}", file=sys.stderr, flush=True)
        return None


def _upcoming_holidays_internal(days_n: int = 14) -> list:
    """In-process version of /api/schedule/upcoming-holidays (no HTTP roundtrip)."""
    today = _dt.now(_PHT).date()
    horizon = today + _td(days=days_n)
    out = []
    for yr in {today.year, horizon.year}:
        for h in _load_holidays(yr):
            try:
                d = _date.fromisoformat(h.get("date", ""))
            except Exception:
                continue
            if today <= d <= horizon:
                out.append({"date": d.isoformat(), "name": h.get("name", ""), "days_away": (d - today).days, "kind": "holiday"})
    for e in _load_manual_events():
        try:
            d = _date.fromisoformat(e.get("date", ""))
        except Exception:
            continue
        if today <= d <= horizon:
            out.append({"date": d.isoformat(), "name": e.get("title", ""), "notes": e.get("notes", ""), "days_away": (d - today).days, "kind": "event"})
    out.sort(key=lambda x: (x["date"], x["name"]))
    return out


def _build_sched_chat_system_prompt() -> str:
    """Brand context + caption/time formats + auto-injected upcoming holidays."""
    horizon = _upcoming_holidays_internal(14)
    if horizon:
        lines = [f"  - {h['name']} ({h['date']}, {h['days_away']} day{'s' if h['days_away'] != 1 else ''} away)" for h in horizon[:8]]
        upcoming_block = "Upcoming PH holidays/events in next 14 days:\n" + "\n".join(lines) + "\nLean into these when relevant to caption topic or posting time."
    else:
        upcoming_block = "No notable PH holidays or RA-flagged events in the next 14 days."

    return f"""You are RA's caption brainstorm partner for DuberyMNL, a Filipino DTC polarized sunglasses brand. Your job is a thinking skill, not a template: read each image's visual register and write captions that match it. Voice is the variable; brand facts are constant.

BRAND CONTEXT (and the voice evolution)
DuberyMNL is repositioning. Same affordable 499 polarized sunglasses, but the imagery has leveled up -- from casual Filipino DTC snapshots toward premium editorial / commercial-grade visuals. The caption voice should follow the image without losing accessibility. The tension to manage: premium feel + affordable price + Filipino DTC honesty. Lean into whichever side THIS image pulls toward. A casual barkada snapshot wants warm Taglish; a Y2K editorial wants confident concept copy; a sunset hero shot wants cinematic minimalism; a clean studio product shot wants product-led restraint.

BRAND FACTS (non-negotiable across every image)
- 11 colorways across 3 lines: Bandits, Outback, Rasta.
- 499 per pair. Free shipping on 2+ pairs. Metro Manila is the primary ads market.
- English-dominant (~95%) with light Filipino sprinkles. Authentic, never corporate-stiff.
- Never write the peso prefix or symbol -- just "499". Never mention internal codes (D518, D918, D008) -- use product name + colorway only.
- Website: duberymnl.com (canonical). Surface it as a soft CTA in roughly 1 out of every 3-4 captions in a brainstorm set -- not every option, never spammy. Naturally fits product-forward, price-led, or social-bait angles ("Shop duberymnl.com.", "duberymnl.com -- 499, free shipping pag 2+.", "Tap. Shop. Equip. duberymnl.com"). Editorial mood / cinematic / story-hook options usually skip the URL because the silence carries.

THE SKILL (how to brainstorm any image)

Step 1 -- READ THE IMAGE. In one sentence, name what's actually there: who's in it, what production register (snapshot / editorial / gritty / polished / retro / cinematic / studio / lifestyle), what mood or world it lives in, what color story and props communicate. Be specific to THIS image. Generic reads ("two people wearing sunglasses") fail the brief.

Step 2 -- MATCH THE CAPTION REGISTER TO THAT READ. Don't force a theme that isn't on screen. The image tells you the register:
- Premium editorial / commercial -> confident, short, concept-driven
- Filipino barkada / slice-of-life -> warmer Taglish, conversational
- Themed / retro / pop-culture visuals -> mine vocabulary from that adjacent world (gaming, anime, music, sports, Y2K, streetwear, etc.) but only because the image already lives there
- Clean studio product -> product-led restraint, the lenses do the talking
- Cinematic hero -> minimal, mood-first, let the silence carry

Step 3 -- GENERATE 5-8 OPTIONS spanning different angles. Label each option in parens with the angle it represents. Labels EMERGE from THIS specific image -- never pick from a fixed menu. Examples of angle types (open list, not exhaustive): product-led, story-hook, scene-anchored, taglish-warmth, cinematic-minimal, social-bait, duo/character-dynamic, place/setting, price-led-CTA, mood-only. Mix tones across the set. If two options would land the same way, drop one and find a fresh angle.

Step 4 -- CLOSE WITH A PICK. One favorite + one sentence on why it fits THIS image best. Then open the next move: "Lean harder into [strongest angle], pivot to [different read], or want a Taglish layer / a CTA version?"

ITERATION
When RA pushes a direction in followup ("lean into the duo dynamic", "more premium", "make it Taglish", "use a CTA"), GO DEEPER into that vein. Don't reset to a generic menu. Each turn either deepens a thread or deliberately opens a new angle. The chat has memory -- reference earlier turns when relevant. If a thread is exhausted, say so and propose 2-3 new angles to riff on next.

CAPTION CRAFT
- Most captions under 200 chars. Multi-line OK when it reads as a small scene.
- ALL CAPS headlines work when short and punchy; skip them when the vibe is restrained.
- Specificity beats generality. The image is your evidence -- name what's actually in it.
- Price/shipping CTAs land when the image is product-forward; skip them when the image is editorial mood.
- Story hooks usually beat feature lists, but not always -- a clean product hero can earn the right to just say the product.

DIFFERENT MODE -- POSTING TIME
If RA asks for a posting time, reply with ONE PHT slot in `Day Mmm DD, H:MM AM/PM PHT` format on its own line, then 1-2 sentences of rationale (audience habits or upcoming event/holiday). No caption options unless also requested.

CONTEXT (auto-injected each turn)
{upcoming_block}

If RA shares image file paths, call the Read tool on each before answering. The image is the brief -- every angle should be traceable to something actually visible in the frame."""


def _sched_chat_get(sid: str) -> dict:
    sess = _SCHED_CHAT_SESSIONS.get(sid)
    if not sess:
        # Try restoring from disk before creating fresh -- preserves history
        # across CC restarts including the Claude resume_id so the model also
        # remembers prior context, not just RA's eyeballs reading the log.
        sess = _sched_chat_load(sid)
        if not sess:
            sess = {
                "messages": [],
                "claude_resume_id": None,
                "images_hash": "",
                "token_estimate": 0,
                "created_at": _dt.now(_PHT).isoformat(),
            }
        _SCHED_CHAT_SESSIONS[sid] = sess
    return sess


def _hash_image_paths(paths: list) -> str:
    import hashlib
    s = "|".join(paths or [])
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]


def _run_sched_chat(prompt_text: str, resume_id: str | None) -> tuple[str, str | None]:
    """Run claude_agent_sdk.query for the Schedule chat. Returns (assistant_text, new_session_id)."""
    from claude_agent_sdk import query, ClaudeAgentOptions

    options = ClaudeAgentOptions(
        cwd=PROJECT_ROOT.as_posix(),
        system_prompt=_build_sched_chat_system_prompt(),
        model=SCHED_CHAT_MODEL,
        max_turns=6,
        permission_mode="bypassPermissions",
        allowed_tools=["Read"],
        resume=resume_id,
    )

    chunks: list[str] = []
    new_sid: str | None = None

    async def _drain():
        nonlocal new_sid
        async for msg in query(prompt=prompt_text, options=options):
            cls_name = type(msg).__name__
            if cls_name == "SystemMessage":
                data = getattr(msg, "data", {}) or {}
                sid = data.get("session_id")
                if sid and new_sid is None:
                    new_sid = sid
            elif cls_name == "AssistantMessage":
                content = getattr(msg, "content", []) or []
                for block in content:
                    text = getattr(block, "text", None)
                    if text:
                        chunks.append(text)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_drain())
    finally:
        loop.close()

    return ("".join(chunks).strip(), new_sid)


@app.route("/api/schedule/chat/history", methods=["GET"])
def sched_chat_history():
    sid = (request.args.get("session_id") or "").strip()
    if not sid:
        return jsonify({"ok": False, "error": "session_id required"}), 400
    # Prefer in-memory; fall back to disk for sessions from before last restart.
    with _SCHED_CHAT_LOCK:
        sess = _SCHED_CHAT_SESSIONS.get(sid) or {}
    if not sess:
        sess = _sched_chat_load(sid) or {}
    return jsonify({
        "ok": True,
        "session_id": sid,
        "messages": sess.get("messages", []),
        "token_estimate": sess.get("token_estimate", 0),
        "has_images": bool(sess.get("images_hash")),
        "created_at": sess.get("created_at"),
    })


@app.route("/api/schedule/chat/sessions", methods=["GET"])
def sched_chat_sessions():
    """List past AI Suggest brainstorms (newest first). Returns metadata only --
    use /api/schedule/chat/history?session_id=... for the full message list."""
    if not _SCHED_CHAT_DIR.exists():
        return jsonify({"ok": True, "sessions": []})
    entries = []
    for p in _SCHED_CHAT_DIR.glob("*.json"):
        if p.name.endswith(".tmp"):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        msgs = data.get("messages") or []
        first_user = next((m.get("content", "") for m in msgs if m.get("role") == "user"), "")
        last_msg = msgs[-1].get("content", "") if msgs else ""
        entries.append({
            "session_id": data.get("session_id") or p.stem,
            "created_at": data.get("created_at"),
            "last_updated": data.get("last_updated"),
            "message_count": data.get("message_count") or len(msgs),
            "first_user_message": (first_user or "")[:140],
            "last_message_preview": (last_msg or "")[:140],
            "has_images": bool(data.get("images_hash")),
        })
    entries.sort(key=lambda e: e.get("last_updated") or "", reverse=True)
    return jsonify({"ok": True, "sessions": entries})


@app.route("/api/schedule/chat", methods=["POST"])
def sched_chat():
    data = request.get_json(silent=True) or {}
    sid = (data.get("session_id") or "").strip()
    message = (data.get("message") or "").strip()
    image_paths_raw = data.get("image_paths") or []

    if not sid:
        return jsonify({"ok": False, "error": "session_id required"}), 400
    if not message:
        return jsonify({"ok": False, "error": "message required"}), 400
    if not isinstance(image_paths_raw, list):
        return jsonify({"ok": False, "error": "image_paths must be a list"}), 400

    # Validate image paths -- accept project-relative; resolve to absolute for Claude's Read tool.
    abs_image_paths: list[str] = []
    for p in image_paths_raw:
        safe = _safe_project_path(p)
        if not safe or not safe.exists():
            return jsonify({"ok": False, "error": f"image not found: {p}"}), 400
        abs_image_paths.append(safe.as_posix())

    with _SCHED_CHAT_LOCK:
        sess = _sched_chat_get(sid)
        new_hash = _hash_image_paths(image_paths_raw)
        is_first_turn = not sess["messages"]
        images_changed = (new_hash != sess.get("images_hash", ""))

        # Build the prompt: first turn (or images changed) embeds the file paths.
        if abs_image_paths and (is_first_turn or images_changed):
            img_block = "\n".join(f"  - {p}" for p in abs_image_paths)
            prompt_text = f"{message}\n\nReference images (call Read on each before answering):\n{img_block}"
            sess["images_hash"] = new_hash
        else:
            prompt_text = message

        # Append user message to history immediately (so a crash mid-call leaves a record)
        sess["messages"].append({"role": "user", "content": message, "ts": _dt.now(_PHT).isoformat()})
        resume_id = sess.get("claude_resume_id")
        _sched_chat_persist(sid, sess)

    # Run the agent OUTSIDE the lock (long-running)
    try:
        reply_text, new_sid = _run_sched_chat(prompt_text, resume_id)
    except Exception as e:
        with _SCHED_CHAT_LOCK:
            sess["messages"].append({"role": "assistant", "content": f"[error] {type(e).__name__}: {e}", "ts": _dt.now(_PHT).isoformat(), "error": True})
            _sched_chat_persist(sid, sess)
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500

    with _SCHED_CHAT_LOCK:
        if new_sid and not sess.get("claude_resume_id"):
            sess["claude_resume_id"] = new_sid
        reply_record = {"role": "assistant", "content": reply_text or "(no reply)", "ts": _dt.now(_PHT).isoformat()}
        sess["messages"].append(reply_record)
        # Rough token estimate: chars / 4
        sess["token_estimate"] = sum(len(m.get("content", "")) for m in sess["messages"]) // 4
        # Persist after every turn so the audit trail survives crashes / restarts.
        _sched_chat_persist(sid, sess)

    return jsonify({
        "ok": True,
        "session_id": sid,
        "message": reply_record,
        "token_estimate": sess["token_estimate"],
        "message_count": len(sess["messages"]),
    })


@app.route("/api/schedule/chat/reset", methods=["POST"])
def sched_chat_reset():
    data = request.get_json(silent=True) or {}
    sid = (data.get("session_id") or "").strip()
    if not sid:
        return jsonify({"ok": False, "error": "session_id required"}), 400
    with _SCHED_CHAT_LOCK:
        _SCHED_CHAT_SESSIONS.pop(sid, None)
    return jsonify({"ok": True, "session_id": sid})


@app.route("/api/schedule/upcoming-holidays")
def sched_upcoming_holidays():
    """Holidays + manual events in the next N days (default 14), sorted by date.

    Query: ?days=14 (clamped 1..60).
    """
    try:
        days_n = int(request.args.get("days", "14"))
    except Exception:
        days_n = 14
    days_n = max(1, min(60, days_n))

    today = _dt.now(_PHT).date()
    horizon = today + _td(days=days_n)

    out = []

    # Holidays in current + next year (to span year-boundary windows)
    years = {today.year, horizon.year}
    for yr in years:
        for h in _load_holidays(yr):
            try:
                d = _date.fromisoformat(h.get("date", ""))
            except Exception:
                continue
            if today <= d <= horizon:
                out.append({
                    "date": d.isoformat(),
                    "name": h.get("name", ""),
                    "days_away": (d - today).days,
                    "kind": "holiday",
                })

    # Manual events
    for e in _load_manual_events():
        try:
            d = _date.fromisoformat(e.get("date", ""))
        except Exception:
            continue
        if today <= d <= horizon:
            out.append({
                "date": d.isoformat(),
                "name": e.get("title", ""),
                "notes": e.get("notes", ""),
                "days_away": (d - today).days,
                "kind": "event",
            })

    out.sort(key=lambda x: (x["date"], x["name"]))
    return jsonify(out)


@app.route("/favicon.ico")
def favicon():
    # Served from static/ once Task 28 creates it. Returns 204 until then.
    fav = STATIC_DIR / "favicon.ico"
    if fav.exists():
        return send_from_directory(str(STATIC_DIR), "favicon.ico")
    return ("", 204)


if __name__ == "__main__":
    print(f"DuberyMNL Command Center starting on port {PORT}", flush=True)
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)

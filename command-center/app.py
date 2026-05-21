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


@app.route("/api/home/summary", methods=["GET"])
def home_summary():
    """Overview tiles for the Home tab. Cheap aggregation, no expensive API calls."""
    import requests as _req

    # --- revenue_today: best-effort; returns None if not computable ---
    revenue_today = None
    try:
        # TODO wire to CRM sheet `leads`/`orders` tab in Phase 3 for real
        # per-day revenue. For Phase 1 we leave it null so the UI shows "--".
        revenue_today = None
    except Exception:
        revenue_today = None

    # --- active_convos: pulled from chatbot /status JSON if reachable ---
    active_convos = None
    try:
        r = _req.get("http://localhost:8080/status", timeout=2)
        if r.ok:
            data = r.json()
            # Chatbot /status returns a stats dict; pick a reasonable count.
            for k in ("active_conversations", "conversations_active", "active_sessions"):
                if k in data:
                    active_convos = int(data[k])
                    break
    except Exception:
        active_convos = None

    # --- pending_approvals: count pipeline items awaiting image/caption review ---
    pending_approvals = None
    try:
        pipeline_path = PROJECT_ROOT / ".tmp" / "pipeline.json"
        if pipeline_path.exists():
            import json as _json
            items = _json.loads(pipeline_path.read_text(encoding="utf-8"))
            pending_approvals = sum(
                1 for c in items
                if c.get("status") in ("PENDING", "PROMPT_READY", "DONE")
            )
    except Exception:
        pending_approvals = None

    # --- system_health: cheap monitors in parallel, not_wired is not a fail ---
    health = "green"
    try:
        cheap = [(n, fn) for (n, fn, exp) in SERVICES if not exp]

        def _safe(fn):
            try:
                return fn().state
            except Exception:
                return "offline"

        with ThreadPoolExecutor(max_workers=len(cheap) or 1) as pool:
            states = list(pool.map(_safe, (fn for _n, fn in cheap)))
        if any(s == "offline" for s in states):
            health = "red"
        elif any(s == "degraded" for s in states):
            health = "yellow"
        else:
            health = "green"
    except Exception:
        health = "yellow"

    return jsonify({
        "revenue_today": revenue_today,
        "active_convos": active_convos,
        "pending_approvals": pending_approvals,
        "system_health": health,
    })


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

    items.sort(key=lambda x: x["mtime"], reverse=True)
    for item in items:
        del item["mtime"]

    return jsonify(items)


@app.route("/api/crm/summary", methods=["GET"])
def crm_summary():
    """Aggregate CRM stats: lead counts by status, order totals."""
    try:
        from chatbot.crm_sync import _get_service, SHEET_ID
    except ImportError as e:
        return jsonify({"error": f"import failed: {e}"}), 500

    service = _get_service()
    if not service:
        return jsonify({"error": "no credentials"}), 503

    try:
        leads_result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="'Leads'!A:K",
        ).execute()
        lead_rows = leads_result.get("values", [])[1:]

        status_counts = {"Cold": 0, "Warm": 0, "Hot": 0, "Converted": 0}
        for row in lead_rows:
            if len(row) >= 10:
                s = row[9].strip() or "Cold"
                status_counts[s] = status_counts.get(s, 0) + 1

        orders_result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="'Orders'!A:K",
        ).execute()
        order_rows = orders_result.get("values", [])[1:]

        total_revenue = 0.0
        for row in order_rows:
            if len(row) >= 5:
                try:
                    total_revenue += float(row[4])
                except (ValueError, TypeError):
                    pass

        from datetime import date
        today_str = date.today().isoformat()
        orders_today = sum(
            1 for row in order_rows
            if len(row) >= 10 and row[9][:10] == today_str
        )

        return jsonify({
            "total_leads": len(lead_rows),
            "status_counts": status_counts,
            "total_orders": len(order_rows),
            "orders_today": orders_today,
            "total_revenue": total_revenue,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/crm/leads", methods=["GET"])
def crm_leads():
    """Return leads from the CRM sheet, newest first (up to 100)."""
    try:
        from chatbot.crm_sync import _get_service, SHEET_ID
    except ImportError as e:
        return jsonify({"error": f"import failed: {e}"}), 500

    service = _get_service()
    if not service:
        return jsonify({"error": "no credentials"}), 503

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="'Leads'!A:K",
        ).execute()
        rows = result.get("values", [])[1:]
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
    """Return orders from the CRM sheet, newest first (up to 100)."""
    try:
        from chatbot.crm_sync import _get_service, SHEET_ID
    except ImportError as e:
        return jsonify({"error": f"import failed: {e}"}), 500

    service = _get_service()
    if not service:
        return jsonify({"error": "no credentials"}), 503

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="'Orders'!A:K",
        ).execute()
        rows = result.get("values", [])[1:]
        keys = ["order_id", "lead_id", "items", "quantity", "total",
                "discount_code", "payment_method", "delivery_preference",
                "delivery_time", "order_date", "status"]
        orders = []
        for row in reversed(rows):
            padded = row + [""] * (11 - len(row))
            orders.append(dict(zip(keys, padded[:11])))
        return jsonify(orders[:100])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/inventory/summary", methods=["GET"])
def inventory_summary():
    """Return per-SKU inventory: initial, sold, remaining."""
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "tools" / "orders"))
        from inventory_report import compute_report  # noqa: E402
        report = compute_report()
        return jsonify(report)
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


# ---------- Schedule v2: AI Suggest chat (per-session in-memory) ----------

_SCHED_CHAT_LOCK = threading.Lock()
_SCHED_CHAT_SESSIONS: dict[str, dict] = {}
# entry: { messages: [{role, content, ts}], claude_resume_id: str|None, images_hash: str, token_estimate: int }

SCHED_CHAT_MODEL = os.environ.get("SCHED_CHAT_MODEL", "claude-sonnet-4-6")


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

    return f"""You are RA's caption brainstorm assistant for DuberyMNL, a Filipino direct-to-consumer polarized sunglasses brand.

BRAND FACTS
- Product: Polarized sunglasses, 11 colorways across 3 lines (Bandits, Outback, Rasta).
- Price: P499 per pair. Free shipping on 2+ pairs. Metro Manila is the primary ads market.
- Voice: Authentic Filipino DTC tone. English-dominant (~95%) with light Filipino sprinkles. Never corporate-stiff.
- Never use the peso prefix "P" or the symbol -- write plain "499". Never mention internal model codes (D518, D918, D008) -- use product name + colorway only.

WHEN ASKED FOR CAPTION OPTIONS
Format your reply as 3 numbered options. Each on its own line, prefixed with `OPTION 1 --`, `OPTION 2 --`, `OPTION 3 --`, followed by a short label like "(product-first)", "(conversational)", "(lifestyle)". Then the caption text. Keep captions under 200 chars unless asked.

WHEN ASKED FOR A POSTING TIME
Reply with ONE PHT slot in `Day Mmm DD, H:MM AM/PM PHT` format on its own line, then 1-2 sentences of rationale referencing the audience or any upcoming event/holiday.

CONTEXT (auto-injected each turn)
{upcoming_block}

If RA shares image file paths, you can call the Read tool to view them and ground your suggestions in the actual product/scene. Keep replies tight -- this is a brainstorm side-panel, not a long doc."""


def _sched_chat_get(sid: str) -> dict:
    sess = _SCHED_CHAT_SESSIONS.get(sid)
    if not sess:
        sess = {"messages": [], "claude_resume_id": None, "images_hash": "", "token_estimate": 0}
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
    with _SCHED_CHAT_LOCK:
        sess = _SCHED_CHAT_SESSIONS.get(sid) or {}
    return jsonify({
        "ok": True,
        "session_id": sid,
        "messages": sess.get("messages", []),
        "token_estimate": sess.get("token_estimate", 0),
        "has_images": bool(sess.get("images_hash")),
    })


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

    # Run the agent OUTSIDE the lock (long-running)
    try:
        reply_text, new_sid = _run_sched_chat(prompt_text, resume_id)
    except Exception as e:
        with _SCHED_CHAT_LOCK:
            sess["messages"].append({"role": "assistant", "content": f"[error] {type(e).__name__}: {e}", "ts": _dt.now(_PHT).isoformat(), "error": True})
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500

    with _SCHED_CHAT_LOCK:
        if new_sid and not sess.get("claude_resume_id"):
            sess["claude_resume_id"] = new_sid
        reply_record = {"role": "assistant", "content": reply_text or "(no reply)", "ts": _dt.now(_PHT).isoformat()}
        sess["messages"].append(reply_record)
        # Rough token estimate: chars / 4
        sess["token_estimate"] = sum(len(m.get("content", "")) for m in sess["messages"]) // 4

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

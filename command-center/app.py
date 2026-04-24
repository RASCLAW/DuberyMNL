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

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

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
    if not full.exists() or not full.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return ("not found", 404)
    return send_from_directory(str(full.parent), full.name)


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

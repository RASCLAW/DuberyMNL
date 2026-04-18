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

from flask import Flask, Response, jsonify, render_template, request, send_from_directory

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

app = Flask(
    __name__,
    static_folder=str(STATIC_DIR),
    template_folder=str(TEMPLATE_DIR),
)


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
            kind, value = q.get()
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


@app.route("/favicon.ico")
def favicon():
    # Served from static/ once Task 28 creates it. Returns 204 until then.
    fav = STATIC_DIR / "favicon.ico"
    if fav.exists():
        return send_from_directory(str(STATIC_DIR), "favicon.ico")
    return ("", 204)


if __name__ == "__main__":
    print(f"DuberyMNL Command Center starting on port {PORT}", flush=True)
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)

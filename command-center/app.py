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

    return jsonify([r.to_dict() for r in results if r is not None])


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

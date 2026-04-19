"""
chatbot/monitor.py -- Watchdog for messenger_webhook.py

Spawns the chatbot subprocess, health-checks it every 30s, restarts on failure,
and sends Telegram notifications. Also polls Telegram for commands from RA.

Commands (send to the Rasclaw bot):
  /restart  -- kill + restart chatbot
  /status   -- report whether process is alive

Run directly: python monitor.py
Task Scheduler: point to start-monitor.bat instead of start-chatbot.bat
"""
import os
import sys
import time
import subprocess
import threading
import urllib.request
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent
load_dotenv(PROJECT_DIR / ".env")

CHATBOT_CMD = [sys.executable, str(BASE_DIR / "messenger_webhook.py")]
_PORT = int(os.environ.get("PORT", 8085))
HEALTH_URL = f"http://localhost:{_PORT}/status"
HEALTH_INTERVAL = 30   # seconds between health checks
FAIL_THRESHOLD = 2     # consecutive failures before restart
STARTUP_GRACE = 15     # seconds to wait before first health check

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")
RA_CHAT_ID = 1762124488  # RA's personal Telegram user ID

# ── Logging ───────────────────────────────────────────────────────────────────
(PROJECT_DIR / ".tmp").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(PROJECT_DIR / ".tmp" / "monitor.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("monitor")

# ── State ─────────────────────────────────────────────────────────────────────
_proc = None
_lock = threading.Lock()
_server_log = None


# ── TG helpers ────────────────────────────────────────────────────────────────
def _tg_post(endpoint, payload):
    if not BOT_TOKEN:
        return
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{BOT_TOKEN}/{endpoint}",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log.warning(f"TG post failed ({endpoint}): {e}")


def tg_notify(text):
    _tg_post("sendMessage", {"chat_id": TG_CHAT_ID, "text": text, "disable_web_page_preview": True})


def tg_reply(chat_id, text):
    _tg_post("sendMessage", {"chat_id": chat_id, "text": text})


# ── Process management ────────────────────────────────────────────────────────
def _open_server_log():
    global _server_log
    if _server_log is None or _server_log.closed:
        _server_log = open(PROJECT_DIR / ".tmp" / "chatbot-server.log", "a", encoding="utf-8")
    return _server_log


def _spawn():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    logfile = _open_server_log()
    proc = subprocess.Popen(CHATBOT_CMD, cwd=str(BASE_DIR), env=env, stdout=logfile, stderr=logfile)
    log.info(f"Chatbot started (pid {proc.pid})")
    return proc


def _kill(proc):
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def restart_chatbot(reason):
    global _proc
    with _lock:
        log.warning(f"Restarting chatbot: {reason}")
        if _proc and _proc.poll() is None:
            _kill(_proc)
        time.sleep(2)
        _proc = _spawn()


# ── Health loop ───────────────────────────────────────────────────────────────
def health_loop():
    time.sleep(STARTUP_GRACE)
    fail_count = 0
    while True:
        # Check if process died between health checks
        with _lock:
            dead = _proc and _proc.poll() is not None
            exit_code = _proc.poll() if dead else None

        if dead:
            log.error(f"Chatbot exited unexpectedly (code {exit_code})")
            tg_notify(f"[DuberyMNL] Chatbot process exited (code {exit_code}). Restarting.")
            restart_chatbot(f"process exited with code {exit_code}")
            fail_count = 0
            time.sleep(HEALTH_INTERVAL)
            continue

        # HTTP health check
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=10) as resp:
                fail_count = 0 if resp.status == 200 else fail_count + 1
        except Exception:
            fail_count += 1
            log.warning(f"Health check failed ({fail_count}/{FAIL_THRESHOLD})")

        if fail_count >= FAIL_THRESHOLD:
            tg_notify("[DuberyMNL] Chatbot unresponsive. Restarting now.")
            restart_chatbot("health check failed")
            fail_count = 0

        time.sleep(HEALTH_INTERVAL)


# ── Telegram command poll ─────────────────────────────────────────────────────
def tg_poll_loop():
    if not BOT_TOKEN:
        log.warning("TELEGRAM_BOT_TOKEN not set — TG command poll disabled")
        return
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=30&offset={offset}"
            with urllib.request.urlopen(url, timeout=40) as resp:
                data = json.loads(resp.read())
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                from_id = msg.get("from", {}).get("id")
                text = msg.get("text", "").strip()
                if from_id != RA_CHAT_ID:
                    continue
                if text == "/restart":
                    log.info("Received /restart from RA via Telegram")
                    tg_reply(RA_CHAT_ID, "Restarting chatbot...")
                    restart_chatbot("/restart command from RA")
                    tg_reply(RA_CHAT_ID, "Chatbot restarted.")
                elif text == "/status":
                    with _lock:
                        alive = _proc and _proc.poll() is None
                        pid = _proc.pid if _proc else None
                    tg_reply(RA_CHAT_ID, f"Chatbot: {'RUNNING' if alive else 'DEAD'} (pid {pid})")
        except Exception as e:
            if "409" in str(e):
                log.warning("TG poll 409 conflict — backing off 60s")
                time.sleep(60)
            else:
                log.warning(f"TG poll error: {e}")
                time.sleep(10)


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    global _proc
    log.info("=== Monitor starting ===")
    _proc = _spawn()
    tg_notify("[DuberyMNL] Monitor started. Chatbot is up.")
    threading.Thread(target=health_loop, daemon=True).start()
    threading.Thread(target=tg_poll_loop, daemon=True).start()
    threading.Event().wait()


if __name__ == "__main__":
    main()

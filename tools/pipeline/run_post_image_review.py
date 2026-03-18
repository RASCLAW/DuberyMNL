"""
Post-Image-Review Orchestrator

Runs after image review to sync the pipeline sheet, update the landing page,
and notify RA via email.

Usage:
    python tools/pipeline/run_post_image_review.py
    python tools/pipeline/run_post_image_review.py --dry-run
    python tools/pipeline/run_post_image_review.py --no-email
"""

import argparse
import json
import smtplib
import subprocess
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
TMP_DIR = PROJECT_DIR / ".tmp"
PIPELINE_FILE = TMP_DIR / "pipeline.json"
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_env():
    env = {}
    env_path = PROJECT_DIR / ".env"
    if not env_path.exists():
        return env
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"\'')
    return env


def count_image_approved():
    if not PIPELINE_FILE.exists():
        return 0
    pipeline = json.loads(PIPELINE_FILE.read_text())
    return sum(1 for c in pipeline if c.get("status") == "IMAGE_APPROVED")


def get_ngrok_url():
    """Return the active ngrok public URL, or None if ngrok is not running."""
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:4040/api/tunnels", timeout=3) as resp:
            data = json.loads(resp.read())
            tunnels = data.get("tunnels", [])
            if tunnels:
                return tunnels[0]["public_url"]
    except Exception:
        pass
    return None


def send_notification(count, preview_url, env):
    sender = env.get("GMAIL_SENDER")
    password = env.get("GMAIL_APP_PASSWORD")
    recipient = env.get("REVIEW_EMAIL_RECIPIENT")

    if not all([sender, password, recipient]):
        print("  Email skipped: GMAIL_SENDER, GMAIL_APP_PASSWORD, REVIEW_EMAIL_RECIPIENT not all set in .env")
        return False

    subject = f"DuberyMNL — {count} ads ready on landing page"

    if preview_url:
        preview_line = f"Preview the landing page:\n{preview_url}"
    else:
        preview_line = (
            "Landing page data updated.\n"
            "Start ngrok to preview: cd dubery-landing && python3 -m http.server 8080"
        )

    body = f"""Hi RA,

Image review complete. {count} ads are now IMAGE_APPROVED and live on the landing page.

{preview_line}

The Google Sheet and captions.json have been updated automatically.

— DuberyMNL Automation
"""

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        print(f"  Email sent to {recipient}: \"{subject}\"")
        return True
    except Exception as e:
        print(f"  Email failed: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Post-image-review orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run without executing")
    parser.add_argument("--no-email", action="store_true", help="Skip email notification")
    args = parser.parse_args()

    approved_count = count_image_approved()
    preview_url = get_ngrok_url()

    print(f"\nPost-Image-Review Orchestrator")
    print(f"{'─' * 40}")
    print(f"  IMAGE_APPROVED captions: {approved_count}")
    print(f"  Landing page preview:    {preview_url or '(ngrok not running)'}")

    if args.dry_run:
        print("\nDRY RUN — no actions taken")
        print("  Would run: sync_pipeline.py --sheets-only")
        print("  Would run: export_captions.py")
        if not args.no_email:
            print(f"  Would send email: '{approved_count} ads ready on landing page'")
        sys.exit(0)

    # Step 1: Sync Google Sheet
    print("\nSyncing Google Sheet...")
    result = subprocess.run(
        [str(VENV_PYTHON), "tools/notion/sync_pipeline.py", "--sheets-only"],
        cwd=PROJECT_DIR,
    )
    if result.returncode != 0:
        print("  Sheet sync failed.")
    else:
        print("  Sheet synced.")

    # Step 2: Export landing page data
    print("\nExporting landing page data...")
    result = subprocess.run(
        [str(VENV_PYTHON), "tools/landing/export_captions.py"],
        cwd=PROJECT_DIR,
    )
    if result.returncode != 0:
        print("  Export failed.")
    else:
        print("  captions.json updated.")

    # Step 3: Send notification email
    if not args.no_email:
        print("\nSending notification email...")
        env = load_env()
        send_notification(approved_count, preview_url, env)

    print(f"\n{'─' * 40}")
    print(f"  Done. {approved_count} ads ready on landing page.")


if __name__ == "__main__":
    main()

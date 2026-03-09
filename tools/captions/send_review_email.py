"""
Send a review notification email via Gmail SMTP.

Usage:
    python tools/captions/send_review_email.py --count 25 --vibes "Commuter, Urban, Sale/Urgency"

Reads GMAIL_SENDER, GMAIL_APP_PASSWORD, REVIEW_EMAIL_RECIPIENT from .env.
"""

import os
import sys
import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

GMAIL_SENDER = os.getenv("GMAIL_SENDER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT = os.getenv("REVIEW_EMAIL_RECIPIENT")


def send_email(count: int, vibes: str):
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD or not RECIPIENT:
        print("Error: GMAIL_SENDER, GMAIL_APP_PASSWORD, REVIEW_EMAIL_RECIPIENT must be set in .env", file=sys.stderr)
        sys.exit(1)

    subject = f"DuberyMNL — {count} captions ready for review"

    vibe_list = "\n".join(f"  • {v.strip()}" for v in vibes.split(","))

    body = f"""Hi RA,

{count} new captions are ready for your review.

Vibes this batch:
{vibe_list}

Open the review page here:
http://localhost:5000

⚠️  Keep the terminal running — the server will shut down automatically after you submit.

---
Rate each caption (★1–5), edit the text if needed, toggle the visual anchor,
add feedback in the comment field, then hit Submit All.

✅ ≥3 stars → APPROVED
❌ <3 stars → REJECTED

— DuberyMNL Automation
"""

    msg = MIMEMultipart()
    msg["From"] = GMAIL_SENDER
    msg["To"] = RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, RECIPIENT, msg.as_string())

    print(f"Email sent to {RECIPIENT}: \"{subject}\"")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, required=True, help="Number of captions generated")
    parser.add_argument("--vibes", type=str, required=True, help="Comma-separated list of vibes")
    args = parser.parse_args()
    send_email(args.count, args.vibes)


if __name__ == "__main__":
    main()

"""
CRM sync module for DuberyMNL Messenger chatbot.

Writes customer data to the "DuberyMNL CRM" Google Sheet:
- Leads tab: one row per sender_id (upserted)
- Orders tab: one row per completed order
- Lead Score Log: one row per status transition

Uses Application Default Credentials (ADC) on Cloud Run.
The sheet must be shared with the Cloud Run service account as Editor.

All functions are safe to call inline -- they swallow errors so a sync
failure never blocks a customer reply.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SHEET_ID = "1wVn9WGdY8pK7c68pZpnNSWoNkhhZvYUywcGqLCqcewA"
TOKEN_FILE = Path(__file__).resolve().parent.parent / "token.json"

# Cache the service client across calls
_service = None


def _get_service():
    global _service
    if _service is None:
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE))
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
            _service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        except Exception as e:
            print(f"CRM sync auth failed: {e}", file=sys.stderr, flush=True)
            return None
    return _service


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


# --- Leads tab columns (order must match create_crm_sheet.py) ---
# Lead ID | Name | Phone | Address | Landmarks | Source | First Contact |
# Last Contact | Model Interest | Status | Notes
LEAD_COLUMNS = [
    "lead_id", "name", "phone", "address", "landmarks", "source",
    "first_contact", "last_contact", "model_interest", "status", "notes",
]

ORDER_COLUMNS = [
    "order_id", "lead_id", "items", "quantity", "total", "discount_code",
    "payment_method", "delivery_preference", "delivery_time",
    "order_date", "status",
]

LOG_COLUMNS = ["lead_id", "timestamp", "previous_status", "new_status", "trigger"]


def _find_lead_row(service, lead_id: str) -> int | None:
    """Return 1-indexed row number of a lead, or None if not found."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="'Leads'!A:A",
        ).execute()
        values = result.get("values", [])
        for i, row in enumerate(values):
            if row and row[0] == lead_id:
                return i + 1
        return None
    except Exception as e:
        print(f"Find lead failed: {e}", file=sys.stderr, flush=True)
        return None


def upsert_lead(
    lead_id: str,
    name: str = "",
    phone: str = "",
    address: str = "",
    landmarks: str = "",
    source: str = "Messenger",
    model_interest: str = "",
    status: str = "Cold",
    notes: str = "",
) -> bool:
    """Create or update a lead row. Safe to call repeatedly."""
    service = _get_service()
    if not service:
        return False

    try:
        now = _now_iso()
        existing_row = _find_lead_row(service, lead_id)

        if existing_row:
            # Update existing row: only update non-empty fields + last_contact
            result = service.spreadsheets().values().get(
                spreadsheetId=SHEET_ID,
                range=f"'Leads'!A{existing_row}:K{existing_row}",
            ).execute()
            current = result.get("values", [[]])[0]
            # Pad to 11 columns
            current = current + [""] * (11 - len(current))

            merged = [
                current[0],  # lead_id (never changes)
                name or current[1],
                phone or current[2],
                address or current[3],
                landmarks or current[4],
                current[5] or source,  # source never overwritten
                current[6] or now,  # first_contact never overwritten
                now,  # last_contact always updated
                model_interest or current[8],
                status or current[9],
                notes or current[10],
            ]

            service.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"'Leads'!A{existing_row}:K{existing_row}",
                valueInputOption="RAW",
                body={"values": [merged]},
            ).execute()
        else:
            # Append new row
            row = [
                lead_id, name, phone, address, landmarks, source,
                now, now, model_interest, status, notes,
            ]
            service.spreadsheets().values().append(
                spreadsheetId=SHEET_ID,
                range="'Leads'!A:K",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [row]},
            ).execute()

        return True
    except Exception as e:
        print(f"Upsert lead failed: {e}", file=sys.stderr, flush=True)
        return False


def log_status_change(lead_id: str, previous_status: str, new_status: str, trigger: str) -> bool:
    """Append a row to the Lead Score Log when a status changes."""
    if previous_status == new_status:
        return True
    service = _get_service()
    if not service:
        return False
    try:
        row = [lead_id, _now_iso(), previous_status, new_status, trigger]
        service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range="'Lead Score Log'!A:E",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()
        return True
    except Exception as e:
        print(f"Log status change failed: {e}", file=sys.stderr, flush=True)
        return False


def create_order(
    lead_id: str,
    items: str = "",
    quantity: int = 1,
    total: float = 0,
    discount_code: str = "",
    payment_method: str = "COD",
    delivery_preference: str = "",
    delivery_time: str = "",
    status: str = "Pending",
) -> str | None:
    """Append a new order row. Returns the generated order_id or None on failure."""
    service = _get_service()
    if not service:
        return None
    try:
        # Generate order ID from timestamp
        order_id = f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        row = [
            order_id, lead_id, items, str(quantity), str(total), discount_code,
            payment_method, delivery_preference, delivery_time,
            _now_iso(), status,
        ]
        service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range="'Orders'!A:K",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()
        return order_id
    except Exception as e:
        print(f"Create order failed: {e}", file=sys.stderr, flush=True)
        return None


# --- Conversation history persistence ---

def append_message(sender_id: str, role: str, content: str, intent: str = "") -> bool:
    """Append a single message to the Conversations tab."""
    service = _get_service()
    if not service:
        return False
    try:
        row = [sender_id, _now_iso(), role, content, intent or ""]
        service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range="'Conversations'!A:E",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()
        return True
    except Exception as e:
        print(f"Append message failed: {e}", file=sys.stderr, flush=True)
        return False


def load_history(sender_id: str, limit: int = 20) -> list:
    """Load recent message history for a sender from the Conversations tab."""
    service = _get_service()
    if not service:
        return []
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="'Conversations'!A:E",
        ).execute()
        rows = result.get("values", [])[1:]  # skip header
        # Filter by sender_id
        sender_rows = [r for r in rows if len(r) >= 4 and r[0] == sender_id]
        # Keep the most recent `limit` entries
        recent = sender_rows[-limit:]
        history = []
        for r in recent:
            row_padded = r + [""] * (5 - len(r))
            history.append({
                "role": row_padded[2],
                "content": row_padded[3],
                "timestamp": row_padded[1],
            })
        return history
    except Exception as e:
        print(f"Load history failed: {e}", file=sys.stderr, flush=True)
        return []


# --- Scoring helper ---

def infer_status(
    message_count: int,
    has_name: bool,
    has_phone: bool,
    has_address: bool,
    asked_pricing: bool,
    asked_product: bool,
    order_complete: bool,
) -> str:
    """Rule-based lead scoring from conversation signals."""
    if order_complete:
        return "Converted"
    if has_phone and (has_name or has_address):
        return "Hot"
    if has_name or has_phone or has_address:
        return "Hot"
    if asked_pricing or asked_product:
        return "Warm"
    if message_count > 0:
        return "Cold"
    return "Cold"

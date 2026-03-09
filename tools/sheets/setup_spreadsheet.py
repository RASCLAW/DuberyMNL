"""
One-time setup: Create the DuberyMNL Master spreadsheet with all tabs and headers.
Also seeds the `brand` tab with DuberyMNL brand reference data.

Run once:
    python setup_spreadsheet.py

Prints the new GOOGLE_SHEETS_SPREADSHEET_ID to add to .env
"""

from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv(Path(__file__).parent.parent.parent / ".env")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = Path(__file__).parent.parent.parent / "credentials.json"
TOKEN_FILE = Path(__file__).parent.parent.parent / "token.json"


def get_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("sheets", "v4", credentials=creds)


SHEETS = {
    "captions": [
        "ID", "Generated_At", "Vibe", "Caption", "Hashtags",
        "Visual_Anchor", "Status", "Notes", "Rating"
    ],
    "images": [
        "ID", "Caption_ID", "Prompt", "Drive_URL", "Drive_File_ID",
        "Generated_At", "Status"
    ],
    "ad_drafts": [
        "ID", "Caption_ID", "Image_ID", "Drive_URL", "Campaign_ID",
        "Ad_Name", "Status", "Created_At", "Launched_At"
    ],
    "leads": [
        "Timestamp", "Name", "Phone", "Email", "Source",
        "PSID", "Status", "Notes"
    ],
    "brand": [
        "Key", "Value"
    ],
}

BRAND_DATA = [
    ["brand_name", "DuberyMNL"],
    ["facebook_page", "facebook.com/duberymnl"],
    ["product_type", "Sunglasses"],
    ["tagline", "Shades that fit your vibe"],
    ["single_price", "₱699"],
    ["bundle_price", "₱1,200 for 2 pairs"],
    ["pricing_rule", "Never mention ₱799. ₱699 is the hook. Delivery cost discovered at checkout."],
    ["never_say", "₱799, ₱1300, Free shipping, Nationwide, PM is key, Experience our polarized technology, anything corporate-sounding"],
    ["delivery", "COD only. Metro Manila only. Lalamove / Grab / MoveIt. Same-day or next-day."],
    ["language_ratio", "60% English / 40% Tagalog"],
    ["vibes", "commuter, outdoor, urban, lifestyle, mirror selfie, haircut, creator, motovlogger, moto camping, palenke, church, dog walking, cat parent, toddler/parent, teen/Gen Z, chaos energy, sale/urgency"],
    ["caption_quotas", "10 product-anchored, 5 bundle, 3 elevated tone per batch"],
    ["hashtags", "#DuberyMNL #PolarizedSunglasses #DuberyOptics #CODMetroManila #SameDayDelivery"],
    ["cta_phrases", "Order na, DM for orders, Grab yours, Available na, Message us, Order na ngayon, DM us now"],
    ["product_models", "Classic, Outback, Bandits, Rasta"],
    ["target_market", "PH, age 18-42, motorcycle riders, commuters, fashion-conscious"],
]


def create_spreadsheet(service):
    body = {
        "properties": {"title": "DuberyMNL Master"},
        "sheets": [{"properties": {"title": name}} for name in SHEETS],
    }
    spreadsheet = service.spreadsheets().create(body=body).execute()
    return spreadsheet["spreadsheetId"], spreadsheet["spreadsheetUrl"]


def seed_headers(service, spreadsheet_id: str):
    data = []
    for sheet_name, headers in SHEETS.items():
        data.append({
            "range": f"{sheet_name}!A1",
            "values": [headers],
        })
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"valueInputOption": "USER_ENTERED", "data": data},
    ).execute()


def seed_brand(service, spreadsheet_id: str):
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="brand!A2",
        valueInputOption="USER_ENTERED",
        body={"values": BRAND_DATA},
    ).execute()


def main():
    service = get_service()
    print("Creating DuberyMNL Master spreadsheet...")
    spreadsheet_id, url = create_spreadsheet(service)
    print(f"Created: {url}")

    print("Seeding headers...")
    seed_headers(service, spreadsheet_id)

    print("Seeding brand data...")
    seed_brand(service, spreadsheet_id)

    print("\nDone! Add this to your .env:")
    print(f"GOOGLE_SHEETS_SPREADSHEET_ID={spreadsheet_id}")


if __name__ == "__main__":
    main()

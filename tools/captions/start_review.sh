#!/bin/bash
# Starts the caption review server + ngrok tunnel.
# Run from the DuberyMNL project root:
#   bash tools/captions/start_review.sh

set -e
cd "$(dirname "$0")/../.."

# Kill any existing instances
pkill -f review_server.py 2>/dev/null || true
pkill -f "ngrok http" 2>/dev/null || true
sleep 1

# Start review server in background
source .venv/bin/activate
python tools/captions/review_server.py > .tmp/review_server.log 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
echo "Starting review server..."
for i in $(seq 1 10); do
  if curl -s http://localhost:5000 > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

# Start ngrok tunnel in background
ngrok http 5000 --log=stdout > .tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok to get a URL
echo "Starting ngrok tunnel..."
TUNNEL_URL=""
for i in $(seq 1 15); do
  TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys,json; t=json.load(sys.stdin).get('tunnels',[]); print(t[0]['public_url'] if t else '')" 2>/dev/null)
  if [ -n "$TUNNEL_URL" ]; then
    break
  fi
  sleep 1
done

if [ -z "$TUNNEL_URL" ]; then
  echo "ERROR: Could not get ngrok URL. Check .tmp/ngrok.log"
  exit 1
fi

echo ""
echo "========================================="
echo "  Review server is live!"
echo "  Open this on your phone:"
echo ""
echo "  $TUNNEL_URL"
echo "========================================="
echo ""

# Send email with the tunnel URL
python tools/captions/send_review_email.py \
  --count "$(python3 -c "
import os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('.env')
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
creds = Credentials.from_authorized_user_file('token.json')
svc = build('sheets', 'v4', credentials=creds)
res = svc.spreadsheets().values().get(spreadsheetId=os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID'), range='captions!A:G').execute()
rows = res.get('values', [])
headers = rows[0] if rows else []
idx = headers.index('Status') if 'Status' in headers else -1
print(sum(1 for r in rows[1:] if len(r) > idx and r[idx].upper() == 'PENDING'))
" 2>/dev/null || echo 0)" \
  --vibes "see sheet" \
  --url "$TUNNEL_URL" 2>/dev/null && echo "Email sent." || echo "Email send skipped (check .env)."

echo "Server PID: $SERVER_PID | ngrok PID: $NGROK_PID"
echo "Both will stop when you close this terminal or press Ctrl+C."
echo ""

# Keep script alive so Ctrl+C kills both
trap "kill $SERVER_PID $NGROK_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait $SERVER_PID

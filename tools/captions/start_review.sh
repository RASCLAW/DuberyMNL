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
PENDING_COUNT=$(python3 -c "
import json
from pathlib import Path
f = Path('.tmp/pipeline.json')
if not f.exists():
    print(0)
else:
    data = json.loads(f.read_text())
    print(sum(1 for c in data if c.get('status') == 'PENDING'))
" 2>/dev/null || echo 0)

VIBES=$(python3 -c "
import json
from pathlib import Path
f = Path('.tmp/pipeline.json')
if not f.exists():
    print('(none)')
else:
    data = json.loads(f.read_text())
    pending = [c for c in data if c.get('status') == 'PENDING']
    vibes = list(dict.fromkeys(c.get('vibe', '') for c in pending))
    print(', '.join(vibes))
" 2>/dev/null || echo "(unknown)")

python tools/captions/send_review_email.py \
  --count "$PENDING_COUNT" \
  --vibes "$VIBES" \
  --url "$TUNNEL_URL" 2>/dev/null && echo "Email sent." || echo "Email send skipped (check .env)."

echo "Server PID: $SERVER_PID | ngrok PID: $NGROK_PID"
echo "Both will stop when you close this terminal or press Ctrl+C."
echo ""

# Keep script alive so Ctrl+C kills both
trap "kill $SERVER_PID $NGROK_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait $SERVER_PID

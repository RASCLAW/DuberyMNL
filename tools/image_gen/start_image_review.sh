#!/bin/bash
# Starts the image review server + ngrok tunnel.
# Run from the DuberyMNL project root:
#   bash tools/image_gen/start_image_review.sh

set -e
cd "$(dirname "$0")/../.."

PORT=5001

# Kill any existing instances
pkill -f image_review_server.py 2>/dev/null || true
pkill -f "ngrok http $PORT" 2>/dev/null || true
sleep 1

# Count images ready for review
IMAGE_COUNT=$(python3 -c "
import json
from pathlib import Path
f = Path('.tmp/captions.json')
if not f.exists():
    print(0)
else:
    data = json.loads(f.read_text())
    print(sum(1 for c in data if c.get('status') == 'DONE'))
" 2>/dev/null || echo 0)

if [ "$IMAGE_COUNT" -eq 0 ]; then
  echo "No images ready for review (status=DONE). Run WF2b first."
  exit 0
fi

# Start review server in background
source .venv/bin/activate
python tools/image_gen/image_review_server.py > .tmp/image_review_server.log 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
echo "Starting image review server..."
for i in $(seq 1 10); do
  if curl -s http://localhost:$PORT > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

# Start ngrok tunnel in background
ngrok http $PORT --log=stdout > .tmp/image_review_ngrok.log 2>&1 &
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
  echo "ERROR: Could not get ngrok URL. Check .tmp/image_review_ngrok.log"
  exit 1
fi

echo ""
echo "========================================="
echo "  Image review server is live!"
echo "  $IMAGE_COUNT image(s) ready for review"
echo ""
echo "  Open on your phone:"
echo "  $TUNNEL_URL"
echo "========================================="
echo ""

# Send email notification
VIBES=$(python3 -c "
import json
from pathlib import Path
f = Path('.tmp/captions.json')
if not f.exists():
    print('(none)')
else:
    data = json.loads(f.read_text())
    done = [c for c in data if c.get('status') == 'DONE']
    vibes = list(dict.fromkeys(c.get('vibe', '') for c in done))
    print(', '.join(vibes))
" 2>/dev/null || echo "(unknown)")

python tools/captions/send_review_email.py \
  --count "$IMAGE_COUNT" \
  --vibes "$VIBES" \
  --url "$TUNNEL_URL" 2>/dev/null && echo "Email sent." || echo "Email send skipped (check .env)."

echo "Server PID: $SERVER_PID | ngrok PID: $NGROK_PID"
echo "Press Ctrl+C to stop."
echo ""

trap "kill $SERVER_PID $NGROK_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait $SERVER_PID

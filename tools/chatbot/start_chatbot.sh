#!/bin/bash
# Starts the DuberyMNL chatbot server + ngrok tunnel.
# Run from the DuberyMNL project root:
#   bash tools/chatbot/start_chatbot.sh

set -e
cd "$(dirname "$0")/../.."

PORT=5002

# Kill any existing instances
pkill -f messenger_webhook.py 2>/dev/null || true
pkill -f "ngrok http $PORT" 2>/dev/null || true
sleep 1

# Start chatbot server in background
source .venv/bin/activate
python tools/chatbot/messenger_webhook.py --port $PORT > .tmp/chatbot_server.log 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
echo "Starting chatbot server..."
for i in $(seq 1 10); do
  if curl -s http://localhost:$PORT/status > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -s http://localhost:$PORT/status > /dev/null 2>&1; then
  echo "ERROR: Server failed to start. Check .tmp/chatbot_server.log"
  exit 1
fi

# Start ngrok tunnel in background
ngrok http $PORT --log=stdout > .tmp/chatbot_ngrok.log 2>&1 &
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
  echo "ERROR: Could not get ngrok URL. Check .tmp/chatbot_ngrok.log"
  exit 1
fi

echo ""
echo "========================================="
echo "  DuberyMNL Chatbot is live!"
echo ""
echo "  Webhook URL (set this in Meta App):"
echo "  ${TUNNEL_URL}/webhook"
echo ""
echo "  Admin dashboard:"
echo "  ${TUNNEL_URL}/conversations"
echo ""
echo "  Health check:"
echo "  ${TUNNEL_URL}/status"
echo "========================================="
echo ""
echo "  Next steps:"
echo "  1. Go to developers.facebook.com"
echo "  2. App 908271865337799 > Messenger > Webhooks"
echo "  3. Set callback URL: ${TUNNEL_URL}/webhook"
echo "  4. Set verify token: (from MESSENGER_VERIFY_TOKEN in .env)"
echo "  5. Subscribe to: messages"
echo ""
echo "Server PID: $SERVER_PID | ngrok PID: $NGROK_PID"
echo "Press Ctrl+C to stop."
echo ""

trap "kill $SERVER_PID $NGROK_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait $SERVER_PID

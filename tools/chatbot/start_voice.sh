#!/bin/bash
# Start DuberyMNL Voice Assistant
# Requires: Chrome browser for speech recognition

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV="$PROJECT_DIR/.venv/bin/activate"

# Activate project venv
if [ -f "$VENV" ]; then
    source "$VENV"
fi

echo "================================================"
echo "  DuberyMNL Voice Assistant"
echo "  Open http://localhost:5003 in Chrome"
echo "  Press Ctrl+C to stop"
echo "================================================"

python "$SCRIPT_DIR/voice_server.py"

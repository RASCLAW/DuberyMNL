#!/bin/bash
# Watchdog for VSCode tunnel (dubery-dev)
# Checks every 5 minutes, restarts if dead

LOG=/tmp/tunnel-watchdog.log

echo "[$(date)] Watchdog started" >> "$LOG"

while true; do
  if ! pgrep -f "code-tunnel" > /dev/null; then
    echo "[$(date)] Tunnel down — restarting..." >> "$LOG"
    rm -f ~/.vscode/cli/tunnel-stable.lock
    nohup code-tunnel tunnel --name dubery-dev --accept-server-license-terms >> "$LOG" 2>&1 &
    sleep 5
    if pgrep -f "code-tunnel" > /dev/null; then
      echo "[$(date)] Tunnel restarted OK" >> "$LOG"
    else
      echo "[$(date)] Restart FAILED" >> "$LOG"
    fi
  fi
  sleep 300
done

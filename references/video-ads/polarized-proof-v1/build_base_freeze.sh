#!/usr/bin/env bash
set -euo pipefail
PROXY="/c/tmp/rev_dubery/build4k/proxy.mp4"
OUT="/c/tmp/rev_dubery/buildfreeze4"
PROJ="/c/Users/RAS/projects/hyperframes/dubery-polarized-proof-v1"
mkdir -p "$OUT"; cd "$OUT"
ENC="-c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p"
FMT="format=yuv420p"
test -f "$PROXY" || { echo "proxy missing"; exit 1; }
seg () { ffmpeg -hide_banner -loglevel error -y -i "$PROXY" -filter:v "$2" -an $ENC "$1.mp4"; }

# Natural 1x playback from the START (src 0.0).  PAUSE at exactly 3.0s (= src 3.0, naked beach, before the lens).
# z1: src 0.0->3.0 (1x) = comp 0-3.0  |  z2: FREEZE src 3.0 for 2.5s = comp 3.0-5.5  |  z3: RESUME src 3.0->27.5 (1x) = comp 5.5-30
seg z1 "trim=0.0:3.0,setpts=PTS-STARTPTS,fps=30,$FMT"
ffmpeg -hide_banner -loglevel error -y -ss 3.0 -i "$PROXY" -frames:v 1 freeze.png
ffmpeg -hide_banner -loglevel error -y -loop 1 -t 2.5 -i freeze.png -filter:v "setsar=1,fps=30,$FMT" $ENC z2.mp4
seg z3 "trim=3.0:27.5,setpts=PTS-STARTPTS,fps=30,$FMT"

rm -f concat.txt
for s in z1 z2 z3; do echo "file '$s.mp4'" >> concat.txt; done
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i concat.txt -c copy basefreeze4.mp4

echo "=== background.mp4 (4K, g10, 30s, 1x from 0.0, pause@3.0s for 2.5s) ==="
ffmpeg -hide_banner -loglevel error -y -i basefreeze4.mp4 \
  -c:v libx264 -crf 18 -preset medium -g 10 -keyint_min 10 -sc_threshold 0 -movflags +faststart -an \
  "$PROJ/background.mp4"
echo "=== DONE ==="
ffmpeg -hide_banner -i "$PROJ/background.mp4" 2>&1 | grep -E "Duration|not found" || true
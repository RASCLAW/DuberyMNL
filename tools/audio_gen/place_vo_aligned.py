"""
Place a single continuous TTS take onto beat timings by FORCED ALIGNMENT.

Why this exists: place_vo.py splits a one-take by picking the "longest pauses"
as line boundaries. That fails whenever the TTS voice doesn't pause consistently
between lines (common with Gemini voices like Kore/Erinome — they run several
lines together). This splitter instead transcribes the take with word-level
timestamps (faster-whisper, local, no API key) and cuts at each line's true
start — so ONE take (consistent tone) is split CORRECTLY regardless of pauses.

Each script line is matched to the transcript by its first 1-2 words (English
anchors are reliable even when Tagalog words mis-transcribe), searched in order.

Usage:
  python place_vo_aligned.py --take take.wav --lines take.txt \
      --starts 0.5,3.2,7.0,11.0,14.5,18.5,24.5 --total 30 --output vo.mp3
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def ffprobe_dur(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "default=noprint_wrappers=1:nokey=1", str(path)]).stdout.strip())


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def transcribe(path, model_size):
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(path), word_timestamps=True, language="en")
    words = []
    for seg in segments:
        for w in (seg.words or []):
            nw = norm(w.word)
            if nw:
                words.append((nw, w.start))
    return words


def line_starts(words, lines):
    """Return the take-time start of each line, matching first words in order."""
    starts, pos = [], 0
    for li, line in enumerate(lines):
        toks = [norm(t) for t in line.split() if norm(t)]
        a1 = toks[0]
        a2 = toks[1] if len(toks) > 1 else None
        found = None
        # try 2-gram anchor first, then 1-gram, searching only forward
        for i in range(pos, len(words)):
            if words[i][0] == a1 and (a2 is None or (i + 1 < len(words) and words[i + 1][0] == a2)):
                found = i
                break
        if found is None:  # fallback: 1-gram only
            for i in range(pos, len(words)):
                if words[i][0] == a1:
                    found = i
                    break
        if found is None:
            sys.exit(f"ERROR: could not align line {li+1} ('{line[:30]}...'). "
                     f"anchor '{a1} {a2 or ''}'. Transcript from pos {pos}: "
                     f"{' '.join(w for w, _ in words[pos:pos+12])}")
        starts.append(words[found][1])
        pos = found + 1
    return starts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--take", required=True)
    ap.add_argument("--lines", required=True, help="text file, one VO line per row")
    ap.add_argument("--starts", required=True, help="comma list of target beat starts (s)")
    ap.add_argument("--total", type=float, default=30.0)
    ap.add_argument("--output", required=True)
    ap.add_argument("--model", default="base", help="faster-whisper model size")
    args = ap.parse_args()

    lines = [ln.strip() for ln in Path(args.lines).read_text(encoding="utf-8").splitlines() if ln.strip()]
    targets = [float(x) for x in args.starts.split(",")]
    n = len(lines)
    if len(targets) != n:
        sys.exit(f"ERROR: {n} lines but {len(targets)} starts")

    dur = ffprobe_dur(args.take)
    words = transcribe(args.take, args.model)
    if not words:
        sys.exit("ERROR: transcript empty")
    cuts = line_starts(words, lines)
    # widen each cut slightly earlier to avoid clipping the first phoneme
    bounds = [max(0.0, c - 0.12) for c in cuts] + [dur]

    tmp = Path(tempfile.mkdtemp())
    trim = ("silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.03,"
            "areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.03,areverse")
    inputs, filters, labels, durs = [], [], [], []
    for i in range(n):
        a, b = bounds[i], bounds[i + 1]
        seg, segt = tmp / f"s{i}.wav", tmp / f"s{i}t.wav"
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", str(a), "-t", str(b - a),
             "-i", str(args.take), "-c:a", "pcm_s16le", str(seg)])
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(seg), "-af", trim, str(segt)])
        durs.append(ffprobe_dur(segt))
        inputs += ["-i", str(segt)]
        ms = int(round(targets[i] * 1000))
        filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[a{i}]")
        labels.append(f"[a{i}]")

    fc = (";".join(filters) + ";" + "".join(labels) +
          f"amix=inputs={n}:normalize=0:dropout_transition=0[m];"
          f"[m]apad=whole_dur={args.total},atrim=0:{args.total}[vo]")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
         "-filter_complex", fc, "-map", "[vo]", "-c:a", "libmp3lame", "-q:a", "2",
         "-ar", "48000", "-ac", "2", args.output])

    ok = True
    for i, (st, sd) in enumerate(zip(targets, durs)):
        end = st + sd
        nxt = args.total if i == n - 1 else targets[i + 1]
        flag = "" if end <= nxt + 0.05 else "  <-- OVERLAP"
        if flag:
            ok = False
        print(f"beat{i+1}: aligned@{cuts[i]:5.2f}s -> start {st:>5}s  dur {sd:5.2f}s  ends {end:5.2f}s{flag}")
    print(f"OUTPUT {args.output}  ({'fits' if ok else 'HAS OVERLAPS'})")


if __name__ == "__main__":
    main()

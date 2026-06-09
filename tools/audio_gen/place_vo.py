"""
Place a single continuous TTS take onto beat timings.

Why: generating each line as its own TTS call makes them sound like different
takes ("different people"). Instead, generate the WHOLE script in ONE take
(consistent voice), then this splits it at its longest inter-line pauses,
trims each line, and lays each at a given start time -> a 30s VO track.

Boundary detection: line breaks get longer pauses than mid-line sentence
breaks, so the (n-1) LONGEST interior silences are the line boundaries.

Usage:
  python place_vo.py --take full_take.wav \
      --starts 0.5,3.0,7.0,12.5,16.0,20.0,25.0 --total 30 --output vo.mp3
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


def detect_silences(path, noise, d):
    txt = run(["ffmpeg", "-hide_banner", "-i", str(path),
               "-af", f"silencedetect=n={noise}:d={d}", "-f", "null", "-"]).stderr
    starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", txt)]
    ends = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", txt)]
    return list(zip(starts, ends))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--take", required=True)
    ap.add_argument("--starts", required=True, help="comma list of beat start times (s)")
    ap.add_argument("--total", type=float, default=30.0)
    ap.add_argument("--output", required=True)
    ap.add_argument("--noise", default="-38dB")
    ap.add_argument("--d", type=float, default=0.18)
    args = ap.parse_args()

    starts = [float(x) for x in args.starts.split(",")]
    n = len(starts)
    dur = ffprobe_dur(args.take)

    # merge near-adjacent silence regions, keep only interior ones
    merged = []
    for s, e in detect_silences(args.take, args.noise, args.d):
        if merged and s - merged[-1][1] < 0.06:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    interior = [(s, e) for s, e in merged if s > 0.05 and e < dur - 0.05]

    if len(interior) < n - 1:
        print(f"ERROR: need {n-1} boundaries, found {len(interior)} interior silences. "
              f"Lower --d or raise --noise.", file=sys.stderr)
        sys.exit(1)

    # pick the (n-1) longest interior silences as line boundaries; cut at their midpoints
    boundaries = sorted((s + e) / 2 for s, e in
                        sorted(interior, key=lambda r: r[1] - r[0], reverse=True)[:n - 1])
    cuts = [0.0] + boundaries + [dur]

    tmp = Path(tempfile.mkdtemp())
    trim = ("silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.03,"
            "areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.03,areverse")
    inputs, filters, labels, seg_durs = [], [], [], []
    for i in range(n):
        a, b = cuts[i], cuts[i + 1]
        seg, segt = tmp / f"s{i}.wav", tmp / f"s{i}t.wav"
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", str(a), "-t", str(b - a),
             "-i", args.take, "-c:a", "pcm_s16le", str(seg)])
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(seg), "-af", trim, str(segt)])
        seg_durs.append(ffprobe_dur(segt))
        inputs += ["-i", str(segt)]
        ms = int(round(starts[i] * 1000))
        filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[a{i}]")
        labels.append(f"[a{i}]")

    fc = (";".join(filters) + ";" + "".join(labels) +
          f"amix=inputs={n}:normalize=0:dropout_transition=0[m];"
          f"[m]apad=whole_dur={args.total},atrim=0:{args.total}[vo]")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
         "-filter_complex", fc, "-map", "[vo]", "-c:a", "libmp3lame", "-q:a", "2",
         "-ar", "48000", "-ac", "2", args.output])

    ok = True
    for i, (st, sd) in enumerate(zip(starts, seg_durs)):
        end = st + sd
        nxt = args.total if i == n - 1 else starts[i + 1]
        flag = "" if end <= nxt + 0.05 else "  <-- OVERLAP"
        if flag:
            ok = False
        print(f"beat{i+1}: start {st:>5}s  dur {sd:5.2f}s  ends {end:5.2f}s{flag}")
    print(f"OUTPUT {args.output}  ({'fits' if ok else 'HAS OVERLAPS'})")


if __name__ == "__main__":
    main()

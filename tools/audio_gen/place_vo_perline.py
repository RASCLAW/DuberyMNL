"""
Build a timed VO track by generating each line as its OWN TTS call, then laying
each at a given start time. Use this as the FALLBACK when a one-take + place_vo.py
mis-splits because the chosen voice reads with even pacing (no clear inter-line
pauses) — common with some Gemini voices (e.g. Schedar, Kore).

Trade-off: separate calls can vary slightly in energy ("different people"), but
when the lines are seconds apart with ambient between them it is not noticeable.
For continuous/overlapping VO, prefer one-take + place_vo.py instead.

Each line is generated via generate_speech.py (so it honors --voice/--model/--style
and the VERTEX_PROJECT billing toggle), trimmed of lead/trail silence, then delayed
to its start and mixed. Prints a per-beat fit report (flags overlaps).

Usage:
  python place_vo_perline.py --lines take.txt --voice Schedar --brand \
      --starts 0.5,3.2,7.0,11.0,14.5,18.5,24.0 --total 30 --output vo.mp3
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

GEN = Path(__file__).with_name("generate_speech.py")
TRIM = ("silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.03,"
        "areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.03,areverse")


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def ffprobe_dur(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "default=noprint_wrappers=1:nokey=1", str(path)]).stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", required=True, help="text file, one VO line per row")
    ap.add_argument("--starts", required=True, help="comma list of beat start times (s)")
    ap.add_argument("--voice", required=True)
    ap.add_argument("--model", default="gemini-2.5-pro-preview-tts")
    ap.add_argument("--style", default=None)
    ap.add_argument("--brand", action="store_true", help="pass --brand to generate_speech.py")
    ap.add_argument("--total", type=float, default=30.0)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    lines = [ln.strip() for ln in Path(args.lines).read_text(encoding="utf-8").splitlines() if ln.strip()]
    starts = [float(x) for x in args.starts.split(",")]
    if len(lines) != len(starts):
        sys.exit(f"ERROR: {len(lines)} lines but {len(starts)} starts")
    n = len(lines)

    tmp = Path(tempfile.mkdtemp())
    inputs, filters, labels, durs = [], [], [], []
    for i, (line, st) in enumerate(zip(lines, starts)):
        raw, seg = tmp / f"l{i}.wav", tmp / f"l{i}t.wav"
        cmd = ["python", str(GEN), "--voice", args.voice, "--model", args.model,
               "--text", line, "--output", str(raw)]
        if args.style:
            cmd += ["--style", args.style]
        if args.brand:
            cmd += ["--brand"]
        r = run(cmd)
        if not raw.exists():
            sys.exit(f"ERROR generating line {i+1}: {r.stderr[-400:]}")
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw), "-af", TRIM, str(seg)])
        durs.append(ffprobe_dur(seg))
        inputs += ["-i", str(seg)]
        ms = int(round(st * 1000))
        filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[a{i}]")
        labels.append(f"[a{i}]")

    fc = (";".join(filters) + ";" + "".join(labels) +
          f"amix=inputs={n}:normalize=0:dropout_transition=0[m];"
          f"[m]apad=whole_dur={args.total},atrim=0:{args.total}[vo]")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
         "-filter_complex", fc, "-map", "[vo]", "-c:a", "libmp3lame", "-q:a", "2",
         "-ar", "48000", "-ac", "2", args.output])

    ok = True
    for i, (st, sd) in enumerate(zip(starts, durs)):
        end = st + sd
        nxt = args.total if i == n - 1 else starts[i + 1]
        flag = "" if end <= nxt + 0.05 else "  <-- OVERLAP"
        if flag:
            ok = False
        print(f"beat{i+1}: start {st:>5}s  dur {sd:5.2f}s  ends {end:5.2f}s{flag}")
    print(f"OUTPUT {args.output}  ({'fits' if ok else 'HAS OVERLAPS'})")


if __name__ == "__main__":
    main()

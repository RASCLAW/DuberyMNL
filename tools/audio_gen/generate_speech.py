"""
Generate speech with Gemini 2.5 TTS via Vertex AI generateContent.

Promptable delivery: a natural-language `--style` instruction controls tone
(e.g. "chill Filipino guy, make questions rise"). English-led Taglish works;
Tagalog words are pronounced natively (no phonetic respelling needed).

Bills VERTEX_PROJECT (default `dubery`) via ADC -- same creds/pool as
generate_music.py (Lyria). Output is 24kHz mono 16-bit PCM wrapped as WAV.

Usage:
    python generate_speech.py --text "Hello po" --voice Puck --output out.wav
    python generate_speech.py --text "..." --style "chill, rising questions" --voice Charon --output out.wav

Voices (prebuilt): Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, Zephyr,
    Algenib, Algieba, Achird, Schedar, ... (see Vertex Gemini TTS docs).
Models: gemini-2.5-flash-preview-tts (cheap) | gemini-2.5-pro-preview-tts.
"""
import argparse
import base64
import json
import os
import re
import sys
import wave
from pathlib import Path

from dotenv import load_dotenv
import google.auth
from google.auth.transport.requests import AuthorizedSession

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")
DEFAULT_LOCATION = os.getenv("VERTEX_TTS_LOCATION", "us-central1")

# Dubery Manila approved ad voices (RA-approved 2026-06-15), all on the Pro TTS
# model with the chill warm-confident read (--brand). Umbriel is the primary
# default; the others are approved alternates (e.g. female read, male narrator).
# Script rule: write the brand as "Dubery Manila", never "DuberyMNL" (TTS spells
# M-N-L letter by letter).
DUBERY_VOICES = {
    "Umbriel": "easy-going male (PRIMARY)",
    "Schedar": "even male",
    "Kore": "firm female",
    "Erinome": "clear female",
}
DUBERY_VOICE = "Umbriel"
DUBERY_MODEL = "gemini-2.5-pro-preview-tts"
DUBERY_STYLE = (
    "Chill, friendly Filipino guy. Warm and confident, like you're recommending "
    "shades to a close friend. Natural relaxed pacing, let the questions rise a little."
)


def synth(text, voice="Puck", style=None,
          model="gemini-2.5-flash-preview-tts", location=DEFAULT_LOCATION):
    project = os.getenv("VERTEX_PROJECT", "dubery")
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    session = AuthorizedSession(creds)
    host = "aiplatform.googleapis.com" if location == "global" else f"{location}-aiplatform.googleapis.com"
    url = (f"https://{host}/v1/projects/{project}/locations/{location}"
           f"/publishers/google/models/{model}:generateContent")

    prompt = f"{style}\n\n{text}" if style else text
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }

    print(f"Gemini TTS {model} voice={voice} project={project} loc={location}", file=sys.stderr)
    resp = session.post(url, json=body, timeout=300)
    if resp.status_code != 200:
        print(f"ERROR {resp.status_code}: {resp.text[:800]}", file=sys.stderr)
        sys.exit(2)

    data = resp.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        ap = next(p for p in parts if "inlineData" in p)
        b64 = ap["inlineData"]["data"]
        mime = ap["inlineData"].get("mimeType", "audio/L16;rate=24000")
    except (KeyError, IndexError, StopIteration):
        print(f"ERROR: no audio in response: {json.dumps(data)[:800]}", file=sys.stderr)
        sys.exit(3)

    m = re.search(r"rate=(\d+)", mime)
    rate = int(m.group(1)) if m else 24000
    return base64.b64decode(b64), rate


def write_wav(pcm, rate, out):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)


def main():
    ap = argparse.ArgumentParser(description="Gemini 2.5 TTS via Vertex AI")
    ap.add_argument("--text")
    ap.add_argument("--voice", default=DUBERY_VOICE)
    ap.add_argument("--style", default=None)
    ap.add_argument("--model", default=DUBERY_MODEL)
    ap.add_argument("--location", default=DEFAULT_LOCATION)
    ap.add_argument("--brand", action="store_true",
                    help="Apply the locked Dubery Manila ad-voice style (if --style not given)")
    ap.add_argument("--list-voices", action="store_true",
                    help="Print the approved Dubery Manila voice roster and exit")
    ap.add_argument("--output")
    args = ap.parse_args()

    if args.list_voices:
        print("Approved Dubery Manila voices (Pro TTS, --brand style):")
        for name, desc in DUBERY_VOICES.items():
            print(f"  {name:<14} {desc}")
        return
    if not args.text or not args.output:
        ap.error("--text and --output are required (unless --list-voices)")

    style = args.style or (DUBERY_STYLE if args.brand else None)
    pcm, rate = synth(args.text, args.voice, style, args.model, args.location)
    write_wav(pcm, rate, args.output)
    print(json.dumps({"success": True, "output": args.output, "rate": rate, "bytes": len(pcm)}))


if __name__ == "__main__":
    main()

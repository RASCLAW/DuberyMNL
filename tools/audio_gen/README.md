# audio_gen — AI music + voiceover for DuberyMNL (Vertex AI)

**What it does**
- **Music:** royalty-free instrumental from a text prompt via Lyria on Vertex AI — ad-safe scoring (no Meta copyright takedown).
- **Voiceover:** Filipino/Taglish narration via **Gemini 2.5 TTS** on Vertex AI — promptable delivery (you instruct the tone), natural Tagalog (no phonetic hacks).

**Key files**

| Script | Purpose |
|---|---|
| `generate_music.py` | Calls the Vertex AI Lyria `:predict` endpoint. Text prompt → 48kHz WAV instrumental clip. Saves to `contents/new/` (or `--output`). Reads `VERTEX_PROJECT` for the billing toggle. |
| `generate_speech.py` | Gemini 2.5 TTS (`gemini-2.5-flash-preview-tts`) via Vertex `:generateContent`. `--text`/`--style`/`--voice` → 24kHz mono WAV. Promptable tone; native Taglish. Same ADC/`VERTEX_PROJECT` as Lyria. Pennies/clip. |
| `place_vo.py` | Takes ONE continuous TTS take + a list of beat start times, auto-splits it at the longest inter-line pauses, trims each line, and lays each at its start → a timed VO track (mp3). Solves the "different people" effect from per-line TTS calls. |

**Run**

```sh
python tools/audio_gen/generate_music.py --prompt "warm tropical lo-fi, upbeat, relaxed" --output contents/new/track.wav
python tools/audio_gen/generate_music.py --prompt "..." --model lyria-002 --negative-prompt "vocals, lyrics" --seed 7

# voiceover: generate ONE consistent take, then split+place onto beat times
python tools/audio_gen/generate_speech.py --voice Achird --style "chill Filipino guy, rising questions, honor '...' pauses" --text "$(cat script.txt)" --output take.wav
python tools/audio_gen/place_vo.py --take take.wav --starts 0.5,3.0,7.0,9.5,13.0,17.0,23.5 --total 30 --output vo.mp3
```

**Voiceover (Gemini TTS) — notes**
- Generate the WHOLE script in ONE call (one performance) — per-line calls sound like different people. `place_vo.py` then splits on the longest pauses and re-times each line.
- Promptable: the `--style` instruction controls tone (e.g. force a rising question — edge-tts can't). Voices: Achird (friendly), Zubenelgenubi (casual), Umbriel, Puck, Charon… (`--voice`).
- Confirmed: `gemini-2.5-flash-preview-tts` **works via Vertex `:generateContent` with our ADC** on project `dubery` (us-central1) — despite the Lyria note below about generate_content; TTS returns base64 PCM (24kHz mono) wrapped to WAV.
- Used for the polarized-proof ad VO; full recipe in DuberyMNL memory `reference_free_taglish_vo_edge_tts`.

**Models / pricing** (per the Vertex AI pricing page)
- `lyria-002` (Lyria 2) — $0.06 / 30s clip (~32.8s, 48kHz WAV). **Confirmed working** (us-central1, `:predict`).
- `lyria-3-clip-preview` (Lyria 3) — $0.04 / 30s clip. **PREVIEW-GATED:** in the catalog but both DuberyMNL accounts returned 404 "project does not have access" (2026-05-31). Needs Model Garden access granted before use.
- `lyria-3-pro-preview` (Lyria 3 Pro) — $0.08 / full song up to 3 min, accepts **image input** for mood. Same preview gating.

> Lyria 3 is NOT a `generate_content` model on Vertex (that 404s) — it uses the same `:predict` endpoint as `lyria-002`. The `generate_content`/`response_modalities` form is the separate **Gemini API** (ai.google.dev) surface, which bills outside the Vertex trial credits.

**Auth / env**
- Uses Application Default Credentials (same as `generate_vertex.py`). Billing project from `VERTEX_PROJECT` (default `dubery`); set it + `GOOGLE_APPLICATION_CREDENTIALS` to bill the $300 trial account. See DuberyMNL memory `reference_vertex_billing_toggle.md`.
- Uses a `requests`-based `AuthorizedSession` (not httplib2), so it sidesteps the laptop's IPv6 Google-API hang.

**Gotchas**
- `--seed` and the internal `sample_count` are mutually exclusive (Lyria API constraint) — passing a seed drops sample_count.
- Output is **instrumental only** (no vocals/lyrics) — use `--negative-prompt "vocals, lyrics"` to reinforce.
- Endpoint is `us-central1` only.
- **Recitation filter:** a `400 "All responses were blocked by recitation checks"` means the output resembled copyrighted/training music — common with iconic genres (punk, classic-rock riffs). Fix: add "original / fresh melody" to the prompt, `--negative-prompt "famous song, cover"`, and a `--seed`, then retry. 400s don't bill, so retries are free.

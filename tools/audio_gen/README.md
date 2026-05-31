# audio_gen — AI music generation for DuberyMNL (Lyria on Vertex AI)

**What it does**
- Generates royalty-free instrumental music from a text prompt via Google's Lyria models on Vertex AI — for scoring video ads / animated carousels with owned, ad-safe audio (no copyright-takedown risk on Meta).

**Key files**

| Script | Purpose |
|---|---|
| `generate_music.py` | Calls the Vertex AI Lyria `:predict` endpoint. Text prompt → 48kHz WAV instrumental clip. Saves to `contents/new/` (or `--output`). Reads `VERTEX_PROJECT` for the billing toggle. |

**Run**

```sh
python tools/audio_gen/generate_music.py --prompt "warm tropical lo-fi, upbeat, relaxed" --output contents/new/track.wav
python tools/audio_gen/generate_music.py --prompt "..." --model lyria-002 --negative-prompt "vocals, lyrics" --seed 7
```

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

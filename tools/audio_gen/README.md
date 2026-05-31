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
- `lyria-002` (Lyria 2) — $0.06 / 30s clip (~32.8s, 48kHz WAV). **Confirmed working.**
- Lyria 3 / Lyria 3 Pro — public preview; $0.04 / 30s clip and $0.08 / full song (up to 3 min, accepts image input). Model IDs to confirm before use.

**Auth / env**
- Uses Application Default Credentials (same as `generate_vertex.py`). Billing project from `VERTEX_PROJECT` (default `dubery`); set it + `GOOGLE_APPLICATION_CREDENTIALS` to bill the $300 trial account. See DuberyMNL memory `reference_vertex_billing_toggle.md`.
- Uses a `requests`-based `AuthorizedSession` (not httplib2), so it sidesteps the laptop's IPv6 Google-API hang.

**Gotchas**
- `--seed` and the internal `sample_count` are mutually exclusive (Lyria API constraint) — passing a seed drops sample_count.
- Output is **instrumental only** (no vocals/lyrics) — use `--negative-prompt "vocals, lyrics"` to reinforce.
- Endpoint is `us-central1` only.

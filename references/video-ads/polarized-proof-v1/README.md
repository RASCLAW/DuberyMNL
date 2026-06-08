# Polarized-Proof Video Ad (v1) — source

DuberyMNL 30s 9:16 video ad (Bandits Tortoise) built with **HyperFrames** (HTML/GSAP → MP4). Session 216 (2026-06-09). Final render delivered to `Downloads/dubery-polarized-proof-v7.mp4`.

This folder preserves the **recreatable source only** (small files). The large media (background.mp4, audio.mp3, renders/*.mp4) live locally in the working project and are NOT in git.

## Files
- `index.html` — the HyperFrames composition (copy, GSAP timeline, typewriter, freeze timing, lens-clear text bands). This is the creative source of truth.
- `assets/fonts/*.woff2` — Clash Display + Satoshi (Fontshare, embedded via @font-face).
- `build_base_freeze.sh` — ffmpeg script that cuts the 4K `background.mp4` from the source clip (natural 1x from src 0.0, freeze @ comp 3.0s for 2.5s, seamless resume). Source clip: `VID_20260607_134620.mp4` (RA's vertical beach + lens demo).
- `polarized-proof-ad-spec.md` — the locked creative spec/brief.

## To rebuild / re-render
Working project: `~/projects/hyperframes/dubery-polarized-proof-v1/`.
1. Run `build_base_freeze.sh` (needs the 4K proxy of the source clip) → writes `background.mp4`.
2. Make `audio.mp3` = 30s ambient bed looped from the source clip.
3. `npx hyperframes preview` (Studio @ localhost:3002) to edit; `npx hyperframes render -q high -f 30 -o renders/out.mp4` to render.

## Gotchas (see memory `reference_hyperframes_video_ad_pipeline`)
- HyperFrames needs **ffprobe** (installed at Python312\Scripts).
- NEVER animate `filter`/`transform` on the `<video>` layer → black frames. Static video + overlay-div grade/bloom.
- Keep text off the lens (lens ~35–68% height) — top/bottom bands only.
- Freeze: bake into the footage; freeze frame's source-time MUST equal the resume segment's start.
- Don't render while the bg encode is still writing (truncated → black).

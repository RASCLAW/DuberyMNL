# Dubery — "Look Again" Polarized-Proof Ad — LOCKED BUILD SPEC

**Status:** LOCKED (2026-06-08). Fast hook confirmed by RA.
**Type:** Proof-of-claim product demonstration (NOT avatar-angled). Job = make the polarized claim undeniable → trust.
**Format:** 9:16, 1080×1920, **15.0s** (extends to ~20s — see §7).
**SKU:** Dubery **Bandits Tortoise** (brown-red mottled frame, non-mirrored brown/bronze polarized lens).
**Source footage:** `C:\Users\RAS\Downloads\VID_20260607_134620.mp4` (native 9:16, 4K, ~27.7s, 29.92fps, original ambient audio).
**Hero still (backup/end-card option):** `C:\Users\RAS\Downloads\Screenshot_20260607_230518_...jpg`
**Audio:** ORIGINAL ambient beach bed, continuous 1x (kept per RA). No VO. Optional reveal whoomph = OFF by default.
**Voice:** English-led, 2 Taglish punches.

---

## 1. Retention logic (why it's built this way)
- Reveal lands by ~3s (intro-retention is the #1 algo signal; aim 70%+ past 3s).
- 15s target (sub-15s ads complete ~53% more than longer).
- Brand/lens readable early (not just end card) → ~40% higher view-through.
- "Show the reveal twice" (0.4s replay) — brain wants to re-see the satisfying moment.
- Final frame echoes the opening → loopable → more watch time.

## 2. Build = 2 phases
**Phase A — base edit (ffmpeg):** trim + speed-ramps + punch-in + light grade → `base_edit.mp4` (1080×1920).
Audio handled separately: extract a continuous 15s ambient slice at 1x as the bed (ambient doesn't need sync, so ramped visuals over a 1x bed sound natural).
**Phase B — HyperFrames overlay pass:** `base_edit.mp4` as background `<video>` (1x) + ambient bed + GSAP overlay timeline → final 1080×1920 render.
> Alt: do the whole thing in HyperFrames by scrubbing `video.currentTime` from the GSAP timeline (frame-accurate ramps/freezes) and laying the 1x ambient bed as a separate audio track. Either path; Phase-A-then-B is simpler to debug.

## 3. Master timeline (15.0s)
| Shot | Time | Screen dur | Beat |
|------|------|-----------|------|
| 1 | 0.00–2.00 | 2.0s | Hook (naked-eye + arrow) |
| 2 | 2.00–3.20 | 1.2s | Lens-mask reveal (the snap) |
| 3 | 3.20–3.60 | 0.4s | Replay of the wipe |
| 4 | 3.60–7.50 | 3.9s | Proof beat (punch-in + A/B) |
| 5 | 7.50–11.50 | 4.0s | Benefit stack (3 fast lines) |
| 6 | 11.50–13.00 | 1.5s | Settle |
| 7 | 13.00–15.00 | 2.0s | CTA / offer (loops to shot 1) |

## 4. Background video map (source-sec → timeline-sec)
Frame refs use the 2fps proxy: `g_NNN ≈ (NNN-1)×0.5s` of source.
| Shot | Source in→out | Timeline | Speed / move |
|------|---------------|----------|--------------|
| 1 | 3.4 → 4.9 | 0.0–2.0 | 0.75x slow; naked-eye clean (≈g_007–g_010) |
| 2 | 5.5 → 7.5 | 2.0–3.2 | 1.67x fast — shades drop in from top (g_012→g_016) |
| 3 | 7.5 → 6.7 | 3.2–3.6 | reverse replay of the wipe |
| 4 | 9.0 → 10.2 | 3.6–7.5 | 0.31x slow on centered lens (g_019–g_021) + **digital punch-in 1.0→1.8x**, origin = lens center |
| 5a | 11.5 → 13.0 | 7.5–8.83 | pan beat (g_024) |
| 5b | 14.5 → 16.0 | 8.83–10.17 | pan beat (g_030) |
| 5c | 19.0 → 20.5 | 10.17–11.5 | pan beat (g_039) |
| 6 | 24.5 → 25.7 | 11.5–13.0 | settle on open sea (g_050–g_052) |
| 7 | freeze @ ~4.5 | 13.0–15.0 | opening-echo frame, gentle 1.03x drift |
**Audio bed:** original audio `3.0 → 18.0` (continuous 15s, 1x) under everything.

## 5. Copy (LOCKED)
- **Shot 1:** `Your eyes are working overtime.` — animated arrow points at the water glare.
- **Shot 2:** (no new text — hook text resolves on the wipe; let the visual breathe)
- **Shot 4:** `That's real polarized.` → swap → `Brown lens. Deeper color. Zero glare.` + A/B labels: `HAZE` (outside lens) ↔ `CLARITY` (inside lens)
- **Shot 5:** `No squint.` · `Colors, back.` · `Ang gaan — parang wala kang suot.` *(Taglish punch)*
- **Shot 6:** `See summer for real.`
- **Shot 7:** `DUBERY` · `Bandits Tortoise` · `₱499 · COD nationwide` · `duberymnl.com` (optional micro-CTA: `I-COD mo na.`)

## 6. Motion + type (non-basic — GSAP/CSS, Tailwind v4 runtime)
**Fonts (free, premium — NOT Anton/Bebas):**
- Headlines: **Clash Display** (Fontshare) — Semibold/Bold.
- Support/labels: **Satoshi** (Fontshare).
- No script fonts (confident, not cute).

**Treatments:**
- **Blur-resolve** (the signature): text from `{filter:blur(14px), opacity:0, scale:1.04, saturate:0.2}` → `{blur(0), opacity:1, scale:1, saturate:1}`, `power3.out`, 0.5s, char-stagger 0.02. The type performs "haze→clarity." Shot-1 hook stays *slightly unresolved/hazy* until the shot-2 wipe, then snaps fully sharp+saturated.
- **Lens-mask wipe** (shot 2): rich layer revealed through an animated lens-shaped `clip-path` (rounded-rect/ellipse) tracking the real lens; radius/scale 0→full, `power4.inOut`, ~0.6s.
- **Punch-in** (shot 4): video `scale 1.0→1.8`, `transform-origin` at lens center, `power2.inOut`, eased over the full 3.9s (slow, camera-like).
- **A/B labels** (shot 4): two pills slide in via `clip-path` inset; `HAZE` muted grey, `CLARITY` warm white.
- **Benefit swaps** (shot 5): one line at a time, in `back.out(2)` scale-pop 0.4s / out `power2.in`; hard cuts land on footage motion.
- **Replay** (shot 3): GSAP timeline reverse on the wipe segment, 0.4s.
- **CTA** (shot 7): logo + SKU scale-pop; offer line blur-resolves; final frame matches opening.

**Grade (honest, subtle):** shot-1 naked-eye gets slight desaturate + bloom + lifted blacks to emphasize the already-present wash-out. In-lens footage stays as-shot (rich). Direction is real; we're not inventing the effect.

**Legibility:** white type, soft dark scrim/long-shadow only where it crosses bright sand/sky. Safe margins: keep text within center 84% (TikTok/Reels UI gutters).

## 7. Extend to ~20s
Add 2 benefit cuts in shot 5: `All-day light.` + a comfort/wear gesture beat (`So light you'll forget them.`). Footage supports it (g_044–g_048).

## 8. Open / honesty note
Phone camera auto-exposes for the bright surroundings, so the in-lens contrast reads a touch stronger than the naked eye sees — but the effect is real (brown polarized genuinely warms + de-hazes + boosts contrast). Defensible if questioned; do not over-claim beyond "polarized."

## 9. Next actions
1. Phase A: cut `base_edit.mp4` per §4 (ffmpeg) + ambient bed.
2. `/hyperframes` init a `dubery-polarized-proof-v1` composition; build overlays per §5–6.
3. Preview → render 1080×1920 → review on phone.
4. Promote this spec + assets out of `.tmp` into the hyperframes project on build.

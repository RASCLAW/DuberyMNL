# Content-Gen Lesson: Storyboard-Driven Multi-Image Generation

*Captured 2026-05-28. Conversation between RA and the Command Center content agent during the "Anatomy of a Bandit" bespoke image series. Saved because the back-and-forth surfaces a reusable principle for generating multiple images that stay **different-but-coherent** instead of templated.*

> Distilled lesson lives in memory: `feedback_storyboard_driven_multi_image.md`. Related: `feedback_bespoke_concept_paste_wins.md`, `reference_cc_bespoke_pipeline.md`.

---

## The arc of the conversation

1. **Single image, dark-premium treatment.** RA: use Bandits Black, dark backdrop, heavy lighting for premium vibe, and fix the infographic — replace the obvious labels (NOSE PADS / TEMPLE / LENS / HINGES). Agent shipped "ANATOMY OF A BANDIT / CHAPTER 01" with brand-flavored labels (PRECISION FIT / INNER PRINT / PRIZM RUBY / STEEL HINGE).

2. **"Create 6 variations."** Agent did 6 (CH02–CH07) varying lens (35/50/85/100/135mm), angle, lighting, label sets.

3. **RA: "most look similar in angles."** Because the prodref locks rotation — varying *lens* doesn't change the shot much. Agent's fix: zoom into different *regions* (LENS / BRIDGE / INNER PATTERN / FRONT / HINGE / CORNER) so each frame is a distinct "study." Shipped CH08–CH13.

4. **RA: "only use 4 lines when it feels right — some images need 1 or 2."** Forcing 4 labels on every frame makes the set feel templated. Agent re-did with **composition decides label count** (CH14–CH19): 1 / 2 / 3 / 4 / 2 / 1.

5. **RA's key catch: "do you realize you're generating the same prompt?"** Agent admitted: across the last 6 prompts it rewrote the same ~50 lines with a few-line diff each. Identical 6×: `product_fidelity` block, `interaction_physics`, the dark-vibe preamble, typography scaffolding, render-quality block, the no-NOSE-PADS guardrail. Only the state paragraph, label list, lighting phrase, chapter number, and pill-count rule actually changed. Cost: token waste, diffs hidden inside walls of duplicated text, and the model attending to repeated scaffolding instead of the small unique parts.

6. **RA's directive: be disciplined, and build a storyboard.** "Create a story or storyboard to follow when generating multiple images so that all images stay different and similar but not the same."

7. **Agent's response — the process that should become default:**
   - **Write the arc first** (1 line per card, before any prompt JSON). Each card gets a JOB: Hook / Curiosity / Proof / Function / Emotion / Close.
   - **Map each beat to a visual treatment** (zoom region + lighting direction + label count + 1–3 word copy).
   - **Build prompts from a shared template** — 80% shared scaffolding, only the deltas vary.
   - **Review the set as a set** before approving. Does each card earn its slot? Cut redundant ones.

8. **Approved storyboard ("ANATOMY OF A BANDIT — Vol. 1", 6-card 1:1):**

   | # | Beat | Card | Labels | Copy job |
   |---|------|------|--------|----------|
   | 01 | HOOK | Cover hero, 3/4, side-key | 0 (title card) | Establish the mood |
   | 02 | CURIOSITY | Macro on inner-arm print | 1 ("WHAT THEY DON'T SEE") | Reveal the secret detail |
   | 03 | PROOF | Joint/hinge macro | 2 (FOLD POINT / ARM RUNNER) | Engineering shown, not told |
   | 04 | FUNCTION | Right lens macro | 2 (PRIZM RUBY / POLARIZED CORE) | What it does for your eyes |
   | 05 | SHOWCASE | Symmetric front-on | 4 (MATTE BROW / MIRROR TWIN / RUBY GLOW / BRIDGE BAR) | The complete reveal |
   | 06 | CLOSE | Edge abstract, corner | 1 ("CUT WITH INTENT") | Brand punctuation |

   **Why the arc works:** rhythm goes QUIET → BUSY → QUIET (0 → 1 → 2 → 2 → 4 → 1), so the eye gets to rest. Cards 1 and 6 bookend the set (both quiet, dark-heavy). Card 5 is the only 4-label frame, so it earns "centerpiece." Each card answers a *different* question — no redundancy.

9. **Built + shipped.** Builder at `.tmp/build_bandit_vol1.py` — one file holds the storyboard (`CARDS` list) plus shared scaffolding (~200 lines total instead of 6×50 duplicated). Per-card only `state`, `lighting_direction_full`, `subject_placement`, `labels`, `camera_settings`, `mood` vary. **Zero 429s** on the run (cleaner prompts may help; possibly coincidence). The QUIET/BUSY/QUIET rhythm landed.

---

## Proposed tool: `bespoke_series_builder.py`

Does for *any* bespoke series what `build_bandit_vol1.py` did for one — generalizes the storyboard pattern so the scaffolding is never rewritten. Three layers it abstracts:

1. **SERIES config** — the "world" of the carousel: `product_id` (auto-loads prodref + spec), `series_title`, `volume`, `treatment` (a named visual-mood preset — `dark_luxe`, `cream_editorial`, `neon_grit` — that bundles background + pill style + typography), `aspect_ratio`.
2. **CARD list** — the storyboard beats, same shape as today: `id`, `beat`, `subtitle`, `prodref`, `state`, `lighting`, `labels[]`, `camera`, `mood`. Validates label count vs. position strings.
3. **OUTPUT** — emits prompts + configs; `--generate` flag runs `generate_vertex.py` sequentially with built-in 429 retry; writes a `series.json` sidecar with the full storyboard for reproducibility.

Invocation:
```
# Build prompts only (review first)
python tools/image_gen/bespoke_series_builder.py .tmp/series_anatomy_rasta_red.py
# Build + generate the full carousel
python tools/image_gen/bespoke_series_builder.py .tmp/series_anatomy_rasta_red.py --generate
```
…where `series_anatomy_rasta_red.py` is ~30 lines: import builder + treatment preset, declare the SERIES dict + CARDS list.

Hardcoded today → knob after:

| Today (`build_bandit_vol1.py`) | After (`bespoke_series_builder.py`) |
|---|---|
| Product fidelity block | Auto-loaded from `product-specs.json` |
| "deep charcoal-black studio background…" | One of 3–5 named treatment presets |
| Pill style hardcoded mustard-gold | Part of the treatment preset |
| Headline scaffolding hardcoded | Treatment preset (color/font character) |
| Guardrail words ("no NOSE PADS…") | Treatment-aware per concept |
| Series-specific (Bandit-only) | Series-agnostic |

**Design call (agent's take = lightweight + hybrid skill on top):**
- **Lightweight (recommended):** series configs as small `.py` files — plain Python, autocomplete, easy to fork per product. No YAML magic.
- **Heavy:** YAML configs + CLI args. More "production-grade" but adds friction for creative iteration.
- **Hybrid:** a `/dubery-bespoke-series` skill that prompts the agent to write the storyboard in markdown, gets approval, then compiles to a series config. The discipline lives in the storyboard step, not the tooling — the skill enforces *write storyboard → approve → build → generate*.

**Open decision:** build now, or hold until 2–3 series exist and the abstraction is obvious. (Agent leaned toward waiting for the pattern to prove itself across more products.)

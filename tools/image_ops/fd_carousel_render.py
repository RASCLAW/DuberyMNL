"""Render the DuberyMNL Father's Day "Kill the Glare" Hormozi carousel.

Six 1080x1080 cards composited from generated/reused base photos + crisp HTML
text (rendered via Playwright at 2x then downscaled, so type stays sharp).

Type/colour is THEME-driven (real typefaces, not Windows Impact -- which reads
as the default AI/meme look). Pick a theme with --theme:
  editorial : Playfair Display serif + champagne gold  (luxury eyewear)
  modern    : Bebas Neue condensed   + warm sand        (clean DTC)
  bold      : Archivo Black grotesque + deep terracotta  (confident)

Usage:
    python tools/image_ops/fd_carousel_render.py --batch 1 --theme editorial
    python tools/image_ops/fd_carousel_render.py --sample   # 3 themes x 2 cards -> .tmp
"""
import argparse
import base64
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

PROJECT = Path(__file__).parent.parent.parent
OUT_DIRS = {1: PROJECT / "contents" / "new" / "fdhz-cards",
            2: PROJECT / "contents" / "new" / "fdhz-cards-2",
            3: PROJECT / "contents" / "new" / "fdhz-cards-sku",
            4: PROJECT / "contents" / "new" / "fdhz-cards-sku2"}
FONT_DIR = PROJECT / "contents" / "assets" / "fonts" / "google"
LOGO = PROJECT / "contents" / "assets" / "logos" / "logo-header.png"

SIZE = 1080
SCALE = 2

# ---- Themes: font + palette -------------------------------------------------
# disp = display/headline face; sizes hand-tuned per face metrics.
THEMES = {
    "editorial": {
        "disp": "playfair", "disp_wt": 800, "case": "none",
        "accent": "#C9A24B", "head": 82, "ls": "0px", "lh": "1.0",
        "wordmark_wt": 700,
    },
    "modern": {
        "disp": "bebas", "disp_wt": 400, "case": "uppercase",
        "accent": "#E6B469", "head": 112, "ls": "1.5px", "lh": "0.9",
        "wordmark_wt": 700,
    },
    "bold": {
        "disp": "archivo", "disp_wt": 400, "case": "uppercase",
        "accent": "#D2552B", "head": 74, "ls": "-1px", "lh": "0.98",
        "wordmark_wt": 800,
    },
}
GREEN = "#1FA94A"
DARK = "#0F0F0F"

FONT_FILES = {
    "playfair": "PlayfairDisplay.ttf",   # variable
    "bebas": "BebasNeue-Regular.ttf",
    "archivo": "ArchivoBlack-Regular.ttf",
    "mont": "Montserrat.ttf",            # variable -- body/sub/wordmark
}


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def data_uri(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    return f"data:{mime};base64,{b64(path)}"


def font_face_css() -> str:
    faces = []
    for fam, fn in FONT_FILES.items():
        rng = "font-weight:100 900;" if fn.endswith(".ttf") and fam in ("playfair", "mont") else ""
        faces.append(f"@font-face{{font-family:'{fam}';src:url(data:font/ttf;base64,"
                     f"{b64(FONT_DIR/fn)}) format('truetype');{rng}}}")
    return "\n".join(faces)


def resolve(prefix: str) -> Path:
    cands = sorted((PROJECT / "contents" / "new").glob(f"*{prefix}*.png"))
    if not cands:
        cands = sorted((PROJECT / "contents" / "new").glob(f"*{prefix}*.jpg"))
    if not cands:
        raise FileNotFoundError(f"no base image matching *{prefix}* in contents/new")
    return cands[0]


def build_css(t: dict) -> str:
    return f"""
{font_face_css()}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:{SIZE}px;height:{SIZE}px;overflow:hidden;}}
.card{{position:relative;width:{SIZE}px;height:{SIZE}px;background:{DARK};
  font-family:'mont',sans-serif;color:#fff;overflow:hidden;}}
.bg{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;}}
.scrim{{position:absolute;inset:0;background:linear-gradient(to bottom,
  rgba(0,0,0,.30) 0%,rgba(0,0,0,0) 28%,rgba(0,0,0,0) 44%,rgba(0,0,0,.80) 100%);}}
.hdr{{position:absolute;top:38px;left:40px;right:40px;display:flex;
  justify-content:space-between;align-items:center;z-index:5;}}
.brand{{display:flex;align-items:center;gap:13px;}}
.brand img{{width:56px;height:56px;object-fit:contain;
  filter:drop-shadow(0 2px 4px rgba(0,0,0,.5));}}
.bt{{display:flex;flex-direction:column;line-height:1.05;}}
.bt .b1{{font-family:'mont';font-weight:{t['wordmark_wt']};font-size:25px;
  letter-spacing:5px;text-shadow:0 2px 5px rgba(0,0,0,.6);}}
.bt .b2{{font-family:'mont';font-weight:500;font-size:13px;letter-spacing:8px;
  opacity:.9;text-shadow:0 2px 5px rgba(0,0,0,.6);}}
.fdpill{{font-family:'mont';font-weight:600;font-size:15px;letter-spacing:2.5px;
  text-transform:uppercase;padding:10px 20px;border-radius:40px;
  background:rgba(0,0,0,.42);border:1px solid rgba(255,255,255,.45);}}
.lower{{position:absolute;left:48px;right:48px;bottom:58px;z-index:5;}}
.headline{{font-family:'{t['disp']}';font-weight:{t['disp_wt']};
  text-transform:{t['case']};line-height:{t['lh']};font-size:{t['head']}px;
  letter-spacing:{t['ls']};text-shadow:0 3px 16px rgba(0,0,0,.55);}}
.headline .accent{{color:{t['accent']};}}
.sub{{font-family:'mont';font-weight:600;font-size:27px;margin-top:20px;
  line-height:1.25;text-shadow:0 2px 10px rgba(0,0,0,.85);max-width:90%;
  letter-spacing:.2px;}}
.ctapill{{display:inline-block;margin-top:26px;background:#fff;color:{DARK};
  font-family:'mont';font-weight:700;font-size:23px;letter-spacing:.5px;
  padding:15px 28px;border-radius:50px;}}
.kicker{{font-family:'mont';font-weight:700;font-size:18px;letter-spacing:4px;
  text-transform:uppercase;color:{t['accent']};margin-bottom:14px;
  text-shadow:0 2px 8px rgba(0,0,0,.8);}}
"""


def header(t, pill="Happy Father's Day"):
    p = f'<div class="fdpill">{pill}</div>' if pill else ""
    return (f'<div class="hdr"><div class="brand"><img src="{data_uri(LOGO)}">'
            f'<div class="bt"><span class="b1">DUBERY</span>'
            f'<span class="b2">MANILA</span></div></div>{p}</div>')


def lifestyle(t, bg, line1, accent, sub, obj_pos="center 28%", kicker=None,
              cta=None, pill="Happy Father's Day"):
    k = f'<div class="kicker">{kicker}</div>' if kicker else ""
    c = f'<div class="ctapill">{cta}</div>' if cta else ""
    return f"""<div class="card">
  <img class="bg" src="{data_uri(bg)}" style="object-position:{obj_pos};">
  <div class="scrim"></div>
  {header(t, pill)}
  <div class="lower">{k}
    <h1 class="headline">{line1}<br><span class="accent">{accent}</span></h1>
    <p class="sub">{sub}</p>{c}
  </div>
</div>"""


def build_cards(t, batch=1):
    if batch == 4:
        sub = "Real polarized · 2 pairs ₱998, free delivery."
        sku = [
            ("hz5-bandits-matte-black", "Bandits Matte Black.", "Street-Ready."),
            ("hz5-bandits-green",       "Bandits Green.",       "Park-Ready."),
            ("hz5-bandits-glossy-black", "Bandits Glossy Black.", "Always Sharp."),
            ("hz5-outback-stripe",      "Outback Stripe.",      "Weekend-Ready."),
            ("hz5-rasta-red",           "Rasta Red.",           "Good Vibes."),
            ("hz5-couple",              "His & Hers.",          "Date-Ready."),
        ]
        return {i + 1: lifestyle(t, resolve(pref), name, vibe, sub, pill="The Range")
                for i, (pref, name, vibe) in enumerate(sku)}
    if batch == 3:
        # SKU-range showcase: name + vibe + offer, one premium worn shot per SKU.
        N = PROJECT / "contents/new"
        sub = "Real polarized · 2 pairs ₱998, free delivery."
        sku = [
            ("hz4-blue.png",          "Outback Blue.",     "Sea-Ready."),
            ("hz4-green-v2.png",      "Outback Green.",    "Trail-Ready."),
            ("hz4-red-v2.png",        "Outback Red.",      "Game-Ready."),
            ("hz4-tortoise.png",      "Bandits Tortoise.", "OOTD-Ready."),
            ("hz4-bandits-blue-v2.png", "Bandits Blue.",   "Beach-Ready."),
            ("hz4-rasta.png",         "Rasta Brown.",      "Everyday Easy."),
        ]
        return {i + 1: lifestyle(t, N / f"2026-06-16_{f}", name, vibe, sub,
                                 pill="The Range")
                for i, (f, name, vibe) in enumerate(sku)}
    if batch == 2:
        return {
            1: lifestyle(t, resolve("hz3-hook"), "This Father's Day,", "Skip the Necktie.",
                         "Give Dad shades that actually cut the glare."),
            2: lifestyle(t, PROJECT / "contents/new/duo-hiking.png", "One for Dad.", "One for You.",
                         "Matching polarized pairs — bundle up this Father's Day.", obj_pos="center 24%"),
            3: lifestyle(t, resolve("hz3-proof"), "The Glare Just", "Disappears.",
                         "Real polarized lenses — see straight into the water.", pill=None),
            4: lifestyle(t, resolve("hz3-guarantee"), "Polarized", "Or It's Free.",
                         "Not truly polarized? You don't pay.", pill="Our Promise"),
            5: lifestyle(t, resolve("hz3-offer"), "Two Pairs.", "₱998.",
                         "Free delivery + cash on delivery, nationwide."),
            6: lifestyle(t, resolve("hz3-cta"), "Give Dad", "The Clear View.",
                         "Message us to order — pay on delivery, nationwide.",
                         kicker="Father's Day · 06.21", cta="Order na — message us  →"),
        }
    return {
        1: lifestyle(t, resolve("hz-hook"), "This Father's Day,", "Skip the Necktie.",
                     "Give Dad shades that actually cut the glare.", obj_pos="center 22%"),
        2: lifestyle(t, PROJECT / "contents/new/duo-swimming.png", "One for Dad.", "One for You.",
                     "Matching polarized pairs — bundle up this Father's Day.", obj_pos="center 30%"),
        3: lifestyle(t, resolve("hz2-proof"), "The Glare Just", "Disappears.",
                     "Real polarized lenses — see straight into the water.", pill=None),
        4: lifestyle(t, PROJECT / "contents/new/2026-06-16_hz2-guarantee-v2.png", "Polarized", "Or It's Free.",
                     "Not truly polarized? You don't pay.", pill="Our Promise"),
        5: lifestyle(t, PROJECT / "contents/new/2026-06-16_hz2-offer-v2.png", "Two Pairs.", "₱998.",
                     "Free delivery + cash on delivery, nationwide."),
        6: lifestyle(t, resolve("hz-cta"), "Give Dad", "The Clear View.",
                     "Message us to order — pay on delivery, nationwide.",
                     obj_pos="center 26%", kicker="Father's Day · 06.21", cta="Order na — message us  →"),
    }


def render(html, out, page, t):
    page.set_content(f"<!doctype html><html><head><meta charset='utf-8'>"
                     f"<style>{build_css(t)}</style></head><body>{html}</body></html>")
    page.wait_for_timeout(150)
    big = out.with_suffix(".2x.png")
    page.screenshot(path=str(big), clip={"x": 0, "y": 0, "width": SIZE, "height": SIZE})
    img = Image.open(big).convert("RGB")
    if img.size != (SIZE, SIZE):
        img = img.resize((SIZE, SIZE), Image.LANCZOS)
    img.save(out, "PNG", optimize=True)
    big.unlink(missing_ok=True)
    print(f"  -> {out.relative_to(PROJECT)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int, default=None)
    ap.add_argument("--batch", type=int, default=1, choices=[1, 2, 3, 4])
    ap.add_argument("--theme", default="modern", choices=list(THEMES))
    ap.add_argument("--sample", action="store_true",
                    help="render cards 1 & 4 across all themes to .tmp for comparison")
    args = ap.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": SIZE, "height": SIZE},
                                device_scale_factor=SCALE)
        if args.sample:
            sdir = PROJECT / ".tmp" / "fdhz" / "samples"
            sdir.mkdir(parents=True, exist_ok=True)
            for name, t in THEMES.items():
                cards = build_cards(t, args.batch)
                for n in (1, 4):
                    render(cards[n], sdir / f"{name}-card{n}.png", page, t)
        else:
            t = THEMES[args.theme]
            out_dir = OUT_DIRS[args.batch]
            out_dir.mkdir(parents=True, exist_ok=True)
            cards = build_cards(t, args.batch)
            targets = {args.only: cards[args.only]} if args.only else cards
            for n, html in targets.items():
                render(html, out_dir / f"card-{n}.png", page, t)
        browser.close()
    print("Done.")


if __name__ == "__main__":
    main()

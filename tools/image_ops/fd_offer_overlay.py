"""
Father's Day offer overlay -- composites the locked DuberyMNL FD 2-pair-bundle
overlay (DUBERY MANILA logo badge + HAPPY FATHER'S DAY pill + ONE FOR DAD /
ONE FOR YOU headline + ₱998 offer card + Order na CTA) onto any base image.

Matches the look of contents/new/fd-beach-offer.png so a batch of FD lifestyle
stills can be rendered into ready-to-post ad creatives without redoing the
layout by hand each time.

Usage:
    python tools/image_ops/fd_offer_overlay.py contents/new/fd-park.png
    python tools/image_ops/fd_offer_overlay.py contents/new/fd-park.png \\
        --output contents/new/fd-park-offer.png
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJECT_DIR = Path(__file__).parent.parent.parent

# Target canvas -- 4:5 at FB feed-optimal resolution
CANVAS_W = 1080
CANVAS_H = 1350

# DuberyMNL brand
ORANGE = (232, 84, 32)        # #E85420
RED_BADGE = (217, 52, 44)     # #D9342C -- offer-card 2 PAIRS badge
GREEN_CHECK = (31, 169, 74)   # #1FA94A
WHITE = (255, 255, 255)
NEAR_BLACK = (15, 15, 15)
DARK_PILL_RGBA = (0, 0, 0, 145)   # translucent dark for top-right pill

LOGO_BADGE = PROJECT_DIR / "contents" / "assets" / "logos" / "logo-header.png"

# Windows font paths (Impact is the closest-on-system to Anton / Archivo Black)
FONTS_DIR = Path("C:/Windows/Fonts")
F_HEADLINE = FONTS_DIR / "impact.ttf"
F_BOLD = FONTS_DIR / "arialbd.ttf"
F_REG = FONTS_DIR / "arial.ttf"


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def _measure(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _draw_text_with_shadow(draw, xy, text, font, fill, shadow=(0, 0, 0, 150), offset=3, blur=False):
    """Draw text with a soft drop shadow for legibility on photo backgrounds."""
    x, y = xy
    # Shadow
    draw.text((x + offset, y + offset), text, font=font, fill=shadow)
    # Main text
    draw.text((x, y), text, font=font, fill=fill)


def compose_overlay(base_path: Path, output_path: Path) -> Path:
    """Composite the FD 2-pair offer overlay onto base_path, save to output_path."""
    # 1. Load + resize base to 1080x1350 (center-crop to 4:5)
    base = Image.open(base_path).convert("RGB")
    bw, bh = base.size
    target_ratio = CANVAS_W / CANVAS_H
    src_ratio = bw / bh
    if src_ratio > target_ratio:
        # Too wide -- crop sides
        new_w = int(bh * target_ratio)
        left = (bw - new_w) // 2
        base = base.crop((left, 0, left + new_w, bh))
    elif src_ratio < target_ratio:
        # Too tall -- crop top/bottom
        new_h = int(bw / target_ratio)
        top = (bh - new_h) // 2
        base = base.crop((0, top, bw, top + new_h))
    base = base.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)

    # 2. Subtle bottom gradient for headline legibility
    canvas = base.convert("RGBA")
    grad = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    grad_top = int(CANVAS_H * 0.50)
    for y in range(grad_top, CANVAS_H):
        alpha = int(180 * ((y - grad_top) / (CANVAS_H - grad_top)) ** 1.3)
        gd.rectangle([(0, y), (CANVAS_W, y + 1)], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas, grad)

    draw = ImageDraw.Draw(canvas)

    # 3. Top-left: DUBERY MANILA logo badge
    logo = Image.open(LOGO_BADGE).convert("RGBA")
    LOGO_H = 70
    aspect = logo.size[0] / logo.size[1]
    logo = logo.resize((int(LOGO_H * aspect), LOGO_H), Image.LANCZOS)
    canvas.paste(logo, (32, 34), logo)
    # DUBERY MANILA text right of badge
    logo_text_x = 32 + logo.size[0] + 14
    f_dubery = _font(F_HEADLINE, 36)
    f_manila = _font(F_BOLD, 16)
    _draw_text_with_shadow(draw, (logo_text_x, 32), "DUBERY", f_dubery, WHITE, offset=2)
    _draw_text_with_shadow(draw, (logo_text_x, 72), "MANILA", f_manila, WHITE, offset=1)

    # 4. Top-right: HAPPY FATHER'S DAY pill
    pill_text = "HAPPY FATHER'S DAY"
    f_pill = _font(F_BOLD, 22)
    tw, th = _measure(draw, pill_text, f_pill)
    pill_pad_x, pill_pad_y = 28, 14
    pill_w = tw + pill_pad_x * 2
    pill_h = th + pill_pad_y * 2 + 4
    pill_x = CANVAS_W - pill_w - 32
    pill_y = 38
    pill_layer = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill_layer)
    _rounded_rect(pd, [(0, 0), (pill_w, pill_h)], radius=pill_h // 2, fill=DARK_PILL_RGBA)
    pd.text((pill_pad_x, pill_pad_y), pill_text, font=f_pill, fill=WHITE)
    canvas.alpha_composite(pill_layer, (pill_x, pill_y))

    draw = ImageDraw.Draw(canvas)  # rebind after alpha_composite

    # 5. Lower-left headline: "ONE FOR DAD," white  /  "ONE FOR YOU." orange
    f_head = _font(F_HEADLINE, 105)
    head_x = 42
    head_y1 = 760
    head_y2 = head_y1 + 110
    _draw_text_with_shadow(draw, (head_x, head_y1), "ONE FOR DAD,", f_head, WHITE, offset=4)
    _draw_text_with_shadow(draw, (head_x, head_y2), "ONE FOR YOU.", f_head, ORANGE, offset=4)

    # 6. Sub-line under headline
    f_sub = _font(F_BOLD, 26)
    sub_text = "Matching polarized shades \u2014 bundle up this Father's Day."
    sub_y = head_y2 + 130
    _draw_text_with_shadow(draw, (head_x, sub_y), sub_text, f_sub, WHITE, offset=2)

    # 7. Offer card: white rounded card with red 2 PAIRS / ₱998 badge + text
    card_y = sub_y + 60
    card_w = CANVAS_W - 84
    card_h = 110
    card_x = 42
    _rounded_rect(draw, [(card_x, card_y), (card_x + card_w, card_y + card_h)],
                  radius=20, fill=WHITE)

    # Red badge inside card (left)
    badge_pad = 14
    badge_w = 170
    badge_h = card_h - badge_pad * 2
    badge_x = card_x + badge_pad
    badge_y = card_y + badge_pad
    _rounded_rect(draw, [(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)],
                  radius=12, fill=RED_BADGE)

    f_pairs = _font(F_BOLD, 18)
    # Use Arial Bold for the price -- Impact lacks the ₱ glyph (renders as a box).
    f_price = _font(F_BOLD, 42)
    # "2 PAIRS"
    pairs_text = "2 PAIRS"
    pw, ph = _measure(draw, pairs_text, f_pairs)
    draw.text((badge_x + (badge_w - pw) // 2, badge_y + 10), pairs_text, font=f_pairs, fill=WHITE)
    # "₱998"
    price_text = "\u20b1998"
    prw, prh = _measure(draw, price_text, f_price)
    draw.text((badge_x + (badge_w - prw) // 2, badge_y + 30), price_text, font=f_price, fill=WHITE)

    # Right-of-badge text in the card
    text_x = badge_x + badge_w + 22
    f_cardhead = _font(F_BOLD, 22)
    f_cardsub = _font(F_REG, 19)
    draw.text((text_x, card_y + 24), "Bundle deal \u2014 best value",
              font=f_cardhead, fill=NEAR_BLACK)
    # Green check + free delivery -- draw the checkmark as two line segments
    # (Arial Bold doesn't ship the \u2713 glyph, so font rendering produces nothing).
    check_x = text_x
    check_y = card_y + 60
    CHECK_D = 22
    draw.ellipse([(check_x, check_y), (check_x + CHECK_D, check_y + CHECK_D)], fill=GREEN_CHECK)
    # Two-stroke checkmark inside the circle
    cx, cy = check_x, check_y
    draw.line(
        [(cx + 5, cy + 11), (cx + 9, cy + 15), (cx + 17, cy + 7)],
        fill=WHITE,
        width=3,
        joint="curve",
    )
    draw.text((check_x + 30, check_y - 2), "FREE delivery, nationwide",
              font=f_cardsub, fill=NEAR_BLACK)

    # 8. CTA pill at the bottom: "Order na — message us  →"
    cta_text = "Order na \u2014 message us  \u2192"
    f_cta = _font(F_BOLD, 22)
    ctw, cth = _measure(draw, cta_text, f_cta)
    cta_pad_x, cta_pad_y = 32, 16
    cta_w = ctw + cta_pad_x * 2
    cta_h = cth + cta_pad_y * 2 + 4
    cta_x = 42
    cta_y = card_y + card_h + 28
    _rounded_rect(draw, [(cta_x, cta_y), (cta_x + cta_w, cta_y + cta_h)],
                  radius=cta_h // 2, fill=WHITE)
    draw.text((cta_x + cta_pad_x, cta_y + cta_pad_y), cta_text, font=f_cta, fill=NEAR_BLACK)

    # 9. Flatten + save
    canvas.convert("RGB").save(output_path, format="PNG", optimize=True)
    return output_path


def main():
    p = argparse.ArgumentParser(description="Father's Day 2-pair offer overlay composer.")
    p.add_argument("base", help="Path to base image (any aspect, will center-crop to 4:5)")
    p.add_argument("--output", "-o", default=None, help="Output path (default: <base>-offer.png)")
    args = p.parse_args()

    base_path = Path(args.base)
    if not base_path.exists():
        print(f"error: base image not found: {base_path}", file=sys.stderr)
        sys.exit(2)

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = base_path.with_name(base_path.stem + "-offer.png")

    result = compose_overlay(base_path, out_path)
    print(f"saved: {result}")


if __name__ == "__main__":
    main()

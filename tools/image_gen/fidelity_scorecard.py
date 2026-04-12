"""
Product Fidelity Scorecard -- tests how well Gemini reproduces each product.

Generates one standardized test image per product using the same prompt template,
isolating product fidelity from scene complexity. Uses angle -1 (3/4 front) by default.

Usage:
    python tools/image_gen/fidelity_scorecard.py                    # all products
    python tools/image_gen/fidelity_scorecard.py bandits-green      # single product
    python tools/image_gen/fidelity_scorecard.py --angle 3          # test angle -3
    python tools/image_gen/fidelity_scorecard.py --dry-run          # write prompts only

Output: contents/new/scorecard/SC-{product}-a{angle}.png + _prompt.json sidecar
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
REFS_DIR = PROJECT_DIR / "contents" / "assets" / "product-refs"
OUTPUT_DIR = PROJECT_DIR / "contents" / "new" / "scorecard"

PRODUCTS = {
    "bandits-blue":         ("Bandits Blue",         "glossy", "slim square"),
    "bandits-glossy-black": ("Bandits Glossy Black", "glossy", "slim square"),
    "bandits-green":        ("Bandits Green",        "glossy", "slim square"),
    "bandits-matte-black":  ("Bandits Matte Black",  "matte",  "slim square"),
    "bandits-tortoise":     ("Bandits Tortoise",     "matte",  "slim square"),
    "outback-black":        ("Outback Black",        "matte",  "rounded classic"),
    "outback-blue":         ("Outback Blue",         "matte",  "rounded classic"),
    "outback-green":        ("Outback Green",        "matte",  "rounded classic"),
    "outback-red":          ("Outback Red",          "matte",  "rounded classic"),
    "rasta-brown":          ("Rasta Brown",          "matte",  "rounded keyhole"),
    "rasta-red":            ("Rasta Red",            "matte",  "rounded keyhole"),
}


def get_ref_path(product: str, angle: int) -> Path | None:
    ref = REFS_DIR / product / f"{product}-{angle}.png"
    return ref if ref.exists() else None


def build_prompt(product: str, angle: int) -> dict | None:
    display, finish, shape = PRODUCTS[product]
    ref_path = get_ref_path(product, angle)
    if not ref_path:
        return None

    prompt = (
        f"A pair of {finish} {shape} sunglasses matching the reference image, "
        f"resting closed on a clean white marble surface. "
        f"Warm natural daylight from the left side. "
        f"The frame has a {finish} finish with subtle surface reflections. "
        f"Professional product photography, 50mm lens, shallow depth of field, "
        f"clean minimal composition with soft shadows."
    )

    return {
        "prompt": prompt,
        "image_input": [str(ref_path)],
        "metadata": {
            "product": product,
            "display_name": display,
            "finish": finish,
            "shape": shape,
            "angle": angle,
        }
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Product Fidelity Scorecard")
    parser.add_argument("product", nargs="?", default="all")
    parser.add_argument("--angle", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.product == "all":
        products = list(PRODUCTS.keys())
    elif args.product in PRODUCTS:
        products = [args.product]
    else:
        print(f"ERROR: Unknown product '{args.product}'", file=sys.stderr)
        print(f"Available: {', '.join(PRODUCTS.keys())}", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    prompts = []
    for product in products:
        data = build_prompt(product, args.angle)
        if not data:
            print(f"SKIP: {product} has no angle -{args.angle}", file=sys.stderr)
            continue
        prompt_file = OUTPUT_DIR / f"SC-{product}-a{args.angle}_prompt.json"
        prompt_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        prompts.append((product, prompt_file))
        print(f"Wrote: {prompt_file.name}", file=sys.stderr)

    if args.dry_run:
        print(f"\nDry run: {len(prompts)} prompts in {OUTPUT_DIR}", file=sys.stderr)
        print(json.dumps({"prompts_written": len(prompts), "output_dir": str(OUTPUT_DIR)}))
        return

    print(f"\nGenerating {len(prompts)} images (~${len(prompts) * 0.07:.2f})...", file=sys.stderr)
    gen_script = Path(__file__).parent / "generate_vertex.py"
    results = []

    for i, (product, prompt_file) in enumerate(prompts, 1):
        output_file = OUTPUT_DIR / f"SC-{product}-a{args.angle}.png"
        print(f"\n[{i}/{len(prompts)}] {product}...", file=sys.stderr)

        result = subprocess.run(
            [sys.executable, str(gen_script), str(prompt_file), str(output_file)],
            capture_output=True, text=True, cwd=str(PROJECT_DIR)
        )

        if result.returncode == 0:
            try:
                gen_result = json.loads(result.stdout.strip())
                results.append({"product": product, "status": "ok", **gen_result})
                print(f"  OK: {gen_result.get('size_kb', '?')}KB", file=sys.stderr)
            except json.JSONDecodeError:
                results.append({"product": product, "status": "ok_no_json"})
                print(f"  OK (no JSON)", file=sys.stderr)
        else:
            results.append({"product": product, "status": "error", "stderr": result.stderr[-500:]})
            print(f"  FAILED: {result.stderr[-200:]}", file=sys.stderr)

    ok = sum(1 for r in results if r["status"].startswith("ok"))
    print(f"\nScorecard: {ok}/{len(results)} generated. Review at {OUTPUT_DIR}", file=sys.stderr)
    print(json.dumps({"total": len(results), "ok": ok, "results": results}))


if __name__ == "__main__":
    main()

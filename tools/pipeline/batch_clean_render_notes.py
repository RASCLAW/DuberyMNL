"""
Batch-clean render_notes in all prompt JSONs.

Strips color/material/texture descriptions from product.render_notes,
keeping ONLY: position, angle, lighting, logo legibility, reference image deference.

This is a one-time cleanup. The prompt writer skill already has the rules --
this fixes the existing prompts that were generated before the rules were enforced.

Usage:
    python tools/pipeline/batch_clean_render_notes.py              # all prompts
    python tools/pipeline/batch_clean_render_notes.py --dry-run    # preview only
"""

import json
import re
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
TMP_DIR = PROJECT_DIR / ".tmp"

# Words/phrases that indicate color/material descriptions (violations)
COLOR_MATERIAL_PATTERNS = [
    # Colors
    r'\b(?:warm\s+)?red(?:-tinted)?\b', r'\bamber\b', r'\bgold(?:en)?\b',
    r'\bblue(?:-mirrored)?\b', r'\bgreen(?:-mirrored)?\b', r'\bbrown\b',
    r'\bblack\b', r'\bdark\b(?!\s+background)', r'\bwhite\b(?!\s+(?:text|border|sky|hazy|sand))',
    r'\bcool\s+sapphire\b', r'\bturquoise\b', r'\bemerald\b',
    # Materials/textures
    r'\bmatte(?:-finish)?\b', r'\bglossy\b', r'\bcamo(?:uflage)?\b',
    r'\btortoise(?:shell)?\b', r'\bearthy\b',
    # Explicit lens/frame color descriptions
    r'\b(?:near-)?black\s+lens\b', r'\bdark\s+lens\b',
    r'\bblue\s+lens\b', r'\bgreen\s+lens\b', r'\bred\s+lens\b',
    r'\bbrown\s+lens\b', r'\bamber\s+lens\b',
    r'\bblack\s+frame\b', r'\bmatte\s+frame\b',
    r'\bmirrored\s+lens\b',
]


def is_color_material_sentence(sentence: str) -> bool:
    """Check if a sentence primarily describes color/material."""
    s = sentence.strip().lower()
    if not s:
        return False

    # Always keep these
    keep_phrases = [
        'dubery logo', 'logo on', 'logo must',
        'reference image', 'frame shape', 'frame shapes match',
        'no person in frame', 'product arrangement',
        'position', 'angle', 'viewing angle',
        'arm style', 'bridge must',
    ]
    for phrase in keep_phrases:
        if phrase in s:
            return False

    # Count color/material hits
    hits = 0
    for pattern in COLOR_MATERIAL_PATTERNS:
        if re.search(pattern, s, re.IGNORECASE):
            hits += 1

    # If more than half the sentence is color/material, flag it
    words = len(s.split())
    if hits >= 2 or (hits >= 1 and words < 12):
        return True

    return False


def clean_render_notes(render_notes: str, models: list, content_type: str) -> str:
    """Rewrite render_notes to remove color/material, keep position/angle/lighting."""

    # Split into sentences
    sentences = re.split(r'(?<=[.!])\s+', render_notes)

    kept = []
    removed = []

    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if is_color_material_sentence(s):
            removed.append(s)
        else:
            # Even in kept sentences, strip inline color descriptions
            # e.g., "warm red-tinted lens catches midday glare" -> "Lens catches midday glare"
            cleaned = re.sub(
                r'(?:warm\s+)?(?:red|blue|green|amber|gold|brown|dark|black|glossy|matte)(?:-tinted|-mirrored|-finish)?\s+',
                '', s, flags=re.IGNORECASE
            ).strip()
            # Fix capitalization if we stripped the start
            if cleaned and cleaned[0].islower():
                cleaned = cleaned[0].upper() + cleaned[1:]
            if cleaned:
                kept.append(cleaned)

    # Build the clean render_notes
    parts = []

    # Determine position context from content_type
    if 'A' in content_type:
        parts.append("Sunglasses worn on subject's face, clearly visible as the hero element.")
    elif 'D' in content_type:
        parts.append("Product is the hero, prominently placed in frame.")
    elif 'B' in content_type or 'C' in content_type:
        parts.append("Product placed naturally in the environment, hero of the composition.")
    elif 'E' in content_type:
        parts.append("Product centered in frame for feature callout layout.")

    # Multi-product note
    if len(models) > 1:
        parts.append(f"Multiple products shown: {', '.join(models)}. Each must match its respective reference image exactly.")
    elif len(models) == 1:
        parts.append(f"Model: {models[0]}. Must match the reference image exactly.")

    # Add back cleaned kept sentences (skip if redundant with what we added)
    for s in kept:
        s_lower = s.lower()
        # Skip if it's just restating what we already said
        if 'hero' in s_lower and ('hero' in ' '.join(parts).lower()):
            continue
        if 'reference image' in s_lower and 'reference image' in ' '.join(parts).lower():
            continue
        parts.append(s)

    # Always ensure these are present
    has_logo = any('dubery logo' in p.lower() or 'logo on' in p.lower() for p in parts)
    if not has_logo:
        parts.append("Dubery logo on the frame must be sharp and legible.")

    has_ref_deference = any('reference image' in p.lower() for p in parts)
    if not has_ref_deference:
        parts.append("Frame shape, color, material, and lens appearance are dictated entirely by the reference image.")

    # Lens reflection -- keep it generic
    has_reflection = any('reflect' in p.lower() or 'reflection' in p.lower() for p in parts)
    if has_reflection:
        # Replace any specific reflection descriptions
        parts = [
            re.sub(
                r'(?:Lens\s+)?[Rr]eflect(?:ion|s)?[^.]*\.',
                'Lens naturally reflects the surrounding environment -- subtle and physically accurate.',
                p
            ) for p in parts
        ]

    return ' '.join(parts)


def main():
    dry_run = '--dry-run' in sys.argv

    prompt_files = sorted(TMP_DIR.glob('*_prompt_structured.json'))
    # Skip .prev.json backups
    prompt_files = [f for f in prompt_files if '.prev.' not in f.name]

    print(f"Batch render_notes cleanup")
    print(f"{'=' * 50}")
    print(f"Found {len(prompt_files)} prompt files")
    if dry_run:
        print("DRY RUN -- no files will be modified\n")

    cleaned = 0
    skipped = 0

    for pf in prompt_files:
        data = json.loads(pf.read_text())
        product = data.get('product', {})
        render_notes = product.get('render_notes', '')
        models = product.get('models', [])
        content_type = data.get('content_type', 'TYPE D')

        if not render_notes:
            skipped += 1
            continue

        # Check if there are actual violations
        has_violation = False
        for pattern in COLOR_MATERIAL_PATTERNS:
            if re.search(pattern, render_notes, re.IGNORECASE):
                has_violation = True
                break

        if not has_violation:
            skipped += 1
            continue

        new_notes = clean_render_notes(render_notes, models, content_type)

        print(f"\n--- {pf.name} ({content_type}, {models}) ---")
        print(f"  OLD: {render_notes[:120]}...")
        print(f"  NEW: {new_notes[:120]}...")

        if not dry_run:
            # Backup
            backup = pf.with_suffix('.json.pre_clean')
            if not backup.exists():  # Don't overwrite existing backups
                backup.write_text(pf.read_text())

            data['product']['render_notes'] = new_notes
            pf.write_text(json.dumps(data, indent=2, ensure_ascii=False))

        cleaned += 1

    print(f"\n{'=' * 50}")
    print(f"Cleaned: {cleaned}, Skipped: {skipped}")
    if dry_run:
        print("Re-run without --dry-run to apply changes.")


if __name__ == '__main__':
    main()

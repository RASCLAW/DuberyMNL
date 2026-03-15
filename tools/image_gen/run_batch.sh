#!/bin/bash
# WF2b batch image generation
# Usage: bash tools/image_gen/run_batch.sh [caption_ids...]
# Example: bash tools/image_gen/run_batch.sh 2 3 6

set -e
PROJECT_DIR="/home/ra/projects/DuberyMNL"
OUTPUT_DIR="${PROJECT_DIR}/output/images"

cd "$PROJECT_DIR"
source .venv/bin/activate

IDS=("$@")

for ID in "${IDS[@]}"; do
    PROMPT_FILE=".tmp/${ID}_prompt_structured.json"
    OUTPUT_FILE="${OUTPUT_DIR}/dubery_${ID}.jpg"

    if [ ! -f "$PROMPT_FILE" ]; then
        echo "SKIP #${ID}: prompt file not found at ${PROMPT_FILE}"
        continue
    fi

    echo "Generating image for caption #${ID}..."
    python tools/image_gen/generate_kie.py "$PROMPT_FILE" "$OUTPUT_FILE" &
done

wait
echo "All jobs complete."

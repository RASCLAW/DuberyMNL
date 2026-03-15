#!/bin/bash
# WF2b batch image generation
# Usage: bash tools/image_gen/run_batch.sh [caption_ids...]
# Example: bash tools/image_gen/run_batch.sh 2 3 6

PROJECT_DIR="/home/ra/projects/DuberyMNL"
OUTPUT_DIR="${PROJECT_DIR}/output/images"

cd "$PROJECT_DIR"
source .venv/bin/activate

if [ "$#" -eq 0 ]; then
    echo "Usage: bash tools/image_gen/run_batch.sh [caption_ids...]"
    exit 1
fi

declare -A PIDS
declare -A IDS_BY_PID

for ID in "$@"; do
    PROMPT_FILE=".tmp/${ID}_prompt_structured.json"
    OUTPUT_FILE="${OUTPUT_DIR}/dubery_${ID}.jpg"

    if [ ! -f "$PROMPT_FILE" ]; then
        echo "SKIP #${ID}: prompt file not found at ${PROMPT_FILE}"
        continue
    fi

    echo "Generating image for caption #${ID}..."
    python3 tools/image_gen/generate_kie.py "$PROMPT_FILE" "$OUTPUT_FILE" \
        > ".tmp/generate_${ID}.log" 2>&1 &
    PID=$!
    PIDS[$ID]=$PID
    IDS_BY_PID[$PID]=$ID
done

if [ ${#PIDS[@]} -eq 0 ]; then
    echo "No jobs started."
    exit 1
fi

echo "Waiting for ${#PIDS[@]} job(s)..."

FAILED=()
SUCCEEDED=()

for ID in "${!PIDS[@]}"; do
    PID=${PIDS[$ID]}
    wait "$PID"
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        SUCCEEDED+=("$ID")
        echo "OK  #${ID}"
    else
        FAILED+=("$ID")
        echo "FAIL #${ID} (exit $EXIT_CODE) — see .tmp/generate_${ID}.log"
    fi
done

echo ""
echo "============================="
echo "  Done: ${#SUCCEEDED[@]} succeeded, ${#FAILED[@]} failed"
if [ ${#FAILED[@]} -gt 0 ]; then
    echo "  Failed IDs: ${FAILED[*]}"
    echo "  Check logs: .tmp/generate_[id].log"
fi
echo "============================="

if [ ${#FAILED[@]} -eq 0 ]; then
    echo ""
    echo "All images generated. Launching image review..."
    bash tools/image_gen/start_image_review.sh
else
    exit 1
fi

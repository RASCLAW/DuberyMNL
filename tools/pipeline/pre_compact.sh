#!/bin/bash
# Auto-runs before every /compact via PreCompact hook
# Saves pipeline state snapshot to .tmp/pre_compact_state.txt

cd /home/ra/projects/DuberyMNL

python3 -c "
import json, datetime

try:
    data = json.loads(open('.tmp/pipeline.json').read())
    counts = {}
    for c in data:
        s = c.get('status', '?')
        counts[s] = counts.get(s, 0) + 1

    lines = [f'Pipeline snapshot [{datetime.datetime.now().strftime(\"%Y-%m-%d %H:%M\")}]']
    for s, n in sorted(counts.items()):
        lines.append(f'  {s}: {n}')
    lines.append(f'  TOTAL: {len(data)}')
    print('\n'.join(lines))
except Exception as e:
    print(f'pre_compact.sh: pipeline read failed ({e})')
" > .tmp/pre_compact_state.txt 2>/dev/null

echo "[pre-compact] State snapshot saved to .tmp/pre_compact_state.txt"

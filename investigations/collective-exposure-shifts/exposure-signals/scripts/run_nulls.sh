#!/bin/zsh
# 19 day-shift null runs, one at a time; stops if the internal disk falls under 200 MB (swap grows there).
cd "${0:A:h}/.." || exit 1
X=../../..
PY=/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
for k in $(seq 1 19); do
  [ -f out/null/seed_$k/manifest.json ] && continue
  free=$(df -k / | awk 'NR==2{print $4}')
  if [ "$free" -lt 204800 ]; then echo "STOP disk ${free}k before seed $k"; exit 2; fi
  PYTHONDONTWRITEBYTECODE=1 $PY -I scripts/run_signals.py --tapes $X/tapes.sqlite --tapes $X/tapes2.sqlite \
    --markets $X/sample_markets.jsonl --markets $X/sample_expanded.jsonl --params params.json \
    --out out/null/seed_$k --null-seed $k --workers 2 || { echo "FAILED seed $k"; exit 1; }
  echo "seed $k done $(date -u +%H:%M:%S) free=$(df -h / | awk 'NR==2{print $4}')"
done
echo NULLS_DONE

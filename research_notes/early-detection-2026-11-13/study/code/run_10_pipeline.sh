#!/bin/bash
# Collection and feature pipeline up to the analytic table. No rate, no test: those run only after the freeze (ana_50, ana_90).
set -euo pipefail
cd "$(dirname "$0")/.."
step() { echo "=== $(date -u +%H:%M:%S) $1" | tee -a logs/pipeline.log; python3 "code/$1.py" >> "logs/$1.log" 2>&1; echo "    done $(date -u +%H:%M:%S)" | tee -a logs/pipeline.log; }
[ -f derived/stage1_counts.json ] || step feat_20_ignitions
step col_30_tapes
step feat_30_features
step col_40_baselines
step ana_00_freeze
echo "PIPELINE_DONE $(date -u +%H:%M:%S)" | tee -a logs/pipeline.log

#!/bin/bash
# Copy the working folder into the worktree, run every test and the repository's evidence check. Commit and push stay separate steps. Usage: sync_commit.sh
set -euo pipefail
ROOT=/Volumes/PHI-Data/global-forensics
TREE=$ROOT/PHI-global-forensics
rsync -a --delete --exclude __pycache__ --exclude '*.tmp' --exclude .DS_Store --exclude '._*' "$ROOT/wip/" "$TREE/investigations/global-forensics/"
cd "$TREE/investigations/global-forensics/engine"
export PYTHONDONTWRITEBYTECODE=1
python3.12 ../tests/test_engine.py 2>&1 | tail -1
python3.12 ../tests/test_shadow.py 2>&1 | tail -1
python3.12 ../tests/test_adversarial_existing.py 2>&1 | tail -1
"$ROOT/venv/bin/python" ../tests/test_study_v2.py 2>&1 | tail -1
python3.12 audit/claims_audit.py --self-test
cd "$TREE"
PHI_ENV_FILES=~/Downloads/.env python3.12 scripts/validate_evidence.py investigations/global-forensics --fill 2>&1 | tail -12
git status -s | wc -l

#!/bin/sh
# Mission 5, full pipeline in order. Each step is outcome-blind until ana_50 (labels joined there; TRAIN labels
# also in ctl_40 for the synthetic controls).
# usage: sh code/run_all.sh STEP   STEP in: check | base | funding | controls | ctlsummary | train | valid | test
#                                            | nulls | nullgate | verdict | assemble
set -eu
export PYTHONDONTWRITEBYTECODE=1
ETUDE=$(cd "$(dirname "$0")/.." && pwd)
RAW=${RAW:-$HOME/Projects/Polymarket-collective-falsification-raw-20261117}
PY=${PY:-/Library/Frameworks/Python.framework/Versions/3.13/bin/python3}
cd "$ETUDE"
TAPES="--tapes data/tapes_all.sqlite --tapes $RAW/train_ext_tapes.sqlite --tapes $RAW/holdout_tapes.sqlite --tapes $RAW/history_tapes.sqlite"
MKS="--markets AUTO=data/sample_expanded.jsonl --markets TRAIN=derived/train_ext_markets.jsonl --markets SPLIT=derived/holdout_markets.jsonl --markets HISTORY=derived/history_markets.jsonl"
COMMON="$TAPES $MKS --meta derived/meta.jsonl --params frozen_deps/exposure-signals/params.json --iran frozen_deps/position-ledger/data/iran_cohort_wallets.json"
ANA="--labels data/labels.jsonl.gz --universe data/universe_markets.jsonl.gz --meta derived/meta.jsonl --holdout derived/holdout_markets.jsonl"
FUND="--funding out/funding/funding.json"
SCEN=${SCEN:-"STRONG:5 MEDIUM:5 WEAK:5 NULL:10 OLD:5"}

case "$1" in
  check)   # inputs outside the study must match the hashes recorded before the freeze
    (cd "$RAW" && shasum -a 256 -c "$ETUDE/derived/tapes_sha256.txt") ;;
  base)
    sh "$0" check
    $PY -I code/feat_30_detect.py $COMMON --out out/base --phase-a-cache out/phase_a_cache --workers 4 ;;
  funding)
    $PY -I code/col_30_funding.py --panel out/base/panel.jsonl.gz --params frozen_deps/exposure-signals/params.json \
        --cache "$RAW/funding_cache_first100" --out out/funding/funding.json ;;
  controls)
    for ITEM in $SCEN; do
      SC=${ITEM%%:*}; N=${ITEM##*:}
      for SEED in $(seq 1 "$N"); do
        T=${SC}_${SEED}
        $PY -I code/ctl_40_inject.py $TAPES $MKS --labels data/labels.jsonl.gz --scenario "$SC" --seed "$SEED" \
            --out controles/inject_$T.json --wallet-first controles/wallet_first.json
        $PY -I code/feat_30_detect.py $COMMON --only-roles TRAIN --out out/ctl_$T --phase-a-cache out/phase_a_cache \
            --inject controles/inject_$T.json --workers 4
        EXTRA=""
        if [ "$SC" = "FUNDLINK" ]; then EXTRA="$FUND --funding-extra controles/inject_${T}_funding.json"; fi
        $PY -I code/ana_50_models.py controls --panel out/ctl_$T/panel.jsonl.gz $ANA $EXTRA --out controles \
            --tag "$T" --inject-manifest controles/inject_${T}_manifest.json
      done
    done
    if [ "${PERMUTED:-1}" = "1" ]; then
      $PY -I code/ana_50_models.py controls --panel out/base/panel.jsonl.gz $ANA --out controles --tag PERMUTED \
          --permute-labels
    fi ;;
  rescore)   # re-run the analysis of every existing control panel (detector outputs unchanged)
    for D in out/ctl_*; do
      T=${D#out/ctl_}; SC=${T%%_*}; EXTRA=""
      if [ "$SC" = "FUNDLINK" ]; then EXTRA="$FUND --funding-extra controles/inject_${T}_funding.json"; fi
      $PY -I code/ana_50_models.py controls --panel "$D/panel.jsonl.gz" $ANA $EXTRA --out controles --tag "$T" \
          --inject-manifest "controles/inject_${T}_manifest.json"
    done
    $PY -I code/ana_50_models.py controls --panel out/base/panel.jsonl.gz $ANA --out controles --tag PERMUTED \
        --permute-labels ;;
  ctlsummary)
    $PY -I code/ctl_45_summary.py controles ;;
  train)
    $PY -I code/ana_50_models.py train --panel out/base/panel.jsonl.gz $ANA $FUND --out out/models ;;
  valid)
    $PY -I code/ana_50_models.py valid --panel out/base/panel.jsonl.gz $ANA $FUND --out out/models ;;
  test)
    $PY -I code/ana_50_models.py test --panel out/base/panel.jsonl.gz $ANA $FUND --out out/models ;;
  nulls)
    for K in $(seq 1 19); do
      $PY -I code/feat_30_detect.py $COMMON --out out/null_$K --phase-a-cache out/phase_a_cache --null-seed $K \
          --null-split TEST --workers 4
    done ;;
  nullgate)
    NP=""; for K in $(seq 1 19); do NP="$NP --null-panel out/null_$K/panel.jsonl.gz"; done
    $PY -I code/ana_50_models.py nullgate --panel out/base/panel.jsonl.gz $ANA --out out/models $NP ;;
  verdict)
    $PY -I code/ana_50_models.py verdict --panel none --labels none --out out/models \
        --controls-summary controles/summary.json ;;
  assemble)
    $PY -I code/ana_60_assemble.py STATISTICAL_RESULTS.json ;;
  *) echo "unknown step $1"; exit 2 ;;
esac

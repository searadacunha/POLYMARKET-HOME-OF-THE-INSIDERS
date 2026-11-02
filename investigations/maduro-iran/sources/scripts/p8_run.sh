#!/bin/bash
set -e
cd "$(dirname "$0")"
python3 p8_features.py > p8/features.log 2>&1
python3 p8_sample.py > p8/sample.log 2>&1
( for k in 0 1 2 3; do python3 p8_funding.py p8/funding_wallets.json $k 4 & done; wait; echo funding_done ) > p8/funding.log 2>&1 &
PF=$!
( for k in 0 1 2 3 4 5; do python3 p8_prices.py $k 6 & done; wait; echo prices_done ) > p8/prices.log 2>&1 &
PP=$!
wait $PF
( for k in 0 1 2 3; do python3 p8_relay_origin.py p8/funding_wallets.json $k 4 & done; wait; echo relay_done ) > p8/relay.log 2>&1
wait $PP
python3 p8_fundfeat.py > p8/fundfeat.log 2>&1
python3 p8_analysis.py > p8/analysis.log 2>&1
python3 p8_extra.py > p8/extra.log 2>&1
echo ALL_DONE

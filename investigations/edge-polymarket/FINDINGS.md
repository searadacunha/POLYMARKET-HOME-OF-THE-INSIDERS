# Findings: edge-polymarket

## F-001 | REFUTED | Calibration before expiry: prices are calibrated, 16 strategies, none survives on TRAIN
- Sources: sources/REPRISE.md ; sources/derived/c10_TRAIN.json
- Method: sources/code/ana_c10_calibration.py, test register
- Limits: Low power, confidence interval of 5% per dollar each way. VALID and TEST not read
- Links: maduro-iran:F-006

## F-002 | UNRESOLVED | Hourly BTC against Binance: collection only, no test
- Sources: sources/REPRISE.md
- Method: Plan described in REPRISE.md
- Limits: Cut off before the positive control
- Links: none

## F-003 | UNRESOLVED | The funding structure has no verdict: plan and positive controls only, labeling stopped at 80/137
- Sources: sources/funding/analysis_plan.md ; sources/funding/controles/controles_positifs.md ; sources/funding/data/col_40.log
- Method: Plan written before any performance calculation
- Limits: No result: conclude nothing
- Links: none

## Missing to conclude

- Resuming along `sources/REPRISE.md`, if wanted.

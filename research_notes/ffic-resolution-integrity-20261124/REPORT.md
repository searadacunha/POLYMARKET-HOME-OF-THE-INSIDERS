# External resolution integrity — FFIC follow-up, 24 November 2026

Status: targeted source-data reconciliation and standalone import diagnostic. No change to historical evidence, README, legal attribution, predictive verdict or the separate draft PR 113.

## Material conflict discovered

The [previous competitor benchmark](../radar-asof-benchmark-2026-11-21/COMPETITOR_BENCHMARK.md) already counted FFIC's 32 market prefixes and documented missing trade histories. This follow-up addresses label correctness instead of repeating the count.

For the market with condition prefix 0x3488f31e, the [pinned FFIC CSV](https://github.com/ForesightFlow/datasets/blob/5ba4127473648a7a278eaa11bd24b82a024181c2/ffic-inventory/ffic-v1.csv) reports NO and approximate volume 89,652,867 USDC. Git blob aeb1ec2ec8ba5845c36e8cda57ad3a5962f48891. The corresponding [Polymarket event page](https://polymarket.com/uk/event/us-strikes-iran-by) displays YES for the same market label and rounded volume. A second public source, [calld-io resolution archive teaser](https://huggingface.co/datasets/calld-io/polymarket-resolution-archive-teaser), shows the full condition ID in reviewed.csv, outcome Yes, payout prices 1|0 and volume 89,652,867.363489. The full identifier is also independently present in this repository's [prior audit](../independent-forensic-audit-2026-11-08/REPORT.md).

These public sources strongly support a conflicting outcome label, rather than a distinct market with a similar title. Direct Gamma API access failed in this session; the on-chain payout vector was not independently replayed. No claim of chain-level certification is made. The archive web snapshot was inspected on 2026-11-24, not content-hash pinned. Only its factual identifier and outcome are recorded; no dataset redistribution is claimed.

All other FFIC labels remain unreviewed here. The external inventory is not wallet-level legal ground truth. A prefix is not a canonical condition ID and cannot establish a join on its own.

## Reproduction

The minimal external_example.csv adapts two fields from Maksym Nechepurenko / Devnull FZCO, ForesightFlow Insider Cases inventory v1, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), under the [dataset-specific licence](https://github.com/ForesightFlow/datasets/blob/main/ffic-inventory/LICENSE). The upstream blob is not changed. reviewed.csv contains a manually reviewed crosswalk, not an automatically trusted oracle.

Run from this directory:

    python3 -m unittest -v audit
    python3 audit.py external_example.csv reviewed.csv

Expected: six synthetic tests pass; the second command emits one CONFLICT and exits 1. These commands passed as expected in an isolated Python environment. The audited input is the single extracted conflict row, not all 32 FFIC records. The full pinned upstream CSV may be supplied separately; unreviewed rows will block acceptance. The tool is an offline review gate, not a production ingestion path. Even CONCORDANT_REVIEWED does not independently authenticate a supplied reference file.

A wrong binary outcome reverses the win/loss label and can corrupt PnL, calibration and detector validation. Do not use this source as an outcome oracle without independently reviewing full identifiers, token ordering and actual payout evidence. For subsequent population replication, preserve raw source versions, independently resolve all market IDs, verify payout vectors and record source availability times. Never train on future outcomes as features.

## Publication boundary

Base main: 9c279334a5dd77ef5fc30c9c2333c9f43aac5a5a. This is a standalone research draft; existing publication checks and repository-wide tests have not been executed in the local environment because a complete clone could not be retrieved. Keep draft until the checks in AGENTS.md and review conditions are satisfied. No external code copied, no new wallet link established, no change to NO_EDGE_VALIDATED.

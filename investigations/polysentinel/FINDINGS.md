# Findings: polysentinel

## F-001 | CONFIRMED | PolySentinel did not detect the 2026 Ballon d'Or affair before it was revealed: its first local cycle is dated October 27, 2026 at 17:07 UTC, after the Upside post of October 23 at 15:17:49 UTC
- Sources: sources/studies/ballon_2026_20261030/results.md
- Method: Replay under a frozen plan (sources/studies/ballon_2026_20261030/PROTOCOL.lock) requiring both a transaction date and an observation date before the cutoff
- Limits: Verdict NOT_DEPLOYED_THEN_AND_COUNTERFACTUAL_NOT_ESTIMABLE: zero alerts on zero data, which measures no failure of sensitivity
- Links: none

## F-002 | SUPPORTED | Assuming immediate availability of trades and an open market status, the conditional replay ranks Thin-Disclaimer-Life as a priority on October 13 at 18:50:49 UTC, rank 1 of 74 pairs, while real historical capacity stays NON_ESTIMABLE
- Sources: sources/studies/detection_20261030/results.md ; sources/studies/signal_validation_20261030/results.md
- Method: Unchanged detector replayed, labels compared after sealing, reproduced in fresh copies
- Limits: Exploratory and conditional. Rank shared with another wallet. The case informed the design of the system, so it is no independent validation. Independent unit: one affair
- Links: ballon-dor-wallets:F-012

## F-003 | UNRESOLVED | The independent rarity, real historical observability and predictive value of the Thin-Disclaimer-Life signal remain NON_ESTIMABLE
- Sources: sources/studies/signal_validation_20261030/results.md
- Method: Frozen exploratory study, delay scenarios of 0, 60, 300 and 900 seconds
- Limits: No group of verified non-insiders, no dated order book
- Links: none

## F-004 | SUPPORTED | On replay scenario S_A, with a control universe, no publicly named account gets a priority: 10,612 wallets seen, 722 wallets in the queue, Thin-Disclaimer-Life at behaviour without priority
- Sources: sources/studies/pipeline_replay_20261101/derived/interim_R3_S_A_20261101.json.gz
- Method: Interim comparison on sealed S_A only, amendment 001
- Limits: Partial: one scenario of five, named accounts are no ground truth. The $2,500 filter and the rotation may hide small buys, cause not verified
- Links: none

## F-005 | UNRESOLVED | The chronological evaluation of October 27 is NON_ESTIMABLE: 0/8 events allow the directional calculation, and no insider detection rate is estimated
- Sources: sources/studies/chronological_20261027/results.md
- Method: Selection frozen before reading outcomes
- Limits: Collection window too short, events conditioned on the collected catalogue
- Links: none

## F-006 | SUPPORTED | The fund flow module links funds on 3 real cases (Deposit Wallet, Proxy, Safe) with a level of proof per relation, on no real ChangeNOW or XMR case
- Sources: sources/docs/FUND_FLOWS.md ; sources/evidence/fund_flow_20261101/audit_claims_2.json
- Method: Real receipts, two independent audits, tests on real data
- Limits: Shadow mode, changes no category or score. Not replayed during consolidation
- Links: none

## Contradictions

- F-002 and F-004 do not cover the same universe: the conditional replay of October 30 ranks Thin as a priority, scenario S_A with a control universe gives it none. This gap forbids presenting the first result as a detection.

## Missing to conclude

- Ground truth on insiders, which does not exist: no precision or recall can be computed.
- The end of the replay (scenarios S_C, S_G, S_B, S_L), its sealing, then the final comparison.

## Prospective monitoring

- Collector and sealed registry running: decisions are sealed before entering the database, with the inputs needed to replay them.
- Signal engine in shadow mode: it refuses to run while the collector is in reduced mode (`sources/evidence/signal_engine_v1/status.json`).
- For a future event: compare sourced public announcements with the kept `emitted_at` time, and conclude nothing about private information from scores alone.

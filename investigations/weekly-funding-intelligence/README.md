# Weekly funding intelligence

Count distinct Polygon trading accounts that actually received a service-linked credit in each ISO week. The pool addresses and face denominations can be checked against the two pinned original source files with `python3 -m weekly_funding.registry_evidence`. The replay verifies the saved registry offline. The archived analysis starts on 13 April 2026, the first week of the historical f2020 payee cohort. Its first reporting window is the eight closed weeks ending on 15 November. The snapshot was assembled on 22 November 2026. The open week W47 is excluded.

[Chronological report and chart](results/REPORT.md) · [Weekly ledger](results/weekly_funding.csv) · [Wallet receipts](results/wallet_funding.csv) · [Machine-readable results, sets and coverage](results/weekly_funding.json) · [Audit of earlier work](AUDIT.md)

## Reproduce offline

From the root of a checkout, use Python 3.11 or newer. All runtime dependencies are in the repository or the standard library.

```bash
cd investigations/weekly-funding-intelligence
python3 -m unittest discover -s tests -v
python3 verify.py
python3 -m weekly_funding --week 2026-W46 --out /tmp/funding-W46
python3 -m weekly_funding --from-week 2026-W39 --to-week 2026-W46 --out /tmp/funding-eight
python3 -m weekly_funding --out /tmp/funding-history
```

Single-week replay reads earlier frozen weeks for first-observation and prior-week comparisons. The verifier checks the frozen protocol, input digests and all five published outputs with network sockets disabled. Archive inputs referenced outside this folder are relative to the repository root.

## Capture another week

```bash
python3 -m weekly_funding.refresh --week 2026-W47 --dest /tmp/capture-W47
```

Run after the requested week closes. The command retains settled range manifests, exact queries, block brackets, funding logs, the sample of trading accounts, activity and pricing evidence, route checks and the report. Interrupted log capture resumes at unresolved ranges. A changed completed range requires a separate snapshot. The new directory also records the checkout commit and observation cutoff. Historical series can be extended with the individual modules' date ranges, saved snapshots and a common activity cutoff. Use a fresh destination for each revision. For consecutive weekly captures, pass the preceding report with `--previous-report`. Missing intermediate history makes new-wallet and comparison claims unavailable.

The GitHub workflow runs offline review on pull requests. On the default branch it captures the preceding closed week on Mondays at 08:23 UTC, with a 35-minute job limit. It retains scoped results and inputs as an Actions artifact for 90 days. Successful promotion to the Git history requires normal review. Core range gaps and unavailable PM classifications produce a failed capture with diagnostics. Trace caps and the fixed Ethereum native archive remain visible in successful scoped reports.

## What enters a count

| Evidence | Rule |
|---|---|
| CONFIRMED_DIRECT | An allowlisted public hot-wallet origin or an official withdrawal log credits the exact Polygon trading address. For an exchange the confirmed event is the payment from that labelled origin. Service ownership remains a sourced attribution and the individual exchange order is unknown. |
| SUPPORTED_INDIRECT | A real source credit reaches a distinct documented trading account through a checked forward. Native amounts use a conservative lower bound. |
| POSSIBLE | Includes actual Polygon receipts from the commingled route, signer-only associations and equal address strings across chains. Only the exact Polygon receipts enter the separate candidate USD series. |
| UNKNOWN | Insufficient source, endpoint, history or path evidence. A missing indexer response never proves absence. |
| REFUTED | A proposed terminal is identified infrastructure, custody or a burn address. The observed transfer remains in gross source intake. |

An address is counted once per service/week, including when direct and indirect sets overlap. Verified intersections, service-only sets and unions are explicit in the JSON. Direct-recipient intake is distinct by chain and address. Summing across proof tiers or weeks can double count an address. The CSV uses the final UTC receipt week, including when an intermediate leg occurred in an earlier week. An `UNKNOWN` global count can coexist with a zero inside the observed sample.

Three different dollar amounts are reported. Gross source intake includes infrastructure and candidate routes. Exact-recipient USD sums transfers to observed Polygon trading addresses. Verified funding USD sums eligible final credits once, per trading address, before applying the 1,000 and 10,000 USD thresholds. Values use the most recent preceding DeFiLlama daily price within 36 hours, with confidence at least 0.9. Unpriced units remain in the wallet ledger, the known subtotal stays available, and a complete USD total is marked unknown. Native roots have the event identifier `native:root`. ERC-20 and pool events use the actual receipt log index.

## Ascertainment and follow-up

- The independent denominator consists of order owners from the three exchange contracts in `monitoring/phi_monitor/chain.py`. Three eight-block windows start at 1/6, 1/2 and 5/6 of each week's Polygon block span. Each week has its own frame. A covered rate counts only funded accounts also present in that week's frame. Population-wide rates are unknown.
- The retrospective account index combines those execution witnesses with the archived ChangeNOW trading accounts and Ballon d'Or fills. Polygon withdrawal recipients and tagged-hot-wallet payees are queried directly. The mixed rail adds exact historical/frame matches, documented signer/proxy pairs and up to 64 deterministic payees per week, ordered by SHA-256 of ISO week plus address. Incomplete ascertainment makes these candidate counts lower bounds. Equality of an Ethereum address and a Polygon address only produces a possible association. No identities are resolved.
- Polymarket v2 activity is checked against the requested user, event type, time, side and pagination. Earliest indexed trade, strictly later BUY, transaction, market, notional, observed later market totals and daily economic PnL have separate fields. A short market identifier is preserved in its original length with the prefix `api:`. A fill at the same second needs independent ordering and is excluded from the strictly-later query. Empty follow-up or a capped sample can leave the first buy unknown. Subsequent observed market buys are lower bounds from distinct visible API records. The archival PnL column is a separately dated September observation. Its incompleteness flag is preserved.
- Indirect discovery covers registered signer/proxy token routes, a bounded first native send after Polygon Tornado withdrawal, and the exact origin keys of archived Relay deposit records. The native path requires an undelegated EOA, a single nonce increment and a successful plain 21,000-gas transfer. The attributable minimum is the lesser of the sent value and the withdrawal less the ending balance and transaction fee, floored at zero. Same-token signer forwarding requires zero opening balance and no competing transfer before the final credit. A matched Relay key stays pending until both chain legs verify. The optional historical `weekly_funding.bridge` screen checks eligible Ethereum payees against successful Relay orders to Polygon. Positive attribution requires a full lower-bound origin in ETH, the actual order ID and matching Polygon receipts from two endpoints. The v2 historical API is rate-limited and v3 requires an API key. The scheduled public capture omits this optional query and reports its absence. Other bridges, customer deposits, swaps, later hops, off-chain payouts and unobserved addresses remain unresolved.
- Test outcomes and predictions never enter attribution. The frozen protocol fixes the five endpoints, two services, controls, time holdout, eligibility gates and multiple-testing family. An optional `snapshot/matched_panel.json` can carry independently frozen covariates, outcome primitives and their observation times under the protocol hash. Without the necessary case/control and price history the report returns NOT_TESTABLE.

[Official pool registry](https://github.com/tornadocash/docs/blob/en/general/tornado-cash-smart-contracts.md) · [Withdrawal ABI](https://github.com/tornadocash/tornado-core/blob/master/contracts/Tornado.sol) · [Polymarket v2 API](https://data-api.polymarket.com/v2/docs) · [Frozen statistical protocol](PROTOCOL.md)

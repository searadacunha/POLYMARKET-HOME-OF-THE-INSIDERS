# Replay protocol: KPMG funding graph, election trading anomalies and paired wallets

**State:** pre-replay specification. This file does not claim to have collected external RPC data. The exploratory target populations are drawn from **already published suspicious cases**, so tests of statistical significance must account for **ascertainment and multiple comparisons**. Source reports are not independent training/validation labels.

## Phase A — KPMG earnings network (first priority)

1. **Population:** keep the core 19 pseudonyms and their 3 separately discovered extensions in `KPMG_WALLETS.csv`. Four full Polygon proxies are publicly linked; resolve the other 18 from exact contemporaneous public profiles, not from similar names. Do not assume all 22 traded the 21 KPMG markets.
2. **Primary chain reconstruction:** for each of the [11 Bitquery-reported handoffs](KPMG_HANDOFFS.csv), obtain the source Polymarket withdrawal event (proxy or deposit-wallet owner), bridge order and destination funding event. Store `chainId, contract, transactionHash, logIndex, blockTimeUTC, tokenDecimals, amountAtomic, amountDecimal, bridgeOrderId, participatingAddress, flowRole, source`. The first transition uses Polygon `0xafed93e173e88e6b1be9f4990bc95770c473c978cd8c0eeb064a58552872e696` and final credit transaction `0xaa6df4010b275200a3fe3617886b1d389d8db53afef1028ac7fabd1f73358d90`. **Do not conclude an edge from time/amount alone**; match both legs through primary protocol records.
3. **Account graph:** separate public platform proxy, deposit-wallet signing key, Solana intermediary, bridge router, exchange hot wallet and deposit endpoint. Count direct value paths, hops, shared credited destinations, ordinary high-fanout service exposure and unresolved legs separately. Run service-label/contract negative controls, including the bridge address `0xf70da97812cb96acdf810712aa562db8dfa3dbef` which paid >2m unrelated wallets in the source reconstruction.
4. **Market graph:** freeze the exact 21 KPMG audited market `conditionId`s and their SEC 8-K `Item 2.02` accepted timestamps. Rebuild open/close/add/redeem and net exposure, including trades after disclosure, fees, unresolved contracts and leftover positions. Use the *actual paid entry prices by market* to compute market-level expected wins, **not** a constant p inferred from 14.3/21.
5. **Statistical test:** use the optional `--market-csv` input of `tools/check_intake.py` to calculate an exact market-level Poisson-binomial tail for distinct market probabilities. Source-cited **19/21, expected 14.3, p = 0.0084** cannot be reproduced without the original 21 price probabilities. The model assumes independent market outcomes conditional on entry prices; account selection after high success, shared industry earnings exposures, and multiple cohort scans can invalidate its unconditional interpretation. Run matched non-KPMG earnings controls plus placebo candidate clusters and out-of-sample checks.
6. **Explicit stop condition:** no named KPMG employee/proxy identification, insider allegation or **confirmed common ownership** without permitted independent evidence. Judicial inquiry reporting about one company cannot be mapped to this multi-company network by theme.

## Phase B — XFM 18-wallet receipt subset (second priority)

- The [9 June 23 split transaction hashes](XFM_NINE_SPLITS.csv) are the first fixed primary-chain sample. Decode original collateral split, CTF TransferSingle/TransferBatch, recipient addresses, token IDs, share quantities and fee events. Recompute **1,779.93 matching Yes and No shares** independently. Do not treat complementary tokens or same transaction as a suspicious direct transfer without establishing what the contract actually did.
- Obtain and verify MSR's 117 receipt matches for the **18-wallet subset** separately from the **97 selected profiles** and **47 complete pairs** used for sequence analysis. Do not move denominators between findings.
- Compare **582 matched-price groups** with 460 zero-gross-edge / 122 adverse / 0 favorable. Reconcile the 15.6271 PUSD reported rebates against order-level qualifying fees. The motive could include liquidity provision, independent execution or activity-based incentives; only operator evidence could distinguish them.

## Phase C — ACDC US midterms (third priority)

- Obtain the 544-wallet, 591-round-trip, 22-market dataset from the authors or rerun source queries across *all* applicable Polymarket election markets. Reconstruct precise filter: purchases >= $500 at at least 95 cents, almost total exit within six hours, less than 1% realized price advantage; verify if rewards/fees were counted. Fix exact filter from published methods before results.
- Differentiate **counterparty self-trades**, two controlled wallets, ordinary market makers and unrelated counterparties. Compute net value paid, revenue, cost and fees *for the same wallets*; $618,395 gross turnover is not at-risk capital and $34 total result is not necessarily the traders' complete PnL.
- Use matched markets at similar prices, liquidity, time to resolution and exposure to incentive programs as controls, plus null models for rapid round-trip frequency.

## Phase D — Ethiopia/Romania candidate volume farming

- Freeze exact market IDs and settlement rules on both original and replacement election markets. Resolve when outcomes became practically settled, when platform resolution happened and when the market remained tradeable.
- Extract complete trades with maker/taker, nonces and accounts, group actual **paired closed loops** only with continuous token balances; evaluate whether the alleged **$284m / $285m** Ethiopian figure, **38k+ loops**, and **9-second** median are reproducible. Count identical transaction hash/log index once. Model independent liquidity providers as negative controls.
- Romania's **99.6%** is reportedly the proportion *in selected weeks*, not the full multi-month trading period. Use the correct denominator and preserve market cancellations and open-state changes.

## Phase E — October 29 supply-chain attack (separate security evidence)

- Treat the [official postmortem](https://status.polymarket.com/cmvvek1i90eme14ruga1z6tuj) as authority on incident, vendor script and planned refunds. Treat [Bitquery's trace](https://bitquery.io/investigations/polymarket-hack) as a **third-party** account and bridge-flow reconstruction.
- Fix attack flow into Poly relayer-approved drains, attacker address `0x3f99139f1c5854bb628c2e576aaf638e99dffc18`, subsequent POL/bridge hops, and Ethereum recipients. Obtain transaction receipts and actual orders. A late transaction after the platform announcement need not mean the original vendor script was still live; distinguish event/action times.
- Derive distinct totals for **$2.7m drained, $1.2m goodwill, $3.9m returned/owed**, and Bitquery's **737 wallets / 985 drains / $2.73m**. Use snapshots and avoid equating POL value at different prices with exact USD reimbursement. The original `hacks-parallel` snapshot covers May/June and is not retroactively rewritten.

## Publication and reproducibility

Keep raw third-party material outside Git unless copyright, credentials, profile-privacy and size scans permit it. In every derived dataset, provide a provenance object, SHA-256 manifest, exact block identifiers and confidence status. Any unverified transfer remains labelled `THIRD_PARTY_REPORTED`, even when it has a full transaction URL but the original logs have not been decoded. Record negative controls and failed hypotheses in *technical* reports; public README promotes only actually source-backed new findings with no false claim of ownership or privileged information.

**No monitoring bot or ongoing scheduled collection is requested.** Use isolated worktrees/PRs, no force-push, no rewrite of the protected README or frozen historical evidence.
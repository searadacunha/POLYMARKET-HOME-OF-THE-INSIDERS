# Coordination analysis — what survived falsification

**2026-11-02.** This is a comparison of archived evidence with a new, purely **synthetic temporal module**. No new real-market cohort was fetched and no prospective detector score was changed. The hypotheses below are **not** claims of common ownership, collusion or insider trading.

## Keep financial, control and behavioral graphs separate

The existing graph already proves specific transfers. The new adapter exports them as **financial** edges only. The behavioral module reports pairs of observed buys of the same outcome within **5s, 30s, 60s, 5m, 15m, 60m**. A verified contract owner/signer link would belong to a *third*, explicit **control** graph, not be inferred from a common exchange or trade time.

- A direct, non-custodial value transfer can be *financially linked* while signers remain separate persons.
- Common funding from **UNKNOWN**, `SERVICE`, `EXCHANGE`, `BRIDGE` or `OMNIBUS` sources is excluded from proven shared-funder clusters.
- An exchange deposit address cannot be assigned to an individual, and use of the same high-volume service is not evidence of a common owner.
- Only the exact transaction, chain, amount and provenance may confer `ONCHAIN_CONFIRMED`. Matching timestamps/amounts are only candidates. Same transaction could contain unrelated makers.

## Existing real-world controls that overturn naive interpretations

| Observed pattern | Proper comparator/result | Verdict |
|---|---|---|
| Two accounts directly exchange a small ETH amount | 1 of 55 named key pairs; 0 of 1,431 control pairs, **pairs not independent** | **Transfer confirmed**, no significance or shared owner inferred |
| First purchase within an hour of funding | 9/11 named vs 32/39 fresh controls, `p=0.69` | **REFUTED as distinctive** in tested scope |
| Same Kane market, quick withdrawals | 10/20 comparable sellers also withdraw within five minutes, `p=0.29` | **REFUTED as distinctive** |
| Close redemptions | One batch of 2,711 accounts in 136 transactions | **REFUTED as link** |
| ChangeNOW-like 90% forwarded within 5min | 18/57 nearby recipients, 31.6% | **Common**, not individual evidence |
| ChangeNOW twin payouts under 10min | 9/57 recipients, 15.8% | **Not distinctive** |
| Similar amount/date outflows from service | 10/530 outflows within 10% amount over a 10-hour window | **Collision-prone candidate**, never proof |
| `Thin-Disclaimer-Life` detected under restricted conditional replay | Sealed S_A replay includes 10,612 wallets/722 queued; Thin gets no priority | **Historical detection non-estimable**, contradictory universe |

Sources: [master report](../../MASTER_REPORT.md), [Ballon d'Or findings](../../investigations/ballon-dor-wallets/FINDINGS.md), [flow trace](../../investigations/ballon-dor-flow-trace/FINDINGS.md), [ChangeNOW false positives](../../investigations/changenow-proof/sources/reports/FALSE_POSITIVES.md) and [PolySentinel findings](../../investigations/polysentinel/FINDINGS.md).

## Statistical protocol for a future confirmatory test

1. **Population first:** universe defined by *trading before outcome*, not wallets selected by wins or press. Record market ID, token/outcome, exact price paid, size, liquidity, era/contract and wallet activity. Price in a binary market is an *imperfect* implied probability (spread, fees, risk premia), not a known physical probability.
2. **Immutable plan:** set 6 time windows, low-probability bins, large-size thresholds, capital freshness definition, exclusions, control strata and expected budgets **before** reading resolved winners.
3. **Exposure before event:** group independent wallets buying the same outcome at their **observed_at** time; distinguish repeated fills/order splitting, market-makers, hedges and the SAME economic account across different addresses only if contract ownership is verified.
4. **Matching:** calendar/day of week, market family, price zone, liquidity, volume, time to resolution, maturity and event cluster. For low-price markets, compare to low-price buyers rather than average wallet.
5. **Null:** block-shift each wallet's entire trading train within eligible market intervals to preserve intra-wallet bursts. Then use order, market and event clustered permutations to stress-test exchangeability. **One circular shift test is not sufficient**: trading intensity, news shocks, market closures and nonstationary activity are confounds.
6. **Multiplicity:** log *all* windows/outcomes/markets/cluster definitions; correct global selection using max-T or permutation-based FWER, with BH-FDR explicitly only for exploratory discovery. Existing collective study logged **140,114 comparisons**, Bonferroni threshold **3.57e-07**; do not recycle it as a threshold for a new experiment.
7. **Future leakage:** `first_seen_by_us` not wallet creation; event announcement and book snapshots must be observed at that time. Never use a newly discovered market winner or later Gamma labels as predictors.
8. **Validation:** train thresholds on TRAIN, freeze hashes, then compare VALID/TEST and ongoing future alerts. Report Wilson/clustered confidence bounds, negative outcomes and coverage gaps.

## Executed synthetic experiment (NOT real evidence)

The new `temporal.py` was run on **180 constructed trades** representing bursts across three markets with outcome grouping. It returned **2,736 pair/window records**; for the 5-second statistic, **90 observed pairs** vs a **median 9** from 199 independent wallet-train shifts. The finite-simulation empirical `p=0.005` belongs **only to these artificial records**. Timing ≈0.05s for window extraction, ≈0.18s for 199 shifts (isolated Linux container, not Mac). This proves deterministic execution of a simple null; **not** false-positive control, predictive skill or insider evidence.

13 offline unit tests passed, including a future-observation exclusion, same-tx multiple log indices, service-funder exclusion and non-duplication. Original full PolySentinel baseline was NOT executed for comparison. [TOOLS_BENCHMARK](TOOLS_BENCHMARK.md).

## Real-world case conclusions

- **Ballon d'Or:** direct key-to-key funding and additional wallet financing are real and worth further chain tracing. No empirically discriminating timed coordination of the eleven was demonstrated; unidentified other operators remain possible.
- **Maduro/Iran:** eight accounts have a demonstrable funding network. The report's post-winner selection makes any rarity or insider interpretation fragile. Earlier out-of-sample executable trading signals failed; one predictive-looking lead lacked demonstrated capture.
- **ChangeNOW:** shared service and near-synchronous payouts are explicitly non-individualized and frequently occur in controls.
- **PolySentinel:** shadow detector must not be altered based on these exploratory results. New future alerts require frozen independent testing.

**Final classification:** money transfers **CONFIRMED** where cited; significant real-market behavioral coordination **NOT DEMONSTRATED**; individual controller **UNRESOLVED**; inside information **NOT DEMONSTRATED**; synthetic null **EXPLORATORY** only.


## Adversarial integrity addendum (no new coordination claim)

The original temporal code silently skipped conflicting duplicated fills at the same `transaction_hash + log_index + wallet + market + outcome`, even if the amount or price changed. Its null model could therefore depend on input ordering. The patched `observed_trades` now raises an explicit error for the conflicting fill, and a negative-control test confirms that identical repetitions are still deduplicated. Different log indices inside one transaction remain distinct.

The original transfer ledger included `raw_amount` in its event identity; a contradictory amount on the same transaction/log could become a second financial edge. The new identity uses chain/tx/log, with a conservative fallback for unindexed documentary events, and refuses payload conflicts. **No previously published coordination finding is changed:** this protects future data, not a newly discovered link.

`coverage.py` detects a 1-block gap in a synthetic 30-block period and refuses to mix a V1 scan with a V2 query, but no live market/contract coverage is yet certified. Thus the criterion **“all observable bettors in a market” remains unmet**. The first real comparison still requires the historical market tape, matched controls, protocol-era event decoder and independently timestamped observations. Current hypothesis classification (including the refuted fast-funding and common-service heuristics) remains unchanged.

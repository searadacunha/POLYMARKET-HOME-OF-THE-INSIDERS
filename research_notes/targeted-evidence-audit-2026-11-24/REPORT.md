# Targeted evidence audit — 24 November 2026

Status: descriptive follow-up, not prospective validation. Base: 9c279334a5dd77ef5fc30c9c2333c9f43aac5a5a (merged PR 112). No new raw evidence, no modified historical claims, no README changes.

## 1. Does the f2020 cohort's loss depend on outliers?

Input: [wallet_summary.csv](../../investigations/data-completion-20261123/results/wallet_summary.csv), Git blob 5b11fc19878e4866a1594dadac68f8d8c7e03480. Exclude ten addresses without fills and two active addresses with partial PnL from complete-case calculations. No service attribution is inferred from the mixed route.

| Complete-case sensitivity | Known trading PnL (USDC-equivalent units as reported by the source) |
|---|---:|
| 141 complete active accounts (28 positive, 113 negative) | -43,586.119089 |
| Excluding largest loss | -33,275.189594 |
| Excluding five largest losses | -16,470.831697 |
| Excluding ten largest losses | -8,907.903777 |

All 153 addresses' known PnL parts sum to -43,650.447579. Losses are not confined to the largest ten losers. This is not a matched comparison with ordinary traders, does not establish a causal effect of funding, and does not exclude informed trading by individual accounts. The sensitivity is descriptive and selected after seeing the cohort; it is not a hypothesis test.

## 2. Does co-betting recover the Nobel cohort before the price move?

Inspired by the behavioral overlap capability in [Samy-z/PolyClusters](https://github.com/Samy-z/PolyClusters) (MIT, method inspiration only; no external code copied). This is a deliberately minimal presence/absence diagnostic, not a reproduction of its weighted clustering algorithm.

Input: [accounts_activity.csv](../nobel-strict-replay-2026-11-20/data/accounts_activity.csv), Git blob a19179f326087574c4255632504fc7102ba5b127. Count distinct (market label, outcome) BUY keys strictly before each cutoff; collapse repeated purchases, exclude sells. Labels are safe only within this archived case, not as cross-dataset market identifiers.

| UTC cutoff (exclusive) | Active buyers | Pairs sharing >=1 key | Pairs sharing >=2 keys |
|---|---:|---:|---:|
| 2025-10-09 23:00:15 (price confirmation in existing replay) | 1 | 0/0 (undefined) | 0/0 (undefined) |
| 2025-10-10 09:00:00 (announcement) | 8 | 28/28 | 3/28 |

All eight eventually bought Machado Yes. Three pairs also shared Sudan's Emergency Response Rooms No. Within this already selected group, co-buy overlap cannot identify a group before the price confirmation; a solo-wallet alert can. No platform-wide controls, no measure of co-betting rarity or owner attribution, no comparison of detectors' false positives. The public-information timestamp and price confirmation are distinct.

## 3. External methods worth importing next — acceptance gates

- [ForesightFlow datasets](https://github.com/ForesightFlow/datasets): CC-BY 4.0 case inventory and public-news/event timestamp datasets. Import only selected, version-pinned cases and timestamps; preserve attribution and distinguish judicial outcomes, allegations, public reports, proxies, and true first-public timestamps. Compare against existing case inventory before collecting.
- [SII-WANGZJ/Polymarket_data](https://huggingface.co/datasets/SII-WANGZJ/Polymarket_data): independently published V1/V2 historical fills. Select only the blocks and case/control markets needed to compare transaction hash + log index with the repository's ledger; log omissions and disagreements, not just matches. Do not import the full 279 GB by default. Its coverage ends on 4 October 2026 and does not include all later contracts.
- [veeradittya/polymarket-insider-detection](https://github.com/veeradittya/polymarket-insider-detection): news anchoring and broad unsupervised scanning. Independently implement time-of-first-observation semantics; no unlicensed source code reuse.
- [Samy-z/PolyClusters](https://github.com/Samy-z/PolyClusters): extend the overlap diagnostic only with canonical condition IDs, pre-cutoff positions and popularity-weighted matching; include active, matched controls and report event-blocked false-alert burden. Require a holdout separate from Nobel/Iran before any deployment.

No external raw data imported in this change. No candidate ranked as an insider; no claimed predictive edge. Preserve NO_EDGE_VALIDATED.

## Reproduce

From repository root:

```sh
python3 research_notes/targeted-evidence-audit-2026-11-24/verify.py --test
python3 research_notes/targeted-evidence-audit-2026-11-24/verify.py
```

The two synthetic Python unit tests passed in an isolated environment. Published input tables were independently aggregated in JavaScript through the GitHub connector; the full Python replay and repository-wide CI have not been run in that environment. Review before merge.

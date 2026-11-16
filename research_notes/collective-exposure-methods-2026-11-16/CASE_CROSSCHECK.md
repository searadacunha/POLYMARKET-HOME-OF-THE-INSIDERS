# Existing Iran evidence: original archive arithmetic and scope correction

**Source artifacts (pre-existing in this repository):**

- [February-28 trade-band descriptive JSON](../independent-forensic-audit-2026-11-08/evidence/feb28_noyes_descriptive.json)
- [38-account roster CSV](../x-history-2026-11-06/verification/data/g38_accounts.csv)
- [November 8 independent forensic audit](../independent-forensic-audit-2026-11-08/REPORT.md)

The 8 November audit had **already** contrasted the 36 selected February-created proxies against other accounts. This is not a newly discovered cohort and the original archived source remains unchanged.

## Independent arithmetic on the archived summaries

| Same-market February 28 observation | Selected cohort | Other sampled accounts |
|---|---:|---:|
| Accounts in the compared sample | 36 | 733 |
| Earliest BUY NO strictly precedes earliest BUY YES | 20 | 16 |
| Share of the selected sample | **55.5556%** | **2.1828%** |

Arithmetic only: ratio of observed percentages **25.4514×**; associated cross-tabulation odds ratio **56.0156**. These are descriptive summaries of a non-random, case-selected cohort and a fixed archived trade band. In particular, they **do not imply** a 25× forecasting advantage, a causal effect, or a valid unadjusted statistical test.

A further important constraint: of 35 selected-cohort accounts with a first observed YES purchase, only **6** had their **first YES** between 27 Feb 20:49 and 23:35 UTC on this single market (versus 9 of 345 other YES purchasers). It is wrong to generalize the broader cross-market first-YES window to all 36 accounts on this market.

## What the original sources really say

- **36/36 in the roster**: NO preceded YES when considering the relevant Iran deadline-market history across markets. It does not certify that any position was sold, or that the sign of portfolio exposure reversed.
- **20/36 on the one February-28 market**: first observed BUY of NO precedes first observed BUY of YES within a bounded activity tape.
- **15/36 YES-only and one with no BUY on that specific market**: these are not NO-before-YES there.
- **16/733 other**: a comparison already available in the archive, not an untouched evaluation sample or a matched control.
- **Window size**: 42,000 trades in 84 pages, as reported by the original audit. The entire underlying trade-band tape has **not** been reproduced by this new note. A finite page/tail sample may omit some prior trade history.
- **Inferential field**: the source itself sets `p_value: null`, because the cohort was selected after its salient outcome.

## New decision from the crosscheck

**The immediate unexploited part is not another NO-before-YES count.** It is the distinction between:

1. `NO(D1) + YES(D2)`: an interval payoff across two deadlines;
2. two-sided inventory and ordinary liquidity operations;
3. a net exposure *rotation* with a genuine change in the payoff vector;
4. a **collective** rotation across accounts independently linked or grouped using only prior data.

If (3) cannot be reconstructed from raw balances and full histories, mark it UNRESOLVED. Only after that should (4) be submitted to a fresh, event-wide out-of-sample test.

## Reproduction

Run [recompute.py](recompute.py) against the original two archive artifacts. It refuses denominator inconsistencies, wrong study scope and a malformed 36-wallet roster. It does **not** reproduce or independently fetch the 42,000 individual trades and makes no chain-level or insider attribution claim.

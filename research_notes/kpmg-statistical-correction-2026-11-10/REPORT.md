# KPMG market statistics: cohort, outcome-rule and timing correction

**10 November 2026.** This follow-up corrects the interpretation of the frozen
[7 November market reconstruction](../financial-links-replay-2026-11-07/REPORT.md).
It leaves that report, its source tables, its original generator and its
financial-transfer evidence unchanged. The corrected current summary is in
[Verified Financial Findings](../../VERIFIED_FINANCIAL_FINDINGS.md#6-kpmg-client-earnings-bets-fourteen-account-to-account-handoffs).

## 1. The original 19 accounts and expanded 22 accounts have different records

The [account register](../financial-links-replay-2026-11-07/data/kpmg_accounts.csv)
labels 19 accounts `ORIGINAL_19` and three accounts `EXPANDED_3`:
`perlgrow`, `boosthero` and `bostonguy`. The
[market CSV](../financial-links-replay-2026-11-07/data/kpmg_earnings_markets.csv)
already carries both scopes. The current findings index previously introduced
a network of 22 accounts but quoted only the original 19 accounts' statistics.

Replaying the selected KPMG rows gives:

| Scope | Accounts | Markets | Aggregate main side wins | Every account's main side wins |
|---|---:|---:|---:|---:|
| `core19` | 19 | 21 | 20 | 18 |
| `all22` | 22 | 21 | 20 | 17 |

These are counts of market outcomes, not counts of profitable accounts. The
scope expansion changes the strict outcome on Amer Sports: its archived
account main sides become opposed. The two scopes must not be substituted
for each other in a headline, probability calculation or validation check.

## 2. The two outcome rules are different events

The original [generator](../financial-links-replay-2026-11-07/tools/kpmg_markets.py)
first retains an account/outcome when its net recorded trade balance exceeds
one share at the cutoff. Among these retained outcomes, it totals cumulative
purchase cost. Sales affect whether an outcome remains eligible; the code
does not reduce those historical purchase costs to the cost basis of the
remaining inventory.

- **Aggregate main side:** the outcome with the largest summed purchase cost
  across the cohort's retained outcomes. A success occurs if that side wins.
- **Every account's main side:** the code first selects each account's own
  largest-cost retained outcome, then asks whether all selected outcomes win.
  A smaller losing hedge does not automatically fail this rule.

The earlier phrase "if any account's losing side counts" was therefore too
broad. The more precise phrase is **every account's main side wins**.

There is a separate error in the probability model. The generator uses the
same `p_main_side_cost_weighted` vector for both success rules. These prices
describe the aggregate main side. When accounts have opposed main sides on
a binary market, the event "every account's main side wins" is impossible
under either resolution; its probability is zero, rather than the aggregate
main side's positive reference price.

| Scope | Market | Account main sides | Reference price reused by the original model |
|---|---|---|---:|
| `core19` and `all22` | Dollar Tree, 3 December 2025 | No and Yes | 0.81 |
| `core19` and `all22` | General Mills, 18 March 2026 | No and Yes | 0.20 |
| `all22` only | Amer Sports, 18 November 2025 | No and Yes | 0.886 |

The archived Poisson-binomial arithmetic can be reproduced, including the
approximately 0.040 tail for `core19` and 0.124 for `all22` under the strict
rule. Reproducing those numbers does not validate them as tail probabilities
for the stated event. This is an event-definition problem, not evidence
that the financial transfers or the descriptive outcome counts are false.

This follow-up does **not** substitute a smaller tail and promote it as a
finding. The cohort was selected retrospectively for its record, the market
probabilities are purchase-price proxies rather than independently calibrated
forecasts, and the market outcomes need not be independent. Fixing one part
of the null model does not resolve those limitations. The dated verifier
reports descriptive results and the opposed-side cases; it calculates no
inferential p-value.

## 3. Not all 21 cutoffs are SEC timestamps

Both scopes contain:

| Cutoff stored in the market CSV | Markets |
|---|---:|
| SEC acceptance of an Item 2.02 filing | 19 |
| Market-close fallback | 2 |

The fallback rows are **Amer Sports quarterly earnings** and **CarMax up or
down after earnings**. The latter is a price-direction market, not another
EPS beat/miss question. All 21 cannot therefore be described as positions
held at the SEC results filing.

Even where an SEC acceptance timestamp exists, it does not establish the
earliest public disclosure of the earnings result. For example, the StoneX
row is a market dated 18 November 2025 while its stored SEC acceptance is
24 November. The source generator explicitly allows this filing delay.
Issuer releases and other first-publication evidence would be needed before
interpreting all pre-filing purchases as trades made before public news.

## 4. What this correction changes

The current findings index now names both populations, separates their two
outcome rules and reports the 19/2 cutoff split. It removes inferential tails
from that overview. The original files remain available as an auditable
record of the earlier calculation; their outputs should not be treated as
an independently validated insider-trading probability.

No transfer is reclassified by this statistical correction. The existing
14 handoffs, seven shared withdrawal destinations and account-to-proxy
mapping remain the subject of their own transaction-level checks. The
statistical replay here neither strengthens nor replaces those checks.

## 5. Reproduction and limits

From the repository root:

```bash
python3 -I research_notes/kpmg-statistical-correction-2026-11-10/verify.py
python3 -I research_notes/kpmg-statistical-correction-2026-11-10/test_verify.py
```

The first command reads the frozen account, market and statistical tables,
rederives the two descriptive records, checks the rule labels against the
recorded winners, rejects cross-cohort accounts and duplicate markets,
checks timestamp/fallback consistency, and compares the result with
[`summary.json`](summary.json). That snapshot records SHA-256 hashes of the
three input tables and the original generator. Normal verification writes
nothing. `verify.py --write` explicitly regenerates this follow-up snapshot.

The eight regression tests exercise opposed sides, falsely reported
unanimous wins, duplicate markets, leakage from the expanded cohort,
market-close fallback, absent SEC timestamps, invalid prices and both real
population counts. This is an offline audit of the published tables. It
does not re-download raw trading histories, verify issuer announcement
times, independently validate every earnings resolution, or remove
retrospective selection bias.

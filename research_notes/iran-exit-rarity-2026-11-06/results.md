# Exit-structure rarity: execution of the frozen 6 November 2026 plan

**Run date:** 19 November 2026, inside the plan's collection window (through 22 November 2026 23:59 UTC).
**Pre-registered verdict:** `UNDETERMINED`.
**What this does not show:** that the Iran cluster-E exit structure is rare, that any wallet pair has one owner, that anyone traded on non-public information, or that a trade taken from this statistic beats the market price. `NO_EDGE_VALIDATED` is unchanged.

The plan, code and `PROTOCOL.lock` were not edited. Lock check on 19 November 2026: 129 of 129 frozen hashes match. Raw Relay and trade pages stayed outside git, at the path named in `code/common.py`. Reduced records are in `data/`.

## Question that was frozen

Among early Yes buyers in other sudden resolutions, how often do wallets share two or more non-service Relay withdrawal recipients with one same other wallet, beyond what their number of recipients and those recipients' popularity predict?

The reference population was already known to contain groups of 9, 4, 2 and 2 wallets that share some recipient. The plan says that reference description is post hoc. Only the comparators were new.

## What was collected

| Step | Frozen command | Result |
|---|---|---|
| Comparator tapes | `code/col_20_populations.py` | 24/24 non-alleged markets `PASSED_WINDOW`, 0 archive rows missing, all `complete: true`. 179 trade-API requests, 179 successes |
| Reference exits | `code/col_30_relay.py reference` | 115/115 wallets from the 5 November 2026 archive. Positive control reproduced: 37 censored, S1 = 17, groups 9, 4, 2, 2 |
| Comparator exits | `code/col_30_relay.py` | 274 distinct wallets, every file `termination: END`. 400 Relay requests, 393 successes, 7 HTTP 429 responses retried |
| Classes | `code/col_40_classes.py` | 17 recipients shared by two or more wallets. All 17 classed `CUSTOMER` (2 to 9 distinct Relay users; none reached 25). One HTTP 429 retried |

Selection, by the frozen rule: 8 alleged markets left out; 17 populations below 10 wallets after removing known groups; 7 populations kept. No tape was incomplete. The seven markets are Eurovision 2026 (Bulgaria), the 2026 Colombian first round (Abelardo de la Espriella), the 2026 Seoul mayoral election (Oh Se-hoon), the November 2025 US government shutdown, Iran airspace by 31 July 2026, the 2025 World Series (Los Angeles Dodgers) and the Israel–Hamas ceasefire by 10 October 2025.

The Dodgers market is a sports outcome that the September 2026 archive had categorised as `other`. The plan already said that archive's sports exclusion could be imperfect. The frozen selector kept it. It did not enter the eligible rate.

## Primary numbers

Statistic M is the number of visible wallets that share at least two `CUSTOMER` recipients with one same other visible wallet. p_M uses 2,000 degree-preserving draws. A comparator is eligible only if a planted benchmark (9 wallets, 3 new recipients) reaches p_M ≤ 0.01 in at least 2 of 3 seeds. The verdict needs at least 10 eligible comparators.

| Population | Wallets after known-group removal | Visible / censored | M | p_M | Power seeds detected | Eligible |
|---|---:|---:|---:|---:|---:|---|
| Reference, Iran cluster E (post hoc) | 115 | 78 / 37 | 5 | 0.0010 (1 of 2,000 draws ≥ 5; null mean 0.56) | 3/3 | not a comparator |
| Seoul mayoral election, shock 3 June 2026 | 69 | 60 / 9 | 2 | 0.1034 | 3/3 | yes |
| US government shutdown, shock 13 Nov 2025 | 88 | 79 / 9 | 0 | 1 | 3/3 | yes |
| Israel–Hamas ceasefire, shock 8 Oct 2025 | 41 | 37 / 4 | 0 | 1 | 0/3 | no |
| Eurovision, Bulgaria | 35 | 32 / 3 | 0 | 1 | 0/3 | no |
| Colombia, first round | 16 | 13 / 3 | 0 | 1 | 0/3 | no |
| Iran airspace | 10 | 9 / 1 | 0 | 1 | 0/3 | no |
| World Series, Dodgers | 38 | 31 / 7 | 0 | 1 | 0/3 | no |

Eligible comparators: **2**. Comparators among them with p_M ≤ 0.01: **0**. Rate 0, exact 95% interval **[0, 0.84]**. Frozen verdict: **`UNDETERMINED`**.

The same classification is returned with known groups kept, with classes ignored, on the two geopolitics markets alone (0 eligible), and when contract or program-owned recipients are treated as services. Details are in `derived/results.json`.

An independent recount, using the withdrawal rule copied from the plan rather than the printed table, reproduces the reference (78 visible, 37 censored, 9 shared recipients, M = 5) and the Seoul row (60 visible, 9 censored, M = 2). The permutation p-values are those of `code/ana_50_stats.py`; recounting M does not re-draw the null.

## The one comparator overlap that is not empty

In the Seoul population, one wallet pair shares three recipients. Each recipient was classed `CUSTOMER`. Relay's own index, on the pages read on 19 November 2026, shows more payers than this pair:

| Recipient | Chain code | Relay users on the class pages | Example order |
|---|---|---:|---|
| `0x5b01ed6740816c54a1b7e27249e870c64f346723` | Polygon, no contract code | 3 | `0xdc84eae7ec39453327b22a5a57d2101074603115313e2a694bb5154cb55cd900` (14 March 2026) and `0x01770786c3219aea553fccf7c292bf84745a0b8947ad9c924766262b559dfc3c` (7 July 2026) |
| `0xcf3e79fe8a04a93a64eccddaf222d003710a45c9` | Polygon, 23-byte code, not flagged as a contract (matches an EIP-7702 delegation) | 4 | `0xe3ecee36c430b55d8640103bf0d52ff410d2d902d252892c002b55946b441aa8` (15 June 2026) |
| `0x2c0fb24e396617dac4808631aa0333cbd7160330` | Ethereum, no contract code | 5 | `0x17915658075560ce7d078d4e9199fd8afb5fc66d17c8e69908531d0c1dfe008f` (9 October 2026) |

The two wallets are `0x0a6d26d31b28fd5a84c301f8b27296612f3b1d0a` and `0xc7d02944a76b9f83b199e9090ecc92c82d241f8a`. p_M = 0.10 does not meet the frozen 0.01 threshold. Three to five Relay users on each recipient means the address is not a pipe used only by this pair. No earlier file in this repository labels these three addresses. Sharing them is not common ownership and not non-public information.

## Collection date

Comparator pages were read on 19 November 2026. Reference pages remain the 5 November archive. Amendment 001, written before any comparator exit statistic was computed, recomputes comparator recipients using only orders created on or before 5 November 2026 23:59:59 UTC and reuses the primary reference result. The reference archive has no later order. Comparator M, S1 and the verdict do not change (`derived/index_horizon.json`). The registry records this line as exploratory because the script is not in the lock.

## Post-hoc timing audit, not a second verdict

The frozen M uses lifetime withdrawals, including cash-outs after the shock. Restricting each comparator to withdrawals created strictly before its own shock gives **M = 0 in all seven populations** (`amendements/pre_shock_timing.py`, `derived/pre_shock_timing.json`). Seoul still has one shared recipient before its shock, but not two shared recipients with the same other wallet. This was looked at after the primary table existed. It is not a p-value and it does not replace `UNDETERMINED`. It does block any reading of these comparator overlaps as something observable at the shock.

## Adversarial reading

- **Not rare, and not shown to be common.** Two eligible comparators cannot support `RARE` (the cut is a rate ≤ 0.10 on at least 10 populations). The interval [0, 0.84] also cannot support `COMMON`. The correct frozen word is `UNDETERMINED`.
- **The reference p-value was not a discovery.** The plan says the reference shape was chosen because an earlier report already described it. p_M = 0.001 says that shape is tighter than a degree-preserving shuffle of the same wallets. It does not say other markets lack it.
- **Five populations had no power.** Treating them as "no excess" would have pushed the rate toward rare. The frozen power rule keeps them out. None of them had p_M ≤ 0.01 anyway (`comparators_with_excess_without_power = 0`), but that is a description, not the test.
- **Service screen did not bind.** All 17 shared recipients had fewer than 25 Relay users, so every one stayed `CUSTOMER`. A hot wallet that is popular outside Relay is invisible. Direct transfers, other bridges and wallets with no Relay withdrawal are censored, not evidence of isolation.
- **Lifetime exits are not an alert at time T.** The post-hoc cut above is the concrete demonstration in this sample.
- **One sports market entered.** The Dodgers row is a failure of the upstream category, preserved rather than deleted after the fact.
- **No executable price was tested.** There is no Brier score, log loss or after-cost return in this run. Nothing here promotes a surveillance rule to a trading signal.

## External methods considered and not imported

This execution does not reimplement an outside detector. Code already reviewed in this repository: `vsbtc/polymarket-insider-detection` and part of `Benja-Pauls/polymarket-insider-detection` use eventual winners, final prices or full-history accuracy (`research_notes/point-in-time-external-score-20261119/REVIEW.md`). `veeradittya/polymarket-insider-detection` has no holdout (`research_notes/github-tooling-audit-2026-11-06/REPORT.md`). `pselamy/polymarket-insider-tracker` was left undeployed in `integrations/forensic-intelligence/GITHUB_FORENSIC_DISCOVERY.md`.

`orcalayer/polymarket-insider-score-backtest` `scripts/early_score_check.py` (blob `10e167ec06839ab4ecfd098eaf636abef1b29204`) scores wallets on later price moves inside period A and then looks at period B. That split is a real walk-forward if the tape is complete, but the score is not computable at the order. The public script needs an OrcaLayer API key and a market file this repository does not have. Their numbers were not reproduced and are not findings of this run.

## Reproduce

From `research_notes/iran-exit-rarity-2026-11-06`, with the reduced files committed here:

```bash
python3 -I -B code/col_30_relay.py reference
python3 -I -B amendements/pre_shock_timing.py
```

`code/ana_50_stats.py` already wrote `derived/results.json` and appended the registry. Running it again repeats the permutations and adds registry lines; it is not required to read the result. Raw pages are local-only and are identified by the `page_sha256` fields.

## Chain for the verdict

Claim: the frozen rarity classification is `UNDETERMINED`. Source: `analysis_plan.md` verdict section and `code/common.py` `verdict`. Transactions: the reduced Relay orders in `data/relay/` and `data/relay_reference/`, classed in `data/classes.json`. Calculation: `code/ana_50_stats.py`. Test: eligible n = 2, which is below the frozen minimum of 10; the two eligible p-values are 0.1034 and 1. Result file: `derived/results.json`. Limit: this is not a statement that the structure is rare, common, criminal, or predictive.

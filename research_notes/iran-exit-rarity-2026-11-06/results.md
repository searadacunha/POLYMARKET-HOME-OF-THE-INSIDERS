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
| Reference, Iran cluster E (post hoc) | 115 | 78 / 37 | 5 | about 0.0012 on a long run of the primary seed; the stored 2,000-draw replicates are 0.0010, 0.0020 and 0.0025 | 3/3 | not a comparator |
| Seoul mayoral election, shock 3 June 2026 | 69 | 60 / 9 | 2 | 0.1034 | 3/3 | yes |
| US government shutdown, shock 13 Nov 2025 | 88 | 79 / 9 | 0 | 1 | 3/3 | yes |
| Israel–Hamas ceasefire, shock 8 Oct 2025 | 41 | 37 / 4 | 0 | 1 | 0/3 | no |
| Eurovision, Bulgaria | 35 | 32 / 3 | 0 | 1 | 0/3 | no |
| Colombia, first round | 16 | 13 / 3 | 0 | 1 | 0/3 | no |
| Iran airspace | 10 | 9 / 1 | 0 | 1 | 0/3 | no |
| World Series, Dodgers | 38 | 31 / 7 | 0 | 1 | 0/3 | no |

Of the 24 non-alleged populations, **17 have fewer than 10 wallets** after the known-group removal. The frozen rule needs 10 eligible comparators. Seven is already below 10, so the exit data cannot change the classification. Frozen verdict: **`UNDETERMINED`**.

Under the primary seed the power rule then marks 2 of those 7 as eligible (Seoul 3 of 3 plants, shutdown 3 of 3). Both have p_M above 0.01. Rate 0 of 2, exact 95% interval **[0, 0.8419]**. That interval covers the cuts for `RARE`, `UNCOMMON` and `COMMON`.

The same data do not fix the eligible count at 2. Seoul's power plants are 3 of 3 on the primary seed, 1 of 3 when known groups are kept (variant A) and 2 of 3 on the collection-date seed. The eligible count is therefore 2 or 1. Variant A does not add a known-group wallet: none of the 25 known-group addresses is in any of the seven populations. Variant B ignores classes on a file in which all 17 shared recipients are already `CUSTOMER`. Both variants reseed the primary graph.

Registry count beside the verdict: **7 real-data lines, 44 comparisons**, Bonferroni reference 0.05/44 = **0.00114**. The frozen code executed **142 permutation tests** (40 tests of an observed M, and 102 power plants). The Iran-airspace population has 9 visible wallets, and `power` returns immediately when a population has fewer than 10 visible wallets, so those plants are not in the 142.

The same `UNDETERMINED` classification is returned with known groups kept, with classes ignored, on the two geopolitics markets alone (0 eligible), and when contract or program-owned recipients are treated as services. Details are in `derived/results.json`.

An independent recount, using the withdrawal rule copied from the plan rather than the printed table, reproduces the reference (78 visible, 37 censored, 9 shared recipients, M = 5) and the Seoul row (60 visible, 9 censored, M = 2). The permutation p-values are those of `code/ana_50_stats.py`; recounting M does not re-draw the null.

## The one comparator overlap that is not empty

In the Seoul population, one wallet pair shares three recipients. Each recipient was classed `CUSTOMER`. The class pages, read on 19 November 2026, record:

| Recipient | Chain code | Relay users on the class pages | Example order |
|---|---|---:|---|
| `0x5b01ed6740816c54a1b7e27249e870c64f346723` | Polygon, no contract code | 3 | `0xdc84eae7ec39453327b22a5a57d2101074603115313e2a694bb5154cb55cd900` (14 March 2026) and `0x01770786c3219aea553fccf7c292bf84745a0b8947ad9c924766262b559dfc3c` (7 July 2026) |
| `0xcf3e79fe8a04a93a64eccddaf222d003710a45c9` | Polygon, 23-byte code, not flagged as a contract (matches an EIP-7702 delegation) | 4 | `0xe3ecee36c430b55d8640103bf0d52ff410d2d902d252892c002b55946b441aa8` (15 June 2026) |
| `0x2c0fb24e396617dac4808631aa0333cbd7160330` | Ethereum, no contract code | 5 | `0x17915658075560ce7d078d4e9199fd8afb5fc66d17c8e69908531d0c1dfe008f` (9 October 2026) |

The two wallets are `0x0a6d26d31b28fd5a84c301f8b27296612f3b1d0a` and `0xc7d02944a76b9f83b199e9090ecc92c82d241f8a`. p_M = 0.10 does not meet the frozen 0.01 threshold. Relay's index lists 3, 4 and 5 distinct users on requests delivered to each address; the committed files identify only the pair. No earlier file in this repository labels these three addresses. Sharing them does not establish common ownership or non-public information.

## Collection date

Comparator pages were read on 19 November 2026. Reference pages remain the 5 November archive. Amendment 001 recomputes comparator recipients using only orders created on or before 5 November 2026 23:59:59 UTC and reuses the primary reference result. The reference archive has no later order. Comparator M, S1 and the verdict do not change (`derived/index_horizon.json`). The registry records this line as exploratory because the script is not in the lock. The amendment and the exit statistics share one git commit, so git does not show that the amendment text was written first. `resultats_vus` is `non verifiable`.

## Post-hoc timing audit, not a second verdict

The frozen M uses lifetime withdrawals, including cash-outs after the shock. Restricting each comparator to withdrawals created strictly before its own shock gives M = 0 in all seven populations (`amendements/pre_shock_timing.py`, `derived/pre_shock_timing.json`). Seoul still has one shared recipient before its shock, but not two shared recipients with the same other wallet. The same cut on the reference, at 28 February 2026 06:15 UTC, also gives M = 0, with 34 wallets that already have a withdrawal and one shared recipient. The comparator result is the same reading as the reference, not a contrast with it. This was looked at after the primary table existed. It is not a p-value and it does not replace `UNDETERMINED`. It does block any reading of these lifetime overlaps as something observable at the shock.

## Adversarial reading

- **The selection already decides the word.** Seventeen of 24 populations are below 10 wallets, and the verdict needs 10 eligible comparators. `UNDETERMINED` follows before any exit p-value. The rate 0 of 2 with interval [0, 0.8419] spans all three rate classes. It is not evidence that the structure is rare.
- **The reference p-value is post hoc and coarse at 2,000 draws.** The plan says the reference shape was chosen because an earlier report already described it. The three stored 2,000-draw replicates of that same graph are 0.0010 (primary, 1 hit, the lowest of the three), 0.0020 (classes ignored) and 0.0025 (contracts treated as services). Extending the primary seed with the frozen `permutation_test` to 420,000 draws gives 500 hits and p = 0.00119. That is below the frozen 0.01 and above 0.05/44 = 0.00114. An independent audit of the same null reported 0.00128 with interval [0.00117, 0.00139]. Both long runs sit in that band. Quote the reference probability as about 0.0012 to 0.0013, post hoc. It does not say other markets lack the structure.
- **The reference M = 5 is three wallet pairs.** Two pairs are inside the known-group list. The third pair has a wallet outside that list. Removing it was not part of the frozen test.
- **Comparators are not 7 independent draws, and they are not independent of the reference.** Twenty-one wallets sit in two or more of the seven populations (one sits in three). Six reference wallets also sit in a comparator population.
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

Claim: the frozen rarity classification is `UNDETERMINED`. Source: `analysis_plan.md` verdict section and `code/common.py` `verdict`. Transactions: the reduced Relay orders in `data/relay/` and `data/relay_reference/`, classed in `data/classes.json`. Calculation: `code/ana_50_stats.py`. Test: 17 of 24 populations have fewer than 10 wallets, so at most 7 comparators can be eligible, and the rule needs 10. Result file: `derived/results.json`. Registry: 7 real-data lines, 44 comparisons. Limit: this is not a statement that the structure is rare, common, criminal, or predictive.

## Deviations

The plan says later changes are dated amendments and are listed here. None of these changes the frozen verdict or the locked files.

1. **Amendment 001 and `amendements/index_horizon.py`.** Collection-date cutoff at 5 November 2026 23:59:59 UTC. `resultats_vus: non verifiable`. Registry line `S_INDEX_HORIZON` is exploratory because the script is outside `PROTOCOL.lock`.
2. **`amendements/pre_shock_timing.py`.** Post hoc. No amendment text of its own, no registry line. Comparators and, in this report, the reference.
3. **Unscripted recount of M.** The reference (M = 5) and the Seoul row (M = 2) were recomputed from the reduced orders with the withdrawal rule copied from the plan. The script was not committed. It does not re-draw the null.
4. **Seoul pair drill-down.** The three shared recipients, the two wallets and the example order ids in the section above. Descriptive, after the primary table.
5. **Class responses stored without SHA-256.** `data/classes.json` records the class, the user count, the page count and the HTTP counters. It does not record a SHA-256 of the Relay or RPC responses used to class the 17 recipients. Those raw responses stayed on the local volume named in `code/common.py`.

# Signal engine

An experimental detection engine that runs beside PolySentinel's frozen rules. It looks for behaviour that public market data can show, on markets whose outcome a small group could know in advance, and it produces files an analyst can check.

It never says a wallet is an insider. It can say: several wallets show unusual exposure on a market whose outcome may be known to a restricted group, here are the transactions, the comparison groups, the links we could verify, and the other explanations.

## Two engines, strictly apart

**Prospective detection** (`prospective_detection.py`) uses only what was observed at the decision time. It cannot read outcomes, future prices, profit or win rates. A test enforces that it does not import the second engine, and a metamorphic test checks that adding later rows does not change a past decision.

**Post-event investigation** (`post_event_investigation.py`) runs after a market ends. It adds profit and loss, price changes at 1, 3 and 7 days, and a comparison with wallets on the other side. It writes to its own journal and never changes a sealed score.

Selecting on past winners would make the outcome part of the detector. This engine does not start from winners, and profit is not an input.

## Evidence axes

The axes stay separate. There is no total score, because adding them would hide what each one means.

| Axis | Module | What it measures | Reads |
|---|---|---|---|
| Market information risk | `market_information_risk.py` | Who decides the outcome and who could know it early | Title, resolution rules, tags |
| Wallet anomaly | `wallet_behavior.py` | Size and frequency breaks, new and concentrated wallets, concentration shifts | The wallet's observed trades |
| Position anomaly | `position_anomalies.py` | Spend for its context, weight in the market, size against liquidity, rapid accumulation | Trades, catalogue liquidity when recent |
| Synchrony | `collective_behavior.py` | Convergence between anomalous wallets, identical amounts, pairs repeated across events | Trades of one event |
| Funding | `funding_graph.py` | Confirmed transfers between wallets, shared funders, shared infrastructure | Receipts decoded on canonical blocks |
| Chronology quality | `evidence_scoring.py` | Whether the first public information is documented, gaps in our collection | Sources, collector gaps |
| Evidence completeness | `evidence_scoring.py` | What is present, missing, or unavailable | All of the above |

## Market information risk

Each market gets a decision structure: single actor, small group, corporate leadership, committee, government or military, judicial, embargoed statistic, competitive micro-event, competitive outcome, broad public, continuous price, natural phenomenon, or unresolved.

Two ordinal values follow from the structure: decision concentration (0 to 3) and plausible early access (0 to 2). Their sum gives `LOW`, `MEDIUM` or `HIGH`. This is a rubric that orders markets for review. It is not a probability, and a high level is not evidence that anything leaked. When no rule matches, the level is `UNKNOWN`, which is different from `LOW`.

Nothing is excluded for its type. Sport and elections are scored like any market: one player's yellow card or one candidate's withdrawal is a different structure from a match result or a national vote.

A dossier keeps four dates apart: when a restricted group knew (not observable, never inferred), the first credible public information, the official announcement, and the market's resolution. An unknown date stays unknown.

## Comparison groups

A measurement counts only if it is extreme against a comparator built from values stored before the decision. Strata combine market family, price zone, time to resolution, wallet maturity and liquidity class. A sparse stratum falls back to a coarser one and the output records the fallback.

No comparator means no finding, and the output says `COMPARATOR_INSUFFICIENT`. Too little history gives `BASELINE_INSUFFICIENT`. Entry price is never suspicious by itself: comparators are per price zone.

Rarity is also measured on combinations. A large buy can be ordinary and a new wallet can be ordinary, while a new, concentrated and large one is not, so `new_and_concentrated` compares against the share of all wallet-event pairs in the stratum that have the whole combination. A wallet in the top decile of spend for its context that is also new or concentrated is a *candidate*: alone it opens nothing, but three candidates on one outcome within 24 hours are corroborated behaviour.

## Categories

| Category | Meaning |
|---|---|
| `INSUFFICIENT_EVIDENCE` | Too little history or too few comparators to conclude. |
| `EXPLORATORY` | One unusual measurement, kept in the counters. No file. |
| `ANOMALOUS` | Behaviour unusual against its comparators: several findings on one wallet, or one extreme finding. |
| `CORROBORATED_BEHAVIOR` | The same, supported by another wallet or by observed funds. |

Findings on one wallet usually describe the same purchases, so they count as one block of evidence. Market risk is a prior and is never evidence about a trader. Only another wallet or confirmed money movement can corroborate. Shared exchanges and other infrastructure never do, and no link ever merges two owners. A category describes evidence, never a person.

## Queue and files

The queue has one line per event, so one busy event cannot hide others. It reads market structure first, then evidence. A re-observation does not reopen a case. A daily ceiling limits notifications; a case held by the ceiling stays visible and says so. Low-risk structures, such as a heavily traded match, are scored and queued but do not notify by themselves, because large bettors align on them every day. Continuous price markets never notify: their rate is a rough placebo.

A file holds 16 sections, the last three being phenomena kept apart, fund flows and deterministic checks: event and markets, wallets, chronology, amounts and positions, price and liquidity, signals, market information risk, comparators, funding and confirmed transactions, public information at the observed time, competing explanations, missing data, and a conclusion limited to the evidence.

Evidence arrives after the alert, in a new version. The first version stays as it was sealed.

## Positions

`reconstruct_from_fills` builds net positions from decoded exchange fills, using only fills where the wallet is the order's owner. The counterparty field is often an exchange or an operator, so a position is never inferred from it. Duplicates count once and removed logs do not count. Splits, merges, conversions and redemptions are outside fills: they need activity rows, and the post-event engine refuses to call a figure realized when they change the cost basis.

## Running in shadow mode

```sh
python -m signal_engine.service seal      # records code and configuration fingerprints
python -m signal_engine.service warmup    # past rows build state and comparators, and can open no case
python -m signal_engine.service once      # one bounded run
python -m signal_engine.service status
python -m signal_engine.service verify    # checks the hash chain
python -m signal_engine.service amend --reason "..."   # the only way to run changed code or configuration
```

It reads the collector's database read-only and keeps its own state outside the project. Each run is bounded in rows, memory and time. Notifications are local. It needs no key and no account, and it cannot trade.

## Limits

- No ground truth exists. Accounts named in public reports are allegations. There is no precision, recall or false positive rate, and none should be inferred from a category.
- The local clock orders events; it is not an independent timestamp.
- First seen by us is not account creation.
- Coverage is partial: taker-side rows, a size filter on the global feed, and a rotating set of followed markets. Maker activity and small trades elsewhere stay unseen, so concentration can be overstated.
- Rules and tags reflect their current text, which may have changed since a past trade.
- Public news coverage is limited: the absence of an article proves nothing.
- Unusual behaviour has many legal explanations, listed in every file.

## Phenomena kept apart

Each file separates six things, with `OBSERVED`, `NOT_OBSERVED` or `NOT_EVALUATED` and the data each would need: size or frequency anomaly, liquidity anomaly, behavioural coordination, presumed market manipulation, possible information advantage, and reaction to public information. Manipulation stays `NOT_EVALUATED` here: spoofing needs order creations and cancellations, and wash trading needs both sides of each fill with their controllers. A high volume or a price rise after a purchase is neither.

## Checks of a file

`case_checks.py` compares each file with the rows it was built from: transactions, amounts, identifiers, time order, proof behind each link, comparator sizes, dates of public information, declared gaps. Each check gives `PASS`, `FAIL`, `INCOMPLETE` or `NOT_VERIFIABLE`, and the overall result is `PASS` only if all of them pass. A file with no public source for its event therefore never reaches `PASS`, by design.

## Funding links

One log is one edge, keyed by chain, transaction and log index. Each link keeps its receipts with token, amount, block, role and completeness, and carries `SHARED_INFRASTRUCTURE`, `COMMON_FUNDING_ROUTE`, `BEHAVIORAL_SIMILARITY` or `POSSIBLE_COORDINATION`, always with `OWNERSHIP_NOT_ESTABLISHED`. Identities are never merged.

A transfer has a role read from its whole transaction: protocol settlement (standard and NegRisk exchanges and adapters), mint, burn, pass-through, or transfer. Only a transfer can support a funding route. On stored receipts of 173 investigated wallets (404 edges, 378 unique logs), a graph built on senders with protocol labels alone gives 1,596 wallet pairs and one group of 78 wallets, all through the zero address minting collateral and a conversion router. With roles, one pair remains. Clustering was therefore not adopted: it has nothing to group on this data. Receipts of sampled trades are not address histories, and the sender behind a mint is not in them, so most real funding routes are still unseen.

## Experiments

`signal_engine/experimental/` is not imported by the service and not covered by its seal. Results below come from `bench.py` on frozen rows with fixed seeds, reproducible byte for byte apart from timing; no insider label exists, so none of this is precision or recall.

Development and test are split by wallet groups and time, with one day of embargo, and the replay's period is excluded. Test: 19,339 rows, 2,627 scored wallet-days, two days only.

Change detection is a CUSUM on causal ranks of each wallet's own past, with time decay and one alarm per episode. Thresholds are chosen on development wallets against shuffled order.

| Injected pattern, 162 wallets, reference seed | CUSUM | Own median and MAD | Fixed quantile |
|---|---|---|---|
| Next 10 buys at 5 times their size | 65 | 36 | 26 |
| Next 10 buys at 20 times their size | 105 | 82 | 87 |
| Five buys in 40 minutes at 5 times the median | 27 | 13 | 3 |
| One buy at 100 times the median | 0 | 98 | 116 |
| New wallet, three buys at 100 times the population median (200 draws) | 0 | 0 | 0 |

Alarms per 1,000 scored wallet-days on test rows, real order then shuffled: CUSUM 6.5 and 0.4, own median and MAD 18.3 and 14.1, quantile 17.9 and 17.9. Shuffled order keeps only chance, so most baseline triggers are not changes.

What this supports: CUSUM finds sustained changes in wallets that have a history, with far fewer chance alarms. It sees neither a single large bet nor a new wallet, the pattern most discussed in insider cases; the engine's comparators cover those. Only about one wallet in twelve has eight buys in the development rows. The chosen threshold moved between seeds, because few alarms decide it. The time-gap stream and the event-level stream added almost nothing and stay out of any recommendation. Added to the live queue as one more finding, over three days, it raises cases from 69 to 89 and reviews stay at 5. It stays an experiment.

Ablation on the same window: removing collective behaviour takes reviews from 5 to 1 and cases from 69 to 59; removing funding changes nothing yet; removing market risk raises reviews to 9. These count load, not quality.

Near-duplicate titles were measured on 170 past cases: grouping them removes 13 %, and mostly merges different matches, so semantic deduplication was not adopted. Exact fingerprints already absorb 2,164 re-observations for those 170 cases.

Reproduce with `python -m signal_engine.experimental.bench --rows FILE --seed N`, `python -m signal_engine.experimental.funding_bench` and `python -m signal_engine.experimental.ablation`; each needs local collected data.

## State page

`reports/etat-polysentinel.html` is rewritten at each run and names a state for each component, such as `COLLECTION_REDUCED`, `SHADOW_REFUSED`, `SIMULATION_RUNNING` or `NO_VERIFIED_RESULT`, so that an empty table cannot be read as an absence of results.

# Methodology

What these investigations accept as evidence, and the errors they already paid for. Each rule points to the file where it comes from.

## Levels of evidence

| Level | Meaning |
|---|---|
| `CONFIRMED` | Shown directly by reproducible elements |
| `SUPPORTED` | Converging signs, proof incomplete |
| `HYPOTHESIS` | Interpretation not demonstrated |
| `REFUTED` | Contradicted by the data. Negative results stay in the record |
| `UNRESOLVED` | Not enough data |

A finding needs its sources, its method, its limits and its links. `scripts/validate_evidence.py` refuses a finding whose title cites a number, a hash or an address that is absent from the files it cites.

## Three readings that are never allowed

- A wallet labeled ChangeNOW does not identify its owner.
- A deposit into ChangeNOW followed by a later payout does not prove a transfer between the same people.
- Suspicious bets do not by themselves prove insider trading. Unusual behaviour, demonstrated coordination and demonstrated insider trading are three separate questions.

An address is not a person. No investigation here looks for a civil identity.

## How a study is run

- **Frozen plans.** Population, labels, windows, thresholds and tests are written before any result, then locked with SHA-256 hashes. Any later change is a dated amendment. See [the Ballon d'Or plan](investigations/ballon-dor-wallets/sources/collective/analysis_plan.md) and [its lock](investigations/ballon-dor-wallets/sources/collective/PROTOCOL.lock).
- **Positive controls before the freeze.** A test that cannot find a planted effect says nothing when it finds none. See [the funding study controls](investigations/edge-polymarket/sources/funding/controles/controles_positifs.md).
- **Every test goes in a register**, including sweeps and exploratory ones. The Ballon d'Or study counts 140,114 real comparisons, so its Bonferroni threshold is 3.57e-07: [results](investigations/ballon-dor-wallets/sources/collective/results.md).
- **Out of sample.** Thresholds are frozen on TRAIN before VALID or TEST is read: [phase 8](investigations/maduro-iran/sources/phase8/PROTOCOLE_PREENREGISTRE.md), [phase 9](investigations/maduro-iran/sources/phase9/PROTOCOLE_P9.md).
- **Rankings before names.** Publicly reported accounts are allegations, never ground truth. A detector is sealed before any list of names is read, and no precision or recall is computed from them: [historical case protocol](investigations/polysentinel/sources/docs/HISTORICAL_CASE_PROTOCOL.md).
- **Independent audit.** The Ballon d'Or report was audited from its evidence files, and the audit changed it: [audit](investigations/ballon-dor-audit/sources/RAPPORT_AUDIT.md). The auditor is also an instance of Claude, which limits how independent it is.

## On-chain reading

- **The trading account is not the signing key.** The Polymarket data API indexes the trading account, which is either the key itself or a deterministic deposit wallet. Querying the key returned false zeros: [case 05](investigations/changenow-polymarket/sources/case_05_proxy_resolved.md).
- **Bridges are crossed by records, not by amounts.** A link between chains rests only on the protocol's own record, or on an identifier read on both chains. Amount and timing alone prove nothing: [flow-trace](investigations/ballon-dor-flow-trace/sources/README.md). Calldata can settle a hop: the `minReturn` of a Bridgers call equals the amount received on TRON: [first Maduro report](investigations/maduro-iran/sources/phase4/RAPPORT_PHASE4_2026-09-29.md).
- **Read native transfers and key histories before writing "no link".** An ETH transfer between two keys was missed by the first report because the funding path only followed tokens: [audit, C1](investigations/ballon-dor-audit/sources/RAPPORT_AUDIT.md).
- **A shared service is not a link.** One ChangeNOW wallet has 1,656,021 transactions, so two accounts touching it says nothing: [ChangeNOW proof](investigations/changenow-proof/sources/reports/CHANGENOW_PROOF_FINAL.md). A common transaction can be a batch: 2,711 accounts were redeemed in 136 transactions on one market: [counter-verification](investigations/ballon-dor-wallets/sources/reports/CONTRE_VERIFICATION.md).
- **Labels copy each other.** Count lineages of sources, not lists, and measure the behaviour of an address apart from its label: [outflows plan](investigations/changenow-outflows/sources/PLAN.md).
- **Address poisoning.** Fake tokens and zero-value transfers inflated one count of destinations from 25 to 156. Only official token contracts count: [phase 4](investigations/maduro-iran/sources/phase4/RAPPORT_PHASE4_2026-09-29.md).
- **Live feeds lie quietly.** The RTDS feed sent 890 markets without a `conditionId`, which a listener filed into one false market: [phase 15](investigations/maduro-iran/sources/phase15/RAPPORT_PHASE15.md).

## Cross-event network reconstruction

The November 6 follow-up applies the same standards to a 38-account Iran cohort and to separate Venezuela/Iran withdrawals. See the [verified findings index](VERIFIED_FINANCIAL_FINDINGS.md) and [wallet-level evidence](research_notes/x-history-2026-11-06/verification/REPORT.md).

- **Describe the edge, not the owner.** Record direct token/native value transfers, matched Relay orders, shared deposit destinations, and timing correlations as different edge types. A direct transfer is stronger evidence of a financial relationship than two customers using the same bridge or exchange; neither alone proves joint control of trading keys.
- **Identify exchange deposits by behaviour.** Check which hot wallet supplies gas, whether a deposit address sweeps balances after each credit, whether the same customer deposit address receives multiple Polymarket withdrawals, and whether unrelated users of the exchange pay that address. Shared customer deposits support a common payout account, not attribution to a specific natural person.
- **Use exact account populations.** Distinguish the eight-account Maduro/Iran network, the 38-account February Iran cohort, and the separate three-account cash-out link. A known overlap must be measured by proxy and route, not by the thematic similarity of their bets. Do not sum figures from different scopes without reconciling duplicate accounts or open positions.
- **Market chronology needs executable times.** Keep the public post's timestamp, market listing metadata, first executed fill, order placement time (if known), and price repricing time separate. A maker fill establishes when a resting order matched, not when the trader originally submitted it. The [Ballon d'Or time study](research_notes/x-history-2026-11-06/verification/ANALYSIS_PLAN.md) treats before/after comparisons and placebo windows explicitly.
- **Check unit economics before ranking winners.** Deposits, outflows, volume, payouts, realised trading result and inventory value are distinct. Reconstruct buys, sells, splits, merges, redemptions, token decimals, fees, and remaining shares. On-chain cash movements across a service do not automatically equal customer trading profit.
- **Archive source provenance.** Historical X posts are leads until the complete text (including `note_tweet` when required), edit provenance, media and `created_at` have been preserved. X Snowflake timestamps can check time encoding, not text authenticity. A repeated post or a summary derived from it is not an independent corroboration. [Corpus and source adjudication](research_notes/x-corpus-reconciliation-2026-11-06/REPORT.md).

## Statistics

- **Selection.** Accounts chosen by the press after the fact, or found from large winners, cannot show that a trait is rare. Compare with people selected on having traded, not on having won: [census protocol](investigations/ballon-dor-census/sources/PROTOCOL.md).
- **Unusable comparators.** A base rate built on truncated histories is invalid: 48 of 78 comparator wallets were unusable: [counter-verification](investigations/ballon-dor-wallets/sources/reports/CONTRE_VERIFICATION.md).
- **Absence of proof is not proof of absence.** A test without a positive control can only say "not found": [audit, C6](investigations/ballon-dor-audit/sources/RAPPORT_AUDIT.md).
- **Replay figures before citing them.** A false total stayed in notes for a month because nobody replayed it: [history of figures](investigations/changenow-polymarket/results/history_of_figures.md).

## Data handling

Original folders are only ever read. Each import records every file with its size and SHA-256, published or not, and why. Secrets, raw HTTP caches, Polymarket profile fields (`bio`, `pseudonym`), images and third-party content stay out of git. A file marked `local_only` is not archived here, and nothing in this repository may claim that it is.

# External research map — Polymarket insider risk and market abuse

**As of:** 2026-11-17 UTC. **Status:** SOURCE DISCOVERY / NON-REPLICATED. **Owner:** this repository's research track.

This is a **separate, attributed literature and evidence map**, not an original chain investigation, a completed backtest or an endorsement of any allegation. The machine-readable [SOURCES.csv](SOURCES.csv) currently indexes **71 distinct source URLs**. It is a broad first-pass bibliography, **not an exhaustive census** of the web, X posts or all historical cases. Sources may change after the review date.

It lives outside `investigations/` because no source has passed the project's investigation-grade independent verification. It neither changes the root README nor replaces frozen evidence, prior findings, publication guards or existing collectors.

## Comparison with this repository

| Topic | What this repository already does | What external research adds | Coverage after this PR |
| --- | --- | --- | --- |
| Cross-chain funding / custody edges | Typed transfers, Relay orders, bridge and cash-out reconciliation; service-address caveats; case-specific proofs | ACDC specialised wallets; Inca's narrow profitable-wallet cohort; Bubblemaps media cases; legally documented identities | **Indexed only**; no outside wallet imported |
| Insider-like trade detection | Price-relative controls, frozen tests, false-positive controls, chronological splits; `NO_EDGE_VALIDATED` | Inca behavioural heuristics, ACDC Orca/Whale/Bot taxonomy, ForesightFlow ILS, vsbtc reveal jumps, IYKYK wallet ranker | Several method ideas overlap; **nothing newly validated** |
| Coordination and follower dynamics | Collective exposure shifts, case cohorts, activity-preserving alternatives, audited causal-timing correction | ACDC followers of Orcas; leading wallets vs followers; large independent historical datasets | **New comparison hypothesis**, not a lead-lag discovery |
| Volume manipulation / wash | Individual co-trading investigations and self-dealing concerns in prior method audit | Columbia network-based wash study; Solidus cross-symbol wash; independent reimplementations | **Large research gap**: no comparable population-scale wash verdict here |
| Oracle / settlement attacks | Resolution semantics in some case investigations; limited order-book study | UMA governance disputes, vote power, oracle adjudication vs real event; Fidonis and Bitquery | **Large research gap**: no systematic vote/proposal/dispute graph |
| Real execution and market microstructure | 2.5-day book observation, cost gates, negative edge | OpenMarket high-frequency data; historical order-book datasets; on-chain reverts | **Data coverage gap**: history is not proved by present-day quotes |
| Prosecutorial / legal ground truth | Published wallets as leads, not labels; no civil-name attribution | DOJ/CFTC Maduro and Google complaints; House inquiry, WIRED FOIA coverage | **New evidence tier**: allegations/charges are not convictions |
| Information pollution and misleading publicity | Source verification of historical X material in `METHODOLOGY.md` | WSJ fake promotion case; unverified posts and self-reported trader profits | **Separate manipulation class**, no attribution to wallet operators |
| Conflicting evidence / negative studies | Strong rejection culture and multiple-testing controls | Profit-concentration research, selection bias, market-maker alternative explanations, negative backtests | **Must be included** to avoid one-sided accusation collecting |

### What is genuinely complementary

1. **Inca Digital**: the public summary states a selection of 488 wallets with at most 10 markets and at least USD 30,000 realised profits, 39 flagged. The linked Google Drive document has **not been independently examined** in this pass. Source IDs: EXT-001, EXT-002. Do not call the 39 guilty, estimate recall, or treat narrow high-profit selection as a population sample.
2. **ACDC**: the author's 20 August 2026 pages report 78,496 longshot wagers across 12,355 wallets, 152 Orca-profile military wallets, and leading Orca trades followed by Whales/Bots. Results are **author-reported** and may share cases with the 38-wallet Iran cohort in this repository; match contract IDs and wallets before claiming independent replication. EXT-003–006.
3. **Wash trading**: Columbia's November 2025 network method labels about one quarter of historical volume *consistent with* wash trading. Its denominator, observation window and economic definition differ from unambiguous self-trades; reported counts are not a count of proven crime. Solidus also describes cross-symbol patterns. EXT-022–026.
4. **Legal reference cases**: publicly filed CFTC/DOJ complaints allege trading on privileged information concerning the Maduro operation and Google's Year in Search release. Court evidence is stronger for labeling an *alleged* operator than a high win rate, but still requires time-stamped procedural status and a chain/account mapping. EXT-015–018.
5. **Counterarguments and negative controls**: `Who Wins and Who Loses` argues largest winning PnL accounts are not readily explained by insider trades; IYKYK documents watchlist contamination of blind ranking; `usepancake/polymarket-history` explicitly says its synthetic last-price tape is not fill history. EXT-032, 053, 061.

## Files

- [SOURCES.csv](SOURCES.csv): 71 URL-level source records; `status` distinguishes author pages, abstracts, news, repository descriptions and unchecked report links.
- [CASES.md](CASES.md): case families, provenance and legal distinctions without invented joins.
- [RESEARCH_GAPS.md](RESEARCH_GAPS.md): staged test designs, no-live-trade conditions and falsification gates.
- [validate_sources.py](validate_sources.py): offline structural CSV checks (no network, no scrape, no opinion-based verification).

## Provenance and reuse rules

- Cite **authors and original links** wherever external facts are mentioned. This bibliography is authored here; the studies, wallet lists, code, data and graphs are **not** represented as original findings of this repository.
- `status` measures **what was actually inspected**, not the credibility of an insider allegation. `report_link_not_read`, `abstract_only`, `press_summary` and `social_snippet_unverified` are explicit incomplete-review states.
- Before integrating outside data or code: record upstream commit/tag/DOI, licence, redistribution rights, schema, timestamps, UTC normalization, chain/exchange type, cost, hashes, sampling limits, and data lineage. **A GitHub README claiming an open licence is not enough**; verify the file and the dataset licence separately.
- A wallet can be both market-maker and directional speculator. Two users touching Binance, ChangeNOW or Relay do not share an operator by that fact. A copied X post is not independent evidence.
- Two `OrderFilled` log rows may describe counterparties of a single economic trade; this is **not** itself wash trading. Do not mix Polymarket V1/V2, negRisk, position tokens, CLOB fills and synthetic bars without an explicit mapping and dedup.
- An oracle result is a protocol-defined settlement outcome, not necessarily the off-chain factual event. Track the exact market wording, rule version and oracle state.
- Separate `REPORTED_BY_SOURCE`, `REPRODUCED_INDEPENDENTLY`, `CONFIRMED_ON_CHAIN`, `UNDER_INVESTIGATION`, `CHARGED`, `ADJUDICATED`, `REFUTED` and `UNRESOLVED`. A procedural charge is not a guilty verdict.
- X posts require a stable post URL/ID, complete original text including long-form text, UTC created/edited time, media provenance and link to public primary corroboration. A platform-generated X trending summary is not the post. Specific original X post links are now indexed (EXT-062, EXT-066, EXT-067, EXT-071), alongside an author-thread mirror (EXT-068); inaccessible posts are not independently archived.
- The current publication's results still read **NO_EDGE_VALIDATED**, including the corrected sign in the 2026-11-17 collective-exposure audit; bibliographic expansion changes **no predictive or economic verdict**.

## Existing related work; avoid redoing it

- [Existing methodology](../../METHODOLOGY.md): strong standards for false positives, services and X archival.
- [Collective exposure method comparisons](../../investigations/collective-exposure-shifts/METHODS_REUSE.md): code-level review of five upstream repos (including intelliFi and smart-money), with previously identified leakage and sampling risks.
- [Book/edge research](../../EDGE_VERDICT.md): quantified lack of validated executable edge; existing GitHub source triage in `edge_research/data/github/`.
- [Historical cases](../../INVENTORY.md): generated inventory of the repository's investigations (do not edit).
- [Evidence-first financial index](../../VERIFIED_FINANCIAL_FINDINGS.md): existing verified on-chain relationships.

The next step for genuine completeness is **reproduction and linkage**, not importing reported numbers into `FINDINGS.md`. See [RESEARCH_GAPS.md](RESEARCH_GAPS.md).

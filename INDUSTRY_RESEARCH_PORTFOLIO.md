# Polymarket Insider-Risk Intelligence — Independent Research Portfolio

**Benjamin Da Cunha · Independent on-chain investigator**  
**Public research snapshot:** 18 November 2026  
**Focus:** Financial reconstruction, potentially informed trading, coordinated wallet behavior, prediction-market surveillance, and falsification of apparent signals.

## Executive assessment

This repository reconstructs how selected Polymarket accounts were funded, how they traded around consequential events, how payouts moved through wallets and cross-chain services, and whether observable behavior could have provided an earlier warning. It combines primary-chain transaction evidence, reconstructed trade ledgers, controlled statistical studies, historical-source review, and reproducible Python verification.

**Two findings must be kept separate:** the repository documents multiple transaction-level financial relationships, but **does not establish that any uncharged individual committed insider trading**; and its quantitative studies have **not validated a net executable predictive edge**. That separation is a methodological result, not a missing disclaimer.

For a fast review, start with the [verified financial evidence index](VERIFIED_FINANCIAL_FINDINGS.md), the [case-by-case review guide](FORENSIC_CASEBOOK.md), the [methodology](METHODOLOGY.md), and the [predictive-edge verdict](EDGE_VERDICT.md).

## Selected primary findings

| Investigation | Recorded evidence | What it does **not** establish | Technical source |
|---|---|---|---|
| **February 2026 Iran cohort** | 38 distinct Polymarket proxies; 36 newly created over four days; 32 direct Polygon payments to the same EVM destination, three further Polygon routes with 12 individually matched Relay credits. Combined recorded trading result **+1,576,522.86 USDC**, including eight accounts still holding shares. | One verified exchange customer, one beneficial owner, or illegal access to information. | [Strict proof-tier audit](research_notes/g38-proof-tier-audit-2026-11-08/REPORT.md) |
| **Maduro / Iran eight-account network** | Direct and intermediate financial paths across Polygon, Ethereum and TRON. **+$509,993.24** aggregate recorded trading PnL including remaining positions; **+$509,624.54** net external cash flow. | That these are solely Maduro/Iran profits, or that financial links imply an information source. | [Accounting and transaction graph](investigations/maduro-iran/FINDINGS.md) |
| **Nobel Peace Prize 2025** | A single Safe owner key sent **372,521.54 USDC** to eight Polymarket accounts; related withdrawal paths and transaction times are documented. | Control of every Safe, privileged knowledge, or a profitable copy-trading strategy. | [Follow-up findings](investigations/followup-20261113/FINDINGS.md) |
| **Ballon d'Or 2026** | 11 investigated accounts: **$304,137.63** observed deposits, **$493,094.76** withdrawals; **+$129,367.79** net flow only for seven settled accounts. A separate Kane account received **5,170 USDC** from a key linked to one investigated account. | Profit of all 11 accounts, a single controller, or proof that the correctly forecast ranking was secret. | [Ballon d'Or investigation](investigations/ballon-dor-wallets/FINDINGS.md) |
| **KPMG-related earnings markets** | **14** archived Relay-to-chain handoffs, with **18–50 s** delays and matched intermediary atomic amounts; 22 resolved Polymarket proxies in the wider accounting. | An insider-trading conviction, an exhaustive source-of-funds tracing, or calibrated p-values from the retrospectively selected cohort. | [Financial replay](research_notes/financial-links-replay-2026-11-07/REPORT.md) |
| **Railgun-funded Venezuela tree** | **71** single-bet proxy wallets within a funding tree: **5** winning positions and **66** losing positions; all five wins relate to one market. | 71 independent predictions, realized total PnL, or an informative signal derived from the five winners alone. | [Independent archive arithmetic](research_notes/financial-cycle-negative-control-20261118/REPORT.md) |
| **Cross-market payments** | 27 indexed same-transaction transfers across the Pulser/cashy/Car control relationships, totaling **14,699.999999 USDC** in recorded directional flow. | Common beneficial ownership or a winning trading strategy. | [Transaction-hash graph](research_notes/iran-pulser-cashy-crossmarket-2026-11-06/REPORT.md) |

The populations and measurement windows differ. **Do not add the financial results across rows:** the tables contain different cohorts, some of which may overlap, and distinguish trading PnL, external cash flow and gross transfers.

## Predictive surveillance: what was actually tested

| Approach | Test scale | Result |
|---|---|---|
| Sudden price ignition led by a new, concentrated wallet (LONELY_THIN) | 34,413-market source universe; 45 validation alerts in 44 events | **13/45** correct; price-relative excess **+3.5 percentage points**, **p = 0.33**. No significant advantage. [Study](PATTERN_RESEARCH.md) |
| Coordinated increases in net wallet exposure | 1,579-market replication; 266 alerts in 197 events | No supported edge. Audit discovered that 117 alert timestamps were not first-causal firings; a causal re-run gives **+0.7 pp** overall, with a confidence interval crossing zero. [Audit](investigations/collective-exposure-shifts/AUDIT.md) |
| Historical order-book and execution diagnostics | 15,555 paired YES/NO quotes; 630 imbalance signals; 12,224 taker control entries | No gross basket arbitrage observed; no supported post-cost execution edge in this narrow, two-event-family sample. [Results](edge_research/results.md) |
| Real-time surveillance | Polygon order-fill monitoring, market resolution, dated account history, one-hop funding and replayable alerts | Code and bounded live tests exist; sustained uninterrupted production coverage and profitability are **not certified**. [Monitor](monitoring/README.md) |

The standing verdict is [NO_EDGE_VALIDATED](EDGE_VERDICT.md). These studies were designed to test and potentially **refute** an explanation rather than retroactively fit a rule to a conspicuous winner.

## Forensic and technical capabilities evidenced by this repository

- **Primary-chain reconstruction:** Polygon order fills, ERC-20 and native-value transfers, proxy versus owner-key separation, transaction/log-index matching, safe accounting in token units.
- **Cross-chain analysis:** Relay order identifiers, bridge outputs, Polygon/Ethereum/TRON/Solana/Monad paths, documented unobservable exchange-internal credits.
- **Graph investigation:** direct payer-to-account relationships, typed service nodes, distinguishing a shared exchange address from a discriminating funding edge.
- **Statistical counter-investigation:** outcome-blind populations, frozen hypotheses, chronological holdouts, multiple-testing correction, event clustering, alternative explanations and negative controls.
- **Engineering and audit:** Python replay tools, immutable source snapshots, SHA-256 manifests, synthetic failure tests, publication guards, CI and explicitly logged non-reproduced raw sources.
- **Public-market surveillance:** source latency measurement, trade-feed coverage, on-chain versus API reconciliation, gap logging and as-of event timing.

## Distinctive methodology

An anomaly is not a legal conclusion. The repository uses the finding levels **CONFIRMED**, **SUPPORTED**, **HYPOTHESIS**, **REFUTED**, and **UNRESOLVED**. These describe the evidence for a *specific financial or analytical claim*, not guilt. The strongest findings are transaction relations or reconstructed ledger quantities, not claims about civil identities or secret information.

The default alternative explanations are public-information timing, chance, high-risk selection, hedging, market making, liquidity effects, shared relayers, exchange deposit-account reuse, retrospective winner selection, and incomplete raw archives. Claims are downgraded when those alternatives cannot be ruled out.

An essential example is the Iran 38-proxy case: a recipient swept assets in a Coinbase-like pattern, but the record cannot independently prove the credited customer account or common beneficial ownership. The [audit](research_notes/g38-proof-tier-audit-2026-11-08/REPORT.md) preserves that distinction.

## Relation to independent research

The [external research bibliography](research_notes/external-market-abuse-corpus-20261117/README.md) indexes 76 sources, including Inca Digital, Anti-Corruption Data Collective, public enforcement materials, academic work, and independent GitHub investigations. **Third-party claims remain attributed to their original authors** until separately replicated. Source indexing is not evidence that this repository re-created their reported wallets, metrics or legal conclusions.

An important comparison is Inca Digital's published analysis of profitable, concentrated bettors: this repository complements behavioral screening with transaction-level cross-chain trails and explicit negative controls. No independent replication of Inca's entire selection and scoring pipeline is claimed.

## Review and reproduction

1. Read [FORENSIC_CASEBOOK.md](FORENSIC_CASEBOOK.md) for per-case evidence tier, critical falsifier and source path.
2. Read [VERIFIED_FINANCIAL_FINDINGS.md](VERIFIED_FINANCIAL_FINDINGS.md) for figures, transaction anchors and accounting boundaries.
3. Read [METHODOLOGY.md](METHODOLOGY.md) for proof classes, chain-link rules and testing discipline.
4. Read [EDGE_VERDICT.md](EDGE_VERDICT.md), [PATTERN_RESEARCH.md](PATTERN_RESEARCH.md) and [collective-exposure audit](investigations/collective-exposure-shifts/AUDIT.md) for predictive failures and corrective work.
5. Follow [AGENTS.md](AGENTS.md) for publication invariants and the named offline validation commands.

**Reproduction boundary:** Some substantial raw tapes, API response caches and RPC archives are local-only and identified in [the inventory](INVENTORY.md) and [master report](MASTER_REPORT.md). Public scripts can reproduce the archived derived inputs they actually contain, but not necessarily the entire historic chain/API collection from GitHub alone. No claim of continuous production monitoring or validated tradable alpha is made.

## Research questions still open

The highest-priority insider-risk questions are whether an **already observed cash-out** can precede an independently traceable **new funding path and subsequent market entry**, whether wallet dormancy/reactivation predicts beyond public market prices, and whether *genuinely linked* collective exposure shifts behave differently from unrelated traders. These are **unvalidated hypotheses**, not reported findings. The [financial-cycle protocol](research_notes/financial-cycle-negative-control-20261118/REPORT.md) sets out event-time, control and executable-price requirements for the first hypothesis.

**Research objective:** produce independently inspectable financial graphs and a low-false-positive, event-time-valid surveillance signal. The demonstrated contribution today is the former; the latter remains an open scientific problem.
